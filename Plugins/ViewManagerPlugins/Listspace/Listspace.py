# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the listspace viewmanager class.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSignal, QFileInfo, QEvent, Qt
from PyQt5.QtWidgets import QStackedWidget, QSplitter, QListWidget, \
    QListWidgetItem, QSizePolicy, QMenu, QApplication

from ViewManager.ViewManager import ViewManager

import QScintilla.Editor
from QScintilla.Editor import Editor

import UI.PixmapCache


class StackedWidget(QStackedWidget):
    """
    Class implementing a custimized StackedWidget.
    """
    def __init__(self, parent):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        """
        super(StackedWidget, self).__init__(parent)
        
        self.editors = []
        
    def addWidget(self, assembly):
        """
        Public method to add a new widget.
        
        @param assembly editor assembly object to be added
            (QScintilla.EditorAssembly.EditorAssembly)
        """
        editor = assembly.getEditor()
        super(StackedWidget, self).addWidget(assembly)
        if editor not in self.editors:
            self.editors.append(editor)
        
    def removeWidget(self, widget):
        """
        Public method to remove a widget.
        
        @param widget widget to be removed (QWidget)
        """
        if isinstance(widget, QScintilla.Editor.Editor):
            self.editors.remove(widget)
            widget = widget.parent()
        super(StackedWidget, self).removeWidget(widget)
        
    def currentWidget(self):
        """
        Public method to get a reference to the current editor.
        
        @return reference to the current editor (Editor)
        """
        widget = super(StackedWidget, self).currentWidget()
        if widget is not None:
            widget = widget.getEditor()
        return widget
        
    def setCurrentWidget(self, widget):
        """
        Public method to set the current widget.
        
        @param widget widget to be made current (QWidget)
        """
        if widget is not None:
            if isinstance(widget, QScintilla.Editor.Editor):
                self.editors.remove(widget)
                self.editors.insert(0, widget)
                widget = widget.parent()
            super(StackedWidget, self).setCurrentWidget(widget)
        
    def setCurrentIndex(self, index):
        """
        Public method to set the current widget by its index.
        
        @param index index of widget to be made current (integer)
        """
        widget = self.widget(index)
        if widget is not None:
            self.setCurrentWidget(widget)
        
    def nextTab(self):
        """
        Public slot used to show the next tab.
        """
        ind = self.currentIndex() + 1
        if ind == self.count():
            ind = 0
            
        self.setCurrentIndex(ind)
        self.currentWidget().setFocus()

    def prevTab(self):
        """
        Public slot used to show the previous tab.
        """
        ind = self.currentIndex() - 1
        if ind == -1:
            ind = self.count() - 1
            
        self.setCurrentIndex(ind)
        self.currentWidget().setFocus()

    def hasEditor(self, editor):
        """
        Public method to check for an editor.
        
        @param editor editor object to check for
        @return flag indicating, whether the editor to be checked belongs
            to the list of editors managed by this stacked widget.
        """
        return editor in self.editors
        
    def firstEditor(self):
        """
        Public method to retrieve the first editor in the list of managed
            editors.
        
        @return first editor in list (QScintilla.Editor.Editor)
        """
        return len(self.editors) and self.editors[0] or None


class Listspace(QSplitter, ViewManager):
    """
    Class implementing the listspace viewmanager class.
    
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
    @signal breakpointToggled(Editor) emitted when a breakpoint is toggled.
    @signal bookmarkToggled(Editor) emitted when a bookmark is toggled.
    @signal syntaxerrorToggled(Editor) emitted when a syntax error is toggled.
    @signal previewStateChanged(bool) emitted to signal a change in the
        preview state
    @signal editorLanguageChanged(Editor) emitted to signal a change of an
        editors language
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
    
    def __init__(self, parent):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        """
        self.stacks = []
        
        QSplitter.__init__(self, parent)
        ViewManager.__init__(self)
        self.setChildrenCollapsible(False)
        
        self.viewlist = QListWidget(self)
        policy = self.viewlist.sizePolicy()
        policy.setHorizontalPolicy(QSizePolicy.Ignored)
        self.viewlist.setSizePolicy(policy)
        self.addWidget(self.viewlist)
        self.viewlist.setContextMenuPolicy(Qt.CustomContextMenu)
        self.viewlist.currentRowChanged.connect(self.__showSelectedView)
        self.viewlist.customContextMenuRequested.connect(self.__showMenu)
        
        self.stackArea = QSplitter(self)
        self.stackArea.setChildrenCollapsible(False)
        self.addWidget(self.stackArea)
        self.stackArea.setOrientation(Qt.Vertical)
        stack = StackedWidget(self.stackArea)
        self.stackArea.addWidget(stack)
        self.stacks.append(stack)
        self.currentStack = stack
        stack.currentChanged.connect(self.__currentChanged)
        stack.installEventFilter(self)
        self.setSizes([int(self.width() * 0.2), int(self.width() * 0.8)])
        # 20% for viewlist, 80% for the editors
        self.__inRemoveView = False
        
        self.__initMenu()
        self.contextMenuEditor = None
        self.contextMenuIndex = -1
        
    def __initMenu(self):
        """
        Private method to initialize the viewlist context menu.
        """
        self.__menu = QMenu(self)
        self.__menu.addAction(
            UI.PixmapCache.getIcon("tabClose.png"),
            self.tr('Close'), self.__contextMenuClose)
        self.closeOthersMenuAct = self.__menu.addAction(
            UI.PixmapCache.getIcon("tabCloseOther.png"),
            self.tr("Close Others"),
            self.__contextMenuCloseOthers)
        self.__menu.addAction(
            self.tr('Close All'), self.__contextMenuCloseAll)
        self.__menu.addSeparator()
        self.saveMenuAct = self.__menu.addAction(
            UI.PixmapCache.getIcon("fileSave.png"),
            self.tr('Save'), self.__contextMenuSave)
        self.__menu.addAction(
            UI.PixmapCache.getIcon("fileSaveAs.png"),
            self.tr('Save As...'), self.__contextMenuSaveAs)
        self.__menu.addAction(
            UI.PixmapCache.getIcon("fileSaveAll.png"),
            self.tr('Save All'), self.__contextMenuSaveAll)
        self.__menu.addSeparator()
        self.openRejectionsMenuAct = self.__menu.addAction(
            self.tr("Open 'rejection' file"),
            self.__contextMenuOpenRejections)
        self.__menu.addSeparator()
        self.__menu.addAction(
            UI.PixmapCache.getIcon("print.png"),
            self.tr('Print'), self.__contextMenuPrintFile)
        self.__menu.addSeparator()
        self.copyPathAct = self.__menu.addAction(
            self.tr("Copy Path to Clipboard"),
            self.__contextMenuCopyPathToClipboard)
        
    def __showMenu(self, point):
        """
        Private slot to handle the customContextMenuRequested signal of
        the viewlist.
        
        @param point position to open the menu at (QPoint)
        """
        if self.editors:
            itm = self.viewlist.itemAt(point)
            if itm is not None:
                row = self.viewlist.row(itm)
                self.contextMenuEditor = self.editors[row]
                self.contextMenuIndex = row
                if self.contextMenuEditor:
                    self.saveMenuAct.setEnabled(
                        self.contextMenuEditor.isModified())
                    fileName = self.contextMenuEditor.getFileName()
                    self.copyPathAct.setEnabled(bool(fileName))
                    if fileName:
                        rej = "{0}.rej".format(fileName)
                        self.openRejectionsMenuAct.setEnabled(
                            os.path.exists(rej))
                    else:
                        self.openRejectionsMenuAct.setEnabled(False)
                    
                    self.closeOthersMenuAct.setEnabled(
                        self.viewlist.count() > 1)
                    
                    self.__menu.popup(self.viewlist.mapToGlobal(point))
        
    def canCascade(self):
        """
        Public method to signal if cascading of managed windows is available.
        
        @return flag indicating cascading of windows is available
        """
        return False
        
    def canTile(self):
        """
        Public method to signal if tiling of managed windows is available.
        
        @return flag indicating tiling of windows is available
        """
        return False
    
    def canSplit(self):
        """
        public method to signal if splitting of the view is available.
        
        @return flag indicating splitting of the view is available.
        """
        return True
        
    def tile(self):
        """
        Public method to tile the managed windows.
        """
        pass
        
    def cascade(self):
        """
        Public method to cascade the managed windows.
        """
        pass
        
    def _removeAllViews(self):
        """
        Protected method to remove all views (i.e. windows).
        """
        self.viewlist.clear()
        for win in self.editors:
            for stack in self.stacks:
                if stack.hasEditor(win):
                    stack.removeWidget(win)
                    break
            win.closeIt()
        
    def _removeView(self, win):
        """
        Protected method to remove a view (i.e. window).
        
        @param win editor window to be removed
        """
        self.__inRemoveView = True
        ind = self.editors.index(win)
        itm = self.viewlist.takeItem(ind)
        if itm:
            del itm
        for stack in self.stacks:
            if stack.hasEditor(win):
                stack.removeWidget(win)
                break
        win.closeIt()
        self.__inRemoveView = False
        if ind > 0:
            ind -= 1
        else:
            if len(self.editors) > 1:
                ind = 1
            else:
                return
        stack.setCurrentWidget(stack.firstEditor())
        self._showView(self.editors[ind].parent())
        
        aw = self.activeWindow()
        fn = aw and aw.getFileName() or None
        if fn:
            self.changeCaption.emit(fn)
            self.editorChanged.emit(fn)
            self.editorLineChanged.emit(fn, aw.getCursorPosition()[0] + 1)
        else:
            self.changeCaption.emit("")
        self.editorChangedEd.emit(aw)
        
    def _addView(self, win, fn=None, noName="", next=False):
        """
        Protected method to add a view (i.e. window).
        
        @param win editor assembly to be added
        @param fn filename of this editor (string)
        @param noName name to be used for an unnamed editor (string)
        @param next flag indicating to add the view next to the current
            view (bool)
        """
        editor = win.getEditor()
        if fn is None:
            if not noName:
                self.untitledCount += 1
                noName = self.tr("Untitled {0}").format(self.untitledCount)
            self.viewlist.addItem(noName)
            editor.setNoName(noName)
        else:
            txt = os.path.basename(fn)
            if not QFileInfo(fn).isWritable():
                txt = self.tr("{0} (ro)").format(txt)
            itm = QListWidgetItem(txt)
            itm.setToolTip(fn)
            self.viewlist.addItem(itm)
        self.currentStack.addWidget(win)
        self.currentStack.setCurrentWidget(win)
        editor.captionChanged.connect(self.__captionChange)
        editor.cursorLineChanged.connect(self.__cursorLineChanged)
        
        index = self.editors.index(editor)
        self.viewlist.setCurrentRow(index)
        editor.setFocus()
        if fn:
            self.changeCaption.emit(fn)
            self.editorChanged.emit(fn)
            self.editorLineChanged.emit(fn, editor.getCursorPosition()[0] + 1)
        else:
            self.changeCaption.emit("")
        self.editorChangedEd.emit(editor)
        
    def __captionChange(self, cap, editor):
        """
        Private method to handle caption change signals from the editor.
        
        Updates the listwidget text to reflect the new caption information.
        
        @param cap Caption for the editor (string)
        @param editor Editor to update the caption for
        """
        fn = editor.getFileName()
        if fn:
            self.setEditorName(editor, fn)
        
    def __cursorLineChanged(self, lineno):
        """
        Private slot to handle a change of the current editor's cursor line.
        
        @param lineno line number of the current editor's cursor (zero based)
        """
        editor = self.sender()
        if editor:
            fn = editor.getFileName()
            if fn:
                self.editorLineChanged.emit(fn, lineno + 1)
        
    def _showView(self, win, fn=None):
        """
        Protected method to show a view (i.e. window).
        
        @param win editor assembly to be shown
        @param fn filename of this editor (string)
        """
        editor = win.getEditor()
        for stack in self.stacks:
            if stack.hasEditor(editor):
                stack.setCurrentWidget(win)
                self.currentStack = stack
                break
        index = self.editors.index(editor)
        self.viewlist.setCurrentRow(index)
        editor.setFocus()
        fn = editor.getFileName()
        if fn:
            self.changeCaption.emit(fn)
            self.editorChanged.emit(fn)
            self.editorLineChanged.emit(fn, editor.getCursorPosition()[0] + 1)
        else:
            self.changeCaption.emit("")
        self.editorChangedEd.emit(editor)
        
    def __showSelectedView(self, row):
        """
        Private slot called to show a view selected in the list.
        
        @param row row number of the item clicked on (integer)
        """
        if row != -1:
            self._showView(self.editors[row].parent())
            self._checkActions(self.editors[row])
        
    def activeWindow(self):
        """
        Public method to return the active (i.e. current) window.
        
        @return reference to the active editor
        """
        return self.currentStack.currentWidget()
        
    def showWindowMenu(self, windowMenu):
        """
        Public method to set up the viewmanager part of the Window menu.
        
        @param windowMenu reference to the window menu
        """
        pass
        
    def _initWindowActions(self):
        """
        Protected method to define the user interface actions for window
        handling.
        """
        pass
        
    def setEditorName(self, editor, newName):
        """
        Public method to change the displayed name of the editor.
        
        @param editor editor window to be changed
        @param newName new name to be shown (string)
        """
        if newName:
            currentRow = self.viewlist.currentRow()
            index = self.editors.index(editor)
            txt = os.path.basename(newName)
            if not QFileInfo(newName).isWritable():
                txt = self.tr("{0} (ro)").format(txt)
            itm = self.viewlist.item(index)
            itm.setText(txt)
            itm.setToolTip(newName)
            self.viewlist.setCurrentRow(currentRow)
            self.changeCaption.emit(newName)
            
    def _modificationStatusChanged(self, m, editor):
        """
        Protected slot to handle the modificationStatusChanged signal.
        
        @param m flag indicating the modification status (boolean)
        @param editor editor window changed
        """
        currentRow = self.viewlist.currentRow()
        index = self.editors.index(editor)
        keys = []
        if m:
            keys.append("fileModified.png")
        if editor.hasSyntaxErrors():
            keys.append("syntaxError22.png")
        elif editor.hasWarnings():
            keys.append("warning22.png")
        if not keys:
            keys.append("empty.png")
        self.viewlist.item(index).setIcon(
            UI.PixmapCache.getCombinedIcon(keys))
        self.viewlist.setCurrentRow(currentRow)
        self._checkActions(editor)
        
    def _syntaxErrorToggled(self, editor):
        """
        Protected slot to handle the syntaxerrorToggled signal.
        
        @param editor editor that sent the signal
        """
        currentRow = self.viewlist.currentRow()
        index = self.editors.index(editor)
        keys = []
        if editor.isModified():
            keys.append("fileModified.png")
        if editor.hasSyntaxErrors():
            keys.append("syntaxError22.png")
        elif editor.hasWarnings():
            keys.append("warning22.png")
        if not keys:
            keys.append("empty.png")
        self.viewlist.item(index).setIcon(
            UI.PixmapCache.getCombinedIcon(keys))
        self.viewlist.setCurrentRow(currentRow)
        
        ViewManager._syntaxErrorToggled(self, editor)
        
    def addSplit(self):
        """
        Public method used to split the current view.
        """
        stack = StackedWidget(self.stackArea)
        stack.show()
        self.stackArea.addWidget(stack)
        self.stacks.append(stack)
        self.currentStack = stack
        stack.currentChanged.connect(self.__currentChanged)
        stack.installEventFilter(self)
        if self.stackArea.orientation() == Qt.Horizontal:
            size = self.stackArea.width()
        else:
            size = self.stackArea.height()
        self.stackArea.setSizes(
            [int(size / len(self.stacks))] * len(self.stacks))
        self.splitRemoveAct.setEnabled(True)
        self.nextSplitAct.setEnabled(True)
        self.prevSplitAct.setEnabled(True)
        
    def removeSplit(self):
        """
        Public method used to remove the current split view.
        
        @return flag indicating successfull removal
        """
        if len(self.stacks) > 1:
            stack = self.currentStack
            res = True
            savedEditors = stack.editors[:]
            for editor in savedEditors:
                res &= self.closeEditor(editor)
            if res:
                try:
                    i = self.stacks.index(stack)
                except ValueError:
                    return True
                if i == len(self.stacks) - 1:
                    i -= 1
                self.stacks.remove(stack)
                stack.close()
                self.currentStack = self.stacks[i]
                if len(self.stacks) == 1:
                    self.splitRemoveAct.setEnabled(False)
                    self.nextSplitAct.setEnabled(False)
                    self.prevSplitAct.setEnabled(False)
                return True
        
        return False
        
    def getSplitOrientation(self):
        """
        Public method to get the orientation of the split view.
        
        @return orientation of the split (Qt.Horizontal or Qt.Vertical)
        """
        return self.stackArea.orientation()
        
    def setSplitOrientation(self, orientation):
        """
        Public method used to set the orientation of the split view.
        
        @param orientation orientation of the split
                (Qt.Horizontal or Qt.Vertical)
        """
        self.stackArea.setOrientation(orientation)
        
    def nextSplit(self):
        """
        Public slot used to move to the next split.
        """
        aw = self.activeWindow()
        _hasFocus = aw and aw.hasFocus()
        ind = self.stacks.index(self.currentStack) + 1
        if ind == len(self.stacks):
            ind = 0
        
        self.currentStack = self.stacks[ind]
        if _hasFocus:
            aw = self.activeWindow()
            if aw:
                aw.setFocus()
        
        index = self.editors.index(self.currentStack.currentWidget())
        self.viewlist.setCurrentRow(index)
        
    def prevSplit(self):
        """
        Public slot used to move to the previous split.
        """
        aw = self.activeWindow()
        _hasFocus = aw and aw.hasFocus()
        ind = self.stacks.index(self.currentStack) - 1
        if ind == -1:
            ind = len(self.stacks) - 1
        
        self.currentStack = self.stacks[ind]
        if _hasFocus:
            aw = self.activeWindow()
            if aw:
                aw.setFocus()
        index = self.editors.index(self.currentStack.currentWidget())
        self.viewlist.setCurrentRow(index)
        
    def __contextMenuClose(self):
        """
        Private method to close the selected editor.
        """
        if self.contextMenuEditor:
            self.closeEditorWindow(self.contextMenuEditor)
        
    def __contextMenuCloseOthers(self):
        """
        Private method to close the other editors.
        """
        index = self.contextMenuIndex
        for i in list(range(self.viewlist.count() - 1, index, -1)) + \
                list(range(index - 1, -1, -1)):
            editor = self.editors[i]
            self.closeEditorWindow(editor)
        
    def __contextMenuCloseAll(self):
        """
        Private method to close all editors.
        """
        savedEditors = self.editors[:]
        for editor in savedEditors:
            self.closeEditorWindow(editor)
        
    def __contextMenuSave(self):
        """
        Private method to save the selected editor.
        """
        if self.contextMenuEditor:
            self.saveEditorEd(self.contextMenuEditor)
        
    def __contextMenuSaveAs(self):
        """
        Private method to save the selected editor to a new file.
        """
        if self.contextMenuEditor:
            self.saveAsEditorEd(self.contextMenuEditor)
        
    def __contextMenuSaveAll(self):
        """
        Private method to save all editors.
        """
        self.saveEditorsList(self.editors)
        
    def __contextMenuOpenRejections(self):
        """
        Private slot to open a rejections file associated with the selected
        editor.
        """
        if self.contextMenuEditor:
            fileName = self.contextMenuEditor.getFileName()
            if fileName:
                rej = "{0}.rej".format(fileName)
                if os.path.exists(rej):
                    self.openSourceFile(rej)
        
    def __contextMenuPrintFile(self):
        """
        Private method to print the selected editor.
        """
        if self.contextMenuEditor:
            self.printEditor(self.contextMenuEditor)
        
    def __contextMenuCopyPathToClipboard(self):
        """
        Private method to copy the file name of the selected editor to the
        clipboard.
        """
        if self.contextMenuEditor:
            fn = self.contextMenuEditor.getFileName()
            if fn:
                cb = QApplication.clipboard()
                cb.setText(fn)
        
    def __currentChanged(self, index):
        """
        Private slot to handle the currentChanged signal.
        
        @param index index of the current editor
        """
        if index == -1 or not self.editors:
            return
        
        editor = self.activeWindow()
        if editor is None:
            return
        
        self._checkActions(editor)
        editor.setFocus()
        fn = editor.getFileName()
        if fn:
            self.changeCaption.emit(fn)
            if not self.__inRemoveView:
                self.editorChanged.emit(fn)
                self.editorLineChanged.emit(
                    fn, editor.getCursorPosition()[0] + 1)
        else:
            self.changeCaption.emit("")
        self.editorChangedEd.emit(editor)
        
        cindex = self.editors.index(editor)
        self.viewlist.setCurrentRow(cindex)
        
    def eventFilter(self, watched, event):
        """
        Public method called to filter the event queue.
        
        @param watched the QObject being watched
        @param event the event that occurred
        @return flag indicating, if we handled the event
        """
        if event.type() == QEvent.MouseButtonPress and \
           not event.button() == Qt.RightButton:
            switched = True
            if isinstance(watched, QStackedWidget):
                switched = watched is not self.currentStack
                self.currentStack = watched
            elif isinstance(watched, QScintilla.Editor.Editor):
                for stack in self.stacks:
                    if stack.hasEditor(watched):
                        switched = stack is not self.currentStack
                        self.currentStack = stack
                        break
            currentWidget = self.currentStack.currentWidget()
            if currentWidget:
                index = self.editors.index(currentWidget)
                self.viewlist.setCurrentRow(index)
            
            aw = self.activeWindow()
            if aw is not None:
                self._checkActions(aw)
                aw.setFocus()
                fn = aw.getFileName()
                if fn:
                    self.changeCaption.emit(fn)
                    if switched:
                        self.editorChanged.emit(fn)
                        self.editorLineChanged.emit(
                            fn, aw.getCursorPosition()[0] + 1)
                else:
                    self.changeCaption.emit("")
                self.editorChangedEd.emit(aw)
        
        return False
