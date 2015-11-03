# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter data to fold patches.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QTreeWidgetItem

from .Ui_HgQueuesFoldDialog import Ui_HgQueuesFoldDialog

import UI.PixmapCache


class HgQueuesFoldDialog(QDialog, Ui_HgQueuesFoldDialog):
    """
    Class implementing a dialog to enter data to fold patches.
    """
    def __init__(self, patchesList, parent=None):
        """
        Constructor
        
        @param patchesList list of patches to select from (list of strings)
        @param parent reference to the parent widget (QWidget)
        """
        super(HgQueuesFoldDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.addButton.setIcon(UI.PixmapCache.getIcon("1downarrow.png"))
        self.removeButton.setIcon(UI.PixmapCache.getIcon("1uparrow.png"))
        self.upButton.setIcon(UI.PixmapCache.getIcon("1uparrow.png"))
        self.downButton.setIcon(UI.PixmapCache.getIcon("1downarrow.png"))
        
        for patch in patchesList:
            name, summary = patch.split("@@")
            QTreeWidgetItem(self.sourcePatches, [name, summary])
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
    
    def __updateOkButton(self):
        """
        Private slot to update the status of the OK button.
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            self.selectedPatches.topLevelItemCount() != 0)
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add a patch to the list of selected patches.
        """
        row = self.sourcePatches.indexOfTopLevelItem(
            self.sourcePatches.currentItem())
        itm = self.sourcePatches.takeTopLevelItem(row)
        
        curItm = self.selectedPatches.currentItem()
        if curItm is not None:
            row = self.selectedPatches.indexOfTopLevelItem(curItm) + 1
            self.selectedPatches.insertTopLevelItem(row, itm)
        else:
            self.selectedPatches.addTopLevelItem(itm)
        
        self.__updateOkButton()
    
    @pyqtSlot()
    def on_removeButton_clicked(self):
        """
        Private slot to remove a patch from the list of selected patches.
        """
        row = self.selectedPatches.indexOfTopLevelItem(
            self.selectedPatches.currentItem())
        itm = self.selectedPatches.takeTopLevelItem(row)
        self.sourcePatches.addTopLevelItem(itm)
        self.sourcePatches.sortItems(0, Qt.AscendingOrder)
        
        self.__updateOkButton()
    
    @pyqtSlot()
    def on_upButton_clicked(self):
        """
        Private slot to move a patch up in the list.
        """
        row = self.selectedPatches.indexOfTopLevelItem(
            self.selectedPatches.currentItem())
        if row > 0:
            targetRow = row - 1
            itm = self.selectedPatches.takeTopLevelItem(row)
            self.selectedPatches.insertTopLevelItem(targetRow, itm)
            self.selectedPatches.setCurrentItem(itm)
    
    @pyqtSlot()
    def on_downButton_clicked(self):
        """
        Private slot to move a patch down in the list.
        """
        row = self.selectedPatches.indexOfTopLevelItem(
            self.selectedPatches.currentItem())
        if row < self.selectedPatches.topLevelItemCount() - 1:
            targetRow = row + 1
            itm = self.selectedPatches.takeTopLevelItem(row)
            self.selectedPatches.insertTopLevelItem(targetRow, itm)
            self.selectedPatches.setCurrentItem(itm)
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_sourcePatches_currentItemChanged(self, current, previous):
        """
        Private slot to react on changes of the current item of source patches.
        
        @param current reference to the new current item (QTreeWidgetItem)
        @param previous reference to the previous current item
            (QTreeWidgetItem)
        """
        self.addButton.setEnabled(current is not None)
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_selectedPatches_currentItemChanged(self, current, previous):
        """
        Private slot to react on changes of the current item of selected
        patches.
        
        @param current reference to the new current item (QTreeWidgetItem)
        @param previous reference to the previous current item
            (QTreeWidgetItem)
        """
        self.removeButton.setEnabled(current is not None)
        
        row = self.selectedPatches.indexOfTopLevelItem(current)
        self.upButton.setEnabled(row > 0)
        self.downButton.setEnabled(
            row < self.selectedPatches.topLevelItemCount() - 1)
    
    def getData(self):
        """
        Public method to retrieve the entered data.
        
        @return tuple of commit message and list of selected patches
            (string, list of strings)
        """
        patchesList = []
        for row in range(self.selectedPatches.topLevelItemCount()):
            patchesList.append(self.selectedPatches.topLevelItem(row).text(0))
        
        return self.messageEdit.toPlainText(), patchesList
