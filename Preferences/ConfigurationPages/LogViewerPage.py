# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Log Viewer configuration page.
"""

from __future__ import unicode_literals

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_LogViewerPage import Ui_LogViewerPage

import Preferences


class LogViewerPage(ConfigurationPageBase, Ui_LogViewerPage):
    """
    Class implementing the Log Viewer configuration page.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(LogViewerPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("LogViewerPage")
        
        self.stdoutFilterEdit.setListWhatsThis(self.tr(
            "<b>Message Filters for Standard Output</b>"
            "<p>This list shows the configured message filters used to"
            " suppress messages received via stdout.</p>"
        ))
        self.stderrFilterEdit.setListWhatsThis(self.tr(
            "<b>Message Filters for Standard Error </b>"
            "<p>This list shows the configured message filters used to"
            " suppress messages received via stderr.</p>"
        ))
        self.stdxxxFilterEdit.setListWhatsThis(self.tr(
            "<b>Message Filters for both</b>"
            "<p>This list shows the configured message filters used to"
            " suppress messages received via stdout or stderr.</p>"
        ))
        
        # set initial values
        self.lvAutoRaiseCheckBox.setChecked(
            Preferences.getUI("LogViewerAutoRaise"))
        
        self.initColour(
            "LogStdErrColour", self.stderrTextColourButton,
            Preferences.getUI)
        
        self.stdoutFilterEdit.setList(
            Preferences.getUI("LogViewerStdoutFilter"))
        self.stderrFilterEdit.setList(
            Preferences.getUI("LogViewerStderrFilter"))
        self.stdxxxFilterEdit.setList(
            Preferences.getUI("LogViewerStdxxxFilter"))
    
    def save(self):
        """
        Public slot to save the Interface configuration.
        """
        Preferences.setUI(
            "LogViewerAutoRaise",
            self.lvAutoRaiseCheckBox.isChecked())
        
        self.saveColours(Preferences.setUI)
        
        Preferences.setUI(
            "LogViewerStdoutFilter",
            self.stdoutFilterEdit.getList())
        Preferences.setUI(
            "LogViewerStderrFilter",
            self.stderrFilterEdit.getList())
        Preferences.setUI(
            "LogViewerStdxxxFilter",
            self.stdxxxFilterEdit.getList())
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = LogViewerPage()
    return page
