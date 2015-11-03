# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the cookie exceptions model.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QAbstractTableModel, QSize, QModelIndex
from PyQt5.QtGui import QFont, QFontMetrics


class CookieExceptionsModel(QAbstractTableModel):
    """
    Class implementing the cookie exceptions model.
    """
    def __init__(self, cookieJar, parent=None):
        """
        Constructor
        
        @param cookieJar reference to the cookie jar (CookieJar)
        @param parent reference to the parent object (QObject)
        """
        super(CookieExceptionsModel, self).__init__(parent)
        
        self.__cookieJar = cookieJar
        self.__allowedCookies = self.__cookieJar.allowedCookies()
        self.__blockedCookies = self.__cookieJar.blockedCookies()
        self.__sessionCookies = self.__cookieJar.allowForSessionCookies()
        
        self.__headers = [
            self.tr("Website"),
            self.tr("Status"),
        ]
    
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
        
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            try:
                return self.__headers[section]
            except IndexError:
                return None
        
        return QAbstractTableModel.headerData(self, section, orientation, role)
    
    def data(self, index, role):
        """
        Public method to get data from the model.
        
        @param index index to get data for (QModelIndex)
        @param role role of the data to retrieve (integer)
        @return requested data
        """
        if index.row() < 0 or index.row() >= self.rowCount():
            return None
        
        if role in (Qt.DisplayRole, Qt.EditRole):
            row = index.row()
            if row < len(self.__allowedCookies):
                if index.column() == 0:
                    return self.__allowedCookies[row]
                elif index.column() == 1:
                    return self.tr("Allow")
                else:
                    return None
            
            row -= len(self.__allowedCookies)
            if row < len(self.__blockedCookies):
                if index.column() == 0:
                    return self.__blockedCookies[row]
                elif index.column() == 1:
                    return self.tr("Block")
                else:
                    return None
            
            row -= len(self.__blockedCookies)
            if row < len(self.__sessionCookies):
                if index.column() == 0:
                    return self.__sessionCookies[row]
                elif index.column() == 1:
                    return self.tr("Allow For Session")
                else:
                    return None
            
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
        @return number of rows (integer)
        """
        if parent.isValid() or self.__cookieJar is None:
            return 0
        else:
            return len(self.__allowedCookies) + \
                len(self.__blockedCookies) + \
                len(self.__sessionCookies)
    
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
        for i in range(lastRow, row - 1, -1):
            rowToRemove = i
            
            if rowToRemove < len(self.__allowedCookies):
                del self.__allowedCookies[rowToRemove]
                continue
            
            rowToRemove -= len(self.__allowedCookies)
            if rowToRemove < len(self.__blockedCookies):
                del self.__blockedCookies[rowToRemove]
                continue
            
            rowToRemove -= len(self.__blockedCookies)
            if rowToRemove < len(self.__sessionCookies):
                del self.__sessionCookies[rowToRemove]
                continue
        
        self.__cookieJar.setAllowedCookies(self.__allowedCookies)
        self.__cookieJar.setBlockedCookies(self.__blockedCookies)
        self.__cookieJar.setAllowForSessionCookies(self.__sessionCookies)
        self.endRemoveRows()
        
        return True
    
    def addRule(self, host, rule):
        """
        Public method to add an exception rule.
        
        @param host name of the host to add a rule for (string)
        @param rule type of rule to add (CookieJar.Allow, CookieJar.Block or
            CookieJar.AllowForSession)
        """
        if not host:
            return
        
        from .CookieJar import CookieJar
        
        if rule == CookieJar.Allow:
            self.__addHost(
                host, self.__allowedCookies, self.__blockedCookies,
                self.__sessionCookies)
            return
        elif rule == CookieJar.Block:
            self.__addHost(
                host, self.__blockedCookies, self.__allowedCookies,
                self.__sessionCookies)
            return
        elif rule == CookieJar.AllowForSession:
            self.__addHost(
                host, self.__sessionCookies, self.__allowedCookies,
                self.__blockedCookies)
            return
    
    def __addHost(self, host, addList, removeList1, removeList2):
        """
        Private method to add a host to an exception list.
        
        @param host name of the host to add (string)
        @param addList reference to the list to add it to (list of strings)
        @param removeList1 reference to first list to remove it from
            (list of strings)
        @param removeList2 reference to second list to remove it from
            (list of strings)
        """
        if host not in addList:
            addList.append(host)
            if host in removeList1:
                removeList1.remove(host)
            if host in removeList2:
                removeList2.remove(host)
        
        # Avoid to have similar rules (with or without leading dot)
        # e.g. python-projects.org and .python-projects.org
        if host.startswith("."):
            otherRule = host[1:]
        else:
            otherRule = '.' + host
        if otherRule in addList:
            addList.removeOne(otherRule)
        if otherRule in removeList1:
            removeList1.remove(otherRule)
        if otherRule in removeList2:
            removeList2.remove(otherRule)
        
        self.beginResetModel()
        self.endResetModel()
