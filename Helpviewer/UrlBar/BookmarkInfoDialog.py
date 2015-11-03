# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show some bookmark info.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDialog

from .Ui_BookmarkInfoDialog import Ui_BookmarkInfoDialog

import UI.PixmapCache


class BookmarkInfoDialog(QDialog, Ui_BookmarkInfoDialog):
    """
    Class implementing a dialog to show some bookmark info.
    """
    def __init__(self, bookmark, parent=None):
        """
        Constructor
        
        @param bookmark reference to the bookmark to be shown (Bookmark)
        @param parent reference to the parent widget (QWidget)
        """
        super(BookmarkInfoDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__bookmark = bookmark
        
        self.icon.setPixmap(UI.PixmapCache.getPixmap("bookmark32.png"))
        
        font = QFont()
        font.setPointSize(font.pointSize() + 2)
        self.title.setFont(font)
        
        if bookmark is None:
            self.titleEdit.setEnabled(False)
        else:
            self.titleEdit.setText(bookmark.title)
            self.titleEdit.setFocus()
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    @pyqtSlot()
    def on_removeButton_clicked(self):
        """
        Private slot to remove the current bookmark.
        """
        import Helpviewer.HelpWindow
        Helpviewer.HelpWindow.HelpWindow.bookmarksManager()\
            .removeBookmark(self.__bookmark)
        self.close()
    
    def accept(self):
        """
        Public slot handling the acceptance of the dialog.
        """
        if self.__bookmark is not None and \
           self.titleEdit.text() != self.__bookmark.title:
            import Helpviewer.HelpWindow
            Helpviewer.HelpWindow.HelpWindow.bookmarksManager()\
                .setTitle(self.__bookmark, self.titleEdit.text())
        self.close()
