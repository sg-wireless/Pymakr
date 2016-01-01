# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog showing signed changesets.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import pyqtSlot, QProcess, QTimer, Qt, QRegExp, \
    QCoreApplication
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QHeaderView, \
    QTreeWidgetItem, QLineEdit

from E5Gui import E5MessageBox

from .Ui_HgGpgSignaturesDialog import Ui_HgGpgSignaturesDialog


class HgGpgSignaturesDialog(QDialog, Ui_HgGpgSignaturesDialog):
    """
    Class implementing a dialog showing signed changesets.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent reference to the parent widget (QWidget)
        """
        super(HgGpgSignaturesDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.process = QProcess()
        self.vcs = vcs
        self.__hgClient = vcs.getClient()
        
        self.process.finished.connect(self.__procFinished)
        self.process.readyReadStandardOutput.connect(self.__readStdout)
        self.process.readyReadStandardError.connect(self.__readStderr)
        
        self.show()
        QCoreApplication.processEvents()
    
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
        
        e.accept()
    
    def start(self, path):
        """
        Public slot to start the list command.
        
        @param path name of directory (string)
        """
        self.errorGroup.hide()
        
        self.intercept = False
        self.activateWindow()
        
        self.__path = path
        dname, fname = self.vcs.splitPath(path)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.vcs.initCommand("sigs")
        
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
            self.process.setWorkingDirectory(repodir)
            
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
        
        self.inputGroup.setEnabled(False)
        self.inputGroup.hide()
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        self.buttonBox.button(QDialogButtonBox.Close).setFocus(
            Qt.OtherFocusReason)
        
        if self.signaturesList.topLevelItemCount() == 0:
            # no patches present
            self.__generateItem("", "", self.tr("no signatures found"))
        self.__resizeColumns()
        self.__resort()
    
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
        self.signaturesList.sortItems(
            self.signaturesList.sortColumn(),
            self.signaturesList.header().sortIndicatorOrder())
    
    def __resizeColumns(self):
        """
        Private method to resize the list columns.
        """
        self.signaturesList.header().resizeSections(
            QHeaderView.ResizeToContents)
        self.signaturesList.header().setStretchLastSection(True)
    
    def __generateItem(self, revision, changeset, signature):
        """
        Private method to generate a patch item in the list of patches.
        
        @param revision revision number (string)
        @param changeset changeset of the bookmark (string)
        @param signature signature of the changeset (string)
        """
        if revision == "" and changeset == "":
            QTreeWidgetItem(self.signaturesList, [signature])
        else:
            revString = "{0:>7}:{1}".format(revision, changeset)
            topItems = self.signaturesList.findItems(
                revString, Qt.MatchExactly)
            if len(topItems) == 0:
                # first signature for this changeset
                topItm = QTreeWidgetItem(self.signaturesList, [
                    "{0:>7}:{1}".format(revision, changeset)])
                topItm.setExpanded(True)
                font = topItm.font(0)
                font.setBold(True)
                topItm.setFont(0, font)
            else:
                topItm = topItems[0]
            QTreeWidgetItem(topItm, [signature])
    
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
        li = line.split()
        if li[-1][0] in "1234567890":
            # last element is a rev:changeset
            rev, changeset = li[-1].split(":", 1)
            del li[-1]
            signature = " ".join(li)
            self.__generateItem(rev, changeset, signature)
    
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
    
    @pyqtSlot()
    def on_signaturesList_itemSelectionChanged(self):
        """
        Private slot handling changes of the selection.
        """
        selectedItems = self.signaturesList.selectedItems()
        if len(selectedItems) == 1 and \
           self.signaturesList.indexOfTopLevelItem(selectedItems[0]) != -1:
            self.verifyButton.setEnabled(True)
        else:
            self.verifyButton.setEnabled(False)
    
    @pyqtSlot()
    def on_verifyButton_clicked(self):
        """
        Private slot to verify the signatures of the selected revision.
        """
        rev = self.signaturesList.selectedItems()[0].text(0)\
            .split(":")[0].strip()
        self.vcs.getExtensionObject("gpg")\
            .hgGpgVerifySignatures(self.__path, rev)
    
    @pyqtSlot(str)
    def on_categoryCombo_activated(self, txt):
        """
        Private slot called, when a new filter category is selected.
        
        @param txt text of the selected category (string)
        """
        self.__filterSignatures()
    
    @pyqtSlot(str)
    def on_rxEdit_textChanged(self, txt):
        """
        Private slot called, when a filter expression is entered.
        
        @param txt filter expression (string)
        """
        self.__filterSignatures()
    
    def __filterSignatures(self):
        """
        Private method to filter the log entries.
        """
        searchRxText = self.rxEdit.text()
        filterTop = self.categoryCombo.currentText() == self.tr("Revision")
        if filterTop and searchRxText.startswith("^"):
            searchRx = QRegExp(
                "^\s*{0}".format(searchRxText[1:]), Qt.CaseInsensitive)
        else:
            searchRx = QRegExp(searchRxText, Qt.CaseInsensitive)
        for topIndex in range(self.signaturesList.topLevelItemCount()):
            topLevelItem = self.signaturesList.topLevelItem(topIndex)
            if filterTop:
                topLevelItem.setHidden(
                    searchRx.indexIn(topLevelItem.text(0)) == -1)
            else:
                visibleChildren = topLevelItem.childCount()
                for childIndex in range(topLevelItem.childCount()):
                    childItem = topLevelItem.child(childIndex)
                    if searchRx.indexIn(childItem.text(0)) == -1:
                        childItem.setHidden(True)
                        visibleChildren -= 1
                    else:
                        childItem.setHidden(False)
                topLevelItem.setHidden(visibleChildren == 0)
    
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
        super(HgGpgSignaturesDialog, self).keyPressEvent(evt)
