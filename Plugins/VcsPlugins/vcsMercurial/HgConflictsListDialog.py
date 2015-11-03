# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show a list of files which had or still have
conflicts.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot, Qt, QPoint, QProcess, QTimer
from PyQt5.QtGui import QWidget
from PyQt5.QtWidgets import QAbstractButton, QDialogButtonBox, QHeaderView, \
    QTreeWidgetItem, QLineEdit, QApplication

from E5Gui import E5MessageBox
from E5Gui.E5Application import e5App

from .Ui_HgConflictsListDialog import Ui_HgConflictsListDialog

import Utilities.MimeTypes


class HgConflictsListDialog(QWidget, Ui_HgConflictsListDialog):
    """
    Class implementing a dialog to show a list of files which had or still
    have conflicts.
    """
    StatusRole = Qt.UserRole + 1
    FilenameRole = Qt.UserRole + 2
    
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super(HgConflictsListDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__position = QPoint()
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.conflictsList.headerItem().setText(
            self.conflictsList.columnCount(), "")
        self.conflictsList.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.refreshButton = self.buttonBox.addButton(
            self.tr("&Refresh"), QDialogButtonBox.ActionRole)
        self.refreshButton.setToolTip(
            self.tr("Press to refresh the list of conflicts"))
        self.refreshButton.setEnabled(False)
        
        self.vcs = vcs
        self.project = e5App().getObject("Project")
        
        self.__hgClient = vcs.getClient()
        if self.__hgClient:
            self.process = None
        else:
            self.process = QProcess()
            self.process.finished.connect(self.__procFinished)
            self.process.readyReadStandardOutput.connect(self.__readStdout)
            self.process.readyReadStandardError.connect(self.__readStderr)
    
    def closeEvent(self, e):
        """
        Protected slot implementing a close event handler.
        
        @param e close event (QCloseEvent)
        """
        if self.__hgClient:
            if self.__hgClient.isExecuting():
                self.__hgClient.cancel()
        else:
            if self.process is not None and \
               self.process.state() != QProcess.NotRunning:
                self.process.terminate()
                QTimer.singleShot(2000, self.process.kill)
                self.process.waitForFinished(3000)
        
        self.__position = self.pos()
        
        e.accept()
    
    def show(self):
        """
        Public slot to show the dialog.
        """
        if not self.__position.isNull():
            self.move(self.__position)
        
        super(HgConflictsListDialog, self).show()
    
    def start(self, path):
        """
        Public slot to start the tags command.
        
        @param path name of directory to list conflicts for (string)
        """
        self.errorGroup.hide()
        QApplication.processEvents()
            
        self.intercept = False
        dname, fname = self.vcs.splitPath(path)
        
        # find the root of the repo
        self.__repodir = dname
        while not os.path.isdir(
                os.path.join(self.__repodir, self.vcs.adminDir)):
            self.__repodir = os.path.dirname(self.__repodir)
            if os.path.splitdrive(self.__repodir)[1] == os.sep:
                return
        
        self.activateWindow()
        self.raise_()
        
        self.conflictsList.clear()
        self.__started = True
        self.__getEntries()
    
    def __getEntries(self):
        """
        Private method to get the conflict entries.
        """
        args = self.vcs.initCommand("resolve")
        args.append('--list')
        
        if self.__hgClient:
            self.inputGroup.setEnabled(False)
            self.inputGroup.hide()
            
            out, err = self.__hgClient.runcommand(args)
            if err:
                self.__showError(err)
            if out:
                for line in out.splitlines():
                    self.__processOutputLine(line)
                    if self.__hgClient.wasCanceled():
                        break
            self.__finish()
        else:
            self.process.kill()
            self.process.setWorkingDirectory(self.__repodir)
            
            self.process.start('hg', args)
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
                    ).format('hg'))
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
        
        QApplication.restoreOverrideCursor()
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.inputGroup.setEnabled(False)
        self.inputGroup.hide()
        self.refreshButton.setEnabled(True)
        
        self.__resizeColumns()
        self.__resort()
        self.on_conflictsList_itemSelectionChanged()
    
    @pyqtSlot(QAbstractButton)
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            if self.__hgClient:
                self.__hgClient.cancel()
            else:
                self.__finish()
        elif button == self.refreshButton:
            self.on_refreshButton_clicked()
    
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.__finish()
    
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.conflictsList.sortItems(
            self.conflictsList.sortColumn(),
            self.conflictsList.header().sortIndicatorOrder())
    
    def __resizeColumns(self):
        """
        Private method to resize the list columns.
        """
        self.conflictsList.header().resizeSections(
            QHeaderView.ResizeToContents)
        self.conflictsList.header().setStretchLastSection(True)
    
    def __generateItem(self, status, name):
        """
        Private method to generate a tag item in the tag list.
        
        @param status status of the file (string)
        @param name name of the file (string)
        """
        itm = QTreeWidgetItem(self.conflictsList)
        if status == "U":
            itm.setText(0, self.tr("Unresolved"))
        elif status == "R":
            itm.setText(0, self.tr("Resolved"))
        else:
            itm.setText(0, self.tr("Unknown Status"))
        itm.setText(1, name)
        
        itm.setData(0, self.StatusRole, status)
        itm.setData(0, self.FilenameRole, self.project.getAbsolutePath(name))
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStdout signal.
        
        It reads the output of the process, formats it and inserts it into
        the contents pane.
        """
        self.process.setReadChannel(QProcess.StandardOutput)
        
        while self.process.canReadLine():
            s = str(self.process.readLine(), self.vcs.getEncoding(),
                    'replace').strip()
            self.__processOutputLine(s)
    
    def __processOutputLine(self, line):
        """
        Private method to process the lines of output.
        
        @param line output line to be processed (string)
        """
        status, filename = line.strip().split(None, 1)
        self.__generateItem(status, filename)
    
    @pyqtSlot()
    def on_refreshButton_clicked(self):
        """
        Private slot to refresh the log.
        """
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.inputGroup.setEnabled(True)
        self.inputGroup.show()
        self.refreshButton.setEnabled(False)
        self.start(self.__repodir)
    
    def __readStderr(self):
        """
        Private slot to handle the readyReadStderr signal.
        
        It reads the error output of the process and inserts it into the
        error pane.
        """
        if self.process is not None:
            s = str(self.process.readAllStandardError(),
                    self.vcs.getEncoding(), 'replace')
            self.__showError(s)
    
    def __showError(self, out):
        """
        Private slot to show some error.
        
        @param out error to be shown (string)
        """
        self.errorGroup.show()
        self.errors.insertPlainText(out)
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
        super(HgConflictsListDialog, self).keyPressEvent(evt)
    
    @pyqtSlot(QTreeWidgetItem, int)
    def on_conflictsList_itemDoubleClicked(self, item, column):
        """
        Private slot to open the double clicked entry.
        
        @param item reference to the double clicked item (QTreeWidgetItem)
        @param column column that was double clicked (integer)
        """
        self.on_editButton_clicked()
    
    @pyqtSlot()
    def on_conflictsList_itemSelectionChanged(self):
        """
        Private slot to handle a change of selected conflict entries.
        """
        selectedCount = len(self.conflictsList.selectedItems())
        unresolved = resolved = 0
        for itm in self.conflictsList.selectedItems():
            status = itm.data(0, self.StatusRole)
            if status == "U":
                unresolved += 1
            elif status == "R":
                resolved += 1
        
        self.resolvedButton.setEnabled(unresolved > 0)
        self.unresolvedButton.setEnabled(resolved > 0)
        self.reMergeButton.setEnabled(unresolved > 0)
        self.editButton.setEnabled(
            selectedCount == 1 and
            Utilities.MimeTypes.isTextFile(
                self.conflictsList.selectedItems()[0].data(
                    0, self.FilenameRole)))
    
    @pyqtSlot()
    def on_resolvedButton_clicked(self):
        """
        Private slot to mark the selected entries as resolved.
        """
        names = [
            itm.data(0, self.FilenameRole)
            for itm in self.conflictsList.selectedItems()
            if itm.data(0, self.StatusRole) == "U"
        ]
        if names:
            self.vcs.hgResolved(names)
            self.on_refreshButton_clicked()
    
    @pyqtSlot()
    def on_unresolvedButton_clicked(self):
        """
        Private slot to mark the selected entries as unresolved.
        """
        names = [
            itm.data(0, self.FilenameRole)
            for itm in self.conflictsList.selectedItems()
            if itm.data(0, self.StatusRole) == "R"
        ]
        if names:
            self.vcs.hgResolved(names, unresolve=True)
            self.on_refreshButton_clicked()
    
    @pyqtSlot()
    def on_reMergeButton_clicked(self):
        """
        Private slot to re-merge the selected entries.
        """
        names = [
            itm.data(0, self.FilenameRole)
            for itm in self.conflictsList.selectedItems()
            if itm.data(0, self.StatusRole) == "U"
        ]
        if names:
            self.vcs.hgReMerge(names)
    
    @pyqtSlot()
    def on_editButton_clicked(self):
        """
        Private slot to open the selected file in an editor.
        """
        itm = self.conflictsList.selectedItems()[0]
        filename = itm.data(0, self.FilenameRole)
        if Utilities.MimeTypes.isTextFile(filename):
            e5App().getObject("ViewManager").getEditor(filename)
