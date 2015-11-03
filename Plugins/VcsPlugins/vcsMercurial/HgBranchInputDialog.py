# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for a branch operation.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_HgBranchInputDialog import Ui_HgBranchInputDialog


class HgBranchInputDialog(QDialog, Ui_HgBranchInputDialog):
    """
    Class implementing a dialog to enter the data for a branch operation.
    """
    def __init__(self, branches, parent=None):
        """
        Constructor
        
        @param branches branch names to populate the branch list with
            (list of string)
        @param parent reference to the parent widget (QWidget)
        """
        super(HgBranchInputDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.branchComboBox.addItems(sorted(branches))
        self.branchComboBox.setEditText("")
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    @pyqtSlot(str)
    def on_branchComboBox_editTextChanged(self, txt):
        """
        Private slot handling a change of the branch name.
        
        @param txt contents of the branch combo box (string)
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(bool(txt))
    
    def getData(self):
        """
        Public method to get the data.
        
        @return tuple of branch name (string) and a flag indicating to
            commit the branch (boolean)
        """
        return (self.branchComboBox.currentText().replace(" ", "_"),
                self.commitCheckBox.isChecked())
