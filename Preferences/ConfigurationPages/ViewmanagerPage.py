# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Viewmanager configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot

from E5Gui.E5Application import e5App

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_ViewmanagerPage import Ui_ViewmanagerPage

import Preferences


class ViewmanagerPage(ConfigurationPageBase, Ui_ViewmanagerPage):
    """
    Class implementing the Viewmanager configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(ViewmanagerPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("ViewmanagerPage")
        
        # set initial values
        self.pluginManager = e5App().getObject("PluginManager")
        self.viewmanagers = \
            self.pluginManager.getPluginDisplayStrings("viewmanager")
        self.windowComboBox.clear()
        currentVm = Preferences.getViewManager()
        
        keys = sorted(self.viewmanagers.keys())
        for key in keys:
            self.windowComboBox.addItem(
                self.tr(self.viewmanagers[key]), key)
        currentIndex = self.windowComboBox.findText(
            self.tr(self.viewmanagers[currentVm]))
        self.windowComboBox.setCurrentIndex(currentIndex)
        self.on_windowComboBox_activated(currentIndex)
        
        self.tabViewGroupBox.setTitle(
            self.tr(self.viewmanagers["tabview"]))
        
        self.filenameLengthSpinBox.setValue(
            Preferences.getUI("TabViewManagerFilenameLength"))
        self.filenameOnlyCheckBox.setChecked(
            Preferences.getUI("TabViewManagerFilenameOnly"))
        self.recentFilesSpinBox.setValue(
            Preferences.getUI("RecentNumber"))
        
    def save(self):
        """
        Public slot to save the Viewmanager configuration.
        """
        vm = self.windowComboBox.itemData(
            self.windowComboBox.currentIndex())
        Preferences.setViewManager(vm)
        Preferences.setUI(
            "TabViewManagerFilenameLength",
            self.filenameLengthSpinBox.value())
        Preferences.setUI(
            "TabViewManagerFilenameOnly",
            self.filenameOnlyCheckBox.isChecked())
        Preferences.setUI(
            "RecentNumber",
            self.recentFilesSpinBox.value())
        
    @pyqtSlot(int)
    def on_windowComboBox_activated(self, index):
        """
        Private slot to show a preview of the selected workspace view type.
        
        @param index index of selected workspace view type (integer)
        """
        workspace = \
            self.windowComboBox.itemData(self.windowComboBox.currentIndex())
        pixmap = \
            self.pluginManager.getPluginPreviewPixmap("viewmanager", workspace)
        
        self.previewPixmap.setPixmap(pixmap)
        self.tabViewGroupBox.setEnabled(workspace == "tabview")
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = ViewmanagerPage()
    return page
