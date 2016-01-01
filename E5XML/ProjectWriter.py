# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the writer class for writing an XML project file.
"""

from __future__ import unicode_literals

import time

from E5Gui.E5Application import e5App

from .XMLStreamWriterBase import XMLStreamWriterBase
from .Config import projectFileFormatVersion

import Preferences
import Utilities


class ProjectWriter(XMLStreamWriterBase):
    """
    Class implementing the writer class for writing an XML project file.
    """
    def __init__(self, device, projectName):
        """
        Constructor
        
        @param device reference to the I/O device to write to (QIODevice)
        @param projectName name of the project (string)
        """
        XMLStreamWriterBase.__init__(self, device)
        
        self.pdata = e5App().getObject("Project").pdata
        self.name = projectName
        
    def writeXML(self):
        """
        Public method to write the XML to the file.
        """
        XMLStreamWriterBase.writeXML(self)
        
        self.writeDTD('<!DOCTYPE Project SYSTEM "Project-{0}.dtd">'.format(
            projectFileFormatVersion))
        
        # add some generation comments
        self.writeComment(
            " eric project file for project {0} ".format(self.name))
        if Preferences.getProject("XMLTimestamp"):
            self.writeComment(
                " Saved: {0} ".format(time.strftime('%Y-%m-%d, %H:%M:%S')))
        self.writeComment(" Copyright (C) {0} {1}, {2} ".format(
            time.strftime('%Y'),
            self.pdata["AUTHOR"][0],
            self.pdata["EMAIL"][0]))
        
        # add the main tag
        self.writeStartElement("Project")
        self.writeAttribute("version", projectFileFormatVersion)
        
        # do the language (used for spell checking)
        self.writeTextElement("Language", self.pdata["SPELLLANGUAGE"][0])
        if len(self.pdata["SPELLWORDS"][0]) > 0:
            self.writeTextElement(
                "ProjectWordList",
                Utilities.fromNativeSeparators(self.pdata["SPELLWORDS"][0]))
        if len(self.pdata["SPELLEXCLUDES"][0]) > 0:
            self.writeTextElement(
                "ProjectExcludeList",
                Utilities.fromNativeSeparators(self.pdata["SPELLEXCLUDES"][0]))
        
        # do the hash
        self.writeTextElement("Hash", self.pdata["HASH"][0])
        
        # do the programming language
        self.writeStartElement("ProgLanguage")
        self.writeAttribute("mixed", str(int(self.pdata["MIXEDLANGUAGE"][0])))
        self.writeCharacters(self.pdata["PROGLANGUAGE"][0])
        self.writeEndElement()
        
        # do the UI type
        self.writeTextElement("ProjectType", self.pdata["PROJECTTYPE"][0])
        
        # do description
        if self.pdata["DESCRIPTION"]:
            self.writeTextElement("Description", self.pdata["DESCRIPTION"][0])
        
        # do version, author and email
        self.writeTextElement("Version", self.pdata["VERSION"][0])
        self.writeTextElement("Author", self.pdata["AUTHOR"][0])
        self.writeTextElement("Email", self.pdata["EMAIL"][0])
            
        # do the translation pattern
        if self.pdata["TRANSLATIONPATTERN"]:
            self.writeTextElement(
                "TranslationPattern",
                Utilities.fromNativeSeparators(
                    self.pdata["TRANSLATIONPATTERN"][0]))
        
        # do the binary translations path
        if self.pdata["TRANSLATIONSBINPATH"]:
            self.writeTextElement(
                "TranslationsBinPath",
                Utilities.fromNativeSeparators(
                    self.pdata["TRANSLATIONSBINPATH"][0]))
        
        # do the eol setting
        if self.pdata["EOL"] and self.pdata["EOL"][0]:
            self.writeEmptyElement("Eol")
            self.writeAttribute("index", str(int(self.pdata["EOL"][0])))
        
        # do the sources
        self.writeStartElement("Sources")
        for name in sorted(self.pdata["SOURCES"]):
            self.writeTextElement(
                "Source", Utilities.fromNativeSeparators(name))
        self.writeEndElement()
        
        # do the forms
        self.writeStartElement("Forms")
        for name in sorted(self.pdata["FORMS"]):
            self.writeTextElement("Form", Utilities.fromNativeSeparators(name))
        self.writeEndElement()
        
        # do the translations
        self.writeStartElement("Translations")
        for name in sorted(self.pdata["TRANSLATIONS"]):
            self.writeTextElement(
                "Translation", Utilities.fromNativeSeparators(name))
        self.writeEndElement()
        
        # do the translation exceptions
        if self.pdata["TRANSLATIONEXCEPTIONS"]:
            self.writeStartElement("TranslationExceptions")
            for name in sorted(self.pdata["TRANSLATIONEXCEPTIONS"]):
                self.writeTextElement(
                    "TranslationException",
                    Utilities.fromNativeSeparators(name))
            self.writeEndElement()
        
        # do the resources
        self.writeStartElement("Resources")
        for name in sorted(self.pdata["RESOURCES"]):
            self.writeTextElement(
                "Resource", Utilities.fromNativeSeparators(name))
        self.writeEndElement()
        
        # do the interfaces (IDL)
        self.writeStartElement("Interfaces")
        for name in sorted(self.pdata["INTERFACES"]):
            self.writeTextElement(
                "Interface", Utilities.fromNativeSeparators(name))
        self.writeEndElement()
        
        # do the others
        self.writeStartElement("Others")
        for name in sorted(self.pdata["OTHERS"]):
            self.writeTextElement(
                "Other", Utilities.fromNativeSeparators(name))
        self.writeEndElement()
        
        # do the main script
        if self.pdata["MAINSCRIPT"]:
            self.writeTextElement(
                "MainScript",
                Utilities.fromNativeSeparators(self.pdata["MAINSCRIPT"][0]))
        
        # do the vcs stuff
        self.writeStartElement("Vcs")
        if self.pdata["VCS"]:
            self.writeTextElement("VcsType", self.pdata["VCS"][0])
        if self.pdata["VCSOPTIONS"]:
            self.writeBasics("VcsOptions", self.pdata["VCSOPTIONS"][0])
        if self.pdata["VCSOTHERDATA"]:
            self.writeBasics("VcsOtherData", self.pdata["VCSOTHERDATA"][0])
        self.writeEndElement()
        
        # do the filetype associations
        self.writeStartElement("FiletypeAssociations")
        for pattern, filetype in sorted(self.pdata["FILETYPES"].items()):
            self.writeEmptyElement("FiletypeAssociation")
            self.writeAttribute("pattern", pattern)
            self.writeAttribute("type", filetype)
        self.writeEndElement()
        
        # do the lexer associations
        if self.pdata["LEXERASSOCS"]:
            self.writeStartElement("LexerAssociations")
            for pattern, lexer in sorted(self.pdata["LEXERASSOCS"].items()):
                self.writeEmptyElement("LexerAssociation")
                self.writeAttribute("pattern", pattern)
                self.writeAttribute("lexer", lexer)
            self.writeEndElement()
        
        # do the extra project data stuff
        if len(self.pdata["PROJECTTYPESPECIFICDATA"]):
            self.writeStartElement("ProjectTypeSpecific")
            if self.pdata["PROJECTTYPESPECIFICDATA"]:
                self.writeBasics(
                    "ProjectTypeSpecificData",
                    self.pdata["PROJECTTYPESPECIFICDATA"])
            self.writeEndElement()
        
        # do the documentation generators stuff
        if len(self.pdata["DOCUMENTATIONPARMS"]):
            self.writeStartElement("Documentation")
            if self.pdata["DOCUMENTATIONPARMS"]:
                self.writeBasics(
                    "DocumentationParams", self.pdata["DOCUMENTATIONPARMS"])
            self.writeEndElement()
        
        # do the packagers stuff
        if len(self.pdata["PACKAGERSPARMS"]):
            self.writeStartElement("Packagers")
            if self.pdata["PACKAGERSPARMS"]:
                self.writeBasics(
                    "PackagersParams", self.pdata["PACKAGERSPARMS"])
            self.writeEndElement()
        
        # do the checkers stuff
        if len(self.pdata["CHECKERSPARMS"]):
            self.writeStartElement("Checkers")
            if self.pdata["CHECKERSPARMS"]:
                self.writeBasics(
                    "CheckersParams", self.pdata["CHECKERSPARMS"])
            self.writeEndElement()
        
        # do the other tools stuff
        if len(self.pdata["OTHERTOOLSPARMS"]):
            self.writeStartElement("OtherTools")
            if self.pdata["OTHERTOOLSPARMS"]:
                self.writeBasics(
                    "OtherToolsParams", self.pdata["OTHERTOOLSPARMS"])
            self.writeEndElement()
        
        self.writeEndElement()
        self.writeEndDocument()
