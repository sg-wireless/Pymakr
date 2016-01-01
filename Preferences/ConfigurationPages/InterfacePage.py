# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Interface configuration page.
"""

from __future__ import unicode_literals

import glob
import os

from PyQt5.QtCore import pyqtSlot, QTranslator
from PyQt5.QtWidgets import QStyleFactory

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5FileDialog

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_InterfacePage import Ui_InterfacePage

import Preferences
import Utilities
import UI.PixmapCache

from eric6config import getConfig


class InterfacePage(ConfigurationPageBase, Ui_InterfacePage):
    """
    Class implementing the Interface configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(InterfacePage, self).__init__()
        self.setupUi(self)
        self.setObjectName("InterfacePage")
        
        self.styleSheetButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.styleSheetCompleter = E5FileCompleter(self.styleSheetEdit)
        
        # set initial values
        self.__populateStyleCombo()
        self.__populateLanguageCombo()
        
        self.uiBrowsersListFoldersFirstCheckBox.setChecked(
            Preferences.getUI("BrowsersListFoldersFirst"))
        self.uiBrowsersHideNonPublicCheckBox.setChecked(
            Preferences.getUI("BrowsersHideNonPublic"))
        self.uiBrowsersSortByOccurrenceCheckBox.setChecked(
            Preferences.getUI("BrowsersListContentsByOccurrence"))
        self.uiBrowsersShowHiddenCheckBox.setChecked(
            Preferences.getUI("BrowsersListHiddenFiles"))
        self.fileFiltersEdit.setText(
            Preferences.getUI("BrowsersFileFilters"))
        
        self.uiCaptionShowsFilenameGroupBox.setChecked(
            Preferences.getUI("CaptionShowsFilename"))
        self.filenameLengthSpinBox.setValue(
            Preferences.getUI("CaptionFilenameLength"))
        self.styleSheetEdit.setText(Preferences.getUI("StyleSheet"))
        
        if Preferences.getUI("TopLeftByLeft"):
            self.tlLeftButton.setChecked(True)
        else:
            self.tlTopButton.setChecked(True)
        if Preferences.getUI("BottomLeftByLeft"):
            self.blLeftButton.setChecked(True)
        else:
            self.blBottomButton.setChecked(True)
        if Preferences.getUI("TopRightByRight"):
            self.trRightButton.setChecked(True)
        else:
            self.trTopButton.setChecked(True)
        if Preferences.getUI("BottomRightByRight"):
            self.brRightButton.setChecked(True)
        else:
            self.brTopButton.setChecked(True)
        
        layout = Preferences.getUILayout()
        if layout[0] == "Sidebars":
            index = 0
        elif layout[0] == "Toolboxes":
            index = 1
        else:
            index = 0   # default for bad values
        self.layoutComboBox.setCurrentIndex(index)
        if layout[1] == 0:
            self.separateShellButton.setChecked(True)
        else:
            self.debugEmbeddedShellButton.setChecked(True)
        if layout[2] == 0:
            self.separateFileBrowserButton.setChecked(True)
        elif layout[2] == 1:
            self.debugEmbeddedFileBrowserButton.setChecked(True)
        else:
            self.projectEmbeddedFileBrowserButton.setChecked(True)
        
        self.tabsGroupBox.setEnabled(True)
        self.tabsCloseButtonCheckBox.setChecked(
            Preferences.getUI("SingleCloseButton"))
        
        self.delaySpinBox.setValue(Preferences.getUI("SidebarDelay"))
        
    def save(self):
        """
        Public slot to save the Interface configuration.
        """
        # save the style settings
        styleIndex = self.styleComboBox.currentIndex()
        style = self.styleComboBox.itemData(styleIndex)
        Preferences.setUI("Style", style)
        
        # save the other UI related settings
        Preferences.setUI(
            "BrowsersListFoldersFirst",
            self.uiBrowsersListFoldersFirstCheckBox.isChecked())
        Preferences.setUI(
            "BrowsersHideNonPublic",
            self.uiBrowsersHideNonPublicCheckBox.isChecked())
        Preferences.setUI(
            "BrowsersListContentsByOccurrence",
            self.uiBrowsersSortByOccurrenceCheckBox.isChecked())
        Preferences.setUI(
            "BrowsersListHiddenFiles",
            self.uiBrowsersShowHiddenCheckBox.isChecked())
        Preferences.setUI(
            "BrowsersFileFilters",
            self.fileFiltersEdit.text())
        
        Preferences.setUI(
            "CaptionShowsFilename",
            self.uiCaptionShowsFilenameGroupBox.isChecked())
        Preferences.setUI(
            "CaptionFilenameLength",
            self.filenameLengthSpinBox.value())
        Preferences.setUI(
            "StyleSheet",
            self.styleSheetEdit.text())
        
        # save the dockarea corner settings
        Preferences.setUI(
            "TopLeftByLeft",
            self.tlLeftButton.isChecked())
        Preferences.setUI(
            "BottomLeftByLeft",
            self.blLeftButton.isChecked())
        Preferences.setUI(
            "TopRightByRight",
            self.trRightButton.isChecked())
        Preferences.setUI(
            "BottomRightByRight",
            self.brRightButton.isChecked())
        
        # save the language settings
        uiLanguageIndex = self.languageComboBox.currentIndex()
        if uiLanguageIndex:
            uiLanguage = \
                self.languageComboBox.itemData(uiLanguageIndex)
        else:
            uiLanguage = None
        Preferences.setUILanguage(uiLanguage)
        
        # save the interface layout settings
        if self.separateShellButton.isChecked():
            layout2 = 0
        else:
            layout2 = 1
        if self.separateFileBrowserButton.isChecked():
            layout3 = 0
        elif self.debugEmbeddedFileBrowserButton.isChecked():
            layout3 = 1
        else:
            layout3 = 2
        if self.layoutComboBox.currentIndex() == 0:
            layout1 = "Sidebars"
        elif self.layoutComboBox.currentIndex() == 1:
            layout1 = "Toolboxes"
        else:
            layout1 = "Sidebars"    # just in case
        layout = (layout1, layout2, layout3)
        Preferences.setUILayout(layout)
        
        Preferences.setUI(
            "SingleCloseButton",
            self.tabsCloseButtonCheckBox.isChecked())
        
        Preferences.setUI("SidebarDelay", self.delaySpinBox.value())
        
    def __populateStyleCombo(self):
        """
        Private method to populate the style combo box.
        """
        curStyle = Preferences.getUI("Style")
        styles = sorted(list(QStyleFactory.keys()))
        self.styleComboBox.addItem(self.tr('System'), "System")
        for style in styles:
            self.styleComboBox.addItem(style, style)
        currentIndex = self.styleComboBox.findData(curStyle)
        if currentIndex == -1:
            currentIndex = 0
        self.styleComboBox.setCurrentIndex(currentIndex)
        
    def __populateLanguageCombo(self):
        """
        Private method to initialize the language combobox of the Interface
        configuration page.
        """
        self.languageComboBox.clear()
        
        fnlist = glob.glob("eric6_*.qm") + \
            glob.glob(os.path.join(
                getConfig('ericTranslationsDir'), "eric6_*.qm")) + \
            glob.glob(os.path.join(Utilities.getConfigDir(), "eric6_*.qm"))
        locales = {}
        for fn in fnlist:
            locale = os.path.basename(fn)[6:-3]
            if locale not in locales:
                translator = QTranslator()
                translator.load(fn)
                locales[locale] = translator.translate(
                    "InterfacePage", "English",
                    "Translate this with your language") + \
                    " ({0})".format(locale)
        localeList = sorted(list(locales.keys()))
        try:
            uiLanguage = Preferences.getUILanguage()
            if uiLanguage == "None" or uiLanguage is None:
                currentIndex = 0
            elif uiLanguage == "System":
                currentIndex = 1
            else:
                currentIndex = localeList.index(uiLanguage) + 2
        except ValueError:
            currentIndex = 0
        self.languageComboBox.clear()
        
        self.languageComboBox.addItem("English (default)", "None")
        self.languageComboBox.addItem(self.tr('System'), "System")
        for locale in localeList:
            self.languageComboBox.addItem(locales[locale], locale)
        self.languageComboBox.setCurrentIndex(currentIndex)
        
    @pyqtSlot()
    def on_styleSheetButton_clicked(self):
        """
        Private method to select the style sheet file via a dialog.
        """
        file = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select style sheet file"),
            self.styleSheetEdit.text(),
            self.tr(
                "Qt Style Sheets (*.qss);;Cascading Style Sheets (*.css);;"
                "All files (*)"))
        
        if file:
            self.styleSheetEdit.setText(Utilities.toNativeSeparators(file))
        
    @pyqtSlot()
    def on_resetLayoutButton_clicked(self):
        """
        Private method to reset layout to factory defaults.
        """
        Preferences.resetLayout()
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = InterfacePage()
    return page
