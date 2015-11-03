# -*- coding: utf-8 -*-

"""
Module implementing the Interface configuration page (variant for web browser).
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QStyleFactory

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5FileDialog

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_HelpInterfacePage import Ui_HelpInterfacePage

import Preferences
import Utilities
import UI.PixmapCache


class HelpInterfacePage(ConfigurationPageBase, Ui_HelpInterfacePage):
    """
    Class implementing the Interface configuration page (variant for web
    browser).
    """
    def __init__(self):
        """
        Constructor
        """
        super(HelpInterfacePage, self).__init__()
        self.setupUi(self)
        self.setObjectName("InterfacePage")
        
        self.styleSheetButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.styleSheetCompleter = E5FileCompleter(self.styleSheetEdit)
        
        # set initial values
        self.__populateStyleCombo()
        self.styleSheetEdit.setText(Preferences.getUI("StyleSheet"))
    
    def save(self):
        """
        Public slot to save the Interface configuration.
        """
        # save the style settings
        styleIndex = self.styleComboBox.currentIndex()
        style = self.styleComboBox.itemData(styleIndex)
        Preferences.setUI("Style", style)
        Preferences.setUI(
            "StyleSheet",
            self.styleSheetEdit.text())
    
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
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = HelpInterfacePage()
    return page
