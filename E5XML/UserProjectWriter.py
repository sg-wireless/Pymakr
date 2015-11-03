# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the writer class for writing an XML user project
properties file.
"""

from __future__ import unicode_literals

import time

from E5Gui.E5Application import e5App

from .XMLStreamWriterBase import XMLStreamWriterBase
from .Config import userProjectFileFormatVersion

import Preferences


class UserProjectWriter(XMLStreamWriterBase):
    """
    Class implementing the writer class for writing an XML user project
    properties  file.
    """
    def __init__(self, device, projectName):
        """
        Constructor
        
        @param device reference to the I/O device to write to (QIODevice)
        @param projectName name of the project (string)
        """
        XMLStreamWriterBase.__init__(self, device)
        
        self.pudata = e5App().getObject("Project").pudata
        self.pdata = e5App().getObject("Project").pdata
        self.name = projectName
        
    def writeXML(self):
        """
        Public method to write the XML to the file.
        """
        XMLStreamWriterBase.writeXML(self)
        
        self.writeDTD(
            '<!DOCTYPE UserProject SYSTEM "UserProject-{0}.dtd">'.format(
                userProjectFileFormatVersion))
        
        # add some generation comments
        self.writeComment(
            " eric6 user project file for project {0} ".format(self.name))
        if Preferences.getProject("XMLTimestamp"):
            self.writeComment(
                " Saved: {0} ".format(time.strftime('%Y-%m-%d, %H:%M:%S')))
            self.writeComment(" Copyright (C) {0} {1}, {2} ".format(
                time.strftime('%Y'), self.pdata["AUTHOR"][0],
                self.pdata["EMAIL"][0]))
        
        # add the main tag
        self.writeStartElement("UserProject")
        self.writeAttribute("version", userProjectFileFormatVersion)
        
        # do the vcs override stuff
        if self.pudata["VCSOVERRIDE"]:
            self.writeTextElement("VcsType", self.pudata["VCSOVERRIDE"][0])
        if self.pudata["VCSSTATUSMONITORINTERVAL"]:
            self.writeEmptyElement("VcsStatusMonitorInterval")
            self.writeAttribute(
                "value", str(self.pudata["VCSSTATUSMONITORINTERVAL"][0]))
        
        self.writeEndElement()
        self.writeEndDocument()
