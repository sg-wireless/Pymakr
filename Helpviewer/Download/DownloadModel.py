# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the download model.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex, QMimeData, QUrl


class DownloadModel(QAbstractListModel):
    """
    Class implementing the download model.
    """
    def __init__(self, manager, parent=None):
        """
        Constructor
        
        @param manager reference to the download manager (DownloadManager)
        @param parent reference to the parent object (QObject)
        """
        super(DownloadModel, self).__init__(parent)
        
        self.__manager = manager
    
    def data(self, index, role):
        """
        Public method to get data from the model.
        
        @param index index to get data for (QModelIndex)
        @param role role of the data to retrieve (integer)
        @return requested data
        """
        if index.row() < 0 or index.row() >= self.rowCount(index.parent()):
            return None
        
        if role == Qt.ToolTipRole:
            if self.__manager.downloads()[index.row()]\
                    .downloadedSuccessfully():
                return self.__manager.downloads()[index.row()].getInfoData()
        
        return None
    
    def rowCount(self, parent=QModelIndex()):
        """
        Public method to get the number of rows of the model.
        
        @param parent parent index (QModelIndex)
        @return number of rows (integer)
        """
        if parent.isValid():
            return 0
        else:
            return self.__manager.count()
    
    def removeRows(self, row, count, parent=QModelIndex()):
        """
        Public method to remove bookmarks from the model.
        
        @param row row of the first bookmark to remove (integer)
        @param count number of bookmarks to remove (integer)
        @param parent index of the parent bookmark node (QModelIndex)
        @return flag indicating successful removal (boolean)
        """
        if parent.isValid():
            return False
        
        if row < 0 or count <= 0 or row + count > self.rowCount(parent):
            return False
        
        lastRow = row + count - 1
        for i in range(lastRow, row - 1, -1):
            if not self.__manager.downloads()[i].downloading():
                self.beginRemoveRows(parent, i, i)
                del self.__manager.downloads()[i]
                self.endRemoveRows()
        self.__manager.changeOccurred()
        return True
    
    def flags(self, index):
        """
        Public method to get flags for an item.
        
        @param index index of the node cell (QModelIndex)
        @return flags (Qt.ItemFlags)
        """
        if index.row() < 0 or index.row() >= self.rowCount(index.parent()):
            return Qt.NoItemFlags
        
        defaultFlags = QAbstractListModel.flags(self, index)
        
        itm = self.__manager.downloads()[index.row()]
        if itm.downloadedSuccessfully():
            return defaultFlags | Qt.ItemIsDragEnabled
        
        return defaultFlags
    
    def mimeData(self, indexes):
        """
        Public method to return the mime data.
        
        @param indexes list of indexes (QModelIndexList)
        @return mime data (QMimeData)
        """
        mimeData = QMimeData()
        urls = []
        for index in indexes:
            if index.isValid():
                itm = self.__manager.downloads()[index.row()]
                urls.append(QUrl.fromLocalFile(itm.absoluteFilePath()))
        mimeData.setUrls(urls)
        return mimeData
