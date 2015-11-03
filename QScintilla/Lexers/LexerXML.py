# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a XML lexer with some additional methods.
"""

from __future__ import unicode_literals

from PyQt5.Qsci import QsciLexerXML

from .Lexer import Lexer
import Preferences


class LexerXML(Lexer, QsciLexerXML):
    """
    Subclass to implement some additional lexer dependant methods.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget of this lexer
        """
        QsciLexerXML.__init__(self, parent)
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
            self.setScriptsStyled(Preferences.getEditor("XMLStyleScripts"))
        except AttributeError:
            pass
    
    def isCommentStyle(self, style):
        """
        Public method to check, if a style is a comment style.
        
        @param style style to check (integer)
        @return flag indicating a comment style (boolean)
        """
        return style in [QsciLexerXML.HTMLComment,
                         QsciLexerXML.ASPXCComment,
                         QsciLexerXML.SGMLComment,
                         QsciLexerXML.SGMLParameterComment,
                         QsciLexerXML.JavaScriptComment,
                         QsciLexerXML.JavaScriptCommentDoc,
                         QsciLexerXML.JavaScriptCommentLine,
                         QsciLexerXML.ASPJavaScriptComment,
                         QsciLexerXML.ASPJavaScriptCommentDoc,
                         QsciLexerXML.ASPJavaScriptCommentLine,
                         QsciLexerXML.VBScriptComment,
                         QsciLexerXML.ASPVBScriptComment,
                         QsciLexerXML.PythonComment,
                         QsciLexerXML.ASPPythonComment,
                         QsciLexerXML.PHPComment]
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @param style style to check (integer)
        @return flag indicating a string style (boolean)
        """
        return style in [QsciLexerXML.HTMLDoubleQuotedString,
                         QsciLexerXML.HTMLSingleQuotedString,
                         QsciLexerXML.SGMLDoubleQuotedString,
                         QsciLexerXML.SGMLSingleQuotedString,
                         QsciLexerXML.JavaScriptDoubleQuotedString,
                         QsciLexerXML.JavaScriptSingleQuotedString,
                         QsciLexerXML.JavaScriptUnclosedString,
                         QsciLexerXML.ASPJavaScriptDoubleQuotedString,
                         QsciLexerXML.ASPJavaScriptSingleQuotedString,
                         QsciLexerXML.ASPJavaScriptUnclosedString,
                         QsciLexerXML.VBScriptString,
                         QsciLexerXML.VBScriptUnclosedString,
                         QsciLexerXML.ASPVBScriptString,
                         QsciLexerXML.ASPVBScriptUnclosedString,
                         QsciLexerXML.PythonDoubleQuotedString,
                         QsciLexerXML.PythonSingleQuotedString,
                         QsciLexerXML.PythonTripleDoubleQuotedString,
                         QsciLexerXML.PythonTripleSingleQuotedString,
                         QsciLexerXML.ASPPythonDoubleQuotedString,
                         QsciLexerXML.ASPPythonSingleQuotedString,
                         QsciLexerXML.ASPPythonTripleDoubleQuotedString,
                         QsciLexerXML.ASPPythonTripleSingleQuotedString,
                         QsciLexerXML.PHPDoubleQuotedString,
                         QsciLexerXML.PHPSingleQuotedString]
    
    def defaultKeywords(self, kwSet):
        """
        Public method to get the default keywords.
        
        @param kwSet number of the keyword set (integer)
        @return string giving the keywords (string) or None
        """
        return QsciLexerXML.keywords(self, kwSet)
