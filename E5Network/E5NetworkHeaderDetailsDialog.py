# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the data of a response or reply header.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

from .Ui_E5NetworkHeaderDetailsDialog import Ui_E5NetworkHeaderDetailsDialog


class E5NetworkHeaderDetailsDialog(QDialog, Ui_E5NetworkHeaderDetailsDialog):
    """
    Class implementing a dialog to show the data of a response or reply header.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QWidget)
        """
        super(E5NetworkHeaderDetailsDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
    
    def setData(self, name, value):
        """
        Public method to set the data to display.
        
        @param name name of the header (string)
        @param value value of the header (string)
        """
        self.nameEdit.setText(name)
        self.valueEdit.setPlainText(value)
