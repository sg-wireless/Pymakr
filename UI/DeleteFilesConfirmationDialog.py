# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to confirm deletion of multiple files.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_DeleteFilesConfirmationDialog import Ui_DeleteFilesConfirmationDialog


class DeleteFilesConfirmationDialog(QDialog, Ui_DeleteFilesConfirmationDialog):
    """
    Class implementing a dialog to confirm deletion of multiple files.
    """
    def __init__(self, parent, caption, message, files):
        """
        Constructor
        
        @param parent parent of this dialog (QWidget)
        @param caption window title for the dialog (string)
        @param message message to be shown (string)
        @param files list of filenames to be shown (list of strings)
        """
        super(DeleteFilesConfirmationDialog, self).__init__(parent)
        self.setupUi(self)
        self.setModal(True)
        
        self.buttonBox.button(QDialogButtonBox.Yes).setAutoDefault(False)
        self.buttonBox.button(QDialogButtonBox.No).setDefault(True)
        self.buttonBox.button(QDialogButtonBox.No).setFocus()
        
        self.setWindowTitle(caption)
        self.message.setText(message)
        
        self.filesList.addItems(files)

    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Yes):
            self.accept()
        elif button == self.buttonBox.button(QDialogButtonBox.No):
            self.reject()
