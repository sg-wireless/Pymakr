# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Python configuration page.
"""

from __future__ import unicode_literals

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_PythonPage import Ui_PythonPage

import Preferences
from Utilities import supportedCodecs


class PythonPage(ConfigurationPageBase, Ui_PythonPage):
    """
    Class implementing the Python configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(PythonPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("PythonPage")
        
        self.stringEncodingComboBox.addItems(sorted(supportedCodecs))
        self.ioEncodingComboBox.addItems(sorted(supportedCodecs))
        
        # set initial values
        index = self.stringEncodingComboBox.findText(
            Preferences.getSystem("StringEncoding"))
        self.stringEncodingComboBox.setCurrentIndex(index)
        index = self.ioEncodingComboBox.findText(
            Preferences.getSystem("IOEncoding"))
        self.ioEncodingComboBox.setCurrentIndex(index)
        
        # these are the same as in the debugger pages
        self.py2ExtensionsEdit.setText(
            Preferences.getDebugger("PythonExtensions"))
        self.py3ExtensionsEdit.setText(
            Preferences.getDebugger("Python3Extensions"))
        
    def save(self):
        """
        Public slot to save the Python configuration.
        """
        enc = self.stringEncodingComboBox.currentText()
        if not enc:
            enc = "utf-8"
        Preferences.setSystem("StringEncoding", enc)
        
        enc = self.ioEncodingComboBox.currentText()
        if not enc:
            enc = "utf-8"
        Preferences.setSystem("IOEncoding", enc)
        
        Preferences.setDebugger(
            "PythonExtensions",
            self.py2ExtensionsEdit.text())
        Preferences.setDebugger(
            "Python3Extensions",
            self.py3ExtensionsEdit.text())
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = PythonPage()
    return page
