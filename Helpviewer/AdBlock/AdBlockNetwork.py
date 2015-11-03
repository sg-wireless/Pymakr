# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the network block class.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtNetwork import QNetworkRequest

from .AdBlockBlockedNetworkReply import AdBlockBlockedNetworkReply


class AdBlockNetwork(QObject):
    """
    Class implementing a network block.
    """
    def block(self, request):
        """
        Public method to check for a network block.
        
        @param request reference to the request object (QNetworkRequest)
        @return reply object (QNetworkReply) or None
        """
        url = request.url()
        urlString = bytes(url.toEncoded()).decode()
        urlDomain = url.host()
        urlScheme = url.scheme()
        refererHost = QUrl.fromEncoded(request.rawHeader(b"Referer")).host()
        
        import Helpviewer.HelpWindow
        manager = Helpviewer.HelpWindow.HelpWindow.adBlockManager()
        if not manager.isEnabled() or \
           not self.canRunOnScheme(urlScheme) or \
           manager.isHostExcepted(urlDomain) or \
           manager.isHostExcepted(refererHost):
            return None
        
        for subscription in manager.subscriptions():
            if subscription.isEnabled():
                blockedRule = subscription.match(request, urlDomain, urlString)
                if blockedRule:
                    webPage = request.attribute(QNetworkRequest.User + 100)
                    if webPage is not None:
                        if not self.__canBeBlocked(webPage.url()):
                            return None
                        
                        webPage.addAdBlockRule(blockedRule, url)
                    
                    reply = AdBlockBlockedNetworkReply(
                        request, subscription, blockedRule, self)
                    return reply
        
        return None
    
    def canRunOnScheme(self, scheme):
        """
        Public method to check, if AdBlock can be performed on the scheme.
        
        @param scheme scheme to check (string)
        @return flag indicating, that AdBlock can be performed (boolean)
        """
        return scheme not in ["data", "eric", "qthelp", "qrc", "file", "abp"]
    
    def __canBeBlocked(self, url):
        """
        Private method to check, if an URL can be blocked.
        
        @param url URL to be checked (QUrl)
        @return flag indicating, that the URL can be blocked (boolean)
        """
        import Helpviewer.HelpWindow
        manager = Helpviewer.HelpWindow.HelpWindow.adBlockManager()
        if manager.isHostExcepted(url.host()):
            return False
        for subscription in manager.subscriptions():
            if subscription.isEnabled() and \
                    subscription.adBlockDisabledForUrl(url):
                return False
        
        return True
