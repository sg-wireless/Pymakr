# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#


"""
Module implementing the Plugin Info Dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QDialog, QTreeWidgetItem, QHeaderView, QMenu

from .Ui_PluginInfoDialog import Ui_PluginInfoDialog


class PluginInfoDialog(QDialog, Ui_PluginInfoDialog):
    """
    Class implementing the Plugin Info Dialog.
    """
    def __init__(self, pluginManager, parent=None):
        """
        Constructor
        
        @param pluginManager reference to the plugin manager object
        @param parent parent of this dialog (QWidget)
        """
        super(PluginInfoDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.pm = pluginManager
        
        self.__autoActivateColumn = 3
        self.__activeColumn = 4
        
        self.pluginList.headerItem().setText(self.pluginList.columnCount(), "")
        
        # populate the list
        self.__populateList()
        self.pluginList.sortByColumn(0, Qt.AscendingOrder)
        
        self.__menu = QMenu(self)
        self.__menu.addAction(self.tr('Show details'), self.__showDetails)
        self.__activateAct = self.__menu.addAction(
            self.tr('Activate'), self.__activatePlugin)
        self.__deactivateAct = self.__menu.addAction(
            self.tr('Deactivate'), self.__deactivatePlugin)
        self.pluginList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pluginList.customContextMenuRequested.connect(
            self.__showContextMenu)
    
    def __populateList(self):
        """
        Private method to (re)populate the list of plugins.
        """
        self.pluginList.clear()
        for info in self.pm.getPluginInfos():
            self.__createEntry(info)
        self.pluginList.sortItems(
            self.pluginList.sortColumn(),
            self.pluginList.header().sortIndicatorOrder())
        
    def __createEntry(self, info):
        """
        Private method to create a list entry based on the provided info.
        
        @param info tuple giving the info for the entry
        """
        infoList = [
            info[0],
            info[1],
            info[2],
            (info[3] and self.tr("Yes") or self.tr("No")),
            (info[4] and self.tr("Yes") or self.tr("No")),
            info[5]
        ]
        itm = QTreeWidgetItem(self.pluginList, infoList)
        if info[6]:
            # plugin error
            for col in range(self.pluginList.columnCount()):
                itm.setForeground(col, QBrush(Qt.red))
        itm.setTextAlignment(self.__autoActivateColumn, Qt.AlignHCenter)
        itm.setTextAlignment(self.__activeColumn, Qt.AlignHCenter)
        
        self.pluginList.header().resizeSections(QHeaderView.ResizeToContents)
        self.pluginList.header().setStretchLastSection(True)
    
    def __showContextMenu(self, coord):
        """
        Private slot to show the context menu of the listview.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        itm = self.pluginList.itemAt(coord)
        if itm is not None:
            autoactivate = (itm.text(self.__autoActivateColumn) ==
                            self.tr("Yes"))
            if itm.text(self.__activeColumn) == self.tr("Yes"):
                self.__activateAct.setEnabled(False)
                self.__deactivateAct.setEnabled(autoactivate)
            else:
                self.__activateAct.setEnabled(autoactivate)
                self.__deactivateAct.setEnabled(False)
            self.__menu.popup(self.mapToGlobal(coord))
    
    @pyqtSlot(QTreeWidgetItem, int)
    def on_pluginList_itemActivated(self, item, column):
        """
        Private slot to show details about a plugin.
        
        @param item reference to the selected item (QTreeWidgetItem)
        @param column column number (integer)
        """
        moduleName = item.text(0)
        details = self.pm.getPluginDetails(moduleName)
        if details is None:
            pass
        else:
            from .PluginDetailsDialog import PluginDetailsDialog
            dlg = PluginDetailsDialog(details, self)
            dlg.show()
    
    def __showDetails(self):
        """
        Private slot to handle the "Show details" context menu action.
        """
        itm = self.pluginList.currentItem()
        self.on_pluginList_itemActivated(itm, 0)
    
    def __activatePlugin(self):
        """
        Private slot to handle the "Deactivate" context menu action.
        """
        itm = self.pluginList.currentItem()
        moduleName = itm.text(0)
        self.pm.activatePlugin(moduleName)
        # repopulate the list
        self.__populateList()
    
    def __deactivatePlugin(self):
        """
        Private slot to handle the "Activate" context menu action.
        """
        itm = self.pluginList.currentItem()
        moduleName = itm.text(0)
        self.pm.deactivatePlugin(moduleName)
        # repopulate the list
        self.__populateList()
