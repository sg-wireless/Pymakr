# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a base class for custom lexers.
"""

from __future__ import unicode_literals

from PyQt5.Qsci import QsciLexer

from .Lexer import Lexer


class LexerContainer(Lexer, QsciLexer):
    """
    Subclass as a base for the implementation of custom lexers.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget of this lexer
        """
        QsciLexer.__init__(self, parent)
        Lexer.__init__(self)
        
        self.editor = parent
    
    def language(self):
        """
        Public method returning the language of the lexer.
        
        @return language of the lexer (string)
        """
        return "Container"
    
    def lexer(self):
        """
        Public method returning the type of the lexer.
        
        @return type of the lexer (string)
        """
        if hasattr(self, 'lexerId'):
            return None
        else:
            return "container"
    
    def description(self, style):
        """
        Public method returning the descriptions of the styles supported
        by the lexer.
        
        <b>Note</b>: This methods needs to be overridden by the lexer class.
        
        @param style style number (integer)
        @return description for the given style (string)
        """
        return ""
    
    def styleBitsNeeded(self):
        """
        Public method to get the number of style bits needed by the lexer.
        
        @return number of style bits needed (integer)
        """
        return 5
    
    def styleText(self, start, end):
        """
        Public method to perform the styling.
        
        @param start position of first character to be styled (integer)
        @param end position of last character to be styled (integer)
        """
        self.editor.startStyling(start, 0x1f)
        self.editor.setStyling(end - start + 1, 0)
    
    def keywords(self, kwSet):
        """
        Public method to get the keywords.
        
        @param kwSet number of the keyword set (integer)
        @return string giving the keywords (string) or None
        """
        return Lexer.keywords(self, kwSet)
