# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a scheme access handler for AdBlock URLs.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import qVersion, QByteArray
from PyQt5.QtNetwork import QNetworkAccessManager

from E5Gui import E5MessageBox

from Helpviewer.Network.SchemeAccessHandler import SchemeAccessHandler
from Helpviewer.Network.EmptyNetworkReply import EmptyNetworkReply


class AdBlockAccessHandler(SchemeAccessHandler):
    """
    Class implementing a scheme access handler for AdBlock URLs.
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
        if op != QNetworkAccessManager.GetOperation:
            return None
        
        url = request.url()
        if url.path() != "subscribe":
            return None
        
        if qVersion() >= "5.0.0":
            from PyQt5.QtCore import QUrlQuery, QUrl
            title = QUrl.fromPercentEncoding(
                QByteArray(QUrlQuery(url).queryItemValue("title").encode()))
        else:
            from PyQt5.QtCore import QUrl
            title = QUrl.fromPercentEncoding(
                url.encodedQueryItemValue(b"title"))
        if not title:
            return None
        res = E5MessageBox.yesNo(
            None,
            self.tr("Subscribe?"),
            self.tr(
                """<p>Subscribe to this AdBlock subscription?</p>"""
                """<p>{0}</p>""").format(title))
        if res:
            from .AdBlockSubscription import AdBlockSubscription
            import Helpviewer.HelpWindow
            
            dlg = Helpviewer.HelpWindow.HelpWindow.adBlockManager()\
                .showDialog()
            subscription = AdBlockSubscription(
                url, False,
                Helpviewer.HelpWindow.HelpWindow.adBlockManager())
            Helpviewer.HelpWindow.HelpWindow.adBlockManager()\
                .addSubscription(subscription)
            dlg.addSubscription(subscription, False)
            dlg.setFocus()
            dlg.raise_()
        
        return EmptyNetworkReply(self.parent())
