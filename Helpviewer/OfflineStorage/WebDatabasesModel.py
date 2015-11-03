# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the web databases model.
"""

from __future__ import unicode_literals

import sys

from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt
from PyQt5.QtWebKit import QWebSecurityOrigin, QWebDatabase


class WebDatabasesModel(QAbstractItemModel):
    """
    Class implementing the web databases model.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(WebDatabasesModel, self).__init__(parent)
        self.__headers = [
            self.tr("Name"),
            self.tr("Size")
        ]
        
        self.__data = []
        for origin in QWebSecurityOrigin.allOrigins():
            self.__data.append([origin, origin.databases()])
    
    def removeRows(self, row, count, parent=QModelIndex()):
        """
        Public method to remove databases from the model.
        
        @param row row of the first database to remove (integer)
        @param count number of databases to remove (integer)
        @param parent index of the security origin (QModelIndex)
        @return flag indicating successful removal (boolean)
        """
        if row < 0 or count <= 0 or row + count > self.rowCount(parent):
            return False
        
        if parent.isValid():
            self.beginRemoveRows(parent, row, row + count - 1)
            parentRow = parent.row()
            for db in self.__data[parentRow][1][row:row + count]:
                QWebDatabase.removeDatabase(db)
            del self.__data[parentRow][1][row:row + count]
            self.endRemoveRows()
        else:
            for parentRow in range(row, row + count):
                self.beginRemoveRows(self.index(parentRow, 0, parent),
                                     0, len(self.__data[parentRow][1]) - 1)
                for db in self.__data[parentRow][1]:
                    QWebDatabase.removeDatabase(db)
                del self.__data[parentRow][1][:]
                self.endRemoveRows()
        
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
        
        @param index index of entry to get data for (QModelIndex)
        @param role data role (integer)
        @return entry data
        """
        if not index.isValid() or index.model() != self:
            return None
        
        if role == Qt.DisplayRole:
            parent = index.parent()
            if not parent.isValid():
                # security origin
                origin = self.__data[index.row()][0]
                if index.column() == 0:
                    if origin.host() == "":
                        return self.tr("Local")
                    elif origin.port() == 0:
                        return "{0}://{1}".format(
                            origin.scheme(),
                            origin.host(),
                        )
                    else:
                        return "{0}://{1}:{2}".format(
                            origin.scheme(),
                            origin.host(),
                            origin.port(),
                        )
                elif index.column() == 1:
                    return self.__dataString(origin.databaseUsage())
            else:
                # web database
                db = self.__data[parent.row()][1][index.row()]
                if index.column() == 0:
                    return self.tr("{0} ({1})").format(
                        db.displayName(), db.name())
                elif index.column() == 1:
                    return self.__dataString(db.size())
    
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
            return len(self.__data)
        else:
            return len(self.__data[parent.row()][1])
    
    def index(self, row, column, parent=QModelIndex()):
        """
        Public method to get a model index for an entry.
        
        @param row row number (integer)
        @param column column number (integer)
        @param parent index of the parent (QModelIndex)
        @return index (QModelIndex)
        """
        if row < 0 or column < 0 or \
           row >= self.rowCount(parent) or column >= self.columnCount(parent):
            return QModelIndex()
        
        if parent.isValid():
            return self.createIndex(row, column, parent.row())
        else:
            return self.createIndex(row, column, sys.maxsize)
    
    def parent(self, index=QModelIndex()):
        """
        Public method to get the index of the parent entry.
        
        @param index index of the child entry (QModelIndex)
        @return index of the parent entry (QModelIndex)
        """
        if not index.isValid():
            return QModelIndex()
        
        if index.internalId() == sys.maxsize:
            return QModelIndex()
        
        return self.createIndex(index.internalId(), 0)
    
    def hasChildren(self, parent=QModelIndex()):
        """
        Public method to check, if a parent node has some children.
        
        @param parent index of the parent node (QModelIndex)
        @return flag indicating the presence of children (boolean)
        """
        if not parent.isValid():
            return True
        
        if parent.internalId() == sys.maxsize:
            return True
        
        return False
    
    def __dataString(self, size):
        """
        Private method to generate a formatted data string.
        
        @param size size to be formatted (integer)
        @return formatted data string (string)
        """
        unit = ""
        if size < 1024:
            unit = self.tr("bytes")
        elif size < 1024 * 1024:
            size /= 1024
            unit = self.tr("kB")
        else:
            size /= 1024 * 1024
            unit = self.tr("MB")
        return "{0:.1f} {1}".format(size, unit)
