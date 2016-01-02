# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the debugger UI.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMenu, QToolBar, QApplication, QDialog, \
    QInputDialog

from UI.Info import Program

from .DebugClientCapabilities import HasDebugger, HasInterpreter, \
    HasProfiler, HasCoverage
import Preferences
import Utilities
import UI.PixmapCache
import UI.Config

from E5Gui.E5Action import E5Action, createActionGroup
from E5Gui import E5MessageBox

from eric6config import getConfig


class DebugUI(QObject):
    """
    Class implementing the debugger part of the UI.
    
    @signal clientStack(stack) emitted at breaking after a reported exception
    @signal compileForms() emitted if changed project forms should be compiled
    @signal compileResources() emitted if changed project resources should be
        compiled
    @signal debuggingStarted(filename) emitted when a debugging session was
        started
    @signal resetUI() emitted to reset the UI
    @signal exceptionInterrupt() emitted after the execution was interrupted
        by an exception and acknowledged by the user
    @signal appendStdout(msg) emitted when the client program has terminated
        and the display of the termination dialog is suppressed
    """
    clientStack = pyqtSignal(list)
    resetUI = pyqtSignal()
    exceptionInterrupt = pyqtSignal()
    compileForms = pyqtSignal()
    compileResources = pyqtSignal()
    debuggingStarted = pyqtSignal(str)
    appendStdout = pyqtSignal(str)
    
    def __init__(self, ui, vm, debugServer, debugViewer, project):
        """
        Constructor
        
        @param ui reference to the main UI
        @param vm reference to the viewmanager
        @param debugServer reference to the debug server
        @param debugViewer reference to the debug viewer widget
        @param project reference to the project object
        """
        super(DebugUI, self).__init__(ui)
        
        self.ui = ui
        self.viewmanager = vm
        self.debugServer = debugServer
        self.debugViewer = debugViewer
        self.project = project
        
        # Clear some variables
        self.projectOpen = False
        self.editorOpen = False
        
        # read the saved debug info values
        self.argvHistory = Preferences.toList(
            Preferences.Prefs.settings.value('DebugInfo/ArgumentsHistory'))
        self.wdHistory = Preferences.toList(
            Preferences.Prefs.settings.value(
                'DebugInfo/WorkingDirectoryHistory'))
        self.envHistory = Preferences.toList(
            Preferences.Prefs.settings.value('DebugInfo/EnvironmentHistory'))
        self.excList = Preferences.toList(
            Preferences.Prefs.settings.value('DebugInfo/Exceptions'))
        self.excIgnoreList = Preferences.toList(
            Preferences.Prefs.settings.value('DebugInfo/IgnoredExceptions'))
        self.exceptions = Preferences.toBool(
            Preferences.Prefs.settings.value(
                'DebugInfo/ReportExceptions', True))
        self.autoClearShell = Preferences.toBool(
            Preferences.Prefs.settings.value('DebugInfo/AutoClearShell', True))
        self.tracePython = Preferences.toBool(
            Preferences.Prefs.settings.value('DebugInfo/TracePython', False))
        self.autoContinue = Preferences.toBool(
            Preferences.Prefs.settings.value('DebugInfo/AutoContinue', True))
        self.forkAutomatically = Preferences.toBool(
            Preferences.Prefs.settings.value(
                'DebugInfo/ForkAutomatically', False))
        self.forkIntoChild = Preferences.toBool(
            Preferences.Prefs.settings.value('DebugInfo/ForkIntoChild', False))
        
        self.evalHistory = []
        self.execHistory = []
        self.lastDebuggedFile = None
        self.lastStartAction = 0    # 0=None, 1=Script, 2=Project
        self.clientType = ""
        self.lastAction = -1
        self.debugActions = [
            self.__continue, self.__step, self.__stepOver, self.__stepOut,
            self.__stepQuit, self.__runToCursor
        ]
        self.localsVarFilter, self.globalsVarFilter = \
            Preferences.getVarFilters()
        self.debugViewer.setVariablesFilter(
            self.globalsVarFilter, self.localsVarFilter)
        
        # Connect the signals emitted by the debug-server
        debugServer.clientGone.connect(self.__clientGone)
        debugServer.clientLine.connect(self.__clientLine)
        debugServer.clientExit.connect(self.__clientExit)
        debugServer.clientSyntaxError.connect(self.__clientSyntaxError)
        debugServer.clientException.connect(self.__clientException)
        debugServer.clientSignal.connect(self.__clientSignal)
        debugServer.clientVariables.connect(self.__clientVariables)
        debugServer.clientVariable.connect(self.__clientVariable)
        debugServer.clientBreakConditionError.connect(
            self.__clientBreakConditionError)
        debugServer.clientWatchConditionError.connect(
            self.__clientWatchConditionError)
        debugServer.passiveDebugStarted.connect(self.__passiveDebugStarted)
        debugServer.clientThreadSet.connect(self.__clientThreadSet)
        
        debugServer.clientRawInput.connect(debugViewer.handleRawInput)
        debugServer.clientRawInputSent.connect(debugViewer.restoreCurrentPage)
        debugServer.clientThreadList.connect(debugViewer.showThreadList)
        
        # Connect the signals emitted by the viewmanager
        vm.editorOpened.connect(self.__editorOpened)
        vm.lastEditorClosed.connect(self.__lastEditorClosed)
        vm.checkActions.connect(self.__checkActions)
        vm.cursorChanged.connect(self.__cursorChanged)
        vm.breakpointToggled.connect(self.__cursorChanged)
        
        # Connect the signals emitted by the project
        project.projectOpened.connect(self.__projectOpened)
        project.newProject.connect(self.__projectOpened)
        project.projectClosed.connect(self.__projectClosed)
        
        # Set a flag for the passive debug mode
        self.passive = Preferences.getDebugger("PassiveDbgEnabled")
        
    def variablesFilter(self, scope):
        """
        Public method to get the variables filter for a scope.
        
        @param scope flag indicating global (True) or local (False) scope
        @return filters list (list of integers)
        """
        if scope:
            return self.globalsVarFilter[:]
        else:
            return self.localsVarFilter[:]
        
    def initActions(self):
        """
        Public method defining the user interface actions.
        """
        self.actions = []
        
        self.runAct = E5Action(
            self.tr('Run Script'),
            UI.PixmapCache.getIcon("runScript.png"),
            self.tr('&Run Script...'),
            Qt.Key_F2, 0, self, 'dbg_run_script')
        self.runAct.setStatusTip(self.tr('Run the current Script'))
        self.runAct.setWhatsThis(self.tr(
            """<b>Run Script</b>"""
            """<p>Set the command line arguments and run the script outside"""
            """ the debugger. If the file has unsaved changes it may be"""
            """ saved first.</p>"""
        ))
        self.runAct.triggered.connect(self.__runScript)
        self.actions.append(self.runAct)

        self.runProjectAct = E5Action(
            self.tr('Run Project'),
            UI.PixmapCache.getIcon("runProject.png"),
            self.tr('Run &Project...'), Qt.SHIFT + Qt.Key_F2, 0, self,
            'dbg_run_project')
        self.runProjectAct.setStatusTip(self.tr('Run the current Project'))
        self.runProjectAct.setWhatsThis(self.tr(
            """<b>Run Project</b>"""
            """<p>Set the command line arguments and run the current project"""
            """ outside the debugger."""
            """ If files of the current project have unsaved changes they"""
            """ may be saved first.</p>"""
        ))
        self.runProjectAct.triggered.connect(self.__runProject)
        self.actions.append(self.runProjectAct)

        self.coverageAct = E5Action(
            self.tr('Coverage run of Script'),
            UI.PixmapCache.getIcon("coverageScript.png"),
            self.tr('Coverage run of Script...'), 0, 0, self,
            'dbg_coverage_script')
        self.coverageAct.setStatusTip(
            self.tr('Perform a coverage run of the current Script'))
        self.coverageAct.setWhatsThis(self.tr(
            """<b>Coverage run of Script</b>"""
            """<p>Set the command line arguments and run the script under"""
            """ the control of a coverage analysis tool. If the file has"""
            """ unsaved changes it may be saved first.</p>"""
        ))
        self.coverageAct.triggered.connect(self.__coverageScript)
        self.actions.append(self.coverageAct)

        self.coverageProjectAct = E5Action(
            self.tr('Coverage run of Project'),
            UI.PixmapCache.getIcon("coverageProject.png"),
            self.tr('Coverage run of Project...'), 0, 0, self,
            'dbg_coverage_project')
        self.coverageProjectAct.setStatusTip(
            self.tr('Perform a coverage run of the current Project'))
        self.coverageProjectAct.setWhatsThis(self.tr(
            """<b>Coverage run of Project</b>"""
            """<p>Set the command line arguments and run the current project"""
            """ under the control of a coverage analysis tool."""
            """ If files of the current project have unsaved changes"""
            """ they may be saved first.</p>"""
        ))
        self.coverageProjectAct.triggered.connect(self.__coverageProject)
        self.actions.append(self.coverageProjectAct)

        self.profileAct = E5Action(
            self.tr('Profile Script'),
            UI.PixmapCache.getIcon("profileScript.png"),
            self.tr('Profile Script...'), 0, 0, self, 'dbg_profile_script')
        self.profileAct.setStatusTip(self.tr('Profile the current Script'))
        self.profileAct.setWhatsThis(self.tr(
            """<b>Profile Script</b>"""
            """<p>Set the command line arguments and profile the script."""
            """ If the file has unsaved changes it may be saved first.</p>"""
        ))
        self.profileAct.triggered.connect(self.__profileScript)
        self.actions.append(self.profileAct)

        self.profileProjectAct = E5Action(
            self.tr('Profile Project'),
            UI.PixmapCache.getIcon("profileProject.png"),
            self.tr('Profile Project...'), 0, 0, self,
            'dbg_profile_project')
        self.profileProjectAct.setStatusTip(
            self.tr('Profile the current Project'))
        self.profileProjectAct.setWhatsThis(self.tr(
            """<b>Profile Project</b>"""
            """<p>Set the command line arguments and profile the current"""
            """ project. If files of the current project have unsaved"""
            """ changes they may be saved first.</p>"""
        ))
        self.profileProjectAct.triggered.connect(self.__profileProject)
        self.actions.append(self.profileProjectAct)

        self.debugAct = E5Action(
            self.tr('Debug Script'),
            UI.PixmapCache.getIcon("debugScript.png"),
            self.tr('&Debug Script...'), Qt.Key_F5, 0, self,
            'dbg_debug_script')
        self.debugAct.setStatusTip(self.tr('Debug the current Script'))
        self.debugAct.setWhatsThis(self.tr(
            """<b>Debug Script</b>"""
            """<p>Set the command line arguments and set the current line"""
            """ to be the first executable Python statement of the current"""
            """ editor window. If the file has unsaved changes it may be"""
            """ saved first.</p>"""
        ))
        self.debugAct.triggered.connect(self.__debugScript)
        self.actions.append(self.debugAct)

        self.debugProjectAct = E5Action(
            self.tr('Debug Project'),
            UI.PixmapCache.getIcon("debugProject.png"),
            self.tr('Debug &Project...'), Qt.SHIFT + Qt.Key_F5, 0, self,
            'dbg_debug_project')
        self.debugProjectAct.setStatusTip(self.tr(
            'Debug the current Project'))
        self.debugProjectAct.setWhatsThis(self.tr(
            """<b>Debug Project</b>"""
            """<p>Set the command line arguments and set the current line"""
            """ to be the first executable Python statement of the main"""
            """ script of the current project. If files of the current"""
            """ project have unsaved changes they may be saved first.</p>"""
        ))
        self.debugProjectAct.triggered.connect(self.__debugProject)
        self.actions.append(self.debugProjectAct)

        self.restartAct = E5Action(
            self.tr('Restart'),
            UI.PixmapCache.getIcon("restart.png"),
            self.tr('Restart'), Qt.Key_F4, 0, self, 'dbg_restart_script')
        self.restartAct.setStatusTip(self.tr(
            'Restart the last debugged script'))
        self.restartAct.setWhatsThis(self.tr(
            """<b>Restart</b>"""
            """<p>Set the command line arguments and set the current line"""
            """ to be the first executable Python statement of the script"""
            """ that was debugged last. If there are unsaved changes, they"""
            """ may be saved first.</p>"""
        ))
        self.restartAct.triggered.connect(self.__doRestart)
        self.actions.append(self.restartAct)

        self.stopAct = E5Action(
            self.tr('Stop'),
            UI.PixmapCache.getIcon("stopScript.png"),
            self.tr('Stop'), Qt.SHIFT + Qt.Key_F10, 0,
            self, 'dbg_stop_script')
        self.stopAct.setStatusTip(self.tr("""Stop the running script."""))
        self.stopAct.setWhatsThis(self.tr(
            """<b>Stop</b>"""
            """<p>This stops the script running in the debugger backend.</p>"""
        ))
        self.stopAct.triggered.connect(self.__stopScript)
        self.actions.append(self.stopAct)

        self.debugActGrp = createActionGroup(self)

        act = E5Action(
            self.tr('Continue'),
            UI.PixmapCache.getIcon("continue.png"),
            self.tr('&Continue'), Qt.Key_F6, 0,
            self.debugActGrp, 'dbg_continue')
        act.setStatusTip(
            self.tr('Continue running the program from the current line'))
        act.setWhatsThis(self.tr(
            """<b>Continue</b>"""
            """<p>Continue running the program from the current line. The"""
            """ program will stop when it terminates or when a breakpoint"""
            """ is reached.</p>"""
        ))
        act.triggered.connect(self.__continue)
        self.actions.append(act)

        act = E5Action(
            self.tr('Continue to Cursor'),
            UI.PixmapCache.getIcon("continueToCursor.png"),
            self.tr('Continue &To Cursor'), Qt.SHIFT + Qt.Key_F6, 0,
            self.debugActGrp, 'dbg_continue_to_cursor')
        act.setStatusTip(self.tr(
            """Continue running the program from the"""
            """ current line to the current cursor position"""))
        act.setWhatsThis(self.tr(
            """<b>Continue To Cursor</b>"""
            """<p>Continue running the program from the current line to the"""
            """ current cursor position.</p>"""
        ))
        act.triggered.connect(self.__runToCursor)
        self.actions.append(act)

        act = E5Action(
            self.tr('Single Step'),
            UI.PixmapCache.getIcon("step.png"),
            self.tr('Sin&gle Step'), Qt.Key_F7, 0,
            self.debugActGrp, 'dbg_single_step')
        act.setStatusTip(self.tr('Execute a single Python statement'))
        act.setWhatsThis(self.tr(
            """<b>Single Step</b>"""
            """<p>Execute a single Python statement. If the statement"""
            """ is an <tt>import</tt> statement, a class constructor, or a"""
            """ method or function call then control is returned to the"""
            """ debugger at the next statement.</p>"""
        ))
        act.triggered.connect(self.__step)
        self.actions.append(act)

        act = E5Action(
            self.tr('Step Over'),
            UI.PixmapCache.getIcon("stepOver.png"),
            self.tr('Step &Over'), Qt.Key_F8, 0,
            self.debugActGrp, 'dbg_step_over')
        act.setStatusTip(self.tr(
            """Execute a single Python statement staying"""
            """ in the current frame"""))
        act.setWhatsThis(self.tr(
            """<b>Step Over</b>"""
            """<p>Execute a single Python statement staying in the same"""
            """ frame. If the statement is an <tt>import</tt> statement,"""
            """ a class constructor, or a method or function call then"""
            """ control is returned to the debugger after the statement"""
            """ has completed.</p>"""
        ))
        act.triggered.connect(self.__stepOver)
        self.actions.append(act)

        act = E5Action(
            self.tr('Step Out'),
            UI.PixmapCache.getIcon("stepOut.png"),
            self.tr('Step Ou&t'), Qt.Key_F9, 0,
            self.debugActGrp, 'dbg_step_out')
        act.setStatusTip(self.tr(
            """Execute Python statements until leaving"""
            """ the current frame"""))
        act.setWhatsThis(self.tr(
            """<b>Step Out</b>"""
            """<p>Execute Python statements until leaving the current"""
            """ frame. If the statements are inside an <tt>import</tt>"""
            """ statement, a class constructor, or a method or function"""
            """ call then control is returned to the debugger after the"""
            """ current frame has been left.</p>"""
        ))
        act.triggered.connect(self.__stepOut)
        self.actions.append(act)

        act = E5Action(
            self.tr('Stop'),
            UI.PixmapCache.getIcon("stepQuit.png"),
            self.tr('&Stop'), Qt.Key_F10, 0,
            self.debugActGrp, 'dbg_stop')
        act.setStatusTip(self.tr('Stop debugging'))
        act.setWhatsThis(self.tr(
            """<b>Stop</b>"""
            """<p>Stop the running debugging session.</p>"""
        ))
        act.triggered.connect(self.__stepQuit)
        self.actions.append(act)
        
        self.debugActGrp2 = createActionGroup(self)

        act = E5Action(
            self.tr('Evaluate'),
            self.tr('E&valuate...'),
            0, 0, self.debugActGrp2, 'dbg_evaluate')
        act.setStatusTip(self.tr('Evaluate in current context'))
        act.setWhatsThis(self.tr(
            """<b>Evaluate</b>"""
            """<p>Evaluate an expression in the current context of the"""
            """ debugged program. The result is displayed in the"""
            """ shell window.</p>"""
        ))
        act.triggered.connect(self.__eval)
        self.actions.append(act)
        
        act = E5Action(
            self.tr('Execute'),
            self.tr('E&xecute...'),
            0, 0, self.debugActGrp2, 'dbg_execute')
        act.setStatusTip(
            self.tr('Execute a one line statement in the current context'))
        act.setWhatsThis(self.tr(
            """<b>Execute</b>"""
            """<p>Execute a one line statement in the current context"""
            """ of the debugged program.</p>"""
        ))
        act.triggered.connect(self.__exec)
        self.actions.append(act)
        
        self.dbgFilterAct = E5Action(
            self.tr('Variables Type Filter'),
            self.tr('Varia&bles Type Filter...'), 0, 0, self,
            'dbg_variables_filter')
        self.dbgFilterAct.setStatusTip(self.tr(
            'Configure variables type filter'))
        self.dbgFilterAct.setWhatsThis(self.tr(
            """<b>Variables Type Filter</b>"""
            """<p>Configure the variables type filter. Only variable types"""
            """ that are not selected are displayed in the global or local"""
            """ variables window during a debugging session.</p>"""
        ))
        self.dbgFilterAct.triggered.connect(
            self.__configureVariablesFilters)
        self.actions.append(self.dbgFilterAct)

        self.excFilterAct = E5Action(
            self.tr('Exceptions Filter'),
            self.tr('&Exceptions Filter...'), 0, 0, self,
            'dbg_exceptions_filter')
        self.excFilterAct.setStatusTip(self.tr(
            'Configure exceptions filter'))
        self.excFilterAct.setWhatsThis(self.tr(
            """<b>Exceptions Filter</b>"""
            """<p>Configure the exceptions filter. Only exception types"""
            """ that are listed are highlighted during a debugging"""
            """ session.</p><p>Please note, that all unhandled exceptions"""
            """ are highlighted indepent from the filter list.</p>"""
        ))
        self.excFilterAct.triggered.connect(
            self.__configureExceptionsFilter)
        self.actions.append(self.excFilterAct)
        
        self.excIgnoreFilterAct = E5Action(
            self.tr('Ignored Exceptions'),
            self.tr('&Ignored Exceptions...'), 0, 0,
            self, 'dbg_ignored_exceptions')
        self.excIgnoreFilterAct.setStatusTip(self.tr(
            'Configure ignored exceptions'))
        self.excIgnoreFilterAct.setWhatsThis(self.tr(
            """<b>Ignored Exceptions</b>"""
            """<p>Configure the ignored exceptions. Only exception types"""
            """ that are not listed are highlighted during a debugging"""
            """ session.</p><p>Please note, that unhandled exceptions"""
            """ cannot be ignored.</p>"""
        ))
        self.excIgnoreFilterAct.triggered.connect(
            self.__configureIgnoredExceptions)
        self.actions.append(self.excIgnoreFilterAct)

        self.dbgSetBpActGrp = createActionGroup(self)

        self.dbgToggleBpAct = E5Action(
            self.tr('Toggle Breakpoint'),
            UI.PixmapCache.getIcon("breakpointToggle.png"),
            self.tr('Toggle Breakpoint'),
            QKeySequence(self.tr("Shift+F11", "Debug|Toggle Breakpoint")),
            0, self.dbgSetBpActGrp, 'dbg_toggle_breakpoint')
        self.dbgToggleBpAct.setStatusTip(self.tr('Toggle Breakpoint'))
        self.dbgToggleBpAct.setWhatsThis(self.tr(
            """<b>Toggle Breakpoint</b>"""
            """<p>Toggles a breakpoint at the current line of the"""
            """ current editor.</p>"""
        ))
        self.dbgToggleBpAct.triggered.connect(self.__toggleBreakpoint)
        self.actions.append(self.dbgToggleBpAct)
        
        self.dbgEditBpAct = E5Action(
            self.tr('Edit Breakpoint'),
            UI.PixmapCache.getIcon("cBreakpointToggle.png"),
            self.tr('Edit Breakpoint...'),
            QKeySequence(self.tr("Shift+F12", "Debug|Edit Breakpoint")), 0,
            self.dbgSetBpActGrp, 'dbg_edit_breakpoint')
        self.dbgEditBpAct.setStatusTip(self.tr('Edit Breakpoint'))
        self.dbgEditBpAct.setWhatsThis(self.tr(
            """<b>Edit Breakpoint</b>"""
            """<p>Opens a dialog to edit the breakpoints properties."""
            """ It works at the current line of the current editor.</p>"""
        ))
        self.dbgEditBpAct.triggered.connect(self.__editBreakpoint)
        self.actions.append(self.dbgEditBpAct)

        self.dbgNextBpAct = E5Action(
            self.tr('Next Breakpoint'),
            UI.PixmapCache.getIcon("breakpointNext.png"),
            self.tr('Next Breakpoint'),
            QKeySequence(
                self.tr("Ctrl+Shift+PgDown", "Debug|Next Breakpoint")), 0,
            self.dbgSetBpActGrp, 'dbg_next_breakpoint')
        self.dbgNextBpAct.setStatusTip(self.tr('Next Breakpoint'))
        self.dbgNextBpAct.setWhatsThis(self.tr(
            """<b>Next Breakpoint</b>"""
            """<p>Go to next breakpoint of the current editor.</p>"""
        ))
        self.dbgNextBpAct.triggered.connect(self.__nextBreakpoint)
        self.actions.append(self.dbgNextBpAct)

        self.dbgPrevBpAct = E5Action(
            self.tr('Previous Breakpoint'),
            UI.PixmapCache.getIcon("breakpointPrevious.png"),
            self.tr('Previous Breakpoint'),
            QKeySequence(
                self.tr("Ctrl+Shift+PgUp", "Debug|Previous Breakpoint")),
            0, self.dbgSetBpActGrp, 'dbg_previous_breakpoint')
        self.dbgPrevBpAct.setStatusTip(self.tr('Previous Breakpoint'))
        self.dbgPrevBpAct.setWhatsThis(self.tr(
            """<b>Previous Breakpoint</b>"""
            """<p>Go to previous breakpoint of the current editor.</p>"""
        ))
        self.dbgPrevBpAct.triggered.connect(self.__previousBreakpoint)
        self.actions.append(self.dbgPrevBpAct)

        act = E5Action(
            self.tr('Clear Breakpoints'),
            self.tr('Clear Breakpoints'),
            QKeySequence(
                self.tr("Ctrl+Shift+C", "Debug|Clear Breakpoints")), 0,
            self.dbgSetBpActGrp, 'dbg_clear_breakpoint')
        act.setStatusTip(self.tr('Clear Breakpoints'))
        act.setWhatsThis(self.tr(
            """<b>Clear Breakpoints</b>"""
            """<p>Clear breakpoints of all editors.</p>"""
        ))
        act.triggered.connect(self.__clearBreakpoints)
        self.actions.append(act)

        self.debugActGrp.setEnabled(False)
        self.debugActGrp2.setEnabled(False)
        self.dbgSetBpActGrp.setEnabled(False)
        self.runAct.setEnabled(False)
        self.runProjectAct.setEnabled(False)
        self.profileAct.setEnabled(False)
        self.profileProjectAct.setEnabled(False)
        self.coverageAct.setEnabled(False)
        self.coverageProjectAct.setEnabled(False)
        self.debugAct.setEnabled(False)
        self.debugProjectAct.setEnabled(False)
        self.restartAct.setEnabled(False)
        self.stopAct.setEnabled(False)
        
    def initMenus(self):
        """
        Public slot to initialize the project menu.
        
        @return the generated menu
        """
        dmenu = QMenu(self.tr('&Debug'), self.parent())
        dmenu.setTearOffEnabled(True)
        smenu = QMenu(self.tr('&Start'), self.parent())
        smenu.setTearOffEnabled(True)
        self.breakpointsMenu = QMenu(self.tr('&Breakpoints'), dmenu)
        
        smenu.addAction(self.restartAct)
        smenu.addAction(self.stopAct)
        smenu.addSeparator()
        smenu.addAction(self.runAct)
        smenu.addAction(self.runProjectAct)
        smenu.addSeparator()
        smenu.addAction(self.debugAct)
        smenu.addAction(self.debugProjectAct)
        smenu.addSeparator()
        smenu.addAction(self.profileAct)
        smenu.addAction(self.profileProjectAct)
        smenu.addSeparator()
        smenu.addAction(self.coverageAct)
        smenu.addAction(self.coverageProjectAct)
        
        dmenu.addActions(self.debugActGrp.actions())
        dmenu.addSeparator()
        dmenu.addActions(self.debugActGrp2.actions())
        dmenu.addSeparator()
        dmenu.addActions(self.dbgSetBpActGrp.actions())
        self.menuBreakpointsAct = dmenu.addMenu(self.breakpointsMenu)
        dmenu.addSeparator()
        dmenu.addAction(self.dbgFilterAct)
        dmenu.addAction(self.excFilterAct)
        dmenu.addAction(self.excIgnoreFilterAct)
        
        self.breakpointsMenu.aboutToShow.connect(self.__showBreakpointsMenu)
        self.breakpointsMenu.triggered.connect(self.__breakpointSelected)
        dmenu.aboutToShow.connect(self.__showDebugMenu)
        
        return smenu, dmenu
        
    def initToolbars(self, toolbarManager):
        """
        Public slot to initialize the debug toolbars.
        
        @param toolbarManager reference to a toolbar manager object
            (E5ToolBarManager)
        @return the generated toolbars (list of QToolBar)
        """
        starttb = QToolBar(self.tr("Start"), self.ui)
        starttb.setIconSize(UI.Config.ToolBarIconSize)
        starttb.setObjectName("StartToolbar")
        starttb.setToolTip(self.tr('Start'))
        
        starttb.addAction(self.restartAct)
        starttb.addAction(self.stopAct)
        starttb.addSeparator()
        starttb.addAction(self.runAct)
        starttb.addAction(self.runProjectAct)
        starttb.addSeparator()
        starttb.addAction(self.debugAct)
        starttb.addAction(self.debugProjectAct)
        
        debugtb = QToolBar(self.tr("Debug"), self.ui)
        debugtb.setIconSize(UI.Config.ToolBarIconSize)
        debugtb.setObjectName("DebugToolbar")
        debugtb.setToolTip(self.tr('Debug'))
        
        debugtb.addActions(self.debugActGrp.actions())
        debugtb.addSeparator()
        debugtb.addAction(self.dbgToggleBpAct)
        debugtb.addAction(self.dbgEditBpAct)
        debugtb.addAction(self.dbgNextBpAct)
        debugtb.addAction(self.dbgPrevBpAct)
        
        toolbarManager.addToolBar(starttb, starttb.windowTitle())
        toolbarManager.addToolBar(debugtb, debugtb.windowTitle())
        toolbarManager.addAction(self.profileAct, starttb.windowTitle())
        toolbarManager.addAction(self.profileProjectAct, starttb.windowTitle())
        toolbarManager.addAction(self.coverageAct, starttb.windowTitle())
        toolbarManager.addAction(self.coverageProjectAct,
                                 starttb.windowTitle())
        
        return [starttb, debugtb]
        
    def setArgvHistory(self, argsStr, clearHistories=False):
        """
        Public slot to initialize the argv history.
        
        @param argsStr the commandline arguments (string)
        @param clearHistories flag indicating, that the list should
            be cleared (boolean)
        """
        if clearHistories:
            self.argvHistory = []
        else:
            if argsStr in self.argvHistory:
                self.argvHistory.remove(argsStr)
        self.argvHistory.insert(0, argsStr)

    def setWdHistory(self, wdStr, clearHistories=False):
        """
        Public slot to initialize the wd history.
        
        @param wdStr the working directory (string)
        @param clearHistories flag indicating, that the list should
            be cleared (boolean)
        """
        if clearHistories:
            self.wdHistory = []
        else:
            if wdStr in self.wdHistory:
                self.wdHistory.remove(wdStr)
        self.wdHistory.insert(0, wdStr)
        
    def setEnvHistory(self, envStr, clearHistories=False):
        """
        Public slot to initialize the env history.
        
        @param envStr the environment settings (string)
        @param clearHistories flag indicating, that the list should
            be cleared (boolean)
        """
        if clearHistories:
            self.envHistory = []
        else:
            if envStr in self.envHistory:
                self.envHistory.remove(envStr)
        self.envHistory.insert(0, envStr)
        
    def setExceptionReporting(self, exceptions):
        """
        Public slot to initialize the exception reporting flag.
        
        @param exceptions flag indicating exception reporting status (boolean)
        """
        self.exceptions = exceptions

    def setExcList(self, excList):
        """
        Public slot to initialize the exceptions type list.
        
        @param excList list of exception types (list of strings)
        """
        self.excList = excList[:]   # keep a copy
        
    def setExcIgnoreList(self, excIgnoreList):
        """
        Public slot to initialize the ignored exceptions type list.
        
        @param excIgnoreList list of ignored exception types (list of strings)
        """
        self.excIgnoreList = excIgnoreList[:]   # keep a copy
        
    def setAutoClearShell(self, autoClearShell):
        """
        Public slot to initialize the autoClearShell flag.
        
        @param autoClearShell flag indicating, that the interpreter window
            should be cleared (boolean)
        """
        self.autoClearShell = autoClearShell

    def setTracePython(self, tracePython):
        """
        Public slot to initialize the trace Python flag.
        
        @param tracePython flag indicating if the Python library should be
            traced as well (boolean)
        """
        self.tracePython = tracePython

    def setAutoContinue(self, autoContinue):
        """
        Public slot to initialize the autoContinue flag.
        
        @param autoContinue flag indicating, that the debugger should not
            stop at the first executable line (boolean)
        """
        self.autoContinue = autoContinue

    def __editorOpened(self, fn):
        """
        Private slot to handle the editorOpened signal.
        
        @param fn filename of the opened editor
        """
        self.editorOpen = True
        
        if fn:
            editor = self.viewmanager.getOpenEditor(fn)
        else:
            editor = None
        self.__checkActions(editor)
        
    def __lastEditorClosed(self):
        """
        Private slot to handle the closeProgram signal.
        """
        self.editorOpen = False
        self.debugAct.setEnabled(False)
        self.runAct.setEnabled(False)
        self.profileAct.setEnabled(False)
        self.coverageAct.setEnabled(False)
        self.debugActGrp.setEnabled(False)
        self.debugActGrp2.setEnabled(False)
        self.dbgSetBpActGrp.setEnabled(False)
        self.lastAction = -1
        if not self.projectOpen:
            self.restartAct.setEnabled(False)
            self.lastDebuggedFile = None
            self.lastStartAction = 0
            self.clientType = ""
        
    def __checkActions(self, editor):
        """
        Private slot to check some actions for their enable/disable status.
        
        @param editor editor window
        """
        if editor:
            fn = editor.getFileName()
        else:
            fn = None
        
        cap = 0
        if fn:
            for language in self.debugServer.getSupportedLanguages():
                exts = self.debugServer.getExtensions(language)
                if fn.endswith(exts):
                    cap = self.debugServer.getClientCapabilities(language)
                    break
            else:
                if editor.isPy2File():
                    cap = self.debugServer.getClientCapabilities('Python2')
                elif editor.isPy3File():
                    cap = self.debugServer.getClientCapabilities('Python3')
                elif editor.isRubyFile():
                    cap = self.debugServer.getClientCapabilities('Ruby')
        
            if not self.passive:
                self.runAct.setEnabled(cap & HasInterpreter)
                self.coverageAct.setEnabled(cap & HasCoverage)
                self.profileAct.setEnabled(cap & HasProfiler)
                self.debugAct.setEnabled(cap & HasDebugger)
            self.dbgSetBpActGrp.setEnabled(cap & HasDebugger)
            if editor.curLineHasBreakpoint():
                self.dbgEditBpAct.setEnabled(True)
            else:
                self.dbgEditBpAct.setEnabled(False)
            if editor.hasBreakpoints():
                self.dbgNextBpAct.setEnabled(True)
                self.dbgPrevBpAct.setEnabled(True)
            else:
                self.dbgNextBpAct.setEnabled(False)
                self.dbgPrevBpAct.setEnabled(False)
        else:
            self.runAct.setEnabled(False)
            self.coverageAct.setEnabled(False)
            self.profileAct.setEnabled(False)
            self.debugAct.setEnabled(False)
            self.dbgSetBpActGrp.setEnabled(False)
        
    def __cursorChanged(self, editor):
        """
        Private slot handling the cursorChanged signal of the viewmanager.
        
        @param editor editor window
        """
        if editor is None:
            return
        
        if editor.isPyFile() or editor.isRubyFile():
            if editor.curLineHasBreakpoint():
                self.dbgEditBpAct.setEnabled(True)
            else:
                self.dbgEditBpAct.setEnabled(False)
            if editor.hasBreakpoints():
                self.dbgNextBpAct.setEnabled(True)
                self.dbgPrevBpAct.setEnabled(True)
            else:
                self.dbgNextBpAct.setEnabled(False)
                self.dbgPrevBpAct.setEnabled(False)
        
    def __projectOpened(self):
        """
        Private slot to handle the projectOpened signal.
        """
        self.projectOpen = True
        cap = self.debugServer.getClientCapabilities(
            self.project.pdata["PROGLANGUAGE"][0])
        if not self.passive:
            self.debugProjectAct.setEnabled(cap & HasDebugger)
            self.runProjectAct.setEnabled(cap & HasInterpreter)
            self.profileProjectAct.setEnabled(cap & HasProfiler)
            self.coverageProjectAct.setEnabled(cap & HasCoverage)
        
    def __projectClosed(self):
        """
        Private slot to handle the projectClosed signal.
        """
        self.projectOpen = False
        self.runProjectAct.setEnabled(False)
        self.profileProjectAct.setEnabled(False)
        self.coverageProjectAct.setEnabled(False)
        self.debugProjectAct.setEnabled(False)
        
        if not self.editorOpen:
            self.restartAct.setEnabled(False)
            self.lastDebuggedFile = None
            self.lastStartAction = 0
            self.clientType = ""
        
    def shutdown(self):
        """
        Public method to perform shutdown actions.
        """
        # Just save the 10 most recent entries
        del self.argvHistory[10:]
        del self.wdHistory[10:]
        del self.envHistory[10:]
        
        Preferences.Prefs.settings.setValue(
            'DebugInfo/ArgumentsHistory', self.argvHistory)
        Preferences.Prefs.settings.setValue(
            'DebugInfo/WorkingDirectoryHistory', self.wdHistory)
        Preferences.Prefs.settings.setValue(
            'DebugInfo/EnvironmentHistory', self.envHistory)
        Preferences.Prefs.settings.setValue(
            'DebugInfo/Exceptions', self.excList)
        Preferences.Prefs.settings.setValue(
            'DebugInfo/IgnoredExceptions', self.excIgnoreList)
        Preferences.Prefs.settings.setValue(
            'DebugInfo/ReportExceptions', self.exceptions)
        Preferences.Prefs.settings.setValue(
            'DebugInfo/AutoClearShell', self.autoClearShell)
        Preferences.Prefs.settings.setValue(
            'DebugInfo/TracePython', self.tracePython)
        Preferences.Prefs.settings.setValue(
            'DebugInfo/AutoContinue', self.autoContinue)
        Preferences.Prefs.settings.setValue(
            'DebugInfo/ForkAutomatically', self.forkAutomatically)
        Preferences.Prefs.settings.setValue(
            'DebugInfo/ForkIntoChild', self.forkIntoChild)
        
    def shutdownServer(self):
        """
        Public method to shut down the debug server.
        
        This is needed to cleanly close the sockets on Win OS.
        
        @return always true
        """
        self.debugServer.shutdownServer()
        return True
        
    def __resetUI(self):
        """
        Private slot to reset the user interface.
        """
        self.lastAction = -1
        self.debugActGrp.setEnabled(False)
        self.debugActGrp2.setEnabled(False)
        if not self.passive:
            if self.editorOpen:
                editor = self.viewmanager.activeWindow()
            else:
                editor = None
            self.__checkActions(editor)
            
            self.debugProjectAct.setEnabled(self.projectOpen)
            self.runProjectAct.setEnabled(self.projectOpen)
            self.profileProjectAct.setEnabled(self.projectOpen)
            self.coverageProjectAct.setEnabled(self.projectOpen)
            if self.lastDebuggedFile is not None and \
                    (self.editorOpen or self.projectOpen):
                self.restartAct.setEnabled(True)
            else:
                self.restartAct.setEnabled(False)
            self.stopAct.setEnabled(False)
        self.resetUI.emit()
        
    def __clientLine(self, fn, line, forStack):
        """
        Private method to handle a change to the current line.
        
        @param fn filename (string)
        @param line linenumber (int)
        @param forStack flag indicating this is for a stack dump (boolean)
        """
        self.ui.raise_()
        self.ui.activateWindow()
        if self.ui.getViewProfile() != "debug":
            self.ui.setDebugProfile()
        self.viewmanager.setFileLine(fn, line)
        if not forStack:
            self.__getThreadList()
            self.__getClientVariables()

        self.debugActGrp.setEnabled(True)
        self.debugActGrp2.setEnabled(True)
        
    def __clientExit(self, status):
        """
        Private method to handle the debugged program terminating.
        
        @param status exit code of the debugged program (int)
        """
        self.viewmanager.exit()

        self.__resetUI()
        
        if not Preferences.getDebugger("SuppressClientExit") or status != 0:
            if self.ui.currentProg is None:
                E5MessageBox.information(
                    self.ui, Program,
                    self.tr('<p>The program has terminated with an exit'
                            ' status of {0}.</p>').format(status))
            else:
                E5MessageBox.information(
                    self.ui, Program,
                    self.tr('<p><b>{0}</b> has terminated with an exit'
                            ' status of {1}.</p>')
                        .format(Utilities.normabspath(self.ui.currentProg),
                                status))
        else:
            if self.ui.notificationsEnabled():
                if self.ui.currentProg is None:
                    msg = self.tr('The program has terminated with an exit'
                                  ' status of {0}.').format(status)
                else:
                    msg = self.tr('"{0}" has terminated with an exit'
                                  ' status of {1}.')\
                        .format(os.path.basename(self.ui.currentProg),
                                status)
                self.ui.showNotification(
                    UI.PixmapCache.getPixmap("debug48.png"),
                    self.tr("Program terminated"), msg)
            else:
                if self.ui.currentProg is None:
                    self.appendStdout.emit(
                        self.tr('The program has terminated with an exit'
                                ' status of {0}.\n').format(status))
                else:
                    self.appendStdout.emit(
                        self.tr('"{0}" has terminated with an exit'
                                ' status of {1}.\n')
                            .format(Utilities.normabspath(self.ui.currentProg),
                                    status))

    def __clientSyntaxError(self, message, filename, lineNo, characterNo):
        """
        Private method to handle a syntax error in the debugged program.
        
        @param message message of the syntax error (string)
        @param filename translated filename of the syntax error position
            (string)
        @param lineNo line number of the syntax error position (integer)
        @param characterNo character number of the syntax error position
            (integer)
        """
        self.__resetUI()
        self.ui.raise_()
        self.ui.activateWindow()
        
        if message is None:
            E5MessageBox.critical(
                self.ui, Program,
                self.tr(
                    'The program being debugged contains an unspecified'
                    ' syntax error.'))
            return
            
        if not os.path.isabs(filename):
            if os.path.exists(os.path.join(self.project.getProjectPath(),
                              filename)):
                filename = os.path.join(self.project.getProjectPath(),
                                        filename)
            else:
                ms = self.project.getMainScript(normalized=True)
                if ms is not None:
                    d = os.path.dirname(ms)
                    if os.path.exists(os.path.join(d, filename)):
                        filename = os.path.join(d, filename)
        self.viewmanager.setFileLine(filename, lineNo, True, True)
        E5MessageBox.critical(
            self.ui, Program,
            self.tr('<p>The file <b>{0}</b> contains the syntax error'
                    ' <b>{1}</b> at line <b>{2}</b>, character <b>{3}</b>.'
                    '</p>')
                .format(filename, message, lineNo, characterNo))
        
    def __clientException(self, exceptionType, exceptionMessage, stackTrace):
        """
        Private method to handle an exception of the debugged program.
        
        @param exceptionType type of exception raised (string)
        @param exceptionMessage message given by the exception (string)
        @param stackTrace list of stack entries (list of string)
        """
        self.ui.raise_()
        QApplication.processEvents()
        if exceptionType is None:
            E5MessageBox.critical(
                self.ui, Program,
                self.tr('An unhandled exception occured.'
                        ' See the shell window for details.'))
            return
        
        if (self.exceptions and
            exceptionType not in self.excIgnoreList and
            (not len(self.excList) or
             (len(self.excList) and exceptionType in self.excList)))\
           or exceptionType.startswith('unhandled'):
            res = None
            if stackTrace:
                try:
                    file, line = stackTrace[0][:2]
                    source, encoding = Utilities.readEncodedFile(file)
                    source = source.splitlines(True)
                    if len(source) >= line and \
                       "__IGNORE_EXCEPTION__" in Utilities.extractLineFlags(
                            source[line - 1]):
                        res = E5MessageBox.No
                except (UnicodeError, IOError):
                    pass
                if res != E5MessageBox.No:
                    self.viewmanager.setFileLine(
                        stackTrace[0][0], stackTrace[0][1], True)
            if res != E5MessageBox.No:
                self.ui.activateWindow()
                if Preferences.getDebugger("BreakAlways"):
                    res = E5MessageBox.Yes
                else:
                    if stackTrace:
                        if exceptionType.startswith('unhandled'):
                            buttons = E5MessageBox.StandardButtons(
                                E5MessageBox.No |
                                E5MessageBox.Yes)
                        else:
                            buttons = E5MessageBox.StandardButtons(
                                E5MessageBox.No |
                                E5MessageBox.Yes |
                                E5MessageBox.Ignore)
                        res = E5MessageBox.critical(
                            self.ui, Program,
                            self.tr(
                                '<p>The debugged program raised the exception'
                                ' <b>{0}</b><br>"<b>{1}</b>"<br>'
                                'File: <b>{2}</b>, Line: <b>{3}</b></p>'
                                '<p>Break here?</p>')
                            .format(
                                exceptionType,
                                Utilities.html_encode(exceptionMessage),
                                stackTrace[0][0],
                                stackTrace[0][1]),
                            buttons,
                            E5MessageBox.No)
                    else:
                        res = E5MessageBox.critical(
                            self.ui, Program,
                            self.tr(
                                '<p>The debugged program raised the exception'
                                ' <b>{0}</b><br>"<b>{1}</b>"</p>')
                            .format(
                                exceptionType,
                                Utilities.html_encode(exceptionMessage)))
            if res == E5MessageBox.Yes:
                self.exceptionInterrupt.emit()
                stack = []
                for fn, ln, func, args in stackTrace:
                    stack.append((fn, ln, func, args))
                self.clientStack.emit(stack)
                self.__getClientVariables()
                self.ui.setDebugProfile()
                self.debugActGrp.setEnabled(True)
                self.debugActGrp2.setEnabled(True)
                return
            elif res == E5MessageBox.Ignore:
                if exceptionType not in self.excIgnoreList:
                    self.excIgnoreList.append(exceptionType)
        
        if self.lastAction != -1:
            if self.lastAction == 2:
                self.__specialContinue()
            else:
                self.debugActions[self.lastAction]()
        else:
            self.__continue()
        
    def __clientSignal(self, message, filename, lineNo, funcName, funcArgs):
        """
        Private method to handle a signal generated on the client side.
        
        @param message message of the syntax error
        @type str
        @param filename translated filename of the syntax error position
        @type str
        @param lineNo line number of the syntax error position
        @type int
        @param funcName name of the function causing the signal
        @type str
        @param funcArgs function arguments
        @type str
        """
        self.ui.raise_()
        self.ui.activateWindow()
        QApplication.processEvents()
        self.viewmanager.setFileLine(filename, lineNo, True)
        E5MessageBox.critical(
            self.ui, Program,
            self.tr("""<p>The program generate the signal "{0}".<br/>"""
                    """File: <b>{1}</b>, Line: <b>{2}</b></p>""").format(
                message, filename, lineNo))
        
    def __clientGone(self, unplanned):
        """
        Private method to handle the disconnection of the debugger client.
        
        @param unplanned True if the client died, False otherwise
        """
        self.__resetUI()
        if unplanned:
            E5MessageBox.information(
                self.ui, Program,
                self.tr('The program being debugged has terminated'
                        ' unexpectedly.'))
        
    def __getThreadList(self):
        """
        Private method to get the list of threads from the client.
        """
        self.debugServer.remoteThreadList()
        
    def __clientThreadSet(self):
        """
        Private method to handle a change of the client's current thread.
        """
        self.debugServer.remoteClientVariables(0, self.localsVarFilter)
        
    def __getClientVariables(self):
        """
        Private method to request the global and local variables.
        
        In the first step, the global variables are requested from the client.
        Once these have been received, the local variables are requested.
        This happens in the method '__clientVariables'.
        """
        # get globals first
        self.debugServer.remoteClientVariables(1, self.globalsVarFilter)
        # the local variables are requested once we have received the globals
        
    def __clientVariables(self, scope, variables):
        """
        Private method to write the clients variables to the user interface.
        
        @param scope scope of the variables (-1 = empty global, 1 = global,
            0 = local)
        @param variables the list of variables from the client
        """
        if scope > 0:
            self.debugViewer.showVariables(variables, True)
            if scope == 1:
                # now get the local variables
                self.debugServer.remoteClientVariables(0, self.localsVarFilter)
        elif scope == 0:
            self.debugViewer.showVariables(variables, False)
        elif scope == -1:
            vlist = [('None', '', '')]
            self.debugViewer.showVariables(vlist, False)
        
    def __clientVariable(self, scope, variables):
        """
        Private method to write the contents of a clients classvariable to
        the user interface.
        
        @param scope scope of the variables (-1 = empty global, 1 = global,
            0 = local)
        @param variables the list of members of a classvariable from the client
        """
        if scope == 1:
            self.debugViewer.showVariable(variables, 1)
        elif scope == 0:
            self.debugViewer.showVariable(variables, 0)
            
    def __clientBreakConditionError(self, filename, lineno):
        """
        Private method to handle a condition error of a breakpoint.
        
        @param filename filename of the breakpoint (string)
        @param lineno linenumber of the breakpoint (integer)
        """
        E5MessageBox.critical(
            self.ui,
            self.tr("Breakpoint Condition Error"),
            self.tr(
                """<p>The condition of the breakpoint <b>{0}, {1}</b>"""
                """ contains a syntax error.</p>""")
            .format(filename, lineno))
        
        model = self.debugServer.getBreakPointModel()
        index = model.getBreakPointIndex(filename, lineno)
        if not index.isValid():
            return
        
        bp = model.getBreakPointByIndex(index)
        if not bp:
            return
        
        fn, line, cond, temp, enabled, count = bp[:6]
        
        from .EditBreakpointDialog import EditBreakpointDialog
        dlg = EditBreakpointDialog(
            (fn, line), (cond, temp, enabled, count),
            [], self.ui, modal=True)
        if dlg.exec_() == QDialog.Accepted:
            cond, temp, enabled, count = dlg.getData()
            model.setBreakPointByIndex(index, fn, line,
                                       (cond, temp, enabled, count))
        
    def __clientWatchConditionError(self, cond):
        """
        Private method to handle a expression error of a watch expression.
        
        Note: This can only happen for normal watch expressions
        
        @param cond expression of the watch expression (string)
        """
        E5MessageBox.critical(
            self.ui,
            self.tr("Watch Expression Error"),
            self.tr("""<p>The watch expression <b>{0}</b>"""
                    """ contains a syntax error.</p>""")
            .format(cond))
        
        model = self.debugServer.getWatchPointModel()
        index = model.getWatchPointIndex(cond)
        if not index.isValid():
            return
        
        wp = model.getWatchPointByIndex(index)
        if not wp:
            return
        
        cond, special, temp, enabled, count = wp[:5]
        
        from .EditWatchpointDialog import EditWatchpointDialog
        dlg = EditWatchpointDialog(
            (cond, temp, enabled, count, special), self)
        if dlg.exec_() == QDialog.Accepted:
            cond, temp, enabled, count, special = dlg.getData()
            
            # check for duplicates
            idx = self.__model.getWatchPointIndex(cond, special)
            duplicate = idx.isValid() and \
                idx.internalPointer() != index.internalPointer()
            if duplicate:
                if not special:
                    msg = self.tr("""<p>A watch expression '<b>{0}</b>'"""
                                  """ already exists.</p>""")\
                        .format(Utilities.html_encode(cond))
                else:
                    msg = self.tr(
                        """<p>A watch expression '<b>{0}</b>'"""
                        """ for the variable <b>{1}</b> already"""
                        """ exists.</p>""")\
                        .format(special,
                                Utilities.html_encode(cond))
                E5MessageBox.warning(
                    self.ui,
                    self.tr("Watch expression already exists"),
                    msg)
                model.deleteWatchPointByIndex(index)
            else:
                model.setWatchPointByIndex(index, cond, special,
                                           (temp, enabled, count))
        
    def __configureVariablesFilters(self):
        """
        Private slot for displaying the variables filter configuration dialog.
        """
        from .VariablesFilterDialog import VariablesFilterDialog
        dlg = VariablesFilterDialog(self.ui, 'Filter Dialog', True)
        dlg.setSelection(self.localsVarFilter, self.globalsVarFilter)
        if dlg.exec_() == QDialog.Accepted:
            self.localsVarFilter, self.globalsVarFilter = dlg.getSelection()
            self.debugViewer.setVariablesFilter(
                self.globalsVarFilter, self.localsVarFilter)

    def __configureExceptionsFilter(self):
        """
        Private slot for displaying the exception filter dialog.
        """
        from .ExceptionsFilterDialog import ExceptionsFilterDialog
        dlg = ExceptionsFilterDialog(self.excList, ignore=False)
        if dlg.exec_() == QDialog.Accepted:
            self.excList = dlg.getExceptionsList()[:]   # keep a copy
        
    def __configureIgnoredExceptions(self):
        """
        Private slot for displaying the ignored exceptions dialog.
        """
        from .ExceptionsFilterDialog import ExceptionsFilterDialog
        dlg = ExceptionsFilterDialog(self.excIgnoreList, ignore=True)
        if dlg.exec_() == QDialog.Accepted:
            self.excIgnoreList = dlg.getExceptionsList()[:]   # keep a copy
        
    def __toggleBreakpoint(self):
        """
        Private slot to handle the 'Set/Reset breakpoint' action.
        """
        self.viewmanager.activeWindow().menuToggleBreakpoint()
        
    def __editBreakpoint(self):
        """
        Private slot to handle the 'Edit breakpoint' action.
        """
        self.viewmanager.activeWindow().menuEditBreakpoint()
        
    def __nextBreakpoint(self):
        """
        Private slot to handle the 'Next breakpoint' action.
        """
        self.viewmanager.activeWindow().menuNextBreakpoint()
        
    def __previousBreakpoint(self):
        """
        Private slot to handle the 'Previous breakpoint' action.
        """
        self.viewmanager.activeWindow().menuPreviousBreakpoint()
        
    def __clearBreakpoints(self):
        """
        Private slot to handle the 'Clear breakpoints' action.
        """
        self.debugServer.getBreakPointModel().deleteAll()
        
    def __showDebugMenu(self):
        """
        Private method to set up the debug menu.
        """
        bpCount = self.debugServer.getBreakPointModel().rowCount()
        self.menuBreakpointsAct.setEnabled(bpCount > 0)
        
    def __showBreakpointsMenu(self):
        """
        Private method to handle the show breakpoints menu signal.
        """
        self.breakpointsMenu.clear()
        
        model = self.debugServer.getBreakPointModel()
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            filename, line, cond = model.getBreakPointByIndex(index)[:3]
            if not cond:
                formattedCond = ""
            else:
                formattedCond = " : {0}".format(cond[:20])
            bpSuffix = " : {0:d}{1}".format(line, formattedCond)
            act = self.breakpointsMenu.addAction(
                "{0}{1}".format(
                    Utilities.compactPath(
                        filename,
                        self.ui.maxMenuFilePathLen - len(bpSuffix)),
                    bpSuffix))
            act.setData([filename, line])
    
    def __breakpointSelected(self, act):
        """
        Private method to handle the breakpoint selected signal.
        
        @param act reference to the action that triggered (QAction)
        """
        qvList = act.data()
        filename = qvList[0]
        line = qvList[1]
        self.viewmanager.openSourceFile(filename, line)
        
    def __compileChangedProjectFiles(self):
        """
        Private method to signal compilation of changed forms and resources
        is wanted.
        """
        if Preferences.getProject("AutoCompileForms"):
            self.compileForms.emit()
        if Preferences.getProject("AutoCompileResources"):
            self.compileResources.emit()
        QApplication.processEvents()
        
    def __coverageScript(self):
        """
        Private slot to handle the coverage of script action.
        """
        self.__doCoverage(False)
        
    def __coverageProject(self):
        """
        Private slot to handle the coverage of project action.
        """
        self.__compileChangedProjectFiles()
        self.__doCoverage(True)
        
    def __doCoverage(self, runProject):
        """
        Private method to handle the coverage actions.
        
        @param runProject flag indicating coverage of the current project
            (True) or script (false)
        """
        from .StartDialog import StartDialog
        
        self.__resetUI()
        doNotStart = False
        
        # Get the command line arguments, the working directory and the
        # exception reporting flag.
        if runProject:
            cap = self.tr("Coverage of Project")
        else:
            cap = self.tr("Coverage of Script")
        dlg = StartDialog(
            cap, self.argvHistory, self.wdHistory,
            self.envHistory, self.exceptions, self.ui, 2,
            autoClearShell=self.autoClearShell)
        if dlg.exec_() == QDialog.Accepted:
            argv, wd, env, exceptions, clearShell, clearHistories, console = \
                dlg.getData()
            eraseCoverage = dlg.getCoverageData()
            
            if runProject:
                fn = self.project.getMainScript(True)
                if fn is None:
                    E5MessageBox.critical(
                        self.ui,
                        self.tr("Coverage of Project"),
                        self.tr(
                            "There is no main script defined for the"
                            " current project. Aborting"))
                    return
                    
                if Preferences.getDebugger("Autosave") and \
                   not self.project.saveAllScripts(reportSyntaxErrors=True):
                    doNotStart = True
                
                # save the info for later use
                self.project.setDbgInfo(
                    argv, wd, env, exceptions, self.excList,
                    self.excIgnoreList, clearShell)
                
                self.lastStartAction = 6
                self.clientType = self.project.getProjectLanguage()
            else:
                editor = self.viewmanager.activeWindow()
                if editor is None:
                    return
                
                if not self.viewmanager.checkDirty(
                        editor,
                        Preferences.getDebugger("Autosave")) or \
                        editor.getFileName() is None:
                    return
                    
                fn = editor.getFileName()
                self.lastStartAction = 5
                self.clientType = editor.determineFileType()
                
            # save the filename for use by the restart method
            self.lastDebuggedFile = fn
            self.restartAct.setEnabled(True)
            
            # This moves any previous occurrence of these arguments to the head
            # of the list.
            self.setArgvHistory(argv, clearHistories)
            self.setWdHistory(wd, clearHistories)
            self.setEnvHistory(env, clearHistories)
            
            # Save the exception flags
            self.exceptions = exceptions
            
            # Save the erase coverage flag
            self.eraseCoverage = eraseCoverage
            
            # Save the clear interpreter flag
            self.autoClearShell = clearShell
            
            # Save the run in console flag
            self.runInConsole = console
            
            # Hide all error highlights
            self.viewmanager.unhighlight()
            
            if not doNotStart:
                if runProject and self.project.getProjectType() in [
                        "E6Plugin"]:
                    argv = '--plugin="{0}" {1}'.format(fn, argv)
                    fn = os.path.join(getConfig('ericDir'), "eric6.py")
                
                self.debugViewer.initCallStackViewer(runProject)
                
                # Ask the client to open the new program.
                self.debugServer.remoteCoverage(
                    fn, argv, wd, env,
                    autoClearShell=self.autoClearShell, erase=eraseCoverage,
                    forProject=runProject, runInConsole=console,
                    clientType=self.clientType)
                
                self.stopAct.setEnabled(True)
            
    def __profileScript(self):
        """
        Private slot to handle the profile script action.
        """
        self.__doProfile(False)
        
    def __profileProject(self):
        """
        Private slot to handle the profile project action.
        """
        self.__compileChangedProjectFiles()
        self.__doProfile(True)
        
    def __doProfile(self, runProject):
        """
        Private method to handle the profile actions.
        
        @param runProject flag indicating profiling of the current project
            (True) or script (False)
        """
        from .StartDialog import StartDialog
        
        self.__resetUI()
        doNotStart = False
        
        # Get the command line arguments, the working directory and the
        # exception reporting flag.
        if runProject:
            cap = self.tr("Profile of Project")
        else:
            cap = self.tr("Profile of Script")
        dlg = StartDialog(
            cap, self.argvHistory, self.wdHistory, self.envHistory,
            self.exceptions, self.ui, 3,
            autoClearShell=self.autoClearShell)
        if dlg.exec_() == QDialog.Accepted:
            argv, wd, env, exceptions, clearShell, clearHistories, console = \
                dlg.getData()
            eraseTimings = dlg.getProfilingData()
            
            if runProject:
                fn = self.project.getMainScript(True)
                if fn is None:
                    E5MessageBox.critical(
                        self.ui,
                        self.tr("Profile of Project"),
                        self.tr(
                            "There is no main script defined for the"
                            " current project. Aborting"))
                    return
                    
                if Preferences.getDebugger("Autosave") and \
                   not self.project.saveAllScripts(reportSyntaxErrors=True):
                    doNotStart = True
                
                # save the info for later use
                self.project.setDbgInfo(
                    argv, wd, env, exceptions, self.excList,
                    self.excIgnoreList, clearShell)
                
                self.lastStartAction = 8
                self.clientType = self.project.getProjectLanguage()
            else:
                editor = self.viewmanager.activeWindow()
                if editor is None:
                    return
                
                if not self.viewmanager.checkDirty(
                        editor,
                        Preferences.getDebugger("Autosave")) or \
                        editor.getFileName() is None:
                    return
                    
                fn = editor.getFileName()
                self.lastStartAction = 7
                self.clientType = editor.determineFileType()
                
            # save the filename for use by the restart method
            self.lastDebuggedFile = fn
            self.restartAct.setEnabled(True)
            
            # This moves any previous occurrence of these arguments to the head
            # of the list.
            self.setArgvHistory(argv, clearHistories)
            self.setWdHistory(wd, clearHistories)
            self.setEnvHistory(env, clearHistories)
            
            # Save the exception flags
            self.exceptions = exceptions
            
            # Save the erase timing flag
            self.eraseTimings = eraseTimings
            
            # Save the clear interpreter flag
            self.autoClearShell = clearShell
            
            # Save the run in console flag
            self.runInConsole = console
            
            # Hide all error highlights
            self.viewmanager.unhighlight()
            
            if not doNotStart:
                if runProject and self.project.getProjectType() in [
                        "E6Plugin"]:
                    argv = '--plugin="{0}" {1}'.format(fn, argv)
                    fn = os.path.join(getConfig('ericDir'), "eric6.py")
                
                self.debugViewer.initCallStackViewer(runProject)
                
                # Ask the client to open the new program.
                self.debugServer.remoteProfile(
                    fn, argv, wd, env,
                    autoClearShell=self.autoClearShell, erase=eraseTimings,
                    forProject=runProject, runInConsole=console,
                    clientType=self.clientType)
                
                self.stopAct.setEnabled(True)
            
    def __runScript(self):
        """
        Private slot to handle the run script action.
        """
        self.__doRun(False)
        
    def __runProject(self):
        """
        Private slot to handle the run project action.
        """
        self.__compileChangedProjectFiles()
        self.__doRun(True)
        
    def __doRun(self, runProject):
        """
        Private method to handle the run actions.
        
        @param runProject flag indicating running the current project (True)
                or script (False)
        """
        from .StartDialog import StartDialog
        
        self.__resetUI()
        doNotStart = False
        
        # Get the command line arguments, the working directory and the
        # exception reporting flag.
        if runProject:
            cap = self.tr("Run Project")
        else:
            cap = self.tr("Run Script")
        dlg = StartDialog(
            cap, self.argvHistory, self.wdHistory, self.envHistory,
            self.exceptions, self.ui, 1,
            autoClearShell=self.autoClearShell,
            autoFork=self.forkAutomatically,
            forkChild=self.forkIntoChild)
        if dlg.exec_() == QDialog.Accepted:
            argv, wd, env, exceptions, clearShell, clearHistories, console = \
                dlg.getData()
            forkAutomatically, forkIntoChild = dlg.getRunData()
            
            if runProject:
                fn = self.project.getMainScript(True)
                if fn is None:
                    E5MessageBox.critical(
                        self.ui,
                        self.tr("Run Project"),
                        self.tr(
                            "There is no main script defined for the"
                            " current project. Aborting"))
                    return
                    
                if Preferences.getDebugger("Autosave") and \
                   not self.project.saveAllScripts(reportSyntaxErrors=True):
                    doNotStart = True
                
                # save the info for later use
                self.project.setDbgInfo(
                    argv, wd, env, exceptions, self.excList,
                    self.excIgnoreList, clearShell)
                
                self.lastStartAction = 4
                self.clientType = self.project.getProjectLanguage()
            else:
                editor = self.viewmanager.activeWindow()
                if editor is None:
                    return
                
                if not self.viewmanager.checkDirty(
                        editor,
                        Preferences.getDebugger("Autosave")) or \
                        editor.getFileName() is None:
                    return
                    
                fn = editor.getFileName()
                self.lastStartAction = 3
                self.clientType = editor.determineFileType()
                
            # save the filename for use by the restart method
            self.lastDebuggedFile = fn
            self.restartAct.setEnabled(True)
            
            # This moves any previous occurrence of these arguments to the head
            # of the list.
            self.setArgvHistory(argv, clearHistories)
            self.setWdHistory(wd, clearHistories)
            self.setEnvHistory(env, clearHistories)
            
            # Save the exception flags
            self.exceptions = exceptions
            
            # Save the clear interpreter flag
            self.autoClearShell = clearShell
            
            # Save the run in console flag
            self.runInConsole = console
            
            # Save the forking flags
            self.forkAutomatically = forkAutomatically
            self.forkIntoChild = forkIntoChild
            
            # Hide all error highlights
            self.viewmanager.unhighlight()
            
            if not doNotStart:
                if runProject and self.project.getProjectType() in [
                        "E6Plugin"]:
                    argv = '--plugin="{0}" {1}'.format(fn, argv)
                    fn = os.path.join(getConfig('ericDir'), "eric6.py")
                
                self.debugViewer.initCallStackViewer(runProject)
                
                # Ask the client to open the new program.
                self.debugServer.remoteRun(
                    fn, argv, wd, env,
                    autoClearShell=self.autoClearShell, forProject=runProject,
                    runInConsole=console, autoFork=forkAutomatically,
                    forkChild=forkIntoChild, clientType=self.clientType)
                
                self.stopAct.setEnabled(True)
        
    def __debugScript(self):
        """
        Private slot to handle the debug script action.
        """
        self.__doDebug(False)
        
    def __debugProject(self):
        """
        Private slot to handle the debug project action.
        """
        self.__compileChangedProjectFiles()
        self.__doDebug(True)
        
    def __doDebug(self, debugProject):
        """
        Private method to handle the debug actions.
        
        @param debugProject flag indicating debugging the current project
            (True) or script (False)
        """
        from .StartDialog import StartDialog
        
        self.__resetUI()
        doNotStart = False
        
        # Get the command line arguments, the working directory and the
        # exception reporting flag.
        if debugProject:
            cap = self.tr("Debug Project")
        else:
            cap = self.tr("Debug Script")
        dlg = StartDialog(
            cap, self.argvHistory, self.wdHistory, self.envHistory,
            self.exceptions, self.ui, 0, tracePython=self.tracePython,
            autoClearShell=self.autoClearShell, autoContinue=self.autoContinue,
            autoFork=self.forkAutomatically, forkChild=self.forkIntoChild)
        if dlg.exec_() == QDialog.Accepted:
            argv, wd, env, exceptions, clearShell, clearHistories, console = \
                dlg.getData()
            tracePython, autoContinue, forkAutomatically, forkIntoChild = \
                dlg.getDebugData()
            
            if debugProject:
                fn = self.project.getMainScript(True)
                if fn is None:
                    E5MessageBox.critical(
                        self.ui,
                        self.tr("Debug Project"),
                        self.tr(
                            "There is no main script defined for the"
                            " current project. No debugging possible."))
                    return
                    
                if Preferences.getDebugger("Autosave") and \
                   not self.project.saveAllScripts(reportSyntaxErrors=True):
                    doNotStart = True
                
                # save the info for later use
                self.project.setDbgInfo(
                    argv, wd, env, exceptions, self.excList,
                    self.excIgnoreList, clearShell, tracePython=tracePython,
                    autoContinue=self.autoContinue)
                
                self.lastStartAction = 2
                self.clientType = self.project.getProjectLanguage()
            else:
                editor = self.viewmanager.activeWindow()
                if editor is None:
                    return
                
                if not self.viewmanager.checkDirty(
                        editor,
                        Preferences.getDebugger("Autosave")) or \
                        editor.getFileName() is None:
                    return
                    
                fn = editor.getFileName()
                self.lastStartAction = 1
                self.clientType = editor.determineFileType()
            
            # save the filename for use by the restart method
            self.lastDebuggedFile = fn
            self.restartAct.setEnabled(True)
            
            # This moves any previous occurrence of these arguments to the head
            # of the list.
            self.setArgvHistory(argv, clearHistories)
            self.setWdHistory(wd, clearHistories)
            self.setEnvHistory(env, clearHistories)
            
            # Save the exception flags
            self.exceptions = exceptions
            
            # Save the tracePython flag
            self.tracePython = tracePython
            
            # Save the clear interpreter flag
            self.autoClearShell = clearShell
            
            # Save the run in console flag
            self.runInConsole = console
            
            # Save the auto continue flag
            self.autoContinue = autoContinue
            
            # Save the forking flags
            self.forkAutomatically = forkAutomatically
            self.forkIntoChild = forkIntoChild
            
            # Hide all error highlights
            self.viewmanager.unhighlight()
            
            if not doNotStart:
                if debugProject and self.project.getProjectType() in [
                        "E6Plugin"]:
                    argv = '--plugin="{0}" {1}'.format(fn, argv)
                    fn = os.path.join(getConfig('ericDir'), "eric6.py")
                    tracePython = True  # override flag because it must be true
                
                self.debugViewer.initCallStackViewer(debugProject)
                
                # Ask the client to send call trace info
                enableCallTrace = self.debugViewer.isCallTraceEnabled()
                self.debugViewer.clearCallTrace()
                self.debugViewer.setCallTraceToProjectMode(debugProject)
                
                # Ask the client to open the new program.
                self.debugServer.remoteLoad(
                    fn, argv, wd, env,
                    autoClearShell=self.autoClearShell,
                    tracePython=tracePython,
                    autoContinue=autoContinue, forProject=debugProject,
                    runInConsole=console, autoFork=forkAutomatically,
                    forkChild=forkIntoChild, clientType=self.clientType,
                    enableCallTrace=enableCallTrace)
                
                # Signal that we have started a debugging session
                self.debuggingStarted.emit(fn)
                
                self.stopAct.setEnabled(True)
        
    def __doRestart(self):
        """
        Private slot to handle the restart action to restart the last
        debugged file.
        """
        self.__resetUI()
        doNotStart = False
        
        # first save any changes
        if self.lastStartAction in [1, 3, 5, 7, 9]:
            editor = self.viewmanager.getOpenEditor(self.lastDebuggedFile)
            if editor and \
               not self.viewmanager.checkDirty(
                    editor, Preferences.getDebugger("Autosave")):
                return
            forProject = False
        elif self.lastStartAction in [2, 4, 6, 8, 10]:
            if Preferences.getDebugger("Autosave") and \
               not self.project.saveAllScripts(reportSyntaxErrors=True):
                doNotStart = True
            self.__compileChangedProjectFiles()
            forProject = True
        else:
            return      # should not happen
                    
        # get the saved stuff
        wd = self.wdHistory[0]
        argv = self.argvHistory[0]
        fn = self.lastDebuggedFile
        env = self.envHistory[0]
        
        # Hide all error highlights
        self.viewmanager.unhighlight()
        
        if not doNotStart:
            if forProject and self.project.getProjectType() in [
                    "E6Plugin"]:
                argv = '--plugin="{0}" {1}'.format(fn, argv)
                fn = os.path.join(getConfig('ericDir'), "eric6.py")
            
            self.debugViewer.initCallStackViewer(forProject)
            
            if self.lastStartAction in [1, 2]:
                # Ask the client to send call trace info
                enableCallTrace = self.debugViewer.isCallTraceEnabled()
                self.debugViewer.clearCallTrace()
                self.debugViewer.setCallTraceToProjectMode(forProject)
                
                # Ask the client to debug the new program.
                self.debugServer.remoteLoad(
                    fn, argv, wd, env,
                    autoClearShell=self.autoClearShell,
                    tracePython=self.tracePython,
                    autoContinue=self.autoContinue,
                    forProject=forProject,
                    runInConsole=self.runInConsole,
                    autoFork=self.forkAutomatically,
                    forkChild=self.forkIntoChild,
                    clientType=self.clientType,
                    enableCallTrace=enableCallTrace)
                
                # Signal that we have started a debugging session
                self.debuggingStarted.emit(fn)
            
            elif self.lastStartAction in [3, 4]:
                # Ask the client to run the new program.
                self.debugServer.remoteRun(
                    fn, argv, wd, env,
                    autoClearShell=self.autoClearShell,
                    forProject=forProject,
                    runInConsole=self.runInConsole,
                    autoFork=self.forkAutomatically,
                    forkChild=self.forkIntoChild,
                    clientType=self.clientType)
            
            elif self.lastStartAction in [5, 6]:
                # Ask the client to coverage run the new program.
                self.debugServer.remoteCoverage(
                    fn, argv, wd, env,
                    autoClearShell=self.autoClearShell,
                    erase=self.eraseCoverage,
                    forProject=forProject,
                    runInConsole=self.runInConsole,
                    clientType=self.clientType)
            
            elif self.lastStartAction in [7, 8]:
                # Ask the client to profile run the new program.
                self.debugServer.remoteProfile(
                    fn, argv, wd, env,
                    autoClearShell=self.autoClearShell,
                    erase=self.eraseTimings,
                    forProject=forProject,
                    runInConsole=self.runInConsole,
                    clientType=self.clientType)
            
            self.stopAct.setEnabled(True)
        
    def __stopScript(self):
        """
        Private slot to stop the running script.
        """
        self.debugServer.startClient(False)
        
    def __passiveDebugStarted(self, fn, exc):
        """
        Private slot to handle a passive debug session start.
        
        @param fn filename of the debugged script
        @param exc flag to enable exception reporting of the IDE (boolean)
        """
        # Hide all error highlights
        self.viewmanager.unhighlight()
        
        # Set filename of script being debugged
        self.ui.currentProg = fn
        
        # Set exception reporting
        self.setExceptionReporting(exc)
        
        # Signal that we have started a debugging session
        self.debuggingStarted.emit(fn)
        
        # Initialize the call stack viewer
        self.debugViewer.initCallStackViewer(False)
        
    def __continue(self):
        """
        Private method to handle the Continue action.
        """
        self.lastAction = 0
        self.__enterRemote()
        self.debugServer.remoteContinue()

    def __specialContinue(self):
        """
        Private method to handle the Special Continue action.
        """
        self.lastAction = 2
        self.__enterRemote()
        self.debugServer.remoteContinue(1)

    def __step(self):
        """
        Private method to handle the Step action.
        """
        self.lastAction = 1
        self.__enterRemote()
        self.debugServer.remoteStep()

    def __stepOver(self):
        """
        Private method to handle the Step Over action.
        """
        self.lastAction = 2
        self.__enterRemote()
        self.debugServer.remoteStepOver()

    def __stepOut(self):
        """
        Private method to handle the Step Out action.
        """
        self.lastAction = 3
        self.__enterRemote()
        self.debugServer.remoteStepOut()

    def __stepQuit(self):
        """
        Private method to handle the Step Quit action.
        """
        self.lastAction = 4
        self.__enterRemote()
        self.debugServer.remoteStepQuit()
        self.__resetUI()

    def __runToCursor(self):
        """
        Private method to handle the Run to Cursor action.
        """
        self.lastAction = 0
        aw = self.viewmanager.activeWindow()
        line = aw.getCursorPosition()[0] + 1
        self.__enterRemote()
        self.debugServer.remoteBreakpoint(
            aw.getFileName(), line, 1, None, 1)
        self.debugServer.remoteContinue()
    
    def __eval(self):
        """
        Private method to handle the Eval action.
        """
        # Get the command line arguments.
        if len(self.evalHistory) > 0:
            curr = 0
        else:
            curr = -1

        arg, ok = QInputDialog.getItem(
            self.ui,
            self.tr("Evaluate"),
            self.tr("Enter the statement to evaluate"),
            self.evalHistory,
            curr, True)

        if ok:
            if not arg:
                return

            # This moves any previous occurrence of this expression to the head
            # of the list.
            if arg in self.evalHistory:
                self.evalHistory.remove(arg)
            self.evalHistory.insert(0, arg)
            
            self.debugServer.remoteEval(arg)
            
    def __exec(self):
        """
        Private method to handle the Exec action.
        """
        # Get the command line arguments.
        if len(self.execHistory) > 0:
            curr = 0
        else:
            curr = -1

        stmt, ok = QInputDialog.getItem(
            self.ui,
            self.tr("Execute"),
            self.tr("Enter the statement to execute"),
            self.execHistory,
            curr, True)

        if ok:
            if not stmt:
                return

            # This moves any previous occurrence of this statement to the head
            # of the list.
            if stmt in self.execHistory:
                self.execHistory.remove(stmt)
            self.execHistory.insert(0, stmt)
            
            self.debugServer.remoteExec(stmt)
            
    def __enterRemote(self):
        """
        Private method to update the user interface.

        This method is called just prior to executing some of
        the program being debugged.
        """
        # Disable further debug commands from the user.
        self.debugActGrp.setEnabled(False)
        self.debugActGrp2.setEnabled(False)
        
        self.viewmanager.unhighlight(True)

    def getActions(self):
        """
        Public method to get a list of all actions.
        
        @return list of all actions (list of E5Action)
        """
        return self.actions[:]
