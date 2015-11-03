# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the snapshot timer widget.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QRect
from PyQt5.QtGui import QPainter, QPalette
from PyQt5.QtWidgets import QWidget, QApplication, QToolTip


class SnapshotTimer(QWidget):
    """
    Class implementing the snapshot timer widget.
    
    @signal timeout() emitted after the timer timed out
    """
    timeout = pyqtSignal()
    
    def __init__(self):
        """
        Constructor
        """
        super(SnapshotTimer, self).__init__(None)
        
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint |
                            Qt.X11BypassWindowManagerHint)
        
        self.__timer = QTimer()
        self.__textRect = QRect()
        self.__time = 0
        self.__length = 0
        self.__toggle = True
        
        # text is taken from paintEvent with maximum number plus some margin
        self.resize(
            self.fontMetrics().width(self.tr(
                "Snapshot will be taken in %n seconds", "", 99)) + 6,
            self.fontMetrics().height() + 4)
        
        self.__timer.timeout.connect(self.__bell)
    
    def start(self, seconds):
        """
        Public method to start the timer.
        
        @param seconds timeout value (integer)
        """
        screenGeom = QApplication.desktop().screenGeometry()
        self.move(screenGeom.width() // 2 - self.size().width() // 2,
                  screenGeom.top())
        self.__toggle = True
        self.__time = 0
        self.__length = seconds
        self.__timer.start(1000)
        self.show()
    
    def stop(self):
        """
        Public method to stop the timer.
        """
        self.setVisible(False)
        self.hide()
        self.__timer.stop()
    
    def __bell(self):
        """
        Private slot handling timer timeouts.
        """
        if self.__time == self.__length - 1:
            self.hide()
        else:
            if self.__time == self.__length:
                self.__timer.stop()
                self.timeout.emit()
        
        self.__time += 1
        self.__toggle = not self.__toggle
        self.update()
    
    def paintEvent(self, evt):
        """
        Protected method handling paint events.
        
        @param evt paint event (QPaintEvent)
        """
        painter = QPainter(self)
        
        if self.__time < self.__length:
            pal = QToolTip.palette()
            textBackgroundColor = pal.color(QPalette.Active, QPalette.Base)
            if self.__toggle:
                textColor = pal.color(QPalette.Active, QPalette.Text)
            else:
                textColor = pal.color(QPalette.Active, QPalette.Base)
            painter.setPen(textColor)
            painter.setBrush(textBackgroundColor)
            helpText = self.tr("Snapshot will be taken in %n seconds", "",
                               self.__length - self.__time)
            textRect = painter.boundingRect(
                self.rect().adjusted(2, 2, -2, -2),
                Qt.AlignHCenter | Qt.TextSingleLine, helpText)
            painter.drawText(textRect, Qt.AlignHCenter | Qt.TextSingleLine,
                             helpText)
    
    def enterEvent(self, evt):
        """
        Protected method handling the mouse cursor entering the widget.
        
        @param evt enter event (QEvent)
        """
        screenGeom = QApplication.desktop().screenGeometry()
        if self.x() == screenGeom.left():
            self.move(
                screenGeom.x() +
                (screenGeom.width() // 2 - self.size().width() // 2),
                screenGeom.top())
        else:
            self.move(screenGeom.topLeft())
