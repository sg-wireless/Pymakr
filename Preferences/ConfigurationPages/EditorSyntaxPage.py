# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor Syntax Checker configuration page.
"""

from __future__ import unicode_literals

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorSyntaxPage import Ui_EditorSyntaxPage

import Preferences


class EditorSyntaxPage(ConfigurationPageBase, Ui_EditorSyntaxPage):
    """
    Class implementing the Editor Syntax Checker configuration page.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(EditorSyntaxPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("EditorSyntaxPage")
        
        # set initial values
        self.onlineCheckBox.setChecked(
            Preferences.getEditor("OnlineSyntaxCheck"))
        self.onlineTimeoutSpinBox.setValue(
            Preferences.getEditor("OnlineSyntaxCheckInterval"))
        self.automaticSyntaxCheckCheckBox.setChecked(
            Preferences.getEditor("AutoCheckSyntax"))
        
        # pyflakes related stuff
        self.includeCheckBox.setChecked(
            Preferences.getFlakes("IncludeInSyntaxCheck"))
        self.ignoreStarImportCheckBox.setChecked(
            Preferences.getFlakes("IgnoreStarImportWarnings"))
    
    def save(self):
        """
        Public slot to save the Editor Syntax Checker configuration.
        """
        Preferences.setEditor(
            "OnlineSyntaxCheck",
            self.onlineCheckBox.isChecked())
        Preferences.setEditor(
            "OnlineSyntaxCheckInterval",
            self.onlineTimeoutSpinBox.value())
        Preferences.setEditor(
            "AutoCheckSyntax",
            self.automaticSyntaxCheckCheckBox.isChecked())
        
        # pyflakes related stuff
        Preferences.setFlakes(
            "IncludeInSyntaxCheck",
            self.includeCheckBox.isChecked())
        Preferences.setFlakes(
            "IgnoreStarImportWarnings",
            self.ignoreStarImportCheckBox.isChecked())


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = EditorSyntaxPage()
    return page
