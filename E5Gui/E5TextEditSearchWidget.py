# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a horizontal search widget for QTextEdit.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QTextDocument
from PyQt5.QtWidgets import QWidget

from E5Gui import E5MessageBox

from .Ui_E5TextEditSearchWidget import Ui_E5TextEditSearchWidget

import UI.PixmapCache


class E5TextEditSearchWidget(QWidget, Ui_E5TextEditSearchWidget):
    """
    Class implementing a horizontal search widget for QTextEdit.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(E5TextEditSearchWidget, self).__init__(parent)
        self.setupUi(self)
        
        self.__textedit = None
        self.__findBackwards = True
        
        self.findPrevButton.setIcon(UI.PixmapCache.getIcon("1leftarrow.png"))
        self.findNextButton.setIcon(UI.PixmapCache.getIcon("1rightarrow.png"))
        
        self.findHistory = []
        
        self.findtextCombo.setCompleter(None)
        self.findtextCombo.lineEdit().returnPressed.connect(
            self.__findByReturnPressed)
        
        self.__setSearchButtons(False)
        
        self.setFocusProxy(self.findtextCombo)
    
    def attachTextEdit(self, textedit):
        """
        Public method to attach a QTextEdit widget.
        
        @param textedit reference to the QTextEdit to be attached (QTextEdit)
        """
        self.__textedit = textedit
    
    def keyPressEvent(self, event):
        """
        Protected slot to handle key press events.
        
        @param event reference to the key press event (QKeyEvent)
        """
        if self.__textedit and event.key() == Qt.Key_Escape:
            self.__textedit.setFocus(Qt.ActiveWindowFocusReason)
            event.accept()
    
    @pyqtSlot(str)
    def on_findtextCombo_editTextChanged(self, txt):
        """
        Private slot to enable/disable the find buttons.
        
        @param txt text of the combobox (string)
        """
        self.__setSearchButtons(txt != "")
    
    def __setSearchButtons(self, enabled):
        """
        Private slot to set the state of the search buttons.
        
        @param enabled flag indicating the state (boolean)
        """
        self.findPrevButton.setEnabled(enabled)
        self.findNextButton.setEnabled(enabled)
    
    def __findByReturnPressed(self):
        """
        Private slot to handle the returnPressed signal of the findtext
        combobox.
        """
        self.__find(self.__findBackwards)
    
    @pyqtSlot()
    def on_findPrevButton_clicked(self):
        """
        Private slot to find the previous occurrence.
        """
        self.__find(True)
    
    @pyqtSlot()
    def on_findNextButton_clicked(self):
        """
        Private slot to find the next occurrence.
        """
        self.__find(False)
    
    def __find(self, backwards):
        """
        Private method to search the associated text edit.
        
        @param backwards flag indicating a backwards search (boolean)
        """
        if not self.__textedit:
            return
        
        txt = self.findtextCombo.currentText()
        self.__findBackwards = backwards
        
        # This moves any previous occurrence of this statement to the head
        # of the list and updates the combobox
        if txt in self.findHistory:
            self.findHistory.remove(txt)
        self.findHistory.insert(0, txt)
        self.findtextCombo.clear()
        self.findtextCombo.addItems(self.findHistory)
        
        if backwards:
            flags = QTextDocument.FindFlags(QTextDocument.FindBackward)
        else:
            flags = QTextDocument.FindFlags()
        if self.caseCheckBox.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.wordCheckBox.isChecked():
            flags |= QTextDocument.FindWholeWords
        ok = self.__textedit.find(txt, flags)
        
        if not ok:
            E5MessageBox.information(
                self,
                self.tr("Find"),
                self.tr("""'{0}' was not found.""").format(txt))
