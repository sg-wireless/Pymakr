# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the tabnanny command
process.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os
import fnmatch

from PyQt5.QtCore import pyqtSlot, Qt, QTimer
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QTreeWidgetItem, \
    QApplication, QHeaderView

from E5Gui.E5Application import e5App

from .Ui_TabnannyDialog import Ui_TabnannyDialog

import Utilities
import Preferences


class TabnannyDialog(QDialog, Ui_TabnannyDialog):
    """
    Class implementing a dialog to show the results of the tabnanny check run.
    """
    filenameRole = Qt.UserRole + 1
    
    def __init__(self, indentCheckService, parent=None):
        """
        Constructor
        
        @param indentCheckService reference to the service (IndentCheckService)
        @param parent The parent widget (QWidget).
        """
        super(TabnannyDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.resultList.headerItem().setText(self.resultList.columnCount(), "")
        self.resultList.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.indentCheckService = indentCheckService
        self.indentCheckService.indentChecked.connect(self.__processResult)
        self.indentCheckService.batchFinished.connect(self.__batchFinished)
        self.indentCheckService.error.connect(self.__processError)
        self.filename = None
        
        self.noResults = True
        self.cancelled = False
        self.__finished = True
        self.__errorItem = None
        
        self.__fileList = []
        self.__project = None
        self.filterFrame.setVisible(False)
        
        self.checkProgress.setVisible(False)
        self.checkProgressLabel.setVisible(False)
        self.checkProgressLabel.setMaximumWidth(600)
        
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.resultList.sortItems(
            self.resultList.sortColumn(),
            self.resultList.header().sortIndicatorOrder())
    
    def __createErrorItem(self, filename, message):
        """
        Private slot to create a new error item in the result list.
        
        @param filename name of the file
        @type str
        @param message error message
        @type str
        """
        if self.__errorItem is None:
            self.__errorItem = QTreeWidgetItem(self.resultList, [
                self.tr("Errors")])
            self.__errorItem.setExpanded(True)
            self.__errorItem.setForeground(0, Qt.red)
        
        msg = "{0} ({1})".format(self.__project.getRelativePath(filename),
                                 message)
        if not self.resultList.findItems(msg, Qt.MatchExactly):
            itm = QTreeWidgetItem(self.__errorItem, [msg])
            itm.setForeground(0, Qt.red)
            itm.setFirstColumnSpanned(True)
        
    def __createResultItem(self, filename, line, sourcecode):
        """
        Private method to create an entry in the result list.
        
        @param filename filename of file (string)
        @param line linenumber of faulty source (integer or string)
        @param sourcecode faulty line of code (string)
        """
        itm = QTreeWidgetItem(self.resultList)
        itm.setData(0, Qt.DisplayRole,
                    self.__project.getRelativePath(filename))
        itm.setData(1, Qt.DisplayRole, line)
        itm.setData(2, Qt.DisplayRole, sourcecode)
        itm.setTextAlignment(1, Qt.AlignRight)
        itm.setData(0, self.filenameRole, filename)
        
    def prepare(self, fileList, project):
        """
        Public method to prepare the dialog with a list of filenames.
        
        @param fileList list of filenames (list of strings)
        @param project reference to the project object (Project)
        """
        self.__fileList = fileList[:]
        self.__project = project
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.filterFrame.setVisible(True)
        
        self.__data = self.__project.getData("CHECKERSPARMS", "Tabnanny")
        if self.__data is None or "ExcludeFiles" not in self.__data:
            self.__data = {"ExcludeFiles": ""}
        self.excludeFilesEdit.setText(self.__data["ExcludeFiles"])
        
    def start(self, fn):
        """
        Public slot to start the tabnanny check.
        
        @param fn File or list of files or directory to be checked
                (string or list of strings)
        """
        if self.__project is None:
            self.__project = e5App().getObject("Project")
        
        self.cancelled = False
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        self.checkProgress.setVisible(True)
        QApplication.processEvents()
        
        if isinstance(fn, list):
            self.files = fn
        elif os.path.isdir(fn):
            self.files = []
            extensions = set(Preferences.getPython("PythonExtensions") +
                             Preferences.getPython("Python3Extensions"))
            for ext in extensions:
                self.files.extend(
                    Utilities.direntries(fn, True, '*{0}'.format(ext), 0))
        else:
            self.files = [fn]
        
        self.__errorItem = None
        
        if len(self.files) > 0:
            self.checkProgress.setMaximum(len(self.files))
            self.checkProgress.setVisible(len(self.files) > 1)
            self.checkProgressLabel.setVisible(len(self.files) > 1)
            QApplication.processEvents()
            
            # now go through all the files
            self.progress = 0
            self.files.sort()
            if len(self.files) == 1:
                self.__batch = False
                self.check()
            else:
                self.__batch = True
                self.checkBatch()

    def check(self, codestring=''):
        """
        Public method to start an indentation check for one file.
        
        The results are reported to the __processResult slot.
        @keyparam codestring optional sourcestring (str)
        """
        if not self.files:
            self.checkProgressLabel.setPath("")
            self.checkProgress.setMaximum(1)
            self.checkProgress.setValue(1)
            self.__finish()
            return
        
        self.filename = self.files.pop(0)
        self.checkProgress.setValue(self.progress)
        self.checkProgressLabel.setPath(self.filename)
        QApplication.processEvents()
        self.__resort()
        
        if self.cancelled:
            return
        
        try:
            self.source = Utilities.readEncodedFile(self.filename)[0]
            self.source = Utilities.normalizeCode(self.source)
        except (UnicodeError, IOError) as msg:
            self.noResults = False
            self.__createResultItem(
                self.filename, 1,
                "Error: {0}".format(str(msg)).rstrip())
            self.progress += 1
            # Continue with next file
            self.check()
            return

        self.__finished = False
        self.indentCheckService.indentCheck(
            None, self.filename, self.source)

    def checkBatch(self):
        """
        Public method to start an indentation check batch job.
        
        The results are reported to the __processResult slot.
        """
        self.__lastFileItem = None
        
        self.checkProgressLabel.setPath(self.tr("Preparing files..."))
        progress = 0
        
        argumentsList = []
        for filename in self.files:
            progress += 1
            self.checkProgress.setValue(progress)
            QApplication.processEvents()
            
            try:
                source = Utilities.readEncodedFile(filename)[0]
                source = Utilities.normalizeCode(source)
            except (UnicodeError, IOError) as msg:
                self.noResults = False
                self.__createResultItem(
                    filename, 1,
                    "Error: {0}".format(str(msg)).rstrip())
                continue
            
            argumentsList.append((filename, source))
        
        # reset the progress bar to the checked files
        self.checkProgress.setValue(self.progress)
        self.checkProgressLabel.setPath(self.tr("Transferring data..."))
        QApplication.processEvents()
        
        self.__finished = False
        self.indentCheckService.indentBatchCheck(argumentsList)
    
    def __batchFinished(self):
        """
        Private slot handling the completion of a batch job.
        """
        self.checkProgressLabel.setPath("")
        self.checkProgress.setMaximum(1)
        self.checkProgress.setValue(1)
        self.__finish()
    
    def __processError(self, fn, msg):
        """
        Private slot to process an error indication from the service.
        
        @param fn filename of the file
        @type str
        @param msg error message
        @type str
        """
        self.__createErrorItem(fn, msg)
        
        if not self.__batch:
            self.check()
    
    def __processResult(self, fn, nok, line, error):
        """
        Private slot called after perfoming a style check on one file.
        
        @param fn filename of the just checked file (str)
        @param nok flag if a problem was found (bool)
        @param line line number (str)
        @param error text of the problem (str)
        """
        if self.__finished:
            return
        
        # Check if it's the requested file, otherwise ignore signal if not
        # in batch mode
        if not self.__batch and fn != self.filename:
            return
        
        if nok:
            self.noResults = False
            self.__createResultItem(fn, line, error.rstrip())
        self.progress += 1
        
        self.checkProgress.setValue(self.progress)
        self.checkProgressLabel.setPath(fn)
        QApplication.processEvents()
        self.__resort()
        
        if not self.__batch:
            self.check()

    def __finish(self):
        """
        Private slot called when the action or the user pressed the button.
        """
        if not self.__finished:
            self.__finished = True
            
            self.cancelled = True
            self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
            self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
            self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
            
            if self.noResults:
                self.__createResultItem(
                    self.tr('No indentation errors found.'), "", "")
                QApplication.processEvents()
            self.resultList.header().resizeSections(
                QHeaderView.ResizeToContents)
            self.resultList.header().setStretchLastSection(True)
            
            self.checkProgress.setVisible(False)
            self.checkProgressLabel.setVisible(False)
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            if self.__batch:
                self.indentCheckService.cancelIndentBatchCheck()
                QTimer.singleShot(1000, self.__finish)
            else:
                self.__finish()
        
    @pyqtSlot()
    def on_startButton_clicked(self):
        """
        Private slot to start a code metrics run.
        """
        fileList = self.__fileList[:]
        
        filterString = self.excludeFilesEdit.text()
        if "ExcludeFiles" not in self.__data or \
           filterString != self.__data["ExcludeFiles"]:
            self.__data["ExcludeFiles"] = filterString
            self.__project.setData("CHECKERSPARMS", "Tabnanny", self.__data)
        filterList = [f.strip() for f in filterString.split(",")
                      if f.strip()]
        if filterList:
            for filter in filterList:
                fileList = \
                    [f for f in fileList if not fnmatch.fnmatch(f, filter)]
        
        self.resultList.clear()
        self.noResults = True
        self.cancelled = False
        self.start(fileList)
        
    def on_resultList_itemActivated(self, itm, col):
        """
        Private slot to handle the activation of an item.
        
        @param itm reference to the activated item (QTreeWidgetItem)
        @param col column the item was activated in (integer)
        """
        if self.noResults:
            return
        
        fn = Utilities.normabspath(itm.data(0, self.filenameRole))
        lineno = int(itm.text(1))
        
        e5App().getObject("ViewManager").openSourceFile(fn, lineno)
