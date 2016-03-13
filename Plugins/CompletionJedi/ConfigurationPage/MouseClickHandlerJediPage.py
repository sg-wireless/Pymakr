# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Jedi Mouse Click Handler configuration page.
"""

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog

from Preferences.ConfigurationPages.ConfigurationPageBase import \
    ConfigurationPageBase

from .Ui_MouseClickHandlerJediPage import Ui_MouseClickHandlerJediPage

from Utilities import MouseUtilities
from Preferences.MouseClickDialog import MouseClickDialog


class MouseClickHandlerJediPage(ConfigurationPageBase,
                                Ui_MouseClickHandlerJediPage):
    """
    Class implementing the Jedi Mouse Click Handler configuration page.
    """
    def __init__(self, plugin):
        """
        Constructor
        
        @param plugin reference to the plugin object
        @type RefactoringRopePlugin
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("MouseClickHandlerJediPage")
        
        self.__plugin = plugin
        
        # set initial values
        self.__modifiers = {
            "goto": (
                self.__plugin.getPreferences("MouseClickGotoModifiers"),
                self.__plugin.getPreferences("MouseClickGotoButton")
            )
        }
        
        self.jediClickHandlerCheckBox.setChecked(
            self.__plugin.getPreferences("MouseClickEnabled"))
        self.gotoClickEdit.setText(MouseUtilities.MouseButtonModifier2String(
            *self.__modifiers["goto"]))
    
    def save(self):
        """
        Public slot to save the Jedi Mouse Click Handler configuration.
        """
        self.__plugin.setPreferences("MouseClickEnabled",
            self.jediClickHandlerCheckBox.isChecked())
        self.__plugin.setPreferences("MouseClickGotoModifiers",
            int(self.__modifiers["goto"][0]))
        self.__plugin.setPreferences("MouseClickGotoButton",
            int(self.__modifiers["goto"][1]))
    
    @pyqtSlot()
    def on_changeGotoButton_clicked(self):
        """
        Private slot to change the 'goto' mouse click sequence.
        """
        dlg = MouseClickDialog(*self.__modifiers["goto"])
        if dlg.exec_() == QDialog.Accepted:
            self.__modifiers["goto"] = dlg.getClick()
            self.gotoClickEdit.setText(
                MouseUtilities.MouseButtonModifier2String(
                    *self.__modifiers["goto"]))
