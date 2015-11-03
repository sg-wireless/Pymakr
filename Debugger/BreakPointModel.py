# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Breakpoint model.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt, QAbstractItemModel, QModelIndex


class BreakPointModel(QAbstractItemModel):
    """
    Class implementing a custom model for breakpoints.
    """
    dataAboutToBeChanged = pyqtSignal(QModelIndex, QModelIndex)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QObject)
        """
        super(BreakPointModel, self).__init__(parent)
        
        self.breakpoints = []
        self.header = [
            self.tr("Filename"),
            self.tr("Line"),
            self.tr('Condition'),
            self.tr('Temporary'),
            self.tr('Enabled'),
            self.tr('Ignore Count'),
        ]
        self.alignments = [Qt.Alignment(Qt.AlignLeft),
                           Qt.Alignment(Qt.AlignRight),
                           Qt.Alignment(Qt.AlignLeft),
                           Qt.Alignment(Qt.AlignHCenter),
                           Qt.Alignment(Qt.AlignHCenter),
                           Qt.Alignment(Qt.AlignRight),
                           Qt.Alignment(Qt.AlignHCenter),
                           ]

    def columnCount(self, parent=QModelIndex()):
        """
        Public method to get the current column count.
        
        @param parent reference to parent index (QModelIndex)
        @return column count (integer)
        """
        return len(self.header)
    
    def rowCount(self, parent=QModelIndex()):
        """
        Public method to get the current row count.
        
        @param parent reference to parent index (QModelIndex)
        @return row count (integer)
        """
        # we do not have a tree, parent should always be invalid
        if not parent.isValid():
            return len(self.breakpoints)
        else:
            return 0
    
    def data(self, index, role=Qt.DisplayRole):
        """
        Public method to get the requested data.
        
        @param index index of the requested data (QModelIndex)
        @param role role of the requested data (Qt.ItemDataRole)
        @return the requested data
        """
        if not index.isValid():
            return None
        
        if role == Qt.DisplayRole:
            if index.column() in [0, 1, 2, 5]:
                return self.breakpoints[index.row()][index.column()]
        
        if role == Qt.CheckStateRole:
            if index.column() in [3, 4]:
                return self.breakpoints[index.row()][index.column()]
        
        if role == Qt.ToolTipRole:
            if index.column() in [0, 2]:
                return self.breakpoints[index.row()][index.column()]
        
        if role == Qt.TextAlignmentRole:
            if index.column() < len(self.alignments):
                return self.alignments[index.column()]
        
        return None
    
    def setData(self, index, value, role=Qt.EditRole):
        """
        Public method to change data in the model.
        
        @param index index of the changed data (QModelIndex)
        @param value value of the changed data
        @param role role of the changed data (Qt.ItemDataRole)
        @return flag indicating success (boolean)
        """
        if not index.isValid() or \
           index.column() >= len(self.header) or \
           index.row() >= len(self.breakpoints):
            return False
        
        self.dataAboutToBeChanged.emit(index, index)
        self.breakpoints[index.row()][index.column()] = value
        self.dataChanged.emit(index, index)
        return True
    
    def flags(self, index):
        """
        Public method to get item flags.
        
        @param index index of the requested flags (QModelIndex)
        @return item flags for the given index (Qt.ItemFlags)
        """
        if not index.isValid():
            return Qt.ItemIsEnabled
        
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Public method to get header data.
        
        @param section section number of the requested header data (integer)
        @param orientation orientation of the header (Qt.Orientation)
        @param role role of the requested data (Qt.ItemDataRole)
        @return header data
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section >= len(self.header):
                return ""
            else:
                return self.header[section]
        
        return None
    
    def index(self, row, column, parent=QModelIndex()):
        """
        Public method to create an index.
        
        @param row row number for the index (integer)
        @param column column number for the index (integer)
        @param parent index of the parent item (QModelIndex)
        @return requested index (QModelIndex)
        """
        if parent.isValid() or \
           row < 0 or row >= len(self.breakpoints) or \
           column < 0 or column >= len(self.header):
            return QModelIndex()
        
        return self.createIndex(row, column, self.breakpoints[row])

    def parent(self, index):
        """
        Public method to get the parent index.
        
        @param index index of item to get parent (QModelIndex)
        @return index of parent (QModelIndex)
        """
        return QModelIndex()
    
    def hasChildren(self, parent=QModelIndex()):
        """
        Public method to check for the presence of child items.
        
        @param parent index of parent item (QModelIndex)
        @return flag indicating the presence of child items (boolean)
        """
        if not parent.isValid():
            return len(self.breakpoints) > 0
        else:
            return False
    
    ###########################################################################
    
    def addBreakPoint(self, fn, line, properties):
        """
        Public method to add a new breakpoint to the list.
        
        @param fn filename of the breakpoint (string)
        @param line line number of the breakpoint (integer)
        @param properties properties of the breakpoint
            (tuple of condition (string), temporary flag (bool),
             enabled flag (bool), ignore count (integer))
        """
        bp = [fn, line] + list(properties)
        cnt = len(self.breakpoints)
        self.beginInsertRows(QModelIndex(), cnt, cnt)
        self.breakpoints.append(bp)
        self.endInsertRows()
    
    def setBreakPointByIndex(self, index, fn, line, properties):
        """
        Public method to set the values of a breakpoint given by index.
        
        @param index index of the breakpoint (QModelIndex)
        @param fn filename of the breakpoint (string)
        @param line line number of the breakpoint (integer)
        @param properties properties of the breakpoint
            (tuple of condition (string), temporary flag (bool),
             enabled flag (bool), ignore count (integer))
        """
        if index.isValid():
            row = index.row()
            index1 = self.createIndex(row, 0, self.breakpoints[row])
            index2 = self.createIndex(
                row, len(self.breakpoints[row]), self.breakpoints[row])
            self.dataAboutToBeChanged.emit(index1, index2)
            self.breakpoints[row] = [fn, line] + list(properties)
            self.dataChanged.emit(index1, index2)

    def setBreakPointEnabledByIndex(self, index, enabled):
        """
        Public method to set the enabled state of a breakpoint given by index.
        
        @param index index of the breakpoint (QModelIndex)
        @param enabled flag giving the enabled state (boolean)
        """
        if index.isValid():
            row = index.row()
            col = 4
            index1 = self.createIndex(row, col, self.breakpoints[row])
            self.dataAboutToBeChanged.emit(index1, index1)
            self.breakpoints[row][col] = enabled
            self.dataChanged.emit(index1, index1)
    
    def deleteBreakPointByIndex(self, index):
        """
        Public method to set the values of a breakpoint given by index.
        
        @param index index of the breakpoint (QModelIndex)
        """
        if index.isValid():
            row = index.row()
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.breakpoints[row]
            self.endRemoveRows()

    def deleteBreakPoints(self, idxList):
        """
        Public method to delete a list of breakpoints given by their indexes.
        
        @param idxList list of breakpoint indexes (list of QModelIndex)
        """
        rows = []
        for index in idxList:
            if index.isValid():
                rows.append(index.row())
        rows.sort(reverse=True)
        for row in rows:
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.breakpoints[row]
            self.endRemoveRows()

    def deleteAll(self):
        """
        Public method to delete all breakpoints.
        """
        if self.breakpoints:
            self.beginRemoveRows(QModelIndex(), 0, len(self.breakpoints) - 1)
            self.breakpoints = []
            self.endRemoveRows()

    def getBreakPointByIndex(self, index):
        """
        Public method to get the values of a breakpoint given by index.
        
        @param index index of the breakpoint (QModelIndex)
        @return breakpoint (list of seven values (filename, line number,
            condition, temporary flag, enabled flag, ignore count))
        """
        if index.isValid():
            return self.breakpoints[index.row()][:]  # return a copy
        else:
            return []

    def getBreakPointIndex(self, fn, lineno):
        """
        Public method to get the index of a breakpoint given by filename and
        line number.
        
        @param fn filename of the breakpoint (string)
        @param lineno line number of the breakpoint (integer)
        @return index (QModelIndex)
        """
        for row in range(len(self.breakpoints)):
            bp = self.breakpoints[row]
            if bp[0] == fn and bp[1] == lineno:
                return self.createIndex(row, 0, self.breakpoints[row])
        
        return QModelIndex()
    
    def isBreakPointTemporaryByIndex(self, index):
        """
        Public method to test, if a breakpoint given by its index is temporary.
        
        @param index index of the breakpoint to test (QModelIndex)
        @return flag indicating a temporary breakpoint (boolean)
        """
        if index.isValid():
            return self.breakpoints[index.row()][3]
        else:
            return False
