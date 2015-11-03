# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Call Stack viewer widget.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt, QFileInfo
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu

from E5Gui.E5Application import e5App
from E5Gui import E5FileDialog, E5MessageBox

import Utilities


class CallStackViewer(QTreeWidget):
    """
    Class implementing the Call Stack viewer widget.
    
    @signal sourceFile(str, int) emitted to show the source of a stack entry
    @signal frameSelected(int) emitted to signal the selection of a frame entry
    """
    sourceFile = pyqtSignal(str, int)
    frameSelected = pyqtSignal(int)
    
    FilenameRole = Qt.UserRole + 1
    LinenoRole = Qt.UserRole + 2
    
    def __init__(self, debugServer, parent=None):
        """
        Constructor
        
        @param debugServer reference to the debug server object (DebugServer)
        @param parent reference to the parent widget (QWidget)
        """
        super(CallStackViewer, self).__init__(parent)
        
        self.setHeaderHidden(True)
        self.setAlternatingRowColors(True)
        self.setItemsExpandable(False)
        self.setRootIsDecorated(False)
        self.setWindowTitle(self.tr("Call Stack"))
        
        self.__menu = QMenu(self)
        self.__sourceAct = self.__menu.addAction(
            self.tr("Show source"), self.__openSource)
        self.__menu.addAction(self.tr("Clear"), self.clear)
        self.__menu.addSeparator()
        self.__menu.addAction(self.tr("Save"), self.__saveStackTrace)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__showContextMenu)
        
        self.__dbs = debugServer
        
        # file name, line number, function name, arguments
        self.__entryFormat = self.tr("File: {0}\nLine: {1}\n{2}{3}")
        # file name, line number
        self.__entryFormatShort = self.tr("File: {0}\nLine: {1}")
        
        self.__projectMode = False
        self.__project = None
        
        self.__dbs.clientStack.connect(self.__showCallStack)
        self.itemDoubleClicked.connect(self.__itemDoubleClicked)
    
    def setDebugger(self, debugUI):
        """
        Public method to set a reference to the Debug UI.
        
        @param debugUI reference to the DebugUI object (DebugUI)
        """
        debugUI.clientStack.connect(self.__showCallStack)
    
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
    
    def __showContextMenu(self, coord):
        """
        Private slot to show the context menu.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        if self.topLevelItemCount() > 0:
            itm = self.currentItem()
            self.__sourceAct.setEnabled(itm is not None)
            self.__menu.popup(self.mapToGlobal(coord))
    
    def __showCallStack(self, stack):
        """
        Private slot to show the call stack of the program being debugged.
        
        @param stack list of tuples with call stack data (file name,
            line number, function name, formatted argument/values list)
        """
        self.clear()
        for fname, fline, ffunc, fargs in stack:
            if self.__projectMode:
                dfname = self.__project.getRelativePath(fname)
            else:
                dfname = fname
            if ffunc and not ffunc.startswith("<"):
                # use normal format
                itm = QTreeWidgetItem(
                    self,
                    [self.__entryFormat.format(dfname, fline, ffunc, fargs)])
            else:
                # use short format
                itm = QTreeWidgetItem(
                    self, [self.__entryFormatShort.format(dfname, fline)])
            itm.setData(0, self.FilenameRole, fname)
            itm.setData(0, self.LinenoRole, fline)
        
        self.resizeColumnToContents(0)
    
    def __itemDoubleClicked(self, itm):
        """
        Private slot to handle a double click of a stack entry.
        
        @param itm reference to the double clicked item (QTreeWidgetItem)
        """
        fname = itm.data(0, self.FilenameRole)
        fline = itm.data(0, self.LinenoRole)
        if self.__projectMode:
            fname = self.__project.getAbsolutePath(fname)
        self.sourceFile.emit(fname, fline)
        
        index = self.indexOfTopLevelItem(itm)
        self.frameSelected.emit(index)
    
    def __openSource(self):
        """
        Private slot to show the source for the selected stack entry.
        """
        itm = self.currentItem()
        if itm:
            self.__itemDoubleClicked(itm)
    
    def __saveStackTrace(self):
        """
        Private slot to save the stack trace info to a file.
        """
        if self.topLevelItemCount() > 0:
            fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
                self,
                self.tr("Save Call Stack Info"),
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
                        self.tr("Save Call Stack Info"),
                        self.tr("<p>The file <b>{0}</b> already exists."
                                " Overwrite it?</p>").format(fname),
                        icon=E5MessageBox.Warning)
                    if not res:
                        return
                    fname = Utilities.toNativeSeparators(fname)
                
                try:
                    f = open(fname, "w", encoding="utf-8")
                    itm = self.topLevelItem(0)
                    while itm is not None:
                        f.write("{0}\n".format(itm.text(0)))
                        f.write(78 * "=" + "\n")
                        itm = self.itemBelow(itm)
                    f.close()
                except IOError as err:
                    E5MessageBox.critical(
                        self,
                        self.tr("Error saving Call Stack Info"),
                        self.tr("""<p>The call stack info could not be"""
                                """ written to <b>{0}</b></p>"""
                                """<p>Reason: {1}</p>""")
                        .format(fname, str(err)))
