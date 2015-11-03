# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a synchronization handler using FTP.
"""

from __future__ import unicode_literals

import ftplib
import io

from PyQt5.QtCore import pyqtSignal, QTimer, QFileInfo, QCoreApplication, \
    QByteArray

from E5Network.E5Ftp import E5Ftp, E5FtpProxyType, E5FtpProxyError

from .SyncHandler import SyncHandler

import Helpviewer.HelpWindow

import Preferences

from Utilities.FtpUtilities import FtpDirLineParser, FtpDirLineParserError


class FtpSyncHandler(SyncHandler):
    """
    Class implementing a synchronization handler using FTP.
    
    @signal syncStatus(type_, message) emitted to indicate the synchronization
        status (string one of "bookmarks", "history", "passwords",
        "useragents" or "speeddial", string)
    @signal syncError(message) emitted for a general error with the error
        message (string)
    @signal syncMessage(message) emitted to send a message about
        synchronization (string)
    @signal syncFinished(type_, done, download) emitted after a
        synchronization has finished (string one of "bookmarks", "history",
        "passwords", "useragents" or "speeddial", boolean, boolean)
    """
    syncStatus = pyqtSignal(str, str)
    syncError = pyqtSignal(str)
    syncMessage = pyqtSignal(str)
    syncFinished = pyqtSignal(str, bool, bool)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(FtpSyncHandler, self).__init__(parent)
        
        self.__state = "idle"
        self.__forceUpload = False
        self.__connected = False
        
        self.__remoteFilesFound = {}
    
    def initialLoadAndCheck(self, forceUpload):
        """
        Public method to do the initial check.
        
        @keyparam forceUpload flag indicating a forced upload of the files
            (boolean)
        """
        if not Preferences.getHelp("SyncEnabled"):
            return
        
        self.__state = "initializing"
        self.__forceUpload = forceUpload
        
        self.__dirLineParser = FtpDirLineParser()
        self.__remoteFilesFound = {}
        
        self.__idleTimer = QTimer(self)
        self.__idleTimer.setInterval(
            Preferences.getHelp("SyncFtpIdleTimeout") * 1000)
        self.__idleTimer.timeout.connect(self.__idleTimeout)
        
        self.__ftp = E5Ftp()
        
        # do proxy setup
        if not Preferences.getUI("UseProxy"):
            proxyType = E5FtpProxyType.NoProxy
        else:
            proxyType = Preferences.getUI("ProxyType/Ftp")
        if proxyType != E5FtpProxyType.NoProxy:
            self.__ftp.setProxy(
                proxyType,
                Preferences.getUI("ProxyHost/Ftp"),
                Preferences.getUI("ProxyPort/Ftp"))
            if proxyType != E5FtpProxyType.NonAuthorizing:
                self.__ftp.setProxyAuthentication(
                    Preferences.getUI("ProxyUser/Ftp"),
                    Preferences.getUI("ProxyPassword/Ftp"),
                    Preferences.getUI("ProxyAccount/Ftp"))
        
        QTimer.singleShot(0, self.__doFtpCommands)
    
    def __doFtpCommands(self):
        """
        Private slot executing the sequence of FTP commands.
        """
        try:
            ok = self.__connectAndLogin()
            if ok:
                self.__changeToStore()
                self.__ftp.retrlines("LIST", self.__dirListCallback)
                self.__initialSync()
                self.__state = "idle"
                self.__idleTimer.start()
        except (ftplib.all_errors + (E5FtpProxyError,)) as err:
            self.syncError.emit(str(err))
    
    def __connectAndLogin(self):
        """
        Private method to connect to the FTP server and log in.
        
        @return flag indicating a successful log in (boolean)
        """
        self.__ftp.connect(
            Preferences.getHelp("SyncFtpServer"),
            Preferences.getHelp("SyncFtpPort"),
            timeout=5)
        self.__ftp.login(
            Preferences.getHelp("SyncFtpUser"),
            Preferences.getHelp("SyncFtpPassword"))
        self.__connected = True
        return True
    
    def __changeToStore(self):
        """
        Private slot to change to the storage directory.
        
        This action will create the storage path on the server, if it
        does not exist. Upon return, the current directory of the server
        is the sync directory.
        """
        storePathList = \
            Preferences.getHelp("SyncFtpPath").replace("\\", "/").split("/")
        if storePathList[0] == "":
            storePathList.pop(0)
        while storePathList:
            path = storePathList[0]
            try:
                self.__ftp.cwd(path)
            except ftplib.error_perm as err:
                code = err.args[0].strip()[:3]
                if code == "550":
                    # path does not exist, create it
                    self.__ftp.mkd(path)
                    self.__ftp.cwd(path)
                else:
                    raise
            storePathList.pop(0)
    
    def __dirListCallback(self, line):
        """
        Private slot handling the receipt of directory listing lines.
        
        @param line the received line of the directory listing (string)
        """
        try:
            urlInfo = self.__dirLineParser.parseLine(line)
        except FtpDirLineParserError:
            # silently ignore parser errors
            urlInfo = None
        
        if urlInfo and urlInfo.isValid() and urlInfo.isFile():
            if urlInfo.name() in self._remoteFiles.values():
                self.__remoteFilesFound[urlInfo.name()] = \
                    urlInfo.lastModified()
        
        QCoreApplication.processEvents()
    
    def __downloadFile(self, type_, fileName, timestamp):
        """
        Private method to downlaod the given file.
        
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords", "useragents" or
            "speeddial")
        @param fileName name of the file to be downloaded (string)
        @param timestamp time stamp in seconds of the file to be downloaded
            (integer)
        """
        self.syncStatus.emit(type_, self._messages[type_]["RemoteExists"])
        buffer = io.BytesIO()
        try:
            self.__ftp.retrbinary(
                "RETR {0}".format(self._remoteFiles[type_]),
                lambda x: self.__downloadFileCallback(buffer, x))
            ok, error = self.writeFile(
                QByteArray(buffer.getvalue()), fileName, type_, timestamp)
            if not ok:
                self.syncStatus.emit(type_, error)
            self.syncFinished.emit(type_, ok, True)
        except ftplib.all_errors as err:
            self.syncStatus.emit(type_, str(err))
            self.syncFinished.emit(type_, False, True)
    
    def __downloadFileCallback(self, buffer, data):
        """
        Private method receiving the downloaded data.
        
        @param buffer reference to the buffer (io.BytesIO)
        @param data byte string to store in the buffer (bytes)
        @return number of bytes written to the buffer (integer)
        """
        res = buffer.write(data)
        QCoreApplication.processEvents()
        return res
    
    def __uploadFile(self, type_, fileName):
        """
        Private method to upload the given file.
        
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords", "useragents" or
            "speeddial")
        @param fileName name of the file to be uploaded (string)
        @return flag indicating success (boolean)
        """
        res = False
        data = self.readFile(fileName, type_)
        if data.isEmpty():
            self.syncStatus.emit(type_, self._messages[type_]["LocalMissing"])
            self.syncFinished.emit(type_, False, False)
        else:
            buffer = io.BytesIO(data.data())
            try:
                self.__ftp.storbinary(
                    "STOR {0}".format(self._remoteFiles[type_]),
                    buffer,
                    callback=lambda x: QCoreApplication.processEvents())
                self.syncFinished.emit(type_, True, False)
                res = True
            except ftplib.all_errors as err:
                self.syncStatus.emit(type_, str(err))
                self.syncFinished.emit(type_, False, False)
        return res
    
    def __initialSyncFile(self, type_, fileName):
        """
        Private method to do the initial synchronization of the given file.
        
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords", "useragents" or
            "speeddial")
        @param fileName name of the file to be synchronized (string)
        """
        if not self.__forceUpload and \
           self._remoteFiles[type_] in self.__remoteFilesFound:
            if QFileInfo(fileName).lastModified() < \
               self.__remoteFilesFound[self._remoteFiles[type_]]:
                self.__downloadFile(
                    type_, fileName,
                    self.__remoteFilesFound[self._remoteFiles[type_]]
                        .toTime_t())
            else:
                self.syncStatus.emit(
                    type_, self.tr("No synchronization required."))
                self.syncFinished.emit(type_, True, True)
        else:
            if self._remoteFiles[type_] not in self.__remoteFilesFound:
                self.syncStatus.emit(
                    type_, self._messages[type_]["RemoteMissing"])
            else:
                self.syncStatus.emit(
                    type_, self._messages[type_]["LocalNewer"])
            self.__uploadFile(type_, fileName)
    
    def __initialSync(self):
        """
        Private slot to do the initial synchronization.
        """
        # Bookmarks
        if Preferences.getHelp("SyncBookmarks"):
            self.__initialSyncFile(
                "bookmarks",
                Helpviewer.HelpWindow.HelpWindow.bookmarksManager()
                .getFileName())
        
        # History
        if Preferences.getHelp("SyncHistory"):
            self.__initialSyncFile(
                "history",
                Helpviewer.HelpWindow.HelpWindow.historyManager()
                .getFileName())
        
        # Passwords
        if Preferences.getHelp("SyncPasswords"):
            self.__initialSyncFile(
                "passwords",
                Helpviewer.HelpWindow.HelpWindow.passwordManager()
                .getFileName())
        
        # User Agent Settings
        if Preferences.getHelp("SyncUserAgents"):
            self.__initialSyncFile(
                "useragents",
                Helpviewer.HelpWindow.HelpWindow.userAgentsManager()
                .getFileName())
        
        # Speed Dial Settings
        if Preferences.getHelp("SyncSpeedDial"):
            self.__initialSyncFile(
                "speeddial",
                Helpviewer.HelpWindow.HelpWindow.speedDial().getFileName())
        
        self.__forceUpload = False
    
    def __syncFile(self, type_, fileName):
        """
        Private method to synchronize the given file.
        
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords", "useragents" or
            "speeddial")
        @param fileName name of the file to be synchronized (string)
        """
        if self.__state == "initializing":
            return
        
        # use idle timeout to check, if we are still connected
        if self.__connected:
            self.__idleTimeout()
        if not self.__connected or self.__ftp.sock is None:
            ok = self.__connectAndLogin()
            if not ok:
                self.syncStatus.emit(
                    type_, self.tr("Cannot log in to FTP host."))
                return
        
        # upload the changed file
        self.__state = "uploading"
        self.syncStatus.emit(type_, self._messages[type_]["Uploading"])
        if self.__uploadFile(type_, fileName):
            self.syncStatus.emit(
                type_, self.tr("Synchronization finished."))
        self.__state = "idle"
    
    def syncBookmarks(self):
        """
        Public method to synchronize the bookmarks.
        """
        self.__syncFile(
            "bookmarks",
            Helpviewer.HelpWindow.HelpWindow.bookmarksManager().getFileName())
    
    def syncHistory(self):
        """
        Public method to synchronize the history.
        """
        self.__syncFile(
            "history",
            Helpviewer.HelpWindow.HelpWindow.historyManager().getFileName())
    
    def syncPasswords(self):
        """
        Public method to synchronize the passwords.
        """
        self.__syncFile(
            "passwords",
            Helpviewer.HelpWindow.HelpWindow.passwordManager().getFileName())
    
    def syncUserAgents(self):
        """
        Public method to synchronize the user agents.
        """
        self.__syncFile(
            "useragents",
            Helpviewer.HelpWindow.HelpWindow.userAgentsManager().getFileName())
    
    def syncSpeedDial(self):
        """
        Public method to synchronize the speed dial data.
        """
        self.__syncFile(
            "speeddial",
            Helpviewer.HelpWindow.HelpWindow.speedDial().getFileName())
    
    def shutdown(self):
        """
        Public method to shut down the handler.
        """
        if self.__idleTimer.isActive():
            self.__idleTimer.stop()
        
        try:
            if self.__connected:
                self.__ftp.quit()
        except ftplib.all_errors:
            pass    # ignore FTP errors because we are shutting down anyway
        self.__connected = False
    
    def __idleTimeout(self):
        """
        Private slot to prevent a disconnect from the server.
        """
        if self.__state == "idle" and self.__connected:
            try:
                self.__ftp.voidcmd("NOOP")
            except ftplib.Error as err:
                code = err.args[0].strip()[:3]
                if code == "421":
                    self.__connected = False
            except IOError:
                self.__connected = False
