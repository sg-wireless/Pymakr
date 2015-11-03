# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a scheme access handler for FTP.
"""

from __future__ import unicode_literals

from PyQt5.QtNetwork import QNetworkAccessManager

from .SchemeAccessHandler import SchemeAccessHandler


class FtpAccessHandler(SchemeAccessHandler):
    """
    Class implementing a scheme access handler for FTP.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(FtpAccessHandler, self).__init__(parent)
        
        self.__authenticatorCache = {}
        self.__proxyAuthenticator = None
    
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
        if op == QNetworkAccessManager.GetOperation:
            from .FtpReply import FtpReply
            return FtpReply(request.url(), self, self.parent())
        else:
            return None
    
    def setAuthenticator(self, realm, authenticator):
        """
        Public method to add or change an authenticator in our cache.
        
        @param realm name of the realm the authenticator belongs to (string)
        @param authenticator authenticator to add to the cache
            (QAuthenticator). If it is None, the entry will be deleted from
            the cache.
        """
        if realm:
            if authenticator:
                self.__authenticatorCache[realm] = authenticator
            else:
                if realm in self.__authenticatorCache:
                    del self.__authenticatorCache[realm]
    
    def getAuthenticator(self, realm):
        """
        Public method to get an authenticator for the given realm.
        
        @param realm name of the realm to get the authenticator for (string)
        @return authenticator for the given realm (QAuthenticator) or None
        """
        if realm in self.__authenticatorCache:
            return self.__authenticatorCache[realm]
        else:
            return None
    
    def setProxyAuthenticator(self, authenticator):
        """
        Public method to add or change the authenticator for the FTP proxy.
        
        @param authenticator authenticator for the FTP proxy (QAuthenticator)
        """
        self.__proxyAuthenticator = authenticator
    
    def getProxyAuthenticator(self):
        """
        Public method to get the authenticator for the FTP proxy.
        
        @return authenticator for the FTP proxy (QAuthenticator)
        """
        return self.__proxyAuthenticator
