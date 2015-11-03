# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing encryption settings wizard page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWizardPage

from .Ui_SyncEncryptionPage import Ui_SyncEncryptionPage

import Preferences


class SyncEncryptionPage(QWizardPage, Ui_SyncEncryptionPage):
    """
    Class implementing encryption settings wizard page.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(SyncEncryptionPage, self).__init__(parent)
        self.setupUi(self)
        
        self.keySizeComboBox.addItem(self.tr("128 Bits"), 16)
        self.keySizeComboBox.addItem(self.tr("192 Bits"), 24)
        self.keySizeComboBox.addItem(self.tr("256 Bits"), 32)
        
        self.registerField("ReencryptData", self.reencryptCheckBox)
        
        self.encryptionGroupBox.setChecked(
            Preferences.getHelp("SyncEncryptData"))
        self.encryptionKeyEdit.setText(
            Preferences.getHelp("SyncEncryptionKey"))
        self.encryptionKeyAgainEdit.setEnabled(False)
        self.keySizeComboBox.setCurrentIndex(self.keySizeComboBox.findData(
            Preferences.getHelp("SyncEncryptionKeyLength")))
        self.loginsOnlyCheckBox.setChecked(
            Preferences.getHelp("SyncEncryptPasswordsOnly"))
    
    def nextId(self):
        """
        Public method returning the ID of the next wizard page.
        
        @return next wizard page ID (integer)
        """
        Preferences.setHelp(
            "SyncEncryptData", self.encryptionGroupBox.isChecked())
        Preferences.setHelp(
            "SyncEncryptionKey", self.encryptionKeyEdit.text())
        Preferences.setHelp(
            "SyncEncryptionKeyLength", self.keySizeComboBox.itemData(
                self.keySizeComboBox.currentIndex()))
        Preferences.setHelp(
            "SyncEncryptPasswordsOnly", self.loginsOnlyCheckBox.isChecked())
        
        from . import SyncGlobals
        return SyncGlobals.PageType
    
    def isComplete(self):
        """
        Public method to check the completeness of the page.
        
        @return flag indicating completeness (boolean)
        """
        if self.encryptionGroupBox.isChecked():
            if self.encryptionKeyEdit.text() == "":
                complete = False
            else:
                if self.reencryptCheckBox.isChecked():
                    complete = (self.encryptionKeyEdit.text() ==
                                self.encryptionKeyAgainEdit.text())
                else:
                    complete = True
        else:
            complete = True
        
        return complete
    
    def __updateUI(self):
        """
        Private slot to update the variable parts of the UI.
        """
        error = ""
        
        if self.encryptionGroupBox.isChecked():
            self.encryptionKeyAgainEdit.setEnabled(
                self.reencryptCheckBox.isChecked())
            
            if self.encryptionKeyEdit.text() == "":
                error = error or self.tr(
                    "Encryption key must not be empty.")
            
            if self.encryptionKeyEdit.text() != "" and \
                    self.reencryptCheckBox.isChecked() and \
                    (self.encryptionKeyEdit.text() !=
                     self.encryptionKeyAgainEdit.text()):
                error = error or self.tr(
                    "Repeated encryption key is wrong.")
        
        self.errorLabel.setText(error)
        self.completeChanged.emit()
    
    @pyqtSlot(str)
    def on_encryptionKeyEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the encryption key.
        
        @param txt content of the edit widget (string)
        """
        self.passwordMeter.checkPasswordStrength(txt)
        self.__updateUI()
    
    @pyqtSlot(str)
    def on_encryptionKeyAgainEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the encryption key repetition.
        
        @param txt content of the edit widget (string)
        """
        self.__updateUI()
    
    @pyqtSlot(bool)
    def on_encryptionGroupBox_toggled(self, on):
        """
        Private slot to handle changes of the encryption selection.
        
        @param on state of the group box (boolean)
        """
        self.__updateUI()
    
    @pyqtSlot(bool)
    def on_reencryptCheckBox_toggled(self, on):
        """
        Private slot to handle changes of the re-encryption selection.
        
        @param on state of the check box (boolean)
        """
        self.__updateUI()
