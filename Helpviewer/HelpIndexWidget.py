# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a window for showing the QtHelp index.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt, QUrl, QEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QMenu, \
    QDialog


class HelpIndexWidget(QWidget):
    """
    Class implementing a window for showing the QtHelp index.
    
    @signal linkActivated(QUrl) emitted when an index entry is activated
    @signal linksActivated(links, keyword) emitted when an index entry
        referencing multiple targets is activated
    @signal escapePressed() emitted when the ESC key was pressed
    """
    linkActivated = pyqtSignal(QUrl)
    linksActivated = pyqtSignal(dict, str)
    escapePressed = pyqtSignal()
    
    def __init__(self, engine, mainWindow, parent=None):
        """
        Constructor
        
        @param engine reference to the help engine (QHelpEngine)
        @param mainWindow reference to the main window object (QMainWindow)
        @param parent reference to the parent widget (QWidget)
        """
        super(HelpIndexWidget, self).__init__(parent)
        
        self.__engine = engine
        self.__mw = mainWindow
        
        self.__searchEdit = None
        self.__index = None
        
        self.__layout = QVBoxLayout(self)
        label = QLabel(self.tr("&Look for:"))
        self.__layout.addWidget(label)
        
        self.__searchEdit = QLineEdit()
        label.setBuddy(self.__searchEdit)
        self.__searchEdit.textChanged.connect(self.__filterIndices)
        self.__searchEdit.installEventFilter(self)
        self.__layout.addWidget(self.__searchEdit)
        
        self.__index = self.__engine.indexWidget()
        self.__index.installEventFilter(self)
        self.__engine.indexModel().indexCreationStarted.connect(
            self.__disableSearchEdit)
        self.__engine.indexModel().indexCreated.connect(
            self.__enableSearchEdit)
        self.__index.activated.connect(self.__activated)
        self.__searchEdit.returnPressed.connect(
            self.__index.activateCurrentItem)
        self.__layout.addWidget(self.__index)
        
        self.__index.viewport().installEventFilter(self)
    
    def __activated(self, idx):
        """
        Private slot to handle the activation of a keyword entry.
        
        @param idx index of the activated entry (QModelIndex)
        """
        model = self.__index.model()
        if model is not None:
            keyword = model.data(idx, Qt.DisplayRole)
            links = model.linksForKeyword(keyword)
            if len(links) == 1:
                self.linkActivated.emit(QUrl(links[list(links.keys())[0]]))
            else:
                self.linksActivated.emit(links, keyword)
    
    def __filterIndices(self, filter):
        """
        Private slot to filter the indices according to the given filter.
        
        @param filter filter to be used (string)
        """
        if '*' in filter:
            self.__index.filterIndices(filter, filter)
        else:
            self.__index.filterIndices(filter)
    
    def __enableSearchEdit(self):
        """
        Private slot to enable the search edit.
        """
        self.__searchEdit.setEnabled(True)
        self.__filterIndices(self.__searchEdit.text())
    
    def __disableSearchEdit(self):
        """
        Private slot to enable the search edit.
        """
        self.__searchEdit.setEnabled(False)
    
    def focusInEvent(self, evt):
        """
        Protected method handling focus in events.
        
        @param evt reference to the focus event object (QFocusEvent)
        """
        if evt.reason() != Qt.MouseFocusReason:
            self.__searchEdit.selectAll()
            self.__searchEdit.setFocus()
    
    def eventFilter(self, watched, event):
        """
        Public method called to filter the event queue.
        
        @param watched the QObject being watched (QObject)
        @param event the event that occurred (QEvent)
        @return flag indicating whether the event was handled (boolean)
        """
        if self.__searchEdit and watched == self.__searchEdit and \
           event.type() == QEvent.KeyPress:
            idx = self.__index.currentIndex()
            if event.key() == Qt.Key_Up:
                idx = self.__index.model().index(
                    idx.row() - 1, idx.column(), idx.parent())
                if idx.isValid():
                    self.__index.setCurrentIndex(idx)
            elif event.key() == Qt.Key_Down:
                idx = self.__index.model().index(
                    idx.row() + 1, idx.column(), idx.parent())
                if idx.isValid():
                    self.__index.setCurrentIndex(idx)
            elif event.key() == Qt.Key_Escape:
                self.escapePressed.emit()
        elif self.__index and watched == self.__index and \
                event.type() == QEvent.ContextMenu:
            idx = self.__index.indexAt(event.pos())
            if idx.isValid():
                menu = QMenu()
                curTab = menu.addAction(self.tr("Open Link"))
                newTab = menu.addAction(self.tr("Open Link in New Tab"))
                menu.move(self.__index.mapToGlobal(event.pos()))
                
                act = menu.exec_()
                if act == curTab:
                    self.__activated(idx)
                elif act == newTab:
                    model = self.__index.model()
                    if model is not None:
                        keyword = model.data(idx, Qt.DisplayRole)
                        links = model.linksForKeyword(keyword)
                        if len(links) == 1:
                            self.__mw.newTab(list(links.values())[0])
                        elif len(links) > 1:
                            from .HelpTopicDialog import HelpTopicDialog
                            dlg = HelpTopicDialog(self, keyword, links)
                            if dlg.exec_() == QDialog.Accepted:
                                self.__mw.newTab(dlg.link())
        elif self.__index and watched == self.__index.viewport() and \
                event.type() == QEvent.MouseButtonRelease:
            idx = self.__index.indexAt(event.pos())
            if idx.isValid() and event.button() == Qt.MidButton:
                model = self.__index.model()
                if model is not None:
                    keyword = model.data(idx, Qt.DisplayRole)
                    links = model.linksForKeyword(keyword)
                    if len(links) == 1:
                        self.__mw.newTab(list(links.values())[0])
                    elif len(links) > 1:
                        from .HelpTopicDialog import HelpTopicDialog
                        dlg = HelpTopicDialog(self, keyword, links)
                        if dlg.exec_() == QDialog.Accepted:
                            self.__mw.newTab(dlg.link())
        
        return QWidget.eventFilter(self, watched, event)
