# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a configuration dialog for the bookmarked files menu.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QFileInfo, Qt, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QListWidgetItem, QDialog

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5FileDialog

from .Ui_BookmarkedFilesDialog import Ui_BookmarkedFilesDialog

import Utilities
import UI.PixmapCache


class BookmarkedFilesDialog(QDialog, Ui_BookmarkedFilesDialog):
    """
    Class implementing a configuration dialog for the bookmarked files menu.
    """
    def __init__(self, bookmarks, parent=None):
        """
        Constructor
        
        @param bookmarks list of bookmarked files (list of strings)
        @param parent parent widget (QWidget)
        """
        super(BookmarkedFilesDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.fileButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.fileCompleter = E5FileCompleter(self.fileEdit)
        
        self.bookmarks = bookmarks[:]
        for bookmark in self.bookmarks:
            itm = QListWidgetItem(bookmark, self.filesList)
            if not QFileInfo(bookmark).exists():
                itm.setBackground(QColor(Qt.red))
            
        if len(self.bookmarks):
            self.filesList.setCurrentRow(0)
        
    def on_fileEdit_textChanged(self, txt):
        """
        Private slot to handle the textChanged signal of the file edit.
        
        @param txt the text of the file edit (string)
        """
        self.addButton.setEnabled(txt != "")
        self.changeButton.setEnabled(
            txt != "" and
            self.filesList.currentRow() != -1)
        
    def on_filesList_currentRowChanged(self, row):
        """
        Private slot to set the lineedit depending on the selected entry.
        
        @param row the current row (integer)
        """
        if row == -1:
            self.fileEdit.clear()
            self.downButton.setEnabled(False)
            self.upButton.setEnabled(False)
            self.deleteButton.setEnabled(False)
            self.changeButton.setEnabled(False)
        else:
            maxIndex = len(self.bookmarks) - 1
            self.upButton.setEnabled(row != 0)
            self.downButton.setEnabled(row != maxIndex)
            self.deleteButton.setEnabled(True)
            self.changeButton.setEnabled(True)
            
            bookmark = self.bookmarks[row]
            self.fileEdit.setText(bookmark)
        
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add a new entry.
        """
        bookmark = self.fileEdit.text()
        if bookmark:
            bookmark = Utilities.toNativeSeparators(bookmark)
            itm = QListWidgetItem(bookmark, self.filesList)
            if not QFileInfo(bookmark).exists():
                itm.setBackground(QColor(Qt.red))
            self.fileEdit.clear()
            self.bookmarks.append(bookmark)
        row = self.filesList.currentRow()
        self.on_filesList_currentRowChanged(row)
        
    @pyqtSlot()
    def on_changeButton_clicked(self):
        """
        Private slot to change an entry.
        """
        row = self.filesList.currentRow()
        bookmark = self.fileEdit.text()
        bookmark = Utilities.toNativeSeparators(bookmark)
        self.bookmarks[row] = bookmark
        itm = self.filesList.item(row)
        itm.setText(bookmark)
        if not QFileInfo(bookmark).exists():
            itm.setBackground(QColor(Qt.red))
        else:
            itm.setBackground(QColor())
        
    @pyqtSlot()
    def on_deleteButton_clicked(self):
        """
        Private slot to delete the selected entry.
        """
        row = self.filesList.currentRow()
        itm = self.filesList.takeItem(row)
        del itm
        del self.bookmarks[row]
        row = self.filesList.currentRow()
        self.on_filesList_currentRowChanged(row)
        
    @pyqtSlot()
    def on_downButton_clicked(self):
        """
        Private slot to move an entry down in the list.
        """
        rows = self.filesList.count()
        row = self.filesList.currentRow()
        if row == rows - 1:
            # we're already at the end
            return
        
        self.__swap(row, row + 1)
        itm = self.filesList.takeItem(row)
        self.filesList.insertItem(row + 1, itm)
        self.filesList.setCurrentItem(itm)
        self.upButton.setEnabled(True)
        if row == rows - 2:
            self.downButton.setEnabled(False)
        else:
            self.downButton.setEnabled(True)
        
    @pyqtSlot()
    def on_upButton_clicked(self):
        """
        Private slot to move an entry up in the list.
        """
        row = self.filesList.currentRow()
        if row == 0:
            # we're already at the top
            return
        
        self.__swap(row - 1, row)
        itm = self.filesList.takeItem(row)
        self.filesList.insertItem(row - 1, itm)
        self.filesList.setCurrentItem(itm)
        if row == 1:
            self.upButton.setEnabled(False)
        else:
            self.upButton.setEnabled(True)
        self.downButton.setEnabled(True)
        
    @pyqtSlot()
    def on_fileButton_clicked(self):
        """
        Private slot to handle the file selection via a file selection dialog.
        """
        bookmark = E5FileDialog.getOpenFileName()
        if bookmark:
            bookmark = Utilities.toNativeSeparators(bookmark)
            self.fileEdit.setText(bookmark)
        
    def getBookmarkedFiles(self):
        """
        Public method to retrieve the tools list.
        
        @return a list of filenames (list of strings)
        """
        return self.bookmarks
        
    def __swap(self, itm1, itm2):
        """
        Private method used two swap two list entries given by their index.
        
        @param itm1 index of first entry (int)
        @param itm2 index of second entry (int)
        """
        tmp = self.bookmarks[itm1]
        self.bookmarks[itm1] = self.bookmarks[itm2]
        self.bookmarks[itm2] = tmp
