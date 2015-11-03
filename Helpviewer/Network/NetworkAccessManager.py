# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a QNetworkAccessManager subclass.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSignal, QByteArray, qVersion
from PyQt5.QtWidgets import QDialog
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, \
    QNetworkReply

from E5Network.E5NetworkProxyFactory import E5NetworkProxyFactory, \
    proxyAuthenticationRequired
try:
    from PyQt5.QtNetwork import QSslSocket
    from E5Network.E5SslErrorHandler import E5SslErrorHandler
    SSL_AVAILABLE = True
except ImportError:
    SSL_AVAILABLE = False

import Preferences
import Utilities


class NetworkAccessManager(QNetworkAccessManager):
    """
    Class implementing a QNetworkAccessManager subclass.
    
    @signal requestCreated emitted after the request has been created passing
        the operation, a reference to the network request and a reference to
        the network reply (QNetworkAccessManager.Operation, QNetworkRequest,
        QNetworkReply)
    """
    requestCreated = pyqtSignal(
        QNetworkAccessManager.Operation, QNetworkRequest, QNetworkReply)
    
    def __init__(self, engine, parent=None):
        """
        Constructor
        
        @param engine reference to the help engine (QHelpEngine)
        @param parent reference to the parent object (QObject)
        """
        super(NetworkAccessManager, self).__init__(parent)
        
        self.__adblockNetwork = None
        
        self.__schemeHandlers = {}  # dictionary of scheme handlers
        
        self.__proxyFactory = E5NetworkProxyFactory()
        self.setProxyFactory(self.__proxyFactory)
        
        self.__setDiskCache()
        self.languagesChanged()
        
        if SSL_AVAILABLE:
            self.__sslErrorHandler = E5SslErrorHandler(self)
            self.sslErrors.connect(self.__sslErrorHandler.sslErrorsReplySlot)
        
        self.proxyAuthenticationRequired.connect(proxyAuthenticationRequired)
        self.authenticationRequired.connect(self.__authenticationRequired)
        
        self.__doNotTrack = Preferences.getHelp("DoNotTrack")
        self.__sendReferer = Preferences.getHelp("SendReferer")
        
        # register scheme handlers
        if engine:
            from .QtHelpAccessHandler import QtHelpAccessHandler
            self.setSchemeHandler("qthelp", QtHelpAccessHandler(engine, self))
        
        from .EricAccessHandler import EricAccessHandler
        self.setSchemeHandler("eric", EricAccessHandler(self))
        
        from .AboutAccessHandler import AboutAccessHandler
        self.setSchemeHandler("about", AboutAccessHandler(self))
        
        from Helpviewer.AdBlock.AdBlockAccessHandler import \
            AdBlockAccessHandler
        self.setSchemeHandler("abp", AdBlockAccessHandler(self))
        
        from .FtpAccessHandler import FtpAccessHandler
        self.setSchemeHandler("ftp", FtpAccessHandler(self))
        
        from .FileAccessHandler import FileAccessHandler
        self.setSchemeHandler("file", FileAccessHandler(self))
    
    def setSchemeHandler(self, scheme, handler):
        """
        Public method to register a scheme handler.
        
        @param scheme access scheme (string)
        @param handler reference to the scheme handler object
            (SchemeAccessHandler)
        """
        self.__schemeHandlers[scheme] = handler
    
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
        scheme = request.url().scheme()
        if scheme == "https" and \
                (not SSL_AVAILABLE or not QSslSocket.supportsSsl()):
            from .NetworkProtocolUnknownErrorReply import \
                NetworkProtocolUnknownErrorReply
            return NetworkProtocolUnknownErrorReply(scheme, self)
        
        import Helpviewer.HelpWindow
        
        if op == QNetworkAccessManager.PostOperation and \
                outgoingData is not None:
            outgoingDataByteArray = outgoingData.peek(1024 * 1024)
            Helpviewer.HelpWindow.HelpWindow.passwordManager().post(
                request, outgoingDataByteArray)
        
        reply = None
        if scheme in self.__schemeHandlers:
            reply = self.__schemeHandlers[scheme]\
                        .createRequest(op, request, outgoingData)
        if reply is not None:
            return reply
        
        # give GreaseMonkey the chance to create a request
        reply = Helpviewer.HelpWindow.HelpWindow.greaseMonkeyManager()\
            .createRequest(op, request, outgoingData)
        if reply is not None:
            return reply
        
        req = QNetworkRequest(request)
        if req.rawHeader(b"X-Eric6-UserLoadAction") == QByteArray(b"1"):
            req.setRawHeader(b"X-Eric6-UserLoadAction", QByteArray())
            req.setAttribute(QNetworkRequest.User + 200, "")
        else:
            req.setAttribute(
                QNetworkRequest.User + 200, req.rawHeader(b"Referer"))
        
        if hasattr(QNetworkRequest, 'HttpPipeliningAllowedAttribute'):
            req.setAttribute(
                QNetworkRequest.HttpPipeliningAllowedAttribute, True)
        if not self.__acceptLanguage.isEmpty():
            req.setRawHeader(b"Accept-Language", self.__acceptLanguage)
        
        # AdBlock code
        if op == QNetworkAccessManager.GetOperation:
            if self.__adblockNetwork is None:
                self.__adblockNetwork = \
                    Helpviewer.HelpWindow.HelpWindow.adBlockManager().network()
            reply = self.__adblockNetwork.block(req)
            if reply is not None:
                reply.setParent(self)
                return reply
        
        # set cache policy
        if op == QNetworkAccessManager.GetOperation:
            urlHost = req.url().host()
            for host in Preferences.getHelp("NoCacheHosts"):
                if host in urlHost:
                    req.setAttribute(
                        QNetworkRequest.CacheLoadControlAttribute,
                        QNetworkRequest.AlwaysNetwork)
                    break
            else:
                req.setAttribute(
                    QNetworkRequest.CacheLoadControlAttribute,
                    Preferences.getHelp("CachePolicy"))
        else:
            req.setAttribute(
                QNetworkRequest.CacheLoadControlAttribute,
                QNetworkRequest.AlwaysNetwork)
        
        # Do Not Track feature
        if self.__doNotTrack:
            req.setRawHeader(b"DNT", b"1")
            req.setRawHeader(b"X-Do-Not-Track", b"1")
        
        # Send referer header?
        if not self.__sendReferer and \
           req.url().host() not in Preferences.getHelp("SendRefererWhitelist"):
            req.setRawHeader(b"Referer", b"")
        
        reply = QNetworkAccessManager.createRequest(
            self, op, req, outgoingData)
        self.requestCreated.emit(op, req, reply)
        
        return reply
    
    def __authenticationRequired(self, reply, auth):
        """
        Private slot to handle an authentication request.
        
        @param reply reference to the reply object (QNetworkReply)
        @param auth reference to the authenticator object (QAuthenticator)
        """
        urlRoot = "{0}://{1}"\
            .format(reply.url().scheme(), reply.url().authority())
        realm = auth.realm()
        if not realm and 'realm' in auth.options():
            realm = auth.option("realm")
        if realm:
            info = self.tr("<b>Enter username and password for '{0}', "
                           "realm '{1}'</b>").format(urlRoot, realm)
        else:
            info = self.tr("<b>Enter username and password for '{0}'</b>")\
                .format(urlRoot)
        
        from UI.AuthenticationDialog import AuthenticationDialog
        import Helpviewer.HelpWindow
        
        dlg = AuthenticationDialog(info, auth.user(),
                                   Preferences.getUser("SavePasswords"),
                                   Preferences.getUser("SavePasswords"))
        if Preferences.getUser("SavePasswords"):
            username, password = \
                Helpviewer.HelpWindow.HelpWindow.passwordManager().getLogin(
                    reply.url(), realm)
            if username:
                dlg.setData(username, password)
        if dlg.exec_() == QDialog.Accepted:
            username, password = dlg.getData()
            auth.setUser(username)
            auth.setPassword(password)
            if Preferences.getUser("SavePasswords"):
                Helpviewer.HelpWindow.HelpWindow.passwordManager().setLogin(
                    reply.url(), realm, username, password)
    
    def preferencesChanged(self):
        """
        Public slot to signal a change of preferences.
        """
        self.__setDiskCache()
        
        self.__doNotTrack = Preferences.getHelp("DoNotTrack")
        self.__sendReferer = Preferences.getHelp("SendReferer")
    
    def languagesChanged(self):
        """
        Public slot to (re-)load the list of accepted languages.
        """
        from Helpviewer.HelpLanguagesDialog import HelpLanguagesDialog
        languages = Preferences.toList(
            Preferences.Prefs.settings.value(
                "Help/AcceptLanguages",
                HelpLanguagesDialog.defaultAcceptLanguages()))
        self.__acceptLanguage = HelpLanguagesDialog.httpString(languages)
    
    def __setDiskCache(self):
        """
        Private method to set the disk cache.
        """
        if Preferences.getHelp("DiskCacheEnabled"):
            from PyQt5.QtWebKit import qWebKitVersion
            from .NetworkDiskCache import NetworkDiskCache
            diskCache = NetworkDiskCache(self)
            location = os.path.join(
                Utilities.getConfigDir(), "browser", 'cache',
                "{0}-Qt{1}".format(qWebKitVersion(), qVersion()))
            size = Preferences.getHelp("DiskCacheSize") * 1024 * 1024
            diskCache.setCacheDirectory(location)
            diskCache.setMaximumCacheSize(size)
        else:
            diskCache = None
        self.setCache(diskCache)
