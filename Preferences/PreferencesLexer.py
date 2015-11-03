# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a special QextScintilla lexer to handle the preferences.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QColor, QFont
from PyQt5.Qsci import QsciLexer

import Preferences
import Globals


class PreferencesLexerError(Exception):
    """
    Class defining a special error for the PreferencesLexer class.
    """
    def __init__(self):
        """
        Constructor
        """
        self._errorMessage = QCoreApplication.translate(
            "PreferencesLexerError",
            "Unspecific PreferencesLexer error.")
        
    def __repr__(self):
        """
        Special method returning a representation of the exception.
        
        @return string representing the error message
        """
        return repr(self._errorMessage)
        
    def __str__(self):
        """
        Special method returning a string representation of the exception.
        
        @return string representing the error message
        """
        return self._errorMessage


class PreferencesLexerLanguageError(PreferencesLexerError):
    """
    Class defining a special error for the PreferencesLexer class.
    """
    def __init__(self, language):
        """
        Constructor
        
        @param language lexer language (string)
        """
        PreferencesLexerError.__init__(self)
        self._errorMessage = QCoreApplication.translate(
            "PreferencesLexerError",
            'Unsupported Lexer Language: {0}').format(language)


class PreferencesLexer(QsciLexer):
    """
    Subclass of QsciLexer to implement preferences specific lexer methods.
    """
    def __init__(self, language, parent=None):
        """
        Constructor
        
        @param language The lexer language. (string)
        @param parent The parent widget of this lexer. (QextScintilla)
        @exception PreferencesLexerLanguageError raised to indicate an invalid
            lexer language
        """
        super(PreferencesLexer, self).__init__(parent)
        
        # These default font families are taken from QScintilla
        if Globals.isWindowsPlatform():
            self.__defaultFontFamily = "Courier New"
        elif Globals.isMacPlatform():
            self.__defaultFontFamily = "Courier"
        else:
            self.__defaultFontFamily = "Bitstream Vera Sans Mono"
        
        # instantiate a lexer object for the given language
        import QScintilla.Lexers
        lex = QScintilla.Lexers.getLexer(language)
        if lex is None:
            raise PreferencesLexerLanguageError(language)
        
        # define the local store
        self.colours = {}
        self.defaultColours = {}
        self.papers = {}
        self.defaultPapers = {}
        self.eolFills = {}
        self.defaultEolFills = {}
        self.fonts = {}
        self.defaultFonts = {}
        self.descriptions = {}
        self.ind2style = {}
        self.styles = []
        
        # fill local store with default values from lexer
        # and built up styles list and conversion table from index to style
        self.__language = lex.language()
        
        index = 0
        for i in range(128):
            desc = lex.description(i)
            if desc:
                self.descriptions[i] = desc
                self.styles.append(desc)
                
                self.colours[i] = lex.defaultColor(i)
                self.papers[i] = lex.defaultPaper(i)
                self.eolFills[i] = lex.defaultEolFill(i)
                self.fonts[i] = lex.defaultFont(i)
                # Override QScintilla's default font family to
                # always use a monospaced font
                self.fonts[i].setFamily(self.__defaultFontFamily)
                
                self.defaultColours[i] = lex.defaultColor(i)
                self.defaultPapers[i] = lex.defaultPaper(i)
                self.defaultEolFills[i] = lex.defaultEolFill(i)
                self.defaultFonts[i] = lex.defaultFont(i)
                self.defaultFonts[i].setFamily(self.__defaultFontFamily)
                
                self.ind2style[index] = i
                index += 1
        
        self.colorChanged.connect(self.setColor)
        self.eolFillChanged.connect(self.setEolFill)
        self.fontChanged.connect(self.setFont)
        self.paperChanged.connect(self.setPaper)
        
        # read the last stored values from preferences file
        self.readSettings(Preferences.Prefs.settings, "Scintilla")
        
    def defaultColor(self, style):
        """
        Public method to get the default colour of a style.
        
        @param style the style number (int)
        @return colour
        """
        return self.defaultColours[style]
        
    def color(self, style):
        """
        Public method to get the colour of a style.
        
        @param style the style number (int)
        @return colour
        """
        return self.colours[style]
        
    def setColor(self, c, style):
        """
        Public method to set the colour for a style.
        
        @param c colour (int)
        @param style the style number (int)
        """
        self.colours[style] = QColor(c)
        
    def defaultPaper(self, style):
        """
        Public method to get the default background for a style.
        
        @param style the style number (int)
        @return colour
        """
        return self.defaultPapers[style]
        
    def paper(self, style):
        """
        Public method to get the background for a style.
        
        @param style the style number (int)
        @return colour
        """
        return self.papers[style]
        
    def setPaper(self, c, style):
        """
        Public method to set the background for a style.
        
        @param c colour (int)
        @param style the style number (int)
        """
        self.papers[style] = QColor(c)
        
    def defaulEolFill(self, style):
        """
        Public method to get the default eolFill flag for a style.
        
        @param style the style number (int)
        @return eolFill flag
        """
        return self.defaultEolFills[style]
        
    def eolFill(self, style):
        """
        Public method to get the eolFill flag for a style.
        
        @param style the style number (int)
        @return eolFill flag
        """
        return self.eolFills[style]
        
    def setEolFill(self, eolfill, style):
        """
        Public method to set the eolFill flag for a style.
        
        @param eolfill eolFill flag (boolean)
        @param style the style number (int)
        """
        self.eolFills[style] = eolfill
        
    def defaultFont(self, style):
        """
        Public method to get the default font for a style.
        
        @param style the style number (int)
        @return font
        """
        return self.defaultFonts[style]
        
    def font(self, style):
        """
        Public method to get the font for a style.
        
        @param style the style number (int)
        @return font
        """
        return self.fonts[style]
        
    def setFont(self, f, style):
        """
        Public method to set the font for a style.
        
        @param f font
        @param style the style number (int)
        """
        self.fonts[style] = QFont(f)
        
    def language(self):
        """
        Public method to get the lexers programming language.
        
        @return language
        """
        return self.__language
        
    def description(self, style):
        """
        Public method to get a descriptive string for a style.
        
        @param style the style number (int)
        @return description of the style (string)
        """
        if style in self.descriptions:
            return self.descriptions[style]
        else:
            return ""
