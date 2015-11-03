# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing dialog-like popup that displays messages without
interrupting the user.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QPoint, QRect
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QApplication


class E5PassivePopup(QFrame):
    """
    Class implementing dialog-like popup that displays messages without
    interrupting the user.
    """
    Boxed = 0
    Custom = 128
    
    clicked = pyqtSignal((), (QPoint, ))
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(E5PassivePopup, self).__init__(None)
        
        self.__popupStyle = DEFAULT_POPUP_TYPE
        self.__msgView = None
        self.__topLayout = None
        self.__hideDelay = DEFAULT_POPUP_TIME
        self.__hideTimer = QTimer(self)
        self.__autoDelete = False
        self.__fixedPosition = QPoint()
        
        self.setWindowFlags(POPUP_FLAGS)
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setLineWidth(2)
        self.__hideTimer.timeout.connect(self.hide)
        self.clicked.connect(self.hide)
    
    def setView(self, child):
        """
        Public method to set the message view.
        
        @param child reference to the widget to set as the message view
            (QWidget)
        """
        self.__msgView = child
        self.__topLayout = QVBoxLayout(self)
        self.__topLayout.addWidget(self.__msgView)
        self.__topLayout.activate()
    
    def view(self):
        """
        Public method to get a reference to the message view.
        
        @return reference to the message view (QWidget)
        """
        return self.__msgView
    
    def setVisible(self, visible):
        """
        Public method to show or hide the popup.
        
        @param visible flag indicating the visibility status (boolean)
        """
        if not visible:
            super(E5PassivePopup, self).setVisible(visible)
            return
        
        if self.size() != self.sizeHint():
            self.resize(self.sizeHint())
        
        if self.__fixedPosition.isNull():
            self.__positionSelf()
        else:
            self.move(self.__fixedPosition)
        super(E5PassivePopup, self).setVisible(True)
        
        delay = self.__hideDelay
        if delay < 0:
            delay = DEFAULT_POPUP_TIME
        if delay > 0:
            self.__hideTimer.start(delay)
    
    def show(self, p=None):
        """
        Public slot to show the popup.
        
        @param p position for the popup (QPoint)
        """
        if p is not None:
            self.__fixedPosition = p
        super(E5PassivePopup, self).show()
    
    def setTimeout(self, delay):
        """
        Public method to set the delay for the popup is removed automatically.
        
        Setting the delay to 0 disables the timeout. If you're doing this, you
        may want to connect the clicked() signal to the hide() slot. Setting
        the delay to -1 makes it use the default value.
        
        @param delay value for the delay in milliseconds (integer)
        """
        self.__hideDelay = delay
        if self.__hideTimer.isActive():
            if delay:
                if delay == -1:
                    delay = DEFAULT_POPUP_TIME
                self.__hideTimer.start(delay)
            else:
                self.__hideTimer.stop()
    
    def timeout(self):
        """
        Public method to get the delay before the popup is removed
        automatically.
        
        @return the delay before the popup is removed automatically (integer)
        """
        return self.__hideDelay
    
    def mouseReleaseEvent(self, evt):
        """
        Protected method to handle a mouse release event.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        self.clicked.emit()
        self.clicked.emit(evt.pos())
    
    def hideEvent(self, evt):
        """
        Protected method to handle the hide event.
        
        @param evt reference to the hide event (QHideEvent)
        """
        self.__hideTimer.stop()
    
    def __defaultArea(self):
        """
        Private method to determine the default rectangle to be passed to
        moveNear().
        
        @return default rectangle (QRect)
        """
        return QRect(100, 100, 200, 200)
    
    def __positionSelf(self):
        """
        Private method to position the popup.
        """
        self.__moveNear(self.__defaultArea())
    
    def __moveNear(self, target):
        """
        Private method to move the popup to be adjacent to the specified
        rectangle.
        
        @param target rectangle to be placed at (QRect)
        """
        pos = self.__calculateNearbyPoint(target)
        self.move(pos.x(), pos.y())
    
    def __calculateNearbyPoint(self, target):
        """
        Private method to calculate the position to place the popup near the
        specified rectangle.
        
        @param target rectangle to be placed at (QRect)
        @return position to place the popup (QPoint)
        """
        pos = target.topLeft()
        x = pos.x()
        y = pos.y()
        w = self.minimumSizeHint().width()
        h = self.minimumSizeHint().height()
        
        r = QApplication.desktop().screenGeometry(
            QPoint(x + w // 2, y + h // 2))
        
        if x < r.center().x():
            x += target.width()
        else:
            x -= w
        
        # It's apparently trying to go off screen, so display it ALL at the
        # bottom.
        if (y + h) > r.bottom():
            y = r.bottom() - h
        
        if (x + w) > r.right():
            x = r.right() - w
        
        if y < r.top():
            y = r.top()
        
        if x < r.left():
            x = r.left()
        
        return QPoint(x, y)

DEFAULT_POPUP_TYPE = E5PassivePopup.Boxed
DEFAULT_POPUP_TIME = 6 * 1000
POPUP_FLAGS = Qt.WindowFlags(
    Qt.Tool | Qt.X11BypassWindowManagerHint |
    Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
