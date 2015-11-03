# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the commit message.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QDialogButtonBox

from .Ui_HgCommitDialog import Ui_HgCommitDialog

import Preferences


class HgCommitDialog(QWidget, Ui_HgCommitDialog):
    """
    Class implementing a dialog to enter the commit message.
    
    @signal accepted() emitted, if the dialog was accepted
    @signal rejected() emitted, if the dialog was rejected
    """
    accepted = pyqtSignal()
    rejected = pyqtSignal()
    
    def __init__(self, vcs, msg, mq, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param msg initial message (string)
        @param mq flag indicating a queue commit (boolean)
        @param parent parent widget (QWidget)
        """
        super(HgCommitDialog, self).__init__(parent, Qt.WindowFlags(Qt.Window))
        self.setupUi(self)
        
        self.logEdit.setPlainText(msg)
        
        if mq:
            self.amendCheckBox.setVisible(False)
            self.subrepoCheckBox.setVisible(False)
        else:
            if vcs.version < (2, 2):
                self.amendCheckBox.setEnabled(False)
            
            self.subrepoCheckBox.setVisible(vcs.hasSubrepositories())
    
    def showEvent(self, evt):
        """
        Protected method called when the dialog is about to be shown.
        
        @param evt the event (QShowEvent)
        """
        self.recentCommitMessages = Preferences.toList(
            Preferences.Prefs.settings.value('Mercurial/Commits'))
        self.recentComboBox.clear()
        self.recentComboBox.addItem("")
        self.recentComboBox.addItems(self.recentCommitMessages)
    
    def logMessage(self):
        """
        Public method to retrieve the log message.
        
        @return the log message (string)
        """
        msg = self.logEdit.toPlainText()
        if msg:
            if msg in self.recentCommitMessages:
                self.recentCommitMessages.remove(msg)
            self.recentCommitMessages.insert(0, msg)
            no = int(Preferences.Prefs.settings.value(
                'Mercurial/CommitMessages', 20))
            del self.recentCommitMessages[no:]
            Preferences.Prefs.settings.setValue(
                'Mercurial/Commits', self.recentCommitMessages)
        return msg
    
    def amend(self):
        """
        Public method to retrieve the state of the amend flag.
        
        @return state of the amend flag (boolean)
        """
        return self.amendCheckBox.isChecked()
    
    def commitSubrepositories(self):
        """
        Public method to retrieve the state of the commit sub-repositories
        flag.
        
        @return state of the sub-repositories flag (boolean)
        """
        return self.subrepoCheckBox.isChecked()
    
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.logEdit.clear()
    
    def on_buttonBox_accepted(self):
        """
        Private slot called by the buttonBox accepted signal.
        """
        self.close()
        self.accepted.emit()
    
    def on_buttonBox_rejected(self):
        """
        Private slot called by the buttonBox rejected signal.
        """
        self.close()
        self.rejected.emit()
    
    @pyqtSlot(str)
    def on_recentComboBox_activated(self, txt):
        """
        Private slot to select a commit message from recent ones.
        
        @param txt text of the selected entry (string)
        """
        if txt:
            self.logEdit.setPlainText(txt)
