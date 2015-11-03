# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a model for password management.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QModelIndex, QAbstractTableModel


class PasswordModel(QAbstractTableModel):
    """
    Class implementing a model for password management.
    """
    def __init__(self, manager, parent=None):
        """
        Constructor
        
        @param manager reference to the password manager (PasswordManager)
        @param parent reference to the parent object (QObject)
        """
        super(PasswordModel, self).__init__(parent)
        
        self.__manager = manager
        manager.changed.connect(self.__passwordsChanged)
        
        self.__headers = [
            self.tr("Website"),
            self.tr("Username"),
            self.tr("Password")
        ]
        
        self.__showPasswords = False
    
    def setShowPasswords(self, on):
        """
        Public methods to show passwords.
        
        @param on flag indicating if passwords shall be shown (boolean)
        """
        self.__showPasswords = on
        self.beginResetModel()
        self.endResetModel()
    
    def showPasswords(self):
        """
        Public method to indicate, if passwords shall be shown.
        
        @return flag indicating if passwords shall be shown (boolean)
        """
        return self.__showPasswords
    
    def __passwordsChanged(self):
        """
        Private slot handling a change of the registered passwords.
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
        
        siteList = self.__manager.allSiteNames()
        for index in range(row, lastRow + 1):
            self.__manager.removePassword(siteList[index])
        
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
            return self.__manager.sitesCount()
    
    def columnCount(self, parent=QModelIndex()):
        """
        Public method to get the number of columns of the model.
        
        @param parent parent index (QModelIndex)
        @return number of columns (integer)
        """
        if self.__showPasswords:
            return 3
        else:
            return 2
    
    def data(self, index, role):
        """
        Public method to get data from the model.
        
        @param index index to get data for (QModelIndex)
        @param role role of the data to retrieve (integer)
        @return requested data
        """
        if index.row() >= self.__manager.sitesCount() or index.row() < 0:
            return None
        
        site = self.__manager.allSiteNames()[index.row()]
        siteInfo = self.__manager.siteInfo(site)
        
        if siteInfo is None:
            return None
        
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return site
            elif index.column() in [1, 2]:
                return siteInfo[index.column() - 1]
        
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
