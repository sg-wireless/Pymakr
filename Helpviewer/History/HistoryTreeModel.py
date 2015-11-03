# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the history tree model.
"""

from __future__ import unicode_literals

import bisect

from PyQt5.QtCore import Qt, QModelIndex, QDate, QAbstractProxyModel

from .HistoryModel import HistoryModel

import UI.PixmapCache


class HistoryTreeModel(QAbstractProxyModel):
    """
    Class implementing the history tree model.
    """
    def __init__(self, sourceModel, parent=None):
        """
        Constructor
        
        @param sourceModel reference to the source model (QAbstractItemModel)
        @param parent reference to the parent object (QObject)
        """
        super(HistoryTreeModel, self).__init__(parent)
        
        self.__sourceRowCache = []
        self.__removingDown = False
        
        self.setSourceModel(sourceModel)
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Public method to get the header data.
        
        @param section section number (integer)
        @param orientation header orientation (Qt.Orientation)
        @param role data role (integer)
        @return header data
        """
        return self.sourceModel().headerData(section, orientation, role)
    
    def data(self, index, role=Qt.DisplayRole):
        """
        Public method to get data from the model.
        
        @param index index of history entry to get data for (QModelIndex)
        @param role data role (integer)
        @return history entry data
        """
        if role in [Qt.DisplayRole, Qt.EditRole]:
            start = index.internalId()
            if start == 0:
                offset = self.__sourceDateRow(index.row())
                if index.column() == 0:
                    idx = self.sourceModel().index(offset, 0)
                    date = idx.data(HistoryModel.DateRole)
                    if date == QDate.currentDate():
                        return self.tr("Earlier Today")
                    return date.toString("yyyy-MM-dd")
                if index.column() == 1:
                    return self.tr(
                        "%n item(s)", "",
                        self.rowCount(index.sibling(index.row(), 0)))
        
        elif role == Qt.DecorationRole:
            if index.column() == 0 and not index.parent().isValid():
                return UI.PixmapCache.getIcon("history.png")
        
        elif role == HistoryModel.DateRole:
            if index.column() == 0 and index.internalId() == 0:
                offset = self.__sourceDateRow(index.row())
                idx = self.sourceModel().index(offset, 0)
                return idx.data(HistoryModel.DateRole)
        
        return QAbstractProxyModel.data(self, index, role)
    
    def columnCount(self, parent=QModelIndex()):
        """
        Public method to get the number of columns.
        
        @param parent index of parent (QModelIndex)
        @return number of columns (integer)
        """
        return self.sourceModel().columnCount(self.mapToSource(parent))
    
    def rowCount(self, parent=QModelIndex()):
        """
        Public method to determine the number of rows.
        
        @param parent index of parent (QModelIndex)
        @return number of rows (integer)
        """
        if parent.internalId() != 0 or \
           parent.column() > 0 or \
           self.sourceModel() is None:
            return 0
        
        # row count OF dates
        if not parent.isValid():
            if self.__sourceRowCache:
                return len(self.__sourceRowCache)
            
            currentDate = QDate()
            rows = 0
            totalRows = self.sourceModel().rowCount()
            
            for row in range(totalRows):
                rowDate = self.sourceModel().index(row, 0)\
                    .data(HistoryModel.DateRole)
                if rowDate != currentDate:
                    self.__sourceRowCache.append(row)
                    currentDate = rowDate
                    rows += 1
            return rows
        
        # row count FOR a date
        start = self.__sourceDateRow(parent.row())
        end = self.__sourceDateRow(parent.row() + 1)
        return end - start
    
    def __sourceDateRow(self, row):
        """
        Private method to translate the top level date row into the offset
        where that date starts.
        
        @param row row number of the date (integer)
        @return offset where that date starts (integer)
        """
        if row <= 0:
            return 0
        
        if len(self.__sourceRowCache) == 0:
            self.rowCount(QModelIndex())
        
        if row >= len(self.__sourceRowCache):
            if self.sourceModel() is None:
                return 0
            return self.sourceModel().rowCount()
        
        return self.__sourceRowCache[row]
    
    def mapToSource(self, proxyIndex):
        """
        Public method to map an index to the source model index.
        
        @param proxyIndex reference to a proxy model index (QModelIndex)
        @return source model index (QModelIndex)
        """
        offset = proxyIndex.internalId()
        if offset == 0:
            return QModelIndex()
        startDateRow = self.__sourceDateRow(offset - 1)
        return self.sourceModel().index(
            startDateRow + proxyIndex.row(), proxyIndex.column())
    
    def index(self, row, column, parent=QModelIndex()):
        """
        Public method to create an index.
        
        @param row row number for the index (integer)
        @param column column number for the index (integer)
        @param parent index of the parent item (QModelIndex)
        @return requested index (QModelIndex)
        """
        if row < 0 or \
           column < 0 or \
           column >= self.columnCount(parent) or \
           parent.column() > 0:
            return QModelIndex()
        
        if not parent.isValid():
            return self.createIndex(row, column, 0)
        return self.createIndex(row, column, parent.row() + 1)

    def parent(self, index):
        """
        Public method to get the parent index.
        
        @param index index of item to get parent (QModelIndex)
        @return index of parent (QModelIndex)
        """
        offset = index.internalId()
        if offset == 0 or not index.isValid():
            return QModelIndex()
        return self.createIndex(offset - 1, 0, 0)
    
    def hasChildren(self, parent=QModelIndex()):
        """
        Public method to check, if an entry has some children.
        
        @param parent index of the entry to check (QModelIndex)
        @return flag indicating the presence of children (boolean)
        """
        grandparent = parent.parent()
        if not grandparent.isValid():
            return True
        return False
    
    def flags(self, index):
        """
        Public method to get the item flags.
        
        @param index index of the item (QModelIndex)
        @return flags (Qt.ItemFlags)
        """
        if not index.isValid():
            return Qt.ItemFlags(Qt.NoItemFlags)
        return Qt.ItemFlags(
            Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)
    
    def setSourceModel(self, sourceModel):
        """
        Public method to set the source model.
        
        @param sourceModel reference to the source model (QAbstractItemModel)
        """
        if self.sourceModel() is not None:
            self.sourceModel().modelReset.disconnect(self.__sourceReset)
            self.sourceModel().layoutChanged.disconnect(self.__sourceReset)
            self.sourceModel().rowsInserted.disconnect(
                self.__sourceRowsInserted)
            self.sourceModel().rowsRemoved.disconnect(self.__sourceRowsRemoved)
        
        super(HistoryTreeModel, self).setSourceModel(sourceModel)
        
        if self.sourceModel() is not None:
            self.__loaded = False
            self.sourceModel().modelReset.connect(self.__sourceReset)
            self.sourceModel().layoutChanged.connect(self.__sourceReset)
            self.sourceModel().rowsInserted.connect(self.__sourceRowsInserted)
            self.sourceModel().rowsRemoved.connect(self.__sourceRowsRemoved)
        
        self.beginResetModel()
        self.endResetModel()
    
    def __sourceReset(self):
        """
        Private slot to handle a reset of the source model.
        """
        self.beginResetModel()
        self.__sourceRowCache = []
        self.endResetModel()
    
    def __sourceRowsInserted(self, parent, start, end):
        """
        Private slot to handle the insertion of data in the source model.
        
        @param parent reference to the parent index (QModelIndex)
        @param start start row (integer)
        @param end end row (integer)
        """
        if not parent.isValid():
            if start != 0 or start != end:
                self.beginResetModel()
                self.__sourceRowCache = []
                self.endResetModel()
                return
            
            self.__sourceRowCache = []
            treeIndex = self.mapFromSource(self.sourceModel().index(start, 0))
            treeParent = treeIndex.parent()
            if self.rowCount(treeParent) == 1:
                self.beginInsertRows(QModelIndex(), 0, 0)
                self.endInsertRows()
            else:
                self.beginInsertRows(treeParent, treeIndex.row(),
                                     treeIndex.row())
                self.endInsertRows()
    
    def mapFromSource(self, sourceIndex):
        """
        Public method to map an index to the proxy model index.
        
        @param sourceIndex reference to a source model index (QModelIndex)
        @return proxy model index (QModelIndex)
        """
        if not sourceIndex.isValid():
            return QModelIndex()
        
        if len(self.__sourceRowCache) == 0:
            self.rowCount(QModelIndex())
        
        try:
            row = self.__sourceRowCache.index(sourceIndex.row())
        except ValueError:
            row = bisect.bisect_left(self.__sourceRowCache, sourceIndex.row())
        if row == len(self.__sourceRowCache) or \
           self.__sourceRowCache[row] != sourceIndex.row():
            row -= 1
        dateRow = max(0, row)
        row = sourceIndex.row() - self.__sourceRowCache[dateRow]
        return self.createIndex(row, sourceIndex.column(), dateRow + 1)
    
    def removeRows(self, row, count, parent=QModelIndex()):
        """
        Public method to remove entries from the model.
        
        @param row row of the first entry to remove (integer)
        @param count number of entries to remove (integer)
        @param parent index of the parent entry (QModelIndex)
        @return flag indicating successful removal (boolean)
        """
        if row < 0 or \
           count <= 0 or \
           row + count > self.rowCount(parent):
            return False
        
        self.__removingDown = True
        if parent.isValid() and self.rowCount(parent) == count - row:
            self.beginRemoveRows(QModelIndex(), parent.row(), parent.row())
        else:
            self.beginRemoveRows(parent, row, row + count - 1)
        if parent.isValid():
            # removing pages
            offset = self.__sourceDateRow(parent.row())
            return self.sourceModel().removeRows(offset + row, count)
        else:
            # removing whole dates
            for i in range(row + count - 1, row - 1, -1):
                dateParent = self.index(i, 0)
                offset = self.__sourceDateRow(dateParent.row())
                if not self.sourceModel().removeRows(
                        offset, self.rowCount(dateParent)):
                    return False
        return True
    
    def __sourceRowsRemoved(self, parent, start, end):
        """
        Private slot to handle the removal of data in the source model.
        
        @param parent reference to the parent index (QModelIndex)
        @param start start row (integer)
        @param end end row (integer)
        """
        if not self.__removingDown:
            self.beginResetModel()
            self.__sourceRowCache = []
            self.endResetModel()
            return
        
        if not parent.isValid():
            if self.__sourceRowCache:
                i = end
                while i >= start:
                    try:
                        ind = self.__sourceRowCache.index(i)
                    except ValueError:
                        ind = bisect.bisect_left(self.__sourceRowCache, i)
                    if ind == len(self.__sourceRowCache) or \
                       self.__sourceRowCache[ind] != i:
                        ind -= 1
                    row = max(0, ind)
                    offset = self.__sourceRowCache[row]
                    dateParent = self.index(row, 0)
                    # If we can remove all the rows in the date do that
                    # and skip over them.
                    rc = self.rowCount(dateParent)
                    if i - rc + 1 == offset and start <= i - rc + 1:
                        del self.__sourceRowCache[row]
                        i -= rc + 1
                    else:
                        row += 1
                        i -= 1
                    for j in range(row, len(self.__sourceRowCache)):
                        self.__sourceRowCache[j] -= 1
            
            if self.__removingDown:
                self.endRemoveRows()
                self.__removingDown = False
