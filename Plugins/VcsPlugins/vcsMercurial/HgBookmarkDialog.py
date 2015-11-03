# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the bookmark dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_HgBookmarkDialog import Ui_HgBookmarkDialog


class HgBookmarkDialog(QDialog, Ui_HgBookmarkDialog):
    """
    Class mplementing the bookmark dialog.
    """
    DEFINE_MODE = 0
    MOVE_MODE = 1
    
    def __init__(self, mode, tagsList, branchesList, bookmarksList,
                 parent=None):
        """
        Constructor
        
        @param mode of the dialog (integer)
        @param tagsList list of tags (list of strings)
        @param branchesList list of branches (list of strings)
        @param bookmarksList list of bookmarks (list of strings)
        @param parent reference to the parent widget (QWidget)
        """
        super(HgBookmarkDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        
        self.__mode = mode
        if mode == self.MOVE_MODE:
            self.nameEdit.hide()
            self.nameCombo.addItems([""] + sorted(bookmarksList))
            self.setWindowTitle(self.tr("Move Bookmark"))
        else:
            self.nameCombo.hide()
            self.setWindowTitle(self.tr("Define Bookmark"))
        
        self.__bookmarksList = bookmarksList[:]
        
        self.tagCombo.addItems(sorted(tagsList))
        self.branchCombo.addItems(["default"] + sorted(branchesList))
        self.bookmarkCombo.addItems(sorted(bookmarksList))
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    def __updateOK(self):
        """
        Private slot to update the OK button.
        """
        if self.__mode == self.MOVE_MODE:
            enabled = self.nameCombo.currentText() != ""
        else:
            enabled = self.nameEdit.text() != ""
        if self.idButton.isChecked():
            enabled = enabled and self.idEdit.text() != ""
        elif self.tagButton.isChecked():
            enabled = enabled and self.tagCombo.currentText() != ""
        elif self.branchButton.isChecked():
            enabled = enabled and self.branchCombo.currentText() != ""
        elif self.bookmarkButton.isChecked():
            enabled = enabled and self.bookmarkCombo.currentText() != ""
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enabled)
    
    def __updateBookmarksCombo(self):
        """
        Private slot to update the bookmarks combo.
        """
        if self.__mode == self.MOVE_MODE:
            bookmark = self.nameCombo.currentText()
            selectedBookmark = self.bookmarkCombo.currentText()
            self.bookmarkCombo.clearEditText()
            self.bookmarkCombo.clear()
            self.bookmarkCombo.addItems(sorted(self.__bookmarksList))
            index = self.bookmarkCombo.findText(bookmark)
            if index > -1:
                self.bookmarkCombo.removeItem(index)
            if selectedBookmark:
                index = self.bookmarkCombo.findText(selectedBookmark)
                if index > -1:
                    self.bookmarkCombo.setCurrentIndex(index)
    
    @pyqtSlot(str)
    def on_nameCombo_activated(self, txt):
        """
        Private slot to handle changes of the selected bookmark name.
        
        @param txt selected combo entry (string)
        """
        self.__updateOK()
        self.__updateBookmarksCombo()
    
    @pyqtSlot(str)
    def on_nameEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the bookmark name.
        
        @param txt text of the edit (string)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_idButton_toggled(self, checked):
        """
        Private slot to handle changes of the ID select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_tagButton_toggled(self, checked):
        """
        Private slot to handle changes of the Tag select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_branchButton_toggled(self, checked):
        """
        Private slot to handle changes of the Branch select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_bookmarkButton_toggled(self, checked):
        """
        Private slot to handle changes of the Bookmark select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_idEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the ID edit.
        
        @param txt text of the edit (string)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_tagCombo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the Tag combo.
        
        @param txt text of the combo (string)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_branchCombo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the Branch combo.
        
        @param txt text of the combo (string)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_bookmarkCombo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the Bookmark combo.
        
        @param txt text of the combo (string)
        """
        self.__updateOK()
    
    def getData(self):
        """
        Public method to retrieve the entered data.
        
        @return tuple naming the revision and the bookmark name
            (string, string)
        """
        if self.numberButton.isChecked():
            rev = "rev({0})".format(self.numberSpinBox.value())
        elif self.idButton.isChecked():
            rev = "id({0})".format(self.idEdit.text())
        elif self.tagButton.isChecked():
            rev = self.tagCombo.currentText()
        elif self.branchButton.isChecked():
            rev = self.branchCombo.currentText()
        elif self.bookmarkButton.isChecked():
            rev = self.bookmarkCombo.currentText()
        else:
            rev = ""
        
        if self.__mode == self.MOVE_MODE:
            name = self.nameCombo.currentText().replace(" ", "_")
        else:
            name = self.nameEdit.text().replace(" ", "_")
        
        return rev, name
