# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to add a bookmark or a bookmark folder.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QModelIndex, QSortFilterProxyModel
from PyQt5.QtWidgets import QDialog, QTreeView

from .Ui_AddBookmarkDialog import Ui_AddBookmarkDialog


class AddBookmarkProxyModel(QSortFilterProxyModel):
    """
    Class implementing a proxy model used by the AddBookmarkDialog dialog.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(AddBookmarkProxyModel, self).__init__(parent)
    
    def columnCount(self, parent):
        """
        Public method to return the number of columns.
        
        @param parent index of the parent (QModelIndex)
        @return number of columns (integer)
        """
        return min(1, QSortFilterProxyModel.columnCount(self, parent))
    
    def filterAcceptsRow(self, sourceRow, sourceParent):
        """
        Public method to determine, if the row is acceptable.
        
        @param sourceRow row number in the source model (integer)
        @param sourceParent index of the source item (QModelIndex)
        @return flag indicating acceptance (boolean)
        """
        idx = self.sourceModel().index(sourceRow, 0, sourceParent)
        return self.sourceModel().hasChildren(idx)
    
    def filterAcceptsColumn(self, sourceColumn, sourceParent):
        """
        Public method to determine, if the column is acceptable.
        
        @param sourceColumn column number in the source model (integer)
        @param sourceParent index of the source item (QModelIndex)
        @return flag indicating acceptance (boolean)
        """
        return sourceColumn == 0
    
    def hasChildren(self, parent=QModelIndex()):
        """
        Public method to check, if a parent node has some children.
        
        @param parent index of the parent node (QModelIndex)
        @return flag indicating the presence of children (boolean)
        """
        sindex = self.mapToSource(parent)
        return self.sourceModel().hasChildren(sindex)


class AddBookmarkDialog(QDialog, Ui_AddBookmarkDialog):
    """
    Class implementing a dialog to add a bookmark or a bookmark folder.
    """
    def __init__(self, parent=None, bookmarksManager=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        @param bookmarksManager reference to the bookmarks manager
            object (BookmarksManager)
        """
        super(AddBookmarkDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__bookmarksManager = bookmarksManager
        self.__addedNode = None
        self.__addFolder = False
        
        if self.__bookmarksManager is None:
            import Helpviewer.HelpWindow
            self.__bookmarksManager = \
                Helpviewer.HelpWindow.HelpWindow.bookmarksManager()
        
        self.__proxyModel = AddBookmarkProxyModel(self)
        model = self.__bookmarksManager.bookmarksModel()
        self.__proxyModel.setSourceModel(model)
        
        self.__treeView = QTreeView(self)
        self.__treeView.setModel(self.__proxyModel)
        self.__treeView.expandAll()
        self.__treeView.header().setStretchLastSection(True)
        self.__treeView.header().hide()
        self.__treeView.setItemsExpandable(False)
        self.__treeView.setRootIsDecorated(False)
        self.__treeView.setIndentation(10)
        self.__treeView.show()
        
        self.locationCombo.setModel(self.__proxyModel)
        self.locationCombo.setView(self.__treeView)
        
        self.addressEdit.setInactiveText(self.tr("Url"))
        self.nameEdit.setInactiveText(self.tr("Title"))
        
        self.resize(self.sizeHint())
    
    def setUrl(self, url):
        """
        Public slot to set the URL of the new bookmark.
        
        @param url URL of the bookmark (string)
        """
        self.addressEdit.setText(url)
        self.resize(self.sizeHint())
    
    def url(self):
        """
        Public method to get the URL of the bookmark.
        
        @return URL of the bookmark (string)
        """
        return self.addressEdit.text()
    
    def setTitle(self, title):
        """
        Public method to set the title of the new bookmark.
        
        @param title title of the bookmark (string)
        """
        self.nameEdit.setText(title)
    
    def title(self):
        """
        Public method to get the title of the bookmark.
        
        @return title of the bookmark (string)
        """
        return self.nameEdit.text()
    
    def setDescription(self, description):
        """
        Public method to set the description of the new bookmark.
        
        @param description description of the bookamrk (string)
        """
        self.descriptionEdit.setPlainText(description)
    
    def description(self):
        """
        Public method to get the description of the bookmark.
        
        @return description of the bookamrk (string)
        """
        return self.descriptionEdit.toPlainText()
    
    def setCurrentIndex(self, idx):
        """
        Public method to set the current index.
        
        @param idx current index to be set (QModelIndex)
        """
        proxyIndex = self.__proxyModel.mapFromSource(idx)
        self.__treeView.setCurrentIndex(proxyIndex)
        self.locationCombo.setCurrentIndex(proxyIndex.row())
    
    def currentIndex(self):
        """
        Public method to get the current index.
        
        @return current index (QModelIndex)
        """
        idx = self.locationCombo.view().currentIndex()
        idx = self.__proxyModel.mapToSource(idx)
        return idx
    
    def setFolder(self, folder):
        """
        Public method to set the dialog to "Add Folder" mode.
        
        @param folder flag indicating "Add Folder" mode (boolean)
        """
        self.__addFolder = folder
        
        if folder:
            self.setWindowTitle(self.tr("Add Folder"))
            self.addressEdit.setVisible(False)
        else:
            self.setWindowTitle(self.tr("Add Bookmark"))
            self.addressEdit.setVisible(True)
        
        self.resize(self.sizeHint())
    
    def isFolder(self):
        """
        Public method to test, if the dialog is in "Add Folder" mode.
        
        @return flag indicating "Add Folder" mode (boolean)
        """
        return self.__addFolder
    
    def addedNode(self):
        """
        Public method to get a reference to the added bookmark node.
        
        @return reference to the added bookmark node (BookmarkNode)
        """
        return self.__addedNode
    
    def accept(self):
        """
        Public slot handling the acceptance of the dialog.
        """
        if (not self.__addFolder and not self.addressEdit.text()) or \
           not self.nameEdit.text():
            super(AddBookmarkDialog, self).accept()
            return
        
        from .BookmarkNode import BookmarkNode
        
        idx = self.currentIndex()
        if not idx.isValid():
            idx = self.__bookmarksManager.bookmarksModel().index(0, 0)
        parent = self.__bookmarksManager.bookmarksModel().node(idx)
        
        if self.__addFolder:
            type_ = BookmarkNode.Folder
        else:
            type_ = BookmarkNode.Bookmark
        bookmark = BookmarkNode(type_)
        bookmark.title = self.nameEdit.text()
        if not self.__addFolder:
            bookmark.url = self.addressEdit.text()
        bookmark.desc = self.descriptionEdit.toPlainText()
        
        self.__bookmarksManager.addBookmark(parent, bookmark)
        self.__addedNode = bookmark
        
        super(AddBookmarkDialog, self).accept()
