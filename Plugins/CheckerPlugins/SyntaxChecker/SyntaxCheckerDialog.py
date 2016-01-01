# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a simple Python syntax checker.
"""

from __future__ import unicode_literals

import os
import fnmatch

from PyQt5.QtCore import pyqtSlot, Qt, QTimer
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QTreeWidgetItem, \
    QApplication, QHeaderView

from E5Gui.E5Application import e5App

from .Ui_SyntaxCheckerDialog import Ui_SyntaxCheckerDialog

import Utilities
import UI.PixmapCache


class SyntaxCheckerDialog(QDialog, Ui_SyntaxCheckerDialog):
    """
    Class implementing a dialog to display the results of a syntax check run.
    """
    filenameRole = Qt.UserRole + 1
    lineRole = Qt.UserRole + 2
    indexRole = Qt.UserRole + 3
    errorRole = Qt.UserRole + 4
    warningRole = Qt.UserRole + 5
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent The parent widget. (QWidget)
        """
        super(SyntaxCheckerDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.showButton = self.buttonBox.addButton(
            self.tr("Show"), QDialogButtonBox.ActionRole)
        self.showButton.setToolTip(
            self.tr("Press to show all files containing an issue"))
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.resultList.headerItem().setText(self.resultList.columnCount(), "")
        self.resultList.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.noResults = True
        self.cancelled = False
        self.__lastFileItem = None
        self.__finished = True
        self.__errorItem = None
        
        self.__fileList = []
        self.__project = None
        self.filterFrame.setVisible(False)
        
        self.checkProgress.setVisible(False)
        self.checkProgressLabel.setVisible(False)
        self.checkProgressLabel.setMaximumWidth(600)
        
        try:
            self.syntaxCheckService = e5App().getObject('SyntaxCheckService')
            self.syntaxCheckService.syntaxChecked.connect(self.__processResult)
            self.syntaxCheckService.batchFinished.connect(self.__batchFinished)
            self.syntaxCheckService.error.connect(self.__processError)
        except KeyError:
            self.syntaxCheckService = None
        self.filename = None
        
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.resultList.sortItems(self.resultList.sortColumn(),
                                  self.resultList.header().sortIndicatorOrder()
                                  )
    
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
        
    def __createResultItem(self, filename, line, index, error, sourcecode,
                           isWarning=False):
        """
        Private method to create an entry in the result list.
        
        @param filename file name of file (string)
        @param line line number of faulty source (integer or string)
        @param index index number of fault (integer)
        @param error error text (string)
        @param sourcecode faulty line of code (string)
        @param isWarning flag indicating a warning message (boolean)
        """
        if self.__lastFileItem is None or \
                self.__lastFileItem.data(0, self.filenameRole) != filename:
            # It's a new file
            self.__lastFileItem = QTreeWidgetItem(self.resultList, [
                self.__project.getRelativePath(filename)])
            self.__lastFileItem.setFirstColumnSpanned(True)
            self.__lastFileItem.setExpanded(True)
            self.__lastFileItem.setData(0, self.filenameRole, filename)
        
        itm = QTreeWidgetItem(self.__lastFileItem)
        if isWarning:
            itm.setIcon(0, UI.PixmapCache.getIcon("warning.png"))
        else:
            itm.setIcon(0, UI.PixmapCache.getIcon("syntaxError.png"))
        itm.setData(0, Qt.DisplayRole, line)
        itm.setData(1, Qt.DisplayRole, error)
        itm.setData(2, Qt.DisplayRole, sourcecode)
        itm.setData(0, self.filenameRole, filename)
        itm.setData(0, self.lineRole, int(line))
        itm.setData(0, self.indexRole, index)
        itm.setData(0, self.errorRole, error)
        itm.setData(0, self.warningRole, isWarning)
        
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
        
        self.__data = self.__project.getData("CHECKERSPARMS", "SyntaxChecker")
        if self.__data is None or "ExcludeFiles" not in self.__data:
            self.__data = {"ExcludeFiles": ""}
        self.excludeFilesEdit.setText(self.__data["ExcludeFiles"])
        
    def start(self, fn, codestring=""):
        """
        Public slot to start the syntax check.
        
        @param fn file or list of files or directory to be checked
                (string or list of strings)
        @param codestring string containing the code to be checked (string).
            If this is given, fn must be a single file name.
        """
        if self.syntaxCheckService is not None:
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
                for ext in self.syntaxCheckService.getExtensions():
                    self.files.extend(
                        Utilities.direntries(fn, True, '*{0}'.format(ext), 0))
            else:
                self.files = [fn]
            
            self.__errorItem = None
            self.__clearErrors(self.files)
            
            if codestring or len(self.files) > 0:
                self.checkProgress.setMaximum(max(1, len(self.files)))
                self.checkProgress.setVisible(len(self.files) > 1)
                self.checkProgressLabel.setVisible(len(self.files) > 1)
                QApplication.processEvents()

                # now go through all the files
                self.progress = 0
                self.files.sort()
                if codestring or len(self.files) == 1:
                    self.__batch = False
                    self.check(codestring)
                else:
                    self.__batch = True
                    self.checkBatch()
    
    def check(self, codestring=''):
        """
        Public method to start a check for one file.
        
        The results are reported to the __processResult slot.
        @keyparam codestring optional sourcestring (str)
        """
        if self.syntaxCheckService is None or not self.files:
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
        
        self.__lastFileItem = None
        
        if codestring:
            self.source = codestring
        else:
            try:
                self.source = Utilities.readEncodedFile(self.filename)[0]
                self.source = Utilities.normalizeCode(self.source)
            except (UnicodeError, IOError) as msg:
                self.noResults = False
                self.__createResultItem(
                    self.filename, 1, 0,
                    self.tr("Error: {0}").format(str(msg))
                    .rstrip(), "")
                self.progress += 1
                # Continue with next file
                self.check()
                return
        
        self.__finished = False
        self.syntaxCheckService.syntaxCheck(None, self.filename, self.source)

    def checkBatch(self):
        """
        Public method to start a style check batch job.
        
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
                    self.filename, 1, 0,
                    self.tr("Error: {0}").format(str(msg))
                    .rstrip(), "")
                continue
            
            argumentsList.append((filename, source))
        
        # reset the progress bar to the checked files
        self.checkProgress.setValue(self.progress)
        self.checkProgressLabel.setPath(self.tr("Transferring data..."))
        QApplication.processEvents()
        
        self.__finished = False
        self.syntaxCheckService.syntaxBatchCheck(argumentsList)
    
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
    
    def __processResult(self, fn, problems):
        """
        Private slot to display the reported messages.
        
        @param fn filename of the checked file (str)
        @param problems dictionary with the keys 'error' and 'warnings' which
            hold a list containing details about the error/ warnings
            (file name, line number, column, codestring (only at syntax
            errors), the message) (dict)
        """
        if self.__finished:
            return
        
        # Check if it's the requested file, otherwise ignore signal if not
        # in batch mode
        if not self.__batch and fn != self.filename:
            return

        error = problems.get('error')
        if error:
            self.noResults = False
            _fn, lineno, col, code, msg = error
            self.__createResultItem(_fn, lineno, col, msg, code, False)
        
        warnings = problems.get('warnings', [])
        if warnings:
            if self.__batch:
                try:
                    source = Utilities.readEncodedFile(fn)[0]
                    source = Utilities.normalizeCode(source)
                    source = source.splitlines()
                except (UnicodeError, IOError):
                    source = ""
            else:
                source = self.source.splitlines()
            for _fn, lineno, col, code, msg in warnings:
                self.noResults = False
                if source:
                    try:
                        scr_line = source[lineno - 1].strip()
                    except IndexError:
                        scr_line = ""
                else:
                    scr_line = ""
                self.__createResultItem(_fn, lineno, col, msg, scr_line, True)

        self.progress += 1
        self.checkProgress.setValue(self.progress)
        self.checkProgressLabel.setPath(fn)
        QApplication.processEvents()
        self.__resort()

        if not self.__batch:
            self.check()
        
    def __finish(self):
        """
        Private slot called when the syntax check finished or the user
        pressed the button.
        """
        if not self.__finished:
            self.__finished = True
            
            self.cancelled = True
            self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
            self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
            self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
            
            if self.noResults:
                QTreeWidgetItem(self.resultList, [self.tr('No issues found.')])
                QApplication.processEvents()
                self.showButton.setEnabled(False)
            else:
                self.showButton.setEnabled(True)
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
                self.syntaxCheckService.cancelSyntaxBatchCheck()
                QTimer.singleShot(1000, self.__finish)
            else:
                self.__finish()
        elif button == self.showButton:
            self.on_showButton_clicked()
        
    @pyqtSlot()
    def on_startButton_clicked(self):
        """
        Private slot to start a syntax check run.
        """
        fileList = self.__fileList[:]
        
        filterString = self.excludeFilesEdit.text()
        if "ExcludeFiles" not in self.__data or \
           filterString != self.__data["ExcludeFiles"]:
            self.__data["ExcludeFiles"] = filterString
            self.__project.setData("CHECKERSPARMS", "SyntaxChecker",
                                   self.__data)
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
        
        vm = e5App().getObject("ViewManager")
        
        if itm.parent():
            fn = Utilities.normabspath(itm.data(0, self.filenameRole))
            lineno = itm.data(0, self.lineRole)
            index = itm.data(0, self.indexRole)
            error = itm.data(0, self.errorRole)
            
            vm.openSourceFile(fn, lineno)
            editor = vm.getOpenEditor(fn)
            
            if itm.data(0, self.warningRole):
                editor.toggleWarning(lineno, 0, True, error)
            else:
                editor.toggleSyntaxError(lineno, index, True, error, show=True)
        else:
            fn = Utilities.normabspath(itm.data(0, self.filenameRole))
            vm.openSourceFile(fn)
            editor = vm.getOpenEditor(fn)
            for index in range(itm.childCount()):
                citm = itm.child(index)
                lineno = citm.data(0, self.lineRole)
                index = citm.data(0, self.indexRole)
                error = citm.data(0, self.errorRole)
                if citm.data(0, self.warningRole):
                    editor.toggleWarning(lineno, 0, True, error)
                else:
                    editor.toggleSyntaxError(
                        lineno, index, True, error, show=True)
        
        editor = vm.activeWindow()
        editor.updateVerticalScrollBar()
        
    @pyqtSlot()
    def on_showButton_clicked(self):
        """
        Private slot to handle the "Show" button press.
        """
        vm = e5App().getObject("ViewManager")
        
        selectedIndexes = []
        for index in range(self.resultList.topLevelItemCount()):
            if self.resultList.topLevelItem(index).isSelected():
                selectedIndexes.append(index)
        if len(selectedIndexes) == 0:
            selectedIndexes = list(range(self.resultList.topLevelItemCount()))
        for index in selectedIndexes:
            itm = self.resultList.topLevelItem(index)
            fn = Utilities.normabspath(itm.data(0, self.filenameRole))
            vm.openSourceFile(fn, 1)
            editor = vm.getOpenEditor(fn)
            editor.clearSyntaxError()
            editor.clearFlakesWarnings()
            for cindex in range(itm.childCount()):
                citm = itm.child(cindex)
                lineno = citm.data(0, self.lineRole)
                index = citm.data(0, self.indexRole)
                error = citm.data(0, self.errorRole)
                if citm.data(0, self.warningRole):
                    editor.toggleWarning(lineno, 0, True, error)
                else:
                    editor.toggleSyntaxError(
                        lineno, index, True, error, show=True)
        
        # go through the list again to clear syntax error and
        # flakes warning markers for files, that are ok
        openFiles = vm.getOpenFilenames()
        errorFiles = []
        for index in range(self.resultList.topLevelItemCount()):
            itm = self.resultList.topLevelItem(index)
            errorFiles.append(
                Utilities.normabspath(itm.data(0, self.filenameRole)))
        for file in openFiles:
            if file not in errorFiles:
                editor = vm.getOpenEditor(file)
                editor.clearSyntaxError()
                editor.clearFlakesWarnings()
        
        editor = vm.activeWindow()
        editor.updateVerticalScrollBar()
        
    def __clearErrors(self, files):
        """
        Private method to clear all error and warning markers of
        open editors to be checked.
        
        @param files list of files to be checked (list of string)
        """
        vm = e5App().getObject("ViewManager")
        openFiles = vm.getOpenFilenames()
        for file in [f for f in openFiles if f in files]:
            editor = vm.getOpenEditor(file)
            editor.clearSyntaxError()
            editor.clearFlakesWarnings()
