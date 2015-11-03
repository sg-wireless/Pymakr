# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the writer class for writing an XML multi project file.
"""

from __future__ import unicode_literals

import os
import time

from .XMLStreamWriterBase import XMLStreamWriterBase
from .Config import multiProjectFileFormatVersion

import Preferences
import Utilities


class MultiProjectWriter(XMLStreamWriterBase):
    """
    Class implementing the writer class for writing an XML project file.
    """
    def __init__(self, device, multiProject, multiProjectName):
        """
        Constructor
        
        @param device reference to the I/O device to write to (QIODevice)
        @param multiProject Reference to the multi project object
        @param multiProjectName name of the project (string)
        """
        XMLStreamWriterBase.__init__(self, device)
        
        self.name = multiProjectName
        self.multiProject = multiProject
        self.path = os.path.dirname(device.fileName())
    
    def writeXML(self):
        """
        Public method to write the XML to the file.
        """
        XMLStreamWriterBase.writeXML(self)
        
        self.writeDTD('<!DOCTYPE MultiProject SYSTEM "MultiProject-{0}.dtd">'
                      .format(multiProjectFileFormatVersion))
        
        # add some generation comments
        self.writeComment(" eric6 multi project file for multi project {0} "
                          .format(self.name))
        if Preferences.getMultiProject("XMLTimestamp"):
            self.writeComment(
                " Saved: {0} ".format(time.strftime('%Y-%m-%d, %H:%M:%S')))
            self.writeComment(
                " Copyright (C) {0} ".format(time.strftime('%Y')))
        
        # add the main tag
        self.writeStartElement("MultiProject")
        self.writeAttribute("version", multiProjectFileFormatVersion)
        
        # do description
        self.writeTextElement("Description", self.multiProject.description)
        
        # do the projects
        self.writeStartElement("Projects")
        for project in self.multiProject.getProjects():
            self.writeStartElement("Project")
            self.writeAttribute("isMaster", str(project['master']))
            self.writeAttribute("uid", project["uid"])
            self.writeTextElement("ProjectName", project['name'])
            self.writeTextElement(
                "ProjectFile",
                Utilities.relativeUniversalPath(project['file'], self.path))
            self.writeTextElement("ProjectDescription", project['description'])
            self.writeTextElement("ProjectCategory", project['category'])
            self.writeEndElement()
        self.writeEndElement()
        
        self.writeEndElement()
        self.writeEndDocument()
