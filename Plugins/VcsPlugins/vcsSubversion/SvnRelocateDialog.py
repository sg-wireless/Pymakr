# -*- coding: utf-8 -*-

# Copyright (c)2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data to relocate the workspace.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_SvnRelocateDialog import Ui_SvnRelocateDialog


class SvnRelocateDialog(QDialog, Ui_SvnRelocateDialog):
    """
    Class implementing a dialog to enter the data to relocate the workspace.
    """
    def __init__(self, currUrl, parent=None):
        """
        Constructor
        
        @param currUrl current repository URL (string)
        @param parent parent widget (QWidget)
        """
        super(SvnRelocateDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.currUrlLabel.setText(currUrl)
        self.newUrlEdit.setText(currUrl)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    def getData(self):
        """
        Public slot used to retrieve the data entered into the dialog.
        
        @return the new repository URL (string) and an indication, if
            the relocate is inside the repository (boolean)
        """
        return self.newUrlEdit.text(), self.insideCheckBox.isChecked()
