# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the AdBlock manager.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSignal, QObject, QUrl, QFile

from .AdBlockSubscription import AdBlockSubscription

from Utilities.AutoSaver import AutoSaver
import Utilities
import Preferences


class AdBlockManager(QObject):
    """
    Class implementing the AdBlock manager.
    
    @signal rulesChanged() emitted after some rule has changed
    """
    rulesChanged = pyqtSignal()
    requiredSubscriptionLoaded = pyqtSignal(AdBlockSubscription)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(AdBlockManager, self).__init__(parent)
        
        self.__loaded = False
        self.__subscriptionsLoaded = False
        self.__enabled = False
        self.__adBlockDialog = None
        self.__adBlockExceptionsDialog = None
        self.__adBlockNetwork = None
        self.__adBlockPage = None
        self.__subscriptions = []
        self.__exceptedHosts = Preferences.getHelp("AdBlockExceptions")
        self.__saveTimer = AutoSaver(self, self.save)
        
        self.__defaultSubscriptionUrlString = \
            "abp:subscribe?location=" \
            "https://easylist-downloads.adblockplus.org/easylist.txt&"\
            "title=EasyList"
        self.__customSubscriptionUrlString = \
            bytes(self.__customSubscriptionUrl().toEncoded()).decode()
        
        self.rulesChanged.connect(self.__saveTimer.changeOccurred)
    
    def close(self):
        """
        Public method to close the open search engines manager.
        """
        self.__adBlockDialog and self.__adBlockDialog.close()
        self.__adBlockExceptionsDialog and \
            self.__adBlockExceptionsDialog.close()
        
        self.__saveTimer.saveIfNeccessary()
    
    def isEnabled(self):
        """
        Public method to check, if blocking ads is enabled.
        
        @return flag indicating the enabled state (boolean)
        """
        if not self.__loaded:
            self.load()
        
        return self.__enabled
    
    def setEnabled(self, enabled):
        """
        Public slot to set the enabled state.
        
        @param enabled flag indicating the enabled state (boolean)
        """
        if self.isEnabled() == enabled:
            return
        
        import Helpviewer.HelpWindow
        self.__enabled = enabled
        for mainWindow in Helpviewer.HelpWindow.HelpWindow.mainWindows():
            mainWindow.adBlockIcon().setEnabled(enabled)
        if enabled:
            self.__loadSubscriptions()
        self.rulesChanged.emit()
    
    def network(self):
        """
        Public method to get a reference to the network block object.
        
        @return reference to the network block object (AdBlockNetwork)
        """
        if self.__adBlockNetwork is None:
            from .AdBlockNetwork import AdBlockNetwork
            self.__adBlockNetwork = AdBlockNetwork(self)
        return self.__adBlockNetwork
    
    def page(self):
        """
        Public method to get a reference to the page block object.
        
        @return reference to the page block object (AdBlockPage)
        """
        if self.__adBlockPage is None:
            from .AdBlockPage import AdBlockPage
            self.__adBlockPage = AdBlockPage(self)
        return self.__adBlockPage
    
    def __customSubscriptionLocation(self):
        """
        Private method to generate the path for custom subscriptions.
        
        @return URL for custom subscriptions (QUrl)
        """
        dataDir = os.path.join(Utilities.getConfigDir(), "browser",
                               "subscriptions")
        if not os.path.exists(dataDir):
            os.makedirs(dataDir)
        fileName = os.path.join(dataDir, "adblock_subscription_custom")
        return QUrl.fromLocalFile(fileName)
    
    def __customSubscriptionUrl(self):
        """
        Private method to generate the URL for custom subscriptions.
        
        @return URL for custom subscriptions (QUrl)
        """
        location = self.__customSubscriptionLocation()
        encodedUrl = bytes(location.toEncoded()).decode()
        url = QUrl("abp:subscribe?location={0}&title={1}".format(
            encodedUrl, self.tr("Custom Rules")))
        return url
    
    def customRules(self):
        """
        Public method to get a subscription for custom rules.
        
        @return subscription object for custom rules (AdBlockSubscription)
        """
        location = self.__customSubscriptionLocation()
        for subscription in self.__subscriptions:
            if subscription.location() == location:
                return subscription
        
        url = self.__customSubscriptionUrl()
        customAdBlockSubscription = AdBlockSubscription(url, True, self)
        self.addSubscription(customAdBlockSubscription)
        return customAdBlockSubscription
    
    def subscriptions(self):
        """
        Public method to get all subscriptions.
        
        @return list of subscriptions (list of AdBlockSubscription)
        """
        if not self.__loaded:
            self.load()
        
        return self.__subscriptions[:]
    
    def subscription(self, location):
        """
        Public method to get a subscription based on its location.
        
        @param location location of the subscription to search for (string)
        @return subscription or None (AdBlockSubscription)
        """
        if location != "":
            for subscription in self.__subscriptions:
                if subscription.location().toString() == location:
                    return subscription
        
        return None
    
    def updateAllSubscriptions(self):
        """
        Public method to update all subscriptions.
        """
        for subscription in self.__subscriptions:
            subscription.updateNow()
    
    def removeSubscription(self, subscription, emitSignal=True):
        """
        Public method to remove an AdBlock subscription.
        
        @param subscription AdBlock subscription to be removed
            (AdBlockSubscription)
        @param emitSignal flag indicating to send a signal (boolean)
        """
        if subscription is None:
            return
        
        if subscription.url().toString().startswith(
            (self.__defaultSubscriptionUrlString,
             self.__customSubscriptionUrlString)):
            return
        
        try:
            self.__subscriptions.remove(subscription)
            rulesFileName = subscription.rulesFileName()
            QFile.remove(rulesFileName)
            requiresSubscriptions = self.getRequiresSubscriptions(subscription)
            for requiresSubscription in requiresSubscriptions:
                self.removeSubscription(requiresSubscription, False)
            if emitSignal:
                self.rulesChanged.emit()
        except ValueError:
            pass
    
    def addSubscription(self, subscription):
        """
        Public method to add an AdBlock subscription.
        
        @param subscription AdBlock subscription to be added
            (AdBlockSubscription)
        """
        if subscription is None:
            return
        
        self.__subscriptions.insert(-1, subscription)
        
        subscription.rulesChanged.connect(self.rulesChanged)
        subscription.changed.connect(self.rulesChanged)
        subscription.enabledChanged.connect(self.rulesChanged)
        
        self.rulesChanged.emit()
    
    def save(self):
        """
        Public method to save the AdBlock subscriptions.
        """
        if not self.__loaded:
            return
        
        Preferences.setHelp("AdBlockEnabled", self.__enabled)
        if self.__subscriptionsLoaded:
            subscriptions = []
            requiresSubscriptions = []
            # intermediate store for subscription requiring others
            for subscription in self.__subscriptions:
                if subscription is None:
                    continue
                urlString = bytes(subscription.url().toEncoded()).decode()
                if "requiresLocation" in urlString:
                    requiresSubscriptions.append(urlString)
                else:
                    subscriptions.append(urlString)
                subscription.saveRules()
            for subscription in requiresSubscriptions:
                subscriptions.insert(-1, subscription)  # custom should be last
            Preferences.setHelp("AdBlockSubscriptions", subscriptions)
    
    def load(self):
        """
        Public method to load the AdBlock subscriptions.
        """
        if self.__loaded:
            return
        
        self.__loaded = True
        
        self.__enabled = Preferences.getHelp("AdBlockEnabled")
        if self.__enabled:
            self.__loadSubscriptions()
    
    def __loadSubscriptions(self):
        """
        Private method to load the set of subscriptions.
        """
        if self.__subscriptionsLoaded:
            return
        
        subscriptions = Preferences.getHelp("AdBlockSubscriptions")
        if subscriptions:
            for subscription in subscriptions:
                if subscription.startswith(
                        self.__defaultSubscriptionUrlString):
                    break
            else:
                subscriptions.insert(0, self.__defaultSubscriptionUrlString)
            for subscription in subscriptions:
                if subscription.startswith(self.__customSubscriptionUrlString):
                    break
            else:
                subscriptions.append(self.__customSubscriptionUrlString)
        else:
            subscriptions = [self.__defaultSubscriptionUrlString,
                             self.__customSubscriptionUrlString]
        for subscription in subscriptions:
            url = QUrl.fromEncoded(subscription.encode("utf-8"))
            adBlockSubscription = AdBlockSubscription(
                url,
                subscription.startswith(self.__customSubscriptionUrlString),
                self,
                subscription.startswith(self.__defaultSubscriptionUrlString))
            adBlockSubscription.rulesChanged.connect(self.rulesChanged)
            adBlockSubscription.changed.connect(self.rulesChanged)
            adBlockSubscription.enabledChanged.connect(self.rulesChanged)
            self.__subscriptions.append(adBlockSubscription)
        
        self.__subscriptionsLoaded = True
    
    def loadRequiredSubscription(self, location, title):
        """
        Public method to load a subscription required by another one.
        
        @param location location of the required subscription (string)
        @param title title of the required subscription (string)
        """
        # Step 1: check, if the subscription is in the list of subscriptions
        urlString = "abp:subscribe?location={0}&title={1}".format(
            location, title)
        for subscription in self.__subscriptions:
            if subscription.url().toString().startswith(urlString):
                # We found it!
                return
        
        # Step 2: if it is not, get it
        url = QUrl.fromEncoded(urlString.encode("utf-8"))
        adBlockSubscription = AdBlockSubscription(url, False, self)
        self.addSubscription(adBlockSubscription)
        self.requiredSubscriptionLoaded.emit(adBlockSubscription)
    
    def getRequiresSubscriptions(self, subscription):
        """
        Public method to get a list of subscriptions, that require the given
        one.
        
        @param subscription subscription to check for (AdBlockSubscription)
        @return list of subscription requiring the given one (list of
            AdBlockSubscription)
        """
        subscriptions = []
        location = subscription.location().toString()
        for subscription in self.__subscriptions:
            if subscription.requiresLocation() == location:
                subscriptions.append(subscription)
        
        return subscriptions
    
    def showDialog(self):
        """
        Public slot to show the AdBlock subscription management dialog.
        
        @return reference to the dialog (AdBlockDialog)
        """
        if self.__adBlockDialog is None:
            from .AdBlockDialog import AdBlockDialog
            self.__adBlockDialog = AdBlockDialog()
        
        self.__adBlockDialog.show()
        return self.__adBlockDialog
    
    def showRule(self):
        """
        Public slot to show an AdBlock rule.
        """
        act = self.sender()
        if act is not None:
            rule = act.data()
            if rule:
                self.showDialog().showRule(rule)
    
    def elementHidingRules(self):
        """
        Public method to get the element hiding rules.
        
        @return element hiding rules (string)
        """
        if not self.__enabled:
            return ""
        
        rules = ""
        
        for subscription in self.__subscriptions:
            rules += subscription.elementHidingRules()
        
        if rules:
            # remove last ",
            rules = rules[:-1]
        
        return rules
    
    def elementHidingRulesForDomain(self, url):
        """
        Public method to get the element hiding rules for a domain.
        
        @param url URL to get hiding rules for (QUrl)
        @return element hiding rules (string)
        """
        if not self.__enabled:
            return ""
        
        rules = ""
        
        for subscription in self.__subscriptions:
            if subscription.elemHideDisabledForUrl(url):
                return ""
            
            rules += subscription.elementHidingRulesForDomain(url.host())
        
        if rules:
            # remove last ",
            rules = rules[:-1]
        
        return rules
    
    def exceptions(self):
        """
        Public method to get a list of excepted hosts.
        
        @return list of excepted hosts (list of string)
        """
        return self.__exceptedHosts
    
    def setExceptions(self, hosts):
        """
        Public method to set the list of excepted hosts.
        
        @param hosts list of excepted hosts (list of string)
        """
        self.__exceptedHosts = hosts[:]
        Preferences.setHelp("AdBlockExceptions", self.__exceptedHosts)
    
    def addException(self, host):
        """
        Public method to add an exception.
        
        @param host to be excepted (string)
        """
        if host and host not in self.__exceptedHosts:
            self.__exceptedHosts.append(host)
            Preferences.setHelp("AdBlockExceptions", self.__exceptedHosts)
    
    def removeException(self, host):
        """
        Public method to remove an exception.
        
        @param host to be removed from the list of exceptions (string)
        """
        if host in self.__exceptedHosts:
            self.__exceptedHosts.remove(host)
            Preferences.setHelp("AdBlockExceptions", self.__exceptedHosts)
    
    def isHostExcepted(self, host):
        """
        Public slot to check, if a host is excepted.
        
        @param host host to check (string)
        @return flag indicating an exception (boolean)
        """
        return host in self.__exceptedHosts
    
    def showExceptionsDialog(self):
        """
        Public method to show the AdBlock Exceptions dialog.
        
        @return reference to the exceptions dialog (AdBlockExceptionsDialog)
        """
        if self.__adBlockExceptionsDialog is None:
            from .AdBlockExceptionsDialog import AdBlockExceptionsDialog
            self.__adBlockExceptionsDialog = AdBlockExceptionsDialog()
        
        self.__adBlockExceptionsDialog.load(self.__exceptedHosts)
        self.__adBlockExceptionsDialog.show()
        return self.__adBlockExceptionsDialog
