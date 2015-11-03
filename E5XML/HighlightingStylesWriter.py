# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the writer class for writing a highlighting styles XML
file.
"""

from __future__ import unicode_literals

import time

from .XMLStreamWriterBase import XMLStreamWriterBase
from .Config import highlightingStylesFileFormatVersion

import Preferences


class HighlightingStylesWriter(XMLStreamWriterBase):
    """
    Class implementing the writer class for writing a highlighting styles XML
    file.
    """
    def __init__(self, device, lexers):
        """
        Constructor
        
        @param device reference to the I/O device to write to (QIODevice)
        @param lexers list of lexer objects for which to export the styles
        """
        XMLStreamWriterBase.__init__(self, device)
        
        self.lexers = lexers
        self.email = Preferences.getUser("Email")
    
    def writeXML(self):
        """
        Public method to write the XML to the file.
        """
        XMLStreamWriterBase.writeXML(self)
        
        self.writeDTD(
            '<!DOCTYPE HighlightingStyles SYSTEM'
            ' "HighlightingStyles-{0}.dtd">'.format(
                highlightingStylesFileFormatVersion))
        
        # add some generation comments
        self.writeComment(" Eric6 highlighting styles ")
        self.writeComment(
            " Saved: {0}".format(time.strftime('%Y-%m-%d, %H:%M:%S')))
        self.writeComment(" Author: {0} ".format(self.email))
        
        # add the main tag
        self.writeStartElement("HighlightingStyles")
        self.writeAttribute("version", highlightingStylesFileFormatVersion)
        
        for lexer in self.lexers:
            self.writeStartElement("Lexer")
            self.writeAttribute("name", lexer.language())
            for style in lexer.descriptions:
                self.writeStartElement("Style")
                self.writeAttribute("style", str(style))
                self.writeAttribute("color", lexer.color(style).name())
                self.writeAttribute("paper", lexer.paper(style).name())
                self.writeAttribute("font", lexer.font(style).toString())
                self.writeAttribute("eolfill", str(lexer.eolFill(style)))
                self.writeCharacters(lexer.description(style))
                self.writeEndElement()
            self.writeEndElement()
        
        self.writeEndElement()
        self.writeEndDocument()
