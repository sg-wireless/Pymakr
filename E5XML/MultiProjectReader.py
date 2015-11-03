# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class for reading an XML multi project file.
"""

from __future__ import unicode_literals

import os

from .Config import multiProjectFileFormatVersion
from .XMLStreamReaderBase import XMLStreamReaderBase

import Utilities


class MultiProjectReader(XMLStreamReaderBase):
    """
    Class for reading an XML multi project file.
    """
    supportedVersions = ["4.2", "5.0", "5.1"]
    
    def __init__(self, device, multiProject):
        """
        Constructor
        
        @param device reference to the I/O device to read from (QIODevice)
        @param multiProject Reference to the multi project object to store the
                information into.
        """
        XMLStreamReaderBase.__init__(self, device)
        
        self.multiProject = multiProject
        self.path = os.path.dirname(device.fileName())
        
        self.version = ""
    
    def readXML(self):
        """
        Public method to read and parse the XML document.
        """
        while not self.atEnd():
            self.readNext()
            if self.isStartElement():
                if self.name() == "MultiProject":
                    self.version = self.attribute(
                        "version",
                        multiProjectFileFormatVersion)
                    if self.version not in self.supportedVersions:
                        self.raiseUnsupportedFormatVersion(self.version)
                elif self.name() == "Description":
                    self.multiProject.description = self.readElementText()
                elif self.name() == "Projects":
                    self.__readProjects()
                else:
                    self.raiseUnexpectedStartTag(self.name())
        
        self.showErrorMessage()
    
    def __readProjects(self):
        """
        Private method to read the project infos.
        """
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Projects":
                break
            
            if self.isStartElement():
                if self.name() == "Project":
                    self.__readProject()
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def __readProject(self):
        """
        Private method to read the project info.
        """
        project = {}
        
        project["master"] = self.toBool(self.attribute("isMaster", "False"))
        uid = self.attribute("uid", "")
        if uid:
            project["uid"] = uid
        else:
            # upgrade from pre 5.1 format
            from PyQt5.QtCore import QUuid
            project["uid"] = QUuid.createUuid().toString()
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Project":
                if 'category' not in project:
                    # upgrade from 4.2 format
                    project["category"] = ""
                self.multiProject.projects.append(project)
                break
            
            if self.isStartElement():
                if self.name() == "ProjectName":
                    project["name"] = self.readElementText()
                elif self.name() == "ProjectFile":
                    project["file"] = Utilities.absoluteUniversalPath(
                        self.readElementText(), self.path)
                elif self.name() == "ProjectDescription":
                    project["description"] = self.readElementText()
                elif self.name() == "ProjectCategory":
                    project["category"] = self.readElementText()
                else:
                    self.raiseUnexpectedStartTag(self.name())
