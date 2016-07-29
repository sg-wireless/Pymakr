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
        import serial.tools.list_ports
        """
        Constructor
        
        @param plugin reference to the plugin object
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("PycomDevicePage")
        
        self.__plugin = plugin


        # current address
        current_address = self.__plugin.getPreferences("address")

        # set initial values
        self.txt_device.addItem(current_address)
        self.txt_user.setText(
            self.__plugin.getPreferences("username"))
        self.txt_password.setText(
            self.__plugin.getPreferences("password"))

        # load the rest of the list
        for n, (portname, desc, hwid) in enumerate(sorted(serial.tools.list_ports.comports())):
            if portname != current_address:
                self.txt_device.addItem(portname)

    def save(self):
        """
        Public slot to save the PycomDevice configuration.
        """
        self.__plugin.setPreferences("address",
            self.txt_device.currentText())
        self.__plugin.setPreferences("username",
            self.txt_user.text())
        self.__plugin.setPreferences("password",
            self.txt_password.text())
        self.__plugin.preferencesChanged()
