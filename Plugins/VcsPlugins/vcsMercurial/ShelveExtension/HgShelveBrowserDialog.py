# -*- coding: utf-8 -*-

"""
Module implementing Mercurial shelve browser dialog.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import pyqtSlot, Qt, QPoint, QProcess, QTimer
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QTreeWidgetItem, \
    QAbstractButton, QMenu, QHeaderView, QApplication, QLineEdit

from E5Gui import E5MessageBox

from .Ui_HgShelveBrowserDialog import Ui_HgShelveBrowserDialog


class HgShelveBrowserDialog(QWidget, Ui_HgShelveBrowserDialog):
    """
    Class implementing Mercurial shelve browser dialog.
    """
    NameColumn = 0
    AgeColumn = 1
    MessageColumn = 2
    
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super(HgShelveBrowserDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.__position = QPoint()
        
        self.__fileStatisticsRole = Qt.UserRole
        self.__totalStatisticsRole = Qt.UserRole + 1
        
        self.shelveList.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.refreshButton = self.buttonBox.addButton(
            self.tr("&Refresh"), QDialogButtonBox.ActionRole)
        self.refreshButton.setToolTip(
            self.tr("Press to refresh the list of shelves"))
        self.refreshButton.setEnabled(False)
        
        self.vcs = vcs
        self.__hgClient = vcs.getClient()
        self.__resetUI()
        
        if self.__hgClient:
            self.process = None
        else:
            self.process = QProcess()
            self.process.finished.connect(self.__procFinished)
            self.process.readyReadStandardOutput.connect(self.__readStdout)
            self.process.readyReadStandardError.connect(self.__readStderr)
        
        self.__contextMenu = QMenu()
        self.__unshelveAct = self.__contextMenu.addAction(
            self.tr("Restore selected shelve"), self.__unshelve)
        self.__deleteAct = self.__contextMenu.addAction(
            self.tr("Delete selected shelves"), self.__deleteShelves)
        self.__contextMenu.addAction(
            self.tr("Delete all shelves"), self.__cleanupShelves)
    
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
        self.__resetUI()
        
        super(HgShelveBrowserDialog, self).show()
    
    def __resetUI(self):
        """
        Private method to reset the user interface.
        """
        self.shelveList.clear()
    
    def __resizeColumnsShelves(self):
        """
        Private method to resize the shelve list columns.
        """
        self.shelveList.header().resizeSections(QHeaderView.ResizeToContents)
        self.shelveList.header().setStretchLastSection(True)
    
    def __generateShelveEntry(self, name, age, message, fileStatistics,
                              totals):
        """
        Private method to generate the shelve items.
        
        @param name name of the shelve (string)
        @param age age of the shelve (string)
        @param message shelve message (string)
        @param fileStatistics per file change statistics (tuple of
            four strings with file name, number of changes, number of
            added lines and number of deleted lines)
        @param totals overall statistics (tuple of three strings with
            number of changed files, number of added lines and number
            of deleted lines)
        """
        itm = QTreeWidgetItem(self.shelveList, [name, age, message])
        itm.setData(0, self.__fileStatisticsRole, fileStatistics)
        itm.setData(0, self.__totalStatisticsRole, totals)
    
    def __getShelveEntries(self):
        """
        Private method to retrieve the list of shelves.
        """
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        QApplication.processEvents()
        
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        
        self.buf = []
        self.errors.clear()
        self.intercept = False
        
        args = self.vcs.initCommand("shelve")
        args.append("--list")
        args.append("--stat")
        
        if self.__hgClient:
            self.inputGroup.setEnabled(False)
            self.inputGroup.hide()
            
            out, err = self.__hgClient.runcommand(args)
            self.buf = out.splitlines(True)
            if err:
                self.__showError(err)
            self.__processBuffer()
            self.__finish()
        else:
            self.process.kill()
            
            self.process.setWorkingDirectory(self.repodir)
            
            self.inputGroup.setEnabled(True)
            self.inputGroup.show()
            
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
    
    def start(self, projectDir):
        """
        Public slot to start the hg shelve command.
        
        @param projectDir name of the project directory (string)
        """
        self.errorGroup.hide()
        QApplication.processEvents()
        
        self.__projectDir = projectDir
        
        # find the root of the repo
        self.repodir = self.__projectDir
        while not os.path.isdir(os.path.join(self.repodir, self.vcs.adminDir)):
            self.repodir = os.path.dirname(self.repodir)
            if os.path.splitdrive(self.repodir)[1] == os.sep:
                return
        
        self.activateWindow()
        self.raise_()
        
        self.shelveList.clear()
        self.__started = True
        self.__getShelveEntries()
    
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.__processBuffer()
        self.__finish()
    
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
    
    def __processBuffer(self):
        """
        Private method to process the buffered output of the hg shelve command.
        """
        lastWasFileStats = False
        firstLine = True
        itemData = {}
        for line in self.buf:
            if firstLine:
                name, line = line.split("(", 1)
                age, message = line.split(")", 1)
                itemData["name"] = name.strip()
                itemData["age"] = age.strip()
                itemData["message"] = message.strip()
                itemData["files"] = []
                firstLine = False
            elif '|' in line:
                # file stats: foo.py |  3 ++-
                file, changes = line.strip().split("|", 1)
                if changes.strip().endswith(("+", "-")):
                    total, addDelete = changes.strip().split(None, 1)
                    additions = str(addDelete.count("+"))
                    deletions = str(addDelete.count("-"))
                else:
                    total = changes.strip()
                    additions = '0'
                    deletions = '0'
                itemData["files"].append((file, total, additions, deletions))
                lastWasFileStats = True
            elif lastWasFileStats:
                # summary line
                # 2 files changed, 15 insertions(+), 1 deletions(-)
                total, added, deleted = line.strip().split(",", 2)
                total = total.split()[0]
                added = added.split()[0]
                deleted = deleted.split()[0]
                itemData["summary"] = (total, added, deleted)
                
                self.__generateShelveEntry(
                    itemData["name"], itemData["age"], itemData["message"],
                    itemData["files"], itemData["summary"])
                
                lastWasFileStats = False
                firstLine = True
                itemData = {}
        
        self.__resizeColumnsShelves()
        
        if self.__started:
            self.shelveList.setCurrentItem(self.shelveList.topLevelItem(0))
            self.__started = False
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStandardOutput signal.
        
        It reads the output of the process and inserts it into a buffer.
        """
        self.process.setReadChannel(QProcess.StandardOutput)
        
        while self.process.canReadLine():
            line = str(self.process.readLine(), self.vcs.getEncoding(),
                       'replace')
            self.buf.append(line)
    
    def __readStderr(self):
        """
        Private slot to handle the readyReadStandardError signal.
        
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
    
    @pyqtSlot(QAbstractButton)
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.cancelled = True
            if self.__hgClient:
                self.__hgClient.cancel()
            else:
                self.__finish()
        elif button == self.refreshButton:
            self.on_refreshButton_clicked()
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_shelveList_currentItemChanged(self, current, previous):
        """
        Private slot called, when the current item of the shelve list changes.
        
        @param current reference to the new current item (QTreeWidgetItem)
        @param previous reference to the old current item (QTreeWidgetItem)
        """
        self.statisticsList.clear()
        if current:
            for dataSet in current.data(0, self.__fileStatisticsRole):
                QTreeWidgetItem(self.statisticsList, list(dataSet))
            self.statisticsList.header().resizeSections(
                QHeaderView.ResizeToContents)
            self.statisticsList.header().setStretchLastSection(True)
            
            totals = current.data(0, self.__totalStatisticsRole)
            self.filesLabel.setText(
                self.tr("%n file(s) changed", None, int(totals[0])))
            self.insertionsLabel.setText(
                self.tr("%n line(s) inserted", None, int(totals[1])))
            self.deletionsLabel.setText(
                self.tr("%n line(s) deleted", None, int(totals[2])))
        else:
            self.filesLabel.setText("")
            self.insertionsLabel.setText("")
            self.deletionsLabel.setText("")
    
    @pyqtSlot(QPoint)
    def on_shelveList_customContextMenuRequested(self, pos):
        """
        Private slot to show the context menu of the shelve list.
        
        @param pos position of the mouse pointer (QPoint)
        """
        selectedItemsCount = len(self.shelveList.selectedItems())
        self.__unshelveAct.setEnabled(selectedItemsCount == 1)
        self.__deleteAct.setEnabled(selectedItemsCount > 0)
        
        self.__contextMenu.popup(self.mapToGlobal(pos))
    
    @pyqtSlot()
    def on_refreshButton_clicked(self):
        """
        Private slot to refresh the list of shelves.
        """
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.inputGroup.setEnabled(True)
        self.inputGroup.show()
        self.refreshButton.setEnabled(False)
        
        self.start(self.__projectDir)
    
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
        Private slot to send the input to the mercurial process.
        """
        input = self.input.text()
        input += os.linesep
        
        if self.passwordCheckBox.isChecked():
            self.errors.insertPlainText(os.linesep)
            self.errors.ensureCursorVisible()
        else:
            self.errors.insertPlainText(input)
            self.errors.ensureCursorVisible()
        self.errorGroup.show()
        
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
        super(HgShelveBrowserDialog, self).keyPressEvent(evt)
    
    def __unshelve(self):
        """
        Private slot to restore the selected shelve of changes.
        """
        itm = self.shelveList.selectedItems()[0]
        if itm is not None:
            name = itm.text(self.NameColumn)
            self.vcs.getExtensionObject("shelve")\
                .hgUnshelve(self.__projectDir, shelveName=name)
            self.on_refreshButton_clicked()
    
    def __deleteShelves(self):
        """
        Private slot to delete the selected shelves.
        """
        shelveNames = []
        for itm in self.shelveList.selectedItems():
            shelveNames.append(itm.text(self.NameColumn))
        if shelveNames:
            self.vcs.getExtensionObject("shelve")\
                .hgDeleteShelves(self.__projectDir, shelveNames=shelveNames)
            self.on_refreshButton_clicked()
    
    def __cleanupShelves(self):
        """
        Private slot to delete all shelves.
        """
        self.vcs.getExtensionObject("shelve")\
            .hgCleanupShelves(self.__projectDir)
        self.on_refreshButton_clicked()
