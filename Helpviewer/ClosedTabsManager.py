# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class to manage closed tabs.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, QUrl, QObject
from PyQt5.QtWebKit import QWebSettings


class ClosedTab(object):
    """
    Class implementing a structure to store data about a closed tab.
    """
    def __init__(self, url=QUrl(), title="", position=-1):
        """
        Constructor
        
        @param url URL of the closed tab (QUrl)
        @param title title of the closed tab (string)
        @param position index of the closed tab (integer)
        """
        self.url = url
        self.title = title
        self.position = position
    
    def __eq__(self, other):
        """
        Special method implementing the equality operator.
        
        @param other reference to the object to compare against (ClosedTab)
        @return flag indicating equality of the tabs (boolean)
        """
        return self.url == other.url and \
            self.title == other.title and \
            self.position == other.position


class ClosedTabsManager(QObject):
    """
    Class implementing a manager for closed tabs.
    
    @signal closedTabAvailable(boolean) emitted to signal a change of
        availability of closed tabs
    """
    closedTabAvailable = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(ClosedTabsManager, self).__init__()
        
        self.__closedTabs = []
    
    def recordBrowser(self, browser, position):
        """
        Public method to record the data of a browser about to be closed.
        
        @param browser reference to the browser to be closed (HelpBrowser)
        @param position index of the tab to be closed (integer)
        """
        globalSettings = QWebSettings.globalSettings()
        if globalSettings.testAttribute(QWebSettings.PrivateBrowsingEnabled):
            return
        
        if browser.url().isEmpty():
            return
        
        tab = ClosedTab(browser.url(), browser.title(), position)
        self.__closedTabs.insert(0, tab)
        self.closedTabAvailable.emit(True)
    
    def getClosedTabAt(self, index):
        """
        Public method to get the indexed closed tab.
        
        @param index index of the tab to return (integer)
        @return requested tab (ClosedTab)
        """
        if len(self.__closedTabs) > 0 and len(self.__closedTabs) > index:
            tab = self.__closedTabs.pop(index)
        else:
            tab = ClosedTab()
        self.closedTabAvailable.emit(len(self.__closedTabs) > 0)
        return tab
    
    def isClosedTabAvailable(self):
        """
        Public method to check for closed tabs.
        
        @return flag indicating the availability of closed tab data (boolean)
        """
        return len(self.__closedTabs) > 0
    
    def clearList(self):
        """
        Public method to clear the list of closed tabs.
        """
        self.__closedTabs = []
        self.closedTabAvailable.emit(False)
    
    def allClosedTabs(self):
        """
        Public method to get a list of all closed tabs.
        
        @return list of closed tabs (list of ClosedTab)
        """
        return self.__closedTabs
