# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the synchronization manager class.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject, pyqtSignal

import Preferences

import Helpviewer.HelpWindow


class SyncManager(QObject):
    """
    Class implementing the synchronization manager.
    
    @signal syncError(message) emitted for a general error with the error
        message (string)
    @signal syncMessage(message) emitted to give status info about the sync
        process (string)
    @signal syncStatus(type_, message) emitted to indicate the synchronization
        status (string one of "bookmarks", "history", "passwords",
        "useragents" or "speeddial", string)
    @signal syncFinished(type_, done, download) emitted after a
        synchronization has finished (string one of "bookmarks", "history",
        "passwords", "useragents" or "speeddial", boolean, boolean)
    """
    syncError = pyqtSignal(str)
    syncMessage = pyqtSignal(str)
    syncStatus = pyqtSignal(str, str)
    syncFinished = pyqtSignal(str, bool, bool)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(SyncManager, self).__init__(parent)
        
        self.__handler = None
    
    def handler(self):
        """
        Public method to get a reference to the sync handler object.
        
        @return reference to the sync handler object (SyncHandler)
        """
        return self.__handler
    
    def showSyncDialog(self):
        """
        Public method to show the synchronization dialog.
        """
        from .SyncAssistantDialog import SyncAssistantDialog
        dlg = SyncAssistantDialog()
        dlg.exec_()
    
    def loadSettings(self, forceUpload=False):
        """
        Public method to load the settings.
        
        @keyparam forceUpload flag indicating a forced upload of the files
            (boolean)
        """
        if self.__handler is not None:
            self.__handler.syncError.disconnect(self.__syncError)
            self.__handler.syncFinished.disconnect(self.__syncFinished)
            self.__handler.syncStatus.disconnect(self.__syncStatus)
            self.__handler.syncMessage.disconnect(self.syncMessage)
            self.__handler.shutdown()
        
        if self.syncEnabled():
            from . import SyncGlobals
            if Preferences.getHelp("SyncType") == SyncGlobals.SyncTypeFtp:
                from .FtpSyncHandler import FtpSyncHandler
                self.__handler = FtpSyncHandler(self)
            elif Preferences.getHelp("SyncType") == \
                    SyncGlobals.SyncTypeDirectory:
                from .DirectorySyncHandler import DirectorySyncHandler
                self.__handler = DirectorySyncHandler(self)
            self.__handler.syncError.connect(self.__syncError)
            self.__handler.syncFinished.connect(self.__syncFinished)
            self.__handler.syncStatus.connect(self.__syncStatus)
            self.__handler.syncMessage.connect(self.syncMessage)
            
            self.__handler.initialLoadAndCheck(forceUpload=forceUpload)
            
            # connect sync manager to bookmarks manager
            if Preferences.getHelp("SyncBookmarks"):
                Helpviewer.HelpWindow.HelpWindow.bookmarksManager()\
                    .bookmarksSaved.connect(self.__syncBookmarks)
            else:
                try:
                    Helpviewer.HelpWindow.HelpWindow.bookmarksManager()\
                        .bookmarksSaved.disconnect(self.__syncBookmarks)
                except TypeError:
                    pass
            
            # connect sync manager to history manager
            if Preferences.getHelp("SyncHistory"):
                Helpviewer.HelpWindow.HelpWindow.historyManager().historySaved\
                    .connect(self.__syncHistory)
            else:
                try:
                    Helpviewer.HelpWindow.HelpWindow.historyManager()\
                        .historySaved.disconnect(self.__syncHistory)
                except TypeError:
                    pass
            
            # connect sync manager to passwords manager
            if Preferences.getHelp("SyncPasswords"):
                Helpviewer.HelpWindow.HelpWindow.passwordManager()\
                    .passwordsSaved.connect(self.__syncPasswords)
            else:
                try:
                    Helpviewer.HelpWindow.HelpWindow.passwordManager()\
                        .passwordsSaved.disconnect(self.__syncPasswords)
                except TypeError:
                    pass
            
            # connect sync manager to user agent manager
            if Preferences.getHelp("SyncUserAgents"):
                Helpviewer.HelpWindow.HelpWindow.userAgentsManager()\
                    .userAgentSettingsSaved.connect(self.__syncUserAgents)
            else:
                try:
                    Helpviewer.HelpWindow.HelpWindow.userAgentsManager()\
                        .userAgentSettingsSaved.disconnect(
                            self.__syncUserAgents)
                except TypeError:
                    pass
            
            # connect sync manager to speed dial
            if Preferences.getHelp("SyncSpeedDial"):
                Helpviewer.HelpWindow.HelpWindow.speedDial()\
                    .speedDialSaved.connect(self.__syncSpeedDial)
            else:
                try:
                    Helpviewer.HelpWindow.HelpWindow.speedDial()\
                        .speedDialSaved.disconnect(self.__syncSpeedDial)
                except TypeError:
                    pass
        else:
            self.__handler = None
            
            try:
                Helpviewer.HelpWindow.HelpWindow.bookmarksManager()\
                    .bookmarksSaved.disconnect(self.__syncBookmarks)
            except TypeError:
                pass
            try:
                Helpviewer.HelpWindow.HelpWindow.historyManager().historySaved\
                    .disconnect(self.__syncHistory)
            except TypeError:
                pass
            try:
                Helpviewer.HelpWindow.HelpWindow.passwordManager()\
                    .passwordsSaved.disconnect(self.__syncPasswords)
            except TypeError:
                pass
            try:
                Helpviewer.HelpWindow.HelpWindow.userAgentsManager()\
                    .userAgentSettingsSaved.disconnect(self.__syncUserAgents)
            except TypeError:
                pass
            try:
                Helpviewer.HelpWindow.HelpWindow.speedDial()\
                    .speedDialSaved.disconnect(self.__syncSpeedDial)
            except TypeError:
                pass
    
    def syncEnabled(self):
        """
        Public method to check, if synchronization is enabled.
        
        @return flag indicating enabled synchronization
        """
        from . import SyncGlobals
        return Preferences.getHelp("SyncEnabled") and \
            Preferences.getHelp("SyncType") != SyncGlobals.SyncTypeNone
    
    def __syncBookmarks(self):
        """
        Private slot to synchronize the bookmarks.
        """
        if self.__handler is not None:
            self.__handler.syncBookmarks()
    
    def __syncHistory(self):
        """
        Private slot to synchronize the history.
        """
        if self.__handler is not None:
            self.__handler.syncHistory()
    
    def __syncPasswords(self):
        """
        Private slot to synchronize the passwords.
        """
        if self.__handler is not None:
            self.__handler.syncPasswords()
    
    def __syncUserAgents(self):
        """
        Private slot to synchronize the user agent settings.
        """
        if self.__handler is not None:
            self.__handler.syncUserAgents()
    
    def __syncSpeedDial(self):
        """
        Private slot to synchronize the speed dial settings.
        """
        if self.__handler is not None:
            self.__handler.syncSpeedDial()
    
    def __syncError(self, message):
        """
        Private slot to handle general synchronization issues.
        
        @param message error message (string)
        """
        self.syncError.emit(message)
    
    def __syncFinished(self, type_, status, download):
        """
        Private slot to handle a finished synchronization event.
        
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords", "useragents" or
            "speeddial")
        @param status flag indicating success (boolean)
        @param download flag indicating a download of a file (boolean)
        """
        if status and download:
            if type_ == "bookmarks":
                Helpviewer.HelpWindow.HelpWindow.bookmarksManager().reload()
            elif type_ == "history":
                Helpviewer.HelpWindow.HelpWindow.historyManager().reload()
            elif type_ == "passwords":
                Helpviewer.HelpWindow.HelpWindow.passwordManager().reload()
            elif type_ == "useragents":
                Helpviewer.HelpWindow.HelpWindow.userAgentsManager().reload()
            elif type_ == "speeddial":
                Helpviewer.HelpWindow.HelpWindow.speedDial().reload()
        self.syncFinished.emit(type_, status, download)
    
    def __syncStatus(self, type_, message):
        """
        Private slot to handle a status update of a synchronization event.
        
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords", "useragents" or
            "speeddial")
        @param message status message for the event (string)
        """
        self.syncMessage.emit(message)
        self.syncStatus.emit(type_, message)
    
    def close(self):
        """
        Public slot to shut down the synchronization manager.
        """
        if not self.syncEnabled():
            return
        
        if self.__handler is not None:
            self.__handler.shutdown()
