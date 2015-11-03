# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the spell checker for the editor component.

The spell checker is based on pyenchant.
"""

from __future__ import unicode_literals

import os
import sys

from PyQt5.QtCore import QTimer, QObject

import Preferences
import Utilities

try:
    import enchant
except (ImportError, AttributeError, OSError):
    pass


class SpellChecker(QObject):
    """
    Class implementing a pyenchant based spell checker.
    """
    # class attributes to be used as defaults
    _spelling_lang = None
    _spelling_dict = None
    
    def __init__(self, editor, indicator, defaultLanguage=None,
                 checkRegion=None):
        """
        Constructor
        
        @param editor reference to the editor object (QScintilla.Editor)
        @param indicator spell checking indicator
        @keyparam defaultLanguage the language to be used as the default
            (string). The string should be in language locale format
            (e.g. en_US, de).
        @keyparam checkRegion reference to a function to check for a valid
            region
        """
        super(SpellChecker, self).__init__(editor)
        
        self.editor = editor
        self.indicator = indicator
        if defaultLanguage is not None:
            self.setDefaultLanguage(defaultLanguage)
        if checkRegion is not None:
            self.__checkRegion = checkRegion
        else:
            self.__checkRegion = lambda r: True
        self.minimumWordSize = 3
        self.lastCheckedLine = -1
        
        self.__ignoreWords = []
        self.__replaceWords = {}
    
    @classmethod
    def getAvailableLanguages(cls):
        """
        Class method to get all available languages.
        
        @return list of available languages (list of strings)
        """
        try:
            return enchant.list_languages()
        except NameError:
            pass
        return []
    
    @classmethod
    def isAvailable(cls):
        """
        Class method to check, if spellchecking is available.
        
        @return flag indicating availability (boolean)
        """
        if Preferences.getEditor("SpellCheckingEnabled"):
            try:
                return len(enchant.list_languages()) > 0
            except (NameError, AttributeError):
                pass
        return False
    
    @classmethod
    def getDefaultPath(cls, isException=False):
        """
        Class method to get the default path names of the user dictionaries.
        
        @param isException flag indicating to return the name of the default
            exception dictionary (boolean)
        @return file name of the default user dictionary or the default user
            exception dictionary (string)
        """
        if isException:
            return os.path.join(
                Utilities.getConfigDir(), "spelling", "pel.dic")
        else:
            return os.path.join(
                Utilities.getConfigDir(), "spelling", "pwl.dic")
    
    @classmethod
    def getUserDictionaryPath(cls, isException=False):
        """
        Class method to get the path name of a user dictionary file.
        
        @param isException flag indicating to return the name of the user
            exception dictionary (boolean)
        @return file name of the user dictionary or the user exception
            dictionary (string)
        """
        if isException:
            dicFile = Preferences.getEditor("SpellCheckingPersonalExcludeList")
            if not dicFile:
                dicFile = SpellChecker.getDefaultPath(False)
        else:
            dicFile = Preferences.getEditor("SpellCheckingPersonalWordList")
            if not dicFile:
                dicFile = SpellChecker.getDefaultPath()
        return dicFile
    
    @classmethod
    def _getDict(cls, lang, pwl="", pel=""):
        """
        Protected classmethod to get a new dictionary.
        
        @param lang the language to be used as the default (string).
            The string should be in language locale format (e.g. en_US, de).
        @keyparam pwl name of the personal/project word list (string)
        @keyparam pel name of the personal/project exclude list (string)
        @return reference to the dictionary (enchant.Dict)
        """
        if not pwl:
            pwl = SpellChecker.getUserDictionaryPath()
            d = os.path.dirname(pwl)
            if not os.path.exists(d):
                os.makedirs(d)
        
        if not pel:
            pel = SpellChecker.getUserDictionaryPath(False)
            d = os.path.dirname(pel)
            if not os.path.exists(d):
                os.makedirs(d)
        
        try:
            d = enchant.DictWithPWL(lang, pwl, pel)
        except:
            # Catch all exceptions, because if pyenchant isn't available, you
            # can't catch the enchant.DictNotFound error.
            d = None
        return d
    
    @classmethod
    def setDefaultLanguage(cls, language):
        """
        Class method to set the default language.
        
        @param language the language to be used as the default (string).
            The string should be in language locale format (e.g. en_US, de).
        """
        cls._spelling_lang = language
        cls._spelling_dict = cls._getDict(language)
    
    def setLanguage(self, language, pwl="", pel=""):
        """
        Public method to set the current language.
        
        @param language the language to be used as the default (string).
            The string should be in language locale format (e.g. en_US, de).
        @keyparam pwl name of the personal/project word list (string)
        @keyparam pel name of the personal/project exclude list (string)
        """
        self._spelling_lang = language
        self._spelling_dict = self._getDict(language, pwl=pwl,
                                            pel=pel)
    
    def getLanguage(self):
        """
        Public method to get the current language.
        
        @return current language in language locale format (string)
        """
        return self._spelling_lang
    
    def setMinimumWordSize(self, size):
        """
        Public method to set the minimum word size.
        
        @param size minimum word size (integer)
        """
        self.minimumWordSize = size
    
    def __getNextWord(self, pos, endPosition):
        """
        Private method to get the next word in the text after the given
        position.
        
        @param pos position to start word extraction (integer)
        @param endPosition position to stop word extraction (integer)
        @return tuple of three values (the extracted word (string),
            start position (integer), end position (integer))
        """
        if pos < 0 or pos >= endPosition:
            return "", -1, -1
        
        ch = self.editor.charAt(pos)
        # 1. skip non-word characters
        while pos < endPosition and not ch.isalnum():
            pos = self.editor.positionAfter(pos)
            ch = self.editor.charAt(pos)
        if pos == endPosition:
            return "", -1, -1
        startPos = pos
        
        # 2. extract the word
        word = ""
        while pos < endPosition and ch.isalnum():
            word += ch
            pos = self.editor.positionAfter(pos)
            ch = self.editor.charAt(pos)
        endPos = pos
        if word.isdigit():
            return self.__getNextWord(endPos, endPosition)
        else:
            return word, startPos, endPos
    
    def getContext(self, wordStart, wordEnd):
        """
        Public method to get the context of a faulty word.
        
        @param wordStart the starting position of the word (integer)
        @param wordEnd the ending position of the word (integer)
        @return tuple of the leading and trailing context (string, string)
        """
        sline, sindex = self.editor.lineIndexFromPosition(wordStart)
        eline, eindex = self.editor.lineIndexFromPosition(wordEnd)
        text = self.editor.text(sline)
        return (text[:sindex], text[eindex:])
    
    def getError(self):
        """
        Public method to get information about the last error found.
        
        @return tuple of last faulty word (string), starting position of the
            faulty word (integer) and ending position of the faulty word
            (integer)
        """
        return (self.word, self.wordStart, self.wordEnd)
    
    def initCheck(self, startPos, endPos):
        """
        Public method to initialize a spell check.
        
        @param startPos position to start at (integer)
        @param endPos position to end at (integer)
        @return flag indicating successful initialization (boolean)
        """
        if startPos == endPos:
            return False
        
        spell = self._spelling_dict
        if spell is None:
            return False
        
        self.editor.clearIndicatorRange(
            self.indicator, startPos, endPos - startPos)
        
        self.pos = startPos
        self.endPos = endPos
        self.word = ""
        self.wordStart = -1
        self.wordEnd = -1
        return True
    
    def __checkDocumentPart(self, startPos, endPos):
        """
        Private method to check some part of the document.
        
        @param startPos position to start at (integer)
        @param endPos position to end at (integer)
        """
        if not self.initCheck(startPos, endPos):
            return
        
        while True:
            try:
                next(self)
                self.editor.setIndicatorRange(self.indicator, self.wordStart,
                                              self.wordEnd - self.wordStart)
            except StopIteration:
                break
    
    def __incrementalCheck(self):
        """
        Private method to check the document incrementally.
        """
        if self.lastCheckedLine < 0:
            return
        
        linesChunk = Preferences.getEditor("AutoSpellCheckChunkSize")
        self.checkLines(self.lastCheckedLine,
                        self.lastCheckedLine + linesChunk)
        self.lastCheckedLine = self.lastCheckedLine + linesChunk + 1
        if self.lastCheckedLine >= self.editor.lines():
            self.lastCheckedLine = -1
        else:
            QTimer.singleShot(0, self.__incrementalCheck)
    
    def checkWord(self, pos, atEnd=False):
        """
        Public method to check the word at position pos.
        
        @param pos position to check at (integer)
        @keyparam atEnd flag indicating the position is at the end of the word
            to check (boolean)
        """
        spell = self._spelling_dict
        if spell is None:
            return
        
        if atEnd:
            pos = self.editor.positionBefore(pos)
        
        if pos >= 0 and self.__checkRegion(pos):
            pos0 = pos
            pos1 = -1
            if not self.editor.charAt(pos).isalnum():
                line, index = self.editor.lineIndexFromPosition(pos)
                self.editor.clearIndicator(
                    self.indicator, line, index, line, index + 1)
                pos1 = self.editor.positionAfter(pos)
                pos0 = self.editor.positionBefore(pos)
            
            for pos in [pos0, pos1]:
                if self.editor.charAt(pos).isalnum():
                    line, index = self.editor.lineIndexFromPosition(pos)
                    word = self.editor.getWord(line, index, useWordChars=False)
                    if len(word) >= self.minimumWordSize:
                        try:
                            ok = spell.check(word)
                        except enchant.errors.Error:
                            ok = True
                    else:
                        ok = True
                    start, end = self.editor.getWordBoundaries(
                        line, index, useWordChars=False)
                    if ok:
                        self.editor.clearIndicator(
                            self.indicator, line, start, line, end)
                    else:
                        # spell check indicated an error
                        self.editor.setIndicator(
                            self.indicator, line, start, line, end)
    
    def checkLines(self, firstLine, lastLine):
        """
        Public method to check some lines of text.
        
        @param firstLine line number of first line to check (integer)
        @param lastLine line number of last line to check (integer)
        """
        startPos = self.editor.positionFromLineIndex(firstLine, 0)
        
        if lastLine >= self.editor.lines():
            lastLine = self.editor.lines() - 1
        endPos = self.editor.lineEndPosition(lastLine)
        
        self.__checkDocumentPart(startPos, endPos)
    
    def checkDocument(self):
        """
        Public method to check the complete document.
        """
        self.__checkDocumentPart(0, self.editor.length())
    
    def checkDocumentIncrementally(self):
        """
        Public method to check the document incrementally.
        """
        spell = self._spelling_dict
        if spell is None:
            return
        
        if Preferences.getEditor("AutoSpellCheckingEnabled"):
            self.lastCheckedLine = 0
            QTimer.singleShot(0, self.__incrementalCheck)
    
    def stopIncrementalCheck(self):
        """
        Public method to stop an incremental check.
        """
        self.lastCheckedLine = -1
    
    def checkSelection(self):
        """
        Public method to check the current selection.
        """
        selStartLine, selStartIndex, selEndLine, selEndIndex = \
            self.editor.getSelection()
        self.__checkDocumentPart(
            self.editor.positionFromLineIndex(selStartLine, selStartIndex),
            self.editor.positionFromLineIndex(selEndLine, selEndIndex)
        )
    
    def checkCurrentPage(self):
        """
        Public method to check the currently visible page.
        """
        startLine = self.editor.firstVisibleLine()
        endLine = startLine + self.editor.linesOnScreen()
        self.checkLines(startLine, endLine)
    
    def clearAll(self):
        """
        Public method to clear all spelling markers.
        """
        self.editor.clearIndicatorRange(
            self.indicator, 0, self.editor.length())
    
    def getSuggestions(self, word):
        """
        Public method to get suggestions for the given word.
        
        @param word word to get suggestions for (string)
        @return list of suggestions (list of strings)
        """
        suggestions = []
        spell = self._spelling_dict
        if spell and len(word) >= self.minimumWordSize:
            try:
                suggestions = spell.suggest(word)
            except enchant.errors.Error:
                # ignore these
                pass
        return suggestions
    
    def add(self, word=None):
        """
        Public method to add a word to the personal word list.
        
        @param word word to add (string)
        """
        spell = self._spelling_dict
        if spell:
            if word is None:
                word = self.word
            spell.add(word)
    
    def remove(self, word):
        """
        Public method to add a word to the personal exclude list.
        
        @param word word to add (string)
        """
        spell = self._spelling_dict
        if spell:
            spell.remove(word)
    
    def ignoreAlways(self, word=None):
        """
        Public method to tell the checker, to always ignore the given word
        or the current word.
        
        @param word word to be ignored (string)
        """
        if word is None:
            word = self.word
        if word not in self.__ignoreWords:
            self.__ignoreWords.append(word)
    
    def replace(self, replacement):
        """
        Public method to tell the checker to replace the current word with
        the replacement string.
        
        @param replacement replacement string (string)
        """
        sline, sindex = self.editor.lineIndexFromPosition(self.wordStart)
        eline, eindex = self.editor.lineIndexFromPosition(self.wordEnd)
        self.editor.setSelection(sline, sindex, eline, eindex)
        self.editor.beginUndoAction()
        self.editor.removeSelectedText()
        self.editor.insert(replacement)
        self.editor.endUndoAction()
        self.pos += len(replacement) - len(self.word)
    
    def replaceAlways(self, replacement):
        """
        Public method to tell the checker to always replace the current word
        with the replacement string.
        
        @param replacement replacement string (string)
        """
        self.__replaceWords[self.word] = replacement
        self.replace(replacement)
    
    ##################################################################
    ## Methods below implement the iterator protocol
    ##################################################################
    
    def __iter__(self):
        """
        Special method to create an iterator.
        
        @return self
        """
        return self
    
    def __next__(self):
        """
        Special method to advance to the next error.
        
        @return self
        @exception StopIteration raised to indicate the end of the iteration
        """
        spell = self._spelling_dict
        if spell:
            while self.pos < self.endPos and self.pos >= 0:
                word, wordStart, wordEnd = \
                    self.__getNextWord(self.pos, self.endPos)
                self.pos = wordEnd
                if (wordEnd - wordStart) >= self.minimumWordSize and \
                   self.__checkRegion(wordStart):
                    try:
                        if spell.check(word):
                            continue
                    except enchant.errors.Error:
                        # ignore these
                        pass
                    if word in self.__ignoreWords:
                        continue
                    self.word = word
                    self.wordStart = wordStart
                    self.wordEnd = wordEnd
                    if word in self.__replaceWords:
                        self.replace(self.__replaceWords[word])
                        continue
                    return self
        
        raise StopIteration
    
    if sys.version_info.major == 2:
        def next(self):
            """
            Public method to advance to the next error.
            
            @return self
            """
            return self.__next__()
