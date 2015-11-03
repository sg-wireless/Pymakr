# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a CSS lexer with some additional methods.
"""

from __future__ import unicode_literals

from PyQt5.Qsci import QsciLexerCSS

from .Lexer import Lexer
import Preferences


class LexerCSS(Lexer, QsciLexerCSS):
    """
    Subclass to implement some additional lexer dependant methods.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget of this lexer
        """
        QsciLexerCSS.__init__(self, parent)
        Lexer.__init__(self)
        
        self.commentString = "#"
        self.streamCommentString = {
            'start': '/* ',
            'end': ' */'
        }
    
    def initProperties(self):
        """
        Public slot to initialize the properties.
        """
        self.setFoldComments(Preferences.getEditor("CssFoldComment"))
        self.setFoldCompact(Preferences.getEditor("AllFoldCompact"))
        try:
            self.setHSSLanguage(
                Preferences.getEditor("CssHssSupport"))
            self.setLessLanguage(
                Preferences.getEditor("CssLessSupport"))
            self.setSCSSLanguage(
                Preferences.getEditor("CssSassySupport"))
        except AttributeError:
            pass
    
    def isCommentStyle(self, style):
        """
        Public method to check, if a style is a comment style.
        
        @param style style to check (integer)
        @return flag indicating a comment style (boolean)
        """
        return style in [QsciLexerCSS.Comment]
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @param style style to check (integer)
        @return flag indicating a string style (boolean)
        """
        return style in [QsciLexerCSS.DoubleQuotedString,
                         QsciLexerCSS.SingleQuotedString]
    
    def defaultKeywords(self, kwSet):
        """
        Public method to get the default keywords.
        
        @param kwSet number of the keyword set (integer)
        @return string giving the keywords (string) or None
        """
        return QsciLexerCSS.keywords(self, kwSet)
