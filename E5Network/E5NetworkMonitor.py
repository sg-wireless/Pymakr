# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a network monitor dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QUrl, \
    QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QDialog
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager

from .Ui_E5NetworkMonitor import Ui_E5NetworkMonitor


class E5NetworkRequest(object):
    """
    Class for storing all data related to a specific request.
    """
    def __init__(self):
        """
        Constructor
        """
        self.op = -1
        self.request = None
        self.reply = None
        
        self.response = ""
        self.length = 0
        self.contentType = ""
        self.info = ""
        self.replyHeaders = []  # list of tuple of two items


class E5NetworkMonitor(QDialog, Ui_E5NetworkMonitor):
    """
    Class implementing a network monitor dialog.
    """
    _monitor = None
    
    @classmethod
    def instance(cls, networkAccessManager):
        """
        Class method to get a reference to our singleton.
        
        @param networkAccessManager reference to the network access manager
            (QNetworkAccessManager)
        @return reference to the network monitor singleton (E5NetworkMonitor)
        """
        if cls._monitor is None:
            cls._monitor = E5NetworkMonitor(networkAccessManager)
        
        return cls._monitor
    
    @classmethod
    def closeMonitor(cls):
        """
        Class method to close the monitor dialog.
        """
        if cls._monitor is not None:
            cls._monitor.close()
    
    def __init__(self, networkAccessManager, parent=None):
        """
        Constructor
        
        @param networkAccessManager reference to the network access manager
            (QNetworkAccessManager)
        @param parent reference to the parent widget (QWidget)
        """
        super(E5NetworkMonitor, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.__requestHeaders = QStandardItemModel(self)
        self.__requestHeaders.setHorizontalHeaderLabels(
            [self.tr("Name"), self.tr("Value")])
        self.requestHeadersList.setModel(self.__requestHeaders)
        self.requestHeadersList.horizontalHeader().setStretchLastSection(True)
        self.requestHeadersList.doubleClicked.connect(self.__showHeaderDetails)
        
        self.__replyHeaders = QStandardItemModel(self)
        self.__replyHeaders.setHorizontalHeaderLabels(
            [self.tr("Name"), self.tr("Value")])
        self.responseHeadersList.setModel(self.__replyHeaders)
        self.responseHeadersList.horizontalHeader().setStretchLastSection(True)
        self.responseHeadersList.doubleClicked.connect(
            self.__showHeaderDetails)
        
        self.requestsList.horizontalHeader().setStretchLastSection(True)
        self.requestsList.verticalHeader().setMinimumSectionSize(-1)
        
        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setFilterKeyColumn(-1)
        self.searchEdit.textChanged.connect(
            self.__proxyModel.setFilterFixedString)
        
        self.removeButton.clicked.connect(self.requestsList.removeSelected)
        self.removeAllButton.clicked.connect(self.requestsList.removeAll)
        
        self.__model = E5RequestModel(networkAccessManager, self)
        self.__proxyModel.setSourceModel(self.__model)
        self.requestsList.setModel(self.__proxyModel)
        self.__proxyModel.rowsInserted.connect(
            self.requestsList.scrollToBottom)
        self.requestsList.selectionModel()\
            .currentChanged[QModelIndex, QModelIndex]\
            .connect(self.__currentChanged)
        
        fm = self.fontMetrics()
        em = fm.width("m")
        self.requestsList.horizontalHeader().resizeSection(0, em * 5)
        self.requestsList.horizontalHeader().resizeSection(1, em * 20)
        self.requestsList.horizontalHeader().resizeSection(3, em * 5)
        self.requestsList.horizontalHeader().resizeSection(4, em * 15)
        
        self.__headersDlg = None
    
    def closeEvent(self, evt):
        """
        Protected method called upon closing the dialog.
        
        @param evt reference to the close event object (QCloseEvent)
        """
        self.__class__._monitor = None
        super(E5NetworkMonitor, self).closeEvent(evt)
    
    def reject(self):
        """
        Public slot to close the dialog with a Reject status.
        """
        self.__class__._monitor = None
        super(E5NetworkMonitor, self).reject()
    
    def __currentChanged(self, current, previous):
        """
        Private slot to handle a change of the current index.
        
        @param current new current index (QModelIndex)
        @param previous old current index (QModelIndex)
        """
        self.__requestHeaders.setRowCount(0)
        self.__replyHeaders.setRowCount(0)
        
        if not current.isValid():
            return
        
        row = self.__proxyModel.mapToSource(current).row()
        
        req = self.__model.requests[row].request
        
        for header in req.rawHeaderList():
            self.__requestHeaders.insertRows(0, 1, QModelIndex())
            self.__requestHeaders.setData(
                self.__requestHeaders.index(0, 0),
                str(header, "utf-8"))
            self.__requestHeaders.setData(
                self.__requestHeaders.index(0, 1),
                str(req.rawHeader(header), "utf-8"))
            self.__requestHeaders.item(0, 0).setFlags(
                Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.__requestHeaders.item(0, 1).setFlags(
                Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        
        for header in self.__model.requests[row].replyHeaders:
            self.__replyHeaders.insertRows(0, 1, QModelIndex())
            self.__replyHeaders.setData(
                self.__replyHeaders.index(0, 0),
                header[0])
            self.__replyHeaders.setData(
                self.__replyHeaders.index(0, 1),
                header[1])
            self.__replyHeaders.item(0, 0).setFlags(
                Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.__replyHeaders.item(0, 1).setFlags(
                Qt.ItemIsSelectable | Qt.ItemIsEnabled)
    
    def __showHeaderDetails(self, index):
        """
        Private slot to show a dialog with the header details.
        
        @param index index of the entry to show (QModelIndex)
        """
        if not index.isValid():
            return
        
        headerList = self.sender()
        if headerList is None:
            return
        
        row = index.row()
        name = headerList.model().data(headerList.model().index(row, 0))
        value = headerList.model().data(headerList.model().index(row, 1))
        if self.__headersDlg is None:
            from .E5NetworkHeaderDetailsDialog import \
                E5NetworkHeaderDetailsDialog
            self.__headersDlg = E5NetworkHeaderDetailsDialog(self)
        self.__headersDlg.setData(name, value)
        self.__headersDlg.show()


class E5RequestModel(QAbstractTableModel):
    """
    Class implementing a model storing request objects.
    """
    def __init__(self, networkAccessManager, parent=None):
        """
        Constructor
        
        @param networkAccessManager reference to the network access manager
            (QNetworkAccessManager)
        @param parent reference to the parent object (QObject)
        """
        super(E5RequestModel, self).__init__(parent)
        
        self.__headerData = [
            self.tr("Method"),
            self.tr("Address"),
            self.tr("Response"),
            self.tr("Length"),
            self.tr("Content Type"),
            self.tr("Info"),
        ]
        
        self.__operations = {
            QNetworkAccessManager.HeadOperation: "HEAD",
            QNetworkAccessManager.GetOperation: "GET",
            QNetworkAccessManager.PutOperation: "PUT",
            QNetworkAccessManager.PostOperation: "POST",
        }
        
        self.requests = []
        networkAccessManager.requestCreated.connect(self.__requestCreated)
    
    def __requestCreated(self, operation, request, reply):
        """
        Private slot handling the creation of a network request.
        
        @param operation network operation (QNetworkAccessManager.Operation)
        @param request reference to the request object (QNetworkRequest)
        @param reply reference to the reply object(QNetworkReply)
        """
        req = E5NetworkRequest()
        req.op = operation
        req.request = QNetworkRequest(request)
        req.reply = reply
        self.__addRequest(req)
    
    def __addRequest(self, req):
        """
        Private method to add a request object to the model.
        
        @param req reference to the request object (E5NetworkRequest)
        """
        self.beginInsertRows(
            QModelIndex(), len(self.requests), len(self.requests))
        self.requests.append(req)
        req.reply.finished.connect(self.__addReply)
        self.endInsertRows()
    
    def __addReply(self):
        """
        Private slot to add the reply data to the model.
        """
        reply = self.sender()
        if reply is None:
            return
        
        offset = len(self.requests) - 1
        while offset >= 0:
            if self.requests[offset].reply is reply:
                break
            offset -= 1
        if offset < 0:
            return
        
        # save the reply header data
        for header in reply.rawHeaderList():
            self.requests[offset].replyHeaders.append((
                str(header, "utf-8"), str(reply.rawHeader(header), "utf-8")))
        
        # save reply info to be displayed
        status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) or 0
        reason = \
            reply.attribute(QNetworkRequest.HttpReasonPhraseAttribute) or ""
        self.requests[offset].response = "{0:d} {1}".format(status, reason)
        self.requests[offset].length = \
            reply.header(QNetworkRequest.ContentLengthHeader)
        self.requests[offset].contentType = \
            reply.header(QNetworkRequest.ContentTypeHeader)
        
        if status == 302:
            target = reply.attribute(
                QNetworkRequest.RedirectionTargetAttribute) or QUrl()
            self.requests[offset].info = \
                self.tr("Redirect: {0}").format(target.toString())
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Public method to get header data from the model.
        
        @param section section number (integer)
        @param orientation orientation (Qt.Orientation)
        @param role role of the data to retrieve (integer)
        @return requested data
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.__headerData[section]
        
        return QAbstractTableModel.headerData(self, section, orientation, role)
    
    def data(self, index, role=Qt.DisplayRole):
        """
        Public method to get data from the model.
        
        @param index index to get data for (QModelIndex)
        @param role role of the data to retrieve (integer)
        @return requested data
        """
        if index.row() < 0 or index.row() >= len(self.requests):
            return None
        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            col = index.column()
            if col == 0:
                try:
                    return self.__operations[self.requests[index.row()].op]
                except KeyError:
                    return self.tr("Unknown")
            elif col == 1:
                return self.requests[index.row()].request.url().toEncoded()
            elif col == 2:
                return self.requests[index.row()].response
            elif col == 3:
                return self.requests[index.row()].length
            elif col == 4:
                return self.requests[index.row()].contentType
            elif col == 5:
                return self.requests[index.row()].info
        
        return None
    
    def columnCount(self, parent):
        """
        Public method to get the number of columns of the model.
        
        @param parent parent index (QModelIndex)
        @return number of columns (integer)
        """
        if parent.column() > 0:
            return 0
        else:
            return len(self.__headerData)
    
    def rowCount(self, parent):
        """
        Public method to get the number of rows of the model.
        
        @param parent parent index (QModelIndex)
        @return number of columns (integer)
        """
        if parent.isValid():
            return 0
        else:
            return len(self.requests)
    
    def removeRows(self, row, count, parent):
        """
        Public method to remove entries from the model.
        
        @param row start row (integer)
        @param count number of rows to remove (integer)
        @param parent parent index (QModelIndex)
        @return flag indicating success (boolean)
        """
        if parent.isValid():
            return False
        
        lastRow = row + count - 1
        self.beginRemoveRows(parent, row, lastRow)
        del self.requests[row:lastRow + 1]
        self.endRemoveRows()
        return True
