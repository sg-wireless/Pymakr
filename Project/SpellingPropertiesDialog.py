# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Spelling Properties dialog.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5FileDialog

from .Ui_SpellingPropertiesDialog import Ui_SpellingPropertiesDialog

import Utilities
import Preferences
import UI.PixmapCache


class SpellingPropertiesDialog(QDialog, Ui_SpellingPropertiesDialog):
    """
    Class implementing the Spelling Properties dialog.
    """
    def __init__(self, project, new, parent):
        """
        Constructor
        
        @param project reference to the project object
        @param new flag indicating the generation of a new project
        @param parent parent widget of this dialog (QWidget)
        """
        super(SpellingPropertiesDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.pwlButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.pelButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.project = project
        self.parent = parent
        
        self.pwlCompleter = E5FileCompleter(self.pwlEdit)
        self.pelCompleter = E5FileCompleter(self.pelEdit)
        
        from QScintilla.SpellChecker import SpellChecker
        self.spellingComboBox.addItem(self.tr("<default>"))
        self.spellingComboBox.addItems(
            sorted(SpellChecker.getAvailableLanguages()))
        
        if not new:
            self.initDialog()
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    def initDialog(self):
        """
        Public method to initialize the dialogs data.
        """
        index = self.spellingComboBox.findText(
            self.project.pdata["SPELLLANGUAGE"][0])
        if index == -1:
            index = 0
        self.spellingComboBox.setCurrentIndex(index)
        if self.project.pdata["SPELLWORDS"][0]:
            self.pwlEdit.setText(Utilities.toNativeSeparators(
                self.project.pdata["SPELLWORDS"][0]))
        if self.project.pdata["SPELLEXCLUDES"][0]:
            self.pelEdit.setText(Utilities.toNativeSeparators(
                self.project.pdata["SPELLEXCLUDES"][0]))
    
    @pyqtSlot()
    def on_pwlButton_clicked(self):
        """
        Private slot to select the project word list file.
        """
        pwl = Utilities.fromNativeSeparators(self.pwlEdit.text())
        if not pwl:
            pwl = self.project.ppath
        elif not os.path.isabs(pwl):
            pwl = Utilities.fromNativeSeparators(
                os.path.join(self.project.ppath, pwl))
        file = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select project word list"),
            pwl,
            self.tr("Dictionary File (*.dic);;All Files (*)"))
        
        if file:
            self.pwlEdit.setText(self.project.getRelativePath(
                Utilities.toNativeSeparators(file)))
    
    @pyqtSlot()
    def on_pelButton_clicked(self):
        """
        Private slot to select the project exclude list file.
        """
        pel = Utilities.fromNativeSeparators(self.pelEdit.text())
        if not pel:
            pel = self.project.ppath
        elif not os.path.isabs(pel):
            pel = Utilities.fromNativeSeparators(
                os.path.join(self.project.ppath, pel))
        file = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select project exclude list"),
            pel,
            self.tr("Dictionary File (*.dic);;All Files (*)"))
            
        if file:
            self.pelEdit.setText(self.project.getRelativePath(
                Utilities.toNativeSeparators(file)))
    
    def storeData(self):
        """
        Public method to store the entered/modified data.
        """
        if self.spellingComboBox.currentIndex() == 0:
            self.project.pdata["SPELLLANGUAGE"] = \
                [Preferences.getEditor("SpellCheckingDefaultLanguage")]
        else:
            self.project.pdata["SPELLLANGUAGE"] = \
                [self.spellingComboBox.currentText()]
        self.project.pdata["SPELLWORDS"] = \
            [self.project.getRelativePath(self.pwlEdit.text())]
        self.project.pdata["SPELLEXCLUDES"] = \
            [self.project.getRelativePath(self.pelEdit.text())]
