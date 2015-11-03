# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data to rename a patch.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_HgQueuesRenamePatchDialog import Ui_HgQueuesRenamePatchDialog


class HgQueuesRenamePatchDialog(QDialog, Ui_HgQueuesRenamePatchDialog):
    """
    Class implementing a dialog to enter the data to rename a patch.
    """
    def __init__(self, currentPatch, patchesList, parent=None):
        """
        Constructor
        
        @param currentPatch name of the current patch (string)
        @param patchesList list of patches to select from (list of strings)
        @param parent reference to the parent widget (QWidget)
        """
        super(HgQueuesRenamePatchDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.currentButton.setText(
            self.tr("Current Patch ({0})").format(currentPatch))
        self.nameCombo.addItems([""] + patchesList)
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    def __updateUI(self):
        """
        Private slot to update the UI.
        """
        enable = self.nameEdit.text() != ""
        if self.namedButton.isChecked():
            enable = enable and self.nameCombo.currentText() != ""
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enable)
    
    @pyqtSlot(str)
    def on_nameEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the new name.
        
        @param txt text of the edit (string)
        """
        self.__updateUI()
    
    @pyqtSlot(bool)
    def on_namedButton_toggled(self, checked):
        """
        Private slot to handle changes of the selection method.
        
        @param checked state of the check box (boolean)
        """
        self.__updateUI()
    
    @pyqtSlot(str)
    def on_nameCombo_currentIndexChanged(self, txt):
        """
        Private slot to handle changes of the selected patch name.
        
        @param txt selected patch name (string)
        """
        self.__updateUI()
    
    def getData(self):
        """
        Public method to retrieve the entered data.
        
        @return tuple of new name and selected patch (string, string)
        """
        selectedPatch = ""
        if self.namedButton.isChecked():
            selectedPatch = self.nameCombo.currentText()
        
        return self.nameEdit.text().replace(" ", "_"), selectedPatch
