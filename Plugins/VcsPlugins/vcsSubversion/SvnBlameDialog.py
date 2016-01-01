# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the svn blame command.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import QTimer, QProcess, Qt, pyqtSlot
from PyQt5.QtWidgets import QHeaderView, QLineEdit, QDialog, \
    QDialogButtonBox, QTreeWidgetItem

from E5Gui import E5MessageBox

from .Ui_SvnBlameDialog import Ui_SvnBlameDialog

import Preferences


class SvnBlameDialog(QDialog, Ui_SvnBlameDialog):
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
        self.setWindowFlags(Qt.Window)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.vcs = vcs
        
        self.blameList.headerItem().setText(self.blameList.columnCount(), "")
        font = Preferences.getEditorOtherFonts("MonospacedFont")
        self.blameList.setFont(font)
        
        self.__ioEncoding = Preferences.getSystem("IOEncoding")
        
        self.process = QProcess()
        self.process.finished.connect(self.__procFinished)
        self.process.readyReadStandardOutput.connect(self.__readStdout)
        self.process.readyReadStandardError.connect(self.__readStderr)
        
    def closeEvent(self, e):
        """
        Protected slot implementing a close event handler.
        
        @param e close event (QCloseEvent)
        """
        if self.process is not None and \
           self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            QTimer.singleShot(2000, self.process.kill)
            self.process.waitForFinished(3000)
        
        e.accept()
        
    def start(self, fn):
        """
        Public slot to start the svn blame command.
        
        @param fn filename to show the blame for (string)
        """
        self.blameList.clear()
        self.errorGroup.hide()
        self.intercept = False
        self.activateWindow()
        self.lineno = 1
        
        dname, fname = self.vcs.splitPath(fn)
        
        self.process.kill()
        
        args = []
        args.append('blame')
        self.vcs.addArguments(args, self.vcs.options['global'])
        args.append(fname)
        
        self.process.setWorkingDirectory(dname)
        
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
        Private slot called when the process finished or the user pressed the
        button.
        """
        if self.process is not None and \
           self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            QTimer.singleShot(2000, self.process.kill)
            self.process.waitForFinished(3000)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        self.buttonBox.button(QDialogButtonBox.Close).setFocus(
            Qt.OtherFocusReason)
        
        self.inputGroup.setEnabled(False)
        self.inputGroup.hide()
        
        self.__resizeColumns()
        
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
        
    def __resizeColumns(self):
        """
        Private method to resize the list columns.
        """
        self.blameList.header().resizeSections(QHeaderView.ResizeToContents)
        
    def __generateItem(self, revision, author, text):
        """
        Private method to generate a blame item in the blame list.
        
        @param revision revision string (string)
        @param author author of the change (string)
        @param text line of text from the annotated file (string)
        """
        itm = QTreeWidgetItem(
            self.blameList,
            [revision, author, "{0:d}".format(self.lineno), text])
        self.lineno += 1
        itm.setTextAlignment(0, Qt.AlignRight)
        itm.setTextAlignment(2, Qt.AlignRight)
        
    def __readStdout(self):
        """
        Private slot to handle the readyReadStdout signal.
        
        It reads the output of the process, formats it and inserts it into
        the contents pane.
        """
        self.process.setReadChannel(QProcess.StandardOutput)
        
        while self.process.canReadLine():
            s = str(self.process.readLine(), self.__ioEncoding, 'replace')\
                .strip()
            rev, s = s.split(None, 1)
            try:
                author, text = s.split(' ', 1)
            except ValueError:
                author = s.strip()
                text = ""
            self.__generateItem(rev, author, text)
        
    def __readStderr(self):
        """
        Private slot to handle the readyReadStderr signal.
        
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
        super(SvnBlameDialog, self).keyPressEvent(evt)
