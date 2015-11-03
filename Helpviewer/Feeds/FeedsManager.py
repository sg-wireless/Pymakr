# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a RSS feeds manager dialog.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QUrl, QXmlStreamReader
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QDialog, QTreeWidgetItem, QMenu, QApplication
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from PyQt5.QtWebKit import QWebSettings

from E5Gui import E5MessageBox

from .Ui_FeedsManager import Ui_FeedsManager

import Preferences
import UI.PixmapCache


class FeedsManager(QDialog, Ui_FeedsManager):
    """
    Class implementing a RSS feeds manager dialog.
    
    @signal openUrl(QUrl, str) emitted to open a URL in the current tab
    @signal newUrl(QUrl, str) emitted to open a URL in a new tab
    """
    openUrl = pyqtSignal(QUrl, str)
    newUrl = pyqtSignal(QUrl, str)
    
    UrlStringRole = Qt.UserRole
    ErrorDataRole = Qt.UserRole + 1
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(FeedsManager, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.__wasShown = False
        self.__loaded = False
        self.__feeds = []
        self.__replies = {}
        # dict key is the id of the request object
        # dict value is a tuple of request and tree item
        
        self.feedsTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.feedsTree.customContextMenuRequested.connect(
            self.__customContextMenuRequested)
        self.feedsTree.itemActivated.connect(self.__itemActivated)
    
    def show(self):
        """
        Public slot to show the feeds manager dialog.
        """
        super(FeedsManager, self).show()
        
        if not self.__wasShown:
            self.__enableButtons()
            self.on_reloadAllButton_clicked()
            self.__wasShown = True
    
    def addFeed(self, urlString, title, icon):
        """
        Public method to add a feed.
        
        @param urlString URL of the feed (string)
        @param title title of the feed (string)
        @param icon icon for the feed (QIcon)
        @return flag indicating a successful addition of the feed (boolean)
        """
        if urlString == "":
            return False
        
        if not self.__loaded:
            self.__load()
        
        # step 1: check, if feed was already added
        for feed in self.__feeds:
            if feed[0] == urlString:
                return False
        
        # step 2: add the feed
        if icon.isNull() or \
                icon == QIcon(QWebSettings.webGraphic(
                    QWebSettings.DefaultFrameIconGraphic)):
            icon = UI.PixmapCache.getIcon("rss16.png")
        feed = (urlString, title, icon)
        self.__feeds.append(feed)
        self.__addFeedItem(feed)
        self.__save()
        
        return True
    
    def __addFeedItem(self, feed):
        """
        Private slot to add a top level feed item.
        
        @param feed tuple containing feed info (URL, title, icon)
            (string, string, QIcon)
        """
        itm = QTreeWidgetItem(self.feedsTree, [feed[1]])
        itm.setIcon(0, feed[2])
        itm.setData(0, FeedsManager.UrlStringRole, feed[0])
    
    def __load(self):
        """
        Private method to load the feeds data.
        """
        self.__feeds = Preferences.getHelp("RssFeeds")
        self.__loaded = True
        
        # populate the feeds tree top level with the feeds
        self.feedsTree.clear()
        for feed in self.__feeds:
            self.__addFeedItem(feed)
    
    def __save(self):
        """
        Private method to store the feeds data.
        """
        if not self.__loaded:
            self.__load()
        
        Preferences.setHelp("RssFeeds", self.__feeds)
    
    @pyqtSlot()
    def on_reloadAllButton_clicked(self):
        """
        Private slot to reload all feeds.
        """
        if not self.__loaded:
            self.__load()
        
        for index in range(self.feedsTree.topLevelItemCount()):
            itm = self.feedsTree.topLevelItem(index)
            self.__reloadFeed(itm)
    
    @pyqtSlot()
    def on_reloadButton_clicked(self):
        """
        Private slot to reload the selected feed.
        """
        itm = self.feedsTree.selectedItems()[0]
        self.__reloadFeed(itm)
    
    @pyqtSlot()
    def on_editButton_clicked(self):
        """
        Private slot to edit the selected feed.
        """
        itm = self.feedsTree.selectedItems()[0]
        origTitle = itm.text(0)
        origUrlString = itm.data(0, FeedsManager.UrlStringRole)
        
        feedToChange = None
        for feed in self.__feeds:
            if feed[0] == origUrlString:
                feedToChange = feed
                break
        if feedToChange:
            feedIndex = self.__feeds.index(feedToChange)
            
            from .FeedEditDialog import FeedEditDialog
            dlg = FeedEditDialog(origUrlString, origTitle)
            if dlg.exec_() == QDialog.Accepted:
                urlString, title = dlg.getData()
                for feed in self.__feeds:
                    if feed[0] == urlString:
                        E5MessageBox.critical(
                            self,
                            self.tr("Duplicate Feed URL"),
                            self.tr(
                                """A feed with the URL {0} exists already."""
                                """ Aborting...""".format(urlString)))
                        return
                
                self.__feeds[feedIndex] = (urlString, title, feedToChange[2])
                self.__save()
                
                itm.setText(0, title)
                itm.setData(0, FeedsManager.UrlStringRole, urlString)
                self.__reloadFeed(itm)
    
    @pyqtSlot()
    def on_deleteButton_clicked(self):
        """
        Private slot to delete the selected feed.
        """
        itm = self.feedsTree.selectedItems()[0]
        title = itm.text(0)
        res = E5MessageBox.yesNo(
            self,
            self.tr("Delete Feed"),
            self.tr(
                """<p>Do you really want to delete the feed"""
                """ <b>{0}</b>?</p>""".format(title)))
        if res:
            urlString = itm.data(0, FeedsManager.UrlStringRole)
            if urlString:
                feedToDelete = None
                for feed in self.__feeds:
                    if feed[0] == urlString:
                        feedToDelete = feed
                        break
                if feedToDelete:
                    self.__feeds.remove(feedToDelete)
                    self.__save()
                
                index = self.feedsTree.indexOfTopLevelItem(itm)
                if index != -1:
                    self.feedsTree.takeTopLevelItem(index)
                    del itm
    
    @pyqtSlot()
    def on_feedsTree_itemSelectionChanged(self):
        """
        Private slot to enable the various buttons depending on the selection.
        """
        self.__enableButtons()
    
    def __enableButtons(self):
        """
        Private slot to disable/enable various buttons.
        """
        selItems = self.feedsTree.selectedItems()
        if len(selItems) == 1 and \
           self.feedsTree.indexOfTopLevelItem(selItems[0]) != -1:
            enable = True
        else:
            enable = False
        
        self.reloadButton.setEnabled(enable)
        self.editButton.setEnabled(enable)
        self.deleteButton.setEnabled(enable)
    
    def __reloadFeed(self, itm):
        """
        Private method to reload the given feed.
        
        @param itm feed item to be reloaded (QTreeWidgetItem)
        """
        urlString = itm.data(0, FeedsManager.UrlStringRole)
        if urlString == "":
            return
        
        for child in itm.takeChildren():
            del child
        
        import Helpviewer.HelpWindow
        request = QNetworkRequest(QUrl(urlString))
        reply = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()\
            .get(request)
        reply.finished.connect(self.__feedLoaded)
        self.__replies[id(reply)] = (reply, itm)
    
    def __feedLoaded(self):
        """
        Private slot to extract the loaded feed data.
        """
        reply = self.sender()
        if id(reply) not in self.__replies:
            return
        
        topItem = self.__replies[id(reply)][1]
        del self.__replies[id(reply)]
        
        if reply.error() == QNetworkReply.NoError:
            linkString = ""
            titleString = ""
            
            xml = QXmlStreamReader()
            xmlData = reply.readAll()
            xml.addData(xmlData)
            
            while not xml.atEnd():
                xml.readNext()
                if xml.isStartElement():
                    if xml.name() == "item":
                        linkString = xml.attributes().value("rss:about")
                    elif xml.name() == "link":
                        linkString = xml.attributes().value("href")
                    currentTag = xml.name()
                elif xml.isEndElement():
                    if xml.name() in ["item", "entry"]:
                        itm = QTreeWidgetItem(topItem)
                        itm.setText(0, titleString)
                        itm.setData(0, FeedsManager.UrlStringRole, linkString)
                        itm.setIcon(0, UI.PixmapCache.getIcon("rss16.png"))
                        
                        linkString = ""
                        titleString = ""
                elif xml.isCharacters() and not xml.isWhitespace():
                    if currentTag == "title":
                        titleString = xml.text()
                    elif currentTag == "link":
                        linkString += xml.text()
            
            if topItem.childCount() == 0:
                itm = QTreeWidgetItem(topItem)
                itm.setText(0, self.tr("Error fetching feed"))
                itm.setData(0, FeedsManager.UrlStringRole, "")
                itm.setData(0, FeedsManager.ErrorDataRole,
                            str(xmlData, encoding="utf-8"))
            
            topItem.setExpanded(True)
        else:
            linkString = ""
            titleString = reply.errorString()
            itm = QTreeWidgetItem(topItem)
            itm.setText(0, titleString)
            itm.setData(0, FeedsManager.UrlStringRole, linkString)
            topItem.setExpanded(True)
    
    def __customContextMenuRequested(self, pos):
        """
        Private slot to handle the context menu request for the bookmarks tree.
        
        @param pos position the context menu was requested (QPoint)
        """
        itm = self.feedsTree.currentItem()
        if itm is None:
            return
        
        if self.feedsTree.indexOfTopLevelItem(itm) != -1:
            return
        
        urlString = itm.data(0, FeedsManager.UrlStringRole)
        if urlString:
            menu = QMenu()
            menu.addAction(
                self.tr("&Open"), self.__openMessageInCurrentTab)
            menu.addAction(
                self.tr("Open in New &Tab"), self.__openMessageInNewTab)
            menu.addSeparator()
            menu.addAction(self.tr("&Copy URL to Clipboard"),
                           self.__copyUrlToClipboard)
            menu.exec_(QCursor.pos())
        else:
            errorString = itm.data(0, FeedsManager.ErrorDataRole)
            if errorString:
                menu = QMenu()
                menu.addAction(
                    self.tr("&Show error data"), self.__showError)
                menu.exec_(QCursor.pos())
    
    def __itemActivated(self, itm, column):
        """
        Private slot to handle the activation of an item.
        
        @param itm reference to the activated item (QTreeWidgetItem)
        @param column column of the activation (integer)
        """
        if self.feedsTree.indexOfTopLevelItem(itm) != -1:
            return
        
        self.__openMessage(
            QApplication.keyboardModifiers() &
            Qt.ControlModifier == Qt.ControlModifier)
        
    def __openMessageInCurrentTab(self):
        """
        Private slot to open a feed message in the current browser tab.
        """
        self.__openMessage(False)
    
    def __openMessageInNewTab(self):
        """
        Private slot to open a feed message in a new browser tab.
        """
        self.__openMessage(True)
    
    def __openMessage(self, newTab):
        """
        Private method to open a feed message.
        
        @param newTab flag indicating to open the feed message in a new tab
            (boolean)
        """
        itm = self.feedsTree.currentItem()
        if itm is None:
            return
        
        urlString = itm.data(0, FeedsManager.UrlStringRole)
        if urlString:
            title = itm.text(0)
            
            if newTab:
                self.newUrl.emit(QUrl(urlString), title)
            else:
                self.openUrl.emit(QUrl(urlString), title)
        else:
            errorString = itm.data(0, FeedsManager.ErrorDataRole)
            if errorString:
                self.__showError()
    
    def __copyUrlToClipboard(self):
        """
        Private slot to copy the URL of the selected item to the clipboard.
        """
        itm = self.feedsTree.currentItem()
        if itm is None:
            return
        
        if self.feedsTree.indexOfTopLevelItem(itm) != -1:
            return
        
        urlString = itm.data(0, FeedsManager.UrlStringRole)
        if urlString:
            QApplication.clipboard().setText(urlString)
    
    def __showError(self):
        """
        Private slot to show error info for a failed load operation.
        """
        itm = self.feedsTree.currentItem()
        if itm is None:
            return
        
        errorStr = itm.data(0, FeedsManager.ErrorDataRole)
        if errorStr:
            E5MessageBox.critical(
                self,
                self.tr("Error loading feed"),
                "{0}".format(errorStr))
