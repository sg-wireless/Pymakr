# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to browse the log history.
"""

from __future__ import unicode_literals

import os
import sys

import pysvn

from PyQt5.QtCore import QMutexLocker, QDate, QRegExp, Qt, pyqtSlot, QPoint
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QHeaderView, QWidget, QApplication, \
    QDialogButtonBox, QTreeWidgetItem

from E5Gui import E5MessageBox

from .SvnUtilities import formatTime, dateFromTime_t
from .SvnDialogMixin import SvnDialogMixin

from .Ui_SvnLogBrowserDialog import Ui_SvnLogBrowserDialog


class SvnLogBrowserDialog(QWidget, SvnDialogMixin, Ui_SvnLogBrowserDialog):
    """
    Class implementing a dialog to browse the log history.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super(SvnLogBrowserDialog, self).__init__(parent)
        self.setupUi(self)
        SvnDialogMixin.__init__(self)
        
        self.__position = QPoint()
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.filesTree.headerItem().setText(self.filesTree.columnCount(), "")
        self.filesTree.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.vcs = vcs
        
        self.__initData()
        
        self.fromDate.setDisplayFormat("yyyy-MM-dd")
        self.toDate.setDisplayFormat("yyyy-MM-dd")
        self.__resetUI()
        
        self.__messageRole = Qt.UserRole
        self.__changesRole = Qt.UserRole + 1
        
        self.flags = {
            'A': self.tr('Added'),
            'D': self.tr('Deleted'),
            'M': self.tr('Modified'),
            'R': self.tr('Replaced'),
        }
        
        self.client = self.vcs.getClient()
        self.client.callback_cancel = \
            self._clientCancelCallback
        self.client.callback_get_login = \
            self._clientLoginCallback
        self.client.callback_ssl_server_trust_prompt = \
            self._clientSslServerTrustPromptCallback
    
    def __initData(self):
        """
        Private method to (re-)initialize some data.
        """
        self.__maxDate = QDate()
        self.__minDate = QDate()
        self.__filterLogsEnabled = True
        
        self.diff = None
        self.__lastRev = 0
    
    def closeEvent(self, e):
        """
        Protected slot implementing a close event handler.
        
        @param e close event (QCloseEvent)
        """
        self.__position = self.pos()
        
        e.accept()
    
    def show(self):
        """
        Public slot to show the dialog.
        """
        if not self.__position.isNull():
            self.move(self.__position)
        self.__resetUI()
        
        super(SvnLogBrowserDialog, self).show()
    
    def __resetUI(self):
        """
        Private method to reset the user interface.
        """
        self.fromDate.setDate(QDate.currentDate())
        self.toDate.setDate(QDate.currentDate())
        self.fieldCombo.setCurrentIndex(self.fieldCombo.findText(
            self.tr("Message")))
        self.limitSpinBox.setValue(self.vcs.getPlugin().getPreferences(
            "LogLimit"))
        self.stopCheckBox.setChecked(self.vcs.getPlugin().getPreferences(
            "StopLogOnCopy"))
        
        self.logTree.clear()
        
        self.nextButton.setEnabled(True)
        self.limitSpinBox.setEnabled(True)

    def _reset(self):
        """
        Protected method to reset the internal state of the dialog.
        """
        SvnDialogMixin._reset(self)
        
        self.cancelled = False
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        QApplication.processEvents()
    
    def __resizeColumnsLog(self):
        """
        Private method to resize the log tree columns.
        """
        self.logTree.header().resizeSections(QHeaderView.ResizeToContents)
        self.logTree.header().setStretchLastSection(True)
    
    def __resortLog(self):
        """
        Private method to resort the log tree.
        """
        self.logTree.sortItems(
            self.logTree.sortColumn(),
            self.logTree.header().sortIndicatorOrder())
    
    def __resizeColumnsFiles(self):
        """
        Private method to resize the changed files tree columns.
        """
        self.filesTree.header().resizeSections(QHeaderView.ResizeToContents)
        self.filesTree.header().setStretchLastSection(True)
    
    def __resortFiles(self):
        """
        Private method to resort the changed files tree.
        """
        sortColumn = self.filesTree.sortColumn()
        self.filesTree.sortItems(
            1, self.filesTree.header().sortIndicatorOrder())
        self.filesTree.sortItems(
            sortColumn, self.filesTree.header().sortIndicatorOrder())
    
    def __generateLogItem(self, author, date, message, revision, changedPaths):
        """
        Private method to generate a log tree entry.
        
        @param author author info (string)
        @param date date info (integer)
        @param message text of the log message (string)
        @param revision revision info (string or pysvn.opt_revision_kind)
        @param changedPaths list of pysvn dictionary like objects containing
            info about the changed files/directories
        @return reference to the generated item (QTreeWidgetItem)
        """
        if revision == "":
            rev = ""
            self.__lastRev = 0
        else:
            rev = revision.number
            self.__lastRev = revision.number
        if date == "":
            dt = ""
        else:
            dt = formatTime(date)
        
        itm = QTreeWidgetItem(self.logTree)
        itm.setData(0, Qt.DisplayRole, rev)
        itm.setData(1, Qt.DisplayRole, author)
        itm.setData(2, Qt.DisplayRole, dt)
        itm.setData(3, Qt.DisplayRole, " ".join(message.splitlines()))
        
        changes = []
        for changedPath in changedPaths:
            if changedPath["copyfrom_path"] is None:
                copyPath = ""
            else:
                copyPath = changedPath["copyfrom_path"]
            if changedPath["copyfrom_revision"] is None:
                copyRev = ""
            else:
                copyRev = "{0:7d}".format(
                    changedPath["copyfrom_revision"].number)
            change = {
                "action": changedPath["action"],
                "path": changedPath["path"],
                "copyfrom_path": copyPath,
                "copyfrom_revision": copyRev,
            }
            changes.append(change)
        itm.setData(0, self.__messageRole, message)
        itm.setData(0, self.__changesRole, changes)
        
        itm.setTextAlignment(0, Qt.AlignRight)
        itm.setTextAlignment(1, Qt.AlignLeft)
        itm.setTextAlignment(2, Qt.AlignLeft)
        itm.setTextAlignment(3, Qt.AlignLeft)
        itm.setTextAlignment(4, Qt.AlignLeft)
        
        return itm
    
    def __generateFileItem(self, action, path, copyFrom, copyRev):
        """
        Private method to generate a changed files tree entry.
        
        @param action indicator for the change action ("A", "D" or "M")
        @param path path of the file in the repository (string)
        @param copyFrom path the file was copied from (None, string)
        @param copyRev revision the file was copied from (None, string)
        @return reference to the generated item (QTreeWidgetItem)
        """
        itm = QTreeWidgetItem(
            self.filesTree,
            [self.flags[action], path, copyFrom, copyRev]
        )
        
        itm.setTextAlignment(3, Qt.AlignRight)
        
        return itm
    
    def __getLogEntries(self, startRev=None):
        """
        Private method to retrieve log entries from the repository.
        
        @param startRev revision number to start from (integer, string)
        """
        fetchLimit = 10
        self._reset()
        
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        
        limit = self.limitSpinBox.value()
        if startRev is None:
            start = pysvn.Revision(pysvn.opt_revision_kind.head)
        else:
            try:
                start = pysvn.Revision(pysvn.opt_revision_kind.number,
                                       int(startRev))
            except TypeError:
                start = pysvn.Revision(pysvn.opt_revision_kind.head)
        
        locker = QMutexLocker(self.vcs.vcsExecutionMutex)
        cwd = os.getcwd()
        os.chdir(self.dname)
        try:
            nextRev = 0
            fetched = 0
            logs = []
            while fetched < limit:
                flimit = min(fetchLimit, limit - fetched)
                if fetched == 0:
                    revstart = start
                else:
                    revstart = pysvn.Revision(
                        pysvn.opt_revision_kind.number, nextRev)
                allLogs = self.client.log(
                    self.fname, revision_start=revstart,
                    discover_changed_paths=True, limit=flimit + 1,
                    strict_node_history=self.stopCheckBox.isChecked())
                if len(allLogs) <= flimit or self._clientCancelCallback():
                    logs.extend(allLogs)
                    break
                else:
                    logs.extend(allLogs[:-1])
                    nextRev = allLogs[-1]["revision"].number
                    fetched += fetchLimit
            locker.unlock()
            
            for log in logs:
                author = log["author"]
                message = log["message"]
                if sys.version_info[0] == 2:
                    author = author.decode('utf-8')
                    message = message.decode('utf-8')
                self.__generateLogItem(
                    author, log["date"], message,
                    log["revision"], log['changed_paths'])
                dt = dateFromTime_t(log["date"])
                if not self.__maxDate.isValid() and \
                        not self.__minDate.isValid():
                    self.__maxDate = dt
                    self.__minDate = dt
                else:
                    if self.__maxDate < dt:
                        self.__maxDate = dt
                    if self.__minDate > dt:
                        self.__minDate = dt
            if len(logs) < limit and not self.cancelled:
                self.nextButton.setEnabled(False)
                self.limitSpinBox.setEnabled(False)
            self.__filterLogsEnabled = False
            self.fromDate.setMinimumDate(self.__minDate)
            self.fromDate.setMaximumDate(self.__maxDate)
            self.fromDate.setDate(self.__minDate)
            self.toDate.setMinimumDate(self.__minDate)
            self.toDate.setMaximumDate(self.__maxDate)
            self.toDate.setDate(self.__maxDate)
            self.__filterLogsEnabled = True
            
            self.__resizeColumnsLog()
            self.__resortLog()
            self.__filterLogs()
        except pysvn.ClientError as e:
            locker.unlock()
            self.__showError(e.args[0])
        os.chdir(cwd)
        self.__finish()
    
    def start(self, fn, isFile=False):
        """
        Public slot to start the svn log command.
        
        @param fn filename to show the log for (string)
        @keyparam isFile flag indicating log for a file is to be shown
            (boolean)
        """
        self.sbsCheckBox.setEnabled(isFile)
        self.sbsCheckBox.setVisible(isFile)
        
        self.__initData()
        
        self.filename = fn
        self.dname, self.fname = self.vcs.splitPath(fn)
        
        self.activateWindow()
        self.raise_()
        
        self.logTree.clear()
        self.__getLogEntries()
        self.logTree.setCurrentItem(self.logTree.topLevelItem(0))
    
    def __finish(self):
        """
        Private slot called when the user pressed the button.
        """
        QApplication.restoreOverrideCursor()
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self._cancel()
    
    def __diffRevisions(self, rev1, rev2, peg_rev):
        """
        Private method to do a diff of two revisions.
        
        @param rev1 first revision number (integer)
        @param rev2 second revision number (integer)
        @param peg_rev revision number to use as a reference (integer)
        """
        if self.sbsCheckBox.isEnabled() and self.sbsCheckBox.isChecked():
            self.vcs.svnSbsDiff(self.filename,
                                revisions=(str(rev1), str(rev2)))
        else:
            if self.diff is None:
                from .SvnDiffDialog import SvnDiffDialog
                self.diff = SvnDiffDialog(self.vcs)
            self.diff.show()
            self.diff.raise_()
            QApplication.processEvents()
            self.diff.start(self.filename, [rev1, rev2], pegRev=peg_rev)
    
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.cancelled = True
            self.__finish()
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_logTree_currentItemChanged(self, current, previous):
        """
        Private slot called, when the current item of the log tree changes.
        
        @param current reference to the new current item (QTreeWidgetItem)
        @param previous reference to the old current item (QTreeWidgetItem)
        """
        if current is not None:
            self.messageEdit.setPlainText(current.data(0, self.__messageRole))
            
            self.filesTree.clear()
            changes = current.data(0, self.__changesRole)
            if len(changes) > 0:
                for change in changes:
                    self.__generateFileItem(
                        change["action"], change["path"],
                        change["copyfrom_path"], change["copyfrom_revision"])
                self.__resizeColumnsFiles()
                self.__resortFiles()
        
        self.diffPreviousButton.setEnabled(
            current != self.logTree.topLevelItem(
                self.logTree.topLevelItemCount() - 1))
    
    @pyqtSlot()
    def on_logTree_itemSelectionChanged(self):
        """
        Private slot called, when the selection has changed.
        """
        self.diffRevisionsButton.setEnabled(
            len(self.logTree.selectedItems()) == 2)
    
    @pyqtSlot()
    def on_nextButton_clicked(self):
        """
        Private slot to handle the Next button.
        """
        if self.__lastRev > 1:
            self.__getLogEntries(self.__lastRev - 1)
    
    @pyqtSlot()
    def on_diffPreviousButton_clicked(self):
        """
        Private slot to handle the Diff to Previous button.
        """
        itm = self.logTree.topLevelItem(0)
        if itm is None:
            self.diffPreviousButton.setEnabled(False)
            return
        peg_rev = int(itm.text(0))
        
        itm = self.logTree.currentItem()
        if itm is None:
            self.diffPreviousButton.setEnabled(False)
            return
        rev2 = int(itm.text(0))
        
        itm = self.logTree.topLevelItem(
            self.logTree.indexOfTopLevelItem(itm) + 1)
        if itm is None:
            self.diffPreviousButton.setEnabled(False)
            return
        rev1 = int(itm.text(0))
        
        self.__diffRevisions(rev1, rev2, peg_rev)
    
    @pyqtSlot()
    def on_diffRevisionsButton_clicked(self):
        """
        Private slot to handle the Compare Revisions button.
        """
        items = self.logTree.selectedItems()
        if len(items) != 2:
            self.diffRevisionsButton.setEnabled(False)
            return
        
        rev2 = int(items[0].text(0))
        rev1 = int(items[1].text(0))
        
        itm = self.logTree.topLevelItem(0)
        if itm is None:
            self.diffPreviousButton.setEnabled(False)
            return
        peg_rev = int(itm.text(0))
        
        self.__diffRevisions(min(rev1, rev2), max(rev1, rev2), peg_rev)
    
    def __showError(self, msg):
        """
        Private slot to show an error message.
        
        @param msg error message to show (string)
        """
        E5MessageBox.critical(
            self,
            self.tr("Subversion Error"),
            msg)
    
    @pyqtSlot(QDate)
    def on_fromDate_dateChanged(self, date):
        """
        Private slot called, when the from date changes.
        
        @param date new date (QDate)
        """
        self.__filterLogs()
    
    @pyqtSlot(QDate)
    def on_toDate_dateChanged(self, date):
        """
        Private slot called, when the from date changes.
        
        @param date new date (QDate)
        """
        self.__filterLogs()
    
    @pyqtSlot(str)
    def on_fieldCombo_activated(self, txt):
        """
        Private slot called, when a new filter field is selected.
        
        @param txt text of the selected field (string)
        """
        self.__filterLogs()
    
    @pyqtSlot(str)
    def on_rxEdit_textChanged(self, txt):
        """
        Private slot called, when a filter expression is entered.
        
        @param txt filter expression (string)
        """
        self.__filterLogs()
    
    def __filterLogs(self):
        """
        Private method to filter the log entries.
        """
        if self.__filterLogsEnabled:
            from_ = self.fromDate.date().toString("yyyy-MM-dd")
            to_ = self.toDate.date().addDays(1).toString("yyyy-MM-dd")
            txt = self.fieldCombo.currentText()
            if txt == self.tr("Author"):
                fieldIndex = 1
                searchRx = QRegExp(self.rxEdit.text(), Qt.CaseInsensitive)
            elif txt == self.tr("Revision"):
                fieldIndex = 0
                txt = self.rxEdit.text()
                if txt.startswith("^"):
                    searchRx = QRegExp(
                        "^\s*{0}".format(txt[1:]), Qt.CaseInsensitive)
                else:
                    searchRx = QRegExp(txt, Qt.CaseInsensitive)
            else:
                fieldIndex = 3
                searchRx = QRegExp(self.rxEdit.text(), Qt.CaseInsensitive)
            
            currentItem = self.logTree.currentItem()
            for topIndex in range(self.logTree.topLevelItemCount()):
                topItem = self.logTree.topLevelItem(topIndex)
                if topItem.text(2) <= to_ and topItem.text(2) >= from_ and \
                   searchRx.indexIn(topItem.text(fieldIndex)) > -1:
                    topItem.setHidden(False)
                    if topItem is currentItem:
                        self.on_logTree_currentItemChanged(topItem, None)
                else:
                    topItem.setHidden(True)
                    if topItem is currentItem:
                        self.messageEdit.clear()
                        self.filesTree.clear()
    
    @pyqtSlot(bool)
    def on_stopCheckBox_clicked(self, checked):
        """
        Private slot called, when the stop on copy/move checkbox is clicked.
        
        @param checked flag indicating the check box state (boolean)
        """
        self.vcs.getPlugin().setPreferences("StopLogOnCopy",
                                            int(self.stopCheckBox.isChecked()))
        self.nextButton.setEnabled(True)
        self.limitSpinBox.setEnabled(True)
