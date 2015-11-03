# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a QNetworkReply subclass reporting a blocked request.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QTimer
from PyQt5.QtNetwork import QNetworkReply, QNetworkAccessManager


class AdBlockBlockedNetworkReply(QNetworkReply):
    """
    Class implementing a QNetworkReply subclass reporting a blocked request.
    """
    def __init__(self, request, subscription, rule, parent=None):
        """
        Constructor
        
        @param request reference to the request object (QNetworkRequest)
        @param subscription subscription containing the matched rule
            (AdBlockSubscription)
        @param rule matching rule (AdBlockRule)
        @param parent reference to the parent object (QObject)
        """
        super(AdBlockBlockedNetworkReply, self).__init__(parent)
        self.setOperation(QNetworkAccessManager.GetOperation)
        self.setRequest(request)
        self.setUrl(request.url())
        self.setError(
            QNetworkReply.ContentAccessDenied,
            "AdBlockRule:{0} ({1})"
            .format(subscription.title(), rule.filter()))
        QTimer.singleShot(0, self.__fireSignals)
    
    def __fireSignals(self):
        """
        Private method to send some signals to end the connection.
        """
        self.error[QNetworkReply.NetworkError].emit(
            QNetworkReply.ContentAccessDenied)
        self.finished.emit()
    
    def readData(self, maxlen):
        """
        Public method to retrieve data from the reply object.
        
        @param maxlen maximum number of bytes to read (integer)
        @return string containing the data (string)
        """
        return None
    
    def abort(self):
        """
        Public slot to abort the operation.
        """
        # do nothing
        pass
