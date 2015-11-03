# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter a series of revisions.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_LfRevisionsInputDialog import Ui_LfRevisionsInputDialog


class LfRevisionsInputDialog(QDialog, Ui_LfRevisionsInputDialog):
    """
    Class implementing a dialog to enter a series of revisions.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(LfRevisionsInputDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
    
    @pyqtSlot()
    def on_revisionsEdit_textChanged(self):
        """
        Private slot handling a change of revisions.
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            bool(self.revisionsEdit.toPlainText()))
    
    def getRevisions(self):
        """
        Public method to retrieve the entered revisions.
        
        @return list of revisions (list of string)
        """
        return self.revisionsEdit.toPlainText().splitlines()
