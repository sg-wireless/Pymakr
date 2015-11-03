# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter lexer associations for the project.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import Qt, pyqtSlot, qVersion
from PyQt5.QtWidgets import QHeaderView, QTreeWidgetItem, QDialog

from .Ui_LexerAssociationDialog import Ui_LexerAssociationDialog


class LexerAssociationDialog(QDialog, Ui_LexerAssociationDialog):
    """
    Class implementing a dialog to enter lexer associations for the project.
    """
    def __init__(self, project, parent=None):
        """
        Constructor
        
        @param project reference to the project object
        @param parent reference to the parent widget (QWidget)
        """
        super(LexerAssociationDialog, self).__init__(parent)
        self.setupUi(self)

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
        
        import QScintilla.Lexers
        languages = [''] + \
            sorted(QScintilla.Lexers.getSupportedLanguages().keys()) + \
            self.extras
        self.editorLexerCombo.addItems(languages)
        
        from pygments.lexers import get_all_lexers
        pygmentsLexers = [''] + sorted([l[0] for l in get_all_lexers()])
        self.pygmentsLexerCombo.addItems(pygmentsLexers)
        
        # set initial values
        self.project = project
        for ext, lexer in list(self.project.pdata["LEXERASSOCS"].items()):
            QTreeWidgetItem(self.editorLexerList, [ext, lexer])
        self.editorLexerList.sortByColumn(0, Qt.AscendingOrder)
    
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
        
        @param text text of the line edit (string)
        """
        if text in self.extras:
            self.pygmentsLexerCombo.setEnabled(True)
            self.pygmentsLabel.setEnabled(True)
        else:
            self.pygmentsLexerCombo.setEnabled(False)
            self.pygmentsLabel.setEnabled(False)

    def transferData(self):
        """
        Public slot to transfer the associations into the projects data
        structure.
        """
        self.project.pdata["LEXERASSOCS"] = {}
        for index in range(self.editorLexerList.topLevelItemCount()):
            itm = self.editorLexerList.topLevelItem(index)
            pattern = itm.text(0)
            self.project.pdata["LEXERASSOCS"][pattern] = itm.text(1)
