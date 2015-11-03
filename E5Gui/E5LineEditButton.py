# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a button class to be used with E5LineEdit.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtGui import QPainter, QPainterPath
from PyQt5.QtWidgets import QAbstractButton


class E5LineEditButton(QAbstractButton):
    """
    Class implementing a button to be used with E5LineEdit.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(E5LineEditButton, self).__init__(parent)
        
        self.__menu = None
        self.__image = None
        
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.ArrowCursor)
        self.setMinimumSize(16, 16)
        
        self.clicked.connect(self.__clicked)
    
    def setMenu(self, menu):
        """
        Public method to set the button menu.
        
        @param menu reference to the menu (QMenu)
        """
        self.__menu = menu
        self.update()
    
    def menu(self):
        """
        Public method to get a reference to the menu.
        
        @return reference to the associated menu (QMenu)
        """
        return self.__menu
    
    def setIcon(self, icon):
        """
        Public method to set the button icon.
        
        @param icon icon to be set (QIcon)
        """
        if icon.isNull():
            self.__image = None
        else:
            self.__image = icon.pixmap(16, 16).toImage()
        super(E5LineEditButton, self).setIcon(icon)
    
    def __clicked(self):
        """
        Private slot to handle a button click.
        """
        if self.__menu:
            pos = self.mapToGlobal(QPoint(0, self.height()))
            self.__menu.exec_(pos)
    
    def paintEvent(self, evt):
        """
        Protected method handling a paint event.
        
        @param evt reference to the paint event (QPaintEvent)
        """
        painter = QPainter(self)
        
        if self.__image is not None and not self.__image.isNull():
            x = (self.width() - self.__image.width()) // 2 - 1
            y = (self.height() - self.__image.height()) // 2 - 1
            painter.drawImage(x, y, self.__image)
        
        if self.__menu is not None:
            triagPath = QPainterPath()
            startPos = QPointF(self.width() - 5, self.height() - 3)
            triagPath.moveTo(startPos)
            triagPath.lineTo(startPos.x() + 4, startPos.y())
            triagPath.lineTo(startPos.x() + 2, startPos.y() + 2)
            triagPath.closeSubpath()
            painter.setPen(Qt.black)
            painter.setBrush(Qt.black)
            painter.setRenderHint(QPainter.Antialiasing, False)
            painter.drawPath(triagPath)
