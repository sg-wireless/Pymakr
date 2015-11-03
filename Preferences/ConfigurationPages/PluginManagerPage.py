# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Plugin Manager configuration page.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot

from E5Gui.E5Completers import E5DirCompleter
from E5Gui import E5FileDialog

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_PluginManagerPage import Ui_PluginManagerPage

import Preferences
import Utilities
import UI.PixmapCache


class PluginManagerPage(ConfigurationPageBase, Ui_PluginManagerPage):
    """
    Class implementing the Plugin Manager configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(PluginManagerPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("PluginManagerPage")
        
        self.downloadDirButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.downloadDirCompleter = E5DirCompleter(self.downloadDirEdit)
        
        # set initial values
        self.activateExternalPluginsCheckBox.setChecked(
            Preferences.getPluginManager("ActivateExternal"))
        self.downloadDirEdit.setText(
            Preferences.getPluginManager("DownloadPath"))
        self.generationsSpinBox.setValue(
            Preferences.getPluginManager("KeepGenerations"))
        self.keepHiddenCheckBox.setChecked(
            Preferences.getPluginManager("KeepHidden"))
        
        period = Preferences.getPluginManager("UpdatesCheckInterval")
        if period == 0:
            self.noCheckRadioButton.setChecked(True)
        elif period == 1:
            self.dailyCheckRadioButton.setChecked(True)
        elif period == 2:
            self.weeklyCheckRadioButton.setChecked(True)
        elif period == 3:
            self.monthlyCheckRadioButton.setChecked(True)
        
        self.downloadedOnlyCheckBox.setChecked(
            Preferences.getPluginManager("CheckInstalledOnly"))
        
        self.__repositoryUrl = Preferences.getUI("PluginRepositoryUrl6")
        self.repositoryUrlEdit.setText(self.__repositoryUrl)
    
    def save(self):
        """
        Public slot to save the Viewmanager configuration.
        """
        Preferences.setPluginManager(
            "ActivateExternal",
            self.activateExternalPluginsCheckBox.isChecked())
        Preferences.setPluginManager(
            "DownloadPath",
            self.downloadDirEdit.text())
        Preferences.setPluginManager(
            "KeepGenerations",
            self.generationsSpinBox.value())
        Preferences.setPluginManager(
            "KeepHidden",
            self.keepHiddenCheckBox.isChecked())
        
        if self.noCheckRadioButton.isChecked():
            period = 0
        elif self.dailyCheckRadioButton.isChecked():
            period = 1
        elif self.weeklyCheckRadioButton.isChecked():
            period = 2
        elif self.monthlyCheckRadioButton.isChecked():
            period = 3
        Preferences.setPluginManager("UpdatesCheckInterval", period)
        
        Preferences.setPluginManager(
            "CheckInstalledOnly",
            self.downloadedOnlyCheckBox.isChecked())
        
        if self.repositoryUrlEdit.text() != self.__repositoryUrl:
            Preferences.setUI(
                "PluginRepositoryUrl6", self.repositoryUrlEdit.text())
    
    @pyqtSlot()
    def on_downloadDirButton_clicked(self):
        """
        Private slot to handle the directory selection via dialog.
        """
        directory = E5FileDialog.getExistingDirectory(
            self,
            self.tr("Select plugins download directory"),
            self.downloadDirEdit.text(),
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
            
        if directory:
            dn = Utilities.toNativeSeparators(directory)
            while dn.endswith(os.sep):
                dn = dn[:-1]
            self.downloadDirEdit.setText(dn)
    
    @pyqtSlot(bool)
    def on_repositoryUrlEditButton_toggled(self, checked):
        """
        Private slot to set the read only status of the repository URL line
        edit.
        
        @param checked state of the push button (boolean)
        """
        self.repositoryUrlEdit.setReadOnly(not checked)
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = PluginManagerPage()
    return page
