# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to edit the various spell checking dictionaries.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot, Qt, QSortFilterProxyModel, QStringListModel
from PyQt5.QtWidgets import QDialog

from .Ui_SpellingDictionaryEditDialog import Ui_SpellingDictionaryEditDialog


class SpellingDictionaryEditDialog(QDialog, Ui_SpellingDictionaryEditDialog):
    """
    Class implementing a dialog to edit the various spell checking
    dictionaries.
    """
    def __init__(self, data, info, parent=None):
        """
        Constructor
        
        @param data contents to be edited (string)
        @param info info string to show at the header (string)
        @param parent reference to the parent widget (QWidget)
        """
        super(SpellingDictionaryEditDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.infoLabel.setText(info)
        
        self.__model = QStringListModel(data.splitlines(), self)
        self.__model.sort(0)
        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.__proxyModel.setDynamicSortFilter(True)
        self.__proxyModel.setSourceModel(self.__model)
        self.wordList.setModel(self.__proxyModel)
        
        self.searchEdit.textChanged.connect(
            self.__proxyModel.setFilterFixedString)
        
        self.removeButton.clicked.connect(self.wordList.removeSelected)
        self.removeAllButton.clicked.connect(self.wordList.removeAll)
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to handle adding an entry.
        """
        self.__model.insertRow(self.__model.rowCount())
        self.wordList.edit(
            self.__proxyModel.index(self.__model.rowCount() - 1, 0))
    
    def getData(self):
        """
        Public method to get the data.
        
        @return data of the dialog (string)
        """
        return os.linesep.join(
            [line for line in self.__model.stringList() if line])
