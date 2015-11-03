# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to list the configured IRC networks.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QTreeWidgetItem

from E5Gui import E5MessageBox

from .Ui_IrcNetworkListDialog import Ui_IrcNetworkListDialog


class IrcNetworkListDialog(QDialog, Ui_IrcNetworkListDialog):
    """
    Class implementing a dialog to list the configured IRC networks.
    """
    def __init__(self, manager, parent=None):
        """
        Constructor
        
        @param manager reference to the IRC network manager (IrcNetworkManager)
        @param parent reference to the parent widget (QWidget)
        """
        super(IrcNetworkListDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__manager = manager
        
        self.__refreshNetworksList()

    def __resizeColumns(self):
        """
        Private slot to resize all columns to their contents.
        """
        for col in range(self.networksList.columnCount()):
            self.networksList.resizeColumnToContents(col)
    
    def __checkButtons(self):
        """
        Private slot to set the enabled state of the buttons.
        """
        enable = True
        selectedItems = self.networksList.selectedItems()
        if len(selectedItems) == 0:
            enable = False
        else:
            for itm in selectedItems:
                enable &= itm.parent() is None
        
        self.editButton.setEnabled(enable)
        self.deleteButton.setEnabled(enable)
        self.autoConnectButton.setEnabled(enable)
        
        if enable:
            itm = self.networksList.selectedItems()[0]
            check = self.__manager.getNetwork(itm.text(0)).autoConnect()
            self.autoConnectButton.setChecked(check)
    
    def __refreshNetworkEntry(self, itm):
        """
        Private method to (re-)set the data of a network entry.
        
        @param itm reference to the network entry (QTreeWidgetItem)
        """
        # step 1: delete all child entries
        children = itm.takeChildren()
        for child in children:
            del child
        
        # step 2: (re-)add the child entries
        from .IrcNetworkManager import IrcIdentity
        networkName = itm.text(0)
        network = self.__manager.getNetwork(networkName)
        server = network.getServer()
        identityName = network.getIdentityName()
        if identityName == IrcIdentity.DefaultIdentityName:
            identityName = IrcIdentity.DefaultIdentityDisplay
        autoConnect = self.tr("Yes") if network.autoConnect() \
            else self.tr("No")
        
        QTreeWidgetItem(
            itm,
            [self.tr("Identity"), identityName])
        QTreeWidgetItem(
            itm,
            [self.tr("Server"), "{0}:{1}".format(
             server.getName(), server.getPort())])
        QTreeWidgetItem(
            itm,
            [self.tr("Channels"), ", ".join(network.getChannelNames())])
        QTreeWidgetItem(
            itm,
            [self.tr("Auto-Connect"), autoConnect])
        
        self.__resizeColumns()
    
    def __refreshNetworksList(self):
        """
        Private method to refresh the complete networks list.
        """
        self.networksList.clear()
        
        networkNames = self.__manager.getNetworkNames()
        for networkName in networkNames:
            topitm = QTreeWidgetItem(self.networksList, [networkName])
            self.__refreshNetworkEntry(topitm)
            topitm.setExpanded(True)
        self.__resizeColumns()
        
        self.__checkButtons()
    
    @pyqtSlot()
    def on_networksList_itemSelectionChanged(self):
        """
        Private slot to handle changes of the selection of networks.
        """
        self.__checkButtons()
    
    @pyqtSlot()
    def on_newButton_clicked(self):
        """
        Private slot to add a new network entry.
        """
        from .IrcNetworkEditDialog import IrcNetworkEditDialog
        dlg = IrcNetworkEditDialog(self.__manager, "", self)
        if dlg.exec_() == QDialog.Accepted:
            network = dlg.getNetwork()
            self.__manager.addNetwork(network)
            self.__refreshNetworksList()
    
    @pyqtSlot()
    def on_editButton_clicked(self):
        """
        Private slot to edit the selected network.
        """
        itm = self.networksList.selectedItems()[0]
        if itm:
            from .IrcNetworkEditDialog import IrcNetworkEditDialog
            networkName = itm.text(0)
            dlg = IrcNetworkEditDialog(self.__manager, networkName, self)
            if dlg.exec_() == QDialog.Accepted:
                network = dlg.getNetwork()
                self.__manager.setNetwork(network, networkName)
                if network.getName() != networkName:
                    itm.setText(0, network.getName())
                self.__refreshNetworkEntry(itm)
    
    @pyqtSlot()
    def on_deleteButton_clicked(self):
        """
        Private slot to delete the selected entry.
        """
        itm = self.networksList.selectedItems()[0]
        if itm.parent() is None:
            networkName = itm.text(0)
            res = E5MessageBox.yesNo(
                self,
                self.tr("Delete Irc Network"),
                self.tr(
                    """Do you really want to delete IRC network <b>{0}</b>?""")
                .format(networkName))
            if res:
                index = self.networksList.indexOfTopLevelItem(itm)
                self.networksList.takeTopLevelItem(index)
                del itm
                
                self.__manager.deleteNetwork(networkName)
    
    @pyqtSlot(QTreeWidgetItem)
    def on_networksList_itemExpanded(self, item):
        """
        Private slot handling the expansion of a top level item.
        
        @param item reference to the expanded item (QTreeWidgetItem)
        """
        self.__resizeColumns()
    
    @pyqtSlot(QTreeWidgetItem)
    def on_networksList_itemCollapsed(self, item):
        """
        Private slot handling the collapse of a top level item.
        
        @param item reference to the collapsed item (QTreeWidgetItem)
        """
        self.__resizeColumns()
    
    @pyqtSlot(bool)
    def on_autoConnectButton_clicked(self, checked):
        """
        Private slot handling the auto-connect selection.
        
        @param checked flag indicating the state of the button (boolean)
        """
        itm = self.networksList.selectedItems()[0]
        if itm.parent() is None:
            networkName = itm.text(0)
            if checked:
                # enable the selected network, disable all others
                # step 1: update network objects
                for name in self.__manager.getNetworkNames():
                    network = self.__manager.getNetwork(networkName)
                    if name == networkName:
                        network.setAutoConnect(True)
                    else:
                        network.setAutoConnect(False)
                    self.__manager.networkChanged()
                
                # step 2: update list entries
                for index in range(self.networksList.topLevelItemCount()):
                    titm = self.networksList.topLevelItem(index)
                    if titm.text(0) == networkName:
                        self.__setAutoConnectEntry(titm, True)
                    else:
                        self.__setAutoConnectEntry(titm, False)
            else:
                # step 1: update network object
                network = self.__manager.getNetwork(networkName)
                network.setAutoConnect(False)
                self.__manager.networkChanged()
                
                # step 2: update list entry
                self.__setAutoConnectEntry(itm, False)
    
    def __setAutoConnectEntry(self, itm, on):
        """
        Private method to set the auto-connect entry of a network item.
        
        @param itm reference to the network item (QTreeWidgetItem)
        @param on flag indicating the auto-connect state (boolean)
        """
        autoConnect = self.tr("Yes") if on else self.tr("No")
        for index in range(itm.childCount()):
            citm = itm.child(index)
            if citm.text(0) == self.tr("Auto-Connect"):
                citm.setText(1, autoConnect)
    
    @pyqtSlot()
    def on_editIdentitiesButton_clicked(self):
        """
        Private slot to edit the identities.
        """
        from .IrcIdentitiesEditDialog import IrcIdentitiesEditDialog
        dlg = IrcIdentitiesEditDialog(self.__manager, "", self)
        dlg.exec_()
        
        selectedNetwork = self.networksList.selectedItems()
        if selectedNetwork:
            selectedNetworkName = selectedNetwork[0].text(0)
        else:
            selectedNetworkName = ""
        self.__refreshNetworksList()
        if selectedNetworkName:
            for index in range(self.networksList.topLevelItemCount()):
                itm = self.networksList.topLevelItem(index)
                if itm.text(0) == selectedNetworkName:
                    itm.setSelected(True)
                    break
