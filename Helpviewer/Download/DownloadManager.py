# -*- coding: utf-8 -*-

"""
Module implementing the download manager class.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, Qt, QModelIndex, QFileInfo
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QDialog, QStyle, QFileIconProvider, QMenu, \
    QApplication
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtWebKit import QWebSettings

from E5Gui import E5MessageBox

from .Ui_DownloadManager import Ui_DownloadManager

from .DownloadModel import DownloadModel

import Helpviewer.HelpWindow

from Utilities.AutoSaver import AutoSaver
import UI.PixmapCache
import Preferences


class DownloadManager(QDialog, Ui_DownloadManager):
    """
    Class implementing the download manager.
    """
    RemoveNever = 0
    RemoveExit = 1
    RemoveSuccessFullDownload = 2
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(DownloadManager, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.__saveTimer = AutoSaver(self, self.save)
        
        self.__model = DownloadModel(self)
        self.__manager = Helpviewer.HelpWindow.HelpWindow\
            .networkAccessManager()
        
        self.__iconProvider = None
        self.__downloads = []
        self.__downloadDirectory = ""
        self.__loaded = False
        
        self.setDownloadDirectory(Preferences.getUI("DownloadPath"))
        
        self.downloadsView.setShowGrid(False)
        self.downloadsView.verticalHeader().hide()
        self.downloadsView.horizontalHeader().hide()
        self.downloadsView.setAlternatingRowColors(True)
        self.downloadsView.horizontalHeader().setStretchLastSection(True)
        self.downloadsView.setModel(self.__model)
        self.downloadsView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.downloadsView.customContextMenuRequested.connect(
            self.__customContextMenuRequested)
        
        self.__load()
    
    def __customContextMenuRequested(self, pos):
        """
        Private slot to handle the context menu request for the bookmarks tree.
        
        @param pos position the context menu was requested (QPoint)
        """
        menu = QMenu()
        
        selectedRowsCount = len(
            self.downloadsView.selectionModel().selectedRows())
        
        if selectedRowsCount == 1:
            row = self.downloadsView.selectionModel().selectedRows()[0].row()
            itm = self.__downloads[row]
            if itm.downloadCanceled():
                menu.addAction(
                    UI.PixmapCache.getIcon("restart.png"),
                    self.tr("Retry"), self.__contextMenuRetry)
            else:
                if itm.downloadedSuccessfully():
                    menu.addAction(
                        UI.PixmapCache.getIcon("open.png"),
                        self.tr("Open"), self.__contextMenuOpen)
                elif itm.downloading():
                    menu.addAction(
                        UI.PixmapCache.getIcon("stopLoading.png"),
                        self.tr("Cancel"), self.__contextMenuCancel)
                    menu.addSeparator()
                menu.addAction(
                    self.tr("Open Containing Folder"),
                    self.__contextMenuOpenFolder)
            menu.addSeparator()
            menu.addAction(
                self.tr("Go to Download Page"),
                self.__contextMenuGotoPage)
            menu.addAction(
                self.tr("Copy Download Link"),
                self.__contextMenuCopyLink)
            menu.addSeparator()
        menu.addAction(self.tr("Select All"), self.__contextMenuSelectAll)
        if selectedRowsCount > 1 or \
           (selectedRowsCount == 1 and
            not self.__downloads[
                self.downloadsView.selectionModel().selectedRows()[0].row()]
                .downloading()):
            menu.addSeparator()
            menu.addAction(
                self.tr("Remove From List"),
                self.__contextMenuRemoveSelected)
        
        menu.exec_(QCursor.pos())
    
    def shutdown(self):
        """
        Public method to stop the download manager.
        """
        self.__saveTimer.changeOccurred()
        self.__saveTimer.saveIfNeccessary()
        self.close()
    
    def activeDownloads(self):
        """
        Public method to get the number of active downloads.
        
        @return number of active downloads (integer)
        """
        count = 0
        
        for download in self.__downloads:
            if download.downloading():
                count += 1
        return count
    
    def allowQuit(self):
        """
        Public method to check, if it is ok to quit.
        
        @return flag indicating allowance to quit (boolean)
        """
        if self.activeDownloads() > 0:
            res = E5MessageBox.yesNo(
                self,
                self.tr(""),
                self.tr("""There are %n downloads in progress.\n"""
                        """Do you want to quit anyway?""", "",
                        self.activeDownloads()),
                icon=E5MessageBox.Warning)
            if not res:
                self.show()
                return False
        return True
    
    def download(self, requestOrUrl, requestFileName=False, mainWindow=None):
        """
        Public method to download a file.
        
        @param requestOrUrl reference to a request object (QNetworkRequest)
            or a URL to be downloaded (QUrl)
        @keyparam requestFileName flag indicating to ask for the
            download file name (boolean)
        @keyparam mainWindow reference to the main window (HelpWindow)
        """
        request = QNetworkRequest(requestOrUrl)
        if request.url().isEmpty():
            return
        self.handleUnsupportedContent(
            self.__manager.get(request),
            requestFileName=requestFileName,
            download=True,
            mainWindow=mainWindow)
    
    def handleUnsupportedContent(self, reply, requestFileName=False,
                                 webPage=None, download=False,
                                 mainWindow=None):
        """
        Public method to handle unsupported content by downloading the
        referenced resource.
        
        @param reply reference to the reply object (QNetworkReply)
        @keyparam requestFileName indicating to ask for a filename
            (boolean)
        @keyparam webPage reference to the web page (HelpWebPage)
        @keyparam download flag indicating a download request (boolean)
        @keyparam mainWindow reference to the main window (HelpWindow)
        """
        if reply is None or reply.url().isEmpty():
            return
        
        size = reply.header(QNetworkRequest.ContentLengthHeader)
        if size == 0:
            return
        
        from .DownloadItem import DownloadItem
        itm = DownloadItem(
            reply=reply, requestFilename=requestFileName,
            webPage=webPage, download=download, parent=self,
            mainWindow=mainWindow)
        self.__addItem(itm)
        
        if itm.canceledFileSelect():
            return
        
        if not self.isVisible():
            self.show()
        
        self.activateWindow()
        self.raise_()
    
    def __addItem(self, itm):
        """
        Private method to add a download to the list of downloads.
        
        @param itm reference to the download item (DownloadItem)
        """
        itm.statusChanged.connect(self.__updateRow)
        itm.downloadFinished.connect(self.__finished)
        
        row = len(self.__downloads)
        self.__model.beginInsertRows(QModelIndex(), row, row)
        self.__downloads.append(itm)
        self.__model.endInsertRows()
        
        self.downloadsView.setIndexWidget(self.__model.index(row, 0), itm)
        icon = self.style().standardIcon(QStyle.SP_FileIcon)
        itm.setIcon(icon)
        self.downloadsView.setRowHeight(row, itm.sizeHint().height() * 1.5)
        # just in case the download finished before the constructor returned
        self.__updateRow(itm)
        self.changeOccurred()
        self.__updateActiveItemCount()
    
    def __updateRow(self, itm=None):
        """
        Private slot to update a download item.
        
        @param itm reference to the download item (DownloadItem)
        """
        if itm is None:
            itm = self.sender()
        
        if itm not in self.__downloads:
            return
        
        row = self.__downloads.index(itm)
        
        if self.__iconProvider is None:
            self.__iconProvider = QFileIconProvider()
        
        icon = self.__iconProvider.icon(QFileInfo(itm.fileName()))
        if icon.isNull():
            icon = self.style().standardIcon(QStyle.SP_FileIcon)
        itm.setIcon(icon)
        
        oldHeight = self.downloadsView.rowHeight(row)
        self.downloadsView.setRowHeight(
            row,
            max(oldHeight, itm.minimumSizeHint().height() * 1.5))
        
        remove = False
        globalSettings = QWebSettings.globalSettings()
        if not itm.downloading() and \
           globalSettings.testAttribute(QWebSettings.PrivateBrowsingEnabled):
            remove = True
        
        if itm.downloadedSuccessfully() and \
           self.removePolicy() == DownloadManager.RemoveSuccessFullDownload:
            remove = True
        
        if remove:
            self.__model.removeRow(row)
        
        self.cleanupButton.setEnabled(
            (len(self.__downloads) - self.activeDownloads()) > 0)
        
        # record the change
        self.changeOccurred()
    
    def removePolicy(self):
        """
        Public method to get the remove policy.
        
        @return remove policy (integer)
        """
        return Preferences.getHelp("DownloadManagerRemovePolicy")
    
    def setRemovePolicy(self, policy):
        """
        Public method to set the remove policy.
        
        @param policy policy to be set
            (DownloadManager.RemoveExit, DownloadManager.RemoveNever,
             DownloadManager.RemoveSuccessFullDownload)
        """
        assert policy in (DownloadManager.RemoveExit,
                          DownloadManager.RemoveNever,
                          DownloadManager.RemoveSuccessFullDownload)
        
        if policy == self.removePolicy():
            return
        
        Preferences.setHelp("DownloadManagerRemovePolicy", self.policy)
    
    def save(self):
        """
        Public method to save the download settings.
        """
        if not self.__loaded:
            return
        
        Preferences.setHelp("DownloadManagerSize", self.size())
        Preferences.setHelp("DownloadManagerPosition", self.pos())
        if self.removePolicy() == DownloadManager.RemoveExit:
            return
        
        downloads = []
        for download in self.__downloads:
            downloads.append(download.getData())
        Preferences.setHelp("DownloadManagerDownloads", downloads)
    
    def __load(self):
        """
        Private method to load the download settings.
        """
        if self.__loaded:
            return
        
        size = Preferences.getHelp("DownloadManagerSize")
        if size.isValid():
            self.resize(size)
        pos = Preferences.getHelp("DownloadManagerPosition")
        self.move(pos)
        
        downloads = Preferences.getHelp("DownloadManagerDownloads")
        for download in downloads:
            if not download[0].isEmpty() and \
               download[1] != "":
                from .DownloadItem import DownloadItem
                itm = DownloadItem(parent=self)
                itm.setData(download)
                self.__addItem(itm)
        self.cleanupButton.setEnabled(
            (len(self.__downloads) - self.activeDownloads()) > 0)
        
        self.__loaded = True
        self.__updateActiveItemCount()
    
    def cleanup(self):
        """
        Public slot to cleanup the downloads.
        """
        self.on_cleanupButton_clicked()
    
    @pyqtSlot()
    def on_cleanupButton_clicked(self):
        """
        Private slot cleanup the downloads.
        """
        if len(self.__downloads) == 0:
            return
        
        self.__model.removeRows(0, len(self.__downloads))
        if len(self.__downloads) == 0 and \
           self.__iconProvider is not None:
            self.__iconProvider = None
        
        self.changeOccurred()
        self.__updateActiveItemCount()
    
    def __updateItemCount(self):
        """
        Private method to update the count label.
        """
        count = len(self.__downloads)
        self.countLabel.setText(self.tr("%n Download(s)", "", count))
    
    def __updateActiveItemCount(self):
        """
        Private method to update the window title.
        """
        count = self.activeDownloads()
        if count > 0:
            self.setWindowTitle(
                self.tr("Downloading %n file(s)", "", count))
        else:
            self.setWindowTitle(self.tr("Downloads"))
    
    def __finished(self):
        """
        Private slot to handle a finished download.
        """
        self.__updateActiveItemCount()
        if self.isVisible():
            QApplication.alert(self)
    
    def setDownloadDirectory(self, directory):
        """
        Public method to set the current download directory.
        
        @param directory current download directory (string)
        """
        self.__downloadDirectory = directory
        if self.__downloadDirectory != "":
            self.__downloadDirectory += "/"
    
    def downloadDirectory(self):
        """
        Public method to get the current download directory.
        
        @return current download directory (string)
        """
        return self.__downloadDirectory
    
    def count(self):
        """
        Public method to get the number of downloads.
        
        @return number of downloads (integer)
        """
        return len(self.__downloads)
    
    def downloads(self):
        """
        Public method to get a reference to the downloads.
        
        @return reference to the downloads (list of DownloadItem)
        """
        return self.__downloads
    
    def changeOccurred(self):
        """
        Public method to signal a change.
        """
        self.__saveTimer.changeOccurred()
        self.__updateItemCount()
    
    ###########################################################################
    ## Context menu related methods below
    ###########################################################################
    
    def __currentItem(self):
        """
        Private method to get a reference to the current item.
        
        @return reference to the current item (DownloadItem)
        """
        index = self.downloadsView.currentIndex()
        if index and index.isValid():
            row = index.row()
            return self.__downloads[row]
        
        return None
    
    def __contextMenuRetry(self):
        """
        Private method to retry of the download.
        """
        itm = self.__currentItem()
        if itm is not None:
            itm.retry()
    
    def __contextMenuOpen(self):
        """
        Private method to open the downloaded file.
        """
        itm = self.__currentItem()
        if itm is not None:
            itm.openFile()
    
    def __contextMenuOpenFolder(self):
        """
        Private method to open the folder containing the downloaded file.
        """
        itm = self.__currentItem()
        if itm is not None:
            itm.openFolder()
    
    def __contextMenuCancel(self):
        """
        Private method to cancel the current download.
        """
        itm = self.__currentItem()
        if itm is not None:
            itm.cancelDownload()
    
    def __contextMenuGotoPage(self):
        """
        Private method to open the download page.
        """
        itm = self.__currentItem()
        if itm is not None:
            url = itm.getPageUrl()
            Helpviewer.HelpWindow.HelpWindow.mainWindow().openUrl(url, "")
    
    def __contextMenuCopyLink(self):
        """
        Private method to copy the download link to the clipboard.
        """
        itm = self.__currentItem()
        if itm is not None:
            url = itm.getPageUrl().toString()
            QApplication.clipboard().setText(url)
    
    def __contextMenuSelectAll(self):
        """
        Private method to select all downloads.
        """
        self.downloadsView.selectAll()
    
    def __contextMenuRemoveSelected(self):
        """
        Private method to remove the selected downloads from the list.
        """
        self.downloadsView.removeSelected()
