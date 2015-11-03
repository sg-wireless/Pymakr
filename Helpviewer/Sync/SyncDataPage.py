# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the synchronization data wizard page.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QWizardPage

from .Ui_SyncDataPage import Ui_SyncDataPage

import Preferences


class SyncDataPage(QWizardPage, Ui_SyncDataPage):
    """
    Class implementing the synchronization data wizard page.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(SyncDataPage, self).__init__(parent)
        self.setupUi(self)
        
        self.bookmarksCheckBox.setChecked(Preferences.getHelp("SyncBookmarks"))
        self.historyCheckBox.setChecked(Preferences.getHelp("SyncHistory"))
        self.passwordsCheckBox.setChecked(Preferences.getHelp("SyncPasswords"))
        self.userAgentsCheckBox.setChecked(
            Preferences.getHelp("SyncUserAgents"))
        self.speedDialCheckBox.setChecked(Preferences.getHelp("SyncSpeedDial"))
        
        self.activeCheckBox.setChecked(Preferences.getHelp("SyncEnabled"))
    
    def nextId(self):
        """
        Public method returning the ID of the next wizard page.
        
        @return next wizard page ID (integer)
        """
        # save the settings
        Preferences.setHelp("SyncEnabled", self.activeCheckBox.isChecked())
        
        Preferences.setHelp(
            "SyncBookmarks", self.bookmarksCheckBox.isChecked())
        Preferences.setHelp(
            "SyncHistory", self.historyCheckBox.isChecked())
        Preferences.setHelp(
            "SyncPasswords", self.passwordsCheckBox.isChecked())
        Preferences.setHelp(
            "SyncUserAgents", self.userAgentsCheckBox.isChecked())
        Preferences.setHelp(
            "SyncSpeedDial", self.speedDialCheckBox.isChecked())
        
        from . import SyncGlobals
        if self.activeCheckBox.isChecked():
            return SyncGlobals.PageEncryption
        else:
            return SyncGlobals.PageCheck
