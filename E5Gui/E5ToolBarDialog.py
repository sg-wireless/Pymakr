# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a toolbar configuration dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QTreeWidgetItem, \
    QInputDialog, QLineEdit, QListWidgetItem, QAbstractButton

from E5Gui import E5MessageBox

from .Ui_E5ToolBarDialog import Ui_E5ToolBarDialog

import UI.PixmapCache


class E5ToolBarItem(object):
    """
    Class storing data belonging to a toolbar entry of the toolbar dialog.
    """
    def __init__(self, toolBarId, actionIDs, default):
        """
        Constructor
        
        @param toolBarId id of the toolbar object (integer)
        @param actionIDs list of action IDs belonging to the toolbar
            (list of integer)
        @param default flag indicating a default toolbar (boolean)
        """
        self.toolBarId = toolBarId
        self.actionIDs = actionIDs[:]
        self.isDefault = default
        self.title = ""
        self.isChanged = False
    

class E5ToolBarDialog(QDialog, Ui_E5ToolBarDialog):
    """
    Class implementing a toolbar configuration dialog.
    """
    ActionIdRole = Qt.UserRole
    WidgetActionRole = Qt.UserRole + 1
    
    def __init__(self, toolBarManager, parent=None):
        """
        Constructor
        
        @param toolBarManager reference to a toolbar manager object
            (E5ToolBarManager)
        @param parent reference to the parent widget (QWidget)
        """
        super(E5ToolBarDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__manager = toolBarManager
        self.__toolbarItems = {}
        # maps toolbar item IDs to toolbar items
        self.__currentToolBarItem = None
        self.__removedToolBarIDs = []
        # remember custom toolbars to be deleted
        
        self.__widgetActionToToolBarItemID = {}
        # maps widget action IDs to toolbar item IDs
        self.__toolBarItemToWidgetActionID = {}
        # maps toolbar item IDs to widget action IDs
        
        self.upButton.setIcon(UI.PixmapCache.getIcon("1uparrow.png"))
        self.downButton.setIcon(UI.PixmapCache.getIcon("1downarrow.png"))
        self.leftButton.setIcon(UI.PixmapCache.getIcon("1leftarrow.png"))
        self.rightButton.setIcon(UI.PixmapCache.getIcon("1rightarrow.png"))
        
        self.__restoreDefaultsButton = \
            self.buttonBox.button(QDialogButtonBox.RestoreDefaults)
        self.__resetButton = self.buttonBox.button(QDialogButtonBox.Reset)
        
        self.actionsTree.header().hide()
        self.__separatorText = self.tr("--Separator--")
        itm = QTreeWidgetItem(self.actionsTree, [self.__separatorText])
        self.actionsTree.setCurrentItem(itm)
        
        for category in sorted(self.__manager.categories()):
            categoryItem = QTreeWidgetItem(self.actionsTree, [category])
            for action in self.__manager.categoryActions(category):
                item = QTreeWidgetItem(categoryItem)
                item.setText(0, action.text())
                item.setIcon(0, action.icon())
                item.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                item.setData(0, E5ToolBarDialog.ActionIdRole, int(id(action)))
                item.setData(0, E5ToolBarDialog.WidgetActionRole, False)
                if self.__manager.isWidgetAction(action):
                    item.setData(0, E5ToolBarDialog.WidgetActionRole, True)
                    item.setData(0, Qt.TextColorRole, QColor(Qt.blue))
                    self.__widgetActionToToolBarItemID[id(action)] = None
            categoryItem.setExpanded(True)
        
        for tbID, actions in list(self.__manager.toolBarsActions().items()):
            tb = self.__manager.toolBarById(tbID)
            default = self.__manager.isDefaultToolBar(tb)
            tbItem = E5ToolBarItem(tbID, [], default)
            self.__toolbarItems[id(tbItem)] = tbItem
            self.__toolBarItemToWidgetActionID[id(tbItem)] = []
            actionIDs = []
            for action in actions:
                if action is None:
                    actionIDs.append(None)
                else:
                    aID = id(action)
                    actionIDs.append(aID)
                    if aID in self.__widgetActionToToolBarItemID:
                        self.__widgetActionToToolBarItemID[aID] = id(tbItem)
                        self.__toolBarItemToWidgetActionID[id(tbItem)]\
                            .append(aID)
            tbItem.actionIDs = actionIDs
            self.toolbarComboBox.addItem(tb.windowTitle(), int(id(tbItem)))
            if default:
                self.toolbarComboBox.setItemData(
                    self.toolbarComboBox.count() - 1,
                    QColor(Qt.darkGreen), Qt.ForegroundRole)
        self.toolbarComboBox.model().sort(0)
        
        self.toolbarComboBox.currentIndexChanged[int].connect(
            self.__toolbarComboBox_currentIndexChanged)
        self.toolbarComboBox.setCurrentIndex(0)
    
    @pyqtSlot()
    def on_newButton_clicked(self):
        """
        Private slot to create a new toolbar.
        """
        name, ok = QInputDialog.getText(
            self,
            self.tr("New Toolbar"),
            self.tr("Toolbar Name:"),
            QLineEdit.Normal)
        if ok and name:
            if self.toolbarComboBox.findText(name) != -1:
                # toolbar with this name already exists
                E5MessageBox.critical(
                    self,
                    self.tr("New Toolbar"),
                    self.tr(
                        """A toolbar with the name <b>{0}</b> already"""
                        """ exists.""")
                    .format(name))
                return
            
            tbItem = E5ToolBarItem(None, [], False)
            tbItem.title = name
            tbItem.isChanged = True
            self.__toolbarItems[id(tbItem)] = tbItem
            self.__toolBarItemToWidgetActionID[id(tbItem)] = []
            self.toolbarComboBox.addItem(name, int(id(tbItem)))
            self.toolbarComboBox.model().sort(0)
            self.toolbarComboBox.setCurrentIndex(
                self.toolbarComboBox.findText(name))
    
    @pyqtSlot()
    def on_removeButton_clicked(self):
        """
        Private slot to remove a custom toolbar.
        """
        name = self.toolbarComboBox.currentText()
        res = E5MessageBox.yesNo(
            self,
            self.tr("Remove Toolbar"),
            self.tr(
                """Should the toolbar <b>{0}</b> really be removed?""")
            .format(name))
        if res:
            index = self.toolbarComboBox.currentIndex()
            tbItemID = self.toolbarComboBox.itemData(index)
            tbItem = self.__toolbarItems[tbItemID]
            if tbItem.toolBarId is not None and \
               tbItem.toolBarId not in self.__removedToolBarIDs:
                self.__removedToolBarIDs.append(tbItem.toolBarId)
            del self.__toolbarItems[tbItemID]
            for widgetActionID in self.__toolBarItemToWidgetActionID[tbItemID]:
                self.__widgetActionToToolBarItemID[widgetActionID] = None
            del self.__toolBarItemToWidgetActionID[tbItemID]
            self.toolbarComboBox.removeItem(index)
    
    @pyqtSlot()
    def on_renameButton_clicked(self):
        """
        Private slot to rename a custom toolbar.
        """
        oldName = self.toolbarComboBox.currentText()
        newName, ok = QInputDialog.getText(
            self,
            self.tr("Rename Toolbar"),
            self.tr("New Toolbar Name:"),
            QLineEdit.Normal,
            oldName)
        if ok and newName:
            if oldName == newName:
                return
            if self.toolbarComboBox.findText(newName) != -1:
                # toolbar with this name already exists
                E5MessageBox.critical(
                    self,
                    self.tr("Rename Toolbar"),
                    self.tr(
                        """A toolbar with the name <b>{0}</b> already"""
                        """ exists.""")
                    .format(newName))
                return
            index = self.toolbarComboBox.currentIndex()
            self.toolbarComboBox.setItemText(index, newName)
            tbItem = \
                self.__toolbarItems[self.toolbarComboBox.itemData(index)]
            tbItem.title = newName
            tbItem.isChanged = True
    
    def __setupButtons(self):
        """
        Private slot to set the buttons state.
        """
        index = self.toolbarComboBox.currentIndex()
        if index > -1:
            itemID = self.toolbarComboBox.itemData(index)
            self.__currentToolBarItem = self.__toolbarItems[itemID]
            self.renameButton.setEnabled(
                not self.__currentToolBarItem.isDefault)
            self.removeButton.setEnabled(
                not self.__currentToolBarItem.isDefault)
            self.__restoreDefaultsButton.setEnabled(
                self.__currentToolBarItem.isDefault)
            self.__resetButton.setEnabled(
                self.__currentToolBarItem.toolBarId is not None)
        
        row = self.toolbarActionsList.currentRow()
        self.upButton.setEnabled(row > 0)
        self.downButton.setEnabled(row < self.toolbarActionsList.count() - 1)
        self.leftButton.setEnabled(self.toolbarActionsList.count() > 0)
        rightEnable = self.actionsTree.currentItem().parent() is not None or \
            self.actionsTree.currentItem().text(0) == self.__separatorText
        self.rightButton.setEnabled(rightEnable)
    
    @pyqtSlot(int)
    def __toolbarComboBox_currentIndexChanged(self, index):
        """
        Private slot called upon a selection of the current toolbar.
        
        @param index index of the new current toolbar (integer)
        """
        itemID = self.toolbarComboBox.itemData(index)
        self.__currentToolBarItem = self.__toolbarItems[itemID]
        self.toolbarActionsList.clear()
        for actionID in self.__currentToolBarItem.actionIDs:
            item = QListWidgetItem(self.toolbarActionsList)
            if actionID is None:
                item.setText(self.__separatorText)
            else:
                action = self.__manager.actionById(actionID)
                item.setText(action.text())
                item.setIcon(action.icon())
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                item.setData(E5ToolBarDialog.ActionIdRole, int(id(action)))
                item.setData(E5ToolBarDialog.WidgetActionRole, False)
                if self.__manager.isWidgetAction(action):
                    item.setData(E5ToolBarDialog.WidgetActionRole, True)
                    item.setData(Qt.TextColorRole, QColor(Qt.blue))
        self.toolbarActionsList.setCurrentRow(0)
        
        self.__setupButtons()
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_actionsTree_currentItemChanged(self, current, previous):
        """
        Private slot called, when the currently selected action changes.
        
        @param current reference to the current item (QTreeWidgetItem)
        @param previous reference to the previous current item
            (QTreeWidgetItem)
        """
        self.__setupButtons()
    
    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def on_toolbarActionsList_currentItemChanged(self, current, previous):
        """
        Private slot to handle a change of the current item.
        
        @param current reference to the current item (QListWidgetItem)
        @param previous reference to the previous current item
            (QListWidgetItem)
        """
        self.__setupButtons()
    
    @pyqtSlot()
    def on_upButton_clicked(self):
        """
        Private slot used to move an action up in the list.
        """
        row = self.toolbarActionsList.currentRow()
        if row == 0:
            # we're already at the top
            return
        
        actionID = self.__currentToolBarItem.actionIDs.pop(row)
        self.__currentToolBarItem.actionIDs.insert(row - 1, actionID)
        self.__currentToolBarItem.isChanged = True
        itm = self.toolbarActionsList.takeItem(row)
        self.toolbarActionsList.insertItem(row - 1, itm)
        self.toolbarActionsList.setCurrentItem(itm)
        self.__setupButtons()
    
    @pyqtSlot()
    def on_downButton_clicked(self):
        """
        Private slot used to move an action down in the list.
        """
        row = self.toolbarActionsList.currentRow()
        if row == self.toolbarActionsList.count() - 1:
            # we're already at the end
            return
        
        actionID = self.__currentToolBarItem.actionIDs.pop(row)
        self.__currentToolBarItem.actionIDs.insert(row + 1, actionID)
        self.__currentToolBarItem.isChanged = True
        itm = self.toolbarActionsList.takeItem(row)
        self.toolbarActionsList.insertItem(row + 1, itm)
        self.toolbarActionsList.setCurrentItem(itm)
        self.__setupButtons()
    
    @pyqtSlot()
    def on_leftButton_clicked(self):
        """
        Private slot to delete an action from the list.
        """
        row = self.toolbarActionsList.currentRow()
        actionID = self.__currentToolBarItem.actionIDs.pop(row)
        self.__currentToolBarItem.isChanged = True
        if actionID in self.__widgetActionToToolBarItemID:
            self.__widgetActionToToolBarItemID[actionID] = None
            self.__toolBarItemToWidgetActionID[id(self.__currentToolBarItem)]\
                .remove(actionID)
        itm = self.toolbarActionsList.takeItem(row)
        del itm
        self.toolbarActionsList.setCurrentRow(row)
        self.__setupButtons()
    
    @pyqtSlot()
    def on_rightButton_clicked(self):
        """
        Private slot to add an action to the list.
        """
        row = self.toolbarActionsList.currentRow() + 1
            
        item = QListWidgetItem()
        if self.actionsTree.currentItem().text(0) == self.__separatorText:
            item.setText(self.__separatorText)
            actionID = None
        else:
            actionID = self.actionsTree.currentItem()\
                .data(0, E5ToolBarDialog.ActionIdRole)
            action = self.__manager.actionById(actionID)
            item.setText(action.text())
            item.setIcon(action.icon())
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            item.setData(E5ToolBarDialog.ActionIdRole, int(id(action)))
            item.setData(E5ToolBarDialog.WidgetActionRole, False)
            if self.__manager.isWidgetAction(action):
                item.setData(E5ToolBarDialog.WidgetActionRole, True)
                item.setData(Qt.TextColorRole, QColor(Qt.blue))
                oldTbItemID = self.__widgetActionToToolBarItemID[actionID]
                if oldTbItemID is not None:
                    self.__toolbarItems[oldTbItemID].actionIDs.remove(actionID)
                    self.__toolbarItems[oldTbItemID].isChanged = True
                    self.__toolBarItemToWidgetActionID[oldTbItemID]\
                        .remove(actionID)
                self.__widgetActionToToolBarItemID[actionID] = \
                    id(self.__currentToolBarItem)
                self.__toolBarItemToWidgetActionID[
                    id(self.__currentToolBarItem)].append(actionID)
        self.toolbarActionsList.insertItem(row, item)
        self.__currentToolBarItem.actionIDs.insert(row, actionID)
        self.__currentToolBarItem.isChanged = True
        self.toolbarActionsList.setCurrentRow(row)
        self.__setupButtons()
    
    @pyqtSlot(QAbstractButton)
    def on_buttonBox_clicked(self, button):
        """
        Private slot called, when a button of the button box was clicked.
        
        @param button reference to the button clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.reject()
        elif button == self.buttonBox.button(QDialogButtonBox.Apply):
            self.__saveToolBars()
            self.__setupButtons()
        elif button == self.buttonBox.button(QDialogButtonBox.Ok):
            self.__saveToolBars()
            self.accept()
        elif button == self.buttonBox.button(QDialogButtonBox.Reset):
            self.__resetCurrentToolbar()
            self.__setupButtons()
        elif button == self.buttonBox.button(QDialogButtonBox.RestoreDefaults):
            self.__restoreCurrentToolbarToDefault()
            self.__setupButtons()
    
    def __saveToolBars(self):
        """
        Private method to save the configured toolbars.
        
        @exception RuntimeError raised to indicate an invalid action
        """
        # step 1: remove toolbars marked for deletion
        for tbID in self.__removedToolBarIDs:
            tb = self.__manager.toolBarById(tbID)
            self.__manager.deleteToolBar(tb)
        self.__removedToolBarIDs = []
        
        # step 2: save configured toolbars
        for tbItem in list(self.__toolbarItems.values()):
            if not tbItem.isChanged:
                continue
            
            if tbItem.toolBarId is None:
                # new custom toolbar
                tb = self.__manager.createToolBar(tbItem.title)
                tbItem.toolBarId = id(tb)
            else:
                tb = self.__manager.toolBarById(tbItem.toolBarId)
                if not tbItem.isDefault and tbItem.title:
                    self.__manager.renameToolBar(tb, tbItem.title)
            
            actions = []
            for actionID in tbItem.actionIDs:
                if actionID is None:
                    actions.append(None)
                else:
                    action = self.__manager.actionById(actionID)
                    if action is None:
                        raise RuntimeError(
                            "No such action, id: 0x{0:x}".format(actionID))
                    actions.append(action)
            self.__manager.setToolBar(tb, actions)
            tbItem.isChanged = False
    
    def __restoreCurrentToolbar(self, actions):
        """
        Private methdo to restore the current toolbar to the given list of
        actions.
        
        @param actions list of actions to set for the current toolbar
        (list of QAction)
        """
        tbItemID = id(self.__currentToolBarItem)
        for widgetActionID in self.__toolBarItemToWidgetActionID[tbItemID]:
            self.__widgetActionToToolBarItemID[widgetActionID] = None
        self.__toolBarItemToWidgetActionID[tbItemID] = []
        self.__currentToolBarItem.actionIDs = []
        
        for action in actions:
            if action is None:
                self.__currentToolBarItem.actionIDs.append(None)
            else:
                actionID = id(action)
                self.__currentToolBarItem.actionIDs.append(actionID)
                if actionID in self.__widgetActionToToolBarItemID:
                    oldTbItemID = self.__widgetActionToToolBarItemID[actionID]
                    if oldTbItemID is not None:
                        self.__toolbarItems[oldTbItemID].actionIDs.remove(
                            actionID)
                        self.__toolbarItems[oldTbItemID].isChanged = True
                        self.__toolBarItemToWidgetActionID[oldTbItemID].remove(
                            actionID)
                    self.__widgetActionToToolBarItemID[actionID] = tbItemID
                    self.__toolBarItemToWidgetActionID[tbItemID].append(
                        actionID)
        self.__toolbarComboBox_currentIndexChanged(
            self.toolbarComboBox.currentIndex())
    
    def __resetCurrentToolbar(self):
        """
        Private method to revert all changes made to the current toolbar.
        """
        tbID = self.__currentToolBarItem.toolBarId
        actions = self.__manager.toolBarActions(tbID)
        self.__restoreCurrentToolbar(actions)
        self.__currentToolBarItem.isChanged = False
    
    def __restoreCurrentToolbarToDefault(self):
        """
        Private method to set the current toolbar to its default configuration.
        """
        if not self.__currentToolBarItem.isDefault:
            return
        
        tbID = self.__currentToolBarItem.toolBarId
        actions = self.__manager.defaultToolBarActions(tbID)
        self.__restoreCurrentToolbar(actions)
        self.__currentToolBarItem.isChanged = True
