# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor Spellchecking configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5FileDialog

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorSpellCheckingPage import Ui_EditorSpellCheckingPage

import Preferences
import Utilities
import UI.PixmapCache


class EditorSpellCheckingPage(ConfigurationPageBase,
                              Ui_EditorSpellCheckingPage):
    """
    Class implementing the Editor Spellchecking configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(EditorSpellCheckingPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("EditorSpellCheckingPage")
        
        self.pwlButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.pelButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        from QScintilla.SpellChecker import SpellChecker
        languages = sorted(SpellChecker.getAvailableLanguages())
        self.defaultLanguageCombo.addItems(languages)
        if languages:
            self.errorLabel.hide()
        else:
            self.spellingFrame.setEnabled(False)
        
        self.pwlFileCompleter = E5FileCompleter(self.pwlEdit, showHidden=True)
        self.pelFileCompleter = E5FileCompleter(self.pelEdit, showHidden=True)
        
        # set initial values
        self.checkingEnabledCheckBox.setChecked(
            Preferences.getEditor("SpellCheckingEnabled"))
        
        self.defaultLanguageCombo.setCurrentIndex(
            self.defaultLanguageCombo.findText(
                Preferences.getEditor("SpellCheckingDefaultLanguage")))
        
        self.stringsOnlyCheckBox.setChecked(
            Preferences.getEditor("SpellCheckStringsOnly"))
        self.minimumWordSizeSlider.setValue(
            Preferences.getEditor("SpellCheckingMinWordSize"))
        
        self.initColour(
            "SpellingMarkers", self.spellingMarkerButton,
            Preferences.getEditorColour, hasAlpha=True)
        
        self.pwlEdit.setText(
            Preferences.getEditor("SpellCheckingPersonalWordList"))
        self.pelEdit.setText(
            Preferences.getEditor("SpellCheckingPersonalExcludeList"))
        
        if self.spellingFrame.isEnabled():
            self.enabledCheckBox.setChecked(
                Preferences.getEditor("AutoSpellCheckingEnabled"))
        else:
            self.enabledCheckBox.setChecked(False)  # not available
        self.chunkSizeSpinBox.setValue(
            Preferences.getEditor("AutoSpellCheckChunkSize"))
        
    def save(self):
        """
        Public slot to save the Editor Search configuration.
        """
        Preferences.setEditor(
            "SpellCheckingEnabled", self.checkingEnabledCheckBox.isChecked())
        
        Preferences.setEditor(
            "SpellCheckingDefaultLanguage",
            self.defaultLanguageCombo.currentText())
        
        Preferences.setEditor(
            "SpellCheckStringsOnly", self.stringsOnlyCheckBox.isChecked())
        Preferences.setEditor(
            "SpellCheckingMinWordSize", self.minimumWordSizeSlider.value())
        
        self.saveColours(Preferences.setEditorColour)
        
        Preferences.setEditor(
            "SpellCheckingPersonalWordList", self.pwlEdit.text())
        Preferences.setEditor(
            "SpellCheckingPersonalExcludeList", self.pelEdit.text())
        
        Preferences.setEditor(
            "AutoSpellCheckingEnabled", self.enabledCheckBox.isChecked())
        Preferences.setEditor(
            "AutoSpellCheckChunkSize", self.chunkSizeSpinBox.value())
    
    @pyqtSlot()
    def on_pwlButton_clicked(self):
        """
        Private method to select the personal word list file.
        """
        file = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select personal word list"),
            self.pwlEdit.text(),
            self.tr("Dictionary File (*.dic);;All Files (*)"))
            
        if file:
            self.pwlEdit.setText(Utilities.toNativeSeparators(file))
    
    @pyqtSlot()
    def on_pelButton_clicked(self):
        """
        Private method to select the personal exclude list file.
        """
        file = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select personal exclude list"),
            self.pelEdit.text(),
            self.tr("Dictionary File (*.dic);;All Files (*)"))
            
        if file:
            self.pelEdit.setText(Utilities.toNativeSeparators(file))


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = EditorSpellCheckingPage()
    return page
