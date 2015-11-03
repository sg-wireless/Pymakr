# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a model for user agent management.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QModelIndex, QAbstractTableModel


class UserAgentModel(QAbstractTableModel):
    """
    Class implementing a model for user agent management.
    """
    def __init__(self, manager, parent=None):
        """
        Constructor
        
        @param manager reference to the user agent manager (UserAgentManager)
        @param parent reference to the parent object (QObject)
        """
        super(UserAgentModel, self).__init__(parent)
        
        self.__manager = manager
        self.__manager.changed.connect(self.__userAgentsChanged)
        
        self.__headers = [
            self.tr("Host"),
            self.tr("User Agent String"),
        ]
    
    def __userAgentsChanged(self):
        """
        Private slot handling a change of the registered user agent strings.
        """
        self.beginResetModel()
        self.endResetModel()
    
    def removeRows(self, row, count, parent=QModelIndex()):
        """
        Public method to remove entries from the model.
        
        @param row start row (integer)
        @param count number of rows to remove (integer)
        @param parent parent index (QModelIndex)
        @return flag indicating success (boolean)
        """
        if parent.isValid():
            return False
        
        if count <= 0:
            return False
        
        lastRow = row + count - 1
        
        self.beginRemoveRows(parent, row, lastRow)
        
        hostsList = self.__manager.allHostNames()
        for index in range(row, lastRow + 1):
            self.__manager.removeUserAgent(hostsList[index])
        
        # removeEngine emits changed()
        #self.endRemoveRows()
        
        return True
    
    def rowCount(self, parent=QModelIndex()):
        """
        Public method to get the number of rows of the model.
        
        @param parent parent index (QModelIndex)
        @return number of rows (integer)
        """
        if parent.isValid():
            return 0
        else:
            return self.__manager.hostsCount()
    
    def columnCount(self, parent=QModelIndex()):
        """
        Public method to get the number of columns of the model.
        
        @param parent parent index (QModelIndex)
        @return number of columns (integer)
        """
        return len(self.__headers)
    
    def data(self, index, role):
        """
        Public method to get data from the model.
        
        @param index index to get data for (QModelIndex)
        @param role role of the data to retrieve (integer)
        @return requested data
        """
        if index.row() >= self.__manager.hostsCount() or index.row() < 0:
            return None
        
        host = self.__manager.allHostNames()[index.row()]
        userAgent = self.__manager.userAgent(host)
        
        if userAgent is None:
            return None
        
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return host
            elif index.column() == 1:
                return userAgent
        
        return None
    
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
        
        return None
