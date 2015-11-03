# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a specialized tab bar for the web browser.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QPoint, QTimer, QEvent
from PyQt5.QtWidgets import QFrame, QLabel

from E5Gui.E5TabWidget import E5WheelTabBar
from E5Gui.E5PassivePopup import E5PassivePopup

import Preferences


class HelpTabBar(E5WheelTabBar):
    """
    Class implementing the tab bar of the web browser.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (HelpTabWidget)
        """
        E5WheelTabBar.__init__(self, parent)
        
        self.__tabWidget = parent
        
        self.__previewPopup = None
        self.__currentTabPreviewIndex = -1
        
        self.setMouseTracking(True)
    
    def __showTabPreview(self):
        """
        Private slot to show the tab preview.
        """
        indexedBrowser = self.__tabWidget.browserAt(
            self.__currentTabPreviewIndex)
        currentBrowser = self.__tabWidget.currentBrowser()
        
        if indexedBrowser is None or currentBrowser is None:
            return
        
        # no previews during load
        if indexedBrowser.progress() != 0:
            return
        
        w = self.tabSizeHint(self.__currentTabPreviewIndex).width()
        h = int(w * currentBrowser.height() / currentBrowser.width())
        
        self.__previewPopup = E5PassivePopup(self)
        self.__previewPopup.setFrameShape(QFrame.StyledPanel)
        self.__previewPopup.setFrameShadow(QFrame.Plain)
        self.__previewPopup.setFixedSize(w, h)
        
        from .HelpSnap import renderTabPreview
        label = QLabel()
        label.setPixmap(renderTabPreview(indexedBrowser.page(), w, h))
        
        self.__previewPopup.setView(label)
        self.__previewPopup.layout().setAlignment(Qt.AlignTop)
        self.__previewPopup.layout().setContentsMargins(0, 0, 0, 0)
        
        tr = self.tabRect(self.__currentTabPreviewIndex)
        pos = QPoint(tr.x(), tr.y() + tr.height())
        
        self.__previewPopup.show(self.mapToGlobal(pos))
    
    def mouseMoveEvent(self, evt):
        """
        Protected method to handle mouse move events.
        
        @param evt reference to the mouse move event (QMouseEvent)
        """
        if self.count() == 1:
            return
        
        E5WheelTabBar.mouseMoveEvent(self, evt)
        
        if Preferences.getHelp("ShowPreview"):
            # Find the tab under the mouse
            i = 0
            tabIndex = -1
            while i < self.count() and tabIndex == -1:
                if self.tabRect(i).contains(evt.pos()):
                    tabIndex = i
                i += 1
            
            # If found and not the current tab then show tab preview
            if tabIndex != -1 and \
               tabIndex != self.currentIndex() and \
               self.__currentTabPreviewIndex != tabIndex and \
               evt.buttons() == Qt.NoButton:
                self.__currentTabPreviewIndex = tabIndex
                QTimer.singleShot(200, self.__showTabPreview)
            
            # If current tab or not found then hide previous tab preview
            if tabIndex == self.currentIndex() or \
               tabIndex == -1:
                if self.__previewPopup is not None:
                    self.__previewPopup.hide()
                self.__currentTabPreviewIndex = -1
    
    def leaveEvent(self, evt):
        """
        Protected method to handle leave events.
        
        @param evt reference to the leave event (QEvent)
        """
        if Preferences.getHelp("ShowPreview"):
            # If leave tabwidget then hide previous tab preview
            if self.__previewPopup is not None:
                self.__previewPopup.hide()
            self.__currentTabPreviewIndex = -1
        
        E5WheelTabBar.leaveEvent(self, evt)
    
    def mousePressEvent(self, evt):
        """
        Protected method to handle mouse press events.
        
        @param evt reference to the mouse press event (QMouseEvent)
        """
        if Preferences.getHelp("ShowPreview"):
            if self.__previewPopup is not None:
                self.__previewPopup.hide()
            self.__currentTabPreviewIndex = -1
        
        E5WheelTabBar.mousePressEvent(self, evt)
    
    def event(self, evt):
        """
        Public method to handle event.
        
        This event handler just handles the tooltip event and passes the
        handling of all others to the superclass.
        
        @param evt reference to the event to be handled (QEvent)
        @return flag indicating, if the event was handled (boolean)
        """
        if evt.type() == QEvent.ToolTip and \
           Preferences.getHelp("ShowPreview"):
            # suppress tool tips if we are showing previews
            evt.setAccepted(True)
            return True
        
        return E5WheelTabBar.event(self, evt)
    
    def tabRemoved(self, index):
        """
        Public slot to handle the removal of a tab.
        
        @param index index of the removed tab (integer)
        """
        if Preferences.getHelp("ShowPreview"):
            if self.__previewPopup is not None:
                self.__previewPopup.hide()
            self.__currentTabPreviewIndex = -1
