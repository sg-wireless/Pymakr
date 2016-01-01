# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the <a href="http://www.virustotal.com">VirusTotal</a>
API class.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import json

from PyQt5.QtCore import QObject, QUrl, QByteArray, pyqtSignal, qVersion
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply

from E5Gui import E5MessageBox

import Preferences


class VirusTotalAPI(QObject):
    """
    Class implementing the <a href="http://www.virustotal.com">VirusTotal</a>
    API.
    
    @signal checkServiceKeyFinished(bool, str) emitted after the service key
        check has been performed. It gives a flag indicating validity
        (boolean) and an error message in case of a network error (string).
    @signal submitUrlError(str) emitted with the error string, if the URL scan
        submission returned an error.
    @signal urlScanReport(str) emitted with the URL of the URL scan report page
    @signal fileScanReport(str) emitted with the URL of the file scan report
        page
    """
    checkServiceKeyFinished = pyqtSignal(bool, str)
    submitUrlError = pyqtSignal(str)
    urlScanReport = pyqtSignal(str)
    fileScanReport = pyqtSignal(str)
    
    TestServiceKeyScanID = \
        "4feed2c2e352f105f6188efd1d5a558f24aee6971bdf96d5fdb19c197d6d3fad"
    
    ServiceResult_ItemQueued = -2
    ServiceResult_ItemNotPresent = 0
    ServiceResult_ItemPresent = 1
    
    # HTTP Status Codes
    ServiceCode_InvalidKey = 202
    ServiceCode_RateLimitExceeded = 204
    ServiceCode_InvalidPrivilege = 403
    
    GetFileReportPattern = "{0}://www.virustotal.com/vtapi/v2/file/report"
    ScanUrlPattern = "{0}://www.virustotal.com/vtapi/v2/url/scan"
    GetUrlReportPattern = "{0}://www.virustotal.com/vtapi/v2/url/report"
    GetIpAddressReportPattern = \
        "{0}://www.virustotal.com/vtapi/v2/ip-address/report"
    GetDomainReportPattern = "{0}://www.virustotal.com/vtapi/v2/domain/report"
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(VirusTotalAPI, self).__init__(parent)
        
        self.__replies = []
        
        self.__loadSettings()
        
        self.__lastIP = ""
        self.__lastDomain = ""
        self.__ipReportDlg = None
        self.__domainReportDlg = None
    
    def __loadSettings(self):
        """
        Private method to load the settings.
        """
        if Preferences.getHelp("VirusTotalSecure"):
            protocol = "https"
        else:
            protocol = "http"
        self.GetFileReportUrl = self.GetFileReportPattern.format(protocol)
        self.ScanUrlUrl = self.ScanUrlPattern.format(protocol)
        self.GetUrlReportUrl = self.GetUrlReportPattern.format(protocol)
        self.GetIpAddressReportUrl = self.GetIpAddressReportPattern.format(
            protocol)
        self.GetDomainReportUrl = self.GetDomainReportPattern.format(protocol)
        
        self.errorMessages = {
            204: self.tr("Request limit has been reached."),
            0: self.tr("Requested item is not present."),
            -2: self.tr("Requested item is still queued."),
        }
    
    def preferencesChanged(self):
        """
        Public slot to handle a change of preferences.
        """
        self.__loadSettings()
    
    def checkServiceKeyValidity(self, key, protocol=""):
        """
        Public method to check the validity of the given service key.
        
        @param key service key (string)
        @param protocol protocol used to access VirusTotal (string)
        """
        if protocol == "":
            urlStr = self.GetFileReportUrl
        else:
            urlStr = self.GetFileReportPattern.format(protocol)
        request = QNetworkRequest(QUrl(urlStr))
        request.setHeader(QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        params = QByteArray("apikey={0}&resource={1}".format(
            key, self.TestServiceKeyScanID).encode("utf-8"))
        
        import Helpviewer.HelpWindow
        nam = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()
        reply = nam.post(request, params)
        reply.finished.connect(self.__checkServiceKeyValidityFinished)
        self.__replies.append(reply)
    
    def __checkServiceKeyValidityFinished(self):
        """
        Private slot to determine the result of the service key validity check.
        """
        res = False
        msg = ""
        
        reply = self.sender()
        if reply.error() == QNetworkReply.NoError:
            res = True
        elif reply.error() == self.ServiceCode_InvalidKey:
            res = False
        else:
            msg = reply.errorString()
        self.__replies.remove(reply)
        reply.deleteLater()
        
        self.checkServiceKeyFinished.emit(res, msg)
    
    def submitUrl(self, url):
        """
        Public method to submit an URL to be scanned.
        
        @param url url to be scanned (QUrl)
        """
        request = QNetworkRequest(QUrl(self.ScanUrlUrl))
        request.setHeader(QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        params = QByteArray("apikey={0}&url=".format(
            Preferences.getHelp("VirusTotalServiceKey")).encode("utf-8"))\
            .append(QUrl.toPercentEncoding(url.toString()))
        
        import Helpviewer.HelpWindow
        nam = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()
        reply = nam.post(request, params)
        reply.finished.connect(self.__submitUrlFinished)
        self.__replies.append(reply)
    
    def __submitUrlFinished(self):
        """
        Private slot to determine the result of the URL scan submission.
        """
        reply = self.sender()
        if reply.error() == QNetworkReply.NoError:
            result = json.loads(str(reply.readAll(), "utf-8"))
            if result["response_code"] == self.ServiceResult_ItemPresent:
                self.urlScanReport.emit(result["permalink"])
                self.__getUrlScanReportUrl(result["scan_id"])
            else:
                if result["response_code"] in self.errorMessages:
                    msg = self.errorMessages[result["response_code"]]
                else:
                    msg = result["verbose_msg"]
                self.submitUrlError.emit(msg)
        elif reply.error() == self.ServiceCode_RateLimitExceeded:
            self.submitUrlError.emit(
                self.errorMessages[result[self.ServiceCode_RateLimitExceeded]])
        else:
            self.submitUrlError.emit(reply.errorString())
        self.__replies.remove(reply)
        reply.deleteLater()
    
    def __getUrlScanReportUrl(self, scanId):
        """
        Private method to get the report URL for a URL scan.
        
        @param scanId ID of the scan to get the report URL for (string)
        """
        request = QNetworkRequest(QUrl(self.GetUrlReportUrl))
        request.setHeader(QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        params = QByteArray("apikey={0}&resource={1}".format(
            Preferences.getHelp("VirusTotalServiceKey"), scanId)
            .encode("utf-8"))
        
        import Helpviewer.HelpWindow
        nam = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()
        reply = nam.post(request, params)
        reply.finished.connect(self.__getUrlScanReportUrlFinished)
        self.__replies.append(reply)
    
    def __getUrlScanReportUrlFinished(self):
        """
        Private slot to determine the result of the URL scan report URL
        request.
        """
        reply = self.sender()
        if reply.error() == QNetworkReply.NoError:
            result = json.loads(str(reply.readAll(), "utf-8"))
            if "filescan_id" in result and result["filescan_id"] is not None:
                self.__getFileScanReportUrl(result["filescan_id"])
        self.__replies.remove(reply)
        reply.deleteLater()
    
    def __getFileScanReportUrl(self, scanId):
        """
        Private method to get the report URL for a file scan.
        
        @param scanId ID of the scan to get the report URL for (string)
        """
        request = QNetworkRequest(QUrl(self.GetFileReportUrl))
        request.setHeader(QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        params = QByteArray("apikey={0}&resource={1}".format(
            Preferences.getHelp("VirusTotalServiceKey"), scanId)
            .encode("utf-8"))
        
        import Helpviewer.HelpWindow
        nam = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()
        reply = nam.post(request, params)
        reply.finished.connect(self.__getFileScanReportUrlFinished)
        self.__replies.append(reply)
    
    def __getFileScanReportUrlFinished(self):
        """
        Private slot to determine the result of the file scan report URL
        request.
        """
        reply = self.sender()
        if reply.error() == QNetworkReply.NoError:
            result = json.loads(str(reply.readAll(), "utf-8"))
            self.fileScanReport.emit(result["permalink"])
        self.__replies.remove(reply)
        reply.deleteLater()
    
    def getIpAddressReport(self, ipAddress):
        """
        Public method to retrieve a report for an IP address.
        
        @param ipAddress valid IPv4 address in dotted quad notation
        @type str
        """
        self.__lastIP = ipAddress
        
        queryItems = [
            ("apikey", Preferences.getHelp("VirusTotalServiceKey")),
            ("ip", ipAddress),
        ]
        url = QUrl(self.GetIpAddressReportUrl)
        if qVersion() >= "5.0.0":
            from PyQt5.QtCore import QUrlQuery
            query = QUrlQuery()
            query.setQueryItems(queryItems)
            url.setQuery(query)
        else:
            url.setQueryItems(queryItems)
        request = QNetworkRequest(url)
        
        import Helpviewer.HelpWindow
        nam = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()
        reply = nam.get(request)
        reply.finished.connect(self.__getIpAddressReportFinished)
        self.__replies.append(reply)
    
    def __getIpAddressReportFinished(self):
        """
        Private slot to process the IP address report data.
        """
        reply = self.sender()
        if reply.error() == QNetworkReply.NoError:
            result = json.loads(str(reply.readAll(), "utf-8"))
            if result["response_code"] == 0:
                E5MessageBox.information(
                    None,
                    self.tr("VirusTotal IP Address Report"),
                    self.tr("""VirusTotal does not have any information for"""
                            """ the given IP address."""))
            elif result["response_code"] == -1:
                E5MessageBox.information(
                    None,
                    self.tr("VirusTotal IP Address Report"),
                    self.tr("""The submitted IP address is invalid."""))
            else:
                owner = result["as_owner"]
                resolutions = result["resolutions"]
                try:
                    urls = result["detected_urls"]
                except KeyError:
                    urls = []
                
                from .VirusTotalIpReportDialog import VirusTotalIpReportDialog
                self.__ipReportDlg = VirusTotalIpReportDialog(
                    self.__lastIP, owner, resolutions, urls)
                self.__ipReportDlg.show()
        self.__replies.remove(reply)
        reply.deleteLater()
    
    def getDomainReport(self, domain):
        """
        Public method to retrieve a report for a domain.
        
        @param domain domain name
        @type str
        """
        self.__lastDomain = domain
        
        queryItems = [
            ("apikey", Preferences.getHelp("VirusTotalServiceKey")),
            ("domain", domain),
        ]
        url = QUrl(self.GetDomainReportUrl)
        if qVersion() >= "5.0.0":
            from PyQt5.QtCore import QUrlQuery
            query = QUrlQuery()
            query.setQueryItems(queryItems)
            url.setQuery(query)
        else:
            url.setQueryItems(queryItems)
        request = QNetworkRequest(url)
        
        import Helpviewer.HelpWindow
        nam = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()
        reply = nam.get(request)
        reply.finished.connect(self.__getDomainReportFinished)
        self.__replies.append(reply)
    
    def __getDomainReportFinished(self):
        """
        Private slot to process the IP address report data.
        """
        reply = self.sender()
        if reply.error() == QNetworkReply.NoError:
            result = json.loads(str(reply.readAll(), "utf-8"))
            if result["response_code"] == 0:
                E5MessageBox.information(
                    None,
                    self.tr("VirusTotal Domain Report"),
                    self.tr("""VirusTotal does not have any information for"""
                            """ the given domain."""))
            elif result["response_code"] == -1:
                E5MessageBox.information(
                    None,
                    self.tr("VirusTotal Domain Report"),
                    self.tr("""The submitted domain address is invalid."""))
            else:
                resolutions = result["resolutions"]
                try:
                    urls = result["detected_urls"]
                except KeyError:
                    urls = []
                try:
                    subdomains = result["subdomains"]
                except KeyError:
                    subdomains = []
                try:
                    bdCategory = result["BitDefender category"]
                except KeyError:
                    bdCategory = self.tr("not available")
                try:
                    tmCategory = result["TrendMicro category"]
                except KeyError:
                    tmCategory = self.tr("not available")
                try:
                    wtsCategory = result["Websense ThreatSeeker category"]
                except KeyError:
                    wtsCategory = self.tr("not available")
                try:
                    whois = result["whois"]
                except KeyError:
                    whois = ""
                
                from .VirusTotalDomainReportDialog import \
                    VirusTotalDomainReportDialog
                self.__domainReportDlg = VirusTotalDomainReportDialog(
                    self.__lastDomain, resolutions, urls, subdomains,
                    bdCategory, tmCategory, wtsCategory, whois)
                self.__domainReportDlg.show()
        self.__replies.remove(reply)
        reply.deleteLater()
    
    def close(self):
        """
        Public slot to close the API.
        """
        for reply in self.__replies:
            reply.abort()
        
        self.__ipReportDlg and self.__ipReportDlg.close()
        self.__domainReportDlg and self.__domainReportDlg.close()
