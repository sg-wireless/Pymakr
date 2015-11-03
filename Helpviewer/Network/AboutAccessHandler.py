# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a scheme access handler for about schemes.
"""

from __future__ import unicode_literals

from .SchemeAccessHandler import SchemeAccessHandler


class AboutAccessHandler(SchemeAccessHandler):
    """
    Class implementing a scheme access handler for about schemes.
    """
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
        from .NetworkProtocolUnknownErrorReply import \
            NetworkProtocolUnknownErrorReply
        return NetworkProtocolUnknownErrorReply("about", self.parent())
