# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a horizontal and a vertical toolbox class.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QToolBox, QTabWidget

from .E5TabWidget import E5TabWidget


class E5VerticalToolBox(QToolBox):
    """
    Class implementing a ToolBox class substituting QToolBox to support wheel
    events.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(E5VerticalToolBox, self).__init__(parent)


class E5HorizontalToolBox(E5TabWidget):
    """
    Class implementing a vertical QToolBox like widget.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        E5TabWidget.__init__(self, parent)
        self.setTabPosition(QTabWidget.West)
        self.setUsesScrollButtons(True)
    
    def addItem(self, widget, icon, text):
        """
        Public method to add a widget to the toolbox.
        
        @param widget reference to the widget to be added (QWidget)
        @param icon the icon to be shown (QIcon)
        @param text the text to be shown (string)
        @return index of the added widget (integer)
        """
        index = self.addTab(widget, icon, "")
        self.setTabToolTip(index, text)
        return index
    
    def insertItem(self, index, widget, icon, text):
        """
        Public method to add a widget to the toolbox.
        
        @param index position at which the widget should be inserted (integer)
        @param widget reference to the widget to be added (QWidget)
        @param icon the icon to be shown (QIcon)
        @param text the text to be shown (string)
        @return index of the added widget (integer)
        """
        index = self.insertTab(index, widget, icon, "")
        self.setTabToolTip(index, text)
        return index
    
    def removeItem(self, index):
        """
        Public method to remove a widget from the toolbox.
        
        @param index index of the widget to remove (integer)
        """
        self.removeTab(index)
    
    def setItemToolTip(self, index, toolTip):
        """
        Public method to set the tooltip of an item.
        
        @param index index of the item (integer)
        @param toolTip tooltip text to be set (string)
        """
        self.setTabToolTip(index, toolTip)
    
    def setItemEnabled(self, index, enabled):
        """
        Public method to set the enabled state of an item.
        
        @param index index of the item (integer)
        @param enabled flag indicating the enabled state (boolean)
        """
        self.setTabEnabled(index, enabled)
