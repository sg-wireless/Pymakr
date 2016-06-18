# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the PycomDevice configuration page.
"""

from Preferences.ConfigurationPages.ConfigurationPageBase import \
    ConfigurationPageBase
from .Ui_PycomDevicePage import Ui_PycomDevicePage


class PycomDevicePage(ConfigurationPageBase, Ui_PycomDevicePage):
    """
    Class implementing the PycomDevice configuration page.
    """
    def __init__(self, plugin):
        """
        Constructor
        
        @param plugin reference to the plugin object
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("PycomDevicePage")
        
        self.__plugin = plugin
        
        # set initial values
        self.txt_device.setText(
            self.__plugin.getPreferences("address"))
        self.txt_user.setText(
            self.__plugin.getPreferences("username"))
        self.txt_password.setText(
            self.__plugin.getPreferences("password"))
        
    def save(self):
        """
        Public slot to save the PycomDevice configuration.
        """
        self.__plugin.setPreferences("address",
            self.txt_device.text())
        self.__plugin.setPreferences("username",
            self.txt_user.text())
        self.__plugin.setPreferences("password",
            self.txt_password.text())
        self.__plugin.preferencesChanged()
