# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to select the zoom scale.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_ZoomDialog import Ui_ZoomDialog


class ZoomDialog(QDialog, Ui_ZoomDialog):
    """
    Class implementing a dialog to select the zoom scale.
    """
    def __init__(self, zoom, parent, name=None, modal=False):
        """
        Constructor
        
        @param zoom zoom factor to show in the spinbox
        @param parent parent widget of this dialog (QWidget)
        @param name name of this dialog (string)
        @param modal modal dialog state (boolean)
        """
        super(ZoomDialog, self).__init__(parent)
        if name:
            self.setObjectName(name)
        self.setupUi(self)
        self.setModal(modal)
        
        self.zoomSpinBox.setValue(zoom)
        self.zoomSpinBox.selectAll()
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    def getZoomSize(self):
        """
        Public method to retrieve the zoom size.
        
        @return zoom size (int)
        """
        return self.zoomSpinBox.value()
