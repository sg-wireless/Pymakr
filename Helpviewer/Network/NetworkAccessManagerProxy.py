# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a network access manager proxy for web pages.
"""

from __future__ import unicode_literals

from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
try:
    from PyQt5.QtNetwork import QSslError   # __IGNORE_EXCEPTION__ __IGNORE_WARNING__
    SSL_AVAILABLE = True
except ImportError:
    SSL_AVAILABLE = False


class NetworkAccessManagerProxy(QNetworkAccessManager):
    """
    Class implementing a network access manager proxy for web pages.
    """
    primaryManager = None
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(NetworkAccessManagerProxy, self).__init__(parent)
        self.__webPage = None
    
    def setWebPage(self, page):
        """
        Public method to set the reference to a web page.
        
        @param page reference to the web page object (HelpWebPage)
        """
        assert page is not None
        self.__webPage = page
    
    def setPrimaryNetworkAccessManager(self, manager):
        """
        Public method to set the primary network access manager.
        
        @param manager reference to the network access manager object
            (QNetworkAccessManager)
        """
        assert manager is not None
        if self.__class__.primaryManager is None:
            self.__class__.primaryManager = manager
        self.setCookieJar(self.__class__.primaryManager.cookieJar())
        # do not steal ownership
        self.cookieJar().setParent(self.__class__.primaryManager)
        
        if SSL_AVAILABLE:
            self.sslErrors.connect(self.__class__.primaryManager.sslErrors)
        self.proxyAuthenticationRequired.connect(
            self.__class__.primaryManager.proxyAuthenticationRequired)
        self.authenticationRequired.connect(
            self.__class__.primaryManager.authenticationRequired)
        self.finished.connect(self.__class__.primaryManager.finished)
    
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
        if self.primaryManager is not None:
            pageRequest = QNetworkRequest(request)
            if self.__webPage is not None:
                self.__webPage.populateNetworkRequest(pageRequest)
            return self.primaryManager.createRequest(
                op, pageRequest, outgoingData)
        else:
            return QNetworkAccessManager.createRequest(
                self, op, request, outgoingData)
