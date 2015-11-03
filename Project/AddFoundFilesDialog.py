# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the found files to the user.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_AddFoundFilesDialog import Ui_AddFoundFilesDialog


class AddFoundFilesDialog(QDialog, Ui_AddFoundFilesDialog):
    """
    Class implementing a dialog to show the found files to the user.
    
    The found files are displayed in a listview. Pressing the 'Add All' button
    adds all files to the current project, the 'Add Selected' button adds only
    the selected files and the 'Cancel' button cancels the operation.
    """
    def __init__(self, files, parent=None, name=None):
        """
        Constructor
        
        @param files list of files, that have been found for addition
            (list of strings)
        @param parent parent widget of this dialog (QWidget)
        @param name name of this dialog (string)
        """
        super(AddFoundFilesDialog, self).__init__(parent)
        if name:
            self.setObjectName(name)
        self.setupUi(self)
        
        self.addAllButton = self.buttonBox.addButton(
            self.tr("Add All"), QDialogButtonBox.AcceptRole)
        self.addAllButton.setToolTip(self.tr("Add all files."))
        self.addSelectedButton = self.buttonBox.addButton(
            self.tr("Add Selected"), QDialogButtonBox.AcceptRole)
        self.addSelectedButton.setToolTip(
            self.tr("Add selected files only."))
        
        self.fileList.addItems(files)
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.addAllButton:
            self.on_addAllButton_clicked()
        elif button == self.addSelectedButton:
            self.on_addSelectedButton_clicked()
        
    @pyqtSlot()
    def on_addAllButton_clicked(self):
        """
        Private slot to handle the 'Add All' button press.
        
        Always returns the value 1 (integer).
        """
        self.done(1)
        
    @pyqtSlot()
    def on_addSelectedButton_clicked(self):
        """
        Private slot to handle the 'Add Selected' button press.
        
        Always returns the value 2 (integer).
        """
        self.done(2)
        
    def getSelection(self):
        """
        Public method to return the selected items.
        
        @return list of selected files (list of strings)
        """
        list_ = []
        for itm in self.fileList.selectedItems():
            list_.append(itm.text())
        return list_
