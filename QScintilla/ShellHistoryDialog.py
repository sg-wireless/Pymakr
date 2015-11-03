# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the shell history dialog.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot, QItemSelectionModel
from PyQt5.QtWidgets import QListWidgetItem, QDialog

from .Ui_ShellHistoryDialog import Ui_ShellHistoryDialog


class ShellHistoryDialog(QDialog, Ui_ShellHistoryDialog):
    """
    Class implementing the shell history dialog.
    """
    def __init__(self, history, vm, shell):
        """
        Constructor
        
        @param history reference to the current shell history (list of strings)
        @param vm reference to the viewmanager object
        @param shell reference to the shell object
        """
        super(ShellHistoryDialog, self).__init__(shell)
        self.setupUi(self)
        
        self.historyList.addItems(history)
        self.historyList.setCurrentRow(
            self.historyList.count() - 1, QItemSelectionModel.Clear)
        self.historyList.scrollToItem(self.historyList.currentItem())
        
        self.vm = vm
        self.shell = shell
    
    @pyqtSlot()
    def on_historyList_itemSelectionChanged(self):
        """
        Private slot to handle a change of the selection.
        """
        selected = len(self.historyList.selectedItems()) > 0
        self.copyButton.setEnabled(selected and
                                   self.vm.activeWindow() is not None)
        self.deleteButton.setEnabled(selected)
        self.executeButton.setEnabled(selected)
    
    @pyqtSlot(QListWidgetItem)
    def on_historyList_itemDoubleClicked(self, item):
        """
        Private slot to handle a double click of an item.
        
        @param item reference to the item that was double clicked
            (QListWidgetItem)
        """
        self.on_executeButton_clicked()
    
    @pyqtSlot()
    def on_deleteButton_clicked(self):
        """
        Private slot to delete the selected entries from the history.
        """
        for itm in self.historyList.selectedItems():
            ditm = self.historyList.takeItem(self.historyList.row(itm))
            del ditm
        self.historyList.scrollToItem(self.historyList.currentItem())
        self.historyList.setFocus()
    
    @pyqtSlot()
    def on_copyButton_clicked(self):
        """
        Private slot to copy the selected entries to the current editor.
        """
        aw = self.vm.activeWindow()
        if aw is not None:
            lines = []
            for index in range(self.historyList.count()):
                # selectedItems() doesn't seem to preserve the order
                itm = self.historyList.item(index)
                if itm.isSelected():
                    lines.append(itm.text())
            eol = aw.getLineSeparator()
            txt = eol.join(lines) + eol
            aw.insert(txt)
        self.historyList.setFocus()
    
    @pyqtSlot()
    def on_executeButton_clicked(self):
        """
        Private slot to execute the selected entries in the shell.
        """
        lines = []
        for index in range(self.historyList.count()):
            # selectedItems() doesn't seem to preserve the order
            itm = self.historyList.item(index)
            if itm.isSelected():
                lines.append(itm.text())
        cmds = os.linesep.join(lines) + os.linesep
        self.shell.executeLines(cmds)
        
        # reload the list because shell modified it
        self.on_reloadButton_clicked()
    
    @pyqtSlot()
    def on_reloadButton_clicked(self):
        """
        Private slot to reload the history.
        """
        history = self.shell.getHistory(None)
        self.historyList.clear()
        self.historyList.addItems(history)
        self.historyList.setCurrentRow(
            self.historyList.count() - 1, QItemSelectionModel.Clear)
        self.historyList.scrollToItem(self.historyList.currentItem())
        
    def getHistory(self):
        """
        Public method to retrieve the history from the dialog.
        
        @return list of history entries (list of strings)
        """
        history = []
        for index in range(self.historyList.count()):
            history.append(self.historyList.item(index).text())
        return history
