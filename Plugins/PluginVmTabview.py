# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Tabview view manager plugin.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QT_TRANSLATE_NOOP, QObject
from PyQt5.QtGui import QPixmap

# Start-Of-Header
name = "Tabview Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = False
deactivateable = False
version = "6.1.0"
pluginType = "viewmanager"
pluginTypename = "tabview"
displayString = QT_TRANSLATE_NOOP('VmTabviewPlugin', 'Tabbed View')
className = "VmTabviewPlugin"
packageName = "__core__"
shortDescription = "Implements the Tabview view manager."
longDescription = """This plugin provides the tabbed view view manager."""
pyqtApi = 2
python2Compatible = True
# End-Of-Header

error = ""


def previewPix():
    """
    Module function to return a preview pixmap.
    
    @return preview pixmap (QPixmap)
    """
    fname = os.path.join(os.path.dirname(__file__),
                         "ViewManagerPlugins", "Tabview", "preview.png")
    return QPixmap(fname)
    

class VmTabviewPlugin(QObject):
    """
    Class implementing the Tabview view manager plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        super(VmTabviewPlugin, self).__init__(ui)
        self.__ui = ui

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of reference to instantiated viewmanager and
            activation status (boolean)
        """
        from ViewManagerPlugins.Tabview.Tabview import Tabview
        self.__object = Tabview(self.__ui)
        return self.__object, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        # do nothing for the moment
        pass
