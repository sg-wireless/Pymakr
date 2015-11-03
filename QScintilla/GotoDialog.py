# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Goto dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_GotoDialog import Ui_GotoDialog


class GotoDialog(QDialog, Ui_GotoDialog):
    """
    Class implementing the Goto dialog.
    """
    def __init__(self, maximum, curLine, parent, name=None, modal=False):
        """
        Constructor
        
        @param maximum maximum allowed for the spinbox (integer)
        @param curLine current line number (integer)
        @param parent parent widget of this dialog (QWidget)
        @param name name of this dialog (string)
        @param modal flag indicating a modal dialog (boolean)
        """
        super(GotoDialog, self).__init__(parent)
        if name:
            self.setObjectName(name)
        self.setupUi(self)
        self.setModal(modal)
        
        self.linenumberSpinBox.setMaximum(maximum)
        self.linenumberSpinBox.setValue(curLine)
        self.linenumberSpinBox.selectAll()
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    def getLinenumber(self):
        """
        Public method to retrieve the linenumber.
        
        @return line number (int)
        """
        return self.linenumberSpinBox.value()
