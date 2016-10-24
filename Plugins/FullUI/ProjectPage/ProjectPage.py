# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the PycomDevice configuration page.
"""

from PyQt5.QtCore import pyqtSlot
import Preferences
import Utilities
import UI.PixmapCache
from E5Gui import E5FileDialog

from Preferences.ConfigurationPages.ConfigurationPageBase import \
    ConfigurationPageBase
from .Ui_ProjectPage import Ui_ProjectPage


class ProjectPage(ConfigurationPageBase, Ui_ProjectPage):
    """
    Class implementing the PycomDevice configuration page.
    """
    def __init__(self):
        """
        Constructor
        
        @param plugin reference to the plugin object
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("ProjectPage")
        
        self.workspaceButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        # set initial values
        self.workspaceEdit.setText(
            Utilities.toNativeSeparators(
                Preferences.getMultiProject("Workspace") or
                Utilities.getHomeDir()))
  
    def save(self):
        """
        Public slot to save the Project configuration.
        """
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
