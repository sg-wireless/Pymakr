# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the VCS configuration page.
"""

from __future__ import unicode_literals

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_VcsPage import Ui_VcsPage

import Preferences


class VcsPage(ConfigurationPageBase, Ui_VcsPage):
    """
    Class implementing the VCS configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(VcsPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("VcsPage")
        
        # set initial values
        self.vcsAutoCloseCheckBox.setChecked(Preferences.getVCS("AutoClose"))
        self.vcsAutoSaveCheckBox.setChecked(
            Preferences.getVCS("AutoSaveFiles"))
        self.vcsAutoSaveProjectCheckBox.setChecked(
            Preferences.getVCS("AutoSaveProject"))
        self.vcsStatusMonitorIntervalSpinBox.setValue(
            Preferences.getVCS("StatusMonitorInterval"))
        self.vcsMonitorLocalStatusCheckBox.setChecked(
            Preferences.getVCS("MonitorLocalStatus"))
        self.autoUpdateCheckBox.setChecked(
            Preferences.getVCS("AutoUpdate"))
        
        self.initColour(
            "VcsAdded", self.pbVcsAddedButton,
            Preferences.getProjectBrowserColour)
        self.initColour(
            "VcsConflict", self.pbVcsConflictButton,
            Preferences.getProjectBrowserColour)
        self.initColour(
            "VcsModified", self.pbVcsModifiedButton,
            Preferences.getProjectBrowserColour)
        self.initColour(
            "VcsReplaced", self.pbVcsReplacedButton,
            Preferences.getProjectBrowserColour)
        self.initColour(
            "VcsUpdate", self.pbVcsUpdateButton,
            Preferences.getProjectBrowserColour)
        self.initColour(
            "VcsRemoved", self.pbVcsRemovedButton,
            Preferences.getProjectBrowserColour)
    
    def save(self):
        """
        Public slot to save the VCS configuration.
        """
        Preferences.setVCS(
            "AutoClose",
            self.vcsAutoCloseCheckBox.isChecked())
        Preferences.setVCS(
            "AutoSaveFiles",
            self.vcsAutoSaveCheckBox.isChecked())
        Preferences.setVCS(
            "AutoSaveProject",
            self.vcsAutoSaveProjectCheckBox.isChecked())
        Preferences.setVCS(
            "StatusMonitorInterval",
            self.vcsStatusMonitorIntervalSpinBox.value())
        Preferences.setVCS(
            "MonitorLocalStatus",
            self.vcsMonitorLocalStatusCheckBox.isChecked())
        Preferences.setVCS(
            "AutoUpdate",
            self.autoUpdateCheckBox.isChecked())
    
        self.saveColours(Preferences.setProjectBrowserColour)


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = VcsPage()
    return page
