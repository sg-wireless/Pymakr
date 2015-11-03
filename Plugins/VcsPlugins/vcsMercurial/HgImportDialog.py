# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter data for the Mercurial import command.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, QDateTime
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from E5Gui import E5FileDialog
from E5Gui.E5Completers import E5FileCompleter

from .Ui_HgImportDialog import Ui_HgImportDialog

import Utilities
import UI.PixmapCache


class HgImportDialog(QDialog, Ui_HgImportDialog):
    """
    Class implementing a dialog to enter data for the Mercurial import command.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(HgImportDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.patchFileButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        
        self.__patchFileCompleter = E5FileCompleter(self.patchFileEdit)
        
        self.__initDateTime = QDateTime.currentDateTime()
        self.dateEdit.setDateTime(self.__initDateTime)
    
    def __updateOK(self):
        """
        Private slot to update the OK button.
        """
        enabled = True
        if self.patchFileEdit.text() == "":
            enabled = False
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enabled)
    
    @pyqtSlot(str)
    def on_patchFileEdit_textChanged(self, txt):
        """
        Private slot to react on changes of the patch file edit.
        
        @param txt contents of the line edit (string)
        """
        self.__updateOK()
    
    @pyqtSlot()
    def on_patchFileButton_clicked(self):
        """
        Private slot called by pressing the file selection button.
        """
        fn = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select patch file"),
            self.patchFileEdit.text(),
            self.tr("Patch Files (*.diff *.patch);;All Files (*)"))
        
        if fn:
            self.patchFileEdit.setText(Utilities.toNativeSeparators(fn))
    
    def getParameters(self):
        """
        Public method to retrieve the import data.
        
        @return tuple naming the patch file, a flag indicating to not commit,
            a commit message, a commit date, a commit user, a strip count and
            a flag indicating to enforce the import
            (string, boolean, string, string, string, integer, boolean)
        """
        if self.dateEdit.dateTime() != self.__initDateTime:
            date = self.dateEdit.dateTime().toString("yyyy-MM-dd hh:mm")
        else:
            date = ""
        
        return (self.patchFileEdit.text(), self.noCommitCheckBox.isChecked(),
                self.messageEdit.toPlainText(), date, self.userEdit.text(),
                self.stripSpinBox.value(), self.forceCheckBox.isChecked())
