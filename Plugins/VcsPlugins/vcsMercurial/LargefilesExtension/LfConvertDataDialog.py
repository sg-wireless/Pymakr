# -*- coding: utf-8 -*-

"""
Module implementing a dialog to enter the data for the repo conversion.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from E5Gui import E5FileDialog
from E5Gui.E5Completers import E5DirCompleter

from .Ui_LfConvertDataDialog import Ui_LfConvertDataDialog

from . import getDefaults

import Utilities
import UI.PixmapCache


class LfConvertDataDialog(QDialog, Ui_LfConvertDataDialog):
    """
    Class implementing a dialog to enter the data for the repo conversion.
    """
    def __init__(self, currentPath, mode, parent=None):
        """
        Constructor
        
        @param currentPath directory name of the current project (string)
        @param mode dialog mode (string, one of 'largefiles' or 'normal')
        @param parent reference to the parent widget (QWidget)
        """
        super(LfConvertDataDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.newProjectButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.__newProjectCompleter = E5DirCompleter(self.newProjectEdit)
        
        self.__defaults = getDefaults()
        self.__currentPath = Utilities.toNativeSeparators(currentPath)
        
        self.currentProjectLabel.setPath(currentPath)
        self.newProjectEdit.setText(os.path.dirname(currentPath))
        
        self.lfFileSizeSpinBox.setValue(self.__defaults["minsize"])
        self.lfFilePatternsEdit.setText(" ".join(self.__defaults["pattern"]))
        
        if mode == 'normal':
            self.lfFileSizeSpinBox.setEnabled(False)
            self.lfFilePatternsEdit.setEnabled(False)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    @pyqtSlot(str)
    def on_newProjectEdit_textChanged(self, txt):
        """
        Private slot to handle editing of the new project directory.
        
        @param txt new project directory name (string)
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            txt and Utilities.toNativeSeparators(txt) != os.path.dirname(
                self.__currentPath))
    
    @pyqtSlot()
    def on_newProjectButton_clicked(self):
        """
        Private slot to select the new project directory name via a directory
        selection dialog.
        """
        directory = Utilities.fromNativeSeparators(self.newProjectEdit.text())
        directory = E5FileDialog.getExistingDirectory(
            self,
            self.tr("New Project Directory"),
            directory,
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
        if directory:
            self.newProjectEdit.setText(
                Utilities.toNativeSeparators(directory))
    
    def getData(self):
        """
        Public method to retrieve the entered data.
        
        @return tuple containing the new project directory name (string),
            minimum file size (integer) and file patterns (list of string)
        """
        patterns = self.lfFilePatternsEdit.text().split()
        if set(patterns) == set(self.__defaults["pattern"]):
            patterns = []
        
        return (
            Utilities.toNativeSeparators(self.newProjectEdit.text()),
            self.lfFileSizeSpinBox.value(),
            patterns,
        )
