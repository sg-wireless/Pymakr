# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Debugger Ruby configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5FileDialog

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_DebuggerRubyPage import Ui_DebuggerRubyPage

import Preferences
import Utilities
import UI.PixmapCache


class DebuggerRubyPage(ConfigurationPageBase, Ui_DebuggerRubyPage):
    """
    Class implementing the Debugger Ruby configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(DebuggerRubyPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("DebuggerRubyPage")
        
        self.rubyInterpreterButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.rubyInterpreterCompleter = E5FileCompleter(
            self.rubyInterpreterEdit)
        
        # set initial values
        self.rubyInterpreterEdit.setText(
            Preferences.getDebugger("RubyInterpreter"))
        self.rbRedirectCheckBox.setChecked(
            Preferences.getDebugger("RubyRedirect"))
        
    def save(self):
        """
        Public slot to save the Debugger Ruby configuration.
        """
        Preferences.setDebugger(
            "RubyInterpreter",
            self.rubyInterpreterEdit.text())
        Preferences.setDebugger(
            "RubyRedirect",
            self.rbRedirectCheckBox.isChecked())
        
    @pyqtSlot()
    def on_rubyInterpreterButton_clicked(self):
        """
        Private slot to handle the Ruby interpreter selection.
        """
        file = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select Ruby interpreter for Debug Client"),
            self.rubyInterpreterEdit.text())
            
        if file:
            self.rubyInterpreterEdit.setText(
                Utilities.toNativeSeparators(file))
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = DebuggerRubyPage()
    return page
