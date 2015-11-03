# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for entering character classes.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, \
    QScrollArea, QPushButton, QSpacerItem, QSizePolicy, QComboBox, QLineEdit, \
    QLabel

from .Ui_QRegularExpressionWizardCharactersDialog import \
    Ui_QRegularExpressionWizardCharactersDialog


class QRegularExpressionWizardCharactersDialog(
        QDialog, Ui_QRegularExpressionWizardCharactersDialog):
    """
    Class implementing a dialog for entering character classes.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(QRegularExpressionWizardCharactersDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__initCharacterSelectors()
        
        self.comboItems = []
        self.singleComboItems = []      # these are in addition to the above
        self.comboItems.append((self.tr("Normal character"), "-c"))
        self.comboItems.append((self.tr(
            "Unicode character in hexadecimal notation"), "-h"))
        self.comboItems.append((self.tr(
            "ASCII/Latin1 character in octal notation"), "-o"))
        self.singleComboItems.extend([
            ("---", "-i"),
            (self.tr("Bell character (\\a)"), "\\a"),
            (self.tr("Escape character (\\e)"), "\\e"),
            (self.tr("Page break (\\f)"), "\\f"),
            (self.tr("Line feed (\\n)"), "\\n"),
            (self.tr("Carriage return (\\r)"), "\\r"),
            (self.tr("Horizontal tabulator (\\t)"), "\\t"),
            ("---", "-i"),
            (self.tr("Character Category"), "-ccp"),
            (self.tr("Special Character Category"), "-csp"),
            (self.tr("Character Block"), "-cbp"),
            (self.tr("POSIX Named Set"), "-psp"),
            (self.tr("Not Character Category"), "-ccn"),
            (self.tr("Not Character Block"), "-cbn"),
            (self.tr("Not Special Character Category"), "-csn"),
            (self.tr("Not POSIX Named Set"), "-psn"),
        ])
        
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
            # display name                                  code
            (self.tr("Letter, Any"), "L"),
            (self.tr("Letter, Lower case"), "Ll"),
            (self.tr("Letter, Modifier"), "Lm"),
            (self.tr("Letter, Other"), "Lo"),
            (self.tr("Letter, Title case"), "Lt"),
            (self.tr("Letter, Upper case"), "Lu"),
            (self.tr("Letter, Lower, Upper or Title"), "L&"),
            (self.tr("Mark, Any"), "M"),
            (self.tr("Mark, Spacing"), "Mc"),
            (self.tr("Mark, Enclosing"), "Me"),
            (self.tr("Mark, Non-spacing"), "Mn"),
            (self.tr("Number, Any"), "N"),
            (self.tr("Number, Decimal"), "Nd"),
            (self.tr("Number, Letter"), "Nl"),
            (self.tr("Number, Other"), "No"),
            (self.tr("Punctuation, Any"), "P"),
            (self.tr("Punctuation, Connector"), "Pc"),
            (self.tr("Punctuation, Dash"), "Pd"),
            (self.tr("Punctuation, Close"), "Pe"),
            (self.tr("Punctuation, Final"), "Pf"),
            (self.tr("Punctuation, Initial"), "Pi"),
            (self.tr("Punctuation, Other"), "Po"),
            (self.tr("Punctuation, Open"), "Ps"),
            (self.tr("Symbol, Any"), "S"),
            (self.tr("Symbol, Currency"), "Sc"),
            (self.tr("Symbol, Modifier"), "Sk"),
            (self.tr("Symbol, Mathematical"), "Sm"),
            (self.tr("Symbol, Other"), "So"),
            (self.tr("Separator, Any"), "Z"),
            (self.tr("Separator, Line"), "Zl"),
            (self.tr("Separator, Paragraph"), "Zp"),
            (self.tr("Separator, Space"), "Zs"),
            (self.tr("Other, Any"), "C"),
            (self.tr("Other, Control"), "Cc"),
            (self.tr("Other, Format"), "Cf"),
            (self.tr("Other, Unassigned"), "Cn"),
            (self.tr("Other, Private Use"), "Co"),
            (self.tr("Other, Surrogat"), "Cn"),
        )
        
        self.__specialCharacterCategories = (
            # display name                           code
            (self.tr("Alphanumeric"), "Xan"),
            (self.tr("POSIX Space"), "Xps"),
            (self.tr("Perl Space"), "Xsp"),
            (self.tr("Universal Character"), "Xuc"),
            (self.tr("Perl Word"), "Xan"),
        )
        
        self.__characterBlocks = (
            # display name                           code
            (self.tr("Arabic"), "Arabic"),
            (self.tr("Armenian"), "Armenian"),
            (self.tr("Avestan"), "Avestan"),
            (self.tr("Balinese"), "Balinese"),
            (self.tr("Bamum"), "Bamum"),
            (self.tr("Batak"), "Batak"),
            (self.tr("Bengali"), "Bengali"),
            (self.tr("Bopomofo"), "Bopomofo"),
            (self.tr("Brahmi"), "Brahmi"),
            (self.tr("Braille"), "Braille"),
            (self.tr("Buginese"), "Buginese"),
            (self.tr("Buhid"), "Buhid"),
            (self.tr("Canadian Aboriginal"), "Canadian_Aboriginal"),
            (self.tr("Carian"), "Carian"),
            (self.tr("Chakma"), "Chakma"),
            (self.tr("Cham"), "Cham"),
            (self.tr("Cherokee"), "Cherokee"),
            (self.tr("Common"), "Common"),
            (self.tr("Coptic"), "Coptic"),
            (self.tr("Cuneiform"), "Cuneiform"),
            (self.tr("Cypriot"), "Cypriot"),
            (self.tr("Cyrillic"), "Cyrillic"),
            (self.tr("Deseret"), "Deseret,"),
            (self.tr("Devanagari"), "Devanagari"),
            (self.tr("Egyptian Hieroglyphs"), "Egyptian_Hieroglyphs"),
            (self.tr("Ethiopic"), "Ethiopic"),
            (self.tr("Georgian"), "Georgian"),
            (self.tr("Glagolitic"), "Glagolitic"),
            (self.tr("Gothic"), "Gothic"),
            (self.tr("Greek"), "Greek"),
            (self.tr("Gujarati"), "Gujarati"),
            (self.tr("Gurmukhi"), "Gurmukhi"),
            (self.tr("Han"), "Han"),
            (self.tr("Hangul"), "Hangul"),
            (self.tr("Hanunoo"), "Hanunoo"),
            (self.tr("Hebrew"), "Hebrew"),
            (self.tr("Hiragana"), "Hiragana"),
            (self.tr("Imperial Aramaic"), "Imperial_Aramaic"),
            (self.tr("Inherited"), "Inherited"),
            (self.tr("Inscriptional Pahlavi"), "Inscriptional_Pahlavi"),
            (self.tr("Inscriptional Parthian"), "Inscriptional_Parthian"),
            (self.tr("Javanese"), "Javanese"),
            (self.tr("Kaithi"), "Kaithi"),
            (self.tr("Kannada"), "Kannada"),
            (self.tr("Katakana"), "Katakana"),
            (self.tr("Kayah Li"), "Kayah_Li"),
            (self.tr("Kharoshthi"), "Kharoshthi"),
            (self.tr("Khmer"), "Khmer"),
            (self.tr("Lao"), "Lao"),
            (self.tr("Latin"), "Latin"),
            (self.tr("Lepcha"), "Lepcha"),
            (self.tr("Limbu"), "Limbu"),
            (self.tr("Linear B"), "Linear_B"),
            (self.tr("Lisu"), "Lisu"),
            (self.tr("Lycian"), "Lycian"),
            (self.tr("Lydian"), "Lydian"),
            (self.tr("Malayalam"), "Malayalam"),
            (self.tr("Mandaic"), "Mandaic"),
            (self.tr("Meetei Mayek"), "Meetei_Mayek"),
            (self.tr("Meroitic Cursive"), "Meroitic_Cursive"),
            (self.tr("Meroitic Hieroglyphs"), "Meroitic_Hieroglyphs"),
            (self.tr("Miao"), "Miao"),
            (self.tr("Mongolian"), "Mongolian"),
            (self.tr("Myanmar"), "Myanmar"),
            (self.tr("New Tai Lue"), "New_Tai_Lue"),
            (self.tr("N'Ko"), "Nko"),
            (self.tr("Ogham"), "Ogham"),
            (self.tr("Old Italic"), "Old_Italic"),
            (self.tr("Old Persian"), "Old_Persian"),
            (self.tr("Old South Arabian"), "Old_South_Arabian"),
            (self.tr("Old Turkic"), "Old_Turkic,"),
            (self.tr("Ol Chiki"), "Ol_Chiki"),
            (self.tr("Oriya"), "Oriya"),
            (self.tr("Osmanya"), "Osmanya"),
            (self.tr("Phags-pa"), "Phags_Pa"),
            (self.tr("Phoenician"), "Phoenician"),
            (self.tr("Rejang"), "Rejang"),
            (self.tr("Runic"), "Runic"),
            (self.tr("Samaritan"), "Samaritan"),
            (self.tr("Saurashtra"), "Saurashtra"),
            (self.tr("Sharada"), "Sharada"),
            (self.tr("Shavian"), "Shavian"),
            (self.tr("Sinhala"), "Sinhala"),
            (self.tr("Sora Sompeng"), "Sora_Sompeng"),
            (self.tr("Sundanese"), "Sundanese"),
            (self.tr("Syloti Nagri"), "Syloti_Nagri"),
            (self.tr("Syriac"), "Syriac"),
            (self.tr("Tagalog"), "Tagalog"),
            (self.tr("Tagbanwa"), "Tagbanwa"),
            (self.tr("Tai Le"), "Tai_Le"),
            (self.tr("Tai Tham"), "Tai_Tham"),
            (self.tr("Tai Viet"), "Tai_Viet"),
            (self.tr("Takri"), "Takri"),
            (self.tr("Tamil"), "Tamil"),
            (self.tr("Telugu"), "Telugu"),
            (self.tr("Thaana"), "Thaana"),
            (self.tr("Thai"), "Thai"),
            (self.tr("Tibetan"), "Tibetan"),
            (self.tr("Tifinagh"), "Tifinagh"),
            (self.tr("Ugaritic"), "Ugaritic"),
            (self.tr("Vai"), "Vai"),
            (self.tr("Yi"), "Yi"),
        )
        
        self.__posixNamedSets = (
            # display name                                  code
            (self.tr("Alphanumeric"), "alnum"),
            (self.tr("Alphabetic"), "alpha"),
            (self.tr("ASCII"), "ascii"),
            (self.tr("Word Letter"), "word"),
            (self.tr("Lower Case Letter"), "lower"),
            (self.tr("Upper Case Letter"), "upper"),
            (self.tr("Decimal Digit"), "digit"),
            (self.tr("Hexadecimal Digit"), "xdigit"),
            (self.tr("Space or Tab"), "blank"),
            (self.tr("White Space"), "space"),
            (self.tr("Printing (excl. space)"), "graph"),
            (self.tr("Printing (incl. space)"), "print"),
            (self.tr("Printing (excl. alphanumeric)"), "punct"),
            (self.tr("Control Character"), "cntrl"),
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
    
    def __populateCharacterCombo(self, combo, format):
        """
        Private method to populate a character selection combo.
        
        @param combo combo box to be populated (QComboBox)
        @param format format identifier (one of "-ccp", "-ccn",
            "-cbp", "-cbn", "-csp", "-csn", "-psp", "-psn")
        """
        combo.clear()
        
        if format in ["-ccp", "-ccn"]:
            items = self.__characterCategories
        elif format in ["-csp", "-csn"]:
            items = self.__specialCharacterCategories
        elif format in ["-cbp", "-cbn"]:
            items = self.__characterBlocks
        elif format in ["-psp", "-psn"]:
            items = self.__posixNamedSets
        
        comboLen = 0
        for txt, code in items:
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
        elif format in ["-ccp", "-ccn", "-cbp", "-cbn", "-csp", "-csn",
                        "-psp", "-psn"]:
            lineedit.setEnabled(False)
            lineedit.hide()
            if combo is not None:
                combo.show()
            self.__populateCharacterCombo(combo, format)
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
        
        if format == "-h":
            while len(char) < 2:
                char = "0" + char
            if len(char) > 2:
                return "\\x{{{0}}}".format(char.lower())
            else:
                return "\\x{0}".format(char.lower())
        elif format == "-o":
            while len(char) < 3:
                char = "0" + char
            if len(char) > 3:
                char = char[:3]
            return "\\{0}".format(char)
        elif format in ["-ccp", "-cbp", "-csp"]:
            return "\\p{{{0}}}".format(char)
        elif format in ["-ccn", "-cbn", "-csn"]:
            return "\\P{{{0}}}".format(char)
        elif format == "-psp":
            return "[:{0}:]".format(char)
        elif format == "-psn":
            return "[:^{0}:]".format(char)
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
        if self.newlineCheckBox.isChecked():
            regexp += "\\R"
        if self.nonNewlineCheckBox.isChecked():
            regexp += "\\N"
        if self.whitespaceCheckBox.isChecked():
            regexp += "\\s"
        if self.nonWhitespaceCheckBox.isChecked():
            regexp += "\\S"
        if self.horizontalWhitespaceCheckBox.isChecked():
            regexp += "\\h"
        if self.nonHorizontalWhitespaceCheckBox.isChecked():
            regexp += "\\H"
        if self.verticalWhitespaceCheckBox.isChecked():
            regexp += "\\v"
        if self.nonVerticalWhitespaceCheckBox.isChecked():
            regexp += "\\V"
        
        # single characters
        for entrieslist in self.singlesEntries:
            format = entrieslist[0].itemData(entrieslist[0].currentIndex())
            if format in ["-ccp", "-ccn", "-cbp", "-cbn", "-csp", "-csn",
                          "-psp", "-psn"]:
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
