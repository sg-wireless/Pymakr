# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the history model.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QUrl

import Helpviewer.HelpWindow


class HistoryModel(QAbstractTableModel):
    """
    Class implementing the history model.
    """
    DateRole = Qt.UserRole + 1
    DateTimeRole = Qt.UserRole + 2
    UrlRole = Qt.UserRole + 3
    UrlStringRole = Qt.UserRole + 4
    TitleRole = Qt.UserRole + 5
    MaxRole = TitleRole
    
    def __init__(self, historyManager, parent=None):
        """
        Constructor
        
        @param historyManager reference to the history manager object
            (HistoryManager)
        @param parent reference to the parent object (QObject)
        """
        super(HistoryModel, self).__init__(parent)
        
        self.__historyManager = historyManager
        
        self.__headers = [
            self.tr("Title"),
            self.tr("Address"),
        ]
        
        self.__historyManager.historyReset.connect(self.historyReset)
        self.__historyManager.entryRemoved.connect(self.historyReset)
        self.__historyManager.entryAdded.connect(self.entryAdded)
        self.__historyManager.entryUpdated.connect(self.entryUpdated)
    
    def historyReset(self):
        """
        Public slot to reset the model.
        """
        self.beginResetModel()
        self.endResetModel()
    
    def entryAdded(self):
        """
        Public slot to handle the addition of a history entry.
        """
        self.beginInsertRows(QModelIndex(), 0, 0)
        self.endInsertRows()
    
    def entryUpdated(self, row):
        """
        Public slot to handle the update of a history entry.
        
        @param row row number of the updated entry (integer)
        """
        idx = self.index(row, 0)
        self.dataChanged.emit(idx, idx)
    
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
        return QAbstractTableModel.headerData(self, section, orientation, role)
    
    def data(self, index, role=Qt.DisplayRole):
        """
        Public method to get data from the model.
        
        @param index index of history entry to get data for (QModelIndex)
        @param role data role (integer)
        @return history entry data
        """
        lst = self.__historyManager.history()
        if index.row() < 0 or index.row() > len(lst):
            return None
        
        itm = lst[index.row()]
        if role == self.DateTimeRole:
            return itm.dateTime
        elif role == self.DateRole:
            return itm.dateTime.date()
        elif role == self.UrlRole:
            return QUrl(itm.url)
        elif role == self.UrlStringRole:
            return itm.url
        elif role == self.TitleRole:
            return itm.userTitle()
        elif role in [Qt.DisplayRole, Qt.EditRole]:
            if index.column() == 0:
                return itm.userTitle()
            elif index.column() == 1:
                return itm.url
        elif role == Qt.DecorationRole:
            if index.column() == 0:
                return Helpviewer.HelpWindow.HelpWindow.icon(QUrl(itm.url))
        
        return None
    
    def columnCount(self, parent=QModelIndex()):
        """
        Public method to get the number of columns.
        
        @param parent index of parent (QModelIndex)
        @return number of columns (integer)
        """
        if parent.isValid():
            return 0
        else:
            return len(self.__headers)
    
    def rowCount(self, parent=QModelIndex()):
        """
        Public method to determine the number of rows.
        
        @param parent index of parent (QModelIndex)
        @return number of rows (integer)
        """
        if parent.isValid():
            return 0
        else:
            return len(self.__historyManager.history())
    
    def removeRows(self, row, count, parent=QModelIndex()):
        """
        Public method to remove history entries from the model.
        
        @param row row of the first history entry to remove (integer)
        @param count number of history entries to remove (integer)
        @param parent index of the parent entry (QModelIndex)
        @return flag indicating successful removal (boolean)
        """
        if parent.isValid():
            return False
        
        lastRow = row + count - 1
        self.beginRemoveRows(parent, row, lastRow)
        lst = self.__historyManager.history()[:]
        for index in range(lastRow, row - 1, -1):
            del lst[index]
        self.__historyManager.historyReset.disconnect(self.historyReset)
        self.__historyManager.setHistory(lst)
        self.__historyManager.historyReset.connect(self.historyReset)
        self.endRemoveRows()
        return True
