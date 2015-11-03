# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing specialized table views.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QItemSelectionModel
from PyQt5.QtWidgets import QTableView


class E5TableView(QTableView):
    """
    Class implementing a table view supporting removal of entries.
    """
    def keyPressEvent(self, evt):
        """
        Protected method implementing special key handling.
        
        @param evt reference to the event (QKeyEvent)
        """
        if evt.key() in [Qt.Key_Delete, Qt.Key_Backspace] and \
           self.model() is not None:
            self.removeSelected()
            evt.setAccepted(True)
        else:
            super(E5TableView, self).keyPressEvent(evt)
    
    def removeSelected(self):
        """
        Public method to remove the selected entries.
        """
        if self.model() is None or self.selectionModel() is None:
            # no models available
            return
        
        row = 0
        selectedRows = self.selectionModel().selectedRows()
        for selectedRow in reversed(selectedRows):
            row = selectedRow.row()
            self.model().removeRow(row, self.rootIndex())
        
        idx = self.model().index(row, 0, self.rootIndex())
        if not idx.isValid():
            idx = self.model().index(row - 1, 0, self.rootIndex())
        self.selectionModel().select(
            idx,
            QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)
        self.setCurrentIndex(idx)
    
    def removeAll(self):
        """
        Public method to clear the view.
        """
        if self.model() is not None:
            self.model().removeRows(0, self.model().rowCount(self.rootIndex()),
                                    self.rootIndex())
