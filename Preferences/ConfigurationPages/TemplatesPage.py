# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Templates configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_TemplatesPage import Ui_TemplatesPage

import Preferences


class TemplatesPage(ConfigurationPageBase, Ui_TemplatesPage):
    """
    Class implementing the Templates configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(TemplatesPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("TemplatesPage")
        
        # set initial values
        self.templatesAutoOpenGroupsCheckBox.setChecked(
            Preferences.getTemplates("AutoOpenGroups"))
        self.templatesSeparatorCharEdit.setText(
            Preferences.getTemplates("SeparatorChar"))
        if Preferences.getTemplates("SingleDialog"):
            self.templatesSingleDialogButton.setChecked(True)
        else:
            self.templatesMultiDialogButton.setChecked(True)
        self.templatesToolTipCheckBox.setChecked(
            Preferences.getTemplates("ShowTooltip"))
        self.editorFont = Preferences.getTemplates("EditorFont")
        self.editorFontSample.setFont(self.editorFont)
        
    def save(self):
        """
        Public slot to save the Templates configuration.
        """
        Preferences.setTemplates(
            "AutoOpenGroups",
            self.templatesAutoOpenGroupsCheckBox.isChecked())
        sepChar = self.templatesSeparatorCharEdit.text()
        if sepChar:
            Preferences.setTemplates("SeparatorChar", sepChar)
        Preferences.setTemplates(
            "SingleDialog",
            self.templatesSingleDialogButton.isChecked())
        Preferences.setTemplates(
            "ShowTooltip",
            self.templatesToolTipCheckBox.isChecked())
        Preferences.setTemplates("EditorFont", self.editorFont)
    
    @pyqtSlot()
    def on_editorFontButton_clicked(self):
        """
        Private method used to select the font to be used by the code editor.
        """
        self.editorFont = self.selectFont(
            self.editorFontSample, self.editorFont)
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = TemplatesPage()
    return page
