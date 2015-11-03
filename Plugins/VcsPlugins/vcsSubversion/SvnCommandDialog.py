# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Subversion command dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from E5Gui.E5Completers import E5DirCompleter
from E5Gui import E5FileDialog

from .Ui_SvnCommandDialog import Ui_SvnCommandDialog

import Utilities
import UI.PixmapCache


class SvnCommandDialog(QDialog, Ui_SvnCommandDialog):
    """
    Class implementing the Subversion command dialog.
    
    It implements a dialog that is used to enter an
    arbitrary subversion command. It asks the user to enter
    the commandline parameters and the working directory.
    """
    def __init__(self, argvList, wdList, ppath, parent=None):
        """
        Constructor
        
        @param argvList history list of commandline arguments (list of strings)
        @param wdList history list of working directories (list of strings)
        @param ppath pathname of the project directory (string)
        @param parent parent widget of this dialog (QWidget)
        """
        super(SvnCommandDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.dirButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.workdirCompleter = E5DirCompleter(self.workdirCombo)
        
        self.okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.setEnabled(False)
        
        self.commandCombo.clear()
        self.commandCombo.addItems(argvList)
        if len(argvList) > 0:
            self.commandCombo.setCurrentIndex(0)
        self.workdirCombo.clear()
        self.workdirCombo.addItems(wdList)
        if len(wdList) > 0:
            self.workdirCombo.setCurrentIndex(0)
        self.projectDirLabel.setText(ppath)
        
        # modify some what's this help texts
        t = self.commandCombo.whatsThis()
        if t:
            t += Utilities.getPercentReplacementHelp()
            self.commandCombo.setWhatsThis(t)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    @pyqtSlot()
    def on_dirButton_clicked(self):
        """
        Private method used to open a directory selection dialog.
        """
        cwd = self.workdirCombo.currentText()
        if not cwd:
            cwd = self.projectDirLabel.text()
        d = E5FileDialog.getExistingDirectory(
            self,
            self.tr("Working directory"),
            cwd,
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
        
        if d:
            self.workdirCombo.setEditText(Utilities.toNativeSeparators(d))
        
    def on_commandCombo_editTextChanged(self, text):
        """
        Private method used to enable/disable the OK-button.
        
        @param text ignored
        """
        self.okButton.setDisabled(self.commandCombo.currentText() == "")
    
    def getData(self):
        """
        Public method to retrieve the data entered into this dialog.
        
        @return a tuple of argv, workdir
        """
        return (self.commandCombo.currentText(),
                self.workdirCombo.currentText())
