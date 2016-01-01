# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a tabbed viewmanager class.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QPoint, QFileInfo, pyqtSignal, QEvent, QByteArray, \
    QMimeData, Qt, QSize
from PyQt5.QtGui import QColor, QDrag, QPixmap
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSplitter, QTabBar, \
    QApplication, QToolButton, QMenu, QLabel

from E5Gui.E5Application import e5App

from ViewManager.ViewManager import ViewManager

import QScintilla.Editor
from QScintilla.Editor import Editor

import UI.PixmapCache

from E5Gui.E5TabWidget import E5TabWidget, E5WheelTabBar
from E5Gui.E5Led import E5Led

import Preferences
from Globals import isMacPlatform

from eric6config import getConfig


class TabBar(E5WheelTabBar):
    """
    Class implementing a customized tab bar supporting drag & drop.
    
    @signal tabMoveRequested(int, int) emitted to signal a tab move request
        giving the old and new index position
    @signal tabRelocateRequested(str, int, int) emitted to signal a tab
        relocation request giving the string encoded id of the old tab widget,
        the index in the old tab widget and the new index position
    @signal tabCopyRequested(str, int, int) emitted to signal a clone request
        giving the string encoded id of the source tab widget, the index in the
        source tab widget and the new index position
    @signal tabCopyRequested(int, int) emitted to signal a clone request giving
        the old and new index position
    """
    tabMoveRequested = pyqtSignal(int, int)
    tabRelocateRequested = pyqtSignal(str, int, int)
    tabCopyRequested = pyqtSignal((str, int, int), (int, int))
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(TabBar, self).__init__(parent)
        self.setAcceptDrops(True)
        
        self.__dragStartPos = QPoint()
    
    def mousePressEvent(self, event):
        """
        Protected method to handle mouse press events.
        
        @param event reference to the mouse press event (QMouseEvent)
        """
        if event.button() == Qt.LeftButton:
            self.__dragStartPos = QPoint(event.pos())
        super(TabBar, self).mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """
        Protected method to handle mouse move events.
        
        @param event reference to the mouse move event (QMouseEvent)
        """
        if event.buttons() == Qt.MouseButtons(Qt.LeftButton) and \
           (event.pos() - self.__dragStartPos).manhattanLength() > \
                QApplication.startDragDistance():
            drag = QDrag(self)
            mimeData = QMimeData()
            index = self.tabAt(event.pos())
            mimeData.setText(self.tabText(index))
            mimeData.setData("action", b"tab-reordering")
            mimeData.setData("tabbar-id", str(id(self)).encode("utf-8"))
            mimeData.setData(
                "source-index",
                QByteArray.number(self.tabAt(self.__dragStartPos)))
            mimeData.setData(
                "tabwidget-id",
                str(id(self.parentWidget())).encode("utf-8"))
            drag.setMimeData(mimeData)
            if event.modifiers() == Qt.KeyboardModifiers(Qt.ShiftModifier):
                drag.exec_(Qt.DropActions(Qt.CopyAction))
            elif event.modifiers() == Qt.KeyboardModifiers(Qt.NoModifier):
                drag.exec_(Qt.DropActions(Qt.MoveAction))
        super(TabBar, self).mouseMoveEvent(event)
    
    def dragEnterEvent(self, event):
        """
        Protected method to handle drag enter events.
        
        @param event reference to the drag enter event (QDragEnterEvent)
        """
        mimeData = event.mimeData()
        formats = mimeData.formats()
        if "action" in formats and \
           mimeData.data("action") == b"tab-reordering" and \
           "tabbar-id" in formats and \
           "source-index" in formats and \
           "tabwidget-id" in formats:
            event.acceptProposedAction()
        super(TabBar, self).dragEnterEvent(event)
    
    def dropEvent(self, event):
        """
        Protected method to handle drop events.
        
        @param event reference to the drop event (QDropEvent)
        """
        mimeData = event.mimeData()
        oldID = int(mimeData.data("tabbar-id"))
        fromIndex = int(mimeData.data("source-index"))
        toIndex = self.tabAt(event.pos())
        if oldID != id(self):
            parentID = int(mimeData.data("tabwidget-id"))
            if event.proposedAction() == Qt.MoveAction:
                self.tabRelocateRequested.emit(
                    str(parentID), fromIndex, toIndex)
                event.acceptProposedAction()
            elif event.proposedAction() == Qt.CopyAction:
                self.tabCopyRequested[str, int, int].emit(
                    str(parentID), fromIndex, toIndex)
                event.acceptProposedAction()
        else:
            if fromIndex != toIndex:
                if event.proposedAction() == Qt.MoveAction:
                    self.tabMoveRequested.emit(fromIndex, toIndex)
                    event.acceptProposedAction()
                elif event.proposedAction() == Qt.CopyAction:
                    self.tabCopyRequested[int, int].emit(fromIndex, toIndex)
                    event.acceptProposedAction()
        super(TabBar, self).dropEvent(event)


class TabWidget(E5TabWidget):
    """
    Class implementing a custimized tab widget.
    """
    def __init__(self, vm):
        """
        Constructor
        
        @param vm view manager widget (Tabview)
        """
        super(TabWidget, self).__init__()
        
        self.__tabBar = TabBar(self)
        self.setTabBar(self.__tabBar)
        iconSize = self.__tabBar.iconSize()
        self.__tabBar.setIconSize(
            QSize(2 * iconSize.width(), iconSize.height()))
        
        self.setUsesScrollButtons(True)
        self.setElideMode(Qt.ElideNone)
        if isMacPlatform():
            self.setDocumentMode(True)
        
        self.__tabBar.tabMoveRequested.connect(self.moveTab)
        self.__tabBar.tabRelocateRequested.connect(self.__relocateTab)
        self.__tabBar.tabCopyRequested[str, int, int].connect(
            self.__copyTabOther)
        self.__tabBar.tabCopyRequested[int, int].connect(self.__copyTab)
        
        self.vm = vm
        self.editors = []
        
        self.indicator = E5Led(self)
        self.setCornerWidget(self.indicator, Qt.TopLeftCorner)
        
        self.rightCornerWidget = QWidget(self)
        self.rightCornerWidgetLayout = QHBoxLayout(self.rightCornerWidget)
        self.rightCornerWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.rightCornerWidgetLayout.setSpacing(0)
        
        self.__navigationMenu = QMenu(self)
        self.__navigationMenu.aboutToShow.connect(self.__showNavigationMenu)
        self.__navigationMenu.triggered.connect(self.__navigationMenuTriggered)
        
        self.navigationButton = QToolButton(self)
        self.navigationButton.setIcon(UI.PixmapCache.getIcon("1downarrow.png"))
        self.navigationButton.setToolTip(self.tr("Show a navigation menu"))
        self.navigationButton.setPopupMode(QToolButton.InstantPopup)
        self.navigationButton.setMenu(self.__navigationMenu)
        self.navigationButton.setEnabled(False)
        self.rightCornerWidgetLayout.addWidget(self.navigationButton)
        
        if Preferences.getUI("SingleCloseButton") or \
           not hasattr(self, 'setTabsClosable'):
            self.closeButton = QToolButton(self)
            self.closeButton.setIcon(UI.PixmapCache.getIcon("close.png"))
            self.closeButton.setToolTip(
                self.tr("Close the current editor"))
            self.closeButton.setEnabled(False)
            self.closeButton.clicked[bool].connect(self.__closeButtonClicked)
            self.rightCornerWidgetLayout.addWidget(self.closeButton)
        else:
            self.tabCloseRequested.connect(self.__closeRequested)
            self.closeButton = None
        
        self.setCornerWidget(self.rightCornerWidget, Qt.TopRightCorner)
        
        self.__initMenu()
        self.contextMenuEditor = None
        self.contextMenuIndex = -1
        
        self.setTabContextMenuPolicy(Qt.CustomContextMenu)
        self.customTabContextMenuRequested.connect(self.__showContextMenu)
        
        ericPic = QPixmap(
            os.path.join(getConfig('ericPixDir'), 'eric_small.png'))
        self.emptyLabel = QLabel()
        self.emptyLabel.setPixmap(ericPic)
        self.emptyLabel.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        super(TabWidget, self).addTab(
            self.emptyLabel,
            UI.PixmapCache.getIcon("empty.png"), "")
        
    def __initMenu(self):
        """
        Private method to initialize the tab context menu.
        """
        self.__menu = QMenu(self)
        self.leftMenuAct = self.__menu.addAction(
            UI.PixmapCache.getIcon("1leftarrow.png"),
            self.tr('Move Left'), self.__contextMenuMoveLeft)
        self.rightMenuAct = self.__menu.addAction(
            UI.PixmapCache.getIcon("1rightarrow.png"),
            self.tr('Move Right'), self.__contextMenuMoveRight)
        self.firstMenuAct = self.__menu.addAction(
            UI.PixmapCache.getIcon("2leftarrow.png"),
            self.tr('Move First'), self.__contextMenuMoveFirst)
        self.lastMenuAct = self.__menu.addAction(
            UI.PixmapCache.getIcon("2rightarrow.png"),
            self.tr('Move Last'), self.__contextMenuMoveLast)
        self.__menu.addSeparator()
        self.__menu.addAction(
            UI.PixmapCache.getIcon("tabClose.png"),
            self.tr('Close'), self.__contextMenuClose)
        self.closeOthersMenuAct = self.__menu.addAction(
            UI.PixmapCache.getIcon("tabCloseOther.png"),
            self.tr("Close Others"), self.__contextMenuCloseOthers)
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
        
    def __showContextMenu(self, coord, index):
        """
        Private slot to show the tab context menu.
        
        @param coord the position of the mouse pointer (QPoint)
        @param index index of the tab the menu is requested for (integer)
        """
        if self.editors:
            self.contextMenuEditor = self.widget(index).getEditor()
            if self.contextMenuEditor:
                self.saveMenuAct.setEnabled(
                    self.contextMenuEditor.isModified())
                fileName = self.contextMenuEditor.getFileName()
                self.copyPathAct.setEnabled(bool(fileName))
                if fileName:
                    rej = "{0}.rej".format(fileName)
                    self.openRejectionsMenuAct.setEnabled(os.path.exists(rej))
                else:
                    self.openRejectionsMenuAct.setEnabled(False)
            
            self.contextMenuIndex = index
            self.leftMenuAct.setEnabled(index > 0)
            self.rightMenuAct.setEnabled(index < self.count() - 1)
            self.firstMenuAct.setEnabled(index > 0)
            self.lastMenuAct.setEnabled(index < self.count() - 1)
            
            self.closeOthersMenuAct.setEnabled(self.count() > 1)
            
            coord = self.mapToGlobal(coord)
            self.__menu.popup(coord)
        
    def __showNavigationMenu(self):
        """
        Private slot to show the navigation button menu.
        """
        self.__navigationMenu.clear()
        for index in range(self.count()):
            act = self.__navigationMenu.addAction(self.tabIcon(index),
                                                  self.tabText(index))
            act.setData(index)
        
    def __navigationMenuTriggered(self, act):
        """
        Private slot called to handle the navigation button menu selection.
        
        @param act reference to the selected action (QAction)
        """
        index = act.data()
        if index is not None:
            self.setCurrentIndex(index)
        
    def showIndicator(self, on):
        """
        Public slot to set the indicator on or off.
        
        @param on flag indicating the dtate of the indicator (boolean)
        """
        if on:
            self.indicator.setColor(QColor("green"))
        else:
            self.indicator.setColor(QColor("red"))
        
    def addTab(self, assembly, title):
        """
        Public method to add a new tab.
        
        @param assembly editor assembly object to be added
            (QScintilla.EditorAssembly.EditorAssembly)
        @param title title for the new tab (string)
        """
        editor = assembly.getEditor()
        super(TabWidget, self).addTab(
            assembly, UI.PixmapCache.getIcon("empty.png"), title)
        if self.closeButton:
            self.closeButton.setEnabled(True)
        else:
            self.setTabsClosable(True)
        self.navigationButton.setEnabled(True)
        
        if editor not in self.editors:
            self.editors.append(editor)
            editor.captionChanged.connect(self.__captionChange)
            editor.cursorLineChanged.connect(self.__cursorLineChanged)
        
        emptyIndex = self.indexOf(self.emptyLabel)
        if emptyIndex > -1:
            self.removeTab(emptyIndex)
        
    def insertWidget(self, index, assembly, title):
        """
        Public method to insert a new tab.
        
        @param index index position for the new tab (integer)
        @param assembly editor assembly object to be added
            (QScintilla.EditorAssembly.EditorAssembly)
        @param title title for the new tab (string)
        @return index of the inserted tab (integer)
        """
        editor = assembly.getEditor()
        newIndex = super(TabWidget, self).insertTab(
            index, assembly,
            UI.PixmapCache.getIcon("empty.png"),
            title)
        if self.closeButton:
            self.closeButton.setEnabled(True)
        else:
            self.setTabsClosable(True)
        self.navigationButton.setEnabled(True)
        
        if editor not in self.editors:
            self.editors.append(editor)
            editor.captionChanged.connect(self.__captionChange)
            editor.cursorLineChanged.connect(self.__cursorLineChanged)
        emptyIndex = self.indexOf(self.emptyLabel)
        if emptyIndex > -1:
            self.removeTab(emptyIndex)
        
        return newIndex
        
    def __captionChange(self, cap, editor):
        """
        Private slot to handle Caption change signals from the editor.
        
        Updates the tab text and tooltip text to reflect the new caption
        information.
        
        @param cap Caption for the editor
        @param editor Editor to update the caption for
        """
        fn = editor.getFileName()
        if fn:
            if Preferences.getUI("TabViewManagerFilenameOnly"):
                txt = os.path.basename(fn)
            else:
                txt = e5App().getObject("Project").getRelativePath(fn)
            
            maxFileNameChars = Preferences.getUI(
                "TabViewManagerFilenameLength")
            if len(txt) > maxFileNameChars:
                txt = "...{0}".format(txt[-maxFileNameChars:])
            if editor.isReadOnly():
                txt = self.tr("{0} (ro)").format(txt)
            
            assembly = editor.parent()
            index = self.indexOf(assembly)
            if index > -1:
                self.setTabText(index, txt)
                self.setTabToolTip(index, fn)
        
    def __cursorLineChanged(self, lineno):
        """
        Private slot to handle a change of the current editor's cursor line.
        
        @param lineno line number of the current editor's cursor (zero based)
        """
        editor = self.sender()
        if editor and isinstance(editor, QScintilla.Editor.Editor):
            fn = editor.getFileName()
            if fn:
                self.vm.editorLineChanged.emit(fn, lineno + 1)
        
    def removeWidget(self, object):
        """
        Public method to remove a widget.
        
        @param object object to be removed (QWidget)
        """
        if isinstance(object, QScintilla.Editor.Editor):
            object.cursorLineChanged.disconnect(self.__cursorLineChanged)
            object.captionChanged.disconnect(self.__captionChange)
            self.editors.remove(object)
            index = self.indexOf(object.parent())
        else:
            index = self.indexOf(object)
        if index > -1:
            self.removeTab(index)
        
        if not self.editors:
            super(TabWidget, self).addTab(
                self.emptyLabel, UI.PixmapCache.getIcon("empty.png"), "")
            self.emptyLabel.show()
            if self.closeButton:
                self.closeButton.setEnabled(False)
            else:
                self.setTabsClosable(False)
            self.navigationButton.setEnabled(False)
        
    def __relocateTab(self, sourceId, sourceIndex, targetIndex):
        """
        Private method to relocate an editor from another TabWidget.
        
        @param sourceId id of the TabWidget to get the editor from (string)
        @param sourceIndex index of the tab in the old tab widget (integer)
        @param targetIndex index position to place it to (integer)
        """
        tw = self.vm.getTabWidgetById(int(sourceId))
        if tw is not None:
            # step 1: get data of the tab of the source
            toolTip = tw.tabToolTip(sourceIndex)
            text = tw.tabText(sourceIndex)
            icon = tw.tabIcon(sourceIndex)
            whatsThis = tw.tabWhatsThis(sourceIndex)
            assembly = tw.widget(sourceIndex)
            
            # step 2: relocate the tab
            tw.removeWidget(assembly.getEditor())
            self.insertWidget(targetIndex, assembly, text)
            
            # step 3: set the tab data again
            self.setTabIcon(targetIndex, icon)
            self.setTabToolTip(targetIndex, toolTip)
            self.setTabWhatsThis(targetIndex, whatsThis)
            
            # step 4: set current widget
            self.setCurrentIndex(targetIndex)
        
    def __copyTabOther(self, sourceId, sourceIndex, targetIndex):
        """
        Private method to copy an editor from another TabWidget.
        
        @param sourceId id of the TabWidget to get the editor from (string)
        @param sourceIndex index of the tab in the old tab widget (integer)
        @param targetIndex index position to place it to (integer)
        """
        tw = self.vm.getTabWidgetById(int(sourceId))
        if tw is not None:
            editor = tw.widget(sourceIndex).getEditor()
            newEditor, assembly = self.vm.cloneEditor(
                editor, editor.getFileType(), editor.getFileName())
            self.vm.insertView(assembly, self, targetIndex,
                               editor.getFileName(), editor.getNoName())
        
    def __copyTab(self, sourceIndex, targetIndex):
        """
        Private method to copy an editor.
        
        @param sourceIndex index of the tab (integer)
        @param targetIndex index position to place it to (integer)
        """
        editor = self.widget(sourceIndex).getEditor()
        newEditor, assembly = self.vm.cloneEditor(
            editor, editor.getFileType(), editor.getFileName())
        self.vm.insertView(assembly, self, targetIndex,
                           editor.getFileName(), editor.getNoName())
        
    def currentWidget(self):
        """
        Public method to return a reference to the current page.
        
        @return reference to the current page (Editor)
        """
        if not self.editors:
            return None
        else:
            return super(TabWidget, self).currentWidget()
        
    def setCurrentWidget(self, assembly):
        """
        Public method to set the current tab by the given editor assembly.
        
        @param assembly editor assembly to determine current tab from
            (EditorAssembly.EditorAssembly)
        """
        super(TabWidget, self).setCurrentWidget(assembly)
        
    def indexOf(self, object):
        """
        Public method to get the tab index of the given editor.
        
        @param object object to get the index for (QLabel or Editor)
        @return tab index of the editor (integer)
        """
        if isinstance(object, QScintilla.Editor.Editor):
            object = object.parent()
        return super(TabWidget, self).indexOf(object)
        
    def hasEditor(self, editor):
        """
        Public method to check for an editor.
        
        @param editor editor object to check for
        @return flag indicating, whether the editor to be checked belongs
            to the list of editors managed by this tab widget.
        """
        return editor in self.editors
        
    def hasEditors(self):
        """
        Public method to test, if any editor is managed.
        
        @return flag indicating editors are managed
        """
        return len(self.editors) > 0
        
    def __contextMenuClose(self):
        """
        Private method to close the selected tab.
        """
        if self.contextMenuEditor:
            self.vm.closeEditorWindow(self.contextMenuEditor)
        
    def __contextMenuCloseOthers(self):
        """
        Private method to close the other tabs.
        """
        index = self.contextMenuIndex
        for i in list(range(self.count() - 1, index, -1)) + \
                list(range(index - 1, -1, -1)):
            editor = self.widget(i).getEditor()
            self.vm.closeEditorWindow(editor)
        
    def __contextMenuCloseAll(self):
        """
        Private method to close all tabs.
        """
        savedEditors = self.editors[:]
        for editor in savedEditors:
            self.vm.closeEditorWindow(editor)
        
    def __contextMenuSave(self):
        """
        Private method to save the selected tab.
        """
        if self.contextMenuEditor:
            self.vm.saveEditorEd(self.contextMenuEditor)
        
    def __contextMenuSaveAs(self):
        """
        Private method to save the selected tab to a new file.
        """
        if self.contextMenuEditor:
            self.vm.saveAsEditorEd(self.contextMenuEditor)
        
    def __contextMenuSaveAll(self):
        """
        Private method to save all tabs.
        """
        self.vm.saveEditorsList(self.editors)
        
    def __contextMenuOpenRejections(self):
        """
        Private slot to open a rejections file associated with the selected
        tab.
        """
        if self.contextMenuEditor:
            fileName = self.contextMenuEditor.getFileName()
            if fileName:
                rej = "{0}.rej".format(fileName)
                if os.path.exists(rej):
                    self.vm.openSourceFile(rej)
        
    def __contextMenuPrintFile(self):
        """
        Private method to print the selected tab.
        """
        if self.contextMenuEditor:
            self.vm.printEditor(self.contextMenuEditor)
    
    def __contextMenuCopyPathToClipboard(self):
        """
        Private method to copy the file name of the selected tab to the
        clipboard.
        """
        if self.contextMenuEditor:
            fn = self.contextMenuEditor.getFileName()
            if fn:
                cb = QApplication.clipboard()
                cb.setText(fn)
        
    def __contextMenuMoveLeft(self):
        """
        Private method to move a tab one position to the left.
        """
        self.moveTab(self.contextMenuIndex, self.contextMenuIndex - 1)
        
    def __contextMenuMoveRight(self):
        """
        Private method to move a tab one position to the right.
        """
        self.moveTab(self.contextMenuIndex, self.contextMenuIndex + 1)
        
    def __contextMenuMoveFirst(self):
        """
        Private method to move a tab to the first position.
        """
        self.moveTab(self.contextMenuIndex, 0)
        
    def __contextMenuMoveLast(self):
        """
        Private method to move a tab to the last position.
        """
        self.moveTab(self.contextMenuIndex, self.count() - 1)
        
    def __closeButtonClicked(self):
        """
        Private method to handle the press of the close button.
        """
        self.vm.closeEditorWindow(self.currentWidget().getEditor())
        
    def __closeRequested(self, index):
        """
        Private method to handle the press of the individual tab close button.
        
        @param index index of the tab (integer)
        """
        if index >= 0:
            self.vm.closeEditorWindow(self.widget(index).getEditor())
        
    def mouseDoubleClickEvent(self, event):
        """
        Protected method handling double click events.
        
        @param event reference to the event object (QMouseEvent)
        """
        self.vm.newEditor()


class Tabview(QSplitter, ViewManager):
    """
    Class implementing a tabbed viewmanager class embedded in a splitter.
    
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
        self.tabWidgets = []
        
        QSplitter.__init__(self, parent)
        ViewManager.__init__(self)
        self.setChildrenCollapsible(False)
        
        tw = TabWidget(self)
        self.addWidget(tw)
        self.tabWidgets.append(tw)
        self.currentTabWidget = tw
        self.currentTabWidget.showIndicator(True)
        tw.currentChanged.connect(self.__currentChanged)
        tw.installEventFilter(self)
        tw.tabBar().installEventFilter(self)
        self.setOrientation(Qt.Vertical)
        self.__inRemoveView = False
        
        self.maxFileNameChars = Preferences.getUI(
            "TabViewManagerFilenameLength")
        self.filenameOnly = Preferences.getUI("TabViewManagerFilenameOnly")
        
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
        for win in self.editors:
            self._removeView(win)
        
    def _removeView(self, win):
        """
        Protected method to remove a view (i.e. window).
        
        @param win editor window to be removed
        """
        self.__inRemoveView = True
        for tw in self.tabWidgets:
            if tw.hasEditor(win):
                tw.removeWidget(win)
                break
        win.closeIt()
        self.__inRemoveView = False
        
        # if this was the last editor in this view, switch to the next, that
        # still has open editors
        for i in list(range(self.tabWidgets.index(tw), -1, -1)) + \
            list(range(self.tabWidgets.index(tw) + 1,
                 len(self.tabWidgets))):
            if self.tabWidgets[i].hasEditors():
                self.currentTabWidget.showIndicator(False)
                self.currentTabWidget = self.tabWidgets[i]
                self.currentTabWidget.showIndicator(True)
                self.activeWindow().setFocus()
                break
        
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
            if next:
                index = self.currentTabWidget.currentIndex() + 1
                self.currentTabWidget.insertWidget(index, win, noName)
            else:
                self.currentTabWidget.addTab(win, noName)
            editor.setNoName(noName)
        else:
            if self.filenameOnly:
                txt = os.path.basename(fn)
            else:
                txt = e5App().getObject("Project").getRelativePath(fn)
            if len(txt) > self.maxFileNameChars:
                txt = "...{0}".format(txt[-self.maxFileNameChars:])
            if not QFileInfo(fn).isWritable():
                txt = self.tr("{0} (ro)").format(txt)
            if next:
                index = self.currentTabWidget.currentIndex() + 1
                self.currentTabWidget.insertWidget(index, win, txt)
            else:
                self.currentTabWidget.addTab(win, txt)
            index = self.currentTabWidget.indexOf(win)
            self.currentTabWidget.setTabToolTip(index, fn)
        self.currentTabWidget.setCurrentWidget(win)
        win.show()
        editor.setFocus()
        if fn:
            self.changeCaption.emit(fn)
            self.editorChanged.emit(fn)
            self.editorLineChanged.emit(fn, editor.getCursorPosition()[0] + 1)
        else:
            self.changeCaption.emit("")
        self.editorChangedEd.emit(editor)
        
    def insertView(self, win, tabWidget, index, fn=None, noName=""):
        """
        Public method to add a view (i.e. window).
        
        @param win editor assembly to be inserted
        @param tabWidget reference to the tab widget to insert the editor into
            (TabWidget)
        @param index index position to insert at (integer)
        @param fn filename of this editor (string)
        @param noName name to be used for an unnamed editor (string)
        """
        editor = win.getEditor()
        if fn is None:
            if not noName:
                self.untitledCount += 1
                noName = self.tr("Untitled {0}").format(self.untitledCount)
            tabWidget.insertWidget(index, win, noName)
            editor.setNoName(noName)
        else:
            if self.filenameOnly:
                txt = os.path.basename(fn)
            else:
                txt = e5App().getObject("Project").getRelativePath(fn)
            if len(txt) > self.maxFileNameChars:
                txt = "...{0}".format(txt[-self.maxFileNameChars:])
            if not QFileInfo(fn).isWritable():
                txt = self.tr("{0} (ro)").format(txt)
            nindex = tabWidget.insertWidget(index, win, txt)
            tabWidget.setTabToolTip(nindex, fn)
        tabWidget.setCurrentWidget(win)
        win.show()
        editor.setFocus()
        if fn:
            self.changeCaption.emit(fn)
            self.editorChanged.emit(fn)
            self.editorLineChanged.emit(fn, editor.getCursorPosition()[0] + 1)
        else:
            self.changeCaption.emit("")
        self.editorChangedEd.emit(editor)
        
        self._modificationStatusChanged(editor.isModified(), editor)
        self._checkActions(editor)
        
    def _showView(self, win, fn=None):
        """
        Protected method to show a view (i.e. window).
        
        @param win editor assembly to be shown
        @param fn filename of this editor (string)
        """
        win.show()
        editor = win.getEditor()
        for tw in self.tabWidgets:
            if tw.hasEditor(editor):
                tw.setCurrentWidget(win)
                self.currentTabWidget.showIndicator(False)
                self.currentTabWidget = tw
                self.currentTabWidget.showIndicator(True)
                break
        editor.setFocus()
        
    def activeWindow(self):
        """
        Public method to return the active (i.e. current) window.
        
        @return reference to the active editor
        """
        cw = self.currentTabWidget.currentWidget()
        if cw:
            return cw.getEditor()
        else:
            return None
        
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
            if self.filenameOnly:
                tabName = os.path.basename(newName)
            else:
                tabName = e5App().getObject("Project").getRelativePath(newName)
            if len(tabName) > self.maxFileNameChars:
                tabName = "...{0}".format(tabName[-self.maxFileNameChars:])
            index = self.currentTabWidget.indexOf(editor)
            self.currentTabWidget.setTabText(index, tabName)
            self.currentTabWidget.setTabToolTip(index, newName)
            self.changeCaption.emit(newName)

    def _modificationStatusChanged(self, m, editor):
        """
        Protected slot to handle the modificationStatusChanged signal.
        
        @param m flag indicating the modification status (boolean)
        @param editor editor window changed
        """
        for tw in self.tabWidgets:
            if tw.hasEditor(editor):
                break
        index = tw.indexOf(editor)
        keys = []
        if m:
            keys.append("fileModified.png")
        if editor.hasSyntaxErrors():
            keys.append("syntaxError22.png")
        elif editor.hasWarnings():
            keys.append("warning22.png")
        if not keys:
            keys.append("empty.png")
        tw.setTabIcon(index, UI.PixmapCache.getCombinedIcon(keys))
        self._checkActions(editor)
        
    def _syntaxErrorToggled(self, editor):
        """
        Protected slot to handle the syntaxerrorToggled signal.
        
        @param editor editor that sent the signal
        """
        for tw in self.tabWidgets:
            if tw.hasEditor(editor):
                break
        index = tw.indexOf(editor)
        keys = []
        if editor.isModified():
            keys.append("fileModified.png")
        if editor.hasSyntaxErrors():
            keys.append("syntaxError22.png")
        elif editor.hasWarnings():
            keys.append("warning22.png")
        if not keys:
            keys.append("empty.png")
        tw.setTabIcon(index, UI.PixmapCache.getCombinedIcon(keys))
        
        ViewManager._syntaxErrorToggled(self, editor)
        
    def addSplit(self):
        """
        Public method used to split the current view.
        """
        tw = TabWidget(self)
        tw.show()
        self.addWidget(tw)
        self.tabWidgets.append(tw)
        self.currentTabWidget.showIndicator(False)
        self.currentTabWidget = self.tabWidgets[-1]
        self.currentTabWidget.showIndicator(True)
        tw.currentChanged.connect(self.__currentChanged)
        tw.installEventFilter(self)
        tw.tabBar().installEventFilter(self)
        if self.orientation() == Qt.Horizontal:
            size = self.width()
        else:
            size = self.height()
        self.setSizes(
            [int(size / len(self.tabWidgets))] * len(self.tabWidgets))
        self.splitRemoveAct.setEnabled(True)
        self.nextSplitAct.setEnabled(True)
        self.prevSplitAct.setEnabled(True)
        
    def removeSplit(self):
        """
        Public method used to remove the current split view.
        
        @return flag indicating successfull removal
        """
        if len(self.tabWidgets) > 1:
            tw = self.currentTabWidget
            res = True
            savedEditors = tw.editors[:]
            for editor in savedEditors:
                res &= self.closeEditor(editor)
            if res:
                try:
                    i = self.tabWidgets.index(tw)
                except ValueError:
                    return True
                if i == len(self.tabWidgets) - 1:
                    i -= 1
                self.tabWidgets.remove(tw)
                tw.close()
                self.currentTabWidget = self.tabWidgets[i]
                for tw in self.tabWidgets:
                    tw.showIndicator(tw == self.currentTabWidget)
                if self.currentTabWidget is not None:
                    assembly = self.currentTabWidget.currentWidget()
                    if assembly is not None:
                        editor = assembly.getEditor()
                        if editor is not None:
                            editor.setFocus(Qt.OtherFocusReason)
                if len(self.tabWidgets) == 1:
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
        return self.orientation()
        
    def setSplitOrientation(self, orientation):
        """
        Public method used to set the orientation of the split view.
        
        @param orientation orientation of the split
                (Qt.Horizontal or Qt.Vertical)
        """
        self.setOrientation(orientation)
        
    def nextSplit(self):
        """
        Public slot used to move to the next split.
        """
        aw = self.activeWindow()
        _hasFocus = aw and aw.hasFocus()
        ind = self.tabWidgets.index(self.currentTabWidget) + 1
        if ind == len(self.tabWidgets):
            ind = 0
        
        self.currentTabWidget.showIndicator(False)
        self.currentTabWidget = self.tabWidgets[ind]
        self.currentTabWidget.showIndicator(True)
        if _hasFocus:
            aw = self.activeWindow()
            if aw:
                aw.setFocus()
        
    def prevSplit(self):
        """
        Public slot used to move to the previous split.
        """
        aw = self.activeWindow()
        _hasFocus = aw and aw.hasFocus()
        ind = self.tabWidgets.index(self.currentTabWidget) - 1
        if ind == -1:
            ind = len(self.tabWidgets) - 1
        
        self.currentTabWidget.showIndicator(False)
        self.currentTabWidget = self.tabWidgets[ind]
        self.currentTabWidget.showIndicator(True)
        if _hasFocus:
            aw = self.activeWindow()
            if aw:
                aw.setFocus()
        
    def __currentChanged(self, index):
        """
        Private slot to handle the currentChanged signal.
        
        @param index index of the current tab (integer)
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
        
    def eventFilter(self, watched, event):
        """
        Public method called to filter the event queue.
        
        @param watched the QObject being watched (QObject)
        @param event the event that occurred (QEvent)
        @return always False
        """
        if event.type() == QEvent.MouseButtonPress and \
           not event.button() == Qt.RightButton:
            switched = True
            self.currentTabWidget.showIndicator(False)
            if isinstance(watched, E5TabWidget):
                switched = watched is not self.currentTabWidget
                self.currentTabWidget = watched
            elif isinstance(watched, QTabBar):
                switched = watched.parent() is not self.currentTabWidget
                self.currentTabWidget = watched.parent()
                if switched:
                    index = self.currentTabWidget.selectTab(event.pos())
                    switched = self.currentTabWidget.widget(index) is \
                        self.activeWindow()
            elif isinstance(watched, QScintilla.Editor.Editor):
                for tw in self.tabWidgets:
                    if tw.hasEditor(watched):
                        switched = tw is not self.currentTabWidget
                        self.currentTabWidget = tw
                        break
            self.currentTabWidget.showIndicator(True)
            
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
        
    def preferencesChanged(self):
        """
        Public slot to handle the preferencesChanged signal.
        """
        ViewManager.preferencesChanged(self)
        
        self.maxFileNameChars = Preferences.getUI(
            "TabViewManagerFilenameLength")
        self.filenameOnly = Preferences.getUI("TabViewManagerFilenameOnly")
        
        for tabWidget in self.tabWidgets:
            for index in range(tabWidget.count()):
                editor = tabWidget.widget(index)
                if isinstance(editor, QScintilla.Editor.Editor):
                    fn = editor.getFileName()
                    if fn:
                        if self.filenameOnly:
                            txt = os.path.basename(fn)
                        else:
                            txt = e5App().getObject("Project")\
                                .getRelativePath(fn)
                        if len(txt) > self.maxFileNameChars:
                            txt = "...{0}".format(txt[-self.maxFileNameChars:])
                        if not QFileInfo(fn).isWritable():
                            txt = self.tr("{0} (ro)").format(txt)
                        tabWidget.setTabText(index, txt)
        
    def getTabWidgetById(self, id_):
        """
        Public method to get a reference to a tab widget knowing its ID.
        
        @param id_ id of the tab widget (long)
        @return reference to the tab widget (TabWidget)
        """
        for tw in self.tabWidgets:
            if id(tw) == id_:
                return tw
        return None
