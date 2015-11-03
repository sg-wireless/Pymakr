# -*- coding: utf-8 -*-

"""
Module implementing a dialog to select multiple shelve names.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_HgShelvesSelectionDialog import Ui_HgShelvesSelectionDialog


class HgShelvesSelectionDialog(QDialog, Ui_HgShelvesSelectionDialog):
    """
    Class implementing a dialog to select multiple shelve names.
    """
    def __init__(self, message, shelveNames, parent=None):
        """
        Constructor
        
        @param message message to be shown (string)
        @param shelveNames list of shelve names (list of string)
        @param parent reference to the parent widget (QWidget)
        """
        super(HgShelvesSelectionDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.message.setText(message)
        self.shelvesList.addItems(shelveNames)
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
    
    @pyqtSlot()
    def on_shelvesList_itemSelectionChanged(self):
        """
        Private slot to enabled the OK button if items have been selected.
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            len(self.shelvesList.selectedItems()) > 0)
    
    def getSelectedShelves(self):
        """
        Public method to retrieve the selected shelve names.
        
        @return selected shelve names (list of string)
        """
        names = []
        for itm in self.shelvesList.selectedItems():
            names.append(itm.text())
        
        return names
