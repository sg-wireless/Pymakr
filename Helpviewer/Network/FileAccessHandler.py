# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a scheme access handler for file.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QFileInfo
from PyQt5.QtNetwork import QNetworkAccessManager

from .SchemeAccessHandler import SchemeAccessHandler


class FileAccessHandler(SchemeAccessHandler):
    """
    Class implementing a scheme access handler for FTP.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(FileAccessHandler, self).__init__(parent)
    
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
            fileInfo = QFileInfo(request.url().toLocalFile())
            if not fileInfo.isDir() or \
               not fileInfo.isReadable() or \
               not fileInfo.exists():
                return None
            from .FileReply import FileReply
            return FileReply(request.url(), self.parent())
        else:
            return None
