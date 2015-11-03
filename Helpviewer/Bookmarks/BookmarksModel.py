# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the bookmark model class.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex, QUrl, \
    QByteArray, QDataStream, QIODevice, QBuffer, QMimeData

import UI.PixmapCache


class BookmarksModel(QAbstractItemModel):
    """
    Class implementing the bookmark model.
    """
    TypeRole = Qt.UserRole + 1
    UrlRole = Qt.UserRole + 2
    UrlStringRole = Qt.UserRole + 3
    SeparatorRole = Qt.UserRole + 4
    
    MIMETYPE = "application/bookmarks.xbel"
    
    def __init__(self, manager, parent=None):
        """
        Constructor
        
        @param manager reference to the bookmark manager object
            (BookmarksManager)
        @param parent reference to the parent object (QObject)
        """
        super(BookmarksModel, self).__init__(parent)
        
        self.__endMacro = False
        self.__bookmarksManager = manager
        
        manager.entryAdded.connect(self.entryAdded)
        manager.entryRemoved.connect(self.entryRemoved)
        manager.entryChanged.connect(self.entryChanged)
        
        self.__headers = [
            self.tr("Title"),
            self.tr("Address"),
        ]
    
    def bookmarksManager(self):
        """
        Public method to get a reference to the bookmarks manager.
        
        @return reference to the bookmarks manager object (BookmarksManager)
        """
        return self.__bookmarksManager
    
    def nodeIndex(self, node):
        """
        Public method to get a model index.
        
        @param node reference to the node to get the index for (BookmarkNode)
        @return model index (QModelIndex)
        """
        parent = node.parent()
        if parent is None:
            return QModelIndex()
        return self.createIndex(parent.children().index(node), 0, node)
    
    def entryAdded(self, node):
        """
        Public slot to add a bookmark node.
        
        @param node reference to the bookmark node to add (BookmarkNode)
        """
        if node is None or node.parent() is None:
            return
        
        parent = node.parent()
        row = parent.children().index(node)
        # node was already added so remove before beginInsertRows is called
        parent.remove(node)
        self.beginInsertRows(self.nodeIndex(parent), row, row)
        parent.add(node, row)
        self.endInsertRows()
    
    def entryRemoved(self, parent, row, node):
        """
        Public slot to remove a bookmark node.
        
        @param parent reference to the parent bookmark node (BookmarkNode)
        @param row row number of the node (integer)
        @param node reference to the bookmark node to remove (BookmarkNode)
        """
        # node was already removed, re-add so beginRemoveRows works
        parent.add(node, row)
        self.beginRemoveRows(self.nodeIndex(parent), row, row)
        parent.remove(node)
        self.endRemoveRows()
    
    def entryChanged(self, node):
        """
        Public method to change a node.
        
        @param node reference to the bookmark node to change (BookmarkNode)
        """
        idx = self.nodeIndex(node)
        self.dataChanged.emit(idx, idx)
    
    def removeRows(self, row, count, parent=QModelIndex()):
        """
        Public method to remove bookmarks from the model.
        
        @param row row of the first bookmark to remove (integer)
        @param count number of bookmarks to remove (integer)
        @param parent index of the parent bookmark node (QModelIndex)
        @return flag indicating successful removal (boolean)
        """
        if row < 0 or count <= 0 or row + count > self.rowCount(parent):
            return False
        
        bookmarkNode = self.node(parent)
        children = bookmarkNode.children()[row:(row + count)]
        for node in children:
            if node == self.__bookmarksManager.menu() or \
               node == self.__bookmarksManager.toolbar():
                continue
            self.__bookmarksManager.removeBookmark(node)
        
        if self.__endMacro:
            self.__bookmarksManager.undoRedoStack().endMacro()
            self.__endMacro = False
        
        return True
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Public method to get the header data.
        
        @param section section number (integer)
        @param orientation header orientation (Qt.Orientation)
        @param role data role (integer)
        @return header data
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            try:
                return self.__headers[section]
            except IndexError:
                pass
        return QAbstractItemModel.headerData(self, section, orientation, role)
    
    def data(self, index, role=Qt.DisplayRole):
        """
        Public method to get data from the model.
        
        @param index index of bookmark to get data for (QModelIndex)
        @param role data role (integer)
        @return bookmark data
        """
        if not index.isValid() or index.model() != self:
            return None
        
        from .BookmarkNode import BookmarkNode
        
        bookmarkNode = self.node(index)
        if role in [Qt.EditRole, Qt.DisplayRole]:
            if bookmarkNode.type() == BookmarkNode.Separator:
                if index.column() == 0:
                    return 50 * '\xB7'
                elif index.column() == 1:
                    return ""
            
            if index.column() == 0:
                return bookmarkNode.title
            elif index.column() == 1:
                return bookmarkNode.url
        
        elif role == self.UrlRole:
            return QUrl(bookmarkNode.url)
        
        elif role == self.UrlStringRole:
            return bookmarkNode.url
        
        elif role == self.TypeRole:
            return bookmarkNode.type()
        
        elif role == self.SeparatorRole:
            return bookmarkNode.type() == BookmarkNode.Separator
        
        elif role == Qt.DecorationRole:
            if index.column() == 0:
                if bookmarkNode.type() == BookmarkNode.Folder:
                    return UI.PixmapCache.getIcon("dirOpen.png")
                import Helpviewer.HelpWindow
                return Helpviewer.HelpWindow.HelpWindow.icon(
                    QUrl(bookmarkNode.url))
        
        return None
    
    def columnCount(self, parent=QModelIndex()):
        """
        Public method to get the number of columns.
        
        @param parent index of parent (QModelIndex)
        @return number of columns (integer)
        """
        if parent.column() > 0:
            return 0
        else:
            return len(self.__headers)
    
    def rowCount(self, parent=QModelIndex()):
        """
        Public method to determine the number of rows.
        
        @param parent index of parent (QModelIndex)
        @return number of rows (integer)
        """
        if parent.column() > 0:
            return 0
        
        if not parent.isValid():
            return len(self.__bookmarksManager.bookmarks().children())
        
        itm = parent.internalPointer()
        return len(itm.children())
    
    def index(self, row, column, parent=QModelIndex()):
        """
        Public method to get a model index for a node cell.
        
        @param row row number (integer)
        @param column column number (integer)
        @param parent index of the parent (QModelIndex)
        @return index (QModelIndex)
        """
        if row < 0 or column < 0 or \
           row >= self.rowCount(parent) or column >= self.columnCount(parent):
            return QModelIndex()
        
        parentNode = self.node(parent)
        return self.createIndex(row, column, parentNode.children()[row])
    
    def parent(self, index=QModelIndex()):
        """
        Public method to get the index of the parent node.
        
        @param index index of the child node (QModelIndex)
        @return index of the parent node (QModelIndex)
        """
        if not index.isValid():
            return QModelIndex()
        
        itemNode = self.node(index)
        if itemNode is None:
            parentNode = None
        else:
            parentNode = itemNode.parent()
        
        if parentNode is None or \
                parentNode == self.__bookmarksManager.bookmarks():
            return QModelIndex()
        
        # get the parent's row
        grandParentNode = parentNode.parent()
        parentRow = grandParentNode.children().index(parentNode)
        return self.createIndex(parentRow, 0, parentNode)
    
    def hasChildren(self, parent=QModelIndex()):
        """
        Public method to check, if a parent node has some children.
        
        @param parent index of the parent node (QModelIndex)
        @return flag indicating the presence of children (boolean)
        """
        if not parent.isValid():
            return True
        
        from .BookmarkNode import BookmarkNode
        parentNode = self.node(parent)
        return parentNode.type() == BookmarkNode.Folder
    
    def flags(self, index):
        """
        Public method to get flags for a node cell.
        
        @param index index of the node cell (QModelIndex)
        @return flags (Qt.ItemFlags)
        """
        if not index.isValid():
            return Qt.NoItemFlags
        
        node = self.node(index)
        type_ = node.type()
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        
        if self.hasChildren(index):
            flags |= Qt.ItemIsDropEnabled
        
        if node == self.__bookmarksManager.menu() or \
           node == self.__bookmarksManager.toolbar():
            return flags
        
        flags |= Qt.ItemIsDragEnabled
        
        from .BookmarkNode import BookmarkNode
        if (index.column() == 0 and type_ != BookmarkNode.Separator) or \
           (index.column() == 1 and type_ == BookmarkNode.Bookmark):
            flags |= Qt.ItemIsEditable
        
        return flags
    
    def supportedDropActions(self):
        """
        Public method to report the supported drop actions.
        
        @return supported drop actions (Qt.DropAction)
        """
        return Qt.CopyAction | Qt.MoveAction
    
    def mimeTypes(self):
        """
        Public method to report the supported mime types.
        
        @return supported mime types (list of strings)
        """
        return [self.MIMETYPE, "text/uri-list"]
    
    def mimeData(self, indexes):
        """
        Public method to return the mime data.
        
        @param indexes list of indexes (QModelIndexList)
        @return mime data (QMimeData)
        """
        from .XbelWriter import XbelWriter
        
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)
        urls = []
        
        for index in indexes:
            if index.column() != 0 or not index.isValid():
                continue
            
            encodedData = QByteArray()
            buffer = QBuffer(encodedData)
            buffer.open(QIODevice.ReadWrite)
            writer = XbelWriter()
            parentNode = self.node(index)
            writer.write(buffer, parentNode)
            stream << encodedData
            urls.append(index.data(self.UrlRole))
        
        mdata = QMimeData()
        mdata.setData(self.MIMETYPE, data)
        mdata.setUrls(urls)
        return mdata
    
    def dropMimeData(self, data, action, row, column, parent):
        """
        Public method to accept the mime data of a drop action.
        
        @param data reference to the mime data (QMimeData)
        @param action drop action requested (Qt.DropAction)
        @param row row number (integer)
        @param column column number (integer)
        @param parent index of the parent node (QModelIndex)
        @return flag indicating successful acceptance of the data (boolean)
        """
        if action == Qt.IgnoreAction:
            return True
        
        if column > 0:
            return False
        
        parentNode = self.node(parent)
        
        if not data.hasFormat(self.MIMETYPE):
            if not data.hasUrls():
                return False
            
            from .BookmarkNode import BookmarkNode
            node = BookmarkNode(BookmarkNode.Bookmark, parentNode)
            node.url = bytes(data.urls()[0].toEncoded()).decode()
            
            if data.hasText():
                node.title = data.text()
            else:
                node.title = node.url
            
            self.__bookmarksManager.addBookmark(parentNode, node, row)
            return True
        
        ba = data.data(self.MIMETYPE)
        stream = QDataStream(ba, QIODevice.ReadOnly)
        if stream.atEnd():
            return False
        
        undoStack = self.__bookmarksManager.undoRedoStack()
        undoStack.beginMacro("Move Bookmarks")
        
        from .XbelReader import XbelReader
        while not stream.atEnd():
            encodedData = QByteArray()
            stream >> encodedData
            buffer = QBuffer(encodedData)
            buffer.open(QIODevice.ReadOnly)
            
            reader = XbelReader()
            rootNode = reader.read(buffer)
            for bookmarkNode in rootNode.children():
                rootNode.remove(bookmarkNode)
                row = max(0, row)
                self.__bookmarksManager.addBookmark(
                    parentNode, bookmarkNode, row)
                self.__endMacro = True
        
        return True
    
    def setData(self, index, value, role=Qt.EditRole):
        """
        Public method to set the data of a node cell.
        
        @param index index of the node cell (QModelIndex)
        @param value value to be set
        @param role role of the data (integer)
        @return flag indicating success (boolean)
        """
        if not index.isValid() or (self.flags(index) & Qt.ItemIsEditable) == 0:
            return False
        
        item = self.node(index)
        
        if role in (Qt.EditRole, Qt.DisplayRole):
            if index.column() == 0:
                self.__bookmarksManager.setTitle(item, value)
            elif index.column() == 1:
                self.__bookmarksManager.setUrl(item, value)
            else:
                return False
        
        elif role == BookmarksModel.UrlRole:
            self.__bookmarksManager.setUrl(item, value.toString())
        
        elif role == BookmarksModel.UrlStringRole:
            self.__bookmarksManager.setUrl(item, value)
        
        else:
            return False
        
        return True
    
    def node(self, index):
        """
        Public method to get a bookmark node given its index.
        
        @param index index of the node (QModelIndex)
        @return bookmark node (BookmarkNode)
        """
        itemNode = index.internalPointer()
        if itemNode is None:
            return self.__bookmarksManager.bookmarks()
        else:
            return itemNode
