# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the svn blame command.
"""

from __future__ import unicode_literals

import os
import sys

import pysvn

from PyQt5.QtCore import QMutexLocker, Qt
from PyQt5.QtWidgets import QHeaderView, QDialog, QDialogButtonBox, \
    QTreeWidgetItem

from .SvnDialogMixin import SvnDialogMixin
from .Ui_SvnBlameDialog import Ui_SvnBlameDialog

import Preferences


class SvnBlameDialog(QDialog, SvnDialogMixin, Ui_SvnBlameDialog):
    """
    Class implementing a dialog to show the output of the svn blame command.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super(SvnBlameDialog, self).__init__(parent)
        self.setupUi(self)
        SvnDialogMixin.__init__(self)
        self.setWindowFlags(Qt.Window)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.vcs = vcs
        
        self.blameList.headerItem().setText(self.blameList.columnCount(), "")
        font = Preferences.getEditorOtherFonts("MonospacedFont")
        self.blameList.setFont(font)
        
        self.client = self.vcs.getClient()
        self.client.callback_cancel = \
            self._clientCancelCallback
        self.client.callback_get_login = \
            self._clientLoginCallback
        self.client.callback_ssl_server_trust_prompt = \
            self._clientSslServerTrustPromptCallback
        
    def start(self, fn):
        """
        Public slot to start the svn blame command.
        
        @param fn filename to show the blame for (string)
        """
        self.blameList.clear()
        self.errorGroup.hide()
        self.activateWindow()
        
        dname, fname = self.vcs.splitPath(fn)
        
        locker = QMutexLocker(self.vcs.vcsExecutionMutex)
        cwd = os.getcwd()
        os.chdir(dname)
        try:
            annotations = self.client.annotate(fname)
            locker.unlock()
            for annotation in annotations:
                author = annotation["author"]
                line = annotation["line"]
                if sys.version_info[0] == 2:
                    author = author.decode('utf-8')
                    line = line.decode('utf-8')
                self.__generateItem(
                    annotation["revision"].number, author,
                    annotation["number"] + 1, line)
        except pysvn.ClientError as e:
            locker.unlock()
            self.__showError(e.args[0] + '\n')
        self.__finish()
        os.chdir(cwd)
        
    def __finish(self):
        """
        Private slot called when the process finished or the user pressed the
        button.
        """
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.__resizeColumns()
        
        self._cancel()
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.__finish()
        
    def __resizeColumns(self):
        """
        Private method to resize the list columns.
        """
        self.blameList.header().resizeSections(QHeaderView.ResizeToContents)
        
    def __generateItem(self, revision, author, lineno, text):
        """
        Private method to generate a blame item in the blame list.
        
        @param revision revision string (string)
        @param author author of the change (string)
        @param lineno linenumber (string)
        @param text line of text from the annotated file (string)
        """
        itm = QTreeWidgetItem(
            self.blameList,
            ["{0:d}".format(revision), author, "{0:d}".format(lineno), text])
        itm.setTextAlignment(0, Qt.AlignRight)
        itm.setTextAlignment(2, Qt.AlignRight)
        
    def __showError(self, msg):
        """
        Private slot to show an error message.
        
        @param msg error message to show (string)
        """
        self.errorGroup.show()
        self.errors.insertPlainText(msg)
        self.errors.ensureCursorVisible()
