# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor Calltips configuration page.
"""

from __future__ import unicode_literals

from PyQt5.Qsci import QsciScintilla

from QScintilla.QsciScintillaCompat import QSCINTILLA_VERSION

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorCalltipsPage import Ui_EditorCalltipsPage

import Preferences


class EditorCalltipsPage(ConfigurationPageBase, Ui_EditorCalltipsPage):
    """
    Class implementing the Editor Calltips configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(EditorCalltipsPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("EditorCalltipsPage")
        
        if QSCINTILLA_VERSION() >= 0x020700:
            self.positionComboBox.addItem(
                self.tr("Below Text"),
                QsciScintilla.CallTipsBelowText)
            self.positionComboBox.addItem(
                self.tr("Above Text"),
                QsciScintilla.CallTipsAboveText)
        else:
            self.calltipsPositionBox.hide()
        
        # set initial values
        self.ctEnabledCheckBox.setChecked(
            Preferences.getEditor("CallTipsEnabled"))
        
        self.ctVisibleSlider.setValue(
            Preferences.getEditor("CallTipsVisible"))
        self.initColour("CallTipsBackground", self.calltipsBackgroundButton,
                        Preferences.getEditorColour)
        
        self.ctScintillaCheckBox.setChecked(
            Preferences.getEditor("CallTipsScintillaOnFail"))
        
        if QSCINTILLA_VERSION() >= 0x020700:
            self.positionComboBox.setCurrentIndex(
                self.positionComboBox.findData(
                    Preferences.getEditor("CallTipsPosition")))
        
    def save(self):
        """
        Public slot to save the EditorCalltips configuration.
        """
        Preferences.setEditor(
            "CallTipsEnabled",
            self.ctEnabledCheckBox.isChecked())
        
        Preferences.setEditor(
            "CallTipsVisible",
            self.ctVisibleSlider.value())
        self.saveColours(Preferences.setEditorColour)
        
        Preferences.setEditor(
            "CallTipsScintillaOnFail",
            self.ctScintillaCheckBox.isChecked())
        
        if QSCINTILLA_VERSION() >= 0x020700:
            Preferences.setEditor(
                "CallTipsPosition",
                self.positionComboBox.itemData(
                    self.positionComboBox.currentIndex()))


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = EditorCalltipsPage()
    return page
