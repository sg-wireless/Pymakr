# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a special list widget for GreaseMonkey scripts.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, QRect
from PyQt5.QtWidgets import QListWidget, QListWidgetItem

from .GreaseMonkeyConfigurationListDelegate import \
    GreaseMonkeyConfigurationListDelegate


class GreaseMonkeyConfigurationListWidget(QListWidget):
    """
    Class implementing a special list widget for GreaseMonkey scripts.
    """
    removeItemRequested = pyqtSignal(QListWidgetItem)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(GreaseMonkeyConfigurationListWidget, self).__init__(parent)
        
        self.__delegate = GreaseMonkeyConfigurationListDelegate(self)
        self.setItemDelegate(self.__delegate)
    
    def __containsRemoveIcon(self, pos):
        """
        Private method to check, if the given position is inside the remove
        icon.
        
        @param pos position to check for (QPoint)
        @return flag indicating success (boolean)
        """
        itm = self.itemAt(pos)
        if itm is None:
            return False
        
        rect = self.visualItemRect(itm)
        iconSize = GreaseMonkeyConfigurationListDelegate.RemoveIconSize
        removeIconXPos = rect.right() - self.__delegate.padding() - iconSize
        center = rect.height() // 2 + rect.top()
        removeIconYPos = center - iconSize // 2
        
        removeIconRect = QRect(removeIconXPos, removeIconYPos,
                               iconSize, iconSize)
        return removeIconRect.contains(pos)
    
    def mousePressEvent(self, evt):
        """
        Protected method handling presses of mouse buttons.
        
        @param evt mouse press event (QMouseEvent)
        """
        if self.__containsRemoveIcon(evt.pos()):
            self.removeItemRequested.emit(self.itemAt(evt.pos()))
            return
        
        super(GreaseMonkeyConfigurationListWidget, self).mousePressEvent(evt)
    
    def mouseDoubleClickEvent(self, evt):
        """
        Protected method handling mouse double click events.
        
        @param evt mouse press event (QMouseEvent)
        """
        if self.__containsRemoveIcon(evt.pos()):
            self.removeItemRequested.emit(self.itemAt(evt.pos()))
            return
        
        super(GreaseMonkeyConfigurationListWidget, self).mouseDoubleClickEvent(
            evt)
