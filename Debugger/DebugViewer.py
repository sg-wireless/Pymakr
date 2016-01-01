# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a widget containing various debug related views.

The views avaliable are:
<ul>
  <li>variables viewer for global variables</li>
  <li>variables viewer for local variables</li>
  <li>call trace viewer</li>
  <li>viewer for breakpoints</li>
  <li>viewer for watch expressions</li>
  <li>viewer for exceptions</li>
  <li>viewer for threads</li>
  <li>a file browser (optional)</li>
  <li>an interpreter shell (optional)</li>
</ul>
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, \
    QSizePolicy, QPushButton, QComboBox, QLabel, QTreeWidget, \
    QTreeWidgetItem, QHeaderView

import UI.PixmapCache
import Preferences

from E5Gui.E5TabWidget import E5TabWidget


class DebugViewer(QWidget):
    """
    Class implementing a widget containing various debug related views.
    
    The individual tabs contain the interpreter shell (optional),
    the filesystem browser (optional), the two variables viewers
    (global and local), a breakpoint viewer, a watch expression viewer and
    the exception logger. Additionally a list of all threads is shown.
    
    @signal sourceFile(string, int) emitted to open a source file at a line
    """
    sourceFile = pyqtSignal(str, int)
    
    def __init__(self, debugServer, docked, vm, parent=None,
                 embeddedShell=True, embeddedBrowser=True):
        """
        Constructor
        
        @param debugServer reference to the debug server object
        @param docked flag indicating a dock window
        @param vm reference to the viewmanager object
        @param parent parent widget (QWidget)
        @param embeddedShell flag indicating whether the shell should be
            included. This flag is set to False by those layouts, that have
            the interpreter shell in a separate window.
        @param embeddedBrowser flag indicating whether the file browser should
            be included. This flag is set to False by those layouts, that
            have the file browser in a separate window or embedded
            in the project browser instead.
        """
        super(DebugViewer, self).__init__(parent)
        
        self.debugServer = debugServer
        self.debugUI = None
        
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        
        self.__mainLayout = QVBoxLayout()
        self.__mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__mainLayout)
        
        self.__tabWidget = E5TabWidget()
        self.__mainLayout.addWidget(self.__tabWidget)
        
        self.embeddedShell = embeddedShell
        if embeddedShell:
            from QScintilla.Shell import ShellAssembly
            # add the interpreter shell
            self.shellAssembly = ShellAssembly(debugServer, vm, False)
            self.shell = self.shellAssembly.shell()
            index = self.__tabWidget.addTab(
                self.shellAssembly,
                UI.PixmapCache.getIcon("shell.png"), '')
            self.__tabWidget.setTabToolTip(index, self.shell.windowTitle())
        
        self.embeddedBrowser = embeddedBrowser
        if embeddedBrowser:
            from UI.Browser import Browser
            # add the browser
            self.browser = Browser()
            index = self.__tabWidget.addTab(
                self.browser,
                UI.PixmapCache.getIcon("browser.png"), '')
            self.__tabWidget.setTabToolTip(index, self.browser.windowTitle())
        
        from .VariablesViewer import VariablesViewer
        # add the global variables viewer
        self.glvWidget = QWidget()
        self.glvWidgetVLayout = QVBoxLayout(self.glvWidget)
        self.glvWidgetVLayout.setContentsMargins(0, 0, 0, 0)
        self.glvWidgetVLayout.setSpacing(3)
        self.glvWidget.setLayout(self.glvWidgetVLayout)
        
        self.globalsViewer = VariablesViewer(self.glvWidget, True)
        self.glvWidgetVLayout.addWidget(self.globalsViewer)
        
        self.glvWidgetHLayout = QHBoxLayout()
        self.glvWidgetHLayout.setContentsMargins(3, 3, 3, 3)
        
        self.globalsFilterEdit = QLineEdit(self.glvWidget)
        self.globalsFilterEdit.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.glvWidgetHLayout.addWidget(self.globalsFilterEdit)
        self.globalsFilterEdit.setToolTip(
            self.tr("Enter regular expression patterns separated by ';'"
                    " to define variable filters. "))
        self.globalsFilterEdit.setWhatsThis(
            self.tr("Enter regular expression patterns separated by ';'"
                    " to define variable filters. All variables and"
                    " class attributes matched by one of the expressions"
                    " are not shown in the list above."))
        
        self.setGlobalsFilterButton = QPushButton(
            self.tr('Set'), self.glvWidget)
        self.glvWidgetHLayout.addWidget(self.setGlobalsFilterButton)
        self.glvWidgetVLayout.addLayout(self.glvWidgetHLayout)
        
        index = self.__tabWidget.addTab(
            self.glvWidget,
            UI.PixmapCache.getIcon("globalVariables.png"), '')
        self.__tabWidget.setTabToolTip(index, self.globalsViewer.windowTitle())
        
        self.setGlobalsFilterButton.clicked.connect(
            self.__setGlobalsFilter)
        self.globalsFilterEdit.returnPressed.connect(self.__setGlobalsFilter)
        
        # add the local variables viewer
        self.lvWidget = QWidget()
        self.lvWidgetVLayout = QVBoxLayout(self.lvWidget)
        self.lvWidgetVLayout.setContentsMargins(0, 0, 0, 0)
        self.lvWidgetVLayout.setSpacing(3)
        self.lvWidget.setLayout(self.lvWidgetVLayout)
        
        self.lvWidgetHLayout1 = QHBoxLayout()
        self.lvWidgetHLayout1.setContentsMargins(3, 3, 3, 3)
        
        self.stackComboBox = QComboBox(self.lvWidget)
        self.stackComboBox.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.lvWidgetHLayout1.addWidget(self.stackComboBox)

        self.sourceButton = QPushButton(self.tr('Source'), self.lvWidget)
        self.lvWidgetHLayout1.addWidget(self.sourceButton)
        self.sourceButton.setEnabled(False)
        self.lvWidgetVLayout.addLayout(self.lvWidgetHLayout1)

        self.localsViewer = VariablesViewer(self.lvWidget, False)
        self.lvWidgetVLayout.addWidget(self.localsViewer)
        
        self.lvWidgetHLayout2 = QHBoxLayout()
        self.lvWidgetHLayout2.setContentsMargins(3, 3, 3, 3)
        
        self.localsFilterEdit = QLineEdit(self.lvWidget)
        self.localsFilterEdit.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.lvWidgetHLayout2.addWidget(self.localsFilterEdit)
        self.localsFilterEdit.setToolTip(
            self.tr(
                "Enter regular expression patterns separated by ';' to define "
                "variable filters. "))
        self.localsFilterEdit.setWhatsThis(
            self.tr(
                "Enter regular expression patterns separated by ';' to define "
                "variable filters. All variables and class attributes matched"
                " by one of the expressions are not shown in the list above."))
        
        self.setLocalsFilterButton = QPushButton(
            self.tr('Set'), self.lvWidget)
        self.lvWidgetHLayout2.addWidget(self.setLocalsFilterButton)
        self.lvWidgetVLayout.addLayout(self.lvWidgetHLayout2)
        
        index = self.__tabWidget.addTab(
            self.lvWidget,
            UI.PixmapCache.getIcon("localVariables.png"), '')
        self.__tabWidget.setTabToolTip(index, self.localsViewer.windowTitle())
        
        self.sourceButton.clicked.connect(self.__showSource)
        self.stackComboBox.currentIndexChanged[int].connect(
            self.__frameSelected)
        self.setLocalsFilterButton.clicked.connect(self.__setLocalsFilter)
        self.localsFilterEdit.returnPressed.connect(self.__setLocalsFilter)
        
        from .CallStackViewer import CallStackViewer
        # add the call stack viewer
        self.callStackViewer = CallStackViewer(self.debugServer)
        index = self.__tabWidget.addTab(
            self.callStackViewer,
            UI.PixmapCache.getIcon("step.png"), "")
        self.__tabWidget.setTabToolTip(
            index, self.callStackViewer.windowTitle())
        self.callStackViewer.sourceFile.connect(self.sourceFile)
        self.callStackViewer.frameSelected.connect(
            self.__callStackFrameSelected)
        
        from .CallTraceViewer import CallTraceViewer
        # add the call trace viewer
        self.callTraceViewer = CallTraceViewer(self.debugServer)
        index = self.__tabWidget.addTab(
            self.callTraceViewer,
            UI.PixmapCache.getIcon("callTrace.png"), "")
        self.__tabWidget.setTabToolTip(
            index, self.callTraceViewer.windowTitle())
        self.callTraceViewer.sourceFile.connect(self.sourceFile)
        
        from .BreakPointViewer import BreakPointViewer
        # add the breakpoint viewer
        self.breakpointViewer = BreakPointViewer()
        self.breakpointViewer.setModel(self.debugServer.getBreakPointModel())
        index = self.__tabWidget.addTab(
            self.breakpointViewer,
            UI.PixmapCache.getIcon("breakpoints.png"), '')
        self.__tabWidget.setTabToolTip(
            index, self.breakpointViewer.windowTitle())
        self.breakpointViewer.sourceFile.connect(self.sourceFile)
        
        from .WatchPointViewer import WatchPointViewer
        # add the watch expression viewer
        self.watchpointViewer = WatchPointViewer()
        self.watchpointViewer.setModel(self.debugServer.getWatchPointModel())
        index = self.__tabWidget.addTab(
            self.watchpointViewer,
            UI.PixmapCache.getIcon("watchpoints.png"), '')
        self.__tabWidget.setTabToolTip(
            index, self.watchpointViewer.windowTitle())
        
        from .ExceptionLogger import ExceptionLogger
        # add the exception logger
        self.exceptionLogger = ExceptionLogger()
        index = self.__tabWidget.addTab(
            self.exceptionLogger,
            UI.PixmapCache.getIcon("exceptions.png"), '')
        self.__tabWidget.setTabToolTip(
            index, self.exceptionLogger.windowTitle())
        
        if self.embeddedShell:
            self.__tabWidget.setCurrentWidget(self.shellAssembly)
        else:
            if self.embeddedBrowser:
                self.__tabWidget.setCurrentWidget(self.browser)
            else:
                self.__tabWidget.setCurrentWidget(self.glvWidget)
        
        # add the threads viewer
        self.__mainLayout.addWidget(QLabel(self.tr("Threads:")))
        self.__threadList = QTreeWidget()
        self.__threadList.setHeaderLabels(
            [self.tr("ID"), self.tr("Name"),
             self.tr("State"), ""])
        self.__threadList.setSortingEnabled(True)
        self.__mainLayout.addWidget(self.__threadList)
        
        self.__doThreadListUpdate = True
        
        self.__threadList.currentItemChanged.connect(self.__threadSelected)
        
        self.__mainLayout.setStretchFactor(self.__tabWidget, 5)
        self.__mainLayout.setStretchFactor(self.__threadList, 1)
        
        self.currPage = None
        self.currentStack = None
        self.framenr = 0
        
        self.debugServer.clientStack.connect(self.handleClientStack)
        
        self.__autoViewSource = Preferences.getDebugger("AutoViewSourceCode")
        self.sourceButton.setVisible(not self.__autoViewSource)
        
    def preferencesChanged(self):
        """
        Public slot to handle the preferencesChanged signal.
        """
        self.__autoViewSource = Preferences.getDebugger("AutoViewSourceCode")
        self.sourceButton.setVisible(not self.__autoViewSource)
        
    def setDebugger(self, debugUI):
        """
        Public method to set a reference to the Debug UI.
        
        @param debugUI reference to the DebugUI object (DebugUI)
        """
        self.debugUI = debugUI
        self.debugUI.clientStack.connect(self.handleClientStack)
        self.callStackViewer.setDebugger(debugUI)
        
    def handleResetUI(self):
        """
        Public method to reset the SBVviewer.
        """
        self.globalsViewer.handleResetUI()
        self.localsViewer.handleResetUI()
        self.__setGlobalsFilter()
        self.__setLocalsFilter()
        self.sourceButton.setEnabled(False)
        self.currentStack = None
        self.stackComboBox.clear()
        self.__threadList.clear()
        if self.embeddedShell:
            self.__tabWidget.setCurrentWidget(self.shellAssembly)
        else:
            if self.embeddedBrowser:
                self.__tabWidget.setCurrentWidget(self.browser)
            else:
                self.__tabWidget.setCurrentWidget(self.glvWidget)
        self.breakpointViewer.handleResetUI()
        
    def handleRawInput(self):
        """
        Public slot to handle the switch to the shell in raw input mode.
        """
        if self.embeddedShell:
            self.saveCurrentPage()
            self.__tabWidget.setCurrentWidget(self.shellAssembly)
        
    def initCallStackViewer(self, projectMode):
        """
        Public method to initialize the call stack viewer.
        
        @param projectMode flag indicating to enable the project mode (boolean)
        """
        self.callStackViewer.clear()
        self.callStackViewer.setProjectMode(projectMode)
        
    def isCallTraceEnabled(self):
        """
        Public method to get the state of the call trace function.
        
        @return flag indicating the state of the call trace function (boolean)
        """
        return self.callTraceViewer.isCallTraceEnabled()
        
    def clearCallTrace(self):
        """
        Public method to clear the recorded call trace.
        """
        self.callTraceViewer.clear()
        
    def setCallTraceToProjectMode(self, enabled):
        """
        Public slot to set the call trace viewer to project mode.
        
        In project mode the call trace info is shown with project relative
        path names.
        
        @param enabled flag indicating to enable the project mode (boolean)
        """
        self.callTraceViewer.setProjectMode(enabled)
        
    def showVariables(self, vlist, globals):
        """
        Public method to show the variables in the respective window.
        
        @param vlist list of variables to display
        @param globals flag indicating global/local state
        """
        if globals:
            self.globalsViewer.showVariables(vlist, self.framenr)
        else:
            self.localsViewer.showVariables(vlist, self.framenr)
            
    def showVariable(self, vlist, globals):
        """
        Public method to show the variables in the respective window.
        
        @param vlist list of variables to display
        @param globals flag indicating global/local state
        """
        if globals:
            self.globalsViewer.showVariable(vlist)
        else:
            self.localsViewer.showVariable(vlist)
            
    def showVariablesTab(self, globals):
        """
        Public method to make a variables tab visible.
        
        @param globals flag indicating global/local state
        """
        if globals:
            self.__tabWidget.setCurrentWidget(self.glvWidget)
        else:
            self.__tabWidget.setCurrentWidget(self.lvWidget)
        
    def saveCurrentPage(self):
        """
        Public slot to save the current page.
        """
        self.currPage = self.__tabWidget.currentWidget()
        
    def restoreCurrentPage(self):
        """
        Public slot to restore the previously saved page.
        """
        if self.currPage is not None:
            self.__tabWidget.setCurrentWidget(self.currPage)
            
    def handleClientStack(self, stack):
        """
        Public slot to show the call stack of the program being debugged.
        
        @param stack list of tuples with call stack data (file name,
            line number, function name, formatted argument/values list)
        """
        block = self.stackComboBox.blockSignals(True)
        self.framenr = 0
        self.stackComboBox.clear()
        self.currentStack = stack
        self.sourceButton.setEnabled(len(stack) > 0)
        for s in stack:
            # just show base filename to make it readable
            s = (os.path.basename(s[0]), s[1], s[2])
            self.stackComboBox.addItem('{0}:{1}:{2}'.format(*s))
        self.stackComboBox.blockSignals(block)
        
    def setVariablesFilter(self, globalsFilter, localsFilter):
        """
        Public slot to set the local variables filter.
        
        @param globalsFilter filter list for global variable types
            (list of int)
        @param localsFilter filter list for local variable types (list of int)
        """
        self.globalsFilter = globalsFilter
        self.localsFilter = localsFilter
        
    def __showSource(self):
        """
        Private slot to handle the source button press to show the selected
        file.
        """
        index = self.stackComboBox.currentIndex()
        if index > -1 and self.currentStack:
            s = self.currentStack[index]
            self.sourceFile.emit(s[0], int(s[1]))
        
    def __frameSelected(self, frmnr):
        """
        Private slot to handle the selection of a new stack frame number.
        
        @param frmnr frame number (0 is the current frame) (int)
        """
        self.framenr = frmnr
        self.debugServer.remoteClientVariables(0, self.localsFilter, frmnr)
        
        if self.__autoViewSource:
            self.__showSource()
        
    def __setGlobalsFilter(self):
        """
        Private slot to set the global variable filter.
        """
        filter = self.globalsFilterEdit.text()
        self.debugServer.remoteClientSetFilter(1, filter)
        self.debugServer.remoteClientVariables(2, self.globalsFilter)
        
    def __setLocalsFilter(self):
        """
        Private slot to set the local variable filter.
        """
        filter = self.localsFilterEdit.text()
        self.debugServer.remoteClientSetFilter(0, filter)
        if self.currentStack:
            self.debugServer.remoteClientVariables(
                0, self.localsFilter, self.framenr)
        
    def handleDebuggingStarted(self):
        """
        Public slot to handle the start of a debugging session.
        
        This slot sets the variables filter expressions.
        """
        self.__setGlobalsFilter()
        self.__setLocalsFilter()
        self.showVariablesTab(False)
        
    def currentWidget(self):
        """
        Public method to get a reference to the current widget.
        
        @return reference to the current widget (QWidget)
        """
        return self.__tabWidget.currentWidget()
        
    def setCurrentWidget(self, widget):
        """
        Public slot to set the current page based on the given widget.
        
        @param widget reference to the widget (QWidget)
        """
        self.__tabWidget.setCurrentWidget(widget)
        
    def showThreadList(self, currentID, threadList):
        """
        Public method to show the thread list.
        
        @param currentID id of the current thread (integer)
        @param threadList list of dictionaries containing the thread data
        """
        citm = None
        
        self.__threadList.clear()
        for thread in threadList:
            if thread['broken']:
                state = self.tr("waiting at breakpoint")
            else:
                state = self.tr("running")
            itm = QTreeWidgetItem(self.__threadList,
                                  ["{0:d}".format(thread['id']),
                                   thread['name'], state])
            if thread['id'] == currentID:
                citm = itm
        
        self.__threadList.header().resizeSections(QHeaderView.ResizeToContents)
        self.__threadList.header().setStretchLastSection(True)
        
        if citm:
            self.__doThreadListUpdate = False
            self.__threadList.setCurrentItem(citm)
            self.__doThreadListUpdate = True
        
    def __threadSelected(self, current, previous):
        """
        Private slot to handle the selection of a thread in the thread list.
        
        @param current reference to the new current item (QTreeWidgetItem)
        @param previous reference to the previous current item
            (QTreeWidgetItem)
        """
        if current is not None and self.__doThreadListUpdate:
            tid = int(current.text(0))
            self.debugServer.remoteSetThread(tid)
    
    def __callStackFrameSelected(self, frameNo):
        """
        Private slot to handle the selection of a call stack entry of the
        call stack viewer.
        
        @param frameNo frame number (index) of the selected entry (integer)
        """
        if frameNo >= 0:
            self.stackComboBox.setCurrentIndex(frameNo)
