# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to manage the QtHelp filters.
"""

from __future__ import unicode_literals

import sqlite3

from PyQt5.QtCore import pyqtSlot, Qt, QItemSelectionModel
from PyQt5.QtWidgets import QDialog, QTreeWidgetItem, QListWidgetItem, \
    QInputDialog, QLineEdit
from PyQt5.QtHelp import QHelpEngineCore

from E5Gui import E5MessageBox

from .Ui_QtHelpFiltersDialog import Ui_QtHelpFiltersDialog


class QtHelpFiltersDialog(QDialog, Ui_QtHelpFiltersDialog):
    """
    Class implementing a dialog to manage the QtHelp filters.
    """
    def __init__(self, engine, parent=None):
        """
        Constructor
        
        @param engine reference to the help engine (QHelpEngine)
        @param parent reference to the parent widget (QWidget)
        """
        super(QtHelpFiltersDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.removeButton.setEnabled(False)
        self.removeAttributeButton.setEnabled(False)
        
        self.__engine = engine
        
        self.filtersList.clear()
        self.attributesList.clear()
        
        help = QHelpEngineCore(self.__engine.collectionFile())
        help.setupData()
        
        self.__removedFilters = []
        self.__filterMap = {}
        self.__filterMapBackup = {}
        self.__removedAttributes = []
        
        for filter in help.customFilters():
            atts = help.filterAttributes(filter)
            self.__filterMapBackup[filter] = atts
            if filter not in self.__filterMap:
                self.__filterMap[filter] = atts
        
        self.filtersList.addItems(sorted(self.__filterMap.keys()))
        for attr in help.filterAttributes():
            QTreeWidgetItem(self.attributesList, [attr])
        self.attributesList.sortItems(0, Qt.AscendingOrder)
        
        if self.__filterMap:
            self.filtersList.setCurrentRow(0)
    
    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def on_filtersList_currentItemChanged(self, current, previous):
        """
        Private slot to update the attributes depending on the current filter.
        
        @param current reference to the current item (QListWidgetitem)
        @param previous reference to the previous current item
            (QListWidgetItem)
        """
        checkedList = []
        if current is not None:
            checkedList = self.__filterMap[current.text()]
        for index in range(0, self.attributesList.topLevelItemCount()):
            itm = self.attributesList.topLevelItem(index)
            if itm.text(0) in checkedList:
                itm.setCheckState(0, Qt.Checked)
            else:
                itm.setCheckState(0, Qt.Unchecked)
    
    @pyqtSlot()
    def on_filtersList_itemSelectionChanged(self):
        """
        Private slot handling a change of selected filters.
        """
        self.removeButton.setEnabled(
            len(self.filtersList.selectedItems()) > 0)
    
    @pyqtSlot(QTreeWidgetItem, int)
    def on_attributesList_itemChanged(self, item, column):
        """
        Private slot to handle a change of an attribute.
        
        @param item reference to the changed item (QTreeWidgetItem)
        @param column column containing the change (integer)
        """
        if self.filtersList.currentItem() is None:
            return
        
        filter = self.filtersList.currentItem().text()
        if filter not in self.__filterMap:
            return
        
        newAtts = []
        for index in range(0, self.attributesList.topLevelItemCount()):
            itm = self.attributesList.topLevelItem(index)
            if itm.checkState(0) == Qt.Checked:
                newAtts.append(itm.text(0))
        self.__filterMap[filter] = newAtts
    
    @pyqtSlot()
    def on_attributesList_itemSelectionChanged(self):
        """
        Private slot handling the selection of attributes.
        """
        self.removeAttributeButton.setEnabled(
            len(self.attributesList.selectedItems()) != 0)
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add a new filter.
        """
        filter, ok = QInputDialog.getText(
            None,
            self.tr("Add Filter"),
            self.tr("Filter name:"),
            QLineEdit.Normal)
        if not filter:
            return
        
        if filter not in self.__filterMap:
            self.__filterMap[filter] = []
            self.filtersList.addItem(filter)
        
        itm = self.filtersList.findItems(filter, Qt.MatchCaseSensitive)[0]
        self.filtersList.setCurrentItem(itm)
    
    @pyqtSlot()
    def on_removeButton_clicked(self):
        """
        Private slot to remove the selected filters.
        """
        ok = E5MessageBox.yesNo(
            self,
            self.tr("Remove Filters"),
            self.tr(
                """Do you really want to remove the selected filters """
                """from the database?"""))
        if not ok:
            return
        
        items = self.filtersList.selectedItems()
        for item in items:
            itm = self.filtersList.takeItem(self.filtersList.row(item))
            if itm is None:
                continue
            
            del self.__filterMap[itm.text()]
            self.__removedFilters.append(itm.text())
            del itm
        
        if self.filtersList.count():
            self.filtersList.setCurrentRow(
                0, QItemSelectionModel.ClearAndSelect)
    
    @pyqtSlot()
    def on_removeAttributeButton_clicked(self):
        """
        Private slot to remove the selected filter attributes.
        """
        ok = E5MessageBox.yesNo(
            self,
            self.tr("Remove Attributes"),
            self.tr(
                """Do you really want to remove the selected attributes """
                """from the database?"""))
        if not ok:
            return
        
        items = self.attributesList.selectedItems()
        for item in items:
            itm = self.attributesList.takeTopLevelItem(
                self.attributesList.indexOfTopLevelItem(item))
            if itm is None:
                continue
            
            attr = itm.text(0)
            self.__removedAttributes.append(attr)
            for filter in self.__filterMap:
                if attr in self.__filterMap[filter]:
                    self.__filterMap[filter].remove(attr)
            
            del itm
    
    @pyqtSlot()
    def on_unusedAttributesButton_clicked(self):
        """
        Private slot to select all unused attributes.
        """
        # step 1: determine all used attributes
        attributes = set()
        for filter in self.__filterMap:
            attributes |= set(self.__filterMap[filter])
        
        # step 2: select all unused attribute items
        self.attributesList.clearSelection()
        for row in range(self.attributesList.topLevelItemCount()):
            itm = self.attributesList.topLevelItem(row)
            if itm.text(0) not in attributes:
                itm.setSelected(True)
    
    def __removeAttributes(self):
        """
        Private method to remove attributes from the Qt Help database.
        """
        try:
            self.__db = sqlite3.connect(self.__engine.collectionFile())
        except sqlite3.DatabaseError:
            pass        # ignore database errors
        
        for attr in self.__removedAttributes:
            self.__db.execute(
                "DELETE FROM FilterAttributeTable WHERE Name = '{0}'"
                .format(attr))
        self.__db.commit()
        self.__db.close()
    
    @pyqtSlot()
    def on_buttonBox_accepted(self):
        """
        Private slot to update the database, if the dialog is accepted.
        """
        filtersChanged = False
        if len(self.__filterMapBackup) != len(self.__filterMap):
            filtersChanged = True
        else:
            for filter in self.__filterMapBackup:
                if filter not in self.__filterMap:
                    filtersChanged = True
                else:
                    oldFilterAtts = self.__filterMapBackup[filter]
                    newFilterAtts = self.__filterMap[filter]
                    if len(oldFilterAtts) != len(newFilterAtts):
                        filtersChanged = True
                    else:
                        for attr in oldFilterAtts:
                            if attr not in newFilterAtts:
                                filtersChanged = True
                                break
                
                if filtersChanged:
                    break
        
        if filtersChanged:
            for filter in self.__removedFilters:
                self.__engine.removeCustomFilter(filter)
            for filter in self.__filterMap:
                self.__engine.addCustomFilter(filter, self.__filterMap[filter])
        
        if self.__removedAttributes:
            self.__removeAttributes()
        
        if filtersChanged or self.__removedAttributes:
            self.__engine.setupData()
        
        self.accept()
