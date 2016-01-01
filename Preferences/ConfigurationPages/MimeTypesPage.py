# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Text Mime Types configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot

from E5Gui import E5MessageBox

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_MimeTypesPage import Ui_MimeTypesPage

import Preferences


class MimeTypesPage(ConfigurationPageBase, Ui_MimeTypesPage):
    """
    Class implementing the Text Mime Types configuration page.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(MimeTypesPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("MimeTypesPage")
        
        # set initial values
        self.textMimeTypesList.setList(
            Preferences.getUI("TextMimeTypes"))
    
    def save(self):
        """
        Public slot to save the Interface configuration.
        """
        Preferences.setUI("TextMimeTypes", self.textMimeTypesList.getList())
    
    @pyqtSlot()
    def on_resetButton_clicked(self):
        """
        Private slot to set the default list of mime types.
        """
        ok = E5MessageBox.yesNo(
            self,
            self.tr("Reset Mime Types"),
            self.tr("""Do you really want to reset the configured list of"""
                    """ mime types?"""))
        if ok:
            self.textMimeTypesList.setList(
                Preferences.Prefs.uiDefaults["TextMimeTypes"])
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = MimeTypesPage()
    return page
