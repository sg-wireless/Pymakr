# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the synchronization host type wizard page.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QWizardPage

from . import SyncGlobals

from .Ui_SyncHostTypePage import Ui_SyncHostTypePage

import Preferences


class SyncHostTypePage(QWizardPage, Ui_SyncHostTypePage):
    """
    Class implementing the synchronization host type wizard page.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(SyncHostTypePage, self).__init__(parent)
        self.setupUi(self)
        
        if Preferences.getHelp("SyncType") == SyncGlobals.SyncTypeFtp:
            self.ftpRadioButton.setChecked(True)
        elif Preferences.getHelp("SyncType") == SyncGlobals.SyncTypeDirectory:
            self.directoryRadioButton.setChecked(True)
        else:
            self.noneRadioButton.setChecked(True)
    
    def nextId(self):
        """
        Public method returning the ID of the next wizard page.
        
        @return next wizard page ID (integer)
        """
        # save the settings
        if self.ftpRadioButton.isChecked():
            Preferences.setHelp("SyncType", SyncGlobals.SyncTypeFtp)
            return SyncGlobals.PageFTPSettings
        elif self.directoryRadioButton.isChecked():
            Preferences.setHelp("SyncType", SyncGlobals.SyncTypeDirectory)
            return SyncGlobals.PageDirectorySettings
        else:
            Preferences.setHelp("SyncType", SyncGlobals.SyncTypeNone)
            return SyncGlobals.PageCheck
