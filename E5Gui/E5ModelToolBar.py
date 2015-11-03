# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a tool bar populated from a QAbstractItemModel.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, qVersion, Qt, QModelIndex, QPoint, QEvent
from PyQt5.QtGui import QDrag, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QToolBar, QToolButton


class E5ModelToolBar(QToolBar):
    """
    Class implementing a tool bar populated from a QAbstractItemModel.
    
    @signal activated(QModelIndex) emitted when an action has been triggered
    """
    activated = pyqtSignal(QModelIndex)
    
    def __init__(self, title=None, parent=None):
        """
        Constructor
        
        @param title title for the tool bar (string)
        @param parent reference to the parent widget (QWidget)
        """
        if title is not None:
            super(E5ModelToolBar, self).__init__(title, parent)
        else:
            super(E5ModelToolBar, self).__init__(parent)
        
        self.__model = None
        
        self.__root = QModelIndex()
        self.__dragStartPosition = QPoint()
        
        if self.isVisible():
            self._build()
        
        self.setAcceptDrops(True)
        
        self._mouseButton = Qt.NoButton
        self._keyboardModifiers = Qt.KeyboardModifiers(Qt.NoModifier)
        self.__dropRow = -1
        self.__dropIndex = None
    
    def setModel(self, model):
        """
        Public method to set the model for the tool bar.
        
        @param model reference to the model (QAbstractItemModel)
        """
        if self.__model is not None:
            self.__model.modelReset.disconnect(self._build)
            self.__model.rowsInserted[QModelIndex, int, int].disconnect(
                self._build)
            self.__model.rowsRemoved[QModelIndex, int, int].disconnect(
                self._build)
            self.__model.dataChanged.disconnect(
                self._build)
        
        self.__model = model
        
        if self.__model is not None:
            self.__model.modelReset.connect(self._build)
            self.__model.rowsInserted[QModelIndex, int, int].connect(
                self._build)
            self.__model.rowsRemoved[QModelIndex, int, int].connect(
                self._build)
            self.__model.dataChanged.connect(
                self._build)
    
    def model(self):
        """
        Public method to get a reference to the model.
        
        @return reference to the model (QAbstractItemModel)
        """
        return self.__model
    
    def setRootIndex(self, idx):
        """
        Public method to set the root index.
        
        @param idx index to be set as the root index (QModelIndex)
        """
        self.__root = idx
    
    def rootIndex(self):
        """
        Public method to get the root index.
        
        @return root index (QModelIndex)
        """
        return self.__root
    
    def _build(self):
        """
        Protected slot to build the tool bar.
        """
        assert self.__model is not None
        
        self.clear()
        
        for i in range(self.__model.rowCount(self.__root)):
            idx = self.__model.index(i, 0, self.__root)
            
            title = idx.data(Qt.DisplayRole)
            icon = idx.data(Qt.DecorationRole)
            if icon == NotImplemented or icon is None:
                icon = QIcon()
            folder = self.__model.hasChildren(idx)
            
            act = self.addAction(icon, title)
            act.setData(idx)
            
            button = self.widgetForAction(act)
            button.installEventFilter(self)
            
            if folder:
                menu = self._createMenu()
                menu.setModel(self.__model)
                menu.setRootIndex(idx)
                act.setMenu(menu)
                button.setPopupMode(QToolButton.InstantPopup)
                button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    
    def index(self, action):
        """
        Public method to get the index of an action.
        
        @param action reference to the action to get the index for (QAction)
        @return index of the action (QModelIndex)
        """
        if action is None:
            return QModelIndex()
        
        idx = action.data()
        if idx is None:
            return QModelIndex()
        
        if not isinstance(idx, QModelIndex):
            return QModelIndex()
        
        return idx
    
    def _createMenu(self):
        """
        Protected method to create the menu for a tool bar action.
        
        @return menu for a tool bar action (E5ModelMenu)
        """
        from .E5ModelMenu import E5ModelMenu
        return E5ModelMenu(self)
    
    def eventFilter(self, obj, evt):
        """
        Public method to handle event for other objects.
        
        @param obj reference to the object (QObject)
        @param evt reference to the event (QEvent)
        @return flag indicating that the event should be filtered out (boolean)
        """
        if evt.type() == QEvent.MouseButtonRelease:
            self._mouseButton = evt.button()
            self._keyboardModifiers = evt.modifiers()
            act = obj.defaultAction()
            idx = self.index(act)
            if idx.isValid():
                self.activated[QModelIndex].emit(idx)
        elif evt.type() == QEvent.MouseButtonPress:
            if evt.buttons() & Qt.LeftButton:
                self.__dragStartPosition = self.mapFromGlobal(evt.globalPos())
        
        return False
    
    def dragEnterEvent(self, evt):
        """
        Protected method to handle drag enter events.
        
        @param evt reference to the event (QDragEnterEvent)
        """
        if self.__model is not None:
            mimeTypes = self.__model.mimeTypes()
            for mimeType in mimeTypes:
                if evt.mimeData().hasFormat(mimeType):
                    evt.acceptProposedAction()
        
        super(E5ModelToolBar, self).dragEnterEvent(evt)
    
    def dropEvent(self, evt):
        """
        Protected method to handle drop events.
        
        @param evt reference to the event (QDropEvent)
        """
        if self.__model is not None:
            act = self.actionAt(evt.pos())
            parentIndex = self.__root
            if act is None:
                row = self.__model.rowCount(self.__root)
            else:
                idx = self.index(act)
                assert idx.isValid()
                row = idx.row()
                if self.__model.hasChildren(idx):
                    parentIndex = idx
                    row = self.__model.rowCount(idx)
            
            self.__dropRow = row
            self.__dropIndex = parentIndex
            evt.acceptProposedAction()
            self.__model.dropMimeData(evt.mimeData(), evt.dropAction(),
                                      row, 0, parentIndex)
        
        super(E5ModelToolBar, self).dropEvent(evt)
    
    def mouseMoveEvent(self, evt):
        """
        Protected method to handle mouse move events.
        
        @param evt reference to the event (QMouseEvent)
        """
        if self.__model is None:
            super(E5ModelToolBar, self).mouseMoveEvent(evt)
            return
        
        if not (evt.buttons() & Qt.LeftButton):
            super(E5ModelToolBar, self).mouseMoveEvent(evt)
            return
        
        manhattanLength = (evt.pos() -
                           self.__dragStartPosition).manhattanLength()
        if manhattanLength <= QApplication.startDragDistance():
            super(E5ModelToolBar, self).mouseMoveEvent(evt)
            return
        
        act = self.actionAt(self.__dragStartPosition)
        if act is None:
            super(E5ModelToolBar, self).mouseMoveEvent(evt)
            return
        
        idx = self.index(act)
        assert idx.isValid()
        
        drag = QDrag(self)
        drag.setMimeData(self.__model.mimeData([idx]))
        actionRect = self.actionGeometry(act)
        if qVersion() >= "5.0.0":
            drag.setPixmap(self.grab(actionRect))
        else:
            drag.setPixmap(QPixmap.grabWidget(self, actionRect))
        
        if drag.exec_() == Qt.MoveAction:
            row = idx.row()
            if self.__dropIndex == idx.parent() and self.__dropRow <= row:
                row += 1
            self.__model.removeRow(row, self.__root)
    
    def hideEvent(self, evt):
        """
        Protected method to handle hide events.
        
        @param evt reference to the hide event (QHideEvent)
        """
        self.clear()
        super(E5ModelToolBar, self).hideEvent(evt)
    
    def showEvent(self, evt):
        """
        Protected method to handle show events.
        
        @param evt reference to the hide event (QHideEvent)
        """
        if len(self.actions()) == 0:
            self._build()
        super(E5ModelToolBar, self).showEvent(evt)
    
    def resetFlags(self):
        """
        Public method to reset the saved internal state.
        """
        self._mouseButton = Qt.NoButton
        self._keyboardModifiers = Qt.KeyboardModifiers(Qt.NoModifier)
