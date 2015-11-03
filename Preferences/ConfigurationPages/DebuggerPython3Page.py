# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Debugger Python3 configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5FileDialog

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_DebuggerPython3Page import Ui_DebuggerPython3Page

import Preferences
import Utilities
import UI.PixmapCache


class DebuggerPython3Page(ConfigurationPageBase, Ui_DebuggerPython3Page):
    """
    Class implementing the Debugger Python3 configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(DebuggerPython3Page, self).__init__()
        self.setupUi(self)
        self.setObjectName("DebuggerPython3Page")
        
        self.interpreterButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.debugClientButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.interpreterCompleter = E5FileCompleter(self.interpreterEdit)
        self.debugClientCompleter = E5FileCompleter(self.debugClientEdit)
        
        # set initial values
        self.interpreterEdit.setText(
            Preferences.getDebugger("Python3Interpreter"))
        dct = Preferences.getDebugger("DebugClientType3")
        if dct == "standard":
            self.standardButton.setChecked(True)
        elif dct == "threaded":
            self.threadedButton.setChecked(True)
        else:
            self.customButton.setChecked(True)
        self.debugClientEdit.setText(
            Preferences.getDebugger("DebugClient3"))
        self.pyRedirectCheckBox.setChecked(
            Preferences.getDebugger("Python3Redirect"))
        self.pyNoEncodingCheckBox.setChecked(
            Preferences.getDebugger("Python3NoEncoding"))
        self.sourceExtensionsEdit.setText(
            Preferences.getDebugger("Python3Extensions"))
        
    def save(self):
        """
        Public slot to save the Debugger Python configuration.
        """
        Preferences.setDebugger(
            "Python3Interpreter",
            self.interpreterEdit.text())
        if self.standardButton.isChecked():
            dct = "standard"
        elif self.threadedButton.isChecked():
            dct = "threaded"
        else:
            dct = "custom"
        Preferences.setDebugger("DebugClientType3", dct)
        Preferences.setDebugger(
            "DebugClient3",
            self.debugClientEdit.text())
        Preferences.setDebugger(
            "Python3Redirect",
            self.pyRedirectCheckBox.isChecked())
        Preferences.setDebugger(
            "Python3NoEncoding",
            self.pyNoEncodingCheckBox.isChecked())
        Preferences.setDebugger(
            "Python3Extensions",
            self.sourceExtensionsEdit.text())
        
    @pyqtSlot()
    def on_interpreterButton_clicked(self):
        """
        Private slot to handle the Python interpreter selection.
        """
        file = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select Python interpreter for Debug Client"),
            self.interpreterEdit.text(),
            "")
            
        if file:
            self.interpreterEdit.setText(
                Utilities.toNativeSeparators(file))
        
    @pyqtSlot()
    def on_debugClientButton_clicked(self):
        """
        Private slot to handle the Debug Client selection.
        """
        file = E5FileDialog.getOpenFileName(
            None,
            self.tr("Select Debug Client"),
            self.debugClientEdit.text(),
            self.tr("Python Files (*.py *.py3)"))
            
        if file:
            self.debugClientEdit.setText(
                Utilities.toNativeSeparators(file))
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = DebuggerPython3Page()
    return page
