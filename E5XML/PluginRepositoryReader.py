# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module to read the plug-in repository contents file.
"""

from __future__ import unicode_literals

from .Config import pluginRepositoryFileFormatVersion
from .XMLStreamReaderBase import XMLStreamReaderBase

import Preferences


class PluginRepositoryReader(XMLStreamReaderBase):
    """
    Class to read the plug-in repository contents file.
    """
    supportedVersions = ["4.1", "4.2"]
    
    def __init__(self, device, entryCallback):
        """
        Constructor
        
        @param device reference to the I/O device to read from (QIODevice)
        @param entryCallback reference to a function to be called once the
            data for a plug-in has been read (function)
        """
        XMLStreamReaderBase.__init__(self, device)
        
        self.__entryCallback = entryCallback
        
        self.version = ""
    
    def readXML(self):
        """
        Public method to read and parse the XML document.
        """
        while not self.atEnd():
            self.readNext()
            if self.isStartElement():
                if self.name() == "Plugins":
                    self.version = self.attribute(
                        "version",
                        pluginRepositoryFileFormatVersion)
                    if self.version not in self.supportedVersions:
                        self.raiseUnsupportedFormatVersion(self.version)
                elif self.name() == "RepositoryUrl":
                    url = self.readElementText()
                    Preferences.setUI("PluginRepositoryUrl6", url)
                elif self.name() == "Plugin":
                    self.__readPlugin()
                else:
                    self._skipUnknownElement()
        
        self.showErrorMessage()
    
    def __readPlugin(self):
        """
        Private method to read the plug-in info.
        """
        pluginInfo = {"name": "",
                      "short": "",
                      "description": "",
                      "url": "",
                      "author": "",
                      "version": "",
                      "filename": "",
                      }
        pluginInfo["status"] = self.attribute("status", "unknown")
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Plugin":
                self.__entryCallback(
                    pluginInfo["name"], pluginInfo["short"],
                    pluginInfo["description"], pluginInfo["url"],
                    pluginInfo["author"], pluginInfo["version"],
                    pluginInfo["filename"], pluginInfo["status"])
                break
            
            if self.isStartElement():
                if self.name() == "Name":
                    pluginInfo["name"] = self.readElementText()
                elif self.name() == "Short":
                    pluginInfo["short"] = self.readElementText()
                elif self.name() == "Description":
                    txt = self.readElementText()
                    pluginInfo["description"] = \
                        [line.strip() for line in txt.splitlines()]
                elif self.name() == "Url":
                    pluginInfo["url"] = self.readElementText()
                elif self.name() == "Author":
                    pluginInfo["author"] = self.readElementText()
                elif self.name() == "Version":
                    pluginInfo["version"] = self.readElementText()
                elif self.name() == "Filename":
                    pluginInfo["filename"] = self.readElementText()
                else:
                    self.raiseUnexpectedStartTag(self.name())
