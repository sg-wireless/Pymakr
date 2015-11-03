# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter data to be used for a fetch operation.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog

from .Ui_HgFetchDialog import Ui_HgFetchDialog

import Preferences


class HgFetchDialog(QDialog, Ui_HgFetchDialog):
    """
    Class implementing a dialog to enter data to be used for a fetch operation.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(HgFetchDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.recentCommitMessages = Preferences.toList(
            Preferences.Prefs.settings.value('Mercurial/Commits'))
        self.recentComboBox.clear()
        self.recentComboBox.addItem("")
        self.recentComboBox.addItems(self.recentCommitMessages)
    
    @pyqtSlot(str)
    def on_recentComboBox_activated(self, txt):
        """
        Private slot to select a commit message from recent ones.
        
        @param txt text of the selected entry (string)
        """
        if txt:
            self.messageEdit.setPlainText(txt)
    
    def getData(self):
        """
        Public method to get the data for the fetch operation.
        
        @return tuple with the commit message and a flag indicating to switch
            the merge order (string, boolean)
        """
        msg = self.messageEdit.toPlainText()
        if msg:
            if msg in self.recentCommitMessages:
                self.recentCommitMessages.remove(msg)
            self.recentCommitMessages.insert(0, msg)
            no = int(Preferences.Prefs.settings.value(
                'Mercurial/CommitMessages', 20))
            del self.recentCommitMessages[no:]
            Preferences.Prefs.settings.setValue(
                'Mercurial/Commits',
                self.recentCommitMessages)
        
        return msg, self.switchCheckBox.isChecked()
