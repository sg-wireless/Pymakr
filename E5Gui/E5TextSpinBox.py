# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a spinbox with textual entries.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QSpinBox


class E5TextSpinBox(QSpinBox):
    """
    Class implementing a spinbox with textual entries.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(E5TextSpinBox, self).__init__(parent)
        
        self.__items = []
        
        self.setMinimum(0)
        self.setMaximum(0)
    
    def addItem(self, txt, data=None):
        """
        Public method to add an item with item data.
        
        @param txt text to be shown (string)
        @param data associated data
        """
        self.__items.append((txt, data))
        self.setMaximum(len(self.__items) - 1)
    
    def itemData(self, index):
        """
        Public method to retrieve the data associated with an item.
        
        @param index index of the item (integer)
        @return associated data
        """
        try:
            return self.__items[index][1]
        except IndexError:
            return None
    
    def currentIndex(self):
        """
        Public method to retrieve the current index.
        
        @return current index (integer)
        """
        return self.value()
    
    def textFromValue(self, value):
        """
        Public method to convert a value to text.
        
        @param value value to be converted (integer)
        @return text for the given value (string)
        """
        try:
            return self.__items[value][0]
        except IndexError:
            return ""
    
    def valueFromText(self, txt):
        """
        Public method to convert a text to a value.
        
        @param txt text to be converted (string)
        @return value for the given text (integer)
        """
        for index in range(len(self.__items)):
            if self.__items[index][0] == txt:
                return index
        
        return self.minimum()
