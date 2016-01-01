# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a widget to select a symbol in various formats.
"""

from __future__ import unicode_literals

import sys
import unicodedata
try:
    # Py3
    import html.entities as html_entities
except (ImportError):
    # Py2
    str = unicode                               # __IGNORE_WARNING__
    chr = unichr                                # __IGNORE_WARNING__
    import htmlentitydefs as html_entities      # __IGNORE_WARNING__

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QAbstractTableModel, \
    QModelIndex, Qt, qVersion, QItemSelectionModel, QLocale
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QHeaderView, QAbstractItemView

from .Ui_SymbolsWidget import Ui_SymbolsWidget

import UI.PixmapCache
import Preferences


class SymbolsModel(QAbstractTableModel):
    """
    Class implementing the model for the symbols widget.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(SymbolsModel, self).__init__(parent)
        
        self.__locale = QLocale()
        
        self.__headerData = [
            self.tr("Code"),
            self.tr("Char"),
            self.tr("Hex"),
            self.tr("HTML"),
            self.tr("Name"),
        ]
        
        self.__tables = [
            # first   last     display name
            (0x0, 0x1f, self.tr("Control Characters")),
            (0x20, 0x7f, self.tr("Basic Latin")),
            (0x80, 0xff, self.tr("Latin-1 Supplement")),
            (0x100, 0x17f, self.tr("Latin Extended-A")),
            (0x180, 0x24f, self.tr("Latin Extended-B")),
            (0x250, 0x2af, self.tr("IPA Extensions")),
            (0x2b0, 0x2ff, self.tr("Spacing Modifier Letters")),
            (0x300, 0x36f, self.tr("Combining Diacritical Marks")),
            (0x370, 0x3ff, self.tr("Greek and Coptic")),
            (0x400, 0x4ff, self.tr("Cyrillic")),
            (0x500, 0x52f, self.tr("Cyrillic Supplement")),
            (0x530, 0x58f, self.tr("Armenian")),
            (0x590, 0x5ff, self.tr("Hebrew")),
            (0x600, 0x6ff, self.tr("Arabic")),
            (0x700, 0x74f, self.tr("Syriac")),
            (0x780, 0x7bf, self.tr("Thaana")),
            (0x7c0, 0x7ff, self.tr("N'Ko")),
            (0x800, 0x83f, self.tr("Samaritan")),
            (0x840, 0x85f, self.tr("Mandaic")),
            (0x8a0, 0x8ff, self.tr("Arabic Extended-A")),
            (0x900, 0x97f, self.tr("Devanagari")),
            (0x980, 0x9ff, self.tr("Bengali")),
            (0xa00, 0xa7f, self.tr("Gurmukhi")),
            (0xa80, 0xaff, self.tr("Gujarati")),
            (0xb00, 0xb7f, self.tr("Oriya")),
            (0xb80, 0xbff, self.tr("Tamil")),
            (0xc00, 0xc7f, self.tr("Telugu")),
            (0xc80, 0xcff, self.tr("Kannada")),
            (0xd00, 0xd7f, self.tr("Malayalam")),
            (0xd80, 0xdff, self.tr("Sinhala")),
            (0xe00, 0xe7f, self.tr("Thai")),
            (0xe80, 0xeff, self.tr("Lao")),
            (0xf00, 0xfff, self.tr("Tibetan")),
            (0x1000, 0x109f, self.tr("Myanmar")),
            (0x10a0, 0x10ff, self.tr("Georgian")),
            (0x1100, 0x11ff, self.tr("Hangul Jamo")),
            (0x1200, 0x137f, self.tr("Ethiopic")),
            (0x1380, 0x139f, self.tr("Ethiopic Supplement")),
            (0x13a0, 0x13ff, self.tr("Cherokee")),
            (0x1400, 0x167f,
             self.tr("Unified Canadian Aboriginal Syllabics")),
            (0x1680, 0x169f, self.tr("Ogham")),
            (0x16a0, 0x16ff, self.tr("Runic")),
            (0x1700, 0x171f, self.tr("Tagalog")),
            (0x1720, 0x173f, self.tr("Hanunoo")),
            (0x1740, 0x175f, self.tr("Buhid")),
            (0x1760, 0x177f, self.tr("Tagbanwa")),
            (0x1780, 0x17ff, self.tr("Khmer")),
            (0x1800, 0x18af, self.tr("Mongolian")),
            (0x18b0, 0x18ff,
             self.tr("Unified Canadian Aboriginal Syllabics Extended")),
            (0x1900, 0x194f, self.tr("Limbu")),
            (0x1950, 0x197f, self.tr("Tai Le")),
            (0x19e0, 0x19ff, self.tr("Khmer Symbols")),
            (0x1a00, 0x1a1f, self.tr("Buginese")),
            (0x1a20, 0x1aaf, self.tr("Tai Tham")),
            (0x1b00, 0x1b7f, self.tr("Balinese")),
            (0x1b80, 0x1bbf, self.tr("Sundanese")),
            (0x1bc0, 0x1bff, self.tr("Batak")),
            (0x1c00, 0x1c4f, self.tr("Lepcha")),
            (0x1c50, 0x1c7f, self.tr("Ol Chiki")),
            (0x1cc0, 0x1ccf, self.tr("Sundanese Supplement")),
            (0x1cd0, 0x1cff, self.tr("Vedic Extensions")),
            (0x1d00, 0x1d7f, self.tr("Phonetic Extensions")),
            (0x1d80, 0x1dbf, self.tr("Phonetic Extensions Supplement")),
            (0x1dc0, 0x1dff,
             self.tr("Combining Diacritical Marks Supplement")),
            (0x1e00, 0x1eff, self.tr("Latin Extended Additional")),
            (0x1f00, 0x1fff, self.tr("Greek Extended")),
            (0x2000, 0x206f, self.tr("General Punctuation")),
            (0x2070, 0x209f, self.tr("Superscripts and Subscripts")),
            (0x20a0, 0x20cf, self.tr("Currency Symbols")),
            (0x20d0, 0x20ff, self.tr("Combining Diacritical Marks")),
            (0x2100, 0x214f, self.tr("Letterlike Symbols")),
            (0x2150, 0x218f, self.tr("Number Forms")),
            (0x2190, 0x21ff, self.tr("Arcolumns")),
            (0x2200, 0x22ff, self.tr("Mathematical Operators")),
            (0x2300, 0x23ff, self.tr("Miscellaneous Technical")),
            (0x2400, 0x243f, self.tr("Control Pictures")),
            (0x2440, 0x245f, self.tr("Optical Character Recognition")),
            (0x2460, 0x24ff, self.tr("Enclosed Alphanumerics")),
            (0x2500, 0x257f, self.tr("Box Drawing")),
            (0x2580, 0x259f, self.tr("Block Elements")),
            (0x25A0, 0x25ff, self.tr("Geometric Shapes")),
            (0x2600, 0x26ff, self.tr("Miscellaneous Symbols")),
            (0x2700, 0x27bf, self.tr("Dingbats")),
            (0x27c0, 0x27ef,
             self.tr("Miscellaneous Mathematical Symbols-A")),
            (0x27f0, 0x27ff, self.tr("Supplement Arcolumns-A")),
            (0x2800, 0x28ff, self.tr("Braille Patterns")),
            (0x2900, 0x297f, self.tr("Supplement Arcolumns-B")),
            (0x2980, 0x29ff,
             self.tr("Miscellaneous Mathematical Symbols-B")),
            (0x2a00, 0x2aff,
             self.tr("Supplemental Mathematical Operators")),
            (0x2b00, 0x2bff,
             self.tr("Miscellaneous Symbols and Arcolumns")),
            (0x2c00, 0x2c5f, self.tr("Glagolitic")),
            (0x2c60, 0x2c7f, self.tr("Latin Extended-C")),
            (0x2c80, 0x2cff, self.tr("Coptic")),
            (0x2d00, 0x2d2f, self.tr("Georgian Supplement")),
            (0x2d30, 0x2d7f, self.tr("Tifinagh")),
            (0x2d80, 0x2ddf, self.tr("Ethiopic Extended")),
            (0x2de0, 0x2dff, self.tr("Cyrillic Extended-A")),
            (0x2e00, 0x2e7f, self.tr("Supplemental Punctuation")),
            (0x2e80, 0x2eff, self.tr("CJK Radicals Supplement")),
            (0x2f00, 0x2fdf, self.tr("KangXi Radicals")),
            (0x2ff0, 0x2fff, self.tr("Ideographic Description Chars")),
            (0x3000, 0x303f, self.tr("CJK Symbols and Punctuation")),
            (0x3040, 0x309f, self.tr("Hiragana")),
            (0x30a0, 0x30ff, self.tr("Katakana")),
            (0x3100, 0x312f, self.tr("Bopomofo")),
            (0x3130, 0x318f, self.tr("Hangul Compatibility Jamo")),
            (0x3190, 0x319f, self.tr("Kanbun")),
            (0x31a0, 0x31bf, self.tr("Bopomofo Extended")),
            (0x31c0, 0x31ef, self.tr("CJK Strokes")),
            (0x31f0, 0x31ff, self.tr("Katakana Phonetic Extensions")),
            (0x3200, 0x32ff, self.tr("Enclosed CJK Letters and Months")),
            (0x3300, 0x33ff, self.tr("CJK Compatibility")),
            (0x3400, 0x4dbf, self.tr("CJK Unified Ideogr. Ext. A")),
            (0x4dc0, 0x4dff, self.tr("Yijing Hexagram Symbols")),
            (0x4e00, 0x9fff, self.tr("CJK Unified Ideographs")),
            (0xa000, 0xa48f, self.tr("Yi Syllables")),
            (0xa490, 0xa4cf, self.tr("Yi Radicals")),
            (0xa4d0, 0xa4ff, self.tr("Lisu")),
            (0xa500, 0xa63f, self.tr("Vai")),
            (0xa640, 0xa69f, self.tr("Cyrillic Extended-B")),
            (0xa6a0, 0xa6ff, self.tr("Bamum")),
            (0xa700, 0xa71f, self.tr("Modifier Tone Letters")),
            (0xa720, 0xa7ff, self.tr("Latin Extended-D")),
            (0xa800, 0xa82f, self.tr("Syloti Nagri")),
            (0xa830, 0xa83f, self.tr("Common Indic Number Forms")),
            (0xa840, 0xa87f, self.tr("Phags-pa")),
            (0xa880, 0xa8df, self.tr("Saurashtra")),
            (0xa8e0, 0xa8ff, self.tr("Devanagari Extended")),
            (0xa900, 0xa92f, self.tr("Kayah Li")),
            (0xa930, 0xa95f, self.tr("Rejang")),
            (0xa960, 0xa97f, self.tr("Hangul Jamo Extended-A")),
            (0xa980, 0xa9df, self.tr("Javanese")),
            (0xaa00, 0xaa5f, self.tr("Cham")),
            (0xaa60, 0xaa7f, self.tr("Myanmar Extended-A")),
            (0xaa80, 0xaadf, self.tr("Tai Viet")),
            (0xaae0, 0xaaff, self.tr("Meetei Mayek Extensions")),
            (0xab00, 0xab2f, self.tr("Ethiopic Extended-A")),
            (0xabc0, 0xabff, self.tr("Meetei Mayek")),
            (0xac00, 0xd7af, self.tr("Hangul Syllables")),
            (0xd7b0, 0xd7ff, self.tr("Hangul Jamo Extended-B")),
            (0xd800, 0xdb7f, self.tr("High Surrogates")),
            (0xdb80, 0xdbff, self.tr("High Private Use Surrogates")),
            (0xdc00, 0xdfff, self.tr("Low Surrogates")),
            (0xe000, 0xf8ff, self.tr("Private Use")),
            (0xf900, 0xfaff, self.tr("CJK Compatibility Ideographs")),
            (0xfb00, 0xfb4f, self.tr("Alphabetic Presentation Forms")),
            (0xfb50, 0xfdff, self.tr("Arabic Presentation Forms-A")),
            (0xfe00, 0xfe0f, self.tr("Variation Selectors")),
            (0xfe10, 0xfe1f, self.tr("Vertical Forms")),
            (0xfe20, 0xfe2f, self.tr("Combining Half Marks")),
            (0xfe30, 0xfe4f, self.tr("CJK Compatibility Forms")),
            (0xfe50, 0xfe6f, self.tr("Small Form Variants")),
            (0xfe70, 0xfeff, self.tr("Arabic Presentation Forms-B")),
            (0xff00, 0xffef, self.tr("Half- and Fullwidth Forms")),
            (0xfff0, 0xffff, self.tr("Specials")),
        ]
        if sys.maxunicode > 0xffff:
            self.__tables.extend([
                (0x10000, 0x1007f, self.tr("Linear B Syllabary")),
                (0x10080, 0x100ff, self.tr("Linear B Ideograms")),
                (0x10100, 0x1013f, self.tr("Aegean Numbers")),
                (0x10140, 0x1018f, self.tr("Ancient Greek Numbers")),
                (0x10190, 0x101cf, self.tr("Ancient Symbols")),
                (0x101d0, 0x101ff, self.tr("Phaistos Disc")),
                (0x10280, 0x1029f, self.tr("Lycian")),
                (0x102a0, 0x102df, self.tr("Carian")),
                (0x10300, 0x1032f, self.tr("Old Italic")),
                (0x10330, 0x1034f, self.tr("Gothic")),
                (0x10380, 0x1039f, self.tr("Ugaritic")),
                (0x103a0, 0x103df, self.tr("Old Persian")),
                (0x10400, 0x1044f, self.tr("Deseret")),
                (0x10450, 0x1047f, self.tr("Shavian")),
                (0x10480, 0x104af, self.tr("Osmanya")),
                (0x10800, 0x1083f, self.tr("Cypriot Syllabary")),
                (0x10840, 0x1085f, self.tr("Imperial Aramaic")),
                (0x10900, 0x1091f, self.tr("Phoenician")),
                (0x10920, 0x1093f, self.tr("Lydian")),
                (0x10980, 0x1099f, self.tr("Meroitic Hieroglyphs")),
                (0x109a0, 0x109ff, self.tr("Meroitic Cursive")),
                (0x10a00, 0x10a5f, self.tr("Kharoshthi")),
                (0x10a60, 0x10a7f, self.tr("Old South Arabian")),
                (0x10b00, 0x10b3f, self.tr("Avestan")),
                (0x10b40, 0x10b5f, self.tr("Inscriptional Parthian")),
                (0x10b60, 0x10b7f, self.tr("Inscriptional Pahlavi")),
                (0x10c00, 0x10c4f, self.tr("Old Turkic")),
                (0x10e60, 0x10e7f, self.tr("Rumi Numeral Symbols")),
                (0x11000, 0x1107f, self.tr("Brahmi")),
                (0x11080, 0x110cf, self.tr("Kaithi")),
                (0x110d0, 0x110ff, self.tr("Sora Sompeng")),
                (0x11100, 0x1114f, self.tr("Chakma")),
                (0x11180, 0x111df, self.tr("Sharada")),
                (0x11680, 0x116cf, self.tr("Takri")),
                (0x12000, 0x123ff, self.tr("Cuneiform")),
                (0x12400, 0x1247f,
                 self.tr("Cuneiform Numbers and Punctuation")),
                (0x13000, 0x1342f, self.tr("Egyptian Hieroglyphs")),
                (0x16800, 0x16a3f, self.tr("Bamum Supplement")),
                (0x16f00, 0x16f9f, self.tr("Miao")),
                (0x1b000, 0x1b0ff, self.tr("Kana Supplement")),
                (0x1d000, 0x1d0ff, self.tr("Byzantine Musical Symbols")),
                (0x1d100, 0x1d1ff, self.tr("Musical Symbols")),
                (0x1d200, 0x1d24f,
                 self.tr("Ancient Greek Musical Notation")),
                (0x1d300, 0x1d35f, self.tr("Tai Xuan Jing Symbols")),
                (0x1d360, 0x1d37f,
                 self.tr("Counting Rod Numerals")),
                (0x1d400, 0x1d7ff,
                 self.tr("Mathematical Alphanumeric Symbols")),
                (0x1ee00, 0x1eeff,
                 self.tr("Arabic Mathematical Alphabetic Symbols")),
                (0x1f000, 0x1f02f, self.tr("Mahjong Tiles")),
                (0x1f030, 0x1f09f, self.tr("Domino Tiles")),
                (0x1f0a0, 0x1f0ff, self.tr("Playing Cards")),
                (0x1f100, 0x1f1ff,
                 self.tr("Enclosed Alphanumeric Supplement")),
                (0x1f200, 0x1f2ff,
                 self.tr("Enclosed Ideographic Supplement")),
                (0x1f300, 0x1f5ff,
                 self.tr("Miscellaneous Symbols And Pictographs")),
                (0x1f600, 0x1f64f, self.tr("Emoticons")),
                (0x1f680, 0x1f6ff, self.tr("Transport And Map Symbols")),
                (0x1f700, 0x1f77f, self.tr("Alchemical Symbols")),
                (0x20000, 0x2a6df, self.tr("CJK Unified Ideogr. Ext. B")),
                (0x2a700, 0x2b73f,
                 self.tr("CJK Unified Ideographs Extension C")),
                (0x2b740, 0x2b81f,
                 self.tr("CJK Unified Ideographs Extension D")),
                (0x2f800, 0x2fa1f,
                 self.tr("CJK Compatapility Ideogr. Suppl.")),
                (0xe0000, 0xe007f, self.tr("Tags")),
                (0xe0100, 0xe01ef,
                 self.tr("Variation Selectors Supplement")),
                (0xf0000, 0xfffff,
                 self.tr("Supplementary Private Use Area-A")),
                (0x100000, 0x10ffff,
                 self.tr("Supplementary Private Use Area-B")),
            ])
        self.__currentTableIndex = 0
    
    def getTableNames(self):
        """
        Public method to get a list of table names.
        
        @return list of table names (list of strings)
        """
        return [table[2] for table in self.__tables]
    
    def getTableBoundaries(self, index):
        """
        Public method to get the first and last character position
        of the given table.
        
        @param index index of the character table (integer)
        @return first and last character position (integer, integer)
        """
        return self.__tables[index][0], self.__tables[index][1]
    
    def getTableIndex(self):
        """
        Public method to get the current table index.
        
        @return current table index (integer)
        """
        return self.__currentTableIndex
    
    def selectTable(self, index):
        """
        Public method to select the shown character table.
        
        @param index index of the character table (integer)
        """
        self.beginResetModel()
        self.__currentTableIndex = index
        self.endResetModel()
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Public method to get header data from the model.
        
        @param section section number (integer)
        @param orientation orientation (Qt.Orientation)
        @param role role of the data to retrieve (integer)
        @return requested data
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.__headerData[section]
        
        return QAbstractTableModel.headerData(self, section, orientation, role)
    
    def data(self, index, role=Qt.DisplayRole):
        """
        Public method to get data from the model.
        
        @param index index to get data for (QModelIndex)
        @param role role of the data to retrieve (integer)
        @return requested data
        """
        id = self.__tables[self.__currentTableIndex][0] + index.row()
        
        if role == Qt.DisplayRole:
            col = index.column()
            if col == 0:
                return self.__locale.toString(id)
            elif col == 1:
                return chr(id)
            elif col == 2:
                return "0x{0:04x}".format(id)
            elif col == 3:
                if id in html_entities.codepoint2name:
                    return "&{0};".format(html_entities.codepoint2name[id])
            elif col == 4:
                return unicodedata.name(chr(id), '').title()
        
        if role == Qt.BackgroundColorRole:
            if index.column() == 0:
                return QColor(Qt.lightGray)
        
        if role == Qt.TextColorRole:
            char = chr(id)
            if self.__isDigit(char):
                return QColor(Qt.darkBlue)
            elif self.__isLetter(char):
                return QColor(Qt.darkGreen)
            elif self.__isMark(char):
                return QColor(Qt.darkRed)
            elif self.__isSymbol(char):
                return QColor(Qt.black)
            elif self.__isPunct(char):
                return QColor(Qt.darkMagenta)
            else:
                return QColor(Qt.darkGray)
        
        if role == Qt.TextAlignmentRole:
            if index.column() in [0, 1, 3]:
                return Qt.AlignHCenter
        
        return None
    
    def columnCount(self, parent):
        """
        Public method to get the number of columns of the model.
        
        @param parent parent index (QModelIndex)
        @return number of columns (integer)
        """
        if parent.column() > 0:
            return 0
        else:
            return len(self.__headerData)
    
    def rowCount(self, parent):
        """
        Public method to get the number of rows of the model.
        
        @param parent parent index (QModelIndex)
        @return number of columns (integer)
        """
        if parent.isValid():
            return 0
        else:
            first, last = self.__tables[self.__currentTableIndex][:2]
            return last - first + 1
    
    def __isDigit(self, char):
        """
        Private method to check, if a character is a digit.
        
        @param char character to test (one character string)
        @return flag indicating a digit (boolean)
        """
        return unicodedata.category(str(char)) == "Nd"
    
    def __isLetter(self, char):
        """
        Private method to check, if a character is a letter.
        
        @param char character to test (one character string)
        @return flag indicating a letter (boolean)
        """
        return unicodedata.category(str(char)) in ["Lu", "Ll", "Lt", "Lm",
                                                   "Lo"]
    
    def __isMark(self, char):
        """
        Private method to check, if a character is a mark character.
        
        @param char character to test (one character string)
        @return flag indicating a mark character (boolean)
        """
        return unicodedata.category(str(char)) in ["Mn", "Mc", "Me"]
    
    def __isSymbol(self, char):
        """
        Private method to check, if a character is a symbol.
        
        @param char character to test (one character string)
        @return flag indicating a symbol (boolean)
        """
        return unicodedata.category(str(char)) in ["Sm", "Sc", "Sk", "So"]
    
    def __isPunct(self, char):
        """
        Private method to check, if a character is a punctuation character.
        
        @param char character to test (one character string)
        @return flag indicating a punctuation character (boolean)
        """
        return unicodedata.category(str(char)) in ["Pc", "Pd", "Ps", "Pe",
                                                   "Pi", "Pf", "Po"]
    
    def getLocale(self):
        """
        Public method to get the used locale.
        
        @return used locale
        @rtype QLocale
        """
        return self.__locale


class SymbolsWidget(QWidget, Ui_SymbolsWidget):
    """
    Class implementing a widget to select a symbol in various formats.
    
    @signal insertSymbol(str) emitted after the user has selected a symbol
    """
    insertSymbol = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(SymbolsWidget, self).__init__(parent)
        self.setupUi(self)
        
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        
        self.__model = SymbolsModel(self)
        self.symbolsTable.setModel(self.__model)
        self.symbolsTable.selectionModel().currentRowChanged.connect(
            self.__currentRowChanged)
        
        if qVersion() >= "5.0.0":
            self.symbolsTable.horizontalHeader().setSectionResizeMode(
                QHeaderView.Fixed)
        else:
            self.symbolsTable.horizontalHeader().setResizeMode(
                QHeaderView.Fixed)
        fm = self.fontMetrics()
        em = fm.width("M")
        self.symbolsTable.horizontalHeader().resizeSection(0, em * 5)
        self.symbolsTable.horizontalHeader().resizeSection(1, em * 5)
        self.symbolsTable.horizontalHeader().resizeSection(2, em * 6)
        self.symbolsTable.horizontalHeader().resizeSection(3, em * 8)
        self.symbolsTable.horizontalHeader().resizeSection(4, em * 85)
        self.symbolsTable.verticalHeader().setDefaultSectionSize(
            fm.height() + 4)
        
        tableIndex = int(
            Preferences.Prefs.settings.value("Symbols/CurrentTable", 1))
        self.tableCombo.addItems(self.__model.getTableNames())
        self.tableCombo.setCurrentIndex(tableIndex)
        
        index = self.__model.index(
            int(Preferences.Prefs.settings.value("Symbols/Top", 0)),
            0)
        self.symbolsTable.scrollTo(index, QAbstractItemView.PositionAtTop)
        self.symbolsTable.selectionModel().setCurrentIndex(
            index,
            QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)
    
    @pyqtSlot(QModelIndex)
    def on_symbolsTable_activated(self, index):
        """
        Private slot to signal the selection of a symbol.
        
        @param index index of the selected symbol (QModelIndex)
        """
        txt = self.__model.data(index)
        if txt:
            self.insertSymbol.emit(txt)
    
    @pyqtSlot()
    def on_symbolSpinBox_editingFinished(self):
        """
        Private slot to move the table to the entered symbol id.
        """
        id = self.symbolSpinBox.value()
        first, last = self.__model.getTableBoundaries(
            self.__model.getTableIndex())
        row = id - first
        self.symbolsTable.selectRow(row)
        self.symbolsTable.scrollTo(
            self.__model.index(row, 0), QAbstractItemView.PositionAtCenter)
    
    @pyqtSlot(int)
    def on_tableCombo_currentIndexChanged(self, index):
        """
        Private slot to select the current character table.
        
        @param index index of the character table (integer)
        """
        self.symbolsTable.setUpdatesEnabled(False)
        self.__model.selectTable(index)
        self.symbolsTable.setUpdatesEnabled(True)
        self.symbolsTable.resizeColumnsToContents()
        
        first, last = self.__model.getTableBoundaries(index)
        self.symbolSpinBox.setMinimum(first)
        self.symbolSpinBox.setMaximum(last)
        
        Preferences.Prefs.settings.setValue("Symbols/CurrentTable", index)
    
    def __currentRowChanged(self, current, previous):
        """
        Private slot recording the currently selected row.
        
        @param current current index (QModelIndex)
        @param previous previous current index (QModelIndex)
        """
        Preferences.Prefs.settings.setValue("Symbols/Top", current.row())
        self.symbolSpinBox.setValue(self.__model.getLocale().toInt(
            self.__model.data(self.__model.index(current.row(), 0)))[0])
