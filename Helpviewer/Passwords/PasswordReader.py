# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class to read login data files.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QXmlStreamReader, QIODevice, QFile, \
    QCoreApplication, QUrl


class PasswordReader(QXmlStreamReader):
    """
    Class implementing a reader object for login data files.
    """
    def __init__(self):
        """
        Constructor
        """
        super(PasswordReader, self).__init__()
    
    def read(self, fileNameOrDevice):
        """
        Public method to read a login data file.
        
        @param fileNameOrDevice name of the file to read (string)
            or reference to the device to read (QIODevice)
        @return tuple containing the logins, forms and never URLs
        """
        self.__logins = {}
        self.__loginForms = {}
        self.__never = []
        
        if isinstance(fileNameOrDevice, QIODevice):
            self.setDevice(fileNameOrDevice)
        else:
            f = QFile(fileNameOrDevice)
            if not f.exists():
                return self.__logins, self.__loginForms, self.__never
            f.open(QFile.ReadOnly)
            self.setDevice(f)
        
        while not self.atEnd():
            self.readNext()
            if self.isStartElement():
                version = self.attributes().value("version")
                if self.name() == "Password" and \
                   (not version or version == "1.0"):
                    self.__readPasswords()
                else:
                    self.raiseError(QCoreApplication.translate(
                        "PasswordReader",
                        "The file is not a Passwords version 1.0 file."))
        
        return self.__logins, self.__loginForms, self.__never
    
    def __readPasswords(self):
        """
        Private method to read and parse the login data file.
        """
        if not self.isStartElement() and self.name() != "Password":
            return
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement():
                break
            
            if self.isStartElement():
                if self.name() == "Logins":
                    self.__readLogins()
                elif self.name() == "Forms":
                    self.__readForms()
                elif self.name() == "Nevers":
                    self.__readNevers()
                else:
                    self.__skipUnknownElement()
    
    def __readLogins(self):
        """
        Private method to read the login information.
        """
        if not self.isStartElement() and self.name() != "Logins":
            return
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement():
                if self.name() == "Login":
                    continue
                else:
                    break
            
            if self.isStartElement():
                if self.name() == "Login":
                    attributes = self.attributes()
                    key = attributes.value("key")
                    user = attributes.value("user")
                    password = attributes.value("password")
                    self.__logins[key] = (user, password)
                else:
                    self.__skipUnknownElement()
    
    def __readForms(self):
        """
        Private method to read the forms information.
        """
        if not self.isStartElement() and self.name() != "Forms":
            return
        
        while not self.atEnd():
            self.readNext()
            if self.isStartElement():
                if self.name() == "Form":
                    from .LoginForm import LoginForm
                    attributes = self.attributes()
                    key = attributes.value("key")
                    form = LoginForm()
                    form.url = QUrl(attributes.value("url"))
                    form.name = attributes.value("name")
                    form.hasAPassword = attributes.value("password") == "yes"
                elif self.name() == "Elements":
                    continue
                elif self.name() == "Element":
                    attributes = self.attributes()
                    name = attributes.value("name")
                    value = attributes.value("value")
                    form.elements.append((name, value))
                else:
                    self.__skipUnknownElement()
            
            if self.isEndElement():
                if self.name() == "Form":
                    self.__loginForms[key] = form
                    continue
                elif self.name() in ["Elements", "Element"]:
                    continue
                else:
                    break
    
    def __readNevers(self):
        """
        Private method to read the never URLs.
        """
        if not self.isStartElement() and self.name() != "Nevers":
            return
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement():
                if self.name() == "Never":
                    continue
                else:
                    break
            
            if self.isStartElement():
                if self.name() == "Never":
                    self.__never.append(self.attributes().value("url"))
                else:
                    self.__skipUnknownElement()
    
    def __skipUnknownElement(self):
        """
        Private method to skip over all unknown elements.
        """
        if not self.isStartElement():
            return
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement():
                break
            
            if self.isStartElement():
                self.__skipUnknownElement()
