# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Help Viewers configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5FileDialog

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_HelpAppearancePage import Ui_HelpAppearancePage

import Preferences
import Utilities
import UI.PixmapCache


class HelpAppearancePage(ConfigurationPageBase, Ui_HelpAppearancePage):
    """
    Class implementing the Help Viewer Appearance page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(HelpAppearancePage, self).__init__()
        self.setupUi(self)
        self.setObjectName("HelpAppearancePage")
        
        self.styleSheetButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.styleSheetCompleter = E5FileCompleter(self.styleSheetEdit)
        
        self.__displayMode = None
        
        # set initial values
        self.standardFont = Preferences.getHelp("StandardFont")
        self.standardFontSample.setFont(self.standardFont)
        self.standardFontSample.setText(
            "{0} {1}".format(self.standardFont.family(),
                             self.standardFont.pointSize()))
        
        self.fixedFont = Preferences.getHelp("FixedFont")
        self.fixedFontSample.setFont(self.fixedFont)
        self.fixedFontSample.setText(
            "{0} {1}".format(self.fixedFont.family(),
                             self.fixedFont.pointSize()))
        
        self.initColour("SaveUrlColor", self.secureURLsColourButton,
                        Preferences.getHelp)
        
        self.autoLoadImagesCheckBox.setChecked(
            Preferences.getHelp("AutoLoadImages"))
        
        self.styleSheetEdit.setText(Preferences.getHelp("UserStyleSheet"))
        
        self.tabsCloseButtonCheckBox.setChecked(
            Preferences.getUI("SingleCloseButton"))
        self.warnOnMultipleCloseCheckBox.setChecked(
            Preferences.getHelp("WarnOnMultipleClose"))
    
    def setMode(self, displayMode):
        """
        Public method to perform mode dependent setups.
        
        @param displayMode mode of the configuration dialog
            (ConfigurationWidget.DefaultMode,
             ConfigurationWidget.HelpBrowserMode,
             ConfigurationWidget.TrayStarterMode)
        """
        from ..ConfigurationDialog import ConfigurationWidget
        assert displayMode in (
            ConfigurationWidget.DefaultMode,
            ConfigurationWidget.HelpBrowserMode,
            ConfigurationWidget.TrayStarterMode
        )
        
        self.__displayMode = displayMode
        if self.__displayMode != ConfigurationWidget.HelpBrowserMode:
            self.separatorLine.hide()
            self.nextStartupNoteLabel.hide()
            self.tabsGroupBox.hide()
    
    def save(self):
        """
        Public slot to save the Help Viewers configuration.
        """
        Preferences.setHelp("StandardFont", self.standardFont)
        Preferences.setHelp("FixedFont", self.fixedFont)
        
        Preferences.setHelp(
            "AutoLoadImages",
            self.autoLoadImagesCheckBox.isChecked())
        
        Preferences.setHelp("UserStyleSheet", self.styleSheetEdit.text())
        
        self.saveColours(Preferences.setHelp)
        
        from ..ConfigurationDialog import ConfigurationWidget
        if self.__displayMode == ConfigurationWidget.HelpBrowserMode:
            Preferences.setUI(
                "SingleCloseButton",
                self.tabsCloseButtonCheckBox.isChecked())
        
        Preferences.setHelp(
            "WarnOnMultipleClose",
            self.warnOnMultipleCloseCheckBox.isChecked())
    
    @pyqtSlot()
    def on_standardFontButton_clicked(self):
        """
        Private method used to select the standard font.
        """
        self.standardFont = \
            self.selectFont(self.standardFontSample, self.standardFont, True)
    
    @pyqtSlot()
    def on_fixedFontButton_clicked(self):
        """
        Private method used to select the fixed-width font.
        """
        self.fixedFont = \
            self.selectFont(self.fixedFontSample, self.fixedFont, True)
    
    @pyqtSlot()
    def on_styleSheetButton_clicked(self):
        """
        Private slot to handle the user style sheet selection.
        """
        file = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select Style Sheet"),
            self.styleSheetEdit.text(),
            "")
        
        if file:
            self.styleSheetEdit.setText(Utilities.toNativeSeparators(file))
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = HelpAppearancePage()
    return page
