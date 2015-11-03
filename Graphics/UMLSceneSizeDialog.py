# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to set the scene sizes.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_UMLSceneSizeDialog import Ui_UMLSceneSizeDialog


class UMLSceneSizeDialog(QDialog, Ui_UMLSceneSizeDialog):
    """
    Class implementing a dialog to set the scene sizes.
    """
    def __init__(self, w, h, minW, minH, parent=None, name=None):
        """
        Constructor
        
        @param w current width of scene (integer)
        @param h current height of scene (integer)
        @param minW minimum width allowed (integer)
        @param minH minimum height allowed (integer)
        @param parent parent widget of this dialog (QWidget)
        @param name name of this widget (string)
        """
        super(UMLSceneSizeDialog, self).__init__(parent)
        if name:
            self.setObjectName(name)
        self.setupUi(self)
        
        self.widthSpinBox.setValue(w)
        self.heightSpinBox.setValue(h)
        self.widthSpinBox.setMinimum(minW)
        self.heightSpinBox.setMinimum(minH)
        self.widthSpinBox.selectAll()
        self.widthSpinBox.setFocus()
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    def getData(self):
        """
        Public method to retrieve the entered data.
        
        @return tuple giving the selected width and height
            (integer, integer)
        """
        return (self.widthSpinBox.value(), self.heightSpinBox.value())
