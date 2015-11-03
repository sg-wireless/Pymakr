# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the synchronization shared directory settings wizard page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWizardPage

from E5Gui import E5FileDialog

from .Ui_SyncDirectorySettingsPage import Ui_SyncDirectorySettingsPage

import Preferences
import Utilities
import UI.PixmapCache


class SyncDirectorySettingsPage(QWizardPage, Ui_SyncDirectorySettingsPage):
    """
    Class implementing the shared directory host settings wizard page.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(SyncDirectorySettingsPage, self).__init__(parent)
        self.setupUi(self)
        
        self.directoryButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.directoryEdit.setText(Preferences.getHelp("SyncDirectoryPath"))
        
        self.directoryEdit.textChanged.connect(self.completeChanged)
    
    def nextId(self):
        """
        Public method returning the ID of the next wizard page.
        
        @return next wizard page ID (integer)
        """
        # save the settings
        Preferences.setHelp(
            "SyncDirectoryPath",
            Utilities.toNativeSeparators(self.directoryEdit.text()))
        
        from . import SyncGlobals
        return SyncGlobals.PageCheck
    
    def isComplete(self):
        """
        Public method to check the completeness of the page.
        
        @return flag indicating completeness (boolean)
        """
        return self.directoryEdit.text() != ""
    
    @pyqtSlot()
    def on_directoryButton_clicked(self):
        """
        Private slot to select the shared directory via a directory selection
        dialog.
        """
        directory = E5FileDialog.getExistingDirectory(
            self,
            self.tr("Shared Directory"),
            self.directoryEdit.text(),
            E5FileDialog.Options(E5FileDialog.Option(0)))
        
        if directory:
            self.directoryEdit.setText(Utilities.toNativeSeparators(directory))
