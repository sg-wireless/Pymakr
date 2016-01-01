# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a Python code coverage dialog.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMenu, QHeaderView, \
    QTreeWidgetItem, QApplication

from E5Gui import E5MessageBox
from E5Gui.E5Application import e5App
from E5Gui.E5ProgressDialog import E5ProgressDialog

from .Ui_PyCoverageDialog import Ui_PyCoverageDialog

import Utilities
from coverage import coverage
from coverage.misc import CoverageException


class PyCoverageDialog(QDialog, Ui_PyCoverageDialog):
    """
    Class implementing a dialog to display the collected code coverage data.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        """
        super(PyCoverageDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.summaryList.headerItem().setText(
            self.summaryList.columnCount(), "")
        self.resultList.headerItem().setText(self.resultList.columnCount(), "")
        
        self.cancelled = False
        self.path = '.'
        self.reload = False
        
        self.excludeList = ['# *pragma[: ]*[nN][oO] *[cC][oO][vV][eE][rR]']
        
        self.__menu = QMenu(self)
        self.__menu.addSeparator()
        self.openAct = self.__menu.addAction(
            self.tr("Open"), self.__openFile)
        self.__menu.addSeparator()
        self.annotate = self.__menu.addAction(
            self.tr('Annotate'), self.__annotate)
        self.__menu.addAction(self.tr('Annotate all'), self.__annotateAll)
        self.__menu.addAction(
            self.tr('Delete annotated files'), self.__deleteAnnotated)
        self.__menu.addSeparator()
        self.__menu.addAction(self.tr('Erase Coverage Info'), self.__erase)
        self.resultList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.resultList.customContextMenuRequested.connect(
            self.__showContextMenu)
    
    def __format_lines(self, lines):
        """
        Private method to format a list of integers into string by coalescing
        groups.
        
        @param lines list of integers
        @return string representing the list
        """
        pairs = []
        lines.sort()
        maxValue = lines[-1]
        start = None
        
        i = lines[0]
        while i <= maxValue:
            try:
                if start is None:
                    start = i
                ind = lines.index(i)
                end = i
                i += 1
            except ValueError:
                pairs.append((start, end))
                start = None
                if ind + 1 >= len(lines):
                    break
                i = lines[ind + 1]
        if start:
            pairs.append((start, end))
        
        def stringify(pair):
            """
            Private helper function to generate a string representation of a
            pair.
            
            @param pair pair of integers
            """
            start, end = pair
            if start == end:
                return "{0:d}".format(start)
            else:
                return "{0:d}-{1:d}".format(start, end)
        
        return ", ".join(map(stringify, pairs))
    
    def __createResultItem(self, file, statements, executed, coverage,
                           excluded, missing):
        """
        Private method to create an entry in the result list.
        
        @param file filename of file (string)
        @param statements amount of statements (integer)
        @param executed amount of executed statements (integer)
        @param coverage percent of coverage (integer)
        @param excluded list of excluded lines (string)
        @param missing list of lines without coverage (string)
        """
        itm = QTreeWidgetItem(self.resultList, [
            file,
            str(statements),
            str(executed),
            "{0:.0f}%".format(coverage),
            excluded,
            missing
        ])
        for col in range(1, 4):
            itm.setTextAlignment(col, Qt.AlignRight)
        if statements != executed:
            font = itm.font(0)
            font.setBold(True)
            for col in range(itm.columnCount()):
                itm.setFont(col, font)
        
    def start(self, cfn, fn):
        """
        Public slot to start the coverage data evaluation.
        
        @param cfn basename of the coverage file (string)
        @param fn file or list of files or directory to be checked
                (string or list of strings)
        """
        self.__cfn = cfn
        self.__fn = fn
        
        self.basename = os.path.splitext(cfn)[0]
        
        self.cfn = "{0}.coverage".format(self.basename)
        
        if isinstance(fn, list):
            files = fn
            self.path = os.path.dirname(cfn)
        elif os.path.isdir(fn):
            files = Utilities.direntries(fn, True, '*.py', False)
            self.path = fn
        else:
            files = [fn]
            self.path = os.path.dirname(cfn)
        files.sort()
        
        cover = coverage(data_file=self.cfn)
        cover.load()
        
        # set the exclude pattern
        self.excludeCombo.clear()
        self.excludeCombo.addItems(self.excludeList)
        
        self.checkProgress.setMaximum(len(files))
        QApplication.processEvents()
        
        total_statements = 0
        total_executed = 0
        total_exceptions = 0
        
        cover.exclude(self.excludeList[0])
        progress = 0
        
        try:
            # disable updates of the list for speed
            self.resultList.setUpdatesEnabled(False)
            self.resultList.setSortingEnabled(False)
            
            # now go through all the files
            for file in files:
                if self.cancelled:
                    return
                
                try:
                    statements, excluded, missing, readable = \
                        cover.analysis2(file)[1:]
                    readableEx = (excluded and self.__format_lines(excluded)
                                  or '')
                    n = len(statements)
                    m = n - len(missing)
                    if n > 0:
                        pc = 100.0 * m / n
                    else:
                        pc = 100.0
                    self.__createResultItem(
                        file, str(n), str(m), pc, readableEx, readable)
                    
                    total_statements = total_statements + n
                    total_executed = total_executed + m
                except CoverageException:
                    total_exceptions += 1
                
                progress += 1
                self.checkProgress.setValue(progress)
                QApplication.processEvents()
        finally:
            # reenable updates of the list
            self.resultList.setSortingEnabled(True)
            self.resultList.setUpdatesEnabled(True)
            self.checkProgress.reset()
        
        # show summary info
        if len(files) > 1:
            if total_statements > 0:
                pc = 100.0 * total_executed / total_statements
            else:
                pc = 100.0
            itm = QTreeWidgetItem(self.summaryList, [
                str(total_statements),
                str(total_executed),
                "{0:.0f}%".format(pc)
            ])
            for col in range(0, 3):
                itm.setTextAlignment(col, Qt.AlignRight)
        else:
            self.summaryGroup.hide()
        
        if total_exceptions:
            E5MessageBox.warning(
                self,
                self.tr("Parse Error"),
                self.tr("""%n file(s) could not be parsed. Coverage"""
                        """ info for these is not available.""", "",
                        total_exceptions))
        
        self.__finish()
        
    def __finish(self):
        """
        Private slot called when the action finished or the user pressed the
        button.
        """
        self.cancelled = True
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        QApplication.processEvents()
        self.resultList.header().resizeSections(QHeaderView.ResizeToContents)
        self.resultList.header().setStretchLastSection(True)
        self.summaryList.header().resizeSections(QHeaderView.ResizeToContents)
        self.summaryList.header().setStretchLastSection(True)
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.__finish()
        
    def __showContextMenu(self, coord):
        """
        Private slot to show the context menu of the listview.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        itm = self.resultList.itemAt(coord)
        if itm:
            self.annotate.setEnabled(True)
            self.openAct.setEnabled(True)
        else:
            self.annotate.setEnabled(False)
            self.openAct.setEnabled(False)
        self.__menu.popup(self.mapToGlobal(coord))
        
    def __openFile(self, itm=None):
        """
        Private slot to open the selected file.
        
        @param itm reference to the item to be opened (QTreeWidgetItem)
        """
        if itm is None:
            itm = self.resultList.currentItem()
        fn = itm.text(0)
        
        vm = e5App().getObject("ViewManager")
        vm.openSourceFile(fn)
        editor = vm.getOpenEditor(fn)
        editor.codeCoverageShowAnnotations()
        
    def __annotate(self):
        """
        Private slot to handle the annotate context menu action.
        
        This method produce an annotated coverage file of the
        selected file.
        """
        itm = self.resultList.currentItem()
        fn = itm.text(0)
        
        cover = coverage(data_file=self.cfn)
        cover.exclude(self.excludeList[0])
        cover.load()
        cover.annotate([fn], None, True)
        
    def __annotateAll(self):
        """
        Private slot to handle the annotate all context menu action.
        
        This method produce an annotated coverage file of every
        file listed in the listview.
        """
        amount = self.resultList.topLevelItemCount()
        if amount == 0:
            return
        
        # get list of all filenames
        files = []
        for index in range(amount):
            itm = self.resultList.topLevelItem(index)
            files.append(itm.text(0))
        
        cover = coverage(data_file=self.cfn)
        cover.exclude(self.excludeList[0])
        cover.load()
        
        # now process them
        progress = E5ProgressDialog(
            self.tr("Annotating files..."), self.tr("Abort"),
            0, len(files), self.tr("%v/%m Files"), self)
        progress.setMinimumDuration(0)
        progress.setWindowTitle(self.tr("Coverage"))
        count = 0
        
        for file in files:
            progress.setValue(count)
            if progress.wasCanceled():
                break
            cover.annotate([file], None)  # , True)
            count += 1
        
        progress.setValue(len(files))
        
    def __erase(self):
        """
        Private slot to handle the erase context menu action.
        
        This method erases the collected coverage data that is
        stored in the .coverage file.
        """
        cover = coverage(data_file=self.cfn)
        cover.load()
        cover.erase()
        
        self.reloadButton.setEnabled(False)
        self.resultList.clear()
        self.summaryList.clear()
        
    def __deleteAnnotated(self):
        """
        Private slot to handle the delete annotated context menu action.
        
        This method deletes all annotated files. These are files
        ending with ',cover'.
        """
        files = Utilities.direntries(self.path, True, '*,cover', False)
        for file in files:
            try:
                os.remove(file)
            except EnvironmentError:
                pass

    @pyqtSlot()
    def on_reloadButton_clicked(self):
        """
        Private slot to reload the coverage info.
        """
        self.resultList.clear()
        self.summaryList.clear()
        self.reload = True
        excludePattern = self.excludeCombo.currentText()
        if excludePattern in self.excludeList:
            self.excludeList.remove(excludePattern)
        self.excludeList.insert(0, excludePattern)
        self.cancelled = False
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        self.start(self.__cfn, self.__fn)
    
    @pyqtSlot(QTreeWidgetItem, int)
    def on_resultList_itemActivated(self, item, column):
        """
        Private slot to handle the activation of an item.
        
        @param item reference to the activated item (QTreeWidgetItem)
        @param column column the item was activated in (integer)
        """
        self.__openFile(item)
