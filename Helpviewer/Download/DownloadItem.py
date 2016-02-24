# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a widget controlling a download.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QTime, QFile, QFileInfo, \
    QUrl, QIODevice, QCryptographicHash, PYQT_VERSION_STR
from PyQt5.QtGui import QPalette, QDesktopServices
from PyQt5.QtWidgets import QWidget, QStyle, QDialog
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply

from E5Gui import E5FileDialog

from .Ui_DownloadItem import Ui_DownloadItem

from .DownloadUtilities import timeString, dataString
from ..HelpUtilities import parseContentDisposition

import UI.PixmapCache
import Preferences


class DownloadItem(QWidget, Ui_DownloadItem):
    """
    Class implementing a widget controlling a download.
    
    @signal statusChanged() emitted upon a status change of a download
    @signal downloadFinished() emitted when a download finished
    @signal progress(int, int) emitted to signal the download progress
    """
    statusChanged = pyqtSignal()
    downloadFinished = pyqtSignal()
    progress = pyqtSignal(int, int)
    
    Downloading = 0
    DownloadSuccessful = 1
    DownloadCancelled = 2
    
    def __init__(self, reply=None, requestFilename=False, webPage=None,
                 download=False, parent=None, mainWindow=None):
        """
        Constructor
        
        @keyparam reply reference to the network reply object (QNetworkReply)
        @keyparam requestFilename flag indicating to ask the user for a
            filename (boolean)
        @keyparam webPage reference to the web page object the download
            originated from (QWebPage)
        @keyparam download flag indicating a download operation (boolean)
        @keyparam parent reference to the parent widget (QWidget)
        @keyparam mainWindow reference to the main window (HelpWindow)
        """
        super(DownloadItem, self).__init__(parent)
        self.setupUi(self)
        
        p = self.infoLabel.palette()
        p.setColor(QPalette.Text, Qt.darkGray)
        self.infoLabel.setPalette(p)
        
        self.progressBar.setMaximum(0)
        
        self.__isFtpDownload = reply is not None and \
            reply.url().scheme() == "ftp"
        
        self.tryAgainButton.setIcon(UI.PixmapCache.getIcon("restart.png"))
        self.tryAgainButton.setEnabled(False)
        self.tryAgainButton.setVisible(False)
        self.stopButton.setIcon(UI.PixmapCache.getIcon("stopLoading.png"))
        self.pauseButton.setIcon(UI.PixmapCache.getIcon("pause.png"))
        self.openButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.openButton.setEnabled(False)
        self.openButton.setVisible(False)
        if self.__isFtpDownload:
            self.stopButton.setEnabled(False)
            self.stopButton.setVisible(False)
            self.pauseButton.setEnabled(False)
            self.pauseButton.setVisible(False)
        
        self.__state = DownloadItem.Downloading
        
        icon = self.style().standardIcon(QStyle.SP_FileIcon)
        self.fileIcon.setPixmap(icon.pixmap(48, 48))
        
        self.__mainWindow = mainWindow
        self.__reply = reply
        self.__requestFilename = requestFilename
        self.__page = webPage
        self.__pageUrl = webPage and webPage.mainFrame().url() or QUrl()
        self.__toDownload = download
        self.__bytesReceived = 0
        self.__bytesTotal = -1
        self.__downloadTime = QTime()
        self.__output = QFile()
        self.__fileName = ""
        self.__originalFileName = ""
        self.__startedSaving = False
        self.__finishedDownloading = False
        self.__gettingFileName = False
        self.__canceledFileSelect = False
        self.__autoOpen = False
        
        self.__sha1Hash = QCryptographicHash(QCryptographicHash.Sha1)
        self.__md5Hash = QCryptographicHash(QCryptographicHash.Md5)
        
        if not requestFilename:
            self.__requestFilename = \
                Preferences.getUI("RequestDownloadFilename")
        
        self.__initialize()
    
    def __initialize(self, tryAgain=False):
        """
        Private method to (re)initialize the widget.
        
        @param tryAgain flag indicating a retry (boolean)
        """
        if self.__reply is None:
            return
        
        self.__startedSaving = False
        self.__finishedDownloading = False
        self.__bytesReceived = 0
        self.__bytesTotal = -1
        
        self.__sha1Hash.reset()
        self.__md5Hash.reset()
        
        # start timer for the download estimation
        self.__downloadTime.start()
        
        # attach to the reply object
        self.__url = self.__reply.url()
        self.__reply.setParent(self)
        self.__reply.setReadBufferSize(16 * 1024 * 1024)
        self.__reply.readyRead.connect(self.__readyRead)
        self.__reply.error.connect(self.__networkError)
        self.__reply.downloadProgress.connect(self.__downloadProgress)
        self.__reply.metaDataChanged.connect(self.__metaDataChanged)
        self.__reply.finished.connect(self.__finished)
        
        # reset info
        self.infoLabel.clear()
        self.progressBar.setValue(0)
        self.__getFileName()
        
        if self.__reply.error() != QNetworkReply.NoError:
            self.__networkError()
            self.__finished()
    
    def __getFileName(self):
        """
        Private method to get the file name to save to from the user.
        """
        if self.__gettingFileName:
            return
        
        import Helpviewer.HelpWindow
        downloadDirectory = Helpviewer.HelpWindow.HelpWindow\
            .downloadManager().downloadDirectory()
        
        if self.__fileName:
            fileName = self.__fileName
            originalFileName = self.__originalFileName
            self.__toDownload = True
            ask = False
        else:
            defaultFileName, originalFileName = \
                self.__saveFileName(downloadDirectory)
            fileName = defaultFileName
            self.__originalFileName = originalFileName
            ask = True
        self.__autoOpen = False
        if not self.__toDownload:
            from .DownloadAskActionDialog import DownloadAskActionDialog
            url = self.__reply.url()
            dlg = DownloadAskActionDialog(
                QFileInfo(originalFileName).fileName(),
                self.__reply.header(QNetworkRequest.ContentTypeHeader),
                "{0}://{1}".format(url.scheme(), url.authority()),
                self)
            if dlg.exec_() == QDialog.Rejected or dlg.getAction() == "cancel":
                self.progressBar.setVisible(False)
                self.__reply.close()
                self.on_stopButton_clicked()
                self.filenameLabel.setText(
                    self.tr("Download canceled: {0}").format(
                        QFileInfo(defaultFileName).fileName()))
                self.__canceledFileSelect = True
                return
            
            if dlg.getAction() == "scan":
                self.__mainWindow.requestVirusTotalScan(url)
                
                self.progressBar.setVisible(False)
                self.__reply.close()
                self.on_stopButton_clicked()
                self.filenameLabel.setText(
                    self.tr("VirusTotal scan scheduled: {0}").format(
                        QFileInfo(defaultFileName).fileName()))
                self.__canceledFileSelect = True
                return
            
            self.__autoOpen = dlg.getAction() == "open"
            if PYQT_VERSION_STR >= "5.0.0":
                from PyQt5.QtCore import QStandardPaths
                tempLocation = QStandardPaths.standardLocations(
                    QStandardPaths.TempLocation)[0]
            else:
                from PyQt5.QtGui import QDesktopServices
                tempLocation = QDesktopServices.storageLocation(
                    QDesktopServices.TempLocation)
            fileName = tempLocation + '/' + \
                QFileInfo(fileName).completeBaseName()
        
        if ask and not self.__autoOpen and self.__requestFilename:
            self.__gettingFileName = True
            fileName = E5FileDialog.getSaveFileName(
                None,
                self.tr("Save File"),
                defaultFileName,
                "")
            self.__gettingFileName = False
            if not fileName:
                self.progressBar.setVisible(False)
                self.__reply.close()
                self.on_stopButton_clicked()
                self.filenameLabel.setText(
                    self.tr("Download canceled: {0}")
                        .format(QFileInfo(defaultFileName).fileName()))
                self.__canceledFileSelect = True
                return
        
        fileInfo = QFileInfo(fileName)
        Helpviewer.HelpWindow.HelpWindow.downloadManager()\
            .setDownloadDirectory(fileInfo.absoluteDir().absolutePath())
        self.filenameLabel.setText(fileInfo.fileName())
        
        self.__output.setFileName(fileName + ".part")
        self.__fileName = fileName
        
        # check file path for saving
        saveDirPath = QFileInfo(self.__fileName).dir()
        if not saveDirPath.exists():
            if not saveDirPath.mkpath(saveDirPath.absolutePath()):
                self.progressBar.setVisible(False)
                self.on_stopButton_clicked()
                self.infoLabel.setText(self.tr(
                    "Download directory ({0}) couldn't be created.")
                    .format(saveDirPath.absolutePath()))
                return
        
        self.filenameLabel.setText(QFileInfo(self.__fileName).fileName())
        if self.__requestFilename:
            self.__readyRead()
    
    def __saveFileName(self, directory):
        """
        Private method to calculate a name for the file to download.
        
        @param directory name of the directory to store the file into (string)
        @return proposed filename and original filename (string, string)
        """
        path = parseContentDisposition(self.__reply)
        info = QFileInfo(path)
        baseName = info.completeBaseName()
        endName = info.suffix()
        
        origName = baseName
        if endName:
            origName += '.' + endName
        
        name = directory + baseName
        if endName:
            name += '.' + endName
            if not self.__requestFilename:
                # do not overwrite, if the user is not being asked
                i = 1
                while QFile.exists(name):
                    # file exists already, don't overwrite
                    name = directory + baseName + ('-{0:d}'.format(i))
                    if endName:
                        name += '.' + endName
                    i += 1
        return name, origName
    
    def __open(self):
        """
        Private slot to open the downloaded file.
        """
        info = QFileInfo(self.__output)
        url = QUrl.fromLocalFile(info.absoluteFilePath())
        QDesktopServices.openUrl(url)
    
    @pyqtSlot()
    def on_tryAgainButton_clicked(self):
        """
        Private slot to retry the download.
        """
        self.retry()
    
    def retry(self):
        """
        Public slot to retry the download.
        """
        if not self.tryAgainButton.isEnabled():
            return
        
        self.tryAgainButton.setEnabled(False)
        self.tryAgainButton.setVisible(False)
        self.openButton.setEnabled(False)
        self.openButton.setVisible(False)
        if not self.__isFtpDownload:
            self.stopButton.setEnabled(True)
            self.stopButton.setVisible(True)
            self.pauseButton.setEnabled(True)
            self.pauseButton.setVisible(True)
        self.progressBar.setVisible(True)
        
        if self.__page:
            nam = self.__page.networkAccessManager()
        else:
            import Helpviewer.HelpWindow
            nam = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()
        reply = nam.get(QNetworkRequest(self.__url))
        if self.__output.exists():
            self.__output.remove()
        self.__output = QFile()
        self.__reply = reply
        self.__initialize(tryAgain=True)
        self.__state = DownloadItem.Downloading
        self.statusChanged.emit()
    
    @pyqtSlot(bool)
    def on_pauseButton_clicked(self, checked):
        """
        Private slot to pause the download.
        
        @param checked flag indicating the state of the button (boolean)
        """
        if checked:
            self.__reply.readyRead.disconnect(self.__readyRead)
            self.__reply.setReadBufferSize(16 * 1024)
        else:
            self.__reply.readyRead.connect(self.__readyRead)
            self.__reply.setReadBufferSize(16 * 1024 * 1024)
            self.__readyRead()
    
    @pyqtSlot()
    def on_stopButton_clicked(self):
        """
        Private slot to stop the download.
        """
        self.cancelDownload()
    
    def cancelDownload(self):
        """
        Public slot to stop the download.
        """
        self.setUpdatesEnabled(False)
        if not self.__isFtpDownload:
            self.stopButton.setEnabled(False)
            self.stopButton.setVisible(False)
            self.pauseButton.setEnabled(False)
            self.pauseButton.setVisible(False)
        self.tryAgainButton.setEnabled(True)
        self.tryAgainButton.setVisible(True)
        self.openButton.setEnabled(False)
        self.openButton.setVisible(False)
        self.setUpdatesEnabled(True)
        self.__state = DownloadItem.DownloadCancelled
        self.__reply.abort()
        self.downloadFinished.emit()
    
    @pyqtSlot()
    def on_openButton_clicked(self):
        """
        Private slot to open the downloaded file.
        """
        self.openFile()
    
    def openFile(self):
        """
        Public slot to open the downloaded file.
        """
        info = QFileInfo(self.__fileName)
        url = QUrl.fromLocalFile(info.absoluteFilePath())
        QDesktopServices.openUrl(url)
    
    def openFolder(self):
        """
        Public slot to open the folder containing the downloaded file.
        """
        info = QFileInfo(self.__fileName)
        url = QUrl.fromLocalFile(info.absolutePath())
        QDesktopServices.openUrl(url)
    
    def __readyRead(self):
        """
        Private slot to read the available data.
        """
        if self.__requestFilename and not self.__output.fileName():
            return
        
        if not self.__output.isOpen():
            # in case someone else has already put a file there
            if not self.__requestFilename:
                self.__getFileName()
            if not self.__output.open(QIODevice.WriteOnly):
                self.infoLabel.setText(
                    self.tr("Error opening save file: {0}")
                    .format(self.__output.errorString()))
                self.on_stopButton_clicked()
                self.statusChanged.emit()
                return
            self.statusChanged.emit()
        
        buffer = self.__reply.readAll()
        self.__sha1Hash.addData(buffer)
        self.__md5Hash.addData(buffer)
        bytesWritten = self.__output.write(buffer)
        if bytesWritten == -1:
            self.infoLabel.setText(
                self.tr("Error saving: {0}")
                    .format(self.__output.errorString()))
            self.on_stopButton_clicked()
        else:
            self.__startedSaving = True
            if self.__finishedDownloading:
                self.__finished()
    
    def __networkError(self):
        """
        Private slot to handle a network error.
        """
        self.infoLabel.setText(
            self.tr("Network Error: {0}")
                .format(self.__reply.errorString()))
        self.tryAgainButton.setEnabled(True)
        self.tryAgainButton.setVisible(True)
        self.downloadFinished.emit()
    
    def __metaDataChanged(self):
        """
        Private slot to handle a change of the meta data.
        """
        locationHeader = self.__reply.header(QNetworkRequest.LocationHeader)
        if locationHeader and locationHeader.isValid():
            self.__url = QUrl(locationHeader)
            import Helpviewer.HelpWindow
            self.__reply = Helpviewer.HelpWindow.HelpWindow\
                .networkAccessManager().get(QNetworkRequest(self.__url))
            self.__initialize()
    
    def __downloadProgress(self, bytesReceived, bytesTotal):
        """
        Private method to show the download progress.
        
        @param bytesReceived number of bytes received (integer)
        @param bytesTotal number of total bytes (integer)
        """
        self.__bytesReceived = bytesReceived
        self.__bytesTotal = bytesTotal
        currentValue = 0
        totalValue = 0
        if bytesTotal > 0:
            currentValue = bytesReceived * 100 / bytesTotal
            totalValue = 100
        self.progressBar.setValue(currentValue)
        self.progressBar.setMaximum(totalValue)
        
        self.progress.emit(currentValue, totalValue)
        self.__updateInfoLabel()
    
    def bytesTotal(self):
        """
        Public method to get the total number of bytes of the download.
        
        @return total number of bytes (integer)
        """
        if self.__bytesTotal == -1:
            self.__bytesTotal = self.__reply.header(
                QNetworkRequest.ContentLengthHeader)
            if self.__bytesTotal is None:
                self.__bytesTotal = -1
        return self.__bytesTotal
    
    def bytesReceived(self):
        """
        Public method to get the number of bytes received.
        
        @return number of bytes received (integer)
        """
        return self.__bytesReceived
    
    def remainingTime(self):
        """
        Public method to get an estimation for the remaining time.
        
        @return estimation for the remaining time (float)
        """
        if not self.downloading():
            return -1.0
        
        if self.bytesTotal() == -1:
            return -1.0
        
        cSpeed = self.currentSpeed()
        if cSpeed != 0:
            timeRemaining = (self.bytesTotal() - self.bytesReceived()) / cSpeed
        else:
            timeRemaining = 1
        
        # ETA should never be 0
        if timeRemaining == 0:
            timeRemaining = 1
        
        return timeRemaining
    
    def currentSpeed(self):
        """
        Public method to get an estimation for the download speed.
        
        @return estimation for the download speed (float)
        """
        if not self.downloading():
            return -1.0
        
        return self.__bytesReceived * 1000.0 / self.__downloadTime.elapsed()
    
    def __updateInfoLabel(self):
        """
        Private method to update the info label.
        """
        if self.__reply.error() != QNetworkReply.NoError:
            return
        
        bytesTotal = self.bytesTotal()
        running = not self.downloadedSuccessfully()
        
        speed = self.currentSpeed()
        timeRemaining = self.remainingTime()
        
        info = ""
        if running:
            remaining = ""
            
            if bytesTotal > 0:
                remaining = timeString(timeRemaining)
            
            info = self.tr("{0} of {1} ({2}/sec)\n{3}")\
                .format(
                    dataString(self.__bytesReceived),
                    bytesTotal == -1 and self.tr("?")
                    or dataString(bytesTotal),
                    dataString(int(speed)),
                    remaining)
        else:
            if self.__bytesReceived == bytesTotal or bytesTotal == -1:
                info = self.tr("{0} downloaded\nSHA1: {1}\nMD5: {2}")\
                    .format(dataString(self.__output.size()),
                            str(self.__sha1Hash.result().toHex(),
                                encoding="ascii"),
                            str(self.__md5Hash.result().toHex(),
                                encoding="ascii")
                            )
            else:
                info = self.tr("{0} of {1} - Stopped")\
                    .format(dataString(self.__bytesReceived),
                            dataString(bytesTotal))
        self.infoLabel.setText(info)
    
    def downloading(self):
        """
        Public method to determine, if a download is in progress.
        
        @return flag indicating a download is in progress (boolean)
        """
        return self.__state == DownloadItem.Downloading
    
    def downloadedSuccessfully(self):
        """
        Public method to check for a successful download.
        
        @return flag indicating a successful download (boolean)
        """
        return self.__state == DownloadItem.DownloadSuccessful
    
    def downloadCanceled(self):
        """
        Public method to check, if the download was cancelled.
        
        @return flag indicating a canceled download (boolean)
        """
        return self.__state == DownloadItem.DownloadCancelled
    
    def __finished(self):
        """
        Private slot to handle the download finished.
        """
        self.__finishedDownloading = True
        if not self.__startedSaving:
            return
        
        noError = self.__reply.error() == QNetworkReply.NoError
        
        self.progressBar.setVisible(False)
        if not self.__isFtpDownload:
            self.stopButton.setEnabled(False)
            self.stopButton.setVisible(False)
            self.pauseButton.setEnabled(False)
            self.pauseButton.setVisible(False)
        self.openButton.setEnabled(noError)
        self.openButton.setVisible(noError)
        self.__output.close()
        if QFile.exists(self.__fileName):
            QFile.remove(self.__fileName)
        self.__output.rename(self.__fileName)
        self.__updateInfoLabel()
        self.__state = DownloadItem.DownloadSuccessful
        self.statusChanged.emit()
        self.downloadFinished.emit()
        
        if self.__autoOpen:
            self.__open()
    
    def canceledFileSelect(self):
        """
        Public method to check, if the user canceled the file selection.
        
        @return flag indicating cancellation (boolean)
        """
        return self.__canceledFileSelect
    
    def setIcon(self, icon):
        """
        Public method to set the download icon.
        
        @param icon reference to the icon to be set (QIcon)
        """
        self.fileIcon.setPixmap(icon.pixmap(48, 48))
    
    def fileName(self):
        """
        Public method to get the name of the output file.
        
        @return name of the output file (string)
        """
        return self.__fileName
    
    def absoluteFilePath(self):
        """
        Public method to get the absolute path of the output file.
        
        @return absolute path of the output file (string)
        """
        return QFileInfo(self.__fileName).absoluteFilePath()
    
    def getData(self):
        """
        Public method to get the relevant download data.
        
        @return tuple of URL, save location, flag and the
            URL of the related web page (QUrl, string, boolean,QUrl)
        """
        return (self.__url, QFileInfo(self.__fileName).filePath(),
                self.downloadedSuccessfully(), self.__pageUrl)
    
    def setData(self, data):
        """
        Public method to set the relevant download data.
        
        @param data tuple of URL, save location, flag and the
            URL of the related web page (QUrl, string, boolean, QUrl)
        """
        self.__url = data[0]
        self.__fileName = data[1]
        self.__pageUrl = data[3]
        self.__isFtpDownload = self.__url.scheme() == "ftp"
        
        self.filenameLabel.setText(QFileInfo(self.__fileName).fileName())
        self.infoLabel.setText(self.__fileName)
        
        self.stopButton.setEnabled(False)
        self.stopButton.setVisible(False)
        self.pauseButton.setEnabled(False)
        self.pauseButton.setVisible(False)
        self.openButton.setEnabled(data[2])
        self.openButton.setVisible(data[2])
        self.tryAgainButton.setEnabled(not data[2])
        self.tryAgainButton.setVisible(not data[2])
        if data[2]:
            self.__state = DownloadItem.DownloadSuccessful
        else:
            self.__state = DownloadItem.DownloadCancelled
        self.progressBar.setVisible(False)
    
    def getInfoData(self):
        """
        Public method to get the text of the info label.
        
        @return text of the info label (string)
        """
        return self.infoLabel.text()
    
    def getPageUrl(self):
        """
        Public method to get the URL of the download page.
        
        @return URL of the download page (QUrl)
        """
        return self.__pageUrl
