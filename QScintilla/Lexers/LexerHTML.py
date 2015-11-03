# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a HTML lexer with some additional methods.
"""

from __future__ import unicode_literals

from PyQt5.Qsci import QsciLexerHTML

from .Lexer import Lexer
import Preferences


class LexerHTML(Lexer, QsciLexerHTML):
    """
    Subclass to implement some additional lexer dependant methods.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget of this lexer
        """
        QsciLexerHTML.__init__(self, parent)
        Lexer.__init__(self)
        
        self.streamCommentString = {
            'start': '<!-- ',
            'end': ' -->'
        }
    
    def initProperties(self):
        """
        Public slot to initialize the properties.
        """
        self.setFoldPreprocessor(Preferences.getEditor("HtmlFoldPreprocessor"))
        self.setCaseSensitiveTags(
            Preferences.getEditor("HtmlCaseSensitiveTags"))
        self.setFoldCompact(Preferences.getEditor("AllFoldCompact"))
        try:
            self.setFoldScriptComments(
                Preferences.getEditor("HtmlFoldScriptComments"))
            self.setFoldScriptHeredocs(
                Preferences.getEditor("HtmlFoldScriptHeredocs"))
        except AttributeError:
            pass
        try:
            self.setDjangoTemplates(
                Preferences.getEditor("HtmlDjangoTemplates"))
            self.setMakoTemplates(Preferences.getEditor("HtmlMakoTemplates"))
        except AttributeError:
            pass
    
    def isCommentStyle(self, style):
        """
        Public method to check, if a style is a comment style.
        
        @param style style to check (integer)
        @return flag indicating a comment style (boolean)
        """
        return style in [QsciLexerHTML.HTMLComment,
                         QsciLexerHTML.ASPXCComment,
                         QsciLexerHTML.SGMLComment,
                         QsciLexerHTML.SGMLParameterComment,
                         QsciLexerHTML.JavaScriptComment,
                         QsciLexerHTML.JavaScriptCommentDoc,
                         QsciLexerHTML.JavaScriptCommentLine,
                         QsciLexerHTML.ASPJavaScriptComment,
                         QsciLexerHTML.ASPJavaScriptCommentDoc,
                         QsciLexerHTML.ASPJavaScriptCommentLine,
                         QsciLexerHTML.VBScriptComment,
                         QsciLexerHTML.ASPVBScriptComment,
                         QsciLexerHTML.PythonComment,
                         QsciLexerHTML.ASPPythonComment,
                         QsciLexerHTML.PHPComment]
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @param style style to check (integer)
        @return flag indicating a string style (boolean)
        """
        return style in [QsciLexerHTML.HTMLDoubleQuotedString,
                         QsciLexerHTML.HTMLSingleQuotedString,
                         QsciLexerHTML.SGMLDoubleQuotedString,
                         QsciLexerHTML.SGMLSingleQuotedString,
                         QsciLexerHTML.JavaScriptDoubleQuotedString,
                         QsciLexerHTML.JavaScriptSingleQuotedString,
                         QsciLexerHTML.JavaScriptUnclosedString,
                         QsciLexerHTML.ASPJavaScriptDoubleQuotedString,
                         QsciLexerHTML.ASPJavaScriptSingleQuotedString,
                         QsciLexerHTML.ASPJavaScriptUnclosedString,
                         QsciLexerHTML.VBScriptString,
                         QsciLexerHTML.VBScriptUnclosedString,
                         QsciLexerHTML.ASPVBScriptString,
                         QsciLexerHTML.ASPVBScriptUnclosedString,
                         QsciLexerHTML.PythonDoubleQuotedString,
                         QsciLexerHTML.PythonSingleQuotedString,
                         QsciLexerHTML.PythonTripleDoubleQuotedString,
                         QsciLexerHTML.PythonTripleSingleQuotedString,
                         QsciLexerHTML.ASPPythonDoubleQuotedString,
                         QsciLexerHTML.ASPPythonSingleQuotedString,
                         QsciLexerHTML.ASPPythonTripleDoubleQuotedString,
                         QsciLexerHTML.ASPPythonTripleSingleQuotedString,
                         QsciLexerHTML.PHPDoubleQuotedString,
                         QsciLexerHTML.PHPSingleQuotedString]
    
    def defaultKeywords(self, kwSet):
        """
        Public method to get the default keywords.
        
        @param kwSet number of the keyword set (integer)
        @return string giving the keywords (string) or None
        """
        return QsciLexerHTML.keywords(self, kwSet)
