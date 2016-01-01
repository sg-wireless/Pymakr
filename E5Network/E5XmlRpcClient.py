# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a xmlrpc client for Qt.
"""

from __future__ import unicode_literals
try:
    import xmlrpclib as xmlrpc
except ImportError:
    import xmlrpc.client as xmlrpc

from PyQt5.QtCore import QObject, QUrl, QByteArray
from PyQt5.QtNetwork import QNetworkAccessManager, \
    QNetworkRequest, QNetworkReply

from E5Network.E5NetworkProxyFactory import proxyAuthenticationRequired
try:
    from E5Network.E5SslErrorHandler import E5SslErrorHandler
    SSL_AVAILABLE = True
except ImportError:
    SSL_AVAILABLE = False


class E5XmlRpcClient(QObject):
    """
    Class implementing a xmlrpc client for Qt.
    """
    def __init__(self, url, parent=None):
        """
        Constructor
        
        @param url xmlrpc handler URL (string or QUrl)
        @param parent parent object (QObject)
        """
        super(E5XmlRpcClient, self).__init__(parent)
        
        # attributes for the network objects
        self.__networkManager = QNetworkAccessManager(self)
        self.__networkManager.proxyAuthenticationRequired.connect(
            proxyAuthenticationRequired)
        self.__networkManager.finished.connect(self.__replyFinished)
        if SSL_AVAILABLE:
            self.__sslErrorHandler = E5SslErrorHandler(self)
            self.__networkManager.sslErrors.connect(self.__sslErrors)
        
        self.__callmap = {}
        
        self.__request = QNetworkRequest(QUrl(url))
        self.__request.setRawHeader(b"User-Agent", b"E5XmlRpcClient/1.0")
        self.__request.setHeader(QNetworkRequest.ContentTypeHeader, "text/xml")
    
    def setUrl(self, url):
        """
        Public slot to set the xmlrpc handler URL.
        
        @param url xmlrpc handler URL (string or QUrl)
        """
        url = QUrl(url)
        if url.isValid():
            self.__request.setUrl(url)
    
    def call(self, method, args, responseCallback, errorCallback):
        """
        Public method to call the remote server.
        
        @param method name of the remote method to be called (string)
        @param args tuple of method arguments (tuple)
        @param responseCallback method to be called with the returned
            result as a tuple (function)
        @param errorCallback method to be called in case of an error
            with error code and error string (function)
        """
        assert isinstance(args, tuple), \
            "argument must be tuple or Fault instance"
        
        data = xmlrpc.dumps(args, method).encode("utf-8")
        reply = self.__networkManager.post(
            self.__request, QByteArray(data))
        self.__callmap[reply] = (responseCallback, errorCallback)
    
    def abort(self):
        """
        Public method to abort all calls.
        """
        for reply in list(self.__callmap):
            if reply.isRunning():
                reply.abort()
    
    def __sslErrors(self, reply, errors):
        """
        Private slot to handle SSL errors.
        
        @param reply reference to the reply object (QNetworkReply)
        @param errors list of SSL errors (list of QSslError)
        """
        ignored = self.__sslErrorHandler.sslErrorsReply(reply, errors)[0]
        if ignored == E5SslErrorHandler.NotIgnored and reply in self.__callmap:
            self.__callmap[reply][1](xmlrpc.TRANSPORT_ERROR, self.tr(
                "SSL Error"))
    
    def __replyFinished(self, reply):
        """
        Private slot handling the receipt of a reply.
        
        @param reply reference to the finished reply (QNetworkReply)
        """
        if reply not in self.__callmap:
            return
        
        if reply.error() != QNetworkReply.NoError:
            self.__callmap[reply][1](xmlrpc.TRANSPORT_ERROR,
                                     reply.errorString())
        else:
            data = bytes(reply.readAll()).decode("utf-8")
            try:
                data = xmlrpc.loads(data)[0]
                self.__callmap[reply][0](data)
            except xmlrpc.Fault as fault:
                self.__callmap[reply][1](fault.faultCode, fault.faultString)
        
        reply.deleteLater()
        del self.__callmap[reply]
