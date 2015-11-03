# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for entering a single template variable.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_TemplateSingleVariableDialog import Ui_TemplateSingleVariableDialog


class TemplateSingleVariableDialog(QDialog, Ui_TemplateSingleVariableDialog):
    """
    Class implementing a dialog for entering a single template variable.
    """
    def __init__(self, variable, parent=None):
        """
        Constructor
        
        @param variable template variable name (string)
        @param parent parent widget of this dialog (QWidget)
        """
        super(TemplateSingleVariableDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.variableLabel.setText(variable)

    def getVariable(self):
        """
        Public method to get the value for the variable.
        
        @return value for the template variable (string)
        """
        return self.variableEdit.toPlainText()
