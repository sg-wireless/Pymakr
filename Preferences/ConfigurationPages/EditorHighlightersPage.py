# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor Highlighter Associations configuration page.
"""

from __future__ import unicode_literals

import os

from pygments.lexers import get_all_lexers

from PyQt5.QtCore import Qt, pyqtSlot, qVersion
from PyQt5.QtWidgets import QHeaderView, QTreeWidgetItem

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorHighlightersPage import Ui_EditorHighlightersPage

import Preferences


class EditorHighlightersPage(ConfigurationPageBase, Ui_EditorHighlightersPage):
    """
    Class implementing the Editor Highlighter Associations configuration page.
    """
    def __init__(self, lexers):
        """
        Constructor
        
        @param lexers reference to the lexers dictionary
        """
        super(EditorHighlightersPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("EditorHighlightersPage")
        
        self.editorLexerList.headerItem().setText(
            self.editorLexerList.columnCount(), "")
        header = self.editorLexerList.header()
        if qVersion() >= "5.0.0":
            header.setSectionResizeMode(QHeaderView.ResizeToContents)
        else:
            header.setResizeMode(QHeaderView.ResizeToContents)
        header.setSortIndicator(0, Qt.AscendingOrder)
        
        try:
            self.extsep = os.extsep
        except AttributeError:
            self.extsep = "."
        
        self.extras = ["-----------", self.tr("Alternative")]
        languages = [''] + sorted(lexers.keys()) + self.extras
        self.editorLexerCombo.addItems(languages)
        
        pygmentsLexers = [''] + sorted([l[0] for l in get_all_lexers()])
        self.pygmentsLexerCombo.addItems(pygmentsLexers)
        
        # set initial values
        lexerAssocs = Preferences.getEditorLexerAssocs()
        for ext in lexerAssocs:
            QTreeWidgetItem(self.editorLexerList, [ext, lexerAssocs[ext]])
        self.editorLexerList.sortByColumn(0, Qt.AscendingOrder)
        
    def save(self):
        """
        Public slot to save the Editor Highlighter Associations configuration.
        """
        lexerAssocs = {}
        for index in range(
                self.editorLexerList.topLevelItemCount()):
            itm = self.editorLexerList.topLevelItem(index)
            lexerAssocs[itm.text(0)] = itm.text(1)
        Preferences.setEditorLexerAssocs(lexerAssocs)
        
    @pyqtSlot()
    def on_addLexerButton_clicked(self):
        """
        Private slot to add the lexer association displayed to the list.
        """
        ext = self.editorFileExtEdit.text()
        if ext.startswith(self.extsep):
            ext.replace(self.extsep, "")
        lexer = self.editorLexerCombo.currentText()
        if lexer in self.extras:
            pygmentsLexer = self.pygmentsLexerCombo.currentText()
            if not pygmentsLexer:
                lexer = pygmentsLexer
            else:
                lexer = "Pygments|{0}".format(pygmentsLexer)
        if ext and lexer:
            itmList = self.editorLexerList.findItems(
                ext, Qt.MatchFlags(Qt.MatchExactly), 0)
            if itmList:
                index = self.editorLexerList.indexOfTopLevelItem(itmList[0])
                itm = self.editorLexerList.takeTopLevelItem(index)
                del itm
            QTreeWidgetItem(self.editorLexerList, [ext, lexer])
            self.editorFileExtEdit.clear()
            self.editorLexerCombo.setCurrentIndex(0)
            self.pygmentsLexerCombo.setCurrentIndex(0)
            self.editorLexerList.sortItems(
                self.editorLexerList.sortColumn(),
                self.editorLexerList.header().sortIndicatorOrder())
        
    @pyqtSlot()
    def on_deleteLexerButton_clicked(self):
        """
        Private slot to delete the currently selected lexer association of the
        list.
        """
        itmList = self.editorLexerList.selectedItems()
        if itmList:
            index = self.editorLexerList.indexOfTopLevelItem(itmList[0])
            itm = self.editorLexerList.takeTopLevelItem(index)
            del itm
            
            self.editorLexerList.clearSelection()
            self.editorFileExtEdit.clear()
            self.editorLexerCombo.setCurrentIndex(0)
        
    def on_editorLexerList_itemClicked(self, itm, column):
        """
        Private slot to handle the clicked signal of the lexer association
        list.
        
        @param itm reference to the selecte item (QTreeWidgetItem)
        @param column column the item was clicked or activated (integer)
            (ignored)
        """
        if itm is None:
            self.editorFileExtEdit.clear()
            self.editorLexerCombo.setCurrentIndex(0)
            self.pygmentsLexerCombo.setCurrentIndex(0)
        else:
            self.editorFileExtEdit.setText(itm.text(0))
            lexer = itm.text(1)
            if lexer.startswith("Pygments|"):
                pygmentsLexer = lexer.split("|")[1]
                pygmentsIndex = self.pygmentsLexerCombo.findText(pygmentsLexer)
                lexer = self.tr("Alternative")
            else:
                pygmentsIndex = 0
            index = self.editorLexerCombo.findText(lexer)
            self.editorLexerCombo.setCurrentIndex(index)
            self.pygmentsLexerCombo.setCurrentIndex(pygmentsIndex)
        
    def on_editorLexerList_itemActivated(self, itm, column):
        """
        Private slot to handle the activated signal of the lexer association
        list.
        
        @param itm reference to the selecte item (QTreeWidgetItem)
        @param column column the item was clicked or activated (integer)
            (ignored)
        """
        self.on_editorLexerList_itemClicked(itm, column)
    
    @pyqtSlot(str)
    def on_editorLexerCombo_currentIndexChanged(self, text):
        """
        Private slot to handle the selection of a lexer.
        
        @param text text of the lexer combo (string)
        """
        if text in self.extras:
            self.pygmentsLexerCombo.setEnabled(True)
            self.pygmentsLabel.setEnabled(True)
        else:
            self.pygmentsLexerCombo.setEnabled(False)
            self.pygmentsLabel.setEnabled(False)


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = EditorHighlightersPage(dlg.getLexers())
    return page
