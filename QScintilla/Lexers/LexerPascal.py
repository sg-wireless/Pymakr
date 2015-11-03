# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a Pascal lexer with some additional methods.
"""

from __future__ import unicode_literals

from PyQt5.Qsci import QsciLexerPascal

from .Lexer import Lexer
import Preferences


class LexerPascal(Lexer, QsciLexerPascal):
    """
    Subclass to implement some additional lexer dependant methods.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget of this lexer
        """
        QsciLexerPascal.__init__(self, parent)
        Lexer.__init__(self)
        
        self.commentString = "//"
        self.streamCommentString = {
            'start': '{ ',
            'end': ' }'
        }
    
    def initProperties(self):
        """
        Public slot to initialize the properties.
        """
        self.setFoldComments(Preferences.getEditor("PascalFoldComment"))
        self.setFoldPreprocessor(
            Preferences.getEditor("PascalFoldPreprocessor"))
        self.setFoldCompact(Preferences.getEditor("AllFoldCompact"))
        try:
            self.setSmartHighlighting(
                Preferences.getEditor("PascalSmartHighlighting"))
        except AttributeError:
            pass
    
    def autoCompletionWordSeparators(self):
        """
        Public method to return the list of separators for autocompletion.
        
        @return list of separators (list of strings)
        """
        return ['.']
    
    def isCommentStyle(self, style):
        """
        Public method to check, if a style is a comment style.
        
        @param style style to check (integer)
        @return flag indicating a comment style (boolean)
        """
        try:
            return style in [QsciLexerPascal.Comment,
                             QsciLexerPascal.CommentDoc,
                             QsciLexerPascal.CommentLine]
        except AttributeError:
            return style in [QsciLexerPascal.Comment,
                             QsciLexerPascal.CommentParenthesis,
                             QsciLexerPascal.CommentLine]
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @param style style to check (integer)
        @return flag indicating a string style (boolean)
        """
        return style in [QsciLexerPascal.SingleQuotedString]
    
    def defaultKeywords(self, kwSet):
        """
        Public method to get the default keywords.
        
        @param kwSet number of the keyword set (integer)
        @return string giving the keywords (string) or None
        """
        return QsciLexerPascal.keywords(self, kwSet)
