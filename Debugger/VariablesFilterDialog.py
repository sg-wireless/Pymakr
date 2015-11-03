# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the variables filter dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from Debugger.Config import ConfigVarTypeDispStrings
import Preferences

from .Ui_VariablesFilterDialog import Ui_VariablesFilterDialog


class VariablesFilterDialog(QDialog, Ui_VariablesFilterDialog):
    """
    Class implementing the variables filter dialog.
    
    It opens a dialog window for the configuration of the variables type
    filter to be applied during a debugging session.
    """
    def __init__(self, parent=None, name=None, modal=False):
        """
        Constructor
        
        @param parent parent widget of this dialog (QWidget)
        @param name name of this dialog (string)
        @param modal flag to indicate a modal dialog (boolean)
        """
        super(VariablesFilterDialog, self).__init__(parent)
        if name:
            self.setObjectName(name)
        self.setModal(modal)
        self.setupUi(self)

        self.defaultButton = self.buttonBox.addButton(
            self.tr("Save Default"), QDialogButtonBox.ActionRole)
        
        lDefaultFilter, gDefaultFilter = Preferences.getVarFilters()
        
        #populate the listboxes and set the default selection
        for lb in self.localsList, self.globalsList:
            for ts in ConfigVarTypeDispStrings:
                lb.addItem(self.tr(ts))
                
        for filterIndex in lDefaultFilter:
            itm = self.localsList.item(filterIndex)
            itm.setSelected(True)
        for filterIndex in gDefaultFilter:
            itm = self.globalsList.item(filterIndex)
            itm.setSelected(True)

    def getSelection(self):
        """
        Public slot to retrieve the current selections.
        
        @return A tuple of lists of integer values. The first list is the
            locals variables filter, the second the globals variables filter.
        """
        lList = []
        gList = []
        for i in range(self.localsList.count()):
            itm = self.localsList.item(i)
            if itm.isSelected():
                lList.append(i)
        for i in range(self.globalsList.count()):
            itm = self.globalsList.item(i)
            if itm.isSelected():
                gList.append(i)
        return (lList, gList)
        
    def setSelection(self, lList, gList):
        """
        Public slot to set the current selection.
        
        @param lList local variables filter (list of int)
        @param gList global variables filter (list of int)
        """
        for filterIndex in lList:
            itm = self.localsList.item(filterIndex)
            itm.setSelected(True)
        for filterIndex in gList:
            itm = self.globalsList.item(filterIndex)
            itm.setSelected(True)

    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.defaultButton:
            Preferences.setVarFilters(self.getSelection())
