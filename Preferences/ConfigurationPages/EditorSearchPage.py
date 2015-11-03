# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor Search configuration page.
"""

from __future__ import unicode_literals

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorSearchPage import Ui_EditorSearchPage

import Preferences


class EditorSearchPage(ConfigurationPageBase, Ui_EditorSearchPage):
    """
    Class implementing the Editor Search configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(EditorSearchPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("EditorSearchPage")
        
        self.editorColours = {}
        
        # set initial values
        self.searchMarkersEnabledCheckBox.setChecked(
            Preferences.getEditor("SearchMarkersEnabled"))
        self.quicksearchMarkersEnabledCheckBox.setChecked(
            Preferences.getEditor("QuickSearchMarkersEnabled"))
        self.occurrencesMarkersEnabledCheckBox.setChecked(
            Preferences.getEditor("MarkOccurrencesEnabled"))
        
        self.markOccurrencesTimeoutSpinBox.setValue(
            Preferences.getEditor("MarkOccurrencesTimeout"))
        
        self.initColour(
            "SearchMarkers", self.searchMarkerButton,
            Preferences.getEditorColour, hasAlpha=True)
        
    def save(self):
        """
        Public slot to save the Editor Search configuration.
        """
        Preferences.setEditor(
            "SearchMarkersEnabled",
            self.searchMarkersEnabledCheckBox.isChecked())
        Preferences.setEditor(
            "QuickSearchMarkersEnabled",
            self.quicksearchMarkersEnabledCheckBox.isChecked())
        Preferences.setEditor(
            "MarkOccurrencesEnabled",
            self.occurrencesMarkersEnabledCheckBox.isChecked())
        
        Preferences.setEditor(
            "MarkOccurrencesTimeout",
            self.markOccurrencesTimeoutSpinBox.value())
        
        self.saveColours(Preferences.setEditorColour)


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = EditorSearchPage()
    return page
