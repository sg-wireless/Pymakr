# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Multi Project configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_MultiProjectPage import Ui_MultiProjectPage

from E5Gui import E5FileDialog

import Preferences
import Utilities
import UI.PixmapCache


class MultiProjectPage(ConfigurationPageBase, Ui_MultiProjectPage):
    """
    Class implementing the Multi Project configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(MultiProjectPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("MultiProjectPage")
        
        self.workspaceButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        # set initial values
        self.openMasterAutomaticallyCheckBox.setChecked(
            Preferences.getMultiProject("OpenMasterAutomatically"))
        self.multiProjectTimestampCheckBox.setChecked(
            Preferences.getMultiProject("XMLTimestamp"))
        self.multiProjectRecentSpinBox.setValue(
            Preferences.getMultiProject("RecentNumber"))
        self.workspaceEdit.setText(
            Utilities.toNativeSeparators(
                Preferences.getMultiProject("Workspace") or
                Utilities.getHomeDir()))
        
    def save(self):
        """
        Public slot to save the Project configuration.
        """
        Preferences.setMultiProject(
            "OpenMasterAutomatically",
            self.openMasterAutomaticallyCheckBox.isChecked())
        Preferences.setMultiProject(
            "XMLTimestamp",
            self.multiProjectTimestampCheckBox.isChecked())
        Preferences.setMultiProject(
            "RecentNumber",
            self.multiProjectRecentSpinBox.value())
        Preferences.setMultiProject(
            "Workspace",
            self.workspaceEdit.text())
    
    @pyqtSlot()
    def on_workspaceButton_clicked(self):
        """
        Private slot to display a directory selection dialog.
        """
        default = self.workspaceEdit.text()
        if default == "":
            default = Utilities.getHomeDir()
        directory = E5FileDialog.getExistingDirectory(
            self,
            self.tr("Select Workspace Directory"),
            default,
            E5FileDialog.Options(0))
        
        if directory:
            self.workspaceEdit.setText(Utilities.toNativeSeparators(directory))
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = MultiProjectPage()
    return page
