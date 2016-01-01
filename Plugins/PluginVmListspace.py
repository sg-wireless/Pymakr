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
name = "Listspace Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = False
deactivateable = False
version = "6.1.0"
pluginType = "viewmanager"
pluginTypename = "listspace"
displayString = QT_TRANSLATE_NOOP('VmListspacePlugin', 'Listspace')
className = "VmListspacePlugin"
packageName = "__core__"
shortDescription = "Implements the Listspace view manager."
longDescription = """This plugin provides the listspace view manager."""
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
                         "ViewManagerPlugins", "Listspace", "preview.png")
    return QPixmap(fname)
    

class VmListspacePlugin(QObject):
    """
    Class implementing the Listspace view manager plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        super(VmListspacePlugin, self).__init__(ui)
        self.__ui = ui

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of reference to instantiated viewmanager and
            activation status (boolean)
        """
        from ViewManagerPlugins.Listspace.Listspace import Listspace
        self.__object = Listspace(self.__ui)
        return self.__object, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        # do nothing for the moment
        pass
