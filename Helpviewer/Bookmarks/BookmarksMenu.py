# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the bookmarks menu.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt, QUrl
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QMenu

from E5Gui.E5ModelMenu import E5ModelMenu

from .BookmarksModel import BookmarksModel
from .BookmarkNode import BookmarkNode


class BookmarksMenu(E5ModelMenu):
    """
    Class implementing the bookmarks menu base class.
    
    @signal openUrl(QUrl, str) emitted to open a URL with the given title in
        the current tab
    @signal newUrl(QUrl, str) emitted to open a URL with the given title in a
        new tab
    """
    openUrl = pyqtSignal(QUrl, str)
    newUrl = pyqtSignal(QUrl, str)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        E5ModelMenu.__init__(self, parent)
        
        self.activated.connect(self.__activated)
        self.setStatusBarTextRole(BookmarksModel.UrlStringRole)
        self.setSeparatorRole(BookmarksModel.SeparatorRole)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__contextMenuRequested)
    
    def createBaseMenu(self):
        """
        Public method to get the menu that is used to populate sub menu's.
        
        @return reference to the menu (BookmarksMenu)
        """
        menu = BookmarksMenu(self)
        menu.openUrl.connect(self.openUrl)
        menu.newUrl.connect(self.newUrl)
        return menu
    
    def __activated(self, idx):
        """
        Private slot handling the activated signal.
        
        @param idx index of the activated item (QModelIndex)
        """
        if self._keyboardModifiers & Qt.ControlModifier:
            self.newUrl.emit(
                idx.data(BookmarksModel.UrlRole),
                idx.data(Qt.DisplayRole))
        else:
            self.openUrl.emit(
                idx.data(BookmarksModel.UrlRole),
                idx.data(Qt.DisplayRole))
        self.resetFlags()
    
    def postPopulated(self):
        """
        Public method to add any actions after the tree.
        """
        if self.isEmpty():
            return
        
        parent = self.rootIndex()
        
        hasBookmarks = False
        
        for i in range(parent.model().rowCount(parent)):
            child = parent.model().index(i, 0, parent)
            
            if child.data(BookmarksModel.TypeRole) == BookmarkNode.Bookmark:
                hasBookmarks = True
                break
        
        if not hasBookmarks:
            return
        
        self.addSeparator()
        act = self.addAction(self.tr("Open all in Tabs"))
        act.triggered.connect(self.openAll)
    
    def openAll(self):
        """
        Public slot to open all the menu's items.
        """
        menu = self.sender().parent()
        if menu is None:
            return
        
        parent = menu.rootIndex()
        if not parent.isValid():
            return
        
        for i in range(parent.model().rowCount(parent)):
            child = parent.model().index(i, 0, parent)
            
            if child.data(BookmarksModel.TypeRole) != BookmarkNode.Bookmark:
                continue
            
            if i == 0:
                self.openUrl.emit(
                    child.data(BookmarksModel.UrlRole),
                    child.data(Qt.DisplayRole))
            else:
                self.newUrl.emit(
                    child.data(BookmarksModel.UrlRole),
                    child.data(Qt.DisplayRole))
    
    def __contextMenuRequested(self, pos):
        """
        Private slot to handle the context menu request.
        
        @param pos position the context menu shall be shown (QPoint)
        """
        act = self.actionAt(pos)
        
        if act is not None and \
                act.menu() is None and \
                self.index(act).isValid():
            menu = QMenu()
            v = act.data()
            
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
            
            execAct = menu.exec_(QCursor.pos())
            if execAct is not None:
                self.close()
                parent = self.parent()
                while parent is not None and isinstance(parent, QMenu):
                    parent.close()
                    parent = parent.parent()
    
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
        self.removeEntry(idx)
    
    def __edit(self):
        """
        Private slot to edit a bookmarks properties.
        """
        from .BookmarkPropertiesDialog import BookmarkPropertiesDialog
        
        idx = self.index(self.sender())
        node = self.model().node(idx)
        dlg = BookmarkPropertiesDialog(node)
        dlg.exec_()

##############################################################################


class BookmarksMenuBarMenu(BookmarksMenu):
    """
    Class implementing a dynamically populated menu for bookmarks.
    
    @signal openUrl(QUrl, str) emitted to open a URL with the given title in
        the current tab
    """
    openUrl = pyqtSignal(QUrl, str)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        BookmarksMenu.__init__(self, parent)
        
        self.__bookmarksManager = None
        self.__initialActions = []
    
    def prePopulated(self):
        """
        Public method to add any actions before the tree.
       
        @return flag indicating if any actions were added (boolean)
        """
        import Helpviewer.HelpWindow
        
        self.__bookmarksManager = Helpviewer.HelpWindow.HelpWindow\
            .bookmarksManager()
        self.setModel(self.__bookmarksManager.bookmarksModel())
        self.setRootIndex(self.__bookmarksManager.bookmarksModel()
                          .nodeIndex(self.__bookmarksManager.menu()))
        
        # initial actions
        for act in self.__initialActions:
            if act == "--SEPARATOR--":
                self.addSeparator()
            else:
                self.addAction(act)
        if len(self.__initialActions) != 0:
            self.addSeparator()
        
        self.createMenu(
            self.__bookmarksManager.bookmarksModel()
                .nodeIndex(self.__bookmarksManager.toolbar()),
            1, self)
        return True
    
    def postPopulated(self):
        """
        Public method to add any actions after the tree.
        """
        if self.isEmpty():
            return
        
        parent = self.rootIndex()
        
        hasBookmarks = False
        
        for i in range(parent.model().rowCount(parent)):
            child = parent.model().index(i, 0, parent)
            
            if child.data(BookmarksModel.TypeRole) == BookmarkNode.Bookmark:
                hasBookmarks = True
                break
        
        if not hasBookmarks:
            return
        
        self.addSeparator()
        act = self.addAction(self.tr("Default Home Page"))
        act.setData("eric:home")
        act.triggered.connect(self.__defaultBookmarkTriggered)
        act = self.addAction(self.tr("Speed Dial"))
        act.setData("eric:speeddial")
        act.triggered.connect(self.__defaultBookmarkTriggered)
        self.addSeparator()
        act = self.addAction(self.tr("Open all in Tabs"))
        act.triggered.connect(self.openAll)
    
    def setInitialActions(self, actions):
        """
        Public method to set the list of actions that should appear first in
        the menu.
        
        @param actions list of initial actions (list of QAction)
        """
        self.__initialActions = actions[:]
        for act in self.__initialActions:
            self.addAction(act)
    
    def __defaultBookmarkTriggered(self):
        """
        Private slot handling the default bookmark menu entries.
        """
        act = self.sender()
        urlStr = act.data()
        if urlStr.startswith("eric:"):
            self.openUrl.emit(QUrl(urlStr), "")
