# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the subversion repository browser dialog.
"""

from __future__ import unicode_literals

import pysvn

from PyQt5.QtCore import QMutexLocker, Qt, pyqtSlot
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QHeaderView, QDialog, QApplication, \
    QDialogButtonBox, QTreeWidgetItem

from E5Gui import E5MessageBox

from .SvnUtilities import formatTime
from .SvnDialogMixin import SvnDialogMixin

from .Ui_SvnRepoBrowserDialog import Ui_SvnRepoBrowserDialog

import UI.PixmapCache


class SvnRepoBrowserDialog(QDialog, SvnDialogMixin, Ui_SvnRepoBrowserDialog):
    """
    Class implementing the subversion repository browser dialog.
    """
    def __init__(self, vcs, mode="browse", parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param mode mode of the dialog (string, "browse" or "select")
        @param parent parent widget (QWidget)
        """
        super(SvnRepoBrowserDialog, self).__init__(parent)
        self.setupUi(self)
        SvnDialogMixin.__init__(self)
        self.setWindowFlags(Qt.Window)
        
        self.repoTree.headerItem().setText(self.repoTree.columnCount(), "")
        self.repoTree.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.vcs = vcs
        self.mode = mode
        
        if self.mode == "select":
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
            self.buttonBox.button(QDialogButtonBox.Close).hide()
        else:
            self.buttonBox.button(QDialogButtonBox.Ok).hide()
            self.buttonBox.button(QDialogButtonBox.Cancel).hide()
        
        self.__dirIcon = UI.PixmapCache.getIcon("dirClosed.png")
        self.__fileIcon = UI.PixmapCache.getIcon("fileMisc.png")
        
        self.__urlRole = Qt.UserRole
        self.__ignoreExpand = False
        
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
        self.repoTree.sortItems(
            self.repoTree.sortColumn(),
            self.repoTree.header().sortIndicatorOrder())
    
    def __resizeColumns(self):
        """
        Private method to resize the tree columns.
        """
        self.repoTree.header().resizeSections(QHeaderView.ResizeToContents)
        self.repoTree.header().setStretchLastSection(True)
    
    def __generateItem(self, parent, repopath, revision, author, size, date,
                       nodekind, url):
        """
        Private method to generate a tree item in the repository tree.
        
        @param parent parent of the item to be created (QTreeWidget or
            QTreeWidgetItem)
        @param repopath path of the item (string)
        @param revision revision info (string or pysvn.opt_revision_kind)
        @param author author info (string)
        @param size size info (integer)
        @param date date info (integer)
        @param nodekind node kind info (pysvn.node_kind)
        @param url url of the entry (string)
        @return reference to the generated item (QTreeWidgetItem)
        """
        if repopath == "/":
            path = url
        else:
            path = url.split("/")[-1]
        
        if revision == "":
            rev = ""
        else:
            rev = revision.number
        if date == "":
            dt = ""
        else:
            dt = formatTime(date)
        if author is None:
            author = ""
        
        itm = QTreeWidgetItem(parent)
        itm.setData(0, Qt.DisplayRole, path)
        itm.setData(1, Qt.DisplayRole, rev)
        itm.setData(2, Qt.DisplayRole, author)
        itm.setData(3, Qt.DisplayRole, size)
        itm.setData(4, Qt.DisplayRole, dt)
        
        if nodekind == pysvn.node_kind.dir:
            itm.setIcon(0, self.__dirIcon)
            itm.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        elif nodekind == pysvn.node_kind.file:
            itm.setIcon(0, self.__fileIcon)
        
        itm.setData(0, self.__urlRole, url)
        
        itm.setTextAlignment(0, Qt.AlignLeft)
        itm.setTextAlignment(1, Qt.AlignRight)
        itm.setTextAlignment(2, Qt.AlignLeft)
        itm.setTextAlignment(3, Qt.AlignRight)
        itm.setTextAlignment(4, Qt.AlignLeft)
        
        return itm
    
    def __listRepo(self, url, parent=None):
        """
        Private method to perform the svn list command.
        
        @param url the repository URL to browser (string)
        @param parent reference to the item, the data should be appended to
            (QTreeWidget or QTreeWidgetItem)
        """
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        
        if parent is None:
            parent = self.repoTree
        
        locker = QMutexLocker(self.vcs.vcsExecutionMutex)
        
        try:
            try:
                entries = self.client.list(url, recurse=False)
                firstTime = parent == self.repoTree
                # dirent elements are all unicode in Python 2
                for dirent, lock in entries:
                    if (firstTime and dirent["path"] != url) or \
                       (parent != self.repoTree and dirent["path"] == url):
                        continue
                    if firstTime:
                        if dirent["repos_path"] != "/":
                            repoUrl = dirent["path"].replace(
                                dirent["repos_path"], "")
                        else:
                            repoUrl = dirent["path"]
                        if repoUrl != url:
                            self.__ignoreExpand = True
                            itm = self.__generateItem(
                                parent, "/", "", "", 0, "",
                                pysvn.node_kind.dir, repoUrl)
                            itm.setExpanded(True)
                            parent = itm
                            urlPart = repoUrl
                            for element in \
                                    dirent["repos_path"].split("/")[:-1]:
                                if element:
                                    urlPart = "{0}/{1}".format(urlPart,
                                                               element)
                                    itm = self.__generateItem(
                                        parent, element, "", "", 0, "",
                                        pysvn.node_kind.dir, urlPart)
                                    itm.setExpanded(True)
                                    parent = itm
                            self.__ignoreExpand = False
                    itm = self.__generateItem(
                        parent, dirent["repos_path"], dirent["created_rev"],
                        dirent["last_author"], dirent["size"], dirent["time"],
                        dirent["kind"], dirent["path"])
                self.__resort()
                self.__resizeColumns()
            except pysvn.ClientError as e:
                self.__showError(e.args[0])
            except AttributeError:
                self.__showError(
                    self.tr("The installed version of PySvn should be "
                            "1.4.0 or better."))
        finally:
            locker.unlock()
            QApplication.restoreOverrideCursor()
    
    def __normalizeUrl(self, url):
        """
        Private method to normalite the url.
        
        @param url the url to normalize (string)
        @return normalized URL (string)
        """
        if url.endswith("/"):
            return url[:-1]
        return url
    
    def start(self, url):
        """
        Public slot to start the svn info command.
        
        @param url the repository URL to browser (string)
        """
        self.repoTree.clear()
        
        self.url = ""
        
        url = self.__normalizeUrl(url)
        if self.urlCombo.findText(url) == -1:
            self.urlCombo.addItem(url)
    
    @pyqtSlot(str)
    def on_urlCombo_currentIndexChanged(self, text):
        """
        Private slot called, when a new repository URL is entered or selected.
        
        @param text the text of the current item (string)
        """
        url = self.__normalizeUrl(text)
        if url != self.url:
            self.url = url
            self.repoTree.clear()
            self.__listRepo(url)
    
    @pyqtSlot(QTreeWidgetItem)
    def on_repoTree_itemExpanded(self, item):
        """
        Private slot called when an item is expanded.
        
        @param item reference to the item to be expanded (QTreeWidgetItem)
        """
        if not self.__ignoreExpand:
            url = item.data(0, self.__urlRole)
            self.__listRepo(url, item)
    
    @pyqtSlot(QTreeWidgetItem)
    def on_repoTree_itemCollapsed(self, item):
        """
        Private slot called when an item is collapsed.
        
        @param item reference to the item to be collapsed (QTreeWidgetItem)
        """
        for child in item.takeChildren():
            del child
    
    @pyqtSlot()
    def on_repoTree_itemSelectionChanged(self):
        """
        Private slot called when the selection changes.
        """
        if self.mode == "select":
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
    
    def __showError(self, msg):
        """
        Private slot to show an error message.
        
        @param msg error message to show (string)
        """
        E5MessageBox.critical(
            self,
            self.tr("Subversion Error"),
            msg)
    
    def accept(self):
        """
        Public slot called when the dialog is accepted.
        """
        if self.focusWidget() == self.urlCombo:
            return
        
        super(SvnRepoBrowserDialog, self).accept()
    
    def getSelectedUrl(self):
        """
        Public method to retrieve the selected repository URL.
        
        @return the selected repository URL (string)
        """
        items = self.repoTree.selectedItems()
        if len(items) == 1:
            return items[0].data(0, self.__urlRole)
        else:
            return ""
