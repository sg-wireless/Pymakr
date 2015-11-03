# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a TCL/Tk lexer with some additional methods.
"""

from __future__ import unicode_literals

from PyQt5.Qsci import QsciLexerTCL

from .Lexer import Lexer

import Preferences


class LexerTCL(Lexer, QsciLexerTCL):
    """
    Subclass to implement some additional lexer dependant methods.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget of this lexer
        """
        QsciLexerTCL.__init__(self, parent)
        Lexer.__init__(self)
        
        self.commentString = "#"
    
    def initProperties(self):
        """
        Public slot to initialize the properties.
        """
        try:
            self.setFoldCompact(Preferences.getEditor("AllFoldCompact"))
        except AttributeError:
            pass
        try:
            self.setFoldComments(Preferences.getEditor("TclFoldComment"))
        except AttributeError:
            pass
    
    def isCommentStyle(self, style):
        """
        Public method to check, if a style is a comment style.
        
        @param style style to check (integer)
        @return flag indicating a comment style (boolean)
        """
        return style in [QsciLexerTCL.Comment,
                         QsciLexerTCL.CommentBlock,
                         QsciLexerTCL.CommentBox,
                         QsciLexerTCL.CommentLine]
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @param style style to check (integer)
        @return flag indicating a string style (boolean)
        """
        return style in [QsciLexerTCL.QuotedString]
    
    def defaultKeywords(self, kwSet):
        """
        Public method to get the default keywords.
        
        @param kwSet number of the keyword set (integer)
        @return string giving the keywords (string) or None
        """
        return QsciLexerTCL.keywords(self, kwSet)
    
    def maximumKeywordSet(self):
        """
        Public method to get the maximum keyword set.
        
        @return maximum keyword set (integer)
        """
        return 9
