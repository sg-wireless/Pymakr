# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to browse the change lists.
"""

from __future__ import unicode_literals

import os
import sys

import pysvn

from PyQt5.QtCore import pyqtSlot, Qt, QMutexLocker
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QListWidgetItem, \
    QApplication

from .SvnDialogMixin import SvnDialogMixin

from .Ui_SvnChangeListsDialog import Ui_SvnChangeListsDialog


class SvnChangeListsDialog(QDialog, SvnDialogMixin, Ui_SvnChangeListsDialog):
    """
    Class implementing a dialog to browse the change lists.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super(SvnChangeListsDialog, self).__init__(parent)
        self.setupUi(self)
        SvnDialogMixin.__init__(self)
        self.setWindowFlags(Qt.Window)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.vcs = vcs
        
        self.client = self.vcs.getClient()
        self.client.callback_cancel = \
            self._clientCancelCallback
        self.client.callback_get_login = \
            self._clientLoginCallback
        self.client.callback_ssl_server_trust_prompt = \
            self._clientSslServerTrustPromptCallback
    
    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def on_changeLists_currentItemChanged(self, current, previous):
        """
        Private slot to handle the selection of a new item.
        
        @param current current item (QListWidgetItem)
        @param previous previous current item (QListWidgetItem)
        """
        self.filesList.clear()
        if current is not None:
            changelist = current.text()
            if changelist in self.changeListsDict:
                self.filesList.addItems(
                    sorted(self.changeListsDict[changelist]))
    
    def start(self, path):
        """
        Public slot to populate the data.
        
        @param path directory name to show change lists for (string)
        """
        self.changeListsDict = {}
        self.cancelled = False
        
        self.filesLabel.setText(
            self.tr("Files (relative to {0}):").format(path))
        
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        
        locker = QMutexLocker(self.vcs.vcsExecutionMutex)
        try:
            entries = self.client.get_changelist(
                path, depth=pysvn.depth.infinity)
            for entry in entries:
                file = entry[0]
                changelist = entry[1]
                if sys.version_info[0] == 2:
                    file = file.decode('utf-8')
                    changelist = changelist.decode('utf-8')
                if changelist not in self.changeListsDict:
                    self.changeListsDict[changelist] = []
                filename = file.replace(path + os.sep, "")
                if filename not in self.changeListsDict[changelist]:
                    self.changeListsDict[changelist].append(filename)
        except pysvn.ClientError as e:
            locker.unlock()
            self.__showError(e.args[0])
        self.__finish()
    
    def __finish(self):
        """
        Private slot called when the user pressed the button.
        """
        self.changeLists.addItems(sorted(self.changeListsDict.keys()))
        QApplication.restoreOverrideCursor()
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        if len(self.changeListsDict) == 0:
            self.changeLists.addItem(self.tr("No changelists found"))
            self.buttonBox.button(QDialogButtonBox.Close).setFocus(
                Qt.OtherFocusReason)
        else:
            self.changeLists.setCurrentRow(0)
            self.changeLists.setFocus(Qt.OtherFocusReason)
    
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.cancelled = True
            self.__finish()
