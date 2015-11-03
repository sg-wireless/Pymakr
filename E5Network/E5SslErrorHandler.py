# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a SSL error handler.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import qVersion, QObject, QByteArray
from PyQt5.QtNetwork import QSslCertificate, QSslConfiguration, QSslSocket, \
    QSslError, QSsl

from E5Gui import E5MessageBox

import Preferences
import Utilities
import Globals


class E5SslErrorHandler(QObject):
    """
    Class implementing a handler for SSL errors.
    
    It also initializes the default SSL configuration with certificates
    permanently accepted by the user already.
    """
    NotIgnored = 0
    SystemIgnored = 1
    UserIgnored = 2
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(E5SslErrorHandler, self).__init__(parent)
        
        caList = self.__getSystemCaCertificates()
        if Preferences.Prefs.settings.contains("Help/CaCertificatesDict"):
            # port old entries stored under 'Help'
            certificateDict = Globals.toDict(
                Preferences.Prefs.settings.value("Help/CaCertificatesDict"))
            Preferences.Prefs.settings.setValue(
                "Ssl/CaCertificatesDict", certificateDict)
            Preferences.Prefs.settings.remove("Help/CaCertificatesDict")
        else:
            certificateDict = Globals.toDict(
                Preferences.Prefs.settings.value("Ssl/CaCertificatesDict"))
        for server in certificateDict:
            for cert in QSslCertificate.fromData(certificateDict[server]):
                if cert not in caList:
                    caList.append(cert)
        sslCfg = QSslConfiguration.defaultConfiguration()
        sslCfg.setCaCertificates(caList)
        sslCfg.setProtocol(QSsl.AnyProtocol)
        try:
            sslCfg.setSslOption(QSsl.SslOptionDisableCompression, True)
        except AttributeError:
            pass
        QSslConfiguration.setDefaultConfiguration(sslCfg)
    
    def sslErrorsReplySlot(self, reply, errors):
        """
        Public slot to handle SSL errors for a network reply.
        
        @param reply reference to the reply object (QNetworkReply)
        @param errors list of SSL errors (list of QSslError)
        """
        self.sslErrorsReply(reply, errors)
    
    def sslErrorsReply(self, reply, errors):
        """
        Public slot to handle SSL errors for a network reply.
        
        @param reply reference to the reply object (QNetworkReply)
        @param errors list of SSL errors (list of QSslError)
        @return tuple indicating to ignore the SSL errors (one of NotIgnored,
            SystemIgnored or UserIgnored) and indicating a change of the
            default SSL configuration (boolean)
        """
        url = reply.url()
        ignore, defaultChanged = self.sslErrors(errors, url.host(), url.port())
        if ignore:
            if defaultChanged:
                reply.setSslConfiguration(
                    QSslConfiguration.defaultConfiguration())
            reply.ignoreSslErrors()
        else:
            reply.abort()
        
        return ignore, defaultChanged
    
    def sslErrors(self, errors, server, port=-1):
        """
        Public method to handle SSL errors.
        
        @param errors list of SSL errors (list of QSslError)
        @param server name of the server (string)
        @keyparam port value of the port (integer)
        @return tuple indicating to ignore the SSL errors (one of NotIgnored,
            SystemIgnored or UserIgnored) and indicating a change of the
            default SSL configuration (boolean)
        """
        caMerge = {}
        certificateDict = Globals.toDict(
            Preferences.Prefs.settings.value("Ssl/CaCertificatesDict"))
        for caServer in certificateDict:
            caMerge[caServer] = QSslCertificate.fromData(
                certificateDict[caServer])
        caNew = []
        
        errorStrings = []
        if port != -1:
            server += ":{0:d}".format(port)
        if errors:
            for err in errors:
                if err.error() == QSslError.NoError:
                    continue
                if server in caMerge and err.certificate() in caMerge[server]:
                    continue
                errorStrings.append(err.errorString())
                if not err.certificate().isNull():
                    cert = err.certificate()
                    if cert not in caNew:
                        caNew.append(cert)
        if not errorStrings:
            return E5SslErrorHandler.SystemIgnored, False
        
        errorString = '.</li><li>'.join(errorStrings)
        ret = E5MessageBox.yesNo(
            None,
            self.tr("SSL Errors"),
            self.tr("""<p>SSL Errors for <br /><b>{0}</b>"""
                    """<ul><li>{1}</li></ul></p>"""
                    """<p>Do you want to ignore these errors?</p>""")
            .format(server, errorString),
            icon=E5MessageBox.Warning)
        
        if ret:
            caRet = False
            if len(caNew) > 0:
                certinfos = []
                for cert in caNew:
                    certinfos.append(self.__certToString(cert))
                caRet = E5MessageBox.yesNo(
                    None,
                    self.tr("Certificates"),
                    self.tr(
                        """<p>Certificates:<br/>{0}<br/>"""
                        """Do you want to accept all these certificates?"""
                        """</p>""")
                    .format("".join(certinfos)))
                if caRet:
                    if server not in caMerge:
                        caMerge[server] = []
                    for cert in caNew:
                        caMerge[server].append(cert)
                    
                    sslCfg = QSslConfiguration.defaultConfiguration()
                    caList = sslCfg.caCertificates()
                    for cert in caNew:
                        caList.append(cert)
                    sslCfg.setCaCertificates(caList)
                    sslCfg.setProtocol(QSsl.AnyProtocol)
                    QSslConfiguration.setDefaultConfiguration(sslCfg)
                    
                    certificateDict = {}
                    for server in caMerge:
                        pems = QByteArray()
                        for cert in caMerge[server]:
                            pems.append(cert.toPem() + b'\n')
                        certificateDict[server] = pems
                    Preferences.Prefs.settings.setValue(
                        "Ssl/CaCertificatesDict",
                        certificateDict)
            
            return E5SslErrorHandler.UserIgnored, caRet
        
        else:
            return E5SslErrorHandler.NotIgnored, False
    
    def __certToString(self, cert):
        """
        Private method to convert a certificate to a formatted string.
        
        @param cert certificate to convert (QSslCertificate)
        @return formatted string (string)
        """
        result = "<p>"
        
        if qVersion() >= "5.0.0":
            result += self.tr("Name: {0}")\
                .format(Utilities.html_encode(Utilities.decodeString(
                    ", ".join(cert.subjectInfo(QSslCertificate.CommonName)))))
            
            result += self.tr("<br/>Organization: {0}")\
                .format(Utilities.html_encode(Utilities.decodeString(
                    ", ".join(cert.subjectInfo(
                        QSslCertificate.Organization)))))
            
            result += self.tr("<br/>Issuer: {0}")\
                .format(Utilities.html_encode(Utilities.decodeString(
                    ", ".join(cert.issuerInfo(QSslCertificate.CommonName)))))
        else:
            result += self.tr("Name: {0}")\
                .format(Utilities.html_encode(Utilities.decodeString(
                    cert.subjectInfo(QSslCertificate.CommonName))))
            
            result += self.tr("<br/>Organization: {0}")\
                .format(Utilities.html_encode(Utilities.decodeString(
                    cert.subjectInfo(QSslCertificate.Organization))))
            
            result += self.tr("<br/>Issuer: {0}")\
                .format(Utilities.html_encode(Utilities.decodeString(
                    cert.issuerInfo(QSslCertificate.CommonName))))
        
        result += self.tr(
            "<br/>Not valid before: {0}<br/>Valid Until: {1}")\
            .format(Utilities.html_encode(
                    cert.effectiveDate().toString("yyyy-MM-dd")),
                    Utilities.html_encode(
                        cert.expiryDate().toString("yyyy-MM-dd")))
        
        result += "</p>"
        
        return result
    
    def __getSystemCaCertificates(self):
        """
        Private method to get the list of system certificates.
        
        @return list of system certificates (list of QSslCertificate)
        """
        caList = QSslCertificate.fromData(Globals.toByteArray(
            Preferences.Prefs.settings.value("Ssl/SystemCertificates")))
        if not caList:
            caList = QSslSocket.systemCaCertificates()
        return caList
