# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor Highlighting Styles configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, Qt, QFileInfo, QFile, QIODevice
from PyQt5.QtGui import QPalette, QFont
from PyQt5.QtWidgets import QColorDialog, QFontDialog, QInputDialog, QMenu

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorHighlightingStylesPage import Ui_EditorHighlightingStylesPage

from E5Gui import E5MessageBox, E5FileDialog

import Preferences


class EditorHighlightingStylesPage(ConfigurationPageBase,
                                   Ui_EditorHighlightingStylesPage):
    """
    Class implementing the Editor Highlighting Styles configuration page.
    """
    FAMILYONLY = 0
    SIZEONLY = 1
    FAMILYANDSIZE = 2
    FONT = 99
    
    def __init__(self, lexers):
        """
        Constructor
        
        @param lexers reference to the lexers dictionary
        """
        super(EditorHighlightingStylesPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("EditorHighlightingStylesPage")
        
        self.__fontButtonMenu = QMenu()
        act = self.__fontButtonMenu.addAction(self.tr("Font"))
        act.setData(self.FONT)
        self.__fontButtonMenu.addSeparator()
        act = self.__fontButtonMenu.addAction(
            self.tr("Family and Size only"))
        act.setData(self.FAMILYANDSIZE)
        act = self.__fontButtonMenu.addAction(self.tr("Family only"))
        act.setData(self.FAMILYONLY)
        act = self.__fontButtonMenu.addAction(self.tr("Size only"))
        act.setData(self.SIZEONLY)
        self.__fontButtonMenu.triggered.connect(self.__fontButtonMenuTriggered)
        self.fontButton.setMenu(self.__fontButtonMenu)
        
        self.__allFontsButtonMenu = QMenu()
        act = self.__allFontsButtonMenu.addAction(self.tr("Font"))
        act.setData(self.FONT)
        self.__allFontsButtonMenu.addSeparator()
        act = self.__allFontsButtonMenu.addAction(
            self.tr("Family and Size only"))
        act.setData(self.FAMILYANDSIZE)
        act = self.__allFontsButtonMenu.addAction(self.tr("Family only"))
        act.setData(self.FAMILYONLY)
        act = self.__allFontsButtonMenu.addAction(self.tr("Size only"))
        act.setData(self.SIZEONLY)
        self.__allFontsButtonMenu.triggered.connect(
            self.__allFontsButtonMenuTriggered)
        self.allFontsButton.setMenu(self.__allFontsButtonMenu)
        
        self.lexer = None
        self.lexers = lexers
        
        # set initial values
        languages = sorted([''] + list(self.lexers.keys()))
        self.lexerLanguageComboBox.addItems(languages)
        self.on_lexerLanguageComboBox_activated("")
        
    def save(self):
        """
        Public slot to save the Editor Highlighting Styles configuration.
        """
        for lexer in list(self.lexers.values()):
            lexer.writeSettings(Preferences.Prefs.settings, "Scintilla")
        
    @pyqtSlot(str)
    def on_lexerLanguageComboBox_activated(self, language):
        """
        Private slot to fill the style combo of the source page.
        
        @param language The lexer language (string)
        """
        self.styleElementList.clear()
        self.styleGroup.setEnabled(False)
        self.lexer = None
        
        self.exportCurrentButton.setEnabled(language != "")
        self.importCurrentButton.setEnabled(language != "")
        
        if not language:
            return
        
        try:
            self.lexer = self.lexers[language]
        except KeyError:
            return
        
        self.styleGroup.setEnabled(True)
        self.styleElementList.addItems(self.lexer.styles)
        self.__styleAllItems()
        self.styleElementList.setCurrentRow(0)
        
    def __styleAllItems(self):
        """
        Private method to style all items of the style element list.
        """
        for row in range(self.styleElementList.count()):
            style = self.lexer.ind2style[row]
            colour = self.lexer.color(style)
            paper = self.lexer.paper(style)
            font = self.lexer.font(style)
            eolfill = self.lexer.eolFill(style)
            
            itm = self.styleElementList.item(row)
            itm.setFont(font)
            itm.setBackground(paper)
            itm.setForeground(colour)
            if eolfill:
                itm.setCheckState(Qt.Checked)
            else:
                itm.setCheckState(Qt.Unchecked)
        
    def on_styleElementList_currentRowChanged(self, index):
        """
        Private method to set up the style element part of the source page.
        
        @param index the style index.
        """
        try:
            self.style = self.lexer.ind2style[index]
        except KeyError:
            return
        
        colour = self.lexer.color(self.style)
        paper = self.lexer.paper(self.style)
        eolfill = self.lexer.eolFill(self.style)
        font = self.lexer.font(self.style)
        
        self.sampleText.setFont(font)
        pl = self.sampleText.palette()
        pl.setColor(QPalette.Text, colour)
        pl.setColor(QPalette.Base, paper)
        self.sampleText.setPalette(pl)
        self.sampleText.repaint()
        self.eolfillCheckBox.setChecked(eolfill)
        
    @pyqtSlot()
    def on_foregroundButton_clicked(self):
        """
        Private method used to select the foreground colour of the selected
        style and lexer.
        """
        colour = QColorDialog.getColor(self.lexer.color(self.style))
        if colour.isValid():
            pl = self.sampleText.palette()
            pl.setColor(QPalette.Text, colour)
            self.sampleText.setPalette(pl)
            self.sampleText.repaint()
            if len(self.styleElementList.selectedItems()) > 1:
                for selItem in self.styleElementList.selectedItems():
                    style = self.lexer.ind2style[
                        self.styleElementList.row(selItem)]
                    self.lexer.setColor(colour, style)
                    selItem.setForeground(colour)
            else:
                self.lexer.setColor(colour, self.style)
                self.styleElementList.currentItem().setForeground(colour)
        
    @pyqtSlot()
    def on_backgroundButton_clicked(self):
        """
        Private method used to select the background colour of the selected
        style and lexer.
        """
        colour = QColorDialog.getColor(self.lexer.paper(self.style))
        if colour.isValid():
            pl = self.sampleText.palette()
            pl.setColor(QPalette.Base, colour)
            self.sampleText.setPalette(pl)
            self.sampleText.repaint()
            if len(self.styleElementList.selectedItems()) > 1:
                for selItem in self.styleElementList.selectedItems():
                    style = self.lexer.ind2style[
                        self.styleElementList.row(selItem)]
                    self.lexer.setPaper(colour, style)
                    selItem.setBackground(colour)
            else:
                self.lexer.setPaper(colour, self.style)
                self.styleElementList.currentItem().setBackground(colour)
        
    @pyqtSlot()
    def on_allBackgroundColoursButton_clicked(self):
        """
        Private method used to select the background colour of all styles of a
        selected lexer.
        """
        colour = QColorDialog.getColor(self.lexer.paper(self.style))
        if colour.isValid():
            pl = self.sampleText.palette()
            pl.setColor(QPalette.Base, colour)
            self.sampleText.setPalette(pl)
            self.sampleText.repaint()
            for style in list(self.lexer.ind2style.values()):
                self.lexer.setPaper(colour, style)
            self.__styleAllItems()
        
    def __changeFont(self, doAll, familyOnly, sizeOnly):
        """
        Private slot to change the highlighter font.
        
        @param doAll flag indicating to change the font for all styles
            (boolean)
        @param familyOnly flag indicating to set the font family only (boolean)
        @param sizeOnly flag indicating to set the font size only (boolean
        """
        def setFont(font, style, familyOnly, sizeOnly):
            """
            Local function to set the font.
            
            @param font font to be set (QFont)
            @param style style to set the font for (integer)
            @param familyOnly flag indicating to set the font family only
                (boolean)
            @param sizeOnly flag indicating to set the font size only (boolean
            """
            if familyOnly or sizeOnly:
                newFont = QFont(self.lexer.font(style))
                if familyOnly:
                    newFont.setFamily(font.family())
                if sizeOnly:
                    newFont.setPointSize(font.pointSize())
                self.lexer.setFont(newFont, style)
            else:
                self.lexer.setFont(font, style)
        
        def setSampleFont(font, familyOnly, sizeOnly):
            """
            Local function to set the font of the sample text.
            
            @param font font to be set (QFont)
            @param familyOnly flag indicating to set the font family only
                (boolean)
            @param sizeOnly flag indicating to set the font size only (boolean
            """
            if familyOnly or sizeOnly:
                newFont = QFont(self.lexer.font(self.style))
                if familyOnly:
                    newFont.setFamily(font.family())
                if sizeOnly:
                    newFont.setPointSize(font.pointSize())
                self.sampleText.setFont(newFont)
            else:
                self.sampleText.setFont(font)
        
        font, ok = QFontDialog.getFont(self.lexer.font(self.style))
        if ok:
            setSampleFont(font, familyOnly, sizeOnly)
            if doAll:
                for style in list(self.lexer.ind2style.values()):
                    setFont(font, style, familyOnly, sizeOnly)
                self.__styleAllItems()
            elif len(self.styleElementList.selectedItems()) > 1:
                for selItem in self.styleElementList.selectedItems():
                    style = self.lexer.ind2style[
                        self.styleElementList.row(selItem)]
                    setFont(font, style, familyOnly, sizeOnly)
                    itmFont = self.lexer.font(style)
                    selItem.setFont(itmFont)
            else:
                setFont(font, self.style, familyOnly, sizeOnly)
                itmFont = self.lexer.font(self.style)
                self.styleElementList.currentItem().setFont(itmFont)
        
    def __fontButtonMenuTriggered(self, act):
        """
        Private slot used to select the font of the selected style and lexer.
        
        @param act reference to the triggering action (QAction)
        """
        if act is None:
            return
        
        familyOnly = act.data() in [self.FAMILYANDSIZE, self.FAMILYONLY]
        sizeOnly = act.data() in [self.FAMILYANDSIZE, self.SIZEONLY]
        self.__changeFont(False, familyOnly, sizeOnly)
        
    def __allFontsButtonMenuTriggered(self, act):
        """
        Private slot used to change the font of all styles of a selected lexer.
        
        @param act reference to the triggering action (QAction)
        """
        if act is None:
            return
        
        familyOnly = act.data() in [self.FAMILYANDSIZE, self.FAMILYONLY]
        sizeOnly = act.data() in [self.FAMILYANDSIZE, self.SIZEONLY]
        self.__changeFont(True, familyOnly, sizeOnly)
        
    def on_eolfillCheckBox_toggled(self, on):
        """
        Private method used to set the eolfill for the selected style and
        lexer.
        
        @param on flag indicating enabled or disabled state (boolean)
        """
        checkState = Qt.Checked if on else Qt.Unchecked
        if len(self.styleElementList.selectedItems()) > 1:
            for selItem in self.styleElementList.selectedItems():
                style = self.lexer.ind2style[
                    self.styleElementList.row(selItem)]
                self.lexer.setEolFill(on, style)
                selItem.setCheckState(checkState)
        else:
            self.lexer.setEolFill(on, self.style)
            self.styleElementList.currentItem().setCheckState(checkState)
        
    @pyqtSlot()
    def on_allEolFillButton_clicked(self):
        """
        Private method used to set the eolfill for all styles of a selected
        lexer.
        """
        on = self.tr("Enabled")
        off = self.tr("Disabled")
        selection, ok = QInputDialog.getItem(
            self,
            self.tr("Fill to end of line"),
            self.tr("Select fill to end of line for all styles"),
            [on, off],
            0, False)
        if ok:
            enabled = selection == on
            self.eolfillCheckBox.setChecked(enabled)
            for style in list(self.lexer.ind2style.values()):
                self.lexer.setEolFill(enabled, style)
            self.__styleAllItems()
        
    @pyqtSlot()
    def on_defaultButton_clicked(self):
        """
        Private method to set the current style to its default values.
        """
        if len(self.styleElementList.selectedItems()) > 1:
            for selItem in self.styleElementList.selectedItems():
                style = self.lexer.ind2style[
                    self.styleElementList.row(selItem)]
                self.__setToDefault(style)
        else:
            self.__setToDefault(self.style)
        self.on_styleElementList_currentRowChanged(
            self.styleElementList.currentRow())
        self.__styleAllItems()
        
    @pyqtSlot()
    def on_allDefaultButton_clicked(self):
        """
        Private method to set all styles to their default values.
        """
        for style in list(self.lexer.ind2style.values()):
            self.__setToDefault(style)
        self.on_styleElementList_currentRowChanged(
            self.styleElementList.currentRow())
        self.__styleAllItems()
        
    def __setToDefault(self, style):
        """
        Private method to set a specific style to its default values.
        
        @param style style to be reset (integer)
        """
        self.lexer.setColor(self.lexer.defaultColor(style), style)
        self.lexer.setPaper(self.lexer.defaultPaper(style), style)
        self.lexer.setFont(self.lexer.defaultFont(style), style)
        self.lexer.setEolFill(self.lexer.defaultEolFill(style), style)
        
    @pyqtSlot()
    def on_importCurrentButton_clicked(self):
        """
        Private slot to import the styles of the current lexer.
        """
        self.__importStyles({self.lexer.language(): self.lexer})
        
    @pyqtSlot()
    def on_exportCurrentButton_clicked(self):
        """
        Private slot to export the styles of the current lexer.
        """
        self.__exportStyles([self.lexer])
        
    @pyqtSlot()
    def on_importAllButton_clicked(self):
        """
        Private slot to import the styles of all lexers.
        """
        self.__importStyles(self.lexers)
        
    @pyqtSlot()
    def on_exportAllButton_clicked(self):
        """
        Private slot to export the styles of all lexers.
        """
        self.__exportStyles(list(self.lexers.values()))
        
    def __exportStyles(self, lexers):
        """
        Private method to export the styles of the given lexers.
        
        @param lexers list of lexer objects for which to export the styles
        """
        fn, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            self,
            self.tr("Export Highlighting Styles"),
            "",
            self.tr("Highlighting styles file (*.e4h)"),
            "",
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        
        if not fn:
            return
        
        ext = QFileInfo(fn).suffix()
        if not ext:
            ex = selectedFilter.split("(*")[1].split(")")[0]
            if ex:
                fn += ex
        
        f = QFile(fn)
        if f.open(QIODevice.WriteOnly):
            from E5XML.HighlightingStylesWriter import HighlightingStylesWriter
            HighlightingStylesWriter(f, lexers).writeXML()
            f.close()
        else:
            E5MessageBox.critical(
                self,
                self.tr("Export Highlighting Styles"),
                self.tr(
                    """<p>The highlighting styles could not be exported"""
                    """ to file <b>{0}</b>.</p><p>Reason: {1}</p>""")
                .format(fn, f.errorString())
            )
        
    def __importStyles(self, lexers):
        """
        Private method to import the styles of the given lexers.
        
        @param lexers dictionary of lexer objects for which to import the
            styles
        """
        fn = E5FileDialog.getOpenFileName(
            self,
            self.tr("Import Highlighting Styles"),
            "",
            self.tr("Highlighting styles file (*.e4h)"))
        
        if not fn:
            return
        
        f = QFile(fn)
        if f.open(QIODevice.ReadOnly):
            from E5XML.HighlightingStylesReader import HighlightingStylesReader
            reader = HighlightingStylesReader(f, lexers)
            reader.readXML()
            f.close()
        else:
            E5MessageBox.critical(
                self,
                self.tr("Import Highlighting Styles"),
                self.tr(
                    """<p>The highlighting styles could not be read"""
                    """ from file <b>{0}</b>.</p><p>Reason: {1}</p>""")
                .format(fn, f.errorString())
            )
            return
        
        if self.lexer:
            colour = self.lexer.color(self.style)
            paper = self.lexer.paper(self.style)
            eolfill = self.lexer.eolFill(self.style)
            font = self.lexer.font(self.style)
            
            self.sampleText.setFont(font)
            pl = self.sampleText.palette()
            pl.setColor(QPalette.Text, colour)
            pl.setColor(QPalette.Base, paper)
            self.sampleText.setPalette(pl)
            self.sampleText.repaint()
            self.eolfillCheckBox.setChecked(eolfill)
            
            self.__styleAllItems()
        
    def saveState(self):
        """
        Public method to save the current state of the widget.
        
        @return array containing the index of the selected lexer language
            (integer) and the index of the selected lexer entry (integer)
        """
        savedState = [
            self.lexerLanguageComboBox.currentIndex(),
            self.styleElementList.currentRow(),
        ]
        return savedState
        
    def setState(self, state):
        """
        Public method to set the state of the widget.
        
        @param state state data generated by saveState
        """
        self.lexerLanguageComboBox.setCurrentIndex(state[0])
        self.on_lexerLanguageComboBox_activated(
            self.lexerLanguageComboBox.currentText())
        self.styleElementList.setCurrentRow(state[1])


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = EditorHighlightingStylesPage(dlg.getLexers())
    return page
