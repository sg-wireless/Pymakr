# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the sort options for a line sort.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_SortOptionsDialog import Ui_SortOptionsDialog


class SortOptionsDialog(QDialog, Ui_SortOptionsDialog):
    """
    Class implementing a dialog to enter the sort options for a line sort.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(SortOptionsDialog, self).__init__(parent)
        self.setupUi(self)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    def getData(self):
        """
        Public method to get the selected options.
        
        @return tuple of three flags indicating ascending order, alphanumeric
            sort and case sensitivity (tuple of three boolean)
        """
        return (
            self.ascendingButton.isChecked(),
            self.alnumButton.isChecked(),
            self.respectCaseButton.isChecked()
        )
