# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the main user interface.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os
import sys
import logging

from PyQt5.QtCore import pyqtSlot, QTimer, QFile, QFileInfo, pyqtSignal, \
    PYQT_VERSION_STR, QDate, QIODevice, qVersion, QProcess, QSize, QUrl, \
    QObject, Qt
from PyQt5.QtGui import QKeySequence, QDesktopServices
from PyQt5.QtWidgets import QSizePolicy, QWidget, QWhatsThis, QToolBar, \
    QDialog, QSplitter, QApplication, QMenu, QVBoxLayout, QDockWidget, \
    QAction, QLabel
from PyQt5.Qsci import QSCINTILLA_VERSION_STR
from PyQt5.QtNetwork import QNetworkProxyFactory, QNetworkAccessManager, \
    QNetworkRequest, QNetworkReply

from .Info import Version, BugAddress, Program, FeatureAddress
from . import Config

from E5Gui.E5SingleApplication import E5SingleApplicationServer
from E5Gui.E5Action import E5Action, createActionGroup
from E5Gui.E5ToolBarManager import E5ToolBarManager
from E5Gui import E5MessageBox, E5FileDialog, E5ErrorMessage
from E5Gui.E5Application import e5App
from E5Gui.E5MainWindow import E5MainWindow
from E5Gui.E5ZoomWidget import E5ZoomWidget
from E5Gui.E5ProgressDialog import E5ProgressDialog
from E5Gui.E5ClickableLabel import E5ClickableLabel

import Preferences
import Utilities

import UI.PixmapCache

from E5Network.E5NetworkProxyFactory import E5NetworkProxyFactory, \
    proxyAuthenticationRequired
try:
    from E5Network.E5SslErrorHandler import E5SslErrorHandler
    SSL_AVAILABLE = True
except ImportError:
    SSL_AVAILABLE = False

from eric6config import getConfig


class Redirector(QObject):
    """
    Helper class used to redirect stdout and stderr to the log window.
    
    @signal appendStderr(str) emitted to write data to stderr logger
    @signal appendStdout(str) emitted to write data to stdout logger
    """
    appendStderr = pyqtSignal(str)
    appendStdout = pyqtSignal(str)
    
    def __init__(self, stderr):
        """
        Constructor
        
        @param stderr flag indicating stderr is being redirected
        """
        super(Redirector, self).__init__()
        self.stderr = stderr
        self.buffer = ''
        
    def __nWrite(self, n):
        """
        Private method used to write data.
        
        @param n max number of bytes to write
        """
        if n:
            line = self.buffer[:n]
            if self.stderr:
                self.appendStderr.emit(line)
            else:
                self.appendStdout.emit(line)
            self.buffer = self.buffer[n:]
            
    def __bufferedWrite(self):
        """
        Private method returning number of characters to write.
        
        @return number of characters buffered or length of buffered line
            (integer)
        """
        return self.buffer.rfind('\n') + 1
        
    def flush(self):
        """
        Public method used to flush the buffered data.
        """
        self.__nWrite(len(self.buffer))
        
    def write(self, s):
        """
        Public method used to write data.
        
        @param s data to be written (it must support the str-method)
        """
        self.buffer += str(s)
        self.__nWrite(self.__bufferedWrite())


class UserInterface(E5MainWindow):
    """
    Class implementing the main user interface.
    
    @signal appendStderr(str) emitted to write data to stderr logger
    @signal appendStdout(str) emitted to write data to stdout logger
    @signal preferencesChanged() emitted after the preferences were changed
    @signal reloadAPIs() emitted to reload the api information
    @signal showMenu(str, QMenu) emitted when a menu is about to be shown. The
        name of the menu and a reference to the menu are given.
    @signal masterPasswordChanged(str, str) emitted after the master
        password has been changed with the old and the new password
    """
    appendStderr = pyqtSignal(str)
    appendStdout = pyqtSignal(str)
    preferencesChanged = pyqtSignal()
    reloadAPIs = pyqtSignal()
    showMenu = pyqtSignal(str, QMenu)
    masterPasswordChanged = pyqtSignal(str, str)
    
    maxFilePathLen = 100
    maxMenuFilePathLen = 75
    
    LeftSide = 1
    BottomSide = 2
    RightSide = 3
    
    ErrorLogFileName = "eric6_error.log"
    
    def __init__(self, app, locale, splash, plugin, noOpenAtStartup,
                 restartArguments):
        """
        Constructor
        
        @param app reference to the application object (E5Application)
        @param locale locale to be used by the UI (string)
        @param splash reference to the splashscreen
            (UI.SplashScreen.SplashScreen)
        @param plugin filename of a plugin to be loaded (used for plugin
            development)
        @param noOpenAtStartup flag indicating that the open at startup option
            should not be executed (boolean)
        @param restartArguments list of command line parameters to be used for
            a restart (list of strings)
        """
        super(UserInterface, self).__init__()
        
        self.__restartArgs = restartArguments[:]
        
        self.setStyle(Preferences.getUI("Style"),
                      Preferences.getUI("StyleSheet"))
        
        self.maxEditorPathLen = Preferences.getUI("CaptionFilenameLength")
        self.locale = locale
        self.__noOpenAtStartup = noOpenAtStartup
        
        self.layoutType, self.embeddedShell, self.embeddedFileBrowser = \
            Preferences.getUILayout()
        
        self.passiveMode = Preferences.getDebugger("PassiveDbgEnabled")
        
        g = Preferences.getGeometry("MainGeometry")
        if g.isEmpty():
            s = QSize(1280, 1024)
            self.resize(s)
        else:
            self.restoreGeometry(g)
        self.__startup = True
        
        self.__proxyFactory = E5NetworkProxyFactory()
        QNetworkProxyFactory.setApplicationProxyFactory(self.__proxyFactory)
        
        self.capProject = ""
        self.capEditor = ""
        self.captionShowsFilename = Preferences.getUI("CaptionShowsFilename")
        
        QApplication.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        self.__setWindowCaption()
        
        # load the view profiles
        self.profiles = Preferences.getUI("ViewProfiles2")
        
        # Generate the debug server object
        from Debugger.DebugServer import DebugServer
        debugServer = DebugServer()
        
        # Create the background service object
        from Utilities.BackgroundService import BackgroundService
        self.backgroundService = BackgroundService()
        
        # Generate an empty project object and multi project object
        from Project.Project import Project
        self.project = Project(self)
        
        from MultiProject.MultiProject import MultiProject
        self.multiProject = MultiProject(self.project, self)
        
        splash.showMessage(self.tr("Initializing Plugin Manager..."))
        
        # Initialize the Plugin Manager (Plugins are initialized later
        from PluginManager.PluginManager import PluginManager
        self.pluginManager = PluginManager(self, develPlugin=plugin)
        
        splash.showMessage(self.tr("Generating Main User Interface..."))
        
        # Create the main window now so that we can connect QActions to it.
        logging.debug("Creating Layout...")
        self.__createLayout(debugServer)
        self.__currentRightWidget = None
        self.__currentBottomWidget = None
        
        # Generate the debugger part of the ui
        logging.debug("Creating Debugger UI...")
        from Debugger.DebugUI import DebugUI
        self.debuggerUI = DebugUI(self, self.viewmanager, debugServer,
                                  self.debugViewer, self.project)
        self.debugViewer.setDebugger(self.debuggerUI)
        self.shell.setDebuggerUI(self.debuggerUI)
        
        # Generate the redirection helpers
        self.stdout = Redirector(False)
        self.stderr = Redirector(True)
        
        # set a few dialog members for dialogs created on demand
        self.programsDialog = None
        self.shortcutsDialog = None
        self.unittestDialog = None
        self.findFileNameDialog = None
        self.diffDlg = None
        self.compareDlg = None
        self.findFilesDialog = None
        self.replaceFilesDialog = None
        self.__notification = None
        
        # now setup the connections
        splash.showMessage(self.tr("Setting up connections..."))
        self.browser.sourceFile[str].connect(
            self.viewmanager.openSourceFile)
        self.browser.sourceFile[str, int].connect(
            self.viewmanager.openSourceFile)
        self.browser.sourceFile[str, list].connect(
            self.viewmanager.openSourceFile)
        self.browser.sourceFile[str, int, str].connect(
            self.viewmanager.openSourceFile)
        self.browser.designerFile.connect(self.__designer)
        self.browser.linguistFile.connect(self.__linguist4)
        self.browser.projectFile.connect(self.project.openProject)
        self.browser.multiProjectFile.connect(
            self.multiProject.openMultiProject)
        self.browser.pixmapEditFile.connect(self.__editPixmap)
        self.browser.pixmapFile.connect(self.__showPixmap)
        self.browser.svgFile.connect(self.__showSvg)
        self.browser.unittestOpen.connect(self.__unittestScript)
        self.browser.trpreview.connect(self.__TRPreviewer)
        
        self.debugViewer.exceptionLogger.sourceFile.connect(
            self.viewmanager.openSourceFile)
        
        self.debugViewer.sourceFile.connect(self.viewmanager.showDebugSource)
        
        self.taskViewer.displayFile.connect(self.viewmanager.openSourceFile)
        
        self.projectBrowser.psBrowser.sourceFile[str].connect(
            self.viewmanager.openSourceFile)
        self.projectBrowser.psBrowser.sourceFile[str, int].connect(
            self.viewmanager.openSourceFile)
        self.projectBrowser.psBrowser.sourceFile[str, list].connect(
            self.viewmanager.openSourceFile)
        self.projectBrowser.psBrowser.sourceFile[str, int, str].connect(
            self.viewmanager.openSourceFile)
        self.projectBrowser.psBrowser.closeSourceWindow.connect(
            self.viewmanager.closeWindow)
        self.projectBrowser.psBrowser.unittestOpen.connect(
            self.__unittestScript)
        
        self.projectBrowser.pfBrowser.designerFile.connect(self.__designer)
        self.projectBrowser.pfBrowser.sourceFile.connect(
            self.viewmanager.openSourceFile)
        self.projectBrowser.pfBrowser.uipreview.connect(self.__UIPreviewer)
        self.projectBrowser.pfBrowser.trpreview.connect(self.__TRPreviewer)
        self.projectBrowser.pfBrowser.closeSourceWindow.connect(
            self.viewmanager.closeWindow)
        self.projectBrowser.pfBrowser.appendStderr.connect(self.appendToStderr)
        
        self.projectBrowser.prBrowser.sourceFile.connect(
            self.viewmanager.openSourceFile)
        self.projectBrowser.prBrowser.closeSourceWindow.connect(
            self.viewmanager.closeWindow)
        self.projectBrowser.prBrowser.appendStderr.connect(self.appendToStderr)
        
        self.projectBrowser.ptBrowser.linguistFile.connect(self.__linguist4)
        self.projectBrowser.ptBrowser.sourceFile.connect(
            self.viewmanager.openSourceFile)
        self.projectBrowser.ptBrowser.trpreview[list].connect(
            self.__TRPreviewer)
        self.projectBrowser.ptBrowser.trpreview[list, bool].connect(
            self.__TRPreviewer)
        self.projectBrowser.ptBrowser.closeSourceWindow.connect(
            self.viewmanager.closeWindow)
        self.projectBrowser.ptBrowser.appendStdout.connect(self.appendToStdout)
        self.projectBrowser.ptBrowser.appendStderr.connect(self.appendToStderr)
        
        self.projectBrowser.piBrowser.sourceFile[str].connect(
            self.viewmanager.openSourceFile)
        self.projectBrowser.piBrowser.sourceFile[str, int].connect(
            self.viewmanager.openSourceFile)
        self.projectBrowser.piBrowser.closeSourceWindow.connect(
            self.viewmanager.closeWindow)
        self.projectBrowser.piBrowser.appendStdout.connect(self.appendToStdout)
        self.projectBrowser.piBrowser.appendStderr.connect(self.appendToStderr)
        
        self.projectBrowser.poBrowser.sourceFile.connect(
            self.viewmanager.openSourceFile)
        self.projectBrowser.poBrowser.closeSourceWindow.connect(
            self.viewmanager.closeWindow)
        self.projectBrowser.poBrowser.pixmapEditFile.connect(self.__editPixmap)
        self.projectBrowser.poBrowser.pixmapFile.connect(self.__showPixmap)
        self.projectBrowser.poBrowser.svgFile.connect(self.__showSvg)
        
        self.project.sourceFile.connect(self.viewmanager.openSourceFile)
        self.project.projectOpened.connect(self.viewmanager.projectOpened)
        self.project.projectClosed.connect(self.viewmanager.projectClosed)
        self.project.projectFileRenamed.connect(
            self.viewmanager.projectFileRenamed)
        self.project.lexerAssociationsChanged.connect(
            self.viewmanager.projectLexerAssociationsChanged)
        self.project.newProject.connect(self.__newProject)
        self.project.projectOpened.connect(self.__projectOpened)
        self.project.projectOpened.connect(self.__activateProjectBrowser)
        self.project.projectClosed.connect(self.__projectClosed)
        self.project.projectClosed.connect(
            self.backgroundService.preferencesOrProjectChanged)
        
        self.multiProject.multiProjectOpened.connect(
            self.__activateMultiProjectBrowser)
        
        self.debuggerUI.resetUI.connect(self.viewmanager.handleResetUI)
        self.debuggerUI.resetUI.connect(self.debugViewer.handleResetUI)
        self.debuggerUI.resetUI.connect(self.__debuggingDone)
        self.debuggerUI.debuggingStarted.connect(
            self.browser.handleProgramChange)
        self.debuggerUI.debuggingStarted.connect(
            self.debugViewer.exceptionLogger.debuggingStarted)
        self.debuggerUI.debuggingStarted.connect(
            self.debugViewer.handleDebuggingStarted)
        self.debuggerUI.debuggingStarted.connect(self.__programChange)
        self.debuggerUI.debuggingStarted.connect(self.__debuggingStarted)
        self.debuggerUI.compileForms.connect(
            self.projectBrowser.pfBrowser.compileChangedForms)
        self.debuggerUI.compileResources.connect(
            self.projectBrowser.prBrowser.compileChangedResources)
        self.debuggerUI.appendStdout.connect(self.appendToStdout)
        
        debugServer.passiveDebugStarted.connect(
            self.debugViewer.exceptionLogger.debuggingStarted)
        debugServer.passiveDebugStarted.connect(
            self.debugViewer.handleDebuggingStarted)
        debugServer.clientException.connect(
            self.debugViewer.exceptionLogger.addException)
        debugServer.clientLine.connect(
            self.debugViewer.breakpointViewer.highlightBreakpoint)
        debugServer.clientProcessStdout.connect(self.appendToStdout)
        debugServer.clientProcessStderr.connect(self.appendToStderr)
        debugServer.clientInterpreterChanged.connect(
            self.browser.handleInterpreterChanged)
        debugServer.appendStdout.connect(self.appendToStdout)
        
        self.stdout.appendStdout.connect(self.appendToStdout)
        self.stderr.appendStderr.connect(self.appendToStderr)
        
        self.preferencesChanged.connect(self.viewmanager.preferencesChanged)
        self.reloadAPIs.connect(self.viewmanager.getAPIsManager().reloadAPIs)
        self.preferencesChanged.connect(self.logViewer.preferencesChanged)
        self.appendStdout.connect(self.logViewer.appendToStdout)
        self.appendStderr.connect(self.logViewer.appendToStderr)
        self.preferencesChanged.connect(self.shell.handlePreferencesChanged)
        self.preferencesChanged.connect(self.project.handlePreferencesChanged)
        self.preferencesChanged.connect(
            self.projectBrowser.handlePreferencesChanged)
        self.preferencesChanged.connect(
            self.projectBrowser.psBrowser.handlePreferencesChanged)
        self.preferencesChanged.connect(
            self.projectBrowser.pfBrowser.handlePreferencesChanged)
        self.preferencesChanged.connect(
            self.projectBrowser.prBrowser.handlePreferencesChanged)
        self.preferencesChanged.connect(
            self.projectBrowser.ptBrowser.handlePreferencesChanged)
        self.preferencesChanged.connect(
            self.projectBrowser.piBrowser.handlePreferencesChanged)
        self.preferencesChanged.connect(
            self.projectBrowser.poBrowser.handlePreferencesChanged)
        self.preferencesChanged.connect(self.browser.handlePreferencesChanged)
        self.preferencesChanged.connect(
            self.taskViewer.handlePreferencesChanged)
        self.preferencesChanged.connect(self.pluginManager.preferencesChanged)
        self.preferencesChanged.connect(debugServer.preferencesChanged)
        self.preferencesChanged.connect(self.debugViewer.preferencesChanged)
        self.preferencesChanged.connect(self.cooperation.preferencesChanged)
        self.preferencesChanged.connect(
            self.backgroundService.preferencesOrProjectChanged)
        
        self.viewmanager.editorSaved.connect(self.project.repopulateItem)
        self.viewmanager.lastEditorClosed.connect(self.__lastEditorClosed)
        self.viewmanager.editorOpened.connect(self.__editorOpened)
        self.viewmanager.changeCaption.connect(self.__setWindowCaption)
        self.viewmanager.checkActions.connect(self.__checkActions)
        self.viewmanager.editorChanged.connect(
            self.projectBrowser.handleEditorChanged)
        self.viewmanager.editorLineChanged.connect(
            self.projectBrowser.handleEditorLineChanged)
        self.viewmanager.checkActions.connect(
            self.cooperation.checkEditorActions)
        
        self.shell.zoomValueChanged.connect(self.viewmanager.zoomValueChanged)
        
        self.cooperation.shareEditor.connect(self.viewmanager.shareEditor)
        self.cooperation.startEdit.connect(self.viewmanager.startSharedEdit)
        self.cooperation.sendEdit.connect(self.viewmanager.sendSharedEdit)
        self.cooperation.cancelEdit.connect(self.viewmanager.cancelSharedEdit)
        self.cooperation.connected.connect(self.viewmanager.shareConnected)
        self.cooperation.editorCommand.connect(self.viewmanager.receive)
        self.viewmanager.setCooperationClient(self.cooperation.getClient())
        
        self.symbolsViewer.insertSymbol.connect(self.viewmanager.insertSymbol)
        
        self.numbersViewer.insertNumber.connect(self.viewmanager.insertNumber)
        
        self.irc.autoConnected.connect(self.__ircAutoConnected)
        
        # create the toolbar manager object
        self.toolbarManager = E5ToolBarManager(self, self)
        self.toolbarManager.setMainWindow(self)
        
        # Initialize the tool groups and list of started tools
        splash.showMessage(self.tr("Initializing Tools..."))
        self.toolGroups, self.currentToolGroup = Preferences.readToolGroups()
        self.toolProcs = []
        self.__initExternalToolsActions()
        
        # create a dummy help window for shortcuts handling
        from Helpviewer.HelpWindow import HelpWindow
        self.dummyHelpViewer = \
            HelpWindow(None, '.', None, 'help viewer', True, True)
        
        # register all relevant objects
        splash.showMessage(self.tr("Registering Objects..."))
        e5App().registerObject("UserInterface", self)
        e5App().registerObject("DebugUI", self.debuggerUI)
        e5App().registerObject("DebugServer", debugServer)
        e5App().registerObject("BackgroundService", self.backgroundService)
        e5App().registerObject("ViewManager", self.viewmanager)
        e5App().registerObject("Project", self.project)
        e5App().registerObject("ProjectBrowser", self.projectBrowser)
        e5App().registerObject("MultiProject", self.multiProject)
        e5App().registerObject("TaskViewer", self.taskViewer)
        e5App().registerObject("TemplateViewer", self.templateViewer)
        e5App().registerObject("Shell", self.shell)
        e5App().registerObject("DummyHelpViewer", self.dummyHelpViewer)
        e5App().registerObject("PluginManager", self.pluginManager)
        e5App().registerObject("ToolbarManager", self.toolbarManager)
        e5App().registerObject("Cooperation", self.cooperation)
        e5App().registerObject("IRC", self.irc)
        e5App().registerObject("Symbols", self.symbolsViewer)
        e5App().registerObject("Numbers", self.numbersViewer)
        
        # Initialize the actions, menus, toolbars and statusbar
        splash.showMessage(self.tr("Initializing Actions..."))
        self.__initActions()
        splash.showMessage(self.tr("Initializing Menus..."))
        self.__initMenus()
        splash.showMessage(self.tr("Initializing Toolbars..."))
        self.__initToolbars()
        splash.showMessage(self.tr("Initializing Statusbar..."))
        self.__initStatusbar()
        
        # connect the appFocusChanged signal after all actions are ready
        app.focusChanged.connect(self.viewmanager.appFocusChanged)
        
        # Initialize the instance variables.
        self.currentProg = None
        self.isProg = False
        self.utEditorOpen = False
        self.utProjectOpen = False
        
        self.inDragDrop = False
        self.setAcceptDrops(True)
        
        self.currentProfile = None
        
        self.shutdownCalled = False
        self.inCloseEevent = False

        # now redirect stdout and stderr
        sys.stdout = self.stdout
        sys.stderr = self.stderr

        # now fire up the single application server
        if Preferences.getUI("SingleApplicationMode"):
            splash.showMessage(
                self.tr("Initializing Single Application Server..."))
            self.SAServer = E5SingleApplicationServer()
        else:
            self.SAServer = None
        
        # now finalize the plugin manager setup
        self.pluginManager.finalizeSetup()
        # now activate plugins having autoload set to True
        splash.showMessage(self.tr("Activating Plugins..."))
        self.pluginManager.activatePlugins()
        splash.showMessage(self.tr("Generating Plugins Toolbars..."))
        self.pluginManager.initPluginToolbars(self.toolbarManager)
        
        # now read the keyboard shortcuts for all the actions
        from Preferences import Shortcuts
        Shortcuts.readShortcuts()
        
        # restore toolbar manager state
        splash.showMessage(self.tr("Restoring Toolbarmanager..."))
        self.toolbarManager.restoreState(
            Preferences.getUI("ToolbarManagerState"))
        
        # now activate the initial view profile
        splash.showMessage(self.tr("Setting View Profile..."))
        self.__setEditProfile()
        
        # now read the saved tasks
        splash.showMessage(self.tr("Reading Tasks..."))
        self.__readTasks()
        
        # now read the saved templates
        splash.showMessage(self.tr("Reading Templates..."))
        self.templateViewer.readTemplates()
        
        # now start the debug client
        splash.showMessage(self.tr("Starting Debugger..."))
        debugServer.startClient(False)
        
        # attributes for the network objects
        self.__networkManager = QNetworkAccessManager(self)
        self.__networkManager.proxyAuthenticationRequired.connect(
            proxyAuthenticationRequired)
        if SSL_AVAILABLE:
            self.__sslErrorHandler = E5SslErrorHandler(self)
            self.__networkManager.sslErrors.connect(self.__sslErrors)
        self.__replies = []
        
        # attribute for the help window
        self.helpWindow = None
        
        # list of web addresses serving the versions file
        self.__httpAlternatives = Preferences.getUI("VersionsUrls6")
        self.__inVersionCheck = False
        self.__versionCheckProgress = None
        
        # set spellchecker defaults
        from QScintilla.SpellChecker import SpellChecker
        SpellChecker.setDefaultLanguage(
            Preferences.getEditor("SpellCheckingDefaultLanguage"))
        
        # attributes for the last shown configuration page and the
        # extended configuration entries
        self.__lastConfigurationPageName = ""
        self.__expandedConfigurationEntries = []
        
    def __createLayout(self, debugServer):
        """
        Private method to create the layout of the various windows.
        
        @param debugServer reference to the debug server object
        @exception ValueError raised to indicate an invalid layout type
        """
        # Create the view manager depending on the configuration setting
        logging.debug("Creating Viewmanager...")
        import ViewManager
        self.viewmanager = \
            ViewManager.factory(self, self, debugServer, self.pluginManager)
        leftWidget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)
        layout.addWidget(self.viewmanager)
        layout.addWidget(self.viewmanager.searchWidget())
        layout.addWidget(self.viewmanager.replaceWidget())
        self.viewmanager.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Expanding)
        leftWidget.setLayout(layout)
        self.viewmanager.searchWidget().hide()
        self.viewmanager.replaceWidget().hide()
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(leftWidget)
        self.setCentralWidget(splitter)
        
        # Create previewer
        logging.debug("Creating Previewer...")
        from .Previewer import Previewer
        self.__previewer = Previewer(self.viewmanager, splitter)
        splitter.addWidget(self.__previewer)
        
        # Create layout with toolbox windows embedded in dock windows
        if self.layoutType == "Toolboxes":
            logging.debug("Creating toolboxes...")
            self.__createToolboxesLayout(debugServer)
        
        # Create layout with sidebar windows embedded in dock windows
        elif self.layoutType == "Sidebars":
            logging.debug("Creating sidebars...")
            self.__createSidebarsLayout(debugServer)
        
        else:
            raise ValueError("Wrong layout type given ({0})".format(
                self.layoutType))
        logging.debug("Created Layout")

    def __createToolboxesLayout(self, debugServer):
        """
        Private method to create the Toolboxes layout.
        
        @param debugServer reference to the debug server object
        """
        from E5Gui.E5ToolBox import E5VerticalToolBox, E5HorizontalToolBox
        
        # Create the left toolbox
        self.lToolboxDock = self.__createDockWindow("lToolboxDock")
        self.lToolbox = E5VerticalToolBox(self.lToolboxDock)
        self.__setupDockWindow(self.lToolboxDock, Qt.LeftDockWidgetArea,
                               self.lToolbox, self.tr("Left Toolbox"))
        
        # Create the horizontal toolbox
        self.hToolboxDock = self.__createDockWindow("hToolboxDock")
        self.hToolbox = E5HorizontalToolBox(self.hToolboxDock)
        self.__setupDockWindow(self.hToolboxDock, Qt.BottomDockWidgetArea,
                               self.hToolbox,
                               self.tr("Horizontal Toolbox"))
        
        # Create the right toolbox
        self.rToolboxDock = self.__createDockWindow("rToolboxDock")
        self.rToolbox = E5VerticalToolBox(self.rToolboxDock)
        self.__setupDockWindow(self.rToolboxDock, Qt.RightDockWidgetArea,
                               self.rToolbox, self.tr("Right Toolbox"))
        
        # Create the project browser
        from Project.ProjectBrowser import ProjectBrowser
        self.projectBrowser = ProjectBrowser(
            self.project, None,
            embeddedBrowser=(self.embeddedFileBrowser == 2))
        self.lToolbox.addItem(self.projectBrowser,
                              UI.PixmapCache.getIcon("projectViewer.png"),
                              self.tr("Project-Viewer"))

        # Create the multi project browser
        from MultiProject.MultiProjectBrowser import MultiProjectBrowser
        self.multiProjectBrowser = MultiProjectBrowser(self.multiProject)
        self.lToolbox.addItem(self.multiProjectBrowser,
                              UI.PixmapCache.getIcon("multiProjectViewer.png"),
                              self.tr("Multiproject-Viewer"))

        # Create the template viewer part of the user interface
        from Templates.TemplateViewer import TemplateViewer
        self.templateViewer = TemplateViewer(None,
                                             self.viewmanager)
        self.lToolbox.addItem(self.templateViewer,
                              UI.PixmapCache.getIcon("templateViewer.png"),
                              self.tr("Template-Viewer"))

        # Create the debug viewer maybe without the embedded shell
        from Debugger.DebugViewer import DebugViewer
        self.debugViewer = DebugViewer(
            debugServer, True, self.viewmanager, None,
            embeddedShell=self.embeddedShell,
            embeddedBrowser=(self.embeddedFileBrowser == 1))
        self.rToolbox.addItem(self.debugViewer,
                              UI.PixmapCache.getIcon("debugViewer.png"),
                              self.tr("Debug-Viewer"))

        # Create the chat part of the user interface
        from Cooperation.ChatWidget import ChatWidget
        self.cooperation = ChatWidget(self)
        self.rToolbox.addItem(self.cooperation,
                              UI.PixmapCache.getIcon("cooperation.png"),
                              self.tr("Cooperation"))
        
        # Create the IRC part of the user interface
        from Network.IRC.IrcWidget import IrcWidget
        self.irc = IrcWidget(self)
        self.rToolbox.addItem(self.irc,
                              UI.PixmapCache.getIcon("irc.png"),
                              self.tr("IRC"))
        
        # Create the task viewer part of the user interface
        from Tasks.TaskViewer import TaskViewer
        self.taskViewer = TaskViewer(None, self.project)
        self.hToolbox.addItem(self.taskViewer,
                              UI.PixmapCache.getIcon("task.png"),
                              self.tr("Task-Viewer"))

        # Create the log viewer part of the user interface
        from .LogView import LogViewer
        self.logViewer = LogViewer(self)
        self.hToolbox.addItem(self.logViewer,
                              UI.PixmapCache.getIcon("logViewer.png"),
                              self.tr("Log-Viewer"))

        if self.embeddedShell:
            self.shell = self.debugViewer.shell
        else:
            # Create the shell
            from QScintilla.Shell import ShellAssembly
            self.shellAssembly = \
                ShellAssembly(debugServer, self.viewmanager, True)
            self.shell = self.shellAssembly.shell()
            self.hToolbox.insertItem(0, self.shellAssembly,
                                     UI.PixmapCache.getIcon("shell.png"),
                                     self.tr("Shell"))

        if self.embeddedFileBrowser == 0:   # separate window
            # Create the file browser
            from .Browser import Browser
            self.browser = Browser()
            self.lToolbox.addItem(self.browser,
                                  UI.PixmapCache.getIcon("browser.png"),
                                  self.tr("File-Browser"))
        elif self.embeddedFileBrowser == 1:  # embedded in debug browser
            self.browser = self.debugViewer.browser
        else:                               # embedded in project browser
            self.browser = self.projectBrowser.fileBrowser
        
        # Create the symbols viewer
        from .SymbolsWidget import SymbolsWidget
        self.symbolsViewer = SymbolsWidget()
        self.lToolbox.addItem(self.symbolsViewer,
                              UI.PixmapCache.getIcon("symbols.png"),
                              self.tr("Symbols"))
        
        # Create the numbers viewer
        from .NumbersWidget import NumbersWidget
        self.numbersViewer = NumbersWidget()
        self.hToolbox.addItem(self.numbersViewer,
                              UI.PixmapCache.getIcon("numbers.png"),
                              self.tr("Numbers"))
        
        self.hToolbox.setCurrentIndex(0)
        
    def __createSidebarsLayout(self, debugServer):
        """
        Private method to create the Sidebars layout.
        
        @param debugServer reference to the debug server object
        """
        from E5Gui.E5SideBar import E5SideBar
        
        delay = Preferences.getUI("SidebarDelay")
        # Create the left sidebar
        self.leftSidebar = E5SideBar(E5SideBar.West, delay)
        
        # Create the bottom sidebar
        self.bottomSidebar = E5SideBar(E5SideBar.South, delay)
        
        # Create the right sidebar
        self.rightSidebar = E5SideBar(E5SideBar.East, delay)
        
        # Create the project browser
        logging.debug("Creating Project Browser...")
        from Project.ProjectBrowser import ProjectBrowser
        self.projectBrowser = ProjectBrowser(
            self.project, None,
            embeddedBrowser=(self.embeddedFileBrowser == 2))
        self.leftSidebar.addTab(
            self.projectBrowser,
            UI.PixmapCache.getIcon("projectViewer.png"),
            self.tr("Project-Viewer"))

        # Create the multi project browser
        logging.debug("Creating Multiproject Browser...")
        from MultiProject.MultiProjectBrowser import MultiProjectBrowser
        self.multiProjectBrowser = MultiProjectBrowser(self.multiProject)
        self.leftSidebar.addTab(
            self.multiProjectBrowser,
            UI.PixmapCache.getIcon("multiProjectViewer.png"),
            self.tr("Multiproject-Viewer"))

        # Create the template viewer part of the user interface
        logging.debug("Creating Template Viewer...")
        from Templates.TemplateViewer import TemplateViewer
        self.templateViewer = TemplateViewer(None,
                                             self.viewmanager)
        self.leftSidebar.addTab(
            self.templateViewer,
            UI.PixmapCache.getIcon("templateViewer.png"),
            self.tr("Template-Viewer"))

        # Create the debug viewer maybe without the embedded shell
        logging.debug("Creating Debug Viewer...")
        from Debugger.DebugViewer import DebugViewer
        self.debugViewer = DebugViewer(
            debugServer, True, self.viewmanager, None,
            embeddedShell=self.embeddedShell,
            embeddedBrowser=(self.embeddedFileBrowser == 1))
        self.rightSidebar.addTab(
            self.debugViewer, UI.PixmapCache.getIcon("debugViewer.png"),
            self.tr("Debug-Viewer"))

        # Create the chat part of the user interface
        logging.debug("Creating Chat Widget...")
        from Cooperation.ChatWidget import ChatWidget
        self.cooperation = ChatWidget(self)
        self.rightSidebar.addTab(
            self.cooperation, UI.PixmapCache.getIcon("cooperation.png"),
            self.tr("Cooperation"))
        
        # Create the IRC part of the user interface
        logging.debug("Creating IRC Widget...")
        from Network.IRC.IrcWidget import IrcWidget
        self.irc = IrcWidget(self)
        self.rightSidebar.addTab(
            self.irc, UI.PixmapCache.getIcon("irc.png"), self.tr("IRC"))
        
        # Create the task viewer part of the user interface
        logging.debug("Creating Task Viewer...")
        from Tasks.TaskViewer import TaskViewer
        self.taskViewer = TaskViewer(None, self.project)
        self.bottomSidebar.addTab(self.taskViewer,
                                  UI.PixmapCache.getIcon("task.png"),
                                  self.tr("Task-Viewer"))

        # Create the log viewer part of the user interface
        logging.debug("Creating Log Viewer...")
        from .LogView import LogViewer
        self.logViewer = LogViewer(self)
        self.bottomSidebar.addTab(self.logViewer,
                                  UI.PixmapCache.getIcon("logViewer.png"),
                                  self.tr("Log-Viewer"))

        if self.embeddedShell:
            self.shell = self.debugViewer.shell
        else:
            # Create the shell
            logging.debug("Creating Shell...")
            from QScintilla.Shell import ShellAssembly
            self.shellAssembly = \
                ShellAssembly(debugServer, self.viewmanager, True)
            self.shell = self.shellAssembly.shell()
            self.bottomSidebar.insertTab(0, self.shellAssembly,
                                         UI.PixmapCache.getIcon("shell.png"),
                                         self.tr("Shell"))

        if self.embeddedFileBrowser == 0:   # separate window
            # Create the file browser
            logging.debug("Creating File Browser...")
            from .Browser import Browser
            self.browser = Browser()
            self.leftSidebar.addTab(self.browser,
                                    UI.PixmapCache.getIcon("browser.png"),
                                    self.tr("File-Browser"))
        elif self.embeddedFileBrowser == 1:  # embedded in debug browser
            self.browser = self.debugViewer.browser
        else:                               # embedded in project browser
            self.browser = self.projectBrowser.fileBrowser
        
        # Create the symbols viewer
        logging.debug("Creating Symbols Viewer...")
        from .SymbolsWidget import SymbolsWidget
        self.symbolsViewer = SymbolsWidget()
        self.leftSidebar.addTab(self.symbolsViewer,
                                UI.PixmapCache.getIcon("symbols.png"),
                                self.tr("Symbols"))
        
        # Create the numbers viewer
        logging.debug("Creating Numbers Viewer...")
        from .NumbersWidget import NumbersWidget
        self.numbersViewer = NumbersWidget()
        self.bottomSidebar.addTab(self.numbersViewer,
                                  UI.PixmapCache.getIcon("numbers.png"),
                                  self.tr("Numbers"))
        
        self.bottomSidebar.setCurrentIndex(0)
        
        # create the central widget
        logging.debug("Creating central widget...")
        cw = self.centralWidget()   # save the current central widget
        self.leftSplitter = QSplitter(Qt.Horizontal)
        self.rightSplitter = QSplitter(Qt.Horizontal)
        self.verticalSplitter = QSplitter(Qt.Vertical)
        self.verticalSplitter.addWidget(cw)
        self.verticalSplitter.addWidget(self.bottomSidebar)
        self.rightSplitter.addWidget(self.verticalSplitter)
        self.rightSplitter.addWidget(self.rightSidebar)
        self.leftSplitter.addWidget(self.leftSidebar)
        self.leftSplitter.addWidget(self.rightSplitter)
        self.setCentralWidget(self.leftSplitter)
        
        self.leftSidebar.setSplitter(self.leftSplitter)
        self.rightSidebar.setSplitter(self.rightSplitter)
        self.bottomSidebar.setSplitter(self.verticalSplitter)
        
    def __configureDockareaCornerUsage(self):
        """
        Private method to configure the usage of the dockarea corners.
        """
        if Preferences.getUI("TopLeftByLeft"):
            self.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
        else:
            self.setCorner(Qt.TopLeftCorner, Qt.TopDockWidgetArea)
        if Preferences.getUI("BottomLeftByLeft"):
            self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        else:
            self.setCorner(Qt.BottomLeftCorner, Qt.BottomDockWidgetArea)
        if Preferences.getUI("TopRightByRight"):
            self.setCorner(Qt.TopRightCorner, Qt.RightDockWidgetArea)
        else:
            self.setCorner(Qt.TopRightCorner, Qt.TopDockWidgetArea)
        if Preferences.getUI("BottomRightByRight"):
            self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)
        else:
            self.setCorner(Qt.BottomRightCorner, Qt.BottomDockWidgetArea)
        
    def addSideWidget(self, side, widget, icon, label):
        """
        Public method to add a widget to the sides.
        
        @param side side to add the widget to (UserInterface.LeftSide,
            UserInterface.BottomSide)
        @param widget reference to the widget to add (QWidget)
        @param icon icon to be used (QIcon)
        @param label label text to be shown (string)
        """
        assert side in [UserInterface.LeftSide, UserInterface.BottomSide]
        
        if self.layoutType == "Toolboxes":
            if side == UserInterface.LeftSide:
                self.lToolbox.addItem(widget, icon, label)
            elif side == UserInterface.BottomSide:
                self.hToolbox.addItem(widget, icon, label)
            elif side == UserInterface.RightSide:
                self.rToolbox.addItem(widget, icon, label)
        elif self.layoutType == "Sidebars":
            if side == UserInterface.LeftSide:
                self.leftSidebar.addTab(widget, icon, label)
            elif side == UserInterface.BottomSide:
                self.bottomSidebar.addTab(widget, icon, label)
            elif side == UserInterface.RightSide:
                self.rightSidebar.addTab(widget, icon, label)
        
    def removeSideWidget(self, widget):
        """
        Public method to remove a widget added using addSideWidget().
        
        @param widget reference to the widget to remove (QWidget)
        """
        if self.layoutType == "Toolboxes":
            for container in [self.lToolbox, self.hToolbox, self.rToolbox]:
                index = container.indexOf(widget)
                if index != -1:
                    container.removeItem(index)
        elif self.layoutType == "Sidebars":
            for container in [self.leftSidebar, self.bottomSidebar,
                              self.rightSidebar]:
                index = container.indexOf(widget)
                if index != -1:
                    container.removeTab(index)
        
    def showLogViewer(self):
        """
        Public method to show the Log-Viewer.
        """
        if Preferences.getUI("LogViewerAutoRaise"):
            if self.layoutType == "Toolboxes":
                self.hToolboxDock.show()
                self.hToolbox.setCurrentWidget(self.logViewer)
                self.hToolboxDock.raise_()
            elif self.layoutType == "Sidebars":
                self.bottomSidebar.show()
                self.bottomSidebar.setCurrentWidget(self.logViewer)
                self.bottomSidebar.raise_()
                if self.bottomSidebar.isAutoHiding():
                    self.bottomSidebar.setFocus()
        
    def __openOnStartup(self, startupType=None):
        """
        Private method to open the last file, project or multiproject.
        
        @param startupType type of startup requested (string, one of
            "Nothing", "File", "Project", "MultiProject" or "Session")
        """
        startupTypeMapping = {
            "Nothing": 0,
            "File": 1,
            "Project": 2,
            "MultiProject": 3,
            "Session": 4,
        }
        
        if startupType is None:
            startup = Preferences.getUI("OpenOnStartup")
        else:
            try:
                startup = startupTypeMapping[startupType]
            except KeyError:
                startup = Preferences.getUI("OpenOnStartup")
        
        if startup == 0:
            # open nothing
            pass
        elif startup == 1:
            # open last file
            recent = self.viewmanager.getMostRecent()
            if recent is not None:
                self.viewmanager.openFiles(recent)
        elif startup == 2:
            # open last project
            recent = self.project.getMostRecent()
            if recent is not None:
                self.project.openProject(recent)
        elif startup == 3:
            # open last multiproject
            recent = self.multiProject.getMostRecent()
            if recent is not None:
                self.multiProject.openMultiProject(recent)
        elif startup == 4:
            # open from session file
            self.__readSession()
        
    def processArgs(self, args):
        """
        Public method to process the command line args passed to the UI.
        
        @param args list of files to open<br />
            The args are processed one at a time. All arguments after a
            '--' option are considered debug arguments to the program
            for the debugger. All files named before the '--' option
            are opened in a text editor, unless the argument ends in
            .e4p, then it is opened as a project file. If it ends in
            .e4m or .e5m, it is opened as a multiproject.
        """
        # no args, return
        if args is None:
            if not self.__noOpenAtStartup:
                self.__openOnStartup()
            return
        
        opens = 0
        
        # holds space delimited list of command args, if any
        argsStr = None
        # flag indicating '--' options was found
        ddseen = False
        
        if Utilities.isWindowsPlatform():
            argChars = ['-', '/']
        else:
            argChars = ['-']

        for arg in args:
            # handle a request to start with last session
            if arg == '--start-file':
                self.__openOnStartup("File")
                # ignore all further arguments
                return
            elif arg == '--start-multi':
                self.__openOnStartup("MultiProject")
                # ignore all further arguments
                return
            elif arg == '--start-project':
                self.__openOnStartup("Project")
                # ignore all further arguments
                return
            elif arg == '--start-session':
                self.__openOnStartup("Session")
                # ignore all further arguments
                return
            
            if arg == '--' and not ddseen:
                ddseen = True
                continue
            
            if arg[0] in argChars or ddseen:
                if argsStr is None:
                    argsStr = arg
                else:
                    argsStr = "{0} {1}".format(argsStr, arg)
                continue
            
            try:
                ext = os.path.splitext(arg)[1]
                ext = os.path.normcase(ext)
            except IndexError:
                ext = ""

            if ext in ['.e4p']:
                self.project.openProject(arg)
                opens += 1
            elif ext in ['.e4m', '.e5m']:
                self.multiProject.openMultiProject(arg)
                opens += 1
            else:
                self.viewmanager.openFiles(arg)
                opens += 1

        # store away any args we had
        if argsStr is not None:
            self.debuggerUI.setArgvHistory(argsStr)
        
        if opens == 0:
            # no files, project or multiproject was given
            if not self.__noOpenAtStartup:
                self.__openOnStartup()
        
    def __createDockWindow(self, name):
        """
        Private method to create a dock window with common properties.
        
        @param name object name of the new dock window (string)
        @return the generated dock window (QDockWindow)
        """
        dock = QDockWidget()
        dock.setObjectName(name)
        dock.setFeatures(
            QDockWidget.DockWidgetFeatures(QDockWidget.AllDockWidgetFeatures))
        return dock

    def __setupDockWindow(self, dock, where, widget, caption):
        """
        Private method to configure the dock window created with
        __createDockWindow().
        
        @param dock the dock window (QDockWindow)
        @param where dock area to be docked to (Qt.DockWidgetArea)
        @param widget widget to be shown in the dock window (QWidget)
        @param caption caption of the dock window (string)
        """
        if caption is None:
            caption = ""
        self.addDockWidget(where, dock)
        dock.setWidget(widget)
        dock.setWindowTitle(caption)
        dock.show()

    def __setWindowCaption(self, editor=None, project=None):
        """
        Private method to set the caption of the Main Window.
        
        @param editor filename to be displayed (string)
        @param project project name to be displayed (string)
        """
        if editor is not None and self.captionShowsFilename:
            self.capEditor = \
                Utilities.compactPath(editor, self.maxFilePathLen)
        if project is not None:
            self.capProject = project
        
        if self.passiveMode:
            if not self.capProject and not self.capEditor:
                self.setWindowTitle(
                    self.tr("{0} - Passive Mode").format(Program))
            elif self.capProject and not self.capEditor:
                self.setWindowTitle(
                    self.tr("{0} - {1} - Passive Mode")
                        .format(self.capProject, Program))
            elif not self.capProject and self.capEditor:
                self.setWindowTitle(
                    self.tr("{0} - {1} - Passive Mode")
                        .format(self.capEditor, Program))
            else:
                self.setWindowTitle(
                    self.tr("{0} - {1} - {2} - Passive Mode")
                    .format(self.capProject, self.capEditor, Program))
        else:
            if not self.capProject and not self.capEditor:
                self.setWindowTitle(Program)
            elif self.capProject and not self.capEditor:
                self.setWindowTitle(
                    "{0} - {1}".format(self.capProject, Program))
            elif not self.capProject and self.capEditor:
                self.setWindowTitle(
                    "{0} - {1}".format(self.capEditor, Program))
            else:
                self.setWindowTitle("{0} - {1} - {2}".format(
                    self.capProject, self.capEditor, Program))
        
    def __initActions(self):
        """
        Private method to define the user interface actions.
        """
        self.actions = []
        self.wizardsActions = []
        
        self.exitAct = E5Action(
            self.tr('Quit'),
            UI.PixmapCache.getIcon("exit.png"),
            self.tr('&Quit'),
            QKeySequence(self.tr("Ctrl+Q", "File|Quit")),
            0, self, 'quit')
        self.exitAct.setStatusTip(self.tr('Quit the IDE'))
        self.exitAct.setWhatsThis(self.tr(
            """<b>Quit the IDE</b>"""
            """<p>This quits the IDE. Any unsaved changes may be saved"""
            """ first. Any Python program being debugged will be stopped"""
            """ and the preferences will be written to disc.</p>"""
        ))
        self.exitAct.triggered.connect(self.__quit)
        self.exitAct.setMenuRole(QAction.QuitRole)
        self.actions.append(self.exitAct)

        self.newWindowAct = E5Action(
            self.tr('New Window'),
            UI.PixmapCache.getIcon("newWindow.png"),
            self.tr('New &Window'),
            QKeySequence(self.tr("Ctrl+Shift+N", "File|New Window")),
            0, self, 'new_window')
        self.newWindowAct.setStatusTip(self.tr(
            'Open a new eric6 instance'))
        self.newWindowAct.setWhatsThis(self.tr(
            """<b>New Window</b>"""
            """<p>This opens a new instance of the eric6 IDE.</p>"""
        ))
        self.newWindowAct.triggered.connect(self.__newWindow)
        self.actions.append(self.newWindowAct)
        self.newWindowAct.setEnabled(
            not Preferences.getUI("SingleApplicationMode"))
        
        self.viewProfileActGrp = createActionGroup(self, "viewprofiles", True)
        
        self.setEditProfileAct = E5Action(
            self.tr('Edit Profile'),
            UI.PixmapCache.getIcon("viewProfileEdit.png"),
            self.tr('Edit Profile'),
            0, 0,
            self.viewProfileActGrp, 'edit_profile', True)
        self.setEditProfileAct.setStatusTip(self.tr(
            'Activate the edit view profile'))
        self.setEditProfileAct.setWhatsThis(self.tr(
            """<b>Edit Profile</b>"""
            """<p>Activate the "Edit View Profile". Windows being shown,"""
            """ if this profile is active, may be configured with the"""
            """ "View Profile Configuration" dialog.</p>"""
        ))
        self.setEditProfileAct.triggered.connect(self.__setEditProfile)
        self.actions.append(self.setEditProfileAct)
        
        self.setDebugProfileAct = E5Action(
            self.tr('Debug Profile'),
            UI.PixmapCache.getIcon("viewProfileDebug.png"),
            self.tr('Debug Profile'),
            0, 0,
            self.viewProfileActGrp, 'debug_profile', True)
        self.setDebugProfileAct.setStatusTip(
            self.tr('Activate the debug view profile'))
        self.setDebugProfileAct.setWhatsThis(self.tr(
            """<b>Debug Profile</b>"""
            """<p>Activate the "Debug View Profile". Windows being shown,"""
            """ if this profile is active, may be configured with the"""
            """ "View Profile Configuration" dialog.</p>"""
        ))
        self.setDebugProfileAct.triggered.connect(self.setDebugProfile)
        self.actions.append(self.setDebugProfileAct)
        
        self.pbActivateAct = E5Action(
            self.tr('Project-Viewer'),
            self.tr('&Project-Viewer'),
            QKeySequence(self.tr("Alt+Shift+P")),
            0, self,
            'project_viewer_activate')
        self.pbActivateAct.setStatusTip(self.tr(
            "Switch the input focus to the Project-Viewer window."))
        self.pbActivateAct.setWhatsThis(self.tr(
            """<b>Activate Project-Viewer</b>"""
            """<p>This switches the input focus to the Project-Viewer"""
            """ window.</p>"""
        ))
        self.pbActivateAct.triggered.connect(self.__activateProjectBrowser)
        self.actions.append(self.pbActivateAct)
        self.addAction(self.pbActivateAct)

        self.mpbActivateAct = E5Action(
            self.tr('Multiproject-Viewer'),
            self.tr('&Multiproject-Viewer'),
            QKeySequence(self.tr("Alt+Shift+M")),
            0, self,
            'multi_project_viewer_activate')
        self.mpbActivateAct.setStatusTip(self.tr(
            "Switch the input focus to the Multiproject-Viewer window."))
        self.mpbActivateAct.setWhatsThis(self.tr(
            """<b>Activate Multiproject-Viewer</b>"""
            """<p>This switches the input focus to the Multiproject-Viewer"""
            """ window.</p>"""
        ))
        self.mpbActivateAct.triggered.connect(
            self.__activateMultiProjectBrowser)
        self.actions.append(self.mpbActivateAct)
        self.addAction(self.mpbActivateAct)

        self.debugViewerActivateAct = E5Action(
            self.tr('Debug-Viewer'),
            self.tr('&Debug-Viewer'),
            QKeySequence(self.tr("Alt+Shift+D")),
            0, self,
            'debug_viewer_activate')
        self.debugViewerActivateAct.setStatusTip(self.tr(
            "Switch the input focus to the Debug-Viewer window."))
        self.debugViewerActivateAct.setWhatsThis(self.tr(
            """<b>Activate Debug-Viewer</b>"""
            """<p>This switches the input focus to the Debug-Viewer"""
            """ window.</p>"""
        ))
        self.debugViewerActivateAct.triggered.connect(
            self.__activateDebugViewer)
        self.actions.append(self.debugViewerActivateAct)
        self.addAction(self.debugViewerActivateAct)

        self.shellActivateAct = E5Action(
            self.tr('Shell'),
            self.tr('&Shell'),
            QKeySequence(self.tr("Alt+Shift+S")),
            0, self,
            'interprter_shell_activate')
        self.shellActivateAct.setStatusTip(self.tr(
            "Switch the input focus to the Shell window."))
        self.shellActivateAct.setWhatsThis(self.tr(
            """<b>Activate Shell</b>"""
            """<p>This switches the input focus to the Shell window.</p>"""
        ))
        self.shellActivateAct.triggered.connect(self.__activateShell)
        self.actions.append(self.shellActivateAct)
        self.addAction(self.shellActivateAct)

        self.browserActivateAct = E5Action(
            self.tr('File-Browser'),
            self.tr('&File-Browser'),
            QKeySequence(self.tr("Alt+Shift+F")),
            0, self,
            'file_browser_activate')
        self.browserActivateAct.setStatusTip(self.tr(
            "Switch the input focus to the File-Browser window."))
        self.browserActivateAct.setWhatsThis(self.tr(
            """<b>Activate File-Browser</b>"""
            """<p>This switches the input focus to the File-Browser"""
            """ window.</p>"""
        ))
        self.browserActivateAct.triggered.connect(self.__activateBrowser)
        self.actions.append(self.browserActivateAct)
        self.addAction(self.browserActivateAct)

        self.logViewerActivateAct = E5Action(
            self.tr('Log-Viewer'),
            self.tr('Lo&g-Viewer'),
            QKeySequence(self.tr("Alt+Shift+G")),
            0, self,
            'log_viewer_activate')
        self.logViewerActivateAct.setStatusTip(self.tr(
            "Switch the input focus to the Log-Viewer window."))
        self.logViewerActivateAct.setWhatsThis(self.tr(
            """<b>Activate Log-Viewer</b>"""
            """<p>This switches the input focus to the Log-Viewer"""
            """ window.</p>"""
        ))
        self.logViewerActivateAct.triggered.connect(
            self.__activateLogViewer)
        self.actions.append(self.logViewerActivateAct)
        self.addAction(self.logViewerActivateAct)

        self.taskViewerActivateAct = E5Action(
            self.tr('Task-Viewer'),
            self.tr('&Task-Viewer'),
            QKeySequence(self.tr("Alt+Shift+T")),
            0, self,
            'task_viewer_activate')
        self.taskViewerActivateAct.setStatusTip(self.tr(
            "Switch the input focus to the Task-Viewer window."))
        self.taskViewerActivateAct.setWhatsThis(self.tr(
            """<b>Activate Task-Viewer</b>"""
            """<p>This switches the input focus to the Task-Viewer"""
            """ window.</p>"""
        ))
        self.taskViewerActivateAct.triggered.connect(
            self.__activateTaskViewer)
        self.actions.append(self.taskViewerActivateAct)
        self.addAction(self.taskViewerActivateAct)

        self.templateViewerActivateAct = E5Action(
            self.tr('Template-Viewer'),
            self.tr('Templ&ate-Viewer'),
            QKeySequence(self.tr("Alt+Shift+A")),
            0, self,
            'template_viewer_activate')
        self.templateViewerActivateAct.setStatusTip(self.tr(
            "Switch the input focus to the Template-Viewer window."))
        self.templateViewerActivateAct.setWhatsThis(self.tr(
            """<b>Activate Template-Viewer</b>"""
            """<p>This switches the input focus to the Template-Viewer"""
            """ window.</p>"""
        ))
        self.templateViewerActivateAct.triggered.connect(
            self.__activateTemplateViewer)
        self.actions.append(self.templateViewerActivateAct)
        self.addAction(self.templateViewerActivateAct)

        self.ltAct = E5Action(
            self.tr('Left Toolbox'),
            self.tr('&Left Toolbox'), 0, 0, self, 'vertical_toolbox', True)
        self.ltAct.setStatusTip(self.tr('Toggle the Left Toolbox window'))
        self.ltAct.setWhatsThis(self.tr(
            """<b>Toggle the Left Toolbox window</b>"""
            """<p>If the Left Toolbox window is hidden then display it."""
            """ If it is displayed then close it.</p>"""
        ))
        self.ltAct.triggered.connect(self.__toggleLeftToolbox)
        self.actions.append(self.ltAct)
        
        self.rtAct = E5Action(
            self.tr('Right Toolbox'),
            self.tr('&Right Toolbox'),
            0, 0, self, 'vertical_toolbox', True)
        self.rtAct.setStatusTip(self.tr('Toggle the Right Toolbox window'))
        self.rtAct.setWhatsThis(self.tr(
            """<b>Toggle the Right Toolbox window</b>"""
            """<p>If the Right Toolbox window is hidden then display it."""
            """ If it is displayed then close it.</p>"""
        ))
        self.rtAct.triggered.connect(self.__toggleRightToolbox)
        self.actions.append(self.rtAct)
        
        self.htAct = E5Action(
            self.tr('Horizontal Toolbox'),
            self.tr('&Horizontal Toolbox'), 0, 0, self,
            'horizontal_toolbox', True)
        self.htAct.setStatusTip(self.tr(
            'Toggle the Horizontal Toolbox window'))
        self.htAct.setWhatsThis(self.tr(
            """<b>Toggle the Horizontal Toolbox window</b>"""
            """<p>If the Horizontal Toolbox window is hidden then display"""
            """ it. If it is displayed then close it.</p>"""
        ))
        self.htAct.triggered.connect(self.__toggleHorizontalToolbox)
        self.actions.append(self.htAct)
        
        self.lsbAct = E5Action(
            self.tr('Left Sidebar'),
            self.tr('&Left Sidebar'),
            0, 0, self, 'left_sidebar', True)
        self.lsbAct.setStatusTip(self.tr('Toggle the left sidebar window'))
        self.lsbAct.setWhatsThis(self.tr(
            """<b>Toggle the left sidebar window</b>"""
            """<p>If the left sidebar window is hidden then display it."""
            """ If it is displayed then close it.</p>"""
        ))
        self.lsbAct.triggered.connect(self.__toggleLeftSidebar)
        self.actions.append(self.lsbAct)
        
        self.rsbAct = E5Action(
            self.tr('Right Sidebar'),
            self.tr('&Right Sidebar'),
            0, 0, self, 'right_sidebar', True)
        self.rsbAct.setStatusTip(self.tr(
            'Toggle the right sidebar window'))
        self.rsbAct.setWhatsThis(self.tr(
            """<b>Toggle the right sidebar window</b>"""
            """<p>If the right sidebar window is hidden then display it."""
            """ If it is displayed then close it.</p>"""
        ))
        self.rsbAct.triggered.connect(self.__toggleRightSidebar)
        self.actions.append(self.rsbAct)
        
        self.bsbAct = E5Action(
            self.tr('Bottom Sidebar'),
            self.tr('&Bottom Sidebar'), 0, 0, self,
            'bottom_sidebar', True)
        self.bsbAct.setStatusTip(self.tr(
            'Toggle the bottom sidebar window'))
        self.bsbAct.setWhatsThis(self.tr(
            """<b>Toggle the bottom sidebar window</b>"""
            """<p>If the bottom sidebar window is hidden then display it."""
            """ If it is displayed then close it.</p>"""
        ))
        self.bsbAct.triggered.connect(self.__toggleBottomSidebar)
        self.actions.append(self.bsbAct)
        
        self.cooperationViewerActivateAct = E5Action(
            self.tr('Cooperation-Viewer'),
            self.tr('Co&operation-Viewer'),
            QKeySequence(self.tr("Alt+Shift+O")),
            0, self,
            'cooperation_viewer_activate')
        self.cooperationViewerActivateAct.setStatusTip(self.tr(
            "Switch the input focus to the Cooperation-Viewer window."))
        self.cooperationViewerActivateAct.setWhatsThis(self.tr(
            """<b>Activate Cooperation-Viewer</b>"""
            """<p>This switches the input focus to the Cooperation-Viewer"""
            """ window.</p>"""
        ))
        self.cooperationViewerActivateAct.triggered.connect(
            self.activateCooperationViewer)
        self.actions.append(self.cooperationViewerActivateAct)
        self.addAction(self.cooperationViewerActivateAct)

        self.ircActivateAct = E5Action(
            self.tr('IRC'),
            self.tr('&IRC'),
            QKeySequence(self.tr("Meta+Shift+I")),
            0, self,
            'irc_widget_activate')
        self.ircActivateAct.setStatusTip(self.tr(
            "Switch the input focus to the IRC window."))
        self.ircActivateAct.setWhatsThis(self.tr(
            """<b>Activate IRC</b>"""
            """<p>This switches the input focus to the IRC window.</p>"""
        ))
        self.ircActivateAct.triggered.connect(
            self.__activateIRC)
        self.actions.append(self.ircActivateAct)
        self.addAction(self.ircActivateAct)

        self.symbolsViewerActivateAct = E5Action(
            self.tr('Symbols-Viewer'),
            self.tr('S&ymbols-Viewer'),
            QKeySequence(self.tr("Alt+Shift+Y")),
            0, self,
            'symbols_viewer_activate')
        self.symbolsViewerActivateAct.setStatusTip(self.tr(
            "Switch the input focus to the Symbols-Viewer window."))
        self.symbolsViewerActivateAct.setWhatsThis(self.tr(
            """<b>Activate Symbols-Viewer</b>"""
            """<p>This switches the input focus to the Symbols-Viewer"""
            """ window.</p>"""
        ))
        self.symbolsViewerActivateAct.triggered.connect(
            self.__activateSymbolsViewer)
        self.actions.append(self.symbolsViewerActivateAct)
        self.addAction(self.symbolsViewerActivateAct)

        self.numbersViewerActivateAct = E5Action(
            self.tr('Numbers-Viewer'),
            self.tr('Num&bers-Viewer'),
            QKeySequence(self.tr("Alt+Shift+B")),
            0, self,
            'numbers_viewer_activate')
        self.numbersViewerActivateAct.setStatusTip(self.tr(
            "Switch the input focus to the Numbers-Viewer window."))
        self.numbersViewerActivateAct.setWhatsThis(self.tr(
            """<b>Activate Numbers-Viewer</b>"""
            """<p>This switches the input focus to the Numbers-Viewer"""
            """ window.</p>"""
        ))
        self.numbersViewerActivateAct.triggered.connect(
            self.__activateNumbersViewer)
        self.actions.append(self.numbersViewerActivateAct)
        self.addAction(self.numbersViewerActivateAct)

        self.whatsThisAct = E5Action(
            self.tr('What\'s This?'),
            UI.PixmapCache.getIcon("whatsThis.png"),
            self.tr('&What\'s This?'),
            QKeySequence(self.tr("Shift+F1")),
            0, self, 'whatsThis')
        self.whatsThisAct.setStatusTip(self.tr('Context sensitive help'))
        self.whatsThisAct.setWhatsThis(self.tr(
            """<b>Display context sensitive help</b>"""
            """<p>In What's This? mode, the mouse cursor shows an arrow with"""
            """ a question mark, and you can click on the interface elements"""
            """ to get a short description of what they do and how to use"""
            """ them. In dialogs, this feature can be accessed using the"""
            """ context help button in the titlebar.</p>"""
        ))
        self.whatsThisAct.triggered.connect(self.__whatsThis)
        self.actions.append(self.whatsThisAct)

        self.helpviewerAct = E5Action(
            self.tr('Helpviewer'),
            UI.PixmapCache.getIcon("help.png"),
            self.tr('&Helpviewer...'),
            QKeySequence(self.tr("F1")),
            0, self, 'helpviewer')
        self.helpviewerAct.setStatusTip(self.tr(
            'Open the helpviewer window'))
        self.helpviewerAct.setWhatsThis(self.tr(
            """<b>Helpviewer</b>"""
            """<p>Display the eric6 web browser. This window will show"""
            """ HTML help files and help from Qt help collections. It has"""
            """ the capability to navigate to links, set bookmarks, print"""
            """ the displayed help and some more features. You may use it to"""
            """ browse the internet as well</p><p>If called with a word"""
            """ selected, this word is search in the Qt help collection.</p>"""
        ))
        self.helpviewerAct.triggered.connect(self.__helpViewer)
        self.actions.append(self.helpviewerAct)
        
        self.__initQtDocActions()
        self.__initPythonDocActions()
        self.__initEricDocAction()
        self.__initPySideDocAction()
      
        self.versionAct = E5Action(
            self.tr('Show Versions'),
            self.tr('Show &Versions'),
            0, 0, self, 'show_versions')
        self.versionAct.setStatusTip(self.tr(
            'Display version information'))
        self.versionAct.setWhatsThis(self.tr(
            """<b>Show Versions</b>"""
            """<p>Display version information.</p>"""
        ))
        self.versionAct.triggered.connect(self.__showVersions)
        self.actions.append(self.versionAct)

        self.checkUpdateAct = E5Action(
            self.tr('Check for Updates'),
            self.tr('Check for &Updates...'), 0, 0, self, 'check_updates')
        self.checkUpdateAct.setStatusTip(self.tr('Check for Updates'))
        self.checkUpdateAct.setWhatsThis(self.tr(
            """<b>Check for Updates...</b>"""
            """<p>Checks the internet for updates of eric6.</p>"""
        ))
        self.checkUpdateAct.triggered.connect(self.performVersionCheck)
        self.actions.append(self.checkUpdateAct)
    
        self.showVersionsAct = E5Action(
            self.tr('Show downloadable versions'),
            self.tr('Show &downloadable versions...'),
            0, 0, self, 'show_downloadable_versions')
        self.showVersionsAct.setStatusTip(
            self.tr('Show the versions available for download'))
        self.showVersionsAct.setWhatsThis(self.tr(
            """<b>Show downloadable versions...</b>"""
            """<p>Shows the eric6 versions available for download """
            """from the internet.</p>"""
        ))
        self.showVersionsAct.triggered.connect(
            self.showAvailableVersionsInfo)
        self.actions.append(self.showVersionsAct)

        self.showErrorLogAct = E5Action(
            self.tr('Show Error Log'),
            self.tr('Show Error &Log...'),
            0, 0, self, 'show_error_log')
        self.showErrorLogAct.setStatusTip(self.tr('Show Error Log'))
        self.showErrorLogAct.setWhatsThis(self.tr(
            """<b>Show Error Log...</b>"""
            """<p>Opens a dialog showing the most recent error log.</p>"""
        ))
        self.showErrorLogAct.triggered.connect(self.__showErrorLog)
        self.actions.append(self.showErrorLogAct)
        
        self.reportBugAct = E5Action(
            self.tr('Report Bug'),
            self.tr('Report &Bug...'),
            0, 0, self, 'report_bug')
        self.reportBugAct.setStatusTip(self.tr('Report a bug'))
        self.reportBugAct.setWhatsThis(self.tr(
            """<b>Report Bug...</b>"""
            """<p>Opens a dialog to report a bug.</p>"""
        ))
        self.reportBugAct.triggered.connect(self.__reportBug)
        self.actions.append(self.reportBugAct)
        
        self.requestFeatureAct = E5Action(
            self.tr('Request Feature'),
            self.tr('Request &Feature...'),
            0, 0, self, 'request_feature')
        self.requestFeatureAct.setStatusTip(self.tr(
            'Send a feature request'))
        self.requestFeatureAct.setWhatsThis(self.tr(
            """<b>Request Feature...</b>"""
            """<p>Opens a dialog to send a feature request.</p>"""
        ))
        self.requestFeatureAct.triggered.connect(self.__requestFeature)
        self.actions.append(self.requestFeatureAct)

        self.utActGrp = createActionGroup(self)
        
        self.utDialogAct = E5Action(
            self.tr('Unittest'),
            UI.PixmapCache.getIcon("unittest.png"),
            self.tr('&Unittest...'),
            0, 0, self.utActGrp, 'unittest')
        self.utDialogAct.setStatusTip(self.tr('Start unittest dialog'))
        self.utDialogAct.setWhatsThis(self.tr(
            """<b>Unittest</b>"""
            """<p>Perform unit tests. The dialog gives you the"""
            """ ability to select and run a unittest suite.</p>"""
        ))
        self.utDialogAct.triggered.connect(self.__unittest)
        self.actions.append(self.utDialogAct)

        self.utRestartAct = E5Action(
            self.tr('Unittest Restart'),
            UI.PixmapCache.getIcon("unittestRestart.png"),
            self.tr('&Restart Unittest...'),
            0, 0, self.utActGrp, 'unittest_restart')
        self.utRestartAct.setStatusTip(self.tr('Restart last unittest'))
        self.utRestartAct.setWhatsThis(self.tr(
            """<b>Restart Unittest</b>"""
            """<p>Restart the unittest performed last.</p>"""
        ))
        self.utRestartAct.triggered.connect(self.__unittestRestart)
        self.utRestartAct.setEnabled(False)
        self.actions.append(self.utRestartAct)
        
        self.utRerunFailedAct = E5Action(
            self.tr('Unittest Rerun Failed'),
            UI.PixmapCache.getIcon("unittestRerunFailed.png"),
            self.tr('Rerun Failed Tests...'),
            0, 0, self.utActGrp, 'unittest_rerun_failed')
        self.utRerunFailedAct.setStatusTip(self.tr(
            'Rerun failed tests of the last run'))
        self.utRerunFailedAct.setWhatsThis(self.tr(
            """<b>Rerun Failed Tests</b>"""
            """<p>Rerun all tests that failed during the last unittest"""
            """ run.</p>"""
        ))
        self.utRerunFailedAct.triggered.connect(self.__unittestRerunFailed)
        self.utRerunFailedAct.setEnabled(False)
        self.actions.append(self.utRerunFailedAct)
        
        self.utScriptAct = E5Action(
            self.tr('Unittest Script'),
            UI.PixmapCache.getIcon("unittestScript.png"),
            self.tr('Unittest &Script...'),
            0, 0, self.utActGrp, 'unittest_script')
        self.utScriptAct.setStatusTip(self.tr(
            'Run unittest with current script'))
        self.utScriptAct.setWhatsThis(self.tr(
            """<b>Unittest Script</b>"""
            """<p>Run unittest with current script.</p>"""
        ))
        self.utScriptAct.triggered.connect(self.__unittestScript)
        self.utScriptAct.setEnabled(False)
        self.actions.append(self.utScriptAct)
        
        self.utProjectAct = E5Action(
            self.tr('Unittest Project'),
            UI.PixmapCache.getIcon("unittestProject.png"),
            self.tr('Unittest &Project...'),
            0, 0, self.utActGrp, 'unittest_project')
        self.utProjectAct.setStatusTip(self.tr(
            'Run unittest with current project'))
        self.utProjectAct.setWhatsThis(self.tr(
            """<b>Unittest Project</b>"""
            """<p>Run unittest with current project.</p>"""
        ))
        self.utProjectAct.triggered.connect(self.__unittestProject)
        self.utProjectAct.setEnabled(False)
        self.actions.append(self.utProjectAct)
        
        # check for Qt4/Qt5 designer and linguist
        if Utilities.isWindowsPlatform():
            designerExe = os.path.join(
                Utilities.getQtBinariesPath(),
                "{0}.exe".format(Utilities.generateQtToolName("designer")))
        elif Utilities.isMacPlatform():
            designerExe = Utilities.getQtMacBundle("designer")
        else:
            designerExe = os.path.join(
                Utilities.getQtBinariesPath(),
                Utilities.generateQtToolName("designer"))
        if os.path.exists(designerExe):
            self.designer4Act = E5Action(
                self.tr('Qt-Designer'),
                UI.PixmapCache.getIcon("designer4.png"),
                self.tr('Qt-&Designer...'),
                0, 0, self, 'qt_designer4')
            self.designer4Act.setStatusTip(self.tr('Start Qt-Designer'))
            self.designer4Act.setWhatsThis(self.tr(
                """<b>Qt-Designer</b>"""
                """<p>Start Qt-Designer.</p>"""
            ))
            self.designer4Act.triggered.connect(self.__designer4)
            self.actions.append(self.designer4Act)
        else:
            self.designer4Act = None
        
        if Utilities.isWindowsPlatform():
            linguistExe = os.path.join(
                Utilities.getQtBinariesPath(),
                "{0}.exe".format(Utilities.generateQtToolName("linguist")))
        elif Utilities.isMacPlatform():
            linguistExe = Utilities.getQtMacBundle("linguist")
        else:
            linguistExe = os.path.join(
                Utilities.getQtBinariesPath(),
                Utilities.generateQtToolName("linguist"))
        if os.path.exists(linguistExe):
            self.linguist4Act = E5Action(
                self.tr('Qt-Linguist'),
                UI.PixmapCache.getIcon("linguist4.png"),
                self.tr('Qt-&Linguist...'),
                0, 0, self, 'qt_linguist4')
            self.linguist4Act.setStatusTip(self.tr('Start Qt-Linguist'))
            self.linguist4Act.setWhatsThis(self.tr(
                """<b>Qt-Linguist</b>"""
                """<p>Start Qt-Linguist.</p>"""
            ))
            self.linguist4Act.triggered.connect(self.__linguist4)
            self.actions.append(self.linguist4Act)
        else:
            self.linguist4Act = None
    
        self.uipreviewerAct = E5Action(
            self.tr('UI Previewer'),
            UI.PixmapCache.getIcon("uiPreviewer.png"),
            self.tr('&UI Previewer...'),
            0, 0, self, 'ui_previewer')
        self.uipreviewerAct.setStatusTip(self.tr('Start the UI Previewer'))
        self.uipreviewerAct.setWhatsThis(self.tr(
            """<b>UI Previewer</b>"""
            """<p>Start the UI Previewer.</p>"""
        ))
        self.uipreviewerAct.triggered.connect(self.__UIPreviewer)
        self.actions.append(self.uipreviewerAct)
        
        self.trpreviewerAct = E5Action(
            self.tr('Translations Previewer'),
            UI.PixmapCache.getIcon("trPreviewer.png"),
            self.tr('&Translations Previewer...'),
            0, 0, self, 'tr_previewer')
        self.trpreviewerAct.setStatusTip(self.tr(
            'Start the Translations Previewer'))
        self.trpreviewerAct.setWhatsThis(self.tr(
            """<b>Translations Previewer</b>"""
            """<p>Start the Translations Previewer.</p>"""
        ))
        self.trpreviewerAct.triggered.connect(self.__TRPreviewer)
        self.actions.append(self.trpreviewerAct)
        
        self.diffAct = E5Action(
            self.tr('Compare Files'),
            UI.PixmapCache.getIcon("diffFiles.png"),
            self.tr('&Compare Files...'),
            0, 0, self, 'diff_files')
        self.diffAct.setStatusTip(self.tr('Compare two files'))
        self.diffAct.setWhatsThis(self.tr(
            """<b>Compare Files</b>"""
            """<p>Open a dialog to compare two files.</p>"""
        ))
        self.diffAct.triggered.connect(self.__compareFiles)
        self.actions.append(self.diffAct)

        self.compareAct = E5Action(
            self.tr('Compare Files side by side'),
            UI.PixmapCache.getIcon("compareFiles.png"),
            self.tr('Compare &Files side by side...'),
            0, 0, self, 'compare_files')
        self.compareAct.setStatusTip(self.tr('Compare two files'))
        self.compareAct.setWhatsThis(self.tr(
            """<b>Compare Files side by side</b>"""
            """<p>Open a dialog to compare two files and show the result"""
            """ side by side.</p>"""
        ))
        self.compareAct.triggered.connect(self.__compareFilesSbs)
        self.actions.append(self.compareAct)

        self.sqlBrowserAct = E5Action(
            self.tr('SQL Browser'),
            UI.PixmapCache.getIcon("sqlBrowser.png"),
            self.tr('SQL &Browser...'),
            0, 0, self, 'sql_browser')
        self.sqlBrowserAct.setStatusTip(self.tr('Browse a SQL database'))
        self.sqlBrowserAct.setWhatsThis(self.tr(
            """<b>SQL Browser</b>"""
            """<p>Browse a SQL database.</p>"""
        ))
        self.sqlBrowserAct.triggered.connect(self.__sqlBrowser)
        self.actions.append(self.sqlBrowserAct)

        self.miniEditorAct = E5Action(
            self.tr('Mini Editor'),
            UI.PixmapCache.getIcon("editor.png"),
            self.tr('Mini &Editor...'),
            0, 0, self, 'mini_editor')
        self.miniEditorAct.setStatusTip(self.tr('Mini Editor'))
        self.miniEditorAct.setWhatsThis(self.tr(
            """<b>Mini Editor</b>"""
            """<p>Open a dialog with a simplified editor.</p>"""
        ))
        self.miniEditorAct.triggered.connect(self.__openMiniEditor)
        self.actions.append(self.miniEditorAct)

        self.webBrowserAct = E5Action(
            self.tr('eric6 Web Browser'),
            UI.PixmapCache.getIcon("ericWeb.png"),
            self.tr('eric6 &Web Browser...'),
            0, 0, self, 'web_browser')
        self.webBrowserAct.setStatusTip(self.tr(
            'Start the eric6 Web Browser'))
        self.webBrowserAct.setWhatsThis(self.tr(
            """<b>eric6 Web Browser</b>"""
            """<p>Browse the Internet with the eric6 Web Browser.</p>"""
        ))
        self.webBrowserAct.triggered.connect(self.__startWebBrowser)
        self.actions.append(self.webBrowserAct)

        self.iconEditorAct = E5Action(
            self.tr('Icon Editor'),
            UI.PixmapCache.getIcon("iconEditor.png"),
            self.tr('&Icon Editor...'),
            0, 0, self, 'icon_editor')
        self.iconEditorAct.setStatusTip(self.tr(
            'Start the eric6 Icon Editor'))
        self.iconEditorAct.setWhatsThis(self.tr(
            """<b>Icon Editor</b>"""
            """<p>Starts the eric6 Icon Editor for editing simple icons.</p>"""
        ))
        self.iconEditorAct.triggered.connect(self.__editPixmap)
        self.actions.append(self.iconEditorAct)

        self.snapshotAct = E5Action(
            self.tr('Snapshot'),
            UI.PixmapCache.getIcon("ericSnap.png"),
            self.tr('&Snapshot...'),
            0, 0, self, 'snapshot')
        self.snapshotAct.setStatusTip(self.tr(
            'Take snapshots of a screen region'))
        self.snapshotAct.setWhatsThis(self.tr(
            """<b>Snapshot</b>"""
            """<p>This opens a dialog to take snapshots of a screen"""
            """ region.</p>"""
        ))
        self.snapshotAct.triggered.connect(self.__snapshot)
        self.actions.append(self.snapshotAct)

        self.prefAct = E5Action(
            self.tr('Preferences'),
            UI.PixmapCache.getIcon("configure.png"),
            self.tr('&Preferences...'),
            0, 0, self, 'preferences')
        self.prefAct.setStatusTip(self.tr(
            'Set the prefered configuration'))
        self.prefAct.setWhatsThis(self.tr(
            """<b>Preferences</b>"""
            """<p>Set the configuration items of the application"""
            """ with your prefered values.</p>"""
        ))
        self.prefAct.triggered.connect(self.showPreferences)
        self.prefAct.setMenuRole(QAction.PreferencesRole)
        self.actions.append(self.prefAct)

        self.prefExportAct = E5Action(
            self.tr('Export Preferences'),
            UI.PixmapCache.getIcon("configureExport.png"),
            self.tr('E&xport Preferences...'),
            0, 0, self, 'export_preferences')
        self.prefExportAct.setStatusTip(self.tr(
            'Export the current configuration'))
        self.prefExportAct.setWhatsThis(self.tr(
            """<b>Export Preferences</b>"""
            """<p>Export the current configuration to a file.</p>"""
        ))
        self.prefExportAct.triggered.connect(self.__exportPreferences)
        self.actions.append(self.prefExportAct)

        self.prefImportAct = E5Action(
            self.tr('Import Preferences'),
            UI.PixmapCache.getIcon("configureImport.png"),
            self.tr('I&mport Preferences...'),
            0, 0, self, 'import_preferences')
        self.prefImportAct.setStatusTip(self.tr(
            'Import a previously exported configuration'))
        self.prefImportAct.setWhatsThis(self.tr(
            """<b>Import Preferences</b>"""
            """<p>Import a previously exported configuration.</p>"""
        ))
        self.prefImportAct.triggered.connect(self.__importPreferences)
        self.actions.append(self.prefImportAct)

        self.reloadAPIsAct = E5Action(
            self.tr('Reload APIs'),
            self.tr('Reload &APIs'),
            0, 0, self, 'reload_apis')
        self.reloadAPIsAct.setStatusTip(self.tr(
            'Reload the API information'))
        self.reloadAPIsAct.setWhatsThis(self.tr(
            """<b>Reload APIs</b>"""
            """<p>Reload the API information.</p>"""
        ))
        self.reloadAPIsAct.triggered.connect(self.__reloadAPIs)
        self.actions.append(self.reloadAPIsAct)

        self.showExternalToolsAct = E5Action(
            self.tr('Show external tools'),
            UI.PixmapCache.getIcon("showPrograms.png"),
            self.tr('Show external &tools'),
            0, 0, self, 'show_external_tools')
        self.showExternalToolsAct.setStatusTip(self.tr(
            'Show external tools'))
        self.showExternalToolsAct.setWhatsThis(self.tr(
            """<b>Show external tools</b>"""
            """<p>Opens a dialog to show the path and versions of all"""
            """ extenal tools used by eric6.</p>"""
        ))
        self.showExternalToolsAct.triggered.connect(
            self.__showExternalTools)
        self.actions.append(self.showExternalToolsAct)

        self.configViewProfilesAct = E5Action(
            self.tr('View Profiles'),
            UI.PixmapCache.getIcon("configureViewProfiles.png"),
            self.tr('&View Profiles...'),
            0, 0, self, 'view_profiles')
        self.configViewProfilesAct.setStatusTip(self.tr(
            'Configure view profiles'))
        self.configViewProfilesAct.setWhatsThis(self.tr(
            """<b>View Profiles</b>"""
            """<p>Configure the view profiles. With this dialog you may"""
            """ set the visibility of the various windows for the"""
            """ predetermined view profiles.</p>"""
        ))
        self.configViewProfilesAct.triggered.connect(
            self.__configViewProfiles)
        self.actions.append(self.configViewProfilesAct)

        self.configToolBarsAct = E5Action(
            self.tr('Toolbars'),
            UI.PixmapCache.getIcon("toolbarsConfigure.png"),
            self.tr('Tool&bars...'),
            0, 0, self, 'configure_toolbars')
        self.configToolBarsAct.setStatusTip(self.tr('Configure toolbars'))
        self.configToolBarsAct.setWhatsThis(self.tr(
            """<b>Toolbars</b>"""
            """<p>Configure the toolbars. With this dialog you may"""
            """ change the actions shown on the various toolbars and"""
            """ define your own toolbars.</p>"""
        ))
        self.configToolBarsAct.triggered.connect(self.__configToolBars)
        self.actions.append(self.configToolBarsAct)

        self.shortcutsAct = E5Action(
            self.tr('Keyboard Shortcuts'),
            UI.PixmapCache.getIcon("configureShortcuts.png"),
            self.tr('Keyboard &Shortcuts...'),
            0, 0, self, 'keyboard_shortcuts')
        self.shortcutsAct.setStatusTip(self.tr(
            'Set the keyboard shortcuts'))
        self.shortcutsAct.setWhatsThis(self.tr(
            """<b>Keyboard Shortcuts</b>"""
            """<p>Set the keyboard shortcuts of the application"""
            """ with your prefered values.</p>"""
        ))
        self.shortcutsAct.triggered.connect(self.__configShortcuts)
        self.actions.append(self.shortcutsAct)

        self.exportShortcutsAct = E5Action(
            self.tr('Export Keyboard Shortcuts'),
            UI.PixmapCache.getIcon("exportShortcuts.png"),
            self.tr('&Export Keyboard Shortcuts...'),
            0, 0, self, 'export_keyboard_shortcuts')
        self.exportShortcutsAct.setStatusTip(self.tr(
            'Export the keyboard shortcuts'))
        self.exportShortcutsAct.setWhatsThis(self.tr(
            """<b>Export Keyboard Shortcuts</b>"""
            """<p>Export the keyboard shortcuts of the application.</p>"""
        ))
        self.exportShortcutsAct.triggered.connect(self.__exportShortcuts)
        self.actions.append(self.exportShortcutsAct)

        self.importShortcutsAct = E5Action(
            self.tr('Import Keyboard Shortcuts'),
            UI.PixmapCache.getIcon("importShortcuts.png"),
            self.tr('&Import Keyboard Shortcuts...'),
            0, 0, self, 'import_keyboard_shortcuts')
        self.importShortcutsAct.setStatusTip(self.tr(
            'Import the keyboard shortcuts'))
        self.importShortcutsAct.setWhatsThis(self.tr(
            """<b>Import Keyboard Shortcuts</b>"""
            """<p>Import the keyboard shortcuts of the application.</p>"""
        ))
        self.importShortcutsAct.triggered.connect(self.__importShortcuts)
        self.actions.append(self.importShortcutsAct)

        if SSL_AVAILABLE:
            self.certificatesAct = E5Action(
                self.tr('Manage SSL Certificates'),
                UI.PixmapCache.getIcon("certificates.png"),
                self.tr('Manage SSL Certificates...'),
                0, 0, self, 'manage_ssl_certificates')
            self.certificatesAct.setStatusTip(self.tr(
                'Manage the saved SSL certificates'))
            self.certificatesAct.setWhatsThis(self.tr(
                """<b>Manage SSL Certificates...</b>"""
                """<p>Opens a dialog to manage the saved SSL certificates."""
                """</p>"""
            ))
            self.certificatesAct.triggered.connect(
                self.__showCertificatesDialog)
            self.actions.append(self.certificatesAct)
        
        self.editMessageFilterAct = E5Action(
            self.tr('Edit Message Filters'),
            UI.PixmapCache.getIcon("warning.png"),
            self.tr('Edit Message Filters...'),
            0, 0, self, 'manage_message_filters')
        self.editMessageFilterAct.setStatusTip(self.tr(
            'Edit the message filters used to suppress unwanted messages'))
        self.editMessageFilterAct.setWhatsThis(self.tr(
            """<b>Edit Message Filters</b>"""
            """<p>Opens a dialog to edit the message filters used to"""
            """ suppress unwanted messages been shown in an error"""
            """ window.</p>"""
        ))
        self.editMessageFilterAct.triggered.connect(
            E5ErrorMessage.editMessageFilters)
        self.actions.append(self.editMessageFilterAct)

        self.viewmanagerActivateAct = E5Action(
            self.tr('Activate current editor'),
            self.tr('Activate current editor'),
            QKeySequence(self.tr("Alt+Shift+E")),
            0, self, 'viewmanager_activate', 1)
        self.viewmanagerActivateAct.triggered.connect(
            self.__activateViewmanager)
        self.actions.append(self.viewmanagerActivateAct)
        self.addAction(self.viewmanagerActivateAct)

        self.nextTabAct = E5Action(
            self.tr('Show next'),
            self.tr('Show next'),
            QKeySequence(self.tr('Ctrl+Alt+Tab')), 0,
            self, 'view_next_tab')
        self.nextTabAct.triggered.connect(self.__showNext)
        self.actions.append(self.nextTabAct)
        self.addAction(self.nextTabAct)
        
        self.prevTabAct = E5Action(
            self.tr('Show previous'),
            self.tr('Show previous'),
            QKeySequence(self.tr('Shift+Ctrl+Alt+Tab')), 0,
            self, 'view_previous_tab')
        self.prevTabAct.triggered.connect(self.__showPrevious)
        self.actions.append(self.prevTabAct)
        self.addAction(self.prevTabAct)
        
        self.switchTabAct = E5Action(
            self.tr('Switch between tabs'),
            self.tr('Switch between tabs'),
            QKeySequence(self.tr('Ctrl+1')), 0,
            self, 'switch_tabs')
        self.switchTabAct.triggered.connect(self.__switchTab)
        self.actions.append(self.switchTabAct)
        self.addAction(self.switchTabAct)
        
        self.pluginInfoAct = E5Action(
            self.tr('Plugin Infos'),
            UI.PixmapCache.getIcon("plugin.png"),
            self.tr('&Plugin Infos...'), 0, 0, self, 'plugin_infos')
        self.pluginInfoAct.setStatusTip(self.tr('Show Plugin Infos'))
        self.pluginInfoAct.setWhatsThis(self.tr(
            """<b>Plugin Infos...</b>"""
            """<p>This opens a dialog, that show some information about"""
            """ loaded plugins.</p>"""
        ))
        self.pluginInfoAct.triggered.connect(self.__showPluginInfo)
        self.actions.append(self.pluginInfoAct)
        
        self.pluginInstallAct = E5Action(
            self.tr('Install Plugins'),
            UI.PixmapCache.getIcon("pluginInstall.png"),
            self.tr('&Install Plugins...'),
            0, 0, self, 'plugin_install')
        self.pluginInstallAct.setStatusTip(self.tr('Install Plugins'))
        self.pluginInstallAct.setWhatsThis(self.tr(
            """<b>Install Plugins...</b>"""
            """<p>This opens a dialog to install or update plugins.</p>"""
        ))
        self.pluginInstallAct.triggered.connect(self.__installPlugins)
        self.actions.append(self.pluginInstallAct)
        
        self.pluginDeinstallAct = E5Action(
            self.tr('Uninstall Plugin'),
            UI.PixmapCache.getIcon("pluginUninstall.png"),
            self.tr('&Uninstall Plugin...'),
            0, 0, self, 'plugin_deinstall')
        self.pluginDeinstallAct.setStatusTip(self.tr('Uninstall Plugin'))
        self.pluginDeinstallAct.setWhatsThis(self.tr(
            """<b>Uninstall Plugin...</b>"""
            """<p>This opens a dialog to uninstall a plugin.</p>"""
        ))
        self.pluginDeinstallAct.triggered.connect(self.__deinstallPlugin)
        self.actions.append(self.pluginDeinstallAct)

        self.pluginRepoAct = E5Action(
            self.tr('Plugin Repository'),
            UI.PixmapCache.getIcon("pluginRepository.png"),
            self.tr('Plugin &Repository...'),
            0, 0, self, 'plugin_repository')
        self.pluginRepoAct.setStatusTip(self.tr(
            'Show Plugins available for download'))
        self.pluginRepoAct.setWhatsThis(self.tr(
            """<b>Plugin Repository...</b>"""
            """<p>This opens a dialog, that shows a list of plugins """
            """available on the Internet.</p>"""
        ))
        self.pluginRepoAct.triggered.connect(self.showPluginsAvailable)
        self.actions.append(self.pluginRepoAct)
        
        # initialize viewmanager actions
        self.viewmanager.initActions()
        
        # initialize debugger actions
        self.debuggerUI.initActions()
        
        # initialize project actions
        self.project.initActions()
        
        # initialize multi project actions
        self.multiProject.initActions()
    
    def __initQtDocActions(self):
        """
        Private slot to initialize the action to show the Qt documentation.
        """
        self.qt4DocAct = E5Action(
            self.tr('Qt4 Documentation'),
            self.tr('Qt&4 Documentation'),
            0, 0, self, 'qt4_documentation')
        self.qt4DocAct.setStatusTip(self.tr('Open Qt4 Documentation'))
        self.qt4DocAct.setWhatsThis(self.tr(
            """<b>Qt4 Documentation</b>"""
            """<p>Display the Qt4 Documentation. Dependent upon your"""
            """ settings, this will either show the help in Eric's internal"""
            """ help viewer, or execute a web browser or Qt Assistant. </p>"""
        ))
        self.qt4DocAct.triggered.connect(self.__showQt4Doc)
        self.actions.append(self.qt4DocAct)
      
        self.qt5DocAct = E5Action(
            self.tr('Qt5 Documentation'),
            self.tr('Qt&5 Documentation'),
            0, 0, self, 'qt5_documentation')
        self.qt5DocAct.setStatusTip(self.tr('Open Qt5 Documentation'))
        self.qt5DocAct.setWhatsThis(self.tr(
            """<b>Qt5 Documentation</b>"""
            """<p>Display the Qt5 Documentation. Dependent upon your"""
            """ settings, this will either show the help in Eric's internal"""
            """ help viewer, or execute a web browser or Qt Assistant. </p>"""
        ))
        self.qt5DocAct.triggered.connect(self.__showQt5Doc)
        self.actions.append(self.qt5DocAct)
      
        try:
            import PyQt4        # __IGNORE_WARNING__
            self.pyqt4DocAct = E5Action(
                self.tr('PyQt4 Documentation'),
                self.tr('PyQt&4 Documentation'),
                0, 0, self, 'pyqt4_documentation')
            self.pyqt4DocAct.setStatusTip(self.tr('Open PyQt4 Documentation'))
            self.pyqt4DocAct.setWhatsThis(self.tr(
                """<b>PyQt4 Documentation</b>"""
                """<p>Display the PyQt4 Documentation. Dependent upon your"""
                """ settings, this will either show the help in Eric's"""
                """ internal help viewer, or execute a web browser or"""
                """ Qt Assistant. </p>"""
            ))
            self.pyqt4DocAct.triggered.connect(self.__showPyQt4Doc)
            self.actions.append(self.pyqt4DocAct)
        except ImportError:
            self.pyqt4DocAct = None
        
        try:
            import PyQt5        # __IGNORE_WARNING__
            self.pyqt5DocAct = E5Action(
                self.tr('PyQt5 Documentation'),
                self.tr('PyQt&5 Documentation'),
                0, 0, self, 'pyqt5_documentation')
            self.pyqt5DocAct.setStatusTip(self.tr(
                'Open PyQt5 Documentation'))
            self.pyqt5DocAct.setWhatsThis(self.tr(
                """<b>PyQt5 Documentation</b>"""
                """<p>Display the PyQt5 Documentation. Dependent upon your"""
                """ settings, this will either show the help in Eric's"""
                """ internal help viewer, or execute a web browser or"""
                """ Qt Assistant. </p>"""
            ))
            self.pyqt5DocAct.triggered.connect(self.__showPyQt5Doc)
            self.actions.append(self.pyqt5DocAct)
        except ImportError:
            self.pyqt5DocAct = None
        
    def __initPythonDocActions(self):
        """
        Private slot to initialize the actions to show the Python
        documentation.
        """
        self.pythonDocAct = E5Action(
            self.tr('Python 3 Documentation'),
            self.tr('Python &3 Documentation'),
            0, 0, self, 'python3_documentation')
        self.pythonDocAct.setStatusTip(self.tr(
            'Open Python 3 Documentation'))
        self.pythonDocAct.setWhatsThis(self.tr(
            """<b>Python 3 Documentation</b>"""
            """<p>Display the Python 3 documentation. If no documentation"""
            """ directory is configured, the location of the Python 3"""
            """ documentation is assumed to be the doc directory underneath"""
            """ the location of the Python 3 executable on Windows and"""
            """ <i>/usr/share/doc/packages/python/html</i> on Unix. Set"""
            """ PYTHON3DOCDIR in your environment to override this.</p>"""
        ))
        self.pythonDocAct.triggered.connect(self.__showPythonDoc)
        self.actions.append(self.pythonDocAct)
        
        self.python2DocAct = E5Action(
            self.tr('Python 2 Documentation'),
            self.tr('Python &2 Documentation'),
            0, 0, self, 'python2_documentation')
        self.python2DocAct.setStatusTip(self.tr(
            'Open Python 2 Documentation'))
        self.python2DocAct.setWhatsThis(self.tr(
            """<b>Python 2 Documentation</b>"""
            """<p>Display the Python 2 documentation. If no documentation"""
            """ directory is configured, the location of the Python 2"""
            """ documentation is assumed to be the doc directory underneath"""
            """ the location of the configured Python 2 executable on"""
            """ Windows and"""
            """ <i>/usr/share/doc/packages/python/html/python-docs-html</i>"""
            """ on Unix. Set PYTHON2DOCDIR in your environment to override"""
            """ this. </p>"""
        ))
        self.python2DocAct.triggered.connect(self.__showPython2Doc)
        self.actions.append(self.python2DocAct)
        
    def __initEricDocAction(self):
        """
        Private slot to initialize the action to show the eric6 documentation.
        """
        self.ericDocAct = E5Action(
            self.tr("Eric API Documentation"),
            self.tr('&Eric API Documentation'),
            0, 0, self, 'eric_documentation')
        self.ericDocAct.setStatusTip(self.tr(
            "Open Eric API Documentation"))
        self.ericDocAct.setWhatsThis(self.tr(
            """<b>Eric API Documentation</b>"""
            """<p>Display the Eric API documentation. The location for the"""
            """ documentation is the Documentation/Source subdirectory of"""
            """ the eric6 installation directory.</p>"""
        ))
        self.ericDocAct.triggered.connect(self.__showEricDoc)
        self.actions.append(self.ericDocAct)
        
    def __initPySideDocAction(self):
        """
        Private slot to initialize the action to show the PySide documentation.
        """
        pyside2, pyside3 = Utilities.checkPyside()
        if pyside2 or pyside3:
            self.pysideDocAct = E5Action(
                self.tr('PySide Documentation'),
                self.tr('Py&Side Documentation'),
                0, 0, self, 'pyside_documentation')
            self.pysideDocAct.setStatusTip(self.tr(
                'Open PySide Documentation'))
            self.pysideDocAct.setWhatsThis(self.tr(
                """<b>PySide Documentation</b>"""
                """<p>Display the PySide Documentation. Dependent upon your"""
                """ settings, this will either show the help in Eric's"""
                """ internal help viewer, or execute a web browser or"""
                """ Qt Assistant. </p>"""
            ))
            self.pysideDocAct.triggered.connect(self.__showPySideDoc)
            self.actions.append(self.pysideDocAct)
        else:
            self.pysideDocAct = None
      
    def __initMenus(self):
        """
        Private slot to create the menus.
        """
        self.__menus = {}
        mb = self.menuBar()
        
        self.__menus["file"] = self.viewmanager.initFileMenu()
        mb.addMenu(self.__menus["file"])
        self.__menus["file"].addSeparator()
        self.__menus["file"].addAction(self.exitAct)
        act = self.__menus["file"].actions()[0]
        sep = self.__menus["file"].insertSeparator(act)
        self.__menus["file"].insertAction(sep, self.newWindowAct)
        self.__menus["file"].aboutToShow.connect(self.__showFileMenu)
        
        self.__menus["edit"] = self.viewmanager.initEditMenu()
        mb.addMenu(self.__menus["edit"])
        
        self.__menus["view"] = self.viewmanager.initViewMenu()
        mb.addMenu(self.__menus["view"])
        
        self.__menus["start"], self.__menus["debug"] = \
            self.debuggerUI.initMenus()
        mb.addMenu(self.__menus["start"])
        mb.addMenu(self.__menus["debug"])
        
        self.__menus["unittest"] = QMenu(self.tr('&Unittest'), self)
        self.__menus["unittest"].setTearOffEnabled(True)
        mb.addMenu(self.__menus["unittest"])
        self.__menus["unittest"].addAction(self.utDialogAct)
        self.__menus["unittest"].addSeparator()
        self.__menus["unittest"].addAction(self.utRestartAct)
        self.__menus["unittest"].addAction(self.utRerunFailedAct)
        self.__menus["unittest"].addSeparator()
        self.__menus["unittest"].addAction(self.utScriptAct)
        self.__menus["unittest"].addAction(self.utProjectAct)
        
        self.__menus["multiproject"] = self.multiProject.initMenu()
        mb.addMenu(self.__menus["multiproject"])
        
        self.__menus["project"] = self.project.initMenu()
        mb.addMenu(self.__menus["project"])
        
        self.__menus["extras"] = QMenu(self.tr('E&xtras'), self)
        self.__menus["extras"].setTearOffEnabled(True)
        self.__menus["extras"].aboutToShow.connect(self.__showExtrasMenu)
        mb.addMenu(self.__menus["extras"])
        self.viewmanager.addToExtrasMenu(self.__menus["extras"])
        self.__menus["wizards"] = QMenu(self.tr('Wi&zards'), self)
        self.__menus["wizards"].setTearOffEnabled(True)
        self.__menus["wizards"].aboutToShow.connect(self.__showWizardsMenu)
        self.wizardsMenuAct = self.__menus["extras"].addMenu(
            self.__menus["wizards"])
        self.wizardsMenuAct.setEnabled(False)
        self.__menus["macros"] = self.viewmanager.initMacroMenu()
        self.__menus["extras"].addMenu(self.__menus["macros"])
        self.toolGroupsMenu = QMenu(self.tr("Select Tool Group"), self)
        self.toolGroupsMenu.aboutToShow.connect(self.__showToolGroupsMenu)
        self.toolGroupsMenu.triggered.connect(self.__toolGroupSelected)
        self.toolGroupsMenuTriggered = False
        self.__menus["extras"].addSeparator()
        self.__initToolsMenus(self.__menus["extras"])
        self.__menus["extras"].addSeparator()
        
        self.__menus["settings"] = QMenu(self.tr('Se&ttings'), self)
        mb.addMenu(self.__menus["settings"])
        self.__menus["settings"].setTearOffEnabled(True)
        self.__menus["settings"].addAction(self.prefAct)
        self.__menus["settings"].addAction(self.prefExportAct)
        self.__menus["settings"].addAction(self.prefImportAct)
        self.__menus["settings"].addSeparator()
        self.__menus["settings"].addAction(self.reloadAPIsAct)
        self.__menus["settings"].addSeparator()
        self.__menus["settings"].addAction(self.configViewProfilesAct)
        self.__menus["settings"].addAction(self.configToolBarsAct)
        self.__menus["settings"].addSeparator()
        self.__menus["settings"].addAction(self.shortcutsAct)
        self.__menus["settings"].addAction(self.exportShortcutsAct)
        self.__menus["settings"].addAction(self.importShortcutsAct)
        self.__menus["settings"].addSeparator()
        self.__menus["settings"].addAction(self.showExternalToolsAct)
        if SSL_AVAILABLE:
            self.__menus["settings"].addSeparator()
            self.__menus["settings"].addAction(self.certificatesAct)
        self.__menus["settings"].addSeparator()
        self.__menus["settings"].addAction(self.editMessageFilterAct)
        
        self.__menus["window"] = QMenu(self.tr('&Window'), self)
        mb.addMenu(self.__menus["window"])
        self.__menus["window"].setTearOffEnabled(True)
        self.__menus["window"].aboutToShow.connect(self.__showWindowMenu)
        
        self.__menus["subwindow"] = QMenu(self.tr("&Windows"),
                                          self.__menus["window"])
        self.__menus["subwindow"].setTearOffEnabled(True)
        # left side
        self.__menus["subwindow"].addAction(self.pbActivateAct)
        self.__menus["subwindow"].addAction(self.mpbActivateAct)
        self.__menus["subwindow"].addAction(self.templateViewerActivateAct)
        self.__menus["subwindow"].addAction(self.browserActivateAct)
        self.__menus["subwindow"].addAction(self.symbolsViewerActivateAct)
        # bottom side
        self.__menus["subwindow"].addAction(self.shellActivateAct)
        self.__menus["subwindow"].addAction(self.taskViewerActivateAct)
        self.__menus["subwindow"].addAction(self.logViewerActivateAct)
        self.__menus["subwindow"].addAction(self.numbersViewerActivateAct)
        # right side
        self.__menus["subwindow"].addAction(self.debugViewerActivateAct)
        self.__menus["subwindow"].addAction(self.cooperationViewerActivateAct)
        self.__menus["subwindow"].addAction(self.ircActivateAct)
        
        self.__menus["toolbars"] = \
            QMenu(self.tr("&Toolbars"), self.__menus["window"])
        self.__menus["toolbars"].setTearOffEnabled(True)
        self.__menus["toolbars"].aboutToShow.connect(self.__showToolbarsMenu)
        self.__menus["toolbars"].triggered.connect(self.__TBMenuTriggered)
        
        self.__showWindowMenu()  # to initialize these actions

        self.__menus["bookmarks"] = self.viewmanager.initBookmarkMenu()
        mb.addMenu(self.__menus["bookmarks"])
        self.__menus["bookmarks"].setTearOffEnabled(True)

        self.__menus["plugins"] = QMenu(self.tr('P&lugins'), self)
        mb.addMenu(self.__menus["plugins"])
        self.__menus["plugins"].setTearOffEnabled(True)
        self.__menus["plugins"].addAction(self.pluginInfoAct)
        self.__menus["plugins"].addAction(self.pluginInstallAct)
        self.__menus["plugins"].addAction(self.pluginDeinstallAct)
        self.__menus["plugins"].addSeparator()
        self.__menus["plugins"].addAction(self.pluginRepoAct)
        self.__menus["plugins"].addSeparator()
        self.__menus["plugins"].addAction(
            self.tr("Configure..."), self.__pluginsConfigure)

        mb.addSeparator()

        self.__menus["help"] = QMenu(self.tr('&Help'), self)
        mb.addMenu(self.__menus["help"])
        self.__menus["help"].setTearOffEnabled(True)
        self.__menus["help"].addAction(self.helpviewerAct)
        self.__menus["help"].addSeparator()
        self.__menus["help"].addAction(self.ericDocAct)
        self.__menus["help"].addAction(self.pythonDocAct)
        self.__menus["help"].addAction(self.python2DocAct)
        self.__menus["help"].addAction(self.qt4DocAct)
        self.__menus["help"].addAction(self.qt5DocAct)
        if self.pyqt4DocAct is not None:
            self.__menus["help"].addAction(self.pyqt4DocAct)
        if self.pyqt5DocAct is not None:
            self.__menus["help"].addAction(self.pyqt5DocAct)
        if self.pysideDocAct is not None:
            self.__menus["help"].addAction(self.pysideDocAct)
        self.__menus["help"].addSeparator()
        self.__menus["help"].addAction(self.versionAct)
        self.__menus["help"].addSeparator()
        self.__menus["help"].addAction(self.checkUpdateAct)
        self.__menus["help"].addAction(self.showVersionsAct)
        self.__menus["help"].addSeparator()
        self.__menus["help"].addAction(self.showErrorLogAct)
        self.__menus["help"].addAction(self.reportBugAct)
        self.__menus["help"].addAction(self.requestFeatureAct)
        self.__menus["help"].addSeparator()
        self.__menus["help"].addAction(self.whatsThisAct)
        self.__menus["help"].aboutToShow.connect(self.__showHelpMenu)
    
    def getToolBarIconSize(self):
        """
        Public method to get the toolbar icon size.
        
        @return toolbar icon size (QSize)
        """
        return Config.ToolBarIconSize
    
    def __initToolbars(self):
        """
        Private slot to create the toolbars.
        """
        filetb = self.viewmanager.initFileToolbar(self.toolbarManager)
        edittb = self.viewmanager.initEditToolbar(self.toolbarManager)
        searchtb, quicksearchtb = self.viewmanager.initSearchToolbars(
            self.toolbarManager)
        viewtb = self.viewmanager.initViewToolbar(self.toolbarManager)
        starttb, debugtb = self.debuggerUI.initToolbars(self.toolbarManager)
        multiprojecttb = self.multiProject.initToolbar(self.toolbarManager)
        projecttb, vcstb = self.project.initToolbars(self.toolbarManager)
        toolstb = QToolBar(self.tr("Tools"), self)
        unittesttb = QToolBar(self.tr("Unittest"), self)
        bookmarktb = self.viewmanager.initBookmarkToolbar(self.toolbarManager)
        spellingtb = self.viewmanager.initSpellingToolbar(self.toolbarManager)
        settingstb = QToolBar(self.tr("Settings"), self)
        helptb = QToolBar(self.tr("Help"), self)
        profilestb = QToolBar(self.tr("Profiles"), self)
        pluginstb = QToolBar(self.tr("Plugins"), self)
        
        toolstb.setIconSize(Config.ToolBarIconSize)
        unittesttb.setIconSize(Config.ToolBarIconSize)
        settingstb.setIconSize(Config.ToolBarIconSize)
        helptb.setIconSize(Config.ToolBarIconSize)
        profilestb.setIconSize(Config.ToolBarIconSize)
        pluginstb.setIconSize(Config.ToolBarIconSize)
        
        toolstb.setObjectName("ToolsToolbar")
        unittesttb.setObjectName("UnittestToolbar")
        settingstb.setObjectName("SettingsToolbar")
        helptb.setObjectName("HelpToolbar")
        profilestb.setObjectName("ProfilesToolbar")
        pluginstb.setObjectName("PluginsToolbar")
        
        toolstb.setToolTip(self.tr("Tools"))
        unittesttb.setToolTip(self.tr("Unittest"))
        settingstb.setToolTip(self.tr("Settings"))
        helptb.setToolTip(self.tr("Help"))
        profilestb.setToolTip(self.tr("Profiles"))
        pluginstb.setToolTip(self.tr("Plugins"))
        
        filetb.addSeparator()
        filetb.addAction(self.exitAct)
        act = filetb.actions()[0]
        sep = filetb.insertSeparator(act)
        filetb.insertAction(sep, self.newWindowAct)
        self.toolbarManager.addToolBar(filetb, filetb.windowTitle())
        
        # setup the unittest toolbar
        unittesttb.addAction(self.utDialogAct)
        unittesttb.addSeparator()
        unittesttb.addAction(self.utRestartAct)
        unittesttb.addAction(self.utRerunFailedAct)
        unittesttb.addSeparator()
        unittesttb.addAction(self.utScriptAct)
        unittesttb.addAction(self.utProjectAct)
        self.toolbarManager.addToolBar(unittesttb, unittesttb.windowTitle())
        
        # setup the tools toolbar
        if self.designer4Act is not None:
            toolstb.addAction(self.designer4Act)
        if self.linguist4Act is not None:
            toolstb.addAction(self.linguist4Act)
        toolstb.addAction(self.uipreviewerAct)
        toolstb.addAction(self.trpreviewerAct)
        toolstb.addSeparator()
        toolstb.addAction(self.diffAct)
        toolstb.addAction(self.compareAct)
        toolstb.addSeparator()
        toolstb.addAction(self.sqlBrowserAct)
        toolstb.addSeparator()
        toolstb.addAction(self.miniEditorAct)
        toolstb.addAction(self.iconEditorAct)
        toolstb.addAction(self.snapshotAct)
        toolstb.addSeparator()
        toolstb.addAction(self.webBrowserAct)
        self.toolbarManager.addToolBar(toolstb, toolstb.windowTitle())
        
        # setup the settings toolbar
        settingstb.addAction(self.prefAct)
        settingstb.addAction(self.configViewProfilesAct)
        settingstb.addAction(self.configToolBarsAct)
        settingstb.addAction(self.shortcutsAct)
        settingstb.addAction(self.showExternalToolsAct)
        self.toolbarManager.addToolBar(settingstb, settingstb.windowTitle())
        self.toolbarManager.addAction(
            self.exportShortcutsAct, settingstb.windowTitle())
        self.toolbarManager.addAction(
            self.importShortcutsAct, settingstb.windowTitle())
        
        # setup the help toolbar
        helptb.addAction(self.whatsThisAct)
        self.toolbarManager.addToolBar(helptb, helptb.windowTitle())
        self.toolbarManager.addAction(self.helpviewerAct, helptb.windowTitle())
        
        # setup the view profiles toolbar
        profilestb.addActions(self.viewProfileActGrp.actions())
        self.toolbarManager.addToolBar(profilestb, profilestb.windowTitle())
        
        # setup the plugins toolbar
        pluginstb.addAction(self.pluginInfoAct)
        pluginstb.addAction(self.pluginInstallAct)
        pluginstb.addAction(self.pluginDeinstallAct)
        pluginstb.addSeparator()
        pluginstb.addAction(self.pluginRepoAct)
        self.toolbarManager.addToolBar(pluginstb, pluginstb.windowTitle())
        
        # add the various toolbars
        self.addToolBar(filetb)
        self.addToolBar(edittb)
        self.addToolBar(searchtb)
        self.addToolBar(quicksearchtb)
        self.addToolBar(viewtb)
        self.addToolBar(starttb)
        self.addToolBar(debugtb)
        self.addToolBar(multiprojecttb)
        self.addToolBar(projecttb)
        self.addToolBar(vcstb)
        self.addToolBar(Qt.RightToolBarArea, settingstb)
        self.addToolBar(Qt.RightToolBarArea, toolstb)
        self.addToolBar(helptb)
        self.addToolBar(bookmarktb)
        self.addToolBar(spellingtb)
        self.addToolBar(unittesttb)
        self.addToolBar(profilestb)
        self.addToolBar(pluginstb)
        
        # hide toolbars not wanted in the initial layout
        searchtb.hide()
        quicksearchtb.hide()
        viewtb.hide()
        debugtb.hide()
        multiprojecttb.hide()
        helptb.hide()
        spellingtb.hide()
        unittesttb.hide()
        pluginstb.hide()

        # just add new toolbars to the end of the list
        self.__toolbars = {}
        self.__toolbars["file"] = [filetb.windowTitle(), filetb]
        self.__toolbars["edit"] = [edittb.windowTitle(), edittb]
        self.__toolbars["search"] = [searchtb.windowTitle(), searchtb]
        self.__toolbars["view"] = [viewtb.windowTitle(), viewtb]
        self.__toolbars["start"] = [starttb.windowTitle(), starttb]
        self.__toolbars["debug"] = [debugtb.windowTitle(), debugtb]
        self.__toolbars["project"] = [projecttb.windowTitle(), projecttb]
        self.__toolbars["tools"] = [toolstb.windowTitle(), toolstb]
        self.__toolbars["help"] = [helptb.windowTitle(), helptb]
        self.__toolbars["settings"] = [settingstb.windowTitle(), settingstb]
        self.__toolbars["bookmarks"] = [bookmarktb.windowTitle(), bookmarktb]
        self.__toolbars["unittest"] = [unittesttb.windowTitle(), unittesttb]
        self.__toolbars["view_profiles"] = [profilestb.windowTitle(),
                                            profilestb]
        self.__toolbars["plugins"] = [pluginstb.windowTitle(), pluginstb]
        self.__toolbars["quicksearch"] = [quicksearchtb.windowTitle(),
                                          quicksearchtb]
        self.__toolbars["multiproject"] = [multiprojecttb.windowTitle(),
                                           multiprojecttb]
        self.__toolbars["spelling"] = [spellingtb.windowTitle(), spellingtb]
        self.__toolbars["vcs"] = [vcstb.windowTitle(), vcstb]
        
    def __initDebugToolbarsLayout(self):
        """
        Private slot to initialize the toolbars layout for the debug profile.
        """
        # Step 1: set the edit profile to be sure
        self.__setEditProfile()
        
        # Step 2: switch to debug profile and do the layout
        initSize = self.size()
        self.setDebugProfile()
        self.__toolbars["project"][1].hide()
        self.__toolbars["debug"][1].show()
        self.resize(initSize)
        
        # Step 3: switch back to edit profile
        self.__setEditProfile()
        
    def __initStatusbar(self):
        """
        Private slot to set up the status bar.
        """
        self.__statusBar = self.statusBar()
        self.__statusBar.setSizeGripEnabled(True)

        self.sbLanguage = E5ClickableLabel(self.__statusBar)
        self.__statusBar.addPermanentWidget(self.sbLanguage)
        self.sbLanguage.setWhatsThis(self.tr(
            """<p>This part of the status bar displays the"""
            """ current editors language.</p>"""
        ))

        self.sbEncoding = E5ClickableLabel(self.__statusBar)
        self.__statusBar.addPermanentWidget(self.sbEncoding)
        self.sbEncoding.setWhatsThis(self.tr(
            """<p>This part of the status bar displays the"""
            """ current editors encoding.</p>"""
        ))

        self.sbEol = E5ClickableLabel(self.__statusBar)
        self.__statusBar.addPermanentWidget(self.sbEol)
        self.sbEol.setWhatsThis(self.tr(
            """<p>This part of the status bar displays the"""
            """ current editors eol setting.</p>"""
        ))

        self.sbWritable = QLabel(self.__statusBar)
        self.__statusBar.addPermanentWidget(self.sbWritable)
        self.sbWritable.setWhatsThis(self.tr(
            """<p>This part of the status bar displays an indication of the"""
            """ current editors files writability.</p>"""
        ))

        self.sbLine = QLabel(self.__statusBar)
        self.__statusBar.addPermanentWidget(self.sbLine)
        self.sbLine.setWhatsThis(self.tr(
            """<p>This part of the status bar displays the line number of"""
            """ the current editor.</p>"""
        ))

        self.sbPos = QLabel(self.__statusBar)
        self.__statusBar.addPermanentWidget(self.sbPos)
        self.sbPos.setWhatsThis(self.tr(
            """<p>This part of the status bar displays the cursor position"""
            """ of the current editor.</p>"""
        ))
        
        self.sbZoom = E5ZoomWidget(
            UI.PixmapCache.getPixmap("zoomOut.png"),
            UI.PixmapCache.getPixmap("zoomIn.png"),
            UI.PixmapCache.getPixmap("zoomReset.png"),
            self.__statusBar)
        self.__statusBar.addPermanentWidget(self.sbZoom)
        self.sbZoom.setWhatsThis(self.tr(
            """<p>This part of the status bar allows zooming the current"""
            """ editor, shell or terminal.</p>"""
        ))
        
        self.viewmanager.setSbInfo(
            self.sbLine, self.sbPos, self.sbWritable, self.sbEncoding,
            self.sbLanguage, self.sbEol, self.sbZoom)

        from VCS.StatusMonitorLed import StatusMonitorLed
        self.sbVcsMonitorLed = StatusMonitorLed(self.project, self.__statusBar)
        self.__statusBar.addPermanentWidget(self.sbVcsMonitorLed)
    
    def __initExternalToolsActions(self):
        """
        Private slot to create actions for the configured external tools.
        """
        self.toolGroupActions = {}
        for toolGroup in self.toolGroups:
            category = self.tr("External Tools/{0}").format(toolGroup[0])
            for tool in toolGroup[1]:
                if tool['menutext'] != '--':
                    act = QAction(UI.PixmapCache.getIcon(tool['icon']),
                                  tool['menutext'], self)
                    act.setObjectName("{0}@@{1}".format(toolGroup[0],
                                      tool['menutext']))
                    act.triggered.connect(self.__toolActionTriggered)
                    self.toolGroupActions[act.objectName()] = act
                    
                    self.toolbarManager.addAction(act, category)
    
    def __updateExternalToolsActions(self):
        """
        Private method to update the external tools actions for the current
        tool group.
        """
        toolGroup = self.toolGroups[self.currentToolGroup]
        groupkey = "{0}@@".format(toolGroup[0])
        groupActionKeys = []
        # step 1: get actions for this group
        for key in self.toolGroupActions:
            if key.startswith(groupkey):
                groupActionKeys.append(key)
        
        # step 2: build keys for all actions i.a.w. current configuration
        ckeys = []
        for tool in toolGroup[1]:
            if tool['menutext'] != '--':
                ckeys.append("{0}@@{1}".format(toolGroup[0], tool['menutext']))
        
        # step 3: remove all actions not configured any more
        for key in groupActionKeys:
            if key not in ckeys:
                self.toolbarManager.removeAction(self.toolGroupActions[key])
                self.toolGroupActions[key].triggered.disconnect(
                    self.__toolActionTriggered)
                del self.toolGroupActions[key]
        
        # step 4: add all newly configured tools
        category = self.tr("External Tools/{0}").format(toolGroup[0])
        for tool in toolGroup[1]:
            if tool['menutext'] != '--':
                key = "{0}@@{1}".format(toolGroup[0], tool['menutext'])
                if key not in groupActionKeys:
                    act = QAction(UI.PixmapCache.getIcon(tool['icon']),
                                  tool['menutext'], self)
                    act.setObjectName(key)
                    act.triggered.connect(self.__toolActionTriggered)
                    self.toolGroupActions[key] = act
                    
                    self.toolbarManager.addAction(act, category)
    
    def __showFileMenu(self):
        """
        Private slot to display the File menu.
        """
        self.showMenu.emit("File", self.__menus["file"])
    
    def __showExtrasMenu(self):
        """
        Private slot to display the Extras menu.
        """
        self.showMenu.emit("Extras", self.__menus["extras"])
    
    def __showWizardsMenu(self):
        """
        Private slot to display the Wizards menu.
        """
        self.showMenu.emit("Wizards", self.__menus["wizards"])
    
    def __showHelpMenu(self):
        """
        Private slot to display the Help menu.
        """
        self.checkUpdateAct.setEnabled(not self.__inVersionCheck)
        self.showVersionsAct.setEnabled(not self.__inVersionCheck)
        self.showErrorLogAct.setEnabled(self.__hasErrorLog())
        
        self.showMenu.emit("Help", self.__menus["help"])
    
    def __showSettingsMenu(self):
        """
        Private slot to show the Settings menu.
        """
        self.editMessageFilterAct.setEnabled(
            E5ErrorMessage.messageHandlerInstalled())
        
        self.showMenu.emit("Settings", self.__menus["settings"])
    
    def __showNext(self):
        """
        Private slot used to show the next tab or file.
        """
        fwidget = QApplication.focusWidget()
        while fwidget and not hasattr(fwidget, 'nextTab'):
            fwidget = fwidget.parent()
        if fwidget:
            fwidget.nextTab()

    def __showPrevious(self):
        """
        Private slot used to show the previous tab or file.
        """
        fwidget = QApplication.focusWidget()
        while fwidget and not hasattr(fwidget, 'prevTab'):
            fwidget = fwidget.parent()
        if fwidget:
            fwidget.prevTab()
    
    def __switchTab(self):
        """
        Private slot used to switch between the current and the previous
        current tab.
        """
        fwidget = QApplication.focusWidget()
        while fwidget and not hasattr(fwidget, 'switchTab'):
            fwidget = fwidget.parent()
        if fwidget:
            fwidget.switchTab()
    
    def __whatsThis(self):
        """
        Private slot called in to enter Whats This mode.
        """
        QWhatsThis.enterWhatsThisMode()
        
    def __showVersions(self):
        """
        Private slot to handle the Versions dialog.
        """
        try:
            import sipconfig
            sip_version_str = sipconfig.Configuration().sip_version_str
        except ImportError:
            sip_version_str = "sip version not available"
        
        versionText = self.tr(
            """<h3>Version Numbers</h3>"""
            """<table>""")
        versionText += """<tr><td><b>Python</b></td><td>{0}</td></tr>"""\
            .format(sys.version.split()[0])
        versionText += """<tr><td><b>Qt</b></td><td>{0}</td></tr>"""\
            .format(qVersion())
        versionText += """<tr><td><b>PyQt</b></td><td>{0}</td></tr>"""\
            .format(PYQT_VERSION_STR)
        versionText += """<tr><td><b>sip</b></td><td>{0}</td></tr>"""\
            .format(sip_version_str)
        versionText += """<tr><td><b>QScintilla</b></td><td>{0}</td></tr>"""\
            .format(QSCINTILLA_VERSION_STR)
        try:
            from PyQt5.QtWebKit import qWebKitVersion
            versionText += """<tr><td><b>WebKit</b></td><td>{0}</td></tr>"""\
                .format(qWebKitVersion())
        except ImportError:
            pass
        versionText += """<tr><td><b>{0}</b></td><td>{1}</td></tr>"""\
            .format(Program, Version)
        versionText += self.tr("""</table>""")
        
        E5MessageBox.about(self, Program, versionText)
        
    def __reportBug(self):
        """
        Private slot to handle the Report Bug dialog.
        """
        self.showEmailDialog("bug")
        
    def __requestFeature(self):
        """
        Private slot to handle the Feature Request dialog.
        """
        self.showEmailDialog("feature")
        
    def showEmailDialog(self, mode, attachFile=None, deleteAttachFile=False):
        """
        Public slot to show the email dialog in a given mode.
        
        @param mode mode of the email dialog (string, "bug" or "feature")
        @param attachFile name of a file to attach to the email (string)
        @param deleteAttachFile flag indicating to delete the attached file
            after it has been sent (boolean)
        """
        if Preferences.getUser("UseSystemEmailClient"):
            self.__showSystemEmailClient(mode, attachFile, deleteAttachFile)
        else:
            if Preferences.getUser("Email") == "" or \
               Preferences.getUser("MailServer") == "":
                E5MessageBox.critical(
                    self,
                    self.tr("Report Bug"),
                    self.tr(
                        """Email address or mail server address is empty."""
                        """ Please configure your Email settings in the"""
                        """ Preferences Dialog."""))
                self.showPreferences("emailPage")
                return
                
            from .EmailDialog import EmailDialog
            self.dlg = EmailDialog(mode=mode)
            if attachFile is not None:
                self.dlg.attachFile(attachFile, deleteAttachFile)
            self.dlg.show()
        
    def __showSystemEmailClient(self, mode, attachFile=None,
                                deleteAttachFile=False):
        """
        Private slot to show the system email dialog.
        
        @param mode mode of the email dialog (string, "bug" or "feature")
        @param attachFile name of a file to put into the body of the
            email (string)
        @param deleteAttachFile flag indicating to delete the file after
            it has been read (boolean)
        """
        if mode == "feature":
            address = FeatureAddress
        else:
            address = BugAddress
        subject = "[eric6] "
        if attachFile is not None:
            f = open(attachFile, "r", encoding="utf-8")
            body = f.read()
            f.close()
            if deleteAttachFile:
                os.remove(attachFile)
        else:
            body = "\r\n----\r\n{0}----\r\n{1}----\r\n{2}".format(
                Utilities.generateVersionInfo("\r\n"),
                Utilities.generatePluginsVersionInfo("\r\n"),
                Utilities.generateDistroInfo("\r\n"))
        
        url = QUrl("mailto:{0}".format(address))
        if qVersion() >= "5.0.0":
            from PyQt5.QtCore import QUrlQuery
            urlQuery = QUrlQuery(url)
            urlQuery.addQueryItem("subject", subject)
            urlQuery.addQueryItem("body", body)
            url.setQuery(urlQuery)
        else:
            url.addQueryItem("subject", subject)
            url.addQueryItem("body", body)
        QDesktopServices.openUrl(url)
        
    def checkForErrorLog(self):
        """
        Public method to check for the presence of an error log and ask the
        user, what to do with it.
        """
        if Preferences.getUI("CheckErrorLog"):
            logFile = os.path.join(Utilities.getConfigDir(),
                                   self.ErrorLogFileName)
            if os.path.exists(logFile):
                from .ErrorLogDialog import ErrorLogDialog
                dlg = ErrorLogDialog(logFile, False, self)
                dlg.exec_()
        
    def __hasErrorLog(self):
        """
        Private method to check, if an error log file exists.
        
        @return flag indicating the existence of an error log file (boolean)
        """
        logFile = os.path.join(Utilities.getConfigDir(),
                               self.ErrorLogFileName)
        return os.path.exists(logFile)
        
    def __showErrorLog(self):
        """
        Private slot to show the most recent error log message.
        """
        logFile = os.path.join(Utilities.getConfigDir(),
                               self.ErrorLogFileName)
        if os.path.exists(logFile):
            from .ErrorLogDialog import ErrorLogDialog
            dlg = ErrorLogDialog(logFile, True, self)
            dlg.show()
        
    def __compareFiles(self):
        """
        Private slot to handle the Compare Files dialog.
        """
        aw = self.viewmanager.activeWindow()
        fn = aw and aw.getFileName() or None
        if self.diffDlg is None:
            from .DiffDialog import DiffDialog
            self.diffDlg = DiffDialog()
        self.diffDlg.show(fn)
        
    def __compareFilesSbs(self):
        """
        Private slot to handle the Compare Files dialog.
        """
        aw = self.viewmanager.activeWindow()
        fn = aw and aw.getFileName() or None
        if self.compareDlg is None:
            from .CompareDialog import CompareDialog
            self.compareDlg = CompareDialog()
        self.compareDlg.show(fn)
        
    def __openMiniEditor(self):
        """
        Private slot to show a mini editor window.
        """
        from QScintilla.MiniEditor import MiniEditor
        editor = MiniEditor(parent=self)
        editor.show()
        
    def addE5Actions(self, actions, type):
        """
        Public method to add actions to the list of actions.
        
        @param actions list of actions to be added (list of E5Action)
        @param type string denoting the action set to get.
            It must be one of "ui" or "wizards".
        """
        if type == 'ui':
            self.actions.extend(actions)
        elif type == 'wizards':
            self.wizardsActions.extend(actions)
        
    def removeE5Actions(self, actions, type='ui'):
        """
        Public method to remove actions from the list of actions.
        
        @param actions list of actions (list of E5Action)
        @param type string denoting the action set to get.
            It must be one of "ui" or "wizards".
        """
        for act in actions:
            try:
                if type == 'ui':
                    self.actions.remove(act)
                elif type == 'wizards':
                    self.wizardsActions.remove(act)
            except ValueError:
                pass
        
    def getActions(self, type):
        """
        Public method to get a list of all actions.
        
        @param type string denoting the action set to get.
            It must be one of "ui" or "wizards".
        @return list of all actions (list of E5Action)
        """
        if type == 'ui':
            return self.actions[:]
        elif type == 'wizards':
            return self.wizardsActions[:]
        else:
            return []
        
    def getMenuAction(self, menuName, actionName):
        """
        Public method to get a reference to an action of a menu.
        
        @param menuName name of the menu to search in (string)
        @param actionName object name of the action to search for
            (string)
        @return reference to the menu action (QAction)
        """
        try:
            menu = self.__menus[menuName]
        except KeyError:
            return None
        
        for act in menu.actions():
            if act.objectName() == actionName:
                return act
        
        return None
        
    def getMenuBarAction(self, menuName):
        """
        Public method to get a reference to an action of the main menu.
        
        @param menuName name of the menu to search in (string)
        @return reference to the menu bar action (QAction)
        """
        try:
            menu = self.__menus[menuName]
        except KeyError:
            return None
        
        return menu.menuAction()
        
    def getMenu(self, name):
        """
        Public method to get a reference to a specific menu.
        
        @param name name of the menu (string)
        @return reference to the menu (QMenu)
        """
        try:
            return self.__menus[name]
        except KeyError:
            return None
        
    def registerToolbar(self, name, text, toolbar):
        """
        Public method to register a toolbar.
        
        This method must be called in order to make a toolbar manageable by the
        UserInterface object.
        
        @param name name of the toolbar (string). This is used as the key into
            the dictionary of toolbar references.
        @param text user visible text for the toolbar entry (string)
        @param toolbar reference to the toolbar to be registered (QToolBar)
        @exception KeyError raised, if a toolbar with the given name was
            already registered
        """
        if name in self.__toolbars:
            raise KeyError("Toolbar '{0}' already registered.".format(name))
        
        self.__toolbars[name] = [text, toolbar]
        
    def reregisterToolbar(self, name, text):
        """
        Public method to change the visible text for the named toolbar.
        
        @param name name of the toolbar to be changed (string)
        @param text new user visible text for the toolbar entry (string)
        """
        if name in self.__toolbars:
            self.__toolbars[name][0] = text
        
    def unregisterToolbar(self, name):
        """
        Public method to unregister a toolbar.
        
        @param name name of the toolbar (string).
        """
        if name in self.__toolbars:
            del self.__toolbars[name]
        
    def getToolbar(self, name):
        """
        Public method to get a reference to a specific toolbar.
        
        @param name name of the toolbar (string)
        @return reference to the toolbar entry (tuple of string and QToolBar)
        """
        try:
            return self.__toolbars[name]
        except KeyError:
            return None
        
    def getLocale(self):
        """
        Public method to get the locale of the IDE.
        
        @return locale of the IDE (string or None)
        """
        return self.locale
        
    def __quit(self):
        """
        Private method to quit the application.
        """
        if self.__shutdown():
            e5App().closeAllWindows()
        
    def __restart(self):
        """
        Private method to restart the application.
        """
        res = E5MessageBox.yesNo(
            self,
            self.tr("Restart application"),
            self.tr(
                """The application needs to be restarted. Do it now?"""),
            yesDefault=True)
        
        if res and self.__shutdown():
            e5App().closeAllWindows()
            program = sys.executable
            eric6 = os.path.join(getConfig("ericDir"), "eric6.py")
            args = [eric6]
            args.append("--start-session")
            args.extend(self.__restartArgs)
            QProcess.startDetached(program, args)
        
    def __newWindow(self):
        """
        Private slot to start a new instance of eric6.
        """
        if not Preferences.getUI("SingleApplicationMode"):
            # start eric6 without any arguments
            program = sys.executable
            eric6 = os.path.join(getConfig("ericDir"), "eric6.py")
            args = [eric6]
            QProcess.startDetached(program, args)
        
    def __initToolsMenus(self, menu):
        """
        Private slot to initialize the various tool menus.
        
        @param menu reference to the parent menu
        @type QMenu
        """
        btMenu = QMenu(self.tr("&Builtin Tools"), self)
        if self.designer4Act is not None:
            btMenu.addAction(self.designer4Act)
        if self.linguist4Act is not None:
            btMenu.addAction(self.linguist4Act)
        btMenu.addAction(self.uipreviewerAct)
        btMenu.addAction(self.trpreviewerAct)
        btMenu.addAction(self.diffAct)
        btMenu.addAction(self.compareAct)
        btMenu.addAction(self.sqlBrowserAct)
        btMenu.addAction(self.miniEditorAct)
        btMenu.addAction(self.iconEditorAct)
        btMenu.addAction(self.snapshotAct)
        btMenu.addAction(self.webBrowserAct)
        
        ptMenu = QMenu(self.tr("&Plugin Tools"), self)
        ptMenu.aboutToShow.connect(self.__showPluginToolsMenu)
        
        utMenu = QMenu(self.tr("&User Tools"), self)
        utMenu.triggered.connect(self.__toolExecute)
        utMenu.aboutToShow.connect(self.__showUserToolsMenu)
        
        menu.addMenu(btMenu)
        menu.addMenu(ptMenu)
        menu.addMenu(utMenu)
        
        self.__menus["builtin_tools"] = btMenu
        self.__menus["plugin_tools"] = ptMenu
        self.__menus["user_tools"] = utMenu
        
    def __showPluginToolsMenu(self):
        """
        Private slot to show the Plugin Tools menu.
        """
        self.showMenu.emit("PluginTools", self.__menus["plugin_tools"])
        
    def __showUserToolsMenu(self):
        """
        Private slot to display the User Tools menu.
        """
        self.__menus["user_tools"].clear()
        
        self.__menus["user_tools"].addMenu(self.toolGroupsMenu)
        act = self.__menus["user_tools"].addAction(
            self.tr("Configure Tool Groups ..."),
            self.__toolGroupsConfiguration)
        act.setData(-1)
        act = self.__menus["user_tools"].addAction(
            self.tr("Configure current Tool Group ..."),
            self.__toolsConfiguration)
        act.setData(-2)
        act.setEnabled(self.currentToolGroup >= 0)
        self.__menus["user_tools"].addSeparator()
        
        # add the configurable entries
        idx = 0
        try:
            for tool in self.toolGroups[self.currentToolGroup][1]:
                if tool['menutext'] == '--':
                    self.__menus["user_tools"].addSeparator()
                else:
                    act = self.__menus["user_tools"].addAction(
                        UI.PixmapCache.getIcon(tool['icon']),
                        tool['menutext'])
                    act.setData(idx)
                idx += 1
        except IndexError:
            # the current tool group might have been deleted
            act = self.__menus["user_tools"].addAction(
                self.tr("No User Tools Configured"))
            act.setData(-3)
        
    def __showToolGroupsMenu(self):
        """
        Private slot to display the Tool Groups menu.
        """
        self.toolGroupsMenu.clear()
        
        # add the configurable tool groups
        if self.toolGroups:
            idx = 0
            for toolGroup in self.toolGroups:
                act = self.toolGroupsMenu.addAction(toolGroup[0])
                act.setData(idx)
                if self.currentToolGroup == idx:
                    font = act.font()
                    font.setBold(True)
                    act.setFont(font)
                idx += 1
        else:
            act = self.toolGroupsMenu.addAction(
                self.tr("No User Tools Configured"))
            act.setData(-3)
        
    def __toolGroupSelected(self, act):
        """
        Private slot to set the current tool group.
        
        @param act reference to the action that was triggered (QAction)
        """
        self.toolGroupsMenuTriggered = True
        idx = act.data()
        if idx is not None:
            self.currentToolGroup = idx
        
    def __showWindowMenu(self):
        """
        Private slot to display the Window menu.
        """
        self.__menus["window"].clear()
        
        self.__menus["window"].addActions(self.viewProfileActGrp.actions())
        self.__menus["window"].addSeparator()
        
        if self.layoutType == "Toolboxes":
            self.__menus["window"].addAction(self.ltAct)
            self.ltAct.setChecked(not self.lToolboxDock.isHidden())
            self.__menus["window"].addAction(self.rtAct)
            self.rtAct.setChecked(not self.lToolboxDock.isHidden())
            self.__menus["window"].addAction(self.htAct)
            self.htAct.setChecked(not self.hToolboxDock.isHidden())
        elif self.layoutType == "Sidebars":
            self.__menus["window"].addAction(self.lsbAct)
            self.lsbAct.setChecked(not self.leftSidebar.isHidden())
            self.__menus["window"].addAction(self.rsbAct)
            self.rsbAct.setChecked(not self.rightSidebar.isHidden())
            self.__menus["window"].addAction(self.bsbAct)
            self.bsbAct.setChecked(not self.bottomSidebar.isHidden())
        
        # Insert menu entry for sub-windows
        self.__menus["window"].addSeparator()
        self.__menus["window"].addMenu(self.__menus["subwindow"])
        
        # Insert menu entry for toolbar settings
        self.__menus["window"].addSeparator()
        self.__menus["window"].addMenu(self.__menus["toolbars"])
        
        # Now do any Source Viewer related stuff.
        self.viewmanager.showWindowMenu(self.__menus["window"])
        
        self.showMenu.emit("Window", self.__menus["window"])
        
    def __showSubWindowMenu(self):
        """
        Private slot to display the Window menu of the Window menu.
        """
        self.showMenu.emit("Subwindows", self.__menus["subwindow"])
        
    def __populateToolbarsMenu(self, menu):
        """
        Private method to populate a toolbars menu.
        
        @param menu reference to the menu to be populated (QMenu)
        """
        menu.clear()
        
        tbList = []
        for name, (text, tb) in list(self.__toolbars.items()):
            tbList.append((text, tb, name))
        
        for text, tb, name in sorted(tbList):
            act = menu.addAction(text)
            act.setCheckable(True)
            act.setChecked(not tb.isHidden())
            act.setData(name)
        menu.addSeparator()
        act = menu.addAction(self.tr("&Show all"))
        act.setData("__SHOW__")
        act = menu.addAction(self.tr("&Hide all"))
        act.setData("__HIDE__")
        
    def createPopupMenu(self):
        """
        Public method to create the toolbars menu for Qt.
        
        @return toolbars menu (QMenu)
        """
        menu = QMenu(self)
        menu.triggered.connect(self.__TBPopupMenuTriggered)
        
        self.__populateToolbarsMenu(menu)
        
        return menu
        
    def __showToolbarsMenu(self):
        """
        Private slot to display the Toolbars menu.
        """
        self.__populateToolbarsMenu(self.__menus["toolbars"])

    def __TBMenuTriggered(self, act):
        """
        Private method to handle the toggle of a toolbar via the Window->
        Toolbars submenu.
        
        @param act reference to the action that was triggered (QAction)
        """
        name = act.data()
        if name:
            if name == "__SHOW__":
                for text, tb in list(self.__toolbars.values()):
                    tb.show()
                if self.__menus["toolbars"].isTearOffMenuVisible():
                    self.__menus["toolbars"].hideTearOffMenu()
            elif name == "__HIDE__":
                for text, tb in list(self.__toolbars.values()):
                    tb.hide()
                if self.__menus["toolbars"].isTearOffMenuVisible():
                    self.__menus["toolbars"].hideTearOffMenu()
            else:
                tb = self.__toolbars[name][1]
                if act.isChecked():
                    tb.show()
                else:
                    tb.hide()

    def __TBPopupMenuTriggered(self, act):
        """
        Private method to handle the toggle of a toolbar via the QMainWindow
        Toolbars popup menu.
        
        @param act reference to the action that was triggered (QAction)
        """
        name = act.data()
        if name:
            if name == "__SHOW__":
                for text, tb in list(self.__toolbars.values()):
                    tb.show()
            elif name == "__HIDE__":
                for text, tb in list(self.__toolbars.values()):
                    tb.hide()
            else:
                tb = self.__toolbars[name][1]
                if act.isChecked():
                    tb.show()
                else:
                    tb.hide()
            if self.__menus["toolbars"].isTearOffMenuVisible():
                self.__menus["toolbars"].hideTearOffMenu()
        
    def __saveCurrentViewProfile(self, save):
        """
        Private slot to save the window geometries of the active profile.
        
        @param save flag indicating that the current profile should
            be saved (boolean)
        """
        if self.currentProfile and save:
            # step 1: save the window geometries of the active profile
            if self.layoutType in ["Toolboxes", "Sidebars"]:
                state = self.saveState()
                self.profiles[self.currentProfile][0] = state
                if self.layoutType == "Sidebars":
                    state = self.leftSplitter.saveState()
                    self.profiles[self.currentProfile][2][0] = state
                    state = self.verticalSplitter.saveState()
                    self.profiles[self.currentProfile][2][1] = state
                    state = self.leftSidebar.saveState()
                    self.profiles[self.currentProfile][2][2] = state
                    state = self.bottomSidebar.saveState()
                    self.profiles[self.currentProfile][2][3] = state
                    state = self.rightSplitter.saveState()
                    self.profiles[self.currentProfile][2][4] = state
                    state = self.rightSidebar.saveState()
                    self.profiles[self.currentProfile][2][5] = state
            # step 2: save the visibility of the windows of the active profile
            if self.layoutType == "Toolboxes":
                self.profiles[self.currentProfile][1][0] = \
                    self.lToolboxDock.isVisible()
                self.profiles[self.currentProfile][1][1] = \
                    self.hToolboxDock.isVisible()
                self.profiles[self.currentProfile][1][2] = \
                    self.rToolboxDock.isVisible()
            elif self.layoutType == "Sidebars":
                self.profiles[self.currentProfile][1][0] = \
                    self.leftSidebar.isVisible()
                self.profiles[self.currentProfile][1][1] = \
                    self.bottomSidebar.isVisible()
                self.profiles[self.currentProfile][1][2] = \
                    self.rightSidebar.isVisible()
            Preferences.setUI("ViewProfiles2", self.profiles)
    
    def __activateViewProfile(self, name, save=True):
        """
        Private slot to activate a view profile.
        
        @param name name of the profile to be activated (string)
        @param save flag indicating that the current profile should
            be saved (boolean)
        """
        if self.currentProfile != name or not save:
            # step 1: save the active profile
            self.__saveCurrentViewProfile(save)
            
            # step 2: set the window geometries of the new profile
            if self.layoutType in ["Toolboxes", "Sidebars"]:
                state = self.profiles[name][0]
                if not state.isEmpty():
                    self.restoreState(state)
                if self.layoutType == "Sidebars":
                    state = self.profiles[name][2][0]
                    if not state.isEmpty():
                        self.leftSplitter.restoreState(state)
                    state = self.profiles[name][2][1]
                    if not state.isEmpty():
                        self.verticalSplitter.restoreState(state)
                    state = self.profiles[name][2][2]
                    if not state.isEmpty():
                        self.leftSidebar.restoreState(state)
                    state = self.profiles[name][2][3]
                    if not state.isEmpty():
                        self.bottomSidebar.restoreState(state)
                    state = self.profiles[name][2][4]
                    if not state.isEmpty():
                        self.rightSplitter.restoreState(state)
                    state = self.profiles[name][2][5]
                    if not state.isEmpty():
                        self.rightSidebar.restoreState(state)
                self.__configureDockareaCornerUsage()
            
            # step 3: activate the windows of the new profile
            if self.layoutType == "Toolboxes":
                self.lToolboxDock.setVisible(self.profiles[name][1][0])
                self.hToolboxDock.setVisible(self.profiles[name][1][1])
                self.rToolboxDock.setVisible(self.profiles[name][1][2])
            elif self.layoutType == "Sidebars":
                self.leftSidebar.setVisible(self.profiles[name][1][0])
                self.bottomSidebar.setVisible(self.profiles[name][1][1])
                self.rightSidebar.setVisible(self.profiles[name][1][2])
            
            # step 4: remember the new profile
            self.currentProfile = name
            
            # step 5: make sure that cursor of the shell is visible
            self.shell.ensureCursorVisible()
            
            # step 6: make sure, that the toolbars and window menu are
            #         shown correctly
            if self.__menus["toolbars"].isTearOffMenuVisible():
                self.__showToolbarsMenu()
            if self.__menus["window"].isTearOffMenuVisible():
                self.__showWindowMenu()
        
    def __debuggingStarted(self):
        """
        Private slot to handle the start of a debugging session.
        """
        self.setDebugProfile()
        if self.layoutType == "Toolboxes":
            self.__currentRightWidget = self.rToolbox.currentWidget()
            self.rToolbox.setCurrentWidget(self.debugViewer)
            if not self.embeddedShell:
                self.__currentBottomWidget = self.hToolbox.currentWidget()
                self.hToolbox.setCurrentWidget(self.shellAssembly)
        elif self.layoutType == "Sidebars":
            self.__currentRightWidget = self.rightSidebar.currentWidget()
            self.rightSidebar.setCurrentWidget(self.debugViewer)
            if not self.embeddedShell:
                self.__currentBottomWidget = self.bottomSidebar.currentWidget()
                self.bottomSidebar.setCurrentWidget(self.shellAssembly)
        
    def __debuggingDone(self):
        """
        Private slot to handle the end of a debugging session.
        """
        self.__setEditProfile()
        if self.layoutType == "Toolboxes":
            if self.__currentRightWidget:
                self.rToolbox.setCurrentWidget(self.__currentRightWidget)
            if self.__currentBottomWidget:
                self.hToolbox.setCurrentWidget(self.__currentBottomWidget)
        elif self.layoutType == "Sidebars":
            if self.__currentRightWidget:
                self.rightSidebar.setCurrentWidget(self.__currentRightWidget)
            if self.__currentBottomWidget:
                self.bottomSidebar.setCurrentWidget(self.__currentBottomWidget)
        self.__currentRightWidget = None
        self.__currentBottomWidget = None
        self.__activateViewmanager()
        
    @pyqtSlot()
    def __setEditProfile(self, save=True):
        """
        Private slot to activate the edit view profile.
        
        @param save flag indicating that the current profile should
            be saved (boolean)
        """
        self.__activateViewProfile("edit", save)
        self.setEditProfileAct.setChecked(True)
        
    @pyqtSlot()
    def setDebugProfile(self, save=True):
        """
        Public slot to activate the debug view profile.
        
        @param save flag indicating that the current profile should
            be saved (boolean)
        """
        self.viewmanager.searchWidget().hide()
        self.viewmanager.replaceWidget().hide()
        self.__activateViewProfile("debug", save)
        self.setDebugProfileAct.setChecked(True)
        
    def getViewProfile(self):
        """
        Public method to get the current view profile.
        
        @return the name of the current view profile (string)
        """
        return self.currentProfile
        
    def __activateProjectBrowser(self):
        """
        Private slot to handle the activation of the project browser.
        """
        if self.layoutType == "Toolboxes":
            self.lToolboxDock.show()
            self.lToolbox.setCurrentWidget(self.projectBrowser)
        elif self.layoutType == "Sidebars":
            self.leftSidebar.show()
            self.leftSidebar.setCurrentWidget(self.projectBrowser)
        else:
            self.projectBrowser.show()
        self.projectBrowser.currentWidget().setFocus(
            Qt.ActiveWindowFocusReason)
        
    def __activateMultiProjectBrowser(self):
        """
        Private slot to handle the activation of the project browser.
        """
        if self.layoutType == "Toolboxes":
            self.lToolboxDock.show()
            self.lToolbox.setCurrentWidget(self.multiProjectBrowser)
        elif self.layoutType == "Sidebars":
            self.leftSidebar.show()
            self.leftSidebar.setCurrentWidget(self.multiProjectBrowser)
        else:
            self.multiProjectBrowser.show()
        self.multiProjectBrowser.setFocus(Qt.ActiveWindowFocusReason)
        
    def __activateDebugViewer(self):
        """
        Private slot to handle the activation of the debug viewer.
        """
        if self.layoutType == "Toolboxes":
            self.rToolboxDock.show()
            self.rToolbox.setCurrentWidget(self.debugViewer)
        elif self.layoutType == "Sidebars":
            self.rightSidebar.show()
            self.rightSidebar.setCurrentWidget(self.debugViewer)
        else:
            self.debugViewer.show()
        self.debugViewer.currentWidget().setFocus(Qt.ActiveWindowFocusReason)
        
    def __activateShell(self):
        """
        Private slot to handle the activation of the Shell window.
        """
        if self.embeddedShell:              # embedded in debug browser
            if self.layoutType == "Toolboxes":
                self.rToolboxDock.show()
                self.rToolbox.setCurrentWidget(self.debugViewer)
            elif self.layoutType == "Sidebars":
                self.rightSidebar.show()
                self.rightSidebar.setCurrentWidget(self.debugViewer)
            else:
                self.debugViewer.show()
            self.debugViewer.setCurrentWidget(self.shellAssembly)
        else:                               # separate window
            if self.layoutType == "Toolboxes":
                self.hToolboxDock.show()
                self.hToolbox.setCurrentWidget(self.shellAssembly)
            elif self.layoutType == "Sidebars":
                self.bottomSidebar.show()
                self.bottomSidebar.setCurrentWidget(self.shellAssembly)
            else:
                self.shell.show()
        self.shell.setFocus(Qt.ActiveWindowFocusReason)
        
    def __activateLogViewer(self):
        """
        Private slot to handle the activation of the Log Viewer.
        """
        if self.layoutType == "Toolboxes":
            self.hToolboxDock.show()
            self.hToolbox.setCurrentWidget(self.logViewer)
        elif self.layoutType == "Sidebars":
            self.bottomSidebar.show()
            self.bottomSidebar.setCurrentWidget(self.logViewer)
        else:
            self.logViewer.show()
        self.logViewer.setFocus(Qt.ActiveWindowFocusReason)
        
    def __activateTaskViewer(self):
        """
        Private slot to handle the activation of the Task Viewer.
        """
        if self.layoutType == "Toolboxes":
            self.hToolboxDock.show()
            self.hToolbox.setCurrentWidget(self.taskViewer)
        elif self.layoutType == "Sidebars":
            self.bottomSidebar.show()
            self.bottomSidebar.setCurrentWidget(self.taskViewer)
        else:
            self.taskViewer.show()
        self.taskViewer.setFocus(Qt.ActiveWindowFocusReason)
        
    def __activateTemplateViewer(self):
        """
        Private slot to handle the activation of the Template Viewer.
        """
        if self.layoutType == "Toolboxes":
            self.lToolboxDock.show()
            self.lToolbox.setCurrentWidget(self.templateViewer)
        elif self.layoutType == "Sidebars":
            self.leftSidebar.show()
            self.leftSidebar.setCurrentWidget(self.templateViewer)
        else:
            self.templateViewer.show()
        self.templateViewer.setFocus(Qt.ActiveWindowFocusReason)
        
    def __activateBrowser(self):
        """
        Private slot to handle the activation of the file browser.
        """
        if self.embeddedFileBrowser == 0:   # separate window
            if self.layoutType == "Toolboxes":
                self.lToolboxDock.show()
                self.lToolbox.setCurrentWidget(self.browser)
            elif self.layoutType == "Sidebars":
                self.leftSidebar.show()
                self.leftSidebar.setCurrentWidget(self.browser)
            else:
                self.browser.show()
        elif self.embeddedFileBrowser == 1:  # embedded in debug browser
            if self.layoutType == "Toolboxes":
                self.rToolboxDock.show()
                self.rToolbox.setCurrentWidget(self.debugViewer)
            elif self.layoutType == "Sidebars":
                self.rightSidebar.show()
                self.rightSidebar.setCurrentWidget(self.debugViewer)
            else:
                self.debugViewer.show()
            self.debugViewer.setCurrentWidget(self.browser)
        else:                               # embedded in project browser
            if self.layoutType == "Toolboxes":
                self.lToolboxDock.show()
                self.lToolbox.setCurrentWidget(self.projectBrowser)
            elif self.layoutType == "Sidebars":
                self.leftSidebar.show()
                self.leftSidebar.setCurrentWidget(self.projectBrowser)
            else:
                self.projectBrowser.show()
            self.projectBrowser.setCurrentWidget(self.browser)
        self.browser.setFocus(Qt.ActiveWindowFocusReason)
        
    def __toggleLeftToolbox(self):
        """
        Private slot to handle the toggle of the Left Toolbox window.
        """
        hasFocus = self.lToolbox.currentWidget().hasFocus()
        shown = self.__toggleWindow(self.lToolboxDock)
        if shown:
            self.lToolbox.currentWidget().setFocus(Qt.ActiveWindowFocusReason)
        else:
            if hasFocus:
                self.__activateViewmanager()
        
    def __toggleRightToolbox(self):
        """
        Private slot to handle the toggle of the Right Toolbox window.
        """
        hasFocus = self.rToolbox.currentWidget().hasFocus()
        shown = self.__toggleWindow(self.rToolboxDock)
        if shown:
            self.rToolbox.currentWidget().setFocus(Qt.ActiveWindowFocusReason)
        else:
            if hasFocus:
                self.__activateViewmanager()
        
    def __toggleHorizontalToolbox(self):
        """
        Private slot to handle the toggle of the Horizontal Toolbox window.
        """
        hasFocus = self.hToolbox.currentWidget().hasFocus()
        shown = self.__toggleWindow(self.hToolboxDock)
        if shown:
            self.hToolbox.currentWidget().setFocus(Qt.ActiveWindowFocusReason)
        else:
            if hasFocus:
                self.__activateViewmanager()
        
    def __toggleLeftSidebar(self):
        """
        Private slot to handle the toggle of the left sidebar window.
        """
        hasFocus = self.leftSidebar.currentWidget().hasFocus()
        shown = self.__toggleWindow(self.leftSidebar)
        if shown:
            self.leftSidebar.currentWidget().setFocus(
                Qt.ActiveWindowFocusReason)
        else:
            if hasFocus:
                self.__activateViewmanager()
        
    def __toggleRightSidebar(self):
        """
        Private slot to handle the toggle of the right sidebar window.
        """
        hasFocus = self.rightSidebar.currentWidget().hasFocus()
        shown = self.__toggleWindow(self.rightSidebar)
        if shown:
            self.rightSidebar.currentWidget().setFocus(
                Qt.ActiveWindowFocusReason)
        else:
            if hasFocus:
                self.__activateViewmanager()
        
    def __toggleBottomSidebar(self):
        """
        Private slot to handle the toggle of the bottom sidebar window.
        """
        hasFocus = self.bottomSidebar.currentWidget().hasFocus()
        shown = self.__toggleWindow(self.bottomSidebar)
        if shown:
            self.bottomSidebar.currentWidget().setFocus(
                Qt.ActiveWindowFocusReason)
        else:
            if hasFocus:
                self.__activateViewmanager()
        
    def activateCooperationViewer(self):
        """
        Public slot to handle the activation of the cooperation window.
        """
        if self.layoutType == "Toolboxes":
            self.rToolboxDock.show()
            self.rToolbox.setCurrentWidget(self.cooperation)
        elif self.layoutType == "Sidebars":
            self.rightSidebar.show()
            self.rightSidebar.setCurrentWidget(self.cooperation)
        else:
            self.cooperation.show()
        self.cooperation.setFocus(Qt.ActiveWindowFocusReason)
        
    def __activateIRC(self):
        """
        Private slot to handle the activation of the IRC window.
        """
        if self.layoutType == "Toolboxes":
            self.rToolboxDock.show()
            self.rToolbox.setCurrentWidget(self.irc)
        elif self.layoutType == "Sidebars":
            self.rightSidebar.show()
            self.rightSidebar.setCurrentWidget(self.irc)
        else:
            self.irc.show()
        self.irc.setFocus(Qt.ActiveWindowFocusReason)
        
    def __activateSymbolsViewer(self):
        """
        Private slot to handle the activation of the Symbols Viewer.
        """
        if self.layoutType == "Toolboxes":
            self.lToolboxDock.show()
            self.lToolbox.setCurrentWidget(self.symbolsViewer)
        elif self.layoutType == "Sidebars":
            self.leftSidebar.show()
            self.leftSidebar.setCurrentWidget(self.symbolsViewer)
        else:
            self.symbolsViewer.show()
        self.symbolsViewer.setFocus(Qt.ActiveWindowFocusReason)
        
    def __activateNumbersViewer(self):
        """
        Private slot to handle the activation of the Numbers Viewer.
        """
        if self.layoutType == "Toolboxes":
            self.hToolboxDock.show()
            self.hToolboxDock.setCurrentWidget(self.numbersViewer)
        elif self.layoutType == "Sidebars":
            self.bottomSidebar.show()
            self.bottomSidebar.setCurrentWidget(self.numbersViewer)
        else:
            self.numbersViewer.show()
        self.numbersViewer.setFocus(Qt.ActiveWindowFocusReason)
        
    def __activateViewmanager(self):
        """
        Private slot to handle the activation of the current editor.
        """
        aw = self.viewmanager.activeWindow()
        if aw is not None:
            aw.setFocus(Qt.ActiveWindowFocusReason)
    
    def __toggleWindow(self, w):
        """
        Private method to toggle a workspace editor window.
        
        @param w reference to the workspace editor window
        @return flag indicating, if the window was shown (boolean)
        """
        if w.isHidden():
            w.show()
            return True
        else:
            w.hide()
            return False
        
    def __toolsConfiguration(self):
        """
        Private slot to handle the tools configuration menu entry.
        """
        from Preferences.ToolConfigurationDialog import ToolConfigurationDialog
        dlg = ToolConfigurationDialog(
            self.toolGroups[self.currentToolGroup][1], self)
        if dlg.exec_() == QDialog.Accepted:
            self.toolGroups[self.currentToolGroup][1] = dlg.getToollist()
            self.__updateExternalToolsActions()
        
    def __toolGroupsConfiguration(self):
        """
        Private slot to handle the tool groups configuration menu entry.
        """
        from Preferences.ToolGroupConfigurationDialog import \
            ToolGroupConfigurationDialog
        dlg = ToolGroupConfigurationDialog(
            self.toolGroups, self.currentToolGroup, self)
        if dlg.exec_() == QDialog.Accepted:
            self.toolGroups, self.currentToolGroup = dlg.getToolGroups()
        
    def __createUnitTestDialog(self):
        """
        Private slot to generate the unit test dialog on demand.
        """
        if self.unittestDialog is None:
            from PyUnit.UnittestDialog import UnittestDialog
            self.unittestDialog = UnittestDialog(
                None, self.debuggerUI.debugServer, self, fromEric=True)
            self.unittestDialog.unittestFile.connect(
                self.viewmanager.setFileLine)
            self.unittestDialog.unittestStopped.connect(self.__unittestStopped)
    
    def __unittestStopped(self):
        """
        Private slot to handle the end of a unit test run.
        """
        self.utRerunFailedAct.setEnabled(self.unittestDialog.hasFailedTests())
        self.utRestartAct.setEnabled(True)
    
    def __unittest(self):
        """
        Private slot for displaying the unittest dialog.
        """
        self.__createUnitTestDialog()
        self.unittestDialog.show()
        self.unittestDialog.raise_()
    
    @pyqtSlot()
    @pyqtSlot(str)
    def __unittestScript(self, prog=None):
        """
        Private slot for displaying the unittest dialog and run the current
        script.
        
        @param prog the python program to be opened
        """
        if prog is None:
            aw = self.viewmanager.activeWindow()
            fn = aw.getFileName()
            tfn = Utilities.getTestFileName(fn)
            if os.path.exists(tfn):
                prog = tfn
            else:
                prog = fn
        
        self.__createUnitTestDialog()
        self.unittestDialog.insertProg(prog)
        self.unittestDialog.show()
        self.unittestDialog.raise_()
        self.utRestartAct.setEnabled(False)
        self.utRerunFailedAct.setEnabled(False)
        
    def __unittestProject(self):
        """
        Private slot for displaying the unittest dialog and run the current
        project.
        """
        fn = self.project.getMainScript(True)
        if fn:
            tfn = Utilities.getTestFileName(fn)
            if os.path.exists(tfn):
                prog = tfn
            else:
                prog = fn
        else:
            E5MessageBox.critical(
                self,
                self.tr("Unittest Project"),
                self.tr(
                    "There is no main script defined for the"
                    " current project. Aborting"))
            return
        
        self.__createUnitTestDialog()
        self.unittestDialog.insertProg(prog)
        self.unittestDialog.show()
        self.unittestDialog.raise_()
        self.utRestartAct.setEnabled(False)
        self.utRerunFailedAct.setEnabled(False)
        
    def __unittestRestart(self):
        """
        Private slot to display the unittest dialog and rerun the last
        unit test.
        """
        self.__createUnitTestDialog()
        self.unittestDialog.show()
        self.unittestDialog.raise_()
        self.unittestDialog.on_startButton_clicked()
        
    def __unittestRerunFailed(self):
        """
        Private slot to display the unittest dialog and rerun all failed tests
        of the last run.
        """
        self.__createUnitTestDialog()
        self.unittestDialog.show()
        self.unittestDialog.raise_()
        self.unittestDialog.on_startButton_clicked(failedOnly=True)
        
    def __designer(self, fn=None, version=0):
        """
        Private slot to start the Qt-Designer executable.
        
        @param fn filename of the form to be opened
        @param version indication for the requested version (Qt 4) (integer)
        """
        if fn is not None and version == 0:
            # determine version from file, if not specified
            try:
                f = open(fn, "r", encoding="utf-8")
                found = False
                while not found:
                    uiLine = f.readline()
                    found = uiLine.lower().startswith("<ui ")
                f.close()
                if uiLine.lower().find("version") == -1:
                    # it is an old version 3 UI file
                    version = 3
                else:
                    if uiLine.split('"')[1].startswith("4."):
                        version = 4
                    else:
                        version = 3
            except IOError:
                pass
        
        if version == 3:
            E5MessageBox.information(
                self,
                self.tr("Qt 3 support"),
                self.tr("""Qt v.3 is not supported by eric6."""))
            return

        args = []
        if fn is not None:
            try:
                if os.path.isfile(fn) and os.path.getsize(fn):
                    args.append(fn)
                else:
                    E5MessageBox.critical(
                        self,
                        self.tr('Problem'),
                        self.tr(
                            '<p>The file <b>{0}</b> does not exist or'
                            ' is zero length.</p>')
                        .format(fn))
                    return
            except EnvironmentError:
                E5MessageBox.critical(
                    self,
                    self.tr('Problem'),
                    self.tr(
                        '<p>The file <b>{0}</b> does not exist or'
                        ' is zero length.</p>')
                    .format(fn))
                return
        
        if Utilities.isMacPlatform():
            designer, args = Utilities.prepareQtMacBundle(
                "designer", version, args)
        else:
            if version == 4:
                designer = os.path.join(
                    Utilities.getQtBinariesPath(),
                    Utilities.generateQtToolName("designer"))
            if Utilities.isWindowsPlatform():
                designer += '.exe'
        
        proc = QProcess()
        if not proc.startDetached(designer, args):
            E5MessageBox.critical(
                self,
                self.tr('Process Generation Error'),
                self.tr(
                    '<p>Could not start Qt-Designer.<br>'
                    'Ensure that it is available as <b>{0}</b>.</p>'
                ).format(designer))
        
    def __designer4(self):
        """
        Private slot to start the Qt-Designer 4 executable.
        """
        self.__designer(version=4)
        
    def __linguist(self, fn=None, version=0):
        """
        Private slot to start the Qt-Linguist executable.
        
        @param fn filename of the translation file to be opened
        @param version indication for the requested version (Qt 4) (integer)
        """
        if version < 4:
            E5MessageBox.information(
                self,
                self.tr("Qt 3 support"),
                self.tr("""Qt v.3 is not supported by eric6."""))
            return

        args = []
        if fn is not None:
            fn = fn.replace('.qm', '.ts')
            try:
                if os.path.isfile(fn) and os.path.getsize(fn) and \
                        fn not in args:
                    args.append(fn)
                else:
                    E5MessageBox.critical(
                        self,
                        self.tr('Problem'),
                        self.tr(
                            '<p>The file <b>{0}</b> does not exist or'
                            ' is zero length.</p>')
                        .format(fn))
                    return
            except EnvironmentError:
                E5MessageBox.critical(
                    self,
                    self.tr('Problem'),
                    self.tr(
                        '<p>The file <b>{0}</b> does not exist or'
                        ' is zero length.</p>')
                    .format(fn))
                return
        
        if Utilities.isMacPlatform():
            linguist, args = Utilities.prepareQtMacBundle(
                "linguist", version, args)
        else:
            if version == 4:
                linguist = os.path.join(
                    Utilities.getQtBinariesPath(),
                    Utilities.generateQtToolName("linguist"))
            if Utilities.isWindowsPlatform():
                linguist += '.exe'
        
        proc = QProcess()
        if not proc.startDetached(linguist, args):
            E5MessageBox.critical(
                self,
                self.tr('Process Generation Error'),
                self.tr(
                    '<p>Could not start Qt-Linguist.<br>'
                    'Ensure that it is available as <b>{0}</b>.</p>'
                ).format(linguist))
    
    @pyqtSlot()
    @pyqtSlot(str)
    def __linguist4(self, fn=None):
        """
        Private slot to start the Qt-Linguist 4 executable.
        
        @param fn filename of the translation file to be opened
        """
        self.__linguist(fn, version=4)

    def __assistant(self, home=None, version=0):
        """
        Private slot to start the Qt-Assistant executable.
        
        @param home full pathname of a file to display (string)
        @param version indication for the requested version (Qt 4) (integer)
        """
        if version < 4:
            E5MessageBox.information(
                self,
                self.tr("Qt 3 support"),
                self.tr("""Qt v.3 is not supported by eric6."""))
            return

        args = []
        if home:
            if version == 4:
                args.append('-showUrl')
            args.append(home)
        
        if Utilities.isMacPlatform():
            assistant, args = Utilities.prepareQtMacBundle(
                "assistant", version, args)
        else:
            if version == 4:
                assistant = os.path.join(
                    Utilities.getQtBinariesPath(),
                    Utilities.generateQtToolName("assistant"))
            if Utilities.isWindowsPlatform():
                assistant += '.exe'
        
        proc = QProcess()
        if not proc.startDetached(assistant, args):
            E5MessageBox.critical(
                self,
                self.tr('Process Generation Error'),
                self.tr(
                    '<p>Could not start Qt-Assistant.<br>'
                    'Ensure that it is available as <b>{0}</b>.</p>'
                ).format(assistant))
        
    def __assistant4(self):
        """
        Private slot to start the Qt-Assistant 4 executable.
        """
        self.__assistant(version=4)
    
    def __startWebBrowser(self):
        """
        Private slot to start the eric6 web browser.
        """
        self.launchHelpViewer("")
        
    def __customViewer(self, home=None):
        """
        Private slot to start a custom viewer.
        
        @param home full pathname of a file to display (string)
        """
        customViewer = Preferences.getHelp("CustomViewer")
        if not customViewer:
            E5MessageBox.information(
                self,
                self.tr("Help"),
                self.tr(
                    """Currently no custom viewer is selected."""
                    """ Please use the preferences dialog to specify one."""))
            return
            
        proc = QProcess()
        args = []
        if home:
            args.append(home)
        
        if not proc.startDetached(customViewer, args):
            E5MessageBox.critical(
                self,
                self.tr('Process Generation Error'),
                self.tr(
                    '<p>Could not start custom viewer.<br>'
                    'Ensure that it is available as <b>{0}</b>.</p>'
                ).format(customViewer))
        
    def __chmViewer(self, home=None):
        """
        Private slot to start the win help viewer to show *.chm files.
        
        @param home full pathname of a file to display (string)
        """
        if home:
            proc = QProcess()
            args = []
            args.append(home)
            
            if not proc.startDetached("hh", args):
                E5MessageBox.critical(
                    self,
                    self.tr('Process Generation Error'),
                    self.tr(
                        '<p>Could not start the help viewer.<br>'
                        'Ensure that it is available as <b>hh</b>.</p>'
                    ))
        
    @pyqtSlot()
    @pyqtSlot(str)
    def __UIPreviewer(self, fn=None):
        """
        Private slot to start the UI Previewer executable.
        
        @param fn filename of the form to be previewed (string)
        """
        proc = QProcess()
        
        viewer = os.path.join(getConfig("ericDir"), "eric6_uipreviewer.py")
        
        args = []
        args.append(viewer)
        
        if fn is not None:
            try:
                if os.path.isfile(fn) and os.path.getsize(fn):
                    args.append(fn)
                else:
                    E5MessageBox.critical(
                        self,
                        self.tr('Problem'),
                        self.tr(
                            '<p>The file <b>{0}</b> does not exist or'
                            ' is zero length.</p>')
                        .format(fn))
                    return
            except EnvironmentError:
                E5MessageBox.critical(
                    self,
                    self.tr('Problem'),
                    self.tr(
                        '<p>The file <b>{0}</b> does not exist or'
                        ' is zero length.</p>')
                    .format(fn))
                return
                
        if not os.path.isfile(viewer) or \
                not proc.startDetached(sys.executable, args):
            E5MessageBox.critical(
                self,
                self.tr('Process Generation Error'),
                self.tr(
                    '<p>Could not start UI Previewer.<br>'
                    'Ensure that it is available as <b>{0}</b>.</p>'
                ).format(viewer))
        
    @pyqtSlot()
    @pyqtSlot(str)
    @pyqtSlot(str, bool)
    def __TRPreviewer(self, fileNames=None, ignore=False):
        """
        Private slot to start the Translation Previewer executable.
        
        @param fileNames filenames of forms and/or translations to be previewed
            (list of strings)
        @param ignore flag indicating non existing files should be ignored
            (boolean)
        """
        proc = QProcess()
        
        viewer = os.path.join(getConfig("ericDir"), "eric6_trpreviewer.py")
        
        args = []
        args.append(viewer)
        
        if fileNames is not None:
            for fn in fileNames:
                try:
                    if os.path.isfile(fn) and os.path.getsize(fn):
                        args.append(fn)
                    else:
                        if not ignore:
                            E5MessageBox.critical(
                                self,
                                self.tr('Problem'),
                                self.tr(
                                    '<p>The file <b>{0}</b> does not exist or'
                                    ' is zero length.</p>')
                                .format(fn))
                            return
                except EnvironmentError:
                    if not ignore:
                        E5MessageBox.critical(
                            self,
                            self.tr('Problem'),
                            self.tr(
                                '<p>The file <b>{0}</b> does not exist or'
                                ' is zero length.</p>')
                            .format(fn))
                        return
        
        if not os.path.isfile(viewer) or \
                not proc.startDetached(sys.executable, args):
            E5MessageBox.critical(
                self,
                self.tr('Process Generation Error'),
                self.tr(
                    '<p>Could not start Translation Previewer.<br>'
                    'Ensure that it is available as <b>{0}</b>.</p>'
                ).format(viewer))
        
    def __sqlBrowser(self):
        """
        Private slot to start the SQL browser tool.
        """
        proc = QProcess()
        
        browser = os.path.join(getConfig("ericDir"), "eric6_sqlbrowser.py")
        
        args = []
        args.append(browser)
        
        if not os.path.isfile(browser) or \
                not proc.startDetached(sys.executable, args):
            E5MessageBox.critical(
                self,
                self.tr('Process Generation Error'),
                self.tr(
                    '<p>Could not start SQL Browser.<br>'
                    'Ensure that it is available as <b>{0}</b>.</p>'
                ).format(browser))
        
    @pyqtSlot()
    @pyqtSlot(str)
    def __editPixmap(self, fn=""):
        """
        Private slot to show a pixmap in a dialog.
        
        @param fn filename of the file to show (string)
        """
        from IconEditor.IconEditorWindow import IconEditorWindow
        dlg = IconEditorWindow(fn, self, fromEric=True, project=self.project)
        dlg.show()
        
    @pyqtSlot()
    @pyqtSlot(str)
    def __showPixmap(self, fn):
        """
        Private slot to show a pixmap in a dialog.
        
        @param fn filename of the file to show (string)
        """
        from Graphics.PixmapDiagram import PixmapDiagram
        dlg = PixmapDiagram(fn, self)
        if dlg.getStatus():
            dlg.show()
        
    @pyqtSlot()
    @pyqtSlot(str)
    def __showSvg(self, fn):
        """
        Private slot to show a SVG file in a dialog.
        
        @param fn filename of the file to show (string)
        """
        from Graphics.SvgDiagram import SvgDiagram
        dlg = SvgDiagram(fn, self)
        dlg.show()
        
    def __snapshot(self):
        """
        Private slot to start the snapshot tool.
        """
        proc = QProcess()
        
        snap = os.path.join(getConfig("ericDir"), "eric6_snap.py")
        
        args = []
        args.append(snap)
        
        if not os.path.isfile(snap) or \
                not proc.startDetached(sys.executable, args):
            E5MessageBox.critical(
                self,
                self.tr('Process Generation Error'),
                self.tr(
                    '<p>Could not start Snapshot tool.<br>'
                    'Ensure that it is available as <b>{0}</b>.</p>'
                ).format(snap))
        
    def __toolActionTriggered(self):
        """
        Private slot called by external tools toolbar actions.
        """
        act = self.sender()
        toolGroupName, toolMenuText = act.objectName().split('@@', 1)
        for toolGroup in self.toolGroups:
            if toolGroup[0] == toolGroupName:
                for tool in toolGroup[1]:
                    if tool['menutext'] == toolMenuText:
                        self.__startToolProcess(tool)
                        return
                
                E5MessageBox.information(
                    self,
                    self.tr("External Tools"),
                    self.tr(
                        """No tool entry found for external tool '{0}' """
                        """in tool group '{1}'.""")
                    .format(toolMenuText, toolGroupName))
                return
        
        E5MessageBox.information(
            self,
            self.tr("External Tools"),
            self.tr("""No toolgroup entry '{0}' found.""")
            .format(toolGroupName)
        )
    
    def __toolExecute(self, act):
        """
        Private slot to execute a particular tool.
        
        @param act reference to the action that was triggered (QAction)
        """
        if self.toolGroupsMenuTriggered:
            # ignore actions triggered from the select tool group submenu
            self.toolGroupsMenuTriggered = False
            return
        
        if self.currentToolGroup < 0:
            # it was an action not to be handled here
            return
        
        idx = act.data()
        if idx is not None and idx >= 0:
            tool = self.toolGroups[self.currentToolGroup][1][idx]
            self.__startToolProcess(tool)
    
    def __startToolProcess(self, tool):
        """
        Private slot to start an external tool process.
        
        @param tool list of tool entries
        """
        proc = QProcess()
        procData = (None,)
        program = tool['executable']
        args = []
        argv = Utilities.parseOptionString(tool['arguments'])
        args.extend(argv)
        t = self.tr("Starting process '{0} {1}'.\n")\
            .format(program, tool['arguments'])
        self.appendToStdout(t)
        
        proc.finished.connect(self.__toolFinished)
        if tool['redirect'] != 'no':
            proc.readyReadStandardOutput.connect(self.__processToolStdout)
            proc.readyReadStandardError.connect(self.__processToolStderr)
            if tool['redirect'] in ["insert", "replaceSelection"]:
                aw = self.viewmanager.activeWindow()
                procData = (aw, tool['redirect'], [])
                if aw is not None:
                    aw.beginUndoAction()
        
        proc.start(program, args)
        if not proc.waitForStarted():
            E5MessageBox.critical(
                self,
                self.tr('Process Generation Error'),
                self.tr(
                    '<p>Could not start the tool entry <b>{0}</b>.<br>'
                    'Ensure that it is available as <b>{1}</b>.</p>')
                .format(tool['menutext'], tool['executable']))
        else:
            self.toolProcs.append((program, proc, procData))
            if tool['redirect'] == 'no':
                proc.closeReadChannel(QProcess.StandardOutput)
                proc.closeReadChannel(QProcess.StandardError)
                proc.closeWriteChannel()
        
    def __processToolStdout(self):
        """
        Private slot to handle the readyReadStdout signal of a tool process.
        """
        ioEncoding = Preferences.getSystem("IOEncoding")
        
        # loop through all running tool processes
        for program, toolProc, toolProcData in self.toolProcs:
            toolProc.setReadChannel(QProcess.StandardOutput)
            
            if toolProcData[0] is None or \
               toolProcData[1] not in ["insert", "replaceSelection"]:
                # not connected to an editor or wrong mode
                while toolProc.canReadLine():
                    output = str(toolProc.readLine(), ioEncoding, 'replace')
                    s = "{0} - {1}".format(program, output)
                    self.appendToStdout(s)
            else:
                if toolProcData[1] == "insert":
                    text = str(toolProc.readAll(), ioEncoding, 'replace')
                    toolProcData[0].insert(text)
                elif toolProcData[1] == "replaceSelection":
                    text = str(toolProc.readAll(), ioEncoding, 'replace')
                    toolProcData[2].append(text)
        
    def __processToolStderr(self):
        """
        Private slot to handle the readyReadStderr signal of a tool process.
        """
        ioEncoding = Preferences.getSystem("IOEncoding")
        
        # loop through all running tool processes
        for program, toolProc, toolProcData in self.toolProcs:
            toolProc.setReadChannel(QProcess.StandardError)
            
            while toolProc.canReadLine():
                error = str(toolProc.readLine(), ioEncoding, 'replace')
                s = "{0} - {1}".format(program, error)
                self.appendToStderr(s)
        
    def __toolFinished(self, exitCode, exitStatus):
        """
        Private slot to handle the finished signal of a tool process.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        exitedProcs = []
        
        # loop through all running tool processes
        for program, toolProc, toolProcData in self.toolProcs:
            if toolProc.state() == QProcess.NotRunning:
                exitedProcs.append((program, toolProc, toolProcData))
                if toolProcData[0] is not None:
                    if toolProcData[1] == "replaceSelection":
                        text = ''.join(toolProcData[2])
                        toolProcData[0].replace(text)
                    toolProcData[0].endUndoAction()
        
        # now delete the exited procs from the list of running processes
        for proc in exitedProcs:
            self.toolProcs.remove(proc)
            t = self.tr("Process '{0}' has exited.\n").format(proc[0])
            self.appendToStdout(t)
    
    def __showPythonDoc(self):
        """
        Private slot to show the Python 3 documentation.
        """
        pythonDocDir = Preferences.getHelp("PythonDocDir")
        if not pythonDocDir:
            if Utilities.isWindowsPlatform():
                pythonDocDir = Utilities.getEnvironmentEntry(
                    "PYTHON3DOCDIR",
                    os.path.join(os.path.dirname(sys.executable), "doc"))
            else:
                pythonDocDir = Utilities.getEnvironmentEntry(
                    "PYTHON3DOCDIR",
                    '/usr/share/doc/packages/python3/html')
        if not pythonDocDir.startswith("http://") and \
           not pythonDocDir.startswith("https://"):
            if pythonDocDir.startswith("file://"):
                pythonDocDir = pythonDocDir[7:]
            if not os.path.splitext(pythonDocDir)[1]:
                home = Utilities.normjoinpath(pythonDocDir, 'index.html')
                
                if Utilities.isWindowsPlatform() and not os.path.exists(home):
                    pyversion = sys.hexversion >> 16
                    vers = "{0:d}{1:d}".format((pyversion >> 8) & 0xff,
                                               pyversion & 0xff)
                    home = os.path.join(
                        pythonDocDir, "python{0}.chm".format(vers))
            else:
                home = pythonDocDir
            
            if not os.path.exists(home):
                E5MessageBox.warning(
                    self,
                    self.tr("Documentation Missing"),
                    self.tr("""<p>The documentation starting point"""
                            """ "<b>{0}</b>" could not be found.</p>""")
                    .format(home))
                return
            
            if not home.endswith(".chm"):
                if Utilities.isWindowsPlatform():
                    home = "file:///" + Utilities.fromNativeSeparators(home)
                else:
                    home = "file://" + home
        else:
            home = pythonDocDir
        
        if home.endswith(".chm"):
            self.__chmViewer(home)
        else:
            hvType = Preferences.getHelp("HelpViewerType")
            if hvType == 1:
                self.launchHelpViewer(home)
            elif hvType == 2:
                self.__assistant(home, version=4)
            elif hvType == 3:
                self.__webBrowser(home)
            else:
                self.__customViewer(home)

    def __showPython2Doc(self):
        """
        Private slot to show the Python 2 documentation.
        """
        pythonDocDir = Preferences.getHelp("Python2DocDir")
        executable = Preferences.getDebugger("PythonInterpreter")
        if not pythonDocDir:
            if Utilities.isWindowsPlatform():
                if executable:
                    default = os.path.join(os.path.dirname(executable), "doc")
                else:
                    default = ""
                pythonDocDir = \
                    Utilities.getEnvironmentEntry("PYTHON2DOCDIR", default)
            else:
                pythonDocDir = Utilities.getEnvironmentEntry(
                    "PYTHON2DOCDIR",
                    '/usr/share/doc/packages/python/html')
        if not pythonDocDir.startswith("http://") and \
           not pythonDocDir.startswith("https://"):
            if pythonDocDir.startswith("file://"):
                pythonDocDir = pythonDocDir[7:]
            if not os.path.splitext(pythonDocDir)[1]:
                home = Utilities.normjoinpath(pythonDocDir, 'index.html')
            else:
                home = pythonDocDir
            
            if not os.path.exists(home):
                E5MessageBox.warning(
                    self,
                    self.tr("Documentation Missing"),
                    self.tr("""<p>The documentation starting point"""
                            """ "<b>{0}</b>" could not be found.</p>""")
                    .format(home))
                return
            
            if not home.endswith(".chm"):
                if Utilities.isWindowsPlatform():
                    home = "file:///" + Utilities.fromNativeSeparators(home)
                else:
                    home = "file://" + home
        else:
            home = pythonDocDir
        
        if home.endswith(".chm"):
            self.__chmViewer(home)
        else:
            hvType = Preferences.getHelp("HelpViewerType")
            if hvType == 1:
                self.launchHelpViewer(home)
            elif hvType == 2:
                self.__assistant(home, version=4)
            elif hvType == 3:
                self.__webBrowser(home)
            else:
                self.__customViewer(home)

    def __showQt4Doc(self):
        """
        Private slot to show the Qt4 documentation.
        """
        self.__showQtDoc(4)
    
    def __showQt5Doc(self):
        """
        Private slot to show the Qt5 documentation.
        """
        self.__showQtDoc(5)
    
    def __showQtDoc(self, version):
        """
        Private method to show the Qt documentation.
        
        @param version Qt version to show documentation for (integer)
        """
        assert version in [4, 5]
        if version == 4:
            qtDocDir = Preferences.getQt4DocDir()
        elif version == 5:
            qtDocDir = Preferences.getQt5DocDir()
        
        if qtDocDir.startswith("qthelp://"):
            if not os.path.splitext(qtDocDir)[1]:
                home = qtDocDir + "/index.html"
            else:
                home = qtDocDir
        elif qtDocDir.startswith("http://") or qtDocDir.startswith("https://"):
            home = qtDocDir
        else:
            if qtDocDir.startswith("file://"):
                qtDocDir = qtDocDir[7:]
            if not os.path.splitext(qtDocDir)[1]:
                home = Utilities.normjoinpath(qtDocDir, 'index.html')
            else:
                home = qtDocDir
            
            if not os.path.exists(home):
                E5MessageBox.warning(
                    self,
                    self.tr("Documentation Missing"),
                    self.tr("""<p>The documentation starting point"""
                            """ "<b>{0}</b>" could not be found.</p>""")
                    .format(home))
                return
            
            if Utilities.isWindowsPlatform():
                home = "file:///" + Utilities.fromNativeSeparators(home)
            else:
                home = "file://" + home
        
        hvType = Preferences.getHelp("HelpViewerType")
        if hvType == 1:
            self.launchHelpViewer(home)
        elif hvType == 2:
            self.__assistant(home, version=4)
        elif hvType == 3:
            self.__webBrowser(home)
        else:
            self.__customViewer(home)
        
    def __showPyQt4Doc(self):
        """
        Private slot to show the PyQt4 documentation.
        """
        pyqt4DocDir = Preferences.getHelp("PyQt4DocDir")
        if not pyqt4DocDir:
            pyqt4DocDir = Utilities.getEnvironmentEntry("PYQT4DOCDIR", None)
        
        if not pyqt4DocDir:
            E5MessageBox.warning(
                self,
                self.tr("Documentation"),
                self.tr("""<p>The PyQt4 documentation starting point"""
                        """ has not been configured.</p>"""))
            return
        
        if not pyqt4DocDir.startswith("http://") and \
           not pyqt4DocDir.startswith("https://"):
            home = ""
            if pyqt4DocDir:
                if pyqt4DocDir.startswith("file://"):
                    pyqt4DocDir = pyqt4DocDir[7:]
                if not os.path.splitext(pyqt4DocDir)[1]:
                    possibleHomes = [
                        Utilities.normjoinpath(pyqt4DocDir, 'index.html'),
                        Utilities.normjoinpath(pyqt4DocDir, 'classes.html'),
                    ]
                    for possibleHome in possibleHomes:
                        if os.path.exists(possibleHome):
                            home = possibleHome
                            break
                else:
                    home = pyqt4DocDir
            
            if not home or not os.path.exists(home):
                E5MessageBox.warning(
                    self,
                    self.tr("Documentation Missing"),
                    self.tr("""<p>The documentation starting point"""
                            """ "<b>{0}</b>" could not be found.</p>""")
                    .format(home))
                return
            
            if Utilities.isWindowsPlatform():
                home = "file:///" + Utilities.fromNativeSeparators(home)
            else:
                home = "file://" + home
        else:
            home = pyqt4DocDir
        
        hvType = Preferences.getHelp("HelpViewerType")
        if hvType == 1:
            self.launchHelpViewer(home)
        elif hvType == 2:
            self.__assistant(home, version=4)
        elif hvType == 3:
            self.__webBrowser(home)
        else:
            self.__customViewer(home)
        
    def __showPyQt5Doc(self):
        """
        Private slot to show the PyQt5 documentation.
        """
        pyqt5DocDir = Preferences.getHelp("PyQt5DocDir")
        if not pyqt5DocDir:
            pyqt5DocDir = Utilities.getEnvironmentEntry("PYQT5DOCDIR", None)
        
        if not pyqt5DocDir:
            E5MessageBox.warning(
                self,
                self.tr("Documentation"),
                self.tr("""<p>The PyQt5 documentation starting point"""
                        """ has not been configured.</p>"""))
            return
        
        if not pyqt5DocDir.startswith("http://") and \
           not pyqt5DocDir.startswith("https://"):
            home = ""
            if pyqt5DocDir:
                if pyqt5DocDir.startswith("file://"):
                    pyqt5DocDir = pyqt5DocDir[7:]
                if not os.path.splitext(pyqt5DocDir)[1]:
                    possibleHomes = [
                        Utilities.normjoinpath(
                            pyqt5DocDir, 'index.html'),
                        Utilities.normjoinpath(
                            pyqt5DocDir, 'class_reference.html'),
                    ]
                    for possibleHome in possibleHomes:
                        if os.path.exists(possibleHome):
                            home = possibleHome
                            break
                else:
                    home = pyqt5DocDir
            
            if not home or not os.path.exists(home):
                E5MessageBox.warning(
                    self,
                    self.tr("Documentation Missing"),
                    self.tr("""<p>The documentation starting point"""
                            """ "<b>{0}</b>" could not be found.</p>""")
                    .format(home))
                return
            
            if Utilities.isWindowsPlatform():
                home = "file:///" + Utilities.fromNativeSeparators(home)
            else:
                home = "file://" + home
        else:
            home = pyqt5DocDir
        
        hvType = Preferences.getHelp("HelpViewerType")
        if hvType == 1:
            self.launchHelpViewer(home)
        elif hvType == 2:
            self.__assistant(home, version=4)
        elif hvType == 3:
            self.__webBrowser(home)
        else:
            self.__customViewer(home)
        
    def __showEricDoc(self):
        """
        Private slot to show the Eric documentation.
        """
        home = Utilities.normjoinpath(
            getConfig('ericDocDir'), "Source", "index.html")
        
        if not home.startswith("http://") and \
           not home.startswith("https://") and \
           not home.startswith("qthelp://"):
            if not os.path.exists(home):
                E5MessageBox.warning(
                    self,
                    self.tr("Documentation Missing"),
                    self.tr("""<p>The documentation starting point"""
                            """ "<b>{0}</b>" could not be found.</p>""")
                    .format(home))
                return
            
            if Utilities.isWindowsPlatform():
                home = "file:///" + Utilities.fromNativeSeparators(home)
            else:
                home = "file://" + home
        
        hvType = Preferences.getHelp("HelpViewerType")
        if hvType == 1:
            self.launchHelpViewer(home)
        elif hvType == 2:
            self.__assistant(home, version=4)
        elif hvType == 3:
            self.__webBrowser(home)
        else:
            self.__customViewer(home)
        
    def __showPySideDoc(self):
        """
        Private slot to show the PySide documentation.
        """
        pysideDocDir = Preferences.getHelp("PySideDocDir")
        if not pysideDocDir:
            pysideDocDir = Utilities.getEnvironmentEntry("PYSIDEDOCDIR", None)
        
        if not pysideDocDir:
            E5MessageBox.warning(
                self,
                self.tr("Documentation"),
                self.tr("""<p>The PySide documentation starting point"""
                        """ has not been configured.</p>"""))
            return
        
        if not pysideDocDir.startswith("http://") and \
           not pysideDocDir.startswith("https://"):
            if pysideDocDir.startswith("file://"):
                pysideDocDir = pysideDocDir[7:]
            if not os.path.splitext(pysideDocDir)[1]:
                home = Utilities.normjoinpath(pysideDocDir, 'index.html')
            else:
                home = pysideDocDir
            if not os.path.exists(home):
                E5MessageBox.warning(
                    self,
                    self.tr("Documentation Missing"),
                    self.tr("""<p>The documentation starting point"""
                            """ "<b>{0}</b>" could not be found.</p>""")
                    .format(home))
                return
            
            if Utilities.isWindowsPlatform():
                home = "file:///" + Utilities.fromNativeSeparators(home)
            else:
                home = "file://" + home
        else:
            home = pysideDocDir
        
        hvType = Preferences.getHelp("HelpViewerType")
        if hvType == 1:
            self.launchHelpViewer(home)
        elif hvType == 2:
            self.__assistant(home, version=4)
        elif hvType == 3:
            self.__webBrowser(home)
        else:
            self.__customViewer(home)
        
    def launchHelpViewer(self, home, searchWord=None, useSingle=False):
        """
        Public slot to start the help viewer.
        
        @param home filename of file to be shown (string)
        @keyparam searchWord word to search for (string)
        @keyparam useSingle flag indicating to use a single browser window
            (boolean)
        """
        if len(home) > 0:
            homeUrl = QUrl(home)
            if not homeUrl.scheme():
                home = QUrl.fromLocalFile(home).toString()
        if not (useSingle or Preferences.getHelp("SingleHelpWindow")) or \
           self.helpWindow is None:
            from Helpviewer.HelpWindow import HelpWindow
            help = HelpWindow(home, '.', None, 'help viewer', True,
                              searchWord=searchWord)

            if QApplication.desktop().width() > 400 and \
               QApplication.desktop().height() > 500:
                help.show()
            else:
                help.showMaximized()
            
            if useSingle or Preferences.getHelp("SingleHelpWindow"):
                self.helpWindow = help
                self.helpWindow.helpClosed.connect(self.__helpClosed)
                self.preferencesChanged.connect(
                    self.helpWindow.preferencesChanged)
                self.masterPasswordChanged.connect(
                    self.helpWindow.masterPasswordChanged)
        elif searchWord is not None:
            self.helpWindow.search(searchWord)
            self.helpWindow.raise_()
        else:
            self.helpWindow.newTab(home)
            self.helpWindow.raise_()
    
    def __helpClosed(self):
        """
        Private slot to handle the helpClosed signal of the help window.
        """
        if Preferences.getHelp("SingleHelpWindow"):
            self.preferencesChanged.disconnect(
                self.helpWindow.preferencesChanged)
            self.masterPasswordChanged.disconnect(
                self.helpWindow.masterPasswordChanged)
            self.helpWindow = None
    
    def __helpViewer(self):
        """
        Private slot to start an empty help viewer.
        """
        searchWord = self.viewmanager.textForFind(False)
        if searchWord == "":
            searchWord = None
        
        self.launchHelpViewer("", searchWord=searchWord)
    
    def __webBrowser(self, home=""):
        """
        Private slot to start the eric6 web browser.
        
        @param home full pathname of a file to display (string)
        """
        started = QDesktopServices.openUrl(QUrl(home))
        if not started:
            E5MessageBox.critical(
                self,
                self.tr('Open Browser'),
                self.tr('Could not start a web browser'))

    def getHelpViewer(self, preview=False):
        """
        Public method to get a reference to the help window instance.
        
        @keyparam preview flag indicating to get a help window for preview
            (boolean)
        @return reference to the help window instance (HelpWindow)
        """
        if self.helpWindow is None:
            self.launchHelpViewer("", useSingle=True)
        self.helpWindow.raise_()
        return self.helpWindow
    
    @pyqtSlot()
    @pyqtSlot(str)
    def showPreferences(self, pageName=None):
        """
        Public slot to set the preferences.
        
        @param pageName name of the configuration page to show (string)
        """
        from Preferences.ConfigurationDialog import ConfigurationDialog
        dlg = ConfigurationDialog(
            self, 'Configuration',
            expandedEntries=self.__expandedConfigurationEntries,
        )
        dlg.preferencesChanged.connect(self.__preferencesChanged)
        dlg.masterPasswordChanged.connect(self.__masterPasswordChanged)
        dlg.show()
        if pageName is not None:
            dlg.showConfigurationPageByName(pageName)
        elif self.__lastConfigurationPageName:
            dlg.showConfigurationPageByName(self.__lastConfigurationPageName)
        else:
            dlg.showConfigurationPageByName("empty")
        dlg.exec_()
        QApplication.processEvents()
        if dlg.result() == QDialog.Accepted:
            dlg.setPreferences()
            Preferences.syncPreferences()
            self.__preferencesChanged()
        self.__lastConfigurationPageName = dlg.getConfigurationPageName()
        self.__expandedConfigurationEntries = dlg.getExpandedEntries()
        
    def __exportPreferences(self):
        """
        Private slot to export the current preferences.
        """
        Preferences.exportPreferences()
        
    def __importPreferences(self):
        """
        Private slot to import preferences.
        """
        Preferences.importPreferences()
        self.__preferencesChanged()
        
    def __preferencesChanged(self):
        """
        Private slot to handle a change of the preferences.
        """
        self.setStyle(Preferences.getUI("Style"),
                      Preferences.getUI("StyleSheet"))
        
        if Preferences.getUI("SingleApplicationMode"):
            if self.SAServer is None:
                self.SAServer = E5SingleApplicationServer()
        else:
            if self.SAServer is not None:
                self.SAServer.shutdown()
                self.SAServer = None
        self.newWindowAct.setEnabled(
            not Preferences.getUI("SingleApplicationMode"))
        
        self.maxEditorPathLen = Preferences.getUI("CaptionFilenameLength")
        self.captionShowsFilename = Preferences.getUI("CaptionShowsFilename")
        if not self.captionShowsFilename:
            self.__setWindowCaption(editor="")
        else:
            aw = self.viewmanager.activeWindow()
            fn = aw and aw.getFileName() or None
            if fn:
                self.__setWindowCaption(editor=fn)
            else:
                self.__setWindowCaption(editor="")
        
        self.__httpAlternatives = Preferences.getUI("VersionsUrls6")
        self.performVersionCheck(False)
        
        self.__configureDockareaCornerUsage()
        
        from QScintilla.SpellChecker import SpellChecker
        SpellChecker.setDefaultLanguage(
            Preferences.getEditor("SpellCheckingDefaultLanguage"))
        
        if self.layoutType == "Sidebars":
            delay = Preferences.getUI("SidebarDelay")
            self.leftSidebar.setDelay(delay)
            self.bottomSidebar.setDelay(delay)
            self.rightSidebar.setDelay(delay)
        
        self.preferencesChanged.emit()
    
    def __masterPasswordChanged(self, oldPassword, newPassword):
        """
        Private slot to handle the change of the master password.
        
        @param oldPassword current master password (string)
        @param newPassword new master password (string)
        """
        self.masterPasswordChanged.emit(oldPassword, newPassword)
        Preferences.convertPasswords(oldPassword, newPassword)
        if self.helpWindow is None:
            from Helpviewer.Passwords.PasswordManager import PasswordManager
            pwManager = PasswordManager()
            pwManager.masterPasswordChanged(oldPassword, newPassword)
        Utilities.crypto.changeRememberedMaster(newPassword)
        
    def __reloadAPIs(self):
        """
        Private slot to reload the api information.
        """
        self.reloadAPIs.emit()
        
    def __showExternalTools(self):
        """
        Private slot to display a dialog show a list of external tools used
        by eric6.
        """
        if self.programsDialog is None:
            from Preferences.ProgramsDialog import ProgramsDialog
            self.programsDialog = ProgramsDialog(self)
        self.programsDialog.show()
        
    def __configViewProfiles(self):
        """
        Private slot to configure the various view profiles.
        """
        from Preferences.ViewProfileDialog import ViewProfileDialog
        dlg = ViewProfileDialog(self.layoutType, self.profiles['edit'][1],
                                self.profiles['debug'][1])
        if dlg.exec_() == QDialog.Accepted:
            edit, debug = dlg.getVisibilities()
            self.profiles['edit'][1] = edit
            self.profiles['debug'][1] = debug
            Preferences.setUI("ViewProfiles2", self.profiles)
            if self.currentProfile == "edit":
                self.__setEditProfile(False)
            elif self.currentProfile == "debug":
                self.setDebugProfile(False)
        
    def __configToolBars(self):
        """
        Private slot to configure the various toolbars.
        """
        from E5Gui.E5ToolBarDialog import E5ToolBarDialog
        dlg = E5ToolBarDialog(self.toolbarManager)
        if dlg.exec_() == QDialog.Accepted:
            Preferences.setUI(
                "ToolbarManagerState", self.toolbarManager.saveState())
        
    def __configShortcuts(self):
        """
        Private slot to configure the keyboard shortcuts.
        """
        if self.shortcutsDialog is None:
            from Preferences.ShortcutsDialog import ShortcutsDialog
            self.shortcutsDialog = ShortcutsDialog(self, 'Shortcuts')
        self.shortcutsDialog.populate()
        self.shortcutsDialog.show()
        
    def __exportShortcuts(self):
        """
        Private slot to export the keyboard shortcuts.
        """
        fn, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            None,
            self.tr("Export Keyboard Shortcuts"),
            "",
            self.tr("Keyboard shortcut file (*.e4k)"),
            "",
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        
        if not fn:
            return
        
        ext = QFileInfo(fn).suffix()
        if not ext:
            ex = selectedFilter.split("(*")[1].split(")")[0]
            if ex:
                fn += ex
        
        from Preferences import Shortcuts
        Shortcuts.exportShortcuts(fn)

    def __importShortcuts(self):
        """
        Private slot to import the keyboard shortcuts.
        """
        fn = E5FileDialog.getOpenFileName(
            None,
            self.tr("Import Keyboard Shortcuts"),
            "",
            self.tr("Keyboard shortcut file (*.e4k)"))
        
        if fn:
            from Preferences import Shortcuts
            Shortcuts.importShortcuts(fn)

    def __showCertificatesDialog(self):
        """
        Private slot to show the certificates management dialog.
        """
        from E5Network.E5SslCertificatesDialog import E5SslCertificatesDialog
        
        dlg = E5SslCertificatesDialog(self)
        dlg.exec_()
        
    def __newProject(self):
        """
        Private slot to handle the NewProject signal.
        """
        self.__setWindowCaption(project=self.project.name)
        
    def __projectOpened(self):
        """
        Private slot to handle the projectOpened signal.
        """
        from Debugger.DebugClientCapabilities import HasUnittest
        self.__setWindowCaption(project=self.project.name)
        cap = e5App().getObject("DebugServer")\
            .getClientCapabilities(self.project.pdata["PROGLANGUAGE"][0])
        self.utProjectAct.setEnabled(cap & HasUnittest)
        self.utProjectOpen = cap & HasUnittest
        
    def __projectClosed(self):
        """
        Private slot to handle the projectClosed signal.
        """
        self.__setWindowCaption(project="")
        self.utProjectAct.setEnabled(False)
        if not self.utEditorOpen:
            self.utRestartAct.setEnabled(False)
            self.utRerunFailedAct.setEnabled(False)
        self.utProjectOpen = False
        
    def __programChange(self, fn):
        """
        Private slot to handle the programChange signal.
        
        This primarily is here to set the currentProg variable.
        
        @param fn filename to be set as current prog (string)
        """
        # Delete the old program if there was one.
        if self.currentProg is not None:
            del self.currentProg

        self.currentProg = os.path.normpath(fn)
        
    def __lastEditorClosed(self):
        """
        Private slot to handle the lastEditorClosed signal.
        """
        self.wizardsMenuAct.setEnabled(False)
        self.utScriptAct.setEnabled(False)
        self.utEditorOpen = False
        if not self.utProjectOpen:
            self.utRestartAct.setEnabled(False)
            self.utRerunFailedAct.setEnabled(False)
        self.__setWindowCaption(editor="")
        
    def __editorOpened(self, fn):
        """
        Private slot to handle the editorOpened signal.
        
        @param fn filename of the opened editor (string)
        """
        self.wizardsMenuAct.setEnabled(
            len(self.__menus["wizards"].actions()) > 0)
        
        if fn and str(fn) != "None":
            dbs = e5App().getObject("DebugServer")
            for language in dbs.getSupportedLanguages():
                exts = dbs.getExtensions(language)
                if fn.endswith(exts):
                    from Debugger.DebugClientCapabilities import HasUnittest
                    cap = dbs.getClientCapabilities(language)
                    self.utScriptAct.setEnabled(cap & HasUnittest)
                    self.utEditorOpen = cap & HasUnittest
                    return
            
            if self.viewmanager.getOpenEditor(fn).isPyFile():
                self.utScriptAct.setEnabled(True)
                self.utEditorOpen = True
        
    def __checkActions(self, editor):
        """
        Private slot to check some actions for their enable/disable status.
        
        @param editor editor window
        """
        if editor:
            fn = editor.getFileName()
        else:
            fn = None
            
        if fn:
            dbs = e5App().getObject("DebugServer")
            for language in dbs.getSupportedLanguages():
                exts = dbs.getExtensions(language)
                if fn.endswith(exts):
                    from Debugger.DebugClientCapabilities import HasUnittest
                    cap = dbs.getClientCapabilities(language)
                    self.utScriptAct.setEnabled(cap & HasUnittest)
                    self.utEditorOpen = cap & HasUnittest
                    return
            
            if editor.isPyFile():
                self.utScriptAct.setEnabled(True)
                self.utEditorOpen = True
                return
        
        self.utScriptAct.setEnabled(False)
    
    def __writeTasks(self):
        """
        Private slot to write the tasks data to an XML file (.e6t).
        """
        fn = os.path.join(Utilities.getConfigDir(), "eric6tasks.e6t")
        f = QFile(fn)
        ok = f.open(QIODevice.WriteOnly)
        if not ok:
            E5MessageBox.critical(
                self,
                self.tr("Save tasks"),
                self.tr(
                    "<p>The tasks file <b>{0}</b> could not be written.</p>")
                .format(fn))
            return
        
        from E5XML.TasksWriter import TasksWriter
        TasksWriter(f, False).writeXML()
        f.close()
        
    def __readTasks(self):
        """
        Private slot to read in the tasks file (.e6t).
        """
        fn = os.path.join(Utilities.getConfigDir(), "eric6tasks.e6t")
        if not os.path.exists(fn):
            # try again with the old extension
            fn = os.path.join(Utilities.getConfigDir(), "eric6tasks.e4t")
            if not os.path.exists(fn):
                return
        f = QFile(fn)
        if f.open(QIODevice.ReadOnly):
            from E5XML.TasksReader import TasksReader
            reader = TasksReader(f, viewer=self.taskViewer)
            reader.readXML()
            f.close()
        else:
            E5MessageBox.critical(
                self,
                self.tr("Read tasks"),
                self.tr(
                    "<p>The tasks file <b>{0}</b> could not be read.</p>")
                .format(fn))
        
    def __writeSession(self):
        """
        Private slot to write the session data to an XML file (.e5s).
        """
        fn = os.path.join(Utilities.getConfigDir(), "eric6session.e5s")
        f = QFile(fn)
        if f.open(QIODevice.WriteOnly):
            from E5XML.SessionWriter import SessionWriter
            SessionWriter(f, None).writeXML()
            f.close()
        else:
            E5MessageBox.critical(
                self,
                self.tr("Save session"),
                self.tr(
                    "<p>The session file <b>{0}</b> could not be written.</p>")
                .format(fn))
        
    def __readSession(self):
        """
        Private slot to read in the session file (.e5s or .e4s).
        """
        fn = os.path.join(Utilities.getConfigDir(), "eric6session.e5s")
        if not os.path.exists(fn):
            fn = os.path.join(Utilities.getConfigDir(), "eric6session.e4s")
            if not os.path.exists(fn):
                E5MessageBox.critical(
                    self,
                    self.tr("Read session"),
                    self.tr(
                        "<p>The session file <b>{0}</b> could not"
                        " be read.</p>")
                    .format(fn))
                return
        
        f = QFile(fn)
        if f.open(QIODevice.ReadOnly):
            from E5XML.SessionReader import SessionReader
            reader = SessionReader(f, True)
            reader.readXML()
            f.close()
        else:
            E5MessageBox.critical(
                self,
                self.tr("Read session"),
                self.tr(
                    "<p>The session file <b>{0}</b> could not be read.</p>")
                .format(fn))
    
    def showFindFileByNameDialog(self):
        """
        Public slot to show the Find File by Name dialog.
        """
        if self.findFileNameDialog is None:
            from .FindFileNameDialog import FindFileNameDialog
            self.findFileNameDialog = FindFileNameDialog(self.project)
            self.findFileNameDialog.sourceFile.connect(
                self.viewmanager.openSourceFile)
            self.findFileNameDialog.designerFile.connect(self.__designer)
        self.findFileNameDialog.show()
        self.findFileNameDialog.raise_()
        self.findFileNameDialog.activateWindow()
    
    def showFindFilesDialog(self, txt="", searchDir="", openFiles=False):
        """
        Public slot to show the Find In Files dialog.
        
        @keyparam txt text to search for (string)
        @keyparam searchDir directory to search in (string)
        @keyparam openFiles flag indicating to operate on open files (boolean)
        """
        if self.findFilesDialog is None:
            from .FindFileDialog import FindFileDialog
            self.findFilesDialog = FindFileDialog(self.project)
            self.findFilesDialog.sourceFile.connect(
                self.viewmanager.openSourceFile)
            self.findFilesDialog.designerFile.connect(self.__designer)
        if searchDir:
            self.findFilesDialog.setSearchDirectory(searchDir)
        self.findFilesDialog.show(txt)
        if openFiles:
            self.findFilesDialog.setOpenFiles()
        self.findFilesDialog.raise_()
        self.findFilesDialog.activateWindow()
    
    def showReplaceFilesDialog(self, txt="", searchDir="", openFiles=False):
        """
        Public slot to show the Find & Replace In Files dialog.
        
        @keyparam txt text to search for (string)
        @keyparam searchDir directory to search in (string)
        @keyparam openFiles flag indicating to operate on open files (boolean)
        """
        if self.replaceFilesDialog is None:
            from .FindFileDialog import FindFileDialog
            self.replaceFilesDialog = \
                FindFileDialog(self.project, replaceMode=True)
            self.replaceFilesDialog.sourceFile.connect(
                self.viewmanager.openSourceFile)
            self.replaceFilesDialog.designerFile.connect(self.__designer)
        if searchDir:
            self.replaceFilesDialog.setSearchDirectory(searchDir)
        self.replaceFilesDialog.show(txt)
        if openFiles:
            self.replaceFilesDialog.setOpenFiles()
        self.replaceFilesDialog.raise_()
        self.replaceFilesDialog.activateWindow()
    
    ##########################################################
    ## Below are slots to handle StdOut and StdErr
    ##########################################################
    
    def appendToStdout(self, s):
        """
        Public slot to append text to the stdout log viewer tab.
        
        @param s output to be appended (string)
        """
        self.appendStdout.emit(s)
    
    def appendToStderr(self, s):
        """
        Public slot to append text to the stderr log viewer tab.
        
        @param s output to be appended (string)
        """
        self.appendStderr.emit(s)
    
    ##########################################################
    ## Below are slots needed by the plugin menu
    ##########################################################
    
    def __showPluginInfo(self):
        """
        Private slot to show the plugin info dialog.
        """
        from PluginManager.PluginInfoDialog import PluginInfoDialog
        self.__pluginInfoDialog = PluginInfoDialog(self.pluginManager, self)
        self.__pluginInfoDialog.show()
        
    @pyqtSlot()
    def __installPlugins(self, pluginFileNames=[]):
        """
        Private slot to show a dialog to install a new plugin.
        
        @param pluginFileNames list of plugin files suggested for
            installation list of strings
        """
        from PluginManager.PluginInstallDialog import PluginInstallDialog
        dlg = PluginInstallDialog(self.pluginManager, pluginFileNames, self)
        dlg.exec_()
        if dlg.restartNeeded():
            self.__restart()
        
    def __deinstallPlugin(self):
        """
        Private slot to show a dialog to uninstall a plugin.
        """
        from PluginManager.PluginUninstallDialog import PluginUninstallDialog
        dlg = PluginUninstallDialog(self.pluginManager, self)
        dlg.exec_()
        
    def showPluginsAvailable(self):
        """
        Public slot to show the plugins available for download.
        """
        from PluginManager.PluginRepositoryDialog import PluginRepositoryDialog
        dlg = PluginRepositoryDialog(self)
        res = dlg.exec_()
        if res == (QDialog.Accepted + 1):
            self.__installPlugins(dlg.getDownloadedPlugins())
        
    def __pluginsConfigure(self):
        """
        Private slot to show the plugin manager configuration page.
        """
        self.showPreferences("pluginManagerPage")
        
    def checkPluginUpdatesAvailable(self):
        """
        Public method to check the availability of updates of plug-ins.
        """
        self.pluginManager.checkPluginUpdatesAvailable()
    
    #################################################################
    ## Drag and Drop Support
    #################################################################
    
    def dragEnterEvent(self, event):
        """
        Protected method to handle the drag enter event.
        
        @param event the drag enter event (QDragEnterEvent)
        """
        self.inDragDrop = event.mimeData().hasUrls()
        if self.inDragDrop:
            event.acceptProposedAction()
        
    def dragMoveEvent(self, event):
        """
        Protected method to handle the drag move event.
        
        @param event the drag move event (QDragMoveEvent)
        """
        if self.inDragDrop:
            event.acceptProposedAction()
        
    def dragLeaveEvent(self, event):
        """
        Protected method to handle the drag leave event.
        
        @param event the drag leave event (QDragLeaveEvent)
        """
        if self.inDragDrop:
            self.inDragDrop = False
        
    def dropEvent(self, event):
        """
        Protected method to handle the drop event.
        
        @param event the drop event (QDropEvent)
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            for url in event.mimeData().urls():
                fname = url.toLocalFile()
                if fname:
                    if QFileInfo(fname).isFile():
                        self.viewmanager.openSourceFile(fname)
                    else:
                        E5MessageBox.information(
                            self,
                            self.tr("Drop Error"),
                            self.tr("""<p><b>{0}</b> is not a file.</p>""")
                            .format(fname))
        
        self.inDragDrop = False
    
    ##########################################################
    ## Below are methods needed for shutting down the IDE
    ##########################################################

    def closeEvent(self, event):
        """
        Protected event handler for the close event.
        
        This event handler saves the preferences.
        
        @param event close event (QCloseEvent)
        """
        if self.__shutdown():
            event.accept()
            if not self.inCloseEevent:
                self.inCloseEevent = True
                QTimer.singleShot(0, e5App().closeAllWindows)
        else:
            event.ignore()

    def __shutdown(self):
        """
        Private method to perform all necessary steps to close down the IDE.
        
        @return flag indicating success
        """
        if self.shutdownCalled:
            return True
        
        if self.helpWindow is not None:
            if not self.helpWindow.shutdown():
                return False
        
        if not self.irc.shutdown():
            return False
        
        self.__writeSession()
        
        if not self.project.closeProject():
            return False
        
        if not self.multiProject.closeMultiProject():
            return False
        
        if not self.viewmanager.closeViewManager():
            return False
        
        self.__previewer.shutdown()
        
        self.shell.closeShell()
        
        self.__writeTasks()
        self.templateViewer.save()
        
        if not self.debuggerUI.shutdownServer():
            return False
        self.debuggerUI.shutdown()
        
        self.backgroundService.shutdown()
        
        self.cooperation.shutdown()
        
        self.pluginManager.doShutdown()
        
        if self.layoutType == "Sidebars":
            self.leftSidebar.shutdown()
            self.bottomSidebar.shutdown()
            self.rightSidebar.shutdown()
        
        if self.SAServer is not None:
            self.SAServer.shutdown()
            self.SAServer = None
        
        Preferences.setGeometry("MainMaximized", self.isMaximized())
        if not self.isMaximized():
            Preferences.setGeometry("MainGeometry", self.saveGeometry())
        self.browser.saveToplevelDirs()
        
        Preferences.setUI(
            "ToolbarManagerState", self.toolbarManager.saveState())
        self.__saveCurrentViewProfile(True)
        Preferences.saveToolGroups(self.toolGroups, self.currentToolGroup)
        Preferences.syncPreferences()
        self.shutdownCalled = True
        return True

    ##############################################
    ## Below are methods to check for new versions
    ##############################################

    def showAvailableVersionsInfo(self):
        """
        Public method to show the eric6 versions available for download.
        """
        self.performVersionCheck(manual=True, showVersions=True)
        
    @pyqtSlot()
    def performVersionCheck(self, manual=True, alternative=0,
                            showVersions=False):
        """
        Public method to check the internet for an eric6 update.
        
        @param manual flag indicating an invocation via the menu (boolean)
        @param alternative index of server to download from (integer)
        @keyparam showVersions flag indicating the show versions mode (boolean)
        """
        if not manual:
            if Version.startswith("@@"):
                return
            else:
                period = Preferences.getUI("PerformVersionCheck")
                if period == 0:
                    return
                elif period in [2, 3, 4]:
                    lastCheck = Preferences.Prefs.settings.value(
                        "Updates/LastCheckDate", QDate(1970, 1, 1))
                    if lastCheck.isValid():
                        now = QDate.currentDate()
                        if period == 2 and lastCheck.day() == now.day():
                            # daily
                            return
                        elif period == 3 and lastCheck.daysTo(now) < 7:
                            # weekly
                            return
                        elif period == 4 and (lastCheck.daysTo(now) <
                                              lastCheck.daysInMonth()):
                            # monthly
                            return
        
        self.__inVersionCheck = True
        self.manualUpdatesCheck = manual
        self.showAvailableVersions = showVersions
        self.httpAlternative = alternative
        url = QUrl(self.__httpAlternatives[alternative])
        self.__versionCheckCanceled = False
        if manual:
            if self.__versionCheckProgress is None:
                self.__versionCheckProgress = E5ProgressDialog(
                    "", self.tr("&Cancel"),
                    0, len(self.__httpAlternatives),
                    self.tr("%v/%m"), self)
                self.__versionCheckProgress.setWindowTitle(
                    self.tr("Version Check"))
                self.__versionCheckProgress.setMinimumDuration(0)
                self.__versionCheckProgress.canceled.connect(
                    self.__versionsDownloadCanceled)
            self.__versionCheckProgress.setLabelText(
                self.tr("Trying host {0}").format(url.host()))
            self.__versionCheckProgress.setValue(alternative)
        request = QNetworkRequest(url)
        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute,
                             QNetworkRequest.AlwaysNetwork)
        reply = self.__networkManager.get(request)
        reply.finished.connect(self.__versionsDownloadDone)
        self.__replies.append(reply)
        
    @pyqtSlot()
    def __versionsDownloadDone(self):
        """
        Private slot called, after the versions file has been downloaded
        from the internet.
        """
        if self.__versionCheckCanceled:
            self.__inVersionCheck = False
            if self.__versionCheckProgress is not None:
                self.__versionCheckProgress.reset()
                self.__versionCheckProgress = None
            return
        
        reply = self.sender()
        
        # This is a hack because sometimes reply is not a QNetworkReply
        if not isinstance(reply, QNetworkReply):
            if reply in self.__replies:
                self.__replies.remove(reply)
            return
        
        reply.deleteLater()
        if reply in self.__replies:
            self.__replies.remove(reply)
        if reply.error() == QNetworkReply.NoError:
            ioEncoding = Preferences.getSystem("IOEncoding")
            versions = str(reply.readAll(), ioEncoding, 'replace').splitlines()
        reply.close()
        if reply.error() != QNetworkReply.NoError or \
            len(versions) == 0 or \
                versions[0].startswith("<"):
            # network error or an error page
            self.httpAlternative += 1
            if self.httpAlternative >= len(self.__httpAlternatives):
                self.__inVersionCheck = False
                if self.__versionCheckProgress is not None:
                    self.__versionCheckProgress.reset()
                    self.__versionCheckProgress = None
                firstFailure = Preferences.Prefs.settings.value(
                    "Updates/FirstFailedCheckDate", QDate.currentDate())
                failedDuration = firstFailure.daysTo(QDate.currentDate())
                Preferences.Prefs.settings.setValue(
                    "Updates/FirstFailedCheckDate", firstFailure)
                if self.manualUpdatesCheck:
                    E5MessageBox.warning(
                        self,
                        self.tr("Error getting versions information"),
                        self.tr("""The versions information could not be"""
                                """ downloaded."""
                                """ Please go online and try again."""))
                elif failedDuration > 7:
                    E5MessageBox.warning(
                        self,
                        self.tr("Error getting versions information"),
                        self.tr("""The versions information could not be"""
                                """ downloaded for the last 7 days."""
                                """ Please go online and try again."""))
                return
            else:
                self.performVersionCheck(self.manualUpdatesCheck,
                                         self.httpAlternative,
                                         self.showAvailableVersions)
                return
        
        self.__inVersionCheck = False
        if self.__versionCheckProgress is not None:
            self.__versionCheckProgress.reset()
            self.__versionCheckProgress = None
        self.__updateVersionsUrls(versions)
        if self.showAvailableVersions:
            self.__showAvailableVersionInfos(versions)
        else:
            Preferences.Prefs.settings.remove("Updates/FirstFailedCheckDate")
            Preferences.Prefs.settings.setValue(
                "Updates/LastCheckDate", QDate.currentDate())
            self.__versionCheckResult(versions)
        
    def __updateVersionsUrls(self, versions):
        """
        Private method to update the URLs from which to retrieve the versions
        file.
        
        @param versions contents of the downloaded versions file (list of
            strings)
        """
        if len(versions) > 5 and versions[4] == "---":
            line = 5
            urls = []
            while line < len(versions):
                urls.append(versions[line])
                line += 1
            
            Preferences.setUI("VersionsUrls6", urls)
        
    def __versionCheckResult(self, versions):
        """
        Private method to show the result of the version check action.
        
        @param versions contents of the downloaded versions file (list of
            strings)
        """
        url = ""
        try:
            if "-snapshot-" in Version:
                # check snapshot version
                if versions[2][0] == "6" and versions[2] > Version:
                    res = E5MessageBox.yesNo(
                        self,
                        self.tr("Update available"),
                        self.tr(
                            """The update to <b>{0}</b> of eric6 is"""
                            """ available at <b>{1}</b>. Would you like to"""
                            """ get it?""")
                        .format(versions[2], versions[3]),
                        yesDefault=True)
                    url = res and versions[3] or ''
                elif versions[0] > Version:
                    res = E5MessageBox.yesNo(
                        self,
                        self.tr("Update available"),
                        self.tr(
                            """The update to <b>{0}</b> of eric6 is"""
                            """ available at <b>{1}</b>. Would you like to"""
                            """ get it?""")
                        .format(versions[0], versions[1]),
                        yesDefault=True)
                    url = res and versions[1] or ''
                else:
                    if self.manualUpdatesCheck:
                        E5MessageBox.information(
                            self,
                            self.tr("Eric6 is up to date"),
                            self.tr(
                                """You are using the latest version of"""
                                """ eric6"""))
            else:
                # check release version
                if versions[0] > Version:
                    res = E5MessageBox.yesNo(
                        self,
                        self.tr("Update available"),
                        self.tr(
                            """The update to <b>{0}</b> of eric6 is"""
                            """ available at <b>{1}</b>. Would you like"""
                            """ to get it?""")
                        .format(versions[0], versions[1]),
                        yesDefault=True)
                    url = res and versions[1] or ''
                else:
                    if self.manualUpdatesCheck:
                        E5MessageBox.information(
                            self,
                            self.tr("Eric6 is up to date"),
                            self.tr(
                                """You are using the latest version of"""
                                """ eric6"""))
        except IndexError:
            E5MessageBox.warning(
                self,
                self.tr("Error during updates check"),
                self.tr("""Could not perform updates check."""))
        
        if url:
            QDesktopServices.openUrl(QUrl(url))
        
    @pyqtSlot()
    def __versionsDownloadCanceled(self):
        """
        Private slot called to cancel the version check.
        """
        if self.__replies:
            self.__versionCheckCanceled = True
            self.__replies[-1].abort()
        
    def __showAvailableVersionInfos(self, versions):
        """
        Private method to show the versions available for download.
        
        @param versions contents of the downloaded versions file (list of
            strings)
        """
        versionText = self.tr(
            """<h3>Available versions</h3>"""
            """<table>""")
        line = 0
        while line < len(versions):
            if versions[line] == "---":
                break
            
            versionText += """<tr><td>{0}</td><td><a href="{1}">{2}</a>""" \
                """</td></tr>""".format(
                    versions[line], versions[line + 1],
                    'sourceforge' in versions[line + 1] and
                    "SourceForge" or versions[line + 1])
            line += 2
        versionText += self.tr("""</table>""")
        
        E5MessageBox.about(self, Program, versionText)
        
    def __sslErrors(self, reply, errors):
        """
        Private slot to handle SSL errors.
        
        @param reply reference to the reply object (QNetworkReply)
        @param errors list of SSL errors (list of QSslError)
        """
        ignored = self.__sslErrorHandler.sslErrorsReply(reply, errors)[0]
        if ignored == E5SslErrorHandler.NotIgnored:
            self.__downloadCancelled = True
    
    #######################################
    ## Below are methods for various checks
    #######################################

    def checkConfigurationStatus(self):
        """
        Public method to check, if eric6 has been configured. If it is not,
        the configuration dialog is shown.
        """
        if not Preferences.isConfigured():
            self.__initDebugToolbarsLayout()
            
            E5MessageBox.information(
                self,
                self.tr("First time usage"),
                self.tr("""eric6 has not been configured yet. """
                        """The configuration dialog will be started."""))
            self.showPreferences()
    
    def checkProjectsWorkspace(self):
        """
        Public method to check, if a projects workspace has been configured. If
        it has not, a dialog is shown.
        """
        if not Preferences.isConfigured():
            # eric hasn't been configured at all
            self.checkConfigurationStatus()
        
        workspace = Preferences.getMultiProject("Workspace")
        if workspace == "":
            default = Utilities.getHomeDir()
            workspace = E5FileDialog.getExistingDirectory(
                None,
                self.tr("Select Workspace Directory"),
                default,
                E5FileDialog.Options(E5FileDialog.Option(0)))
            Preferences.setMultiProject("Workspace", workspace)
    
    def versionIsNewer(self, required, snapshot=None):
        """
        Public method to check, if the eric6 version is good compared to
        the required version.
        
        @param required required version (string)
        @param snapshot required snapshot version (string)
        @return flag indicating, that the version is newer than the required
            one (boolean)
        """
        if Version.startswith("@@"):
            # development version, always newer
            return True
        
        if "-snapshot-" in Version:
            # check snapshot version
            if snapshot is None:
                return True
            else:
                vers = Version.split("-snapshot-")[1]
                return vers.split()[0] > snapshot
        
        return Version.split()[0] > required
    
    #################################
    ## Below are some utility methods
    #################################

    def __getFloatingGeometry(self, w):
        """
        Private method to get the geometry of a floating windows.
        
        @param w reference to the widget to be saved (QWidget)
        @return list giving the widget's geometry and its visibility
        """
        s = w.size()
        p = w.pos()
        return [p.x(), p.y(), s.width(), s.height(), not w.isHidden()]
    
    ############################
    ## some event handlers below
    ############################
    
    def showEvent(self, evt):
        """
        Protected method to handle the show event.
        
        @param evt reference to the show event (QShowEvent)
        """
        if self.__startup:
            if Preferences.getGeometry("MainMaximized"):
                self.setWindowState(Qt.WindowStates(Qt.WindowMaximized))
            self.__startup = False
    
    ##########################################
    ## Support for desktop notifications below
    ##########################################
    
    def showNotification(self, icon, heading, text):
        """
        Public method to show a desktop notification.
        
        @param icon icon to be shown in the notification (QPixmap)
        @param heading heading of the notification (string)
        @param text text of the notification (string)
        """
        if Preferences.getUI("NotificationsEnabled"):
            if self.__notification is None:
                from .NotificationWidget import NotificationWidget
                self.__notification = NotificationWidget(parent=self)
            self.__notification.setPixmap(icon)
            self.__notification.setHeading(heading)
            self.__notification.setText(text)
            self.__notification.setTimeout(
                Preferences.getUI("NotificationTimeout"))
            self.__notification.move(Preferences.getUI("NotificationPosition"))
            self.__notification.show()
    
    def notificationsEnabled(self):
        """
        Public method to check, if notifications are enabled.
        
        @return flag indicating, if notifications are enabled (boolean)
        """
        return Preferences.getUI("NotificationsEnabled")
    
    #########################
    ## Support for IRC  below
    #########################
    
    def autoConnectIrc(self):
        """
        Public method to initiate the IRC auto connection.
        """
        self.irc.autoConnect()
    
    def __ircAutoConnected(self):
        """
        Private slot handling the automatic connection of the IRC client.
        """
        self.__activateIRC()
