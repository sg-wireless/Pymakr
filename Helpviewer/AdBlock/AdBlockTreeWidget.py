# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a tree widget for the AdBlock configuration dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QAbstractItemView, QTreeWidgetItem, QInputDialog, \
    QLineEdit, QMenu, QApplication

from E5Gui.E5TreeWidget import E5TreeWidget


class AdBlockTreeWidget(E5TreeWidget):
    """
    Class implementing a tree widget for the AdBlock configuration dialog.
    """
    def __init__(self, subscription, parent=None):
        """
        Constructor
        
        @param subscription reference to the subscription (AdBlockSubscription)
        @param parent reference to the parent widget (QWidget)
        """
        super(AdBlockTreeWidget, self).__init__(parent)
        
        self.__subscription = subscription
        self.__topItem = None
        self.__ruleToBeSelected = ""
        self.__itemChangingBlock = False
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setDefaultItemShowMode(E5TreeWidget.ItemsExpanded)
        self.setHeaderHidden(True)
        self.setAlternatingRowColors(True)
        
        self.customContextMenuRequested.connect(self.__contextMenuRequested)
        self.itemChanged.connect(self.__itemChanged)
        self.__subscription.changed.connect(self.__subscriptionChanged)
        self.__subscription.rulesChanged.connect(self.__subscriptionChanged)
    
    def subscription(self):
        """
        Public method to get a reference to the subscription.
        
        @return reference to the subscription (AdBlockSubscription)
        """
        return self.__subscription
    
    def showRule(self, rule):
        """
        Public method to highlight the given rule.
        
        @param rule AdBlock rule to be shown (AdBlockRule)
        """
        if rule:
            self.__ruleToBeSelected = rule.filter()
        if not self.__topItem:
            return
        if self.__ruleToBeSelected:
            items = self.findItems(self.__ruleToBeSelected, Qt.MatchRecursive)
            if items:
                item = items[0]
                self.setCurrentItem(item)
                self.scrollToItem(item, QAbstractItemView.PositionAtCenter)
            
            self.__ruleToBeSelected = ""
    
    def refresh(self):
        """
        Public method to refresh the tree.
        """
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.__itemChangingBlock = True
        self.clear()
        
        boldFont = QFont()
        boldFont.setBold(True)
        
        self.__topItem = QTreeWidgetItem(self)
        self.__topItem.setText(0, self.__subscription.title())
        self.__topItem.setFont(0, boldFont)
        self.addTopLevelItem(self.__topItem)
        
        allRules = self.__subscription.allRules()
        
        index = 0
        for rule in allRules:
            item = QTreeWidgetItem(self.__topItem)
            item.setText(0, rule.filter())
            item.setData(0, Qt.UserRole, index)
            if self.__subscription.canEditRules():
                item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.__adjustItemFeatures(item, rule)
            index += 1
        
        self.expandAll()
        self.showRule(None)
        self.__itemChangingBlock = False
        QApplication.restoreOverrideCursor()
        QApplication.processEvents()
    
    def addRule(self, filter=""):
        """
        Public slot to add a new rule.
        
        @param filter filter to be added (string)
        """
        if not self.__subscription.canEditRules():
            return
        
        if not filter:
            filter = QInputDialog.getText(
                self,
                self.tr("Add Custom Rule"),
                self.tr("Write your rule here:"),
                QLineEdit.Normal)
            if filter == "":
                return
        
        from .AdBlockRule import AdBlockRule
        rule = AdBlockRule(filter, self.__subscription)
        offset = self.__subscription.addRule(rule)
        
        item = QTreeWidgetItem()
        item.setText(0, filter)
        item.setData(0, Qt.UserRole, offset)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        
        self.__itemChangingBlock = True
        self.__topItem.addChild(item)
        self.__itemChangingBlock = False
        
        self.__adjustItemFeatures(item, rule)
    
    def removeRule(self):
        """
        Public slot to remove the current rule.
        """
        item = self.currentItem()
        if item is None or \
           not self.__subscription.canEditRules() or \
           item == self.__topItem:
            return
        
        offset = item.data(0, Qt.UserRole)
        self.__subscription.removeRule(offset)
        self.deleteItem(item)
    
    def __contextMenuRequested(self, pos):
        """
        Private slot to show the context menu.
        
        @param pos position for the menu (QPoint)
        """
        if not self.__subscription.canEditRules():
            return
        
        item = self.itemAt(pos)
        if item is None:
            return
        
        menu = QMenu()
        menu.addAction(self.tr("Add Rule"), self.addRule)
        menu.addSeparator()
        act = menu.addAction(self.tr("Remove Rule"), self.removeRule)
        if item.parent() is None:
            act.setDisabled(True)
        
        menu.exec_(self.viewport().mapToGlobal(pos))
    
    def __itemChanged(self, itm):
        """
        Private slot to handle the change of an item.
        
        @param itm changed item (QTreeWidgetItem)
        """
        if itm is None or self.__itemChangingBlock:
            return
        
        self.__itemChangingBlock = True
        
        offset = itm.data(0, Qt.UserRole)
        oldRule = self.__subscription.rule(offset)
        
        if itm.checkState(0) == Qt.Unchecked and oldRule.isEnabled():
            # Disable rule
            rule = self.__subscription.setRuleEnabled(offset, False)
            self.__adjustItemFeatures(itm, rule)
        elif itm.checkState(0) == Qt.Checked and not oldRule.isEnabled():
            # Enable rule
            rule = self.__subscription.setRuleEnabled(offset, True)
            self.__adjustItemFeatures(itm, rule)
        elif self.__subscription.canEditRules():
            from .AdBlockRule import AdBlockRule
            # Custom rule has been changed
            rule = self.__subscription.replaceRule(
                AdBlockRule(itm.text(0), self.__subscription), offset)
            self.__adjustItemFeatures(itm, rule)
        
        self.__itemChangingBlock = False
    
    def __copyFilter(self):
        """
        Private slot to copy the current filter to the clipboard.
        """
        item = self.currentItem()
        if item is not None:
            QApplication.clipboard().setText(item.text(0))
    
    def __subscriptionChanged(self):
        """
        Private slot handling a subscription change.
        """
        self.refresh()
        
        self.__itemChangingBlock = True
        self.__topItem.setText(
            0, self.tr("{0} (recently updated)").format(
                self.__subscription.title()))
        self.__itemChangingBlock = False
    
    def __adjustItemFeatures(self, itm, rule):
        """
        Private method to adjust an item.
        
        @param itm item to be adjusted (QTreeWidgetItem)
        @param rule rule for the adjustment (AdBlockRule)
        """
        if not rule.isEnabled():
            font = QFont()
            font.setItalic(True)
            itm.setForeground(0, QColor(Qt.gray))
            
            if not rule.isComment() and not rule.isHeader():
                itm.setFlags(itm.flags() | Qt.ItemIsUserCheckable)
                itm.setCheckState(0, Qt.Unchecked)
                itm.setFont(0, font)
            
            return
        
        itm.setFlags(itm.flags() | Qt.ItemIsUserCheckable)
        itm.setCheckState(0, Qt.Checked)
        
        if rule.isCSSRule():
            itm.setForeground(0, QColor(Qt.darkBlue))
            itm.setFont(0, QFont())
        elif rule.isException():
            itm.setForeground(0, QColor(Qt.darkGreen))
            itm.setFont(0, QFont())
        else:
            itm.setForeground(0, QColor())
            itm.setFont(0, QFont())
    
    def keyPressEvent(self, evt):
        """
        Protected method handling key presses.
        
        @param evt key press event (QKeyEvent)
        """
        if evt.key() == Qt.Key_C and \
           evt.modifiers() & Qt.ControlModifier:
            self.__copyFilter()
        elif evt.key() == Qt.Key_Delete:
            self.removeRule()
        else:
            super(AdBlockTreeWidget, self).keyPressEvent(evt)
