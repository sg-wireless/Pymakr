# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the label to show the web site icon.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

from PyQt5.QtCore import Qt, QPoint, QUrl, QMimeData
from PyQt5.QtGui import QDrag, QPixmap
from PyQt5.QtWidgets import QLabel, QApplication


class FavIconLabel(QLabel):
    """
    Class implementing the label to show the web site icon.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(FavIconLabel, self).__init__(parent)
        
        self.__browser = None
        self.__dragStartPos = QPoint()
        
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.ArrowCursor)
        self.setMinimumSize(16, 16)
        self.resize(16, 16)
        
        self.__browserIconChanged()
    
    def __browserIconChanged(self):
        """
        Private slot to set the icon.
        """
        import Helpviewer.HelpWindow
        try:
            url = QUrl()
            if self.__browser:
                url = self.__browser.url()
            self.setPixmap(
                Helpviewer.HelpWindow.HelpWindow.icon(url).pixmap(16, 16))
        except RuntimeError:
            pass
    
    def __clearIcon(self):
        """
        Private slot to clear the icon.
        """
        self.setPixmap(QPixmap())
    
    def setBrowser(self, browser):
        """
        Public method to set the browser connection.
        
        @param browser reference to the browser widegt (HelpBrowser)
        """
        self.__browser = browser
        self.__browser.loadFinished.connect(self.__browserIconChanged)
        self.__browser.iconChanged.connect(self.__browserIconChanged)
        self.__browser.loadStarted.connect(self.__clearIcon)
    
    def mousePressEvent(self, evt):
        """
        Protected method to handle mouse press events.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        if evt.button() == Qt.LeftButton:
            self.__dragStartPos = evt.pos()
        super(FavIconLabel, self).mousePressEvent(evt)
    
    def mouseMoveEvent(self, evt):
        """
        Protected method to handle mouse move events.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        if evt.button() == Qt.LeftButton and \
           (evt.pos() - self.__dragStartPos).manhattanLength() > \
                QApplication.startDragDistance() and \
           self.__browser is not None:
            drag = QDrag(self)
            mimeData = QMimeData()
            title = self.__browser.title()
            if title == "":
                title = str(self.__browser.url().toEncoded(), encoding="utf-8")
            mimeData.setText(title)
            mimeData.setUrls([self.__browser.url()])
            p = self.pixmap()
            if p:
                drag.setPixmap(p)
            drag.setMimeData(mimeData)
            drag.exec_()
