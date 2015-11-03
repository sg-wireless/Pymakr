# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a CoffeeScript lexer with some additional methods.
"""

from __future__ import unicode_literals

from PyQt5.Qsci import QsciLexerCoffeeScript

from .Lexer import Lexer
import Preferences


class LexerCoffeeScript(Lexer, QsciLexerCoffeeScript):
    """
    Subclass to implement some additional lexer dependant methods.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget of this lexer
        """
        QsciLexerCoffeeScript.__init__(self, parent)
        Lexer.__init__(self)
        
        self.commentString = "#"
        self.streamCommentString = {
            'start': '###\n',
            'end': '\n###'
        }

    def initProperties(self):
        """
        Public slot to initialize the properties.
        """
        self.setDollarsAllowed(
            Preferences.getEditor("CoffeeScriptDollarsAllowed"))
        self.setFoldComments(
            Preferences.getEditor("CoffeScriptFoldComment"))
        self.setStylePreprocessor(
            Preferences.getEditor("CoffeeScriptStylePreprocessor"))
        self.setFoldCompact(
            Preferences.getEditor("AllFoldCompact"))
    
    def isCommentStyle(self, style):
        """
        Public method to check, if a style is a comment style.
        
        @param style style to check (integer)
        @return flag indicating a comment style (boolean)
        """
        return style in [QsciLexerCoffeeScript.Comment,
                         QsciLexerCoffeeScript.CommentDoc,
                         QsciLexerCoffeeScript.CommentLine,
                         QsciLexerCoffeeScript.CommentLineDoc,
                         QsciLexerCoffeeScript.CommentBlock,
                         QsciLexerCoffeeScript.BlockRegexComment]
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @param style style to check (integer)
        @return flag indicating a string style (boolean)
        """
        return style in [QsciLexerCoffeeScript.DoubleQuotedString,
                         QsciLexerCoffeeScript.SingleQuotedString,
                         QsciLexerCoffeeScript.UnclosedString,
                         QsciLexerCoffeeScript.VerbatimString]
    
    def defaultKeywords(self, kwSet):
        """
        Public method to get the default keywords.
        
        @param kwSet number of the keyword set (integer)
        @return string giving the keywords (string) or None
        """
        return QsciLexerCoffeeScript.keywords(self, kwSet)
    
    def maximumKeywordSet(self):
        """
        Public method to get the maximum keyword set.
        
        @return maximum keyword set (integer)
        """
        return 4
