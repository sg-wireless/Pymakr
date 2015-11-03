# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter data for the Mercurial export command.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot, QDir
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from E5Gui import E5FileDialog
from E5Gui.E5Completers import E5DirCompleter

from .Ui_HgExportDialog import Ui_HgExportDialog

import Utilities
import UI.PixmapCache


class HgExportDialog(QDialog, Ui_HgExportDialog):
    """
    Class documentation goes here.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(HgExportDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.directoryButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        
        self.__directoryCompleter = E5DirCompleter(self.directoryEdit)
        
        # set default values for directory and pattern
        self.patternEdit.setText("%b_%r_%h_%n_of_%N.diff")
        self.directoryEdit.setText(QDir.tempPath())
    
    def __updateOK(self):
        """
        Private slot to update the OK button.
        """
        enabled = True
        
        if self.directoryEdit.text() == "":
            enabled = False
        elif self.patternEdit.text() == "":
            enabled = False
        elif self.changesetsEdit.toPlainText() == "":
            enabled = False
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enabled)
    
    @pyqtSlot(str)
    def on_directoryEdit_textChanged(self, txt):
        """
        Private slot to react on changes of the export directory edit.
        
        @param txt contents of the line edit (string)
        """
        self.__updateOK()
    
    @pyqtSlot()
    def on_directoryButton_clicked(self):
        """
        Private slot called by pressing the export directory selection button.
        """
        dn = E5FileDialog.getExistingDirectory(
            self,
            self.tr("Export Patches"),
            self.directoryEdit.text(),
            E5FileDialog.Options(E5FileDialog.Option(0)))
        
        if dn:
            self.directoryEdit.setText(Utilities.toNativeSeparators(dn))
    
    @pyqtSlot(str)
    def on_patternEdit_textChanged(self, txt):
        """
        Private slot to react on changes of the export file name pattern edit.
        
        @param txt contents of the line edit (string)
        """
        self.__updateOK()
    
    @pyqtSlot()
    def on_changesetsEdit_textChanged(self):
        """
        Private slot to react on changes of the changesets edit.
        """
        self.__updateOK()
    
    def getParameters(self):
        """
        Public method to retrieve the export data.
        
        @return tuple naming the output file name, the list of revisions to
            export, and flags indicating to compare against the second parent,
            to treat all files as text, to omit dates in the diff headers and
            to use the git extended diff format (string, list of strings,
            boolean, boolean, boolean, boolean)
        """
        return (
            os.path.join(
                Utilities.toNativeSeparators(self.directoryEdit.text()),
                self.patternEdit.text()),
            self.changesetsEdit.toPlainText().splitlines(),
            self.switchParentCheckBox.isChecked(),
            self.textCheckBox.isChecked(),
            self.datesCheckBox.isChecked(),
            self.gitCheckBox.isChecked()
        )
