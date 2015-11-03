# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the network part of the IRC widget.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QPoint, QFileInfo, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QWidget, QApplication, QMenu

from E5Gui import E5MessageBox, E5FileDialog

from .Ui_IrcNetworkWidget import Ui_IrcNetworkWidget

from .IrcUtilities import ircFilter, ircTimestamp

import UI.PixmapCache
import Preferences
import Utilities


class IrcNetworkWidget(QWidget, Ui_IrcNetworkWidget):
    """
    Class implementing the network part of the IRC widget.
    
    @signal connectNetwork(str,bool) emitted to connect or disconnect from
        a network
    @signal editNetwork(str) emitted to edit a network configuration
    @signal joinChannel(str) emitted to join a channel
    @signal nickChanged(str) emitted to change the nick name
    @signal sendData(str) emitted to send a message to the channel
    @signal away(bool) emitted to indicate the away status
    @signal autoConnected() emitted after an automatic connection was initiated
    """
    connectNetwork = pyqtSignal(str, bool)
    editNetwork = pyqtSignal(str)
    joinChannel = pyqtSignal(str)
    nickChanged = pyqtSignal(str)
    sendData = pyqtSignal(str)
    away = pyqtSignal(bool)
    autoConnected = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(IrcNetworkWidget, self).__init__(parent)
        self.setupUi(self)
        
        self.connectButton.setIcon(UI.PixmapCache.getIcon("ircConnect.png"))
        self.editButton.setIcon(UI.PixmapCache.getIcon("ircConfigure.png"))
        self.joinButton.setIcon(UI.PixmapCache.getIcon("ircJoinChannel.png"))
        self.awayButton.setIcon(UI.PixmapCache.getIcon("ircUserPresent.png"))
        
        self.joinButton.setEnabled(False)
        self.nickCombo.setEnabled(False)
        self.awayButton.setEnabled(False)
        
        self.channelCombo.lineEdit().returnPressed.connect(
            self.on_joinButton_clicked)
        self.nickCombo.lineEdit().returnPressed.connect(
            self.on_nickCombo_currentIndexChanged)
        
        self.setConnected(False)
        
        self.__initMessagesMenu()
        
        self.__manager = None
        self.__connected = False
        self.__registered = False
        self.__away = False
    
    def initialize(self, manager):
        """
        Public method to initialize the widget.
        
        @param manager reference to the network manager (IrcNetworkManager)
        """
        self.__manager = manager
        
        self.networkCombo.addItems(self.__manager.getNetworkNames())
        
        self.__manager.networksChanged.connect(self.__refreshNetworks)
        self.__manager.identitiesChanged.connect(self.__refreshNetworks)
    
    def autoConnect(self):
        """
        Public method to perform the IRC auto connection.
        """
        for networkName in self.__manager.getNetworkNames():
            if self.__manager.getNetwork(networkName).autoConnect():
                row = self.networkCombo.findText(networkName)
                self.networkCombo.setCurrentIndex(row)
                self.on_connectButton_clicked()
                self.autoConnected.emit()
                break
    
    @pyqtSlot()
    def __refreshNetworks(self):
        """
        Private slot to refresh all network related widgets.
        """
        currentNetwork = self.networkCombo.currentText()
        currentNick = self.nickCombo.currentText()
        currentChannel = self.channelCombo.currentText()
        blocked = self.networkCombo.blockSignals(True)
        self.networkCombo.clear()
        self.networkCombo.addItems(self.__manager.getNetworkNames())
        self.networkCombo.blockSignals(blocked)
        row = self.networkCombo.findText(currentNetwork)
        if row == -1:
            row = 0
        blocked = self.nickCombo.blockSignals(True)
        self.networkCombo.setCurrentIndex(row)
        self.nickCombo.setEditText(currentNick)
        self.nickCombo.blockSignals(blocked)
        self.channelCombo.setEditText(currentChannel)
    
    @pyqtSlot()
    def on_connectButton_clicked(self):
        """
        Private slot to connect to a network.
        """
        network = self.networkCombo.currentText()
        self.connectNetwork.emit(network, not self.__connected)
    
    @pyqtSlot()
    def on_awayButton_clicked(self):
        """
        Private slot to toggle the away status.
        """
        if self.__away:
            self.sendData.emit("AWAY")
            self.awayButton.setIcon(
                UI.PixmapCache.getIcon("ircUserPresent.png"))
            self.__away = False
        else:
            networkName = self.networkCombo.currentText()
            identityName = self.__manager.getNetwork(networkName)\
                .getIdentityName()
            awayMessage = self.__manager.getIdentity(identityName)\
                .getAwayMessage()
            self.sendData.emit("AWAY :" + awayMessage)
            self.awayButton.setIcon(UI.PixmapCache.getIcon("ircUserAway.png"))
            self.__away = True
        self.away.emit(self.__away)
    
    @pyqtSlot()
    def on_editButton_clicked(self):
        """
        Private slot to edit a network.
        """
        network = self.networkCombo.currentText()
        self.editNetwork.emit(network)
    
    @pyqtSlot(str)
    def on_channelCombo_editTextChanged(self, txt):
        """
        Private slot to react upon changes of the channel.
        
        @param txt current text of the channel combo (string)
        """
        on = bool(txt) and self.__registered
        self.joinButton.setEnabled(on)
    
    @pyqtSlot()
    def on_joinButton_clicked(self):
        """
        Private slot to join a channel.
        """
        channel = self.channelCombo.currentText()
        self.joinChannel.emit(channel)
    
    @pyqtSlot(str)
    def on_networkCombo_currentIndexChanged(self, networkName):
        """
        Private slot to handle selections of a network.
        
        @param networkName selected network name (string)
        """
        network = self.__manager.getNetwork(networkName)
        self.nickCombo.clear()
        self.channelCombo.clear()
        if network:
            channels = network.getChannelNames()
            self.channelCombo.addItems(channels)
            self.channelCombo.setEnabled(True)
            identity = self.__manager.getIdentity(
                network.getIdentityName())
            if identity:
                self.nickCombo.addItems(identity.getNickNames())
        else:
            self.channelCombo.setEnabled(False)
    
    def getNetworkChannels(self):
        """
        Public method to get the list of channels associated with the
        selected network.
        
        @return associated channels (list of IrcChannel)
        """
        networkName = self.networkCombo.currentText()
        network = self.__manager.getNetwork(networkName)
        return network.getChannels()
    
    @pyqtSlot(str)
    def on_nickCombo_currentIndexChanged(self, nick=""):
        """
        Private slot to use another nick name.
        
        @param nick nick name to use (string)
        """
        if self.__connected:
            self.nickChanged.emit(self.nickCombo.currentText())
    
    def getNickname(self):
        """
        Public method to get the currently selected nick name.
        
        @return selected nick name (string)
        """
        return self.nickCombo.currentText()
    
    def setNickName(self, nick):
        """
        Public slot to set the nick name in use.
        
        @param nick nick name in use (string)
        """
        self.nickCombo.blockSignals(True)
        self.nickCombo.setEditText(nick)
        self.nickCombo.blockSignals(False)
    
    def addMessage(self, msg):
        """
        Public method to add a message.
        
        @param msg message to be added (string)
        """
        s = '<font color="{0}">{1} {2}</font>'.format(
            Preferences.getIrc("NetworkMessageColour"),
            ircTimestamp(),
            msg
        )
        self.messages.append(s)
    
    def addServerMessage(self, msgType, msg, filterMsg=True):
        """
        Public method to add a server message.
        
        @param msgType txpe of the message (string)
        @param msg message to be added (string)
        @keyparam filterMsg flag indicating to filter the message (boolean)
        """
        if filterMsg:
            msg = ircFilter(msg)
        s = '<font color="{0}">{1} <b>[</b>{2}<b>]</b> {3}</font>'.format(
            Preferences.getIrc("ServerMessageColour"),
            ircTimestamp(),
            msgType,
            msg
        )
        self.messages.append(s)
    
    def addErrorMessage(self, msgType, msg):
        """
        Public method to add an error message.
        
        @param msgType txpe of the message (string)
        @param msg message to be added (string)
        """
        s = '<font color="{0}">{1} <b>[</b>{2}<b>]</b> {3}</font>'.format(
            Preferences.getIrc("ErrorMessageColour"),
            ircTimestamp(),
            msgType,
            msg
        )
        self.messages.append(s)
    
    def setConnected(self, connected):
        """
        Public slot to set the connection state.
        
        @param connected flag indicating the connection state (boolean)
        """
        self.__connected = connected
        if self.__connected:
            self.connectButton.setIcon(
                UI.PixmapCache.getIcon("ircDisconnect.png"))
            self.connectButton.setToolTip(
                self.tr("Press to disconnect from the network"))
        else:
            self.connectButton.setIcon(
                UI.PixmapCache.getIcon("ircConnect.png"))
            self.connectButton.setToolTip(
                self.tr("Press to connect to the selected network"))
    
    def isConnected(self):
        """
        Public method to check, if the network is connected.
        
        @return flag indicating a connected network (boolean)
        """
        return self.__connected
    
    def setRegistered(self, registered):
        """
        Public slot to set the registered state.
        
        @param registered flag indicating the registration state (boolean)
        """
        self.__registered = registered
        on = bool(self.channelCombo.currentText()) and self.__registered
        self.joinButton.setEnabled(on)
        self.nickCombo.setEnabled(registered)
        self.awayButton.setEnabled(registered)
        if registered:
            self.awayButton.setIcon(
                UI.PixmapCache.getIcon("ircUserPresent.png"))
            self.__away = False
    
    def __clearMessages(self):
        """
        Private slot to clear the contents of the messages display.
        """
        self.messages.clear()
    
    def __copyMessages(self):
        """
        Private slot to copy the selection of the messages display to
        the clipboard.
        """
        self.messages.copy()
    
    def __copyAllMessages(self):
        """
        Private slot to copy the contents of the messages display to
        the clipboard.
        """
        txt = self.messages.toPlainText()
        if txt:
            cb = QApplication.clipboard()
            cb.setText(txt)
    
    def __cutAllMessages(self):
        """
        Private slot to cut the contents of the messages display to
        the clipboard.
        """
        txt = self.messages.toPlainText()
        if txt:
            cb = QApplication.clipboard()
            cb.setText(txt)
        self.messages.clear()
    
    def __saveMessages(self):
        """
        Private slot to save the contents of the messages display.
        """
        hasText = not self.messages.document().isEmpty()
        if hasText:
            if Utilities.isWindowsPlatform():
                htmlExtension = "htm"
            else:
                htmlExtension = "html"
            fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
                self,
                self.tr("Save Messages"),
                "",
                self.tr(
                    "HTML Files (*.{0});;Text Files (*.txt);;All Files (*)")
                .format(htmlExtension),
                None,
                E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
            if fname:
                ext = QFileInfo(fname).suffix()
                if not ext:
                    ex = selectedFilter.split("(*")[1].split(")")[0]
                    if ex:
                        fname += ex
                    ext = QFileInfo(fname).suffix()
                if QFileInfo(fname).exists():
                    res = E5MessageBox.yesNo(
                        self,
                        self.tr("Save Messages"),
                        self.tr("<p>The file <b>{0}</b> already exists."
                                " Overwrite it?</p>").format(fname),
                        icon=E5MessageBox.Warning)
                    if not res:
                        return
                    fname = Utilities.toNativeSeparators(fname)
                
                try:
                    if ext.lower() in ["htm", "html"]:
                        txt = self.messages.toHtml()
                    else:
                        txt = self.messages.toPlainText()
                    f = open(fname, "w", encoding="utf-8")
                    f.write(txt)
                    f.close()
                except IOError as err:
                    E5MessageBox.critical(
                        self,
                        self.tr("Error saving Messages"),
                        self.tr(
                            """<p>The messages contents could not be written"""
                            """ to <b>{0}</b></p><p>Reason: {1}</p>""")
                        .format(fname, str(err)))
    
    def __initMessagesMenu(self):
        """
        Private slot to initialize the context menu of the messages pane.
        """
        self.__messagesMenu = QMenu(self)
        self.__copyMessagesAct = \
            self.__messagesMenu.addAction(
                UI.PixmapCache.getIcon("editCopy.png"),
                self.tr("Copy"), self.__copyMessages)
        self.__messagesMenu.addSeparator()
        self.__cutAllMessagesAct = \
            self.__messagesMenu.addAction(
                UI.PixmapCache.getIcon("editCut.png"),
                self.tr("Cut all"), self.__cutAllMessages)
        self.__copyAllMessagesAct = \
            self.__messagesMenu.addAction(
                UI.PixmapCache.getIcon("editCopy.png"),
                self.tr("Copy all"), self.__copyAllMessages)
        self.__messagesMenu.addSeparator()
        self.__clearMessagesAct = \
            self.__messagesMenu.addAction(
                UI.PixmapCache.getIcon("editDelete.png"),
                self.tr("Clear"), self.__clearMessages)
        self.__messagesMenu.addSeparator()
        self.__saveMessagesAct = \
            self.__messagesMenu.addAction(
                UI.PixmapCache.getIcon("fileSave.png"),
                self.tr("Save"), self.__saveMessages)
        
        self.on_messages_copyAvailable(False)
    
    @pyqtSlot(bool)
    def on_messages_copyAvailable(self, yes):
        """
        Private slot to react to text selection/deselection of the
        messages edit.
        
        @param yes flag signaling the availability of selected text (boolean)
        """
        self.__copyMessagesAct.setEnabled(yes)
    
    @pyqtSlot(QPoint)
    def on_messages_customContextMenuRequested(self, pos):
        """
        Private slot to show the context menu of the messages pane.
        
        @param pos position the menu should be opened at (QPoint)
        """
        enable = not self.messages.document().isEmpty()
        self.__cutAllMessagesAct.setEnabled(enable)
        self.__copyAllMessagesAct.setEnabled(enable)
        self.__saveMessagesAct.setEnabled(enable)
        self.__messagesMenu.popup(self.messages.mapToGlobal(pos))
    
    @pyqtSlot(QUrl)
    def on_messages_anchorClicked(self, url):
        """
        Private slot to open links in the default browser.
        
        @param url URL to be opened (QUrl)
        """
        QDesktopServices.openUrl(url)
