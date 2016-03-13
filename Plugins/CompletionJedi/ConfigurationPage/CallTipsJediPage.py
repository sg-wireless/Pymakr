# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Jedi Calltips configuration page.
"""

from Preferences.ConfigurationPages.ConfigurationPageBase import \
    ConfigurationPageBase
from .Ui_CallTipsJediPage import Ui_CallTipsJediPage


class CallTipsJediPage(ConfigurationPageBase, Ui_CallTipsJediPage):
    """
    Class implementing the Jedi Calltips configuration page.
    """
    def __init__(self, plugin):
        """
        Constructor
        
        @param plugin reference to the plugin object
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("CallTipsJediPage")
        
        self.__plugin = plugin
        
        # set initial values
        self.jediCalltipsCheckBox.setChecked(
            self.__plugin.getPreferences("JediCalltipsEnabled"))
        
    def save(self):
        """
        Public slot to save the Jedi Calltips configuration.
        """
        self.__plugin.setPreferences(
            "JediCalltipsEnabled", self.jediCalltipsCheckBox.isChecked())
