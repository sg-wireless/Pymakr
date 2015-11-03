# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for an unshelve operation.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_HgUnshelveDataDialog import Ui_HgUnshelveDataDialog


class HgUnshelveDataDialog(QDialog, Ui_HgUnshelveDataDialog):
    """
    Class implementing a dialog to enter the data for an unshelve operation.
    """
    def __init__(self, shelveNames, shelveName="", parent=None):
        """
        Constructor
        
        @param shelveNames list of available shelves (list of string)
        @param shelveName name of the shelve to restore (string)
        @param parent reference to the parent widget (QWidget)
        """
        super(HgUnshelveDataDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.nameComboBox.addItem("")
        self.nameComboBox.addItems(sorted(shelveNames))
        
        if shelveName and shelveName in shelveNames:
            self.nameComboBox.setCurrentIndex(
                self.nameComboBox.findText(shelveName))
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    def getData(self):
        """
        Public method to get the user data.
        
        @return tuple containing the name (string) and a flag indicating
            to keep the shelved change (boolean)
        """
        return (
            self.nameComboBox.currentText().replace(" ", "_"),
            self.keepCheckBox.isChecked()
        )
