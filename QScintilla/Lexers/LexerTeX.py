# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a Tex lexer with some additional methods.
"""

from __future__ import unicode_literals

from PyQt5.Qsci import QsciLexerTeX

from .Lexer import Lexer
import Preferences


class LexerTeX(Lexer, QsciLexerTeX):
    """
    Subclass to implement some additional lexer dependant methods.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget of this lexer
        """
        QsciLexerTeX.__init__(self, parent)
        Lexer.__init__(self)
        
        self.commentString = "%"
    
    def initProperties(self):
        """
        Public slot to initialize the properties.
        """
        try:
            self.setFoldCompact(Preferences.getEditor("AllFoldCompact"))
            self.setFoldComments(Preferences.getEditor("TexFoldComment"))
            self.setProcessComments(
                Preferences.getEditor("TexProcessComments"))
            self.setProcessIf(Preferences.getEditor("TexProcessIf"))
        except AttributeError:
            pass
    
    def isCommentStyle(self, style):
        """
        Public method to check, if a style is a comment style.
        
        @param style style to check (integer)
        @return flag indicating a comment style (boolean)
        """
        return False
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @param style style to check (integer)
        @return flag indicating a string style (boolean)
        """
        return style in [QsciLexerTeX.Text]
    
    def defaultKeywords(self, kwSet):
        """
        Public method to get the default keywords.
        
        @param kwSet number of the keyword set (integer)
        @return string giving the keywords (string) or None
        """
        return QsciLexerTeX.keywords(self, kwSet)
