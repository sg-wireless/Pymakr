# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the watch expression viewer widget.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QModelIndex, qVersion, QItemSelectionModel, \
    QSortFilterProxyModel
from PyQt5.QtWidgets import QTreeView, QAbstractItemView, QMenu, QHeaderView, \
    QDialog

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox

import Utilities


class WatchPointViewer(QTreeView):
    """
    Class implementing the watch expression viewer widget.
    
    Watch expressions will be shown with all their details. They can be
    modified through the context menu of this widget.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent the parent (QWidget)
        """
        super(WatchPointViewer, self).__init__(parent)
        self.setObjectName("WatchExpressionViewer")
        
        self.__model = None
        
        self.setItemsExpandable(False)
        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        self.setWindowTitle(self.tr("Watchpoints"))
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__showContextMenu)
        self.doubleClicked.connect(self.__doubleClicked)
        
        self.__createPopupMenus()
        
    def setModel(self, model):
        """
        Public slot to set the watch expression model.
        
        @param model reference to the watch expression model (WatchPointModel)
        """
        self.__model = model
        
        self.sortingModel = QSortFilterProxyModel()
        self.sortingModel.setDynamicSortFilter(True)
        self.sortingModel.setSourceModel(self.__model)
        super(WatchPointViewer, self).setModel(self.sortingModel)
        
        header = self.header()
        header.setSortIndicator(0, Qt.AscendingOrder)
        header.setSortIndicatorShown(True)
        if qVersion() >= "5.0.0":
            header.setSectionsClickable(True)
        else:
            header.setClickable(True)
        
        self.setSortingEnabled(True)
        
        self.__layoutDisplay()
        
    def __layoutDisplay(self):
        """
        Private slot to perform a layout operation.
        """
        self.__resizeColumns()
        self.__resort()
        
    def __resizeColumns(self):
        """
        Private slot to resize the view when items get added, edited or
        deleted.
        """
        self.header().resizeSections(QHeaderView.ResizeToContents)
        self.header().setStretchLastSection(True)
    
    def __resort(self):
        """
        Private slot to resort the tree.
        """
        self.model().sort(self.header().sortIndicatorSection(),
                          self.header().sortIndicatorOrder())
        
    def __toSourceIndex(self, index):
        """
        Private slot to convert an index to a source index.
        
        @param index index to be converted (QModelIndex)
        @return mapped index (QModelIndex)
        """
        return self.sortingModel.mapToSource(index)
        
    def __fromSourceIndex(self, sindex):
        """
        Private slot to convert a source index to an index.
        
        @param sindex source index to be converted (QModelIndex)
        @return mapped index (QModelIndex)
        """
        return self.sortingModel.mapFromSource(sindex)
        
    def __setRowSelected(self, index, selected=True):
        """
        Private slot to select a complete row.
        
        @param index index determining the row to be selected (QModelIndex)
        @param selected flag indicating the action (bool)
        """
        if not index.isValid():
            return
        
        if selected:
            flags = QItemSelectionModel.SelectionFlags(
                QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        else:
            flags = QItemSelectionModel.SelectionFlags(
                QItemSelectionModel.Deselect | QItemSelectionModel.Rows)
        self.selectionModel().select(index, flags)
        
    def __createPopupMenus(self):
        """
        Private method to generate the popup menus.
        """
        self.menu = QMenu()
        self.menu.addAction(self.tr("Add"), self.__addWatchPoint)
        self.menu.addAction(self.tr("Edit..."), self.__editWatchPoint)
        self.menu.addSeparator()
        self.menu.addAction(self.tr("Enable"), self.__enableWatchPoint)
        self.menu.addAction(self.tr("Enable all"),
                            self.__enableAllWatchPoints)
        self.menu.addSeparator()
        self.menu.addAction(self.tr("Disable"), self.__disableWatchPoint)
        self.menu.addAction(self.tr("Disable all"),
                            self.__disableAllWatchPoints)
        self.menu.addSeparator()
        self.menu.addAction(self.tr("Delete"), self.__deleteWatchPoint)
        self.menu.addAction(self.tr("Delete all"),
                            self.__deleteAllWatchPoints)
        self.menu.addSeparator()
        self.menu.addAction(self.tr("Configure..."), self.__configure)

        self.backMenuActions = {}
        self.backMenu = QMenu()
        self.backMenu.addAction(self.tr("Add"), self.__addWatchPoint)
        self.backMenuActions["EnableAll"] = \
            self.backMenu.addAction(self.tr("Enable all"),
                                    self.__enableAllWatchPoints)
        self.backMenuActions["DisableAll"] = \
            self.backMenu.addAction(self.tr("Disable all"),
                                    self.__disableAllWatchPoints)
        self.backMenuActions["DeleteAll"] = \
            self.backMenu.addAction(self.tr("Delete all"),
                                    self.__deleteAllWatchPoints)
        self.backMenu.addSeparator()
        self.backMenu.addAction(self.tr("Configure..."), self.__configure)
        self.backMenu.aboutToShow.connect(self.__showBackMenu)

        self.multiMenu = QMenu()
        self.multiMenu.addAction(self.tr("Add"), self.__addWatchPoint)
        self.multiMenu.addSeparator()
        self.multiMenu.addAction(self.tr("Enable selected"),
                                 self.__enableSelectedWatchPoints)
        self.multiMenu.addAction(self.tr("Enable all"),
                                 self.__enableAllWatchPoints)
        self.multiMenu.addSeparator()
        self.multiMenu.addAction(self.tr("Disable selected"),
                                 self.__disableSelectedWatchPoints)
        self.multiMenu.addAction(self.tr("Disable all"),
                                 self.__disableAllWatchPoints)
        self.multiMenu.addSeparator()
        self.multiMenu.addAction(self.tr("Delete selected"),
                                 self.__deleteSelectedWatchPoints)
        self.multiMenu.addAction(self.tr("Delete all"),
                                 self.__deleteAllWatchPoints)
        self.multiMenu.addSeparator()
        self.multiMenu.addAction(self.tr("Configure..."), self.__configure)
    
    def __showContextMenu(self, coord):
        """
        Private slot to show the context menu.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        cnt = self.__getSelectedItemsCount()
        if cnt <= 1:
            index = self.indexAt(coord)
            if index.isValid():
                cnt = 1
                self.__setRowSelected(index)
        coord = self.mapToGlobal(coord)
        if cnt > 1:
            self.multiMenu.popup(coord)
        elif cnt == 1:
            self.menu.popup(coord)
        else:
            self.backMenu.popup(coord)
    
    def __clearSelection(self):
        """
        Private slot to clear the selection.
        """
        for index in self.selectedIndexes():
            self.__setRowSelected(index, False)
    
    def __findDuplicates(self, cond, special, showMessage=False,
                         index=QModelIndex()):
        """
        Private method to check, if an entry already exists.
        
        @param cond condition to check (string)
        @param special special condition to check (string)
        @param showMessage flag indicating a message should be shown,
            if a duplicate entry is found (boolean)
        @param index index that should not be considered duplicate
            (QModelIndex)
        @return flag indicating a duplicate entry (boolean)
        """
        idx = self.__model.getWatchPointIndex(cond, special)
        duplicate = idx.isValid() and \
            idx.internalPointer() != index.internalPointer()
        if showMessage and duplicate:
            if not special:
                msg = self.tr("""<p>A watch expression '<b>{0}</b>'"""
                              """ already exists.</p>""")\
                    .format(Utilities.html_encode(cond))
            else:
                msg = self.tr(
                    """<p>A watch expression '<b>{0}</b>'"""
                    """ for the variable <b>{1}</b> already exists.</p>""")\
                    .format(special, Utilities.html_encode(cond))
            E5MessageBox.warning(
                self,
                self.tr("Watch expression already exists"),
                msg)
        
        return duplicate
    
    def __addWatchPoint(self):
        """
        Private slot to handle the add watch expression context menu entry.
        """
        from .EditWatchpointDialog import EditWatchpointDialog
        dlg = EditWatchpointDialog(("", False, True, 0, ""), self)
        if dlg.exec_() == QDialog.Accepted:
            cond, temp, enabled, ignorecount, special = dlg.getData()
            if not self.__findDuplicates(cond, special, True):
                self.__model.addWatchPoint(cond, special,
                                           (temp, enabled, ignorecount))
                self.__resizeColumns()
                self.__resort()

    def __doubleClicked(self, index):
        """
        Private slot to handle the double clicked signal.
        
        @param index index of the entry that was double clicked (QModelIndex)
        """
        if index.isValid():
            self.__doEditWatchPoint(index)

    def __editWatchPoint(self):
        """
        Private slot to handle the edit watch expression context menu entry.
        """
        index = self.currentIndex()
        if index.isValid():
            self.__doEditWatchPoint(index)
    
    def __doEditWatchPoint(self, index):
        """
        Private slot to edit a watch expression.
        
        @param index index of watch expression to be edited (QModelIndex)
        """
        sindex = self.__toSourceIndex(index)
        if sindex.isValid():
            wp = self.__model.getWatchPointByIndex(sindex)
            if not wp:
                return
            
            cond, special, temp, enabled, count = wp[:5]
            
            from .EditWatchpointDialog import EditWatchpointDialog
            dlg = EditWatchpointDialog(
                (cond, temp, enabled, count, special), self)
            if dlg.exec_() == QDialog.Accepted:
                cond, temp, enabled, count, special = dlg.getData()
                if not self.__findDuplicates(cond, special, True, sindex):
                    self.__model.setWatchPointByIndex(
                        sindex, cond, special, (temp, enabled, count))
                    self.__resizeColumns()
                    self.__resort()

    def __setWpEnabled(self, index, enabled):
        """
        Private method to set the enabled status of a watch expression.
        
        @param index index of watch expression to be enabled/disabled
            (QModelIndex)
        @param enabled flag indicating the enabled status to be set (boolean)
        """
        sindex = self.__toSourceIndex(index)
        if sindex.isValid():
            self.__model.setWatchPointEnabledByIndex(sindex, enabled)
        
    def __enableWatchPoint(self):
        """
        Private slot to handle the enable watch expression context menu entry.
        """
        index = self.currentIndex()
        self.__setWpEnabled(index, True)
        self.__resizeColumns()
        self.__resort()

    def __enableAllWatchPoints(self):
        """
        Private slot to handle the enable all watch expressions context menu
        entry.
        """
        index = self.model().index(0, 0)
        while index.isValid():
            self.__setWpEnabled(index, True)
            index = self.indexBelow(index)
        self.__resizeColumns()
        self.__resort()

    def __enableSelectedWatchPoints(self):
        """
        Private slot to handle the enable selected watch expressions context
        menu entry.
        """
        for index in self.selectedIndexes():
            if index.column() == 0:
                self.__setWpEnabled(index, True)
        self.__resizeColumns()
        self.__resort()

    def __disableWatchPoint(self):
        """
        Private slot to handle the disable watch expression context menu entry.
        """
        index = self.currentIndex()
        self.__setWpEnabled(index, False)
        self.__resizeColumns()
        self.__resort()

    def __disableAllWatchPoints(self):
        """
        Private slot to handle the disable all watch expressions context menu
        entry.
        """
        index = self.model().index(0, 0)
        while index.isValid():
            self.__setWpEnabled(index, False)
            index = self.indexBelow(index)
        self.__resizeColumns()
        self.__resort()

    def __disableSelectedWatchPoints(self):
        """
        Private slot to handle the disable selected watch expressions context
        menu entry.
        """
        for index in self.selectedIndexes():
            if index.column() == 0:
                self.__setWpEnabled(index, False)
        self.__resizeColumns()
        self.__resort()

    def __deleteWatchPoint(self):
        """
        Private slot to handle the delete watch expression context menu entry.
        """
        index = self.currentIndex()
        sindex = self.__toSourceIndex(index)
        if sindex.isValid():
            self.__model.deleteWatchPointByIndex(sindex)
        
    def __deleteAllWatchPoints(self):
        """
        Private slot to handle the delete all watch expressions context menu
        entry.
        """
        self.__model.deleteAll()

    def __deleteSelectedWatchPoints(self):
        """
        Private slot to handle the delete selected watch expressions context
        menu entry.
        """
        idxList = []
        for index in self.selectedIndexes():
            sindex = self.__toSourceIndex(index)
            if sindex.isValid() and index.column() == 0:
                idxList.append(sindex)
        self.__model.deleteWatchPoints(idxList)

    def __showBackMenu(self):
        """
        Private slot to handle the aboutToShow signal of the background menu.
        """
        if self.model().rowCount() == 0:
            self.backMenuActions["EnableAll"].setEnabled(False)
            self.backMenuActions["DisableAll"].setEnabled(False)
            self.backMenuActions["DeleteAll"].setEnabled(False)
        else:
            self.backMenuActions["EnableAll"].setEnabled(True)
            self.backMenuActions["DisableAll"].setEnabled(True)
            self.backMenuActions["DeleteAll"].setEnabled(True)

    def __getSelectedItemsCount(self):
        """
        Private method to get the count of items selected.
        
        @return count of items selected (integer)
        """
        count = len(self.selectedIndexes()) // (self.__model.columnCount() - 1)
        # column count is 1 greater than selectable
        return count
    
    def __configure(self):
        """
        Private method to open the configuration dialog.
        """
        e5App().getObject("UserInterface")\
            .showPreferences("debuggerGeneralPage")
