# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show a list of tags or branches.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import pyqtSlot, QProcess, Qt, QTimer, QCoreApplication
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QHeaderView, \
    QTreeWidgetItem, QLineEdit

from E5Gui import E5MessageBox

from .Ui_HgTagBranchListDialog import Ui_HgTagBranchListDialog


class HgTagBranchListDialog(QDialog, Ui_HgTagBranchListDialog):
    """
    Class implementing a dialog to show a list of tags or branches.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super(HgTagBranchListDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.vcs = vcs
        self.tagsList = None
        self.allTagsList = None
        self.__hgClient = vcs.getClient()
        
        self.tagList.headerItem().setText(self.tagList.columnCount(), "")
        self.tagList.header().setSortIndicator(3, Qt.AscendingOrder)
        
        if self.__hgClient:
            self.process = None
        else:
            self.process = QProcess()
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
    
    def start(self, path, tags, tagsList, allTagsList):
        """
        Public slot to start the tags command.
        
        @param path name of directory to be listed (string)
        @param tags flag indicating a list of tags is requested
            (False = branches, True = tags)
        @param tagsList reference to string list receiving the tags
            (list of strings)
        @param allTagsList reference to string list all tags (list of strings)
        """
        self.errorGroup.hide()
        
        self.intercept = False
        self.tagsMode = tags
        if not tags:
            self.setWindowTitle(self.tr("Mercurial Branches List"))
            self.tagList.headerItem().setText(2, self.tr("Status"))
        self.activateWindow()
        
        self.tagsList = tagsList
        self.allTagsList = allTagsList
        dname, fname = self.vcs.splitPath(path)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        if self.tagsMode:
            args = self.vcs.initCommand("tags")
            args.append('--verbose')
        else:
            args = self.vcs.initCommand("branches")
            args.append('--closed')
        
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
        self.tagList.sortItems(
            self.tagList.sortColumn(),
            self.tagList.header().sortIndicatorOrder())
    
    def __resizeColumns(self):
        """
        Private method to resize the list columns.
        """
        self.tagList.header().resizeSections(QHeaderView.ResizeToContents)
        self.tagList.header().setStretchLastSection(True)
    
    def __generateItem(self, revision, changeset, status, name):
        """
        Private method to generate a tag item in the tag list.
        
        @param revision revision of the tag/branch (string)
        @param changeset changeset of the tag/branch (string)
        @param status of the tag/branch (string)
        @param name name of the tag/branch (string)
        """
        itm = QTreeWidgetItem(self.tagList)
        itm.setData(0, Qt.DisplayRole, int(revision))
        itm.setData(1, Qt.DisplayRole, changeset)
        itm.setData(2, Qt.DisplayRole, status)
        itm.setData(3, Qt.DisplayRole, name)
        itm.setTextAlignment(0, Qt.AlignRight)
        itm.setTextAlignment(1, Qt.AlignRight)
        itm.setTextAlignment(2, Qt.AlignHCenter)
    
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
            if self.tagsMode:
                status = ""
            else:
                status = self.tr("active")
            rev, changeset = li[-1].split(":", 1)
            del li[-1]
        else:
            if self.tagsMode:
                status = self.tr("yes")
            else:
                status = li[-1][1:-1]
            rev, changeset = li[-2].split(":", 1)
            del li[-2:]
        name = " ".join(li)
        self.__generateItem(rev, changeset, status, name)
        if name not in ["tip", "default"]:
            if self.tagsList is not None:
                self.tagsList.append(name)
            if self.allTagsList is not None:
                self.allTagsList.append(name)
    
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
        super(HgTagBranchListDialog, self).keyPressEvent(evt)
