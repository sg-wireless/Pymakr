# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Printer configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_GraphicsPage import Ui_GraphicsPage

import Preferences


class GraphicsPage(ConfigurationPageBase, Ui_GraphicsPage):
    """
    Class implementing the Printer configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(GraphicsPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("GraphicsPage")
        
        # set initial values
        self.graphicsFont = Preferences.getGraphics("Font")
        self.graphicsFontSample.setFont(self.graphicsFont)
        
    def save(self):
        """
        Public slot to save the Printer configuration.
        """
        Preferences.setGraphics("Font", self.graphicsFont)
        
    @pyqtSlot()
    def on_graphicsFontButton_clicked(self):
        """
        Private method used to select the font for the graphics items.
        """
        self.graphicsFont = self.selectFont(self.graphicsFontSample,
                                            self.graphicsFont)
        
    def polishPage(self):
        """
        Public slot to perform some polishing actions.
        """
        self.graphicsFontSample.setFont(self.graphicsFont)
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = GraphicsPage()
    return page
