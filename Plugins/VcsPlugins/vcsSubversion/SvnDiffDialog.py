# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the svn diff command
process.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import QTimer, QFileInfo, QProcess, pyqtSlot, Qt
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QWidget, QLineEdit, QDialogButtonBox

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox, E5FileDialog

from .Ui_SvnDiffDialog import Ui_SvnDiffDialog
from .SvnDiffHighlighter import SvnDiffHighlighter

import Utilities
import Preferences


class SvnDiffDialog(QWidget, Ui_SvnDiffDialog):
    """
    Class implementing a dialog to show the output of the svn diff command
    process.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super(SvnDiffDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.refreshButton = self.buttonBox.addButton(
            self.tr("Refresh"), QDialogButtonBox.ActionRole)
        self.refreshButton.setToolTip(
            self.tr("Press to refresh the display"))
        self.refreshButton.setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Save).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.searchWidget.attachTextEdit(self.contents)
        
        self.process = QProcess()
        self.vcs = vcs
        
        font = Preferences.getEditorOtherFonts("MonospacedFont")
        self.contents.setFontFamily(font.family())
        self.contents.setFontPointSize(font.pointSize())
        
        self.highlighter = SvnDiffHighlighter(self.contents.document())
        
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
        
    def __getVersionArg(self, version):
        """
        Private method to get a svn revision argument for the given revision.
        
        @param version revision (integer or string)
        @return version argument (string)
        """
        if version == "WORKING":
            return None
        else:
            return str(version)
        
    def start(self, fn, versions=None, urls=None, summary=False,
              refreshable=False):
        """
        Public slot to start the svn diff command.
        
        @param fn filename to be diffed (string)
        @param versions list of versions to be diffed (list of up to 2 strings
            or None)
        @keyparam urls list of repository URLs (list of 2 strings)
        @keyparam summary flag indicating a summarizing diff
            (only valid for URL diffs) (boolean)
        @keyparam refreshable flag indicating a refreshable diff (boolean)
        """
        self.refreshButton.setVisible(refreshable)
        
        self.errorGroup.hide()
        self.inputGroup.show()
        self.inputGroup.setEnabled(True)
        self.intercept = False
        self.filename = fn
        
        self.process.kill()
        
        self.contents.clear()
        self.paras = 0
        
        self.filesCombo.clear()
        
        self.__oldFile = ""
        self.__oldFileLine = -1
        self.__fileSeparators = []
        
        args = []
        args.append('diff')
        self.vcs.addArguments(args, self.vcs.options['global'])
        self.vcs.addArguments(args, self.vcs.options['diff'])
        if '--diff-cmd' in self.vcs.options['diff']:
            self.buttonBox.button(QDialogButtonBox.Save).hide()
        
        if versions is not None:
            self.raise_()
            self.activateWindow()
            
            rev1 = self.__getVersionArg(versions[0])
            rev2 = None
            if len(versions) == 2:
                rev2 = self.__getVersionArg(versions[1])
            
            if rev1 is not None or rev2 is not None:
                args.append('-r')
                if rev1 is not None and rev2 is not None:
                    args.append('{0}:{1}'.format(rev1, rev2))
                elif rev2 is None:
                    args.append(rev1)
                elif rev1 is None:
                    args.append(rev2)
        
        self.summaryPath = None
        if urls is not None:
            if summary:
                args.append("--summarize")
                self.summaryPath = urls[0]
            args.append("--old={0}".format(urls[0]))
            args.append("--new={0}".format(urls[1]))
            if isinstance(fn, list):
                dname, fnames = self.vcs.splitPathList(fn)
            else:
                dname, fname = self.vcs.splitPath(fn)
                fnames = [fname]
            project = e5App().getObject('Project')
            if dname == project.getProjectPath():
                path = ""
            else:
                path = project.getRelativePath(dname)
            if path:
                path += "/"
            for fname in fnames:
                args.append(path + fname)
        else:
            if isinstance(fn, list):
                dname, fnames = self.vcs.splitPathList(fn)
                self.vcs.addArguments(args, fnames)
            else:
                dname, fname = self.vcs.splitPath(fn)
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
        
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.inputGroup.setEnabled(False)
        self.inputGroup.hide()
        self.refreshButton.setEnabled(True)
        
        if self.paras == 0:
            self.contents.setPlainText(self.tr('There is no difference.'))
            
        self.buttonBox.button(QDialogButtonBox.Save).setEnabled(self.paras > 0)
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        self.buttonBox.button(QDialogButtonBox.Close).setFocus(
            Qt.OtherFocusReason)
        
        tc = self.contents.textCursor()
        tc.movePosition(QTextCursor.Start)
        self.contents.setTextCursor(tc)
        self.contents.ensureCursorVisible()
        
        self.filesCombo.addItem(self.tr("<Start>"), 0)
        self.filesCombo.addItem(self.tr("<End>"), -1)
        for oldFile, newFile, pos in sorted(self.__fileSeparators):
            if oldFile != newFile:
                self.filesCombo.addItem(
                    "{0}\n{1}".format(oldFile, newFile), pos)
            else:
                self.filesCombo.addItem(oldFile, pos)
        
    def __appendText(self, txt):
        """
        Private method to append text to the end of the contents pane.
        
        @param txt text to insert (string)
        """
        tc = self.contents.textCursor()
        tc.movePosition(QTextCursor.End)
        self.contents.setTextCursor(tc)
        self.contents.insertPlainText(txt)
        
    def __extractFileName(self, line):
        """
        Private method to extract the file name out of a file separator line.
        
        @param line line to be processed (string)
        @return extracted file name (string)
        """
        f = line.split(None, 1)[1]
        f = f.rsplit(None, 2)[0]
        return f
    
    def __processFileLine(self, line):
        """
        Private slot to process a line giving the old/new file.
        
        @param line line to be processed (string)
        """
        if line.startswith('---'):
            self.__oldFileLine = self.paras
            self.__oldFile = self.__extractFileName(line)
        else:
            self.__fileSeparators.append(
                (self.__oldFile, self.__extractFileName(line),
                 self.__oldFileLine))
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStandardOutput signal.
        
        It reads the output of the process, formats it and inserts it into
        the contents pane.
        """
        self.process.setReadChannel(QProcess.StandardOutput)
        
        while self.process.canReadLine():
            line = str(self.process.readLine(),
                       Preferences.getSystem("IOEncoding"),
                       'replace')
            if self.summaryPath:
                line = line.replace(self.summaryPath + '/', '')
                line = " ".join(line.split())
            if line.startswith("--- ") or line.startswith("+++ "):
                    self.__processFileLine(line)
                
            self.__appendText(line)
            self.paras += 1
        
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
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Save):
            self.on_saveButton_clicked()
        elif button == self.refreshButton:
            self.on_refreshButton_clicked()
    
    @pyqtSlot(int)
    def on_filesCombo_activated(self, index):
        """
        Private slot to handle the selection of a file.
        
        @param index activated row (integer)
        """
        para = self.filesCombo.itemData(index)
        
        if para == 0:
            tc = self.contents.textCursor()
            tc.movePosition(QTextCursor.Start)
            self.contents.setTextCursor(tc)
            self.contents.ensureCursorVisible()
        elif para == -1:
            tc = self.contents.textCursor()
            tc.movePosition(QTextCursor.End)
            self.contents.setTextCursor(tc)
            self.contents.ensureCursorVisible()
        else:
            # step 1: move cursor to end
            tc = self.contents.textCursor()
            tc.movePosition(QTextCursor.End)
            self.contents.setTextCursor(tc)
            self.contents.ensureCursorVisible()
            
            # step 2: move cursor to desired line
            tc = self.contents.textCursor()
            delta = tc.blockNumber() - para
            tc.movePosition(QTextCursor.PreviousBlock, QTextCursor.MoveAnchor,
                            delta)
            self.contents.setTextCursor(tc)
            self.contents.ensureCursorVisible()
    
    @pyqtSlot()
    def on_saveButton_clicked(self):
        """
        Private slot to handle the Save button press.
        
        It saves the diff shown in the dialog to a file in the local
        filesystem.
        """
        if isinstance(self.filename, list):
            if len(self.filename) > 1:
                fname = self.vcs.splitPathList(self.filename)[0]
            else:
                dname, fname = self.vcs.splitPath(self.filename[0])
                if fname != '.':
                    fname = "{0}.diff".format(self.filename[0])
                else:
                    fname = dname
        else:
            fname = self.vcs.splitPath(self.filename)[0]
        
        fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            self,
            self.tr("Save Diff"),
            fname,
            self.tr("Patch Files (*.diff)"),
            None,
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        
        if not fname:
            return  # user aborted
        
        ext = QFileInfo(fname).suffix()
        if not ext:
            ex = selectedFilter.split("(*")[1].split(")")[0]
            if ex:
                fname += ex
        if QFileInfo(fname).exists():
            res = E5MessageBox.yesNo(
                self,
                self.tr("Save Diff"),
                self.tr("<p>The patch file <b>{0}</b> already exists."
                        " Overwrite it?</p>").format(fname),
                icon=E5MessageBox.Warning)
            if not res:
                return
        fname = Utilities.toNativeSeparators(fname)
        
        eol = e5App().getObject("Project").getEolString()
        try:
            f = open(fname, "w", encoding="utf-8", newline="")
            f.write(eol.join(self.contents.toPlainText().splitlines()))
            f.close()
        except IOError as why:
            E5MessageBox.critical(
                self, self.tr('Save Diff'),
                self.tr(
                    '<p>The patch file <b>{0}</b> could not be saved.'
                    '<br>Reason: {1}</p>')
                .format(fname, str(why)))
        
    @pyqtSlot()
    def on_refreshButton_clicked(self):
        """
        Private slot to refresh the display.
        """
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        
        self.buttonBox.button(QDialogButtonBox.Save).setEnabled(False)
        self.refreshButton.setEnabled(False)
        
        self.start(self.filename, refreshable=True)
    
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
        super(SvnDiffDialog, self).keyPressEvent(evt)
