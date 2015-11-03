# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the hg log command process.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import pyqtSlot, QProcess, QTimer, QUrl, QByteArray, \
    qVersion
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QApplication, QLineEdit

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox

from .Ui_HgLogDialog import Ui_HgLogDialog

import Utilities


class HgLogDialog(QWidget, Ui_HgLogDialog):
    """
    Class implementing a dialog to show the output of the hg log command
    process.
    
    The dialog is nonmodal. Clicking a link in the upper text pane shows
    a diff of the revisions.
    """
    def __init__(self, vcs, mode="log", bundle=None, isFile=False,
                 parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param mode mode of the dialog (string; one of log, incoming, outgoing)
        @param bundle name of a bundle file (string)
        @param isFile flag indicating log for a file is to be shown (boolean)
        @param parent parent widget (QWidget)
        """
        super(HgLogDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.process = QProcess()
        self.vcs = vcs
        if mode in ("log", "incoming", "outgoing"):
            self.mode = mode
        else:
            self.mode = "log"
        self.bundle = bundle
        self.__hgClient = self.vcs.getClient()
        
        self.contents.setHtml(
            self.tr('<b>Processing your request, please wait...</b>'))
        
        self.process.finished.connect(self.__procFinished)
        self.process.readyReadStandardOutput.connect(self.__readStdout)
        self.process.readyReadStandardError.connect(self.__readStderr)
        
        self.contents.anchorClicked.connect(self.__sourceChanged)
        
        self.revisions = []  # stack of remembered revisions
        self.revString = self.tr('Revision')
        self.projectMode = False
        
        self.logEntries = []        # list of log entries
        self.lastLogEntry = {}
        self.fileCopies = {}
        self.endInitialText = False
        self.initialText = []
        
        self.diff = None
        
        self.sbsCheckBox.setEnabled(isFile)
        self.sbsCheckBox.setVisible(isFile)
    
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
    
    def start(self, fn, noEntries=0, revisions=None):
        """
        Public slot to start the hg log command.
        
        @param fn filename to show the log for (string)
        @param noEntries number of entries to show (integer)
        @param revisions revisions to show log for (list of strings)
        """
        self.errorGroup.hide()
        QApplication.processEvents()
        
        self.intercept = False
        self.filename = fn
        self.dname, self.fname = self.vcs.splitPath(fn)
        
        # find the root of the repo
        self.repodir = self.dname
        while not os.path.isdir(os.path.join(self.repodir, self.vcs.adminDir)):
            self.repodir = os.path.dirname(self.repodir)
            if os.path.splitdrive(self.repodir)[1] == os.sep:
                return
        
        self.projectMode = (self.fname == "." and self.dname == self.repodir)
        
        self.activateWindow()
        self.raise_()
        
        preargs = []
        args = self.vcs.initCommand(self.mode)
        if noEntries and self.mode == "log":
            args.append('--limit')
            args.append(str(noEntries))
        if self.mode in ("incoming", "outgoing"):
            args.append("--newest-first")
            if self.vcs.hasSubrepositories():
                args.append("--subrepos")
        if self.mode == "log":
            args.append('--copies')
        if self.vcs.version >= (3, 0):
            args.append('--template')
            args.append(os.path.join(os.path.dirname(__file__),
                                     "templates",
                                     "logDialogBookmarkPhase.tmpl"))
        else:
            args.append('--style')
            if self.vcs.version >= (2, 1):
                args.append(os.path.join(os.path.dirname(__file__),
                                         "styles",
                                         "logDialogBookmarkPhase.style"))
            else:
                args.append(os.path.join(os.path.dirname(__file__),
                                         "styles",
                                         "logDialogBookmark.style"))
        if self.mode == "incoming":
            if self.bundle:
                args.append(self.bundle)
            elif not self.vcs.hasSubrepositories():
                project = e5App().getObject("Project")
                self.vcs.bundleFile = os.path.join(
                    project.getProjectManagementDir(), "hg-bundle.hg")
                if os.path.exists(self.vcs.bundleFile):
                    os.remove(self.vcs.bundleFile)
                preargs = args[:]
                preargs.append("--quiet")
                preargs.append('--bundle')
                preargs.append(self.vcs.bundleFile)
                args.append(self.vcs.bundleFile)
        if revisions:
            for rev in revisions:
                args.append("--rev")
                args.append(rev)
        if not self.projectMode:
            args.append(self.filename)
        
        if self.__hgClient:
            self.inputGroup.setEnabled(False)
            self.inputGroup.hide()
            
            if preargs:
                out, err = self.__hgClient.runcommand(preargs)
            else:
                err = ""
            if err:
                self.__showError(err)
            elif self.mode != "incoming" or \
                (self.vcs.bundleFile and
                 os.path.exists(self.vcs.bundleFile)) or \
                    self.bundle:
                out, err = self.__hgClient.runcommand(args)
                if err:
                    self.__showError(err)
                if out and self.isVisible():
                    for line in out.splitlines(True):
                        self.__processOutputLine(line)
                        if self.__hgClient.wasCanceled():
                            break
            self.__finish()
        else:
            self.process.kill()
            
            self.process.setWorkingDirectory(self.repodir)
            
            if preargs:
                process = QProcess()
                process.setWorkingDirectory(self.repodir)
                process.start('hg', args)
                procStarted = process.waitForStarted(5000)
                if procStarted:
                    process.waitForFinished(30000)
            
            if self.mode != "incoming" or \
                (self.vcs.bundleFile and
                 os.path.exists(self.vcs.bundleFile)) or \
                    self.bundle:
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
                self.__finish()
    
    def __getParents(self, rev):
        """
        Private method to get the parents of the currently viewed
        file/directory.
        
        @param rev revision number to get parents for (string)
        @return list of parent revisions (list of strings)
        """
        errMsg = ""
        parents = []
        
        if int(rev) > 0:
            args = self.vcs.initCommand("parents")
            if self.mode == "incoming":
                if self.bundle:
                    args.append("--repository")
                    args.append(self.bundle)
                elif self.vcs.bundleFile and \
                        os.path.exists(self.vcs.bundleFile):
                    args.append("--repository")
                    args.append(self.vcs.bundleFile)
            args.append("--template")
            args.append("{rev}:{node|short}\n")
            args.append("-r")
            args.append(rev)
            if not self.projectMode:
                args.append(self.filename)
            
            output = ""
            if self.__hgClient:
                output, errMsg = self.__hgClient.runcommand(args)
            else:
                process = QProcess()
                process.setWorkingDirectory(self.repodir)
                process.start('hg', args)
                procStarted = process.waitForStarted(5000)
                if procStarted:
                    finished = process.waitForFinished(30000)
                    if finished and process.exitCode() == 0:
                        output = str(process.readAllStandardOutput(),
                                     self.vcs.getEncoding(), 'replace')
                    else:
                        if not finished:
                            errMsg = self.tr(
                                "The hg process did not finish within 30s.")
                else:
                    errMsg = self.tr("Could not start the hg executable.")
            
            if errMsg:
                E5MessageBox.critical(
                    self,
                    self.tr("Mercurial Error"),
                    errMsg)
            
            if output:
                parents = [p for p in output.strip().splitlines()]
        
        return parents
    
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.__finish()
    
    def __finish(self):
        """
        Private slot called when the process finished or the user pressed
        the button.
        """
        self.inputGroup.setEnabled(False)
        self.inputGroup.hide()
        
        self.contents.clear()
        
        if not self.logEntries:
            self.errors.append(self.tr("No log available for '{0}'")
                               .format(self.filename))
            self.errorGroup.show()
            return
        
        html = ""
        
        if self.initialText:
            for line in self.initialText:
                html += Utilities.html_encode(line.strip())
                html += '<br />\n'
            html += '{0}<br/>\n'.format(80 * "=")
            
        for entry in self.logEntries:
            fileCopies = {}
            if entry["file_copies"]:
                for fentry in entry["file_copies"].split(", "):
                    newName, oldName = fentry[:-1].split(" (")
                    fileCopies[newName] = oldName
            
            rev, hexRev = entry["change"].split(":")
            dstr = '<p><b>{0} {1}</b>'.format(self.revString, entry["change"])
            if entry["parents"]:
                parents = entry["parents"].split()
            else:
                parents = self.__getParents(rev)
            for parent in parents:
                url = QUrl()
                url.setScheme("file")
                url.setPath(self.filename)
                if qVersion() >= "5.0.0":
                    query = parent.split(":")[0] + '_' + rev
                    url.setQuery(query)
                else:
                    query = QByteArray()
                    query.append(parent.split(":")[0]).append('_').append(rev)
                    url.setEncodedQuery(query)
                dstr += ' [<a href="{0}" name="{1}" id="{1}">{2}</a>]'.format(
                    url.toString(), query,
                    self.tr('diff to {0}').format(parent),
                )
            dstr += '<br />\n'
            html += dstr
            
            if "phase" in entry:
                html += self.tr("Phase: {0}<br />\n")\
                    .format(entry["phase"])
            
            html += self.tr("Branch: {0}<br />\n")\
                .format(entry["branches"])
            
            html += self.tr("Tags: {0}<br />\n").format(entry["tags"])
            
            if "bookmarks" in entry:
                html += self.tr("Bookmarks: {0}<br />\n")\
                    .format(entry["bookmarks"])
            
            html += self.tr("Parents: {0}<br />\n")\
                .format(entry["parents"])
            
            html += self.tr('<i>Author: {0}</i><br />\n')\
                .format(Utilities.html_encode(entry["user"]))
            
            date, time = entry["date"].split()[:2]
            html += self.tr('<i>Date: {0}, {1}</i><br />\n')\
                .format(date, time)
            
            for line in entry["description"]:
                html += Utilities.html_encode(line.strip())
                html += '<br />\n'
            
            if entry["file_adds"]:
                html += '<br />\n'
                for f in entry["file_adds"].strip().split(", "):
                    if f in fileCopies:
                        html += self.tr(
                            'Added {0} (copied from {1})<br />\n')\
                            .format(Utilities.html_encode(f),
                                    Utilities.html_encode(fileCopies[f]))
                    else:
                        html += self.tr('Added {0}<br />\n')\
                            .format(Utilities.html_encode(f))
            
            if entry["files_mods"]:
                html += '<br />\n'
                for f in entry["files_mods"].strip().split(", "):
                    html += self.tr('Modified {0}<br />\n')\
                        .format(Utilities.html_encode(f))
            
            if entry["file_dels"]:
                html += '<br />\n'
                for f in entry["file_dels"].strip().split(", "):
                    html += self.tr('Deleted {0}<br />\n')\
                        .format(Utilities.html_encode(f))
            
            html += '</p>{0}<br/>\n'.format(60 * "=")
        
        self.contents.setHtml(html)
        tc = self.contents.textCursor()
        tc.movePosition(QTextCursor.Start)
        self.contents.setTextCursor(tc)
        self.contents.ensureCursorVisible()
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStandardOutput signal.
        
        It reads the output of the process and inserts it into a buffer.
        """
        self.process.setReadChannel(QProcess.StandardOutput)
        
        while self.process.canReadLine():
            s = str(self.process.readLine(), self.vcs.getEncoding(), 'replace')
            self.__processOutputLine(s)
    
    def __processOutputLine(self, line):
        """
        Private method to process the lines of output.
        
        @param line output line to be processed (string)
        """
        if line == "@@@\n":
            self.logEntries.append(self.lastLogEntry)
            self.lastLogEntry = {}
            self.fileCopies = {}
        else:
            try:
                key, value = line.split("|", 1)
            except ValueError:
                key = ""
                value = line
            if key == "change":
                self.endInitialText = True
            if key in ("change", "tags", "parents", "user", "date",
                       "file_copies", "file_adds", "files_mods", "file_dels",
                       "bookmarks", "phase"):
                self.lastLogEntry[key] = value.strip()
            elif key == "branches":
                if value.strip():
                    self.lastLogEntry[key] = value.strip()
                else:
                    self.lastLogEntry[key] = "default"
            elif key == "description":
                self.lastLogEntry[key] = [value.strip()]
            else:
                if self.endInitialText:
                    self.lastLogEntry["description"].append(value.strip())
                else:
                    self.initialText.append(value)
    
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
    
    def __sourceChanged(self, url):
        """
        Private slot to handle the sourceChanged signal of the contents pane.
        
        @param url the url that was clicked (QUrl)
        """
        filename = url.path()
        if Utilities.isWindowsPlatform():
            if filename.startswith("/"):
                filename = filename[1:]
        if qVersion() >= "5.0.0":
            ver = url.query()
        else:
            ver = bytes(url.encodedQuery()).decode()
        v1, v2 = ver.split('_')
        if v1 == "" or v2 == "":
            return
        self.contents.scrollToAnchor(ver)
        
        if self.sbsCheckBox.isEnabled() and self.sbsCheckBox.isChecked():
            self.vcs.hgSbsDiff(filename, revisions=(v1, v2))
        else:
            if self.diff is None:
                from .HgDiffDialog import HgDiffDialog
                self.diff = HgDiffDialog(self.vcs)
            self.diff.show()
            self.diff.start(filename, [v1, v2], self.bundle)
    
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
        Private slot to send the input to the hg process.
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
        super(HgLogDialog, self).keyPressEvent(evt)
