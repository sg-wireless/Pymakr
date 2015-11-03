# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a configuration dialog for the tools menu.
"""

from __future__ import unicode_literals

import copy

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QDialog

from E5Gui import E5MessageBox

from .Ui_ToolGroupConfigurationDialog import Ui_ToolGroupConfigurationDialog


class ToolGroupConfigurationDialog(QDialog, Ui_ToolGroupConfigurationDialog):
    """
    Class implementing a configuration dialog for the tool groups.
    """
    def __init__(self, toolGroups, currentGroup, parent=None):
        """
        Constructor
        
        @param toolGroups list of configured tool groups
        @param currentGroup number of the active group (integer)
        @param parent parent widget (QWidget)
        """
        super(ToolGroupConfigurationDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.currentGroup = currentGroup
        self.toolGroups = copy.deepcopy(toolGroups)
        for group in toolGroups:
            self.groupsList.addItem(group[0])
        
        if len(toolGroups):
            self.groupsList.setCurrentRow(0)
            self.on_groupsList_currentRowChanged(0)
        
    @pyqtSlot()
    def on_newButton_clicked(self):
        """
        Private slot to clear all entry fields.
        """
        self.nameEdit.clear()
        
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add a new entry.
        """
        groupName = self.nameEdit.text()
        
        if not groupName:
            E5MessageBox.critical(
                self,
                self.tr("Add tool group entry"),
                self.tr("You have to give a name for the group to add."))
            return
        
        if len(self.groupsList.findItems(
                groupName, Qt.MatchFlags(Qt.MatchExactly))):
            E5MessageBox.critical(
                self,
                self.tr("Add tool group entry"),
                self.tr("An entry for the group name {0} already exists.")
                .format(groupName))
            return
        
        self.groupsList.addItem(groupName)
        self.toolGroups.append([groupName, []])
    
    @pyqtSlot()
    def on_changeButton_clicked(self):
        """
        Private slot to change an entry.
        """
        row = self.groupsList.currentRow()
        if row < 0:
            return
        
        groupName = self.nameEdit.text()
        
        if not groupName:
            E5MessageBox.critical(
                self,
                self.tr("Add tool group entry"),
                self.tr("You have to give a name for the group to add."))
            return
        
        if len(self.groupsList.findItems(
                groupName, Qt.MatchFlags(Qt.MatchExactly))):
            E5MessageBox.critical(
                self,
                self.tr("Add tool group entry"),
                self.tr("An entry for the group name {0} already exists.")
                .format(groupName))
            return
        
        self.toolGroups[row][0] = groupName
        self.groupsList.currentItem().setText(groupName)
        
    @pyqtSlot()
    def on_deleteButton_clicked(self):
        """
        Private slot to delete the selected entry.
        """
        row = self.groupsList.currentRow()
        if row < 0:
            return
        
        res = E5MessageBox.yesNo(
            self,
            self.tr("Delete tool group entry"),
            self.tr("""<p>Do you really want to delete the tool group"""
                    """ <b>"{0}"</b>?</p>""")
            .format(self.groupsList.currentItem().text()),
            icon=E5MessageBox.Warning)
        if not res:
            return
        
        if row == self.currentGroup:
            # set to default group if current group gets deleted
            self.currentGroup = -1
        
        del self.toolGroups[row]
        itm = self.groupsList.takeItem(row)
        del itm
        if row >= len(self.toolGroups):
            row -= 1
        self.groupsList.setCurrentRow(row)
        self.on_groupsList_currentRowChanged(row)
        
    @pyqtSlot()
    def on_downButton_clicked(self):
        """
        Private slot to move an entry down in the list.
        """
        curr = self.groupsList.currentRow()
        self.__swap(curr, curr + 1)
        self.groupsList.clear()
        for group in self.toolGroups:
            self.groupsList.addItem(group[0])
        self.groupsList.setCurrentRow(curr + 1)
        if curr + 1 == len(self.toolGroups):
            self.downButton.setEnabled(False)
        self.upButton.setEnabled(True)
        
    @pyqtSlot()
    def on_upButton_clicked(self):
        """
        Private slot to move an entry up in the list.
        """
        curr = self.groupsList.currentRow()
        self.__swap(curr - 1, curr)
        self.groupsList.clear()
        for group in self.toolGroups:
            self.groupsList.addItem(group[0])
        self.groupsList.setCurrentRow(curr - 1)
        if curr - 1 == 0:
            self.upButton.setEnabled(False)
        self.downButton.setEnabled(True)
        
    def on_groupsList_currentRowChanged(self, row):
        """
        Private slot to set the lineedits depending on the selected entry.
        
        @param row the row of the selected entry (integer)
        """
        if row >= 0 and row < len(self.toolGroups):
            group = self.toolGroups[row]
            self.nameEdit.setText(group[0])
            
            self.deleteButton.setEnabled(True)
            self.changeButton.setEnabled(True)
            
            if row != 0:
                self.upButton.setEnabled(True)
            else:
                self.upButton.setEnabled(False)
            
            if row + 1 != len(self.toolGroups):
                self.downButton.setEnabled(True)
            else:
                self.downButton.setEnabled(False)
        else:
            self.nameEdit.clear()
            self.downButton.setEnabled(False)
            self.upButton.setEnabled(False)
            self.deleteButton.setEnabled(False)
            self.changeButton.setEnabled(False)
        
    def getToolGroups(self):
        """
        Public method to retrieve the tool groups.
        
        @return a list of lists containing the group name and the
            tool group entries
        """
        return self.toolGroups[:], self.currentGroup
        
    def __swap(self, itm1, itm2):
        """
        Private method used two swap two list entries given by their index.
        
        @param itm1 index of first entry (int)
        @param itm2 index of second entry (int)
        """
        tmp = self.toolGroups[itm1]
        self.toolGroups[itm1] = self.toolGroups[itm2]
        self.toolGroups[itm2] = tmp
