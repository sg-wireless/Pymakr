# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for editing IRC network definitions.
"""

from __future__ import unicode_literals

import copy

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QTreeWidgetItem

from E5Gui import E5MessageBox

from .Ui_IrcNetworkEditDialog import Ui_IrcNetworkEditDialog

import UI.PixmapCache


class IrcNetworkEditDialog(QDialog, Ui_IrcNetworkEditDialog):
    """
    Class implementing a dialog for editing IRC network definitions.
    """
    def __init__(self, manager, networkName, parent=None):
        """
        Constructor
        
        @param manager reference to the IRC network manager object
            (IrcNetworkManager)
        @param networkName name of the network to work on (string)
        @param parent reference to the parent widget (QWidget)
        """
        super(IrcNetworkEditDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__manager = manager
        
        self.editIdentitiesButton.setIcon(
            UI.PixmapCache.getIcon("ircConfigure.png"))
        self.editServerButton.setIcon(
            UI.PixmapCache.getIcon("ircConfigure.png"))
        self.editChannelButton.setIcon(
            UI.PixmapCache.getIcon("ircConfigure.png"))
        self.addChannelButton.setIcon(UI.PixmapCache.getIcon("plus.png"))
        self.deleteChannelButton.setIcon(UI.PixmapCache.getIcon("minus.png"))
        
        self.__okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        
        if networkName:
            self.__network = copy.deepcopy(
                self.__manager.getNetwork(networkName))
        else:
            from .IrcNetworkManager import IrcNetwork
            self.__network = IrcNetwork("")
        
        # network name
        self.networkEdit.setText(networkName)
        
        # identities
        self.__refreshIdentityCombo(self.__network.getIdentityName())
        
        # server
        self.serverEdit.setText(self.__network.getServerName())
        
        # channels
        for channelName in sorted(self.__network.getChannelNames()):
            channel = self.__network.getChannel(channelName)
            if channel.autoJoin():
                autoJoin = self.tr("Yes")
            else:
                autoJoin = self.tr("No")
            QTreeWidgetItem(self.channelList, [channelName, autoJoin])
        
        self.__updateOkButton()
        self.on_channelList_itemSelectionChanged()
    
    def __updateOkButton(self):
        """
        Private method to update the OK button state.
        """
        enable = True
        enable &= self.networkEdit.text() != ""
        enable &= self.serverEdit.text() != ""
        
        self.__okButton.setEnabled(enable)
    
    @pyqtSlot(str)
    def on_networkEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the network name.
        
        @param txt text entered into the network name edit (string)
        """
        self.__updateOkButton()
    
    def __refreshIdentityCombo(self, currentIdentity):
        """
        Private method to refresh the identity combo.
        
        @param currentIdentity name of the identity to select (string)
        """
        self.identityCombo.clear()
        
        from .IrcNetworkManager import IrcIdentity
        identities = list(sorted(self.__manager.getIdentityNames()))
        identities[identities.index(IrcIdentity.DefaultIdentityName)] = \
            IrcIdentity.DefaultIdentityDisplay
        self.identityCombo.addItems(identities)
        if currentIdentity == IrcIdentity.DefaultIdentityName:
            currentIdentity = IrcIdentity.DefaultIdentityDisplay
        index = self.identityCombo.findText(currentIdentity)
        if index == -1:
            index = 0
        self.identityCombo.setCurrentIndex(index)
    
    @pyqtSlot(str)
    def on_identityCombo_currentIndexChanged(self, identity):
        """
        Private slot to handle the selection of an identity.
        
        @param identity selected entity (string)
        """
        from .IrcNetworkManager import IrcIdentity
        if identity == IrcIdentity.DefaultIdentityDisplay:
            identity = IrcIdentity.DefaultIdentityName
        self.__network.setIdentityName(identity)
    
    @pyqtSlot()
    def on_editIdentitiesButton_clicked(self):
        """
        Private slot to edit the identities.
        """
        from .IrcIdentitiesEditDialog import IrcIdentitiesEditDialog
        currentIdentity = self.identityCombo.currentText()
        dlg = IrcIdentitiesEditDialog(self.__manager, currentIdentity, self)
        dlg.exec_()
        self.__refreshIdentityCombo(currentIdentity)
    
    @pyqtSlot(str)
    def on_serverEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the server name.
        
        @param txt text entered into the server name edit (string)
        """
        self.__updateOkButton()
    
    @pyqtSlot()
    def on_editServerButton_clicked(self):
        """
        Private slot to edit the server configuration.
        """
        from .IrcServerEditDialog import IrcServerEditDialog
        dlg = IrcServerEditDialog(self.__network.getServer())
        if dlg.exec_() == QDialog.Accepted:
            self.__network.setServer(dlg.getServer())
            self.serverEdit.setText(self.__network.getServerName())
    
    @pyqtSlot()
    def on_addChannelButton_clicked(self):
        """
        Private slot to add a channel.
        """
        self.__editChannel(None)
    
    @pyqtSlot()
    def on_editChannelButton_clicked(self):
        """
        Private slot to edit the selected channel.
        """
        itm = self.channelList.selectedItems()[0]
        if itm:
            self.__editChannel(itm)
    
    @pyqtSlot()
    def on_deleteChannelButton_clicked(self):
        """
        Private slot to delete the selected channel.
        """
        itm = self.channelList.selectedItems()[0]
        if itm:
            res = E5MessageBox.yesNo(
                self,
                self.tr("Delete Channel"),
                self.tr(
                    """Do you really want to delete channel <b>{0}</b>?""")
                .format(itm.text(0)))
            if res:
                self.__network.deleteChannel(itm.text(0))
                
                index = self.channelList.indexOfTopLevelItem(itm)
                self.channelList.takeTopLevelItem(index)
                del itm
    
    @pyqtSlot(QTreeWidgetItem, int)
    def on_channelList_itemActivated(self, item, column):
        """
        Private slot to handle the activation of a channel entry.
        
        @param item reference to the activated item (QTreeWidgetItem)
        @param column column the activation occurred in (integer)
        """
        self.__editChannel(item)
    
    @pyqtSlot()
    def on_channelList_itemSelectionChanged(self):
        """
        Private slot to handle changes of the selection of channels.
        """
        selectedItems = self.channelList.selectedItems()
        if len(selectedItems) == 0:
            enable = False
        else:
            enable = True
        self.editChannelButton.setEnabled(enable)
        self.deleteChannelButton.setEnabled(enable)
    
    def __editChannel(self, itm):
        """
        Private method to edit a channel.
        
        @param itm reference to the item to be edited (QTreeWidgetItem)
        """
        if itm:
            channel = self.__network.getChannel(itm.text(0))
            name = channel.getName()
            key = channel.getKey()
            autoJoin = channel.autoJoin()
        else:
            # add a new channel
            name = ""
            key = ""
            autoJoin = False
        
        from .IrcChannelEditDialog import IrcChannelEditDialog
        dlg = IrcChannelEditDialog(name, key, autoJoin, itm is not None, self)
        if dlg.exec_() == QDialog.Accepted:
            from .IrcNetworkManager import IrcChannel
            name, key, autoJoin = dlg.getData()
            channel = IrcChannel(name)
            channel.setKey(key)
            channel.setAutoJoin(autoJoin)
            if itm:
                if autoJoin:
                    itm.setText(1, self.tr("Yes"))
                else:
                    itm.setText(1, self.tr("No"))
                self.__network.setChannel(channel)
            else:
                if autoJoin:
                    autoJoinTxt = self.tr("Yes")
                else:
                    autoJoinTxt = self.tr("No")
                QTreeWidgetItem(self.channelList, [name, autoJoinTxt])
                self.__network.addChannel(channel)
    
    def getNetwork(self):
        """
        Public method to get the network object.
        
        @return edited network object (IrcNetwork)
        """
        self.__network.setName(self.networkEdit.text())
        return self.__network
