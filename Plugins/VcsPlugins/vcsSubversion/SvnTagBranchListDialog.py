# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
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

from PyQt5.QtCore import QTimer, QProcess, QRegExp, Qt, pyqtSlot
from PyQt5.QtWidgets import QHeaderView, QLineEdit, QDialog, QInputDialog, \
    QDialogButtonBox, QTreeWidgetItem

from E5Gui import E5MessageBox

from .Ui_SvnTagBranchListDialog import Ui_SvnTagBranchListDialog

import Preferences


class SvnTagBranchListDialog(QDialog, Ui_SvnTagBranchListDialog):
    """
    Class implementing a dialog to show a list of tags or branches.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super(SvnTagBranchListDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.vcs = vcs
        self.tagsList = None
        self.allTagsList = None
        
        self.tagList.headerItem().setText(self.tagList.columnCount(), "")
        self.tagList.header().setSortIndicator(3, Qt.AscendingOrder)
        
        self.process = QProcess()
        self.process.finished.connect(self.__procFinished)
        self.process.readyReadStandardOutput.connect(self.__readStdout)
        self.process.readyReadStandardError.connect(self.__readStderr)
        
        self.rx_list = QRegExp(
            r"""\w*\s*(\d+)\s+(\w+)\s+\d*\s*"""
            r"""((?:\w+\s+\d+|[0-9.]+\s+\w+)\s+[0-9:]+)\s+(.+)/\s*""")
        
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
        
    def start(self, path, tags, tagsList, allTagsList):
        """
        Public slot to start the svn status command.
        
        @param path name of directory to be listed (string)
        @param tags flag indicating a list of tags is requested
            (False = branches, True = tags)
        @param tagsList reference to string list receiving the tags
            (list of strings)
        @param allTagsList reference to string list all tags (list of strings)
        """
        self.errorGroup.hide()
        
        self.tagList.clear()
        
        self.intercept = False
        if not tags:
            self.setWindowTitle(self.tr("Subversion Branches List"))
        self.activateWindow()
        
        self.tagsList = tagsList
        self.allTagsList = allTagsList
        dname, fname = self.vcs.splitPath(path)
        
        self.process.kill()
        
        reposURL = self.vcs.svnGetReposName(dname)
        if reposURL is None:
            E5MessageBox.critical(
                self,
                self.tr("Subversion Error"),
                self.tr(
                    """The URL of the project repository could not be"""
                    """ retrieved from the working copy. The list operation"""
                    """ will be aborted"""))
            self.close()
            return
        
        args = []
        args.append('list')
        self.vcs.addArguments(args, self.vcs.options['global'])
        args.append('--verbose')
        
        if self.vcs.otherData["standardLayout"]:
            # determine the base path of the project in the repository
            rx_base = QRegExp('(.+)/(trunk|tags|branches).*')
            if not rx_base.exactMatch(reposURL):
                E5MessageBox.critical(
                    self,
                    self.tr("Subversion Error"),
                    self.tr(
                        """The URL of the project repository has an"""
                        """ invalid format. The list operation will"""
                        """ be aborted"""))
                return
            
            reposRoot = rx_base.cap(1)
            
            if tags:
                args.append("{0}/tags".format(reposRoot))
            else:
                args.append("{0}/branches".format(reposRoot))
            self.path = None
        else:
            reposPath, ok = QInputDialog.getText(
                self,
                self.tr("Subversion List"),
                self.tr("Enter the repository URL containing the tags"
                        " or branches"),
                QLineEdit.Normal,
                self.vcs.svnNormalizeURL(reposURL))
            if not ok:
                self.close()
                return
            if not reposPath:
                E5MessageBox.critical(
                    self,
                    self.tr("Subversion List"),
                    self.tr("""The repository URL is empty."""
                            """ Aborting..."""))
                self.close()
                return
            args.append(reposPath)
            self.path = reposPath
        
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
        self.__resort()
        
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
        
    def __generateItem(self, revision, author, date, name):
        """
        Private method to generate a tag item in the taglist.
        
        @param revision revision string (string)
        @param author author of the tag (string)
        @param date date of the tag (string)
        @param name name (path) of the tag (string)
        """
        itm = QTreeWidgetItem(self.tagList)
        itm.setData(0, Qt.DisplayRole, int(revision))
        itm.setData(1, Qt.DisplayRole, author)
        itm.setData(2, Qt.DisplayRole, date)
        itm.setData(3, Qt.DisplayRole, name)
        itm.setTextAlignment(0, Qt.AlignRight)
        
    def __readStdout(self):
        """
        Private slot to handle the readyReadStdout signal.
        
        It reads the output of the process, formats it and inserts it into
        the contents pane.
        """
        self.process.setReadChannel(QProcess.StandardOutput)
        
        while self.process.canReadLine():
            s = str(self.process.readLine(),
                    Preferences.getSystem("IOEncoding"),
                    'replace')
            if self.rx_list.exactMatch(s):
                rev = "{0:6}".format(self.rx_list.cap(1))
                author = self.rx_list.cap(2)
                date = self.rx_list.cap(3)
                path = self.rx_list.cap(4)
                if path == ".":
                    continue
                self.__generateItem(rev, author, date, path)
                if not self.vcs.otherData["standardLayout"]:
                    path = self.path + '/' + path
                if self.tagsList is not None:
                    self.tagsList.append(path)
                if self.allTagsList is not None:
                    self.allTagsList.append(path)
        
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
        super(SvnTagBranchListDialog, self).keyPressEvent(evt)
