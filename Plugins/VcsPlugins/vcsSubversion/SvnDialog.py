# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog starting a process and showing its output.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import QTimer, QProcess, pyqtSlot, Qt, QProcessEnvironment
from PyQt5.QtWidgets import QLineEdit, QDialog, QDialogButtonBox

from E5Gui import E5MessageBox

from .Ui_SvnDialog import Ui_SvnDialog

import Preferences


class SvnDialog(QDialog, Ui_SvnDialog):
    """
    Class implementing a dialog starting a process and showing its output.
    
    It starts a QProcess and displays a dialog that
    shows the output of the process. The dialog is modal,
    which causes a synchronized execution of the process.
    """
    def __init__(self, text, parent=None):
        """
        Constructor
        
        @param text text to be shown by the label (string)
        @param parent parent widget (QWidget)
        """
        super(SvnDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.proc = None
        self.username = ''
        self.password = ''
        
        self.outputGroup.setTitle(text)
        
    def __finish(self):
        """
        Private slot called when the process finished or the user pressed the
        button.
        """
        if self.proc is not None and \
           self.proc.state() != QProcess.NotRunning:
            self.proc.terminate()
            QTimer.singleShot(2000, self.proc.kill)
            self.proc.waitForFinished(3000)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.inputGroup.setEnabled(False)
        self.inputGroup.hide()
        
        self.proc = None
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        self.buttonBox.button(QDialogButtonBox.Close).setFocus(
            Qt.OtherFocusReason)
        
        if Preferences.getVCS("AutoClose") and \
           self.normal and \
           self.errors.toPlainText() == "":
            self.accept()
        
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
        self.normal = (exitStatus == QProcess.NormalExit) and (exitCode == 0)
        self.__finish()
        
    def startProcess(self, args, workingDir=None, setLanguage=False):
        """
        Public slot used to start the process.
        
        @param args list of arguments for the process (list of strings)
        @param workingDir working directory for the process (string)
        @param setLanguage flag indicating to set the language to "C" (boolean)
        @return flag indicating a successful start of the process
        """
        self.errorGroup.hide()
        self.normal = False
        self.intercept = False
        
        self.__hasAddOrDelete = False
        
        self.proc = QProcess()
        if setLanguage:
            env = QProcessEnvironment.systemEnvironment()
            env.insert("LANG", "C")
            self.proc.setProcessEnvironment(env)
        nargs = []
        lastWasPwd = False
        for arg in args:
            if lastWasPwd:
                lastWasPwd = True
                continue
            nargs.append(arg)
            if arg == '--password':
                lastWasPwd = True
                nargs.append('*****')
            
        self.resultbox.append(' '.join(nargs))
        self.resultbox.append('')
        
        self.proc.finished.connect(self.__procFinished)
        self.proc.readyReadStandardOutput.connect(self.__readStdout)
        self.proc.readyReadStandardError.connect(self.__readStderr)
        
        if workingDir:
            self.proc.setWorkingDirectory(workingDir)
        self.proc.start('svn', args)
        procStarted = self.proc.waitForStarted(5000)
        if not procStarted:
            self.buttonBox.setFocus()
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
        return procStarted
        
    def normalExit(self):
        """
        Public method to check for a normal process termination.
        
        @return flag indicating normal process termination (boolean)
        """
        return self.normal
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStdout signal.
        
        It reads the output of the process, formats it and inserts it into
        the contents pane.
        """
        if self.proc is not None:
            s = str(self.proc.readAllStandardOutput(),
                    Preferences.getSystem("IOEncoding"),
                    'replace')
            self.resultbox.insertPlainText(s)
            self.resultbox.ensureCursorVisible()
            if not self.__hasAddOrDelete and len(s) > 0:
                # check the output
                for l in s.split(os.linesep):
                    if '.e4p' in l:
                        self.__hasAddOrDelete = True
                        break
                    if l and l[0:2].strip() in ['A', 'D']:
                        self.__hasAddOrDelete = True
                        break
        
    def __readStderr(self):
        """
        Private slot to handle the readyReadStderr signal.
        
        It reads the error output of the process and inserts it into the
        error pane.
        """
        if self.proc is not None:
            self.errorGroup.show()
            s = str(self.proc.readAllStandardError(),
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
        
        self.proc.write(input)
        
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
        super(SvnDialog, self).keyPressEvent(evt)
        
    def hasAddOrDelete(self):
        """
        Public method to check, if the last action contained an add or delete.
        
        @return flag indicating the presence of an add or delete (boolean)
        """
        return self.__hasAddOrDelete
