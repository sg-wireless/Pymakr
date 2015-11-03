# -*- coding: utf-8 -*-

"""
Module implementing a dialog to enter the icon size.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_IconSizeDialog import Ui_IconSizeDialog


class IconSizeDialog(QDialog, Ui_IconSizeDialog):
    """
    Class implementing a dialog to enter the icon size.
    """
    def __init__(self, width, height, parent=None):
        """
        Constructor
        
        @param width width to be set (integer)
        @param height height to be set (integer)
        @param parent reference to the parent widget (QWidget)
        """
        super(IconSizeDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.widthSpin.setValue(width)
        self.heightSpin.setValue(height)
        
        self.widthSpin.selectAll()
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    def getData(self):
        """
        Public method to get the entered data.
        
        @return tuple with width and height (tuple of two integers)
        """
        return self.widthSpin.value(), self.heightSpin.value()
