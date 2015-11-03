# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to remove sub-repositories.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog

from .Ui_HgRemoveSubrepositoriesDialog import Ui_HgRemoveSubrepositoriesDialog


class HgRemoveSubrepositoriesDialog(QDialog, Ui_HgRemoveSubrepositoriesDialog):
    """
    Class implementing a dialog to remove sub-repositories.
    """
    def __init__(self, subrepositories, parent=None):
        """
        Constructor
        
        @param subrepositories list of sub-repository entries (list of strings)
        @param parent reference to the parent widget (QWidget)
        """
        super(HgRemoveSubrepositoriesDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.subrepositories.addItems(subrepositories)
        self.__removed = []
    
    @pyqtSlot()
    def on_subrepositories_itemSelectionChanged(self):
        """
        Private slot handling the selection of entries.
        """
        self.removeButton.setEnabled(
            len(self.subrepositories.selectedItems()) > 0)
    
    @pyqtSlot()
    def on_removeButton_clicked(self):
        """
        Private slot handling the removal of the selected entries.
        """
        for itm in self.subrepositories.selectedItems():
            self.__removed.append(itm.text())
            row = self.subrepositories.row(itm)
            self.subrepositories.takeItem(row)
            del itm
    
    def getData(self):
        """
        Public method to retrieve the data.
        
        @return tuple giving the remaining sub-repositories, the removed ones
            and a flag indicating to delete the removed ones from disc (list
            of strings, list of strings, boolean)
        """
        return (
            [self.subrepositories.item(row).text()
             for row in range(self.subrepositories.count())],
            self.__removed,
            self.deleteCheckBox.isChecked()
        )
