# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the PycomDevice configuration page.
"""

from Preferences.ConfigurationPages.ConfigurationPageBase import \
    ConfigurationPageBase
from .Ui_PycomDevicePage import Ui_PycomDevicePage
from PyQt5.QtCore import Qt


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


        # current address
        current_address = self.__plugin.getPreferences("address")
    
        self.softResetConnectState = self.__plugin.getPreferences("softResetConnect")
        self.softResetScriptsState = self.__plugin.getPreferences("softResetScripts")

        if self.softResetConnectState == None: 
            self.softResetConnectState = Qt.Unchecked
            self.softResetScriptsState = Qt.Unchecked

        # set initial values
        self.txt_device.addItem(current_address)
        self.txt_device.lineEdit().setPlaceholderText("Set the device IP address or com port")
        self.txt_user.setText(
            self.__plugin.getPreferences("username"))
        self.txt_user.setPlaceholderText("Default: micro")
        self.txt_password.setText(
            self.__plugin.getPreferences("password"))
        self.txt_password.setPlaceholderText("Default: python")

        self.label_4.setOpenExternalLinks(True)

        self.softResetConnect.setCheckState(int(self.softResetConnectState))
        self.softResetScripts.setCheckState(int(self.softResetScriptsState))

        # load the rest of the list
        self.loadSerialPortsList(current_address)

    def loadSerialPortsList(self, current_address):
        try:
            import serial.tools.list_ports
            for n, (portname, desc, hwid) in enumerate(sorted(serial.tools.list_ports.comports())):
                if portname != current_address:
                    self.txt_device.addItem(portname)            
        except:
            pass

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
        self.__plugin.setPreferences("softResetConnect",
            self.softResetConnect.checkState())
        self.__plugin.setPreferences("softResetScripts",
            self.softResetScripts.checkState())
        self.__plugin.preferencesChanged()
