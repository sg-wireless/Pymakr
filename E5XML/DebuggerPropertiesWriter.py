# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the writer class for writing an XML project debugger
properties file.
"""

from __future__ import unicode_literals

import time

from E5Gui.E5Application import e5App

from .XMLStreamWriterBase import XMLStreamWriterBase
from .Config import debuggerPropertiesFileFormatVersion

import Preferences


class DebuggerPropertiesWriter(XMLStreamWriterBase):
    """
    Class implementing the writer class for writing an XML project debugger
    properties file.
    """
    def __init__(self, device, projectName):
        """
        Constructor
        
        @param device reference to the I/O device to write to (QIODevice)
        @param projectName name of the project (string)
        """
        XMLStreamWriterBase.__init__(self, device)
        
        self.name = projectName
        self.project = e5App().getObject("Project")
        
    def writeXML(self):
        """
        Public method to write the XML to the file.
        """
        XMLStreamWriterBase.writeXML(self)
        
        self.writeDTD(
            '<!DOCTYPE DebuggerProperties SYSTEM'
            ' "DebuggerProperties-{0}.dtd">'.format(
                debuggerPropertiesFileFormatVersion))
        
        # add some generation comments
        self.writeComment(
            " eric6 debugger properties file for project {0} ".format(
                self.name))
        self.writeComment(
            " This file was generated automatically, do not edit. ")
        if Preferences.getProject("XMLTimestamp"):
            self.writeComment(
                " Saved: {0} ".format(time.strftime('%Y-%m-%d, %H:%M:%S')))
        
        # add the main tag
        self.writeStartElement("DebuggerProperties")
        self.writeAttribute("version", debuggerPropertiesFileFormatVersion)
        
        self.writeTextElement(
            "Interpreter", self.project.debugProperties["INTERPRETER"])
        
        self.writeTextElement(
            "DebugClient", self.project.debugProperties["DEBUGCLIENT"])
        
        self.writeStartElement("Environment")
        self.writeAttribute(
            "override",
            str(int(self.project.debugProperties["ENVIRONMENTOVERRIDE"])))
        self.writeCharacters(self.project.debugProperties["ENVIRONMENTSTRING"])
        self.writeEndElement()
        
        self.writeStartElement("RemoteDebugger")
        self.writeAttribute(
            "on", str(int(self.project.debugProperties["REMOTEDEBUGGER"])))
        self.writeTextElement(
            "RemoteHost", self.project.debugProperties["REMOTEHOST"])
        self.writeTextElement(
            "RemoteCommand", self.project.debugProperties["REMOTECOMMAND"])
        self.writeEndElement()
        
        self.writeStartElement("PathTranslation")
        self.writeAttribute(
            "on", str(int(self.project.debugProperties["PATHTRANSLATION"])))
        self.writeTextElement(
            "RemotePath", self.project.debugProperties["REMOTEPATH"])
        self.writeTextElement(
            "LocalPath", self.project.debugProperties["LOCALPATH"])
        self.writeEndElement()
        
        self.writeStartElement("ConsoleDebugger")
        self.writeAttribute(
            "on", str(int(self.project.debugProperties["CONSOLEDEBUGGER"])))
        self.writeCharacters(self.project.debugProperties["CONSOLECOMMAND"])
        self.writeEndElement()
        
        self.writeEmptyElement("Redirect")
        self.writeAttribute(
            "on", str(int(self.project.debugProperties["REDIRECT"])))
        
        self.writeEmptyElement("Noencoding")
        self.writeAttribute(
            "on", str(int(self.project.debugProperties["NOENCODING"])))
        
        self.writeEndElement()
        self.writeEndDocument()
