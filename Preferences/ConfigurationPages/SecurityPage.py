# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Security configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWebKit import QWebSettings

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_SecurityPage import Ui_SecurityPage

import Preferences


class SecurityPage(ConfigurationPageBase, Ui_SecurityPage):
    """
    Class implementing the Security configuration page.
    """
    def __init__(self, configDialog):
        """
        Constructor
        
        @param configDialog reference to the configuration dialog
            (ConfigurationDialog)
        """
        super(SecurityPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("SecurityPage")
        
        self.__configDlg = configDialog
        
        # set initial values
        self.savePasswordsCheckBox.setChecked(
            Preferences.getUser("SavePasswords"))
        self.masterPasswordCheckBox.setChecked(
            Preferences.getUser("UseMasterPassword"))
        self.masterPasswordButton.setEnabled(
            Preferences.getUser("UseMasterPassword"))
        if hasattr(QWebSettings, "DnsPrefetchEnabled"):
            self.dnsPrefetchCheckBox.setChecked(
                Preferences.getHelp("DnsPrefetchEnabled"))
        else:
            self.dnsPrefetchCheckBox.setEnabled(False)
        
        self.__newPassword = ""
        self.__oldUseMasterPassword = Preferences.getUser("UseMasterPassword")
    
    def save(self):
        """
        Public slot to save the Help Viewers configuration.
        """
        Preferences.setUser(
            "SavePasswords",
            self.savePasswordsCheckBox.isChecked())
        Preferences.setUser(
            "UseMasterPassword",
            self.masterPasswordCheckBox.isChecked())
        if self.dnsPrefetchCheckBox.isEnabled():
            Preferences.setHelp(
                "DnsPrefetchEnabled",
                self.dnsPrefetchCheckBox.isChecked())
        
        if self.__oldUseMasterPassword != \
                self.masterPasswordCheckBox.isChecked():
            self.__configDlg.masterPasswordChanged.emit("", self.__newPassword)
    
    @pyqtSlot(bool)
    def on_masterPasswordCheckBox_clicked(self, checked):
        """
        Private slot to handle the use of a master password.
        
        @param checked flag indicating the state of the check box (boolean)
        """
        if checked:
            from .MasterPasswordEntryDialog import MasterPasswordEntryDialog
            dlg = MasterPasswordEntryDialog("", self)
            if dlg.exec_() == QDialog.Accepted:
                Preferences.setUser(
                    "MasterPassword",
                    dlg.getMasterPassword())
                self.masterPasswordButton.setEnabled(True)
                self.__newPassword = dlg.getMasterPassword()
            else:
                self.masterPasswordCheckBox.setChecked(False)
        else:
            self.masterPasswordButton.setEnabled(False)
            self.__newPassword = ""
    
    @pyqtSlot()
    def on_masterPasswordButton_clicked(self):
        """
        Private slot to change the master password.
        """
        from .MasterPasswordEntryDialog import MasterPasswordEntryDialog
        dlg = MasterPasswordEntryDialog(
            Preferences.getUser("MasterPassword"), self)
        if dlg.exec_() == QDialog.Accepted:
            Preferences.setUser(
                "MasterPassword",
                dlg.getMasterPassword())
            
            if self.__oldUseMasterPassword != \
                    self.masterPasswordCheckBox.isChecked():
                # the user is about to change the use of a master password
                # just save the changed password
                self.__newPassword = dlg.getMasterPassword()
            else:
                self.__configDlg.masterPasswordChanged.emit(
                    dlg.getCurrentPassword(), dlg.getMasterPassword())


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = SecurityPage(dlg)
    return page
