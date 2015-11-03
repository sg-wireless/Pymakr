# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a clickable label.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt, QPoint
from PyQt5.QtWidgets import QLabel


class E5ClickableLabel(QLabel):
    """
    Class implementing a clickable label.
    
    @signal clicked(QPoint) emitted upon a click on the label
        with the left button
    @signal middleClicked(QPoint) emitted upon a click on the label
        with the middle button or CTRL and left button
    """
    clicked = pyqtSignal(QPoint)
    middleClicked = pyqtSignal(QPoint)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(E5ClickableLabel, self).__init__(parent)
    
    def mouseReleaseEvent(self, evt):
        """
        Protected method handling mouse release events.
        
        @param evt mouse event (QMouseEvent)
        """
        if evt.button() == Qt.LeftButton and self.rect().contains(evt.pos()):
            if evt.modifiers() == Qt.ControlModifier:
                self.middleClicked.emit(evt.globalPos())
            else:
                self.clicked.emit(evt.globalPos())
        elif evt.button() == Qt.MidButton and \
                self.rect().contains(evt.pos()):
            self.middleClicked.emit(evt.globalPos())
        else:
            super(E5ClickableLabel, self).mouseReleaseEvent(evt)
