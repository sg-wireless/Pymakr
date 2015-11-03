# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Application configuration page.
"""

from __future__ import unicode_literals

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_ApplicationPage import Ui_ApplicationPage

import Preferences


class ApplicationPage(ConfigurationPageBase, Ui_ApplicationPage):
    """
    Class implementing the Application configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(ApplicationPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("ApplicationPage")
        
        # set initial values
        self.singleApplicationCheckBox.setChecked(
            Preferences.getUI("SingleApplicationMode"))
        self.splashScreenCheckBox.setChecked(
            Preferences.getUI("ShowSplash"))
        
        openOnStartup = Preferences.getUI("OpenOnStartup")
        if openOnStartup == 0:
            self.noOpenRadioButton.setChecked(True)
        elif openOnStartup == 1:
            self.lastFileRadioButton.setChecked(True)
        elif openOnStartup == 2:
            self.lastProjectRadioButton.setChecked(True)
        elif openOnStartup == 3:
            self.lastMultiprojectRadioButton.setChecked(True)
        elif openOnStartup == 4:
            self.globalSessionRadioButton.setChecked(True)
        
        period = Preferences.getUI("PerformVersionCheck")
        if period == 0:
            self.noCheckRadioButton.setChecked(True)
        elif period == 1:
            self.alwaysCheckRadioButton.setChecked(True)
        elif period == 2:
            self.dailyCheckRadioButton.setChecked(True)
        elif period == 3:
            self.weeklyCheckRadioButton.setChecked(True)
        elif period == 4:
            self.monthlyCheckRadioButton.setChecked(True)
        
        self.systemEmailClientCheckBox.setChecked(
            Preferences.getUser("UseSystemEmailClient"))
        
        self.errorlogCheckBox.setChecked(
            Preferences.getUI("CheckErrorLog"))
        
    def save(self):
        """
        Public slot to save the Application configuration.
        """
        Preferences.setUI(
            "SingleApplicationMode",
            self.singleApplicationCheckBox.isChecked())
        Preferences.setUI(
            "ShowSplash",
            self.splashScreenCheckBox.isChecked())
        
        if self.noOpenRadioButton.isChecked():
            openOnStartup = 0
        elif self.lastFileRadioButton.isChecked():
            openOnStartup = 1
        elif self.lastProjectRadioButton.isChecked():
            openOnStartup = 2
        elif self.lastMultiprojectRadioButton.isChecked():
            openOnStartup = 3
        elif self.globalSessionRadioButton.isChecked():
            openOnStartup = 4
        Preferences.setUI("OpenOnStartup", openOnStartup)
        
        if self.noCheckRadioButton.isChecked():
            period = 0
        elif self.alwaysCheckRadioButton.isChecked():
            period = 1
        elif self.dailyCheckRadioButton.isChecked():
            period = 2
        elif self.weeklyCheckRadioButton.isChecked():
            period = 3
        elif self.monthlyCheckRadioButton.isChecked():
            period = 4
        Preferences.setUI("PerformVersionCheck", period)
        
        Preferences.setUser(
            "UseSystemEmailClient",
            self.systemEmailClientCheckBox.isChecked())
        
        Preferences.setUI(
            "CheckErrorLog",
            self.errorlogCheckBox.isChecked())
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = ApplicationPage()
    return page
