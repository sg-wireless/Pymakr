# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the viewmanager base class.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSignal, QSignalMapper, QTimer, \
    QFileInfo, QRegExp, QObject, Qt, QCoreApplication
from PyQt5.QtGui import QColor, QKeySequence, QPalette, QPixmap
from PyQt5.QtWidgets import QLineEdit, QToolBar, QWidgetAction, QDialog, \
    QApplication, QMenu, QComboBox
from PyQt5.Qsci import QsciScintilla

from E5Gui.E5Application import e5App
from E5Gui import E5FileDialog, E5MessageBox

from Globals import recentNameFiles, isMacPlatform

import Preferences

from QScintilla.Editor import Editor

import Utilities

import UI.PixmapCache
import UI.Config

from E5Gui.E5Action import E5Action, createActionGroup


class QuickSearchLineEdit(QLineEdit):
    """
    Class implementing a line edit that reacts to newline and cancel commands.
    
    @signal escPressed() emitted after the cancel command was activated
    @signal returnPressed() emitted after a newline command was activated
    @signal gotFocus() emitted when the focus is changed to this widget
    """
    escPressed = pyqtSignal()
    gotFocus = pyqtSignal()
    
    def editorCommand(self, cmd):
        """
        Public method to perform an editor command.
        
        @param cmd the scintilla command to be performed
        """
        if cmd == QsciScintilla.SCI_NEWLINE:
            cb = self.parent()
            hasEntry = cb.findText(self.text()) != -1
            if not hasEntry:
                if cb.insertPolicy() == QComboBox.InsertAtTop:
                    cb.insertItem(0, self.text())
                else:
                    cb.addItem(self.text())
            self.returnPressed.emit()
        elif cmd == QsciScintilla.SCI_CANCEL:
            self.escPressed.emit()
    
    def keyPressEvent(self, evt):
        """
        Protected method to handle the press of the ESC key.
        
        @param evt key event (QKeyPressEvent)
        """
        if evt.key() == Qt.Key_Escape:
            self.escPressed.emit()
        else:
            super(QuickSearchLineEdit, self).keyPressEvent(evt)  # pass it on
    
    def focusInEvent(self, evt):
        """
        Protected method to record the current editor widget.
        
        @param evt focus event (QFocusEvent)
        """
        self.gotFocus.emit()
        super(QuickSearchLineEdit, self).focusInEvent(evt)   # pass it on


class ViewManager(QObject):
    """
    Base class inherited by all specific viewmanager classes.
    
    It defines the interface to be implemented by specific
    viewmanager classes and all common methods.
    
    @signal changeCaption(str) emitted if a change of the caption is necessary
    @signal editorChanged(str) emitted when the current editor has changed
    @signal editorChangedEd(Editor) emitted when the current editor has changed
    @signal lastEditorClosed() emitted after the last editor window was closed
    @signal editorOpened(str) emitted after an editor window was opened
    @signal editorOpenedEd(Editor) emitted after an editor window was opened
    @signal editorClosed(str) emitted just before an editor window gets closed
    @signal editorClosedEd(Editor) emitted just before an editor window gets
        closed
    @signal editorRenamed(str) emitted after an editor was renamed
    @signal editorRenamedEd(Editor) emitted after an editor was renamed
    @signal editorSaved(str) emitted after an editor window was saved
    @signal editorSavedEd(Editor) emitted after an editor window was saved
    @signal checkActions(Editor) emitted when some actions should be checked
        for their status
    @signal cursorChanged(Editor) emitted after the cursor position of the
        active window has changed
    @signal breakpointToggled(Editor) emitted when a breakpoint is toggled
    @signal bookmarkToggled(Editor) emitted when a bookmark is toggled
    @signal syntaxerrorToggled(Editor) emitted when a syntax error is toggled
    @signal previewStateChanged(bool) emitted to signal a change in the
        preview state
    @signal editorLanguageChanged(Editor) emitted to signal a change of an
        editor's language
    @signal editorTextChanged(Editor) emitted to signal a change of an
        editor's text
    @signal editorLineChanged(str,int) emitted to signal a change of an
        editor's current line (line is given one based)
    """
    changeCaption = pyqtSignal(str)
    editorChanged = pyqtSignal(str)
    editorChangedEd = pyqtSignal(Editor)
    lastEditorClosed = pyqtSignal()
    editorOpened = pyqtSignal(str)
    editorOpenedEd = pyqtSignal(Editor)
    editorClosed = pyqtSignal(str)
    editorClosedEd = pyqtSignal(Editor)
    editorRenamed = pyqtSignal(str)
    editorRenamedEd = pyqtSignal(Editor)
    editorSaved = pyqtSignal(str)
    editorSavedEd = pyqtSignal(Editor)
    checkActions = pyqtSignal(Editor)
    cursorChanged = pyqtSignal(Editor)
    breakpointToggled = pyqtSignal(Editor)
    bookmarkToggled = pyqtSignal(Editor)
    syntaxerrorToggled = pyqtSignal(Editor)
    previewStateChanged = pyqtSignal(bool)
    editorLanguageChanged = pyqtSignal(Editor)
    editorTextChanged = pyqtSignal(Editor)
    editorLineChanged = pyqtSignal(str, int)
    
    def __init__(self):
        """
        Constructor
        """
        super(ViewManager, self).__init__()
        
        # initialize the instance variables
        self.editors = []
        self.currentEditor = None
        self.untitledCount = 0
        self.srHistory = {
            "search": [],
            "replace": []
        }
        self.editorsCheckFocusIn = True
        
        self.recent = []
        self.__loadRecent()
        
        self.bookmarked = []
        bs = Preferences.Prefs.settings.value("Bookmarked/Sources")
        if bs is not None:
            self.bookmarked = bs
        
        # initialize the autosave timer
        self.autosaveInterval = Preferences.getEditor("AutosaveInterval")
        self.autosaveTimer = QTimer(self)
        self.autosaveTimer.setObjectName("AutosaveTimer")
        self.autosaveTimer.setSingleShot(True)
        self.autosaveTimer.timeout.connect(self.__autosave)
        
        # initialize the APIs manager
        from QScintilla.APIsManager import APIsManager
        self.apisManager = APIsManager(parent=self)
        
        self.__cooperationClient = None
        
        self.__lastFocusWidget = None
        
    def setReferences(self, ui, dbs):
        """
        Public method to set some references needed later on.
        
        @param ui reference to the main user interface
        @param dbs reference to the debug server object
        """
        from QScintilla.SearchReplaceWidget import SearchReplaceSlidingWidget
        
        self.ui = ui
        self.dbs = dbs
        
        self.__searchWidget = SearchReplaceSlidingWidget(False, self, ui)
        self.__replaceWidget = SearchReplaceSlidingWidget(True, self, ui)
        
        self.checkActions.connect(self.__searchWidget.updateSelectionCheckBox)
        self.checkActions.connect(self.__replaceWidget.updateSelectionCheckBox)
        
    def searchWidget(self):
        """
        Public method to get a reference to the search widget.
        
        @return reference to the search widget (SearchReplaceSlidingWidget)
        """
        return self.__searchWidget
        
    def replaceWidget(self):
        """
        Public method to get a reference to the replace widget.
        
        @return reference to the replace widget (SearchReplaceSlidingWidget)
        """
        return self.__replaceWidget
        
    def __loadRecent(self):
        """
        Private method to load the recently opened filenames.
        """
        self.recent = []
        Preferences.Prefs.rsettings.sync()
        rs = Preferences.Prefs.rsettings.value(recentNameFiles)
        if rs is not None:
            for f in Preferences.toList(rs):
                if QFileInfo(f).exists():
                    self.recent.append(f)
        
    def __saveRecent(self):
        """
        Private method to save the list of recently opened filenames.
        """
        Preferences.Prefs.rsettings.setValue(recentNameFiles, self.recent)
        Preferences.Prefs.rsettings.sync()
        
    def getMostRecent(self):
        """
        Public method to get the most recently opened file.
        
        @return path of the most recently opened file (string)
        """
        if len(self.recent):
            return self.recent[0]
        else:
            return None
        
    def setSbInfo(self, sbLine, sbPos, sbWritable, sbEncoding, sbLanguage,
                  sbEol, sbZoom):
        """
        Public method to transfer statusbar info from the user interface to
        viewmanager.
        
        @param sbLine reference to the line number part of the statusbar
            (QLabel)
        @param sbPos reference to the character position part of the statusbar
            (QLabel)
        @param sbWritable reference to the writability indicator part of
            the statusbar (QLabel)
        @param sbEncoding reference to the encoding indicator part of the
            statusbar (QLabel)
        @param sbLanguage reference to the language indicator part of the
            statusbar (QLabel)
        @param sbEol reference to the eol indicator part of the statusbar
            (QLabel)
        @param sbZoom reference to the zoom widget (E5ZoomWidget)
        """
        self.sbLine = sbLine
        self.sbPos = sbPos
        self.sbWritable = sbWritable
        self.sbEnc = sbEncoding
        self.sbLang = sbLanguage
        self.sbEol = sbEol
        self.sbZoom = sbZoom
        self.sbZoom.valueChanged.connect(self.__zoomTo)
        self.__setSbFile(zoom=0)
        
        self.sbLang.clicked.connect(self.__showLanguagesMenu)
        self.sbEol.clicked.connect(self.__showEolMenu)
        self.sbEnc.clicked.connect(self.__showEncodingsMenu)
    
    ##################################################################
    ## Below are menu handling methods for status bar labels
    ##################################################################
    
    def __showLanguagesMenu(self, pos):
        """
        Private slot to show the Languages menu of the current editor.
        
        @param pos position the menu should be shown at (QPoint)
        """
        aw = self.activeWindow()
        if aw is not None:
            menu = aw.getMenu("Languages")
            if menu is not None:
                menu.exec_(pos)
    
    def __showEolMenu(self, pos):
        """
        Private slot to show the EOL menu of the current editor.
        
        @param pos position the menu should be shown at (QPoint)
        """
        aw = self.activeWindow()
        if aw is not None:
            menu = aw.getMenu("Eol")
            if menu is not None:
                menu.exec_(pos)
    
    def __showEncodingsMenu(self, pos):
        """
        Private slot to show the Encodings menu of the current editor.
        
        @param pos position the menu should be shown at (QPoint)
        """
        aw = self.activeWindow()
        if aw is not None:
            menu = aw.getMenu("Encodings")
            if menu is not None:
                menu.exec_(pos)
    
    ###########################################################################
    ## methods below need to be implemented by a subclass
    ###########################################################################
    
    def canCascade(self):
        """
        Public method to signal if cascading of managed windows is available.
        
        @ireturn flag indicating cascading of windows is available
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def canTile(self):
        """
        Public method to signal if tiling of managed windows is available.
        
        @ireturn flag indicating tiling of windows is available
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def tile(self):
        """
        Public method to tile the managed windows.
        
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def cascade(self):
        """
        Public method to cascade the managed windows.
        
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def activeWindow(self):
        """
        Public method to return the active (i.e. current) window.
        
        @ireturn reference to the active editor
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def _removeAllViews(self):
        """
        Protected method to remove all views (i.e. windows).
        
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def _removeView(self, win):
        """
        Protected method to remove a view (i.e. window).
        
        @param win editor window to be removed
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def _addView(self, win, fn=None, noName="", next=False):
        """
        Protected method to add a view (i.e. window).
        
        @param win editor assembly to be added
        @param fn filename of this editor
        @param noName name to be used for an unnamed editor (string)
        @param next flag indicating to add the view next to the current
            view (bool)
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def _showView(self, win, fn=None):
        """
        Protected method to show a view (i.e. window).
        
        @param win editor assembly to be shown
        @param fn filename of this editor
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def showWindowMenu(self, windowMenu):
        """
        Public method to set up the viewmanager part of the Window menu.
        
        @param windowMenu reference to the window menu
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def _initWindowActions(self):
        """
        Protected method to define the user interface actions for window
        handling.
        
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def setEditorName(self, editor, newName):
        """
        Public method to change the displayed name of the editor.
        
        @param editor editor window to be changed
        @param newName new name to be shown (string)
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
        
    def _modificationStatusChanged(self, m, editor):
        """
        Protected slot to handle the modificationStatusChanged signal.
        
        @param m flag indicating the modification status (boolean)
        @param editor editor window changed
        @exception RuntimeError Not implemented
        """
        raise RuntimeError('Not implemented')
    
    #####################################################################
    ## methods above need to be implemented by a subclass
    #####################################################################
    
    def canSplit(self):
        """
        Public method to signal if splitting of the view is available.
        
        @return flag indicating splitting of the view is available.
        """
        return False
        
    def addSplit(self):
        """
        Public method used to split the current view.
        """
        pass
        
    def removeSplit(self):
        """
        Public method used to remove the current split view.
        
        @return Flag indicating successful deletion
        """
        return False
        
    def getSplitOrientation(self):
        """
        Public method to get the orientation of the split view.
        
        @return orientation of the split (Qt.Horizontal or Qt.Vertical)
        """
        return Qt.Vertical
        
    def setSplitOrientation(self, orientation):
        """
        Public method used to set the orientation of the split view.
        
        @param orientation orientation of the split
            (Qt.Horizontal or Qt.Vertical)
        """
        pass
        
    def nextSplit(self):
        """
        Public slot used to move to the next split.
        """
        pass
        
    def prevSplit(self):
        """
        Public slot used to move to the previous split.
        """
        pass
        
    def eventFilter(self, object, event):
        """
        Public method called to filter an event.
        
        @param object object, that generated the event (QObject)
        @param event the event, that was generated by object (QEvent)
        @return flag indicating if event was filtered out
        """
        return False
    
    #####################################################################
    ## methods above need to be implemented by a subclass, that supports
    ## splitting of the viewmanager area.
    #####################################################################
    
    def initActions(self):
        """
        Public method defining the user interface actions.
        """
        # list containing all edit actions
        self.editActions = []
        
        # list containing all file actions
        self.fileActions = []
        
        # list containing all search actions
        self.searchActions = []
        
        # list containing all view actions
        self.viewActions = []
        
        # list containing all window actions
        self.windowActions = []
        
        # list containing all macro actions
        self.macroActions = []
        
        # list containing all bookmark actions
        self.bookmarkActions = []
        
        # list containing all spell checking actions
        self.spellingActions = []
        
        self.__actions = {
            "bookmark": self.bookmarkActions,
            "edit": self.editActions,
            "file": self.fileActions,
            "macro": self.macroActions,
            "search": self.searchActions,
            "spelling": self.spellingActions,
            "view": self.viewActions,
            "window": self.windowActions,
        }
        
        self._initWindowActions()
        self.__initFileActions()
        self.__initEditActions()
        self.__initSearchActions()
        self.__initViewActions()
        self.__initMacroActions()
        self.__initBookmarkActions()
        self.__initSpellingActions()
        
    ##################################################################
    ## Initialize the file related actions, file menu and toolbar
    ##################################################################
    
    def __initFileActions(self):
        """
        Private method defining the user interface actions for file handling.
        """
        self.newAct = E5Action(
            QCoreApplication.translate('ViewManager', 'New'),
            UI.PixmapCache.getIcon("new.png"),
            QCoreApplication.translate('ViewManager', '&New'),
            QKeySequence(
                QCoreApplication.translate('ViewManager', "Ctrl+N",
                                           "File|New")),
            0, self, 'vm_file_new')
        self.newAct.setStatusTip(
            QCoreApplication.translate(
                'ViewManager', 'Open an empty editor window'))
        self.newAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>New</b>"""
            """<p>An empty editor window will be created.</p>"""
        ))
        self.newAct.triggered.connect(self.newEditor)
        self.fileActions.append(self.newAct)
        
        self.openAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Open'),
            UI.PixmapCache.getIcon("open.png"),
            QCoreApplication.translate('ViewManager', '&Open...'),
            QKeySequence(
                QCoreApplication.translate('ViewManager', "Ctrl+O",
                                           "File|Open")),
            0, self, 'vm_file_open')
        self.openAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Open a file'))
        self.openAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Open a file</b>"""
            """<p>You will be asked for the name of a file to be opened"""
            """ in an editor window.</p>"""
        ))
        self.openAct.triggered.connect(self.__openFiles)
        self.fileActions.append(self.openAct)
        
        self.closeActGrp = createActionGroup(self)
        
        self.closeAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Close'),
            UI.PixmapCache.getIcon("close.png"),
            QCoreApplication.translate('ViewManager', '&Close'),
            QKeySequence(
                QCoreApplication.translate('ViewManager', "Ctrl+W",
                                           "File|Close")),
            0, self.closeActGrp, 'vm_file_close')
        self.closeAct.setStatusTip(
            QCoreApplication.translate('ViewManager',
                                       'Close the current window'))
        self.closeAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Close Window</b>"""
            """<p>Close the current window.</p>"""
        ))
        self.closeAct.triggered.connect(self.closeCurrentWindow)
        self.fileActions.append(self.closeAct)
        
        self.closeAllAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Close All'),
            QCoreApplication.translate('ViewManager', 'Clos&e All'),
            0, 0, self.closeActGrp, 'vm_file_close_all')
        self.closeAllAct.setStatusTip(
            QCoreApplication.translate('ViewManager',
                                       'Close all editor windows'))
        self.closeAllAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Close All Windows</b>"""
            """<p>Close all editor windows.</p>"""
        ))
        self.closeAllAct.triggered.connect(self.closeAllWindows)
        self.fileActions.append(self.closeAllAct)
        
        self.closeActGrp.setEnabled(False)
        
        self.saveActGrp = createActionGroup(self)
        
        self.saveAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Save'),
            UI.PixmapCache.getIcon("fileSave.png"),
            QCoreApplication.translate('ViewManager', '&Save'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+S", "File|Save")),
            0, self.saveActGrp, 'vm_file_save')
        self.saveAct.setStatusTip(
            QCoreApplication.translate('ViewManager', 'Save the current file'))
        self.saveAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Save File</b>"""
            """<p>Save the contents of current editor window.</p>"""
        ))
        self.saveAct.triggered.connect(self.saveCurrentEditor)
        self.fileActions.append(self.saveAct)
        
        self.saveAsAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Save as'),
            UI.PixmapCache.getIcon("fileSaveAs.png"),
            QCoreApplication.translate('ViewManager', 'Save &as...'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Shift+Ctrl+S", "File|Save As")),
            0, self.saveActGrp, 'vm_file_save_as')
        self.saveAsAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Save the current file to a new one'))
        self.saveAsAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Save File as</b>"""
            """<p>Save the contents of current editor window to a new file."""
            """ The file can be entered in a file selection dialog.</p>"""
        ))
        self.saveAsAct.triggered.connect(self.saveAsCurrentEditor)
        self.fileActions.append(self.saveAsAct)
        
        self.saveCopyAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Save Copy'),
            UI.PixmapCache.getIcon("fileSaveCopy.png"),
            QCoreApplication.translate('ViewManager', 'Save &Copy...'),
            0, 0, self.saveActGrp, 'vm_file_save_copy')
        self.saveCopyAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Save a copy of the current file'))
        self.saveCopyAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Save Copy</b>"""
            """<p>Save a copy of the contents of current editor window."""
            """ The file can be entered in a file selection dialog.</p>"""
        ))
        self.saveCopyAct.triggered.connect(self.saveCopyCurrentEditor)
        self.fileActions.append(self.saveCopyAct)
        
        self.saveAllAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Save all'),
            UI.PixmapCache.getIcon("fileSaveAll.png"),
            QCoreApplication.translate('ViewManager', 'Save a&ll'),
            0, 0, self.saveActGrp, 'vm_file_save_all')
        self.saveAllAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Save all files'))
        self.saveAllAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Save All Files</b>"""
            """<p>Save the contents of all editor windows.</p>"""
        ))
        self.saveAllAct.triggered.connect(self.saveAllEditors)
        self.fileActions.append(self.saveAllAct)
        
        self.saveActGrp.setEnabled(False)

        self.printAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Print'),
            UI.PixmapCache.getIcon("print.png"),
            QCoreApplication.translate('ViewManager', '&Print'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+P", "File|Print")),
            0, self, 'vm_file_print')
        self.printAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Print the current file'))
        self.printAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Print File</b>"""
            """<p>Print the contents of current editor window.</p>"""
        ))
        self.printAct.triggered.connect(self.printCurrentEditor)
        self.printAct.setEnabled(False)
        self.fileActions.append(self.printAct)
        
        self.printPreviewAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Print Preview'),
            UI.PixmapCache.getIcon("printPreview.png"),
            QCoreApplication.translate('ViewManager', 'Print Preview'),
            0, 0, self, 'vm_file_print_preview')
        self.printPreviewAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Print preview of the current file'))
        self.printPreviewAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Print Preview</b>"""
            """<p>Print preview of the current editor window.</p>"""
        ))
        self.printPreviewAct.triggered.connect(
            self.printPreviewCurrentEditor)
        self.printPreviewAct.setEnabled(False)
        self.fileActions.append(self.printPreviewAct)
        
        self.findFileNameAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Search File'),
            QCoreApplication.translate('ViewManager', 'Search &File...'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Alt+Ctrl+F", "File|Search File")),
            0, self, 'vm_file_search_file')
        self.findFileNameAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Search for a file'))
        self.findFileNameAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Search File</b>"""
            """<p>Search for a file.</p>"""
        ))
        self.findFileNameAct.triggered.connect(self.__findFileName)
        self.fileActions.append(self.findFileNameAct)
        
    def initFileMenu(self):
        """
        Public method to create the File menu.
        
        @return the generated menu
        """
        menu = QMenu(QCoreApplication.translate('ViewManager', '&File'),
                     self.ui)
        self.recentMenu = QMenu(
            QCoreApplication.translate('ViewManager', 'Open &Recent Files'),
            menu)
        self.bookmarkedMenu = QMenu(
            QCoreApplication.translate('ViewManager',
                                       'Open &Bookmarked Files'),
            menu)
        self.exportersMenu = self.__initContextMenuExporters()
        menu.setTearOffEnabled(True)
        
        menu.addAction(self.newAct)
        menu.addAction(self.openAct)
        self.menuRecentAct = menu.addMenu(self.recentMenu)
        menu.addMenu(self.bookmarkedMenu)
        menu.addSeparator()
        menu.addAction(self.closeAct)
        menu.addAction(self.closeAllAct)
        menu.addSeparator()
        menu.addAction(self.findFileNameAct)
        menu.addSeparator()
        menu.addAction(self.saveAct)
        menu.addAction(self.saveAsAct)
        menu.addAction(self.saveCopyAct)
        menu.addAction(self.saveAllAct)
        self.exportersMenuAct = menu.addMenu(self.exportersMenu)
        menu.addSeparator()
        menu.addAction(self.printPreviewAct)
        menu.addAction(self.printAct)
        
        self.recentMenu.aboutToShow.connect(self.__showRecentMenu)
        self.recentMenu.triggered.connect(self.__openSourceFile)
        self.bookmarkedMenu.aboutToShow.connect(self.__showBookmarkedMenu)
        self.bookmarkedMenu.triggered.connect(self.__openSourceFile)
        menu.aboutToShow.connect(self.__showFileMenu)
        
        self.exportersMenuAct.setEnabled(False)
        
        return menu
        
    def initFileToolbar(self, toolbarManager):
        """
        Public method to create the File toolbar.
        
        @param toolbarManager reference to a toolbar manager object
            (E5ToolBarManager)
        @return the generated toolbar
        """
        tb = QToolBar(QCoreApplication.translate('ViewManager', 'File'),
                      self.ui)
        tb.setIconSize(UI.Config.ToolBarIconSize)
        tb.setObjectName("FileToolbar")
        tb.setToolTip(QCoreApplication.translate('ViewManager', 'File'))
        
        tb.addAction(self.newAct)
        tb.addAction(self.openAct)
        tb.addAction(self.closeAct)
        tb.addSeparator()
        tb.addAction(self.saveAct)
        tb.addAction(self.saveAsAct)
        tb.addAction(self.saveCopyAct)
        tb.addAction(self.saveAllAct)
        
        toolbarManager.addToolBar(tb, tb.windowTitle())
        toolbarManager.addAction(self.printPreviewAct, tb.windowTitle())
        toolbarManager.addAction(self.printAct, tb.windowTitle())
        
        return tb
        
    def __initContextMenuExporters(self):
        """
        Private method used to setup the Exporters sub menu.
        
        @return reference to the generated menu (QMenu)
        """
        menu = QMenu(QCoreApplication.translate('ViewManager', "Export as"))
        
        import QScintilla.Exporters
        supportedExporters = QScintilla.Exporters.getSupportedFormats()
        exporters = sorted(list(supportedExporters.keys()))
        for exporter in exporters:
            act = menu.addAction(supportedExporters[exporter])
            act.setData(exporter)
        
        menu.triggered.connect(self.__exportMenuTriggered)
        
        return menu
    
    ##################################################################
    ## Initialize the edit related actions, edit menu and toolbar
    ##################################################################
    
    def __initEditActions(self):
        """
        Private method defining the user interface actions for the edit
            commands.
        """
        self.editActGrp = createActionGroup(self)
        
        self.undoAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Undo'),
            UI.PixmapCache.getIcon("editUndo.png"),
            QCoreApplication.translate('ViewManager', '&Undo'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+Z", "Edit|Undo")),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Alt+Backspace", "Edit|Undo")),
            self.editActGrp, 'vm_edit_undo')
        self.undoAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Undo the last change'))
        self.undoAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Undo</b>"""
            """<p>Undo the last change done in the current editor.</p>"""
        ))
        self.undoAct.triggered.connect(self.__editUndo)
        self.editActions.append(self.undoAct)
        
        self.redoAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Redo'),
            UI.PixmapCache.getIcon("editRedo.png"),
            QCoreApplication.translate('ViewManager', '&Redo'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+Shift+Z", "Edit|Redo")),
            0,
            self.editActGrp, 'vm_edit_redo')
        self.redoAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Redo the last change'))
        self.redoAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Redo</b>"""
            """<p>Redo the last change done in the current editor.</p>"""
        ))
        self.redoAct.triggered.connect(self.__editRedo)
        self.editActions.append(self.redoAct)
        
        self.revertAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Revert to last saved state'),
            QCoreApplication.translate(
                'ViewManager', 'Re&vert to last saved state'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+Y", "Edit|Revert")),
            0,
            self.editActGrp, 'vm_edit_revert')
        self.revertAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Revert to last saved state'))
        self.revertAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Revert to last saved state</b>"""
            """<p>Undo all changes up to the last saved state"""
            """ of the current editor.</p>"""
        ))
        self.revertAct.triggered.connect(self.__editRevert)
        self.editActions.append(self.revertAct)
        
        self.copyActGrp = createActionGroup(self.editActGrp)
        
        self.cutAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Cut'),
            UI.PixmapCache.getIcon("editCut.png"),
            QCoreApplication.translate('ViewManager', 'Cu&t'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+X", "Edit|Cut")),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Shift+Del", "Edit|Cut")),
            self.copyActGrp, 'vm_edit_cut')
        self.cutAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Cut the selection'))
        self.cutAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Cut</b>"""
            """<p>Cut the selected text of the current editor to the"""
            """ clipboard.</p>"""
        ))
        self.cutAct.triggered.connect(self.__editCut)
        self.editActions.append(self.cutAct)
        
        self.copyAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Copy'),
            UI.PixmapCache.getIcon("editCopy.png"),
            QCoreApplication.translate('ViewManager', '&Copy'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+C", "Edit|Copy")),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+Ins", "Edit|Copy")),
            self.copyActGrp, 'vm_edit_copy')
        self.copyAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Copy the selection'))
        self.copyAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Copy</b>"""
            """<p>Copy the selected text of the current editor to the"""
            """ clipboard.</p>"""
        ))
        self.copyAct.triggered.connect(self.__editCopy)
        self.editActions.append(self.copyAct)
        
        self.pasteAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Paste'),
            UI.PixmapCache.getIcon("editPaste.png"),
            QCoreApplication.translate('ViewManager', '&Paste'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+V", "Edit|Paste")),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Shift+Ins", "Edit|Paste")),
            self.copyActGrp, 'vm_edit_paste')
        self.pasteAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Paste the last cut/copied text'))
        self.pasteAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Paste</b>"""
            """<p>Paste the last cut/copied text from the clipboard to"""
            """ the current editor.</p>"""
        ))
        self.pasteAct.triggered.connect(self.__editPaste)
        self.editActions.append(self.pasteAct)
        
        self.deleteAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Clear'),
            UI.PixmapCache.getIcon("editDelete.png"),
            QCoreApplication.translate('ViewManager', 'Clear'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Alt+Shift+C", "Edit|Clear")),
            0,
            self.copyActGrp, 'vm_edit_clear')
        self.deleteAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Clear all text'))
        self.deleteAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Clear</b>"""
            """<p>Delete all text of the current editor.</p>"""
        ))
        self.deleteAct.triggered.connect(self.__editDelete)
        self.editActions.append(self.deleteAct)
        
        self.joinAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Join Lines'),
            QCoreApplication.translate('ViewManager', 'Join Lines'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+J", "Edit|Join Lines")),
            0,
            self.copyActGrp, 'vm_edit_join_lines')
        self.joinAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Join Lines'))
        self.joinAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Join Lines</b>"""
            """<p>Join the current and the next lines.</p>"""
        ))
        self.joinAct.triggered.connect(self.__editJoin)
        self.editActions.append(self.joinAct)
        
        self.indentAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Indent'),
            UI.PixmapCache.getIcon("editIndent.png"),
            QCoreApplication.translate('ViewManager', '&Indent'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+I", "Edit|Indent")),
            0,
            self.editActGrp, 'vm_edit_indent')
        self.indentAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Indent line'))
        self.indentAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Indent</b>"""
            """<p>Indents the current line or the lines of the"""
            """ selection by one level.</p>"""
        ))
        self.indentAct.triggered.connect(self.__editIndent)
        self.editActions.append(self.indentAct)
        
        self.unindentAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Unindent'),
            UI.PixmapCache.getIcon("editUnindent.png"),
            QCoreApplication.translate('ViewManager', 'U&nindent'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+Shift+I", "Edit|Unindent")),
            0,
            self.editActGrp, 'vm_edit_unindent')
        self.unindentAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Unindent line'))
        self.unindentAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Unindent</b>"""
            """<p>Unindents the current line or the lines of the"""
            """ selection by one level.</p>"""
        ))
        self.unindentAct.triggered.connect(self.__editUnindent)
        self.editActions.append(self.unindentAct)
        
        self.smartIndentAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Smart indent'),
            UI.PixmapCache.getIcon("editSmartIndent.png"),
            QCoreApplication.translate('ViewManager', 'Smart indent'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+Alt+I", "Edit|Smart indent")),
            0,
            self.editActGrp, 'vm_edit_smart_indent')
        self.smartIndentAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Smart indent Line or Selection'))
        self.smartIndentAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Smart indent</b>"""
            """<p>Indents the current line or the lines of the"""
            """ current selection smartly.</p>"""
        ))
        self.smartIndentAct.triggered.connect(self.__editSmartIndent)
        self.editActions.append(self.smartIndentAct)
        
        self.commentAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Comment'),
            UI.PixmapCache.getIcon("editComment.png"),
            QCoreApplication.translate('ViewManager', 'C&omment'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+M", "Edit|Comment")),
            0,
            self.editActGrp, 'vm_edit_comment')
        self.commentAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Comment Line or Selection'))
        self.commentAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Comment</b>"""
            """<p>Comments the current line or the lines of the"""
            """ current selection.</p>"""
        ))
        self.commentAct.triggered.connect(self.__editComment)
        self.editActions.append(self.commentAct)
        
        self.uncommentAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Uncomment'),
            UI.PixmapCache.getIcon("editUncomment.png"),
            QCoreApplication.translate('ViewManager', 'Unco&mment'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Alt+Ctrl+M", "Edit|Uncomment")),
            0,
            self.editActGrp, 'vm_edit_uncomment')
        self.uncommentAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Uncomment Line or Selection'))
        self.uncommentAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Uncomment</b>"""
            """<p>Uncomments the current line or the lines of the"""
            """ current selection.</p>"""
        ))
        self.uncommentAct.triggered.connect(self.__editUncomment)
        self.editActions.append(self.uncommentAct)
        
        self.toggleCommentAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Toggle Comment'),
            UI.PixmapCache.getIcon("editToggleComment.png"),
            QCoreApplication.translate('ViewManager', 'Toggle Comment'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+Shift+M", "Edit|Toggle Comment")),
            0,
            self.editActGrp, 'vm_edit_toggle_comment')
        self.toggleCommentAct.setStatusTip(QCoreApplication.translate(
            'ViewManager',
            'Toggle the comment of the current line, selection or'
            ' comment block'))
        self.toggleCommentAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Toggle Comment</b>"""
            """<p>If the current line does not start with a block comment,"""
            """ the current line or selection is commented. If it is already"""
            """ commented, this comment block is uncommented. </p>"""
        ))
        self.toggleCommentAct.triggered.connect(self.__editToggleComment)
        self.editActions.append(self.toggleCommentAct)
        
        self.streamCommentAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Stream Comment'),
            QCoreApplication.translate('ViewManager', 'Stream Comment'),
            0, 0,
            self.editActGrp, 'vm_edit_stream_comment')
        self.streamCommentAct.setStatusTip(QCoreApplication.translate(
            'ViewManager',
            'Stream Comment Line or Selection'))
        self.streamCommentAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Stream Comment</b>"""
            """<p>Stream comments the current line or the current"""
            """ selection.</p>"""
        ))
        self.streamCommentAct.triggered.connect(self.__editStreamComment)
        self.editActions.append(self.streamCommentAct)
        
        self.boxCommentAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Box Comment'),
            QCoreApplication.translate('ViewManager', 'Box Comment'),
            0, 0,
            self.editActGrp, 'vm_edit_box_comment')
        self.boxCommentAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Box Comment Line or Selection'))
        self.boxCommentAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Box Comment</b>"""
            """<p>Box comments the current line or the lines of the"""
            """ current selection.</p>"""
        ))
        self.boxCommentAct.triggered.connect(self.__editBoxComment)
        self.editActions.append(self.boxCommentAct)
        
        self.selectBraceAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Select to brace'),
            QCoreApplication.translate('ViewManager', 'Select to &brace'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+E", "Edit|Select to brace")),
            0,
            self.editActGrp, 'vm_edit_select_to_brace')
        self.selectBraceAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Select text to the matching brace'))
        self.selectBraceAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Select to brace</b>"""
            """<p>Select text of the current editor to the matching"""
            """ brace.</p>"""
        ))
        self.selectBraceAct.triggered.connect(self.__editSelectBrace)
        self.editActions.append(self.selectBraceAct)
        
        self.selectAllAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Select all'),
            UI.PixmapCache.getIcon("editSelectAll.png"),
            QCoreApplication.translate('ViewManager', '&Select all'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+A", "Edit|Select all")),
            0,
            self.editActGrp, 'vm_edit_select_all')
        self.selectAllAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Select all text'))
        self.selectAllAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Select All</b>"""
            """<p>Select all text of the current editor.</p>"""
        ))
        self.selectAllAct.triggered.connect(self.__editSelectAll)
        self.editActions.append(self.selectAllAct)
        
        self.deselectAllAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Deselect all'),
            QCoreApplication.translate('ViewManager', '&Deselect all'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Alt+Ctrl+A", "Edit|Deselect all")),
            0,
            self.editActGrp, 'vm_edit_deselect_all')
        self.deselectAllAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Deselect all text'))
        self.deselectAllAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Deselect All</b>"""
            """<p>Deselect all text of the current editor.</p>"""
        ))
        self.deselectAllAct.triggered.connect(self.__editDeselectAll)
        self.editActions.append(self.deselectAllAct)
        
        self.convertEOLAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Convert Line End Characters'),
            QCoreApplication.translate(
                'ViewManager', 'Convert &Line End Characters'),
            0, 0,
            self.editActGrp, 'vm_edit_convert_eol')
        self.convertEOLAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Convert Line End Characters'))
        self.convertEOLAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Convert Line End Characters</b>"""
            """<p>Convert the line end characters to the currently set"""
            """ type.</p>"""
        ))
        self.convertEOLAct.triggered.connect(self.__convertEOL)
        self.editActions.append(self.convertEOLAct)
        
        self.shortenEmptyAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Shorten empty lines'),
            QCoreApplication.translate('ViewManager', 'Shorten empty lines'),
            0, 0,
            self.editActGrp, 'vm_edit_shorten_empty_lines')
        self.shortenEmptyAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Shorten empty lines'))
        self.shortenEmptyAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Shorten empty lines</b>"""
            """<p>Shorten lines consisting solely of whitespace"""
            """ characters.</p>"""
        ))
        self.shortenEmptyAct.triggered.connect(self.__shortenEmptyLines)
        self.editActions.append(self.shortenEmptyAct)
        
        self.autoCompleteAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Complete'),
            QCoreApplication.translate('ViewManager', '&Complete'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+Space", "Edit|Complete")),
            0,
            self.editActGrp, 'vm_edit_autocomplete')
        self.autoCompleteAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Complete current word'))
        self.autoCompleteAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Complete</b>"""
            """<p>Performs a completion of the word containing"""
            """ the cursor.</p>"""
        ))
        self.autoCompleteAct.triggered.connect(self.__editAutoComplete)
        self.editActions.append(self.autoCompleteAct)
        
        self.autoCompleteFromDocAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Complete from Document'),
            QCoreApplication.translate(
                'ViewManager', 'Complete from Document'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+Shift+Space",
                "Edit|Complete from Document")),
            0,
            self.editActGrp, 'vm_edit_autocomplete_from_document')
        self.autoCompleteFromDocAct.setStatusTip(QCoreApplication.translate(
            'ViewManager',
            'Complete current word from Document'))
        self.autoCompleteFromDocAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Complete from Document</b>"""
            """<p>Performs a completion from document of the word"""
            """ containing the cursor.</p>"""
        ))
        self.autoCompleteFromDocAct.triggered.connect(
            self.__editAutoCompleteFromDoc)
        self.editActions.append(self.autoCompleteFromDocAct)
        
        self.autoCompleteFromAPIsAct = E5Action(
            QCoreApplication.translate('ViewManager',
                                       'Complete from APIs'),
            QCoreApplication.translate('ViewManager',
                                       'Complete from APIs'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+Alt+Space",
                "Edit|Complete from APIs")),
            0,
            self.editActGrp, 'vm_edit_autocomplete_from_api')
        self.autoCompleteFromAPIsAct.setStatusTip(QCoreApplication.translate(
            'ViewManager',
            'Complete current word from APIs'))
        self.autoCompleteFromAPIsAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Complete from APIs</b>"""
            """<p>Performs a completion from APIs of the word"""
            """ containing the cursor.</p>"""
        ))
        self.autoCompleteFromAPIsAct.triggered.connect(
            self.__editAutoCompleteFromAPIs)
        self.editActions.append(self.autoCompleteFromAPIsAct)
        
        self.autoCompleteFromAllAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Complete from Document and APIs'),
            QCoreApplication.translate(
                'ViewManager', 'Complete from Document and APIs'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Alt+Shift+Space",
                "Edit|Complete from Document and APIs")),
            0,
            self.editActGrp, 'vm_edit_autocomplete_from_all')
        self.autoCompleteFromAllAct.setStatusTip(QCoreApplication.translate(
            'ViewManager',
            'Complete current word from Document and APIs'))
        self.autoCompleteFromAllAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Complete from Document and APIs</b>"""
            """<p>Performs a completion from document and APIs"""
            """ of the word containing the cursor.</p>"""
        ))
        self.autoCompleteFromAllAct.triggered.connect(
            self.__editAutoCompleteFromAll)
        self.editActions.append(self.autoCompleteFromAllAct)
        
        self.calltipsAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Calltip'),
            QCoreApplication.translate('ViewManager', '&Calltip'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Meta+Alt+Space", "Edit|Calltip")),
            0,
            self.editActGrp, 'vm_edit_calltip')
        self.calltipsAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Show Calltips'))
        self.calltipsAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Calltip</b>"""
            """<p>Show calltips based on the characters immediately to the"""
            """ left of the cursor.</p>"""
        ))
        self.calltipsAct.triggered.connect(self.__editShowCallTips)
        self.editActions.append(self.calltipsAct)
        
        self.sortAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Sort'),
            QCoreApplication.translate('ViewManager', 'Sort'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+Alt+S", "Edit|Sort")),
            0,
            self.editActGrp, 'vm_edit_sort')
        self.sortAct.setStatusTip(QCoreApplication.translate(
            'ViewManager',
            'Sort the lines containing the rectangular selection'))
        self.sortAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Sort</b>"""
            """<p>Sort the lines spanned by a rectangular selection based on"""
            """ the selection ignoring leading and trailing whitespace.</p>"""
        ))
        self.sortAct.triggered.connect(self.__editSortSelectedLines)
        self.editActions.append(self.sortAct)
        
        self.editActGrp.setEnabled(False)
        self.copyActGrp.setEnabled(False)
        
        ####################################################################
        ## Below follow the actions for QScintilla standard commands.
        ####################################################################
        
        self.esm = QSignalMapper(self)
        self.esm.mapped[int].connect(self.__editorCommand)
        
        self.editorActGrp = createActionGroup(self.editActGrp)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager',
                                       'Move left one character'),
            QCoreApplication.translate('ViewManager',
                                       'Move left one character'),
            QKeySequence(QCoreApplication.translate('ViewManager', 'Left')), 0,
            self.editorActGrp, 'vm_edit_move_left_char')
        self.esm.setMapping(act, QsciScintilla.SCI_CHARLEFT)
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+B')))
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager',
                                       'Move right one character'),
            QCoreApplication.translate('ViewManager',
                                       'Move right one character'),
            QKeySequence(QCoreApplication.translate('ViewManager', 'Right')),
            0, self.editorActGrp, 'vm_edit_move_right_char')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+F')))
        self.esm.setMapping(act, QsciScintilla.SCI_CHARRIGHT)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Move up one line'),
            QCoreApplication.translate('ViewManager', 'Move up one line'),
            QKeySequence(QCoreApplication.translate('ViewManager', 'Up')), 0,
            self.editorActGrp, 'vm_edit_move_up_line')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+P')))
        self.esm.setMapping(act, QsciScintilla.SCI_LINEUP)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Move down one line'),
            QCoreApplication.translate('ViewManager', 'Move down one line'),
            QKeySequence(QCoreApplication.translate('ViewManager', 'Down')), 0,
            self.editorActGrp, 'vm_edit_move_down_line')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+N')))
        self.esm.setMapping(act, QsciScintilla.SCI_LINEDOWN)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager',
                                       'Move left one word part'),
            QCoreApplication.translate('ViewManager',
                                       'Move left one word part'),
            0, 0,
            self.editorActGrp, 'vm_edit_move_left_word_part')
        if not isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Alt+Left')))
        self.esm.setMapping(act, QsciScintilla.SCI_WORDPARTLEFT)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager',
                                       'Move right one word part'),
            QCoreApplication.translate('ViewManager',
                                       'Move right one word part'),
            0, 0,
            self.editorActGrp, 'vm_edit_move_right_word_part')
        if not isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Alt+Right')))
        self.esm.setMapping(act, QsciScintilla.SCI_WORDPARTRIGHT)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Move left one word'),
            QCoreApplication.translate('ViewManager', 'Move left one word'),
            0, 0,
            self.editorActGrp, 'vm_edit_move_left_word')
        if isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Alt+Left')))
        else:
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+Left')))
        self.esm.setMapping(act, QsciScintilla.SCI_WORDLEFT)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Move right one word'),
            QCoreApplication.translate('ViewManager', 'Move right one word'),
            0, 0,
            self.editorActGrp, 'vm_edit_move_right_word')
        if not isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+Right')))
        self.esm.setMapping(act, QsciScintilla.SCI_WORDRIGHT)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager',
                'Move to first visible character in document line'),
            QCoreApplication.translate(
                'ViewManager',
                'Move to first visible character in document line'),
            0, 0,
            self.editorActGrp, 'vm_edit_move_first_visible_char')
        if not isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Home')))
        self.esm.setMapping(act, QsciScintilla.SCI_VCHOME)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Move to start of display line'),
            QCoreApplication.translate(
                'ViewManager', 'Move to start of display line'),
            0, 0,
            self.editorActGrp, 'vm_edit_move_start_line')
        if isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+Left')))
        else:
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Alt+Home')))
        self.esm.setMapping(act, QsciScintilla.SCI_HOMEDISPLAY)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Move to end of document line'),
            QCoreApplication.translate(
                'ViewManager', 'Move to end of document line'),
            0, 0,
            self.editorActGrp, 'vm_edit_move_end_line')
        if isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+E')))
        else:
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'End')))
        self.esm.setMapping(act, QsciScintilla.SCI_LINEEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager',
                                       'Scroll view down one line'),
            QCoreApplication.translate('ViewManager',
                                       'Scroll view down one line'),
            QKeySequence(QCoreApplication.translate('ViewManager',
                                                    'Ctrl+Down')),
            0, self.editorActGrp, 'vm_edit_scroll_down_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINESCROLLDOWN)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager',
                                       'Scroll view up one line'),
            QCoreApplication.translate('ViewManager',
                                       'Scroll view up one line'),
            QKeySequence(QCoreApplication.translate('ViewManager', 'Ctrl+Up')),
            0, self.editorActGrp, 'vm_edit_scroll_up_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINESCROLLUP)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Move up one paragraph'),
            QCoreApplication.translate('ViewManager', 'Move up one paragraph'),
            QKeySequence(QCoreApplication.translate('ViewManager', 'Alt+Up')),
            0, self.editorActGrp, 'vm_edit_move_up_para')
        self.esm.setMapping(act, QsciScintilla.SCI_PARAUP)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager',
                                       'Move down one paragraph'),
            QCoreApplication.translate('ViewManager',
                                       'Move down one paragraph'),
            QKeySequence(QCoreApplication.translate('ViewManager',
                                                    'Alt+Down')),
            0, self.editorActGrp, 'vm_edit_move_down_para')
        self.esm.setMapping(act, QsciScintilla.SCI_PARADOWN)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Move up one page'),
            QCoreApplication.translate('ViewManager', 'Move up one page'),
            QKeySequence(QCoreApplication.translate('ViewManager', 'PgUp')), 0,
            self.editorActGrp, 'vm_edit_move_up_page')
        self.esm.setMapping(act, QsciScintilla.SCI_PAGEUP)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Move down one page'),
            QCoreApplication.translate('ViewManager', 'Move down one page'),
            QKeySequence(QCoreApplication.translate('ViewManager', 'PgDown')),
            0, self.editorActGrp, 'vm_edit_move_down_page')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+V')))
        self.esm.setMapping(act, QsciScintilla.SCI_PAGEDOWN)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager',
                                       'Move to start of document'),
            QCoreApplication.translate('ViewManager',
                                       'Move to start of document'),
            0, 0,
            self.editorActGrp, 'vm_edit_move_start_text')
        if isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+Up')))
        else:
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+Home')))
        self.esm.setMapping(act, QsciScintilla.SCI_DOCUMENTSTART)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager',
                                       'Move to end of document'),
            QCoreApplication.translate('ViewManager',
                                       'Move to end of document'),
            0, 0,
            self.editorActGrp, 'vm_edit_move_end_text')
        if isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+Down')))
        else:
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+End')))
        self.esm.setMapping(act, QsciScintilla.SCI_DOCUMENTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Indent one level'),
            QCoreApplication.translate('ViewManager', 'Indent one level'),
            QKeySequence(QCoreApplication.translate('ViewManager', 'Tab')), 0,
            self.editorActGrp, 'vm_edit_indent_one_level')
        self.esm.setMapping(act, QsciScintilla.SCI_TAB)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Unindent one level'),
            QCoreApplication.translate('ViewManager', 'Unindent one level'),
            QKeySequence(QCoreApplication.translate('ViewManager',
                                                    'Shift+Tab')),
            0, self.editorActGrp, 'vm_edit_unindent_one_level')
        self.esm.setMapping(act, QsciScintilla.SCI_BACKTAB)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection left one character'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection left one character'),
            QKeySequence(QCoreApplication.translate('ViewManager',
                                                    'Shift+Left')),
            0, self.editorActGrp, 'vm_edit_extend_selection_left_char')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+Shift+B')))
        self.esm.setMapping(act, QsciScintilla.SCI_CHARLEFTEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection right one character'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection right one character'),
            QKeySequence(QCoreApplication.translate('ViewManager',
                                                    'Shift+Right')),
            0, self.editorActGrp, 'vm_edit_extend_selection_right_char')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+Shift+F')))
        self.esm.setMapping(act, QsciScintilla.SCI_CHARRIGHTEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection up one line'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection up one line'),
            QKeySequence(QCoreApplication.translate('ViewManager',
                                                    'Shift+Up')),
            0, self.editorActGrp, 'vm_edit_extend_selection_up_line')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+Shift+P')))
        self.esm.setMapping(act, QsciScintilla.SCI_LINEUPEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection down one line'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection down one line'),
            QKeySequence(QCoreApplication.translate('ViewManager',
                                                    'Shift+Down')),
            0, self.editorActGrp, 'vm_edit_extend_selection_down_line')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+Shift+N')))
        self.esm.setMapping(act, QsciScintilla.SCI_LINEDOWNEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection left one word part'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection left one word part'),
            0, 0,
            self.editorActGrp, 'vm_edit_extend_selection_left_word_part')
        if not isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Alt+Shift+Left')))
        self.esm.setMapping(act, QsciScintilla.SCI_WORDPARTLEFTEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection right one word part'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection right one word part'),
            0, 0,
            self.editorActGrp, 'vm_edit_extend_selection_right_word_part')
        if not isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Alt+Shift+Right')))
        self.esm.setMapping(act, QsciScintilla.SCI_WORDPARTRIGHTEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection left one word'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection left one word'),
            0, 0,
            self.editorActGrp, 'vm_edit_extend_selection_left_word')
        if isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Alt+Shift+Left')))
        else:
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+Shift+Left')))
        self.esm.setMapping(act, QsciScintilla.SCI_WORDLEFTEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection right one word'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection right one word'),
            0, 0,
            self.editorActGrp, 'vm_edit_extend_selection_right_word')
        if isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Alt+Shift+Right')))
        else:
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+Shift+Right')))
        self.esm.setMapping(act, QsciScintilla.SCI_WORDRIGHTEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager',
                'Extend selection to first visible character in document'
                ' line'),
            QCoreApplication.translate(
                'ViewManager',
                'Extend selection to first visible character in document'
                ' line'),
            0, 0,
            self.editorActGrp, 'vm_edit_extend_selection_first_visible_char')
        if not isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Shift+Home')))
        self.esm.setMapping(act, QsciScintilla.SCI_VCHOMEEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection to end of document line'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection to end of document line'),
            0, 0,
            self.editorActGrp, 'vm_edit_extend_selection_end_line')
        if isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+Shift+E')))
        else:
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Shift+End')))
        self.esm.setMapping(act, QsciScintilla.SCI_LINEENDEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection up one paragraph'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection up one paragraph'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', 'Alt+Shift+Up')),
            0,
            self.editorActGrp, 'vm_edit_extend_selection_up_para')
        self.esm.setMapping(act, QsciScintilla.SCI_PARAUPEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection down one paragraph'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection down one paragraph'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', 'Alt+Shift+Down')),
            0,
            self.editorActGrp, 'vm_edit_extend_selection_down_para')
        self.esm.setMapping(act, QsciScintilla.SCI_PARADOWNEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection up one page'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection up one page'),
            QKeySequence(QCoreApplication.translate('ViewManager',
                                                    'Shift+PgUp')),
            0, self.editorActGrp, 'vm_edit_extend_selection_up_page')
        self.esm.setMapping(act, QsciScintilla.SCI_PAGEUPEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection down one page'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection down one page'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', 'Shift+PgDown')),
            0,
            self.editorActGrp, 'vm_edit_extend_selection_down_page')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+Shift+V')))
        self.esm.setMapping(act, QsciScintilla.SCI_PAGEDOWNEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection to start of document'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection to start of document'),
            0, 0,
            self.editorActGrp, 'vm_edit_extend_selection_start_text')
        if isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+Shift+Up')))
        else:
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+Shift+Home')))
        self.esm.setMapping(act, QsciScintilla.SCI_DOCUMENTSTARTEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection to end of document'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection to end of document'),
            0, 0,
            self.editorActGrp, 'vm_edit_extend_selection_end_text')
        if isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+Shift+Down')))
        else:
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+Shift+End')))
        self.esm.setMapping(act, QsciScintilla.SCI_DOCUMENTENDEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager',
                                       'Delete previous character'),
            QCoreApplication.translate('ViewManager',
                                       'Delete previous character'),
            QKeySequence(QCoreApplication.translate('ViewManager',
                                                    'Backspace')),
            0, self.editorActGrp, 'vm_edit_delete_previous_char')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+H')))
        else:
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Shift+Backspace')))
        self.esm.setMapping(act, QsciScintilla.SCI_DELETEBACK)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager',
                'Delete previous character if not at start of line'),
            QCoreApplication.translate(
                'ViewManager',
                'Delete previous character if not at start of line'),
            0, 0,
            self.editorActGrp, 'vm_edit_delet_previous_char_not_line_start')
        self.esm.setMapping(act, QsciScintilla.SCI_DELETEBACKNOTLINE)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager',
                                       'Delete current character'),
            QCoreApplication.translate('ViewManager',
                                       'Delete current character'),
            QKeySequence(QCoreApplication.translate('ViewManager', 'Del')),
            0, self.editorActGrp, 'vm_edit_delete_current_char')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+D')))
        self.esm.setMapping(act, QsciScintilla.SCI_CLEAR)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Delete word to left'),
            QCoreApplication.translate('ViewManager', 'Delete word to left'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', 'Ctrl+Backspace')),
            0,
            self.editorActGrp, 'vm_edit_delete_word_left')
        self.esm.setMapping(act, QsciScintilla.SCI_DELWORDLEFT)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Delete word to right'),
            QCoreApplication.translate('ViewManager', 'Delete word to right'),
            QKeySequence(QCoreApplication.translate('ViewManager',
                                                    'Ctrl+Del')),
            0, self.editorActGrp, 'vm_edit_delete_word_right')
        self.esm.setMapping(act, QsciScintilla.SCI_DELWORDRIGHT)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Delete line to left'),
            QCoreApplication.translate('ViewManager', 'Delete line to left'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', 'Ctrl+Shift+Backspace')),
            0,
            self.editorActGrp, 'vm_edit_delete_line_left')
        self.esm.setMapping(act, QsciScintilla.SCI_DELLINELEFT)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Delete line to right'),
            QCoreApplication.translate('ViewManager', 'Delete line to right'),
            0, 0,
            self.editorActGrp, 'vm_edit_delete_line_right')
        if isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+K')))
        else:
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+Shift+Del')))
        self.esm.setMapping(act, QsciScintilla.SCI_DELLINERIGHT)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Insert new line'),
            QCoreApplication.translate('ViewManager', 'Insert new line'),
            QKeySequence(QCoreApplication.translate('ViewManager', 'Return')),
            QKeySequence(QCoreApplication.translate('ViewManager', 'Enter')),
            self.editorActGrp, 'vm_edit_insert_line')
        self.esm.setMapping(act, QsciScintilla.SCI_NEWLINE)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Insert new line below current line'),
            QCoreApplication.translate(
                'ViewManager', 'Insert new line below current line'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', 'Shift+Return')),
            QKeySequence(QCoreApplication.translate('ViewManager',
                                                    'Shift+Enter')),
            self.editorActGrp, 'vm_edit_insert_line_below')
        act.triggered.connect(self.__newLineBelow)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Delete current line'),
            QCoreApplication.translate('ViewManager', 'Delete current line'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', 'Ctrl+Shift+L')),
            0,
            self.editorActGrp, 'vm_edit_delete_current_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINEDELETE)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Duplicate current line'),
            QCoreApplication.translate(
                'ViewManager', 'Duplicate current line'),
            QKeySequence(QCoreApplication.translate('ViewManager', 'Ctrl+D')),
            0, self.editorActGrp, 'vm_edit_duplicate_current_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINEDUPLICATE)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Swap current and previous lines'),
            QCoreApplication.translate(
                'ViewManager', 'Swap current and previous lines'),
            QKeySequence(QCoreApplication.translate('ViewManager', 'Ctrl+T')),
            0, self.editorActGrp, 'vm_edit_swap_current_previous_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINETRANSPOSE)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Cut current line'),
            QCoreApplication.translate('ViewManager', 'Cut current line'),
            QKeySequence(QCoreApplication.translate('ViewManager',
                                                    'Alt+Shift+L')),
            0, self.editorActGrp, 'vm_edit_cut_current_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINECUT)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Copy current line'),
            QCoreApplication.translate('ViewManager', 'Copy current line'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', 'Ctrl+Shift+T')),
            0,
            self.editorActGrp, 'vm_edit_copy_current_line')
        self.esm.setMapping(act, QsciScintilla.SCI_LINECOPY)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Toggle insert/overtype'),
            QCoreApplication.translate(
                'ViewManager', 'Toggle insert/overtype'),
            QKeySequence(QCoreApplication.translate('ViewManager', 'Ins')),
            0, self.editorActGrp, 'vm_edit_toggle_insert_overtype')
        self.esm.setMapping(act, QsciScintilla.SCI_EDITTOGGLEOVERTYPE)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Move to end of display line'),
            QCoreApplication.translate(
                'ViewManager', 'Move to end of display line'),
            0, 0,
            self.editorActGrp, 'vm_edit_move_end_displayed_line')
        if isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+Right')))
        else:
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Alt+End')))
        self.esm.setMapping(act, QsciScintilla.SCI_LINEENDDISPLAY)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend selection to end of display line'),
            QCoreApplication.translate(
                'ViewManager', 'Extend selection to end of display line'),
            0, 0,
            self.editorActGrp, 'vm_edit_extend_selection_end_displayed_line')
        if isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Ctrl+Shift+Right')))
        self.esm.setMapping(act, QsciScintilla.SCI_LINEENDDISPLAYEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Formfeed'),
            QCoreApplication.translate('ViewManager', 'Formfeed'),
            0, 0,
            self.editorActGrp, 'vm_edit_formfeed')
        self.esm.setMapping(act, QsciScintilla.SCI_FORMFEED)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate('ViewManager', 'Escape'),
            QCoreApplication.translate('ViewManager', 'Escape'),
            QKeySequence(QCoreApplication.translate('ViewManager', 'Esc')), 0,
            self.editorActGrp, 'vm_edit_escape')
        self.esm.setMapping(act, QsciScintilla.SCI_CANCEL)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend rectangular selection down one line'),
            QCoreApplication.translate(
                'ViewManager', 'Extend rectangular selection down one line'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', 'Alt+Ctrl+Down')),
            0,
            self.editorActGrp, 'vm_edit_extend_rect_selection_down_line')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+Alt+Shift+N')))
        self.esm.setMapping(act, QsciScintilla.SCI_LINEDOWNRECTEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Extend rectangular selection up one line'),
            QCoreApplication.translate(
                'ViewManager', 'Extend rectangular selection up one line'),
            QKeySequence(QCoreApplication.translate('ViewManager',
                                                    'Alt+Ctrl+Up')),
            0, self.editorActGrp, 'vm_edit_extend_rect_selection_up_line')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+Alt+Shift+P')))
        self.esm.setMapping(act, QsciScintilla.SCI_LINEUPRECTEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager',
                'Extend rectangular selection left one character'),
            QCoreApplication.translate(
                'ViewManager',
                'Extend rectangular selection left one character'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', 'Alt+Ctrl+Left')),
            0,
            self.editorActGrp, 'vm_edit_extend_rect_selection_left_char')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+Alt+Shift+B')))
        self.esm.setMapping(act, QsciScintilla.SCI_CHARLEFTRECTEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager',
                'Extend rectangular selection right one character'),
            QCoreApplication.translate(
                'ViewManager',
                'Extend rectangular selection right one character'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', 'Alt+Ctrl+Right')),
            0,
            self.editorActGrp, 'vm_edit_extend_rect_selection_right_char')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+Alt+Shift+F')))
        self.esm.setMapping(act, QsciScintilla.SCI_CHARRIGHTRECTEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager',
                'Extend rectangular selection to first visible character in'
                ' document line'),
            QCoreApplication.translate(
                'ViewManager',
                'Extend rectangular selection to first visible character in'
                ' document line'),
            0, 0,
            self.editorActGrp,
            'vm_edit_extend_rect_selection_first_visible_char')
        if not isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Alt+Shift+Home')))
        self.esm.setMapping(act, QsciScintilla.SCI_VCHOMERECTEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager',
                'Extend rectangular selection to end of document line'),
            QCoreApplication.translate(
                'ViewManager',
                'Extend rectangular selection to end of document line'),
            0, 0,
            self.editorActGrp, 'vm_edit_extend_rect_selection_end_line')
        if isMacPlatform():
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+Alt+Shift+E')))
        else:
            act.setShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Alt+Shift+End')))
        self.esm.setMapping(act, QsciScintilla.SCI_LINEENDRECTEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager',
                'Extend rectangular selection up one page'),
            QCoreApplication.translate(
                'ViewManager',
                'Extend rectangular selection up one page'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', 'Alt+Shift+PgUp')),
            0,
            self.editorActGrp, 'vm_edit_extend_rect_selection_up_page')
        self.esm.setMapping(act, QsciScintilla.SCI_PAGEUPRECTEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager',
                'Extend rectangular selection down one page'),
            QCoreApplication.translate(
                'ViewManager',
                'Extend rectangular selection down one page'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', 'Alt+Shift+PgDown')),
            0,
            self.editorActGrp, 'vm_edit_extend_rect_selection_down_page')
        if isMacPlatform():
            act.setAlternateShortcut(QKeySequence(
                QCoreApplication.translate('ViewManager', 'Meta+Alt+Shift+V')))
        self.esm.setMapping(act, QsciScintilla.SCI_PAGEDOWNRECTEXTEND)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        act = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Duplicate current selection'),
            QCoreApplication.translate(
                'ViewManager', 'Duplicate current selection'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', 'Ctrl+Shift+D')),
            0,
            self.editorActGrp, 'vm_edit_duplicate_current_selection')
        self.esm.setMapping(act, QsciScintilla.SCI_SELECTIONDUPLICATE)
        act.triggered.connect(self.esm.map)
        self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_SCROLLTOSTART"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager', 'Scroll to start of document'),
                QCoreApplication.translate(
                    'ViewManager', 'Scroll to start of document'),
                0, 0,
                self.editorActGrp, 'vm_edit_scroll_start_text')
            if isMacPlatform():
                act.setShortcut(QKeySequence(
                    QCoreApplication.translate('ViewManager', 'Home')))
            self.esm.setMapping(act, QsciScintilla.SCI_SCROLLTOSTART)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_SCROLLTOEND"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager', 'Scroll to end of document'),
                QCoreApplication.translate(
                    'ViewManager', 'Scroll to end of document'),
                0, 0,
                self.editorActGrp, 'vm_edit_scroll_end_text')
            if isMacPlatform():
                act.setShortcut(QKeySequence(
                    QCoreApplication.translate('ViewManager', 'End')))
            self.esm.setMapping(act, QsciScintilla.SCI_SCROLLTOEND)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_VERTICALCENTRECARET"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager', 'Scroll vertically to center current line'),
                QCoreApplication.translate(
                    'ViewManager', 'Scroll vertically to center current line'),
                0, 0,
                self.editorActGrp, 'vm_edit_scroll_vertically_center')
            if isMacPlatform():
                act.setShortcut(QKeySequence(
                    QCoreApplication.translate('ViewManager', 'Meta+L')))
            self.esm.setMapping(act, QsciScintilla.SCI_VERTICALCENTRECARET)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_WORDRIGHTEND"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager', 'Move to end of next word'),
                QCoreApplication.translate(
                    'ViewManager', 'Move to end of next word'),
                0, 0,
                self.editorActGrp, 'vm_edit_move_end_next_word')
            if isMacPlatform():
                act.setShortcut(QKeySequence(
                    QCoreApplication.translate('ViewManager', 'Alt+Right')))
            self.esm.setMapping(act, QsciScintilla.SCI_WORDRIGHTEND)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_WORDRIGHTENDEXTEND"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager', 'Extend selection to end of next word'),
                QCoreApplication.translate(
                    'ViewManager', 'Extend selection to end of next word'),
                0, 0,
                self.editorActGrp, 'vm_edit_select_end_next_word')
            if isMacPlatform():
                act.setShortcut(QKeySequence(
                    QCoreApplication.translate('ViewManager',
                                               'Alt+Shift+Right')))
            self.esm.setMapping(act, QsciScintilla.SCI_WORDRIGHTENDEXTEND)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_WORDLEFTEND"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager', 'Move to end of previous word'),
                QCoreApplication.translate(
                    'ViewManager', 'Move to end of previous word'),
                0, 0,
                self.editorActGrp, 'vm_edit_move_end_previous_word')
            self.esm.setMapping(act, QsciScintilla.SCI_WORDLEFTEND)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_WORDLEFTENDEXTEND"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager', 'Extend selection to end of previous word'),
                QCoreApplication.translate(
                    'ViewManager', 'Extend selection to end of previous word'),
                0, 0,
                self.editorActGrp, 'vm_edit_select_end_previous_word')
            self.esm.setMapping(act, QsciScintilla.SCI_WORDLEFTENDEXTEND)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_HOME"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager', 'Move to start of document line'),
                QCoreApplication.translate(
                    'ViewManager', 'Move to start of document line'),
                0, 0,
                self.editorActGrp, 'vm_edit_move_start_document_line')
            if isMacPlatform():
                act.setShortcut(QKeySequence(
                    QCoreApplication.translate('ViewManager', 'Meta+A')))
            self.esm.setMapping(act, QsciScintilla.SCI_HOME)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_HOMEEXTEND"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager',
                    'Extend selection to start of document line'),
                QCoreApplication.translate(
                    'ViewManager',
                    'Extend selection to start of document line'),
                0, 0,
                self.editorActGrp,
                'vm_edit_extend_selection_start_document_line')
            if isMacPlatform():
                act.setShortcut(QKeySequence(
                    QCoreApplication.translate('ViewManager', 'Meta+Shift+A')))
            self.esm.setMapping(act, QsciScintilla.SCI_HOMEEXTEND)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_HOMERECTEXTEND"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager',
                    'Extend rectangular selection to start of document line'),
                QCoreApplication.translate(
                    'ViewManager',
                    'Extend rectangular selection to start of document line'),
                0, 0,
                self.editorActGrp, 'vm_edit_select_rect_start_line')
            if isMacPlatform():
                act.setShortcut(QKeySequence(
                    QCoreApplication.translate('ViewManager',
                                               'Meta+Alt+Shift+A')))
            self.esm.setMapping(act, QsciScintilla.SCI_HOMERECTEXTEND)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_HOMEDISPLAYEXTEND"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager',
                    'Extend selection to start of display line'),
                QCoreApplication.translate(
                    'ViewManager',
                    'Extend selection to start of display line'),
                0, 0,
                self.editorActGrp,
                'vm_edit_extend_selection_start_display_line')
            if isMacPlatform():
                act.setShortcut(QKeySequence(
                    QCoreApplication.translate('ViewManager',
                                               'Ctrl+Shift+Left')))
            self.esm.setMapping(act, QsciScintilla.SCI_HOMEDISPLAYEXTEND)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_HOMEWRAP"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager',
                    'Move to start of display or document line'),
                QCoreApplication.translate(
                    'ViewManager',
                    'Move to start of display or document line'),
                0, 0,
                self.editorActGrp, 'vm_edit_move_start_display_document_line')
            self.esm.setMapping(act, QsciScintilla.SCI_HOMEWRAP)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_HOMEWRAPEXTEND"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager',
                    'Extend selection to start of display or document line'),
                QCoreApplication.translate(
                    'ViewManager',
                    'Extend selection to start of display or document line'),
                0, 0,
                self.editorActGrp,
                'vm_edit_extend_selection_start_display_document_line')
            self.esm.setMapping(act, QsciScintilla.SCI_HOMEWRAPEXTEND)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_VCHOMEWRAP"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager',
                    'Move to first visible character in display or document'
                    ' line'),
                QCoreApplication.translate(
                    'ViewManager',
                    'Move to first visible character in display or document'
                    ' line'),
                0, 0,
                self.editorActGrp,
                'vm_edit_move_first_visible_char_document_line')
            self.esm.setMapping(act, QsciScintilla.SCI_VCHOMEWRAP)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_VCHOMEWRAPEXTEND"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager',
                    'Extend selection to first visible character in'
                    ' display or document line'),
                QCoreApplication.translate(
                    'ViewManager',
                    'Extend selection to first visible character in'
                    ' display or document line'),
                0, 0,
                self.editorActGrp,
                'vm_edit_extend_selection_first_visible_char_document_line')
            self.esm.setMapping(act, QsciScintilla.SCI_VCHOMEWRAPEXTEND)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_LINEENDWRAP"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager',
                    'Move to end of display or document line'),
                QCoreApplication.translate(
                    'ViewManager',
                    'Move to end of display or document line'),
                0, 0,
                self.editorActGrp, 'vm_edit_end_start_display_document_line')
            self.esm.setMapping(act, QsciScintilla.SCI_LINEENDWRAP)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_LINEENDWRAPEXTEND"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager',
                    'Extend selection to end of display or document line'),
                QCoreApplication.translate(
                    'ViewManager',
                    'Extend selection to end of display or document line'),
                0, 0,
                self.editorActGrp,
                'vm_edit_extend_selection_end_display_document_line')
            self.esm.setMapping(act, QsciScintilla.SCI_LINEENDWRAPEXTEND)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_STUTTEREDPAGEUP"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager', 'Stuttered move up one page'),
                QCoreApplication.translate(
                    'ViewManager', 'Stuttered move up one page'),
                0, 0,
                self.editorActGrp, 'vm_edit_stuttered_move_up_page')
            self.esm.setMapping(act, QsciScintilla.SCI_STUTTEREDPAGEUP)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_STUTTEREDPAGEUPEXTEND"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager', 'Stuttered extend selection up one page'),
                QCoreApplication.translate(
                    'ViewManager', 'Stuttered extend selection up one page'),
                0, 0,
                self.editorActGrp,
                'vm_edit_stuttered_extend_selection_up_page')
            self.esm.setMapping(act, QsciScintilla.SCI_STUTTEREDPAGEUPEXTEND)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_STUTTEREDPAGEDOWN"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager', 'Stuttered move down one page'),
                QCoreApplication.translate(
                    'ViewManager', 'Stuttered move down one page'),
                0, 0,
                self.editorActGrp, 'vm_edit_stuttered_move_down_page')
            self.esm.setMapping(act, QsciScintilla.SCI_STUTTEREDPAGEDOWN)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_STUTTEREDPAGEDOWNEXTEND"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager', 'Stuttered extend selection down one page'),
                QCoreApplication.translate(
                    'ViewManager', 'Stuttered extend selection down one page'),
                0, 0,
                self.editorActGrp,
                'vm_edit_stuttered_extend_selection_down_page')
            self.esm.setMapping(act, QsciScintilla.SCI_STUTTEREDPAGEDOWNEXTEND)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_DELWORDRIGHTEND"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager', 'Delete right to end of next word'),
                QCoreApplication.translate(
                    'ViewManager', 'Delete right to end of next word'),
                0, 0,
                self.editorActGrp, 'vm_edit_delete_right_end_next_word')
            if isMacPlatform():
                act.setShortcut(QKeySequence(
                    QCoreApplication.translate('ViewManager', 'Alt+Del')))
            self.esm.setMapping(act, QsciScintilla.SCI_DELWORDRIGHTEND)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_MOVESELECTEDLINESUP"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager', 'Move selected lines up one line'),
                QCoreApplication.translate(
                    'ViewManager', 'Move selected lines up one line'),
                0, 0,
                self.editorActGrp, 'vm_edit_move_selection_up_one_line')
            self.esm.setMapping(act, QsciScintilla.SCI_MOVESELECTEDLINESUP)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        if hasattr(QsciScintilla, "SCI_MOVESELECTEDLINESDOWN"):
            act = E5Action(
                QCoreApplication.translate(
                    'ViewManager', 'Move selected lines down one line'),
                QCoreApplication.translate(
                    'ViewManager', 'Move selected lines down one line'),
                0, 0,
                self.editorActGrp, 'vm_edit_move_selection_down_one_line')
            self.esm.setMapping(act, QsciScintilla.SCI_MOVESELECTEDLINESDOWN)
            act.triggered.connect(self.esm.map)
            self.editActions.append(act)
        
        self.editorActGrp.setEnabled(False)
        
        self.editLowerCaseAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Convert selection to lower case'),
            QCoreApplication.translate(
                'ViewManager', 'Convert selection to lower case'),
            QKeySequence(QCoreApplication.translate('ViewManager',
                                                    'Alt+Shift+U')),
            0, self.editActGrp, 'vm_edit_convert_selection_lower')
        self.esm.setMapping(self.editLowerCaseAct, QsciScintilla.SCI_LOWERCASE)
        self.editLowerCaseAct.triggered.connect(self.esm.map)
        self.editActions.append(self.editLowerCaseAct)
        
        self.editUpperCaseAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Convert selection to upper case'),
            QCoreApplication.translate(
                'ViewManager', 'Convert selection to upper case'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', 'Ctrl+Shift+U')),
            0,
            self.editActGrp, 'vm_edit_convert_selection_upper')
        self.esm.setMapping(self.editUpperCaseAct, QsciScintilla.SCI_UPPERCASE)
        self.editUpperCaseAct.triggered.connect(self.esm.map)
        self.editActions.append(self.editUpperCaseAct)
    
    def initEditMenu(self):
        """
        Public method to create the Edit menu.
        
        @return the generated menu
        """
        autocompletionMenu = QMenu(
            QCoreApplication.translate('ViewManager', 'Complete'),
            self.ui)
        autocompletionMenu.setTearOffEnabled(True)
        autocompletionMenu.addAction(self.autoCompleteAct)
        autocompletionMenu.addAction(self.autoCompleteFromDocAct)
        autocompletionMenu.addAction(self.autoCompleteFromAPIsAct)
        autocompletionMenu.addAction(self.autoCompleteFromAllAct)
        
        searchMenu = QMenu(
            QCoreApplication.translate('ViewManager', '&Search'),
            self.ui)
        searchMenu.setTearOffEnabled(True)
        searchMenu.addAction(self.quickSearchAct)
        searchMenu.addAction(self.quickSearchBackAct)
        searchMenu.addAction(self.searchAct)
        searchMenu.addAction(self.searchNextAct)
        searchMenu.addAction(self.searchPrevAct)
        searchMenu.addAction(self.searchNextWordAct)
        searchMenu.addAction(self.searchPrevWordAct)
        searchMenu.addAction(self.replaceAct)
        searchMenu.addSeparator()
        searchMenu.addAction(self.searchClearMarkersAct)
        searchMenu.addSeparator()
        searchMenu.addAction(self.searchFilesAct)
        searchMenu.addAction(self.replaceFilesAct)
        searchMenu.addSeparator()
        searchMenu.addAction(self.searchOpenFilesAct)
        searchMenu.addAction(self.replaceOpenFilesAct)
        
        menu = QMenu(QCoreApplication.translate('ViewManager', '&Edit'),
                     self.ui)
        menu.setTearOffEnabled(True)
        menu.addAction(self.undoAct)
        menu.addAction(self.redoAct)
        menu.addAction(self.revertAct)
        menu.addSeparator()
        menu.addAction(self.cutAct)
        menu.addAction(self.copyAct)
        menu.addAction(self.pasteAct)
        menu.addAction(self.deleteAct)
        menu.addSeparator()
        menu.addAction(self.indentAct)
        menu.addAction(self.unindentAct)
        menu.addAction(self.smartIndentAct)
        menu.addSeparator()
        menu.addAction(self.commentAct)
        menu.addAction(self.uncommentAct)
        menu.addAction(self.toggleCommentAct)
        menu.addAction(self.streamCommentAct)
        menu.addAction(self.boxCommentAct)
        menu.addSeparator()
        menu.addAction(self.editUpperCaseAct)
        menu.addAction(self.editLowerCaseAct)
        menu.addAction(self.sortAct)
        menu.addSeparator()
        menu.addMenu(autocompletionMenu)
        menu.addAction(self.calltipsAct)
        menu.addSeparator()
        menu.addMenu(searchMenu)
        menu.addSeparator()
        menu.addAction(self.gotoAct)
        menu.addAction(self.gotoBraceAct)
        menu.addAction(self.gotoLastEditAct)
        menu.addAction(self.gotoPreviousDefAct)
        menu.addAction(self.gotoNextDefAct)
        menu.addSeparator()
        menu.addAction(self.selectBraceAct)
        menu.addAction(self.selectAllAct)
        menu.addAction(self.deselectAllAct)
        menu.addSeparator()
        menu.addAction(self.shortenEmptyAct)
        menu.addAction(self.convertEOLAct)
        
        return menu
        
    def initEditToolbar(self, toolbarManager):
        """
        Public method to create the Edit toolbar.
        
        @param toolbarManager reference to a toolbar manager object
            (E5ToolBarManager)
        @return the generated toolbar
        """
        tb = QToolBar(QCoreApplication.translate('ViewManager', 'Edit'),
                      self.ui)
        tb.setIconSize(UI.Config.ToolBarIconSize)
        tb.setObjectName("EditToolbar")
        tb.setToolTip(QCoreApplication.translate('ViewManager', 'Edit'))
        
        tb.addAction(self.undoAct)
        tb.addAction(self.redoAct)
        tb.addSeparator()
        tb.addAction(self.cutAct)
        tb.addAction(self.copyAct)
        tb.addAction(self.pasteAct)
        tb.addAction(self.deleteAct)
        tb.addSeparator()
        tb.addAction(self.commentAct)
        tb.addAction(self.uncommentAct)
        tb.addAction(self.toggleCommentAct)
        
        toolbarManager.addToolBar(tb, tb.windowTitle())
        toolbarManager.addAction(self.smartIndentAct, tb.windowTitle())
        toolbarManager.addAction(self.indentAct, tb.windowTitle())
        toolbarManager.addAction(self.unindentAct, tb.windowTitle())
        
        return tb
        
    ##################################################################
    ## Initialize the search related actions and the search toolbar
    ##################################################################
    
    def __initSearchActions(self):
        """
        Private method defining the user interface actions for the search
        commands.
        """
        self.searchActGrp = createActionGroup(self)
        
        self.searchAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Search'),
            UI.PixmapCache.getIcon("find.png"),
            QCoreApplication.translate('ViewManager', '&Search...'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+F", "Search|Search")),
            0,
            self.searchActGrp, 'vm_search')
        self.searchAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Search for a text'))
        self.searchAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Search</b>"""
            """<p>Search for some text in the current editor. A"""
            """ dialog is shown to enter the searchtext and options"""
            """ for the search.</p>"""
        ))
        self.searchAct.triggered.connect(self.__search)
        self.searchActions.append(self.searchAct)
        
        self.searchNextAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Search next'),
            UI.PixmapCache.getIcon("findNext.png"),
            QCoreApplication.translate('ViewManager', 'Search &next'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "F3", "Search|Search next")),
            0,
            self.searchActGrp, 'vm_search_next')
        self.searchNextAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Search next occurrence of text'))
        self.searchNextAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Search next</b>"""
            """<p>Search the next occurrence of some text in the current"""
            """ editor. The previously entered searchtext and options are"""
            """ reused.</p>"""
        ))
        self.searchNextAct.triggered.connect(self.__searchWidget.findNext)
        self.searchActions.append(self.searchNextAct)
        
        self.searchPrevAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Search previous'),
            UI.PixmapCache.getIcon("findPrev.png"),
            QCoreApplication.translate('ViewManager', 'Search &previous'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Shift+F3", "Search|Search previous")),
            0,
            self.searchActGrp, 'vm_search_previous')
        self.searchPrevAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Search previous occurrence of text'))
        self.searchPrevAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Search previous</b>"""
            """<p>Search the previous occurrence of some text in the current"""
            """ editor. The previously entered searchtext and options are"""
            """ reused.</p>"""
        ))
        self.searchPrevAct.triggered.connect(self.__searchWidget.findPrev)
        self.searchActions.append(self.searchPrevAct)
        
        self.searchClearMarkersAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Clear search markers'),
            UI.PixmapCache.getIcon("findClear.png"),
            QCoreApplication.translate('ViewManager', 'Clear search markers'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+3", "Search|Clear search markers")),
            0,
            self.searchActGrp, 'vm_clear_search_markers')
        self.searchClearMarkersAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Clear all displayed search markers'))
        self.searchClearMarkersAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Clear search markers</b>"""
            """<p>Clear all displayed search markers.</p>"""
        ))
        self.searchClearMarkersAct.triggered.connect(
            self.__searchClearMarkers)
        self.searchActions.append(self.searchClearMarkersAct)
        
        self.searchNextWordAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Search current word forward'),
            UI.PixmapCache.getIcon("findWordNext.png"),
            QCoreApplication.translate(
                'ViewManager', 'Search current word forward'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager',
                "Ctrl+.", "Search|Search current word forward")),
            0,
            self.searchActGrp, 'vm_search_word_next')
        self.searchNextWordAct.setStatusTip(QCoreApplication.translate(
            'ViewManager',
            'Search next occurrence of the current word'))
        self.searchNextWordAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Search current word forward</b>"""
            """<p>Search the next occurrence of the current word of the"""
            """ current editor.</p>"""
        ))
        self.searchNextWordAct.triggered.connect(self.__findNextWord)
        self.searchActions.append(self.searchNextWordAct)
        
        self.searchPrevWordAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Search current word backward'),
            UI.PixmapCache.getIcon("findWordPrev.png"),
            QCoreApplication.translate(
                'ViewManager', 'Search current word backward'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager',
                "Ctrl+,", "Search|Search current word backward")),
            0,
            self.searchActGrp, 'vm_search_word_previous')
        self.searchPrevWordAct.setStatusTip(QCoreApplication.translate(
            'ViewManager',
            'Search previous occurrence of the current word'))
        self.searchPrevWordAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Search current word backward</b>"""
            """<p>Search the previous occurrence of the current word of the"""
            """ current editor.</p>"""
        ))
        self.searchPrevWordAct.triggered.connect(self.__findPrevWord)
        self.searchActions.append(self.searchPrevWordAct)
        
        self.replaceAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Replace'),
            QCoreApplication.translate('ViewManager', '&Replace...'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+R", "Search|Replace")),
            0,
            self.searchActGrp, 'vm_search_replace')
        self.replaceAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Replace some text'))
        self.replaceAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Replace</b>"""
            """<p>Search for some text in the current editor and replace it."""
            """ A dialog is shown to enter the searchtext, the replacement"""
            """ text and options for the search and replace.</p>"""
        ))
        self.replaceAct.triggered.connect(self.__replace)
        self.searchActions.append(self.replaceAct)
        
        self.quickSearchAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Quicksearch'),
            UI.PixmapCache.getIcon("quickFindNext.png"),
            QCoreApplication.translate('ViewManager', '&Quicksearch'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+Shift+K", "Search|Quicksearch")),
            0,
            self.searchActGrp, 'vm_quicksearch')
        self.quickSearchAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Perform a quicksearch'))
        self.quickSearchAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Quicksearch</b>"""
            """<p>This activates the quicksearch function of the IDE by"""
            """ giving focus to the quicksearch entry field. If this field"""
            """ is already active and contains text, it searches for the"""
            """ next occurrence of this text.</p>"""
        ))
        self.quickSearchAct.triggered.connect(self.__quickSearch)
        self.searchActions.append(self.quickSearchAct)
        
        self.quickSearchBackAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Quicksearch backwards'),
            UI.PixmapCache.getIcon("quickFindPrev.png"),
            QCoreApplication.translate(
                'ViewManager', 'Quicksearch &backwards'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager',
                "Ctrl+Shift+J", "Search|Quicksearch backwards")),
            0, self.searchActGrp, 'vm_quicksearch_backwards')
        self.quickSearchBackAct.setStatusTip(QCoreApplication.translate(
            'ViewManager',
            'Perform a quicksearch backwards'))
        self.quickSearchBackAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Quicksearch backwards</b>"""
            """<p>This searches the previous occurrence of the quicksearch"""
            """ text.</p>"""
        ))
        self.quickSearchBackAct.triggered.connect(self.__quickSearchPrev)
        self.searchActions.append(self.quickSearchBackAct)
        
        self.quickSearchExtendAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Quicksearch extend'),
            UI.PixmapCache.getIcon("quickFindExtend.png"),
            QCoreApplication.translate('ViewManager', 'Quicksearch e&xtend'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+Shift+H", "Search|Quicksearch extend")),
            0,
            self.searchActGrp, 'vm_quicksearch_extend')
        self.quickSearchExtendAct.setStatusTip(QCoreApplication.translate(
            'ViewManager',
            'Extend the quicksearch to the end of the current word'))
        self.quickSearchExtendAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Quicksearch extend</b>"""
            """<p>This extends the quicksearch text to the end of the word"""
            """ currently found.</p>"""
        ))
        self.quickSearchExtendAct.triggered.connect(
            self.__quickSearchExtend)
        self.searchActions.append(self.quickSearchExtendAct)
        
        self.gotoAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Goto Line'),
            UI.PixmapCache.getIcon("goto.png"),
            QCoreApplication.translate('ViewManager', '&Goto Line...'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+G", "Search|Goto Line")),
            0,
            self.searchActGrp, 'vm_search_goto_line')
        self.gotoAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Goto Line'))
        self.gotoAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Goto Line</b>"""
            """<p>Go to a specific line of text in the current editor."""
            """ A dialog is shown to enter the linenumber.</p>"""
        ))
        self.gotoAct.triggered.connect(self.__goto)
        self.searchActions.append(self.gotoAct)
        
        self.gotoBraceAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Goto Brace'),
            UI.PixmapCache.getIcon("gotoBrace.png"),
            QCoreApplication.translate('ViewManager', 'Goto &Brace'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+L", "Search|Goto Brace")),
            0,
            self.searchActGrp, 'vm_search_goto_brace')
        self.gotoBraceAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Goto Brace'))
        self.gotoBraceAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Goto Brace</b>"""
            """<p>Go to the matching brace in the current editor.</p>"""
        ))
        self.gotoBraceAct.triggered.connect(self.__gotoBrace)
        self.searchActions.append(self.gotoBraceAct)
        
        self.gotoLastEditAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Goto Last Edit Location'),
            UI.PixmapCache.getIcon("gotoLastEditPosition.png"),
            QCoreApplication.translate(
                'ViewManager', 'Goto Last &Edit Location'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager',
                "Ctrl+Shift+G", "Search|Goto Last Edit Location")),
            0,
            self.searchActGrp, 'vm_search_goto_last_edit_location')
        self.gotoLastEditAct.setStatusTip(
            QCoreApplication.translate(
                'ViewManager', 'Goto Last Edit Location'))
        self.gotoLastEditAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Goto Last Edit Location</b>"""
            """<p>Go to the location of the last edit in the current"""
            """ editor.</p>"""
        ))
        self.gotoLastEditAct.triggered.connect(self.__gotoLastEditPosition)
        self.searchActions.append(self.gotoLastEditAct)
        
        self.gotoPreviousDefAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Goto Previous Method or Class'),
            QCoreApplication.translate(
                'ViewManager', 'Goto Previous Method or Class'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager',
                "Ctrl+Shift+Up", "Search|Goto Previous Method or Class")),
            0,
            self.searchActGrp, 'vm_search_goto_previous_method_or_class')
        self.gotoPreviousDefAct.setStatusTip(
            QCoreApplication.translate(
                'ViewManager',
                'Go to the previous method or class definition'))
        self.gotoPreviousDefAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Goto Previous Method or Class</b>"""
            """<p>Goes to the line of the previous method or class"""
            """ definition and highlights the name.</p>"""
        ))
        self.gotoPreviousDefAct.triggered.connect(
            self.__gotoPreviousMethodClass)
        self.searchActions.append(self.gotoPreviousDefAct)
        
        self.gotoNextDefAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Goto Next Method or Class'),
            QCoreApplication.translate(
                'ViewManager', 'Goto Next Method or Class'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager',
                "Ctrl+Shift+Down", "Search|Goto Next Method or Class")),
            0,
            self.searchActGrp, 'vm_search_goto_next_method_or_class')
        self.gotoNextDefAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Go to the next method or class definition'))
        self.gotoNextDefAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Goto Next Method or Class</b>"""
            """<p>Goes to the line of the next method or class definition"""
            """ and highlights the name.</p>"""
        ))
        self.gotoNextDefAct.triggered.connect(self.__gotoNextMethodClass)
        self.searchActions.append(self.gotoNextDefAct)
        
        self.searchActGrp.setEnabled(False)
        
        self.searchFilesAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Search in Files'),
            UI.PixmapCache.getIcon("projectFind.png"),
            QCoreApplication.translate('ViewManager', 'Search in &Files...'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Shift+Ctrl+F", "Search|Search Files")),
            0,
            self, 'vm_search_in_files')
        self.searchFilesAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Search for a text in files'))
        self.searchFilesAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Search in Files</b>"""
            """<p>Search for some text in the files of a directory tree"""
            """ or the project. A dialog is shown to enter the searchtext"""
            """ and options for the search and to display the result.</p>"""
        ))
        self.searchFilesAct.triggered.connect(self.__searchFiles)
        self.searchActions.append(self.searchFilesAct)
        
        self.replaceFilesAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Replace in Files'),
            QCoreApplication.translate('ViewManager', 'Replace in F&iles...'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Shift+Ctrl+R", "Search|Replace in Files")),
            0,
            self, 'vm_replace_in_files')
        self.replaceFilesAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Search for a text in files and replace it'))
        self.replaceFilesAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Replace in Files</b>"""
            """<p>Search for some text in the files of a directory tree"""
            """ or the project and replace it. A dialog is shown to enter"""
            """ the searchtext, the replacement text and options for the"""
            """ search and to display the result.</p>"""
        ))
        self.replaceFilesAct.triggered.connect(self.__replaceFiles)
        self.searchActions.append(self.replaceFilesAct)
        
        self.searchOpenFilesAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Search in Open Files'),
            UI.PixmapCache.getIcon("documentFind.png"),
            QCoreApplication.translate(
                'ViewManager', 'Search in Open Files...'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager',
                "Meta+Ctrl+Alt+F", "Search|Search Open Files")),
            0,
            self.searchActGrp, 'vm_search_in_open_files')
        self.searchOpenFilesAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Search for a text in open files'))
        self.searchOpenFilesAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Search in Open Files</b>"""
            """<p>Search for some text in the currently opened files."""
            """ A dialog is shown to enter the searchtext"""
            """ and options for the search and to display the result.</p>"""
        ))
        self.searchOpenFilesAct.triggered.connect(self.__searchOpenFiles)
        self.searchActions.append(self.searchOpenFilesAct)
        
        self.replaceOpenFilesAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Replace in Open Files'),
            QCoreApplication.translate(
                'ViewManager', 'Replace in Open Files...'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager',
                "Meta+Ctrl+Alt+R", "Search|Replace in Open Files")),
            0,
            self.searchActGrp, 'vm_replace_in_open_files')
        self.replaceOpenFilesAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Search for a text in open files and replace it'))
        self.replaceOpenFilesAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Replace in Open Files</b>"""
            """<p>Search for some text in the currently opened files"""
            """ and replace it. A dialog is shown to enter"""
            """ the searchtext, the replacement text and options for the"""
            """ search and to display the result.</p>"""
        ))
        self.replaceOpenFilesAct.triggered.connect(self.__replaceOpenFiles)
        self.searchActions.append(self.replaceOpenFilesAct)
        
    def initSearchToolbars(self, toolbarManager):
        """
        Public method to create the Search toolbars.
        
        @param toolbarManager reference to a toolbar manager object
            (E5ToolBarManager)
        @return a tuple of the generated toolbar (search, quicksearch)
        """
        qtb = QToolBar(QCoreApplication.translate(
            'ViewManager', 'Quicksearch'), self.ui)
        qtb.setIconSize(UI.Config.ToolBarIconSize)
        qtb.setObjectName("QuicksearchToolbar")
        qtb.setToolTip(QCoreApplication.translate(
            'ViewManager', 'Quicksearch'))
        
        self.quickFindLineEdit = QuickSearchLineEdit(self)
        self.quickFindtextCombo = QComboBox(self)
        self.quickFindtextCombo.setEditable(True)
        self.quickFindtextCombo.setLineEdit(self.quickFindLineEdit)
        self.quickFindtextCombo.setDuplicatesEnabled(False)
        self.quickFindtextCombo.setInsertPolicy(QComboBox.InsertAtTop)
        self.quickFindtextCombo.lastActive = None
        self.quickFindtextCombo.lastCursorPos = None
        self.quickFindtextCombo.lastSearchText = ""
        self.quickFindtextCombo._editor = self.quickFindtextCombo.lineEdit()
        # this allows us not to jump across searched text
        # just because of autocompletion enabled
        self.quickFindtextCombo.setMinimumWidth(250)
        self.quickFindtextCombo.setSizeAdjustPolicy(
            QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.quickFindtextCombo.addItem("")
        self.quickFindtextCombo.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<p>Enter the searchtext directly into this field."""
            """ The search will be performed case insensitive."""
            """ The quicksearch function is activated upon activation"""
            """ of the quicksearch next action (default key Ctrl+Shift+K),"""
            """ if this entry field does not have the input focus."""
            """ Otherwise it searches for the next occurrence of the"""
            """ text entered. The quicksearch backwards action"""
            """ (default key Ctrl+Shift+J) searches backward."""
            """ Activating the 'quicksearch extend' action"""
            """ (default key Ctrl+Shift+H) extends the current"""
            """ searchtext to the end of the currently found word."""
            """ The quicksearch can be ended by pressing the Return key"""
            """ while the quicksearch entry has the the input focus.</p>"""
        ))
        self.quickFindtextCombo._editor.returnPressed.connect(
            self.__quickSearchEnter)
        self.quickFindtextCombo._editor.textChanged.connect(
            self.__quickSearchText)
        self.quickFindtextCombo._editor.escPressed.connect(
            self.__quickSearchEscape)
        self.quickFindtextCombo._editor.gotFocus.connect(
            self.__quickSearchFocusIn)
        self.quickFindtextAction = QWidgetAction(self)
        self.quickFindtextAction.setDefaultWidget(self.quickFindtextCombo)
        self.quickFindtextAction.setObjectName("vm_quickfindtext_action")
        self.quickFindtextAction.setText(self.tr("Quicksearch Textedit"))
        qtb.addAction(self.quickFindtextAction)
        qtb.addAction(self.quickSearchAct)
        qtb.addAction(self.quickSearchBackAct)
        qtb.addAction(self.quickSearchExtendAct)
        self.quickFindtextCombo.setEnabled(False)
        self.__quickSearchToolbar = qtb
        self.__quickSearchToolbarVisibility = None
        
        tb = QToolBar(QCoreApplication.translate('ViewManager', 'Search'),
                      self.ui)
        tb.setIconSize(UI.Config.ToolBarIconSize)
        tb.setObjectName("SearchToolbar")
        tb.setToolTip(QCoreApplication.translate('ViewManager', 'Search'))
        
        tb.addAction(self.searchAct)
        tb.addAction(self.searchNextAct)
        tb.addAction(self.searchPrevAct)
        tb.addAction(self.searchNextWordAct)
        tb.addAction(self.searchPrevWordAct)
        tb.addSeparator()
        tb.addAction(self.searchClearMarkersAct)
        tb.addSeparator()
        tb.addAction(self.searchFilesAct)
        tb.addAction(self.searchOpenFilesAct)
        tb.addSeparator()
        tb.addAction(self.gotoLastEditAct)
        
        tb.setAllowedAreas(
            Qt.ToolBarAreas(Qt.TopToolBarArea | Qt.BottomToolBarArea))
        
        toolbarManager.addToolBar(qtb, qtb.windowTitle())
        toolbarManager.addToolBar(tb, tb.windowTitle())
        toolbarManager.addAction(self.gotoAct, tb.windowTitle())
        toolbarManager.addAction(self.gotoBraceAct, tb.windowTitle())
        
        return tb, qtb
    
    ##################################################################
    ## Initialize the view related actions, view menu and toolbar
    ##################################################################
    
    def __initViewActions(self):
        """
        Private method defining the user interface actions for the view
        commands.
        """
        self.viewActGrp = createActionGroup(self)
        self.viewFoldActGrp = createActionGroup(self)
        
        self.zoomInAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Zoom in'),
            UI.PixmapCache.getIcon("zoomIn.png"),
            QCoreApplication.translate('ViewManager', 'Zoom &in'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl++", "View|Zoom in")),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Zoom In", "View|Zoom in")),
            self.viewActGrp, 'vm_view_zoom_in')
        self.zoomInAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Zoom in on the text'))
        self.zoomInAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Zoom in</b>"""
            """<p>Zoom in on the text. This makes the text bigger.</p>"""
        ))
        self.zoomInAct.triggered.connect(self.__zoomIn)
        self.viewActions.append(self.zoomInAct)
        
        self.zoomOutAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Zoom out'),
            UI.PixmapCache.getIcon("zoomOut.png"),
            QCoreApplication.translate('ViewManager', 'Zoom &out'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+-", "View|Zoom out")),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Zoom Out", "View|Zoom out")),
            self.viewActGrp, 'vm_view_zoom_out')
        self.zoomOutAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Zoom out on the text'))
        self.zoomOutAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Zoom out</b>"""
            """<p>Zoom out on the text. This makes the text smaller.</p>"""
        ))
        self.zoomOutAct.triggered.connect(self.__zoomOut)
        self.viewActions.append(self.zoomOutAct)
        
        self.zoomResetAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Zoom reset'),
            UI.PixmapCache.getIcon("zoomReset.png"),
            QCoreApplication.translate('ViewManager', 'Zoom &reset'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+0", "View|Zoom reset")),
            0,
            self.viewActGrp, 'vm_view_zoom_reset')
        self.zoomResetAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Reset the zoom of the text'))
        self.zoomResetAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Zoom reset</b>"""
            """<p>Reset the zoom of the text. """
            """This sets the zoom factor to 100%.</p>"""
        ))
        self.zoomResetAct.triggered.connect(self.__zoomReset)
        self.viewActions.append(self.zoomResetAct)
        
        self.zoomToAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Zoom'),
            UI.PixmapCache.getIcon("zoomTo.png"),
            QCoreApplication.translate('ViewManager', '&Zoom'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+#", "View|Zoom")),
            0,
            self.viewActGrp, 'vm_view_zoom')
        self.zoomToAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Zoom the text'))
        self.zoomToAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Zoom</b>"""
            """<p>Zoom the text. This opens a dialog where the"""
            """ desired size can be entered.</p>"""
        ))
        self.zoomToAct.triggered.connect(self.__zoom)
        self.viewActions.append(self.zoomToAct)
        
        self.toggleAllAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Toggle all folds'),
            QCoreApplication.translate('ViewManager', 'Toggle &all folds'),
            0, 0, self.viewFoldActGrp, 'vm_view_toggle_all_folds')
        self.toggleAllAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Toggle all folds'))
        self.toggleAllAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Toggle all folds</b>"""
            """<p>Toggle all folds of the current editor.</p>"""
        ))
        self.toggleAllAct.triggered.connect(self.__toggleAll)
        self.viewActions.append(self.toggleAllAct)
        
        self.toggleAllChildrenAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Toggle all folds (including children)'),
            QCoreApplication.translate(
                'ViewManager', 'Toggle all &folds (including children)'),
            0, 0, self.viewFoldActGrp, 'vm_view_toggle_all_folds_children')
        self.toggleAllChildrenAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Toggle all folds (including children)'))
        self.toggleAllChildrenAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Toggle all folds (including children)</b>"""
            """<p>Toggle all folds of the current editor including"""
            """ all children.</p>"""
        ))
        self.toggleAllChildrenAct.triggered.connect(
            self.__toggleAllChildren)
        self.viewActions.append(self.toggleAllChildrenAct)
        
        self.toggleCurrentAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Toggle current fold'),
            QCoreApplication.translate('ViewManager', 'Toggle &current fold'),
            0, 0, self.viewFoldActGrp, 'vm_view_toggle_current_fold')
        self.toggleCurrentAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Toggle current fold'))
        self.toggleCurrentAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Toggle current fold</b>"""
            """<p>Toggle the folds of the current line of the current"""
            """ editor.</p>"""
        ))
        self.toggleCurrentAct.triggered.connect(self.__toggleCurrent)
        self.viewActions.append(self.toggleCurrentAct)
        
        self.unhighlightAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Remove all highlights'),
            UI.PixmapCache.getIcon("unhighlight.png"),
            QCoreApplication.translate('ViewManager', 'Remove all highlights'),
            0, 0,
            self, 'vm_view_unhighlight')
        self.unhighlightAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Remove all highlights'))
        self.unhighlightAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Remove all highlights</b>"""
            """<p>Remove the highlights of all editors.</p>"""
        ))
        self.unhighlightAct.triggered.connect(self.__unhighlight)
        self.viewActions.append(self.unhighlightAct)
        
        self.newDocumentViewAct = E5Action(
            QCoreApplication.translate('ViewManager', 'New Document View'),
            UI.PixmapCache.getIcon("documentNewView.png"),
            QCoreApplication.translate('ViewManager', 'New &Document View'),
            0, 0, self, 'vm_view_new_document_view')
        self.newDocumentViewAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Open a new view of the current document'))
        self.newDocumentViewAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>New Document View</b>"""
            """<p>Opens a new view of the current document. Both views show"""
            """ the same document. However, the cursors may be positioned"""
            """ independently.</p>"""
        ))
        self.newDocumentViewAct.triggered.connect(self.__newDocumentView)
        self.viewActions.append(self.newDocumentViewAct)
        
        self.newDocumentSplitViewAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'New Document View (with new split)'),
            UI.PixmapCache.getIcon("splitVertical.png"),
            QCoreApplication.translate(
                'ViewManager', 'New Document View (with new split)'),
            0, 0, self, 'vm_view_new_document_split_view')
        self.newDocumentSplitViewAct.setStatusTip(QCoreApplication.translate(
            'ViewManager',
            'Open a new view of the current document in a new split'))
        self.newDocumentSplitViewAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>New Document View</b>"""
            """<p>Opens a new view of the current document in a new split."""
            """ Both views show the same document. However, the cursors may"""
            """ be positioned independently.</p>"""
        ))
        self.newDocumentSplitViewAct.triggered.connect(
            self.__newDocumentSplitView)
        self.viewActions.append(self.newDocumentSplitViewAct)
        
        self.splitViewAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Split view'),
            UI.PixmapCache.getIcon("splitVertical.png"),
            QCoreApplication.translate('ViewManager', '&Split view'),
            0, 0, self, 'vm_view_split_view')
        self.splitViewAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Add a split to the view'))
        self.splitViewAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Split view</b>"""
            """<p>Add a split to the view.</p>"""
        ))
        self.splitViewAct.triggered.connect(self.__splitView)
        self.viewActions.append(self.splitViewAct)
        
        self.splitOrientationAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Arrange horizontally'),
            QCoreApplication.translate('ViewManager', 'Arrange &horizontally'),
            0, 0, self, 'vm_view_arrange_horizontally', True)
        self.splitOrientationAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Arrange the splitted views horizontally'))
        self.splitOrientationAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Arrange horizontally</b>"""
            """<p>Arrange the splitted views horizontally.</p>"""
        ))
        self.splitOrientationAct.setChecked(False)
        self.splitOrientationAct.toggled[bool].connect(self.__splitOrientation)
        self.viewActions.append(self.splitOrientationAct)
        
        self.splitRemoveAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Remove split'),
            UI.PixmapCache.getIcon("remsplitVertical.png"),
            QCoreApplication.translate('ViewManager', '&Remove split'),
            0, 0, self, 'vm_view_remove_split')
        self.splitRemoveAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Remove the current split'))
        self.splitRemoveAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Remove split</b>"""
            """<p>Remove the current split.</p>"""
        ))
        self.splitRemoveAct.triggered.connect(self.removeSplit)
        self.viewActions.append(self.splitRemoveAct)
        
        self.nextSplitAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Next split'),
            QCoreApplication.translate('ViewManager', '&Next split'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+Alt+N", "View|Next split")),
            0,
            self, 'vm_next_split')
        self.nextSplitAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Move to the next split'))
        self.nextSplitAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Next split</b>"""
            """<p>Move to the next split.</p>"""
        ))
        self.nextSplitAct.triggered.connect(self.nextSplit)
        self.viewActions.append(self.nextSplitAct)
        
        self.prevSplitAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Previous split'),
            QCoreApplication.translate('ViewManager', '&Previous split'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+Alt+P", "View|Previous split")),
            0, self, 'vm_previous_split')
        self.prevSplitAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Move to the previous split'))
        self.prevSplitAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Previous split</b>"""
            """<p>Move to the previous split.</p>"""
        ))
        self.prevSplitAct.triggered.connect(self.prevSplit)
        self.viewActions.append(self.prevSplitAct)
        
        self.previewAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Preview'),
            UI.PixmapCache.getIcon("previewer.png"),
            QCoreApplication.translate('ViewManager', 'Preview'),
            0, 0, self, 'vm_preview', True)
        self.previewAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Preview the current file in the web browser'))
        self.previewAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Preview</b>"""
            """<p>This opens the web browser with a preview of"""
            """ the current file.</p>"""
        ))
        self.previewAct.setChecked(Preferences.getUI("ShowFilePreview"))
        self.previewAct.toggled[bool].connect(self.__previewEditor)
        self.viewActions.append(self.previewAct)
        
        self.viewActGrp.setEnabled(False)
        self.viewFoldActGrp.setEnabled(False)
        self.unhighlightAct.setEnabled(False)
        self.splitViewAct.setEnabled(False)
        self.splitOrientationAct.setEnabled(False)
        self.splitRemoveAct.setEnabled(False)
        self.nextSplitAct.setEnabled(False)
        self.prevSplitAct.setEnabled(False)
        self.previewAct.setEnabled(True)
        
        self.splitOrientationAct.setChecked(
            Preferences.getUI("SplitOrientationVertical"))
        
    def initViewMenu(self):
        """
        Public method to create the View menu.
        
        @return the generated menu
        """
        menu = QMenu(QCoreApplication.translate('ViewManager', '&View'),
                     self.ui)
        menu.setTearOffEnabled(True)
        menu.addActions(self.viewActGrp.actions())
        menu.addSeparator()
        menu.addActions(self.viewFoldActGrp.actions())
        menu.addSeparator()
        menu.addAction(self.previewAct)
        menu.addSeparator()
        menu.addAction(self.unhighlightAct)
        menu.addSeparator()
        menu.addAction(self.newDocumentViewAct)
        if self.canSplit():
            menu.addAction(self.newDocumentSplitViewAct)
            menu.addSeparator()
            menu.addAction(self.splitViewAct)
            menu.addAction(self.splitOrientationAct)
            menu.addAction(self.splitRemoveAct)
            menu.addAction(self.nextSplitAct)
            menu.addAction(self.prevSplitAct)
        
        return menu
        
    def initViewToolbar(self, toolbarManager):
        """
        Public method to create the View toolbar.
        
        @param toolbarManager reference to a toolbar manager object
            (E5ToolBarManager)
        @return the generated toolbar
        """
        tb = QToolBar(QCoreApplication.translate('ViewManager', 'View'),
                      self.ui)
        tb.setIconSize(UI.Config.ToolBarIconSize)
        tb.setObjectName("ViewToolbar")
        tb.setToolTip(QCoreApplication.translate('ViewManager', 'View'))
        
        tb.addActions(self.viewActGrp.actions())
        tb.addSeparator()
        tb.addAction(self.previewAct)
        tb.addSeparator()
        tb.addAction(self.newDocumentViewAct)
        if self.canSplit():
            tb.addAction(self.newDocumentSplitViewAct)
        
        toolbarManager.addToolBar(tb, tb.windowTitle())
        toolbarManager.addAction(self.unhighlightAct, tb.windowTitle())
        toolbarManager.addAction(self.splitViewAct, tb.windowTitle())
        toolbarManager.addAction(self.splitRemoveAct, tb.windowTitle())
        
        return tb
    
    ##################################################################
    ## Initialize the macro related actions and macro menu
    ##################################################################
    
    def __initMacroActions(self):
        """
        Private method defining the user interface actions for the macro
        commands.
        """
        self.macroActGrp = createActionGroup(self)

        self.macroStartRecAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Start Macro Recording'),
            QCoreApplication.translate(
                'ViewManager', 'S&tart Macro Recording'),
            0, 0, self.macroActGrp, 'vm_macro_start_recording')
        self.macroStartRecAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Start Macro Recording'))
        self.macroStartRecAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Start Macro Recording</b>"""
            """<p>Start recording editor commands into a new macro.</p>"""
        ))
        self.macroStartRecAct.triggered.connect(self.__macroStartRecording)
        self.macroActions.append(self.macroStartRecAct)
        
        self.macroStopRecAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Stop Macro Recording'),
            QCoreApplication.translate('ViewManager', 'Sto&p Macro Recording'),
            0, 0, self.macroActGrp, 'vm_macro_stop_recording')
        self.macroStopRecAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Stop Macro Recording'))
        self.macroStopRecAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Stop Macro Recording</b>"""
            """<p>Stop recording editor commands into a new macro.</p>"""
        ))
        self.macroStopRecAct.triggered.connect(self.__macroStopRecording)
        self.macroActions.append(self.macroStopRecAct)
        
        self.macroRunAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Run Macro'),
            QCoreApplication.translate('ViewManager', '&Run Macro'),
            0, 0, self.macroActGrp, 'vm_macro_run')
        self.macroRunAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Run Macro'))
        self.macroRunAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Run Macro</b>"""
            """<p>Run a previously recorded editor macro.</p>"""
        ))
        self.macroRunAct.triggered.connect(self.__macroRun)
        self.macroActions.append(self.macroRunAct)
        
        self.macroDeleteAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Delete Macro'),
            QCoreApplication.translate('ViewManager', '&Delete Macro'),
            0, 0, self.macroActGrp, 'vm_macro_delete')
        self.macroDeleteAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Delete Macro'))
        self.macroDeleteAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Delete Macro</b>"""
            """<p>Delete a previously recorded editor macro.</p>"""
        ))
        self.macroDeleteAct.triggered.connect(self.__macroDelete)
        self.macroActions.append(self.macroDeleteAct)
        
        self.macroLoadAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Load Macro'),
            QCoreApplication.translate('ViewManager', '&Load Macro'),
            0, 0, self.macroActGrp, 'vm_macro_load')
        self.macroLoadAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Load Macro'))
        self.macroLoadAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Load Macro</b>"""
            """<p>Load an editor macro from a file.</p>"""
        ))
        self.macroLoadAct.triggered.connect(self.__macroLoad)
        self.macroActions.append(self.macroLoadAct)
        
        self.macroSaveAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Save Macro'),
            QCoreApplication.translate('ViewManager', '&Save Macro'),
            0, 0, self.macroActGrp, 'vm_macro_save')
        self.macroSaveAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Save Macro'))
        self.macroSaveAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Save Macro</b>"""
            """<p>Save a previously recorded editor macro to a file.</p>"""
        ))
        self.macroSaveAct.triggered.connect(self.__macroSave)
        self.macroActions.append(self.macroSaveAct)
        
        self.macroActGrp.setEnabled(False)
        
    def initMacroMenu(self):
        """
        Public method to create the Macro menu.
        
        @return the generated menu
        """
        menu = QMenu(QCoreApplication.translate('ViewManager', "&Macros"),
                     self.ui)
        menu.setTearOffEnabled(True)
        menu.addActions(self.macroActGrp.actions())
        
        return menu
    
    #####################################################################
    ## Initialize the bookmark related actions, bookmark menu and toolbar
    #####################################################################
    
    def __initBookmarkActions(self):
        """
        Private method defining the user interface actions for the bookmarks
        commands.
        """
        self.bookmarkActGrp = createActionGroup(self)

        self.bookmarkToggleAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Toggle Bookmark'),
            UI.PixmapCache.getIcon("bookmarkToggle.png"),
            QCoreApplication.translate('ViewManager', '&Toggle Bookmark'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Alt+Ctrl+T", "Bookmark|Toggle")),
            0,
            self.bookmarkActGrp, 'vm_bookmark_toggle')
        self.bookmarkToggleAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Toggle Bookmark'))
        self.bookmarkToggleAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Toggle Bookmark</b>"""
            """<p>Toggle a bookmark at the current line of the current"""
            """ editor.</p>"""
        ))
        self.bookmarkToggleAct.triggered.connect(self.__toggleBookmark)
        self.bookmarkActions.append(self.bookmarkToggleAct)
        
        self.bookmarkNextAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Next Bookmark'),
            UI.PixmapCache.getIcon("bookmarkNext.png"),
            QCoreApplication.translate('ViewManager', '&Next Bookmark'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+PgDown", "Bookmark|Next")),
            0,
            self.bookmarkActGrp, 'vm_bookmark_next')
        self.bookmarkNextAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Next Bookmark'))
        self.bookmarkNextAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Next Bookmark</b>"""
            """<p>Go to next bookmark of the current editor.</p>"""
        ))
        self.bookmarkNextAct.triggered.connect(self.__nextBookmark)
        self.bookmarkActions.append(self.bookmarkNextAct)
        
        self.bookmarkPreviousAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Previous Bookmark'),
            UI.PixmapCache.getIcon("bookmarkPrevious.png"),
            QCoreApplication.translate('ViewManager', '&Previous Bookmark'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Ctrl+PgUp", "Bookmark|Previous")),
            0,
            self.bookmarkActGrp, 'vm_bookmark_previous')
        self.bookmarkPreviousAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Previous Bookmark'))
        self.bookmarkPreviousAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Previous Bookmark</b>"""
            """<p>Go to previous bookmark of the current editor.</p>"""
        ))
        self.bookmarkPreviousAct.triggered.connect(self.__previousBookmark)
        self.bookmarkActions.append(self.bookmarkPreviousAct)
        
        self.bookmarkClearAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Clear Bookmarks'),
            QCoreApplication.translate('ViewManager', '&Clear Bookmarks'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Alt+Ctrl+C", "Bookmark|Clear")),
            0,
            self.bookmarkActGrp, 'vm_bookmark_clear')
        self.bookmarkClearAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Clear Bookmarks'))
        self.bookmarkClearAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Clear Bookmarks</b>"""
            """<p>Clear bookmarks of all editors.</p>"""
        ))
        self.bookmarkClearAct.triggered.connect(self.__clearAllBookmarks)
        self.bookmarkActions.append(self.bookmarkClearAct)
        
        self.syntaxErrorGotoAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Goto Syntax Error'),
            UI.PixmapCache.getIcon("syntaxErrorGoto.png"),
            QCoreApplication.translate('ViewManager', '&Goto Syntax Error'),
            0, 0,
            self.bookmarkActGrp, 'vm_syntaxerror_goto')
        self.syntaxErrorGotoAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Goto Syntax Error'))
        self.syntaxErrorGotoAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Goto Syntax Error</b>"""
            """<p>Go to next syntax error of the current editor.</p>"""
        ))
        self.syntaxErrorGotoAct.triggered.connect(self.__gotoSyntaxError)
        self.bookmarkActions.append(self.syntaxErrorGotoAct)
        
        self.syntaxErrorClearAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Clear Syntax Errors'),
            QCoreApplication.translate('ViewManager', 'Clear &Syntax Errors'),
            0, 0,
            self.bookmarkActGrp, 'vm_syntaxerror_clear')
        self.syntaxErrorClearAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Clear Syntax Errors'))
        self.syntaxErrorClearAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Clear Syntax Errors</b>"""
            """<p>Clear syntax errors of all editors.</p>"""
        ))
        self.syntaxErrorClearAct.triggered.connect(
            self.__clearAllSyntaxErrors)
        self.bookmarkActions.append(self.syntaxErrorClearAct)
        
        self.warningsNextAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Next warning message'),
            UI.PixmapCache.getIcon("warningNext.png"),
            QCoreApplication.translate('ViewManager', '&Next warning message'),
            0, 0,
            self.bookmarkActGrp, 'vm_warning_next')
        self.warningsNextAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Next warning message'))
        self.warningsNextAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Next warning message</b>"""
            """<p>Go to next line of the current editor"""
            """ having a pyflakes warning.</p>"""
        ))
        self.warningsNextAct.triggered.connect(self.__nextWarning)
        self.bookmarkActions.append(self.warningsNextAct)
        
        self.warningsPreviousAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Previous warning message'),
            UI.PixmapCache.getIcon("warningPrev.png"),
            QCoreApplication.translate(
                'ViewManager', '&Previous warning message'),
            0, 0,
            self.bookmarkActGrp, 'vm_warning_previous')
        self.warningsPreviousAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Previous warning message'))
        self.warningsPreviousAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Previous warning message</b>"""
            """<p>Go to previous line of the current editor"""
            """ having a pyflakes warning.</p>"""
        ))
        self.warningsPreviousAct.triggered.connect(self.__previousWarning)
        self.bookmarkActions.append(self.warningsPreviousAct)
        
        self.warningsClearAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Clear Warning Messages'),
            QCoreApplication.translate(
                'ViewManager', 'Clear &Warning Messages'),
            0, 0,
            self.bookmarkActGrp, 'vm_warnings_clear')
        self.warningsClearAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Clear Warning Messages'))
        self.warningsClearAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Clear Warning Messages</b>"""
            """<p>Clear pyflakes warning messages of all editors.</p>"""
        ))
        self.warningsClearAct.triggered.connect(self.__clearAllWarnings)
        self.bookmarkActions.append(self.warningsClearAct)
        
        self.notcoveredNextAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Next uncovered line'),
            UI.PixmapCache.getIcon("notcoveredNext.png"),
            QCoreApplication.translate('ViewManager', '&Next uncovered line'),
            0, 0,
            self.bookmarkActGrp, 'vm_uncovered_next')
        self.notcoveredNextAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Next uncovered line'))
        self.notcoveredNextAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Next uncovered line</b>"""
            """<p>Go to next line of the current editor marked as not"""
            """ covered.</p>"""
        ))
        self.notcoveredNextAct.triggered.connect(self.__nextUncovered)
        self.bookmarkActions.append(self.notcoveredNextAct)
        
        self.notcoveredPreviousAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Previous uncovered line'),
            UI.PixmapCache.getIcon("notcoveredPrev.png"),
            QCoreApplication.translate(
                'ViewManager', '&Previous uncovered line'),
            0, 0,
            self.bookmarkActGrp, 'vm_uncovered_previous')
        self.notcoveredPreviousAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Previous uncovered line'))
        self.notcoveredPreviousAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Previous uncovered line</b>"""
            """<p>Go to previous line of the current editor marked"""
            """ as not covered.</p>"""
        ))
        self.notcoveredPreviousAct.triggered.connect(
            self.__previousUncovered)
        self.bookmarkActions.append(self.notcoveredPreviousAct)
        
        self.taskNextAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Next Task'),
            UI.PixmapCache.getIcon("taskNext.png"),
            QCoreApplication.translate('ViewManager', '&Next Task'),
            0, 0,
            self.bookmarkActGrp, 'vm_task_next')
        self.taskNextAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Next Task'))
        self.taskNextAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Next Task</b>"""
            """<p>Go to next line of the current editor having a task.</p>"""
        ))
        self.taskNextAct.triggered.connect(self.__nextTask)
        self.bookmarkActions.append(self.taskNextAct)
        
        self.taskPreviousAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Previous Task'),
            UI.PixmapCache.getIcon("taskPrev.png"),
            QCoreApplication.translate(
                'ViewManager', '&Previous Task'),
            0, 0,
            self.bookmarkActGrp, 'vm_task_previous')
        self.taskPreviousAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Previous Task'))
        self.taskPreviousAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Previous Task</b>"""
            """<p>Go to previous line of the current editor having a"""
            """ task.</p>"""
        ))
        self.taskPreviousAct.triggered.connect(self.__previousTask)
        self.bookmarkActions.append(self.taskPreviousAct)
        
        self.changeNextAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Next Change'),
            UI.PixmapCache.getIcon("changeNext.png"),
            QCoreApplication.translate('ViewManager', '&Next Change'),
            0, 0,
            self.bookmarkActGrp, 'vm_change_next')
        self.changeNextAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Next Change'))
        self.changeNextAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Next Change</b>"""
            """<p>Go to next line of the current editor having a change"""
            """ marker.</p>"""
        ))
        self.changeNextAct.triggered.connect(self.__nextChange)
        self.bookmarkActions.append(self.changeNextAct)
        
        self.changePreviousAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Previous Change'),
            UI.PixmapCache.getIcon("changePrev.png"),
            QCoreApplication.translate(
                'ViewManager', '&Previous Change'),
            0, 0,
            self.bookmarkActGrp, 'vm_change_previous')
        self.changePreviousAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Previous Change'))
        self.changePreviousAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Previous Change</b>"""
            """<p>Go to previous line of the current editor having"""
            """ a change marker.</p>"""
        ))
        self.changePreviousAct.triggered.connect(self.__previousChange)
        self.bookmarkActions.append(self.changePreviousAct)
        
        self.bookmarkActGrp.setEnabled(False)
        
    def initBookmarkMenu(self):
        """
        Public method to create the Bookmark menu.
        
        @return the generated menu
        """
        menu = QMenu(QCoreApplication.translate('ViewManager', '&Bookmarks'),
                     self.ui)
        self.bookmarksMenu = QMenu(
            QCoreApplication.translate('ViewManager', '&Bookmarks'),
            menu)
        menu.setTearOffEnabled(True)
        
        menu.addAction(self.bookmarkToggleAct)
        menu.addAction(self.bookmarkNextAct)
        menu.addAction(self.bookmarkPreviousAct)
        menu.addAction(self.bookmarkClearAct)
        menu.addSeparator()
        self.menuBookmarksAct = menu.addMenu(self.bookmarksMenu)
        menu.addSeparator()
        menu.addAction(self.syntaxErrorGotoAct)
        menu.addAction(self.syntaxErrorClearAct)
        menu.addSeparator()
        menu.addAction(self.warningsNextAct)
        menu.addAction(self.warningsPreviousAct)
        menu.addAction(self.warningsClearAct)
        menu.addSeparator()
        menu.addAction(self.notcoveredNextAct)
        menu.addAction(self.notcoveredPreviousAct)
        menu.addSeparator()
        menu.addAction(self.taskNextAct)
        menu.addAction(self.taskPreviousAct)
        menu.addSeparator()
        menu.addAction(self.changeNextAct)
        menu.addAction(self.changePreviousAct)
        
        self.bookmarksMenu.aboutToShow.connect(self.__showBookmarksMenu)
        self.bookmarksMenu.triggered.connect(self.__bookmarkSelected)
        menu.aboutToShow.connect(self.__showBookmarkMenu)
        
        return menu
        
    def initBookmarkToolbar(self, toolbarManager):
        """
        Public method to create the Bookmark toolbar.
        
        @param toolbarManager reference to a toolbar manager object
            (E5ToolBarManager)
        @return the generated toolbar
        """
        tb = QToolBar(QCoreApplication.translate('ViewManager', 'Bookmarks'),
                      self.ui)
        tb.setIconSize(UI.Config.ToolBarIconSize)
        tb.setObjectName("BookmarksToolbar")
        tb.setToolTip(QCoreApplication.translate('ViewManager', 'Bookmarks'))
        
        tb.addAction(self.bookmarkToggleAct)
        tb.addAction(self.bookmarkNextAct)
        tb.addAction(self.bookmarkPreviousAct)
        tb.addSeparator()
        tb.addAction(self.syntaxErrorGotoAct)
        tb.addSeparator()
        tb.addAction(self.warningsNextAct)
        tb.addAction(self.warningsPreviousAct)
        tb.addSeparator()
        tb.addAction(self.taskNextAct)
        tb.addAction(self.taskPreviousAct)
        tb.addSeparator()
        tb.addAction(self.changeNextAct)
        tb.addAction(self.changePreviousAct)
        
        toolbarManager.addToolBar(tb, tb.windowTitle())
        toolbarManager.addAction(self.notcoveredNextAct, tb.windowTitle())
        toolbarManager.addAction(self.notcoveredPreviousAct, tb.windowTitle())
        
        return tb
    
    ##################################################################
    ## Initialize the spell checking related actions
    ##################################################################
    
    def __initSpellingActions(self):
        """
        Private method to initialize the spell checking actions.
        """
        self.spellingActGrp = createActionGroup(self)
        
        self.spellCheckAct = E5Action(
            QCoreApplication.translate('ViewManager', 'Check spelling'),
            UI.PixmapCache.getIcon("spellchecking.png"),
            QCoreApplication.translate(
                'ViewManager', 'Check &spelling...'),
            QKeySequence(QCoreApplication.translate(
                'ViewManager', "Shift+F7", "Spelling|Spell Check")),
            0,
            self.spellingActGrp, 'vm_spelling_spellcheck')
        self.spellCheckAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', 'Perform spell check of current editor'))
        self.spellCheckAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Check spelling</b>"""
            """<p>Perform a spell check of the current editor.</p>"""
        ))
        self.spellCheckAct.triggered.connect(self.__spellCheck)
        self.spellingActions.append(self.spellCheckAct)
        
        self.autoSpellCheckAct = E5Action(
            QCoreApplication.translate(
                'ViewManager', 'Automatic spell checking'),
            UI.PixmapCache.getIcon("autospellchecking.png"),
            QCoreApplication.translate(
                'ViewManager', '&Automatic spell checking'),
            0, 0,
            self.spellingActGrp, 'vm_spelling_autospellcheck', True)
        self.autoSpellCheckAct.setStatusTip(QCoreApplication.translate(
            'ViewManager', '(De-)Activate automatic spell checking'))
        self.autoSpellCheckAct.setWhatsThis(QCoreApplication.translate(
            'ViewManager',
            """<b>Automatic spell checking</b>"""
            """<p>Activate or deactivate the automatic spell checking"""
            """ function of all editors.</p>"""
        ))
        self.autoSpellCheckAct.setChecked(
            Preferences.getEditor("AutoSpellCheckingEnabled"))
        self.autoSpellCheckAct.triggered.connect(
            self.__setAutoSpellChecking)
        self.spellingActions.append(self.autoSpellCheckAct)
        
        self.__enableSpellingActions()
        
    def __enableSpellingActions(self):
        """
        Private method to set the enabled state of the spelling actions.
        """
        from QScintilla.SpellChecker import SpellChecker
        spellingAvailable = SpellChecker.isAvailable()
        
        self.spellCheckAct.setEnabled(
            len(self.editors) != 0 and spellingAvailable)
        self.autoSpellCheckAct.setEnabled(spellingAvailable)
    
    def addToExtrasMenu(self, menu):
        """
        Public method to add some actions to the extras menu.
        
        @param menu reference to the menu to add actions to (QMenu)
        """
        self.__editSpellingMenu = QMenu(QCoreApplication.translate(
            'ViewManager', "Edit Dictionary"))
        self.__editProjectPwlAct = self.__editSpellingMenu.addAction(
            QCoreApplication.translate('ViewManager', "Project Word List"),
            self.__editProjectPWL)
        self.__editProjectPelAct = self.__editSpellingMenu.addAction(
            QCoreApplication.translate(
                'ViewManager', "Project Exception List"),
            self.__editProjectPEL)
        self.__editSpellingMenu.addSeparator()
        self.__editUserPwlAct = self.__editSpellingMenu.addAction(
            QCoreApplication.translate('ViewManager', "User Word List"),
            self.__editUserPWL)
        self.__editUserPelAct = self.__editSpellingMenu.addAction(
            QCoreApplication.translate('ViewManager', "User Exception List"),
            self.__editUserPEL)
        self.__editSpellingMenu.aboutToShow.connect(
            self.__showEditSpellingMenu)
        
        menu.addAction(self.spellCheckAct)
        menu.addAction(self.autoSpellCheckAct)
        menu.addMenu(self.__editSpellingMenu)
        menu.addSeparator()
    
    def initSpellingToolbar(self, toolbarManager):
        """
        Public method to create the Spelling toolbar.
        
        @param toolbarManager reference to a toolbar manager object
            (E5ToolBarManager)
        @return the generated toolbar
        """
        tb = QToolBar(QCoreApplication.translate('ViewManager', 'Spelling'),
                      self.ui)
        tb.setIconSize(UI.Config.ToolBarIconSize)
        tb.setObjectName("SpellingToolbar")
        tb.setToolTip(QCoreApplication.translate('ViewManager', 'Spelling'))
        
        tb.addAction(self.spellCheckAct)
        tb.addAction(self.autoSpellCheckAct)
        
        toolbarManager.addToolBar(tb, tb.windowTitle())
        
        return tb
    
    ##################################################################
    ## Methods and slots that deal with file and window handling
    ##################################################################
    
    def __openFiles(self):
        """
        Private slot to open some files.
        """
        # set the cwd of the dialog based on the following search criteria:
        #     1: Directory of currently active editor
        #     2: Directory of currently active project
        #     3: CWD
        import QScintilla.Lexers
        filter = self._getOpenFileFilter()
        progs = E5FileDialog.getOpenFileNamesAndFilter(
            self.ui,
            QCoreApplication.translate('ViewManager', "Open files"),
            self._getOpenStartDir(),
            QScintilla.Lexers.getOpenFileFiltersList(True, True),
            filter)[0]
        for prog in progs:
            self.openFiles(prog)
    
    def openFiles(self, prog):
        """
        Public slot to open some files.
        
        @param prog name of file to be opened (string)
        """
        prog = Utilities.normabspath(prog)
        # Open up the new files.
        self.openSourceFile(prog)

    def checkDirty(self, editor, autosave=False):
        """
        Public method to check dirty status and open a message window.
        
        @param editor editor window to check
        @param autosave flag indicating that the file should be saved
            automatically (boolean)
        @return flag indicating successful reset of the dirty flag (boolean)
        """
        if editor.isModified():
            fn = editor.getFileName()
            # ignore the dirty status, if there is more than one open editor
            # for the same file
            if fn and self.getOpenEditorCount(fn) > 1:
                return True
            
            if fn is None:
                fn = editor.getNoName()
                autosave = False
            if autosave:
                res = editor.saveFile()
            else:
                res = E5MessageBox.okToClearData(
                    self.ui,
                    QCoreApplication.translate('ViewManager', "File Modified"),
                    QCoreApplication.translate(
                        'ViewManager',
                        """<p>The file <b>{0}</b> has unsaved changes.</p>""")
                    .format(fn),
                    editor.saveFile)
            if res:
                self.setEditorName(editor, editor.getFileName())
            return res
        
        return True
        
    def checkAllDirty(self):
        """
        Public method to check the dirty status of all editors.
        
        @return flag indicating successful reset of all dirty flags (boolean)
        """
        for editor in self.editors:
            if not self.checkDirty(editor):
                return False
        
        return True
        
    def closeEditor(self, editor):
        """
        Public method to close an editor window.
        
        @param editor editor window to be closed
        @return flag indicating success (boolean)
        """
        # save file if necessary
        if not self.checkDirty(editor):
            return False
        
        # get the filename of the editor for later use
        fn = editor.getFileName()
        
        # remove the window
        editor.parent().shutdownTimer()
        self._removeView(editor)
        self.editors.remove(editor)
        
        # send a signal, if it was the last editor for this filename
        if fn and self.getOpenEditor(fn) is None:
            self.editorClosed.emit(fn)
        self.editorClosedEd.emit(editor)
        
        # send a signal, if it was the very last editor
        if not len(self.editors):
            self.__lastEditorClosed()
            self.lastEditorClosed.emit()
        
        editor.deleteLater()
        
        return True
        
    def closeCurrentWindow(self):
        """
        Public method to close the current window.
        
        @return flag indicating success (boolean)
        """
        aw = self.activeWindow()
        if aw is None:
            return False
        
        res = self.closeEditor(aw)
        if res and aw == self.currentEditor:
            self.currentEditor = None
        
        return res
        
    def closeAllWindows(self):
        """
        Public method to close all editor windows via file menu.
        """
        savedEditors = self.editors[:]
        for editor in savedEditors:
            self.closeEditor(editor)
        
    def closeWindow(self, fn):
        """
        Public method to close an arbitrary source editor.
        
        @param fn filename of editor to be closed
        @return flag indicating success (boolean)
        """
        for editor in self.editors:
            if Utilities.samepath(fn, editor.getFileName()):
                break
        else:
            return True
        
        res = self.closeEditor(editor)
        if res and editor == self.currentEditor:
            self.currentEditor = None
        
        return res
        
    def closeEditorWindow(self, editor):
        """
        Public method to close an arbitrary source editor.
        
        @param editor editor to be closed
        """
        if editor is None:
            return
        
        res = self.closeEditor(editor)
        if res and editor == self.currentEditor:
            self.currentEditor = None
        
    def exit(self):
        """
        Public method to handle the debugged program terminating.
        """
        if self.currentEditor is not None:
            self.currentEditor.highlight()
            self.currentEditor = None
        
        for editor in self.editors:
            editor.refreshCoverageAnnotations()
        
        self.__setSbFile()
        
    def openSourceFile(self, fn, lineno=-1, filetype="",
                       selStart=0, selEnd=0, pos=0, next=False):
        """
        Public slot to display a file in an editor.
        
        @param fn name of file to be opened (string)
        @param lineno line number to place the cursor at (integer) or
            list of line numbers (list of integers) (cursor will be
            placed at the next line greater than the current one)
        @param filetype type of the source file (string)
        @param selStart start of an area to be selected (integer)
        @param selEnd end of an area to be selected (integer)
        @param pos position within the line to place the cursor at (integer)
        @param next flag indicating to add the file next to the current
            editor (bool)
        """
        try:
            newWin, editor = self.getEditor(fn, filetype=filetype, next=next)
        except (IOError, UnicodeDecodeError):
            return
        
        if newWin:
            self._modificationStatusChanged(editor.isModified(), editor)
        self._checkActions(editor)
        
        cline, cindex = editor.getCursorPosition()
        cline += 1
        if isinstance(lineno, list):
            if len(lineno) > 1:
                for line in lineno:
                    if line > cline:
                        break
                else:
                    line = lineno[0]
            elif len(lineno) == 1:
                line = lineno[0]
            else:
                line = -1
        else:
            line = lineno
            
        if line >= 0 and line != cline:
            editor.ensureVisibleTop(line)
            editor.gotoLine(line, pos)
            
            if selStart != selEnd:
                editor.setSelection(line - 1, selStart, line - 1, selEnd)
        
        # insert filename into list of recently opened files
        self.addToRecentList(fn)
        
    def __connectEditor(self, editor):
        """
        Private method to establish all editor connections.
        
        @param editor reference to the editor object to be connected
        """
        editor.modificationStatusChanged.connect(
            self._modificationStatusChanged)
        editor.cursorChanged.connect(self.__cursorChanged)
        editor.editorSaved.connect(self.__editorSaved)
        editor.editorRenamed.connect(self.__editorRenamed)
        editor.breakpointToggled.connect(self.__breakpointToggled)
        editor.bookmarkToggled.connect(self.__bookmarkToggled)
        editor.syntaxerrorToggled.connect(self._syntaxErrorToggled)
        editor.coverageMarkersShown.connect(self.__coverageMarkersShown)
        editor.autoCompletionAPIsAvailable.connect(
            self.__editorAutoCompletionAPIsAvailable)
        editor.undoAvailable.connect(self.undoAct.setEnabled)
        editor.redoAvailable.connect(self.redoAct.setEnabled)
        editor.taskMarkersUpdated.connect(self.__taskMarkersUpdated)
        editor.changeMarkersUpdated.connect(self.__changeMarkersUpdated)
        editor.languageChanged.connect(self.__editorConfigChanged)
        editor.eolChanged.connect(self.__editorConfigChanged)
        editor.encodingChanged.connect(self.__editorConfigChanged)
        editor.selectionChanged.connect(self.__searchWidget.selectionChanged)
        editor.selectionChanged.connect(self.__replaceWidget.selectionChanged)
        editor.selectionChanged.connect(self.__editorSelectionChanged)
        editor.lastEditPositionAvailable.connect(
            self.__lastEditPositionAvailable)
        editor.zoomValueChanged.connect(self.zoomValueChanged)
        
        editor.languageChanged.connect(
            lambda: self.editorLanguageChanged.emit(editor))
        editor.textChanged.connect(lambda: self.editorTextChanged.emit(editor))

    def newEditorView(self, fn, caller, filetype=""):
        """
        Public method to create a new editor displaying the given document.
        
        @param fn filename of this view
        @param caller reference to the editor calling this method
        @param filetype type of the source file (string)
        """
        editor, assembly = self.cloneEditor(caller, filetype, fn)
        
        self._addView(assembly, fn, caller.getNoName())
        self._modificationStatusChanged(editor.isModified(), editor)
        self._checkActions(editor)

    def cloneEditor(self, caller, filetype, fn):
        """
        Public method to clone an editor displaying the given document.
        
        @param caller reference to the editor calling this method
        @param filetype type of the source file (string)
        @param fn filename of this view
        @return reference to the new editor object (Editor.Editor) and the new
            edito assembly object (EditorAssembly.EditorAssembly)
        """
        from QScintilla.EditorAssembly import EditorAssembly
        assembly = EditorAssembly(self.dbs, fn, self, filetype=filetype,
                                  editor=caller,
                                  tv=e5App().getObject("TaskViewer"))
        editor = assembly.getEditor()
        self.editors.append(editor)
        self.__connectEditor(editor)
        self.__editorOpened()
        self.editorOpened.emit(fn)
        self.editorOpenedEd.emit(editor)

        return editor, assembly
        
    def addToRecentList(self, fn):
        """
        Public slot to add a filename to the list of recently opened files.
        
        @param fn name of the file to be added
        """
        for recent in self.recent[:]:
            if Utilities.samepath(fn, recent):
                self.recent.remove(recent)
        self.recent.insert(0, fn)
        maxRecent = Preferences.getUI("RecentNumber")
        if len(self.recent) > maxRecent:
            self.recent = self.recent[:maxRecent]
        self.__saveRecent()
        
    def showDebugSource(self, fn, line):
        """
        Public method to open the given file and highlight the given line in
        it.
        
        @param fn filename of editor to update (string)
        @param line line number to highlight (int)
        """
        self.openSourceFile(fn, line)
        self.setFileLine(fn, line)
        
    def setFileLine(self, fn, line, error=False, syntaxError=False):
        """
        Public method to update the user interface when the current program
        or line changes.
        
        @param fn filename of editor to update (string)
        @param line line number to highlight (int)
        @param error flag indicating an error highlight (boolean)
        @param syntaxError flag indicating a syntax error
        """
        try:
            newWin, self.currentEditor = self.getEditor(fn)
        except (IOError, UnicodeDecodeError):
            return
        
        enc = self.currentEditor.getEncoding()
        lang = self.currentEditor.getLanguage()
        eol = self.currentEditor.getEolIndicator()
        zoom = self.currentEditor.getZoom()
        self.__setSbFile(fn, line, encoding=enc, language=lang, eol=eol,
                         zoom=zoom)
        
        # Change the highlighted line.
        self.currentEditor.highlight(line, error, syntaxError)
        
        self.currentEditor.highlightVisible()
        self._checkActions(self.currentEditor, False)
        
    def __setSbFile(self, fn=None, line=None, pos=None,
                    encoding=None, language=None, eol=None,
                    zoom=None):
        """
        Private method to set the file info in the status bar.
        
        @param fn filename to display (string)
        @param line line number to display (int)
        @param pos character position to display (int)
        @param encoding encoding name to display (string)
        @param language language to display (string)
        @param eol eol indicator to display (string)
        @param zoom zoom value (integer)
        """
        if not fn:
            fn = ''
            writ = '  '
        else:
            if QFileInfo(fn).isWritable():
                writ = 'rw'
            else:
                writ = 'ro'
        self.sbWritable.setText(writ)
        
        if line is None:
            line = ''
        self.sbLine.setText(
            QCoreApplication.translate('ViewManager', 'Line: {0:5}')
            .format(line))
        
        if pos is None:
            pos = ''
        self.sbPos.setText(
            QCoreApplication.translate('ViewManager', 'Pos: {0:5}')
            .format(pos))
        
        if encoding is None:
            encoding = ''
        self.sbEnc.setText(encoding)
        
        if language is None:
            language = ''
        import QScintilla.Lexers
        pixmap = QScintilla.Lexers.getLanguageIcon(language, True)
        self.sbLang.setPixmap(pixmap)
        if pixmap.isNull():
            self.sbLang.setText(language)
            self.sbLang.setToolTip("")
        else:
            self.sbLang.setText("")
            self.sbLang.setToolTip(
                QCoreApplication.translate('ViewManager', 'Language: {0}')
                .format(language))
        
        if eol is None:
            eol = ''
        self.sbEol.setPixmap(self.__eolPixmap(eol))
        self.sbEol.setToolTip(
            QCoreApplication.translate('ViewManager', 'EOL Mode: {0}')
            .format(eol))
        
        if zoom is None:
            if QApplication.focusWidget() == e5App().getObject("Shell"):
                aw = e5App().getObject("Shell")
            else:
                aw = self.activeWindow()
            if aw:
                self.sbZoom.setValue(aw.getZoom())
        else:
            self.sbZoom.setValue(zoom)
        
    def __eolPixmap(self, eolIndicator):
        """
        Private method to get an EOL pixmap for an EOL string.
        
        @param eolIndicator eol indicator string (string)
        @return pixmap for the eol indicator (QPixmap)
        """
        if eolIndicator == "LF":
            pixmap = UI.PixmapCache.getPixmap("eolLinux.png")
        elif eolIndicator == "CR":
            pixmap = UI.PixmapCache.getPixmap("eolMac.png")
        elif eolIndicator == "CRLF":
            pixmap = UI.PixmapCache.getPixmap("eolWindows.png")
        else:
            pixmap = QPixmap()
        return pixmap
        
    def __unhighlight(self):
        """
        Private slot to switch of all highlights.
        """
        self.unhighlight()
        
    def unhighlight(self, current=False):
        """
        Public method to switch off all highlights or the highlight of
        the current editor.
        
        @param current flag indicating only the current editor should be
            unhighlighted (boolean)
        """
        if current:
            if self.currentEditor is not None:
                self.currentEditor.highlight()
        else:
            for editor in self.editors:
                editor.highlight()
        
    def getOpenFilenames(self):
        """
        Public method returning a list of the filenames of all editors.
        
        @return list of all opened filenames (list of strings)
        """
        filenames = []
        for editor in self.editors:
            fn = editor.getFileName()
            if fn is not None and fn not in filenames and os.path.exists(fn):
                # only return names of existing files
                filenames.append(fn)
        
        return filenames
        
    def getEditor(self, fn, filetype="", next=False):
        """
        Public method to return the editor displaying the given file.
        
        If there is no editor with the given file, a new editor window is
        created.
        
        @param fn filename to look for
        @param filetype type of the source file (string)
        @param next flag indicating that if a new editor needs to be created,
            it should be added next to the current editor (bool)
        @return tuple of two values giving a flag indicating a new window
            creation and a reference to the editor displaying this file
        """
        newWin = False
        editor = self.activeWindow()
        if editor is None or not Utilities.samepath(fn, editor.getFileName()):
            for editor in self.editors:
                if Utilities.samepath(fn, editor.getFileName()):
                    break
            else:
                from QScintilla.EditorAssembly import EditorAssembly
                assembly = EditorAssembly(self.dbs, fn, self,
                                          filetype=filetype,
                                          tv=e5App().getObject("TaskViewer"))
                editor = assembly.getEditor()
                self.editors.append(editor)
                self.__connectEditor(editor)
                self.__editorOpened()
                self.editorOpened.emit(fn)
                self.editorOpenedEd.emit(editor)
                newWin = True
        
        if newWin:
            self._addView(assembly, fn, next=next)
        else:
            self._showView(editor.parent(), fn)
        
        return (newWin, editor)
        
    def getOpenEditors(self):
        """
        Public method to get references to all open editors.
        
        @return list of references to all open editors (list of
            QScintilla.editor)
        """
        return self.editors
        
    def getOpenEditorsCount(self):
        """
        Public method to get the number of open editors.
        
        @return number of open editors (integer)
        """
        return len(self.editors)
        
    def getOpenEditor(self, fn):
        """
        Public method to return the editor displaying the given file.
        
        @param fn filename to look for
        @return a reference to the editor displaying this file or None, if
            no editor was found
        """
        for editor in self.editors:
            if Utilities.samepath(fn, editor.getFileName()):
                return editor
        
        return None
        
    def getOpenEditorCount(self, fn):
        """
        Public method to return the count of editors displaying the given file.
        
        @param fn filename to look for
        @return count of editors displaying this file (integer)
        """
        count = 0
        for editor in self.editors:
            if Utilities.samepath(fn, editor.getFileName()):
                count += 1
        return count
        
    def getActiveName(self):
        """
        Public method to retrieve the filename of the active window.
        
        @return filename of active window (string)
        """
        aw = self.activeWindow()
        if aw:
            return aw.getFileName()
        else:
            return None
        
    def saveEditor(self, fn):
        """
        Public method to save a named editor file.
        
        @param fn filename of editor to be saved (string)
        @return flag indicating success (boolean)
        """
        for editor in self.editors:
            if Utilities.samepath(fn, editor.getFileName()):
                break
        else:
            return True
        
        if not editor.isModified():
            return True
        else:
            ok = editor.saveFile()
            return ok
        
    def saveEditorEd(self, ed):
        """
        Public slot to save the contents of an editor.
        
        @param ed editor to be saved
        @return flag indicating success (boolean)
        """
        if ed:
            if not ed.isModified():
                return True
            else:
                ok = ed.saveFile()
                if ok:
                    self.setEditorName(ed, ed.getFileName())
                return ok
        else:
            return False
        
    def saveCurrentEditor(self):
        """
        Public slot to save the contents of the current editor.
        """
        aw = self.activeWindow()
        self.saveEditorEd(aw)

    def saveAsEditorEd(self, ed):
        """
        Public slot to save the contents of an editor to a new file.
        
        @param ed editor to be saved
        """
        if ed:
            ok = ed.saveFileAs()
            if ok:
                self.setEditorName(ed, ed.getFileName())
        
    def saveAsCurrentEditor(self):
        """
        Public slot to save the contents of the current editor to a new file.
        """
        aw = self.activeWindow()
        self.saveAsEditorEd(aw)

    def saveCopyEditorEd(self, ed):
        """
        Public slot to save the contents of an editor to a new copy of
        the file.
        
        @param ed editor to be saved
        """
        if ed:
            ed.saveFileCopy()
        
    def saveCopyCurrentEditor(self):
        """
        Public slot to save the contents of the current editor to a new copy
        of the file.
        """
        aw = self.activeWindow()
        self.saveCopyEditorEd(aw)
        
    def saveEditorsList(self, editors):
        """
        Public slot to save a list of editors.
        
        @param editors list of editors to be saved
        """
        for editor in editors:
            ok = editor.saveFile()
            if ok:
                self.setEditorName(editor, editor.getFileName())
        
    def saveAllEditors(self):
        """
        Public slot to save the contents of all editors.
        """
        for editor in self.editors:
            ok = editor.saveFile()
            if ok:
                self.setEditorName(editor, editor.getFileName())
        
        # restart autosave timer
        if self.autosaveInterval > 0:
            self.autosaveTimer.start(self.autosaveInterval * 60000)
        
    def __exportMenuTriggered(self, act):
        """
        Private method to handle the selection of an export format.
        
        @param act reference to the action that was triggered (QAction)
        """
        aw = self.activeWindow()
        if aw:
            exporterFormat = act.data()
            aw.exportFile(exporterFormat)
        
    def newEditor(self):
        """
        Public slot to generate a new empty editor.
        """
        from QScintilla.EditorAssembly import EditorAssembly
        assembly = EditorAssembly(self.dbs, None, self,
                                  tv=e5App().getObject("TaskViewer"))
        editor = assembly.getEditor()
        self.editors.append(editor)
        self.__connectEditor(editor)
        self._addView(assembly, None)
        self.__editorOpened()
        self._checkActions(editor)
        self.editorOpened.emit("")
        self.editorOpenedEd.emit(editor)
        
    def printEditor(self, editor):
        """
        Public slot to print an editor.
        
        @param editor editor to be printed
        """
        if editor:
            editor.printFile()
        else:
            return
        
    def printCurrentEditor(self):
        """
        Public slot to print the contents of the current editor.
        """
        aw = self.activeWindow()
        self.printEditor(aw)
        
    def printPreviewCurrentEditor(self):
        """
        Public slot to show a print preview of the current editor.
        """
        aw = self.activeWindow()
        if aw:
            aw.printPreviewFile()
        
    def __showFileMenu(self):
        """
        Private method to set up the file menu.
        """
        self.menuRecentAct.setEnabled(len(self.recent) > 0)
        
    def __showRecentMenu(self):
        """
        Private method to set up recent files menu.
        """
        self.__loadRecent()
        
        self.recentMenu.clear()
        
        idx = 1
        for rs in self.recent:
            if idx < 10:
                formatStr = '&{0:d}. {1}'
            else:
                formatStr = '{0:d}. {1}'
            act = self.recentMenu.addAction(
                formatStr.format(
                    idx,
                    Utilities.compactPath(rs, self.ui.maxMenuFilePathLen)))
            act.setData(rs)
            act.setEnabled(QFileInfo(rs).exists())
            idx += 1
        
        self.recentMenu.addSeparator()
        self.recentMenu.addAction(
            QCoreApplication.translate('ViewManager', '&Clear'),
            self.__clearRecent)
        
    def __openSourceFile(self, act):
        """
        Private method to open a file from the list of recently opened files.
        
        @param act reference to the action that triggered (QAction)
        """
        file = act.data()
        if file:
            self.openSourceFile(file)
        
    def __clearRecent(self):
        """
        Private method to clear the recent files menu.
        """
        self.recent = []
        
    def __showBookmarkedMenu(self):
        """
        Private method to set up bookmarked files menu.
        """
        self.bookmarkedMenu.clear()
        
        for rp in self.bookmarked:
            act = self.bookmarkedMenu.addAction(
                Utilities.compactPath(rp, self.ui.maxMenuFilePathLen))
            act.setData(rp)
            act.setEnabled(QFileInfo(rp).exists())
        
        if len(self.bookmarked):
            self.bookmarkedMenu.addSeparator()
        self.bookmarkedMenu.addAction(
            QCoreApplication.translate('ViewManager', '&Add'),
            self.__addBookmarked)
        self.bookmarkedMenu.addAction(
            QCoreApplication.translate('ViewManager', '&Edit...'),
            self.__editBookmarked)
        self.bookmarkedMenu.addAction(
            QCoreApplication.translate('ViewManager', '&Clear'),
            self.__clearBookmarked)
        
    def __addBookmarked(self):
        """
        Private method to add the current file to the list of bookmarked files.
        """
        an = self.getActiveName()
        if an is not None and an not in self.bookmarked:
            self.bookmarked.append(an)
        
    def __editBookmarked(self):
        """
        Private method to edit the list of bookmarked files.
        """
        from .BookmarkedFilesDialog import BookmarkedFilesDialog
        dlg = BookmarkedFilesDialog(self.bookmarked, self.ui)
        if dlg.exec_() == QDialog.Accepted:
            self.bookmarked = dlg.getBookmarkedFiles()
        
    def __clearBookmarked(self):
        """
        Private method to clear the bookmarked files menu.
        """
        self.bookmarked = []
        
    def projectOpened(self):
        """
        Public slot to handle the projectOpened signal.
        """
        for editor in self.editors:
            editor.projectOpened()
        
        self.__editProjectPwlAct.setEnabled(True)
        self.__editProjectPelAct.setEnabled(True)
    
    def projectClosed(self):
        """
        Public slot to handle the projectClosed signal.
        """
        for editor in self.editors:
            editor.projectClosed()
        
        self.__editProjectPwlAct.setEnabled(False)
        self.__editProjectPelAct.setEnabled(False)
    
    def projectFileRenamed(self, oldfn, newfn):
        """
        Public slot to handle the projectFileRenamed signal.
        
        @param oldfn old filename of the file (string)
        @param newfn new filename of the file (string)
        """
        editor = self.getOpenEditor(oldfn)
        if editor:
            editor.fileRenamed(newfn)
        
    def projectLexerAssociationsChanged(self):
        """
        Public slot to handle changes of the project lexer associations.
        """
        for editor in self.editors:
            editor.projectLexerAssociationsChanged()
        
    def enableEditorsCheckFocusIn(self, enabled):
        """
        Public method to set a flag enabling the editors to perform focus in
        checks.
        
        @param enabled flag indicating focus in checks should be performed
            (boolean)
        """
        self.editorsCheckFocusIn = enabled
        
    def editorsCheckFocusInEnabled(self):
        """
        Public method returning the flag indicating editors should perform
        focus in checks.
        
        @return flag indicating focus in checks should be performed (boolean)
        """
        return self.editorsCheckFocusIn

    def __findFileName(self):
        """
        Private method to handle the search for file action.
        """
        self.ui.showFindFileByNameDialog()
    
    def appFocusChanged(self, old, now):
        """
        Public method to handle the global change of focus.
        
        @param old reference to the widget loosing focus (QWidget)
        @param now reference to the widget gaining focus (QWidget)
        """
        from QScintilla.Shell import Shell
        
        if not isinstance(now, (Editor, Shell)):
            self.editActGrp.setEnabled(False)
            self.copyActGrp.setEnabled(False)
            self.viewActGrp.setEnabled(False)
            self.sbZoom.setEnabled(False)
        else:
            self.sbZoom.setEnabled(True)
            self.sbZoom.setValue(now.getZoom())
        
        if not isinstance(now, (Editor, Shell)) and \
           now is not self.quickFindtextCombo:
            self.searchActGrp.setEnabled(False)
        
        if now is self.quickFindtextCombo:
            self.searchActGrp.setEnabled(True)
        
        if not isinstance(now, (Editor, Shell)):
            self.__lastFocusWidget = old
    
    ##################################################################
    ## Below are the action methods for the edit menu
    ##################################################################
    
    def __editUndo(self):
        """
        Private method to handle the undo action.
        """
        self.activeWindow().undo()
        
    def __editRedo(self):
        """
        Private method to handle the redo action.
        """
        self.activeWindow().redo()
        
    def __editRevert(self):
        """
        Private method to handle the revert action.
        """
        self.activeWindow().revertToUnmodified()
        
    def __editCut(self):
        """
        Private method to handle the cut action.
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            e5App().getObject("Shell").cut()
        else:
            self.activeWindow().cut()
        
    def __editCopy(self):
        """
        Private method to handle the copy action.
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            e5App().getObject("Shell").copy()
        else:
            self.activeWindow().copy()
        
    def __editPaste(self):
        """
        Private method to handle the paste action.
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            e5App().getObject("Shell").paste()
        else:
            self.activeWindow().paste()
        
    def __editDelete(self):
        """
        Private method to handle the delete action.
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            e5App().getObject("Shell").clear()
        else:
            self.activeWindow().clear()
        
    def __editJoin(self):
        """
        Private method to handle the join action.
        """
        self.activeWindow().joinLines()
        
    def __editIndent(self):
        """
        Private method to handle the indent action.
        """
        self.activeWindow().indentLineOrSelection()
        
    def __editUnindent(self):
        """
        Private method to handle the unindent action.
        """
        self.activeWindow().unindentLineOrSelection()
        
    def __editSmartIndent(self):
        """
        Private method to handle the smart indent action.
        """
        self.activeWindow().smartIndentLineOrSelection()
        
    def __editToggleComment(self):
        """
        Private method to handle the toggle comment action.
        """
        self.activeWindow().toggleCommentBlock()
        
    def __editComment(self):
        """
        Private method to handle the comment action.
        """
        self.activeWindow().commentLineOrSelection()
        
    def __editUncomment(self):
        """
        Private method to handle the uncomment action.
        """
        self.activeWindow().uncommentLineOrSelection()
        
    def __editStreamComment(self):
        """
        Private method to handle the stream comment action.
        """
        self.activeWindow().streamCommentLineOrSelection()
        
    def __editBoxComment(self):
        """
        Private method to handle the box comment action.
        """
        self.activeWindow().boxCommentLineOrSelection()
        
    def __editSelectBrace(self):
        """
        Private method to handle the select to brace action.
        """
        self.activeWindow().selectToMatchingBrace()
        
    def __editSelectAll(self):
        """
        Private method to handle the select all action.
        """
        self.activeWindow().selectAll(True)
        
    def __editDeselectAll(self):
        """
        Private method to handle the select all action.
        """
        self.activeWindow().selectAll(False)
        
    def __convertEOL(self):
        """
        Private method to handle the convert line end characters action.
        """
        aw = self.activeWindow()
        aw.convertEols(aw.eolMode())
        
    def __shortenEmptyLines(self):
        """
        Private method to handle the shorten empty lines action.
        """
        self.activeWindow().shortenEmptyLines()
        
    def __editAutoComplete(self):
        """
        Private method to handle the autocomplete action.
        """
        self.activeWindow().autoComplete()
        
    def __editAutoCompleteFromDoc(self):
        """
        Private method to handle the autocomplete from document action.
        """
        self.activeWindow().autoCompleteFromDocument()
        
    def __editAutoCompleteFromAPIs(self):
        """
        Private method to handle the autocomplete from APIs action.
        """
        self.activeWindow().autoCompleteFromAPIs()
        
    def __editAutoCompleteFromAll(self):
        """
        Private method to handle the autocomplete from All action.
        """
        self.activeWindow().autoCompleteFromAll()
        
    def __editorAutoCompletionAPIsAvailable(self, available):
        """
        Private method to handle the availability of API autocompletion signal.
        
        @param available flag indicating the availability of API
        autocompletion (boolean)
        """
        editor = self.sender()
        self.autoCompleteAct.setEnabled(
            editor.canProvideDynamicAutoCompletion())
        self.autoCompleteFromAPIsAct.setEnabled(available)
        self.autoCompleteFromAllAct.setEnabled(available)
        self.calltipsAct.setEnabled(editor.canProvideCallTipps())
        
    def __editShowCallTips(self):
        """
        Private method to handle the calltips action.
        """
        self.activeWindow().callTip()
    
    ##################################################################
    ## Below are the action and utility methods for the search menu
    ##################################################################

    def textForFind(self, getCurrentWord=True):
        """
        Public method to determine the selection or the current word for the
        next find operation.
        
        @param getCurrentWord flag indicating to return the current word, if
            no selected text was found (boolean)
        @return selection or current word (string)
        """
        aw = self.activeWindow()
        if aw is None:
            return ""
        
        return aw.getSearchText(not getCurrentWord)
        
    def getSRHistory(self, key):
        """
        Public method to get the search or replace history list.
        
        @param key list to return (must be 'search' or 'replace')
        @return the requested history list (list of strings)
        """
        return self.srHistory[key]
        
    def __quickSearch(self):
        """
        Private slot to handle the incremental quick search.
        """
        # first we have to check if quick search is active
        # and try to activate it if not
        if self.__quickSearchToolbarVisibility is None:
            self.__quickSearchToolbarVisibility = \
                self.__quickSearchToolbar.isVisible()
        if not self.__quickSearchToolbar.isVisible():
            self.__quickSearchToolbar.show()
        if not self.quickFindtextCombo.lineEdit().hasFocus():
            aw = self.activeWindow()
            self.quickFindtextCombo.lastActive = aw
            if aw:
                self.quickFindtextCombo.lastCursorPos = aw.getCursorPosition()
            else:
                self.quickFindtextCombo.lastCursorPos = None
            tff = self.textForFind(False)
            if tff:
                self.quickFindtextCombo.lineEdit().setText(tff)
            self.quickFindtextCombo.lineEdit().setFocus()
            self.quickFindtextCombo.lineEdit().selectAll()
            self.__quickSearchSetEditColors(False)
        else:
            self.__quickSearchInEditor(True, False)
        
    def __quickSearchFocusIn(self):
        """
        Private method to handle a focus in signal of the quicksearch lineedit.
        """
        self.quickFindtextCombo.lastActive = self.activeWindow()
        
    def __quickSearchEnter(self):
        """
        Private slot to handle the incremental quick search return pressed
        (jump back to text).
        """
        if self.quickFindtextCombo.lastActive:
            self.quickFindtextCombo.lastActive.setFocus()
        if self.__quickSearchToolbarVisibility is not None:
            self.__quickSearchToolbar.setVisible(
                self.__quickSearchToolbarVisibility)
            self.__quickSearchToolbarVisibility = None
        
    def __quickSearchEscape(self):
        """
        Private slot to handle the incremental quick search escape pressed
        (jump back to text).
        """
        if self.quickFindtextCombo.lastActive:
            self.quickFindtextCombo.lastActive.setFocus()
            aw = self.activeWindow()
            if aw:
                aw.hideFindIndicator()
                if self.quickFindtextCombo.lastCursorPos:
                    aw.setCursorPosition(
                        self.quickFindtextCombo.lastCursorPos[0],
                        self.quickFindtextCombo.lastCursorPos[1])
                
        if self.__quickSearchToolbarVisibility is not None:
            self.__quickSearchToolbar.setVisible(
                self.__quickSearchToolbarVisibility)
            self.__quickSearchToolbarVisibility = None
        
    def __quickSearchText(self):
        """
        Private slot to handle the textChanged signal of the quicksearch edit.
        """
        self.__quickSearchInEditor(False, False)
        
    def __quickSearchPrev(self):
        """
        Private slot to handle the quickFindPrev toolbutton action.
        """
        # first we have to check if quick search is active
        # and try to activate it if not
        if self.__quickSearchToolbarVisibility is None:
            self.__quickSearchToolbarVisibility = \
                self.__quickSearchToolbar.isVisible()
        if not self.__quickSearchToolbar.isVisible():
            self.__quickSearchToolbar.show()
        if not self.quickFindtextCombo.lineEdit().hasFocus():
            aw = self.activeWindow()
            self.quickFindtextCombo.lastActive = aw
            if aw:
                self.quickFindtextCombo.lastCursorPos = aw.getCursorPosition()
            else:
                self.quickFindtextCombo.lastCursorPos = None
            tff = self.textForFind(False)
            if tff:
                self.quickFindtextCombo.lineEdit().setText(tff)
            self.quickFindtextCombo.lineEdit().setFocus()
            self.quickFindtextCombo.lineEdit().selectAll()
            self.__quickSearchSetEditColors(False)
        else:
            self.__quickSearchInEditor(True, True)
        
    def __quickSearchMarkOccurrences(self, txt):
        """
        Private method to mark all occurrences of the search text.
        
        @param txt text to search for (string)
        """
        aw = self.activeWindow()
        
        lineFrom = 0
        indexFrom = 0
        lineTo = -1
        indexTo = -1
        
        aw.clearSearchIndicators()
        ok = aw.findFirstTarget(txt, False, False, False,
                                lineFrom, indexFrom, lineTo, indexTo)
        while ok:
            tgtPos, tgtLen = aw.getFoundTarget()
            aw.setSearchIndicator(tgtPos, tgtLen)
            ok = aw.findNextTarget()
        
    def __quickSearchInEditor(self, again, back):
        """
        Private slot to perform a quick search.
        
        @param again flag indicating a repeat of the last search (boolean)
        @param back flag indicating a backwards search operation (boolean)
        """
        aw = self.activeWindow()
        if not aw:
            return
        
        aw.hideFindIndicator()
        
        text = self.quickFindtextCombo.lineEdit().text()
        if not text and again:
                text = self.quickFindtextCombo.lastSearchText
        if not text:
            if Preferences.getEditor("QuickSearchMarkersEnabled"):
                aw.clearSearchIndicators()
            return
        else:
            self.quickFindtextCombo.lastSearchText = text
        
        if Preferences.getEditor("QuickSearchMarkersEnabled"):
            self.__quickSearchMarkOccurrences(text)
        
        lineFrom, indexFrom, lineTo, indexTo = aw.getSelection()
        cline, cindex = aw.getCursorPosition()
        if again:
            if back:
                if indexFrom != 0:
                    index = indexFrom - 1
                    line = lineFrom
                elif lineFrom == 0:
                    return
                else:
                    line = lineFrom - 1
                    index = aw.lineLength(line)
                ok = aw.findFirst(text, False, False, False, True, False,
                                  line, index)
            else:
                ok = aw.findFirst(text, False, False, False, True, not back,
                                  cline, cindex)
        else:
            ok = aw.findFirst(text, False, False, False, True, not back,
                              lineFrom, indexFrom)
        if ok:
            sline, sindex, eline, eindex = aw.getSelection()
            aw.showFindIndicator(sline, sindex, eline, eindex)
        self.__quickSearchSetEditColors(not ok)
    
    def __quickSearchSetEditColors(self, error):
        """
        Private method to set the quick search edit colors.
        
        @param error flag indicating an error (boolean)
        """
        if error:
            palette = self.quickFindtextCombo.lineEdit().palette()
            palette.setColor(QPalette.Base, QColor("red"))
            palette.setColor(QPalette.Text, QColor("white"))
            self.quickFindtextCombo.lineEdit().setPalette(palette)
        else:
            palette = self.quickFindtextCombo.lineEdit().palette()
            palette.setColor(
                QPalette.Base,
                self.quickFindtextCombo.palette().color(QPalette.Base))
            palette.setColor(
                QPalette.Text,
                self.quickFindtextCombo.palette().color(QPalette.Text))
            self.quickFindtextCombo.lineEdit().setPalette(palette)
    
    def __quickSearchExtend(self):
        """
        Private method to handle the quicksearch extend action.
        """
        aw = self.activeWindow()
        if aw is None:
            return
        
        txt = self.quickFindtextCombo.lineEdit().text()
        if not txt:
            return
        
        line, index = aw.getCursorPosition()
        text = aw.text(line)
        
        reg = QRegExp('[^\w_]')
        end = reg.indexIn(text, index)
        if end > index:
            ext = text[index:end]
            txt += ext
            self.quickFindtextCombo.lineEdit().setText(txt)
        
    def __search(self):
        """
        Private method to handle the search action.
        """
        self.__replaceWidget.hide()
        self.__searchWidget.show()
        self.__searchWidget.show(self.textForFind())
        
    def __replace(self):
        """
        Private method to handle the replace action.
        """
        self.__searchWidget.hide()
        self.__replaceWidget.show(self.textForFind())
        
    def __findNextWord(self):
        """
        Private slot to find the next occurrence of the current word of the
        current editor.
        """
        self.activeWindow().searchCurrentWordForward()
        
    def __findPrevWord(self):
        """
        Private slot to find the previous occurrence of the current word of
        the current editor.
        """
        self.activeWindow().searchCurrentWordBackward()
        
    def __searchClearMarkers(self):
        """
        Private method to clear the search markers of the active window.
        """
        self.activeWindow().clearSearchIndicators()
        
    def __goto(self):
        """
        Private method to handle the goto action.
        """
        from QScintilla.GotoDialog import GotoDialog
        
        aw = self.activeWindow()
        lines = aw.lines()
        curLine = aw.getCursorPosition()[0] + 1
        dlg = GotoDialog(lines, curLine, self.ui, None, True)
        if dlg.exec_() == QDialog.Accepted:
            aw.gotoLine(dlg.getLinenumber())
        
    def __gotoBrace(self):
        """
        Private method to handle the goto brace action.
        """
        self.activeWindow().moveToMatchingBrace()
        
    def __gotoLastEditPosition(self):
        """
        Private method to move the cursor to the last edit position.
        """
        self.activeWindow().gotoLastEditPosition()
        
    def __lastEditPositionAvailable(self):
        """
        Private slot to handle the lastEditPositionAvailable signal of an
        editor.
        """
        self.gotoLastEditAct.setEnabled(True)
        
    def __gotoNextMethodClass(self):
        """
        Private slot to go to the next Python/Ruby method or class definition.
        """
        self.activeWindow().gotoMethodClass(False)
        
    def __gotoPreviousMethodClass(self):
        """
        Private slot to go to the previous Python/Ruby method or class
        definition.
        """
        self.activeWindow().gotoMethodClass(True)
        
    def __searchFiles(self):
        """
        Private method to handle the search in files action.
        """
        self.ui.showFindFilesDialog(self.textForFind())
        
    def __replaceFiles(self):
        """
        Private method to handle the replace in files action.
        """
        self.ui.showReplaceFilesDialog(self.textForFind())
        
    def __searchOpenFiles(self):
        """
        Private method to handle the search in open files action.
        """
        self.ui.showFindFilesDialog(self.textForFind(), openFiles=True)
        
    def __replaceOpenFiles(self):
        """
        Private method to handle the replace in open files action.
        """
        self.ui.showReplaceFilesDialog(self.textForFind(), openFiles=True)
    
    ##################################################################
    ## Below are the action methods for the view menu
    ##################################################################
    
    def __zoomIn(self):
        """
        Private method to handle the zoom in action.
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            e5App().getObject("Shell").zoomIn()
        else:
            aw = self.activeWindow()
            if aw:
                aw.zoomIn()
                self.sbZoom.setValue(aw.getZoom())
        
    def __zoomOut(self):
        """
        Private method to handle the zoom out action.
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            e5App().getObject("Shell").zoomOut()
        else:
            aw = self.activeWindow()
            if aw:
                aw.zoomOut()
                self.sbZoom.setValue(aw.getZoom())
        
    def __zoomReset(self):
        """
        Private method to reset the zoom factor.
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            e5App().getObject("Shell").zoomTo(0)
        else:
            aw = self.activeWindow()
            if aw:
                aw.zoomTo(0)
                self.sbZoom.setValue(aw.getZoom())
        
    def __zoom(self):
        """
        Private method to handle the zoom action.
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            aw = e5App().getObject("Shell")
        else:
            aw = self.activeWindow()
        if aw:
            from QScintilla.ZoomDialog import ZoomDialog
            dlg = ZoomDialog(aw.getZoom(), self.ui, None, True)
            if dlg.exec_() == QDialog.Accepted:
                value = dlg.getZoomSize()
                self.__zoomTo(value)
        
    def __zoomTo(self, value):
        """
        Private slot to zoom to a given value.
        
        @param value zoom value to be set (integer)
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            aw = e5App().getObject("Shell")
        else:
            aw = self.activeWindow()
        if aw:
            aw.zoomTo(value)
            self.sbZoom.setValue(aw.getZoom())
        
    def zoomValueChanged(self, value):
        """
        Public slot to handle changes of the zoom value.
        
        @param value new zoom value (integer)
        """
        if QApplication.focusWidget() == e5App().getObject("Shell"):
            aw = e5App().getObject("Shell")
        else:
            aw = self.activeWindow()
        if aw and aw == self.sender():
            self.sbZoom.setValue(value)
        
    def __toggleAll(self):
        """
        Private method to handle the toggle all folds action.
        """
        aw = self.activeWindow()
        if aw:
            aw.foldAll()
        
    def __toggleAllChildren(self):
        """
        Private method to handle the toggle all folds (including children)
        action.
        """
        aw = self.activeWindow()
        if aw:
            aw.foldAll(True)
        
    def __toggleCurrent(self):
        """
        Private method to handle the toggle current fold action.
        """
        aw = self.activeWindow()
        if aw:
            line, index = aw.getCursorPosition()
            aw.foldLine(line)
        
    def __newDocumentView(self):
        """
        Private method to open a new view of the current editor.
        """
        aw = self.activeWindow()
        if aw:
            self.newEditorView(aw.getFileName(), aw, aw.getFileType())
        
    def __newDocumentSplitView(self):
        """
        Private method to open a new view of the current editor in a new split.
        """
        aw = self.activeWindow()
        if aw:
            self.addSplit()
            self.newEditorView(aw.getFileName(), aw, aw.getFileType())
        
    def __splitView(self):
        """
        Private method to handle the split view action.
        """
        self.addSplit()
        
    def __splitOrientation(self, checked):
        """
        Private method to handle the split orientation action.
        
        @param checked flag indicating the checked state of the action
            (boolean). True means splitting horizontally.
        """
        if checked:
            self.setSplitOrientation(Qt.Horizontal)
            self.splitViewAct.setIcon(
                UI.PixmapCache.getIcon("splitHorizontal.png"))
            self.splitRemoveAct.setIcon(
                UI.PixmapCache.getIcon("remsplitHorizontal.png"))
            self.newDocumentSplitViewAct.setIcon(
                UI.PixmapCache.getIcon("splitHorizontal.png"))
        else:
            self.setSplitOrientation(Qt.Vertical)
            self.splitViewAct.setIcon(
                UI.PixmapCache.getIcon("splitVertical.png"))
            self.splitRemoveAct.setIcon(
                UI.PixmapCache.getIcon("remsplitVertical.png"))
            self.newDocumentSplitViewAct.setIcon(
                UI.PixmapCache.getIcon("splitVertical.png"))
        Preferences.setUI("SplitOrientationVertical", checked)
    
    def __previewEditor(self, checked):
        """
        Private slot to handle a change of the preview selection state.
        
        @param checked state of the action (boolean)
        """
        Preferences.setUI("ShowFilePreview", checked)
        self.previewStateChanged.emit(checked)
    
    ##################################################################
    ## Below are the action methods for the macro menu
    ##################################################################
    
    def __macroStartRecording(self):
        """
        Private method to handle the start macro recording action.
        """
        self.activeWindow().macroRecordingStart()
        
    def __macroStopRecording(self):
        """
        Private method to handle the stop macro recording action.
        """
        self.activeWindow().macroRecordingStop()
        
    def __macroRun(self):
        """
        Private method to handle the run macro action.
        """
        self.activeWindow().macroRun()
        
    def __macroDelete(self):
        """
        Private method to handle the delete macro action.
        """
        self.activeWindow().macroDelete()
        
    def __macroLoad(self):
        """
        Private method to handle the load macro action.
        """
        self.activeWindow().macroLoad()
        
    def __macroSave(self):
        """
        Private method to handle the save macro action.
        """
        self.activeWindow().macroSave()
    
    ##################################################################
    ## Below are the action methods for the bookmarks menu
    ##################################################################
    
    def __toggleBookmark(self):
        """
        Private method to handle the toggle bookmark action.
        """
        self.activeWindow().menuToggleBookmark()
        
    def __nextBookmark(self):
        """
        Private method to handle the next bookmark action.
        """
        self.activeWindow().nextBookmark()
    
    def __previousBookmark(self):
        """
        Private method to handle the previous bookmark action.
        """
        self.activeWindow().previousBookmark()
    
    def __clearAllBookmarks(self):
        """
        Private method to handle the clear all bookmarks action.
        """
        for editor in self.editors:
            editor.clearBookmarks()
        
        self.bookmarkNextAct.setEnabled(False)
        self.bookmarkPreviousAct.setEnabled(False)
        self.bookmarkClearAct.setEnabled(False)
    
    def __showBookmarkMenu(self):
        """
        Private method to set up the bookmark menu.
        """
        bookmarksFound = 0
        filenames = self.getOpenFilenames()
        for filename in filenames:
            editor = self.getOpenEditor(filename)
            bookmarksFound = len(editor.getBookmarks()) > 0
            if bookmarksFound:
                self.menuBookmarksAct.setEnabled(True)
                return
        self.menuBookmarksAct.setEnabled(False)
        
    def __showBookmarksMenu(self):
        """
        Private method to handle the show bookmarks menu signal.
        """
        self.bookmarksMenu.clear()
        
        filenames = self.getOpenFilenames()
        for filename in sorted(filenames):
            editor = self.getOpenEditor(filename)
            for bookmark in editor.getBookmarks():
                bmSuffix = " : {0:d}".format(bookmark)
                act = self.bookmarksMenu.addAction(
                    "{0}{1}".format(
                        Utilities.compactPath(
                            filename,
                            self.ui.maxMenuFilePathLen - len(bmSuffix)),
                        bmSuffix))
                act.setData([filename, bookmark])
        
    def __bookmarkSelected(self, act):
        """
        Private method to handle the bookmark selected signal.
        
        @param act reference to the action that triggered (QAction)
        """
        bmList = act.data()
        filename = bmList[0]
        line = bmList[1]
        self.openSourceFile(filename, line)
        
    def __bookmarkToggled(self, editor):
        """
        Private slot to handle the bookmarkToggled signal.
        
        It checks some bookmark actions and reemits the signal.
        
        @param editor editor that sent the signal
        """
        if editor.hasBookmarks():
            self.bookmarkNextAct.setEnabled(True)
            self.bookmarkPreviousAct.setEnabled(True)
            self.bookmarkClearAct.setEnabled(True)
        else:
            self.bookmarkNextAct.setEnabled(False)
            self.bookmarkPreviousAct.setEnabled(False)
            self.bookmarkClearAct.setEnabled(False)
        self.bookmarkToggled.emit(editor)
        
    def __gotoSyntaxError(self):
        """
        Private method to handle the goto syntax error action.
        """
        self.activeWindow().gotoSyntaxError()
        
    def __clearAllSyntaxErrors(self):
        """
        Private method to handle the clear all syntax errors action.
        """
        for editor in self.editors:
            editor.clearSyntaxError()
        
    def _syntaxErrorToggled(self, editor):
        """
        Protected slot to handle the syntaxerrorToggled signal.
        
        It checks some syntax error actions and reemits the signal.
        
        @param editor editor that sent the signal
        """
        if editor.hasSyntaxErrors():
            self.syntaxErrorGotoAct.setEnabled(True)
            self.syntaxErrorClearAct.setEnabled(True)
        else:
            self.syntaxErrorGotoAct.setEnabled(False)
            self.syntaxErrorClearAct.setEnabled(False)
        if editor.hasWarnings():
            self.warningsNextAct.setEnabled(True)
            self.warningsPreviousAct.setEnabled(True)
            self.warningsClearAct.setEnabled(True)
        else:
            self.warningsNextAct.setEnabled(False)
            self.warningsPreviousAct.setEnabled(False)
            self.warningsClearAct.setEnabled(False)
        self.syntaxerrorToggled.emit(editor)
        
    def __nextWarning(self):
        """
        Private method to handle the next warning action.
        """
        self.activeWindow().nextWarning()
        
    def __previousWarning(self):
        """
        Private method to handle the previous warning action.
        """
        self.activeWindow().previousWarning()
        
    def __clearAllWarnings(self):
        """
        Private method to handle the clear all warnings action.
        """
        for editor in self.editors:
            editor.clearWarnings()
        
    def __nextUncovered(self):
        """
        Private method to handle the next uncovered action.
        """
        self.activeWindow().nextUncovered()
        
    def __previousUncovered(self):
        """
        Private method to handle the previous uncovered action.
        """
        self.activeWindow().previousUncovered()
        
    def __coverageMarkersShown(self, shown):
        """
        Private slot to handle the coverageMarkersShown signal.
        
        @param shown flag indicating whether the markers were shown or cleared
        """
        if shown:
            self.notcoveredNextAct.setEnabled(True)
            self.notcoveredPreviousAct.setEnabled(True)
        else:
            self.notcoveredNextAct.setEnabled(False)
            self.notcoveredPreviousAct.setEnabled(False)
        
    def __taskMarkersUpdated(self, editor):
        """
        Private slot to handle the taskMarkersUpdated signal.
        
        @param editor editor that sent the signal
        """
        if editor.hasTaskMarkers():
            self.taskNextAct.setEnabled(True)
            self.taskPreviousAct.setEnabled(True)
        else:
            self.taskNextAct.setEnabled(False)
            self.taskPreviousAct.setEnabled(False)
        
    def __nextTask(self):
        """
        Private method to handle the next task action.
        """
        self.activeWindow().nextTask()
        
    def __previousTask(self):
        """
        Private method to handle the previous task action.
        """
        self.activeWindow().previousTask()
        
    def __changeMarkersUpdated(self, editor):
        """
        Private slot to handle the changeMarkersUpdated signal.
        
        @param editor editor that sent the signal
        """
        if editor.hasChangeMarkers():
            self.changeNextAct.setEnabled(True)
            self.changePreviousAct.setEnabled(True)
        else:
            self.changeNextAct.setEnabled(False)
            self.changePreviousAct.setEnabled(False)
        
    def __nextChange(self):
        """
        Private method to handle the next change action.
        """
        self.activeWindow().nextChange()
        
    def __previousChange(self):
        """
        Private method to handle the previous change action.
        """
        self.activeWindow().previousChange()
    
    ##################################################################
    ## Below are the action methods for the spell checking functions
    ##################################################################
    
    def __showEditSpellingMenu(self):
        """
        Private method to set up the edit dictionaries menu.
        """
        proj = e5App().getObject("Project")
        projetOpen = proj.isOpen()
        pwl = e5App().getObject("Project").getProjectDictionaries()[0]
        self.__editProjectPwlAct.setEnabled(projetOpen and bool(pwl))
        pel = e5App().getObject("Project").getProjectDictionaries()[1]
        self.__editProjectPelAct.setEnabled(projetOpen and bool(pel))
        
        from QScintilla.SpellChecker import SpellChecker
        pwl = SpellChecker.getUserDictionaryPath()
        self.__editUserPwlAct.setEnabled(bool(pwl))
        pel = SpellChecker.getUserDictionaryPath(True)
        self.__editUserPelAct.setEnabled(bool(pel))
    
    def __setAutoSpellChecking(self):
        """
        Private slot to set the automatic spell checking of all editors.
        """
        enabled = self.autoSpellCheckAct.isChecked()
        Preferences.setEditor("AutoSpellCheckingEnabled", enabled)
        for editor in self.editors:
            editor.setAutoSpellChecking()
    
    def __spellCheck(self):
        """
        Private slot to perform a spell check of the current editor.
        """
        aw = self.activeWindow()
        if aw:
            aw.checkSpelling()
    
    def __editProjectPWL(self):
        """
        Private slot to edit the project word list.
        """
        pwl = e5App().getObject("Project").getProjectDictionaries()[0]
        self.__editSpellingDictionary(pwl)
    
    def __editProjectPEL(self):
        """
        Private slot to edit the project exception list.
        """
        pel = e5App().getObject("Project").getProjectDictionaries()[1]
        self.__editSpellingDictionary(pel)
    
    def __editUserPWL(self):
        """
        Private slot to edit the user word list.
        """
        from QScintilla.SpellChecker import SpellChecker
        pwl = SpellChecker.getUserDictionaryPath()
        self.__editSpellingDictionary(pwl)
    
    def __editUserPEL(self):
        """
        Private slot to edit the user exception list.
        """
        from QScintilla.SpellChecker import SpellChecker
        pel = SpellChecker.getUserDictionaryPath(True)
        self.__editSpellingDictionary(pel)
    
    def __editSpellingDictionary(self, dictionaryFile):
        """
        Private slot to edit the given spelling dictionary.
        
        @param dictionaryFile file name of the dictionary to edit (string)
        """
        if os.path.exists(dictionaryFile):
            try:
                f = open(dictionaryFile, "r", encoding="utf-8")
                data = f.read()
                f.close()
            except (IOError, OSError) as err:
                E5MessageBox.critical(
                    self.ui,
                    QCoreApplication.translate(
                        'ViewManager', "Edit Spelling Dictionary"),
                    QCoreApplication.translate(
                        'ViewManager',
                        """<p>The spelling dictionary file <b>{0}</b> could"""
                        """ not be read.</p><p>Reason: {1}</p>""").format(
                        dictionaryFile, str(err)))
                return
            
            fileInfo = dictionaryFile if len(dictionaryFile) < 40 \
                else "...{0}".format(dictionaryFile[-40:])
            from QScintilla.SpellingDictionaryEditDialog import \
                SpellingDictionaryEditDialog
            dlg = SpellingDictionaryEditDialog(
                data,
                QCoreApplication.translate('ViewManager', "Editing {0}")
                .format(fileInfo),
                self.ui)
            if dlg.exec_() == QDialog.Accepted:
                data = dlg.getData()
                try:
                    f = open(dictionaryFile, "w", encoding="utf-8")
                    f.write(data)
                    f.close()
                except (IOError, OSError) as err:
                    E5MessageBox.critical(
                        self.ui,
                        QCoreApplication.translate(
                            'ViewManager', "Edit Spelling Dictionary"),
                        QCoreApplication.translate(
                            'ViewManager',
                            """<p>The spelling dictionary file <b>{0}</b>"""
                            """ could not be written.</p>"""
                            """<p>Reason: {1}</p>""").format(
                            dictionaryFile, str(err)))
                    return
                
                if self.ui.notificationsEnabled():
                    self.ui.showNotification(
                        UI.PixmapCache.getPixmap("spellchecking48.png"),
                        QCoreApplication.translate(
                            'ViewManager', "Edit Spelling Dictionary"),
                        QCoreApplication.translate(
                            'ViewManager',
                            "The spelling dictionary was saved successfully."))
    
    ##################################################################
    ## Below are general utility methods
    ##################################################################
    
    def handleResetUI(self):
        """
        Public slot to handle the resetUI signal.
        """
        editor = self.activeWindow()
        if editor is None:
            self.__setSbFile()
        else:
            line, pos = editor.getCursorPosition()
            enc = editor.getEncoding()
            lang = editor.getLanguage()
            eol = editor.getEolIndicator()
            zoom = editor.getZoom()
            self.__setSbFile(editor.getFileName(), line + 1, pos, enc, lang,
                             eol, zoom)
        
    def closeViewManager(self):
        """
        Public method to shutdown the viewmanager.
        
        If it cannot close all editor windows, it aborts the shutdown process.
        
        @return flag indicating success (boolean)
        """
        e5App().focusChanged.disconnect(self.appFocusChanged)
        
        self.closeAllWindows()
        
        # save the list of recently opened projects
        self.__saveRecent()
        
        # save the list of recently opened projects
        Preferences.Prefs.settings.setValue(
            'Bookmarked/Sources', self.bookmarked)
        
        if len(self.editors):
            res = False
        else:
            res = True
        
        if not res:
            e5App().focusChanged.connect(self.appFocusChanged)
        
        return res
        
    def __lastEditorClosed(self):
        """
        Private slot to handle the lastEditorClosed signal.
        """
        self.closeActGrp.setEnabled(False)
        self.saveActGrp.setEnabled(False)
        self.exportersMenuAct.setEnabled(False)
        self.printAct.setEnabled(False)
        if self.printPreviewAct:
            self.printPreviewAct.setEnabled(False)
        self.editActGrp.setEnabled(False)
        self.searchActGrp.setEnabled(False)
        self.quickFindtextCombo.setEnabled(False)
        self.viewActGrp.setEnabled(False)
        self.viewFoldActGrp.setEnabled(False)
        self.unhighlightAct.setEnabled(False)
        self.newDocumentViewAct.setEnabled(False)
        self.newDocumentSplitViewAct.setEnabled(False)
        self.splitViewAct.setEnabled(False)
        self.splitOrientationAct.setEnabled(False)
        self.previewAct.setEnabled(True)
        self.macroActGrp.setEnabled(False)
        self.bookmarkActGrp.setEnabled(False)
        self.__enableSpellingActions()
        self.__setSbFile(zoom=0)
        
        # remove all split views, if this is supported
        if self.canSplit():
            while self.removeSplit():
                pass
        
        # stop the autosave timer
        if self.autosaveTimer.isActive():
            self.autosaveTimer.stop()
        
        # hide search and replace widgets
        self.__searchWidget.hide()
        self.__replaceWidget.hide()
        
    def __editorOpened(self):
        """
        Private slot to handle the editorOpened signal.
        """
        self.closeActGrp.setEnabled(True)
        self.saveActGrp.setEnabled(True)
        self.exportersMenuAct.setEnabled(True)
        self.printAct.setEnabled(True)
        if self.printPreviewAct:
            self.printPreviewAct.setEnabled(True)
        self.editActGrp.setEnabled(True)
        self.searchActGrp.setEnabled(True)
        self.quickFindtextCombo.setEnabled(True)
        self.viewActGrp.setEnabled(True)
        self.viewFoldActGrp.setEnabled(True)
        self.unhighlightAct.setEnabled(True)
        self.newDocumentViewAct.setEnabled(True)
        if self.canSplit():
            self.newDocumentSplitViewAct.setEnabled(True)
            self.splitViewAct.setEnabled(True)
            self.splitOrientationAct.setEnabled(True)
        self.macroActGrp.setEnabled(True)
        self.bookmarkActGrp.setEnabled(True)
        self.__enableSpellingActions()
        
        # activate the autosave timer
        if not self.autosaveTimer.isActive() and \
           self.autosaveInterval > 0:
            self.autosaveTimer.start(self.autosaveInterval * 60000)
        
    def __autosave(self):
        """
        Private slot to save the contents of all editors automatically.
        
        Only named editors will be saved by the autosave timer.
        """
        for editor in self.editors:
            if editor.shouldAutosave():
                ok = editor.saveFile()
                if ok:
                    self.setEditorName(editor, editor.getFileName())
        
        # restart autosave timer
        if self.autosaveInterval > 0:
            self.autosaveTimer.start(self.autosaveInterval * 60000)
        
    def _checkActions(self, editor, setSb=True):
        """
        Protected slot to check some actions for their enable/disable status
        and set the statusbar info.
        
        @param editor editor window
        @param setSb flag indicating an update of the status bar is wanted
            (boolean)
        """
        if editor is not None:
            self.saveAct.setEnabled(editor.isModified())
            self.revertAct.setEnabled(editor.isModified())
            
            self.undoAct.setEnabled(editor.isUndoAvailable())
            self.redoAct.setEnabled(editor.isRedoAvailable())
            self.gotoLastEditAct.setEnabled(
                editor.isLastEditPositionAvailable())
            
            lex = editor.getLexer()
            if lex is not None:
                self.commentAct.setEnabled(lex.canBlockComment())
                self.uncommentAct.setEnabled(lex.canBlockComment())
                self.streamCommentAct.setEnabled(lex.canStreamComment())
                self.boxCommentAct.setEnabled(lex.canBoxComment())
            else:
                self.commentAct.setEnabled(False)
                self.uncommentAct.setEnabled(False)
                self.streamCommentAct.setEnabled(False)
                self.boxCommentAct.setEnabled(False)
            
            if editor.hasBookmarks():
                self.bookmarkNextAct.setEnabled(True)
                self.bookmarkPreviousAct.setEnabled(True)
                self.bookmarkClearAct.setEnabled(True)
            else:
                self.bookmarkNextAct.setEnabled(False)
                self.bookmarkPreviousAct.setEnabled(False)
                self.bookmarkClearAct.setEnabled(False)
            
            if editor.hasSyntaxErrors():
                self.syntaxErrorGotoAct.setEnabled(True)
                self.syntaxErrorClearAct.setEnabled(True)
            else:
                self.syntaxErrorGotoAct.setEnabled(False)
                self.syntaxErrorClearAct.setEnabled(False)
            
            if editor.hasWarnings():
                self.warningsNextAct.setEnabled(True)
                self.warningsPreviousAct.setEnabled(True)
                self.warningsClearAct.setEnabled(True)
            else:
                self.warningsNextAct.setEnabled(False)
                self.warningsPreviousAct.setEnabled(False)
                self.warningsClearAct.setEnabled(False)
            
            if editor.hasCoverageMarkers():
                self.notcoveredNextAct.setEnabled(True)
                self.notcoveredPreviousAct.setEnabled(True)
            else:
                self.notcoveredNextAct.setEnabled(False)
                self.notcoveredPreviousAct.setEnabled(False)
            
            if editor.hasTaskMarkers():
                self.taskNextAct.setEnabled(True)
                self.taskPreviousAct.setEnabled(True)
            else:
                self.taskNextAct.setEnabled(False)
                self.taskPreviousAct.setEnabled(False)
            
            if editor.hasChangeMarkers():
                self.changeNextAct.setEnabled(True)
                self.changePreviousAct.setEnabled(True)
            else:
                self.changeNextAct.setEnabled(False)
                self.changePreviousAct.setEnabled(False)
            
            if editor.canAutoCompleteFromAPIs():
                self.autoCompleteFromAPIsAct.setEnabled(True)
                self.autoCompleteFromAllAct.setEnabled(True)
            else:
                self.autoCompleteFromAPIsAct.setEnabled(False)
                self.autoCompleteFromAllAct.setEnabled(False)
            self.autoCompleteAct.setEnabled(
                editor.canProvideDynamicAutoCompletion())
            self.calltipsAct.setEnabled(editor.canProvideCallTipps())
            
            if editor.isPyFile() or editor.isRubyFile():
                self.gotoPreviousDefAct.setEnabled(True)
                self.gotoNextDefAct.setEnabled(True)
            else:
                self.gotoPreviousDefAct.setEnabled(False)
                self.gotoNextDefAct.setEnabled(False)
            
            self.sortAct.setEnabled(editor.selectionIsRectangle())
            enable = editor.hasSelection()
            self.editUpperCaseAct.setEnabled(enable)
            self.editLowerCaseAct.setEnabled(enable)
            
            if setSb:
                line, pos = editor.getCursorPosition()
                enc = editor.getEncoding()
                lang = editor.getLanguage()
                eol = editor.getEolIndicator()
                zoom = editor.getZoom()
                self.__setSbFile(
                    editor.getFileName(), line + 1, pos, enc, lang, eol, zoom)
            
            self.checkActions.emit(editor)
        
        saveAllEnable = False
        for editor in self.editors:
            if editor.isModified():
                saveAllEnable = True
        self.saveAllAct.setEnabled(saveAllEnable)
        
    def preferencesChanged(self):
        """
        Public slot to handle the preferencesChanged signal.
        
        This method performs the following actions
            <ul>
            <li>reread the colours for the syntax highlighting</li>
            <li>reloads the already created API objetcs</li>
            <li>starts or stops the autosave timer</li>
            <li><b>Note</b>: changes in viewmanager type are activated
              on an application restart.</li>
            </ul>
        """
        # reload the APIs
        self.apisManager.reloadAPIs()
        
        # reload editor settings
        for editor in self.editors:
            zoom = editor.getZoom()
            editor.readSettings()
            editor.zoomTo(zoom)
        
        # reload the autosave timer setting
        self.autosaveInterval = Preferences.getEditor("AutosaveInterval")
        if len(self.editors):
            if self.autosaveTimer.isActive() and \
               self.autosaveInterval == 0:
                self.autosaveTimer.stop()
            elif not self.autosaveTimer.isActive() and \
                    self.autosaveInterval > 0:
                self.autosaveTimer.start(self.autosaveInterval * 60000)
        
        self.__enableSpellingActions()
        
    def __editorSaved(self, fn):
        """
        Private slot to handle the editorSaved signal.
        
        It simply reemits the signal.
        
        @param fn filename of the saved editor (string)
        """
        self.editorSaved.emit(fn)
        editor = self.sender()
        if editor:
            self.editorSavedEd.emit(editor)
        
    def __editorRenamed(self, fn):
        """
        Private slot to handle the editorRenamed signal.
        
        It simply reemits the signal.
        
        @param fn filename of the renamed editor (string)
        """
        self.editorRenamed.emit(fn)
        editor = self.sender()
        if editor:
            self.editorRenamedEd.emit(editor)
        
    def __cursorChanged(self, fn, line, pos):
        """
        Private slot to handle the cursorChanged signal.
        
        It emits the signal cursorChanged with parameter editor.
        
        @param fn filename (string)
        @param line line number of the cursor (int)
        @param pos position in line of the cursor (int)
        """
        editor = self.getOpenEditor(fn)
        if editor is None:
            editor = self.sender()
        
        if editor is not None:
            enc = editor.getEncoding()
            lang = editor.getLanguage()
            eol = editor.getEolIndicator()
        else:
            enc = None
            lang = None
            eol = None
        self.__setSbFile(fn, line, pos, enc, lang, eol)
        self.cursorChanged.emit(editor)
        
    def __breakpointToggled(self, editor):
        """
        Private slot to handle the breakpointToggled signal.
        
        It simply reemits the signal.
        
        @param editor editor that sent the signal
        """
        self.breakpointToggled.emit(editor)
        
    def getActions(self, type):
        """
        Public method to get a list of all actions.
        
        @param type string denoting the action set to get.
                It must be one of "edit", "file", "search",
                "view", "window", "macro", "bookmark" or
                "spelling".
        @return list of all actions (list of E5Action)
        """
        try:
            return self.__actions[type][:]
        except KeyError:
            return []
        
    def __editorCommand(self, cmd):
        """
        Private method to send an editor command to the active window.
        
        @param cmd the scintilla command to be sent
        """
        focusWidget = QApplication.focusWidget()
        if focusWidget == e5App().getObject("Shell"):
            e5App().getObject("Shell").editorCommand(cmd)
        elif focusWidget == self.quickFindtextCombo:
            self.quickFindtextCombo._editor.editorCommand(cmd)
        else:
            aw = self.activeWindow()
            if aw:
                aw.editorCommand(cmd)
        
    def __newLineBelow(self):
        """
        Private method to insert a new line below the current one even if
        cursor is not at the end of the line.
        """
        focusWidget = QApplication.focusWidget()
        if focusWidget == e5App().getObject("Shell") or \
           focusWidget == self.quickFindtextCombo:
            return
        else:
            aw = self.activeWindow()
            if aw:
                aw.newLineBelow()
        
    def __editorConfigChanged(self):
        """
        Private slot to handle changes of an editor's configuration.
        """
        editor = self.sender()
        fn = editor.getFileName()
        line, pos = editor.getCursorPosition()
        enc = editor.getEncoding()
        lang = editor.getLanguage()
        eol = editor.getEolIndicator()
        zoom = editor.getZoom()
        self.__setSbFile(
            fn, line + 1, pos, encoding=enc, language=lang, eol=eol, zoom=zoom)
        self._checkActions(editor, False)
    
    def __editorSelectionChanged(self):
        """
        Private slot to handle changes of the current editors selection.
        """
        editor = self.sender()
        if editor:
            self.sortAct.setEnabled(editor.selectionIsRectangle())
            enable = editor.hasSelection()
            self.editUpperCaseAct.setEnabled(enable)
            self.editLowerCaseAct.setEnabled(enable)
        else:
            self.sortAct.setEnabled(False)
    
    def __editSortSelectedLines(self):
        """
        Private slot to sort the selected lines.
        """
        editor = self.activeWindow()
        if editor:
            editor.sortLines()
    
    ##################################################################
    ## Below are protected utility methods
    ##################################################################
    
    def _getOpenStartDir(self):
        """
        Protected method to return the starting directory for a file open
        dialog.
        
        The appropriate starting directory is calculated
        using the following search order, until a match is found:<br />
            1: Directory of currently active editor<br />
            2: Directory of currently active Project<br />
            3: CWD
        
        @return name of directory to start (string)
        """
        # if we have an active source, return its path
        if self.activeWindow() is not None and \
           self.activeWindow().getFileName():
            return os.path.dirname(self.activeWindow().getFileName())
        
        # check, if there is an active project and return its path
        elif e5App().getObject("Project").isOpen():
            return e5App().getObject("Project").ppath
        
        else:
            return Preferences.getMultiProject("Workspace") or \
                Utilities.getHomeDir()
        
    def _getOpenFileFilter(self):
        """
        Protected method to return the active filename filter for a file open
        dialog.
        
        The appropriate filename filter is determined by file extension of
        the currently active editor.
        
        @return name of the filename filter (string) or None
        """
        if self.activeWindow() is not None and \
           self.activeWindow().getFileName():
            ext = os.path.splitext(self.activeWindow().getFileName())[1]
            rx = QRegExp(".*\*\.{0}[ )].*".format(ext[1:]))
            import QScintilla.Lexers
            filters = QScintilla.Lexers.getOpenFileFiltersList()
            index = -1
            for i in range(len(filters)):
                if rx.exactMatch(filters[i]):
                    index = i
                    break
            if index == -1:
                return Preferences.getEditor("DefaultOpenFilter")
            else:
                return filters[index]
        else:
            return Preferences.getEditor("DefaultOpenFilter")
    
    ##################################################################
    ## Below are API handling methods
    ##################################################################
    
    def getAPIsManager(self):
        """
        Public method to get a reference to the APIs manager.

        @return the APIs manager object (eric6.QScintilla.APIsManager)
        """
        return self.apisManager
    
    #######################################################################
    ## Cooperation related methods
    #######################################################################
    
    def setCooperationClient(self, client):
        """
        Public method to set a reference to the cooperation client.
        
        @param client reference to the cooperation client (CooperationClient)
        """
        self.__cooperationClient = client
    
    def isConnected(self):
        """
        Public method to check the connection status of the IDE.
        
        @return flag indicating the connection status (boolean)
        """
        return self.__cooperationClient.hasConnections()
    
    def send(self, fileName, message):
        """
        Public method to send an editor command to remote editors.
        
        @param fileName file name of the editor (string)
        @param message command message to be sent (string)
        """
        project = e5App().getObject("Project")
        if project.isProjectFile(fileName):
            self.__cooperationClient.sendEditorCommand(
                project.getHash(),
                project.getRelativeUniversalPath(fileName),
                message
            )
    
    def receive(self, hash, fileName, command):
        """
        Public slot to handle received editor commands.
        
        @param hash hash of the project (string)
        @param fileName project relative file name of the editor (string)
        @param command command string (string)
        """
        project = e5App().getObject("Project")
        if hash == project.getHash():
            fn = project.getAbsoluteUniversalPath(fileName)
            editor = self.getOpenEditor(fn)
            if editor:
                editor.receive(command)
    
    def shareConnected(self, connected):
        """
        Public slot to handle a change of the connected state.
        
        @param connected flag indicating the connected state (boolean)
        """
        for editor in self.getOpenEditors():
            editor.shareConnected(connected)
    
    def shareEditor(self, share):
        """
        Public slot to set the shared status of the current editor.
        
        @param share flag indicating the share status (boolean)
        """
        aw = self.activeWindow()
        if aw is not None:
            fn = aw.getFileName()
            if fn and e5App().getObject("Project").isProjectFile(fn):
                aw.shareEditor(share)
    
    def startSharedEdit(self):
        """
        Public slot to start a shared edit session for the current editor.
        """
        aw = self.activeWindow()
        if aw is not None:
            fn = aw.getFileName()
            if fn and e5App().getObject("Project").isProjectFile(fn):
                aw.startSharedEdit()
    
    def sendSharedEdit(self):
        """
        Public slot to end a shared edit session for the current editor and
        send the changes.
        """
        aw = self.activeWindow()
        if aw is not None:
            fn = aw.getFileName()
            if fn and e5App().getObject("Project").isProjectFile(fn):
                aw.sendSharedEdit()
    
    def cancelSharedEdit(self):
        """
        Public slot to cancel a shared edit session for the current editor.
        """
        aw = self.activeWindow()
        if aw is not None:
            fn = aw.getFileName()
            if fn and e5App().getObject("Project").isProjectFile(fn):
                aw.cancelSharedEdit()
    
    #######################################################################
    ## Symbols viewer related methods
    #######################################################################
    
    def insertSymbol(self, txt):
        """
        Public slot to insert a symbol text into the active window.
        
        @param txt text to be inserted (string)
        """
        if self.__lastFocusWidget == e5App().getObject("Shell"):
            e5App().getObject("Shell").insert(txt)
        else:
            aw = self.activeWindow()
            if aw is not None:
                curline, curindex = aw.getCursorPosition()
                aw.insert(txt)
                aw.setCursorPosition(curline, curindex + len(txt))
    
    #######################################################################
    ## Numbers viewer related methods
    #######################################################################
    
    def insertNumber(self, txt):
        """
        Public slot to insert a number text into the active window.
        
        @param txt text to be inserted (string)
        """
        if self.__lastFocusWidget == e5App().getObject("Shell"):
            aw = e5App().getObject("Shell")
            if aw.hasSelectedText():
                aw.removeSelectedText()
            aw.insert(txt)
        else:
            aw = self.activeWindow()
            if aw is not None:
                if aw.hasSelectedText():
                    aw.removeSelectedText()
                curline, curindex = aw.getCursorPosition()
                aw.insert(txt)
                aw.setCursorPosition(curline, curindex + len(txt))
    
    def getNumber(self):
        """
        Public method to get a number from the active window.
        
        @return selected text of the active window (string)
        """
        txt = ""
        if self.__lastFocusWidget == e5App().getObject("Shell"):
            aw = e5App().getObject("Shell")
            if aw.hasSelectedText():
                txt = aw.selectedText()
        else:
            aw = self.activeWindow()
            if aw is not None:
                if aw.hasSelectedText():
                    txt = aw.selectedText()
        return txt
