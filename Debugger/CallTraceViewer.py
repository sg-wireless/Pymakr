# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Call Trace viewer widget.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QRegExp, QFileInfo
from PyQt5.QtWidgets import QWidget, QTreeWidgetItem

from E5Gui.E5Application import e5App
from E5Gui import E5FileDialog, E5MessageBox

from .Ui_CallTraceViewer import Ui_CallTraceViewer

import UI.PixmapCache
import Preferences
import Utilities


class CallTraceViewer(QWidget, Ui_CallTraceViewer):
    """
    Class implementing the Call Trace viewer widget.
    
    @signal sourceFile(str, int) emitted to show the source of a call/return
        point
    """
    sourceFile = pyqtSignal(str, int)
    
    def __init__(self, debugServer, parent=None):
        """
        Constructor
        
        @param debugServer reference to the debug server object (DebugServer)
        @param parent reference to the parent widget (QWidget)
        """
        super(CallTraceViewer, self).__init__(parent)
        self.setupUi(self)
        
        self.__dbs = debugServer
        
        self.startTraceButton.setIcon(
            UI.PixmapCache.getIcon("callTraceStart.png"))
        self.stopTraceButton.setIcon(
            UI.PixmapCache.getIcon("callTraceStop.png"))
        self.resizeButton.setIcon(UI.PixmapCache.getIcon("resizeColumns.png"))
        self.clearButton.setIcon(UI.PixmapCache.getIcon("editDelete.png"))
        self.saveButton.setIcon(UI.PixmapCache.getIcon("fileSave.png"))
        
        self.__headerItem = QTreeWidgetItem(
            ["", self.tr("From"), self.tr("To")])
        self.__headerItem.setIcon(0, UI.PixmapCache.getIcon("callReturn.png"))
        self.callTrace.setHeaderItem(self.__headerItem)
        
        self.__callStack = []
        
        self.__entryFormat = "{0}:{1} ({2})"
        self.__entryRe = QRegExp(r"""(.+):(\d+)\s\((.*)\)""")
        
        self.__projectMode = False
        self.__project = None
        
        self.__callTraceEnabled = Preferences.toBool(
            Preferences.Prefs.settings.value("CallTrace/Enabled", False))
        if self.__callTraceEnabled:
            self.startTraceButton.setEnabled(False)
        else:
            self.stopTraceButton.setEnabled(False)
        
        self.__dbs.callTraceInfo.connect(self.__addCallTraceInfo)
    
    def __setCallTraceEnabled(self, enabled):
        """
        Private slot to set the call trace enabled status.
        
        @param enabled flag indicating the new state (boolean)
        """
        self.__dbs.setCallTraceEnabled(enabled)
        self.stopTraceButton.setEnabled(enabled)
        self.startTraceButton.setEnabled(not enabled)
        self.__callTraceEnabled = enabled
        Preferences.Prefs.settings.setValue("CallTrace/Enabled", enabled)
    
    @pyqtSlot()
    def on_startTraceButton_clicked(self):
        """
        Private slot to start call tracing.
        """
        self.__setCallTraceEnabled(True)
    
    @pyqtSlot()
    def on_stopTraceButton_clicked(self):
        """
        Private slot to start call tracing.
        """
        self.__setCallTraceEnabled(False)
    
    @pyqtSlot()
    def on_resizeButton_clicked(self):
        """
        Private slot to resize the columns of the call trace to their contents.
        """
        for column in range(self.callTrace.columnCount()):
            self.callTrace.resizeColumnToContents(column)
    
    @pyqtSlot()
    def on_clearButton_clicked(self):
        """
        Private slot to clear the call trace.
        """
        self.clear()
    
    @pyqtSlot()
    def on_saveButton_clicked(self):
        """
        Private slot to save the call trace info to a file.
        """
        if self.callTrace.topLevelItemCount() > 0:
            fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
                self,
                self.tr("Save Call Trace Info"),
                "",
                self.tr("Text Files (*.txt);;All Files (*)"),
                None,
                E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
            if fname:
                ext = QFileInfo(fname).suffix()
                if not ext:
                    ex = selectedFilter.split("(*")[1].split(")")[0]
                    if ex:
                        fname += ex
                if QFileInfo(fname).exists():
                    res = E5MessageBox.yesNo(
                        self,
                        self.tr("Save Call Trace Info"),
                        self.tr("<p>The file <b>{0}</b> already exists."
                                " Overwrite it?</p>").format(fname),
                        icon=E5MessageBox.Warning)
                    if not res:
                        return
                    fname = Utilities.toNativeSeparators(fname)
                
                try:
                    f = open(fname, "w", encoding="utf-8")
                    itm = self.callTrace.topLevelItem(0)
                    while itm is not None:
                        isCall = itm.data(0, Qt.UserRole)
                        if isCall:
                            call = "->"
                        else:
                            call = "<-"
                        f.write("{0} {1} || {2}\n".format(
                            call,
                            itm.text(1), itm.text(2)))
                        itm = self.callTrace.itemBelow(itm)
                    f.close()
                except IOError as err:
                    E5MessageBox.critical(
                        self,
                        self.tr("Error saving Call Trace Info"),
                        self.tr("""<p>The call trace info could not"""
                                """ be written to <b>{0}</b></p>"""
                                """<p>Reason: {1}</p>""")
                        .format(fname, str(err)))
    
    @pyqtSlot(QTreeWidgetItem, int)
    def on_callTrace_itemDoubleClicked(self, item, column):
        """
        Private slot to open the double clicked file in an editor.
        
        @param item reference to the double clicked item (QTreeWidgetItem)
        @param column column that was double clicked (integer)
        """
        if item is not None and column > 0:
            columnStr = item.text(column)
            if self.__entryRe.exactMatch(columnStr.strip()):
                filename, lineno, func = self.__entryRe.capturedTexts()[1:]
                try:
                    lineno = int(lineno)
                except ValueError:
                    # do nothing, if the line info is not an integer
                    return
                if self.__projectMode:
                    filename = self.__project.getAbsolutePath(filename)
                self.sourceFile.emit(filename, lineno)
    
    def clear(self):
        """
        Public slot to clear the call trace info.
        """
        self.callTrace.clear()
        self.__callStack = []
    
    def setProjectMode(self, enabled):
        """
        Public slot to set the call trace viewer to project mode.
        
        In project mode the call trace info is shown with project relative
        path names.
        
        @param enabled flag indicating to enable the project mode (boolean)
        """
        self.__projectMode = enabled
        if enabled and self.__project is None:
            self.__project = e5App().getObject("Project")
    
    def __addCallTraceInfo(self, isCall, fromFile, fromLine, fromFunction,
                           toFile, toLine, toFunction):
        """
        Private method to add an entry to the call trace viewer.
        
        @param isCall flag indicating a 'call' (boolean)
        @param fromFile name of the originating file (string)
        @param fromLine line number in the originating file (string)
        @param fromFunction name of the originating function (string)
        @param toFile name of the target file (string)
        @param toLine line number in the target file (string)
        @param toFunction name of the target function (string)
        """
        if isCall:
            icon = UI.PixmapCache.getIcon("forward.png")
        else:
            icon = UI.PixmapCache.getIcon("back.png")
        parentItem = \
            self.__callStack[-1] if self.__callStack else self.callTrace
        
        if self.__projectMode:
            fromFile = self.__project.getRelativePath(fromFile)
            toFile = self.__project.getRelativePath(toFile)
        
        itm = QTreeWidgetItem(
            parentItem,
            ["",
             self.__entryFormat.format(fromFile, fromLine, fromFunction),
             self.__entryFormat.format(toFile, toLine, toFunction)])
        itm.setIcon(0, icon)
        itm.setData(0, Qt.UserRole, isCall)
        itm.setExpanded(True)
        
        if isCall:
            self.__callStack.append(itm)
        else:
            if self.__callStack:
                self.__callStack.pop(-1)
    
    def isCallTraceEnabled(self):
        """
        Public method to get the state of the call trace function.
        
        @return flag indicating the state of the call trace function (boolean)
        """
        return self.__callTraceEnabled
