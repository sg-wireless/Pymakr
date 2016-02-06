# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the editor component of the eric6 IDE.
"""
from __future__ import unicode_literals
try:
    str = unicode
    chr = unichr
except NameError:
    pass

import os
import re
import difflib

from PyQt5.QtCore import QDir, QTimer, QModelIndex, QFileInfo, pyqtSignal, \
    pyqtSlot, QCryptographicHash, QEvent, QDateTime, QRegExp, Qt, qVersion
from PyQt5.QtGui import QCursor, QPalette, QFont, QPixmap, QPainter
from PyQt5.QtWidgets import QLineEdit, QActionGroup, QDialog, QInputDialog, \
    QApplication, QMenu
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QAbstractPrintDialog
from PyQt5.Qsci import QsciScintilla, QsciMacro, QsciStyledText

from E5Gui.E5Application import e5App
from E5Gui import E5FileDialog, E5MessageBox

from .QsciScintillaCompat import QsciScintillaCompat, QSCINTILLA_VERSION
from .EditorMarkerMap import EditorMarkerMap

import Preferences
import Utilities
from Utilities import MouseUtilities

import UI.PixmapCache

EditorAutoCompletionListID = 1
TemplateCompletionListID = 2


class Editor(QsciScintillaCompat):
    """
    Class implementing the editor component of the eric6 IDE.
    
    @signal modificationStatusChanged(bool, QsciScintillaCompat) emitted when
        the modification status has changed
    @signal undoAvailable(bool) emitted to signal the undo availability
    @signal redoAvailable(bool) emitted to signal the redo availability
    @signal cursorChanged(str, int, int) emitted when the cursor position
        was changed
    @signal cursorLineChanged(int) emitted when the cursor line was changed
    @signal editorAboutToBeSaved(str) emitted before the editor is saved
    @signal editorSaved(str) emitted after the editor has been saved
    @signal editorRenamed(str) emitted after the editor got a new name
        (i.e. after a 'Save As')
    @signal captionChanged(str, QsciScintillaCompat) emitted when the caption
        is updated. Typically due to a readOnly attribute change.
    @signal breakpointToggled(QsciScintillaCompat) emitted when a breakpoint
        is toggled
    @signal bookmarkToggled(QsciScintillaCompat) emitted when a bookmark is
        toggled
    @signal syntaxerrorToggled(QsciScintillaCompat) emitted when a syntax error
        was discovered
    @signal autoCompletionAPIsAvailable(bool) emitted after the autocompletion
        function has been configured
    @signal coverageMarkersShown(bool) emitted after the coverage markers have
        been shown or cleared
    @signal taskMarkersUpdated(QsciScintillaCompat) emitted when the task
        markers were updated
    @signal changeMarkersUpdated(QsciScintillaCompat) emitted when the change
        markers were updated
    @signal showMenu(str, QMenu, QsciScintillaCompat) emitted when a menu is
        about to be shown. The name of the menu, a reference to the menu and
        a reference to the editor are given.
    @signal languageChanged(str) emitted when the editors language was set. The
        language is passed as a parameter.
    @signal eolChanged(str) emitted when the editors eol type was set. The eol
        string is passed as a parameter.
    @signal encodingChanged(str) emitted when the editors encoding was set. The
            encoding name is passed as a parameter.
    @signal lastEditPositionAvailable() emitted when a last edit position is
        available
    @signal refreshed() emitted to signal a refresh of the editor contents
    """
    modificationStatusChanged = pyqtSignal(bool, QsciScintillaCompat)
    undoAvailable = pyqtSignal(bool)
    redoAvailable = pyqtSignal(bool)
    cursorChanged = pyqtSignal(str, int, int)
    cursorLineChanged = pyqtSignal(int)
    editorAboutToBeSaved = pyqtSignal(str)
    editorSaved = pyqtSignal(str)
    editorRenamed = pyqtSignal(str)
    captionChanged = pyqtSignal(str, QsciScintillaCompat)
    breakpointToggled = pyqtSignal(QsciScintillaCompat)
    bookmarkToggled = pyqtSignal(QsciScintillaCompat)
    syntaxerrorToggled = pyqtSignal(QsciScintillaCompat)
    autoCompletionAPIsAvailable = pyqtSignal(bool)
    coverageMarkersShown = pyqtSignal(bool)
    taskMarkersUpdated = pyqtSignal(QsciScintillaCompat)
    changeMarkersUpdated = pyqtSignal(QsciScintillaCompat)
    showMenu = pyqtSignal(str, QMenu, QsciScintillaCompat)
    languageChanged = pyqtSignal(str)
    eolChanged = pyqtSignal(str)
    encodingChanged = pyqtSignal(str)
    lastEditPositionAvailable = pyqtSignal()
    refreshed = pyqtSignal()
    
    WarningCode = 1
    WarningStyle = 2
    
    # Autocompletion icon definitions
    ClassID = 1
    ClassProtectedID = 2
    ClassPrivateID = 3
    MethodID = 4
    MethodProtectedID = 5
    MethodPrivateID = 6
    AttributeID = 7
    AttributeProtectedID = 8
    AttributePrivateID = 9
    EnumID = 10
    
    FromDocumentID = 99
    
    TemplateImageID = 100
    
    # Cooperation related definitions
    Separator = "@@@"
    
    StartEditToken = "START_EDIT"
    EndEditToken = "END_EDIT"
    CancelEditToken = "CANCEL_EDIT"
    RequestSyncToken = "REQUEST_SYNC"
    SyncToken = "SYNC"
    
    def __init__(self, dbs, fn=None, vm=None,
                 filetype="", editor=None, tv=None):
        """
        Constructor
        
        @param dbs reference to the debug server object
        @param fn name of the file to be opened (string). If it is None,
                a new (empty) editor is opened
        @param vm reference to the view manager object
            (ViewManager.ViewManager)
        @param filetype type of the source file (string)
        @param editor reference to an Editor object, if this is a cloned view
        @param tv reference to the task viewer object
        @exception IOError raised to indicate an issue accessing the file
        """
        super(Editor, self).__init__()
        self.setAttribute(Qt.WA_KeyCompression)
        self.setUtf8(True)
        
        self.dbs = dbs
        self.taskViewer = tv
        self.fileName = fn
        self.vm = vm
        self.filetype = filetype
        self.filetypeByFlag = False
        self.noName = ""
        self.project = e5App().getObject("Project")
        
        # clear some variables
        self.lastHighlight = None   # remember the last highlighted line
        self.lastErrorMarker = None   # remember the last error line
        self.lastCurrMarker = None   # remember the last current line
        
        self.breaks = {}
        # key:   marker handle,
        # value: (lineno, condition, temporary,
        #         enabled, ignorecount)
        self.bookmarks = []
        # bookmarks are just a list of handles to the
        # bookmark markers
        self.syntaxerrors = {}
        # key:   marker handle
        # value: list of (error message, error index)
        self.warnings = {}
        # key:   marker handle
        # value: list of (warning message, warning type)
        self.notcoveredMarkers = []  # just a list of marker handles
        self.showingNotcoveredMarkers = False
        
        self.condHistory = []
        self.lexer_ = None
        self.__lexerReset = False
        self.completer = None
        self.encoding = Preferences.getEditor("DefaultEncoding")
        self.apiLanguage = ''
        self.lastModified = 0
        self.line = -1
        self.inReopenPrompt = False
        # true if the prompt to reload a changed source is present
        self.inFileRenamed = False
        # true if we are propagating a rename action
        self.inLanguageChanged = False
        # true if we are propagating a language change
        self.inEolChanged = False
        # true if we are propagating an eol change
        self.inEncodingChanged = False
        # true if we are propagating an encoding change
        self.inDragDrop = False
        # true if we are in drop mode
        self.inLinesChanged = False
        # true if we are propagating a lines changed event
        self.__hasTaskMarkers = False
        # no task markers present
            
        self.macros = {}    # list of defined macros
        self.curMacro = None
        self.recording = False
        
        self.acAPI = False
        
        self.__lastEditPosition = None
        self.__annotationLines = 0
        
        # list of clones
        self.__clones = []
        
        # clear QScintilla defined keyboard commands
        # we do our own handling through the view manager
        self.clearAlternateKeys()
        self.clearKeys()
        
        # initialize the mark occurrences timer
        self.__markOccurrencesTimer = QTimer(self)
        self.__markOccurrencesTimer.setSingleShot(True)
        self.__markOccurrencesTimer.setInterval(
            Preferences.getEditor("MarkOccurrencesTimeout"))
        self.__markOccurrencesTimer.timeout.connect(self.__markOccurrences)
        self.__markedText = ""
        self.__searchIndicatorLines = []
        
        # initialize some spellchecking stuff
        self.spell = None
        self.lastLine = 0
        self.lastIndex = 0
        
        # initialize some cooperation stuff
        self.__isSyncing = False
        self.__receivedWhileSyncing = []
        self.__savedText = ""
        self.__inSharedEdit = False
        self.__isShared = False
        self.__inRemoteSharedEdit = False
        
        # connect signals before loading the text
        self.modificationChanged.connect(self.__modificationChanged)
        self.cursorPositionChanged.connect(self.__cursorPositionChanged)
        self.modificationAttempted.connect(self.__modificationReadOnly)
        self.userListActivated.connect(self.__completionListSelected)
        
        # margins layout
        if QSCINTILLA_VERSION() >= 0x020301:
            self.__unifiedMargins = Preferences.getEditor("UnifiedMargins")
        else:
            self.__unifiedMargins = True
        
        # define the margins markers
        self.__changeMarkerSaved = self.markerDefine(
            self.__createChangeMarkerPixmap(
                "OnlineChangeTraceMarkerSaved"))
        self.__changeMarkerUnsaved = self.markerDefine(
            self.__createChangeMarkerPixmap(
                "OnlineChangeTraceMarkerUnsaved"))
        self.breakpoint = \
            self.markerDefine(UI.PixmapCache.getPixmap("break.png"))
        self.cbreakpoint = \
            self.markerDefine(UI.PixmapCache.getPixmap("cBreak.png"))
        self.tbreakpoint = \
            self.markerDefine(UI.PixmapCache.getPixmap("tBreak.png"))
        self.tcbreakpoint = \
            self.markerDefine(UI.PixmapCache.getPixmap("tCBreak.png"))
        self.dbreakpoint = \
            self.markerDefine(UI.PixmapCache.getPixmap("breakDisabled.png"))
        self.bookmark = \
            self.markerDefine(UI.PixmapCache.getPixmap("bookmark16.png"))
        self.syntaxerror = \
            self.markerDefine(UI.PixmapCache.getPixmap("syntaxError.png"))
        self.notcovered = \
            self.markerDefine(UI.PixmapCache.getPixmap("notcovered.png"))
        self.taskmarker = \
            self.markerDefine(UI.PixmapCache.getPixmap("task.png"))
        self.warning = \
            self.markerDefine(UI.PixmapCache.getPixmap("warning.png"))
        
        # define the line markers
        self.currentline = self.markerDefine(QsciScintilla.Background)
        self.errorline = self.markerDefine(QsciScintilla.Background)
        self.__setLineMarkerColours()
        
        self.breakpointMask = (1 << self.breakpoint) | \
                              (1 << self.cbreakpoint) | \
                              (1 << self.tbreakpoint) | \
                              (1 << self.tcbreakpoint) | \
                              (1 << self.dbreakpoint)
        
        self.changeMarkersMask = (1 << self.__changeMarkerSaved) | \
                                 (1 << self.__changeMarkerUnsaved)
        
        self.__markerMap = EditorMarkerMap(self)
        
        # configure the margins
        self.__setMarginsDisplay()
        self.linesChanged.connect(self.__resizeLinenoMargin)
        
        self.marginClicked.connect(self.__marginClicked)
        
        # set the eol mode
        self.__setEolMode()
        
        # set the text display
        self.__setTextDisplay()
        
        # initialize the online syntax check timer
        try:
            self.syntaxCheckService = e5App().getObject('SyntaxCheckService')
            self.syntaxCheckService.syntaxChecked.connect(
                self.__processSyntaxCheckResult)
            self.syntaxCheckService.error.connect(
                self.__processSyntaxCheckError)
            self.__initOnlineSyntaxCheck()
        except KeyError:
            self.syntaxCheckService = None
        
        self.isResourcesFile = False
        if editor is None:
            if self.fileName is not None:
                if (QFileInfo(self.fileName).size() // 1024) > \
                   Preferences.getEditor("WarnFilesize"):
                    res = E5MessageBox.yesNo(
                        self,
                        self.tr("Open File"),
                        self.tr("""<p>The size of the file <b>{0}</b>"""
                                """ is <b>{1} KB</b>."""
                                """ Do you really want to load it?</p>""")
                        .format(self.fileName,
                                QFileInfo(self.fileName).size() // 1024),
                        icon=E5MessageBox.Warning)
                    if not res:
                        raise IOError()
                self.readFile(self.fileName, True)
                self.__bindLexer(self.fileName)
                self.__bindCompleter(self.fileName)
                self.checkSyntax()
                self.isResourcesFile = self.fileName.endswith(".qrc")
                
                self.recolor()
        else:
            # clone the given editor
            self.setDocument(editor.document())
            self.breaks = editor.breaks
            self.bookmarks = editor.bookmarks
            self.syntaxerrors = editor.syntaxerrors
            self.notcoveredMarkers = editor.notcoveredMarkers
            self.showingNotcoveredMarkers = editor.showingNotcoveredMarkers
            self.isResourcesFile = editor.isResourcesFile
            self.lastModified = editor.lastModified
            
            self.addClone(editor)
            editor.addClone(self)
        
        self.gotoLine(1)
        
        # set the text display again
        self.__setTextDisplay()
        
        # set the autocompletion and calltips function
        self.__acHookFunction = None
        self.__completionListHookFunctions = {}
        self.__setAutoCompletion()
        self.__ctHookFunction = None
        self.__ctHookFunctions = {}
        self.__setCallTips()
        
        # set the mouse click handlers (fired on mouse release)
        self.__mouseClickHandlers = {}
        # dictionary with tuple of keyboard modifier and mouse button as key
        # and tuple of plug-in name and function as value
        
        sh = self.sizeHint()
        if sh.height() < 300:
            sh.setHeight(300)
        self.resize(sh)
        
        # Make sure tabbing through a QWorkspace works.
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.__updateReadOnly(True)
        
        self.setWhatsThis(self.tr(
            """<b>A Source Editor Window</b>"""
            """<p>This window is used to display and edit a source file."""
            """  You can open as many of these as you like. The name of the"""
            """ file is displayed in the window's titlebar.</p>"""
            """<p>In order to set breakpoints just click in the space"""
            """ between the line numbers and the fold markers. Via the"""
            """ context menu of the margins they may be edited.</p>"""
            """<p>In order to set bookmarks just Shift click in the space"""
            """ between the line numbers and the fold markers.</p>"""
            """<p>These actions can be reversed via the context menu.</p>"""
            """<p>Ctrl clicking on a syntax error marker shows some info"""
            """ about this error.</p>"""
        ))
        
        # Set the editors size, if it is too big for the view manager.
        if self.vm is not None:
            req = self.size()
            bnd = req.boundedTo(self.vm.size())
            
            if bnd.width() < req.width() or bnd.height() < req.height():
                self.resize(bnd)
            
        # set the autosave flag
        self.autosaveEnabled = Preferences.getEditor("AutosaveInterval") > 0
        self.autosaveManuallyDisabled = False
        
        self.__initContextMenu()
        self.__initContextMenuMargins()
        
        self.__checkEol()
        if editor is None:
            self.__checkLanguage()
            self.__checkEncoding()
        else:
            # it's a clone
            self.__languageChanged(editor.apiLanguage, propagate=False)
            self.__encodingChanged(editor.encoding, propagate=False)
        
        self.setAcceptDrops(True)
        
        # breakpoint handling
        self.breakpointModel = self.dbs.getBreakPointModel()
        self.__restoreBreakpoints()
        self.breakpointModel.rowsAboutToBeRemoved.connect(
            self.__deleteBreakPoints)
        self.breakpointModel.dataAboutToBeChanged.connect(
            self.__breakPointDataAboutToBeChanged)
        self.breakpointModel.dataChanged.connect(
            self.__changeBreakPoints)
        self.breakpointModel.rowsInserted.connect(
            self.__addBreakPoints)
        self.SCN_MODIFIED.connect(self.__modified)
        
        # establish connection to some ViewManager action groups
        self.addActions(self.vm.editorActGrp.actions())
        self.addActions(self.vm.editActGrp.actions())
        self.addActions(self.vm.copyActGrp.actions())
        self.addActions(self.vm.viewActGrp.actions())
        
        # register images to be shown in autocompletion lists
        self.__registerImages()
        
        # connect signals after loading the text
        self.textChanged.connect(self.__textChanged)
        
        # initialize the online change trace timer
        self.__initOnlineChangeTrace()
        
        if self.fileName and \
           self.project.isOpen() and \
           self.project.isProjectSource(self.fileName):
            self.project.projectPropertiesChanged.connect(
                self.__projectPropertiesChanged)
        
        self.grabGesture(Qt.PinchGesture)
        
        self.SCN_ZOOM.connect(self.__markerMap.update)
        self.__markerMap.update()
    
    def __registerImages(self):
        """
        Private method to register images for autocompletion lists.
        """
        self.registerImage(self.ClassID,
                           UI.PixmapCache.getPixmap("class.png"))
        self.registerImage(self.ClassProtectedID,
                           UI.PixmapCache.getPixmap("class_protected.png"))
        self.registerImage(self.ClassPrivateID,
                           UI.PixmapCache.getPixmap("class_private.png"))
        self.registerImage(self.MethodID,
                           UI.PixmapCache.getPixmap("method.png"))
        self.registerImage(self.MethodProtectedID,
                           UI.PixmapCache.getPixmap("method_protected.png"))
        self.registerImage(self.MethodPrivateID,
                           UI.PixmapCache.getPixmap("method_private.png"))
        self.registerImage(self.AttributeID,
                           UI.PixmapCache.getPixmap("attribute.png"))
        self.registerImage(self.AttributeProtectedID,
                           UI.PixmapCache.getPixmap("attribute_protected.png"))
        self.registerImage(self.AttributePrivateID,
                           UI.PixmapCache.getPixmap("attribute_private.png"))
        self.registerImage(self.EnumID,
                           UI.PixmapCache.getPixmap("enum.png"))
        
        self.registerImage(self.FromDocumentID,
                           UI.PixmapCache.getPixmap("editor.png"))
        
        self.registerImage(self.TemplateImageID,
                           UI.PixmapCache.getPixmap("templateViewer.png"))
    
    def addClone(self, editor):
        """
        Public method to add a clone to our list.
        
        @param editor reference to the cloned editor (Editor)
        """
        self.__clones.append(editor)
        
        editor.editorRenamed.connect(self.fileRenamed)
        editor.languageChanged.connect(self.languageChanged)
        editor.eolChanged.connect(self.__eolChanged)
        editor.encodingChanged.connect(self.__encodingChanged)
        
    def removeClone(self, editor):
        """
        Public method to remove a clone from our list.
        
        @param editor reference to the cloned editor (Editor)
        """
        if editor in self.__clones:
            editor.editorRenamed.disconnect(self.fileRenamed)
            editor.languageChanged.disconnect(self.languageChanged)
            editor.eolChanged.disconnect(self.__eolChanged)
            editor.encodingChanged.disconnect(self.__encodingChanged)
            self.__clones.remove(editor)
        
    def __bindName(self, line0):
        """
        Private method to generate a dummy filename for binding a lexer.
        
        @param line0 first line of text to use in the generation process
            (string)
        @return dummy file name to be used for binding a lexer (string)
        """
        bindName = ""
        line0 = line0.lower()
        
        # check first line if it does not start with #!
        if line0.startswith(("<html", "<!doctype html", "<?php")):
            bindName = "dummy.html"
        elif line0.startswith(("<?xml", "<!doctype")):
            bindName = "dummy.xml"
        elif line0.startswith("index: "):
            bindName = "dummy.diff"
        elif line0.startswith("\\documentclass"):
            bindName = "dummy.tex"
        
        # check filetype
        if not bindName and self.filetype:
            if self.filetype in ["Python", "Python2"]:
                bindName = "dummy.py"
            elif self.filetype == "Python3":
                bindName = "dummy.py"
            elif self.filetype == "Ruby":
                bindName = "dummy.rb"
            elif self.filetype == "D":
                bindName = "dummy.d"
            elif self.filetype == "Properties":
                bindName = "dummy.ini"
            elif self.filetype == "JavaScript":
                bindName = "dummy.js"
        
        # #! marker detection
        if not bindName and line0.startswith("#!"):
            if "python3" in line0:
                bindName = "dummy.py"
                self.filetype = "Python3"
            elif "python2" in line0:
                bindName = "dummy.py"
                self.filetype = "Python2"
            elif "python" in line0:
                bindName = "dummy.py"
                self.filetype = "Python2"
            elif ("/bash" in line0 or "/sh" in line0):
                bindName = "dummy.sh"
            elif "ruby" in line0:
                bindName = "dummy.rb"
                self.filetype = "Ruby"
            elif "perl" in line0:
                bindName = "dummy.pl"
            elif "lua" in line0:
                bindName = "dummy.lua"
            elif "dmd" in line0:
                bindName = "dummy.d"
                self.filetype = "D"
        
        if not bindName:
            bindName = self.fileName
        
        return bindName
        
    def getMenu(self, menuName):
        """
        Public method to get a reference to the main context menu or a submenu.
        
        @param menuName name of the menu (string)
        @return reference to the requested menu (QMenu) or None
        """
        try:
            return self.__menus[menuName]
        except KeyError:
            return None
        
    def hasMiniMenu(self):
        """
        Public method to check the miniMenu flag.
        
        @return flag indicating a minimized context menu (boolean)
        """
        return self.miniMenu
        
    def __initContextMenu(self):
        """
        Private method used to setup the context menu.
        """
        self.miniMenu = Preferences.getEditor("MiniContextMenu")
        
        self.menuActs = {}
        self.menu = QMenu()
        self.__menus = {
            "Main": self.menu,
        }
        
        self.languagesMenu = self.__initContextMenuLanguages()
        self.__menus["Languages"] = self.languagesMenu
        if self.isResourcesFile:
            self.resourcesMenu = self.__initContextMenuResources()
            self.__menus["Resources"] = self.resourcesMenu
        else:
            self.checksMenu = self.__initContextMenuChecks()
            self.menuShow = self.__initContextMenuShow()
            self.graphicsMenu = self.__initContextMenuGraphics()
            self.autocompletionMenu = self.__initContextMenuAutocompletion()
            self.__menus["Checks"] = self.checksMenu
            self.__menus["Show"] = self.menuShow
            self.__menus["Graphics"] = self.graphicsMenu
            self.__menus["Autocompletion"] = self.autocompletionMenu
        self.toolsMenu = self.__initContextMenuTools()
        self.__menus["Tools"] = self.toolsMenu
        self.exportersMenu = self.__initContextMenuExporters()
        self.__menus["Exporters"] = self.exportersMenu
        self.eolMenu = self.__initContextMenuEol()
        self.__menus["Eol"] = self.eolMenu
        self.encodingsMenu = self.__initContextMenuEncodings()
        self.__menus["Encodings"] = self.encodingsMenu
        
        self.menuActs["Undo"] = self.menu.addAction(
            UI.PixmapCache.getIcon("editUndo.png"),
            self.tr('Undo'), self.undo)
        self.menuActs["Redo"] = self.menu.addAction(
            UI.PixmapCache.getIcon("editRedo.png"),
            self.tr('Redo'), self.redo)
        self.menuActs["Revert"] = self.menu.addAction(
            self.tr("Revert to last saved state"),
            self.revertToUnmodified)
        self.menu.addSeparator()
        self.menuActs["Cut"] = self.menu.addAction(
            UI.PixmapCache.getIcon("editCut.png"),
            self.tr('Cut'), self.cut)
        self.menuActs["Copy"] = self.menu.addAction(
            UI.PixmapCache.getIcon("editCopy.png"),
            self.tr('Copy'), self.copy)
        self.menu.addAction(
            UI.PixmapCache.getIcon("editPaste.png"),
            self.tr('Paste'), self.paste)
        if not self.miniMenu:
            self.menu.addSeparator()
            self.menu.addAction(
                UI.PixmapCache.getIcon("editIndent.png"),
                self.tr('Indent'), self.indentLineOrSelection)
            self.menu.addAction(
                UI.PixmapCache.getIcon("editUnindent.png"),
                self.tr('Unindent'), self.unindentLineOrSelection)
            self.menuActs["Comment"] = self.menu.addAction(
                UI.PixmapCache.getIcon("editComment.png"),
                self.tr('Comment'), self.commentLineOrSelection)
            self.menuActs["Uncomment"] = self.menu.addAction(
                UI.PixmapCache.getIcon("editUncomment.png"),
                self.tr('Uncomment'), self.uncommentLineOrSelection)
            self.menuActs["StreamComment"] = self.menu.addAction(
                self.tr('Stream Comment'),
                self.streamCommentLineOrSelection)
            self.menuActs["BoxComment"] = self.menu.addAction(
                self.tr('Box Comment'),
                self.boxCommentLineOrSelection)
            self.menu.addSeparator()
            self.menu.addAction(
                self.tr('Select to brace'), self.selectToMatchingBrace)
            self.menu.addAction(self.tr('Select all'), self.__selectAll)
            self.menu.addAction(
                self.tr('Deselect all'), self.__deselectAll)
            self.menu.addSeparator()
        self.menuActs["SpellCheck"] = self.menu.addAction(
            UI.PixmapCache.getIcon("spellchecking.png"),
            self.tr('Check spelling...'), self.checkSpelling)
        self.menuActs["SpellCheckSelection"] = self.menu.addAction(
            UI.PixmapCache.getIcon("spellchecking.png"),
            self.tr('Check spelling of selection...'),
            self.__checkSpellingSelection)
        self.menuActs["SpellCheckRemove"] = self.menu.addAction(
            self.tr("Remove from dictionary"),
            self.__removeFromSpellingDictionary)
        self.menu.addSeparator()
        self.menu.addAction(
            self.tr('Shorten empty lines'), self.shortenEmptyLines)
        self.menu.addSeparator()
        self.menuActs["Languages"] = self.menu.addMenu(self.languagesMenu)
        self.menuActs["Encodings"] = self.menu.addMenu(self.encodingsMenu)
        self.menuActs["Eol"] = self.menu.addMenu(self.eolMenu)
        self.menu.addSeparator()
        self.menuActs["MonospacedFont"] = self.menu.addAction(
            self.tr("Use Monospaced Font"),
            self.handleMonospacedEnable)
        self.menuActs["MonospacedFont"].setCheckable(True)
        self.menuActs["MonospacedFont"].setChecked(self.useMonospaced)
        self.menuActs["AutosaveEnable"] = self.menu.addAction(
            self.tr("Autosave enabled"), self.__autosaveEnable)
        self.menuActs["AutosaveEnable"].setCheckable(True)
        self.menuActs["AutosaveEnable"].setChecked(self.autosaveEnabled)
        self.menuActs["TypingAidsEnabled"] = self.menu.addAction(
            self.tr("Typing aids enabled"), self.__toggleTypingAids)
        self.menuActs["TypingAidsEnabled"].setCheckable(True)
        self.menuActs["TypingAidsEnabled"].setEnabled(
            self.completer is not None)
        self.menuActs["TypingAidsEnabled"].setChecked(
            self.completer is not None and self.completer.isEnabled())
        self.menuActs["AutoCompletionEnable"] = self.menu.addAction(
            self.tr("Automatic Completion enabled"),
            self.__toggleAutoCompletionEnable)
        self.menuActs["AutoCompletionEnable"].setCheckable(True)
        self.menuActs["AutoCompletionEnable"].setChecked(
            self.autoCompletionThreshold() != -1)
        if not self.isResourcesFile:
            self.menu.addMenu(self.autocompletionMenu)
            self.menuActs["calltip"] = self.menu.addAction(
                self.tr('Calltip'), self.callTip)
        self.menu.addSeparator()
        if self.isResourcesFile:
            self.menu.addMenu(self.resourcesMenu)
        else:
            self.menuActs["Check"] = self.menu.addMenu(self.checksMenu)
            self.menu.addSeparator()
            self.menuActs["Show"] = self.menu.addMenu(self.menuShow)
            self.menu.addSeparator()
            self.menuActs["Diagrams"] = self.menu.addMenu(self.graphicsMenu)
        self.menu.addSeparator()
        self.menuActs["Tools"] = self.menu.addMenu(self.toolsMenu)
        self.menu.addSeparator()
        self.menu.addAction(
            UI.PixmapCache.getIcon("documentNewView.png"),
            self.tr('New Document View'), self.__newView)
        self.menuActs["NewSplit"] = self.menu.addAction(
            UI.PixmapCache.getIcon("splitVertical.png"),
            self.tr('New Document View (with new split)'),
            self.__newViewNewSplit)
        self.menuActs["NewSplit"].setEnabled(self.vm.canSplit())
        self.menu.addAction(
            UI.PixmapCache.getIcon("close.png"),
            self.tr('Close'), self.__contextClose)
        self.menu.addSeparator()
        self.reopenEncodingMenu = self.__initContextMenuReopenWithEncoding()
        self.menuActs["Reopen"] = self.menu.addMenu(self.reopenEncodingMenu)
        self.menuActs["Save"] = self.menu.addAction(
            UI.PixmapCache.getIcon("fileSave.png"),
            self.tr('Save'), self.__contextSave)
        self.menu.addAction(
            UI.PixmapCache.getIcon("fileSaveAs.png"),
            self.tr('Save As...'), self.__contextSaveAs)
        self.menu.addAction(
            UI.PixmapCache.getIcon("fileSaveCopy.png"),
            self.tr('Save Copy...'), self.__contextSaveCopy)
        if not self.miniMenu:
            self.menu.addMenu(self.exportersMenu)
            self.menu.addSeparator()
            self.menuActs["OpenRejections"] = self.menu.addAction(
                self.tr("Open 'rejection' file"),
                self.__contextOpenRejections)
            self.menu.addSeparator()
            self.menu.addAction(
                UI.PixmapCache.getIcon("printPreview.png"),
                self.tr("Print Preview"), self.printPreviewFile)
            self.menu.addAction(
                UI.PixmapCache.getIcon("print.png"),
                self.tr('Print'), self.printFile)
        else:
            self.menuActs["OpenRejections"] = None
        
        self.menu.aboutToShow.connect(self.__showContextMenu)
        
        self.spellingMenu = QMenu()
        self.__menus["Spelling"] = self.spellingMenu
        
        self.spellingMenu.aboutToShow.connect(self.__showContextMenuSpelling)
        self.spellingMenu.triggered.connect(
            self.__contextMenuSpellingTriggered)

    def __initContextMenuAutocompletion(self):
        """
        Private method used to setup the Checks context sub menu.
        
        @return reference to the generated menu (QMenu)
        """
        menu = QMenu(self.tr('Complete'))
        
        self.menuActs["acDynamic"] = menu.addAction(
            self.tr('dynamic'), self.autoComplete)
        menu.addSeparator()
        menu.addAction(
            self.tr('from Document'), self.autoCompleteFromDocument)
        self.menuActs["acAPI"] = menu.addAction(
            self.tr('from APIs'), self.autoCompleteFromAPIs)
        self.menuActs["acAPIDocument"] = menu.addAction(
            self.tr('from Document and APIs'), self.autoCompleteFromAll)
        
        menu.aboutToShow.connect(self.__showContextMenuAutocompletion)
        
        return menu

    def __initContextMenuChecks(self):
        """
        Private method used to setup the Checks context sub menu.
        
        @return reference to the generated menu (QMenu)
        """
        menu = QMenu(self.tr('Check'))
        menu.aboutToShow.connect(self.__showContextMenuChecks)
        return menu

    def __initContextMenuTools(self):
        """
        Private method used to setup the Tools context sub menu.
        
        @return reference to the generated menu (QMenu)
        """
        menu = QMenu(self.tr('Tools'))
        menu.aboutToShow.connect(self.__showContextMenuTools)
        return menu

    def __initContextMenuShow(self):
        """
        Private method used to setup the Show context sub menu.
        
        @return reference to the generated menu (QMenu)
        """
        menu = QMenu(self.tr('Show'))
        
        menu.addAction(self.tr('Code metrics...'), self.__showCodeMetrics)
        self.coverageMenuAct = menu.addAction(
            self.tr('Code coverage...'), self.__showCodeCoverage)
        self.coverageShowAnnotationMenuAct = menu.addAction(
            self.tr('Show code coverage annotations'),
            self.codeCoverageShowAnnotations)
        self.coverageHideAnnotationMenuAct = menu.addAction(
            self.tr('Hide code coverage annotations'),
            self.__codeCoverageHideAnnotations)
        self.profileMenuAct = menu.addAction(
            self.tr('Profile data...'), self.__showProfileData)
        
        menu.aboutToShow.connect(self.__showContextMenuShow)
        
        return menu
        
    def __initContextMenuGraphics(self):
        """
        Private method used to setup the diagrams context sub menu.
        
        @return reference to the generated menu (QMenu)
        """
        menu = QMenu(self.tr('Diagrams'))
        
        menu.addAction(
            self.tr('Class Diagram...'), self.__showClassDiagram)
        menu.addAction(
            self.tr('Package Diagram...'), self.__showPackageDiagram)
        menu.addAction(
            self.tr('Imports Diagram...'), self.__showImportsDiagram)
        self.applicationDiagramMenuAct = menu.addAction(
            self.tr('Application Diagram...'),
            self.__showApplicationDiagram)
        menu.addSeparator()
        menu.addAction(
            UI.PixmapCache.getIcon("open.png"),
            self.tr("Load Diagram..."), self.__loadDiagram)
        
        menu.aboutToShow.connect(self.__showContextMenuGraphics)
        
        return menu

    def __initContextMenuLanguages(self):
        """
        Private method used to setup the Languages context sub menu.
        
        @return reference to the generated menu (QMenu)
        """
        menu = QMenu(self.tr("Languages"))
        
        self.languagesActGrp = QActionGroup(self)
        self.noLanguageAct = menu.addAction(self.tr("No Language"))
        self.noLanguageAct.setCheckable(True)
        self.noLanguageAct.setData("None")
        self.languagesActGrp.addAction(self.noLanguageAct)
        menu.addSeparator()
        
        from . import Lexers
        self.supportedLanguages = {}
        supportedLanguages = Lexers.getSupportedLanguages()
        languages = sorted(list(supportedLanguages.keys()))
        for language in languages:
            if language != "Guessed":
                self.supportedLanguages[language] = \
                    supportedLanguages[language][:2]
                act = menu.addAction(
                    UI.PixmapCache.getIcon(supportedLanguages[language][2]),
                    self.supportedLanguages[language][0])
                act.setCheckable(True)
                act.setData(language)
                self.supportedLanguages[language].append(act)
                self.languagesActGrp.addAction(act)
        
        menu.addSeparator()
        self.pygmentsAct = menu.addAction(self.tr("Guessed"))
        self.pygmentsAct.setCheckable(True)
        self.pygmentsAct.setData("Guessed")
        self.languagesActGrp.addAction(self.pygmentsAct)
        self.pygmentsSelAct = menu.addAction(self.tr("Alternatives"))
        self.pygmentsSelAct.setData("Alternatives")
        
        menu.triggered.connect(self.__languageMenuTriggered)
        menu.aboutToShow.connect(self.__showContextMenuLanguages)
        
        return menu
        
    def __initContextMenuEncodings(self):
        """
        Private method used to setup the Encodings context sub menu.
        
        @return reference to the generated menu (QMenu)
        """
        self.supportedEncodings = {}
        
        menu = QMenu(self.tr("Encodings"))
        
        self.encodingsActGrp = QActionGroup(self)
        
        for encoding in sorted(Utilities.supportedCodecs):
            act = menu.addAction(encoding)
            act.setCheckable(True)
            act.setData(encoding)
            self.supportedEncodings[encoding] = act
            self.encodingsActGrp.addAction(act)
        
        menu.triggered.connect(self.__encodingsMenuTriggered)
        menu.aboutToShow.connect(self.__showContextMenuEncodings)
        
        return menu
        
    def __initContextMenuReopenWithEncoding(self):
        """
        Private method used to setup the Reopen With Encoding context sub menu.
        
        @return reference to the generated menu (QMenu)
        """
        menu = QMenu(self.tr("Re-Open With Encoding"))
        menu.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        for encoding in sorted(Utilities.supportedCodecs):
            act = menu.addAction(encoding)
            act.setData(encoding)
        
        menu.triggered.connect(self.__reopenWithEncodingMenuTriggered)
        
        return menu
        
    def __initContextMenuEol(self):
        """
        Private method to setup the eol context sub menu.
        
        @return reference to the generated menu (QMenu)
        """
        self.supportedEols = {}
        
        menu = QMenu(self.tr("End-of-Line Type"))
        
        self.eolActGrp = QActionGroup(self)
        
        act = menu.addAction(UI.PixmapCache.getIcon("eolLinux.png"),
                             self.tr("Unix"))
        act.setCheckable(True)
        act.setData('\n')
        self.supportedEols['\n'] = act
        self.eolActGrp.addAction(act)
        
        act = menu.addAction(UI.PixmapCache.getIcon("eolWindows.png"),
                             self.tr("Windows"))
        act.setCheckable(True)
        act.setData('\r\n')
        self.supportedEols['\r\n'] = act
        self.eolActGrp.addAction(act)
        
        act = menu.addAction(UI.PixmapCache.getIcon("eolMac.png"),
                             self.tr("Macintosh"))
        act.setCheckable(True)
        act.setData('\r')
        self.supportedEols['\r'] = act
        self.eolActGrp.addAction(act)
        
        menu.triggered.connect(self.__eolMenuTriggered)
        menu.aboutToShow.connect(self.__showContextMenuEol)
        
        return menu
        
    def __initContextMenuExporters(self):
        """
        Private method used to setup the Exporters context sub menu.
        
        @return reference to the generated menu (QMenu)
        """
        menu = QMenu(self.tr("Export as"))
        
        from . import Exporters
        supportedExporters = Exporters.getSupportedFormats()
        exporters = sorted(list(supportedExporters.keys()))
        for exporter in exporters:
            act = menu.addAction(supportedExporters[exporter])
            act.setData(exporter)
        
        menu.triggered.connect(self.__exportMenuTriggered)
        
        return menu
        
    def __initContextMenuMargins(self):
        """
        Private method used to setup the context menu for the margins.
        """
        self.marginMenuActs = {}
        
        if self.__unifiedMargins:
            self.__initContextMenuUnifiedMargins()
        else:
            self.__initContextMenuSeparateMargins()
        
    def __initContextMenuSeparateMargins(self):
        """
        Private method used to setup the context menu for the separated
        margins.
        """
        # bookmark margin
        self.bmMarginMenu = QMenu()
        
        self.bmMarginMenu.addAction(
            self.tr('Toggle bookmark'), self.menuToggleBookmark)
        self.marginMenuActs["NextBookmark"] = self.bmMarginMenu.addAction(
            self.tr('Next bookmark'), self.nextBookmark)
        self.marginMenuActs["PreviousBookmark"] = self.bmMarginMenu.addAction(
            self.tr('Previous bookmark'), self.previousBookmark)
        self.marginMenuActs["ClearBookmark"] = self.bmMarginMenu.addAction(
            self.tr('Clear all bookmarks'), self.clearBookmarks)
        
        self.bmMarginMenu.aboutToShow.connect(self.__showContextMenuMargin)
        
        # breakpoint margin
        self.bpMarginMenu = QMenu()
        
        self.marginMenuActs["Breakpoint"] = self.bpMarginMenu.addAction(
            self.tr('Toggle breakpoint'), self.menuToggleBreakpoint)
        self.marginMenuActs["TempBreakpoint"] = self.bpMarginMenu.addAction(
            self.tr('Toggle temporary breakpoint'),
            self.__menuToggleTemporaryBreakpoint)
        self.marginMenuActs["EditBreakpoint"] = self.bpMarginMenu.addAction(
            self.tr('Edit breakpoint...'), self.menuEditBreakpoint)
        self.marginMenuActs["EnableBreakpoint"] = self.bpMarginMenu.addAction(
            self.tr('Enable breakpoint'),
            self.__menuToggleBreakpointEnabled)
        self.marginMenuActs["NextBreakpoint"] = self.bpMarginMenu.addAction(
            self.tr('Next breakpoint'), self.menuNextBreakpoint)
        self.marginMenuActs["PreviousBreakpoint"] = \
            self.bpMarginMenu.addAction(
                self.tr('Previous breakpoint'),
                self.menuPreviousBreakpoint)
        self.marginMenuActs["ClearBreakpoint"] = self.bpMarginMenu.addAction(
            self.tr('Clear all breakpoints'), self.__menuClearBreakpoints)
        
        self.bpMarginMenu.aboutToShow.connect(self.__showContextMenuMargin)
        
        # indicator margin
        self.indicMarginMenu = QMenu()
        
        self.marginMenuActs["GotoSyntaxError"] = \
            self.indicMarginMenu.addAction(
                self.tr('Goto syntax error'), self.gotoSyntaxError)
        self.marginMenuActs["ShowSyntaxError"] = \
            self.indicMarginMenu.addAction(
                self.tr('Show syntax error message'),
                self.__showSyntaxError)
        self.marginMenuActs["ClearSyntaxError"] = \
            self.indicMarginMenu.addAction(
                self.tr('Clear syntax error'), self.clearSyntaxError)
        self.indicMarginMenu.addSeparator()
        self.marginMenuActs["NextWarningMarker"] = \
            self.indicMarginMenu.addAction(
                self.tr("Next warning"), self.nextWarning)
        self.marginMenuActs["PreviousWarningMarker"] = \
            self.indicMarginMenu.addAction(
                self.tr("Previous warning"), self.previousWarning)
        self.marginMenuActs["ShowWarning"] = \
            self.indicMarginMenu.addAction(
                self.tr('Show warning message'), self.__showWarning)
        self.marginMenuActs["ClearWarnings"] = \
            self.indicMarginMenu.addAction(
                self.tr('Clear warnings'), self.clearWarnings)
        self.indicMarginMenu.addSeparator()
        self.marginMenuActs["NextCoverageMarker"] = \
            self.indicMarginMenu.addAction(
                self.tr('Next uncovered line'), self.nextUncovered)
        self.marginMenuActs["PreviousCoverageMarker"] = \
            self.indicMarginMenu.addAction(
                self.tr('Previous uncovered line'), self.previousUncovered)
        self.indicMarginMenu.addSeparator()
        self.marginMenuActs["NextTaskMarker"] = \
            self.indicMarginMenu.addAction(
                self.tr('Next task'), self.nextTask)
        self.marginMenuActs["PreviousTaskMarker"] = \
            self.indicMarginMenu.addAction(
                self.tr('Previous task'), self.previousTask)
        self.indicMarginMenu.addSeparator()
        self.marginMenuActs["NextChangeMarker"] = \
            self.indicMarginMenu.addAction(
                self.tr('Next change'), self.nextChange)
        self.marginMenuActs["PreviousChangeMarker"] = \
            self.indicMarginMenu.addAction(
                self.tr('Previous change'), self.previousChange)
        
        self.indicMarginMenu.aboutToShow.connect(self.__showContextMenuMargin)
        
    def __initContextMenuUnifiedMargins(self):
        """
        Private method used to setup the context menu for the unified margins.
        """
        self.marginMenu = QMenu()
        
        self.marginMenu.addAction(
            self.tr('Toggle bookmark'), self.menuToggleBookmark)
        self.marginMenuActs["NextBookmark"] = self.marginMenu.addAction(
            self.tr('Next bookmark'), self.nextBookmark)
        self.marginMenuActs["PreviousBookmark"] = self.marginMenu.addAction(
            self.tr('Previous bookmark'), self.previousBookmark)
        self.marginMenuActs["ClearBookmark"] = self.marginMenu.addAction(
            self.tr('Clear all bookmarks'), self.clearBookmarks)
        self.marginMenu.addSeparator()
        self.marginMenuActs["GotoSyntaxError"] = self.marginMenu.addAction(
            self.tr('Goto syntax error'), self.gotoSyntaxError)
        self.marginMenuActs["ShowSyntaxError"] = self.marginMenu.addAction(
            self.tr('Show syntax error message'), self.__showSyntaxError)
        self.marginMenuActs["ClearSyntaxError"] = self.marginMenu.addAction(
            self.tr('Clear syntax error'), self.clearSyntaxError)
        self.marginMenu.addSeparator()
        self.marginMenuActs["NextWarningMarker"] = self.marginMenu.addAction(
            self.tr("Next warning"), self.nextWarning)
        self.marginMenuActs["PreviousWarningMarker"] = \
            self.marginMenu.addAction(
                self.tr("Previous warning"), self.previousWarning)
        self.marginMenuActs["ShowWarning"] = self.marginMenu.addAction(
            self.tr('Show warning message'), self.__showWarning)
        self.marginMenuActs["ClearWarnings"] = self.marginMenu.addAction(
            self.tr('Clear warnings'), self.clearWarnings)
        self.marginMenu.addSeparator()
        self.marginMenuActs["Breakpoint"] = self.marginMenu.addAction(
            self.tr('Toggle breakpoint'), self.menuToggleBreakpoint)
        self.marginMenuActs["TempBreakpoint"] = self.marginMenu.addAction(
            self.tr('Toggle temporary breakpoint'),
            self.__menuToggleTemporaryBreakpoint)
        self.marginMenuActs["EditBreakpoint"] = self.marginMenu.addAction(
            self.tr('Edit breakpoint...'), self.menuEditBreakpoint)
        self.marginMenuActs["EnableBreakpoint"] = self.marginMenu.addAction(
            self.tr('Enable breakpoint'),
            self.__menuToggleBreakpointEnabled)
        self.marginMenuActs["NextBreakpoint"] = self.marginMenu.addAction(
            self.tr('Next breakpoint'), self.menuNextBreakpoint)
        self.marginMenuActs["PreviousBreakpoint"] = self.marginMenu.addAction(
            self.tr('Previous breakpoint'), self.menuPreviousBreakpoint)
        self.marginMenuActs["ClearBreakpoint"] = self.marginMenu.addAction(
            self.tr('Clear all breakpoints'), self.__menuClearBreakpoints)
        self.marginMenu.addSeparator()
        self.marginMenuActs["NextCoverageMarker"] = self.marginMenu.addAction(
            self.tr('Next uncovered line'), self.nextUncovered)
        self.marginMenuActs["PreviousCoverageMarker"] = \
            self.marginMenu.addAction(
                self.tr('Previous uncovered line'), self.previousUncovered)
        self.marginMenu.addSeparator()
        self.marginMenuActs["NextTaskMarker"] = self.marginMenu.addAction(
            self.tr('Next task'), self.nextTask)
        self.marginMenuActs["PreviousTaskMarker"] = self.marginMenu.addAction(
            self.tr('Previous task'), self.previousTask)
        self.marginMenu.addSeparator()
        self.marginMenuActs["NextChangeMarker"] = self.marginMenu.addAction(
            self.tr('Next change'), self.nextChange)
        self.marginMenuActs["PreviousChangeMarker"] = \
            self.marginMenu.addAction(
                self.tr('Previous change'), self.previousChange)
        self.marginMenu.addSeparator()
        self.marginMenuActs["LMBbookmarks"] = self.marginMenu.addAction(
            self.tr('LMB toggles bookmarks'), self.__lmBbookmarks)
        self.marginMenuActs["LMBbookmarks"].setCheckable(True)
        self.marginMenuActs["LMBbookmarks"].setChecked(False)
        self.marginMenuActs["LMBbreakpoints"] = self.marginMenu.addAction(
            self.tr('LMB toggles breakpoints'), self.__lmBbreakpoints)
        self.marginMenuActs["LMBbreakpoints"].setCheckable(True)
        self.marginMenuActs["LMBbreakpoints"].setChecked(True)
        
        self.marginMenu.aboutToShow.connect(self.__showContextMenuMargin)
        
    def __exportMenuTriggered(self, act):
        """
        Private method to handle the selection of an export format.
        
        @param act reference to the action that was triggered (QAction)
        """
        exporterFormat = act.data()
        self.exportFile(exporterFormat)
        
    def exportFile(self, exporterFormat):
        """
        Public method to export the file.
        
        @param exporterFormat format the file should be exported into (string)
        """
        if exporterFormat:
            from . import Exporters
            exporter = Exporters.getExporter(exporterFormat, self)
            if exporter:
                exporter.exportSource()
            else:
                E5MessageBox.critical(
                    self,
                    self.tr("Export source"),
                    self.tr(
                        """<p>No exporter available for the """
                        """export format <b>{0}</b>. Aborting...</p>""")
                    .format(exporterFormat))
        else:
            E5MessageBox.critical(
                self,
                self.tr("Export source"),
                self.tr("""No export format given. Aborting..."""))
        
    def __showContextMenuLanguages(self):
        """
        Private slot handling the aboutToShow signal of the languages context
        menu.
        """
        if self.apiLanguage.startswith("Pygments|"):
            self.pygmentsSelAct.setText(
                self.tr("Alternatives ({0})").format(
                    self.getLanguage(normalized=False)))
        else:
            self.pygmentsSelAct.setText(self.tr("Alternatives"))
        self.showMenu.emit("Languages", self.languagesMenu, self)
        
    def __selectPygmentsLexer(self):
        """
        Private method to select a specific pygments lexer.
        
        @return name of the selected pygments lexer (string)
        """
        from pygments.lexers import get_all_lexers
        lexerList = sorted([l[0] for l in get_all_lexers()])
        try:
            lexerSel = lexerList.index(
                self.getLanguage(normalized=False, forPygments=True))
        except ValueError:
            lexerSel = 0
        lexerName, ok = QInputDialog.getItem(
            self,
            self.tr("Pygments Lexer"),
            self.tr("Select the Pygments lexer to apply."),
            lexerList,
            lexerSel,
            False)
        if ok and lexerName:
            return lexerName
        else:
            return ""
        
    def __languageMenuTriggered(self, act):
        """
        Private method to handle the selection of a lexer language.
        
        @param act reference to the action that was triggered (QAction)
        """
        if act == self.noLanguageAct:
            self.__resetLanguage()
        elif act == self.pygmentsAct:
            self.setLanguage("dummy.pygments")
        elif act == self.pygmentsSelAct:
            language = self.__selectPygmentsLexer()
            if language:
                self.setLanguage("dummy.pygments", pyname=language)
        else:
            language = act.data()
            if language:
                self.filetype = language
                self.setLanguage(self.supportedLanguages[language][1])
                self.checkSyntax()
        
    def __languageChanged(self, language, propagate=True):
        """
        Private slot handling a change of a connected editor's language.
        
        @param language language to be set (string)
        @keyparam propagate flag indicating to propagate the change (boolean)
        """
        if language == '':
            self.__resetLanguage(propagate=propagate)
        elif language == "Guessed":
            self.setLanguage("dummy.pygments")
        elif language.startswith("Pygments|"):
            pyname = language.split("|", 1)[1]
            self.setLanguage("dummy.pygments", pyname=pyname)
        else:
            self.filetype = language
            self.setLanguage(self.supportedLanguages[language][1],
                             propagate=propagate)
            self.checkSyntax()
        
    def __resetLanguage(self, propagate=True):
        """
        Private method used to reset the language selection.
        
        @keyparam propagate flag indicating to propagate the change (boolean)
        """
        if self.lexer_ is not None and \
           (self.lexer_.lexer() == "container" or self.lexer_.lexer() is None):
            self.SCN_STYLENEEDED.disconnect(self.__styleNeeded)
        
        self.apiLanguage = ""
        self.lexer_ = None
        self.__lexerReset = True
        self.setLexer()
        if self.completer is not None:
            self.completer.setEnabled(False)
            self.completer = None
        useMonospaced = self.useMonospaced
        self.__setTextDisplay()
        self.setMonospaced(useMonospaced)
        self.menuActs["MonospacedFont"].setChecked(self.useMonospaced)
        
        if not self.inLanguageChanged and propagate:
            self.inLanguageChanged = True
            self.languageChanged.emit(self.apiLanguage)
            self.inLanguageChanged = False
        
    def setLanguage(self, filename, initTextDisplay=True, propagate=True,
                    pyname=""):
        """
        Public method to set a lexer language.
        
        @param filename filename used to determine the associated lexer
            language (string)
        @param initTextDisplay flag indicating an initialization of the text
            display is required as well (boolean)
        @keyparam propagate flag indicating to propagate the change (boolean)
        @keyparam pyname name of the pygments lexer to use (string)
        """
        self.menuActs["MonospacedFont"].setChecked(False)
        
        self.__lexerReset = False
        self.__bindLexer(filename, pyname=pyname)
        self.__bindCompleter(filename)
        self.recolor()
        self.__checkLanguage()
        
        # set the text display
        if initTextDisplay:
            self.__setTextDisplay()
        
        # set the autocompletion and calltips function
        self.__setAutoCompletion()
        self.__setCallTips()
        
        if not self.inLanguageChanged and propagate:
            self.inLanguageChanged = True
            self.languageChanged.emit(self.apiLanguage)
            self.inLanguageChanged = False
    
    def __checkLanguage(self):
        """
        Private method to check the selected language of the language submenu.
        """
        if self.apiLanguage == "":
            self.noLanguageAct.setChecked(True)
        elif self.apiLanguage == "Guessed":
            self.pygmentsAct.setChecked(True)
        elif self.apiLanguage.startswith("Pygments|"):
            act = self.languagesActGrp.checkedAction()
            if act:
                act.setChecked(False)
        else:
            self.supportedLanguages[self.apiLanguage][2].setChecked(True)
    
    def projectLexerAssociationsChanged(self):
        """
        Public slot to handle changes of the project lexer associations.
        """
        self.setLanguage(self.fileName)
    
    def __showContextMenuEncodings(self):
        """
        Private slot handling the aboutToShow signal of the encodings context
        menu.
        """
        self.showMenu.emit("Encodings", self.encodingsMenu, self)
        
    def __encodingsMenuTriggered(self, act):
        """
        Private method to handle the selection of an encoding.
        
        @param act reference to the action that was triggered (QAction)
        """
        encoding = act.data()
        self.setModified(True)
        self.__encodingChanged("{0}-selected".format(encoding))
        
    def __checkEncoding(self):
        """
        Private method to check the selected encoding of the encodings submenu.
        """
        try:
            self.supportedEncodings[self.__normalizedEncoding()]\
                .setChecked(True)
        except (AttributeError, KeyError):
            pass
        
    def __encodingChanged(self, encoding, propagate=True):
        """
        Private slot to handle a change of the encoding.
        
        @param encoding changed encoding (string)
        @keyparam propagate flag indicating to propagate the change (boolean)
        """
        self.encoding = encoding
        self.__checkEncoding()
        
        if not self.inEncodingChanged and propagate:
            self.inEncodingChanged = True
            self.encodingChanged.emit(self.encoding)
            self.inEncodingChanged = False
        
    def __normalizedEncoding(self, encoding=""):
        """
        Private method to calculate the normalized encoding string.
        
        @param encoding encoding to be normalized (string)
        @return normalized encoding (string)
        """
        if not encoding:
            encoding = self.encoding
        return encoding.replace("-default", "")\
                       .replace("-guessed", "")\
                       .replace("-selected", "")
        
    def __showContextMenuEol(self):
        """
        Private slot handling the aboutToShow signal of the eol context menu.
        """
        self.showMenu.emit("Eol", self.eolMenu, self)
        
    def __eolMenuTriggered(self, act):
        """
        Private method to handle the selection of an eol type.
        
        @param act reference to the action that was triggered (QAction)
        """
        eol = act.data()
        self.setEolModeByEolString(eol)
        self.convertEols(self.eolMode())
        
    def __checkEol(self):
        """
        Private method to check the selected eol type of the eol submenu.
        """
        try:
            self.supportedEols[self.getLineSeparator()].setChecked(True)
        except (AttributeError, TypeError):
            pass
        
    def __eolChanged(self):
        """
        Private slot to handle a change of the eol mode.
        """
        self.__checkEol()
        
        if not self.inEolChanged:
            self.inEolChanged = True
            eol = self.getLineSeparator()
            self.eolChanged.emit(eol)
            self.inEolChanged = False
        
    def __bindLexer(self, filename, pyname=""):
        """
        Private slot to set the correct lexer depending on language.
        
        @param filename filename used to determine the associated lexer
            language (string)
        @keyparam pyname name of the pygments lexer to use (string)
        """
        if self.lexer_ is not None and \
           (self.lexer_.lexer() == "container" or self.lexer_.lexer() is None):
            self.SCN_STYLENEEDED.disconnect(self.__styleNeeded)
        
        language = ""
        if not self.filetype:
            if filename:
                basename = os.path.basename(filename)
                if self.project.isOpen() and \
                        self.project.isProjectFile(filename):
                    language = self.project.getEditorLexerAssoc(basename)
                if not language:
                    language = Preferences.getEditorLexerAssoc(basename)
            if not language:
                bindName = self.__bindName(self.text(0))
                if bindName:
                    language = Preferences.getEditorLexerAssoc(bindName)
            if language == "Python":
                # correction for Python
                pyVer = Utilities.determinePythonVersion(
                    filename, self.text(0), self)
                language = "Python{0}".format(pyVer)
            if language in ['Python2', 'Python3', 'Ruby', 'JavaScript']:
                self.filetype = language
            else:
                self.filetype = ""
        else:
            language = self.filetype
        
        if language.startswith("Pygments|"):
            pyname = language.split("|", 1)[1]
            language = ""
        
        from . import Lexers
        self.lexer_ = Lexers.getLexer(language, self, pyname=pyname)
        if self.lexer_ is None:
            self.setLexer()
            self.apiLanguage = ""
            return
        
        if pyname:
            self.apiLanguage = "Pygments|{0}".format(pyname)
        else:
            # Change API language for lexer where QScintilla reports
            # an abbreviated name.
            self.apiLanguage = self.lexer_.language()
            if self.apiLanguage == "POV":
                self.apiLanguage = "Povray"
            elif self.apiLanguage == "PO":
                self.apiLanguage = "Gettext"
        self.setLexer(self.lexer_)
        self.__setMarginsDisplay()
        if self.lexer_.lexer() == "container" or self.lexer_.lexer() is None:
            self.setStyleBits(self.lexer_.styleBitsNeeded())
            self.SCN_STYLENEEDED.connect(self.__styleNeeded)
        
        # get the font for style 0 and set it as the default font
        key = 'Scintilla/{0}/style0/font'.format(self.lexer_.language())
        fdesc = Preferences.Prefs.settings.value(key)
        if fdesc is not None:
            font = QFont(fdesc[0], int(fdesc[1]))
            self.lexer_.setDefaultFont(font)
        self.lexer_.readSettings(Preferences.Prefs.settings, "Scintilla")
        
        # now set the lexer properties
        self.lexer_.initProperties()
        
        # initialize the lexer APIs settings
        api = self.vm.getAPIsManager().getAPIs(self.apiLanguage)
        if api is not None and not api.isEmpty():
            self.lexer_.setAPIs(api.getQsciAPIs())
            self.acAPI = True
        else:
            self.acAPI = False
        self.autoCompletionAPIsAvailable.emit(self.acAPI)
        
        self.__setAnnotationStyles()
        
        self.lexer_.setDefaultColor(self.lexer_.color(0))
        self.lexer_.setDefaultPaper(self.lexer_.paper(0))
        
    def __styleNeeded(self, position):
        """
        Private slot to handle the need for more styling.
        
        @param position end position, that needs styling (integer)
        """
        self.lexer_.styleText(self.getEndStyled(), position)
        
    def getLexer(self):
        """
        Public method to retrieve a reference to the lexer object.
        
        @return the lexer object (Lexer)
        """
        return self.lexer_
        
    def getLanguage(self, normalized=True, forPygments=False):
        """
        Public method to retrieve the language of the editor.
        
        @keyparam normalized flag indicating to normalize some Pygments
            lexer names (boolean)
        @keyparam forPygments flag indicating to normalize some lexer
            names for Pygments (boolean)
        @return language of the editor (string)
        """
        if self.apiLanguage == "Guessed" or \
                self.apiLanguage.startswith("Pygments|"):
            lang = self.lexer_.name()
            if normalized:
                # adjust some Pygments lexer names
                if lang == "Python":
                    lang = "Python2"
                elif lang == "Python 3":
                    lang = "Python3"
        else:
            lang = self.apiLanguage
            if forPygments:
                # adjust some names to Pygments lexer names
                if lang == "Python2":
                    lang = "Python"
                elif lang == "Python3":
                    lang = "Python 3"
        return lang
        
    def __bindCompleter(self, filename):
        """
        Private slot to set the correct typing completer depending on language.
        
        @param filename filename used to determine the associated typing
            completer language (string)
        """
        if self.completer is not None:
            self.completer.setEnabled(False)
            self.completer = None
        
        filename = os.path.basename(filename)
        apiLanguage = Preferences.getEditorLexerAssoc(filename)
        if apiLanguage == "":
            pyVer = self.__getPyVersion()
            if pyVer:
                apiLanguage = "Python{0}".format(pyVer)
            elif self.isRubyFile():
                apiLanguage = "Ruby"
        
        from . import TypingCompleters
        self.completer = TypingCompleters.getCompleter(apiLanguage, self)
        
    def getCompleter(self):
        """
        Public method to retrieve a reference to the completer object.
        
        @return the completer object (CompleterBase)
        """
        return self.completer
        
    def __modificationChanged(self, m):
        """
        Private slot to handle the modificationChanged signal.
        
        It emits the signal modificationStatusChanged with parameters
        m and self.
        
        @param m modification status
        """
        if not m and self.fileName is not None:
            self.lastModified = QFileInfo(self.fileName).lastModified()
        self.modificationStatusChanged.emit(m, self)
        self.undoAvailable.emit(self.isUndoAvailable())
        self.redoAvailable.emit(self.isRedoAvailable())
        
    def __cursorPositionChanged(self, line, index):
        """
        Private slot to handle the cursorPositionChanged signal.
        
        It emits the signal cursorChanged with parameters fileName,
        line and pos.
        
        @param line line number of the cursor
        @param index position in line of the cursor
        """
        self.cursorChanged.emit(self.fileName, line + 1, index)
        
        if Preferences.getEditor("MarkOccurrencesEnabled"):
            self.__markOccurrencesTimer.stop()
            self.__markOccurrencesTimer.start()
        
        if self.lastLine != line:
            self.cursorLineChanged.emit(line)
        
        if self.spell is not None:
            # do spell checking
            doSpelling = True
            if self.lastLine == line:
                start, end = self.getWordBoundaries(
                    line, index, useWordChars=False)
                if start <= self.lastIndex and self.lastIndex <= end:
                    doSpelling = False
            if doSpelling:
                pos = self.positionFromLineIndex(self.lastLine, self.lastIndex)
                self.spell.checkWord(pos)
        
        if self.lastLine != line:
            self.__markerMap.update()
        
        self.lastLine = line
        self.lastIndex = index
        
    def __modificationReadOnly(self):
        """
        Private slot to handle the modificationAttempted signal.
        """
        E5MessageBox.warning(
            self,
            self.tr("Modification of Read Only file"),
            self.tr("""You are attempting to change a read only file. """
                    """Please save to a different file first."""))
        
    def setNoName(self, noName):
        """
        Public method to set the display string for an unnamed editor.
        
        @param noName display string for this unnamed editor (string)
        """
        self.noName = noName
        
    def getNoName(self):
        """
        Public method to get the display string for an unnamed editor.
        
        @return display string for this unnamed editor (string)
        """
        return self.noName
        
    def getFileName(self):
        """
        Public method to return the name of the file being displayed.
        
        @return filename of the displayed file (string)
        """
        return self.fileName
        
    def getFileType(self):
        """
        Public method to return the type of the file being displayed.
        
        @return type of the displayed file (string)
        """
        return self.filetype
        
    def getFileTypeByFlag(self):
        """
        Public method to return the type of the file, if it was set by an
        eflag: marker.
        
        @return type of the displayed file, if set by an eflag: marker or an
            empty string (string)
        """
        if self.filetypeByFlag:
            return self.filetype
        else:
            return ""
        
    def determineFileType(self):
        """
        Public method to determine the file type using various tests.
        
        @return type of the displayed file or an empty string (string)
        """
        ftype = self.filetype
        if not ftype:
            pyVer = self.__getPyVersion()
            if pyVer:
                ftype = "Python{0}".format(pyVer)
            elif self.isRubyFile():
                ftype = "Ruby"
            else:
                ftype = ""
        
        return ftype
        
    def getEncoding(self):
        """
        Public method to return the current encoding.
        
        @return current encoding (string)
        """
        return self.encoding
    
    def __getPyVersion(self):
        """
        Private method to return the Python main version (2 or 3) or 0 if it's
        not a Python file at all.
        
        @return Python version (2 or 3) or 0 if it's not a Python file (int)
        """
        return Utilities.determinePythonVersion(
            self.fileName, self.text(0), self)
    
    def isPyFile(self):
        """
        Public method to return a flag indicating a Python (2 or 3) file.
        
        @return flag indicating a Python (2 or 3) file (boolean)
        """
        return self.__getPyVersion() in [2, 3]
    
    def isPy2File(self):
        """
        Public method to return a flag indicating a Python2 file.
        
        @return flag indicating a Python2 file (boolean)
        """
        return self.__getPyVersion() == 2

    def isPy3File(self):
        """
        Public method to return a flag indicating a Python3 file.
        
        @return flag indicating a Python3 file (boolean)
        """
        return self.__getPyVersion() == 3

    def isRubyFile(self):
        """
        Public method to return a flag indicating a Ruby file.
        
        @return flag indicating a Ruby file (boolean)
        """
        if self.filetype == "Ruby":
            return True
        
        if self.filetype == "":
            line0 = self.text(0)
            if line0.startswith("#!") and \
               "ruby" in line0:
                self.filetype = "Ruby"
                return True
            
            if self.fileName is not None and \
               os.path.splitext(self.fileName)[1] in \
                    self.dbs.getExtensions('Ruby'):
                self.filetype = "Ruby"
                return True
        
        return False

    def isJavascriptFile(self):
        """
        Public method to return a flag indicating a Javascript file.
        
        @return flag indicating a Javascript file (boolean)
        """
        if self.filetype == "JavaScript":
            return True
        
        if self.filetype == "":
            if self.fileName is not None and \
               os.path.splitext(self.fileName)[1] == ".js":
                self.filetype = "JavaScript"
                return True
        
        return False
    
    def highlightVisible(self):
        """
        Public method to make sure that the highlight is visible.
        """
        if self.lastHighlight is not None:
            lineno = self.markerLine(self.lastHighlight)
            self.ensureVisible(lineno + 1)
        
    def highlight(self, line=None, error=False, syntaxError=False):
        """
        Public method to highlight [or de-highlight] a particular line.
        
        @param line line number to highlight (integer)
        @param error flag indicating whether the error highlight should be
            used (boolean)
        @param syntaxError flag indicating a syntax error (boolean)
        """
        if line is None:
            self.lastHighlight = None
            if self.lastErrorMarker is not None:
                self.markerDeleteHandle(self.lastErrorMarker)
            self.lastErrorMarker = None
            if self.lastCurrMarker is not None:
                self.markerDeleteHandle(self.lastCurrMarker)
            self.lastCurrMarker = None
        else:
            if error:
                if self.lastErrorMarker is not None:
                    self.markerDeleteHandle(self.lastErrorMarker)
                self.lastErrorMarker = self.markerAdd(line - 1, self.errorline)
                self.lastHighlight = self.lastErrorMarker
            else:
                if self.lastCurrMarker is not None:
                    self.markerDeleteHandle(self.lastCurrMarker)
                self.lastCurrMarker = self.markerAdd(line - 1,
                                                     self.currentline)
                self.lastHighlight = self.lastCurrMarker
            self.setCursorPosition(line - 1, 0)
        
    def getHighlightPosition(self):
        """
        Public method to return the position of the highlight bar.
        
        @return line number of the highlight bar (integer)
        """
        if self.lastHighlight is not None:
            return self.markerLine(self.lastHighlight)
        else:
            return 1
    
    ###########################################################################
    ## Breakpoint handling methods below
    ###########################################################################

    def __modified(self, pos, mtype, text, length, linesAdded, line, foldNow,
                   foldPrev, token, annotationLinesAdded):
        """
        Private method to handle changes of the number of lines.
        
        @param pos start position of change (integer)
        @param mtype flags identifying the change (integer)
        @param text text that is given to the Undo system (string)
        @param length length of the change (integer)
        @param linesAdded number of added/deleted lines (integer)
        @param line line number of a fold level or marker change (integer)
        @param foldNow new fold level (integer)
        @param foldPrev previous fold level (integer)
        @param token ???
        @param annotationLinesAdded number of added/deleted annotation lines
            (integer)
        """
        if mtype & (self.SC_MOD_INSERTTEXT | self.SC_MOD_DELETETEXT) and \
           linesAdded != 0:
            if self.breaks:
                bps = []    # list of breakpoints
                for handle, (ln, cond, temp, enabled, ignorecount) in \
                        self.breaks.items():
                    line = self.markerLine(handle) + 1
                    if ln != line:
                        bps.append((ln, line))
                        self.breaks[handle] = (line, cond, temp, enabled,
                                               ignorecount)
                self.inLinesChanged = True
                for ln, line in sorted(bps, reverse=linesAdded > 0):
                    index1 = self.breakpointModel.getBreakPointIndex(
                        self.fileName, ln)
                    index2 = self.breakpointModel.index(index1.row(), 1)
                    self.breakpointModel.setData(index2, line)
                self.inLinesChanged = False
        
    def __restoreBreakpoints(self):
        """
        Private method to restore the breakpoints.
        """
        for handle in list(self.breaks.keys()):
            self.markerDeleteHandle(handle)
        self.__addBreakPoints(
            QModelIndex(), 0, self.breakpointModel.rowCount() - 1)
        self.__markerMap.update()
        
    def __deleteBreakPoints(self, parentIndex, start, end):
        """
        Private slot to delete breakpoints.
        
        @param parentIndex index of parent item (QModelIndex)
        @param start start row (integer)
        @param end end row (integer)
        """
        for row in range(start, end + 1):
            index = self.breakpointModel.index(row, 0, parentIndex)
            fn, lineno = self.breakpointModel.getBreakPointByIndex(index)[0:2]
            if fn == self.fileName:
                self.clearBreakpoint(lineno)
        
    def __changeBreakPoints(self, startIndex, endIndex):
        """
        Private slot to set changed breakpoints.
        
        @param startIndex start index of the breakpoints being changed
            (QModelIndex)
        @param endIndex end index of the breakpoints being changed
            (QModelIndex)
        """
        if not self.inLinesChanged:
            self.__addBreakPoints(QModelIndex(), startIndex.row(),
                                  endIndex.row())
        
    def __breakPointDataAboutToBeChanged(self, startIndex, endIndex):
        """
        Private slot to handle the dataAboutToBeChanged signal of the
        breakpoint model.
        
        @param startIndex start index of the rows to be changed (QModelIndex)
        @param endIndex end index of the rows to be changed (QModelIndex)
        """
        self.__deleteBreakPoints(QModelIndex(), startIndex.row(),
                                 endIndex.row())
        
    def __addBreakPoints(self, parentIndex, start, end):
        """
        Private slot to add breakpoints.
        
        @param parentIndex index of parent item (QModelIndex)
        @param start start row (integer)
        @param end end row (integer)
        """
        for row in range(start, end + 1):
            index = self.breakpointModel.index(row, 0, parentIndex)
            fn, line, cond, temp, enabled, ignorecount = \
                self.breakpointModel.getBreakPointByIndex(index)[:6]
            if fn == self.fileName:
                self.newBreakpointWithProperties(
                    line, (cond, temp, enabled, ignorecount))
        
    def clearBreakpoint(self, line):
        """
        Public method to clear a breakpoint.
        
        Note: This doesn't clear the breakpoint in the debugger,
        it just deletes it from the editor internal list of breakpoints.
        
        @param line linenumber of the breakpoint (integer)
        """
        if self.inLinesChanged:
            return
        
        for handle, (ln, _, _, _, _) in list(self.breaks.items()):
            if self.markerLine(handle) == line - 1:
                break
        else:
            # not found, simply ignore it
            return
        
        del self.breaks[handle]
        self.markerDeleteHandle(handle)
        self.__markerMap.update()
        
    def newBreakpointWithProperties(self, line, properties):
        """
        Public method to set a new breakpoint and its properties.
        
        @param line line number of the breakpoint (integer)
        @param properties properties for the breakpoint (tuple)
                (condition, temporary flag, enabled flag, ignore count)
        """
        if not properties[2]:
            marker = self.dbreakpoint
        elif properties[0]:
            marker = properties[1] and self.tcbreakpoint or self.cbreakpoint
        else:
            marker = properties[1] and self.tbreakpoint or self.breakpoint
            
        if self.markersAtLine(line - 1) & self.breakpointMask == 0:
            handle = self.markerAdd(line - 1, marker)
            self.breaks[handle] = (line,) + properties
            self.breakpointToggled.emit(self)
            self.__markerMap.update()
        
    def __toggleBreakpoint(self, line, temporary=False):
        """
        Private method to toggle a breakpoint.
        
        @param line line number of the breakpoint (integer)
        @param temporary flag indicating a temporary breakpoint (boolean)
        """
        for handle, (ln, _, _, _, _) in list(self.breaks.items()):
            if self.markerLine(handle) == line - 1:
                # delete breakpoint or toggle it to the next state
                index = self.breakpointModel.getBreakPointIndex(
                    self.fileName, line)
                if Preferences.getDebugger("ThreeStateBreakPoints") and \
                        not self.breakpointModel.isBreakPointTemporaryByIndex(
                            index):
                    self.breakpointModel.deleteBreakPointByIndex(index)
                    self.__addBreakPoint(line, True)
                else:
                    self.breakpointModel.deleteBreakPointByIndex(index)
                    self.breakpointToggled.emit(self)
                break
        else:
            self.__addBreakPoint(line, temporary)

    def __addBreakPoint(self, line, temporary):
        """
        Private method to add a new breakpoint.
        
        @param line line number of the breakpoint (integer)
        @param temporary flag indicating a temporary breakpoint (boolean)
        """
        if self.fileName and \
           (self.isPyFile() or self.isRubyFile()):
            self.breakpointModel.addBreakPoint(
                self.fileName, line, ('', temporary, True, 0))
            self.breakpointToggled.emit(self)
        
    def __toggleBreakpointEnabled(self, line):
        """
        Private method to toggle a breakpoints enabled status.
        
        @param line line number of the breakpoint (integer)
        """
        for handle, (ln, cond, temp, enabled, ignorecount) in \
                self.breaks.items():
            if self.markerLine(handle) == line - 1:
                break
        else:
            # no breakpoint found on that line
            return
        
        index = self.breakpointModel.getBreakPointIndex(self.fileName, line)
        self.breakpointModel.setBreakPointEnabledByIndex(index, not enabled)
        
    def curLineHasBreakpoint(self):
        """
        Public method to check for the presence of a breakpoint at the current
        line.
        
        @return flag indicating the presence of a breakpoint (boolean)
        """
        line, _ = self.getCursorPosition()
        return self.markersAtLine(line) & self.breakpointMask != 0
        
    def getBreakpointLines(self):
        """
        Public method to get the lines containing a breakpoint.
        
        @return list of lines containing a breakpoint (list of integer)
        """
        lines = []
        line = -1
        while True:
            line = self.markerFindNext(line + 1, self.breakpointMask)
            if line < 0:
                break
            else:
                lines.append(line)
        return lines
        
    def hasBreakpoints(self):
        """
        Public method to check for the presence of breakpoints.
        
        @return flag indicating the presence of breakpoints (boolean)
        """
        return len(self.breaks) > 0
        
    def __menuToggleTemporaryBreakpoint(self):
        """
        Private slot to handle the 'Toggle temporary breakpoint' context menu
        action.
        """
        if self.line < 0:
            self.line, index = self.getCursorPosition()
        self.line += 1
        self.__toggleBreakpoint(self.line, 1)
        self.line = -1
        
    def menuToggleBreakpoint(self):
        """
        Public slot to handle the 'Toggle breakpoint' context menu action.
        """
        if self.line < 0:
            self.line, index = self.getCursorPosition()
        self.line += 1
        self.__toggleBreakpoint(self.line)
        self.line = -1
        
    def __menuToggleBreakpointEnabled(self):
        """
        Private slot to handle the 'Enable/Disable breakpoint' context menu
        action.
        """
        if self.line < 0:
            self.line, index = self.getCursorPosition()
        self.line += 1
        self.__toggleBreakpointEnabled(self.line)
        self.line = -1
        
    def menuEditBreakpoint(self, line=None):
        """
        Public slot to handle the 'Edit breakpoint' context menu action.
        
        @param line linenumber of the breakpoint to edit
        """
        if line is not None:
            self.line = line - 1
        if self.line < 0:
            self.line, index = self.getCursorPosition()
        found = False
        for handle, (ln, cond, temp, enabled, ignorecount) in \
                self.breaks.items():
            if self.markerLine(handle) == self.line:
                found = True
                break
        
        if found:
            index = self.breakpointModel.getBreakPointIndex(self.fileName, ln)
            if not index.isValid():
                return
            
            from Debugger.EditBreakpointDialog import EditBreakpointDialog
            dlg = EditBreakpointDialog(
                (self.fileName, ln),
                (cond, temp, enabled, ignorecount),
                self.condHistory, self, modal=True)
            if dlg.exec_() == QDialog.Accepted:
                cond, temp, enabled, ignorecount = dlg.getData()
                self.breakpointModel.setBreakPointByIndex(
                    index, self.fileName, ln,
                    (cond, temp, enabled, ignorecount))
        
        self.line = -1
        
    def menuNextBreakpoint(self):
        """
        Public slot to handle the 'Next breakpoint' context menu action.
        """
        line, index = self.getCursorPosition()
        if line == self.lines() - 1:
            line = 0
        else:
            line += 1
        bpline = self.markerFindNext(line, self.breakpointMask)
        if bpline < 0:
            # wrap around
            bpline = self.markerFindNext(0, self.breakpointMask)
        if bpline >= 0:
            self.setCursorPosition(bpline, 0)
            self.ensureLineVisible(bpline)
        
    def menuPreviousBreakpoint(self):
        """
        Public slot to handle the 'Previous breakpoint' context menu action.
        """
        line, index = self.getCursorPosition()
        if line == 0:
            line = self.lines() - 1
        else:
            line -= 1
        bpline = self.markerFindPrevious(line, self.breakpointMask)
        if bpline < 0:
            # wrap around
            bpline = self.markerFindPrevious(
                self.lines() - 1, self.breakpointMask)
        if bpline >= 0:
            self.setCursorPosition(bpline, 0)
            self.ensureLineVisible(bpline)
        
    def __menuClearBreakpoints(self):
        """
        Private slot to handle the 'Clear all breakpoints' context menu action.
        """
        self.__clearBreakpoints(self.fileName)
        
    def __clearBreakpoints(self, fileName):
        """
        Private slot to clear all breakpoints.
        
        @param fileName name of the file (string)
        """
        idxList = []
        for handle, (ln, _, _, _, _) in list(self.breaks.items()):
            index = self.breakpointModel.getBreakPointIndex(fileName, ln)
            if index.isValid():
                idxList.append(index)
        if idxList:
            self.breakpointModel.deleteBreakPoints(idxList)
    
    ###########################################################################
    ## Bookmark handling methods below
    ###########################################################################
    
    def toggleBookmark(self, line):
        """
        Public method to toggle a bookmark.
        
        @param line line number of the bookmark (integer)
        """
        for handle in self.bookmarks:
            if self.markerLine(handle) == line - 1:
                self.bookmarks.remove(handle)
                self.markerDeleteHandle(handle)
                break
        else:
            # set a new bookmark
            handle = self.markerAdd(line - 1, self.bookmark)
            self.bookmarks.append(handle)
        self.bookmarkToggled.emit(self)
        self.__markerMap.update()
        
    def getBookmarks(self):
        """
        Public method to retrieve the bookmarks.
        
        @return sorted list of all lines containing a bookmark
            (list of integer)
        """
        bmlist = []
        for handle in self.bookmarks:
            bmlist.append(self.markerLine(handle) + 1)
        
        bmlist.sort()
        return bmlist
        
    def getBookmarkLines(self):
        """
        Public method to get the lines containing a bookmark.
        
        @return list of lines containing a bookmark (list of integer)
        """
        lines = []
        line = -1
        while True:
            line = self.markerFindNext(line + 1, 1 << self.bookmark)
            if line < 0:
                break
            else:
                lines.append(line)
        return lines
        
    def hasBookmarks(self):
        """
        Public method to check for the presence of bookmarks.
        
        @return flag indicating the presence of bookmarks (boolean)
        """
        return len(self.bookmarks) > 0
    
    def menuToggleBookmark(self):
        """
        Public slot to handle the 'Toggle bookmark' context menu action.
        """
        if self.line < 0:
            self.line, index = self.getCursorPosition()
        self.line += 1
        self.toggleBookmark(self.line)
        self.line = -1
        
    def nextBookmark(self):
        """
        Public slot to handle the 'Next bookmark' context menu action.
        """
        line, index = self.getCursorPosition()
        if line == self.lines() - 1:
            line = 0
        else:
            line += 1
        bmline = self.markerFindNext(line, 1 << self.bookmark)
        if bmline < 0:
            # wrap around
            bmline = self.markerFindNext(0, 1 << self.bookmark)
        if bmline >= 0:
            self.setCursorPosition(bmline, 0)
            self.ensureLineVisible(bmline)
        
    def previousBookmark(self):
        """
        Public slot to handle the 'Previous bookmark' context menu action.
        """
        line, index = self.getCursorPosition()
        if line == 0:
            line = self.lines() - 1
        else:
            line -= 1
        bmline = self.markerFindPrevious(line, 1 << self.bookmark)
        if bmline < 0:
            # wrap around
            bmline = self.markerFindPrevious(
                self.lines() - 1, 1 << self.bookmark)
        if bmline >= 0:
            self.setCursorPosition(bmline, 0)
            self.ensureLineVisible(bmline)
        
    def clearBookmarks(self):
        """
        Public slot to handle the 'Clear all bookmarks' context menu action.
        """
        for handle in self.bookmarks:
            self.markerDeleteHandle(handle)
        self.bookmarks = []
        self.bookmarkToggled.emit(self)
        self.__markerMap.update()
    
    ###########################################################################
    ## Printing methods below
    ###########################################################################

    def printFile(self):
        """
        Public slot to print the text.
        """
        from .Printer import Printer
        printer = Printer(mode=QPrinter.HighResolution)
        sb = e5App().getObject("UserInterface").statusBar()
        printDialog = QPrintDialog(printer, self)
        if self.hasSelectedText():
            printDialog.setOption(QAbstractPrintDialog.PrintSelection, True)
        if printDialog.exec_() == QDialog.Accepted:
            sb.showMessage(self.tr('Printing...'))
            QApplication.processEvents()
            fn = self.getFileName()
            if fn is not None:
                printer.setDocName(os.path.basename(fn))
            else:
                printer.setDocName(self.noName)
            if printDialog.printRange() == QAbstractPrintDialog.Selection:
                # get the selection
                fromLine, fromIndex, toLine, toIndex = self.getSelection()
                if toIndex == 0:
                    toLine -= 1
                # Qscintilla seems to print one line more than told
                res = printer.printRange(self, fromLine, toLine - 1)
            else:
                res = printer.printRange(self)
            if res:
                sb.showMessage(self.tr('Printing completed'), 2000)
            else:
                sb.showMessage(self.tr('Error while printing'), 2000)
            QApplication.processEvents()
        else:
            sb.showMessage(self.tr('Printing aborted'), 2000)
            QApplication.processEvents()

    def printPreviewFile(self):
        """
        Public slot to show a print preview of the text.
        """
        from PyQt5.QtPrintSupport import QPrintPreviewDialog
        from .Printer import Printer
        
        printer = Printer(mode=QPrinter.HighResolution)
        fn = self.getFileName()
        if fn is not None:
            printer.setDocName(os.path.basename(fn))
        else:
            printer.setDocName(self.noName)
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(self.__printPreview)
        preview.exec_()
    
    def __printPreview(self, printer):
        """
        Private slot to generate a print preview.
        
        @param printer reference to the printer object
            (QScintilla.Printer.Printer)
        """
        printer.printRange(self)
    
    ###########################################################################
    ## Task handling methods below
    ###########################################################################
    
    def getTaskLines(self):
        """
        Public method to get the lines containing a task.
        
        @return list of lines containing a task (list of integer)
        """
        lines = []
        line = -1
        while True:
            line = self.markerFindNext(line + 1, 1 << self.taskmarker)
            if line < 0:
                break
            else:
                lines.append(line)
        return lines
        
    def hasTaskMarkers(self):
        """
        Public method to determine, if this editor contains any task markers.
        
        @return flag indicating the presence of task markers (boolean)
        """
        return self.__hasTaskMarkers
        
    def nextTask(self):
        """
        Public slot to handle the 'Next task' context menu action.
        """
        line, index = self.getCursorPosition()
        if line == self.lines() - 1:
            line = 0
        else:
            line += 1
        taskline = self.markerFindNext(line, 1 << self.taskmarker)
        if taskline < 0:
            # wrap around
            taskline = self.markerFindNext(0, 1 << self.taskmarker)
        if taskline >= 0:
            self.setCursorPosition(taskline, 0)
            self.ensureLineVisible(taskline)
        
    def previousTask(self):
        """
        Public slot to handle the 'Previous task' context menu action.
        """
        line, index = self.getCursorPosition()
        if line == 0:
            line = self.lines() - 1
        else:
            line -= 1
        taskline = self.markerFindPrevious(line, 1 << self.taskmarker)
        if taskline < 0:
            # wrap around
            taskline = self.markerFindPrevious(
                self.lines() - 1, 1 << self.taskmarker)
        if taskline >= 0:
            self.setCursorPosition(taskline, 0)
            self.ensureLineVisible(taskline)
        
    def extractTasks(self):
        """
        Public slot to extract all tasks.
        """
        from Tasks.Task import Task
        markers = {
            Task.TypeWarning:
            Preferences.getTasks("TasksWarningMarkers").split(),
            Task.TypeNote:
            Preferences.getTasks("TasksNoteMarkers").split(),
            Task.TypeTodo:
            Preferences.getTasks("TasksTodoMarkers").split(),
            Task.TypeFixme:
            Preferences.getTasks("TasksFixmeMarkers").split(),
        }
        txtList = self.text().split(self.getLineSeparator())
        
        # clear all task markers and tasks
        self.markerDeleteAll(self.taskmarker)
        self.taskViewer.clearFileTasks(self.fileName)
        self.__hasTaskMarkers = False
        
        # now search tasks and record them
        lineIndex = -1
        for line in txtList:
            lineIndex += 1
            shouldBreak = False
            
            for taskType, taskMarkers in markers.items():
                for taskMarker in taskMarkers:
                    index = line.find(taskMarker)
                    if index > -1:
                        task = line[index:]
                        self.markerAdd(lineIndex, self.taskmarker)
                        self.taskViewer.addFileTask(
                            task, self.fileName, lineIndex + 1, taskType)
                        self.__hasTaskMarkers = True
                        shouldBreak = True
                        break
                if shouldBreak:
                    break
        self.taskMarkersUpdated.emit(self)
        self.__markerMap.update()
    
    ###########################################################################
    ## Change tracing methods below
    ###########################################################################
    
    def __createChangeMarkerPixmap(self, key, size=16, width=4):
        """
        Private method to create a pixmap for the change markers.
        
        @param key key of the color to use (string)
        @param size size of the pixmap (integer)
        @param width width of the marker line (integer)
        @return create pixmap (QPixmap)
        """
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.fillRect(size - 4, 0, 4, size,
                         Preferences.getEditorColour(key))
        painter.end()
        return pixmap
        
    def __initOnlineChangeTrace(self):
        """
        Private slot to initialize the online change trace.
        """
        self.__hasChangeMarkers = False
        self.__oldText = self.text()
        self.__lastSavedText = self.text()
        self.__onlineChangeTraceTimer = QTimer(self)
        self.__onlineChangeTraceTimer.setSingleShot(True)
        self.__onlineChangeTraceTimer.setInterval(
            Preferences.getEditor("OnlineChangeTraceInterval"))
        self.__onlineChangeTraceTimer.timeout.connect(
            self.__onlineChangeTraceTimerTimeout)
        self.textChanged.connect(self.__resetOnlineChangeTraceTimer)
        
    def __reinitOnlineChangeTrace(self):
        """
        Private slot to re-initialize the online change trace.
        """
        self.__oldText = self.text()
        self.__lastSavedText = self.text()
        self.__deleteAllChangeMarkers()
        
    def __resetOnlineChangeTraceTimer(self):
        """
        Private method to reset the online syntax check timer.
        """
        if Preferences.getEditor("OnlineChangeTrace"):
            self.__onlineChangeTraceTimer.stop()
            self.__onlineChangeTraceTimer.start()
        
    def __onlineChangeTraceTimerTimeout(self):
        """
        Private slot to mark added and changed lines.
        """
        self.__deleteAllChangeMarkers()
        
        # step 1: mark saved changes
        oldL = self.__oldText.splitlines()
        newL = self.__lastSavedText.splitlines()
        matcher = difflib.SequenceMatcher(None, oldL, newL)
        
        for token, i1, i2, j1, j2 in matcher.get_opcodes():
            if token in ["insert", "replace"]:
                for lineNo in range(j1, j2):
                    self.markerAdd(lineNo, self.__changeMarkerSaved)
                    self.__hasChangeMarkers = True
        
        # step 2: mark unsaved changes
        oldL = self.__lastSavedText.splitlines()
        newL = self.text().splitlines()
        matcher = difflib.SequenceMatcher(None, oldL, newL)
        
        for token, i1, i2, j1, j2 in matcher.get_opcodes():
            if token in ["insert", "replace"]:
                for lineNo in range(j1, j2):
                    self.markerAdd(lineNo, self.__changeMarkerUnsaved)
                    self.__hasChangeMarkers = True
        
        if self.__hasChangeMarkers:
            self.changeMarkersUpdated.emit(self)
            self.__markerMap.update()
        
    def __resetOnlineChangeTraceInfo(self):
        """
        Private slot to reset the online change trace info.
        """
        self.__lastSavedText = self.text()
        self.__deleteAllChangeMarkers()
        
        # mark saved changes
        oldL = self.__oldText.splitlines()
        newL = self.__lastSavedText.splitlines()
        matcher = difflib.SequenceMatcher(None, oldL, newL)
        
        for token, i1, i2, j1, j2 in matcher.get_opcodes():
            if token in ["insert", "replace"]:
                for lineNo in range(j1, j2):
                    self.markerAdd(lineNo, self.__changeMarkerSaved)
                    self.__hasChangeMarkers = True
        
        if self.__hasChangeMarkers:
            self.changeMarkersUpdated.emit(self)
            self.__markerMap.update()
        
    def __deleteAllChangeMarkers(self):
        """
        Private slot to delete all change markers.
        """
        self.markerDeleteAll(self.__changeMarkerUnsaved)
        self.markerDeleteAll(self.__changeMarkerSaved)
        self.__hasChangeMarkers = False
        self.changeMarkersUpdated.emit(self)
        self.__markerMap.update()
        
    def getChangeLines(self):
        """
        Public method to get the lines containing a change.
        
        @return list of lines containing a change (list of integer)
        """
        lines = []
        line = -1
        while True:
            line = self.markerFindNext(line + 1, self.changeMarkersMask)
            if line < 0:
                break
            else:
                lines.append(line)
        return lines
        
    def hasChangeMarkers(self):
        """
        Public method to determine, if this editor contains any change markers.
        
        @return flag indicating the presence of change markers (boolean)
        """
        return self.__hasChangeMarkers
        
    def nextChange(self):
        """
        Public slot to handle the 'Next change' context menu action.
        """
        line, index = self.getCursorPosition()
        if line == self.lines() - 1:
            line = 0
        else:
            line += 1
        changeline = self.markerFindNext(line, self.changeMarkersMask)
        if changeline < 0:
            # wrap around
            changeline = self.markerFindNext(0, self.changeMarkersMask)
        if changeline >= 0:
            self.setCursorPosition(changeline, 0)
            self.ensureLineVisible(changeline)
        
    def previousChange(self):
        """
        Public slot to handle the 'Previous task' context menu action.
        """
        line, index = self.getCursorPosition()
        if line == 0:
            line = self.lines() - 1
        else:
            line -= 1
        changeline = self.markerFindPrevious(line, self.changeMarkersMask)
        if changeline < 0:
            # wrap around
            changeline = self.markerFindPrevious(
                self.lines() - 1, self.changeMarkersMask)
        if changeline >= 0:
            self.setCursorPosition(changeline, 0)
            self.ensureLineVisible(changeline)
    
    ###########################################################################
    ## Flags handling methods below
    ###########################################################################
    
    def __processFlags(self):
        """
        Private method to extract flags and process them.
        
        @return list of change flags (list of string)
        """
        txt = self.text()
        flags = Utilities.extractFlags(txt)
        
        changedFlags = []
        
        # Flag 1: FileType
        if "FileType" in flags:
            oldFiletype = self.filetype
            if isinstance(flags["FileType"], str):
                self.filetype = flags["FileType"]
                self.filetypeByFlag = True
                if oldFiletype != self.filetype:
                    changedFlags.append("FileType")
        else:
            if self.filetype != "" and self.filetypeByFlag:
                self.filetype = ""
                self.filetypeByFlag = False
                self.__bindName(txt.splitlines()[0])
                changedFlags.append("FileType")
        
        return changedFlags
    
    ###########################################################################
    ## File handling methods below
    ###########################################################################
    
    def checkDirty(self):
        """
        Public method to check dirty status and open a message window.
        
        @return flag indicating successful reset of the dirty flag (boolean)
        """
        if self.isModified():
            fn = self.fileName
            if fn is None:
                fn = self.noName
            res = E5MessageBox.okToClearData(
                self,
                self.tr("File Modified"),
                self.tr("<p>The file <b>{0}</b> has unsaved changes.</p>")
                .format(fn),
                self.saveFile)
            if res:
                self.vm.setEditorName(self, self.fileName)
            return res
        
        return True
        
    def revertToUnmodified(self):
        """
        Public method to revert back to the last saved state.
        """
        undo_ = True
        while self.isModified():
            if undo_:
                # try undo first
                if self.isUndoAvailable():
                    self.undo()
                else:
                    undo_ = False
            else:
                # try redo next
                if self.isRedoAvailable():
                    self.redo()
                else:
                    break
                    # Couldn't find the unmodified state
    
    def readFile(self, fn, createIt=False, encoding=""):
        """
        Public slot to read the text from a file.
        
        @param fn filename to read from (string)
        @keyparam createIt flag indicating the creation of a new file, if the
            given one doesn't exist (boolean)
        @keyparam encoding encoding to be used to read the file (string)
            (Note: this parameter overrides encoding detection)
        """
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        
        try:
            if createIt and not os.path.exists(fn):
                f = open(fn, "w")
                f.close()
            if encoding:
                txt, self.encoding = Utilities.readEncodedFileWithEncoding(
                    fn, encoding)
            else:
                txt, self.encoding = Utilities.readEncodedFile(fn)
        except (UnicodeDecodeError, IOError) as why:
            QApplication.restoreOverrideCursor()
            E5MessageBox.critical(
                self.vm,
                self.tr('Open File'),
                self.tr('<p>The file <b>{0}</b> could not be opened.</p>'
                        '<p>Reason: {1}</p>')
                    .format(fn, str(why)))
            QApplication.restoreOverrideCursor()
            raise
        fileEol = self.detectEolString(txt)
        
        modified = False
        if (not Preferences.getEditor("TabForIndentation")) and \
                Preferences.getEditor("ConvertTabsOnLoad") and \
                not (self.lexer_ and
                     self.lexer_.alwaysKeepTabs()):
            txtExpanded = txt.expandtabs(Preferences.getEditor("TabWidth"))
            if txtExpanded != txt:
                modified = True
            txt = txtExpanded
            del txtExpanded
        
        self.setText(txt)
        
        # get eric specific flags
        self.__processFlags()
        
        # perform automatic eol conversion
        if Preferences.getEditor("AutomaticEOLConversion"):
            self.convertEols(self.eolMode())
        else:
            self.setEolModeByEolString(fileEol)
        
        self.extractTasks()
        
        QApplication.restoreOverrideCursor()
        
        self.setModified(modified)
        self.lastModified = QFileInfo(self.fileName).lastModified()
        
    def __removeTrailingWhitespace(self):
        """
        Private method to remove trailing whitespace.
        """
        searchRE = r"[ \t]+$"    # whitespace at the end of a line
        
        ok = self.findFirstTarget(searchRE, True, False, False, 0, 0)
        self.beginUndoAction()
        while ok:
            self.replaceTarget("")
            ok = self.findNextTarget()
        self.endUndoAction()
        
    def writeFile(self, fn, backup=True):
        """
        Public slot to write the text to a file.
        
        @param fn filename to write to (string)
        @param backup flag indicating to save a backup (boolean)
        @return flag indicating success (boolean)
        """
        if Preferences.getEditor("StripTrailingWhitespace"):
            self.__removeTrailingWhitespace()
        
        txt = self.text()
        # work around glitch in scintilla: always make sure,
        # that the last line is terminated properly
        eol = self.getLineSeparator()
        if eol:
            if len(txt) >= len(eol):
                if txt[-len(eol):] != eol:
                    txt += eol
            else:
                txt += eol
        
        # create a backup file, if the option is set
        createBackup = backup and Preferences.getEditor("CreateBackupFile")
        if createBackup:
            if os.path.islink(fn):
                fn = os.path.realpath(fn)
            bfn = '{0}~'.format(fn)
            try:
                permissions = os.stat(fn).st_mode
                perms_valid = True
            except EnvironmentError:
                # if there was an error, ignore it
                perms_valid = False
            try:
                os.remove(bfn)
            except EnvironmentError:
                # if there was an error, ignore it
                pass
            try:
                os.rename(fn, bfn)
            except EnvironmentError:
                # if there was an error, ignore it
                pass
        
        # now write text to the file fn
        try:
            self.encoding = Utilities.writeEncodedFile(fn, txt, self.encoding)
            if createBackup and perms_valid:
                os.chmod(fn, permissions)
            return True
        except (IOError, Utilities.CodingError, UnicodeError) as why:
            E5MessageBox.critical(
                self,
                self.tr('Save File'),
                self.tr('<p>The file <b>{0}</b> could not be saved.<br/>'
                        'Reason: {1}</p>')
                .format(fn, str(why)))
            return False
        
    def __getSaveFileName(self, path=None):
        """
        Private method to get the name of the file to be saved.
        
        @param path directory to save the file in (string)
        @return file name (string)
        """
        # save to project, if a project is loaded
        if self.project.isOpen():
            if self.fileName is not None and \
               self.project.startswithProjectPath(self.fileName):
                path = os.path.dirname(self.fileName)
            else:
                path = self.project.getProjectPath()
        
        if not path and self.fileName is not None:
            path = os.path.dirname(self.fileName)
        if not path:
            path = Preferences.getMultiProject("Workspace") or \
                Utilities.getHomeDir()
        
        from . import Lexers
        if self.fileName:
            filterPattern = "(*{0})".format(
                os.path.splitext(self.fileName)[1])
            for filter in Lexers.getSaveFileFiltersList(True):
                if filterPattern in filter:
                    defaultFilter = filter
                    break
            else:
                defaultFilter = Preferences.getEditor("DefaultSaveFilter")
        else:
            defaultFilter = Preferences.getEditor("DefaultSaveFilter")
        fn, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            self,
            self.tr("Save File"),
            path,
            Lexers.getSaveFileFiltersList(True, True),
            defaultFilter,
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        
        if fn:
            if fn.endswith("."):
                fn = fn[:-1]
            
            ext = QFileInfo(fn).suffix()
            if not ext:
                ex = selectedFilter.split("(*")[1].split(")")[0]
                if ex:
                    fn += ex
            if QFileInfo(fn).exists():
                res = E5MessageBox.yesNo(
                    self,
                    self.tr("Save File"),
                    self.tr("<p>The file <b>{0}</b> already exists."
                            " Overwrite it?</p>").format(fn),
                    icon=E5MessageBox.Warning)
                if not res:
                    return ""
            fn = Utilities.toNativeSeparators(fn)
        
        return fn
        
    def saveFileCopy(self, path=None):
        """
        Public method to save a copy of the file.
        
        @param path directory to save the file in (string)
        @return flag indicating success (boolean)
        """
        fn = self.__getSaveFileName(path)
        if not fn:
            return False
        
        res = self.writeFile(fn)
        if res:
            # save to project, if a project is loaded
            if self.project.isOpen() and \
                    self.project.startswithProjectPath(fn):
                self.project.appendFile(fn)
        
        return res
        
    def saveFile(self, saveas=False, path=None):
        """
        Public method to save the text to a file.
        
        @param saveas flag indicating a 'save as' action (boolean)
        @param path directory to save the file in (string)
        @return flag indicating success (boolean)
        """
        if not saveas and not self.isModified():
            return False      # do nothing if text wasn't changed
            
        newName = None
        if saveas or self.fileName is None:
            saveas = True
            
            fn = self.__getSaveFileName(path)
            if not fn:
                return False
            
            newName = fn
            
            # save to project, if a project is loaded
            if self.project.isOpen() and \
                    self.project.startswithProjectPath(fn):
                self.setEolModeByEolString(self.project.getEolString())
                self.convertEols(self.eolMode())
        else:
            fn = self.fileName
        
        self.editorAboutToBeSaved.emit(self.fileName)
        if self.writeFile(fn):
            if saveas:
                self.__clearBreakpoints(self.fileName)
            self.fileName = fn
            self.setModified(False)
            self.setReadOnly(False)
            self.setWindowTitle(self.fileName)
            # get eric specific flags
            changedFlags = self.__processFlags()
            if not self.__lexerReset and "FileType" in changedFlags:
                self.setLanguage(self.fileName)
            
            if saveas:
                self.isResourcesFile = self.fileName.endswith(".qrc")
                self.__initContextMenu()
                self.editorRenamed.emit(self.fileName)
                
                # save to project, if a project is loaded
                if self.project.isOpen() and \
                        self.project.startswithProjectPath(fn):
                    self.project.appendFile(fn)
                    self.addedToProject()
                
                self.setLanguage(self.fileName)
            
            self.lastModified = QFileInfo(self.fileName).lastModified()
            if newName is not None:
                self.vm.addToRecentList(newName)
            self.editorSaved.emit(self.fileName)
            self.checkSyntax()
            self.extractTasks()
            self.__resetOnlineChangeTraceInfo()
            self.__checkEncoding()
            return True
        else:
            self.lastModified = QFileInfo(fn).lastModified()
            return False
        
    def saveFileAs(self, path=None, toProject=False):
        """
        Public slot to save a file with a new name.
        
        @param path directory to save the file in (string)
        @keyparam toProject flag indicating a save to project operation
            (boolean)
        @return tuple of two values (boolean, string) giving a success
            indicator and the name of the saved file
        """
        return self.saveFile(True, path)
        
    def handleRenamed(self, fn):
        """
        Public slot to handle the editorRenamed signal.
        
        @param fn filename to be set for the editor (string).
        """
        self.__clearBreakpoints(fn)
        
        self.fileName = fn
        self.setWindowTitle(self.fileName)
        
        if self.lexer_ is None:
            self.setLanguage(self.fileName)
        
        self.lastModified = QFileInfo(self.fileName).lastModified()
        self.vm.setEditorName(self, self.fileName)
        self.__updateReadOnly(True)
        
    def fileRenamed(self, fn):
        """
        Public slot to handle the editorRenamed signal.
        
        @param fn filename to be set for the editor (string).
        """
        self.handleRenamed(fn)
        if not self.inFileRenamed:
            self.inFileRenamed = True
            self.editorRenamed.emit(self.fileName)
            self.inFileRenamed = False
    
    ###########################################################################
    ## Utility methods below
    ###########################################################################

    def ensureVisible(self, line):
        """
        Public slot to ensure, that the specified line is visible.
        
        @param line line number to make visible
        """
        self.ensureLineVisible(line - 1)
        
    def ensureVisibleTop(self, line):
        """
        Public slot to ensure, that the specified line is visible at the top
        of the editor.
        
        @param line line number to make visible
        """
        self.setFirstVisibleLine(line - 1)
        
    def __marginClicked(self, margin, line, modifiers):
        """
        Private slot to handle the marginClicked signal.
        
        @param margin id of the clicked margin (integer)
        @param line line number of the click (integer)
        @param modifiers keyboard modifiers (Qt.KeyboardModifiers)
        """
        if self.__unifiedMargins:
            if margin == 1:
                if modifiers & Qt.KeyboardModifiers(Qt.ShiftModifier):
                    if self.marginMenuActs["LMBbreakpoints"].isChecked():
                        self.toggleBookmark(line + 1)
                    else:
                        self.__toggleBreakpoint(line + 1)
                elif modifiers & Qt.KeyboardModifiers(Qt.ControlModifier):
                    if self.markersAtLine(line) & (1 << self.syntaxerror):
                        self.__showSyntaxError(line)
                    elif self.markersAtLine(line) & (1 << self.warning):
                        self.__showWarning(line)
                else:
                    if self.marginMenuActs["LMBbreakpoints"].isChecked():
                        self.__toggleBreakpoint(line + 1)
                    else:
                        self.toggleBookmark(line + 1)
        else:
            if margin == self.__bmMargin:
                        self.toggleBookmark(line + 1)
            elif margin == self.__bpMargin:
                        self.__toggleBreakpoint(line + 1)
            elif margin == self.__indicMargin:
                if self.markersAtLine(line) & (1 << self.syntaxerror):
                    self.__showSyntaxError(line)
                elif self.markersAtLine(line) & (1 << self.warning):
                    self.__showWarning(line)
        
    def handleMonospacedEnable(self):
        """
        Public slot to handle the Use Monospaced Font context menu entry.
        """
        if self.menuActs["MonospacedFont"].isChecked():
            if not self.lexer_:
                self.setMonospaced(True)
        else:
            if self.lexer_:
                self.lexer_.readSettings(
                    Preferences.Prefs.settings, "Scintilla")
                self.lexer_.initProperties()
            self.setMonospaced(False)
            self.__setMarginsDisplay()
        
    def getWordBoundaries(self, line, index, useWordChars=True):
        """
        Public method to get the word boundaries at a position.
        
        @param line number of line to look at (int)
        @param index position to look at (int)
        @keyparam useWordChars flag indicating to use the wordCharacters
            method (boolean)
        @return tuple with start and end indexes of the word at the position
            (integer, integer)
        """
        text = self.text(line)
        if self.caseSensitive():
            cs = Qt.CaseSensitive
        else:
            cs = Qt.CaseInsensitive
        wc = self.wordCharacters()
        if wc is None or not useWordChars:
            regExp = QRegExp('[^\w_]', cs)
        else:
            wc = re.sub('\w', "", wc)
            regExp = QRegExp('[^\w{0}]'.format(re.escape(wc)), cs)
        start = regExp.lastIndexIn(text, index) + 1
        end = regExp.indexIn(text, index)
        if start == end + 1 and index > 0:
            # we are on a word boundary, try again
            start = regExp.lastIndexIn(text, index - 1) + 1
        if start == -1:
            start = 0
        if end == -1:
            end = len(text)
        
        return (start, end)
        
    def getWord(self, line, index, direction=0, useWordChars=True):
        """
        Public method to get the word at a position.
        
        @param line number of line to look at (int)
        @param index position to look at (int)
        @param direction direction to look in (0 = whole word, 1 = left,
            2 = right)
        @keyparam useWordChars flag indicating to use the wordCharacters
            method (boolean)
        @return the word at that position (string)
        """
        start, end = self.getWordBoundaries(line, index, useWordChars)
        if direction == 1:
            end = index
        elif direction == 2:
            start = index
        if end > start:
            text = self.text(line)
            word = text[start:end]
        else:
            word = ''
        return word
        
    def getWordLeft(self, line, index):
        """
        Public method to get the word to the left of a position.
        
        @param line number of line to look at (int)
        @param index position to look at (int)
        @return the word to the left of that position (string)
        """
        return self.getWord(line, index, 1)
        
    def getWordRight(self, line, index):
        """
        Public method to get the word to the right of a position.
        
        @param line number of line to look at (int)
        @param index position to look at (int)
        @return the word to the right of that position (string)
        """
        return self.getWord(line, index, 2)
        
    def getCurrentWord(self):
        """
        Public method to get the word at the current position.
        
        @return the word at that current position (string)
        """
        line, index = self.getCursorPosition()
        return self.getWord(line, index)
        
    def getCurrentWordBoundaries(self):
        """
        Public method to get the word boundaries at the current position.
        
        @return tuple with start and end indexes of the current word
            (integer, integer)
        """
        line, index = self.getCursorPosition()
        return self.getWordBoundaries(line, index)
        
    def selectWord(self, line, index):
        """
        Public method to select the word at a position.
        
        @param line number of line to look at (int)
        @param index position to look at (int)
        """
        start, end = self.getWordBoundaries(line, index)
        self.setSelection(line, start, line, end)
        
    def selectCurrentWord(self):
        """
        Public method to select the current word.
        """
        line, index = self.getCursorPosition()
        self.selectWord(line, index)
        
    def __getCharacter(self, pos):
        """
        Private method to get the character to the left of the current position
        in the current line.
        
        @param pos position to get character at (integer)
        @return requested character or "", if there are no more (string) and
            the next position (i.e. pos - 1)
        """
        if pos <= 0:
            return "", pos
        
        pos = self.positionBefore(pos)
        ch = self.charAt(pos)
        
        # Don't go past the end of the previous line
        if ch == '\n' or ch == '\r':
            return "", pos
        
        return ch, pos
    
    def getSearchText(self, selectionOnly=False):
        """
        Public method to determine the selection or the current word for the
        next search operation.
        
        @param selectionOnly flag indicating that only selected text should be
            returned (boolean)
        @return selection or current word (string)
        """
        if self.hasSelectedText():
            text = self.selectedText()
            if '\r' in text or '\n' in text:
                # the selection contains at least a newline, it is
                # unlikely to be the expression to search for
                return ''
            
            return text
        
        if not selectionOnly:
            # no selected text, determine the word at the current position
            return self.getCurrentWord()
        
        return ''
        
    def setSearchIndicator(self, startPos, indicLength):
        """
        Public method to set a search indicator for the given range.
        
        @param startPos start position of the indicator (integer)
        @param indicLength length of the indicator (integer)
        """
        self.setIndicatorRange(self.searchIndicator, startPos, indicLength)
        line = self.lineIndexFromPosition(startPos)[0]
        if line not in self.__searchIndicatorLines:
            self.__searchIndicatorLines.append(line)
        
    def clearSearchIndicators(self):
        """
        Public method to clear all search indicators.
        """
        self.clearAllIndicators(self.searchIndicator)
        self.__markedText = ""
        self.__searchIndicatorLines = []
        self.__markerMap.update()
        
    def __markOccurrences(self):
        """
        Private method to mark all occurrences of the current word.
        """
        word = self.getCurrentWord()
        if not word:
            self.clearSearchIndicators()
            return
        
        if self.__markedText == word:
            return
        
        self.clearSearchIndicators()
        ok = self.findFirstTarget(word, False, self.caseSensitive(), True,
                                  0, 0)
        while ok:
            tgtPos, tgtLen = self.getFoundTarget()
            self.setSearchIndicator(tgtPos, tgtLen)
            ok = self.findNextTarget()
        self.__markedText = word
        self.__markerMap.update()
    
    def getSearchIndicatorLines(self):
        """
        Public method to get the lines containing a search indicator.
        
        @return list of lines containing a search indicator (list of integer)
        """
        return self.__searchIndicatorLines[:]
    
    def updateMarkerMap(self):
        """
        Public method to initiate an update of the marker map.
        """
        self.__markerMap.update()
    
    ###########################################################################
    ## Comment handling methods below
    ###########################################################################
    
    def __isCommentedLine(self, line, commentStr):
        """
        Private method to check, if the given line is a comment line as
        produced by the configured comment rules.
        
        @param line text of the line to check (string)
        @param commentStr comment string to check against (string)
        @return flag indicating a commented line (boolean)
        """
        if Preferences.getEditor("CommentColumn0"):
            return line.startswith(commentStr)
        else:
            return line.strip().startswith(commentStr)
    
    def toggleCommentBlock(self):
        """
        Public slot to toggle the comment of a block.
        
        If the line of the cursor or the selection is not commented, it will
        be commented. If it is commented, the comment block will be removed.
        The later works independent of the current selection.
        """
        if self.lexer_ is None or not self.lexer_.canBlockComment():
            return
        
        commentStr = self.lexer_.commentStr()
        line, index = self.getCursorPosition()
        
        # check if line starts with our comment string (i.e. was commented
        # by our comment...() slots
        if self.hasSelectedText() and \
                self.__isCommentedLine(self.text(self.getSelection()[0]),
                                       commentStr):
            self.uncommentLineOrSelection()
        elif not self.__isCommentedLine(self.text(line), commentStr):
            # it doesn't, so comment the line or selection
            self.commentLineOrSelection()
        else:
            # determine the start of the comment block
            begline = line
            while begline > 0 and \
                    self.__isCommentedLine(self.text(begline - 1), commentStr):
                begline -= 1
            # determine the end of the comment block
            endline = line
            lines = self.lines()
            while endline < lines and \
                    self.__isCommentedLine(self.text(endline + 1), commentStr):
                endline += 1
            
            self.setSelection(begline, 0, endline, self.lineLength(endline))
            self.uncommentLineOrSelection()
            
            # reset the cursor
            self.setCursorPosition(line, index - len(commentStr))
        
    def commentLine(self):
        """
        Public slot to comment the current line.
        """
        if self.lexer_ is None or not self.lexer_.canBlockComment():
            return
        
        line, index = self.getCursorPosition()
        self.beginUndoAction()
        if Preferences.getEditor("CommentColumn0"):
            self.insertAt(self.lexer_.commentStr(), line, 0)
        else:
            self.insertAt(self.lexer_.commentStr(), line,
                          self.indentation(line))
        self.endUndoAction()
        
    def uncommentLine(self):
        """
        Public slot to uncomment the current line.
        """
        if self.lexer_ is None or not self.lexer_.canBlockComment():
            return
        
        commentStr = self.lexer_.commentStr()
        line, index = self.getCursorPosition()
        
        # check if line starts with our comment string (i.e. was commented
        # by our comment...() slots
        if not self.__isCommentedLine(self.text(line), commentStr):
            return
        
        # now remove the comment string
        self.beginUndoAction()
        if Preferences.getEditor("CommentColumn0"):
            self.setSelection(line, 0, line, len(commentStr))
        else:
            self.setSelection(line, self.indentation(line),
                              line, self.indentation(line) + len(commentStr))
        self.removeSelectedText()
        self.endUndoAction()
        
    def commentSelection(self):
        """
        Public slot to comment the current selection.
        """
        if self.lexer_ is None or not self.lexer_.canBlockComment():
            return
        
        if not self.hasSelectedText():
            return
        
        commentStr = self.lexer_.commentStr()
        
        # get the selection boundaries
        lineFrom, indexFrom, lineTo, indexTo = self.getSelection()
        if indexTo == 0:
            endLine = lineTo - 1
        else:
            endLine = lineTo
        
        self.beginUndoAction()
        # iterate over the lines
        for line in range(lineFrom, endLine + 1):
            if Preferences.getEditor("CommentColumn0"):
                self.insertAt(commentStr, line, 0)
            else:
                self.insertAt(commentStr, line, self.indentation(line))
        
        # change the selection accordingly
        self.setSelection(lineFrom, 0, endLine + 1, 0)
        self.endUndoAction()
        
    def uncommentSelection(self):
        """
        Public slot to uncomment the current selection.
        """
        if self.lexer_ is None or not self.lexer_.canBlockComment():
            return
        
        if not self.hasSelectedText():
            return
        
        commentStr = self.lexer_.commentStr()
        
        # get the selection boundaries
        lineFrom, indexFrom, lineTo, indexTo = self.getSelection()
        if indexTo == 0:
            endLine = lineTo - 1
        else:
            endLine = lineTo
        
        self.beginUndoAction()
        # iterate over the lines
        for line in range(lineFrom, endLine + 1):
            # check if line starts with our comment string (i.e. was commented
            # by our comment...() slots
            if not self.__isCommentedLine(self.text(line), commentStr):
                continue
            
            if Preferences.getEditor("CommentColumn0"):
                self.setSelection(line, 0, line, len(commentStr))
            else:
                self.setSelection(line,
                                  self.indentation(line),
                                  line,
                                  self.indentation(line) + len(commentStr))
            self.removeSelectedText()
            
            # adjust selection start
            if line == lineFrom:
                indexFrom -= len(commentStr)
                if indexFrom < 0:
                    indexFrom = 0
            
            # adjust selection end
            if line == lineTo:
                indexTo -= len(commentStr)
                if indexTo < 0:
                    indexTo = 0
            
        # change the selection accordingly
        self.setSelection(lineFrom, indexFrom, lineTo, indexTo)
        self.endUndoAction()
        
    def commentLineOrSelection(self):
        """
        Public slot to comment the current line or current selection.
        """
        if self.hasSelectedText():
            self.commentSelection()
        else:
            self.commentLine()

    def uncommentLineOrSelection(self):
        """
        Public slot to uncomment the current line or current selection.
        """
        if self.hasSelectedText():
            self.uncommentSelection()
        else:
            self.uncommentLine()

    def streamCommentLine(self):
        """
        Public slot to stream comment the current line.
        """
        if self.lexer_ is None or not self.lexer_.canStreamComment():
            return
        
        commentStr = self.lexer_.streamCommentStr()
        line, index = self.getCursorPosition()
        
        self.beginUndoAction()
        self.insertAt(commentStr['end'], line, self.lineLength(line))
        self.insertAt(commentStr['start'], line, 0)
        self.endUndoAction()
        
    def streamCommentSelection(self):
        """
        Public slot to comment the current selection.
        """
        if self.lexer_ is None or not self.lexer_.canStreamComment():
            return
        
        if not self.hasSelectedText():
            return
        
        commentStr = self.lexer_.streamCommentStr()
        
        # get the selection boundaries
        lineFrom, indexFrom, lineTo, indexTo = self.getSelection()
        if indexTo == 0:
            endLine = lineTo - 1
            endIndex = self.lineLength(endLine)
        else:
            endLine = lineTo
            endIndex = indexTo
        
        self.beginUndoAction()
        self.insertAt(commentStr['end'], endLine, endIndex)
        self.insertAt(commentStr['start'], lineFrom, indexFrom)
        
        # change the selection accordingly
        if indexTo > 0:
            indexTo += len(commentStr['end'])
            if lineFrom == endLine:
                indexTo += len(commentStr['start'])
        self.setSelection(lineFrom, indexFrom, lineTo, indexTo)
        self.endUndoAction()
        
    def streamCommentLineOrSelection(self):
        """
        Public slot to stream comment the current line or current selection.
        """
        if self.hasSelectedText():
            self.streamCommentSelection()
        else:
            self.streamCommentLine()
        
    def boxCommentLine(self):
        """
        Public slot to box comment the current line.
        """
        if self.lexer_ is None or not self.lexer_.canBoxComment():
            return
        
        commentStr = self.lexer_.boxCommentStr()
        line, index = self.getCursorPosition()
        
        eol = self.getLineSeparator()
        self.beginUndoAction()
        self.insertAt(eol, line, self.lineLength(line))
        self.insertAt(commentStr['end'], line + 1, 0)
        self.insertAt(commentStr['middle'], line, 0)
        self.insertAt(eol, line, 0)
        self.insertAt(commentStr['start'], line, 0)
        self.endUndoAction()
        
    def boxCommentSelection(self):
        """
        Public slot to box comment the current selection.
        """
        if self.lexer_ is None or not self.lexer_.canBoxComment():
            return
        
        if not self.hasSelectedText():
            return
            
        commentStr = self.lexer_.boxCommentStr()
        
        # get the selection boundaries
        lineFrom, indexFrom, lineTo, indexTo = self.getSelection()
        if indexTo == 0:
            endLine = lineTo - 1
        else:
            endLine = lineTo
        
        self.beginUndoAction()
        # iterate over the lines
        for line in range(lineFrom, endLine + 1):
            self.insertAt(commentStr['middle'], line, 0)
        
        # now do the comments before and after the selection
        eol = self.getLineSeparator()
        self.insertAt(eol, endLine, self.lineLength(endLine))
        self.insertAt(commentStr['end'], endLine + 1, 0)
        self.insertAt(eol, lineFrom, 0)
        self.insertAt(commentStr['start'], lineFrom, 0)
        
        # change the selection accordingly
        self.setSelection(lineFrom, 0, endLine + 3, 0)
        self.endUndoAction()
        
    def boxCommentLineOrSelection(self):
        """
        Public slot to box comment the current line or current selection.
        """
        if self.hasSelectedText():
            self.boxCommentSelection()
        else:
            self.boxCommentLine()
    
    ###########################################################################
    ## Indentation handling methods below
    ###########################################################################

    def __indentLine(self, indent=True):
        """
        Private method to indent or unindent the current line.
        
        @param indent flag indicating an indent operation (boolean)
                <br />If the flag is true, an indent operation is performed.
                Otherwise the current line is unindented.
        """
        line, index = self.getCursorPosition()
        self.beginUndoAction()
        if indent:
            self.indent(line)
        else:
            self.unindent(line)
        self.endUndoAction()
        if indent:
            self.setCursorPosition(line, index + self.indentationWidth())
        else:
            self.setCursorPosition(line, index - self.indentationWidth())
        
    def __indentSelection(self, indent=True):
        """
        Private method to indent or unindent the current selection.
        
        @param indent flag indicating an indent operation (boolean)
                <br />If the flag is true, an indent operation is performed.
                Otherwise the current line is unindented.
        """
        if not self.hasSelectedText():
            return
        
        # get the selection
        lineFrom, indexFrom, lineTo, indexTo = self.getSelection()
        
        if indexTo == 0:
            endLine = lineTo - 1
        else:
            endLine = lineTo
        
        self.beginUndoAction()
        # iterate over the lines
        for line in range(lineFrom, endLine + 1):
            if indent:
                self.indent(line)
            else:
                self.unindent(line)
        self.endUndoAction()
        if indent:
            if indexTo == 0:
                self.setSelection(
                    lineFrom, indexFrom + self.indentationWidth(),
                    lineTo, 0)
            else:
                self.setSelection(
                    lineFrom, indexFrom + self.indentationWidth(),
                    lineTo, indexTo + self.indentationWidth())
        else:
            indexStart = indexFrom - self.indentationWidth()
            if indexStart < 0:
                indexStart = 0
            indexEnd = indexTo - self.indentationWidth()
            if indexEnd < 0:
                indexEnd = 0
            self.setSelection(lineFrom, indexStart, lineTo, indexEnd)
        
    def indentLineOrSelection(self):
        """
        Public slot to indent the current line or current selection.
        """
        if self.hasSelectedText():
            self.__indentSelection(True)
        else:
            self.__indentLine(True)
        
    def unindentLineOrSelection(self):
        """
        Public slot to unindent the current line or current selection.
        """
        if self.hasSelectedText():
            self.__indentSelection(False)
        else:
            self.__indentLine(False)
        
    def smartIndentLineOrSelection(self):
        """
        Public slot to indent current line smartly.
        """
        if self.hasSelectedText():
            if self.lexer_ and self.lexer_.hasSmartIndent():
                self.lexer_.smartIndentSelection(self)
            else:
                self.__indentSelection(True)
        else:
            if self.lexer_ and self.lexer_.hasSmartIndent():
                self.lexer_.smartIndentLine(self)
            else:
                self.__indentLine(True)
        
    def gotoLine(self, line, pos=1, firstVisible=False):
        """
        Public slot to jump to the beginning of a line.
        
        @param line line number to go to (integer)
        @keyparam pos position in line to go to (integer)
        @keyparam firstVisible flag indicating to make the line the first
            visible line (boolean)
        """
        self.setCursorPosition(line - 1, pos - 1)
        if firstVisible:
            self.ensureVisibleTop(line)
        else:
            self.ensureVisible(line)
    
    def __textChanged(self):
        """
        Private slot to handle a change of the editor text.
        
        This slot defers the handling to the next time the event loop
        is run in order to ensure, that cursor position has been updated
        by the underlying Scintilla editor.
        """
        QTimer.singleShot(0, self.__saveLastEditPosition)
    
    def __saveLastEditPosition(self):
        """
        Private slot to record the last edit position.
        """
        self.__lastEditPosition = self.getCursorPosition()
        self.lastEditPositionAvailable.emit()
    
    def isLastEditPositionAvailable(self):
        """
        Public method to check, if a last edit position is available.
        
        @return flag indicating availability (boolean)
        """
        return self.__lastEditPosition is not None
    
    def gotoLastEditPosition(self):
        """
        Public method to move the cursor to the last edit position.
        """
        self.setCursorPosition(*self.__lastEditPosition)
        self.ensureVisible(self.__lastEditPosition[0])
    
    def gotoMethodClass(self, goUp=False):
        """
        Public method to go to the next Python method or class definition.
        
        @param goUp flag indicating the move direction (boolean)
        """
        if self.isPyFile() or self.isRubyFile():
            lineNo = self.getCursorPosition()[0]
            line = self.text(lineNo)
            if line.strip().startswith(("class ", "def ", "module ")):
                if goUp:
                    lineNo -= 1
                else:
                    lineNo += 1
            while True:
                if goUp and lineNo < 0:
                    self.setCursorPosition(0, 0)
                    self.ensureVisible(0)
                    return
                elif not goUp and lineNo == self.lines():
                    lineNo = self.lines() - 1
                    self.setCursorPosition(lineNo, self.lineLength(lineNo))
                    self.ensureVisible(lineNo)
                    return
                
                line = self.text(lineNo)
                if line.strip().startswith(("class ", "def ", "module ")):
                    # try 'def ' first because it occurs more often
                    first = line.find("def ")
                    if first > -1:
                        first += 4
                    else:
                        first = line.find("class ")
                        if first > -1:
                            first += 6
                        else:
                            first = line.find("module ") + 7
                    match = re.search("[:(]", line)
                    if match:
                        end = match.start()
                    else:
                        end = self.lineLength(lineNo) - 1
                    self.setSelection(lineNo, first, lineNo, end)
                    self.ensureVisible(lineNo)
                    return
                
                if goUp:
                    lineNo -= 1
                else:
                    lineNo += 1
    
    ###########################################################################
    ## Setup methods below
    ###########################################################################

    def readSettings(self):
        """
        Public slot to read the settings into our lexer.
        """
        # read the lexer settings and reinit the properties
        if self.lexer_ is not None:
            self.lexer_.readSettings(Preferences.Prefs.settings, "Scintilla")
            self.lexer_.initProperties()
            
            self.lexer_.setDefaultColor(self.lexer_.color(0))
            self.lexer_.setDefaultPaper(self.lexer_.paper(0))
        
        self.__bindLexer(self.fileName)
        self.recolor()
        
        # read the typing completer settings
        if self.completer is not None:
            self.completer.readSettings()
        
        # set the margins layout
        if QSCINTILLA_VERSION() >= 0x020301:
            self.__unifiedMargins = Preferences.getEditor("UnifiedMargins")
        
        # set the line marker colours
        self.__setLineMarkerColours()
        
        # set the text display
        self.__setTextDisplay()
        
        # set margin 0 and 2 configuration
        self.__setMarginsDisplay()
        
        # set the autocompletion and calltips function
        self.__setAutoCompletion()
        self.__setCallTips()
        
        # set the autosave flags
        self.autosaveEnabled = Preferences.getEditor("AutosaveInterval") > 0
        
        if Preferences.getEditor("MiniContextMenu") != self.miniMenu:
            # regenerate context menu
            self.__initContextMenu()
        else:
            # set checked context menu items
            self.menuActs["AutoCompletionEnable"].setChecked(
                self.autoCompletionThreshold() != -1)
            self.menuActs["MonospacedFont"].setChecked(
                self.useMonospaced)
            self.menuActs["AutosaveEnable"].setChecked(
                self.autosaveEnabled and not self.autosaveManuallyDisabled)
        
        # regenerate the margins context menu(s)
        self.__initContextMenuMargins()
        
        if Preferences.getEditor("MarkOccurrencesEnabled"):
            self.__markOccurrencesTimer.setInterval(
                Preferences.getEditor("MarkOccurrencesTimeout"))
        else:
            self.__markOccurrencesTimer.stop()
            self.clearSearchIndicators()
        
        if Preferences.getEditor("OnlineSyntaxCheck"):
            self.__onlineSyntaxCheckTimer.setInterval(
                Preferences.getEditor("OnlineSyntaxCheckInterval") * 1000)
        else:
            self.__onlineSyntaxCheckTimer.stop()
        
        if Preferences.getEditor("OnlineChangeTrace"):
            self.__onlineChangeTraceTimer.setInterval(
                Preferences.getEditor("OnlineChangeTraceInterval"))
        else:
            self.__onlineChangeTraceTimer.stop()
            self.__deleteAllChangeMarkers()
        self.markerDefine(self.__createChangeMarkerPixmap(
            "OnlineChangeTraceMarkerUnsaved"), self.__changeMarkerUnsaved)
        self.markerDefine(self.__createChangeMarkerPixmap(
            "OnlineChangeTraceMarkerSaved"), self.__changeMarkerSaved)
        
        # refresh the annotations display
        self.__refreshAnnotations()
        
        self.__markerMap.initColors()
    
    def __setLineMarkerColours(self):
        """
        Private method to set the line marker colours.
        """
        self.setMarkerForegroundColor(
            Preferences.getEditorColour("CurrentMarker"), self.currentline)
        self.setMarkerBackgroundColor(
            Preferences.getEditorColour("CurrentMarker"), self.currentline)
        self.setMarkerForegroundColor(
            Preferences.getEditorColour("ErrorMarker"), self.errorline)
        self.setMarkerBackgroundColor(
            Preferences.getEditorColour("ErrorMarker"), self.errorline)
        
    def __setMarginsDisplay(self):
        """
        Private method to configure margins 0 and 2.
        """
        # set the settings for all margins
        self.setMarginsFont(Preferences.getEditorOtherFonts("MarginsFont"))
        self.setMarginsForegroundColor(
            Preferences.getEditorColour("MarginsForeground"))
        self.setMarginsBackgroundColor(
            Preferences.getEditorColour("MarginsBackground"))
        
        # reset standard margins settings
        for margin in range(5):
            self.setMarginLineNumbers(margin, False)
            self.setMarginMarkerMask(margin, 0)
            self.setMarginWidth(margin, 0)
            self.setMarginSensitivity(margin, False)
        
        # set marker margin(s) settings
        if self.__unifiedMargins:
            margin1Mask = (1 << self.breakpoint) | \
                          (1 << self.cbreakpoint) | \
                          (1 << self.tbreakpoint) | \
                          (1 << self.tcbreakpoint) | \
                          (1 << self.dbreakpoint) | \
                          (1 << self.currentline) | \
                          (1 << self.errorline) | \
                          (1 << self.bookmark) | \
                          (1 << self.syntaxerror) | \
                          (1 << self.notcovered) | \
                          (1 << self.taskmarker) | \
                          (1 << self.warning) | \
                          (1 << self.__changeMarkerUnsaved) | \
                          (1 << self.__changeMarkerSaved)
            self.setMarginWidth(1, 16)
            self.setMarginSensitivity(1, True)
            self.setMarginMarkerMask(1, margin1Mask)
            
            self.__linenoMargin = 0
            self.__foldMargin = 2
        else:
            
            self.__bmMargin = 0
            self.__linenoMargin = 1
            self.__bpMargin = 2
            self.__foldMargin = 3
            self.__indicMargin = 4
            
            marginBmMask = (1 << self.bookmark)
            self.setMarginWidth(self.__bmMargin, 16)
            self.setMarginSensitivity(self.__bmMargin, True)
            self.setMarginMarkerMask(self.__bmMargin, marginBmMask)
            
            marginBpMask = (1 << self.breakpoint) | \
                           (1 << self.cbreakpoint) | \
                           (1 << self.tbreakpoint) | \
                           (1 << self.tcbreakpoint) | \
                           (1 << self.dbreakpoint) | \
                           (1 << self.currentline) | \
                           (1 << self.errorline)
            self.setMarginWidth(self.__bpMargin, 16)
            self.setMarginSensitivity(self.__bpMargin, True)
            self.setMarginMarkerMask(self.__bpMargin, marginBpMask)
            
            marginIndicMask = (1 << self.syntaxerror) | \
                              (1 << self.notcovered) | \
                              (1 << self.taskmarker) | \
                              (1 << self.warning) | \
                              (1 << self.__changeMarkerUnsaved) | \
                              (1 << self.__changeMarkerSaved)
            self.setMarginWidth(self.__indicMargin, 16)
            self.setMarginSensitivity(self.__indicMargin, True)
            self.setMarginMarkerMask(self.__indicMargin, marginIndicMask)
        
        # set linenumber margin settings
        linenoMargin = Preferences.getEditor("LinenoMargin")
        self.setMarginLineNumbers(self.__linenoMargin, linenoMargin)
        if linenoMargin:
            self.__resizeLinenoMargin()
        else:
            self.setMarginWidth(self.__linenoMargin, 0)
        
        # set folding margin settings
        if Preferences.getEditor("FoldingMargin"):
            self.setMarginWidth(self.__foldMargin, 16)
            folding = Preferences.getEditor("FoldingStyle")
            try:
                folding = QsciScintilla.FoldStyle(folding)
            except AttributeError:
                pass
            self.setFolding(folding, self.__foldMargin)
            self.setFoldMarginColors(
                Preferences.getEditorColour("FoldmarginBackground"),
                Preferences.getEditorColour("FoldmarginBackground"))
            self.setFoldMarkersColors(
                Preferences.getEditorColour("FoldMarkersForeground"),
                Preferences.getEditorColour("FoldMarkersBackground"))
        else:
            self.setMarginWidth(self.__foldMargin, 0)
            self.setFolding(QsciScintilla.NoFoldStyle, self.__foldMargin)
    
    def __resizeLinenoMargin(self):
        """
        Private slot to resize the line numbers margin.
        """
        linenoMargin = Preferences.getEditor("LinenoMargin")
        if linenoMargin:
            self.setMarginWidth(
                self.__linenoMargin, '8' * (len(str(self.lines())) + 1))
    
    def __setTextDisplay(self):
        """
        Private method to configure the text display.
        """
        self.setTabWidth(Preferences.getEditor("TabWidth"))
        self.setIndentationWidth(Preferences.getEditor("IndentWidth"))
        if self.lexer_ and self.lexer_.alwaysKeepTabs():
            self.setIndentationsUseTabs(True)
        else:
            self.setIndentationsUseTabs(
                Preferences.getEditor("TabForIndentation"))
        self.setTabIndents(Preferences.getEditor("TabIndents"))
        self.setBackspaceUnindents(Preferences.getEditor("TabIndents"))
        self.setIndentationGuides(Preferences.getEditor("IndentationGuides"))
        self.setIndentationGuidesBackgroundColor(
            Preferences.getEditorColour("IndentationGuidesBackground"))
        self.setIndentationGuidesForegroundColor(
            Preferences.getEditorColour("IndentationGuidesForeground"))
        if Preferences.getEditor("ShowWhitespace"):
            self.setWhitespaceVisibility(QsciScintilla.WsVisible)
            try:
                self.setWhitespaceForegroundColor(
                    Preferences.getEditorColour("WhitespaceForeground"))
                self.setWhitespaceBackgroundColor(
                    Preferences.getEditorColour("WhitespaceBackground"))
                self.setWhitespaceSize(
                    Preferences.getEditor("WhitespaceSize"))
            except AttributeError:
                # QScintilla before 2.5 doesn't support this
                pass
        else:
            self.setWhitespaceVisibility(QsciScintilla.WsInvisible)
        self.setEolVisibility(Preferences.getEditor("ShowEOL"))
        self.setAutoIndent(Preferences.getEditor("AutoIndentation"))
        if Preferences.getEditor("BraceHighlighting"):
            self.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        else:
            self.setBraceMatching(QsciScintilla.NoBraceMatch)
        self.setMatchedBraceForegroundColor(
            Preferences.getEditorColour("MatchingBrace"))
        self.setMatchedBraceBackgroundColor(
            Preferences.getEditorColour("MatchingBraceBack"))
        self.setUnmatchedBraceForegroundColor(
            Preferences.getEditorColour("NonmatchingBrace"))
        self.setUnmatchedBraceBackgroundColor(
            Preferences.getEditorColour("NonmatchingBraceBack"))
        if Preferences.getEditor("CustomSelectionColours"):
            self.setSelectionBackgroundColor(
                Preferences.getEditorColour("SelectionBackground"))
        else:
            self.setSelectionBackgroundColor(
                QApplication.palette().color(QPalette.Highlight))
        if Preferences.getEditor("ColourizeSelText"):
            self.resetSelectionForegroundColor()
        elif Preferences.getEditor("CustomSelectionColours"):
            self.setSelectionForegroundColor(
                Preferences.getEditorColour("SelectionForeground"))
        else:
            self.setSelectionForegroundColor(
                QApplication.palette().color(QPalette.HighlightedText))
        self.setSelectionToEol(Preferences.getEditor("ExtendSelectionToEol"))
        self.setCaretForegroundColor(
            Preferences.getEditorColour("CaretForeground"))
        self.setCaretLineBackgroundColor(
            Preferences.getEditorColour("CaretLineBackground"))
        self.setCaretLineVisible(Preferences.getEditor("CaretLineVisible"))
        self.setCaretLineAlwaysVisible(
            Preferences.getEditor("CaretLineAlwaysVisible"))
        self.caretWidth = Preferences.getEditor("CaretWidth")
        self.setCaretWidth(self.caretWidth)
        self.useMonospaced = Preferences.getEditor("UseMonospacedFont")
        self.setMonospaced(self.useMonospaced)
        edgeMode = Preferences.getEditor("EdgeMode")
        edge = QsciScintilla.EdgeMode(edgeMode)
        self.setEdgeMode(edge)
        if edgeMode:
            self.setEdgeColumn(Preferences.getEditor("EdgeColumn"))
            self.setEdgeColor(Preferences.getEditorColour("Edge"))
        
        wrapVisualFlag = Preferences.getEditor("WrapVisualFlag")
        self.setWrapMode(Preferences.getEditor("WrapLongLinesMode"))
        self.setWrapVisualFlags(wrapVisualFlag, wrapVisualFlag)
        
        self.zoomTo(Preferences.getEditor("ZoomFactor"))
        
        self.searchIndicator = QsciScintilla.INDIC_CONTAINER
        self.indicatorDefine(
            self.searchIndicator, QsciScintilla.INDIC_BOX,
            Preferences.getEditorColour("SearchMarkers"))
        if not Preferences.getEditor("SearchMarkersEnabled") and \
           not Preferences.getEditor("QuickSearchMarkersEnabled") and \
           not Preferences.getEditor("MarkOccurrencesEnabled"):
            self.clearAllIndicators(self.searchIndicator)
        
        self.spellingIndicator = QsciScintilla.INDIC_CONTAINER + 1
        self.indicatorDefine(
            self.spellingIndicator, QsciScintilla.INDIC_SQUIGGLE,
            Preferences.getEditorColour("SpellingMarkers"))
        self.__setSpelling()
        
        self.setCursorFlashTime(QApplication.cursorFlashTime())
        
        try:
            if Preferences.getEditor("AnnotationsEnabled"):
                self.setAnnotationDisplay(QsciScintilla.AnnotationBoxed)
            else:
                self.setAnnotationDisplay(QsciScintilla.AnnotationHidden)
        except AttributeError:
            pass
        self.__setAnnotationStyles()
        
        if Preferences.getEditor("OverrideEditAreaColours"):
            self.setColor(Preferences.getEditorColour("EditAreaForeground"))
            self.setPaper(Preferences.getEditorColour("EditAreaBackground"))
        
        self.setVirtualSpaceOptions(
            Preferences.getEditor("VirtualSpaceOptions"))
        
        self.__markerMap.setEnabled(True)
    
    def __setEolMode(self):
        """
        Private method to configure the eol mode of the editor.
        """
        if self.fileName and \
           self.project.isOpen() and \
           self.project.isProjectFile(self.fileName):
            self.setEolModeByEolString(self.project.getEolString())
        else:
            eolMode = Preferences.getEditor("EOLMode")
            eolMode = QsciScintilla.EolMode(eolMode)
            self.setEolMode(eolMode)
        self.__eolChanged()
        
    def __setAutoCompletion(self):
        """
        Private method to configure the autocompletion function.
        """
        if self.lexer_:
            self.setAutoCompletionFillupsEnabled(
                Preferences.getEditor("AutoCompletionFillups"))
        self.setAutoCompletionCaseSensitivity(
            Preferences.getEditor("AutoCompletionCaseSensitivity"))
        self.setAutoCompletionReplaceWord(
            Preferences.getEditor("AutoCompletionReplaceWord"))
        try:
            self.setAutoCompletionUseSingle(
                Preferences.getEditor("AutoCompletionShowSingle"))
        except AttributeError:
            self.setAutoCompletionShowSingle(
                Preferences.getEditor("AutoCompletionShowSingle"))
        autoCompletionSource = Preferences.getEditor("AutoCompletionSource")
        if autoCompletionSource == QsciScintilla.AcsDocument:
            self.setAutoCompletionSource(QsciScintilla.AcsDocument)
        elif autoCompletionSource == QsciScintilla.AcsAPIs:
            self.setAutoCompletionSource(QsciScintilla.AcsAPIs)
        else:
            self.setAutoCompletionSource(QsciScintilla.AcsAll)
        if Preferences.getEditor("AutoCompletionEnabled"):
            if self.__acHookFunction is None or \
                    not self.__completionListHookFunctions:
                self.setAutoCompletionThreshold(
                    Preferences.getEditor("AutoCompletionThreshold"))
            else:
                self.setAutoCompletionThreshold(0)
        else:
            self.setAutoCompletionThreshold(-1)
            self.setAutoCompletionSource(QsciScintilla.AcsNone)
        
    def __setCallTips(self):
        """
        Private method to configure the calltips function.
        """
        self.setCallTipsBackgroundColor(
            Preferences.getEditorColour("CallTipsBackground"))
        self.setCallTipsVisible(Preferences.getEditor("CallTipsVisible"))
        calltipsStyle = Preferences.getEditor("CallTipsStyle")
        try:
            self.setCallTipsPosition(
                Preferences.getEditor("CallTipsPosition"))
        except AttributeError:
            pass
        
        if Preferences.getEditor("CallTipsEnabled"):
            if calltipsStyle == QsciScintilla.CallTipsNoContext:
                self.setCallTipsStyle(QsciScintilla.CallTipsNoContext)
            elif calltipsStyle == \
                    QsciScintilla.CallTipsNoAutoCompletionContext:
                self.setCallTipsStyle(
                    QsciScintilla.CallTipsNoAutoCompletionContext)
            else:
                self.setCallTipsStyle(QsciScintilla.CallTipsContext)
        else:
            self.setCallTipsStyle(QsciScintilla.CallTipsNone)

    ###########################################################################
    ## Autocompletion handling methods below
    ###########################################################################

    def canAutoCompleteFromAPIs(self):
        """
        Public method to check for API availablity.
        
        @return flag indicating autocompletion from APIs is available (boolean)
        """
        return self.acAPI
        
    def autoCompleteQScintilla(self):
        """
        Public method to perform an autocompletion using QScintilla methods.
        """
        acs = Preferences.getEditor("AutoCompletionSource")
        if acs == QsciScintilla.AcsDocument:
            self.autoCompleteFromDocument()
        elif acs == QsciScintilla.AcsAPIs:
            self.autoCompleteFromAPIs()
        elif acs == QsciScintilla.AcsAll:
            self.autoCompleteFromAll()
        else:
            E5MessageBox.information(
                self,
                self.tr("Autocompletion"),
                self.tr(
                    """Autocompletion is not available because"""
                    """ there is no autocompletion source set."""))
        
    def setAutoCompletionEnabled(self, enable):
        """
        Public method to enable/disable autocompletion.
        
        @param enable flag indicating the desired autocompletion status
            (boolean)
        """
        if enable:
            self.setAutoCompletionThreshold(
                Preferences.getEditor("AutoCompletionThreshold"))
            autoCompletionSource = \
                Preferences.getEditor("AutoCompletionSource")
            if autoCompletionSource == QsciScintilla.AcsDocument:
                self.setAutoCompletionSource(QsciScintilla.AcsDocument)
            elif autoCompletionSource == QsciScintilla.AcsAPIs:
                self.setAutoCompletionSource(QsciScintilla.AcsAPIs)
            else:
                self.setAutoCompletionSource(QsciScintilla.AcsAll)
        else:
            self.setAutoCompletionThreshold(-1)
            self.setAutoCompletionSource(QsciScintilla.AcsNone)
        
    def __toggleAutoCompletionEnable(self):
        """
        Private slot to handle the Enable Autocompletion context menu entry.
        """
        if self.menuActs["AutoCompletionEnable"].isChecked():
            self.setAutoCompletionEnabled(True)
        else:
            self.setAutoCompletionEnabled(False)
    
    #################################################################
    ## Support for autocompletion hook methods
    #################################################################
    
    def __charAdded(self, charNumber):
        """
        Private slot called to handle the user entering a character.
        
        @param charNumber value of the character entered (integer)
        """
        if self.isListActive():
            char = chr(charNumber)
            if self.__isStartChar(char):
                self.cancelList()
                self.autoComplete(auto=True, context=True)
                return
            elif char == '(':
                self.cancelList()
        
        if self.callTipsStyle() != QsciScintilla.CallTipsNone and \
           self.lexer_ is not None and chr(charNumber) in '()':
            self.callTip()
        
        if not self.isCallTipActive():
            char = chr(charNumber)
            if self.__isStartChar(char):
                self.autoComplete(auto=True, context=True)
                return
            
            line, col = self.getCursorPosition()
            txt = self.getWordLeft(line, col)
            if len(txt) >= Preferences.getEditor("AutoCompletionThreshold"):
                self.autoComplete(auto=True, context=False)
                return
    
    def __isStartChar(self, ch):
        """
        Private method to check, if a character is an autocompletion start
        character.
        
        @param ch character to be checked (one character string)
        @return flag indicating the result (boolean)
        """
        if self.lexer_ is None:
            return False
        
        wseps = self.lexer_.autoCompletionWordSeparators()
        for wsep in wseps:
            if wsep.endswith(ch):
                return True
        
        return False
    
    #####################################################
    ## old auto-completion hook interfaces (before 6.1.0)
    #####################################################
    
    def setAutoCompletionHook(self, func):
        """
        Public method to set an autocompletion hook.
        
        @param func Function to be set to handle autocompletion. func
            should be a function taking a reference to the editor and
            a boolean indicating to complete a context.
        """
        if self.__acHookFunction is not None:
            # there is another provider registered already
            E5MessageBox.warning(
                self,
                self.tr("Activating Auto-Completion Provider"),
                self.tr("""Auto-completion provider cannot be connected"""
                        """ because there is already another one active."""
                        """ Please check your configuration."""))
            return
        
        if self.autoCompletionThreshold() > 0:
            self.setAutoCompletionThreshold(0)
        self.__acHookFunction = func
        self.SCN_CHARADDED.connect(self.__charAdded)
    
    def unsetAutoCompletionHook(self):
        """
        Public method to unset a previously installed autocompletion hook.
        """
        self.SCN_CHARADDED.disconnect(self.__charAdded)
        self.__acHookFunction = None
        if self.autoCompletionThreshold() == 0:
            self.setAutoCompletionThreshold(
                Preferences.getEditor("AutoCompletionThreshold"))
    
    def autoCompletionHook(self):
        """
        Public method to get the autocompletion hook function.
        
        @return function set by setAutoCompletionHook()
        """
        return self.__acHookFunction
    
    ########################################################
    ## new auto-completion hook interfaces (6.1.0 and later)
    ########################################################
    
    def addCompletionListHook(self, key, func):
        """
        Public method to set an auto-completion list provider.
        
        @param key name of the provider
        @type str
        @param func function providing completion list. func
            should be a function taking a reference to the editor and
            a boolean indicating to complete a context. It should return
            the possible completions as a list of strings.
        @type function(editor, bool) -> list of str
        """
        if key in self.__completionListHookFunctions:
            # it was already registered
            E5MessageBox.warning(
                self,
                self.tr("Auto-Completion Provider"),
                self.tr("""The completion list provider '{0}' was already"""
                        """ registered. Ignoring duplicate request.""")
                .format(key))
            return
        
        if not self.__completionListHookFunctions:
            if self.autoCompletionThreshold() > 0:
                self.setAutoCompletionThreshold(0)
            self.SCN_CHARADDED.connect(self.__charAdded)
        self.__completionListHookFunctions[key] = func
    
    def removeCompletionListHook(self, key):
        """
        Public method to remove a previously registered completion list
        provider.
        
        @param key name of the provider
        @type str
        """
        if key in self.__completionListHookFunctions:
            del self.__completionListHookFunctions[key]
        
        if not self.__completionListHookFunctions:
            self.SCN_CHARADDED.disconnect(self.__charAdded)
            if self.autoCompletionThreshold() == 0:
                self.setAutoCompletionThreshold(
                    Preferences.getEditor("AutoCompletionThreshold"))
    
    def getCompletionListHook(self, key):
        """
        Public method to get the registered completion list provider.
        
        @param key name of the provider
        @type str
        @return function providing completion list
        @rtype function or None
        """
        if key in self.__completionListHookFunctions:
            return self.__completionListHookFunctions[key]
        else:
            return None
    
    def autoComplete(self, auto=False, context=True):
        """
        Public method to start autocompletion.
        
        @keyparam auto flag indicating a call from the __charAdded method
            (boolean)
        @keyparam context flag indicating to complete a context (boolean)
        """
        if auto and self.autoCompletionThreshold() == -1:
            # autocompletion is disabled
            return
        
        if self.__completionListHookFunctions:
            if self.isListActive():
                self.cancelList()
            completionsList = []
            for key in self.__completionListHookFunctions:
                completionsList.extend(
                    self.__completionListHookFunctions[key](self, context))
            completionsList = list(set(completionsList))
            if len(completionsList) == 0:
                if Preferences.getEditor("AutoCompletionScintillaOnFail") and \
                    (self.autoCompletionSource() != QsciScintilla.AcsNone or
                     not auto):
                    self.autoCompleteQScintilla()
            else:
                completionsList.sort()
                self.showUserList(EditorAutoCompletionListID,
                                  completionsList)
        elif self.__acHookFunction is not None:
            # for backward compatibility
            self.__acHookFunction(self, context)
        elif not auto:
            self.autoCompleteQScintilla()
        elif self.autoCompletionSource() != QsciScintilla.AcsNone:
            self.autoCompleteQScintilla()
    
    def __completionListSelected(self, id, txt):
        """
        Private slot to handle the selection from the completion list.
        
        @param id the ID of the user list (should be 1) (integer)
        @param txt the selected text (string)
        """
        if id == EditorAutoCompletionListID:
            lst = txt.split()
            if len(lst) > 1:
                txt = lst[0]
            
            if Preferences.getEditor("AutoCompletionReplaceWord"):
                self.selectCurrentWord()
                self.removeSelectedText()
                line, col = self.getCursorPosition()
            else:
                line, col = self.getCursorPosition()
                wLeft = self.getWordLeft(line, col)
                if not txt.startswith(wLeft):
                    self.selectCurrentWord()
                    self.removeSelectedText()
                    line, col = self.getCursorPosition()
                elif wLeft:
                    txt = txt[len(wLeft):]
            self.insert(txt)
            self.setCursorPosition(line, col + len(txt))
        elif id == TemplateCompletionListID:
            self.__applyTemplate(txt, self.getLanguage())
    
    def canProvideDynamicAutoCompletion(self):
        """
        Public method to test the dynamic auto-completion availability.
        
        @return flag indicating the availability of dynamic auto-completion
            (boolean)
        """
        return (self.acAPI or
                self.__acHookFunction is not None or
                bool(self.__completionListHookFunctions))
    
    def callTip(self):
        """
        Public method to show calltips.
        """
        if bool(self.__ctHookFunctions) or self.__ctHookFunction is not None:
            self.__callTip()
        else:
            super(Editor, self).callTip()
    
    def __callTip(self):
        """
        Private method to show call tips provided by a plugin.
        """
        pos = self.currentPosition()
        
        # move backward to the start of the current calltip working out
        # which argument to highlight
        commas = 0
        found = False
        ch, pos = self.__getCharacter(pos)
        while ch:
            if ch == ',':
                commas += 1
            elif ch == ')':
                depth = 1
                
                # ignore everything back to the start of the corresponding
                # parenthesis
                ch, pos = self.__getCharacter(pos)
                while ch:
                    if ch == ')':
                        depth += 1
                    elif ch == '(':
                        depth -= 1
                        if depth == 0:
                            break
                    ch, pos = self.__getCharacter(pos)
            elif ch == '(':
                found = True
                break
            
            ch, pos = self.__getCharacter(pos)
        
        self.SendScintilla(QsciScintilla.SCI_CALLTIPCANCEL)
        
        if not found:
            return
        
        if self.__ctHookFunctions:
            callTips = []
            for key in self.__ctHookFunctions:
                callTips.extend(self.__ctHookFunctions[key](self, pos, commas))
            callTips = list(set(callTips))
            callTips.sort()
        else:
            # for backward compatibility
            callTips = self.__ctHookFunction(self, pos, commas)
        if len(callTips) == 0:
            if Preferences.getEditor("CallTipsScintillaOnFail"):
                # try QScintilla calltips
                super(Editor, self).callTip()
            return
        
        ctshift = 0
        for ct in callTips:
            shift = ct.index("(")
            if ctshift < shift:
                ctshift = shift
        
        cv = self.callTipsVisible()
        if cv > 0:
            # this is just a safe guard
            ct = self._encodeString("\n".join(callTips[:cv]))
        else:
            # until here and unindent below
            ct = self._encodeString("\n".join(callTips))
        
        self.SendScintilla(QsciScintilla.SCI_CALLTIPSHOW,
                           self.__adjustedCallTipPosition(ctshift, pos), ct)
        if b'\n' in ct:
            return
        
        # Highlight the current argument
        if commas == 0:
            astart = ct.find(b'(')
        else:
            astart = ct.find(b',')
            commas -= 1
            while astart != -1 and commas > 0:
                astart = ct.find(b',', astart + 1)
                commas -= 1
        
        if astart == -1:
            return
        
        depth = 0
        for aend in range(astart + 1, len(ct)):
            ch = ct[aend:aend + 1]
            
            if ch == b',' and depth == 0:
                break
            elif ch == b'(':
                depth += 1
            elif ch == b')':
                if depth == 0:
                    break
                
                depth -= 1
        
        if astart != aend:
            self.SendScintilla(QsciScintilla.SCI_CALLTIPSETHLT,
                               astart + 1, aend)
    
    def __adjustedCallTipPosition(self, ctshift, pos):
        """
        Private method to calculate an adjusted position for showing calltips.
        
        @param ctshift amount the calltip shall be shifted (integer)
        @param pos position into the text (integer)
        @return new position for the calltip (integer)
        """
        ct = pos
        if ctshift:
            ctmin = self.SendScintilla(
                QsciScintilla.SCI_POSITIONFROMLINE,
                self.SendScintilla(QsciScintilla.SCI_LINEFROMPOSITION, ct))
            if ct - ctshift < ctmin:
                ct = ctmin
            else:
                ct = ct - ctshift
        return ct
    
    ##############################################
    ## old calltips hook interfaces (before 6.1.0)
    ##############################################
    
    def setCallTipHook(self, func):
        """
        Public method to set a calltip hook.
        
        @param func Function to be set to determine calltips. func
            should be a function taking a reference to the editor,
            a position into the text and the amount of commas to the
            left of the cursor. It should return the possible
            calltips as a list of strings.
        """
        if self.__ctHookFunction is not None:
            # there is another provider registered already
            E5MessageBox.warning(
                self,
                self.tr("Activating Calltip Provider"),
                self.tr("""Calltip provider cannot be connected"""
                        """ because there is already another one active."""
                        """ Please check your configuration."""))
            return
        
        self.__ctHookFunction = func
    
    def unsetCallTipHook(self):
        """
        Public method to unset a calltip hook.
        """
        self.__ctHookFunction = None
    
    def callTipHook(self):
        """
        Public method to get the calltip hook function.
        
        @return function set by setCallTipHook()
        """
        return self.__ctHookFunction
    
    ########################################################
    ## new auto-completion hook interfaces (6.1.0 and later)
    ########################################################
    
    def addCallTipHook(self, key, func):
        """
        Public method to set a calltip provider.
        
        @param key name of the provider
        @type str
        @param func function providing calltips. func
            should be a function taking a reference to the editor,
            a position into the text and the amount of commas to the
            left of the cursor. It should return the possible
            calltips as a list of strings.
        @type function(editor, int, int) -> list of str
        """
        if key in self.__ctHookFunctions:
            # it was already registered
            E5MessageBox.warning(
                self,
                self.tr("Call-Tips Provider"),
                self.tr("""The call-tips provider '{0}' was already"""
                        """ registered. Ignoring duplicate request.""")
                .format(key))
            return
        
        self.__ctHookFunctions[key] = func
    
    def removeCallTipHook(self, key):
        """
        Public method to remove a previously registered calltip provider.
        
        @param key name of the provider
        @type str
        """
        if key in self.__ctHookFunctions:
            del self.__ctHookFunctions[key]
    
    def getCallTipHook(self, key):
        """
        Public method to get the registered calltip provider.
        
        @param key name of the provider
        @type str
        @return function providing calltips
        @rtype function or None
        """
        if key in self.__ctHookFunctions:
            return self.__ctHookFunctions[key]
        else:
            return None
    
    def canProvideCallTipps(self):
        """
        Public method to test the calltips availability.
        
        @return flag indicating the availability of calltips (boolean)
        """
        return (self.acAPI or
                self.__ctHookFunction is not None or
                bool(self.__ctHookFunctions))
    
    #################################################################
    ## Methods needed by the context menu
    #################################################################
    
    def __marginNumber(self, xPos):
        """
        Private method to calculate the margin number based on a x position.
        
        @param xPos x position (integer)
        @return margin number (integer, -1 for no margin)
        """
        width = 0
        for margin in range(5):
            width += self.marginWidth(margin)
            if xPos <= width:
                return margin
        return -1
        
    def contextMenuEvent(self, evt):
        """
        Protected method implementing the context menu event.
        
        @param evt the context menu event (QContextMenuEvent)
        """
        evt.accept()
        if self.__marginNumber(evt.x()) == -1:
            self.spellingMenuPos = self.positionFromPoint(evt.pos())
            if self.spellingMenuPos >= 0 and \
               self.spell is not None and \
               self.hasIndicator(self.spellingIndicator, self.spellingMenuPos):
                self.spellingMenu.popup(evt.globalPos())
            else:
                self.menu.popup(evt.globalPos())
        else:
            self.line = self.lineAt(evt.pos())
            if self.__unifiedMargins:
                self.marginMenu.popup(evt.globalPos())
            else:
                if self.__marginNumber(evt.x()) in [self.__bmMargin,
                                                    self.__linenoMargin]:
                    self.bmMarginMenu.popup(evt.globalPos())
                elif self.__marginNumber(evt.x()) == self.__bpMargin:
                    self.bpMarginMenu.popup(evt.globalPos())
                elif self.__marginNumber(evt.x()) == self.__indicMargin:
                    self.indicMarginMenu.popup(evt.globalPos())
        
    def __showContextMenu(self):
        """
        Private slot handling the aboutToShow signal of the context menu.
        """
        self.menuActs["Reopen"].setEnabled(
            not self.isModified() and bool(self.fileName))
        self.menuActs["Save"].setEnabled(self.isModified())
        self.menuActs["Undo"].setEnabled(self.isUndoAvailable())
        self.menuActs["Redo"].setEnabled(self.isRedoAvailable())
        self.menuActs["Revert"].setEnabled(self.isModified())
        if not self.miniMenu:
            self.menuActs["Cut"].setEnabled(self.hasSelectedText())
            self.menuActs["Copy"].setEnabled(self.hasSelectedText())
        if not self.isResourcesFile:
            if self.fileName and self.isPyFile():
                self.menuActs["Show"].setEnabled(True)
            else:
                self.menuActs["Show"].setEnabled(False)
            if self.fileName and \
               (self.isPyFile() or self.isRubyFile()):
                self.menuActs["Diagrams"].setEnabled(True)
            else:
                self.menuActs["Diagrams"].setEnabled(False)
        if not self.miniMenu:
            if self.lexer_ is not None:
                self.menuActs["Comment"].setEnabled(
                    self.lexer_.canBlockComment())
                self.menuActs["Uncomment"].setEnabled(
                    self.lexer_.canBlockComment())
                self.menuActs["StreamComment"].setEnabled(
                    self.lexer_.canStreamComment())
                self.menuActs["BoxComment"].setEnabled(
                    self.lexer_.canBoxComment())
            else:
                self.menuActs["Comment"].setEnabled(False)
                self.menuActs["Uncomment"].setEnabled(False)
                self.menuActs["StreamComment"].setEnabled(False)
                self.menuActs["BoxComment"].setEnabled(False)
        
        self.menuActs["TypingAidsEnabled"].setEnabled(
            self.completer is not None)
        self.menuActs["TypingAidsEnabled"].setChecked(
            self.completer is not None and self.completer.isEnabled())
        
        if not self.isResourcesFile:
            self.menuActs["calltip"].setEnabled(self.acAPI)
        
        from .SpellChecker import SpellChecker
        spellingAvailable = SpellChecker.isAvailable()
        self.menuActs["SpellCheck"].setEnabled(spellingAvailable)
        self.menuActs["SpellCheckSelection"].setEnabled(
            spellingAvailable and self.hasSelectedText())
        self.menuActs["SpellCheckRemove"].setEnabled(
            spellingAvailable and self.spellingMenuPos >= 0)
        
        if self.menuActs["OpenRejections"]:
            if self.fileName:
                rej = "{0}.rej".format(self.fileName)
                self.menuActs["OpenRejections"].setEnabled(os.path.exists(rej))
            else:
                self.menuActs["OpenRejections"].setEnabled(False)
        
        self.menuActs["MonospacedFont"].setEnabled(self.lexer_ is None)
        
        splitOrientation = self.vm.getSplitOrientation()
        if splitOrientation == Qt.Horizontal:
            self.menuActs["NewSplit"].setIcon(
                UI.PixmapCache.getIcon("splitHorizontal.png"))
        else:
            self.menuActs["NewSplit"].setIcon(
                UI.PixmapCache.getIcon("splitVertical.png"))
        
        self.menuActs["Tools"].setEnabled(not self.toolsMenu.isEmpty())
        
        self.showMenu.emit("Main", self.menu, self)
        
    def __showContextMenuAutocompletion(self):
        """
        Private slot called before the autocompletion menu is shown.
        """
        self.menuActs["acDynamic"].setEnabled(
            self.canProvideDynamicAutoCompletion())
        self.menuActs["acAPI"].setEnabled(self.acAPI)
        self.menuActs["acAPIDocument"].setEnabled(self.acAPI)
        self.menuActs["calltip"].setEnabled(self.canProvideCallTipps())
        
        self.showMenu.emit("Autocompletion", self.autocompletionMenu, self)
        
    def __showContextMenuShow(self):
        """
        Private slot called before the show menu is shown.
        """
        prEnable = False
        coEnable = False
        
        # first check if the file belongs to a project
        if self.project.isOpen() and \
                self.project.isProjectSource(self.fileName):
            fn = self.project.getMainScript(True)
            if fn is not None:
                tfn = Utilities.getTestFileName(fn)
                basename = os.path.splitext(fn)[0]
                tbasename = os.path.splitext(tfn)[0]
                prEnable = prEnable or \
                    os.path.isfile("{0}.profile".format(basename)) or \
                    os.path.isfile("{0}.profile".format(tbasename))
                coEnable = (
                    coEnable or
                    os.path.isfile("{0}.coverage".format(basename)) or
                    os.path.isfile("{0}.coverage".format(tbasename))) and \
                    (self.project.isPy3Project() or
                        self.project.isPy2Project())
        
        # now check ourself
        fn = self.getFileName()
        if fn is not None:
            tfn = Utilities.getTestFileName(fn)
            basename = os.path.splitext(fn)[0]
            tbasename = os.path.splitext(tfn)[0]
            prEnable = prEnable or \
                os.path.isfile("{0}.profile".format(basename)) or \
                os.path.isfile("{0}.profile".format(tbasename))
            coEnable = (
                coEnable or
                os.path.isfile("{0}.coverage".format(basename)) or
                os.path.isfile("{0}.coverage".format(tbasename))) and \
                self.isPyFile()
        
        # now check for syntax errors
        if self.hasSyntaxErrors():
            coEnable = False
        
        self.profileMenuAct.setEnabled(prEnable)
        self.coverageMenuAct.setEnabled(coEnable)
        self.coverageShowAnnotationMenuAct.setEnabled(
            coEnable and len(self.notcoveredMarkers) == 0)
        self.coverageHideAnnotationMenuAct.setEnabled(
            len(self.notcoveredMarkers) > 0)
        
        self.showMenu.emit("Show", self.menuShow, self)
        
    def __showContextMenuGraphics(self):
        """
        Private slot handling the aboutToShow signal of the diagrams context
        menu.
        """
        if self.project.isOpen() and \
                self.project.isProjectSource(self.fileName):
            self.applicationDiagramMenuAct.setEnabled(True)
        else:
            self.applicationDiagramMenuAct.setEnabled(False)
        
        self.showMenu.emit("Graphics", self.graphicsMenu, self)
        
    def __showContextMenuMargin(self):
        """
        Private slot handling the aboutToShow signal of the margins context
        menu.
        """
        if self.fileName and (self.isPyFile() or self.isRubyFile()):
            self.marginMenuActs["Breakpoint"].setEnabled(True)
            self.marginMenuActs["TempBreakpoint"].setEnabled(True)
            if self.markersAtLine(self.line) & self.breakpointMask:
                self.marginMenuActs["EditBreakpoint"].setEnabled(True)
                self.marginMenuActs["EnableBreakpoint"].setEnabled(True)
            else:
                self.marginMenuActs["EditBreakpoint"].setEnabled(False)
                self.marginMenuActs["EnableBreakpoint"].setEnabled(False)
            if self.markersAtLine(self.line) & (1 << self.dbreakpoint):
                self.marginMenuActs["EnableBreakpoint"].setText(
                    self.tr('Enable breakpoint'))
            else:
                self.marginMenuActs["EnableBreakpoint"].setText(
                    self.tr('Disable breakpoint'))
            if self.breaks:
                self.marginMenuActs["NextBreakpoint"].setEnabled(True)
                self.marginMenuActs["PreviousBreakpoint"].setEnabled(True)
                self.marginMenuActs["ClearBreakpoint"].setEnabled(True)
            else:
                self.marginMenuActs["NextBreakpoint"].setEnabled(False)
                self.marginMenuActs["PreviousBreakpoint"].setEnabled(False)
                self.marginMenuActs["ClearBreakpoint"].setEnabled(False)
        else:
            self.marginMenuActs["Breakpoint"].setEnabled(False)
            self.marginMenuActs["TempBreakpoint"].setEnabled(False)
            self.marginMenuActs["EditBreakpoint"].setEnabled(False)
            self.marginMenuActs["EnableBreakpoint"].setEnabled(False)
            self.marginMenuActs["NextBreakpoint"].setEnabled(False)
            self.marginMenuActs["PreviousBreakpoint"].setEnabled(False)
            self.marginMenuActs["ClearBreakpoint"].setEnabled(False)
            
        if self.bookmarks:
            self.marginMenuActs["NextBookmark"].setEnabled(True)
            self.marginMenuActs["PreviousBookmark"].setEnabled(True)
            self.marginMenuActs["ClearBookmark"].setEnabled(True)
        else:
            self.marginMenuActs["NextBookmark"].setEnabled(False)
            self.marginMenuActs["PreviousBookmark"].setEnabled(False)
            self.marginMenuActs["ClearBookmark"].setEnabled(False)
            
        if len(self.syntaxerrors):
            self.marginMenuActs["GotoSyntaxError"].setEnabled(True)
            self.marginMenuActs["ClearSyntaxError"].setEnabled(True)
            if self.markersAtLine(self.line) & (1 << self.syntaxerror):
                self.marginMenuActs["ShowSyntaxError"].setEnabled(True)
            else:
                self.marginMenuActs["ShowSyntaxError"].setEnabled(False)
        else:
            self.marginMenuActs["GotoSyntaxError"].setEnabled(False)
            self.marginMenuActs["ClearSyntaxError"].setEnabled(False)
            self.marginMenuActs["ShowSyntaxError"].setEnabled(False)
        
        if len(self.warnings):
            self.marginMenuActs["NextWarningMarker"].setEnabled(True)
            self.marginMenuActs["PreviousWarningMarker"].setEnabled(True)
            self.marginMenuActs["ClearWarnings"].setEnabled(True)
            if self.markersAtLine(self.line) & (1 << self.warning):
                self.marginMenuActs["ShowWarning"].setEnabled(True)
            else:
                self.marginMenuActs["ShowWarning"].setEnabled(False)
        else:
            self.marginMenuActs["NextWarningMarker"].setEnabled(False)
            self.marginMenuActs["PreviousWarningMarker"].setEnabled(False)
            self.marginMenuActs["ClearWarnings"].setEnabled(False)
            self.marginMenuActs["ShowWarning"].setEnabled(False)
        
        if self.notcoveredMarkers:
            self.marginMenuActs["NextCoverageMarker"].setEnabled(True)
            self.marginMenuActs["PreviousCoverageMarker"].setEnabled(True)
        else:
            self.marginMenuActs["NextCoverageMarker"].setEnabled(False)
            self.marginMenuActs["PreviousCoverageMarker"].setEnabled(False)
        
        if self.__hasTaskMarkers:
            self.marginMenuActs["PreviousTaskMarker"].setEnabled(True)
            self.marginMenuActs["NextTaskMarker"].setEnabled(True)
        else:
            self.marginMenuActs["PreviousTaskMarker"].setEnabled(False)
            self.marginMenuActs["NextTaskMarker"].setEnabled(False)
        
        if self.__hasChangeMarkers:
            self.marginMenuActs["PreviousChangeMarker"].setEnabled(True)
            self.marginMenuActs["NextChangeMarker"].setEnabled(True)
        else:
            self.marginMenuActs["PreviousChangeMarker"].setEnabled(False)
            self.marginMenuActs["NextChangeMarker"].setEnabled(False)
        
        self.showMenu.emit("Margin", self.sender(), self)
        
    def __showContextMenuChecks(self):
        """
        Private slot handling the aboutToShow signal of the checks context
        menu.
        """
        self.showMenu.emit("Checks", self.checksMenu, self)
        
    def __showContextMenuTools(self):
        """
        Private slot handling the aboutToShow signal of the tools context
        menu.
        """
        self.showMenu.emit("Tools", self.toolsMenu, self)
        
    def __reopenWithEncodingMenuTriggered(self, act):
        """
        Private method to handle the rereading of the file with a selected
        encoding.
        
        @param act reference to the action that was triggered (QAction)
        """
        encoding = act.data()
        self.readFile(self.fileName, encoding=encoding)
        self.__checkEncoding()
        
    def __contextSave(self):
        """
        Private slot handling the save context menu entry.
        """
        ok = self.saveFile()
        if ok:
            self.vm.setEditorName(self, self.fileName)
        
    def __contextSaveAs(self):
        """
        Private slot handling the save as context menu entry.
        """
        ok = self.saveFileAs()
        if ok:
            self.vm.setEditorName(self, self.fileName)
        
    def __contextSaveCopy(self):
        """
        Private slot handling the save copy context menu entry.
        """
        self.saveFileCopy()
        
    def __contextClose(self):
        """
        Private slot handling the close context menu entry.
        """
        self.vm.closeEditor(self)
    
    def __contextOpenRejections(self):
        """
        Private slot handling the open rejections file context menu entry.
        """
        if self.fileName:
            rej = "{0}.rej".format(self.fileName)
            if os.path.exists(rej):
                self.vm.openSourceFile(rej)
    
    def __newView(self):
        """
        Private slot to create a new view to an open document.
        """
        self.vm.newEditorView(self.fileName, self, self.filetype)
        
    def __newViewNewSplit(self):
        """
        Private slot to create a new view to an open document.
        """
        self.vm.addSplit()
        self.vm.newEditorView(self.fileName, self, self.filetype)
        
    def __selectAll(self):
        """
        Private slot handling the select all context menu action.
        """
        self.selectAll(True)
            
    def __deselectAll(self):
        """
        Private slot handling the deselect all context menu action.
        """
        self.selectAll(False)
        
    def joinLines(self):
        """
        Public slot to join the current line with the next one.
        """
        curLine = self.getCursorPosition()[0]
        if curLine == self.lines() - 1:
            return
        
        line0Text = self.text(curLine)
        line1Text = self.text(curLine + 1)
        if line1Text in ["", "\r", "\n", "\r\n"]:
            return
        
        if line0Text.rstrip("\r\n\\ \t").endswith(("'", '"')) and \
                line1Text.lstrip().startswith(("'", '"')):
            # merging multi line strings
            startChars = "\r\n\\ \t'\""
            endChars = " \t'\""
        else:
            startChars = "\r\n\\ \t"
            endChars = " \t"
        
        # determine start index
        startIndex = len(line0Text)
        while startIndex > 0 and line0Text[startIndex - 1] in startChars:
            startIndex -= 1
        if startIndex == 0:
            return
        
        # determine end index
        endIndex = 0
        while line1Text[endIndex] in endChars:
            endIndex += 1
        
        self.setSelection(curLine, startIndex, curLine + 1, endIndex)
        self.beginUndoAction()
        self.removeSelectedText()
        self.insertAt(" ", curLine, startIndex)
        self.endUndoAction()
        
    def shortenEmptyLines(self):
        """
        Public slot to compress lines consisting solely of whitespace
        characters.
        """
        searchRE = r"^[ \t]+$"
        
        ok = self.findFirstTarget(searchRE, True, False, False, 0, 0)
        self.beginUndoAction()
        while ok:
            self.replaceTarget("")
            ok = self.findNextTarget()
        self.endUndoAction()
        
    def __autosaveEnable(self):
        """
        Private slot handling the autosave enable context menu action.
        """
        if self.menuActs["AutosaveEnable"].isChecked():
            self.autosaveManuallyDisabled = False
        else:
            self.autosaveManuallyDisabled = True
        
    def shouldAutosave(self):
        """
        Public slot to check the autosave flags.
        
        @return flag indicating this editor should be saved (boolean)
        """
        return self.fileName is not None and \
            not self.autosaveManuallyDisabled and \
            not self.isReadOnly()

    def checkSyntax(self):
        """
        Public method to perform an automatic syntax check of the file.
        """
        if self.syntaxCheckService is None or \
                self.filetype not in self.syntaxCheckService.getLanguages():
            return
        
        if Preferences.getEditor("AutoCheckSyntax"):
            if Preferences.getEditor("OnlineSyntaxCheck"):
                self.__onlineSyntaxCheckTimer.stop()
            
            self.syntaxCheckService.syntaxCheck(
                self.filetype, self.fileName or "(Unnamed)", self.text())

    def __processSyntaxCheckError(self, fn, msg):
        """
        Private slot to report an error message of a syntax check.
        
        @param fn filename of the file
        @type str
        @param msg error message
        @type str
        """
        if fn != self.fileName and (
                self.fileName is not None or fn != "(Unnamed)"):
            return
        
        self.clearSyntaxError()
        self.clearFlakesWarnings()
        
        self.toggleWarning(0, 0, True, msg)
        
        self.updateVerticalScrollBar()
    
    def __processSyntaxCheckResult(self, fn, problems):
        """
        Private slot to report the resulting messages of a syntax check.
        
        @param fn filename of the checked file (str)
        @param problems dictionary with the keys 'error' and 'warnings' which
            hold a list containing details about the error/ warnings
            (file name, line number, column, codestring (only at syntax
            errors), the message) (dict)
        """
        # Check if it's the requested file, otherwise ignore signal
        if fn != self.fileName and (
                self.fileName is not None or fn != "(Unnamed)"):
            return
        
        self.clearSyntaxError()
        self.clearFlakesWarnings()
        
        error = problems.get('error')
        if error:
            _fn, lineno, col, code, msg = error
            self.toggleSyntaxError(lineno, col, True, msg)
        
        warnings = problems.get('warnings', [])
        for _fn, lineno, col, code, msg in warnings:
            self.toggleWarning(lineno, col, True, msg)
        
        self.updateVerticalScrollBar()
 
    def __initOnlineSyntaxCheck(self):
        """
        Private slot to initialize the online syntax check.
        """
        self.__onlineSyntaxCheckTimer = QTimer(self)
        self.__onlineSyntaxCheckTimer.setSingleShot(True)
        self.__onlineSyntaxCheckTimer.setInterval(
            Preferences.getEditor("OnlineSyntaxCheckInterval") * 1000)
        self.__onlineSyntaxCheckTimer.timeout.connect(self.checkSyntax)
        self.textChanged.connect(self.__resetOnlineSyntaxCheckTimer)
        
    def __resetOnlineSyntaxCheckTimer(self):
        """
        Private method to reset the online syntax check timer.
        """
        if Preferences.getEditor("OnlineSyntaxCheck"):
            self.__onlineSyntaxCheckTimer.stop()
            self.__onlineSyntaxCheckTimer.start()
        
    def __showCodeMetrics(self):
        """
        Private method to handle the code metrics context menu action.
        """
        if not self.checkDirty():
            return
        
        from DataViews.CodeMetricsDialog import CodeMetricsDialog
        self.codemetrics = CodeMetricsDialog()
        self.codemetrics.show()
        self.codemetrics.start(self.fileName)
        
    def __getCodeCoverageFile(self):
        """
        Private method to get the filename of the file containing coverage
        info.
        
        @return filename of the coverage file (string)
        """
        files = []
        
        # first check if the file belongs to a project and there is
        # a project coverage file
        if self.project.isOpen() and \
                self.project.isProjectSource(self.fileName):
            fn = self.project.getMainScript(True)
            if fn is not None:
                tfn = Utilities.getTestFileName(fn)
                basename = os.path.splitext(fn)[0]
                tbasename = os.path.splitext(tfn)[0]
                
                f = "{0}.coverage".format(basename)
                tf = "{0}.coverage".format(tbasename)
                if os.path.isfile(f):
                    files.append(f)
                if os.path.isfile(tf):
                    files.append(tf)
        
        # now check, if there are coverage files belonging to ourself
        fn = self.getFileName()
        if fn is not None:
            tfn = Utilities.getTestFileName(fn)
            basename = os.path.splitext(fn)[0]
            tbasename = os.path.splitext(tfn)[0]
            
            f = "{0}.coverage".format(basename)
            tf = "{0}.coverage".format(tbasename)
            if os.path.isfile(f) and f not in files:
                files.append(f)
            if os.path.isfile(tf) and tf not in files:
                files.append(tf)
        
        if files:
            if len(files) > 1:
                fn, ok = QInputDialog.getItem(
                    self,
                    self.tr("Code Coverage"),
                    self.tr("Please select a coverage file"),
                    files,
                    0, False)
                if not ok:
                    return
            else:
                fn = files[0]
        else:
            fn = None
        
        return fn
        
    def __showCodeCoverage(self):
        """
        Private method to handle the code coverage context menu action.
        """
        fn = self.__getCodeCoverageFile()
        if fn:
            from DataViews.PyCoverageDialog import PyCoverageDialog
            self.codecoverage = PyCoverageDialog()
            self.codecoverage.show()
            self.codecoverage.start(fn, self.fileName)
        
    def refreshCoverageAnnotations(self):
        """
        Public method to refresh the code coverage annotations.
        """
        if self.showingNotcoveredMarkers:
            self.codeCoverageShowAnnotations(silent=True)
        
    def codeCoverageShowAnnotations(self, silent=False):
        """
        Public method to handle the show code coverage annotations context
        menu action.
        
        @param silent flag indicating to not show any dialog (boolean)
        """
        self.__codeCoverageHideAnnotations()
        
        fn = self.__getCodeCoverageFile()
        if fn:
            from coverage import coverage
            cover = coverage(data_file=fn)
            cover.load()
            missing = cover.analysis2(self.fileName)[3]
            if missing:
                for line in missing:
                    handle = self.markerAdd(line - 1, self.notcovered)
                    self.notcoveredMarkers.append(handle)
                self.coverageMarkersShown.emit(True)
                self.__markerMap.update()
            else:
                if not silent:
                    E5MessageBox.information(
                        self,
                        self.tr("Show Code Coverage Annotations"),
                        self.tr("""All lines have been covered."""))
            self.showingNotcoveredMarkers = True
        else:
            if not silent:
                E5MessageBox.warning(
                    self,
                    self.tr("Show Code Coverage Annotations"),
                    self.tr("""There is no coverage file available."""))
        
    def __codeCoverageHideAnnotations(self):
        """
        Private method to handle the hide code coverage annotations context
        menu action.
        """
        for handle in self.notcoveredMarkers:
            self.markerDeleteHandle(handle)
        self.notcoveredMarkers = []
        self.coverageMarkersShown.emit(False)
        self.showingNotcoveredMarkers = False
        self.__markerMap.update()
        
    def getCoverageLines(self):
        """
        Public method to get the lines containing a coverage marker.
        
        @return list of lines containing a coverage marker (list of integer)
        """
        lines = []
        line = -1
        while True:
            line = self.markerFindNext(line + 1, 1 << self.notcovered)
            if line < 0:
                break
            else:
                lines.append(line)
        return lines
        
    def hasCoverageMarkers(self):
        """
        Public method to test, if there are coverage markers.
        
        @return flag indicating the presence of coverage markers (boolean)
        """
        return len(self.notcoveredMarkers) > 0
        
    def nextUncovered(self):
        """
        Public slot to handle the 'Next uncovered' context menu action.
        """
        line, index = self.getCursorPosition()
        if line == self.lines() - 1:
            line = 0
        else:
            line += 1
        ucline = self.markerFindNext(line, 1 << self.notcovered)
        if ucline < 0:
            # wrap around
            ucline = self.markerFindNext(0, 1 << self.notcovered)
        if ucline >= 0:
            self.setCursorPosition(ucline, 0)
            self.ensureLineVisible(ucline)
        
    def previousUncovered(self):
        """
        Public slot to handle the 'Previous uncovered' context menu action.
        """
        line, index = self.getCursorPosition()
        if line == 0:
            line = self.lines() - 1
        else:
            line -= 1
        ucline = self.markerFindPrevious(line, 1 << self.notcovered)
        if ucline < 0:
            # wrap around
            ucline = self.markerFindPrevious(
                self.lines() - 1, 1 << self.notcovered)
        if ucline >= 0:
            self.setCursorPosition(ucline, 0)
            self.ensureLineVisible(ucline)
        
    def __showProfileData(self):
        """
        Private method to handle the show profile data context menu action.
        """
        files = []
        
        # first check if the file belongs to a project and there is
        # a project profile file
        if self.project.isOpen() and \
                self.project.isProjectSource(self.fileName):
            fn = self.project.getMainScript(True)
            if fn is not None:
                tfn = Utilities.getTestFileName(fn)
                basename = os.path.splitext(fn)[0]
                tbasename = os.path.splitext(tfn)[0]
                
                f = "{0}.profile".format(basename)
                tf = "{0}.profile".format(tbasename)
                if os.path.isfile(f):
                    files.append(f)
                if os.path.isfile(tf):
                    files.append(tf)
        
        # now check, if there are profile files belonging to ourself
        fn = self.getFileName()
        if fn is not None:
            tfn = Utilities.getTestFileName(fn)
            basename = os.path.splitext(fn)[0]
            tbasename = os.path.splitext(tfn)[0]
            
            f = "{0}.profile".format(basename)
            tf = "{0}.profile".format(tbasename)
            if os.path.isfile(f) and f not in files:
                files.append(f)
            if os.path.isfile(tf) and tf not in files:
                files.append(tf)
        
        if files:
            if len(files) > 1:
                fn, ok = QInputDialog.getItem(
                    self,
                    self.tr("Profile Data"),
                    self.tr("Please select a profile file"),
                    files,
                    0, False)
                if not ok:
                    return
            else:
                fn = files[0]
        else:
            return
        
        from DataViews.PyProfileDialog import PyProfileDialog
        self.profiledata = PyProfileDialog()
        self.profiledata.show()
        self.profiledata.start(fn, self.fileName)
        
    def __lmBbookmarks(self):
        """
        Private method to handle the 'LMB toggles bookmark' context menu
        action.
        """
        self.marginMenuActs["LMBbookmarks"].setChecked(True)
        self.marginMenuActs["LMBbreakpoints"].setChecked(False)
        
    def __lmBbreakpoints(self):
        """
        Private method to handle the 'LMB toggles breakpoint' context menu
        action.
        """
        self.marginMenuActs["LMBbookmarks"].setChecked(True)
        self.marginMenuActs["LMBbreakpoints"].setChecked(False)
    
    ###########################################################################
    ## Syntax error handling methods below
    ###########################################################################

    def toggleSyntaxError(self, line, index, error, msg="", show=False):
        """
        Public method to toggle a syntax error indicator.
        
        @param line line number of the syntax error (integer)
        @param index index number of the syntax error (integer)
        @param error flag indicating if the error marker should be
            set or deleted (boolean)
        @param msg error message (string)
        @keyparam show flag indicating to set the cursor to the error position
            (boolean)
        """
        if line == 0:
            line = 1
            # hack to show a syntax error marker, if line is reported to be 0
        if error:
            # set a new syntax error marker
            markers = self.markersAtLine(line - 1)
            index += self.indentation(line - 1)
            if not (markers & (1 << self.syntaxerror)):
                handle = self.markerAdd(line - 1, self.syntaxerror)
                self.syntaxerrors[handle] = [(msg, index)]
                self.syntaxerrorToggled.emit(self)
            else:
                for handle in list(self.syntaxerrors.keys()):
                    if self.markerLine(handle) == line - 1 and \
                       (msg, index) not in self.syntaxerrors[handle]:
                        self.syntaxerrors[handle].append((msg, index))
            if show:
                self.setCursorPosition(line - 1, index)
                self.ensureLineVisible(line - 1)
        else:
            for handle in list(self.syntaxerrors.keys()):
                if self.markerLine(handle) == line - 1:
                    del self.syntaxerrors[handle]
                    self.markerDeleteHandle(handle)
                    self.syntaxerrorToggled.emit(self)
        
        self.__setAnnotation(line - 1)
        self.__markerMap.update()
        
    def getSyntaxErrors(self):
        """
        Public method to retrieve the syntax error markers.
        
        @return sorted list of all lines containing a syntax error
            (list of integer)
        """
        selist = []
        for handle in list(self.syntaxerrors.keys()):
            selist.append(self.markerLine(handle) + 1)
        
        selist.sort()
        return selist
        
    def getSyntaxErrorLines(self):
        """
        Public method to get the lines containing a syntax error.
        
        @return list of lines containing a syntax error (list of integer)
        """
        lines = []
        line = -1
        while True:
            line = self.markerFindNext(line + 1, 1 << self.syntaxerror)
            if line < 0:
                break
            else:
                lines.append(line)
        return lines
        
    def hasSyntaxErrors(self):
        """
        Public method to check for the presence of syntax errors.
        
        @return flag indicating the presence of syntax errors (boolean)
        """
        return len(self.syntaxerrors) > 0
    
    def gotoSyntaxError(self):
        """
        Public slot to handle the 'Goto syntax error' context menu action.
        """
        seline = self.markerFindNext(0, 1 << self.syntaxerror)
        if seline >= 0:
            index = 0
            for handle in self.syntaxerrors.keys():
                if self.markerLine(handle) == seline:
                    index = self.syntaxerrors[handle][0][1]
            self.setCursorPosition(seline, index)
        self.ensureLineVisible(seline)
        
    def clearSyntaxError(self):
        """
        Public slot to handle the 'Clear all syntax error' context menu action.
        """
        for handle in list(self.syntaxerrors.keys()):
            line = self.markerLine(handle) + 1
            self.toggleSyntaxError(line, 0, False)
        
        self.syntaxerrors = {}
        self.syntaxerrorToggled.emit(self)
    
    def __showSyntaxError(self, line=-1):
        """
        Private slot to handle the 'Show syntax error message'
        context menu action.
        
        @param line line number to show the syntax error for (integer)
        """
        if line == -1:
            line = self.line
        
        for handle in list(self.syntaxerrors.keys()):
            if self.markerLine(handle) == line:
                errors = [e[0] for e in self.syntaxerrors[handle]]
                E5MessageBox.critical(
                    self,
                    self.tr("Syntax Error"),
                    "\n".join(errors))
                break
        else:
            E5MessageBox.critical(
                self,
                self.tr("Syntax Error"),
                self.tr("No syntax error message available."))
    
    ###########################################################################
    ## Warning handling methods below
    ###########################################################################
    
    def toggleWarning(
            self, line, col, warning, msg="", warningType=WarningCode):
        """
        Public method to toggle a warning indicator.
        
        Note: This method is used to set pyflakes and code style warnings.
        
        @param line line number of the warning
        @param col column of the warning
        @param warning flag indicating if the warning marker should be
            set or deleted (boolean)
        @param msg warning message (string)
        @keyparam warningType type of warning message (integer)
        """
        if line == 0:
            line = 1
            # hack to show a warning marker, if line is reported to be 0
        if warning:
            # set/amend a new warning marker
            warn = (msg, warningType)
            markers = self.markersAtLine(line - 1)
            if not (markers & (1 << self.warning)):
                handle = self.markerAdd(line - 1, self.warning)
                self.warnings[handle] = [warn]
                self.syntaxerrorToggled.emit(self)
            else:
                for handle in list(self.warnings.keys()):
                    if self.markerLine(handle) == line - 1 and \
                       warn not in self.warnings[handle]:
                        self.warnings[handle].append(warn)
        else:
            for handle in list(self.warnings.keys()):
                if self.markerLine(handle) == line - 1:
                    del self.warnings[handle]
                    self.markerDeleteHandle(handle)
                    self.syntaxerrorToggled.emit(self)
        
        self.__setAnnotation(line - 1)
        self.__markerMap.update()
    
    def getWarnings(self):
        """
        Public method to retrieve the warning markers.
        
        @return sorted list of all lines containing a warning
            (list of integer)
        """
        fwlist = []
        for handle in list(self.warnings.keys()):
            fwlist.append(self.markerLine(handle) + 1)
        
        fwlist.sort()
        return fwlist
    
    def getWarningLines(self):
        """
        Public method to get the lines containing a warning.
        
        @return list of lines containing a warning (list of integer)
        """
        lines = []
        line = -1
        while True:
            line = self.markerFindNext(line + 1, 1 << self.warning)
            if line < 0:
                break
            else:
                lines.append(line)
        return lines
        
    def hasWarnings(self):
        """
        Public method to check for the presence of warnings.
        
        @return flag indicating the presence of warnings (boolean)
        """
        return len(self.warnings) > 0
    
    def nextWarning(self):
        """
        Public slot to handle the 'Next warning' context menu action.
        """
        line, index = self.getCursorPosition()
        if line == self.lines() - 1:
            line = 0
        else:
            line += 1
        fwline = self.markerFindNext(line, 1 << self.warning)
        if fwline < 0:
            # wrap around
            fwline = self.markerFindNext(0, 1 << self.warning)
        if fwline >= 0:
            self.setCursorPosition(fwline, 0)
            self.ensureLineVisible(fwline)
    
    def previousWarning(self):
        """
        Public slot to handle the 'Previous warning' context menu action.
        """
        line, index = self.getCursorPosition()
        if line == 0:
            line = self.lines() - 1
        else:
            line -= 1
        fwline = self.markerFindPrevious(line, 1 << self.warning)
        if fwline < 0:
            # wrap around
            fwline = self.markerFindPrevious(
                self.lines() - 1, 1 << self.warning)
        if fwline >= 0:
            self.setCursorPosition(fwline, 0)
            self.ensureLineVisible(fwline)
    
    def clearFlakesWarnings(self):
        """
        Public slot to clear all pyflakes warnings.
        """
        self.__clearTypedWarning(Editor.WarningCode)
    
    def clearStyleWarnings(self):
        """
        Public slot to clear all style warnings.
        """
        self.__clearTypedWarning(Editor.WarningStyle)
    
    def __clearTypedWarning(self, warningKind):
        """
        Private method to clear warnings of a specific kind.
        
        @param warningKind kind of warning to clear (Editor.WarningCode,
            Editor.WarningStyle)
        """
        assert warningKind in [Editor.WarningCode, Editor.WarningStyle]
        
        for handle in list(self.warnings.keys()):
            warnings = []
            for msg, warningType in self.warnings[handle]:
                if warningType == warningKind:
                    continue
                
                warnings.append((msg, warningType))
            
            if warnings:
                self.warnings[handle] = warnings
                self.__setAnnotation(self.markerLine(handle))
            else:
                del self.warnings[handle]
                self.__setAnnotation(self.markerLine(handle))
                self.markerDeleteHandle(handle)
        self.syntaxerrorToggled.emit(self)
        self.__markerMap.update()
    
    def clearWarnings(self):
        """
        Public slot to clear all warnings.
        """
        for handle in self.warnings:
            self.warnings[handle] = []
            self.__setAnnotation(self.markerLine(handle))
            self.markerDeleteHandle(handle)
        self.warnings = {}
        self.syntaxerrorToggled.emit(self)
        self.__markerMap.update()
    
    def __showWarning(self, line=-1):
        """
        Private slot to handle the 'Show warning' context menu action.
        
        @param line line number to show the warning for (integer)
        """
        if line == -1:
            line = self.line
        
        for handle in list(self.warnings.keys()):
            if self.markerLine(handle) == line:
                E5MessageBox.warning(
                    self,
                    self.tr("Warning"),
                    '\n'.join([w[0] for w in self.warnings[handle]]))
                break
        else:
            E5MessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("No warning messages available."))
    
    ###########################################################################
    ## Annotation handling methods below
    ###########################################################################
    
    def __setAnnotationStyles(self):
        """
        Private slot to define the style used by inline annotations.
        """
        if hasattr(QsciScintilla, "annotate"):
            self.annotationWarningStyle = \
                QsciScintilla.STYLE_LASTPREDEFINED + 1
            self.SendScintilla(
                QsciScintilla.SCI_STYLESETFORE,
                self.annotationWarningStyle,
                Preferences.getEditorColour("AnnotationsWarningForeground"))
            self.SendScintilla(
                QsciScintilla.SCI_STYLESETBACK,
                self.annotationWarningStyle,
                Preferences.getEditorColour("AnnotationsWarningBackground"))
            
            self.annotationErrorStyle = self.annotationWarningStyle + 1
            self.SendScintilla(
                QsciScintilla.SCI_STYLESETFORE,
                self.annotationErrorStyle,
                Preferences.getEditorColour("AnnotationsErrorForeground"))
            self.SendScintilla(
                QsciScintilla.SCI_STYLESETBACK,
                self.annotationErrorStyle,
                Preferences.getEditorColour("AnnotationsErrorBackground"))
            
            self.annotationStyleStyle = self.annotationErrorStyle + 1
            self.SendScintilla(
                QsciScintilla.SCI_STYLESETFORE,
                self.annotationStyleStyle,
                Preferences.getEditorColour("AnnotationsStyleForeground"))
            self.SendScintilla(
                QsciScintilla.SCI_STYLESETBACK,
                self.annotationStyleStyle,
                Preferences.getEditorColour("AnnotationsStyleBackground"))
        
    def __setAnnotation(self, line):
        """
        Private method to set the annotations for the given line.
        
        @param line number of the line that needs annotation (integer)
        """
        if hasattr(QsciScintilla, "annotate"):
            warningAnnotations = []
            errorAnnotations = []
            styleAnnotations = []
            
            # step 1: do warnings
            for handle in self.warnings.keys():
                if self.markerLine(handle) == line:
                    for msg, warningType in self.warnings[handle]:
                        if warningType == self.WarningStyle:
                            styleAnnotations.append(
                                self.tr("Style: {0}").format(msg))
                        else:
                            warningAnnotations.append(
                                self.tr("Warning: {0}").format(msg))
            
            # step 2: do syntax errors
            for handle in self.syntaxerrors.keys():
                if self.markerLine(handle) == line:
                    for msg, _ in self.syntaxerrors[handle]:
                        errorAnnotations.append(
                            self.tr("Error: {0}").format(msg))
            
            annotations = []
            if styleAnnotations:
                annotationStyleTxt = "\n".join(styleAnnotations)
                if warningAnnotations or errorAnnotations:
                    annotationStyleTxt += "\n"
                annotations.append(QsciStyledText(
                    annotationStyleTxt, self.annotationStyleStyle))
            
            if warningAnnotations:
                annotationWarningTxt = "\n".join(warningAnnotations)
                if errorAnnotations:
                    annotationWarningTxt += "\n"
                annotations.append(QsciStyledText(
                    annotationWarningTxt, self.annotationWarningStyle))
            
            if errorAnnotations:
                annotationErrorTxt = "\n".join(errorAnnotations)
                annotations.append(QsciStyledText(
                    annotationErrorTxt, self.annotationErrorStyle))
            
            if annotations:
                self.annotate(line, annotations)
            else:
                self.clearAnnotations(line)
    
    def __refreshAnnotations(self):
        """
        Private method to refresh the annotations.
        """
        if hasattr(QsciScintilla, "annotate"):
            self.clearAnnotations()
            for handle in list(self.warnings.keys()) + \
                    list(self.syntaxerrors.keys()):
                line = self.markerLine(handle)
                self.__setAnnotation(line)
    
    #################################################################
    ## Macro handling methods
    #################################################################
    
    def __getMacroName(self):
        """
        Private method to select a macro name from the list of macros.
        
        @return Tuple of macro name and a flag, indicating, if the user
            pressed ok or canceled the operation. (string, boolean)
        """
        qs = []
        for s in list(self.macros.keys()):
            qs.append(s)
        qs.sort()
        return QInputDialog.getItem(
            self,
            self.tr("Macro Name"),
            self.tr("Select a macro name:"),
            qs,
            0, False)
        
    def macroRun(self):
        """
        Public method to execute a macro.
        """
        name, ok = self.__getMacroName()
        if ok and name:
            self.macros[name].play()
        
    def macroDelete(self):
        """
        Public method to delete a macro.
        """
        name, ok = self.__getMacroName()
        if ok and name:
            del self.macros[name]
        
    def macroLoad(self):
        """
        Public method to load a macro from a file.
        """
        configDir = Utilities.getConfigDir()
        fname = E5FileDialog.getOpenFileName(
            self,
            self.tr("Load macro file"),
            configDir,
            self.tr("Macro files (*.macro)"))
        
        if not fname:
            return  # user aborted
        
        try:
            f = open(fname, "r", encoding="utf-8")
            lines = f.readlines()
            f.close()
        except IOError:
            E5MessageBox.critical(
                self,
                self.tr("Error loading macro"),
                self.tr(
                    "<p>The macro file <b>{0}</b> could not be read.</p>")
                .format(fname))
            return
        
        if len(lines) != 2:
            E5MessageBox.critical(
                self,
                self.tr("Error loading macro"),
                self.tr("<p>The macro file <b>{0}</b> is corrupt.</p>")
                .format(fname))
            return
        
        macro = QsciMacro(lines[1], self)
        self.macros[lines[0].strip()] = macro
        
    def macroSave(self):
        """
        Public method to save a macro to a file.
        """
        configDir = Utilities.getConfigDir()
        
        name, ok = self.__getMacroName()
        if not ok or not name:
            return  # user abort
        
        fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            self,
            self.tr("Save macro file"),
            configDir,
            self.tr("Macro files (*.macro)"),
            "",
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        
        if not fname:
            return  # user aborted
        
        ext = QFileInfo(fname).suffix()
        if not ext:
            ex = selectedFilter.split("(*")[1].split(")")[0]
            if ex:
                fname += ex
        if QFileInfo(fname).exists():
            res = E5MessageBox.yesNo(
                self,
                self.tr("Save macro"),
                self.tr("<p>The macro file <b>{0}</b> already exists."
                        " Overwrite it?</p>").format(fname),
                icon=E5MessageBox.Warning)
            if not res:
                return
        fname = Utilities.toNativeSeparators(fname)
        
        try:
            f = open(fname, "w", encoding="utf-8")
            f.write("{0}{1}".format(name, "\n"))
            f.write(self.macros[name].save())
            f.close()
        except IOError:
            E5MessageBox.critical(
                self,
                self.tr("Error saving macro"),
                self.tr(
                    "<p>The macro file <b>{0}</b> could not be written.</p>")
                .format(fname))
            return
        
    def macroRecordingStart(self):
        """
        Public method to start macro recording.
        """
        if self.recording:
            res = E5MessageBox.yesNo(
                self,
                self.tr("Start Macro Recording"),
                self.tr("Macro recording is already active. Start new?"),
                icon=E5MessageBox.Warning,
                yesDefault=True)
            if res:
                self.macroRecordingStop()
            else:
                return
        else:
            self.recording = True
        
        self.curMacro = QsciMacro(self)
        self.curMacro.startRecording()
        
    def macroRecordingStop(self):
        """
        Public method to stop macro recording.
        """
        if not self.recording:
            return      # we are not recording
        
        self.curMacro.endRecording()
        self.recording = False
        
        name, ok = QInputDialog.getText(
            self,
            self.tr("Macro Recording"),
            self.tr("Enter name of the macro:"),
            QLineEdit.Normal)
        
        if ok and name:
            self.macros[name] = self.curMacro
        
        self.curMacro = None
        
    #################################################################
    ## Overwritten methods
    #################################################################
    
    def undo(self):
        """
        Public method to undo the last recorded change.
        """
        super(Editor, self).undo()
        self.undoAvailable.emit(self.isUndoAvailable())
        self.redoAvailable.emit(self.isRedoAvailable())
        
    def redo(self):
        """
        Public method to redo the last recorded change.
        """
        super(Editor, self).redo()
        self.undoAvailable.emit(self.isUndoAvailable())
        self.redoAvailable.emit(self.isRedoAvailable())
        
    def close(self, alsoDelete=False):
        """
        Public method called when the window gets closed.
        
        This overwritten method redirects the action to our
        ViewManager.closeEditor, which in turn calls our closeIt
        method.
        
        @param alsoDelete ignored
        @return flag indicating a successful close of the editor (boolean)
        """
        return self.vm.closeEditor(self)
        
    def closeIt(self):
        """
        Public method called by the viewmanager to finally get rid of us.
        """
        if Preferences.getEditor("ClearBreaksOnClose") and not self.__clones:
            self.__menuClearBreakpoints()
        
        for clone in self.__clones[:]:
            self.removeClone(clone)
            clone.removeClone(self)
        
        self.breakpointModel.rowsAboutToBeRemoved.disconnect(
            self.__deleteBreakPoints)
        self.breakpointModel.dataAboutToBeChanged.disconnect(
            self.__breakPointDataAboutToBeChanged)
        self.breakpointModel.dataChanged.disconnect(
            self.__changeBreakPoints)
        self.breakpointModel.rowsInserted.disconnect(
            self.__addBreakPoints)
        
        if self.syntaxCheckService is not None:
            self.syntaxCheckService.syntaxChecked.disconnect(
                self.__processSyntaxCheckResult)
            self.syntaxCheckService.error.disconnect(
                self.__processSyntaxCheckError)
        
        if self.spell:
            self.spell.stopIncrementalCheck()
        
        try:
            self.project.projectPropertiesChanged.disconnect(
                self.__projectPropertiesChanged)
        except TypeError:
            pass
        
        if self.fileName:
            self.taskViewer.clearFileTasks(self.fileName, True)
        
        super(Editor, self).close()
        
    def keyPressEvent(self, ev):
        """
        Protected method to handle the user input a key at a time.
        
        @param ev key event (QKeyEvent)
        """
        txt = ev.text()
        
        # See it is text to insert.
        if len(txt) and txt >= " ":
            super(Editor, self).keyPressEvent(ev)
        else:
            ev.ignore()
        
    def focusInEvent(self, event):
        """
        Protected method called when the editor receives focus.
        
        This method checks for modifications of the current file and
        rereads it upon request. The cursor is placed at the current position
        assuming, that it is in the vicinity of the old position after the
        reread.
        
        @param event the event object (QFocusEvent)
        """
        self.recolor()
        self.vm.editActGrp.setEnabled(True)
        self.vm.editorActGrp.setEnabled(True)
        self.vm.copyActGrp.setEnabled(True)
        self.vm.viewActGrp.setEnabled(True)
        self.vm.searchActGrp.setEnabled(True)
        try:
            self.setCaretWidth(self.caretWidth)
        except AttributeError:
            pass
        self.__updateReadOnly(False)
        if self.vm.editorsCheckFocusInEnabled() and \
           not self.inReopenPrompt and self.fileName and \
           QFileInfo(self.fileName).lastModified().toString() != \
                self.lastModified.toString():
            self.inReopenPrompt = True
            if Preferences.getEditor("AutoReopen") and not self.isModified():
                self.refresh()
            else:
                msg = self.tr(
                    """<p>The file <b>{0}</b> has been changed while it"""
                    """ was opened in eric6. Reread it?</p>""")\
                    .format(self.fileName)
                yesDefault = True
                if self.isModified():
                    msg += self.tr(
                        """<br><b>Warning:</b> You will lose"""
                        """ your changes upon reopening it.""")
                    yesDefault = False
                res = E5MessageBox.yesNo(
                    self,
                    self.tr("File changed"), msg,
                    icon=E5MessageBox.Warning,
                    yesDefault=yesDefault)
                if res:
                    self.refresh()
                else:
                    # do not prompt for this change again...
                    self.lastModified = QFileInfo(self.fileName).lastModified()
            self.inReopenPrompt = False
        
        self.setCursorFlashTime(QApplication.cursorFlashTime())
        
        super(Editor, self).focusInEvent(event)
        
    def focusOutEvent(self, event):
        """
        Protected method called when the editor loses focus.
        
        @param event the event object (QFocusEvent)
        """
        self.vm.editorActGrp.setEnabled(False)
        self.setCaretWidth(0)
        
        super(Editor, self).focusOutEvent(event)
        
    def changeEvent(self, evt):
        """
        Protected method called to process an event.
        
        This implements special handling for the events showMaximized,
        showMinimized and showNormal. The windows caption is shortened
        for the minimized mode and reset to the full filename for the
        other modes. This is to make the editor windows work nicer
        with the QWorkspace.
        
        @param evt the event, that was generated (QEvent)
        """
        if evt.type() == QEvent.WindowStateChange and \
           self.fileName is not None:
            if self.windowState() == Qt.WindowStates(Qt.WindowMinimized):
                cap = os.path.basename(self.fileName)
            else:
                cap = self.fileName
            if self.isReadOnly():
                cap = self.tr("{0} (ro)").format(cap)
            self.setWindowTitle(cap)
        
        super(Editor, self).changeEvent(evt)
        
    def mousePressEvent(self, event):
        """
        Protected method to handle the mouse press event.
        
        @param event the mouse press event (QMouseEvent)
        """
        self.vm.eventFilter(self, event)
        super(Editor, self).mousePressEvent(event)
        
    def wheelEvent(self, evt):
        """
        Protected method to handle wheel events.
        
        @param evt reference to the wheel event (QWheelEvent)
        """
        if qVersion() >= "5.0.0":
            delta = evt.angleDelta().y()
        else:
            delta = evt.delta()
        if evt.modifiers() & Qt.ControlModifier:
            if delta < 0:
                self.zoomOut()
            else:
                self.zoomIn()
            evt.accept()
            return
        
        if evt.modifiers() & Qt.ShiftModifier:
            if delta < 0:
                self.gotoMethodClass(False)
            else:
                self.gotoMethodClass(True)
            evt.accept()
            return
        
        super(Editor, self).wheelEvent(evt)
    
    def event(self, evt):
        """
        Public method handling events.
        
        @param evt reference to the event (QEvent)
        @return flag indicating, if the event was handled (boolean)
        """
        if evt.type() == QEvent.Gesture:
            self.gestureEvent(evt)
            return True
        
        return super(Editor, self).event(evt)
    
    def gestureEvent(self, evt):
        """
        Protected method handling gesture events.
        
        @param evt reference to the gesture event (QGestureEvent
        """
        pinch = evt.gesture(Qt.PinchGesture)
        if pinch:
            if pinch.state() == Qt.GestureStarted:
                zoom = (self.getZoom() + 10) / 10.0
                pinch.setScaleFactor(zoom)
            else:
                zoom = int(pinch.scaleFactor() * 10) - 10
                if zoom <= -9:
                    zoom = -9
                    pinch.setScaleFactor(0.1)
                elif zoom >= 20:
                    zoom = 20
                    pinch.setScaleFactor(3.0)
                self.zoomTo(zoom)
            evt.accept()
    
    def resizeEvent(self, evt):
        """
        Protected method handling resize events.
        
        @param evt reference to the resize event (QResizeEvent)
        """
        super(Editor, self).resizeEvent(evt)
        self.__markerMap.calculateGeometry()
    
    def viewportEvent(self, evt):
        """
        Protected method handling event of the viewport.
        
        @param evt reference to the event (QEvent)
        @return flag indiating that the event was handled (boolean)
        """
        self.__markerMap.calculateGeometry()
        return super(Editor, self).viewportEvent(evt)
    
    def __updateReadOnly(self, bForce=True):
        """
        Private method to update the readOnly information for this editor.
        
        If bForce is True, then updates everything regardless if
        the attributes have actually changed, such as during
        initialization time.  A signal is emitted after the
        caption change.

        @param bForce True to force change, False to only update and emit
                signal if there was an attribute change.
        """
        if self.fileName is None:
            return
        readOnly = not QFileInfo(self.fileName).isWritable() or \
            self.isReadOnly()
        if not bForce and (readOnly == self.isReadOnly()):
            return
        cap = self.fileName
        if readOnly:
            cap = self.tr("{0} (ro)".format(cap))
        self.setReadOnly(readOnly)
        self.setWindowTitle(cap)
        self.captionChanged.emit(cap, self)
        
    def refresh(self):
        """
        Public slot to refresh the editor contents.
        """
        # save cursor position
        cline, cindex = self.getCursorPosition()
        
        # save bookmarks and breakpoints and clear them
        bmlist = self.getBookmarks()
        self.clearBookmarks()
        
        # clear syntax error markers
        self.clearSyntaxError()
        
        # clear flakes warning markers
        self.clearWarnings()
        
        # clear breakpoint markers
        for handle in list(self.breaks.keys()):
            self.markerDeleteHandle(handle)
        self.breaks = {}
        
        if not os.path.exists(self.fileName):
            # close the file, if it was deleted in the background
            self.close()
            return
        
        # reread the file
        try:
            self.readFile(self.fileName)
        except IOError:
            # do not prompt for this change again...
            self.lastModified = QDateTime.currentDateTime()
        self.setModified(False)
        
        # re-initialize the online change tracer
        self.__reinitOnlineChangeTrace()
        
        # reset cursor position
        self.setCursorPosition(cline, cindex)
        self.ensureCursorVisible()
        
        # reset bookmarks and breakpoints to their old position
        if bmlist:
            for bm in bmlist:
                self.toggleBookmark(bm)
        self.__restoreBreakpoints()
        
        self.editorSaved.emit(self.fileName)
        self.checkSyntax()
        
        self.__markerMap.update()
        
        self.refreshed.emit()
        
    def setMonospaced(self, on):
        """
        Public method to set/reset a monospaced font.
        
        @param on flag to indicate usage of a monospace font (boolean)
        """
        if on:
            if not self.lexer_:
                f = Preferences.getEditorOtherFonts("MonospacedFont")
                self.monospacedStyles(f)
        else:
            if not self.lexer_:
                self.clearStyles()
                self.__setMarginsDisplay()
            self.setFont(Preferences.getEditorOtherFonts("DefaultFont"))
        
        self.useMonospaced = on
    
    def clearStyles(self):
        """
        Public method to set the styles according the selected Qt style
        or the selected editor colours.
        """
        super(Editor, self).clearStyles()
        if Preferences.getEditor("OverrideEditAreaColours"):
            self.setColor(Preferences.getEditorColour("EditAreaForeground"))
            self.setPaper(Preferences.getEditorColour("EditAreaBackground"))
    
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
        else:
            super(Editor, self).dragEnterEvent(event)
        
    def dragMoveEvent(self, event):
        """
        Protected method to handle the drag move event.
        
        @param event the drag move event (QDragMoveEvent)
        """
        if self.inDragDrop:
            event.accept()
        else:
            super(Editor, self).dragMoveEvent(event)
        
    def dragLeaveEvent(self, event):
        """
        Protected method to handle the drag leave event.
        
        @param event the drag leave event (QDragLeaveEvent)
        """
        if self.inDragDrop:
            self.inDragDrop = False
            event.accept()
        else:
            super(Editor, self).dragLeaveEvent(event)
        
    def dropEvent(self, event):
        """
        Protected method to handle the drop event.
        
        @param event the drop event (QDropEvent)
        """
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                fname = url.toLocalFile()
                if fname:
                    if not QFileInfo(fname).isDir():
                        self.vm.openSourceFile(fname)
                    else:
                        E5MessageBox.information(
                            self,
                            self.tr("Drop Error"),
                            self.tr("""<p><b>{0}</b> is not a file.</p>""")
                            .format(fname))
            event.acceptProposedAction()
        else:
            super(Editor, self).dropEvent(event)
        
        self.inDragDrop = False
    
    #################################################################
    ## Support for Qt resources files
    #################################################################
    
    def __initContextMenuResources(self):
        """
        Private method used to setup the Resources context sub menu.
        
        @return reference to the generated menu (QMenu)
        """
        menu = QMenu(self.tr('Resources'))
        
        menu.addAction(
            self.tr('Add file...'), self.__addFileResource)
        menu.addAction(
            self.tr('Add files...'), self.__addFileResources)
        menu.addAction(
            self.tr('Add aliased file...'),
            self.__addFileAliasResource)
        menu.addAction(
            self.tr('Add localized resource...'),
            self.__addLocalizedResource)
        menu.addSeparator()
        menu.addAction(
            self.tr('Add resource frame'), self.__addResourceFrame)
        
        menu.aboutToShow.connect(self.__showContextMenuResources)
        
        return menu
        
    def __showContextMenuResources(self):
        """
        Private slot handling the aboutToShow signal of the resources context
        menu.
        """
        self.showMenu.emit("Resources", self.resourcesMenu, self)
        
    def __addFileResource(self):
        """
        Private method to handle the Add file context menu action.
        """
        dirStr = os.path.dirname(self.fileName)
        file = E5FileDialog.getOpenFileName(
            self,
            self.tr("Add file resource"),
            dirStr,
            "")
        if file:
            relFile = QDir(dirStr).relativeFilePath(file)
            line, index = self.getCursorPosition()
            self.insert("  <file>{0}</file>\n".format(relFile))
            self.setCursorPosition(line + 1, index)
        
    def __addFileResources(self):
        """
        Private method to handle the Add files context menu action.
        """
        dirStr = os.path.dirname(self.fileName)
        files = E5FileDialog.getOpenFileNames(
            self,
            self.tr("Add file resources"),
            dirStr,
            "")
        if files:
            myDir = QDir(dirStr)
            filesText = ""
            for file in files:
                relFile = myDir.relativeFilePath(file)
                filesText += "  <file>{0}</file>\n".format(relFile)
            line, index = self.getCursorPosition()
            self.insert(filesText)
            self.setCursorPosition(line + len(files), index)
        
    def __addFileAliasResource(self):
        """
        Private method to handle the Add aliased file context menu action.
        """
        dirStr = os.path.dirname(self.fileName)
        file = E5FileDialog.getOpenFileName(
            self,
            self.tr("Add aliased file resource"),
            dirStr,
            "")
        if file:
            relFile = QDir(dirStr).relativeFilePath(file)
            alias, ok = QInputDialog.getText(
                self,
                self.tr("Add aliased file resource"),
                self.tr("Alias for file <b>{0}</b>:").format(relFile),
                QLineEdit.Normal,
                relFile)
            if ok and alias:
                line, index = self.getCursorPosition()
                self.insert('  <file alias="{1}">{0}</file>\n'
                            .format(relFile, alias))
                self.setCursorPosition(line + 1, index)
        
    def __addLocalizedResource(self):
        """
        Private method to handle the Add localized resource context menu
        action.
        """
        from Project.AddLanguageDialog import AddLanguageDialog
        dlg = AddLanguageDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            lang = dlg.getSelectedLanguage()
            line, index = self.getCursorPosition()
            self.insert('<qresource lang="{0}">\n</qresource>\n'.format(lang))
            self.setCursorPosition(line + 2, index)
        
    def __addResourceFrame(self):
        """
        Private method to handle the Add resource frame context menu action.
        """
        line, index = self.getCursorPosition()
        self.insert('<!DOCTYPE RCC>\n'
                    '<RCC version="1.0">\n'
                    '<qresource>\n'
                    '</qresource>\n'
                    '</RCC>\n')
        self.setCursorPosition(line + 5, index)
    
    #################################################################
    ## Support for diagrams below
    #################################################################
    
    def __showClassDiagram(self):
        """
        Private method to handle the Class Diagram context menu action.
        """
        from Graphics.UMLDialog import UMLDialog
        if not self.checkDirty():
            return
        
        self.classDiagram = UMLDialog(
            UMLDialog.ClassDiagram, self.project, self.fileName,
            self, noAttrs=False)
        self.classDiagram.show()
        
    def __showPackageDiagram(self):
        """
        Private method to handle the Package Diagram context menu action.
        """
        from Graphics.UMLDialog import UMLDialog
        if not self.checkDirty():
            return
        
        package = os.path.isdir(self.fileName) and \
            self.fileName or os.path.dirname(self.fileName)
        res = E5MessageBox.yesNo(
            self,
            self.tr("Package Diagram"),
            self.tr("""Include class attributes?"""),
            yesDefault=True)
        self.packageDiagram = UMLDialog(
            UMLDialog.PackageDiagram, self.project, package,
            self, noAttrs=not res)
        self.packageDiagram.show()
        
    def __showImportsDiagram(self):
        """
        Private method to handle the Imports Diagram context menu action.
        """
        from Graphics.UMLDialog import UMLDialog
        if not self.checkDirty():
            return
        
        package = os.path.isdir(self.fileName) and self.fileName \
            or os.path.dirname(self.fileName)
        res = E5MessageBox.yesNo(
            self,
            self.tr("Imports Diagram"),
            self.tr("""Include imports from external modules?"""))
        self.importsDiagram = UMLDialog(
            UMLDialog.ImportsDiagram, self.project, package,
            self, showExternalImports=res)
        self.importsDiagram.show()
        
    def __showApplicationDiagram(self):
        """
        Private method to handle the Imports Diagram context menu action.
        """
        from Graphics.UMLDialog import UMLDialog
        res = E5MessageBox.yesNo(
            self,
            self.tr("Application Diagram"),
            self.tr("""Include module names?"""),
            yesDefault=True)
        self.applicationDiagram = UMLDialog(
            UMLDialog.ApplicationDiagram, self.project,
            self, noModules=not res)
        self.applicationDiagram.show()
    
    def __loadDiagram(self):
        """
        Private slot to load a diagram from file.
        """
        from Graphics.UMLDialog import UMLDialog
        self.loadedDiagram = UMLDialog(
            UMLDialog.NoDiagram, self.project, parent=self)
        if self.loadedDiagram.load():
            self.loadedDiagram.show(fromFile=True)
        else:
            self.loadedDiagram = None
    
    #######################################################################
    ## Typing aids related methods below
    #######################################################################
    
    def __toggleTypingAids(self):
        """
        Private slot to toggle the typing aids.
        """
        if self.menuActs["TypingAidsEnabled"].isChecked():
            self.completer.setEnabled(True)
        else:
            self.completer.setEnabled(False)
    
    #######################################################################
    ## Autocompleting templates
    #######################################################################
    
    def editorCommand(self, cmd):
        """
        Public method to perform a simple editor command.
        
        @param cmd the scintilla command to be performed
        """
        if cmd == QsciScintilla.SCI_TAB:
            line, index = self.getCursorPosition()
            tmplName = self.getWordLeft(line, index)
            if tmplName:
                if e5App().getObject("TemplateViewer").hasTemplate(
                        tmplName, self.getLanguage()):
                    self.__applyTemplate(tmplName, self.getLanguage())
                    return
                else:
                    templateNames = \
                        e5App().getObject("TemplateViewer").getTemplateNames(
                            tmplName, self.getLanguage())
                    if len(templateNames) == 1:
                        self.__applyTemplate(templateNames[0],
                                             self.getLanguage())
                        return
                    elif len(templateNames) > 1:
                        self.showUserList(
                            TemplateCompletionListID,
                            ["{0}?{1:d}".format(t, self.TemplateImageID)
                             for t in templateNames])
                        return
        
        super(Editor, self).editorCommand(cmd)
    
    def __applyTemplate(self, templateName, language):
        """
        Private method to apply a template by name.
        
        @param templateName name of the template to apply (string)
        @param language name of the language (group) to get the template
            from (string)
        """
        if e5App().getObject("TemplateViewer").hasTemplate(
                templateName, self.getLanguage()):
            self.extendSelectionWordLeft()
            e5App().getObject("TemplateViewer").applyNamedTemplate(
                templateName, self.getLanguage())
    
    #######################################################################
    ## Project related methods
    #######################################################################
    
    def __projectPropertiesChanged(self):
        """
        Private slot to handle changes of the project properties.
        """
        if self.spell:
            pwl, pel = self.project.getProjectDictionaries()
            self.__setSpellingLanguage(self.project.getProjectSpellLanguage(),
                                       pwl=pwl, pel=pel)
        
        self.setEolModeByEolString(self.project.getEolString())
        self.convertEols(self.eolMode())
    
    def addedToProject(self):
        """
        Public method to signal, that this editor has been added to a project.
        """
        if self.spell:
            pwl, pel = self.project.getProjectDictionaries()
            self.__setSpellingLanguage(self.project.getProjectSpellLanguage(),
                                       pwl=pwl, pel=pel)
        
        self.project.projectPropertiesChanged.connect(
            self.__projectPropertiesChanged)
    
    def projectOpened(self):
        """
        Public slot to handle the opening of a project.
        """
        if self.fileName and \
           self.project.isProjectSource(self.fileName):
            self.project.projectPropertiesChanged.connect(
                self.__projectPropertiesChanged)
            self.setSpellingForProject()
    
    def projectClosed(self):
        """
        Public slot to handle the closing of a project.
        """
        try:
            self.project.projectPropertiesChanged.disconnect(
                self.__projectPropertiesChanged)
        except TypeError:
            pass
    
    #######################################################################
    ## Spellchecking related methods
    #######################################################################
    
    def __setSpellingLanguage(self, language, pwl="", pel=""):
        """
        Private slot to set the spell checking language.
        
        @param language spell checking language to be set (string)
        @keyparam pwl name of the personal/project word list (string)
        @keyparam pel name of the personal/project exclude list (string)
        """
        if self.spell and self.spell.getLanguage() != language:
            self.spell.setLanguage(language, pwl=pwl, pel=pel)
            self.spell.checkDocumentIncrementally()
    
    def __setSpelling(self):
        """
        Private method to initialize the spell checking functionality.
        """
        if Preferences.getEditor("SpellCheckingEnabled"):
            self.__spellCheckStringsOnly = Preferences.getEditor(
                "SpellCheckStringsOnly")
            if self.spell is None:
                from .SpellChecker import SpellChecker
                self.spell = SpellChecker(self, self.spellingIndicator,
                                          checkRegion=self.isSpellCheckRegion)
            self.setSpellingForProject()
            self.spell.setMinimumWordSize(
                Preferences.getEditor("SpellCheckingMinWordSize"))
            
            self.setAutoSpellChecking()
        else:
            self.spell = None
            self.clearAllIndicators(self.spellingIndicator)

    def setSpellingForProject(self):
        """
        Public method to set the spell checking options for files belonging
        to the current project.
        """
        if self.fileName and \
           self.project.isOpen() and \
           self.project.isProjectSource(self.fileName):
            pwl, pel = self.project.getProjectDictionaries()
            self.__setSpellingLanguage(self.project.getProjectSpellLanguage(),
                                       pwl=pwl, pel=pel)
    
    def setAutoSpellChecking(self):
        """
        Public method to set the automatic spell checking.
        """
        if Preferences.getEditor("AutoSpellCheckingEnabled"):
            try:
                self.SCN_CHARADDED.connect(
                    self.__spellCharAdded, Qt.UniqueConnection)
            except TypeError:
                pass
            self.spell.checkDocumentIncrementally()
        else:
            try:
                self.SCN_CHARADDED.disconnect(self.__spellCharAdded)
            except TypeError:
                pass
            self.clearAllIndicators(self.spellingIndicator)
    
    def isSpellCheckRegion(self, pos):
        """
        Public method to check, if the given position is within a region, that
        should be spell checked.
        
        @param pos position to be checked (integer)
        @return flag indicating pos is in a spell check region (boolean)
        """
        if self.__spellCheckStringsOnly:
            style = self.styleAt(pos)
            if self.lexer_ is not None:
                return self.lexer_.isCommentStyle(style) or \
                    self.lexer_.isStringStyle(style)
        return True
    
    @pyqtSlot(int)
    def __spellCharAdded(self, charNumber):
        """
        Private slot called to handle the user entering a character.
        
        @param charNumber value of the character entered (integer)
        """
        if self.spell:
            if not chr(charNumber).isalnum():
                self.spell.checkWord(
                    self.positionBefore(self.currentPosition()), True)
            elif self.hasIndicator(
                    self.spellingIndicator, self.currentPosition()):
                self.spell.checkWord(self.currentPosition())
    
    def checkSpelling(self):
        """
        Public slot to perform an interactive spell check of the document.
        """
        if self.spell:
            cline, cindex = self.getCursorPosition()
            from .SpellCheckingDialog import SpellCheckingDialog
            dlg = SpellCheckingDialog(self.spell, 0, self.length(), self)
            dlg.exec_()
            self.setCursorPosition(cline, cindex)
            if Preferences.getEditor("AutoSpellCheckingEnabled"):
                self.spell.checkDocumentIncrementally()
    
    def __checkSpellingSelection(self):
        """
        Private slot to spell check the current selection.
        """
        from .SpellCheckingDialog import SpellCheckingDialog
        sline, sindex, eline, eindex = self.getSelection()
        startPos = self.positionFromLineIndex(sline, sindex)
        endPos = self.positionFromLineIndex(eline, eindex)
        dlg = SpellCheckingDialog(self.spell, startPos, endPos, self)
        dlg.exec_()
    
    def __checkSpellingWord(self):
        """
        Private slot to check the word below the spelling context menu.
        """
        from .SpellCheckingDialog import SpellCheckingDialog
        line, index = self.lineIndexFromPosition(self.spellingMenuPos)
        wordStart, wordEnd = self.getWordBoundaries(line, index)
        wordStartPos = self.positionFromLineIndex(line, wordStart)
        wordEndPos = self.positionFromLineIndex(line, wordEnd)
        dlg = SpellCheckingDialog(self.spell, wordStartPos, wordEndPos, self)
        dlg.exec_()
    
    def __showContextMenuSpelling(self):
        """
        Private slot to set up the spelling menu before it is shown.
        """
        self.spellingMenu.clear()
        self.spellingSuggActs = []
        line, index = self.lineIndexFromPosition(self.spellingMenuPos)
        word = self.getWord(line, index)
        suggestions = self.spell.getSuggestions(word)
        for suggestion in suggestions[:5]:
            self.spellingSuggActs.append(
                self.spellingMenu.addAction(suggestion))
        if suggestions:
            self.spellingMenu.addSeparator()
        self.spellingMenu.addAction(
            UI.PixmapCache.getIcon("spellchecking.png"),
            self.tr("Check spelling..."), self.__checkSpellingWord)
        self.spellingMenu.addAction(
            self.tr("Add to dictionary"), self.__addToSpellingDictionary)
        self.spellingMenu.addAction(
            self.tr("Ignore All"), self.__ignoreSpellingAlways)
        
        self.showMenu.emit("Spelling", self.spellingMenu, self)
    
    def __contextMenuSpellingTriggered(self, action):
        """
        Private slot to handle the selection of a suggestion of the spelling
        context menu.
        
        @param action reference to the action that was selected (QAction)
        """
        if action in self.spellingSuggActs:
            replacement = action.text()
            line, index = self.lineIndexFromPosition(self.spellingMenuPos)
            wordStart, wordEnd = self.getWordBoundaries(line, index)
            self.setSelection(line, wordStart, line, wordEnd)
            self.beginUndoAction()
            self.removeSelectedText()
            self.insert(replacement)
            self.endUndoAction()
    
    def __addToSpellingDictionary(self):
        """
        Private slot to add the word below the spelling context menu to the
        dictionary.
        """
        line, index = self.lineIndexFromPosition(self.spellingMenuPos)
        word = self.getWord(line, index)
        self.spell.add(word)
        
        wordStart, wordEnd = self.getWordBoundaries(line, index)
        self.clearIndicator(self.spellingIndicator, line, wordStart,
                            line, wordEnd)
        if Preferences.getEditor("AutoSpellCheckingEnabled"):
            self.spell.checkDocumentIncrementally()
    
    def __removeFromSpellingDictionary(self):
        """
        Private slot to remove the word below the context menu to the
        dictionary.
        """
        line, index = self.lineIndexFromPosition(self.spellingMenuPos)
        word = self.getWord(line, index)
        self.spell.remove(word)
        
        if Preferences.getEditor("AutoSpellCheckingEnabled"):
            self.spell.checkDocumentIncrementally()
    
    def __ignoreSpellingAlways(self):
        """
        Private to always ignore the word below the spelling context menu.
        """
        line, index = self.lineIndexFromPosition(self.spellingMenuPos)
        word = self.getWord(line, index)
        self.spell.ignoreAlways(word)
        if Preferences.getEditor("AutoSpellCheckingEnabled"):
            self.spell.checkDocumentIncrementally()
    
    #######################################################################
    ## Cooperation related methods
    #######################################################################
    
    def getSharingStatus(self):
        """
        Public method to get some share status info.
        
        @return tuple indicating, if the editor is sharable, the sharing
            status, if it is inside a locally initiated shared edit session
            and if it is inside a remotely initiated shared edit session
            (boolean, boolean, boolean, boolean)
        """
        return self.fileName is not None and \
            self.project.isOpen() and \
            self.project.isProjectFile(self.fileName), \
            self.__isShared, self.__inSharedEdit, self.__inRemoteSharedEdit
    
    def shareConnected(self, connected):
        """
        Public slot to handle a change of the connected state.
        
        @param connected flag indicating the connected state (boolean)
        """
        if not connected:
            self.__inRemoteSharedEdit = False
            self.setReadOnly(False)
            self.__updateReadOnly()
            self.cancelSharedEdit(send=False)
            self.__isSyncing = False
            self.__receivedWhileSyncing = []
    
    def shareEditor(self, share):
        """
        Public slot to set the shared status of the editor.
        
        @param share flag indicating the share status (boolean)
        """
        self.__isShared = share
        if not share:
            self.shareConnected(False)
    
    def startSharedEdit(self):
        """
        Public slot to start a shared edit session for the editor.
        """
        self.__inSharedEdit = True
        self.__savedText = self.text()
        hash = str(
            QCryptographicHash.hash(
                Utilities.encode(self.__savedText, self.encoding)[0],
                QCryptographicHash.Sha1).toHex(),
            encoding="utf-8")
        self.__send(Editor.StartEditToken, hash)
    
    def sendSharedEdit(self):
        """
        Public slot to end a shared edit session for the editor and
        send the changes.
        """
        commands = self.__calculateChanges(self.__savedText, self.text())
        self.__send(Editor.EndEditToken, commands)
        self.__inSharedEdit = False
        self.__savedText = ""
    
    def cancelSharedEdit(self, send=True):
        """
        Public slot to cancel a shared edit session for the editor.
        
        @keyparam send flag indicating to send the CancelEdit command (boolean)
        """
        self.__inSharedEdit = False
        self.__savedText = ""
        if send:
            self.__send(Editor.CancelEditToken)
    
    def __send(self, token, args=None):
        """
        Private method to send an editor command to remote editors.
        
        @param token command token (string)
        @param args arguments for the command (string)
        """
        if self.vm.isConnected():
            msg = ""
            if token in (Editor.StartEditToken,
                         Editor.EndEditToken,
                         Editor.RequestSyncToken,
                         Editor.SyncToken):
                msg = "{0}{1}{2}".format(
                    token,
                    Editor.Separator,
                    args
                )
            elif token == Editor.CancelEditToken:
                msg = "{0}{1}c".format(
                    token,
                    Editor.Separator
                )
            
            self.vm.send(self.fileName, msg)
    
    def receive(self, command):
        """
        Public slot to handle received editor commands.
        
        @param command command string (string)
        """
        if self.__isShared:
            if self.__isSyncing and \
               not command.startswith(Editor.SyncToken + Editor.Separator):
                self.__receivedWhileSyncing.append(command)
            else:
                self.__dispatchCommand(command)
    
    def __dispatchCommand(self, command):
        """
        Private method to dispatch received commands.
        
        @param command command to be processed (string)
        """
        token, argsString = command.split(Editor.Separator, 1)
        if token == Editor.StartEditToken:
            self.__processStartEditCommand(argsString)
        elif token == Editor.CancelEditToken:
            self.shareConnected(False)
        elif token == Editor.EndEditToken:
            self.__processEndEditCommand(argsString)
        elif token == Editor.RequestSyncToken:
            self.__processRequestSyncCommand(argsString)
        elif token == Editor.SyncToken:
            self.__processSyncCommand(argsString)
    
    def __processStartEditCommand(self, argsString):
        """
        Private slot to process a remote StartEdit command.
        
        @param argsString string containing the command parameters (string)
        """
        if not self.__inSharedEdit and not self.__inRemoteSharedEdit:
            self.__inRemoteSharedEdit = True
            self.setReadOnly(True)
            self.__updateReadOnly()
            hash = str(
                QCryptographicHash.hash(
                    Utilities.encode(self.text(), self.encoding)[0],
                    QCryptographicHash.Sha1).toHex(),
                encoding="utf-8")
            if hash != argsString:
                # text is different to the remote site, request to sync it
                self.__isSyncing = True
                self.__send(Editor.RequestSyncToken, argsString)
    
    def __calculateChanges(self, old, new):
        """
        Private method to determine change commands to convert old text into
        new text.
        
        @param old old text (string)
        @param new new text (string)
        @return commands to change old into new (string)
        """
        oldL = old.splitlines()
        newL = new.splitlines()
        matcher = difflib.SequenceMatcher(None, oldL, newL)
        
        formatStr = "@@{0} {1} {2} {3}"
        commands = []
        for token, i1, i2, j1, j2 in matcher.get_opcodes():
            if token == "insert":
                commands.append(formatStr.format("i", j1, j2 - j1, -1))
                commands.extend(newL[j1:j2])
            elif token == "delete":
                commands.append(formatStr.format("d", j1, i2 - i1, -1))
            elif token == "replace":
                commands.append(formatStr.format("r", j1, i2 - i1, j2 - j1))
                commands.extend(newL[j1:j2])
        
        return "\n".join(commands) + "\n"
    
    def __processEndEditCommand(self, argsString):
        """
        Private slot to process a remote EndEdit command.
        
        @param argsString string containing the command parameters (string)
        """
        commands = argsString.splitlines()
        sep = self.getLineSeparator()
        cur = self.getCursorPosition()
        
        self.setReadOnly(False)
        self.beginUndoAction()
        while commands:
            commandLine = commands.pop(0)
            if not commandLine.startswith("@@"):
                continue
            
            args = commandLine.split()
            command = args.pop(0)
            pos, l1, l2 = [int(arg) for arg in args]
            if command == "@@i":
                txt = sep.join(commands[0:l1]) + sep
                self.insertAt(txt, pos, 0)
                del commands[0:l1]
            elif command == "@@d":
                self.setSelection(pos, 0, pos + l1, 0)
                self.removeSelectedText()
            elif command == "@@r":
                self.setSelection(pos, 0, pos + l1, 0)
                self.removeSelectedText()
                txt = sep.join(commands[0:l2]) + sep
                self.insertAt(txt, pos, 0)
                del commands[0:l2]
        self.endUndoAction()
        self.__updateReadOnly()
        self.__inRemoteSharedEdit = False
        
        self.setCursorPosition(*cur)
    
    def __processRequestSyncCommand(self, argsString):
        """
        Private slot to process a remote RequestSync command.
        
        @param argsString string containing the command parameters (string)
        """
        if self.__inSharedEdit:
            hash = str(
                QCryptographicHash.hash(
                    Utilities.encode(self.__savedText, self.encoding)[0],
                    QCryptographicHash.Sha1).toHex(),
                encoding="utf-8")
            
            if hash == argsString:
                self.__send(Editor.SyncToken, self.__savedText)
    
    def __processSyncCommand(self, argsString):
        """
        Private slot to process a remote Sync command.
        
        @param argsString string containing the command parameters (string)
        """
        if self.__isSyncing:
            cur = self.getCursorPosition()
            
            self.setReadOnly(False)
            self.beginUndoAction()
            self.selectAll()
            self.removeSelectedText()
            self.insertAt(argsString, 0, 0)
            self.endUndoAction()
            self.setReadOnly(True)
            
            self.setCursorPosition(*cur)
            
            while self.__receivedWhileSyncing:
                command = self.__receivedWhileSyncing.pop(0)
                self.__dispatchCommand(command)
            
            self.__isSyncing = False
    
    #######################################################################
    ## Special search related methods
    #######################################################################
    
    def searchCurrentWordForward(self):
        """
        Public slot to search the current word forward.
        """
        self.__searchCurrentWord(forward=True)
    
    def searchCurrentWordBackward(self):
        """
        Public slot to search the current word backward.
        """
        self.__searchCurrentWord(forward=False)
    
    def __searchCurrentWord(self, forward=True):
        """
        Private slot to search the next occurrence of the current word.
        
        @param forward flag indicating the search direction (boolean)
        """
        self.hideFindIndicator()
        line, index = self.getCursorPosition()
        word = self.getCurrentWord()
        wordStart, wordEnd = self.getCurrentWordBoundaries()
        wordStartPos = self.positionFromLineIndex(line, wordStart)
        wordEndPos = self.positionFromLineIndex(line, wordEnd)
        
        regExp = re.compile(r"\b{0}\b".format(word))
        if forward:
            startPos = wordEndPos
        else:
            startPos = wordStartPos
        
        matches = [m for m in regExp.finditer(self.text())]
        if matches:
            if forward:
                matchesAfter = [m for m in matches if m.start() >= startPos]
                if matchesAfter:
                    match = matchesAfter[0]
                else:
                    # wrap around
                    match = matches[0]
            else:
                matchesBefore = [m for m in matches if m.start() < startPos]
                if matchesBefore:
                    match = matchesBefore[-1]
                else:
                    # wrap around
                    match = matches[-1]
            line, index = self.lineIndexFromPosition(match.start())
            self.setSelection(line, index + len(match.group(0)), line, index)
            self.showFindIndicator(line, index,
                                   line, index + len(match.group(0)))
    
    #######################################################################
    ## Sort related methods
    #######################################################################
    
    def sortLines(self):
        """
        Public slot to sort the lines spanned by a rectangular selection.
        """
        if not self.selectionIsRectangle():
            return
        
        from .SortOptionsDialog import SortOptionsDialog
        dlg = SortOptionsDialog()
        if dlg.exec_() == QDialog.Accepted:
            ascending, alnum, caseSensitive = dlg.getData()
            origStartLine, origStartIndex, origEndLine, origEndIndex = \
                self.getRectangularSelection()
            # convert to upper-left to lower-right
            startLine = min(origStartLine, origEndLine)
            startIndex = min(origStartIndex, origEndIndex)
            endLine = max(origStartLine, origEndLine)
            endIndex = max(origStartIndex, origEndIndex)
            
            # step 1: extract the text of the rectangular selection and
            #         the lines
            selText = {}
            txtLines = {}
            for line in range(startLine, endLine + 1):
                txtLines[line] = self.text(line)
                txt = txtLines[line][startIndex:endIndex].strip()
                if not alnum:
                    try:
                        txt = float(txt)
                    except ValueError:
                        E5MessageBox.critical(
                            self,
                            self.tr("Sort Lines"),
                            self.tr(
                                """The selection contains illegal data for a"""
                                """ numerical sort."""))
                        return
                
                if txt in selText:
                    selText[txt].append(line)
                else:
                    selText[txt] = [line]
            
            # step 2: calculate the sort parameters
            reverse = not ascending
            if alnum and not caseSensitive:
                keyFun = str.lower
            else:
                keyFun = None
            
            # step 3: sort the lines
            eol = self.getLineSeparator()
            lastWithEol = True
            newLines = []
            for txt in sorted(selText.keys(), key=keyFun, reverse=reverse):
                for line in selText[txt]:
                    txt = txtLines[line]
                    if not txt.endswith(eol):
                        lastWithEol = False
                        txt += eol
                    newLines.append(txt)
            if not lastWithEol:
                newLines[-1] = newLines[-1][:-len(eol)]
            
            # step 4: replace the lines by the sorted ones
            self.setSelection(startLine, 0, endLine + 1, 0)
            self.beginUndoAction()
            self.replaceSelectedText("".join(newLines))
            self.endUndoAction()
            
            # step 5: reset the rectangular selection
            self.setRectangularSelection(origStartLine, origStartIndex,
                                         origEndLine, origEndIndex)
            self.selectionChanged.emit()
    
    #######################################################################
    ## Mouse click handler related methods
    #######################################################################
    
    def mouseReleaseEvent(self, evt):
        """
        Protected method calling a registered mouse click handler function.
        
        @param evt event object
        @type QMouseEvent
        """
        modifiers = evt.modifiers()
        button = evt.button()
        key = (int(modifiers), int(button))
        
        self.vm.eventFilter(self, evt)
        super(Editor, self).mouseReleaseEvent(evt)
        
        if button != Qt.NoButton and \
            Preferences.getEditor("MouseClickHandlersEnabled") and \
                key in self.__mouseClickHandlers:
            evt.accept()
            self.__mouseClickHandlers[key][1](self)
    
    def setMouseClickHandler(self, name, modifiers, button, function):
        """
        Public method to set a mouse click handler.
        
        @param name name of the plug-in (or 'internal') setting this handler
        @type str
        @param modifiers keyboard modifiers of the handler
        @type Qt.KeyboardModifiers or int
        @param button mouse button of the handler
        @type Qt.MouseButton or int
        @param function handler function
        @type func
        @return flag indicating success
        @rtype bool
        """
        if int(button):
            key = (int(modifiers), int(button))
            if key in self.__mouseClickHandlers:
                E5MessageBox.warning(
                    self,
                    self.tr("Register Mouse Click Handler"),
                    self.tr("""A mouse click handler for "{0}" was already"""
                            """ registered by "{1}". Aborting request by"""
                            """ "{2}"...""").format(
                        MouseUtilities.MouseButtonModifier2String(
                            modifiers, button),
                        self.__mouseClickHandlers[key][0],
                        name))
                return False
            
            self.__mouseClickHandlers[key] = (name, function)
            return True
        
        return False
    
    def getMouseClickHandler(self, modifiers, button):
        """
        Public method to get a registered mouse click handler.
        
        @param modifiers keyboard modifiers of the handler
        @type Qt.KeyboardModifiers
        @param button mouse button of the handler
        @type Qt.MouseButton
        @return plug-in name and registered function
        @rtype tuple of str and func
        """
        key = (int(modifiers), int(button))
        if key in self.__mouseClickHandlers:
            return self.__mouseClickHandlers[key]
        else:
            return ("", None)
    
    def getMouseClickHandlers(self, name):
        """
        Public method to get all registered mouse click handlers of
        a plug-in.
        
        @param name name of the plug-in
        @type str
        @return registered mouse click handlers as list of modifiers,
            mouse button and function
        @rtype list of tuple of (Qt.KeyboardModifiers, Qt.MouseButton,func)
        """
        lst = []
        for key, value in self.__mouseClickHandlers.items():
            if value[0] == name:
                lst.append((key[0], key[1], value[1]))
        return lst
    
    def removeMouseClickHandler(self, modifiers, button):
        """
        Public method to un-registered a mouse click handler.
        
        @param modifiers keyboard modifiers of the handler
        @type Qt.KeyboardModifiers
        @param button mouse button of the handler
        @type Qt.MouseButton
        """
        key = (int(modifiers), int(button))
        if key in self.__mouseClickHandlers:
            del self.__mouseClickHandlers[key]
    
    def removeMouseClickHandlers(self, name):
        """
        Public method to un-registered all mouse click handlers of
        a plug-in.
        
        @param name name of the plug-in
        @type str
        """
        keys = []
        for key in self.__mouseClickHandlers:
            if self.__mouseClickHandlers[key][0] == name:
                keys.append(key)
        for key in keys:
            del self.__mouseClickHandlers[key]
