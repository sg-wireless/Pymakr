# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for a new dialog class file.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QDir, pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from E5Gui.E5Completers import E5DirCompleter
from E5Gui import E5FileDialog

from .Ui_NewDialogClassDialog import Ui_NewDialogClassDialog

import UI.PixmapCache


class NewDialogClassDialog(QDialog, Ui_NewDialogClassDialog):
    """
    Class implementing a dialog to ente the data for a new dialog class file.
    """
    def __init__(self, defaultClassName, defaultFile, defaultPath,
                 parent=None):
        """
        Constructor
        
        @param defaultClassName proposed name for the new class (string)
        @param defaultFile proposed name for the source file (string)
        @param defaultPath default path for the new file (string)
        @param parent parent widget if the dialog (QWidget)
        """
        super(NewDialogClassDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.pathButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.setEnabled(False)
        
        self.pathnameCompleter = E5DirCompleter(self.pathnameEdit)
        
        self.classnameEdit.setText(defaultClassName)
        self.filenameEdit.setText(defaultFile)
        self.pathnameEdit.setText(QDir.toNativeSeparators(defaultPath))
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    @pyqtSlot()
    def on_pathButton_clicked(self):
        """
        Private slot called to open a directory selection dialog.
        """
        path = E5FileDialog.getExistingDirectory(
            self,
            self.tr("Select source directory"),
            QDir.fromNativeSeparators(self.pathnameEdit.text()))
        if path:
            self.pathnameEdit.setText(QDir.toNativeSeparators(path))
        
    def __enableOkButton(self):
        """
        Private slot to set the enable state of theok button.
        """
        self.okButton.setEnabled(
            self.classnameEdit.text() != "" and
            self.filenameEdit.text() != "" and
            self.pathnameEdit.text() != "")
        
    def on_classnameEdit_textChanged(self, text):
        """
        Private slot called, when thext of the classname edit has changed.
        
        @param text changed text (string)
        """
        self.__enableOkButton()
        
    def on_filenameEdit_textChanged(self, text):
        """
        Private slot called, when thext of the filename edit has changed.
        
        @param text changed text (string)
        """
        self.__enableOkButton()
        
    def on_pathnameEdit_textChanged(self, text):
        """
        Private slot called, when thext of the pathname edit has changed.
        
        @param text changed text (string)
        """
        self.__enableOkButton()
        
    def getData(self):
        """
        Public method to retrieve the data entered into the dialog.
        
        @return tuple giving the classname (string) and the file name (string)
        """
        return self.classnameEdit.text(), \
            os.path.join(self.pathnameEdit.text(),
                         self.filenameEdit.text())
