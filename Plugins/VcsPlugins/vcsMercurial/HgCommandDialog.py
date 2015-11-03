# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Mercurial command dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_HgCommandDialog import Ui_HgCommandDialog

import Utilities


class HgCommandDialog(QDialog, Ui_HgCommandDialog):
    """
    Class implementing the Mercurial command dialog.
    
    It implements a dialog that is used to enter an
    arbitrary Mercurial command. It asks the user to enter
    the commandline parameters.
    """
    def __init__(self, argvList, ppath, parent=None):
        """
        Constructor
        
        @param argvList history list of commandline arguments (list of strings)
        @param ppath pathname of the project directory (string)
        @param parent parent widget of this dialog (QWidget)
        """
        super(HgCommandDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.setEnabled(False)
        
        self.commandCombo.clear()
        self.commandCombo.addItems(argvList)
        if len(argvList) > 0:
            self.commandCombo.setCurrentIndex(0)
        self.projectDirLabel.setText(ppath)
        
        # modify some what's this help texts
        t = self.commandCombo.whatsThis()
        if t:
            t += Utilities.getPercentReplacementHelp()
            self.commandCombo.setWhatsThis(t)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    @pyqtSlot(str)
    def on_commandCombo_editTextChanged(self, text):
        """
        Private method used to enable/disable the OK-button.
        
        @param text ignored
        """
        self.okButton.setDisabled(self.commandCombo.currentText() == "")
    
    def getData(self):
        """
        Public method to retrieve the data entered into this dialog.
        
        @return commandline parameters (string)
        """
        return self.commandCombo.currentText()
