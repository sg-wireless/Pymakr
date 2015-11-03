# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a network reply object for special data.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QTimer, QIODevice, QByteArray
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest


class NetworkReply(QNetworkReply):
    """
    Class implementing a QNetworkReply subclass for special data.
    """
    def __init__(self, request, fileData, mimeType, parent=None):
        """
        Constructor
        
        @param request reference to the request object (QNetworkRequest)
        @param fileData reference to the data buffer (QByteArray)
        @param mimeType for the reply (string)
        @param parent reference to the parent object (QObject)
        """
        super(NetworkReply, self).__init__(parent)
        
        self.__data = fileData
        
        self.setRequest(request)
        self.setOpenMode(QIODevice.ReadOnly)
        
        self.setHeader(QNetworkRequest.ContentTypeHeader, mimeType)
        self.setHeader(QNetworkRequest.ContentLengthHeader,
                       QByteArray.number(fileData.length()))
        self.setAttribute(QNetworkRequest.HttpStatusCodeAttribute, 200)
        self.setAttribute(QNetworkRequest.HttpReasonPhraseAttribute, "OK")
        QTimer.singleShot(0, lambda: self.metaDataChanged.emit())
        QTimer.singleShot(0, lambda: self.readyRead.emit())
        QTimer.singleShot(0, lambda: self.finished.emit())
    
    def abort(self):
        """
        Public slot to abort the operation.
        """
        # do nothing
        pass
    
    def bytesAvailable(self):
        """
        Public method to determined the bytes available for being read.
        
        @return bytes available (integer)
        """
        return self.__data.length() + QNetworkReply.bytesAvailable(self)
    
    def readData(self, maxlen):
        """
        Public method to retrieve data from the reply object.
        
        @param maxlen maximum number of bytes to read (integer)
        @return string containing the data (bytes)
        """
        len_ = min(maxlen, self.__data.length())
        buffer = bytes(self.__data[:len_])
        self.__data.remove(0, len_)
        return buffer
    
    def isFinished(self):
        """
        Public method to check, if the reply has finished.
        
        @return flag indicating the finished state (boolean)
        """
        return True
