# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to get the data to rename a bookmark.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_HgBookmarkRenameDialog import Ui_HgBookmarkRenameDialog


class HgBookmarkRenameDialog(QDialog, Ui_HgBookmarkRenameDialog):
    """
    Class implementing a dialog to get the data to rename a bookmark.
    """
    def __init__(self, bookmarksList, parent=None):
        """
        Constructor
        
        @param bookmarksList list of bookmarks (list of strings)
        @param parent reference to the parent widget (QWidget)
        """
        super(HgBookmarkRenameDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
       
        self.bookmarkCombo.addItems(sorted(bookmarksList))
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    def __updateUI(self):
        """
        Private slot to update the UI.
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            self.nameEdit.text() != "" and
            self.bookmarkCombo.currentText() != ""
        )
    
    @pyqtSlot(str)
    def on_nameEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the bookmark name.
        
        @param txt text of the edit (string)
        """
        self.__updateUI()
    
    @pyqtSlot(str)
    def on_bookmarkCombo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the selected bookmark.
        
        @param txt name of the selected bookmark (string)
        """
        self.__updateUI()
    
    def getData(self):
        """
        Public method to retrieve the entered data.
        
        @return tuple naming the new and old bookmark names
            (string, string)
        """
        return (
            self.nameEdit.text().replace(" ", "_"),
            self.bookmarkCombo.currentText().replace(" ", "_")
        )
