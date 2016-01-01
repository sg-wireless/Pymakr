# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor General configuration page.
"""

from __future__ import unicode_literals

from PyQt5.Qsci import QsciScintillaBase

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorGeneralPage import Ui_EditorGeneralPage

import Preferences


class EditorGeneralPage(ConfigurationPageBase, Ui_EditorGeneralPage):
    """
    Class implementing the Editor General configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(EditorGeneralPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("EditorGeneralPage")
        
        # set initial values
        self.tabwidthSlider.setValue(
            Preferences.getEditor("TabWidth"))
        self.indentwidthSlider.setValue(
            Preferences.getEditor("IndentWidth"))
        self.tabforindentationCheckBox.setChecked(
            Preferences.getEditor("TabForIndentation"))
        self.tabindentsCheckBox.setChecked(
            Preferences.getEditor("TabIndents"))
        self.converttabsCheckBox.setChecked(
            Preferences.getEditor("ConvertTabsOnLoad"))
        self.autoindentCheckBox.setChecked(
            Preferences.getEditor("AutoIndentation"))
        self.comment0CheckBox.setChecked(
            Preferences.getEditor("CommentColumn0"))
        
        virtualSpaceOptions = Preferences.getEditor("VirtualSpaceOptions")
        self.vsSelectionCheckBox.setChecked(
            virtualSpaceOptions & QsciScintillaBase.SCVS_RECTANGULARSELECTION)
        self.vsUserCheckBox.setChecked(
            virtualSpaceOptions & QsciScintillaBase.SCVS_USERACCESSIBLE)
        
    def save(self):
        """
        Public slot to save the Editor General configuration.
        """
        Preferences.setEditor(
            "TabWidth",
            self.tabwidthSlider.value())
        Preferences.setEditor(
            "IndentWidth",
            self.indentwidthSlider.value())
        Preferences.setEditor(
            "TabForIndentation",
            self.tabforindentationCheckBox.isChecked())
        Preferences.setEditor(
            "TabIndents",
            self.tabindentsCheckBox.isChecked())
        Preferences.setEditor(
            "ConvertTabsOnLoad",
            self.converttabsCheckBox.isChecked())
        Preferences.setEditor(
            "AutoIndentation",
            self.autoindentCheckBox.isChecked())
        Preferences.setEditor(
            "CommentColumn0",
            self.comment0CheckBox.isChecked())
        
        virtualSpaceOptions = QsciScintillaBase.SCVS_NONE
        if self.vsSelectionCheckBox.isChecked():
            virtualSpaceOptions |= QsciScintillaBase.SCVS_RECTANGULARSELECTION
        if self.vsUserCheckBox.isChecked():
            virtualSpaceOptions |= QsciScintillaBase.SCVS_USERACCESSIBLE
        Preferences.setEditor("VirtualSpaceOptions", virtualSpaceOptions)
        
    def on_tabforindentationCheckBox_toggled(self, checked):
        """
        Private slot used to set the tab conversion check box.
        
        @param checked flag received from the signal (boolean)
        """
        if checked and self.converttabsCheckBox.isChecked():
            self.converttabsCheckBox.setChecked(not checked)
        self.converttabsCheckBox.setEnabled(not checked)
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = EditorGeneralPage()
    return page
