# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter or change the master password.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_MasterPasswordEntryDialog import Ui_MasterPasswordEntryDialog


class MasterPasswordEntryDialog(QDialog, Ui_MasterPasswordEntryDialog):
    """
    Class implementing a dialog to enter or change the master password.
    """
    def __init__(self, oldPasswordHash, parent=None):
        """
        Constructor
        
        @param oldPasswordHash hash of the current password (string)
        @param parent reference to the parent widget (QWidget)
        """
        super(MasterPasswordEntryDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__oldPasswordHash = oldPasswordHash
        if self.__oldPasswordHash == "":
            self.currentPasswordEdit.setEnabled(False)
            if hasattr(self.currentPasswordEdit, "setPlaceholderText"):
                self.currentPasswordEdit.setPlaceholderText(
                    self.tr("(not defined yet)"))
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
    
    def __updateUI(self):
        """
        Private slot to update the variable parts of the UI.
        """
        enable = True
        error = ""
        if self.currentPasswordEdit.isEnabled():
            from Utilities.crypto.py3PBKDF2 import verifyPassword
            enable = verifyPassword(
                self.currentPasswordEdit.text(), self.__oldPasswordHash)
            if not enable:
                error = error or self.tr("Wrong password entered.")
        
        if self.newPasswordEdit.text() == "":
            enable = False
            error = error or self.tr("New password must not be empty.")
        
        if self.newPasswordEdit.text() != "" and \
           self.newPasswordEdit.text() != self.newPasswordAgainEdit.text():
            enable = False
            error = error or self.tr("Repeated password is wrong.")
        
        if self.currentPasswordEdit.isEnabled():
            if self.newPasswordEdit.text() == self.currentPasswordEdit.text():
                enable = False
                error = error or \
                    self.tr("Old and new password must not be the same.")
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enable)
        self.errorLabel.setText(error)
    
    @pyqtSlot(str)
    def on_currentPasswordEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the current password.
        
        @param txt content of the edit widget (string)
        """
        self.__updateUI()
    
    @pyqtSlot(str)
    def on_newPasswordEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the new password.
        
        @param txt content of the edit widget (string)
        """
        self.passwordMeter.checkPasswordStrength(txt)
        self.__updateUI()
    
    @pyqtSlot(str)
    def on_newPasswordAgainEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the new again password.
        
        @param txt content of the edit widget (string)
        """
        self.__updateUI()
    
    def getMasterPassword(self):
        """
        Public method to get the new master password.
        
        @return new master password (string)
        """
        return self.newPasswordEdit.text()
    
    def getCurrentPassword(self):
        """
        Public method to get the current master password.
        
        @return current master password (string)
        """
        return self.currentPasswordEdit.text()
