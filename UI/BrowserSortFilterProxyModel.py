# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the browser sort filter proxy model.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QModelIndex, QSortFilterProxyModel

import Preferences


class BrowserSortFilterProxyModel(QSortFilterProxyModel):
    """
    Class implementing the browser sort filter proxy model.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(BrowserSortFilterProxyModel, self).__init__(parent)
        self.hideNonPublic = Preferences.getUI("BrowsersHideNonPublic")
        
    def sort(self, column, order):
        """
        Public method to sort the items.
        
        @param column column number to sort on (integer)
        @param order sort order for the sort (Qt.SortOrder)
        """
        self.__sortColumn = column
        self.__sortOrder = order
        super(BrowserSortFilterProxyModel, self).sort(column, order)
        
    def lessThan(self, left, right):
        """
        Public method used to sort the displayed items.
        
        It implements a special sorting function that takes into account,
        if folders should be shown first, and that __init__ is always the first
        method of a class.
        
        @param left index of left item (QModelIndex)
        @param right index of right item (QModelIndex)
        @return true, if left is less than right (boolean)
        """
        le = left.model() and left.model().item(left) or None
        ri = right.model() and right.model().item(right) or None
        
        if le and ri:
            return le.lessThan(ri, self.__sortColumn, self.__sortOrder)
        
        return False
        
    def item(self, index):
        """
        Public method to get a reference to an item.
        
        @param index index of the data to retrieve (QModelIndex)
        @return requested item reference (BrowserItem)
        """
        if not index.isValid():
            return None
        
        sindex = self.mapToSource(index)
        return self.sourceModel().item(sindex)
    
    def hasChildren(self, parent=QModelIndex()):
        """
        Public method to check for the presence of child items.
        
        We always return True for normal items in order to do lazy
        population of the tree.
        
        @param parent index of parent item (QModelIndex)
        @return flag indicating the presence of child items (boolean)
        """
        sindex = self.mapToSource(parent)
        return self.sourceModel().hasChildren(sindex)

    def filterAcceptsRow(self, source_row, source_parent):
        """
        Public method to filter rows.
        
        It implements a filter to suppress the display of non public
        classes, methods and attributes.
        
        @param source_row row number (in the source model) of item (integer)
        @param source_parent index of parent item (in the source model)
            of item (QModelIndex)
        @return flag indicating, if the item should be shown (boolean)
        """
        if self.hideNonPublic:
            sindex = self.sourceModel().index(source_row, 0, source_parent)
            return self.sourceModel().item(sindex).isPublic()
        else:
            return True
    
    def preferencesChanged(self):
        """
        Public slot called to handle a change of the preferences settings.
        """
        hideNonPublic = Preferences.getUI("BrowsersHideNonPublic")
        if self.hideNonPublic != hideNonPublic:
            self.hideNonPublic = hideNonPublic
            self.invalidateFilter()
