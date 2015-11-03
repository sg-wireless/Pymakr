# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class for reading an XML project debugger properties
file.
"""

from __future__ import unicode_literals

from .Config import debuggerPropertiesFileFormatVersion
from .XMLStreamReaderBase import XMLStreamReaderBase


class DebuggerPropertiesReader(XMLStreamReaderBase):
    """
    Class for reading an XML project debugger properties file.
    """
    supportedVersions = ["3.9"]
    
    def __init__(self, device, project):
        """
        Constructor
        
        @param device reference to the I/O device to read from (QIODevice)
        @param project Reference to the project object to store the
                information into.
        """
        XMLStreamReaderBase.__init__(self, device)
    
        self.project = project
        
        self.version = ""
    
    def readXML(self, quiet=False):
        """
        Public method to read and parse the XML document.
        
        @param quiet flag indicating quiet operations.
                If this flag is true, no errors are reported.
        """
        while not self.atEnd():
            self.readNext()
            if self.isStartElement():
                if self.name() == "DebuggerProperties":
                    self.version = self.attribute(
                        "version", debuggerPropertiesFileFormatVersion)
                    if self.version not in self.supportedVersions:
                        self.raiseUnsupportedFormatVersion(self.version)
                elif self.name() == "Interpreter":
                    self.project.debugProperties["INTERPRETER"] = \
                        self.readElementText()
                elif self.name() == "DebugClient":
                    self.project.debugProperties["DEBUGCLIENT"] = \
                        self.readElementText()
                elif self.name() == "Environment":
                    self.project.debugProperties["ENVIRONMENTOVERRIDE"] = \
                        int(self.attribute("override", "0"))
                    self.project.debugProperties["ENVIRONMENTSTRING"] = \
                        self.readElementText()
                elif self.name() == "RemoteDebugger":
                    self.__readRemoteDebugger()
                elif self.name() == "PathTranslation":
                    self.__readPathTranslation()
                elif self.name() == "ConsoleDebugger":
                    self.project.debugProperties["CONSOLEDEBUGGER"] = \
                        int(self.attribute("on", "0"))
                    self.project.debugProperties["CONSOLECOMMAND"] = \
                        self.readElementText()
                elif self.name() == "Redirect":
                    self.project.debugProperties["REDIRECT"] = \
                        int(self.attribute("on", "1"))
                elif self.name() == "Noencoding":
                    self.project.debugProperties["NOENCODING"] = \
                        int(self.attribute("on", "0"))
                else:
                    self.raiseUnexpectedStartTag(self.name())
        
        if not quiet:
            self.showErrorMessage()
    
    def __readRemoteDebugger(self):
        """
        Private method to read the remote debugger info.
        """
        self.project.debugProperties["REMOTEDEBUGGER"] = int(self.attribute(
            "on", "0"))
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "RemoteDebugger":
                break
            
            if self.isStartElement():
                if self.name() == "RemoteHost":
                    self.project.debugProperties["REMOTEHOST"] = \
                        self.readElementText()
                elif self.name() == "RemoteCommand":
                    self.project.debugProperties["REMOTECOMMAND"] = \
                        self.readElementText()
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def __readPathTranslation(self):
        """
        Private method to read the path translation info.
        """
        self.project.debugProperties["PATHTRANSLATION"] = int(self.attribute(
            "on", "0"))
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "PathTranslation":
                break
            
            if self.isStartElement():
                if self.name() == "RemotePath":
                    self.project.debugProperties["REMOTEPATH"] = \
                        self.readElementText()
                elif self.name() == "LocalPath":
                    self.project.debugProperties["LOCALPATH"] = \
                        self.readElementText()
                else:
                    self.raiseUnexpectedStartTag(self.name())
