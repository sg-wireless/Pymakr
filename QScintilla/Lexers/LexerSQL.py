# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a SQL lexer with some additional methods.
"""

from __future__ import unicode_literals

from PyQt5.Qsci import QsciLexerSQL

from .Lexer import Lexer
import Preferences


class LexerSQL(Lexer, QsciLexerSQL):
    """
    Subclass to implement some additional lexer dependant methods.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget of this lexer
        """
        QsciLexerSQL.__init__(self, parent)
        Lexer.__init__(self)
        
        self.commentString = "--"
    
    def initProperties(self):
        """
        Public slot to initialize the properties.
        """
        self.setFoldComments(Preferences.getEditor("SqlFoldComment"))
        self.setBackslashEscapes(Preferences.getEditor("SqlBackslashEscapes"))
        self.setFoldCompact(Preferences.getEditor("AllFoldCompact"))
        try:
            self.setDottedWords(Preferences.getEditor("SqlDottedWords"))
            self.setFoldAtElse(Preferences.getEditor("SqlFoldAtElse"))
            self.setFoldOnlyBegin(Preferences.getEditor("SqlFoldOnlyBegin"))
            self.setHashComments(Preferences.getEditor("SqlHashComments"))
            self.setQuotedIdentifiers(
                Preferences.getEditor("SqlQuotedIdentifiers"))
        except AttributeError:
            pass
    
    def isCommentStyle(self, style):
        """
        Public method to check, if a style is a comment style.
        
        @param style style to check (integer)
        @return flag indicating a comment style (boolean)
        """
        return style in [QsciLexerSQL.Comment,
                         QsciLexerSQL.CommentDoc,
                         QsciLexerSQL.CommentLine,
                         QsciLexerSQL.CommentLineHash]
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @param style style to check (integer)
        @return flag indicating a string style (boolean)
        """
        return style in [QsciLexerSQL.DoubleQuotedString,
                         QsciLexerSQL.SingleQuotedString]
    
    def defaultKeywords(self, kwSet):
        """
        Public method to get the default keywords.
        
        @param kwSet number of the keyword set (integer)
        @return string giving the keywords (string) or None
        """
        return QsciLexerSQL.keywords(self, kwSet)
    
    def maximumKeywordSet(self):
        """
        Public method to get the maximum keyword set.
        
        @return maximum keyword set (integer)
        """
        return 8
