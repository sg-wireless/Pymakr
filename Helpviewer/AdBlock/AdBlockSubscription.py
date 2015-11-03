# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the AdBlock subscription class.
"""

from __future__ import unicode_literals

import os
import re
import hashlib
import base64

from PyQt5.QtCore import pyqtSignal, Qt, QObject, QByteArray, QDateTime, \
    QUrl, QCryptographicHash, QFile, QIODevice, QTextStream, QDate, QTime, \
    qVersion
from PyQt5.QtNetwork import QNetworkReply

from E5Gui import E5MessageBox

import Utilities
import Preferences


class AdBlockSubscription(QObject):
    """
    Class implementing the AdBlock subscription.
    
    @signal changed() emitted after the subscription has changed
    @signal rulesChanged() emitted after the subscription's rules have changed
    @signal enabledChanged(bool) emitted after the enabled state was changed
    """
    changed = pyqtSignal()
    rulesChanged = pyqtSignal()
    enabledChanged = pyqtSignal(bool)
    
    def __init__(self, url, custom, parent=None, default=False):
        """
        Constructor
        
        @param url AdBlock URL for the subscription (QUrl)
        @param custom flag indicating a custom subscription (boolean)
        @param parent reference to the parent object (QObject)
        @param default flag indicating a default subscription (boolean)
        """
        super(AdBlockSubscription, self).__init__(parent)
        
        self.__custom = custom
        self.__url = url.toEncoded()
        self.__enabled = False
        self.__downloading = None
        self.__defaultSubscription = default
        
        self.__title = ""
        self.__location = QByteArray()
        self.__lastUpdate = QDateTime()
        self.__requiresLocation = ""
        self.__requiresTitle = ""
        
        self.__updatePeriod = 0     # update period in hours, 0 = use default
        self.__remoteModified = QDateTime()
        
        self.__rules = []   # list containing all AdBlock rules
        
        self.__networkExceptionRules = []
        self.__networkBlockRules = []
        self.__domainRestrictedCssRules = []
        self.__elementHidingRules = ""
        self.__documentRules = []
        self.__elemhideRules = []
        
        self.__checksumRe = re.compile(
            r"""^\s*!\s*checksum[\s\-:]+([\w\+\/=]+).*\n""",
            re.IGNORECASE | re.MULTILINE)
        self.__expiresRe = re.compile(
            r"""(?:expires:|expires after)\s*(\d+)\s*(hour|h)?""",
            re.IGNORECASE)
        self.__remoteModifiedRe = re.compile(
            r"""!\s*(?:Last modified|Updated):\s*(\d{1,2})\s*"""
            r"""(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*"""
            r"""(\d{2,4})\s*((\d{1,2}):(\d{2}))?""",
            re.IGNORECASE)
        
        self.__monthNameToNumber = {
            "Jan": 1,
            "Feb": 2,
            "Mar": 3,
            "Apr": 4,
            "May": 5,
            "Jun": 6,
            "Jul": 7,
            "Aug": 8,
            "Sep": 9,
            "Oct": 10,
            "Nov": 11,
            "Dec": 12
        }
        
        self.__parseUrl(url)
    
    def __parseUrl(self, url):
        """
        Private method to parse the AdBlock URL for the subscription.
        
        @param url AdBlock URL for the subscription (QUrl)
        """
        if url.scheme() != "abp":
            return
        
        if url.path() != "subscribe":
            return
        
        if qVersion() >= "5.0.0":
            from PyQt5.QtCore import QUrlQuery
            urlQuery = QUrlQuery(url)
            self.__title = QUrl.fromPercentEncoding(
                QByteArray(urlQuery.queryItemValue("title").encode()))
            self.__enabled = urlQuery.queryItemValue("enabled") != "false"
            self.__location = QByteArray(QUrl.fromPercentEncoding(
                QByteArray(urlQuery.queryItemValue("location").encode()))
                .encode("utf-8"))
            
            # Check for required subscription
            self.__requiresLocation = QUrl.fromPercentEncoding(
                QByteArray(urlQuery.queryItemValue(
                    "requiresLocation").encode()))
            self.__requiresTitle = QUrl.fromPercentEncoding(
                QByteArray(urlQuery.queryItemValue("requiresTitle").encode()))
            if self.__requiresLocation and self.__requiresTitle:
                import Helpviewer.HelpWindow
                Helpviewer.HelpWindow.HelpWindow.adBlockManager()\
                    .loadRequiredSubscription(self.__requiresLocation,
                                              self.__requiresTitle)
            
            lastUpdateString = urlQuery.queryItemValue("lastUpdate")
            self.__lastUpdate = QDateTime.fromString(lastUpdateString,
                                                     Qt.ISODate)
        else:
            self.__title = \
                QUrl.fromPercentEncoding(url.encodedQueryItemValue(b"title"))
            self.__enabled = QUrl.fromPercentEncoding(
                url.encodedQueryItemValue(b"enabled")) != "false"
            self.__location = QByteArray(QUrl.fromPercentEncoding(
                url.encodedQueryItemValue(b"location")).encode("utf-8"))
            
            # Check for required subscription
            self.__requiresLocation = QUrl.fromPercentEncoding(
                url.encodedQueryItemValue(b"requiresLocation"))
            self.__requiresTitle = QUrl.fromPercentEncoding(
                url.encodedQueryItemValue(b"requiresTitle"))
            if self.__requiresLocation and self.__requiresTitle:
                import Helpviewer.HelpWindow
                Helpviewer.HelpWindow.HelpWindow.adBlockManager()\
                    .loadRequiredSubscription(self.__requiresLocation,
                                              self.__requiresTitle)
            
            lastUpdateByteArray = url.encodedQueryItemValue(b"lastUpdate")
            lastUpdateString = QUrl.fromPercentEncoding(lastUpdateByteArray)
            self.__lastUpdate = QDateTime.fromString(lastUpdateString,
                                                     Qt.ISODate)
        
        self.__loadRules()
    
    def url(self):
        """
        Public method to generate the URL for this subscription.
        
        @return AdBlock URL for the subscription (QUrl)
        """
        url = QUrl()
        url.setScheme("abp")
        url.setPath("subscribe")
        
        queryItems = []
        queryItems.append(("location", bytes(self.__location).decode()))
        queryItems.append(("title", self.__title))
        if self.__requiresLocation and self.__requiresTitle:
            queryItems.append(("requiresLocation", self.__requiresLocation))
            queryItems.append(("requiresTitle", self.__requiresTitle))
        if not self.__enabled:
            queryItems.append(("enabled", "false"))
        if self.__lastUpdate.isValid():
            queryItems.append(("lastUpdate",
                               self.__lastUpdate.toString(Qt.ISODate)))
        if qVersion() >= "5.0.0":
            from PyQt5.QtCore import QUrlQuery
            query = QUrlQuery()
            query.setQueryItems(queryItems)
            url.setQuery(query)
        else:
            url.setQueryItems(queryItems)
        return url
    
    def isEnabled(self):
        """
        Public method to check, if the subscription is enabled.
        
        @return flag indicating the enabled status (boolean)
        """
        return self.__enabled
    
    def setEnabled(self, enabled):
        """
        Public method to set the enabled status.
        
        @param enabled flag indicating the enabled status (boolean)
        """
        if self.__enabled == enabled:
            return
        
        self.__enabled = enabled
        self.enabledChanged.emit(enabled)
    
    def title(self):
        """
        Public method to get the subscription title.
        
        @return subscription title (string)
        """
        return self.__title
    
    def setTitle(self, title):
        """
        Public method to set the subscription title.
        
        @param title subscription title (string)
        """
        if self.__title == title:
            return
        
        self.__title = title
        self.changed.emit()
    
    def location(self):
        """
        Public method to get the subscription location.
        
        @return URL of the subscription location (QUrl)
        """
        return QUrl.fromEncoded(self.__location)
    
    def setLocation(self, url):
        """
        Public method to set the subscription location.
        
        @param url URL of the subscription location (QUrl)
        """
        if url == self.location():
            return
        
        self.__location = url.toEncoded()
        self.__lastUpdate = QDateTime()
        self.changed.emit()
    
    def requiresLocation(self):
        """
        Public method to get the location of a required subscription.
        
        @return location of a required subscription (string)
        """
        return self.__requiresLocation
    
    def lastUpdate(self):
        """
        Public method to get the date and time of the last update.
        
        @return date and time of the last update (QDateTime)
        """
        return self.__lastUpdate
    
    def rulesFileName(self):
        """
        Public method to get the name of the rules file.
        
        @return name of the rules file (string)
        """
        if self.location().scheme() == "file":
            return self.location().toLocalFile()
        
        if self.__location.isEmpty():
            return ""
        
        sha1 = bytes(QCryptographicHash.hash(
            self.__location, QCryptographicHash.Sha1).toHex()).decode()
        dataDir = os.path.join(
            Utilities.getConfigDir(), "browser", "subscriptions")
        if not os.path.exists(dataDir):
            os.makedirs(dataDir)
        fileName = os.path.join(
            dataDir, "adblock_subscription_{0}".format(sha1))
        return fileName
    
    def __loadRules(self):
        """
        Private method to load the rules of the subscription.
        """
        fileName = self.rulesFileName()
        f = QFile(fileName)
        if f.exists():
            if not f.open(QIODevice.ReadOnly):
                E5MessageBox.warning(
                    None,
                    self.tr("Load subscription rules"),
                    self.tr(
                        """Unable to open adblock file '{0}' for reading.""")
                    .format(fileName))
            else:
                textStream = QTextStream(f)
                header = textStream.readLine(1024)
                if not header.startswith("[Adblock"):
                    E5MessageBox.warning(
                        None,
                        self.tr("Load subscription rules"),
                        self.tr("""AdBlock file '{0}' does not start"""
                                """ with [Adblock.""")
                        .format(fileName))
                    f.close()
                    f.remove()
                    self.__lastUpdate = QDateTime()
                else:
                    from .AdBlockRule import AdBlockRule
                    
                    self.__updatePeriod = 0
                    self.__remoteModified = QDateTime()
                    self.__rules = []
                    self.__rules.append(AdBlockRule(header, self))
                    while not textStream.atEnd():
                        line = textStream.readLine()
                        self.__rules.append(AdBlockRule(line, self))
                        expires = self.__expiresRe.search(line)
                        if expires:
                            period, kind = expires.groups()
                            if kind:
                                # hours
                                self.__updatePeriod = int(period)
                            else:
                                # days
                                self.__updatePeriod = int(period) * 24
                        remoteModified = self.__remoteModifiedRe.search(line)
                        if remoteModified:
                            day, month, year, time, hour, minute = \
                                remoteModified.groups()
                            self.__remoteModified.setDate(
                                QDate(int(year),
                                      self.__monthNameToNumber[month],
                                      int(day))
                            )
                            if time:
                                self.__remoteModified.setTime(
                                    QTime(int(hour), int(minute)))
                    self.__populateCache()
                    self.changed.emit()
        elif not fileName.endswith("_custom"):
            self.__lastUpdate = QDateTime()
        
        self.checkForUpdate()
    
    def checkForUpdate(self):
        """
        Public method to check for an update.
        """
        if self.__updatePeriod:
            updatePeriod = self.__updatePeriod
        else:
            updatePeriod = Preferences.getHelp("AdBlockUpdatePeriod") * 24
        if not self.__lastUpdate.isValid() or \
           (self.__remoteModified.isValid() and
            self.__remoteModified.addSecs(updatePeriod * 3600) <
                QDateTime.currentDateTime()) or \
           self.__lastUpdate.addSecs(updatePeriod * 3600) < \
                QDateTime.currentDateTime():
            self.updateNow()
    
    def updateNow(self):
        """
        Public method to update the subscription immediately.
        """
        if self.__downloading is not None:
            return
        
        if not self.location().isValid():
            return
        
        if self.location().scheme() == "file":
            self.__lastUpdate = QDateTime.currentDateTime()
            self.__loadRules()
            return
        
        import Helpviewer.HelpWindow
        from Helpviewer.Network.FollowRedirectReply import FollowRedirectReply
        self.__downloading = FollowRedirectReply(
            self.location(),
            Helpviewer.HelpWindow.HelpWindow.networkAccessManager())
        self.__downloading.finished.connect(self.__rulesDownloaded)
    
    def __rulesDownloaded(self):
        """
        Private slot to deal with the downloaded rules.
        """
        reply = self.sender()
        
        response = reply.readAll()
        reply.close()
        self.__downloading = None
        
        if reply.error() != QNetworkReply.NoError:
            if not self.__defaultSubscription:
                # don't show error if we try to load the default
                E5MessageBox.warning(
                    None,
                    self.tr("Downloading subscription rules"),
                    self.tr(
                        """<p>Subscription rules could not be"""
                        """ downloaded.</p><p>Error: {0}</p>""")
                    .format(reply.errorString()))
            else:
                # reset after first download attempt
                self.__defaultSubscription = False
            return
        
        if response.isEmpty():
            E5MessageBox.warning(
                None,
                self.tr("Downloading subscription rules"),
                self.tr("""Got empty subscription rules."""))
            return
        
        fileName = self.rulesFileName()
        QFile.remove(fileName)
        f = QFile(fileName)
        if not f.open(QIODevice.ReadWrite):
            E5MessageBox.warning(
                None,
                self.tr("Downloading subscription rules"),
                self.tr(
                    """Unable to open adblock file '{0}' for writing.""")
                .file(fileName))
            return
        f.write(response)
        f.close()
        self.__lastUpdate = QDateTime.currentDateTime()
        if self.__validateCheckSum(fileName):
            self.__loadRules()
        else:
            QFile.remove(fileName)
        self.__downloading = None
        reply.deleteLater()
    
    def __validateCheckSum(self, fileName):
        """
        Private method to check the subscription file's checksum.
        
        @param fileName name of the file containing the subscription (string)
        @return flag indicating a valid file (boolean). A file is considered
            valid, if the checksum is OK or the file does not contain a
            checksum (i.e. cannot be checked).
        """
        try:
            f = open(fileName, "r", encoding="utf-8")
            data = f.read()
            f.close()
        except (IOError, OSError):
            return False
        
        match = re.search(self.__checksumRe, data)
        if match:
            expectedChecksum = match.group(1)
        else:
            # consider it as valid
            return True
        
        # normalize the data
        data = re.sub(r"\r", "", data)              # normalize eol
        data = re.sub(r"\n+", "\n", data)           # remove empty lines
        data = re.sub(self.__checksumRe, "", data)  # remove checksum line
        
        # calculate checksum
        md5 = hashlib.md5()
        md5.update(data.encode("utf-8"))
        calculatedChecksum = base64.b64encode(md5.digest()).decode()\
            .rstrip("=")
        if calculatedChecksum == expectedChecksum:
            return True
        else:
            res = E5MessageBox.yesNo(
                None,
                self.tr("Downloading subscription rules"),
                self.tr(
                    """<p>AdBlock subscription <b>{0}</b> has a wrong"""
                    """ checksum.<br/>"""
                    """Found: {1}<br/>"""
                    """Calculated: {2}<br/>"""
                    """Use it anyway?</p>""")
                .format(self.__title, expectedChecksum,
                        calculatedChecksum))
            return res
    
    def saveRules(self):
        """
        Public method to save the subscription rules.
        """
        fileName = self.rulesFileName()
        if not fileName:
            return
        
        f = QFile(fileName)
        if not f.open(QIODevice.ReadWrite | QIODevice.Truncate):
            E5MessageBox.warning(
                None,
                self.tr("Saving subscription rules"),
                self.tr(
                    """Unable to open adblock file '{0}' for writing.""")
                .format(fileName))
            return
        
        textStream = QTextStream(f)
        if not self.__rules or not self.__rules[0].isHeader():
            textStream << "[Adblock Plus 1.1.1]\n"
        for rule in self.__rules:
            textStream << rule.filter() << "\n"
    
    def match(self, req, urlDomain, urlString):
        """
        Public method to check the subscription for a matching rule.
        
        @param req reference to the network request (QNetworkRequest)
        @param urlDomain domain of the URL (string)
        @param urlString URL (string)
        @return reference to the rule object or None (AdBlockRule)
        """
        for rule in self.__networkExceptionRules:
            if rule.networkMatch(req, urlDomain, urlString):
                return None
        
        for rule in self.__networkBlockRules:
            if rule.networkMatch(req, urlDomain, urlString):
                return rule
        
        return None
    
    def adBlockDisabledForUrl(self, url):
        """
        Public method to check, if AdBlock is disabled for the given URL.
        
        @param url URL to check (QUrl)
        @return flag indicating disabled state (boolean)
        """
        for rule in self.__documentRules:
            if rule.urlMatch(url):
                return True
        
        return False
    
    def elemHideDisabledForUrl(self, url):
        """
        Public method to check, if element hiding is disabled for the given
        URL.
        
        @param url URL to check (QUrl)
        @return flag indicating disabled state (boolean)
        """
        if self.adBlockDisabledForUrl(url):
            return True
        
        for rule in self.__elemhideRules:
            if rule.urlMatch(url):
                return True
        
        return False
    
    def elementHidingRules(self):
        """
        Public method to get the element hiding rules.
        
        @return element hiding rules (string)
        """
        return self.__elementHidingRules
    
    def elementHidingRulesForDomain(self, domain):
        """
        Public method to get the element hiding rules for the given domain.
        
        @param domain domain name (string)
        @return element hiding rules (string)
        """
        rules = ""
        
        for rule in self.__domainRestrictedCssRules:
            if rule.matchDomain(domain):
                rules += rule.cssSelector() + ","
        
        return rules
    
    def rule(self, offset):
        """
        Public method to get a specific rule.
        
        @param offset offset of the rule (integer)
        @return requested rule (AdBlockRule)
        """
        if offset >= len(self.__rules):
            return None
        
        return self.__rules[offset]
    
    def allRules(self):
        """
        Public method to get the list of rules.
        
        @return list of rules (list of AdBlockRule)
        """
        return self.__rules[:]
    
    def addRule(self, rule):
        """
        Public method to add a rule.
        
        @param rule reference to the rule to add (AdBlockRule)
        @return offset of the rule (integer)
        """
        self.__rules.append(rule)
        self.__populateCache()
        self.rulesChanged.emit()
        
        return len(self.__rules) - 1
    
    def removeRule(self, offset):
        """
        Public method to remove a rule given the offset.
        
        @param offset offset of the rule to remove (integer)
        """
        if offset < 0 or offset > len(self.__rules):
            return
        
        del self.__rules[offset]
        self.__populateCache()
        self.rulesChanged.emit()
    
    def replaceRule(self, rule, offset):
        """
        Public method to replace a rule given the offset.
        
        @param rule reference to the rule to set (AdBlockRule)
        @param offset offset of the rule to remove (integer)
        @return requested rule (AdBlockRule)
        """
        if offset >= len(self.__rules):
            return None
        
        self.__rules[offset] = rule
        self.__populateCache()
        self.rulesChanged.emit()
        
        return self.__rules[offset]
    
    def __populateCache(self):
        """
        Private method to populate the various rule caches.
        """
        self.__networkExceptionRules = []
        self.__networkBlockRules = []
        self.__domainRestrictedCssRules = []
        self.__elementHidingRules = ""
        self.__documentRules = []
        self.__elemhideRules = []
        
        for rule in self.__rules:
            if not rule.isEnabled():
                continue
            
            if rule.isCSSRule():
                if rule.isDomainRestricted():
                    self.__domainRestrictedCssRules.append(rule)
                else:
                    self.__elementHidingRules += rule.cssSelector() + ","
            elif rule.isDocument():
                self.__documentRules.append(rule)
            elif rule.isElementHiding():
                self.__elemhideRules.append(rule)
            elif rule.isException():
                self.__networkExceptionRules.append(rule)
            else:
                self.__networkBlockRules.append(rule)
    
    def canEditRules(self):
        """
        Public method to check, if rules can be edited.
        
        @return flag indicating rules may be edited (boolean)
        """
        return self.__custom
    
    def canBeRemoved(self):
        """
        Public method to check, if the subscription can be removed.
        
        @return flag indicating removal is allowed (boolean)
        """
        return not self.__custom and not self.__defaultSubscription
    
    def setRuleEnabled(self, offset, enabled):
        """
        Public method to enable a specific rule.
        
        @param offset offset of the rule (integer)
        @param enabled new enabled state (boolean)
        @return reference to the changed rule (AdBlockRule)
        """
        if offset >= len(self.__rules):
            return None
        
        rule = self.__rules[offset]
        rule.setEnabled(enabled)
        if rule.isCSSRule():
            import Helpviewer.HelpWindow
            self.__populateCache()
            Helpviewer.HelpWindow.HelpWindow.mainWindow()\
                .reloadUserStyleSheet()
        
        return rule
