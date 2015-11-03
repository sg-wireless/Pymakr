# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class to write login data files.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QXmlStreamWriter, QIODevice, QFile


class PasswordWriter(QXmlStreamWriter):
    """
    Class implementing a writer object to generate login data files.
    """
    def __init__(self):
        """
        Constructor
        """
        super(PasswordWriter, self).__init__()
        
        self.setAutoFormatting(True)
    
    def write(self, fileNameOrDevice, logins, forms, nevers):
        """
        Public method to write an login data file.
        
        @param fileNameOrDevice name of the file to write (string)
            or device to write to (QIODevice)
        @param logins dictionary with login data (user name, password)
        @param forms list of forms data (list of LoginForm)
        @param nevers list of URLs to never store data for (list of strings)
        @return flag indicating success (boolean)
        """
        if isinstance(fileNameOrDevice, QIODevice):
            f = fileNameOrDevice
        else:
            f = QFile(fileNameOrDevice)
            if not f.open(QFile.WriteOnly):
                return False
        
        self.setDevice(f)
        return self.__write(logins, forms, nevers)
    
    def __write(self, logins, forms, nevers):
        """
        Private method to write an login data file.
        
        @param logins dictionary with login data (user name, password)
        @param forms list of forms data (list of LoginForm)
        @param nevers list of URLs to never store data for (list of strings)
        @return flag indicating success (boolean)
        """
        self.writeStartDocument()
        self.writeDTD("<!DOCTYPE passwords>")
        self.writeStartElement("Password")
        self.writeAttribute("version", "1.0")
        
        if logins:
            self.__writeLogins(logins)
        if forms:
            self.__writeForms(forms)
        if nevers:
            self.__writeNevers(nevers)
        
        self.writeEndDocument()
        return True
    
    def __writeLogins(self, logins):
        """
        Private method to write the login data.
        
        @param logins dictionary with login data (user name, password)
        """
        self.writeStartElement("Logins")
        for key, login in logins.items():
            self.writeEmptyElement("Login")
            self.writeAttribute("key", key)
            self.writeAttribute("user", login[0])
            self.writeAttribute("password", login[1])
        self.writeEndElement()
    
    def __writeForms(self, forms):
        """
        Private method to write forms data.
        
        @param forms list of forms data (list of LoginForm)
        """
        self.writeStartElement("Forms")
        for key, form in forms.items():
            self.writeStartElement("Form")
            self.writeAttribute("key", key)
            self.writeAttribute("url", form.url.toString())
            self.writeAttribute("name", str(form.name))
            self.writeAttribute(
                "password", "yes" if form.hasAPassword else "no")
            if form.elements:
                self.writeStartElement("Elements")
                for element in form.elements:
                    self.writeEmptyElement("Element")
                    self.writeAttribute("name", element[0])
                    self.writeAttribute("value", element[1])
                self.writeEndElement()
            self.writeEndElement()
        self.writeEndElement()
    
    def __writeNevers(self, nevers):
        """
        Private method to write the URLs never to store login data for.
        
        @param nevers list of URLs to never store data for (list of strings)
        """
        self.writeStartElement("Nevers")
        for never in nevers:
            self.writeEmptyElement("Never")
            self.writeAttribute("url", never)
        self.writeEndElement()
