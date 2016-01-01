# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to browse the change lists.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import pyqtSlot, Qt, QProcess, QRegExp, QTimer
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QListWidgetItem, \
    QLineEdit

from E5Gui import E5MessageBox

from .Ui_SvnChangeListsDialog import Ui_SvnChangeListsDialog

import Preferences


class SvnChangeListsDialog(QDialog, Ui_SvnChangeListsDialog):
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
        self.setWindowFlags(Qt.Window)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.vcs = vcs
        
        self.process = QProcess()
        self.process.finished.connect(self.__procFinished)
        self.process.readyReadStandardOutput.connect(self.__readStdout)
        self.process.readyReadStandardError.connect(self.__readStderr)
        
        self.rx_status = QRegExp(
            '(.{8,9})\\s+([0-9-]+)\\s+([0-9?]+)\\s+(\\S+)\\s+(.+)\\s*')
        # flags (8 or 9 anything), revision, changed rev, author, path
        self.rx_status2 = \
            QRegExp('(.{8,9})\\s+(.+)\\s*')
        # flags (8 or 9 anything), path
        self.rx_changelist = \
            QRegExp('--- \\S+ .([\\w\\s]+).:\\s+')
        # three dashes, Changelist (translated), quote,
        # changelist name, quote, :
    
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
        
        self.filesLabel.setText(
            self.tr("Files (relative to {0}):").format(path))
        
        self.errorGroup.hide()
        self.intercept = False
        
        self.path = path
        self.currentChangelist = ""
        
        args = []
        args.append('status')
        self.vcs.addArguments(args, self.vcs.options['global'])
        self.vcs.addArguments(args, self.vcs.options['status'])
        if '--verbose' not in self.vcs.options['global'] and \
           '--verbose' not in self.vcs.options['status']:
            args.append('--verbose')
        if isinstance(path, list):
            self.dname, fnames = self.vcs.splitPathList(path)
            self.vcs.addArguments(args, fnames)
        else:
            self.dname, fname = self.vcs.splitPath(path)
            args.append(fname)
        
        self.process.setWorkingDirectory(self.dname)
        
        self.process.start('svn', args)
        procStarted = self.process.waitForStarted(5000)
        if not procStarted:
            self.inputGroup.setEnabled(False)
            self.inputGroup.hide()
            E5MessageBox.critical(
                self,
                self.tr('Process Generation Error'),
                self.tr(
                    'The process {0} could not be started. '
                    'Ensure, that it is in the search path.'
                ).format('svn'))
        else:
            self.inputGroup.setEnabled(True)
            self.inputGroup.show()
    
    def __finish(self):
        """
        Private slot called when the process finished or the user pressed
        the button.
        """
        if self.process is not None and \
           self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            QTimer.singleShot(2000, self.process.kill)
            self.process.waitForFinished(3000)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.inputGroup.setEnabled(False)
        self.inputGroup.hide()
        
        if len(self.changeListsDict) == 0:
            self.changeLists.addItem(self.tr("No changelists found"))
            self.buttonBox.button(QDialogButtonBox.Close).setFocus(
                Qt.OtherFocusReason)
        else:
            self.changeLists.addItems(sorted(self.changeListsDict.keys()))
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
            self.__finish()
        
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.__finish()
        
    def __readStdout(self):
        """
        Private slot to handle the readyReadStandardOutput signal.
        
        It reads the output of the process, formats it and inserts it into
        the contents pane.
        """
        if self.process is not None:
            self.process.setReadChannel(QProcess.StandardOutput)
            
            while self.process.canReadLine():
                s = str(self.process.readLine(),
                        Preferences.getSystem("IOEncoding"),
                        'replace')
                if self.currentChangelist != "" and \
                        self.rx_status.exactMatch(s):
                    file = self.rx_status.cap(5).strip()
                    filename = file.replace(self.path + os.sep, "")
                    if filename not in \
                            self.changeListsDict[self.currentChangelist]:
                        self.changeListsDict[self.currentChangelist].append(
                            filename)
                elif self.currentChangelist != "" and \
                        self.rx_status2.exactMatch(s):
                    file = self.rx_status2.cap(2).strip()
                    filename = file.replace(self.path + os.sep, "")
                    if filename not in \
                            self.changeListsDict[self.currentChangelist]:
                        self.changeListsDict[self.currentChangelist].append(
                            filename)
                elif self.rx_changelist.exactMatch(s):
                    self.currentChangelist = self.rx_changelist.cap(1)
                    if self.currentChangelist not in self.changeListsDict:
                        self.changeListsDict[self.currentChangelist] = []
        
    def __readStderr(self):
        """
        Private slot to handle the readyReadStandardError signal.
        
        It reads the error output of the process and inserts it into the
        error pane.
        """
        if self.process is not None:
            self.errorGroup.show()
            s = str(self.process.readAllStandardError(),
                    Preferences.getSystem("IOEncoding"),
                    'replace')
            self.errors.insertPlainText(s)
            self.errors.ensureCursorVisible()
        
    def on_passwordCheckBox_toggled(self, isOn):
        """
        Private slot to handle the password checkbox toggled.
        
        @param isOn flag indicating the status of the check box (boolean)
        """
        if isOn:
            self.input.setEchoMode(QLineEdit.Password)
        else:
            self.input.setEchoMode(QLineEdit.Normal)
        
    @pyqtSlot()
    def on_sendButton_clicked(self):
        """
        Private slot to send the input to the subversion process.
        """
        input = self.input.text()
        input += os.linesep
        
        if self.passwordCheckBox.isChecked():
            self.errors.insertPlainText(os.linesep)
            self.errors.ensureCursorVisible()
        else:
            self.errors.insertPlainText(input)
            self.errors.ensureCursorVisible()
        
        self.process.write(input)
        
        self.passwordCheckBox.setChecked(False)
        self.input.clear()
        
    def on_input_returnPressed(self):
        """
        Private slot to handle the press of the return key in the input field.
        """
        self.intercept = True
        self.on_sendButton_clicked()
        
    def keyPressEvent(self, evt):
        """
        Protected slot to handle a key press event.
        
        @param evt the key press event (QKeyEvent)
        """
        if self.intercept:
            self.intercept = False
            evt.accept()
            return
        super(SvnChangeListsDialog, self).keyPressEvent(evt)
