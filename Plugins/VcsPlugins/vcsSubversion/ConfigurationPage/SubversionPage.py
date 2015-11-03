# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Subversion configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot

from Preferences.ConfigurationPages.ConfigurationPageBase import \
    ConfigurationPageBase
from .Ui_SubversionPage import Ui_SubversionPage


class SubversionPage(ConfigurationPageBase, Ui_SubversionPage):
    """
    Class implementing the Subversion configuration page.
    """
    def __init__(self, plugin):
        """
        Constructor
        
        @param plugin reference to the plugin object
        """
        super(SubversionPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("SubversionPage")
        
        self.__plugin = plugin
        
        # set initial values
        self.logSpinBox.setValue(self.__plugin.getPreferences("LogLimit"))
        self.commitSpinBox.setValue(
            self.__plugin.getPreferences("CommitMessages"))
        
    def save(self):
        """
        Public slot to save the Subversion configuration.
        """
        self.__plugin.setPreferences("LogLimit", self.logSpinBox.value())
        self.__plugin.setPreferences(
            "CommitMessages", self.commitSpinBox.value())
    
    @pyqtSlot()
    def on_configButton_clicked(self):
        """
        Private slot to edit the Subversion config file.
        """
        from QScintilla.MiniEditor import MiniEditor
        cfgFile = self.__plugin.getConfigPath()
        editor = MiniEditor(cfgFile, "Properties", self)
        editor.show()
    
    @pyqtSlot()
    def on_serversButton_clicked(self):
        """
        Private slot to edit the Subversion servers file.
        """
        from QScintilla.MiniEditor import MiniEditor
        serversFile = self.__plugin.getServersPath()
        editor = MiniEditor(serversFile, "Properties", self)
        editor.show()
