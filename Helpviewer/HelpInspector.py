# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a QWebInspector wrapper to save and restore the geometry.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QSize
from PyQt5.QtWebKitWidgets import QWebInspector

import Preferences


class HelpInspector(QWebInspector):
    """
    Class implementing a QWebInspector wrapper to save and restore the
    geometry.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget
        @type QWidget
        """
        super(HelpInspector, self).__init__(parent)
        self.__reloadGeometry()

    def closeEvent(self, evt):
        """
        Protected method to save the geometry when closed.
        
        @param evt event object
        @type QCloseEvent
        """
        Preferences.setGeometry("HelpInspectorGeometry", self.saveGeometry())
        super(HelpInspector, self).closeEvent(evt)

    def __reloadGeometry(self):
        """
        Private method to restore the geometry.
        """
        geom = Preferences.getGeometry("HelpInspectorGeometry")
        if geom.isEmpty():
            s = QSize(600, 600)
            self.resize(s)
        else:
            self.restoreGeometry(geom)
