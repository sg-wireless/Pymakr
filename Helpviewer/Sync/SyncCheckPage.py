# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the synchronization status wizard page.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QByteArray, QTimer
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QWizardPage

from . import SyncGlobals

from .Ui_SyncCheckPage import Ui_SyncCheckPage

import Preferences
import UI.PixmapCache

from eric6config import getConfig


class SyncCheckPage(QWizardPage, Ui_SyncCheckPage):
    """
    Class implementing the synchronization status wizard page.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(SyncCheckPage, self).__init__(parent)
        self.setupUi(self)
    
    def initializePage(self):
        """
        Public method to initialize the page.
        """
        self.syncErrorLabel.hide()
        
        forceUpload = self.field("ReencryptData")
        
        import Helpviewer.HelpWindow
        syncMgr = Helpviewer.HelpWindow.HelpWindow.syncManager()
        syncMgr.syncError.connect(self.__syncError)
        syncMgr.syncStatus.connect(self.__updateMessages)
        syncMgr.syncFinished.connect(self.__updateLabels)
        
        if Preferences.getHelp("SyncType") == SyncGlobals.SyncTypeFtp:
            self.handlerLabel.setText(self.tr("FTP"))
            self.infoLabel.setText(self.tr("Host:"))
            self.infoDataLabel.setText(Preferences.getHelp("SyncFtpServer"))
        elif Preferences.getHelp("SyncType") == SyncGlobals.SyncTypeDirectory:
            self.handlerLabel.setText(self.tr("Shared Directory"))
            self.infoLabel.setText(self.tr("Directory:"))
            self.infoDataLabel.setText(
                Preferences.getHelp("SyncDirectoryPath"))
        else:
            self.handlerLabel.setText(self.tr("No Synchronization"))
            self.hostLabel.setText("")
        
        self.bookmarkMsgLabel.setText("")
        self.historyMsgLabel.setText("")
        self.passwordsMsgLabel.setText("")
        self.userAgentsMsgLabel.setText("")
        self.speedDialMsgLabel.setText("")
        
        if not syncMgr.syncEnabled():
            self.bookmarkLabel.setPixmap(
                UI.PixmapCache.getPixmap("syncNo.png"))
            self.historyLabel.setPixmap(UI.PixmapCache.getPixmap("syncNo.png"))
            self.passwordsLabel.setPixmap(
                UI.PixmapCache.getPixmap("syncNo.png"))
            self.userAgentsLabel.setPixmap(
                UI.PixmapCache.getPixmap("syncNo.png"))
            self.speedDialLabel.setPixmap(
                UI.PixmapCache.getPixmap("syncNo.png"))
            return
        
        animationFile = os.path.join(getConfig("ericPixDir"), "loading.gif")
        
        # bookmarks
        if Preferences.getHelp("SyncBookmarks"):
            self.__makeAnimatedLabel(animationFile, self.bookmarkLabel)
        else:
            self.bookmarkLabel.setPixmap(
                UI.PixmapCache.getPixmap("syncNo.png"))
        
        # history
        if Preferences.getHelp("SyncHistory"):
            self.__makeAnimatedLabel(animationFile, self.historyLabel)
        else:
            self.historyLabel.setPixmap(UI.PixmapCache.getPixmap("syncNo.png"))
        
        # Passwords
        if Preferences.getHelp("SyncPasswords"):
            self.__makeAnimatedLabel(animationFile, self.passwordsLabel)
        else:
            self.passwordsLabel.setPixmap(
                UI.PixmapCache.getPixmap("syncNo.png"))
        
        # user agent settings
        if Preferences.getHelp("SyncUserAgents"):
            self.__makeAnimatedLabel(animationFile, self.userAgentsLabel)
        else:
            self.userAgentsLabel.setPixmap(
                UI.PixmapCache.getPixmap("syncNo.png"))
        
        # speed dial settings
        if Preferences.getHelp("SyncSpeedDial"):
            self.__makeAnimatedLabel(animationFile, self.speedDialLabel)
        else:
            self.speedDialLabel.setPixmap(
                UI.PixmapCache.getPixmap("syncNo.png"))
        
        QTimer.singleShot(
            0, lambda: syncMgr.loadSettings(forceUpload=forceUpload))
    
    def __makeAnimatedLabel(self, fileName, label):
        """
        Private slot to create an animated label.
        
        @param fileName name of the file containing the animation (string)
        @param label reference to the label to be animated (QLabel)
        """
        movie = QMovie(fileName, QByteArray(), label)
        movie.setSpeed(100)
        label.setMovie(movie)
        movie.start()
    
    def __updateMessages(self, type_, msg):
        """
        Private slot to update the synchronization status info.
        
        @param type_ type of synchronization data (string)
        @param msg synchronization message (string)
        """
        if type_ == "bookmarks":
            self.bookmarkMsgLabel.setText(msg)
        elif type_ == "history":
            self.historyMsgLabel.setText(msg)
        elif type_ == "passwords":
            self.passwordsMsgLabel.setText(msg)
        elif type_ == "useragents":
            self.userAgentsMsgLabel.setText(msg)
        elif type_ == "speeddial":
            self.speedDialMsgLabel.setText(msg)
    
    def __updateLabels(self, type_, status, download):
        """
        Private slot to handle a finished synchronization event.
        
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords", "useragents" or
            "speeddial")
        @param status flag indicating success (boolean)
        @param download flag indicating a download of a file (boolean)
        """
        if type_ == "bookmarks":
            if status:
                self.bookmarkLabel.setPixmap(
                    UI.PixmapCache.getPixmap("syncCompleted.png"))
            else:
                self.bookmarkLabel.setPixmap(
                    UI.PixmapCache.getPixmap("syncFailed.png"))
        elif type_ == "history":
            if status:
                self.historyLabel.setPixmap(
                    UI.PixmapCache.getPixmap("syncCompleted.png"))
            else:
                self.historyLabel.setPixmap(
                    UI.PixmapCache.getPixmap("syncFailed.png"))
        elif type_ == "passwords":
            if status:
                self.passwordsLabel.setPixmap(
                    UI.PixmapCache.getPixmap("syncCompleted.png"))
            else:
                self.passwordsLabel.setPixmap(
                    UI.PixmapCache.getPixmap("syncFailed.png"))
        elif type_ == "useragents":
            if status:
                self.userAgentsLabel.setPixmap(
                    UI.PixmapCache.getPixmap("syncCompleted.png"))
            else:
                self.userAgentsLabel.setPixmap(
                    UI.PixmapCache.getPixmap("syncFailed.png"))
        elif type_ == "speeddial":
            if status:
                self.speedDialLabel.setPixmap(
                    UI.PixmapCache.getPixmap("syncCompleted.png"))
            else:
                self.speedDialLabel.setPixmap(
                    UI.PixmapCache.getPixmap("syncFailed.png"))
    
    def __syncError(self, message):
        """
        Private slot to handle general synchronization issues.
        
        @param message error message (string)
        """
        self.syncErrorLabel.show()
        self.syncErrorLabel.setText(self.tr(
            '<font color="#FF0000"><b>Error:</b> {0}</font>').format(message))
