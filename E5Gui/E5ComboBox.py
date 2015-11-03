# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing combobox classes using the eric6 line edits.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QComboBox


class E5ComboBox(QComboBox):
    """
    Class implementing a combobox using the eric6 line edit.
    """
    def __init__(self, parent=None, inactiveText=""):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        @param inactiveText text to be shown on inactivity (string)
        """
        super(E5ComboBox, self).__init__(parent)
        
        self.setMinimumHeight(24)
        
        from .E5LineEdit import E5LineEdit
        self.__lineedit = E5LineEdit(self, inactiveText)
        self.setLineEdit(self.__lineedit)
        
        self.setMinimumHeight(self.__lineedit.minimumHeight() + 3)
    
    def inactiveText(self):
        """
        Public method to get the inactive text.
        
        @return inactive text (string)
        """
        return self.__lineedit.inactiveText()
    
    def setInactiveText(self, inactiveText):
        """
        Public method to set the inactive text.
        
        @param inactiveText text to be shown on inactivity (string)
        """
        self.__lineedit.setInactiveText()


class E5ClearableComboBox(E5ComboBox):
    """
    Class implementing a combobox using the eric6 line edit.
    """
    def __init__(self, parent=None, inactiveText=""):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        @param inactiveText text to be shown on inactivity (string)
        """
        super(E5ClearableComboBox, self).__init__(parent, inactiveText)
        
        from .E5LineEdit import E5ClearableLineEdit
        self.__lineedit = E5ClearableLineEdit(self, inactiveText)
        self.setLineEdit(self.__lineedit)
