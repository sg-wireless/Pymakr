# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the web plug-in factory.
"""

from __future__ import unicode_literals

from PyQt5.QtWebKit import QWebPluginFactory


class WebPluginFactory(QWebPluginFactory):
    """
    Class implementing the web plug-in factory.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(WebPluginFactory, self).__init__(parent)
        
        self.__loaded = False
    
    def create(self, mimeType, url, argumentNames, argumentValues):
        """
        Public method to create a plug-in instance for the given MIME type with
        the given data.
        
        @param mimeType MIME type for the plug-in (string)
        @param url URL for the plug-in (QUrl)
        @param argumentNames list of argument names (list of strings)
        @param argumentValues list of argument values (list of strings)
        @return reference to the created object (QObject)
        """
        if not self.__loaded:
            self.__initialize()
        
        if mimeType in self.__pluginsCache:
            return self.__pluginsCache[mimeType].create(
                mimeType, url, argumentNames, argumentValues)
        else:
            return None
    
    def plugins(self):
        """
        Public method to get a list of plug-ins.
        
        @return list of plug-ins (list of QWebPluginFactory.Plugin)
        """
        if not self.__loaded:
            self.__initialize()
        
        plugins = []
        for plugin in self.__plugins.values():
            if not plugin.isAnonymous():
                pluginInfo = plugin.metaPlugin()
                plugins.append(pluginInfo)
        return plugins
    
    def refreshPlugins(self):
        """
        Public method to refresh the list of supported plug-ins.
        """
        self.__initialize()
        super(WebPluginFactory, self).refreshPlugins()
    
    def __initialize(self):
        """
        Private method to initialize the factory.
        """
        self.__loaded = True
        self.__plugins = {}
        self.__pluginsCache = {}
        
        from .ClickToFlash.ClickToFlashPlugin import ClickToFlashPlugin
        self.__plugins["ClickToFlash"] = ClickToFlashPlugin()
        
        for plugin in self.__plugins.values():
            for pluginMimeType in plugin.metaPlugin().mimeTypes:
                self.__pluginsCache[pluginMimeType.name] = plugin
    
    def plugin(self, name):
        """
        Public method to get a reference to the named plug-in.
        
        @param name name of the plug-in (string)
        @return reference to the named plug-in
        """
        if not self.__loaded:
            self.__initialize()
        
        if name in self.__plugins:
            return self.__plugins[name]
        
        return None
