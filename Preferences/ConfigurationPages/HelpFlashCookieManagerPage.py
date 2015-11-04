# -*- coding: utf-8 -*-

# Copyright (c) 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Flash Cookies Manager configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot

from E5Gui.E5Completers import E5DirCompleter
from E5Gui import E5FileDialog

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_HelpFlashCookieManagerPage import Ui_HelpFlashCookieManagerPage

import Preferences
import Utilities
import UI.PixmapCache


class HelpFlashCookieManagerPage(ConfigurationPageBase,
                                 Ui_HelpFlashCookieManagerPage):
    """
    Class implementing the Flash Cookies Manager configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(HelpFlashCookieManagerPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("HelpFlashCookieManagerPage")
        
        self.flashDataPathButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.flashDataPathCompleter = E5DirCompleter(self.flashDataPathEdit)
        
        # set initial values
        self.flashDataPathEdit.setText(
            Preferences.getHelp("FlashCookiesDataPath"))
        self.autoModeGroup.setChecked(
            Preferences.getHelp("FlashCookieAutoRefresh"))
        self.notificationGroup.setChecked(
            Preferences.getHelp("FlashCookieNotify"))
        self.deleteGroup.setChecked(
            Preferences.getHelp("FlashCookiesDeleteOnStartExit"))
    
    def save(self):
        """
        Public slot to save the Flash Cookies Manager configuration.
        """
        Preferences.setHelp("FlashCookiesDataPath",
                            self.flashDataPathEdit.text())
        Preferences.setHelp("FlashCookieAutoRefresh",
                            self.autoModeGroup.isChecked())
        Preferences.setHelp("FlashCookieNotify",
                            self.notificationGroup.isChecked())
        Preferences.setHelp("FlashCookiesDeleteOnStartExit",
                            self.deleteGroup.isChecked())
    
    @pyqtSlot()
    def on_flashDataPathButton_clicked(self):
        """
        Private slot to handle the flash data path selection.
        """
        path = E5FileDialog.getExistingDirectory(
            self,
            self.tr("Select Flash Cookies Data Path"),
            self.flashDataPathEdit.text(),
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
        
        if path:
            self.flashDataPathEdit.setText(Utilities.toNativeSeparators(path))
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = HelpFlashCookieManagerPage()
    return page
