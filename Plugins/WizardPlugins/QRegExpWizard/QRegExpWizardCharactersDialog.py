# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for entering character classes.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QSizePolicy, QSpacerItem, QWidget, QHBoxLayout, \
    QLineEdit, QPushButton, QDialog, QScrollArea, QComboBox, QVBoxLayout, \
    QLabel

from .Ui_QRegExpWizardCharactersDialog import Ui_QRegExpWizardCharactersDialog


class QRegExpWizardCharactersDialog(QDialog, Ui_QRegExpWizardCharactersDialog):
    """
    Class implementing a dialog for entering character classes.
    """
    RegExpMode = 0
    WildcardMode = 1
    W3CMode = 2
    
    def __init__(self, mode=RegExpMode, parent=None):
        """
        Constructor
        
        @param mode mode of the dialog (one of RegExpMode, WildcardMode,
            W3CMode)
        @param parent parent widget (QWidget)
        """
        super(QRegExpWizardCharactersDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__mode = mode
        
        if mode == QRegExpWizardCharactersDialog.WildcardMode:
            self.predefinedBox.setEnabled(False)
            self.predefinedBox.hide()
        elif mode == QRegExpWizardCharactersDialog.RegExpMode:
            self.w3cInitialIdentifierCheckBox.hide()
            self.w3cNonInitialIdentifierCheckBox.hide()
            self.w3cNmtokenCheckBox.hide()
            self.w3cNonNmtokenCheckBox.hide()
        elif mode == QRegExpWizardCharactersDialog.W3CMode:
            self.__initCharacterSelectors()
        
        self.comboItems = []
        self.singleComboItems = []      # these are in addition to the above
        self.comboItems.append((self.tr("Normal character"), "-c"))
        if mode == QRegExpWizardCharactersDialog.RegExpMode:
            self.comboItems.append((self.tr(
                "Unicode character in hexadecimal notation"), "-h"))
            self.comboItems.append((self.tr(
                "ASCII/Latin1 character in octal notation"), "-o"))
            self.singleComboItems.append(("---", "-i"))
            self.singleComboItems.append(
                (self.tr("Bell character (\\a)"), "\\a"))
            self.singleComboItems.append(
                (self.tr("Page break (\\f)"), "\\f"))
            self.singleComboItems.append(
                (self.tr("Line feed (\\n)"), "\\n"))
            self.singleComboItems.append(
                (self.tr("Carriage return (\\r)"), "\\r"))
            self.singleComboItems.append(
                (self.tr("Horizontal tabulator (\\t)"), "\\t"))
            self.singleComboItems.append(
                (self.tr("Vertical tabulator (\\v)"), "\\v"))
        elif mode == QRegExpWizardCharactersDialog.W3CMode:
            self.comboItems.append((self.tr(
                "Unicode character in hexadecimal notation"), "-h"))
            self.comboItems.append((self.tr(
                "ASCII/Latin1 character in octal notation"), "-o"))
            self.singleComboItems.append(("---", "-i"))
            self.singleComboItems.append(
                (self.tr("Line feed (\\n)"), "\\n"))
            self.singleComboItems.append(
                (self.tr("Carriage return (\\r)"), "\\r"))
            self.singleComboItems.append(
                (self.tr("Horizontal tabulator (\\t)"), "\\t"))
            self.singleComboItems.append(("---", "-i"))
            self.singleComboItems.append(
                (self.tr("Character Category"), "-ccp"))
            self.singleComboItems.append(
                (self.tr("Character Block"), "-cbp"))
            self.singleComboItems.append(
                (self.tr("Not Character Category"), "-ccn"))
            self.singleComboItems.append(
                (self.tr("Not Character Block"), "-cbn"))
        
        self.charValidator = QRegExpValidator(QRegExp(".{0,1}"), self)
        self.hexValidator = QRegExpValidator(QRegExp("[0-9a-fA-F]{0,4}"), self)
        self.octValidator = QRegExpValidator(QRegExp("[0-3]?[0-7]{0,2}"), self)
        
        # generate dialog part for single characters
        self.singlesBoxLayout = QVBoxLayout(self.singlesBox)
        self.singlesBoxLayout.setObjectName("singlesBoxLayout")
        self.singlesBoxLayout.setSpacing(6)
        self.singlesBoxLayout.setContentsMargins(6, 6, 6, 6)
        self.singlesBox.setLayout(self.singlesBoxLayout)
        self.singlesView = QScrollArea(self.singlesBox)
        self.singlesView.setObjectName("singlesView")
        self.singlesBoxLayout.addWidget(self.singlesView)
        
        self.singlesItemsBox = QWidget(self)
        self.singlesView.setWidget(self.singlesItemsBox)
        self.singlesItemsBox.setObjectName("singlesItemsBox")
        self.singlesItemsBox.setMinimumWidth(1000)
        self.singlesItemsBoxLayout = QVBoxLayout(self.singlesItemsBox)
        self.singlesItemsBoxLayout.setContentsMargins(6, 6, 6, 6)
        self.singlesItemsBoxLayout.setSpacing(6)
        self.singlesItemsBox.setLayout(self.singlesItemsBoxLayout)
        self.singlesEntries = []
        self.__addSinglesLine()
        
        hlayout0 = QHBoxLayout()
        hlayout0.setContentsMargins(0, 0, 0, 0)
        hlayout0.setSpacing(6)
        hlayout0.setObjectName("hlayout0")
        self.moreSinglesButton = QPushButton(
            self.tr("Additional Entries"), self.singlesBox)
        self.moreSinglesButton.setObjectName("moreSinglesButton")
        hlayout0.addWidget(self.moreSinglesButton)
        hspacer0 = QSpacerItem(
            30, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        hlayout0.addItem(hspacer0)
        self.singlesBoxLayout.addLayout(hlayout0)
        self.moreSinglesButton.clicked.connect(self.__addSinglesLine)
        
        # generate dialog part for character ranges
        self.rangesBoxLayout = QVBoxLayout(self.rangesBox)
        self.rangesBoxLayout.setObjectName("rangesBoxLayout")
        self.rangesBoxLayout.setSpacing(6)
        self.rangesBoxLayout.setContentsMargins(6, 6, 6, 6)
        self.rangesBox.setLayout(self.rangesBoxLayout)
        self.rangesView = QScrollArea(self.rangesBox)
        self.rangesView.setObjectName("rangesView")
        self.rangesBoxLayout.addWidget(self.rangesView)
        
        self.rangesItemsBox = QWidget(self)
        self.rangesView.setWidget(self.rangesItemsBox)
        self.rangesItemsBox.setObjectName("rangesItemsBox")
        self.rangesItemsBox.setMinimumWidth(1000)
        self.rangesItemsBoxLayout = QVBoxLayout(self.rangesItemsBox)
        self.rangesItemsBoxLayout.setContentsMargins(6, 6, 6, 6)
        self.rangesItemsBoxLayout.setSpacing(6)
        self.rangesItemsBox.setLayout(self.rangesItemsBoxLayout)
        self.rangesEntries = []
        self.__addRangesLine()
        
        hlayout1 = QHBoxLayout()
        hlayout1.setContentsMargins(0, 0, 0, 0)
        hlayout1.setSpacing(6)
        hlayout1.setObjectName("hlayout1")
        self.moreRangesButton = QPushButton(
            self.tr("Additional Entries"), self.rangesBox)
        self.moreSinglesButton.setObjectName("moreRangesButton")
        hlayout1.addWidget(self.moreRangesButton)
        hspacer1 = QSpacerItem(
            30, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        hlayout1.addItem(hspacer1)
        self.rangesBoxLayout.addLayout(hlayout1)
        self.moreRangesButton.clicked.connect(self.__addRangesLine)
        
    def __initCharacterSelectors(self):
        """
        Private method to initialize the W3C character selector entries.
        """
        self.__characterCategories = (
            # display name                              code
            (self.tr("Letter, Any"), "L"),
            (self.tr("Letter, Uppercase"), "Lu"),
            (self.tr("Letter, Lowercase"), "Ll"),
            (self.tr("Letter, Titlecase"), "Lt"),
            (self.tr("Letter, Modifier"), "Lm"),
            (self.tr("Letter, Other"), "Lo"),
            (self.tr("Mark, Any"), "M"),
            (self.tr("Mark, Nonspacing"), "Mn"),
            (self.tr("Mark, Spacing Combining"), "Mc"),
            (self.tr("Mark, Enclosing"), "Me"),
            (self.tr("Number, Any"), "N"),
            (self.tr("Number, Decimal Digit"), "Nd"),
            (self.tr("Number, Letter"), "Nl"),
            (self.tr("Number, Other"), "No"),
            (self.tr("Punctuation, Any"), "P"),
            (self.tr("Punctuation, Connector"), "Pc"),
            (self.tr("Punctuation, Dash"), "Pd"),
            (self.tr("Punctuation, Open"), "Ps"),
            (self.tr("Punctuation, Close"), "Pe"),
            (self.tr("Punctuation, Initial Quote"), "Pi"),
            (self.tr("Punctuation, Final Quote"), "Pf"),
            (self.tr("Punctuation, Other"), "Po"),
            (self.tr("Symbol, Any"), "S"),
            (self.tr("Symbol, Math"), "Sm"),
            (self.tr("Symbol, Currency"), "Sc"),
            (self.tr("Symbol, Modifier"), "Sk"),
            (self.tr("Symbol, Other"), "So"),
            (self.tr("Separator, Any"), "Z"),
            (self.tr("Separator, Space"), "Zs"),
            (self.tr("Separator, Line"), "Zl"),
            (self.tr("Separator, Paragraph"), "Zp"),
            (self.tr("Other, Any"), "C"),
            (self.tr("Other, Control"), "Cc"),
            (self.tr("Other, Format"), "Cf"),
            (self.tr("Other, Private Use"), "Co"),
            (self.tr("Other, Not Assigned"), "Cn"),
        )
        
        self.__characterBlocks = (
            (self.tr("Basic Latin"),
             "IsBasicLatin"),
            (self.tr("Latin-1 Supplement"),
             "IsLatin-1Supplement"),
            (self.tr("Latin Extended-A"),
             "IsLatinExtended-A"),
            (self.tr("Latin Extended-B"),
             "IsLatinExtended-B"),
            (self.tr("IPA Extensions"),
             "IsIPAExtensions"),
            (self.tr("Spacing Modifier Letters"),
             "IsSpacingModifierLetters"),
            (self.tr("Combining Diacritical Marks"),
             "IsCombiningDiacriticalMarks"),
            (self.tr("Greek"),
             "IsGreek"),
            (self.tr("Cyrillic"),
             "IsCyrillic"),
            (self.tr("Armenian"),
             "IsArmenian"),
            (self.tr("Hebrew"),
             "IsHebrew"),
            (self.tr("Arabic"),
             "IsArabic"),
            (self.tr("Syriac"),
             "IsSyriac"),
            (self.tr("Thaana"),
             "IsThaana"),
            (self.tr("Devanagari"),
             "IsDevanagari"),
            (self.tr("Bengali"),
             "IsBengali"),
            (self.tr("Gurmukhi"),
             "IsBengali"),
            (self.tr("Gujarati"),
             "IsGujarati"),
            (self.tr("Oriya"),
             "IsOriya"),
            (self.tr("Tamil"),
             "IsTamil"),
            (self.tr("Telugu"),
             "IsTelugu"),
            (self.tr("Kannada"),
             "IsKannada"),
            (self.tr("Malayalam"),
             "IsMalayalam"),
            (self.tr("Sinhala"),
             "IsSinhala"),
            (self.tr("Thai"),
             "IsThai"),
            (self.tr("Lao"),
             "IsLao"),
            (self.tr("Tibetan"),
             "IsTibetan"),
            (self.tr("Myanmar"),
             "IsMyanmar"),
            (self.tr("Georgian"),
             "IsGeorgian"),
            (self.tr("Hangul Jamo"),
             "IsHangulJamo"),
            (self.tr("Ethiopic"),
             "IsEthiopic"),
            (self.tr("Cherokee"),
             "IsCherokee"),
            (self.tr("Unified Canadian Aboriginal Syllabics"),
             "IsUnifiedCanadianAboriginalSyllabics"),
            (self.tr("Ogham"),
             "IsOgham"),
            (self.tr("Runic"),
             "IsRunic"),
            (self.tr("Khmer"),
             "IsKhmer"),
            (self.tr("Mongolian"),
             "IsMongolian"),
            (self.tr("Latin Extended Additional"),
             "IsLatinExtendedAdditional"),
            (self.tr("Greek Extended"),
             "IsGreekExtended"),
            (self.tr("General Punctuation"),
             "IsGeneralPunctuation"),
            (self.tr("Superscripts and Subscripts"),
             "IsSuperscriptsandSubscripts"),
            (self.tr("Currency Symbols"),
             "IsCurrencySymbols"),
            (self.tr("Combining Marks for Symbols"),
             "IsCombiningMarksforSymbols"),
            (self.tr("Letterlike Symbols"),
             "IsLetterlikeSymbols"),
            (self.tr("Number Forms"),
             "IsNumberForms"),
            (self.tr("Arrows"),
             "IsArrows"),
            (self.tr("Mathematical Operators"),
             "IsMathematicalOperators"),
            (self.tr("Miscellaneous Technical"),
             "IsMiscellaneousTechnical"),
            (self.tr("Control Pictures"),
             "IsControlPictures"),
            (self.tr("Optical Character Recognition"),
             "IsOpticalCharacterRecognition"),
            (self.tr("Enclosed Alphanumerics"),
             "IsEnclosedAlphanumerics"),
            (self.tr("Box Drawing"),
             "IsBoxDrawing"),
            (self.tr("Block Elements"),
             "IsBlockElements"),
            (self.tr("Geometric Shapes"),
             "IsGeometricShapes"),
            (self.tr("Miscellaneous Symbols"),
             "IsMiscellaneousSymbols"),
            (self.tr("Dingbats"),
             "IsDingbats"),
            (self.tr("Braille Patterns"),
             "IsBraillePatterns"),
            (self.tr("CJK Radicals Supplement"),
             "IsCJKRadicalsSupplement"),
            (self.tr("KangXi Radicals"),
             "IsKangXiRadicals"),
            (self.tr("Ideographic Description Chars"),
             "IsIdeographicDescriptionChars"),
            (self.tr("CJK Symbols and Punctuation"),
             "IsCJKSymbolsandPunctuation"),
            (self.tr("Hiragana"),
             "IsHiragana"),
            (self.tr("Katakana"),
             "IsKatakana"),
            (self.tr("Bopomofo"),
             "IsBopomofo"),
            (self.tr("Hangul Compatibility Jamo"),
             "IsHangulCompatibilityJamo"),
            (self.tr("Kanbun"),
             "IsKanbun"),
            (self.tr("Bopomofo Extended"),
             "IsBopomofoExtended"),
            (self.tr("Enclosed CJK Letters and Months"),
             "IsEnclosedCJKLettersandMonths"),
            (self.tr("CJK Compatibility"),
             "IsCJKCompatibility"),
            (self.tr("CJK Unified Ideographs Extension A"),
             "IsCJKUnifiedIdeographsExtensionA"),
            (self.tr("CJK Unified Ideographs"),
             "IsCJKUnifiedIdeographs"),
            (self.tr("Yi Syllables"),
             "IsYiSyllables"),
            (self.tr("Yi Radicals"),
             "IsYiRadicals"),
            (self.tr("Hangul Syllables"),
             "IsHangulSyllables"),
            (self.tr("Private Use"),
             "IsPrivateUse"),
            (self.tr("CJK Compatibility Ideographs"),
             "IsCJKCompatibilityIdeographs"),
            (self.tr("Alphabetic Presentation Forms"),
             "IsAlphabeticPresentationForms"),
            (self.tr("Arabic Presentation Forms-A"),
             "IsArabicPresentationForms-A"),
            (self.tr("Combining Half Marks"),
             "IsCombiningHalfMarks"),
            (self.tr("CJK Compatibility Forms"),
             "IsCJKCompatibilityForms"),
            (self.tr("Small Form Variants"),
             "IsSmallFormVariants"),
            (self.tr("Arabic Presentation Forms-B"),
             "IsArabicPresentationForms-B"),
            (self.tr("Halfwidth and Fullwidth Forms"),
             "IsHalfwidthandFullwidthForms"),
            (self.tr("Specials"),
             "IsSpecials"),
            (self.tr("Old Italic"),
             "IsOldItalic"),
            (self.tr("Gothic"),
             "IsGothic"),
            (self.tr("Deseret"),
             "IsDeseret"),
            (self.tr("Byzantine Musical Symbols"),
             "IsByzantineMusicalSymbols"),
            (self.tr("Musical Symbols"),
             "IsMusicalSymbols"),
            (self.tr("Mathematical Alphanumeric Symbols"),
             "IsMathematicalAlphanumericSymbols"),
            (self.tr("CJK Unified Ideographic Extension B"),
             "IsCJKUnifiedIdeographicExtensionB"),
            (self.tr("CJK Compatapility Ideographic Supplement"),
             "IsCJKCompatapilityIdeographicSupplement"),
            (self.tr("Tags"),
             "IsTags"),
        )
        
    def __populateCharTypeCombo(self, combo, isSingle):
        """
        Private method to populate a given character type selection combo box.
        
        @param combo reference to the combo box to be populated (QComboBox)
        @param isSingle flag indicating a singles combo (boolean)
        """
        for txt, value in self.comboItems:
            combo.addItem(txt, value)
        if isSingle:
            for txt, value in self.singleComboItems:
                combo.addItem(txt, value)
        
    def __addSinglesLine(self):
        """
        Private slot to add a line of entry widgets for single characters.
        """
        hbox = QWidget(self.singlesItemsBox)
        hboxLayout = QHBoxLayout(hbox)
        hboxLayout.setContentsMargins(0, 0, 0, 0)
        hboxLayout.setSpacing(6)
        hbox.setLayout(hboxLayout)
        cb1 = QComboBox(hbox)
        cb1.setEditable(False)
        self.__populateCharTypeCombo(cb1, True)
        hboxLayout.addWidget(cb1)
        le1 = QLineEdit(hbox)
        le1.setValidator(self.charValidator)
        hboxLayout.addWidget(le1)
        cb1a = QComboBox(hbox)
        cb1a.setEditable(False)
        cb1a.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        hboxLayout.addWidget(cb1a)
        cb1a.hide()
        cb2 = QComboBox(hbox)
        cb2.setEditable(False)
        self.__populateCharTypeCombo(cb2, True)
        hboxLayout.addWidget(cb2)
        le2 = QLineEdit(hbox)
        le2.setValidator(self.charValidator)
        hboxLayout.addWidget(le2)
        cb2a = QComboBox(hbox)
        cb2a.setEditable(False)
        cb2a.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        hboxLayout.addWidget(cb2a)
        cb2a.hide()
        self.singlesItemsBoxLayout.addWidget(hbox)
        
        cb1.activated[int].connect(self.__singlesCharTypeSelected)
        cb2.activated[int].connect(self.__singlesCharTypeSelected)
        hbox.show()
        
        self.singlesItemsBox.adjustSize()
        
        self.singlesEntries.append([cb1, le1, cb1a])
        self.singlesEntries.append([cb2, le2, cb2a])
        
    def __addRangesLine(self):
        """
        Private slot to add a line of entry widgets for character ranges.
        """
        hbox = QWidget(self.rangesItemsBox)
        hboxLayout = QHBoxLayout(hbox)
        hboxLayout.setContentsMargins(0, 0, 0, 0)
        hboxLayout.setSpacing(6)
        hbox.setLayout(hboxLayout)
        cb1 = QComboBox(hbox)
        cb1.setEditable(False)
        self.__populateCharTypeCombo(cb1, False)
        hboxLayout.addWidget(cb1)
        l1 = QLabel(self.tr("Between:"), hbox)
        hboxLayout.addWidget(l1)
        le1 = QLineEdit(hbox)
        le1.setValidator(self.charValidator)
        hboxLayout.addWidget(le1)
        l2 = QLabel(self.tr("And:"), hbox)
        hboxLayout.addWidget(l2)
        le2 = QLineEdit(hbox)
        le2.setValidator(self.charValidator)
        hboxLayout.addWidget(le2)
        self.rangesItemsBoxLayout.addWidget(hbox)
        
        cb1.activated[int].connect(self.__rangesCharTypeSelected)
        hbox.show()
        
        self.rangesItemsBox.adjustSize()
        
        self.rangesEntries.append([cb1, le1, le2])
        
    def __populateW3cCharacterCombo(self, combo, format):
        """
        Private method to populate a W3C character selection combo.
        
        @param combo combo box to be populated (QComboBox)
        @param format format identifier (one of "-ccp", "-ccn", "-cbp", "-cbn")
        """
        combo.clear()
        
        if format in ["-ccp", "-ccn"]:
            comboLen = 0
            for txt, code in self.__characterCategories:
                combo.addItem(txt, code)
                comboLen = max(comboLen, len(txt))
            combo.setMinimumContentsLength(comboLen)
        elif format in ["-cbp", "-cbn"]:
            comboLen = 0
            for txt, code in self.__characterBlocks:
                combo.addItem(txt, code)
                comboLen = max(comboLen, len(txt))
            combo.setMinimumContentsLength(comboLen)
        
    def __performSelectedAction(self, format, lineedit, combo):
        """
        Private method performing some actions depending on the input.
        
        @param format format of the selected entry (string)
        @param lineedit line edit widget to act on (QLineEdit)
        @param combo combo box widget to act on (QComboBox)
        """
        if format == "-i":
            return
        
        if format in ["-c", "-h", "-o"]:
            lineedit.show()
            lineedit.setEnabled(True)
            if combo is not None:
                combo.hide()
            if format == "-c":
                lineedit.setValidator(self.charValidator)
            elif format == "-h":
                lineedit.setValidator(self.hexValidator)
            elif format == "-o":
                lineedit.setValidator(self.octValidator)
        elif format in ["-ccp", "-ccn", "-cbp", "-cbn"]:
            lineedit.setEnabled(False)
            lineedit.hide()
            if combo is not None:
                combo.show()
            self.__populateW3cCharacterCombo(combo, format)
        else:
            lineedit.setEnabled(False)
            lineedit.hide()
            if combo is not None:
                combo.hide()
        lineedit.clear()
        
    def __singlesCharTypeSelected(self, index):
        """
        Private slot to handle the activated(int) signal of the single chars
        combo boxes.
        
        @param index selected list index (integer)
        """
        combo = self.sender()
        for entriesList in self.singlesEntries:
            if combo == entriesList[0]:
                format = combo.itemData(index)
                self.__performSelectedAction(
                    format, entriesList[1], entriesList[2])
                break
        
    def __rangesCharTypeSelected(self, index):
        """
        Private slot to handle the activated(int) signal of the char ranges
        combo boxes.
        
        @param index selected list index (integer)
        """
        combo = self.sender()
        for entriesList in self.rangesEntries:
            if combo == entriesList[0]:
                format = combo.itemData(index)
                self.__performSelectedAction(format, entriesList[1], None)
                self.__performSelectedAction(format, entriesList[2], None)
                break
        
    def __formatCharacter(self, char, format):
        """
        Private method to format the characters entered into the dialog.
        
        @param char character string entered into the dialog (string)
        @param format string giving a special format (-c, -h, -i or -o) or
            the already formatted character (string)
        @return formatted character string (string)
        """
        if format == "-c":
            return char
        elif format == "-i":
            return ""
        
        if self.__mode in [QRegExpWizardCharactersDialog.RegExpMode,
                           QRegExpWizardCharactersDialog.W3CMode]:
            if format == "-h":
                return "\\x{0}".format(char.lower())
            elif format == "-o":
                return "\\0{0}".format(char)
            elif format in ["-ccp", "-cbp"]:
                return "\\p{{{0}}}".format(char)
            elif format in ["-ccn", "-cbn"]:
                return "\\P{{{0}}}".format(char)
            else:
                return format
        
    def getCharacters(self):
        """
        Public method to return the character string assembled via the dialog.
        
        @return formatted string for character classes (string)
        """
        regexp = ""
        
        # negative character range
        if self.negativeCheckBox.isChecked():
            regexp += "^"
            
        # predefined character ranges
        if self.wordCharCheckBox.isChecked():
            regexp += "\\w"
        if self.nonWordCharCheckBox.isChecked():
            regexp += "\\W"
        if self.digitsCheckBox.isChecked():
            regexp += "\\d"
        if self.nonDigitsCheckBox.isChecked():
            regexp += "\\D"
        if self.whitespaceCheckBox.isChecked():
            regexp += "\\s"
        if self.nonWhitespaceCheckBox.isChecked():
            regexp += "\\S"
        if self.w3cInitialIdentifierCheckBox.isChecked():
            regexp += "\\i"
        if self.w3cNonInitialIdentifierCheckBox.isChecked():
            regexp += "\\I"
        if self.w3cNmtokenCheckBox.isChecked():
            regexp += "\\c"
        if self.w3cNonNmtokenCheckBox.isChecked():
            regexp += "\\C"
            
        # single characters
        for entrieslist in self.singlesEntries:
            format = entrieslist[0].itemData(entrieslist[0].currentIndex())
            if format in ["-ccp", "-ccn", "-cbp", "-cbn"]:
                char = entrieslist[2].itemData(entrieslist[2].currentIndex())
            else:
                char = entrieslist[1].text()
            regexp += self.__formatCharacter(char, format)
        
        # character ranges
        for entrieslist in self.rangesEntries:
            if not entrieslist[1].text() or \
               not entrieslist[2].text():
                continue
            format = entrieslist[0].itemData(entrieslist[0].currentIndex())
            char1 = entrieslist[1].text()
            char2 = entrieslist[2].text()
            regexp += "{0}-{1}".format(
                self.__formatCharacter(char1, format),
                self.__formatCharacter(char2, format))
        
        if regexp:
            if (regexp.startswith("\\") and
                regexp.count("\\") == 1 and
                "-" not in regexp) or \
               len(regexp) == 1:
                return regexp
            else:
                return "[{0}]".format(regexp)
        else:
            return ""
