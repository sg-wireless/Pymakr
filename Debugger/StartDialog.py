# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Start Program dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from E5Gui.E5Completers import E5DirCompleter
from E5Gui import E5FileDialog

import Utilities
import Preferences
import UI.PixmapCache


class StartDialog(QDialog):
    """
    Class implementing the Start Program dialog.
    
    It implements a dialog that is used to start an
    application for debugging. It asks the user to enter
    the commandline parameters, the working directory and
    whether exception reporting should be disabled.
    """
    def __init__(self, caption, argvList, wdList, envList, exceptions,
                 parent=None, type=0, modfuncList=None, tracePython=False,
                 autoClearShell=True, autoContinue=True, autoFork=False,
                 forkChild=False):
        """
        Constructor
        
        @param caption the caption to be displayed (string)
        @param argvList history list of commandline arguments (list of strings)
        @param wdList history list of working directories (list of strings)
        @param envList history list of environment settings (list of strings)
        @param exceptions exception reporting flag (boolean)
        @param parent parent widget of this dialog (QWidget)
        @param type type of the start dialog
                <ul>
                <li>0 = start debug dialog</li>
                <li>1 = start run dialog</li>
                <li>2 = start coverage dialog</li>
                <li>3 = start profile dialog</li>
                </ul>
        @keyparam modfuncList history list of module functions
            (list of strings)
        @keyparam tracePython flag indicating if the Python library should
            be traced as well (boolean)
        @keyparam autoClearShell flag indicating, that the interpreter window
            should be cleared automatically (boolean)
        @keyparam autoContinue flag indicating, that the debugger should not
            stop at the first executable line (boolean)
        @keyparam autoFork flag indicating the automatic fork mode (boolean)
        @keyparam forkChild flag indicating to debug the child after forking
            (boolean)
        """
        super(StartDialog, self).__init__(parent)
        self.setModal(True)
        
        self.type = type
        if type == 0:
            from .Ui_StartDebugDialog import Ui_StartDebugDialog
            self.ui = Ui_StartDebugDialog()
        elif type == 1:
            from .Ui_StartRunDialog import Ui_StartRunDialog
            self.ui = Ui_StartRunDialog()
        elif type == 2:
            from .Ui_StartCoverageDialog import Ui_StartCoverageDialog
            self.ui = Ui_StartCoverageDialog()
        elif type == 3:
            from .Ui_StartProfileDialog import Ui_StartProfileDialog
            self.ui = Ui_StartProfileDialog()
        self.ui.setupUi(self)
        self.ui.dirButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.clearButton = self.ui.buttonBox.addButton(
            self.tr("Clear Histories"), QDialogButtonBox.ActionRole)
        
        self.workdirCompleter = E5DirCompleter(self.ui.workdirCombo)
        
        self.setWindowTitle(caption)
        self.ui.cmdlineCombo.clear()
        self.ui.cmdlineCombo.addItems(argvList)
        if len(argvList) > 0:
            self.ui.cmdlineCombo.setCurrentIndex(0)
        self.ui.workdirCombo.clear()
        self.ui.workdirCombo.addItems(wdList)
        if len(wdList) > 0:
            self.ui.workdirCombo.setCurrentIndex(0)
        self.ui.environmentCombo.clear()
        self.ui.environmentCombo.addItems(envList)
        self.ui.exceptionCheckBox.setChecked(exceptions)
        self.ui.clearShellCheckBox.setChecked(autoClearShell)
        self.ui.consoleCheckBox.setEnabled(
            Preferences.getDebugger("ConsoleDbgCommand") != "")
        self.ui.consoleCheckBox.setChecked(False)
        
        if type == 0:        # start debug dialog
            self.ui.tracePythonCheckBox.setChecked(tracePython)
            self.ui.tracePythonCheckBox.show()
            self.ui.autoContinueCheckBox.setChecked(autoContinue)
            self.ui.forkModeCheckBox.setChecked(autoFork)
            self.ui.forkChildCheckBox.setChecked(forkChild)
        
        if type == 1:       # start run dialog
            self.ui.forkModeCheckBox.setChecked(autoFork)
            self.ui.forkChildCheckBox.setChecked(forkChild)
        
        if type == 3:       # start coverage or profile dialog
            self.ui.eraseCheckBox.setChecked(True)
        
        self.__clearHistoryLists = False
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    @pyqtSlot()
    def on_dirButton_clicked(self):
        """
        Private method used to open a directory selection dialog.
        """
        cwd = self.ui.workdirCombo.currentText()
        d = E5FileDialog.getExistingDirectory(
            self,
            self.tr("Working directory"),
            cwd,
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
            
        if d:
            self.ui.workdirCombo.setEditText(Utilities.toNativeSeparators(d))
        
    def on_modFuncCombo_editTextChanged(self):
        """
        Private slot to enable/disable the OK button.
        """
        self.ui.buttonBox.button(QDialogButtonBox.Ok).setDisabled(
            self.ui.modFuncCombo.currentText() == "")
        
    def getData(self):
        """
        Public method to retrieve the data entered into this dialog.
        
        @return a tuple of argv (string), workdir (string), environment
            (string), exceptions flag (boolean), clear interpreter flag
            (boolean), clear histories flag (boolean) and run in console
            flag (boolean)
        """
        cmdLine = self.ui.cmdlineCombo.currentText()
        workdir = self.ui.workdirCombo.currentText()
        environment = self.ui.environmentCombo.currentText()
        
        return (cmdLine,
                workdir,
                environment,
                self.ui.exceptionCheckBox.isChecked(),
                self.ui.clearShellCheckBox.isChecked(),
                self.__clearHistoryLists,
                self.ui.consoleCheckBox.isChecked())
        
    def getDebugData(self):
        """
        Public method to retrieve the debug related data entered into this
        dialog.
        
        @return a tuple of a flag indicating, if the Python library should be
            traced as well, a flag indicating, that the debugger should not
            stop at the first executable line (boolean), a flag indicating,
            that the debugger should fork automatically (boolean) and a flag
            indicating, that the debugger should debug the child process after
            forking automatically (boolean)
        """
        if self.type == 0:
            return (self.ui.tracePythonCheckBox.isChecked(),
                    self.ui.autoContinueCheckBox.isChecked(),
                    self.ui.forkModeCheckBox.isChecked(),
                    self.ui.forkChildCheckBox.isChecked())
        
    def getRunData(self):
        """
        Public method to retrieve the debug related data entered into this
        dialog.
        
        @return a tuple of a flag indicating, that the debugger should fork
            automatically (boolean) and a flag indicating, that the debugger
            should debug the child process after forking automatically
            (boolean)
        """
        if self.type == 1:
            return (self.ui.forkModeCheckBox.isChecked(),
                    self.ui.forkChildCheckBox.isChecked())
        
    def getCoverageData(self):
        """
        Public method to retrieve the coverage related data entered into this
        dialog.
        
        @return flag indicating erasure of coverage info (boolean)
        """
        if self.type == 2:
            return self.ui.eraseCheckBox.isChecked()
        
    def getProfilingData(self):
        """
        Public method to retrieve the profiling related data entered into this
        dialog.
        
        @return flag indicating erasure of profiling info (boolean)
        """
        if self.type == 3:
            return self.ui.eraseCheckBox.isChecked()
        
    def __clearHistories(self):
        """
        Private slot to clear the combo boxes lists and record a flag to
        clear the lists.
        """
        self.__clearHistoryLists = True
        
        cmdLine = self.ui.cmdlineCombo.currentText()
        workdir = self.ui.workdirCombo.currentText()
        environment = self.ui.environmentCombo.currentText()
        
        self.ui.cmdlineCombo.clear()
        self.ui.workdirCombo.clear()
        self.ui.environmentCombo.clear()
        
        self.ui.cmdlineCombo.addItem(cmdLine)
        self.ui.workdirCombo.addItem(workdir)
        self.ui.environmentCombo.addItem(environment)
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.clearButton:
            self.__clearHistories()
