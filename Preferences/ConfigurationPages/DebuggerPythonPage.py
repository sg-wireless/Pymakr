# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Debugger Python configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5FileDialog

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_DebuggerPythonPage import Ui_DebuggerPythonPage

import Preferences
import Utilities
import UI.PixmapCache


class DebuggerPythonPage(ConfigurationPageBase, Ui_DebuggerPythonPage):
    """
    Class implementing the Debugger Python configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(DebuggerPythonPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("DebuggerPythonPage")
        
        self.interpreterButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.debugClientButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.interpreterCompleter = E5FileCompleter(self.interpreterEdit)
        self.debugClientCompleter = E5FileCompleter(self.debugClientEdit)
        
        # set initial values
        self.interpreterEdit.setText(
            Preferences.getDebugger("PythonInterpreter"))
        dct = Preferences.getDebugger("DebugClientType")
        if dct == "standard":
            self.standardButton.setChecked(True)
        elif dct == "threaded":
            self.threadedButton.setChecked(True)
        else:
            self.customButton.setChecked(True)
        self.debugClientEdit.setText(
            Preferences.getDebugger("DebugClient"))
        self.pyRedirectCheckBox.setChecked(
            Preferences.getDebugger("PythonRedirect"))
        self.pyNoEncodingCheckBox.setChecked(
            Preferences.getDebugger("PythonNoEncoding"))
        self.sourceExtensionsEdit.setText(
            Preferences.getDebugger("PythonExtensions"))
        
    def save(self):
        """
        Public slot to save the Debugger Python configuration.
        """
        Preferences.setDebugger(
            "PythonInterpreter",
            self.interpreterEdit.text())
        if self.standardButton.isChecked():
            dct = "standard"
        elif self.threadedButton.isChecked():
            dct = "threaded"
        else:
            dct = "custom"
        Preferences.setDebugger("DebugClientType", dct)
        Preferences.setDebugger(
            "DebugClient",
            self.debugClientEdit.text())
        Preferences.setDebugger(
            "PythonRedirect",
            self.pyRedirectCheckBox.isChecked())
        Preferences.setDebugger(
            "PythonNoEncoding",
            self.pyNoEncodingCheckBox.isChecked())
        Preferences.setDebugger(
            "PythonExtensions",
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
            self.tr("Python Files (*.py *.py2)"))
            
        if file:
            self.debugClientEdit.setText(
                Utilities.toNativeSeparators(file))
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = DebuggerPythonPage()
    return page
