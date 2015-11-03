# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the tray starter configuration page.
"""

from __future__ import unicode_literals

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_TrayStarterPage import Ui_TrayStarterPage

import Preferences
import UI.PixmapCache


class TrayStarterPage(ConfigurationPageBase, Ui_TrayStarterPage):
    """
    Class implementing the tray starter configuration page.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(TrayStarterPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("TrayStarterPage")
        
        self.standardButton.setIcon(UI.PixmapCache.getIcon("erict.png"))
        self.highContrastButton.setIcon(UI.PixmapCache.getIcon("erict-hc.png"))
        self.blackWhiteButton.setIcon(UI.PixmapCache.getIcon("erict-bw.png"))
        self.blackWhiteInverseButton.setIcon(
            UI.PixmapCache.getIcon("erict-bwi.png"))
        
        # set initial values
        iconName = Preferences.getTrayStarter("TrayStarterIcon")
        if iconName == "erict.png":
            self.standardButton.setChecked(True)
        elif iconName == "erict-hc.png":
            self.highContrastButton.setChecked(True)
        elif iconName == "erict-bw.png":
            self.blackWhiteButton.setChecked(True)
        elif iconName == "erict-bwi.png":
            self.blackWhiteInverseButton.setChecked(True)
    
    def save(self):
        """
        Public slot to save the Python configuration.
        """
        if self.standardButton.isChecked():
            iconName = "erict.png"
        elif self.highContrastButton.isChecked():
            iconName = "erict-hc.png"
        elif self.blackWhiteButton.isChecked():
            iconName = "erict-bw.png"
        elif self.blackWhiteInverseButton.isChecked():
            iconName = "erict-bwi.png"
        Preferences.setTrayStarter("TrayStarterIcon", iconName)
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = TrayStarterPage()
    return page
