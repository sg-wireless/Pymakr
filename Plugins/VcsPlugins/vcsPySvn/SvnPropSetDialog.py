# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for a new property.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_SvnPropSetDialog import Ui_SvnPropSetDialog


class SvnPropSetDialog(QDialog, Ui_SvnPropSetDialog):
    """
    Class implementing a dialog to enter the data for a new property.
    """
    def __init__(self, recursive, parent=None):
        """
        Constructor
        
        @param recursive flag indicating a recursive set is requested
        @param parent parent widget (QWidget)
        """
        super(SvnPropSetDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.recurseCheckBox.setChecked(recursive)
        
    def getData(self):
        """
        Public slot used to retrieve the data entered into the dialog.
        
        @return tuple of three values giving the property name, the text
            of the property and a flag indicating, that this property
            should be applied recursively. (string, string, boolean)
        """
        return (self.propNameEdit.text(),
                self.propTextEdit.toPlainText(),
                self.recurseCheckBox.isChecked())
