# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class for reading an XML project file.
"""

from __future__ import unicode_literals

from .Config import projectFileFormatVersion
from .XMLStreamReaderBase import XMLStreamReaderBase

import Utilities


class ProjectReader(XMLStreamReaderBase):
    """
    Class for reading an XML project file.
    """
    supportedVersions = ["4.6", "5.0", "5.1"]
    
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
                if self.name() == "Project":
                    self.version = \
                        self.attribute("version", projectFileFormatVersion)
                    if self.version not in self.supportedVersions:
                        self.raiseUnsupportedFormatVersion(self.version)
                elif self.name() == "Language":
                    self.project.pdata["SPELLLANGUAGE"] = [
                        self.readElementText()]
                elif self.name() == "ProjectWordList":
                    self.project.pdata["SPELLWORDS"] = \
                        [Utilities.toNativeSeparators(self.readElementText())]
                elif self.name() == "ProjectExcludeList":
                    self.project.pdata["SPELLEXCLUDES"] = \
                        [Utilities.toNativeSeparators(self.readElementText())]
                elif self.name() == "Hash":
                    self.project.pdata["HASH"] = [self.readElementText()]
                elif self.name() == "ProgLanguage":
                    self.project.pdata["MIXEDLANGUAGE"] = \
                        [int(self.attribute("mixed", "0"))]
                    self.project.pdata["PROGLANGUAGE"] = [
                        self.readElementText()]
                    if self.project.pdata["PROGLANGUAGE"][0] == "Python":
                        # convert Python to the more specific Python2
                        self.project.pdata["PROGLANGUAGE"][0] = "Python2"
                elif self.name() == "ProjectType":
                    self.project.pdata["PROJECTTYPE"] = [
                        self.readElementText()]
                elif self.name() == "Description":
                    self.project.pdata["DESCRIPTION"] = [
                        self.readElementText()]
                elif self.name() == "Version":
                    self.project.pdata["VERSION"] = [self.readElementText()]
                elif self.name() == "Author":
                    self.project.pdata["AUTHOR"] = [self.readElementText()]
                elif self.name() == "Email":
                    self.project.pdata["EMAIL"] = [self.readElementText()]
                elif self.name() == "TranslationPattern":
                    self.project.pdata["TRANSLATIONPATTERN"] = \
                        [Utilities.toNativeSeparators(self.readElementText())]
                elif self.name() == "TranslationsBinPath":
                    self.project.pdata["TRANSLATIONSBINPATH"] = \
                        [Utilities.toNativeSeparators(self.readElementText())]
                elif self.name() == "Eol":
                    self.project.pdata["EOL"] = [
                        int(self.attribute("index", "0"))]
                elif self.name() == "Sources":
                    self.__readFiles("Sources", "Source", "SOURCES")
                elif self.name() == "Forms":
                    self.__readFiles("Forms", "Form", "FORMS")
                elif self.name() == "Translations":
                    self.__readFiles(
                        "Translations", "Translation", "TRANSLATIONS")
                elif self.name() == "TranslationExceptions":
                    self.__readFiles(
                        "TranslationExceptions", "TranslationException",
                        "TRANSLATIONEXCEPTIONS")
                elif self.name() == "Resources":
                    self.__readFiles("Resources", "Resource", "RESOURCES")
                elif self.name() == "Interfaces":
                    self.__readFiles("Interfaces", "Interface", "INTERFACES")
                elif self.name() == "Others":
                    self.__readFiles("Others", "Other", "OTHERS")
                elif self.name() == "MainScript":
                    self.project.pdata["MAINSCRIPT"] = \
                        [Utilities.toNativeSeparators(self.readElementText())]
                elif self.name() == "Vcs":
                    self.__readVcs()
                elif self.name() == "FiletypeAssociations":
                    self.__readFiletypeAssociations()
                elif self.name() == "LexerAssociations":
                    self.__readLexerAssociations()
                elif self.name() == "ProjectTypeSpecific":
                    self.__readBasicDataField(
                        "ProjectTypeSpecific", "ProjectTypeSpecificData",
                        "PROJECTTYPESPECIFICDATA")
                elif self.name() == "Documentation":
                    self.__readBasicDataField(
                        "Documentation", "DocumentationParams",
                        "DOCUMENTATIONPARMS")
                elif self.name() == "Packagers":
                    self.__readBasicDataField(
                        "Packagers", "PackagersParams", "PACKAGERSPARMS")
                elif self.name() == "Checkers":
                    self.__readBasicDataField(
                        "Checkers", "CheckersParams", "CHECKERSPARMS")
                elif self.name() == "OtherTools":
                    self.__readBasicDataField(
                        "OtherTools", "OtherToolsParams", "OTHERTOOLSPARMS")
                else:
                    self.raiseUnexpectedStartTag(self.name())
        
        self.showErrorMessage()
    
    def __readFiles(self, tag, listTag, dataKey):
        """
        Private method to read a list of files.
        
        @param tag name of the list tag (string)
        @param listTag name of the list element tag (string)
        @param dataKey key of the project data element (string)
        """
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == tag:
                break
            
            if self.isStartElement():
                if self.name() == listTag:
                    self.project.pdata[dataKey].append(
                        Utilities.toNativeSeparators(self.readElementText()))
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def __readBasicDataField(self, tag, dataTag, dataKey):
        """
        Private method to read a list of files.
        
        @param tag name of the list tag (string)
        @param dataTag name of the data tag (string)
        @param dataKey key of the project data element (string)
        """
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == tag:
                break
            
            if self.isStartElement():
                if self.name() == dataTag:
                    self.project.pdata[dataKey] = self._readBasics()
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def __readVcs(self):
        """
        Private method to read the VCS info.
        """
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Vcs":
                break
            
            if self.isStartElement():
                if self.name() == "VcsType":
                    self.project.pdata["VCS"] = [self.readElementText()]
                elif self.name() == "VcsOptions":
                    self.project.pdata["VCSOPTIONS"] = [self._readBasics()]
                elif self.name() == "VcsOtherData":
                    self.project.pdata["VCSOTHERDATA"] = [self._readBasics()]
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def __readFiletypeAssociations(self):
        """
        Private method to read the file type associations.
        """
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "FiletypeAssociations":
                break
            
            if self.isStartElement():
                if self.name() == "FiletypeAssociation":
                    pattern = self.attribute("pattern", "")
                    filetype = self.attribute("type", "OTHERS")
                    if pattern:
                        self.project.pdata["FILETYPES"][pattern] = filetype
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def __readLexerAssociations(self):
        """
        Private method to read the lexer associations.
        """
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "LexerAssociations":
                break
            
            if self.isStartElement():
                if self.name() == "LexerAssociation":
                    pattern = self.attribute("pattern", "")
                    lexer = self.attribute("lexer")
                    if pattern:
                        self.project.pdata["LEXERASSOCS"][pattern] = lexer
                else:
                    self.raiseUnexpectedStartTag(self.name())
