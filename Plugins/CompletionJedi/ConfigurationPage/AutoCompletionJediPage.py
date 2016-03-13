# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Jedi Auto-completion configuration page.
"""

from E5Gui.E5Application import e5App

from Preferences.ConfigurationPages.ConfigurationPageBase import \
    ConfigurationPageBase
from .Ui_AutoCompletionJediPage import Ui_AutoCompletionJediPage


class AutoCompletionJediPage(ConfigurationPageBase, Ui_AutoCompletionJediPage):
    """
    Class implementing the Jedi Auto-completion configuration page.
    """
    def __init__(self, plugin):
        """
        Constructor
        
        @param plugin reference to the plugin object
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("AutoCompletionJediPage")
        
        self.__plugin = plugin
        
        # set initial values
        self.jediAutocompletionCheckBox.setChecked(
            self.__plugin.getPreferences("JediCompletionsEnabled"))
        self.jediCompletionsTimeoutSpinBox.setValue(
            self.__plugin.getPreferences("JediCompletionsTimeout"))
        self.qscintillaCheckBox.setChecked(
            self.__plugin.getPreferences("ShowQScintillaCompletions"))
        if e5App().getObject("UserInterface").versionIsNewer("6.0.99",
                                                             "20150530"):
            self.qscintillaCheckBox.setVisible(False)
        
    def save(self):
        """
        Public slot to save the Jedi Auto-completion configuration.
        """
        self.__plugin.setPreferences(
            "JediCompletionsEnabled",
            self.jediAutocompletionCheckBox.isChecked())
        self.__plugin.setPreferences(
            "JediCompletionsTimeout",
            self.jediCompletionsTimeoutSpinBox.value())
        self.__plugin.setPreferences(
            "ShowQScintillaCompletions", self.qscintillaCheckBox.isChecked())
