# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a sidebar class.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QEvent, QSize, Qt, QByteArray, QDataStream, \
    QIODevice, QTimer, qVersion
from PyQt5.QtWidgets import QTabBar, QWidget, QStackedWidget, QBoxLayout, \
    QToolButton, QSizePolicy

from E5Gui.E5Application import e5App

import UI.PixmapCache


class E5SideBar(QWidget):
    """
    Class implementing a sidebar with a widget area, that is hidden or shown,
    if the current tab is clicked again.
    """
    Version = 1
    
    North = 0
    East = 1
    South = 2
    West = 3
    
    def __init__(self, orientation=None, delay=200, parent=None):
        """
        Constructor
        
        @param orientation orientation of the sidebar widget (North, East,
            South, West)
        @param delay value for the expand/shrink delay in milliseconds
            (integer)
        @param parent parent widget (QWidget)
        """
        super(E5SideBar, self).__init__(parent)
        
        self.__tabBar = QTabBar()
        self.__tabBar.setDrawBase(True)
        self.__tabBar.setShape(QTabBar.RoundedNorth)
        self.__tabBar.setUsesScrollButtons(True)
        self.__tabBar.setDrawBase(False)
        self.__stackedWidget = QStackedWidget(self)
        self.__stackedWidget.setContentsMargins(0, 0, 0, 0)
        self.__autoHideButton = QToolButton()
        self.__autoHideButton.setCheckable(True)
        self.__autoHideButton.setIcon(
            UI.PixmapCache.getIcon("autoHideOff.png"))
        self.__autoHideButton.setChecked(True)
        self.__autoHideButton.setToolTip(
            self.tr("Deselect to activate automatic collapsing"))
        self.barLayout = QBoxLayout(QBoxLayout.LeftToRight)
        self.barLayout.setContentsMargins(0, 0, 0, 0)
        self.layout = QBoxLayout(QBoxLayout.TopToBottom)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.barLayout.addWidget(self.__autoHideButton)
        self.barLayout.addWidget(self.__tabBar)
        self.layout.addLayout(self.barLayout)
        self.layout.addWidget(self.__stackedWidget)
        self.setLayout(self.layout)
        
        # initialize the delay timer
        self.__actionMethod = None
        self.__delayTimer = QTimer(self)
        self.__delayTimer.setSingleShot(True)
        self.__delayTimer.setInterval(delay)
        self.__delayTimer.timeout.connect(self.__delayedAction)
        
        self.__minimized = False
        self.__minSize = 0
        self.__maxSize = 0
        self.__bigSize = QSize()
        
        self.splitter = None
        self.splitterSizes = []
        
        self.__hasFocus = False
        # flag storing if this widget or any child has the focus
        self.__autoHide = False
        
        self.__tabBar.installEventFilter(self)
        
        self.__orientation = E5SideBar.North
        if orientation is None:
            orientation = E5SideBar.North
        self.setOrientation(orientation)
        
        self.__tabBar.currentChanged[int].connect(
            self.__stackedWidget.setCurrentIndex)
        e5App().focusChanged[QWidget, QWidget].connect(self.__appFocusChanged)
        self.__autoHideButton.toggled[bool].connect(self.__autoHideToggled)
    
    def setSplitter(self, splitter):
        """
        Public method to set the splitter managing the sidebar.
        
        @param splitter reference to the splitter (QSplitter)
        """
        self.splitter = splitter
        self.splitter.splitterMoved.connect(self.__splitterMoved)
        self.splitter.setChildrenCollapsible(False)
        index = self.splitter.indexOf(self)
        self.splitter.setCollapsible(index, False)
    
    def __splitterMoved(self, pos, index):
        """
        Private slot to react on splitter moves.
        
        @param pos new position of the splitter handle (integer)
        @param index index of the splitter handle (integer)
        """
        if self.splitter:
            self.splitterSizes = self.splitter.sizes()
    
    def __delayedAction(self):
        """
        Private slot to handle the firing of the delay timer.
        """
        if self.__actionMethod is not None:
            self.__actionMethod()
    
    def setDelay(self, delay):
        """
        Public method to set the delay value for the expand/shrink delay in
        milliseconds.
        
        @param delay value for the expand/shrink delay in milliseconds
            (integer)
        """
        self.__delayTimer.setInterval(delay)
    
    def delay(self):
        """
        Public method to get the delay value for the expand/shrink delay in
        milliseconds.
        
        @return value for the expand/shrink delay in milliseconds (integer)
        """
        return self.__delayTimer.interval()
    
    def __cancelDelayTimer(self):
        """
        Private method to cancel the current delay timer.
        """
        self.__delayTimer.stop()
        self.__actionMethod = None
    
    def shrink(self):
        """
        Public method to record a shrink request.
        """
        self.__delayTimer.stop()
        self.__actionMethod = self.__shrinkIt
        self.__delayTimer.start()
   
    def __shrinkIt(self):
        """
        Private method to shrink the sidebar.
        """
        self.__minimized = True
        self.__bigSize = self.size()
        if self.__orientation in [E5SideBar.North, E5SideBar.South]:
            self.__minSize = self.minimumSizeHint().height()
            self.__maxSize = self.maximumHeight()
        else:
            self.__minSize = self.minimumSizeHint().width()
            self.__maxSize = self.maximumWidth()
        if self.splitter:
            self.splitterSizes = self.splitter.sizes()
        
        self.__stackedWidget.hide()
        
        if self.__orientation in [E5SideBar.North, E5SideBar.South]:
            self.setFixedHeight(self.__tabBar.minimumSizeHint().height())
        else:
            self.setFixedWidth(self.__tabBar.minimumSizeHint().width())
        
        self.__actionMethod = None
    
    def expand(self):
        """
        Public method to record a expand request.
        """
        self.__delayTimer.stop()
        self.__actionMethod = self.__expandIt
        self.__delayTimer.start()
    
    def __expandIt(self):
        """
        Private method to expand the sidebar.
        """
        self.__minimized = False
        self.__stackedWidget.show()
        self.resize(self.__bigSize)
        if self.__orientation in [E5SideBar.North, E5SideBar.South]:
            minSize = max(self.__minSize, self.minimumSizeHint().height())
            self.setMinimumHeight(minSize)
            self.setMaximumHeight(self.__maxSize)
        else:
            minSize = max(self.__minSize, self.minimumSizeHint().width())
            self.setMinimumWidth(minSize)
            self.setMaximumWidth(self.__maxSize)
        if self.splitter:
            self.splitter.setSizes(self.splitterSizes)
        
        self.__actionMethod = None
    
    def isMinimized(self):
        """
        Public method to check the minimized state.
        
        @return flag indicating the minimized state (boolean)
        """
        return self.__minimized
    
    def isAutoHiding(self):
        """
        Public method to check, if the auto hide function is active.
        
        @return flag indicating the state of auto hiding (boolean)
        """
        return self.__autoHide
    
    def eventFilter(self, obj, evt):
        """
        Public method to handle some events for the tabbar.
        
        @param obj reference to the object (QObject)
        @param evt reference to the event object (QEvent)
        @return flag indicating, if the event was handled (boolean)
        """
        if obj == self.__tabBar:
            if evt.type() == QEvent.MouseButtonPress:
                pos = evt.pos()
                for i in range(self.__tabBar.count()):
                    if self.__tabBar.tabRect(i).contains(pos):
                        break
                
                if i == self.__tabBar.currentIndex():
                    if self.isMinimized():
                        self.expand()
                    else:
                        self.shrink()
                    return True
                elif self.isMinimized():
                    self.expand()
            elif evt.type() == QEvent.Wheel:
                if qVersion() >= "5.0.0":
                    delta = evt.angleDelta().y()
                else:
                    delta = evt.delta()
                if delta > 0:
                    self.prevTab()
                else:
                    self.nextTab()
                return True
        
        return QWidget.eventFilter(self, obj, evt)
    
    def addTab(self, widget, iconOrLabel, label=None):
        """
        Public method to add a tab to the sidebar.
        
        @param widget reference to the widget to add (QWidget)
        @param iconOrLabel reference to the icon or the label text of the tab
            (QIcon, string)
        @param label the labeltext of the tab (string) (only to be
            used, if the second parameter is a QIcon)
        """
        if label:
            index = self.__tabBar.addTab(iconOrLabel, label)
            self.__tabBar.setTabToolTip(index, label)
        else:
            index = self.__tabBar.addTab(iconOrLabel)
            self.__tabBar.setTabToolTip(index, iconOrLabel)
        self.__stackedWidget.addWidget(widget)
        if self.__orientation in [E5SideBar.North, E5SideBar.South]:
            self.__minSize = self.minimumSizeHint().height()
        else:
            self.__minSize = self.minimumSizeHint().width()
    
    def insertTab(self, index, widget, iconOrLabel, label=None):
        """
        Public method to insert a tab into the sidebar.
        
        @param index the index to insert the tab at (integer)
        @param widget reference to the widget to insert (QWidget)
        @param iconOrLabel reference to the icon or the labeltext of the tab
            (QIcon, string)
        @param label the labeltext of the tab (string) (only to be
            used, if the second parameter is a QIcon)
        """
        if label:
            index = self.__tabBar.insertTab(index, iconOrLabel, label)
            self.__tabBar.setTabToolTip(index, label)
        else:
            index = self.__tabBar.insertTab(index, iconOrLabel)
            self.__tabBar.setTabToolTip(index, iconOrLabel)
        self.__stackedWidget.insertWidget(index, widget)
        if self.__orientation in [E5SideBar.North, E5SideBar.South]:
            self.__minSize = self.minimumSizeHint().height()
        else:
            self.__minSize = self.minimumSizeHint().width()
    
    def removeTab(self, index):
        """
        Public method to remove a tab.
        
        @param index the index of the tab to remove (integer)
        """
        self.__stackedWidget.removeWidget(self.__stackedWidget.widget(index))
        self.__tabBar.removeTab(index)
        if self.__orientation in [E5SideBar.North, E5SideBar.South]:
            self.__minSize = self.minimumSizeHint().height()
        else:
            self.__minSize = self.minimumSizeHint().width()
    
    def clear(self):
        """
        Public method to remove all tabs.
        """
        while self.count() > 0:
            self.removeTab(0)
    
    def prevTab(self):
        """
        Public slot used to show the previous tab.
        """
        ind = self.currentIndex() - 1
        if ind == -1:
            ind = self.count() - 1
            
        self.setCurrentIndex(ind)
        self.currentWidget().setFocus()
    
    def nextTab(self):
        """
        Public slot used to show the next tab.
        """
        ind = self.currentIndex() + 1
        if ind == self.count():
            ind = 0
            
        self.setCurrentIndex(ind)
        self.currentWidget().setFocus()
    
    def count(self):
        """
        Public method to get the number of tabs.
        
        @return number of tabs in the sidebar (integer)
        """
        return self.__tabBar.count()
    
    def currentIndex(self):
        """
        Public method to get the index of the current tab.
        
        @return index of the current tab (integer)
        """
        return self.__stackedWidget.currentIndex()
    
    def setCurrentIndex(self, index):
        """
        Public slot to set the current index.
        
        @param index the index to set as the current index (integer)
        """
        self.__tabBar.setCurrentIndex(index)
        self.__stackedWidget.setCurrentIndex(index)
        if self.isMinimized():
            self.expand()
    
    def currentWidget(self):
        """
        Public method to get a reference to the current widget.
        
        @return reference to the current widget (QWidget)
        """
        return self.__stackedWidget.currentWidget()
    
    def setCurrentWidget(self, widget):
        """
        Public slot to set the current widget.
        
        @param widget reference to the widget to become the current widget
            (QWidget)
        """
        self.__stackedWidget.setCurrentWidget(widget)
        self.__tabBar.setCurrentIndex(self.__stackedWidget.currentIndex())
        if self.isMinimized():
            self.expand()
    
    def indexOf(self, widget):
        """
        Public method to get the index of the given widget.
        
        @param widget reference to the widget to get the index of (QWidget)
        @return index of the given widget (integer)
        """
        return self.__stackedWidget.indexOf(widget)
    
    def isTabEnabled(self, index):
        """
        Public method to check, if a tab is enabled.
        
        @param index index of the tab to check (integer)
        @return flag indicating the enabled state (boolean)
        """
        return self.__tabBar.isTabEnabled(index)
    
    def setTabEnabled(self, index, enabled):
        """
        Public method to set the enabled state of a tab.
        
        @param index index of the tab to set (integer)
        @param enabled enabled state to set (boolean)
        """
        self.__tabBar.setTabEnabled(index, enabled)
    
    def orientation(self):
        """
        Public method to get the orientation of the sidebar.
        
        @return orientation of the sidebar (North, East, South, West)
        """
        return self.__orientation
    
    def setOrientation(self, orient):
        """
        Public method to set the orientation of the sidebar.

        @param orient orientation of the sidebar (North, East, South, West)
        """
        if orient == E5SideBar.North:
            self.__tabBar.setShape(QTabBar.RoundedNorth)
            self.__tabBar.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.barLayout.setDirection(QBoxLayout.LeftToRight)
            self.layout.setDirection(QBoxLayout.TopToBottom)
            self.layout.setAlignment(self.barLayout, Qt.AlignLeft)
        elif orient == E5SideBar.East:
            self.__tabBar.setShape(QTabBar.RoundedEast)
            self.__tabBar.setSizePolicy(
                QSizePolicy.Preferred, QSizePolicy.Expanding)
            self.barLayout.setDirection(QBoxLayout.TopToBottom)
            self.layout.setDirection(QBoxLayout.RightToLeft)
            self.layout.setAlignment(self.barLayout, Qt.AlignTop)
        elif orient == E5SideBar.South:
            self.__tabBar.setShape(QTabBar.RoundedSouth)
            self.__tabBar.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.barLayout.setDirection(QBoxLayout.LeftToRight)
            self.layout.setDirection(QBoxLayout.BottomToTop)
            self.layout.setAlignment(self.barLayout, Qt.AlignLeft)
        elif orient == E5SideBar.West:
            self.__tabBar.setShape(QTabBar.RoundedWest)
            self.__tabBar.setSizePolicy(
                QSizePolicy.Preferred, QSizePolicy.Expanding)
            self.barLayout.setDirection(QBoxLayout.TopToBottom)
            self.layout.setDirection(QBoxLayout.LeftToRight)
            self.layout.setAlignment(self.barLayout, Qt.AlignTop)
        self.__orientation = orient
    
    def tabIcon(self, index):
        """
        Public method to get the icon of a tab.
        
        @param index index of the tab (integer)
        @return icon of the tab (QIcon)
        """
        return self.__tabBar.tabIcon(index)
    
    def setTabIcon(self, index, icon):
        """
        Public method to set the icon of a tab.
        
        @param index index of the tab (integer)
        @param icon icon to be set (QIcon)
        """
        self.__tabBar.setTabIcon(index, icon)
    
    def tabText(self, index):
        """
        Public method to get the text of a tab.
        
        @param index index of the tab (integer)
        @return text of the tab (string)
        """
        return self.__tabBar.tabText(index)
    
    def setTabText(self, index, text):
        """
        Public method to set the text of a tab.
        
        @param index index of the tab (integer)
        @param text text to set (string)
        """
        self.__tabBar.setTabText(index, text)
    
    def tabToolTip(self, index):
        """
        Public method to get the tooltip text of a tab.
        
        @param index index of the tab (integer)
        @return tooltip text of the tab (string)
        """
        return self.__tabBar.tabToolTip(index)
    
    def setTabToolTip(self, index, tip):
        """
        Public method to set the tooltip text of a tab.
        
        @param index index of the tab (integer)
        @param tip tooltip text to set (string)
        """
        self.__tabBar.setTabToolTip(index, tip)
    
    def tabWhatsThis(self, index):
        """
        Public method to get the WhatsThis text of a tab.
        
        @param index index of the tab (integer)
        @return WhatsThis text of the tab (string)
        """
        return self.__tabBar.tabWhatsThis(index)
    
    def setTabWhatsThis(self, index, text):
        """
        Public method to set the WhatsThis text of a tab.
        
        @param index index of the tab (integer)
        @param text WhatsThis text to set (string)
        """
        self.__tabBar.setTabWhatsThis(index, text)
    
    def widget(self, index):
        """
        Public method to get a reference to the widget associated with a tab.
        
        @param index index of the tab (integer)
        @return reference to the widget (QWidget)
        """
        return self.__stackedWidget.widget(index)
    
    def saveState(self):
        """
        Public method to save the state of the sidebar.
        
        @return saved state as a byte array (QByteArray)
        """
        if len(self.splitterSizes) == 0:
            if self.splitter:
                self.splitterSizes = self.splitter.sizes()
            self.__bigSize = self.size()
            if self.__orientation in [E5SideBar.North, E5SideBar.South]:
                self.__minSize = self.minimumSizeHint().height()
                self.__maxSize = self.maximumHeight()
            else:
                self.__minSize = self.minimumSizeHint().width()
                self.__maxSize = self.maximumWidth()
        
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)
        stream.setVersion(QDataStream.Qt_4_6)
        
        stream.writeUInt16(self.Version)
        stream.writeBool(self.__minimized)
        stream << self.__bigSize
        stream.writeUInt16(self.__minSize)
        stream.writeUInt16(self.__maxSize)
        stream.writeUInt16(len(self.splitterSizes))
        for size in self.splitterSizes:
            stream.writeUInt16(size)
        stream.writeBool(self.__autoHide)
        
        return data
    
    def restoreState(self, state):
        """
        Public method to restore the state of the sidebar.
        
        @param state byte array containing the saved state (QByteArray)
        @return flag indicating success (boolean)
        """
        if state.isEmpty():
            return False
        
        if self.__orientation in [E5SideBar.North, E5SideBar.South]:
            minSize = self.layout.minimumSize().height()
            maxSize = self.maximumHeight()
        else:
            minSize = self.layout.minimumSize().width()
            maxSize = self.maximumWidth()
        
        data = QByteArray(state)
        stream = QDataStream(data, QIODevice.ReadOnly)
        stream.setVersion(QDataStream.Qt_4_6)
        stream.readUInt16()  # version
        minimized = stream.readBool()
        
        if minimized and not self.__minimized:
            self.shrink()
        
        stream >> self.__bigSize
        self.__minSize = max(stream.readUInt16(), minSize)
        self.__maxSize = max(stream.readUInt16(), maxSize)
        count = stream.readUInt16()
        self.splitterSizes = []
        for i in range(count):
            self.splitterSizes.append(stream.readUInt16())
        
        self.__autoHide = stream.readBool()
        self.__autoHideButton.setChecked(not self.__autoHide)
        
        if not minimized:
            self.expand()
        
        return True
    
    #######################################################################
    ## methods below implement the autohide functionality
    #######################################################################
    
    def __autoHideToggled(self, checked):
        """
        Private slot to handle the toggling of the autohide button.
        
        @param checked flag indicating the checked state of the button
            (boolean)
        """
        self.__autoHide = not checked
        if self.__autoHide:
            self.__autoHideButton.setIcon(
                UI.PixmapCache.getIcon("autoHideOn.png"))
        else:
            self.__autoHideButton.setIcon(
                UI.PixmapCache.getIcon("autoHideOff.png"))
    
    def __appFocusChanged(self, old, now):
        """
        Private slot to handle a change of the focus.
        
        @param old reference to the widget, that lost focus (QWidget or None)
        @param now reference to the widget having the focus (QWidget or None)
        """
        self.__hasFocus = self.isAncestorOf(now)
        if self.__autoHide and not self.__hasFocus and not self.isMinimized():
            self.shrink()
        elif self.__autoHide and self.__hasFocus and self.isMinimized():
            self.expand()
    
    def enterEvent(self, event):
        """
        Protected method to handle the mouse entering this widget.
        
        @param event reference to the event (QEvent)
        """
        if self.__autoHide and self.isMinimized():
            self.expand()
        else:
            self.__cancelDelayTimer()
    
    def leaveEvent(self, event):
        """
        Protected method to handle the mouse leaving this widget.
        
        @param event reference to the event (QEvent)
        """
        if self.__autoHide and not self.__hasFocus and not self.isMinimized():
            self.shrink()
        else:
            self.__cancelDelayTimer()
    
    def shutdown(self):
        """
        Public method to shut down the object.
        
        This method does some preparations so the object can be deleted
        properly. It disconnects from the focusChanged signal in order to
        avoid trouble later on.
        """
        e5App().focusChanged[QWidget, QWidget].disconnect(
            self.__appFocusChanged)
