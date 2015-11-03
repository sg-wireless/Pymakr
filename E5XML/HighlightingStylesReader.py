# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#


"""
Module implementing a class for reading a highlighting styles XML file.
"""

from __future__ import unicode_literals

from PyQt5.QtGui import QColor, QFont

from .Config import highlightingStylesFileFormatVersion
from .XMLStreamReaderBase import XMLStreamReaderBase


class HighlightingStylesReader(XMLStreamReaderBase):
    """
    Class for reading a highlighting styles XML file.
    """
    supportedVersions = ["4.3"]
    
    def __init__(self, device, lexers):
        """
        Constructor
        
        @param device reference to the I/O device to read from (QIODevice)
        @param lexers list of lexer objects for which to export the styles
        """
        XMLStreamReaderBase.__init__(self, device)
        
        self.lexers = lexers
        
        self.version = ""
    
    def readXML(self):
        """
        Public method to read and parse the XML document.
        """
        while not self.atEnd():
            self.readNext()
            if self.isStartElement():
                if self.name() == "HighlightingStyles":
                    self.version = self.attribute(
                        "version",
                        highlightingStylesFileFormatVersion)
                    if self.version not in self.supportedVersions:
                        self.raiseUnsupportedFormatVersion(self.version)
                elif self.name() == "Lexer":
                    self.__readLexer()
                else:
                    self.raiseUnexpectedStartTag(self.name())
        
        self.showErrorMessage()
    
    def __readLexer(self):
        """
        Private method to read the lexer info.
        """
        language = self.attribute("name")
        if language and language in self.lexers:
            lexer = self.lexers[language]
        else:
            lexer = None
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Lexer":
                break
            
            if self.isStartElement():
                if self.name() == "Style":
                    self.__readStyle(lexer)
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def __readStyle(self, lexer):
        """
        Private method to read the style info.
        
        @param lexer reference to the lexer object
        """
        if lexer is not None:
            style = self.attribute("style")
            if style:
                style = int(style)
                
                color = self.attribute("color")
                if color:
                    color = QColor(color)
                else:
                    color = lexer.defaultColor(style)
                lexer.setColor(color, style)
                
                paper = self.attribute("paper")
                if paper:
                    paper = QColor(paper)
                else:
                    paper = lexer.defaultPaper(style)
                lexer.setPaper(paper, style)
                
                fontStr = self.attribute("font")
                if fontStr:
                    font = QFont()
                    font.fromString(fontStr)
                else:
                    font = lexer.defaultFont(style)
                lexer.setFont(font, style)
                
                eolfill = self.attribute("eolfill")
                if eolfill:
                    eolfill = self.toBool(eolfill)
                    if eolfill is None:
                        eolfill = lexer.defaulEolFill(style)
                else:
                    eolfill = lexer.defaulEolFill(style)
                lexer.setEolFill(eolfill, style)
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Style":
                break
            
            if self.isStartElement():
                self.raiseUnexpectedStartTag(self.name())
