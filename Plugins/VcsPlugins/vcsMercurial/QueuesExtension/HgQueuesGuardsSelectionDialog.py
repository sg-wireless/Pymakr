# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to select a list of guards.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QListWidgetItem, \
    QAbstractItemView

from .Ui_HgQueuesGuardsSelectionDialog import Ui_HgQueuesGuardsSelectionDialog


class HgQueuesGuardsSelectionDialog(QDialog, Ui_HgQueuesGuardsSelectionDialog):
    """
    Class implementing a dialog to select a list of guards.
    """
    def __init__(self, guards, activeGuards=None, listOnly=False, parent=None):
        """
        Constructor
        
        @param guards list of guards to select from (list of strings)
        @keyparam activeGuards list of active guards (list of strings)
        @param listOnly flag indicating to only list the guards (boolean)
        @param parent reference to the parent widget (QWidget)
        """
        super(HgQueuesGuardsSelectionDialog, self).__init__(parent)
        self.setupUi(self)
        
        for guard in guards:
            itm = QListWidgetItem(guard, self.guardsList)
            if activeGuards is not None and guard in activeGuards:
                font = itm.font()
                font.setBold(True)
                itm.setFont(font)
        self.guardsList.sortItems()
        
        if listOnly:
            self.buttonBox.button(QDialogButtonBox.Cancel).hide()
            self.guardsList.setSelectionMode(QAbstractItemView.NoSelection)
            self.setWindowTitle(self.tr("Active Guards"))
    
    def getData(self):
        """
        Public method to retrieve the data.
        
        @return list of selected guards (list of strings)
        """
        guardsList = []
        
        for itm in self.guardsList.selectedItems():
            guardsList.append(itm.text())
        
        return guardsList
