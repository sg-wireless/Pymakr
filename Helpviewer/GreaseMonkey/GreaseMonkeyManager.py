# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the manager for GreaseMonkey scripts.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSignal, QObject, QTimer, QFile, QDir, QSettings, \
    QUrl, QByteArray
from PyQt5.QtNetwork import QNetworkAccessManager

import Utilities
import Preferences


class GreaseMonkeyManager(QObject):
    """
    Class implementing the manager for GreaseMonkey scripts.
    """
    scriptsChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(GreaseMonkeyManager, self).__init__(parent)
        
        self.__disabledScripts = []
        self.__endScripts = []
        self.__startScripts = []
        self.__downloaders = []
        
        QTimer.singleShot(0, self.__load)
    
    def showConfigurationDialog(self, parent=None):
        """
        Public method to show the configuration dialog.
        
        @param parent reference to the parent widget (QWidget)
        """
        from .GreaseMonkeyConfiguration.GreaseMonkeyConfigurationDialog \
            import GreaseMonkeyConfigurationDialog
        self.__configDiaolg = GreaseMonkeyConfigurationDialog(self, parent)
        self.__configDiaolg.show()
    
    def downloadScript(self, request):
        """
        Public method to download a GreaseMonkey script.
        
        @param request reference to the request (QNetworkRequest)
        """
        from .GreaseMonkeyDownloader import GreaseMonkeyDownloader
        downloader = GreaseMonkeyDownloader(request, self)
        downloader.finished.connect(self.__downloaderFinished)
        self.__downloaders.append(downloader)
    
    def __downloaderFinished(self):
        """
        Private slot to handle the completion of a script download.
        """
        downloader = self.sender()
        if downloader is None or downloader not in self.__downloaders:
            return
        
        self.__downloaders.remove(downloader)
    
    def scriptsDirectory(self):
        """
        Public method to get the path of the scripts directory.
        
        @return path of the scripts directory (string)
        """
        return os.path.join(
            Utilities.getConfigDir(), "browser", "greasemonkey")
    
    def requireScriptsDirectory(self):
        """
        Public method to get the path of the scripts directory.
        
        @return path of the scripts directory (string)
        """
        return os.path.join(self.scriptsDirectory(), "requires")
    
    def requireScripts(self, urlList):
        """
        Public method to get the sources of all required scripts.
        
        @param urlList list of URLs (list of string)
        @return sources of all required scripts (string)
        """
        requiresDir = QDir(self.requireScriptsDirectory())
        if not requiresDir.exists() or len(urlList) == 0:
            return ""
        
        script = ""
        
        settings = QSettings(
            os.path.join(self.requireScriptsDirectory(), "requires.ini"),
            QSettings.IniFormat)
        settings.beginGroup("Files")
        for url in urlList:
            if settings.contains(url):
                fileName = settings.value(url)
                try:
                    f = open(fileName, "r", encoding="utf-8")
                    source = f.read()
                    f.close()
                except (IOError, OSError):
                    source = ""
                script += source.strip() + "\n"
        
        return script
    
    def saveConfiguration(self):
        """
        Public method to save the configuration.
        """
        Preferences.setHelp("GreaseMonkeyDisabledScripts",
                            self.__disabledScripts)
    
    def allScripts(self):
        """
        Public method to get a list of all scripts.
        
        @return list of all scripts (list of GreaseMonkeyScript)
        """
        return self.__startScripts[:] + self.__endScripts[:]
    
    def containsScript(self, fullName):
        """
        Public method to check, if the given script exists.
        
        @param fullName full name of the script (string)
        @return flag indicating the existence (boolean)
        """
        for script in self.__startScripts:
            if script.fullName() == fullName:
                return True
        for script in self.__endScripts:
            if script.fullName() == fullName:
                return True
        return False
    
    def enableScript(self, script):
        """
        Public method to enable the given script.
        
        @param script script to be enabled (GreaseMonkeyScript)
        """
        script.setEnabled(True)
        fullName = script.fullName()
        if fullName in self.__disabledScripts:
            self.__disabledScripts.remove(fullName)
    
    def disableScript(self, script):
        """
        Public method to disable the given script.
        
        @param script script to be disabled (GreaseMonkeyScript)
        """
        script.setEnabled(False)
        fullName = script.fullName()
        if fullName not in self.__disabledScripts:
            self.__disabledScripts.append(fullName)
    
    def addScript(self, script):
        """
        Public method to add a script.
        
        @param script script to be added (GreaseMonkeyScript)
        @return flag indicating success (boolean)
        """
        if not script:
            return False
        
        from .GreaseMonkeyScript import GreaseMonkeyScript
        if script.startAt() == GreaseMonkeyScript.DocumentStart:
            self.__startScripts.append(script)
        else:
            self.__endScripts.append(script)
        
        self.scriptsChanged.emit()
        return True
    
    def removeScript(self, script):
        """
        Public method to remove a script.
        
        @param script script to be removed (GreaseMonkeyScript)
        @return flag indicating success (boolean)
        """
        if not script:
            return False
        
        from .GreaseMonkeyScript import GreaseMonkeyScript
        if script.startAt() == GreaseMonkeyScript.DocumentStart:
            try:
                self.__startScripts.remove(script)
            except ValueError:
                pass
        else:
            try:
                self.__endScripts.remove(script)
            except ValueError:
                pass
        
        fullName = script.fullName()
        if fullName in self.__disabledScripts:
            self.__disabledScripts.remove(fullName)
        QFile.remove(script.fileName())
        
        self.scriptsChanged.emit()
        return True
    
    def canRunOnScheme(self, scheme):
        """
        Public method to check, if scripts can be run on a scheme.
        
        @param scheme scheme to check (string)
        @return flag indicating, that scripts can be run (boolean)
        """
        return scheme in ["http", "https", "data", "ftp"]
    
    def pageLoadStarted(self):
        """
        Public slot to handle the start of loading a page.
        """
        frame = self.sender()
        if not frame:
            return
        
        urlScheme = frame.url().scheme()
        urlString = bytes(frame.url().toEncoded()).decode()
        
        if not self.canRunOnScheme(urlScheme):
            return
        
        from .GreaseMonkeyJavaScript import bootstrap_js
        for script in self.__startScripts:
            if script.match(urlString):
                frame.evaluateJavaScript(bootstrap_js + script.script())
        
        for script in self.__endScripts:
            if script.match(urlString):
                javascript = 'window.addEventListener("DOMContentLoaded",' \
                    'function(e) {{ {0} }}, false);'.format(
                        bootstrap_js + script.script())
                frame.evaluateJavaScript(javascript)
    
    def __load(self):
        """
        Private slot to load the available scripts into the manager.
        """
        scriptsDir = QDir(self.scriptsDirectory())
        if not scriptsDir.exists():
            scriptsDir.mkpath(self.scriptsDirectory())
        
        if not scriptsDir.exists("requires"):
            scriptsDir.mkdir("requires")
        
        self.__disabledScripts = \
            Preferences.getHelp("GreaseMonkeyDisabledScripts")
        
        from .GreaseMonkeyScript import GreaseMonkeyScript
        for fileName in scriptsDir.entryList(["*.js"], QDir.Files):
            absolutePath = scriptsDir.absoluteFilePath(fileName)
            script = GreaseMonkeyScript(self, absolutePath)
            
            if script.fullName() in self.__disabledScripts:
                script.setEnabled(False)
            
            if script.startAt() == GreaseMonkeyScript.DocumentStart:
                self.__startScripts.append(script)
            else:
                self.__endScripts.append(script)
    
    def connectPage(self, page):
        """
        Public method to allow the GreaseMonkey manager to connect to the page.
        
        @param page reference to the web page (HelpWebPage)
        """
        page.mainFrame().javaScriptWindowObjectCleared.connect(
            self.pageLoadStarted)
    
    def createRequest(self, op, request, outgoingData=None):
        """
        Public method to create a request.
        
        @param op the operation to be performed
            (QNetworkAccessManager.Operation)
        @param request reference to the request object (QNetworkRequest)
        @param outgoingData reference to an IODevice containing data to be sent
            (QIODevice)
        @return reference to the created reply object (QNetworkReply)
        """
        if op == QNetworkAccessManager.GetOperation and \
           request.rawHeader(b"X-Eric6-UserLoadAction") == QByteArray(b"1"):
            urlString = request.url().toString(
                QUrl.RemoveFragment | QUrl.RemoveQuery)
            if urlString.endswith(".user.js"):
                self.downloadScript(request)
                from Helpviewer.Network.EmptyNetworkReply import \
                    EmptyNetworkReply
                return EmptyNetworkReply(self)
        
        return None
