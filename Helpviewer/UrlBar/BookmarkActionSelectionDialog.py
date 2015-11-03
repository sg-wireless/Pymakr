# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to select the action to be performed on the
bookmark.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog

from .Ui_BookmarkActionSelectionDialog import Ui_BookmarkActionSelectionDialog

import UI.PixmapCache


class BookmarkActionSelectionDialog(QDialog, Ui_BookmarkActionSelectionDialog):
    """
    Class implementing a dialog to select the action to be performed on
    the bookmark.
    """
    Undefined = -1
    AddBookmark = 0
    EditBookmark = 1
    AddSpeeddial = 2
    RemoveSpeeddial = 3
    
    def __init__(self, url, parent=None):
        """
        Constructor
        
        @param url URL to be worked on (QUrl)
        @param parent reference to the parent widget (QWidget)
        """
        super(BookmarkActionSelectionDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__action = self.Undefined
        
        self.icon.setPixmap(UI.PixmapCache.getPixmap("bookmark32.png"))
        
        import Helpviewer.HelpWindow
        
        if Helpviewer.HelpWindow.HelpWindow.bookmarksManager()\
           .bookmarkForUrl(url) is None:
            self.__bmAction = self.AddBookmark
            self.bookmarkPushButton.setText(self.tr("Add Bookmark"))
        else:
            self.__bmAction = self.EditBookmark
            self.bookmarkPushButton.setText(self.tr("Edit Bookmark"))
        
        if Helpviewer.HelpWindow.HelpWindow.speedDial().pageForUrl(url).url:
            self.__sdAction = self.RemoveSpeeddial
            self.speeddialPushButton.setText(
                self.tr("Remove from Speed Dial"))
        else:
            self.__sdAction = self.AddSpeeddial
            self.speeddialPushButton.setText(self.tr("Add to Speed Dial"))
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    @pyqtSlot()
    def on_bookmarkPushButton_clicked(self):
        """
        Private slot handling selection of a bookmark action.
        """
        self.__action = self.__bmAction
        self.accept()
    
    @pyqtSlot()
    def on_speeddialPushButton_clicked(self):
        """
        Private slot handling selection of a speed dial action.
        """
        self.__action = self.__sdAction
        self.accept()
    
    def getAction(self):
        """
        Public method to get the selected action.
        
        @return reference to the associated action
        """
        return self.__action
