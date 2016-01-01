# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor Mouse Click Handlers configuration page.
"""

from __future__ import unicode_literals

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorMouseClickHandlerPage import Ui_EditorMouseClickHandlerPage

import Preferences


class EditorMouseClickHandlerPage(ConfigurationPageBase,
                                  Ui_EditorMouseClickHandlerPage):
    """
    Class implementing the Editor Mouse Click Handlers configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(EditorMouseClickHandlerPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("EditorMouseClickHandlerPage")
        
        # set initial values
        self.mcEnabledCheckBox.setChecked(
            Preferences.getEditor("MouseClickHandlersEnabled"))
        
    def save(self):
        """
        Public slot to save the Editor Mouse Click Handlers configuration.
        """
        Preferences.setEditor(
            "MouseClickHandlersEnabled",
            self.mcEnabledCheckBox.isChecked())
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = EditorMouseClickHandlerPage()
    return page
