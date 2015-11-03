# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a network reply delegate allowing to check redirects.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtNetwork import QNetworkRequest


class FollowRedirectReply(QObject):
    """
    Class implementing a network reply delegate allowing to check redirects.
    """
    finished = pyqtSignal()
    
    def __init__(self, url, manager, maxRedirects=5):
        """
        Constructor
        
        @param url URL to get (QUrl)
        @param manager reference to the network access manager
            (QNetworkAccessManager)
        @keyparam maxRedirects maximum allowed redirects (integer)
        """
        super(FollowRedirectReply, self).__init__()
        
        self.__manager = manager
        self.__maxRedirects = maxRedirects
        self.__redirectCount = 0
        
        self.__reply = self.__manager.get(QNetworkRequest(url))
        self.__reply.finished.connect(self.__replyFinished)
    
    def reply(self):
        """
        Public method to get the reply object.
        
        @return reference to the reply object (QNetworkReply)
        """
        return self.__reply
    
    def originalUrl(self):
        """
        Public method to get the original URL.
        
        @return original URL (QUrl)
        """
        return self.__reply.request().url()
    
    def url(self):
        """
        Public method to get the final URL (after redirects).
        
        @return final URL (QUrl)
        """
        return self.__reply.url()
    
    def error(self):
        """
        Public method to get the error information.
        
        @return error code (QNetworkReply.NetworkError)
        """
        return self.__reply.error()
    
    def errorString(self):
        """
        Public method to get the error message.
        
        @return error message (string)
        """
        return self.__reply.errorString()
    
    def readAll(self):
        """
        Public method to read all received data.
        
        @return received raw data (QByteArray)
        """
        return self.__reply.readAll()
    
    def close(self):
        """
        Public method to close the data stream.
        """
        self.__reply.close()
    
    def __replyFinished(self):
        """
        Private slot handling the receipt of the requested data.
        """
        replyStatus = self.__reply.attribute(
            QNetworkRequest.HttpStatusCodeAttribute)
        if (replyStatus != 301 and replyStatus != 302) or \
           self.__redirectCount == self.__maxRedirects:
            self.finished.emit()
            return
        
        self.__redirectCount += 1
        
        redirectUrl = self.__reply.attribute(
            QNetworkRequest.RedirectionTargetAttribute)
        self.__reply.close()
        self.__reply.deleteLater()
        self.__reply = None
        
        self.__reply = self.__manager.get(QNetworkRequest(redirectUrl))
        self.__reply.finished.connect(self.__replyFinished)
