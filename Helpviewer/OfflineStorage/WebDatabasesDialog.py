# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show all web databases.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QDialog

from E5Gui.E5TreeSortFilterProxyModel import E5TreeSortFilterProxyModel

from .Ui_WebDatabasesDialog import Ui_WebDatabasesDialog

from .WebDatabasesModel import WebDatabasesModel


class WebDatabasesDialog(QDialog, Ui_WebDatabasesDialog):
    """
    Class implementing a dialog to show all web databases.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(WebDatabasesDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.removeButton.clicked.connect(self.databasesTree.removeSelected)
        self.removeAllButton.clicked.connect(self.databasesTree.removeAll)
        
        model = WebDatabasesModel(self)
        self.__proxyModel = E5TreeSortFilterProxyModel(self)
        self.__proxyModel.setFilterKeyColumn(-1)
        self.__proxyModel.setSourceModel(model)
        
        self.searchEdit.textChanged.connect(
            self.__proxyModel.setFilterFixedString)
        
        self.databasesTree.setModel(self.__proxyModel)
        fm = QFontMetrics(self.font())
        header = fm.width("m") * 30
        self.databasesTree.header().resizeSection(0, header)
        self.databasesTree.model().sort(
            self.databasesTree.header().sortIndicatorSection(),
            Qt.AscendingOrder)
        self.databasesTree.expandAll()
