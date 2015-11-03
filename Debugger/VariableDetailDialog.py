# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the variable detail dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_VariableDetailDialog import Ui_VariableDetailDialog


class VariableDetailDialog(QDialog, Ui_VariableDetailDialog):
    """
    Class implementing the variable detail dialog.
    
    This dialog shows the name, the type and the value of a variable
    in a read only dialog. It is opened upon a double click in the
    variables viewer widget.
    """
    def __init__(self, var, vtype, value):
        """
        Constructor
        
        @param var the variables name (string)
        @param vtype the variables type (string)
        @param value the variables value (string)
        """
        super(VariableDetailDialog, self).__init__()
        self.setupUi(self)
        
        # set the different fields
        self.eName.setText(var)
        self.eType.setText(vtype)
        self.eValue.setPlainText(value)
