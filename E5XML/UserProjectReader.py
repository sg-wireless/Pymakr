# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class for reading an XML user project properties file.
"""

from __future__ import unicode_literals

from .Config import userProjectFileFormatVersion
from .XMLStreamReaderBase import XMLStreamReaderBase

import Preferences


class UserProjectReader(XMLStreamReaderBase):
    """
    Class for reading an XML user project properties file.
    """
    supportedVersions = ["4.0"]
    
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
    
    def readXML(self):
        """
        Public method to read and parse the XML document.
        """
        while not self.atEnd():
            self.readNext()
            if self.isStartElement():
                if self.name() == "UserProject":
                    self.version = self.attribute(
                        "version", userProjectFileFormatVersion)
                    if self.version not in self.supportedVersions:
                        self.raiseUnsupportedFormatVersion(self.version)
                elif self.name() == "VcsType":
                    self.project.pudata["VCSOVERRIDE"] = [
                        self.readElementText()]
                elif self.name() == "VcsStatusMonitorInterval":
                    interval = int(self.attribute(
                        "value",
                        Preferences.getVCS("StatusMonitorInterval")))
                    self.project.pudata["VCSSTATUSMONITORINTERVAL"] = [
                        interval]
                else:
                    self.raiseUnexpectedStartTag(self.name())
        
        self.showErrorMessage()
