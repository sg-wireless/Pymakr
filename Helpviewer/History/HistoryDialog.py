# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to manage history.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt, QUrl
from PyQt5.QtGui import QFontMetrics, QCursor
from PyQt5.QtWidgets import QDialog, QMenu, QApplication

from E5Gui.E5TreeSortFilterProxyModel import E5TreeSortFilterProxyModel

from .HistoryModel import HistoryModel

from .Ui_HistoryDialog import Ui_HistoryDialog


class HistoryDialog(QDialog, Ui_HistoryDialog):
    """
    Class implementing a dialog to manage history.
    
    @signal openUrl(QUrl, str) emitted to open a URL in the current tab
    @signal newUrl(QUrl, str) emitted to open a URL in a new tab
    """
    openUrl = pyqtSignal(QUrl, str)
    newUrl = pyqtSignal(QUrl, str)
    
    def __init__(self, parent=None, manager=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget
        @param manager reference to the history manager object (HistoryManager)
        """
        super(HistoryDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.__historyManager = manager
        if self.__historyManager is None:
            import Helpviewer.HelpWindow
            self.__historyManager = \
                Helpviewer.HelpWindow.HelpWindow.historyManager()
        
        self.__model = self.__historyManager.historyTreeModel()
        self.__proxyModel = E5TreeSortFilterProxyModel(self)
        self.__proxyModel.setSortRole(HistoryModel.DateTimeRole)
        self.__proxyModel.setFilterKeyColumn(-1)
        self.__proxyModel.setSourceModel(self.__model)
        self.historyTree.setModel(self.__proxyModel)
        self.historyTree.expandAll()
        fm = QFontMetrics(self.font())
        header = fm.width("m") * 40
        self.historyTree.header().resizeSection(0, header)
        self.historyTree.header().setStretchLastSection(True)
        self.historyTree.setContextMenuPolicy(Qt.CustomContextMenu)
        
        self.historyTree.activated.connect(self.__activated)
        self.historyTree.customContextMenuRequested.connect(
            self.__customContextMenuRequested)
        
        self.searchEdit.textChanged.connect(
            self.__proxyModel.setFilterFixedString)
        self.removeButton.clicked.connect(self.historyTree.removeSelected)
        self.removeAllButton.clicked.connect(self.__historyManager.clear)
        
        self.__proxyModel.modelReset.connect(self.__modelReset)
    
    def __modelReset(self):
        """
        Private slot handling a reset of the tree view's model.
        """
        self.historyTree.expandAll()
    
    def __customContextMenuRequested(self, pos):
        """
        Private slot to handle the context menu request for the bookmarks tree.
        
        @param pos position the context menu was requested (QPoint)
        """
        menu = QMenu()
        idx = self.historyTree.indexAt(pos)
        idx = idx.sibling(idx.row(), 0)
        if idx.isValid() and not self.historyTree.model().hasChildren(idx):
            menu.addAction(
                self.tr("&Open"), self.__openHistoryInCurrentTab)
            menu.addAction(
                self.tr("Open in New &Tab"), self.__openHistoryInNewTab)
            menu.addSeparator()
            menu.addAction(self.tr("&Copy"), self.__copyHistory)
        menu.addAction(self.tr("&Remove"), self.historyTree.removeSelected)
        menu.exec_(QCursor.pos())
    
    def __activated(self, idx):
        """
        Private slot to handle the activation of an entry.
        
        @param idx reference to the entry index (QModelIndex)
        """
        self.__openHistory(
            QApplication.keyboardModifiers() & Qt.ControlModifier)
        
    def __openHistoryInCurrentTab(self):
        """
        Private slot to open a history entry in the current browser tab.
        """
        self.__openHistory(False)
    
    def __openHistoryInNewTab(self):
        """
        Private slot to open a history entry in a new browser tab.
        """
        self.__openHistory(True)
    
    def __openHistory(self, newTab):
        """
        Private method to open a history entry.
        
        @param newTab flag indicating to open the history entry in a new tab
            (boolean)
        """
        idx = self.historyTree.currentIndex()
        if newTab:
            self.newUrl.emit(
                idx.data(HistoryModel.UrlRole),
                idx.data(HistoryModel.TitleRole))
        else:
            self.openUrl.emit(
                idx.data(HistoryModel.UrlRole),
                idx.data(HistoryModel.TitleRole))
    
    def __copyHistory(self):
        """
        Private slot to copy a history entry's URL to the clipboard.
        """
        idx = self.historyTree.currentIndex()
        if not idx.parent().isValid():
            return
        
        url = idx.data(HistoryModel.UrlStringRole)
        
        clipboard = QApplication.clipboard()
        clipboard.setText(url)
