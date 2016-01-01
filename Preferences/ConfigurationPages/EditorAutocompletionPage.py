# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor Autocompletion configuration page.
"""

from __future__ import unicode_literals

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorAutocompletionPage import Ui_EditorAutocompletionPage

import Preferences


class EditorAutocompletionPage(ConfigurationPageBase,
                               Ui_EditorAutocompletionPage):
    """
    Class implementing the Editor Autocompletion configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(EditorAutocompletionPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("EditorAutocompletionPage")
        
        # set initial values
        self.acEnabledCheckBox.setChecked(
            Preferences.getEditor("AutoCompletionEnabled"))
        self.acCaseSensitivityCheckBox.setChecked(
            Preferences.getEditor("AutoCompletionCaseSensitivity"))
        self.acReplaceWordCheckBox.setChecked(
            Preferences.getEditor("AutoCompletionReplaceWord"))
        self.acThresholdSlider.setValue(
            Preferences.getEditor("AutoCompletionThreshold"))
        self.acScintillaCheckBox.setChecked(
            Preferences.getEditor("AutoCompletionScintillaOnFail"))
        
    def save(self):
        """
        Public slot to save the Editor Autocompletion configuration.
        """
        Preferences.setEditor(
            "AutoCompletionEnabled",
            self.acEnabledCheckBox.isChecked())
        Preferences.setEditor(
            "AutoCompletionCaseSensitivity",
            self.acCaseSensitivityCheckBox.isChecked())
        Preferences.setEditor(
            "AutoCompletionReplaceWord",
            self.acReplaceWordCheckBox.isChecked())
        Preferences.setEditor(
            "AutoCompletionThreshold",
            self.acThresholdSlider.value())
        Preferences.setEditor(
            "AutoCompletionScintillaOnFail",
            self.acScintillaCheckBox.isChecked())
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = EditorAutocompletionPage()
    return page
