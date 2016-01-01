# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Flash cookie manager.
"""

from __future__ import unicode_literals

try:
    str = unicode       # __IGNORE_EXCEPTION__
except NameError:
    pass

import shutil

from PyQt5.QtCore import QObject, QTimer, QDir, QFileInfo, QFile

from .FlashCookie import FlashCookie
from .FlashCookieReader import FlashCookieReader, FlashCookieReaderError

import Helpviewer.HelpWindow

import Preferences


class FlashCookieManager(QObject):
    """
    Class implementing the Flash cookie manager object.
    """
    RefreshInterval = 60 * 1000
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object
        @type QObject
        """
        super(FlashCookieManager, self).__init__(parent)
        
        self.__flashCookieManagerDialog = None
        self.__flashCookies = []    # list of FlashCookie
        self.__newCookiesList = []  # list of str
        self.__whitelist = []       # list of str
        self.__blacklist = []       # list of str
        
        self.__timer = QTimer(self)
        self.__timer.setInterval(FlashCookieManager.RefreshInterval)
        self.__timer.timeout.connect(self.__autoRefresh)
        
        # start the timer if needed
        self.__startStopTimer()
        
        if Preferences.getHelp("FlashCookiesDeleteOnStartExit"):
            self.__loadFlashCookies()
            self.__removeAllButWhitelisted()
    
    def shutdown(self):
        """
        Public method to perform shutdown actions.
        """
        if self.__flashCookieManagerDialog is not None:
            self.__flashCookieManagerDialog.close()
        
        if Preferences.getHelp("FlashCookiesDeleteOnStartExit"):
            self.__removeAllButWhitelisted()
    
    def setFlashCookies(self, cookies):
        """
        Public method to set the list of cached Flash cookies.
        
        @param cookies list of Flash cookies to store
        @type list of FlashCookie
        """
        self.__flashCookies = cookies[:]
    
    def flashCookies(self):
        """
        Public method to get the list of cached Flash cookies.
        
        @return list of Flash cookies
        @rtype list of FlashCookie
        """
        if not self.__flashCookies:
            self.__loadFlashCookies()
        
        return self.__flashCookies[:]
    
    def newCookiesList(self):
        """
        Public method to get the list of newly detected Flash cookies.
        
        @return list of newly detected Flash cookies
        @rtype list of str
        """
        return self.__newCookiesList[:]
    
    def clearNewOrigins(self):
        """
        Public method to clear the list of newly detected Flash cookies.
        """
        self.__newCookiesList = []
    
    def clearCache(self):
        """
        Public method to clear the list of cached Flash cookies.
        """
        self.__flashCookies = []
    
    def __isBlacklisted(self, cookie):
        """
        Private method to check for a blacklisted cookie.
        
        @param cookie Flash cookie to be tested
        @type FlashCookie
        @return flag indicating a blacklisted cookie
        @rtype bool
        """
        return cookie.origin in Preferences.getHelp("FlashCookiesBlacklist")
    
    def __isWhitelisted(self, cookie):
        """
        Private method to check for a whitelisted cookie.
        
        @param cookie Flash cookie to be tested
        @type FlashCookie
        @return flag indicating a whitelisted cookie
        @rtype bool
        """
        return cookie.origin in Preferences.getHelp("FlashCookiesWhitelist")
    
    def __removeAllButWhitelisted(self):
        """
        Private method to remove all non-whitelisted cookies.
        """
        for cookie in self.__flashCookies[:]:
            if not self.__isWhitelisted(cookie):
                self.removeCookie(cookie)
    
    def __sharedObjectDirName(self):
        """
        Private slot to determine the path of the shared data objects.
        
        @return path of the shared data objects
        @rtype str
        """
        if "macromedia" in self.flashPlayerDataPath().lower() or \
                "/.gnash" not in self.flashPlayerDataPath().lower():
            return "/#SharedObjects/"
        else:
            return "/SharedObjects/"
    
    def flashPlayerDataPath(self):
        """
        Public method to get the Flash Player data path.
        
        @return Flash Player data path
        @rtype str
        """
        return Preferences.getHelp("FlashCookiesDataPath")
    
    def preferencesChanged(self):
        """
        Public slot to handle a change of preferences.
        """
        self.__startStopTimer()
    
    def removeCookie(self, cookie):
        """
        Public method to remove a cookie of the list of cached cookies.
        
        @param cookie Flash cookie to be removed
        @type FlashCookie
        """
        if cookie in self.__flashCookies:
            self.__flashCookies.remove(cookie)
            shutil.rmtree(cookie.path, True)
    
    def __autoRefresh(self):
        """
        Private slot to refresh the list of cookies.
        """
        if self.__flashCookieManagerDialog and \
                self.__flashCookieManagerDialog.isVisible():
            return
        
        oldFlashCookies = self.__flashCookies[:]
        self.__loadFlashCookies()
        newCookieList = []
        
        for cookie in self.__flashCookies[:]:
            if self.__isBlacklisted(cookie):
                self.removeCookie(cookie)
                continue
            
            if self.__isWhitelisted(cookie):
                continue
            
            newCookie = True
            for oldCookie in oldFlashCookies:
                if (oldCookie.path + oldCookie.name ==
                        cookie.path + cookie.name):
                    newCookie = False
                    break
            
            if newCookie:
                newCookieList.append(cookie.path + "/" + cookie.name)
        
        if newCookieList and Preferences.getHelp("FlashCookieNotify"):
            self.__newCookiesList.extend(newCookieList)
            win = Helpviewer.HelpWindow.HelpWindow.mainWindow()
            if win is None:
                return
            
            view = win.currentBrowser()
            if view is None:
                return
            
            from .FlashCookieNotification import FlashCookieNotification
            notification = FlashCookieNotification(
                view, self, len(newCookieList))
            notification.show()
    
    def showFlashCookieManagerDialog(self):
        """
        Public method to show the Flash cookies management dialog.
        """
        if self.__flashCookieManagerDialog is None:
            from .FlashCookieManagerDialog import FlashCookieManagerDialog
            self.__flashCookieManagerDialog = FlashCookieManagerDialog(self)
        
        self.__flashCookieManagerDialog.refreshView()
        self.__flashCookieManagerDialog.showPage(0)
        self.__flashCookieManagerDialog.show()
        self.__flashCookieManagerDialog.raise_()
    
    def __startStopTimer(self):
        """
        Private slot to start or stop the auto refresh timer.
        """
        if Preferences.getHelp("FlashCookieAutoRefresh"):
            if not self.__timer.isActive():
                if not bool(self.__flashCookies):
                    self.__loadFlashCookies()
                
                self.__timer.start()
        else:
            self.__timer.stop()
    
    def __loadFlashCookies(self):
        """
        Private slot to load the Flash cookies to be cached.
        """
        self.__flashCookies = []
        self.__loadFlashCookiesFromPath(self.flashPlayerDataPath())
    
    def __loadFlashCookiesFromPath(self, path):
        """
        Private slot to load the Flash cookies from a path.
        
        @param path Flash cookies path
        @type str
        """
        if path.endswith("#AppContainer"):
            # specific to IE and Windows
            return
        
        path = path.replace("\\", "/")
        solDir = QDir(path)
        entryList = solDir.entryList()
        for entry in entryList:
            if entry == "." or entry == "..":
                continue
            entryInfo = QFileInfo(path + "/" + entry)
            if entryInfo.isDir():
                self.__loadFlashCookiesFromPath(entryInfo.filePath())
            else:
                self.__insertFlashCookie(entryInfo.filePath())
    
    def __insertFlashCookie(self, path):
        """
        Private method to insert a Flash cookie into the cache.
        
        @param path Flash cookies path
        @type str
        """
        solFile = QFile(path)
        if not solFile.open(QFile.ReadOnly):
            return
        
        dataStr = ""
        data = bytes(solFile.readAll())
        if data:
            try:
                reader = FlashCookieReader()
                reader.setBytes(data)
                reader.parse()
                dataStr = reader.toString()
            except FlashCookieReaderError as err:
                dataStr = err.msg
        
        solFileInfo = QFileInfo(solFile)
        
        cookie = FlashCookie()
        cookie.contents = dataStr
        cookie.name = solFileInfo.fileName()
        cookie.path = solFileInfo.canonicalPath()
        cookie.size = int(solFile.size())
        cookie.lastModified = solFileInfo.lastModified()
        cookie.origin = self.__extractOriginFrom(path)
        
        self.__flashCookies.append(cookie)
    
    def __extractOriginFrom(self, path):
        """
        Private method to extract the cookie origin given its file name.
        
        @param path file name of the cookie file
        @type str
        @return cookie origin
        @rtype str
        """
        origin = path
        if path.startswith(
                self.flashPlayerDataPath() + self.__sharedObjectDirName()):
            origin = origin.replace(
                self.flashPlayerDataPath() + self.__sharedObjectDirName(), "")
            if "/" in origin:
                origin = origin.split("/", 1)[1]
        elif path.startswith(
            self.flashPlayerDataPath() +
                "/macromedia.com/support/flashplayer/sys/"):
            origin = origin.replace(
                self.flashPlayerDataPath() +
                "/macromedia.com/support/flashplayer/sys/", "")
            if origin == "settings.sol":
                return self.tr("!default")
            elif origin.startswith("#"):
                origin = origin[1:]
        else:
            origin = ""
        
        index = origin.find("/")
        if index == -1:
            return self.tr("!other")
        
        origin = origin[:index]
        if origin in ["localhost", "local"]:
            origin = "!localhost"
        
        return origin
