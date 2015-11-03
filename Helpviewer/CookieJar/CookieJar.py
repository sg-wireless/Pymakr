# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a QNetworkCookieJar subclass with various accept policies.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSignal, QByteArray, QDataStream, QIODevice, \
    QSettings, QDateTime
from PyQt5.QtNetwork import QNetworkCookieJar, QNetworkCookie
from PyQt5.QtWebKit import QWebSettings

from Utilities.AutoSaver import AutoSaver
import Utilities
import Preferences


class CookieJar(QNetworkCookieJar):
    """
    Class implementing a QNetworkCookieJar subclass with various accept
    policies.
    
    @signal cookiesChanged() emitted after the cookies have been changed
    """
    cookiesChanged = pyqtSignal()
    
    JAR_VERSION = 23
    
    AcceptAlways = 0
    AcceptNever = 1
    AcceptOnlyFromSitesNavigatedTo = 2

    KeepUntilExpire = 0
    KeepUntilExit = 1
    KeepUntilTimeLimit = 2
    
    Allow = 0
    Block = 1
    AllowForSession = 2
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(CookieJar, self).__init__(parent)
        
        self.__loaded = False
        self.__acceptCookies = self.AcceptOnlyFromSitesNavigatedTo
        self.__saveTimer = AutoSaver(self, self.save)
        
        self.__cookiesFile = os.path.join(Utilities.getConfigDir(),
                                          "browser", "cookies.ini")
    
    def saveCookies(self, cookiesList):
        """
        Public method to save the cookies.
        
        @param cookiesList list of cookies to be saved
        @return saved cookies as a byte array (QByteArray)
        """
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)
        stream.setVersion(QDataStream.Qt_4_6)
        stream.writeUInt16(self.JAR_VERSION)
        stream.writeUInt32(len(cookiesList))
        for cookie in cookiesList:
            stream << cookie.toRawForm()
        
        return data
    
    def loadCookies(self, cookies):
        """
        Public method to restore the saved cookies.
        
        @param cookies byte array containing the saved cookies (QByteArray)
        @return list of cookies
        """
        if cookies.isEmpty():
            return []
        
        cookiesList = []
        data = QByteArray(cookies)
        stream = QDataStream(data, QIODevice.ReadOnly)
        stream.setVersion(QDataStream.Qt_4_6)
        
        version = stream.readUInt16()
        if version != self.JAR_VERSION:
            return []
        
        stream.readUInt32()  # number of cookies
        
        rawCookie = QByteArray()
        while not stream.atEnd():
            stream >> rawCookie
            newCookies = QNetworkCookie.parseCookies(rawCookie)
            for newCookie in newCookies:
                cookiesList.append(newCookie)
        
        return cookiesList
    
    def close(self):
        """
        Public slot to close the cookie jar.
        """
        if self.__loaded and self.__keepCookies == self.KeepUntilExit:
            self.clear()
        self.__saveTimer.saveIfNeccessary()
    
    def clear(self):
        """
        Public method to clear all cookies.
        """
        if not self.__loaded:
            self.load()
        
        self.setAllCookies([])
        self.__saveTimer.changeOccurred()
        self.cookiesChanged.emit()
    
    def load(self):
        """
        Public method to load the cookies.
        """
        if self.__loaded:
            return
        
        cookieSettings = QSettings(self.__cookiesFile, QSettings.IniFormat)
        
        # load cookies
        cookies = cookieSettings.value("Cookies")
        if cookies:
            cookiesList = self.loadCookies(cookies)
        else:
            cookiesList = []
        self.setAllCookies(cookiesList)
        
        # load exceptions
        self.__exceptionsBlock = Preferences.toList(
            cookieSettings.value("Exceptions/block"))
        self.__exceptionsAllow = Preferences.toList(
            cookieSettings.value("Exceptions/allow"))
        self.__exceptionsAllowForSession = Preferences.toList(
            cookieSettings.value("Exceptions/allowForSession"))
        self.__exceptionsBlock.sort()
        self.__exceptionsAllow.sort()
        self.__exceptionsAllowForSession.sort()
        
        self.__acceptCookies = Preferences.getHelp("AcceptCookies")
        self.__keepCookies = Preferences.getHelp("KeepCookiesUntil")
        if self.__keepCookies == self.KeepUntilExit:
            self.setAllCookies([])
        
        self.__filterTrackingCookies = Preferences.toBool(
            Preferences.getHelp("FilterTrackingCookies"))
        
        self.__loaded = True
        self.cookiesChanged.emit()
    
    def save(self):
        """
        Public method to save the cookies.
        """
        if not self.__loaded:
            return
        
        self.__purgeOldCookies()
        
        cookieSettings = QSettings(self.__cookiesFile, QSettings.IniFormat)
        
        cookiesList = self.allCookies()
        for index in range(len(cookiesList) - 1, -1, -1):
            if cookiesList[index].isSessionCookie():
                del cookiesList[index]
        cookies = self.saveCookies(cookiesList)
        
        cookieSettings.setValue("Cookies", cookies)
        cookieSettings.setValue("Exceptions/block", self.__exceptionsBlock)
        cookieSettings.setValue("Exceptions/allow", self.__exceptionsAllow)
        cookieSettings.setValue("Exceptions/allowForSession",
                                self.__exceptionsAllowForSession)
        
        Preferences.setHelp("AcceptCookies", self.__acceptCookies)
        Preferences.setHelp("KeepCookiesUntil", self.__keepCookies)
        Preferences.setHelp("FilterTrackingCookies",
                            self.__filterTrackingCookies)
    
    def __purgeOldCookies(self):
        """
        Private method to purge old cookies.
        """
        cookies = self.allCookies()
        if len(cookies) == 0:
            return
        
        oldCount = len(cookies)
        now = QDateTime.currentDateTime()
        for index in range(len(cookies) - 1, -1, -1):
            if not cookies[index].isSessionCookie() and \
               cookies[index].expirationDate() < now:
                del cookies[index]
        if oldCount == len(cookies):
            return
        self.setAllCookies(cookies)
        self.cookiesChanged.emit()
    
    def cookiesForUrl(self, url):
        """
        Public method to get the cookies for a URL.
        
        @param url URL to get cookies for (QUrl)
        @return list of cookies (list of QNetworkCookie)
        """
        if not self.__loaded:
            self.load()
        
        globalSettings = QWebSettings.globalSettings()
        if globalSettings.testAttribute(QWebSettings.PrivateBrowsingEnabled):
            return []
        
        return QNetworkCookieJar.cookiesForUrl(self, url)
    
    def setCookiesFromUrl(self, cookieList, url):
        """
        Public method to set cookies for a URL.
        
        @param cookieList list of cookies to set (list of QNetworkCookie)
        @param url url to set cookies for (QUrl)
        @return flag indicating cookies were set (boolean)
        """
        if not self.__loaded:
            self.load()
        
        globalSettings = QWebSettings.globalSettings()
        if globalSettings.testAttribute(QWebSettings.PrivateBrowsingEnabled):
            return False
        
        host = url.host()
        eBlock = self.__isOnDomainList(self.__exceptionsBlock, host)
        eAllow = not eBlock and \
            self.__isOnDomainList(self.__exceptionsAllow, host)
        eAllowSession = not eBlock and \
            not eAllow and \
            self.__isOnDomainList(
                self.__exceptionsAllowForSession, host)
        
        addedCookies = False
        acceptInitially = self.__acceptCookies != self.AcceptNever
        if (acceptInitially and not eBlock) or \
           (not acceptInitially and (eAllow or eAllowSession)):
            # url domain == cookie domain
            soon = QDateTime.currentDateTime()
            soon = soon.addDays(90)
            for cookie in cookieList:
                lst = []
                if not (self.__filterTrackingCookies and
                        cookie.name().startsWith(b"__utm")):
                    if eAllowSession:
                        cookie.setExpirationDate(QDateTime())
                    if self.__keepCookies == self.KeepUntilTimeLimit and \
                       not cookie.isSessionCookie and \
                       cookie.expirationDate() > soon:
                        cookie.setExpirationDate(soon)
                    lst.append(cookie)
                    if QNetworkCookieJar.setCookiesFromUrl(self, lst, url):
                        addedCookies = True
                    elif self.__acceptCookies == self.AcceptAlways:
                        # force it in if wanted
                        cookies = self.allCookies()
                        for ocookie in cookies[:]:
                            # does the cookie exist already?
                            if cookie.name() == ocookie.name() and \
                               cookie.domain() == ocookie.domain() and \
                               cookie.path() == ocookie.path():
                                # found a match
                                cookies.remove(ocookie)
                        
                        cookies.append(cookie)
                        self.setAllCookies(cookies)
                        addedCookies = True
        
        if addedCookies:
            self.__saveTimer.changeOccurred()
            self.cookiesChanged.emit()
        
        return addedCookies
    
    def acceptPolicy(self):
        """
        Public method to get the accept policy.
        
        @return current accept policy
        """
        if not self.__loaded:
            self.load()
        return self.__acceptCookies
    
    def setAcceptPolicy(self, policy):
        """
        Public method to set the accept policy.
        
        @param policy accept policy to be set
        """
        if not self.__loaded:
            self.load()
        if policy > self.AcceptOnlyFromSitesNavigatedTo:
            return
        if policy == self.__acceptCookies:
            return
        self.__acceptCookies = policy
        self.__saveTimer.changeOccurred()
    
    def keepPolicy(self):
        """
        Public method to get the keep policy.
        
        @return keep policy
        """
        if not self.__loaded:
            self.load()
        return self.__keepCookies
    
    def setKeepPolicy(self, policy):
        """
        Public method to set the keep policy.
        
        @param policy keep policy to be set
        """
        if not self.__loaded:
            self.load()
        if policy > self.KeepUntilTimeLimit:
            return
        if policy == self.__keepCookies:
            return
        self.__keepCookies = policy
        self.__saveTimer.changeOccurred()
    
    def blockedCookies(self):
        """
        Public method to return the blocked cookies.
        
        @return list of blocked cookies (list of strings)
        """
        if not self.__loaded:
            self.load()
        return self.__exceptionsBlock
    
    def allowedCookies(self):
        """
        Public method to return the allowed cookies.
        
        @return list of allowed cookies (list of strings)
        """
        if not self.__loaded:
            self.load()
        return self.__exceptionsAllow
    
    def allowForSessionCookies(self):
        """
        Public method to return the allowed session cookies.
        
        @return list of allowed session cookies (list of strings)
        """
        if not self.__loaded:
            self.load()
        return self.__exceptionsAllowForSession
    
    def setBlockedCookies(self, list_):
        """
        Public method to set the list of blocked cookies.
        
        @param list_ list of blocked cookies (list of strings)
        """
        if not self.__loaded:
            self.load()
        self.__exceptionsBlock = list_[:]
        self.__exceptionsBlock.sort()
        self.__applyRules()
        self.__saveTimer.changeOccurred()
    
    def setAllowedCookies(self, list_):
        """
        Public method to set the list of allowed cookies.
        
        @param list_ list of allowed cookies (list of strings)
        """
        if not self.__loaded:
            self.load()
        self.__exceptionsAllow = list_[:]
        self.__exceptionsAllow.sort()
        self.__applyRules()
        self.__saveTimer.changeOccurred()
    
    def setAllowForSessionCookies(self, list_):
        """
        Public method to set the list of allowed session cookies.
        
        @param list_ list of allowed session cookies (list of strings)
        """
        if not self.__loaded:
            self.load()
        self.__exceptionsAllowForSession = list_[:]
        self.__exceptionsAllowForSession.sort()
        self.__applyRules()
        self.__saveTimer.changeOccurred()
    
    def filterTrackingCookies(self):
        """
        Public method to get the filter tracking cookies flag.
        
        @return filter tracking cookies flag (boolean)
        """
        return self.__filterTrackingCookies
    
    def setFilterTrackingCookies(self, filterTrackingCookies):
        """
        Public method to set the filter tracking cookies flag.
        
        @param filterTrackingCookies filter tracking cookies flag (boolean)
        """
        self.__filterTrackingCookies = filterTrackingCookies
    
    def __isOnDomainList(self, rules, domain):
        """
        Private method to check, if either the rule matches the domain exactly
        or the domain ends with ".rule".
        
        @param rules list of rules (list of strings)
        @param domain domain name to check (string)
        @return flag indicating a match (boolean)
        """
        for rule in rules:
            if rule.startswith("."):
                if domain.endswith(rule):
                    return True
                
                withoutDot = rule[1:]
                if domain == withoutDot:
                    return True
            else:
                domainEnding = domain[-(len(rule) + 1):]
                if domainEnding and \
                   domainEnding[0] == "." and \
                   domain.endswith(rule):
                    return True
                
                if rule == domain:
                    return True
        
        return False
    
    def __applyRules(self):
        """
        Private method to apply the cookie rules.
        """
        cookiesList = self.allCookies()
        changed = False
        
        for index in range(len(cookiesList) - 1, -1, -1):
            cookie = cookiesList[index]
            if self.__isOnDomainList(self.__exceptionsBlock, cookie.domain()):
                del cookiesList[index]
                changed = True
            elif self.__isOnDomainList(self.__exceptionsAllowForSession,
                                       cookie.domain()):
                cookie.setExpirationDate(QDateTime())
                changed = True
        
        if changed:
            self.setAllCookies(cookiesList)
            self.__saveTimer.changeOccurred()
            self.cookiesChanged.emit()
    
    def cookies(self):
        """
        Public method to get the cookies of the cookie jar.
        
        @return list of all cookies (list of QNetworkCookie)
        """
        if not self.__loaded:
            self.load()
        
        return self.allCookies()
    
    def setCookies(self, cookies):
        """
        Public method to set all cookies.
        
        @param cookies list of cookies to be set (list of QNetworkCookie)
        """
        if not self.__loaded:
            self.load()
        
        self.setAllCookies(cookies)
        self.__saveTimer.changeOccurred()
        self.cookiesChanged.emit()
