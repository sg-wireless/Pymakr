# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a tool bar showing bookmarks.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt, QUrl, QCoreApplication
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWebKitWidgets import QWebPage

from E5Gui.E5ModelToolBar import E5ModelToolBar

import Helpviewer.HelpWindow

from .BookmarksModel import BookmarksModel


class BookmarksToolBar(E5ModelToolBar):
    """
    Class implementing a tool bar showing bookmarks.
    
    @signal openUrl(QUrl, str) emitted to open a URL in the current tab
    @signal newUrl(QUrl, str) emitted to open a URL in a new tab
    """
    openUrl = pyqtSignal(QUrl, str)
    newUrl = pyqtSignal(QUrl, str)
    
    def __init__(self, mainWindow, model, parent=None):
        """
        Constructor
        
        @param mainWindow reference to the main window (HelpWindow)
        @param model reference to the bookmarks model (BookmarksModel)
        @param parent reference to the parent widget (QWidget)
        """
        E5ModelToolBar.__init__(
            self, QCoreApplication.translate("BookmarksToolBar", "Bookmarks"),
            parent)
        
        self.__mw = mainWindow
        self.__bookmarksModel = model
        
        Helpviewer.HelpWindow.HelpWindow.bookmarksManager()\
            .bookmarksReloaded.connect(self.__rebuild)
        
        self.setModel(model)
        self.setRootIndex(model.nodeIndex(
            Helpviewer.HelpWindow.HelpWindow.bookmarksManager().toolbar()))
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__contextMenuRequested)
        self.activated.connect(self.__bookmarkActivated)
        
        self.setHidden(True)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        self._build()
    
    def __rebuild(self):
        """
        Private slot to rebuild the toolbar.
        """
        self.__bookmarksModel = \
            Helpviewer.HelpWindow.HelpWindow.bookmarksManager()\
            .bookmarksModel()
        self.setModel(self.__bookmarksModel)
        self.setRootIndex(self.__bookmarksModel.nodeIndex(
            Helpviewer.HelpWindow.HelpWindow.bookmarksManager().toolbar()))
        self._build()
    
    def __contextMenuRequested(self, pos):
        """
        Private slot to handle the context menu request.
        
        @param pos position the context menu shall be shown (QPoint)
        """
        act = self.actionAt(pos)
        menu = QMenu()
        
        if act is not None:
            v = act.data()
            
            if act.menu() is None:
                menuAction = menu.addAction(
                    self.tr("&Open"), self.__openBookmark)
                menuAction.setData(v)
                menuAction = menu.addAction(
                    self.tr("Open in New &Tab\tCtrl+LMB"),
                    self.__openBookmarkInNewTab)
                menuAction.setData(v)
                menu.addSeparator()
            
            menuAction = menu.addAction(
                self.tr("&Remove"), self.__removeBookmark)
            menuAction.setData(v)
            menu.addSeparator()
            
            menuAction = menu.addAction(
                self.tr("&Properties..."), self.__edit)
            menuAction.setData(v)
            menu.addSeparator()
        
        menu.addAction(self.tr("Add &Bookmark..."), self.__newBookmark)
        menu.addAction(self.tr("Add &Folder..."), self.__newFolder)
        
        menu.exec_(QCursor.pos())
    
    def __bookmarkActivated(self, idx):
        """
        Private slot handling the activation of a bookmark.
        
        @param idx index of the activated bookmark (QModelIndex)
        """
        assert idx.isValid()
        
        if self._mouseButton == Qt.XButton1:
            self.__mw.currentBrowser().pageAction(QWebPage.Back).trigger()
        elif self._mouseButton == Qt.XButton2:
            self.__mw.currentBrowser().pageAction(QWebPage.Forward).trigger()
        elif self._mouseButton == Qt.LeftButton:
            if self._keyboardModifiers & Qt.ControlModifier:
                self.newUrl.emit(
                    idx.data(BookmarksModel.UrlRole),
                    idx.data(Qt.DisplayRole))
            else:
                self.openUrl.emit(
                    idx.data(BookmarksModel.UrlRole),
                    idx.data(Qt.DisplayRole))
    
    def __openToolBarBookmark(self):
        """
        Private slot to open a bookmark in the current browser tab.
        """
        idx = self.index(self.sender())
        
        if self._keyboardModifiers & Qt.ControlModifier:
            self.newUrl.emit(
                idx.data(BookmarksModel.UrlRole),
                idx.data(Qt.DisplayRole))
        else:
            self.openUrl.emit(
                idx.data(BookmarksModel.UrlRole),
                idx.data(Qt.DisplayRole))
        self.resetFlags()
    
    def __openBookmark(self):
        """
        Private slot to open a bookmark in the current browser tab.
        """
        idx = self.index(self.sender())
        
        self.openUrl.emit(
            idx.data(BookmarksModel.UrlRole),
            idx.data(Qt.DisplayRole))
    
    def __openBookmarkInNewTab(self):
        """
        Private slot to open a bookmark in a new browser tab.
        """
        idx = self.index(self.sender())
        
        self.newUrl.emit(
            idx.data(BookmarksModel.UrlRole),
            idx.data(Qt.DisplayRole))
    
    def __removeBookmark(self):
        """
        Private slot to remove a bookmark.
        """
        idx = self.index(self.sender())
        
        self.__bookmarksModel.removeRow(idx.row(), self.rootIndex())
    
    def __newBookmark(self):
        """
        Private slot to add a new bookmark.
        """
        from .AddBookmarkDialog import AddBookmarkDialog
        dlg = AddBookmarkDialog()
        dlg.setCurrentIndex(self.rootIndex())
        dlg.exec_()
    
    def __newFolder(self):
        """
        Private slot to add a new bookmarks folder.
        """
        from .AddBookmarkDialog import AddBookmarkDialog
        dlg = AddBookmarkDialog()
        dlg.setCurrentIndex(self.rootIndex())
        dlg.setFolder(True)
        dlg.exec_()
    
    def _createMenu(self):
        """
        Protected method to create the menu for a tool bar action.
        
        @return menu for a tool bar action (E5ModelMenu)
        """
        from .BookmarksMenu import BookmarksMenu
        menu = BookmarksMenu(self)
        menu.openUrl.connect(self.openUrl)
        menu.newUrl.connect(self.newUrl)
        return menu
    
    def __edit(self):
        """
        Private slot to edit a bookmarks properties.
        """
        from .BookmarkPropertiesDialog import BookmarkPropertiesDialog
        idx = self.index(self.sender())
        node = self.__bookmarksModel.node(idx)
        dlg = BookmarkPropertiesDialog(node)
        dlg.exec_()
