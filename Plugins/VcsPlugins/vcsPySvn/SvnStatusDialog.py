# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the svn status command
process.
"""

from __future__ import unicode_literals

import os
import sys

import pysvn

from PyQt5.QtCore import QMutexLocker, Qt, pyqtSlot
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QHeaderView, QApplication, QMenu, \
    QDialogButtonBox, QTreeWidgetItem

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox

from .SvnConst import svnStatusMap
from .SvnDialogMixin import SvnDialogMixin

from .Ui_SvnStatusDialog import Ui_SvnStatusDialog

import Preferences
import Utilities


class SvnStatusDialog(QWidget, SvnDialogMixin, Ui_SvnStatusDialog):
    """
    Class implementing a dialog to show the output of the svn status command
    process.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super(SvnStatusDialog, self).__init__(parent)
        self.setupUi(self)
        SvnDialogMixin.__init__(self)
        
        self.__toBeCommittedColumn = 0
        self.__changelistColumn = 1
        self.__statusColumn = 2
        self.__propStatusColumn = 3
        self.__lockedColumn = 4
        self.__historyColumn = 5
        self.__switchedColumn = 6
        self.__lockinfoColumn = 7
        self.__upToDateColumn = 8
        self.__pathColumn = 12
        self.__lastColumn = self.statusList.columnCount()
        
        self.refreshButton = \
            self.buttonBox.addButton(self.tr("Refresh"),
                                     QDialogButtonBox.ActionRole)
        self.refreshButton.setToolTip(
            self.tr("Press to refresh the status display"))
        self.refreshButton.setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.diff = None
        self.vcs = vcs
        self.vcs.committed.connect(self.__committed)
        
        self.statusList.headerItem().setText(self.__lastColumn, "")
        self.statusList.header().setSortIndicator(self.__pathColumn,
                                                  Qt.AscendingOrder)
        if pysvn.svn_version < (1, 5, 0) or pysvn.version < (1, 6, 0):
            self.statusList.header().hideSection(self.__changelistColumn)
        
        self.menuactions = []
        self.menu = QMenu()
        self.menuactions.append(self.menu.addAction(
            self.tr("Commit changes to repository..."), self.__commit))
        self.menuactions.append(self.menu.addAction(
            self.tr("Select all for commit"), self.__commitSelectAll))
        self.menuactions.append(self.menu.addAction(
            self.tr("Deselect all from commit"), self.__commitDeselectAll))
        self.menu.addSeparator()
        self.menuactions.append(self.menu.addAction(
            self.tr("Add to repository"), self.__add))
        self.menuactions.append(self.menu.addAction(
            self.tr("Show differences"), self.__diff))
        self.menuactions.append(self.menu.addAction(
            self.tr("Show differences side-by-side"), self.__sbsDiff))
        self.menuactions.append(self.menu.addAction(
            self.tr("Revert changes"), self.__revert))
        self.menuactions.append(self.menu.addAction(
            self.tr("Restore missing"), self.__restoreMissing))
        if pysvn.svn_version >= (1, 5, 0) and pysvn.version >= (1, 6, 0):
            self.menu.addSeparator()
            self.menuactions.append(self.menu.addAction(
                self.tr("Add to Changelist"), self.__addToChangelist))
            self.menuactions.append(self.menu.addAction(
                self.tr("Remove from Changelist"),
                self.__removeFromChangelist))
        if self.vcs.version >= (1, 2, 0):
            self.menu.addSeparator()
            self.menuactions.append(
                self.menu.addAction(self.tr("Lock"), self.__lock))
            self.menuactions.append(
                self.menu.addAction(self.tr("Unlock"), self.__unlock))
            self.menuactions.append(self.menu.addAction(
                self.tr("Break lock"),
                self.__breakLock))
            self.menuactions.append(self.menu.addAction(
                self.tr("Steal lock"),
                self.__stealLock))
        self.menu.addSeparator()
        self.menuactions.append(self.menu.addAction(
            self.tr("Adjust column sizes"),
            self.__resizeColumns))
        for act in self.menuactions:
            act.setEnabled(False)
        
        self.statusList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.statusList.customContextMenuRequested.connect(
            self.__showContextMenu)
        
        self.modifiedIndicators = [
            self.tr(svnStatusMap[pysvn.wc_status_kind.added]),
            self.tr(svnStatusMap[pysvn.wc_status_kind.deleted]),
            self.tr(svnStatusMap[pysvn.wc_status_kind.modified])
        ]
        
        self.missingIndicators = [
            self.tr(svnStatusMap[pysvn.wc_status_kind.missing]),
        ]
        
        self.unversionedIndicators = [
            self.tr(svnStatusMap[pysvn.wc_status_kind.unversioned]),
        ]
        
        self.lockedIndicators = [
            self.tr('locked'),
        ]
        
        self.stealBreakLockIndicators = [
            self.tr('other lock'),
            self.tr('stolen lock'),
            self.tr('broken lock'),
        ]
        
        self.unlockedIndicators = [
            self.tr('not locked'),
        ]
        
        self.lockinfo = {
            ' ': self.tr('not locked'),
            'L': self.tr('locked'),
            'O': self.tr('other lock'),
            'S': self.tr('stolen lock'),
            'B': self.tr('broken lock'),
        }
        self.yesno = [
            self.tr('no'),
            self.tr('yes'),
        ]
        
        self.client = self.vcs.getClient()
        self.client.callback_cancel = \
            self._clientCancelCallback
        self.client.callback_get_login = \
            self._clientLoginCallback
        self.client.callback_ssl_server_trust_prompt = \
            self._clientSslServerTrustPromptCallback
        
        self.show()
        QApplication.processEvents()
        
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.statusList.sortItems(
            self.statusList.sortColumn(),
            self.statusList.header().sortIndicatorOrder())
        
    def __resizeColumns(self):
        """
        Private method to resize the list columns.
        """
        self.statusList.header().resizeSections(QHeaderView.ResizeToContents)
        self.statusList.header().setStretchLastSection(True)
        
    def __generateItem(self, changelist, status, propStatus, locked, history,
                       switched, lockinfo, uptodate, revision, change, author,
                       path):
        """
        Private method to generate a status item in the status list.
        
        @param changelist name of the changelist (string)
        @param status text status (pysvn.wc_status_kind)
        @param propStatus property status (pysvn.wc_status_kind)
        @param locked locked flag (boolean)
        @param history history flag (boolean)
        @param switched switched flag (boolean)
        @param lockinfo lock indicator (string)
        @param uptodate up to date flag (boolean)
        @param revision revision (integer)
        @param change revision of last change (integer)
        @param author author of the last change (string)
        @param path path of the file or directory (string)
        """
        statusText = self.tr(svnStatusMap[status])
        itm = QTreeWidgetItem(self.statusList)
        itm.setData(0, Qt.DisplayRole, "")
        itm.setData(1, Qt.DisplayRole, changelist)
        itm.setData(2, Qt.DisplayRole, statusText)
        itm.setData(3, Qt.DisplayRole, self.tr(svnStatusMap[propStatus]))
        itm.setData(4, Qt.DisplayRole, self.yesno[locked])
        itm.setData(5, Qt.DisplayRole, self.yesno[history])
        itm.setData(6, Qt.DisplayRole, self.yesno[switched])
        itm.setData(7, Qt.DisplayRole, self.lockinfo[lockinfo])
        itm.setData(8, Qt.DisplayRole, self.yesno[uptodate])
        itm.setData(9, Qt.DisplayRole, revision)
        itm.setData(10, Qt.DisplayRole, change)
        itm.setData(11, Qt.DisplayRole, author)
        itm.setData(12, Qt.DisplayRole, path)
        
        itm.setTextAlignment(1, Qt.AlignLeft)
        itm.setTextAlignment(2, Qt.AlignHCenter)
        itm.setTextAlignment(3, Qt.AlignHCenter)
        itm.setTextAlignment(4, Qt.AlignHCenter)
        itm.setTextAlignment(5, Qt.AlignHCenter)
        itm.setTextAlignment(6, Qt.AlignHCenter)
        itm.setTextAlignment(7, Qt.AlignHCenter)
        itm.setTextAlignment(8, Qt.AlignHCenter)
        itm.setTextAlignment(9, Qt.AlignRight)
        itm.setTextAlignment(10, Qt.AlignRight)
        itm.setTextAlignment(11, Qt.AlignLeft)
        itm.setTextAlignment(12, Qt.AlignLeft)
        
        if status in [pysvn.wc_status_kind.added,
                      pysvn.wc_status_kind.deleted,
                      pysvn.wc_status_kind.modified] or \
           propStatus in [pysvn.wc_status_kind.added,
                          pysvn.wc_status_kind.deleted,
                          pysvn.wc_status_kind.modified]:
            itm.setFlags(itm.flags() | Qt.ItemIsUserCheckable)
            itm.setCheckState(self.__toBeCommittedColumn, Qt.Checked)
        else:
            itm.setFlags(itm.flags() & ~Qt.ItemIsUserCheckable)
        
        if statusText not in self.__statusFilters:
            self.__statusFilters.append(statusText)
        
    def start(self, fn):
        """
        Public slot to start the svn status command.
        
        @param fn filename(s)/directoryname(s) to show the status of
            (string or list of strings)
        """
        self.errorGroup.hide()
        
        for act in self.menuactions:
            act.setEnabled(False)
        
        self.addButton.setEnabled(False)
        self.commitButton.setEnabled(False)
        self.diffButton.setEnabled(False)
        self.sbsDiffButton.setEnabled(False)
        self.revertButton.setEnabled(False)
        self.restoreButton.setEnabled(False)

        self.statusFilterCombo.clear()
        self.__statusFilters = []
        self.statusList.clear()
        self.shouldCancel = False
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        self.refreshButton.setEnabled(False)
        
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        
        self.args = fn
        
        self.setWindowTitle(self.tr('Subversion Status'))
        self.activateWindow()
        self.raise_()
        
        if isinstance(fn, list):
            self.dname, fnames = self.vcs.splitPathList(fn)
        else:
            self.dname, fname = self.vcs.splitPath(fn)
            fnames = [fname]
        
        opts = self.vcs.options['global'] + self.vcs.options['status']
        verbose = "--verbose" in opts
        recurse = "--non-recursive" not in opts
        update = "--show-updates" in opts
        
        hideChangelistColumn = True
        hidePropertyStatusColumn = True
        hideLockColumns = True
        hideUpToDateColumn = True
        hideHistoryColumn = True
        hideSwitchedColumn = True
        
        locker = QMutexLocker(self.vcs.vcsExecutionMutex)
        cwd = os.getcwd()
        os.chdir(self.dname)
        try:
            for name in fnames:
                # step 1: determine changelists and their files
                changelistsDict = {}
                if hasattr(self.client, 'get_changelist'):
                    if recurse:
                        depth = pysvn.depth.infinity
                    else:
                        depth = pysvn.depth.immediate
                    changelists = self.client.get_changelist(name, depth=depth)
                    for fpath, changelist in changelists:
                        if sys.version_info[0] == 2:
                            fpath = fpath.decode('utf-8')
                            changelist = changelist.decode('utf-8')
                        fpath = Utilities.normcasepath(fpath)
                        changelistsDict[fpath] = changelist
                hideChangelistColumn = hideChangelistColumn and \
                    len(changelistsDict) == 0
                
                # step 2: determine status of files
                allFiles = self.client.status(name, recurse=recurse,
                                              get_all=verbose, ignore=True,
                                              update=update)
                counter = 0
                for file in allFiles:
                    uptodate = True
                    if file.repos_text_status != pysvn.wc_status_kind.none:
                        uptodate = uptodate and \
                            file.repos_text_status != \
                            pysvn.wc_status_kind.modified
                    if file.repos_prop_status != pysvn.wc_status_kind.none:
                        uptodate = uptodate and \
                            file.repos_prop_status != \
                            pysvn.wc_status_kind.modified
                    
                    lockState = " "
                    if file.entry is not None and \
                       hasattr(file.entry, 'lock_token') and \
                       file.entry.lock_token is not None:
                        lockState = "L"
                    if hasattr(file, 'repos_lock') and update:
                        if lockState == "L" and file.repos_lock is None:
                            lockState = "B"
                        elif lockState == " " and file.repos_lock is not None:
                            lockState = "O"
                        elif lockState == "L" and \
                            file.repos_lock is not None and \
                            file.entry.lock_token != \
                                file.repos_lock["token"]:
                            lockState = "S"
                    
                    fpath = Utilities.normcasepath(
                        os.path.join(self.dname, file.path))
                    if fpath in changelistsDict:
                        changelist = changelistsDict[fpath]
                    else:
                        changelist = ""
                    
                    hidePropertyStatusColumn = hidePropertyStatusColumn and \
                        file.prop_status in [
                            pysvn.wc_status_kind.none,
                            pysvn.wc_status_kind.normal
                        ]
                    hideLockColumns = hideLockColumns and \
                        not file.is_locked and lockState == " "
                    hideUpToDateColumn = hideUpToDateColumn and uptodate
                    hideHistoryColumn = hideHistoryColumn and \
                        not file.is_copied
                    hideSwitchedColumn = hideSwitchedColumn and \
                        not file.is_switched
                    
                    self.__generateItem(
                        changelist,
                        file.text_status,
                        file.prop_status,
                        file.is_locked,
                        file.is_copied,
                        file.is_switched,
                        lockState,
                        uptodate,
                        file.entry and file.entry.revision.number or "",
                        file.entry and file.entry.commit_revision.number or "",
                        file.entry and file.entry.commit_author or "",
                        file.path
                    )
                    counter += 1
                    if counter == 30:
                        # check for cancel every 30 items
                        counter = 0
                        if self._clientCancelCallback():
                            break
                if self._clientCancelCallback():
                    break
        except pysvn.ClientError as e:
            self.__showError(e.args[0] + '\n')
        
        self.statusList.setColumnHidden(self.__propStatusColumn,
                                        hidePropertyStatusColumn)
        self.statusList.setColumnHidden(self.__lockedColumn,
                                        hideLockColumns)
        self.statusList.setColumnHidden(self.__lockinfoColumn,
                                        hideLockColumns)
        self.statusList.setColumnHidden(self.__upToDateColumn,
                                        hideUpToDateColumn)
        self.statusList.setColumnHidden(self.__historyColumn,
                                        hideHistoryColumn)
        self.statusList.setColumnHidden(self.__switchedColumn,
                                        hideSwitchedColumn)
        self.statusList.setColumnHidden(self.__changelistColumn,
                                        hideChangelistColumn)
        
        locker.unlock()
        self.__finish()
        os.chdir(cwd)
        
    def __finish(self):
        """
        Private slot called when the process finished or the user pressed
        the button.
        """
        QApplication.restoreOverrideCursor()
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.refreshButton.setEnabled(True)
        self.__updateButtons()
        self.__updateCommitButton()
        
        self.__statusFilters.sort()
        self.__statusFilters.insert(0, "<{0}>".format(self.tr("all")))
        self.statusFilterCombo.addItems(self.__statusFilters)
        
        for act in self.menuactions:
            act.setEnabled(True)
        
        self.__resizeColumns()
        self.__resort()
        
        self._cancel()
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.__finish()
        elif button == self.refreshButton:
            self.on_refreshButton_clicked()
        
    @pyqtSlot()
    def on_refreshButton_clicked(self):
        """
        Private slot to refresh the status display.
        """
        self.start(self.args)
        
    def __showError(self, msg):
        """
        Private slot to show an error message.
        
        @param msg error message to show (string)
        """
        self.errorGroup.show()
        self.errors.insertPlainText(msg)
        self.errors.ensureCursorVisible()
    
    def __updateButtons(self):
        """
        Private method to update the VCS buttons status.
        """
        modified = len(self.__getModifiedItems())
        unversioned = len(self.__getUnversionedItems())
        missing = len(self.__getMissingItems())

        self.addButton.setEnabled(unversioned)
        self.diffButton.setEnabled(modified)
        self.sbsDiffButton.setEnabled(modified == 1)
        self.revertButton.setEnabled(modified)
        self.restoreButton.setEnabled(missing)
    
    def __updateCommitButton(self):
        """
        Private method to update the Commit button status.
        """
        commitable = len(self.__getCommitableItems())
        self.commitButton.setEnabled(commitable)
    
    @pyqtSlot(str)
    def on_statusFilterCombo_activated(self, txt):
        """
        Private slot to react to the selection of a status filter.
        
        @param txt selected status filter (string)
        """
        if txt == "<{0}>".format(self.tr("all")):
            for topIndex in range(self.statusList.topLevelItemCount()):
                topItem = self.statusList.topLevelItem(topIndex)
                topItem.setHidden(False)
        else:
            for topIndex in range(self.statusList.topLevelItemCount()):
                topItem = self.statusList.topLevelItem(topIndex)
                topItem.setHidden(topItem.text(self.__statusColumn) != txt)
    
    @pyqtSlot(QTreeWidgetItem, int)
    def on_statusList_itemChanged(self, item, column):
        """
        Private slot to act upon item changes.
        
        @param item reference to the changed item (QTreeWidgetItem)
        @param column index of column that changed (integer)
        """
        if column == self.__toBeCommittedColumn:
            self.__updateCommitButton()
    
    @pyqtSlot()
    def on_statusList_itemSelectionChanged(self):
        """
        Private slot to act upon changes of selected items.
        """
        self.__updateButtons()
    
    @pyqtSlot()
    def on_commitButton_clicked(self):
        """
        Private slot to handle the press of the Commit button.
        """
        self.__commit()
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to handle the press of the Add button.
        """
        self.__add()
    
    @pyqtSlot()
    def on_diffButton_clicked(self):
        """
        Private slot to handle the press of the Differences button.
        """
        self.__diff()
    
    @pyqtSlot()
    def on_sbsDiffButton_clicked(self):
        """
        Private slot to handle the press of the Side-by-Side Diff button.
        """
        self.__sbsDiff()
    
    @pyqtSlot()
    def on_revertButton_clicked(self):
        """
        Private slot to handle the press of the Revert button.
        """
        self.__revert()
    
    @pyqtSlot()
    def on_restoreButton_clicked(self):
        """
        Private slot to handle the press of the Restore button.
        """
        self.__restoreMissing()
    
    ###########################################################################
    ## Context menu handling methods
    ###########################################################################
    
    def __showContextMenu(self, coord):
        """
        Private slot to show the context menu of the status list.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        self.menu.popup(self.statusList.mapToGlobal(coord))
        
    def __commit(self):
        """
        Private slot to handle the Commit context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn))
                 for itm in self.__getCommitableItems()]
        if not names:
            E5MessageBox.information(
                self,
                self.tr("Commit"),
                self.tr("""There are no entries selected to be"""
                        """ committed."""))
            return
        
        if Preferences.getVCS("AutoSaveFiles"):
            vm = e5App().getObject("ViewManager")
            for name in names:
                vm.saveEditor(name)
        self.vcs.vcsCommit(names, '')
       
    def __committed(self):
        """
        Private slot called after the commit has finished.
        """
        if self.isVisible():
            self.on_refreshButton_clicked()
            self.vcs.checkVCSStatus()
        
    def __commitSelectAll(self):
        """
        Private slot to select all entries for commit.
        """
        self.__commitSelect(True)
    
    def __commitDeselectAll(self):
        """
        Private slot to deselect all entries from commit.
        """
        self.__commitSelect(False)
    
    def __add(self):
        """
        Private slot to handle the Add context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn))
                 for itm in self.__getUnversionedItems()]
        if not names:
            E5MessageBox.information(
                self,
                self.tr("Add"),
                self.tr("""There are no unversioned entries"""
                        """ available/selected."""))
            return
        
        self.vcs.vcsAdd(names)
        self.on_refreshButton_clicked()
        
        project = e5App().getObject("Project")
        for name in names:
            project.getModel().updateVCSStatus(name)
        self.vcs.checkVCSStatus()

    def __revert(self):
        """
        Private slot to handle the Revert context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn))
                 for itm in self.__getModifiedItems()]
        if not names:
            E5MessageBox.information(
                self,
                self.tr("Revert"),
                self.tr("""There are no uncommitted changes"""
                        """ available/selected."""))
            return
        
        self.vcs.vcsRevert(names)
        self.raise_()
        self.activateWindow()
        self.on_refreshButton_clicked()
        
        project = e5App().getObject("Project")
        for name in names:
            project.getModel().updateVCSStatus(name)
        self.vcs.checkVCSStatus()
        
    def __restoreMissing(self):
        """
        Private slot to handle the Restore Missing context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn))
                 for itm in self.__getMissingItems()]
        if not names:
            E5MessageBox.information(
                self,
                self.tr("Revert"),
                self.tr("""There are no missing entries"""
                        """ available/selected."""))
            return
        
        self.vcs.vcsRevert(names)
        self.on_refreshButton_clicked()
        self.vcs.checkVCSStatus()
        
    def __diff(self):
        """
        Private slot to handle the Diff context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn))
                 for itm in self.__getModifiedItems()]
        if not names:
            E5MessageBox.information(
                self,
                self.tr("Differences"),
                self.tr("""There are no uncommitted changes"""
                        """ available/selected."""))
            return
        
        if self.diff is None:
            from .SvnDiffDialog import SvnDiffDialog
            self.diff = SvnDiffDialog(self.vcs)
        self.diff.show()
        QApplication.processEvents()
        self.diff.start(names, refreshable=True)
    
    def __sbsDiff(self):
        """
        Private slot to handle the Side-by-Side Diff context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn))
                 for itm in self.__getModifiedItems()]
        if not names:
            E5MessageBox.information(
                self,
                self.tr("Side-by-Side Diff"),
                self.tr("""There are no uncommitted changes"""
                        """ available/selected."""))
            return
        elif len(names) > 1:
            E5MessageBox.information(
                self,
                self.tr("Side-by-Side Diff"),
                self.tr("""Only one file with uncommitted changes"""
                        """ must be selected."""))
            return
        
        self.vcs.svnSbsDiff(names[0])
    
    def __lock(self):
        """
        Private slot to handle the Lock context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn))
                 for itm in self.__getLockActionItems(self.unlockedIndicators)]
        if not names:
            E5MessageBox.information(
                self,
                self.tr("Lock"),
                self.tr("""There are no unlocked files"""
                        """ available/selected."""))
            return
        
        self.vcs.svnLock(names, parent=self)
        self.on_refreshButton_clicked()
        
    def __unlock(self):
        """
        Private slot to handle the Unlock context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn))
                 for itm in self.__getLockActionItems(self.lockedIndicators)]
        if not names:
            E5MessageBox.information(
                self,
                self.tr("Unlock"),
                self.tr("""There are no locked files"""
                        """ available/selected."""))
            return
        
        self.vcs.svnUnlock(names, parent=self)
        self.on_refreshButton_clicked()
        
    def __breakLock(self):
        """
        Private slot to handle the Break Lock context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn))
                 for itm in self.__getLockActionItems(
                     self.stealBreakLockIndicators)]
        if not names:
            E5MessageBox.information(
                self,
                self.tr("Break Lock"),
                self.tr("""There are no locked files"""
                        """ available/selected."""))
            return
        
        self.vcs.svnUnlock(names, parent=self, breakIt=True)
        self.on_refreshButton_clicked()

    def __stealLock(self):
        """
        Private slot to handle the Break Lock context menu entry.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn))
                 for itm in self.__getLockActionItems(
                     self.stealBreakLockIndicators)]
        if not names:
            E5MessageBox.information(
                self,
                self.tr("Steal Lock"),
                self.tr("""There are no locked files"""
                        """ available/selected."""))
            return
        
        self.vcs.svnLock(names, parent=self, stealIt=True)
        self.on_refreshButton_clicked()

    def __addToChangelist(self):
        """
        Private slot to add entries to a changelist.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn))
                 for itm in self.__getNonChangelistItems()]
        if not names:
            E5MessageBox.information(
                self,
                self.tr("Remove from Changelist"),
                self.tr(
                    """There are no files available/selected not """
                    """belonging to a changelist."""
                )
            )
            return
        self.vcs.svnAddToChangelist(names)
        self.on_refreshButton_clicked()

    def __removeFromChangelist(self):
        """
        Private slot to remove entries from their changelists.
        """
        names = [os.path.join(self.dname, itm.text(self.__pathColumn))
                 for itm in self.__getChangelistItems()]
        if not names:
            E5MessageBox.information(
                self,
                self.tr("Remove from Changelist"),
                self.tr(
                    """There are no files available/selected belonging"""
                    """ to a changelist."""
                )
            )
            return
        self.vcs.svnRemoveFromChangelist(names)
        self.on_refreshButton_clicked()

    def __getCommitableItems(self):
        """
        Private method to retrieve all entries the user wants to commit.
        
        @return list of all items, the user has checked
        """
        commitableItems = []
        for index in range(self.statusList.topLevelItemCount()):
            itm = self.statusList.topLevelItem(index)
            if itm.checkState(self.__toBeCommittedColumn) == Qt.Checked:
                commitableItems.append(itm)
        return commitableItems
    
    def __getModifiedItems(self):
        """
        Private method to retrieve all entries, that have a modified status.
        
        @return list of all items with a modified status
        """
        modifiedItems = []
        for itm in self.statusList.selectedItems():
            if itm.text(self.__statusColumn) in self.modifiedIndicators or \
               itm.text(self.__propStatusColumn) in self.modifiedIndicators:
                modifiedItems.append(itm)
        return modifiedItems
        
    def __getUnversionedItems(self):
        """
        Private method to retrieve all entries, that have an
        unversioned status.
        
        @return list of all items with an unversioned status
        """
        unversionedItems = []
        for itm in self.statusList.selectedItems():
            if itm.text(self.__statusColumn) in self.unversionedIndicators:
                unversionedItems.append(itm)
        return unversionedItems
        
    def __getMissingItems(self):
        """
        Private method to retrieve all entries, that have a missing status.
        
        @return list of all items with a missing status
        """
        missingItems = []
        for itm in self.statusList.selectedItems():
            if itm.text(self.__statusColumn) in self.missingIndicators:
                missingItems.append(itm)
        return missingItems
        
    def __getLockActionItems(self, indicators):
        """
        Private method to retrieve all entries, that have a locked status.
        
        @param indicators list of indicators to check against (list of strings)
        @return list of all items with a locked status
        """
        lockitems = []
        for itm in self.statusList.selectedItems():
            if itm.text(self.__lockinfoColumn) in indicators:
                lockitems.append(itm)
        return lockitems
        
    def __getChangelistItems(self):
        """
        Private method to retrieve all entries, that are members of
        a changelist.
        
        @return list of all items belonging to a changelist
        """
        clitems = []
        for itm in self.statusList.selectedItems():
            if itm.text(self.__changelistColumn):
                clitems.append(itm)
        return clitems
        
    def __getNonChangelistItems(self):
        """
        Private method to retrieve all entries, that are not members of
        a changelist.
        
        @return list of all items not belonging to a changelist
        """
        clitems = []
        for itm in self.statusList.selectedItems():
            if not itm.text(self.__changelistColumn):
                clitems.append(itm)
        return clitems
    
    def __commitSelect(self, selected):
        """
        Private slot to select or deselect all entries.
        
        @param selected commit selection state to be set (boolean)
        """
        for index in range(self.statusList.topLevelItemCount()):
            itm = self.statusList.topLevelItem(index)
            if itm.flags() & Qt.ItemIsUserCheckable:
                if selected:
                    itm.setCheckState(self.__toBeCommittedColumn, Qt.Checked)
                else:
                    itm.setCheckState(self.__toBeCommittedColumn, Qt.Unchecked)
