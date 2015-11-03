# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for a copy operation.
"""

from __future__ import unicode_literals

import os.path

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from E5Gui.E5Completers import E5FileCompleter, E5DirCompleter
from E5Gui import E5FileDialog

from .Ui_SvnCopyDialog import Ui_SvnCopyDialog

import Utilities
import UI.PixmapCache


class SvnCopyDialog(QDialog, Ui_SvnCopyDialog):
    """
    Class implementing a dialog to enter the data for a copy or rename
    operation.
    """
    def __init__(self, source, parent=None, move=False, force=False):
        """
        Constructor
        
        @param source name of the source file/directory (string)
        @param parent parent widget (QWidget)
        @param move flag indicating a move operation (boolean)
        @param force flag indicating a forced operation (boolean)
        """
        super(SvnCopyDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.dirButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.source = source
        if os.path.isdir(self.source):
            self.targetCompleter = E5DirCompleter(self.targetEdit)
        else:
            self.targetCompleter = E5FileCompleter(self.targetEdit)
        
        if move:
            self.setWindowTitle(self.tr('Subversion Move'))
        else:
            self.forceCheckBox.setEnabled(False)
        self.forceCheckBox.setChecked(force)
        
        self.sourceEdit.setText(source)
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    def getData(self):
        """
        Public method to retrieve the copy data.
        
        @return the target name (string) and a flag indicating
            the operation should be enforced (boolean)
        """
        target = self.targetEdit.text()
        if not os.path.isabs(target):
            sourceDir = os.path.dirname(self.sourceEdit.text())
            target = os.path.join(sourceDir, target)
        return (Utilities.toNativeSeparators(target),
                self.forceCheckBox.isChecked())
        
    @pyqtSlot()
    def on_dirButton_clicked(self):
        """
        Private slot to handle the button press for selecting the target via a
        selection dialog.
        """
        if os.path.isdir(self.source):
            target = E5FileDialog.getExistingDirectory(
                None,
                self.tr("Select target"),
                self.targetEdit.text(),
                E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
        else:
            target = E5FileDialog.getSaveFileName(
                None,
                self.tr("Select target"),
                self.targetEdit.text(),
                "",
                E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        
        if target:
            self.targetEdit.setText(Utilities.toNativeSeparators(target))
    
    @pyqtSlot(str)
    def on_targetEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the target.
        
        @param txt contents of the target edit (string)
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            os.path.isabs(txt) or os.path.dirname(txt) == "")
