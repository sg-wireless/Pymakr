# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Flash blocker plug-in.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWebKit import QWebPluginFactory

from ..WebPluginInterface import WebPluginInterface

import Preferences


class ClickToFlashPlugin(WebPluginInterface):
    """
    Class implementing the flash blocker plug-in.
    """
    ClickToFlashData = {
        "application/x-shockwave-flash": {
            "extensions": ["swf"],
            "icon": "flashBlock-flash.png"
        },
        "application/futuresplash": {
            "extensions": ["spl"],
            "icon": "flashBlock-flash.png"
        },
        "application/x-director": {
            "extensions": ["dir", "dcr", "dxr"],
            "icon": "flashBlock-director.png"
        },
        "application/x-authorware-map": {
            "extensions": ["aam"],
            "icon": "flashBlock-authorware.png"
        },
        "application/x-authorware-seg": {
            "extensions": ["aas"],
            "icon": "flashBlock-authorware.png"
        },
        "application/x-authorware-bin": {
            "extensions": ["aab", "x32", "u32", "vox"],
            "icon": "flashBlock-authorware.png"
        },
        "image/x-freehand": {
            "extensions": ["fh4", "fh7", "fh5", "fhc", "fh"],
            "icon": "flashBlock-freehand.png"
        },
        "application/x-silverlight-app": {
            "extensions": ["xap"],
            "icon": "flashBlock-silverlight.png"
        },
        "application/xaml+xml": {
            "extensions": ["xaml"],
            "icon": "flashBlock-silverlight.png"
        },
        "application/x-ms-xbap": {
            "extensions": ["xbap"],
            "icon": "flashBlock-silverlight.png"
        },
        "application/x-java-applet": {
            "extensions": [],
            "icon": "flashBlock-java.png"
        },
    }
    
    def __init__(self):
        """
        Constructor
        """
        self.__loaded = False
        self.__whitelist = []
    
    def metaPlugin(self):
        """
        Public method to create a meta plug-in object containing plug-in info.
        
        @return meta plug-in object (QWebPluginFactory.Plugin)
        """
        plugin = QWebPluginFactory.Plugin()
        plugin.name = "ClickToFlashPlugin"
        mimeTypes = plugin.mimeTypes
        for mime, value in ClickToFlashPlugin.ClickToFlashData.items():
            mimeType = QWebPluginFactory.MimeType()
            mimeType.name = mime
            extensions = value["extensions"]
            if extensions:
                fileExtensions = mimeType.fileExtensions
                for extension in extensions:
                    fileExtensions.append(extension)
                mimeType.fileExtensions = fileExtensions
            mimeTypes.append(mimeType)
        plugin.mimeTypes = mimeTypes
        
        return plugin
    
    def create(self, mimeType, url, argumentNames, argumentValues):
        """
        Public method to create a plug-in instance for the given data.
        
        @param mimeType MIME type for the plug-in (string)
        @param url URL for the plug-in (QUrl)
        @param argumentNames list of argument names (list of strings)
        @param argumentValues list of argument values (list of strings)
        @return reference to the created object (QWidget)
        """
        self.__load()
        if not self.__enabled():
            return None
        
        if self.onWhitelist(url.host()):
            return None
        
        from .ClickToFlash import ClickToFlash
        
        if ClickToFlash.isAlreadyAccepted(url, argumentNames, argumentValues):
            return None
        
        ctf = ClickToFlash(self, mimeType, url, argumentNames, argumentValues)
        return ctf
    
    def configure(self):
        """
        Public method to configure the plug-in.
        """
        from .ClickToFlashWhitelistDialog import ClickToFlashWhitelistDialog
        self.__load()
        dlg = ClickToFlashWhitelistDialog(self.__whitelist)
        if dlg.exec_() == QDialog.Accepted:
            self.__whitelist = dlg.getWhitelist()
            self.__save()
    
    def isAnonymous(self):
        """
        Public method to indicate an anonymous plug-in.
        
        @return flag indicating anonymous state (boolean)
        """
        return True
    
    def onWhitelist(self, host):
        """
        Public method to check, if a host is on the whitelist.
        
        @param host host to check for (string)
        @return flag indicating presence in the whitelist (boolean)
        """
        return host in self.__whitelist or \
            "www." + host in self.__whitelist or \
            host.replace("www.", "") in self.__whitelist
    
    def addToWhitelist(self, host):
        """
        Public method to add a host to the whitelist.
        
        @param host host to be added (string)
        """
        if not self.onWhitelist(host):
            self.__whitelist.append(host)
            self.__save()
    
    def removeFromWhitelist(self, host):
        """
        Public method to remove a host from the whitelist.
        
        @param host host to be removed (string)
        """
        if self.onWhitelist(host):
            if host in self.__whitelist:
                self.__whitelist.remove(host)
            elif "www." + host in self.__whitelist:
                self.__whitelist.remove("www." + host)
            elif host.replace("www.", "") in self.__whitelist:
                self.__whitelist.remove(host.replace("www.", ""))
            self.__save()
    
    def __load(self):
        """
        Private method to load the configuration.
        """
        if self.__loaded:
            return
        
        self.__loaded = True
        self.__whitelist = Preferences.getHelp("ClickToFlashWhitelist")
    
    def __save(self):
        """
        Private method to save the configuration.
        """
        Preferences.setHelp("ClickToFlashWhitelist", self.__whitelist)
    
    def __enabled(self):
        """
        Private method to check, if the plug-in is enabled.
        
        @return enabled status (boolean)
        """
        return Preferences.getHelp("ClickToFlashEnabled")
    
    @classmethod
    def getIconName(cls, mimeType):
        """
        Class method to get the icon name for the mime type.
        
        @param mimeType mime type to get the icon for (string)
        @return name of the icon file (string)
        """
        if mimeType in cls.ClickToFlashData:
            return cls.ClickToFlashData[mimeType]["icon"]
        
        return ""
