# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a network proxy factory.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import Qt, QUrl, QCoreApplication, QRegExp
from PyQt5.QtWidgets import QDialog
from PyQt5.QtNetwork import QNetworkProxyFactory, QNetworkProxy, \
    QNetworkProxyQuery

from E5Gui import E5MessageBox

import Preferences
import Globals
import Utilities


def schemeFromProxyType(proxyType):
    """
    Module function to determine the scheme name from the proxy type.
    
    @param proxyType type of the proxy (QNetworkProxy.ProxyType)
    @return scheme (string, one of Http, Https, Ftp)
    """
    scheme = ""
    if proxyType == QNetworkProxy.HttpProxy:
        scheme = "Http"
    elif proxyType == QNetworkProxy.HttpCachingProxy:
        scheme = "Https"
    elif proxyType == QNetworkProxy.FtpCachingProxy:
        scheme = "Ftp"
    elif proxyType == QNetworkProxy.NoProxy:
        scheme = "NoProxy"
    return scheme


def proxyAuthenticationRequired(proxy, auth):
    """
    Module slot to handle a proxy authentication request.
    
    @param proxy reference to the proxy object (QNetworkProxy)
    @param auth reference to the authenticator object (QAuthenticator)
    """
    info = QCoreApplication.translate(
        "E5NetworkProxyFactory",
        "<b>Connect to proxy '{0}' using:</b>")\
        .format(Utilities.html_encode(proxy.hostName()))
    
    from UI.AuthenticationDialog import AuthenticationDialog
    dlg = AuthenticationDialog(info, proxy.user(), True)
    dlg.setData(proxy.user(), proxy.password())
    if dlg.exec_() == QDialog.Accepted:
        username, password = dlg.getData()
        auth.setUser(username)
        auth.setPassword(password)
        if dlg.shallSave():
            scheme = schemeFromProxyType(proxy.type())
            if scheme and scheme != "NoProxy":
                Preferences.setUI("ProxyUser/{0}".format(scheme), username)
                Preferences.setUI("ProxyPassword/{0}".format(scheme), password)
            proxy.setUser(username)
            proxy.setPassword(password)


class HostnameMatcher(object):
    """
    Class implementing a matcher for host names.
    """
    def __init__(self, pattern):
        """
        Constructor
        
        @param pattern pattern to be matched against
        @type str
        """
        self.__regExp = None
        self.setPattern(pattern)
    
    def setPattern(self, pattern):
        """
        Public method to set the match pattern.
        
        @param pattern pattern to be matched against
        """
        self.__pattern = pattern
        
        if "?" in pattern or "*" in pattern:
            regexp = "^.*{0}.*$".format(
                pattern
                .replace(".", "\\.")
                .replace("*", ".*")
                .replace("?", ".")
            )
            self.__regExp = QRegExp(regexp, Qt.CaseInsensitive)
    
    def pattern(self):
        """
        Public method to get the match pattern.
        
        @return match pattern
        @rtype str
        """
        return self.__pattern
    
    def match(self, host):
        """
        Public method to test the given string.
        
        @param host host name to be matched
        @type str
        @return flag indicating a successful match
        @rtype bool
        """
        if self.__regExp is None:
            return self.__pattern in host
        
        return self.__regExp.indexIn(host) > -1


class E5NetworkProxyFactory(QNetworkProxyFactory):
    """
    Class implementing a network proxy factory.
    """
    def __init__(self):
        """
        Constructor
        """
        super(E5NetworkProxyFactory, self).__init__()
        
        self.__hostnameMatchers = []
        self.__exceptions = ""
    
    def __setExceptions(self, exceptions):
        """
        Private method to set the host name exceptions.
        
        @param exceptions list of exceptions separated by ','
        @type str
        """
        self.__hostnameMatchers = []
        self.__exceptions = exceptions
        for exception in self.__exceptions.split(","):
            self.__hostnameMatchers.append(HostnameMatcher(exception.strip()))
    
    def queryProxy(self, query):
        """
        Public method to determine a proxy for a given query.
        
        @param query reference to the query object (QNetworkProxyQuery)
        @return list of proxies in order of preference (list of QNetworkProxy)
        """
        if query.queryType() == QNetworkProxyQuery.UrlRequest and \
           query.protocolTag() in ["http", "https", "ftp"]:
            # use proxy at all ?
            if not Preferences.getUI("UseProxy"):
                return [QNetworkProxy(QNetworkProxy.NoProxy)]
            
            # test for exceptions
            exceptions = Preferences.getUI("ProxyExceptions")
            if exceptions != self.__exceptions:
                self.__setExceptions(exceptions)
            urlHost = query.url().host()
            for matcher in self.__hostnameMatchers:
                if matcher.match(urlHost):
                    return [QNetworkProxy(QNetworkProxy.NoProxy)]
            
            # determine proxy
            if Preferences.getUI("UseSystemProxy"):
                proxyList = QNetworkProxyFactory.systemProxyForQuery(query)
                if not Globals.isWindowsPlatform() and \
                   len(proxyList) == 1 and \
                   proxyList[0].type() == QNetworkProxy.NoProxy:
                    # try it the Python way
                    # scan the environment for variables named <scheme>_proxy
                    # scan over whole environment to make this case insensitive
                    for name, value in os.environ.items():
                        name = name.lower()
                        if value and name[-6:] == '_proxy' and \
                           name[:-6] == query.protocolTag().lower():
                            url = QUrl(value)
                            if url.scheme() == "http":
                                proxyType = QNetworkProxy.HttpProxy
                            elif url.scheme() == "https":
                                proxyType = QNetworkProxy.HttpCachingProxy
                            elif url.scheme() == "ftp":
                                proxyType = QNetworkProxy.FtpCachingProxy
                            else:
                                proxyType = QNetworkProxy.HttpProxy
                            proxy = QNetworkProxy(
                                proxyType, url.host(), url.port(),
                                url.userName(), url.password())
                            proxyList = [proxy]
                            break
                if proxyList:
                    scheme = schemeFromProxyType(proxyList[0].type())
                    if scheme == "":
                        scheme = "Http"
                    if scheme != "NoProxy":
                        proxyList[0].setUser(
                            Preferences.getUI("ProxyUser/{0}".format(scheme)))
                        proxyList[0].setPassword(
                            Preferences.getUI(
                                "ProxyPassword/{0}".format(scheme)))
                    return proxyList
                else:
                    return [QNetworkProxy(QNetworkProxy.NoProxy)]
            else:
                if Preferences.getUI("UseHttpProxyForAll"):
                    protocolKey = "Http"
                else:
                    protocolKey = query.protocolTag().capitalize()
                host = Preferences.getUI("ProxyHost/{0}".format(protocolKey))
                if not host:
                    E5MessageBox.critical(
                        None,
                        QCoreApplication.translate(
                            "E5NetworkProxyFactory",
                            "Proxy Configuration Error"),
                        QCoreApplication.translate(
                            "E5NetworkProxyFactory",
                            """Proxy usage was activated"""
                            """ but no proxy host for protocol"""
                            """ '{0}' configured.""").format(protocolKey))
                    return [QNetworkProxy(QNetworkProxy.DefaultProxy)]
                else:
                    if protocolKey in ["Http", "Https", "Ftp"]:
                        if query.protocolTag() == "ftp":
                            proxyType = QNetworkProxy.FtpCachingProxy
                        elif query.protocolTag() == "https":
                            proxyType = QNetworkProxy.HttpCachingProxy
                        else:
                            proxyType = QNetworkProxy.HttpProxy
                        proxy = QNetworkProxy(
                            proxyType, host,
                            Preferences.getUI("ProxyPort/" + protocolKey),
                            Preferences.getUI("ProxyUser/" + protocolKey),
                            Preferences.getUI("ProxyPassword/" + protocolKey))
                    else:
                        proxy = QNetworkProxy(QNetworkProxy.DefaultProxy)
                    return [proxy, QNetworkProxy(QNetworkProxy.DefaultProxy)]
        else:
            return [QNetworkProxy(QNetworkProxy.NoProxy)]
