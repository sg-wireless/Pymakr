# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class for reading an XML shortcuts file.
"""

from __future__ import unicode_literals

from .Config import shortcutsFileFormatVersion
from .XMLStreamReaderBase import XMLStreamReaderBase


class ShortcutsReader(XMLStreamReaderBase):
    """
    Class for reading an XML shortcuts file.
    """
    supportedVersions = ["3.6"]
    
    def __init__(self, device):
        """
        Constructor
        
        @param device reference to the I/O device to read from (QIODevice)
        """
        XMLStreamReaderBase.__init__(self, device)
        
        self.version = ""
        self.shortcuts = {}
    
    def readXML(self):
        """
        Public method to read and parse the XML document.
        """
        while not self.atEnd():
            self.readNext()
            if self.isStartElement():
                if self.name() == "Shortcuts":
                    self.version = self.attribute(
                        "version", shortcutsFileFormatVersion)
                    if self.version not in self.supportedVersions:
                        self.raiseUnsupportedFormatVersion(self.version)
                elif self.name() == "Shortcut":
                    self.__readShortCut()
                else:
                    self.raiseUnexpectedStartTag(self.name())
        
        self.showErrorMessage()
    
    def __readShortCut(self):
        """
        Private method to read the shortcut data.
        """
        category = self.attribute("category")
        name = ""
        accel = ""
        altAccel = ""
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Shortcut":
                if category:
                    if category not in self.shortcuts:
                        self.shortcuts[category] = {}
                    self.shortcuts[category][name] = (accel, altAccel)
                break
            
            if self.isStartElement():
                if self.name() == "Name":
                    name = self.readElementText()
                elif self.name() == "Accel":
                    accel = self.readElementText()
                elif self.name() == "AltAccel":
                    altAccel = self.readElementText()
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def getShortcuts(self):
        """
        Public method to retrieve the shortcuts.
        
        @return Dictionary of dictionaries of shortcuts. The keys of the
            dictionary are the categories, the values are dictionaries.
            These dictionaries have the shortcut name as their key and
            a tuple of accelerators as their value.
        """
        return self.shortcuts
