# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a widget showing the SQL connections.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt, qVersion
from PyQt5.QtWidgets import QWidget, QHeaderView, QTreeWidget, QVBoxLayout, \
    QTreeWidgetItem, QAction
from PyQt5.QtSql import QSqlDatabase


class SqlConnectionWidget(QWidget):
    """
    Class implementing a widget showing the SQL connections.
    
    @signal tableActivated(str) emitted after the entry for a table has been
        activated
    @signal schemaRequested(str) emitted when the schema display is requested
    @signal cleared() emitted after the connection tree has been cleared
    """
    tableActivated = pyqtSignal(str)
    schemaRequested = pyqtSignal(str)
    cleared = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(SqlConnectionWidget, self).__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.__connectionTree = QTreeWidget(self)
        self.__connectionTree.setObjectName("connectionTree")
        self.__connectionTree.setHeaderLabels([self.tr("Database")])
        if qVersion() >= "5.0.0":
            self.__connectionTree.header().setSectionResizeMode(
                QHeaderView.Stretch)
        else:
            self.__connectionTree.header().setResizeMode(QHeaderView.Stretch)
        refreshAction = QAction(self.tr("Refresh"), self.__connectionTree)
        self.__schemaAction = QAction(
            self.tr("Show Schema"), self.__connectionTree)
        
        refreshAction.triggered.connect(self.refresh)
        self.__schemaAction.triggered.connect(self.showSchema)
        
        self.__connectionTree.addAction(refreshAction)
        self.__connectionTree.addAction(self.__schemaAction)
        self.__connectionTree.setContextMenuPolicy(Qt.ActionsContextMenu)
        
        layout.addWidget(self.__connectionTree)
        
        self.__activating = False
        
        self.__connectionTree.itemActivated.connect(self.__itemActivated)
        self.__connectionTree.currentItemChanged.connect(
            self.__currentItemChanged)
        
        self.__activeDb = ""
    
    def refresh(self):
        """
        Public slot to refresh the connection tree.
        """
        self.__connectionTree.clear()
        self.cleared.emit()
        
        connectionNames = QSqlDatabase.connectionNames()
        
        foundActiveDb = False
        for name in connectionNames:
            root = QTreeWidgetItem(self.__connectionTree)
            db = QSqlDatabase.database(name, False)
            root.setText(0, self.__dbCaption(db))
            if name == self.__activeDb:
                foundActiveDb = True
                self.__setActive(root)
            if db.isOpen():
                tables = db.tables()
                for table in tables:
                    itm = QTreeWidgetItem(root)
                    itm.setText(0, table)
        
        if not foundActiveDb and connectionNames:
            self.__activeDb = connectionNames[0]
            self.__setActive(self.__connectionTree.topLevelItem(0))
    
    def showSchema(self):
        """
        Public slot to show schema data of a database.
        """
        cItm = self.__connectionTree.currentItem()
        if cItm is None or cItm.parent() is None:
            return
        self.__setActive(cItm.parent())
        self.schemaRequested.emit(cItm.text(0))
    
    def __itemActivated(self, itm, column):
        """
        Private slot handling the activation of an item.
        
        @param itm reference to the item (QTreeWidgetItem)
        @param column column that was activated (integer)
        """
        if itm is None:
            return
        
        if not self.__activating:
            self.__activating = True
            if itm.parent() is None:
                self.__setActive(itm)
            else:
                self.__setActive(itm.parent())
                self.tableActivated.emit(itm.text(0))
            self.__activating = False
    
    def __currentItemChanged(self, current, previous):
        """
        Private slot handling a change of the current item.
        
        @param current reference to the new current item (QTreeWidgetItem)
        @param previous reference to the previous current item
            (QTreeWidgetItem)
        """
        self.__schemaAction.setEnabled(
            current is not None and current.parent() is not None)
    
    def __dbCaption(self, db):
        """
        Private method to assemble a string for the caption.
        
        @param db reference to the database object (QSqlDatabase)
        @return caption string (string)
        """
        nm = db.driverName()
        nm += ":"
        if db.userName():
            nm += db.userName()
            nm += "@"
        nm += db.databaseName()
        return nm
    
    def __setBold(self, itm, bold):
        """
        Private slot to set the font to bold.
        
        @param itm reference to the item to be changed (QTreeWidgetItem)
        @param bold flag indicating bold (boolean)
        """
        font = itm.font(0)
        font.setBold(bold)
        itm.setFont(0, font)
    
    def currentDatabase(self):
        """
        Public method to get the current database.
        
        @return reference to the current database (QSqlDatabase)
        """
        return QSqlDatabase.database(self.__activeDb)
    
    def __setActive(self, itm):
        """
        Private slot to set an item to active.
        
        @param itm reference to the item to set as the active item
            (QTreeWidgetItem)
        """
        for index in range(self.__connectionTree.topLevelItemCount()):
            if self.__connectionTree.topLevelItem(index).font(0).bold():
                self.__setBold(
                    self.__connectionTree.topLevelItem(index), False)
        
        if itm is None:
            return
        
        self.__setBold(itm, True)
        self.__activeDb = QSqlDatabase.connectionNames()[
            self.__connectionTree.indexOfTopLevelItem(itm)]
