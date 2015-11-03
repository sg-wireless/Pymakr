# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the IRC configuration page.
"""

from __future__ import unicode_literals

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_IrcPage import Ui_IrcPage

import Preferences


class IrcPage(ConfigurationPageBase, Ui_IrcPage):
    """
    Class implementing the IRC configuration page.
    """
    TimeFormats = ["hh:mm", "hh:mm:ss", "h:mm ap", "h:mm:ss ap"]
    DateFormats = ["yyyy-MM-dd", "dd.MM.yyyy", "MM/dd/yyyy",
                   "yyyy MMM. dd", "dd MMM. yyyy", "MMM. dd, yyyy"]
    
    def __init__(self):
        """
        Constructor
        """
        super(IrcPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("IrcPage")
        
        self.timeFormatCombo.addItems(IrcPage.TimeFormats)
        self.dateFormatCombo.addItems(IrcPage.DateFormats)
        
        # set initial values
        # timestamps
        self.timestampGroup.setChecked(Preferences.getIrc("ShowTimestamps"))
        self.showDateCheckBox.setChecked(
            Preferences.getIrc("TimestampIncludeDate"))
        self.timeFormatCombo.setCurrentIndex(
            self.timeFormatCombo.findText(Preferences.getIrc("TimeFormat")))
        self.dateFormatCombo.setCurrentIndex(
            self.dateFormatCombo.findText(Preferences.getIrc("DateFormat")))
        
        # colours
        self.initColour("NetworkMessageColour", self.networkButton,
                        Preferences.getIrc, byName=True)
        self.initColour("ServerMessageColour", self.serverButton,
                        Preferences.getIrc, byName=True)
        self.initColour("ErrorMessageColour", self.errorButton,
                        Preferences.getIrc, byName=True)
        self.initColour("TimestampColour", self.timestampButton,
                        Preferences.getIrc, byName=True)
        self.initColour("HyperlinkColour", self.hyperlinkButton,
                        Preferences.getIrc, byName=True)
        self.initColour("ChannelMessageColour", self.channelButton,
                        Preferences.getIrc, byName=True)
        self.initColour("OwnNickColour", self.ownNickButton,
                        Preferences.getIrc, byName=True)
        self.initColour("NickColour", self.nickButton,
                        Preferences.getIrc, byName=True)
        self.initColour("JoinChannelColour", self.joinButton,
                        Preferences.getIrc, byName=True)
        self.initColour("LeaveChannelColour", self.leaveButton,
                        Preferences.getIrc, byName=True)
        self.initColour("ChannelInfoColour", self.infoButton,
                        Preferences.getIrc, byName=True)
        
        # notifications
        self.notificationsGroup.setChecked(
            Preferences.getIrc("ShowNotifications"))
        self.joinLeaveCheckBox.setChecked(Preferences.getIrc("NotifyJoinPart"))
        self.messageCheckBox.setChecked(Preferences.getIrc("NotifyMessage"))
        self.ownNickCheckBox.setChecked(Preferences.getIrc("NotifyNick"))
        
        # IRC text colors
        self.initColour("IrcColor0", self.ircColor0Button,
                        Preferences.getIrc, byName=True)
        self.initColour("IrcColor1", self.ircColor1Button,
                        Preferences.getIrc, byName=True)
        self.initColour("IrcColor2", self.ircColor2Button,
                        Preferences.getIrc, byName=True)
        self.initColour("IrcColor3", self.ircColor3Button,
                        Preferences.getIrc, byName=True)
        self.initColour("IrcColor4", self.ircColor4Button,
                        Preferences.getIrc, byName=True)
        self.initColour("IrcColor5", self.ircColor5Button,
                        Preferences.getIrc, byName=True)
        self.initColour("IrcColor6", self.ircColor6Button,
                        Preferences.getIrc, byName=True)
        self.initColour("IrcColor7", self.ircColor7Button,
                        Preferences.getIrc, byName=True)
        self.initColour("IrcColor8", self.ircColor8Button,
                        Preferences.getIrc, byName=True)
        self.initColour("IrcColor9", self.ircColor9Button,
                        Preferences.getIrc, byName=True)
        self.initColour("IrcColor10", self.ircColor10Button,
                        Preferences.getIrc, byName=True)
        self.initColour("IrcColor11", self.ircColor11Button,
                        Preferences.getIrc, byName=True)
        self.initColour("IrcColor12", self.ircColor12Button,
                        Preferences.getIrc, byName=True)
        self.initColour("IrcColor13", self.ircColor13Button,
                        Preferences.getIrc, byName=True)
        self.initColour("IrcColor14", self.ircColor14Button,
                        Preferences.getIrc, byName=True)
        self.initColour("IrcColor15", self.ircColor15Button,
                        Preferences.getIrc, byName=True)
        
        # Automatic User Information Lookup
        self.whoGroup.setChecked(Preferences.getIrc("AutoUserInfoLookup"))
        self.whoUsersSpinBox.setValue(Preferences.getIrc("AutoUserInfoMax"))
        self.whoIntervalSpinBox.setValue(
            Preferences.getIrc("AutoUserInfoInterval"))
        
        # Markers
        self.markWhenHiddenCheckBox.setChecked(
            Preferences.getIrc("MarkPositionWhenHidden"))
        self.initColour("MarkerLineForegroundColour",
                        self.markerForegroundButton,
                        Preferences.getIrc, byName=True)
        self.initColour("MarkerLineBackgroundColour",
                        self.markerBackgroundButton,
                        Preferences.getIrc, byName=True)
        
        # Shutdown
        self.confirmShutdownCheckBox.setChecked(
            Preferences.getIrc("AskOnShutdown"))
    
    def save(self):
        """
        Public slot to save the IRC configuration.
        """
        # timestamps
        Preferences.setIrc("ShowTimestamps", self.timestampGroup.isChecked())
        Preferences.setIrc(
            "TimestampIncludeDate", self.showDateCheckBox.isChecked())
        Preferences.setIrc("TimeFormat", self.timeFormatCombo.currentText())
        Preferences.setIrc("DateFormat", self.dateFormatCombo.currentText())
        
        # notifications
        Preferences.setIrc(
            "ShowNotifications", self.notificationsGroup.isChecked())
        Preferences.setIrc(
            "NotifyJoinPart", self.joinLeaveCheckBox.isChecked())
        Preferences.setIrc("NotifyMessage", self.messageCheckBox.isChecked())
        Preferences.setIrc("NotifyNick", self.ownNickCheckBox.isChecked())
        
        # Automatic User Information Lookup
        Preferences.setIrc("AutoUserInfoLookup", self.whoGroup.isChecked())
        Preferences.setIrc("AutoUserInfoMax", self.whoUsersSpinBox.value())
        Preferences.setIrc(
            "AutoUserInfoInterval", self.whoIntervalSpinBox.value())
        
        # Markers
        Preferences.setIrc(
            "MarkPositionWhenHidden",
            self.markWhenHiddenCheckBox.isChecked())
        
        # Shutdown
        Preferences.setIrc(
            "AskOnShutdown", self.confirmShutdownCheckBox.isChecked())
        
        # colours
        self.saveColours(Preferences.setIrc)


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = IrcPage()
    return page
