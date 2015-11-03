# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to add RSS feeds.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QDialog, QPushButton, QLabel

from E5Gui import E5MessageBox

from .Ui_FeedsDialog import Ui_FeedsDialog

import UI.PixmapCache


class FeedsDialog(QDialog, Ui_FeedsDialog):
    """
    Class documentation goes here.
    """
    def __init__(self, availableFeeds, browser, parent=None):
        """
        Constructor
        
        @param availableFeeds list of available RSS feeds (list of tuple of
            two strings)
        @param browser reference to the browser widget (HelpBrowser)
        @param parent reference to the parent widget (QWidget)
        """
        super(FeedsDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.iconLabel.setPixmap(UI.PixmapCache.getPixmap("rss48.png"))
        
        self.__browser = browser
        
        self.__availableFeeds = availableFeeds[:]
        for row in range(len(self.__availableFeeds)):
            feed = self.__availableFeeds[row]
            button = QPushButton(self)
            button.setText(self.tr("Add"))
            button.feed = feed
            label = QLabel(self)
            label.setText(feed[0])
            self.feedsLayout.addWidget(label, row, 0)
            self.feedsLayout.addWidget(button, row, 1)
            button.clicked.connect(self.__addFeed)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    def __addFeed(self):
        """
        Private slot to add a RSS feed.
        """
        button = self.sender()
        urlString = button.feed[1]
        url = QUrl(urlString)
        if not url.host():
            if not urlString.startswith("/"):
                urlString = "/" + urlString
            urlString = self.__browser.url().host() + urlString
            tmpUrl = QUrl(urlString)
            if not tmpUrl.scheme():
                urlString = "http://" + urlString
            tmpUrl = QUrl(urlString)
            if not tmpUrl.scheme() or not tmpUrl.host():
                return
        if not url.isValid():
            return
        
        if button.feed[0]:
            title = button.feed[0]
        else:
            title = self.__browser.url().host()
        
        import Helpviewer.HelpWindow
        feedsManager = Helpviewer.HelpWindow.HelpWindow.feedsManager()
        if feedsManager.addFeed(urlString, title, self.__browser.icon()):
            if Helpviewer.HelpWindow.HelpWindow.notificationsEnabled():
                Helpviewer.HelpWindow.HelpWindow.showNotification(
                    UI.PixmapCache.getPixmap("rss48.png"),
                    self.tr("Add RSS Feed"),
                    self.tr("""The feed was added successfully."""))
            else:
                E5MessageBox.information(
                    self,
                    self.tr("Add RSS Feed"),
                    self.tr("""The feed was added successfully."""))
        else:
            E5MessageBox.warning(
                self,
                self.tr("Add RSS Feed"),
                self.tr("""The feed was already added before."""))
            
        self.close()
