# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a code metrics dialog.
"""

from __future__ import unicode_literals

import os
import fnmatch

from PyQt5.QtCore import pyqtSlot, Qt, QLocale, qVersion
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMenu, QHeaderView, \
    QTreeWidgetItem, QApplication

from .Ui_CodeMetricsDialog import Ui_CodeMetricsDialog
from . import CodeMetrics

import Utilities


class CodeMetricsDialog(QDialog, Ui_CodeMetricsDialog):
    """
    Class implementing a dialog to display the code metrics.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        """
        super(CodeMetricsDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.summaryList.headerItem().setText(
            self.summaryList.columnCount(), "")
        self.summaryList.header().resizeSection(0, 200)
        self.summaryList.header().resizeSection(1, 100)
        
        self.resultList.headerItem().setText(self.resultList.columnCount(), "")
        
        self.cancelled = False
        
        self.__menu = QMenu(self)
        self.__menu.addAction(self.tr("Collapse all"),
                              self.__resultCollapse)
        self.__menu.addAction(self.tr("Expand all"), self.__resultExpand)
        self.resultList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.resultList.customContextMenuRequested.connect(
            self.__showContextMenu)
        
        self.__fileList = []
        self.__project = None
        self.filterFrame.setVisible(False)
        
    def __resizeResultColumns(self):
        """
        Private method to resize the list columns.
        """
        self.resultList.header().resizeSections(QHeaderView.ResizeToContents)
        self.resultList.header().setStretchLastSection(True)
        
    def __createResultItem(self, parent, values):
        """
        Private slot to create a new item in the result list.
        
        @param parent parent of the new item (QTreeWidget or QTreeWidgetItem)
        @param values values to be displayed (list)
        @return the generated item
        """
        data = [values[0]]
        for value in values[1:]:
            try:
                data.append("{0:5}".format(int(value)))
            except ValueError:
                data.append(value)
        itm = QTreeWidgetItem(parent, data)
        for col in range(1, 7):
            itm.setTextAlignment(col, Qt.Alignment(Qt.AlignRight))
        return itm
        
    def __resizeSummaryColumns(self):
        """
        Private method to resize the list columns.
        """
        self.summaryList.header().resizeSections(QHeaderView.ResizeToContents)
        self.summaryList.header().setStretchLastSection(True)
        
    def __createSummaryItem(self, col0, col1):
        """
        Private slot to create a new item in the summary list.
        
        @param col0 string for column 0 (string)
        @param col1 string for column 1 (string)
        """
        itm = QTreeWidgetItem(self.summaryList, [col0, col1])
        itm.setTextAlignment(1, Qt.Alignment(Qt.AlignRight))
        
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
        
        self.__data = self.__project.getData("OTHERTOOLSPARMS", "CodeMetrics")
        if self.__data is None or "ExcludeFiles" not in self.__data:
            self.__data = {"ExcludeFiles": ""}
        self.excludeFilesEdit.setText(self.__data["ExcludeFiles"])
        
    def start(self, fn):
        """
        Public slot to start the code metrics determination.
        
        @param fn file or list of files or directory to show
                the code metrics for (string or list of strings)
        """
        self.cancelled = False
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        QApplication.processEvents()
        
        loc = QLocale()
        if isinstance(fn, list):
            files = fn
        elif os.path.isdir(fn):
            files = Utilities.direntries(fn, True, '*.py', False)
        else:
            files = [fn]
        files.sort()
        # check for missing files
        for f in files[:]:
            if not os.path.exists(f):
                files.remove(f)
        
        self.checkProgress.setMaximum(len(files))
        QApplication.processEvents()
        
        total = {}
        CodeMetrics.summarize(total, 'files', len(files))
        
        progress = 0
        
        try:
            # disable updates of the list for speed
            self.resultList.setUpdatesEnabled(False)
            self.resultList.setSortingEnabled(False)
            
            # now go through all the files
            for file in files:
                if self.cancelled:
                    return
                
                stats = CodeMetrics.analyze(file, total)
                
                v = self.__getValues(loc, stats, 'TOTAL ')
                fitm = self.__createResultItem(self.resultList, [file] + v)
                
                identifiers = stats.identifiers
                for identifier in identifiers:
                    v = self.__getValues(loc, stats, identifier)
                    
                    self.__createResultItem(fitm, [identifier] + v)
                self.resultList.expandItem(fitm)
                
                progress += 1
                self.checkProgress.setValue(progress)
                QApplication.processEvents()
        finally:
            # reenable updates of the list
            self.resultList.setSortingEnabled(True)
            self.resultList.setUpdatesEnabled(True)
        self.__resizeResultColumns()
        
        # now do the summary stuff
        self.__createSummaryItem(self.tr("files"),
                                 loc.toString(total['files']))
        self.__createSummaryItem(self.tr("lines"),
                                 loc.toString(total['lines']))
        self.__createSummaryItem(self.tr("bytes"),
                                 loc.toString(total['bytes']))
        self.__createSummaryItem(self.tr("comments"),
                                 loc.toString(total['comments']))
        self.__createSummaryItem(self.tr("comment lines"),
                                 loc.toString(total['commentlines']))
        self.__createSummaryItem(self.tr("empty lines"),
                                 loc.toString(total['empty lines']))
        self.__createSummaryItem(self.tr("non-commentary lines"),
                                 loc.toString(total['non-commentary lines']))
        self.__resizeSummaryColumns()
        self.__finish()
        
    def __getValues(self, loc, stats, identifier):
        """
        Private method to extract the code metric values.
        
        @param loc reference to the locale object (QLocale)
        @param stats reference to the code metric statistics object
        @param identifier identifier to get values for
        @return list of values suitable for display (list of strings)
        """
        counters = stats.counters.get(identifier, {})
        v = []
        for key in ('start', 'end', 'lines', 'nloc', 'commentlines', 'empty'):
            if counters.get(key, 0):
                v.append(loc.toString(counters[key]))
            else:
                v.append('')
        return v
        
    def __finish(self):
        """
        Private slot called when the action finished or the user pressed the
        button.
        """
        self.cancelled = True
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        if qVersion() >= "5.0.0":
            self.resultList.header().setSectionResizeMode(
                QHeaderView.Interactive)
            self.summaryList.header().setSectionResizeMode(
                QHeaderView.Interactive)
        else:
            self.resultList.header().setResizeMode(QHeaderView.Interactive)
            self.summaryList.header().setResizeMode(QHeaderView.Interactive)
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
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
            self.__project.setData("OTHERTOOLSPARMS", "CodeMetrics",
                                   self.__data)
        filterList = filterString.split(",")
        if filterList:
            for filter in filterList:
                fileList = [f for f in fileList
                            if not fnmatch.fnmatch(f, filter.strip())]
        
        self.resultList.clear()
        self.summaryList.clear()
        self.start(fileList)
        
    def __showContextMenu(self, coord):
        """
        Private slot to show the context menu of the listview.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        if self.resultList.topLevelItemCount() > 0:
            self.__menu.popup(self.mapToGlobal(coord))
        
    def __resultCollapse(self):
        """
        Private slot to collapse all entries of the resultlist.
        """
        for index in range(self.resultList.topLevelItemCount()):
            self.resultList.topLevelItem(index).setExpanded(False)
        
    def __resultExpand(self):
        """
        Private slot to expand all entries of the resultlist.
        """
        for index in range(self.resultList.topLevelItemCount()):
            self.resultList.topLevelItem(index).setExpanded(True)
