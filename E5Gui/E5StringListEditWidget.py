# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to edit a list of strings.
"""

from __future__ import unicode_literals
from PyQt5.QtCore import pyqtSlot, Qt, QSortFilterProxyModel, QStringListModel
from PyQt5.QtWidgets import QWidget, QInputDialog, QLineEdit

from .Ui_E5StringListEditWidget import Ui_E5StringListEditWidget


class E5StringListEditWidget(QWidget, Ui_E5StringListEditWidget):
    """
    Class implementing a dialog to edit a list of strings.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(E5StringListEditWidget, self).__init__(parent)
        self.setupUi(self)
        
        self.__model = QStringListModel(self)
        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.__proxyModel.setSourceModel(self.__model)
        self.stringList.setModel(self.__proxyModel)
        
        self.searchEdit.textChanged.connect(
            self.__proxyModel.setFilterFixedString)
        
        self.removeButton.clicked.connect(self.stringList.removeSelected)
        self.removeAllButton.clicked.connect(self.stringList.removeAll)
    
    def setList(self, stringList):
        """
        Public method to set the list of strings to be edited.
        
        @param stringList list of strings to be edited (list of string)
        """
        self.__model.setStringList(stringList)
        self.__model.sort(0)
    
    def getList(self):
        """
        Public method to get the edited list of strings.
        
        @return edited list of string (list of string)
        """
        return self.__model.stringList()[:]
    
    def setListWhatsThis(self, txt):
        """
        Public method to set a what's that help text for the string list.
        
        @param txt help text to be set (string)
        """
        self.stringList.setWhatsThis(txt)
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add an entry to the list.
        """
        entry, ok = QInputDialog.getText(
            self,
            self.tr("Add Entry"),
            self.tr("Enter the entry to add to the list:"),
            QLineEdit.Normal)
        if ok and entry != "" and entry not in self.__model.stringList():
            self.__model.insertRow(self.__model.rowCount())
            self.__model.setData(
                self.__model.index(self.__model.rowCount() - 1), entry)
            self.__model.sort(0)
