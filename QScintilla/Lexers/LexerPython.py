# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a Python lexer with some additional methods.
"""

from __future__ import unicode_literals

import re

from PyQt5.Qsci import QsciLexerPython, QsciScintilla

from .Lexer import Lexer
import Preferences


class LexerPython(Lexer, QsciLexerPython):
    """
    Subclass to implement some additional lexer dependant methods.
    """
    def __init__(self, variant="", parent=None):
        """
        Constructor
        
        @param variant name of the language variant (string)
        @param parent parent widget of this lexer
        """
        QsciLexerPython.__init__(self, parent)
        Lexer.__init__(self)
        
        self.variant = variant
        self.commentString = "#"
    
    def language(self):
        """
        Public method to get the lexer language.
        
        @return lexer language (string)
        """
        if not self.variant:
            return QsciLexerPython.language(self)
        else:
            return self.variant
    
    def initProperties(self):
        """
        Public slot to initialize the properties.
        """
        self.setIndentationWarning(
            Preferences.getEditor("PythonBadIndentation"))
        self.setFoldComments(Preferences.getEditor("PythonFoldComment"))
        self.setFoldQuotes(Preferences.getEditor("PythonFoldString"))
        if not Preferences.getEditor("PythonAutoIndent"):
            self.setAutoIndentStyle(QsciScintilla.AiMaintain)
        try:
            self.setV2UnicodeAllowed(
                Preferences.getEditor("PythonAllowV2Unicode"))
            self.setV3BinaryOctalAllowed(
                Preferences.getEditor("PythonAllowV3Binary"))
            self.setV3BytesAllowed(Preferences.getEditor("PythonAllowV3Bytes"))
        except AttributeError:
            pass
        try:
            self.setFoldQuotes(Preferences.getEditor("PythonFoldQuotes"))
            self.setStringsOverNewlineAllowed(
                Preferences.getEditor("PythonStringsOverNewLineAllowed"))
        except AttributeError:
            pass
        try:
            self.setHighlightSubidentifiers(
                Preferences.getEditor("PythonHighlightSubidentifier"))
        except AttributeError:
            pass
        
    def getIndentationDifference(self, line, editor):
        """
        Public method to determine the difference for the new indentation.
        
        @param line line to perform the calculation for (integer)
        @param editor QScintilla editor
        @return amount of difference in indentation (integer)
        """
        indent_width = Preferences.getEditor('IndentWidth')
        
        lead_spaces = editor.indentation(line)
        
        pline = line - 1
        while pline >= 0 and re.match('^\s*(#.*)?$', editor.text(pline)):
            pline -= 1
        
        if pline < 0:
            last = 0
        else:
            previous_lead_spaces = editor.indentation(pline)
            # trailing spaces
            m = re.search(':\s*(#.*)?$', editor.text(pline))
            last = previous_lead_spaces
            if m:
                last += indent_width
            else:
                # special cases, like pass (unindent) or return (also unindent)
                m = re.search('(pass\s*(#.*)?$)|(^[^#]return)',
                              editor.text(pline))
                if m:
                    last -= indent_width
        
        if lead_spaces % indent_width != 0 or lead_spaces == 0 \
           or self.lastIndented != line:
            indentDifference = last - lead_spaces
        else:
            indentDifference = -indent_width
        
        return indentDifference
    
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
        return style in [QsciLexerPython.Comment,
                         QsciLexerPython.CommentBlock]
    
    def isStringStyle(self, style):
        """
        Public method to check, if a style is a string style.
        
        @param style style to check (integer)
        @return flag indicating a string style (boolean)
        """
        return style in [QsciLexerPython.DoubleQuotedString,
                         QsciLexerPython.SingleQuotedString,
                         QsciLexerPython.TripleDoubleQuotedString,
                         QsciLexerPython.TripleSingleQuotedString,
                         QsciLexerPython.UnclosedString]
    
    def defaultKeywords(self, kwSet):
        """
        Public method to get the default keywords.
        
        @param kwSet number of the keyword set (integer)
        @return string giving the keywords (string) or None
        """
        return QsciLexerPython.keywords(self, kwSet)
    
    def maximumKeywordSet(self):
        """
        Public method to get the maximum keyword set.
        
        @return maximum keyword set (integer)
        """
        return 2
