# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a Notification widget.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget

from .Ui_NotificationWidget import Ui_NotificationWidget

import Globals


class NotificationWidget(QWidget, Ui_NotificationWidget):
    """
    Class implementing a Notification widget.
    """
    def __init__(self, parent=None, setPosition=False):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        @param setPosition flag indicating to set the display
            position interactively (boolean)
        """
        super(NotificationWidget, self).__init__(parent)
        self.setupUi(self)
        
        self.__timeout = 5000
        self.__icon = QPixmap()
        self.__heading = ""
        self.__text = ""
        self.__dragPosition = QPoint()
        
        self.__settingPosition = setPosition
        
        flags = Qt.Tool | \
            Qt.FramelessWindowHint | \
            Qt.WindowStaysOnTopHint | \
            Qt.X11BypassWindowManagerHint
        if Globals.isWindowsPlatform():
            flags |= Qt.ToolTip
        self.setWindowFlags(flags)
        
        self.frame.layout().setAlignment(
            self.verticalLayout, Qt.AlignLeft | Qt.AlignVCenter)
        
        self.__timer = QTimer(self)
        self.__timer.setSingleShot(True)
        self.__timer.timeout.connect(self.close)
        
        if self.__settingPosition:
            self.setCursor(Qt.OpenHandCursor)
    
    def setPixmap(self, icon):
        """
        Public method to set the icon for the notification.
        
        @param icon icon to be used (QPixmap)
        """
        self.__icon = QPixmap(icon)
    
    def setHeading(self, heading):
        """
        Public method to set the heading for the notification.
        
        @param heading heading to be used (string)
        """
        self.__heading = heading
    
    def setText(self, text):
        """
        Public method to set the text for the notification.
        
        @param text text to be used (string)
        """
        self.__text = text
    
    def setTimeout(self, timeout):
        """
        Public method to set the timeout for the notification.
        
        @param timeout timeout to be used in seconds (integer)
        """
        self.__timeout = timeout * 1000
    
    def show(self):
        """
        Public method to show the notification.
        """
        self.icon.setPixmap(self.__icon)
        self.heading.setText(self.__heading)
        self.text.setText(self.__text)
        
        if not self.__settingPosition:
            self.__timer.stop()
            self.__timer.setInterval(self.__timeout)
            self.__timer.start()
        
        super(NotificationWidget, self).show()
        
        sh = self.sizeHint()
        self.resize(max(self.width(), sh.width()), sh.height())
    
    def mousePressEvent(self, evt):
        """
        Protected method to handle presses of a mouse button.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        if not self.__settingPosition:
            self.close()
            return
        
        if evt.button() == Qt.LeftButton:
            self.__dragPosition = \
                evt.globalPos() - self.frameGeometry().topLeft()
            self.setCursor(Qt.ClosedHandCursor)
            evt.accept()
    
    def mouseReleaseEvent(self, evt):
        """
        Protected method to handle releases of a mouse button.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        if self.__settingPosition and evt.button() == Qt.LeftButton:
            self.setCursor(Qt.OpenHandCursor)
    
    def mouseMoveEvent(self, evt):
        """
        Protected method to handle dragging the window.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        if evt.buttons() & Qt.LeftButton:
            self.move(evt.globalPos() - self.__dragPosition)
            evt.accept()
