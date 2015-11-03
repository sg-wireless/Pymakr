# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the cookie model.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QAbstractTableModel, QSize, QModelIndex
from PyQt5.QtGui import QFont, QFontMetrics


class CookieModel(QAbstractTableModel):
    """
    Class implementing the cookie model.
    """
    def __init__(self, cookieJar, parent=None):
        """
        Constructor
        
        @param cookieJar reference to the cookie jar (CookieJar)
        @param parent reference to the parent object (QObject)
        """
        super(CookieModel, self).__init__(parent)
        
        self.__headers = [
            self.tr("Website"),
            self.tr("Name"),
            self.tr("Path"),
            self.tr("Secure"),
            self.tr("Expires"),
            self.tr("Contents"),
        ]
        self.__cookieJar = cookieJar
        self.__cookieJar.cookiesChanged.connect(self.__cookiesChanged)
        self.__cookieJar.load()
    
    def headerData(self, section, orientation, role):
        """
        Public method to get header data from the model.
        
        @param section section number (integer)
        @param orientation orientation (Qt.Orientation)
        @param role role of the data to retrieve (integer)
        @return requested data
        """
        if role == Qt.SizeHintRole:
            fm = QFontMetrics(QFont())
            height = fm.height() + fm.height() // 3
            width = \
                fm.width(self.headerData(section, orientation, Qt.DisplayRole))
            return QSize(width, height)
        
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                try:
                    return self.__headers[section]
                except IndexError:
                    return None
            
            return None
        
        return QAbstractTableModel.headerData(self, section, orientation, role)
    
    def data(self, index, role):
        """
        Public method to get data from the model.
        
        @param index index to get data for (QModelIndex)
        @param role role of the data to retrieve (integer)
        @return requested data
        """
        lst = []
        if self.__cookieJar is not None:
            lst = self.__cookieJar.cookies()
        if index.row() < 0 or index.row() >= len(lst):
            return None
        
        if role in (Qt.DisplayRole, Qt.EditRole):
            cookie = lst[index.row()]
            col = index.column()
            if col == 0:
                return cookie.domain()
            elif col == 1:
                return bytes(cookie.name()).decode()
            elif col == 2:
                return cookie.path()
            elif col == 3:
                return cookie.isSecure()
            elif col == 4:
                return cookie.expirationDate()
            elif col == 5:
                return cookie.value()
            else:
                return None
        
        return None
    
    def columnCount(self, parent=QModelIndex()):
        """
        Public method to get the number of columns of the model.
        
        @param parent parent index (QModelIndex)
        @return number of columns (integer)
        """
        if parent.isValid():
            return 0
        else:
            return len(self.__headers)
    
    def rowCount(self, parent=QModelIndex()):
        """
        Public method to get the number of rows of the model.
        
        @param parent parent index (QModelIndex)
        @return number of columns (integer)
        """
        if parent.isValid() or self.__cookieJar is None:
            return 0
        else:
            return len(self.__cookieJar.cookies())
    
    def removeRows(self, row, count, parent=QModelIndex()):
        """
        Public method to remove entries from the model.
        
        @param row start row (integer)
        @param count number of rows to remove (integer)
        @param parent parent index (QModelIndex)
        @return flag indicating success (boolean)
        """
        if parent.isValid() or self.__cookieJar is None:
            return False
        
        lastRow = row + count - 1
        self.beginRemoveRows(parent, row, lastRow)
        lst = self.__cookieJar.cookies()
        del lst[row:lastRow + 1]
        self.__cookieJar.setCookies(lst)
        self.endRemoveRows()
        
        return True
    
    def __cookiesChanged(self):
        """
        Private slot handling changes of the cookies list in the cookie jar.
        """
        self.beginResetModel()
        self.endResetModel()
