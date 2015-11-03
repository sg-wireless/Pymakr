# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing specialized tree views.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView


class E5TreeWidget(QTreeWidget):
    """
    Class implementing an extended tree widget.
    
    @signal itemControlClicked(QTreeWidgetItem) emitted after a Ctrl-Click
            on an item
    @signal itemMiddleButtonClicked(QTreeWidgetItem) emitted after a click
            of the middle button on an item
    """
    ItemsCollapsed = 0
    ItemsExpanded = 1
    
    itemControlClicked = pyqtSignal(QTreeWidgetItem)
    itemMiddleButtonClicked = pyqtSignal(QTreeWidgetItem)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(E5TreeWidget, self).__init__(parent)
        
        self.__refreshAllItemsNeeded = True
        self.__allTreeItems = []
        self.__showMode = E5TreeWidget.ItemsCollapsed
        
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        
        self.itemChanged.connect(self.__scheduleRefresh)
    
    def setDefaultItemShowMode(self, mode):
        """
        Public method to set the default item show mode.
        
        @param mode default mode (ItemsCollapsed, ItemsExpanded)
        """
        assert mode in [E5TreeWidget.ItemsCollapsed,
                        E5TreeWidget.ItemsExpanded]
        
        self.__showMode = mode
    
    def allItems(self):
        """
        Public method to get a list of all items.
        
        @return list of all items (list of QTreeWidgetItem)
        """
        if self.__refreshAllItemsNeeded:
            self.__allTreeItems = []
            self.__iterateAllItems(None)
            self.__refreshAllItemsNeeded = False
        
        return self.__allTreeItems
    
    def appendToParentItem(self, parent, item):
        """
        Public method to append an item to a parent item.
        
        @param parent text of the parent item (string) or
            the parent item (QTreeWidgetItem)
        @param item item to be appended (QTreeWidgetItem)
        @return flag indicating success (boolean)
        @exception RuntimeError raised to indicate an illegal type for
            the parent
        """
        if isinstance(parent, QTreeWidgetItem):
            if parent is None or parent.treeWidget() != self:
                return False
            parentItem = parent
        elif isinstance(parent, str):
            lst = self.findItems(parent, Qt.MatchExactly)
            if not lst:
                return False
            parentItem = lst[0]
            if parentItem is None:
                return False
        else:
            raise RuntimeError("illegal type for parent")
        
        self.__allTreeItems.append(item)
        parentItem.addChild(item)
        return True
    
    def prependToParentItem(self, parent, item):
        """
        Public method to prepend an item to a parent item.
        
        @param parent text of the parent item (string) or
            the parent item (QTreeWidgetItem)
        @param item item to be prepended (QTreeWidgetItem)
        @return flag indicating success (boolean)
        @exception RuntimeError raised to indicate an illegal type for
            the parent
        """
        if isinstance(parent, QTreeWidgetItem):
            if parent is None or parent.treeWidget() != self:
                return False
            parentItem = parent
        elif isinstance(parent, str):
            lst = self.findItems(parent, Qt.MatchExactly)
            if not lst:
                return False
            parentItem = lst[0]
            if parentItem is None:
                return False
        else:
            raise RuntimeError("illegal type for parent")
        
        self.__allTreeItems.append(item)
        parentItem.insertChild(0, item)
        return True
    
    def addTopLevelItem(self, item):
        """
        Public method to add a top level item.
        
        @param item item to be added as a top level item (QTreeWidgetItem)
        """
        self.__allTreeItems.append(item)
        super(E5TreeWidget, self).addTopLevelItem(item)
    
    def addTopLevelItems(self, items):
        """
        Public method to add a list of top level items.
        
        @param items items to be added as top level items
            (list of QTreeWidgetItem)
        """
        self.__allTreeItems.extend(items)
        super(E5TreeWidget, self).addTopLevelItems(items)
    
    def insertTopLevelItem(self, index, item):
        """
        Public method to insert a top level item.
        
        @param index index for the insertion (integer)
        @param item item to be inserted as a top level item (QTreeWidgetItem)
        """
        self.__allTreeItems.append(item)
        super(E5TreeWidget, self).insertTopLevelItem(index, item)
    
    def insertTopLevelItems(self, index, items):
        """
        Public method to insert a list of top level items.
        
        @param index index for the insertion (integer)
        @param items items to be inserted as top level items
            (list of QTreeWidgetItem)
        """
        self.__allTreeItems.extend(items)
        super(E5TreeWidget, self).insertTopLevelItems(index, items)
    
    def deleteItem(self, item):
        """
        Public method to delete an item.
        
        @param item item to be deleted (QTreeWidgetItem)
        """
        if item in self.__allTreeItems:
            self.__allTreeItems.remove(item)
        
        self.__refreshAllItemsNeeded = True
        
        del item
    
    def deleteItems(self, items):
        """
        Public method to delete a list of items.
        
        @param items items to be deleted (list of QTreeWidgetItem)
        """
        for item in items:
            self.deleteItem(item)
    
    def filterString(self, filter):
        """
        Public slot to set a new filter.
        
        @param filter filter to be set (string)
        """
        self.expandAll()
        allItems = self.allItems()
        
        if filter:
            lFilter = filter.lower()
            for itm in allItems:
                itm.setHidden(lFilter not in itm.text(0).lower())
                itm.setExpanded(True)
            for index in range(self.topLevelItemCount()):
                self.topLevelItem(index).setHidden(False)
            
            firstItm = self.topLevelItem(0)
            belowItm = self.itemBelow(firstItm)
            topLvlIndex = 0
            while firstItm:
                if lFilter in firstItm.text(0).lower():
                    firstItm.setHidden(False)
                elif not firstItm.parent() and not belowItm:
                    firstItm.setHidden(True)
                elif not belowItm:
                    break
                elif not firstItm.parent() and not belowItm.parent():
                    firstItm.setHidden(True)
                
                topLvlIndex += 1
                firstItm = self.topLevelItem(topLvlIndex)
                belowItm = self.itemBelow(firstItm)
        else:
            for itm in allItems:
                itm.setHidden(False)
            for index in range(self.topLevelItemCount()):
                self.topLevelItem(index).setHidden(False)
            if self.__showMode == E5TreeWidget.ItemsCollapsed:
                self.collapseAll()
    
    def clear(self):
        """
        Public slot to clear the tree.
        """
        self.__allTreeItems = []
        super(E5TreeWidget, self).clear()
    
    def __scheduleRefresh(self):
        """
        Private slot to schedule a refresh of the tree.
        """
        self.__refreshAllItemsNeeded = True
    
    def mousePressEvent(self, evt):
        """
        Protected method handling mouse press events.
        
        @param evt mouse press event (QMouseEvent)
        """
        if evt.modifiers() == Qt.ControlModifier and \
           evt.buttons() == Qt.LeftButton:
            self.itemControlClicked.emit(self.itemAt(evt.pos()))
            return
        elif evt.buttons() == Qt.MidButton:
            self.itemMiddleButtonClicked.emit(self.itemAt(evt.pos()))
            return
        else:
            super(E5TreeWidget, self).mousePressEvent(evt)
    
    def __iterateAllItems(self, parent):
        """
        Private method to iterate over the child items of the parent.
        
        @param parent parent item to iterate (QTreeWidgetItem)
        """
        if parent:
            count = parent.childCount()
        else:
            count = self.topLevelItemCount()
        
        for index in range(count):
            if parent:
                itm = parent.child(index)
            else:
                itm = self.topLevelItem(index)
            
            if itm.childCount() == 0:
                self.__allTreeItems.append(itm)
            
            self.__iterateAllItems(itm)
