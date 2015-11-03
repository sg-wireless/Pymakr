# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class to write user agent data files.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QXmlStreamWriter, QIODevice, QFile


class UserAgentWriter(QXmlStreamWriter):
    """
    Class implementing a writer object to generate user agent data files.
    """
    def __init__(self):
        """
        Constructor
        """
        super(UserAgentWriter, self).__init__()
        
        self.setAutoFormatting(True)
    
    def write(self, fileNameOrDevice, agents):
        """
        Public method to write a user agent data file.
        
        @param fileNameOrDevice name of the file to write (string)
            or device to write to (QIODevice)
        @param agents dictionary with user agent data (host as key, agent
            string as value)
        @return flag indicating success (boolean)
        """
        if isinstance(fileNameOrDevice, QIODevice):
            f = fileNameOrDevice
        else:
            f = QFile(fileNameOrDevice)
            if not f.open(QFile.WriteOnly):
                return False
        
        self.setDevice(f)
        return self.__write(agents)
    
    def __write(self, agents):
        """
        Private method to write a user agent file.
        
        @param agents dictionary with user agent data (host as key, agent
            string as value)
        @return flag indicating success (boolean)
        """
        self.writeStartDocument()
        self.writeDTD("<!DOCTYPE useragents>")
        self.writeStartElement("UserAgents")
        self.writeAttribute("version", "1.0")
        
        for host, agent in agents.items():
            self.writeEmptyElement("UserAgent")
            self.writeAttribute("host", host)
            self.writeAttribute("agent", agent)
        
        self.writeEndDocument()
        return True
