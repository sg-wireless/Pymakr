# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a LED to indicate the status of the VCS status monitor
thread.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QInputDialog, QMenu

from E5Gui.E5Led import E5ClickableLed, E5LedRectangular

import Preferences


class StatusMonitorLed(E5ClickableLed):
    """
    Class implementing a LED to indicate the status of the VCS status monitor
    thread.
    """
    def __init__(self, project, parent):
        """
        Constructor
        
        @param project reference to the project object (Project.Project)
        @param parent reference to the parent object (QWidget)
        """
        super(StatusMonitorLed, self).__init__(
            parent, shape=E5LedRectangular, rectRatio=1.0)
        
        self.__vcsClean = True
        self.project = project
        
        self.vcsMonitorLedColors = {
            "off": QColor(Qt.lightGray),
            "ok": QColor(Qt.green),
            "nok": QColor(Qt.red),
            "op": QColor(Qt.yellow),
            "send": QColor(Qt.blue),
            "wait": QColor(Qt.cyan),
            "timeout": QColor(Qt.darkRed)
        }
        self.__on = False
        
        self.setWhatsThis(self.tr(
            """<p>This LED indicates the operating"""
            """ status of the VCS monitor thread (off = monitoring off,"""
            """ green = monitoring on and ok, red = monitoring on, but"""
            """ not ok, yellow = checking VCS status). A status description"""
            """ is given in the tooltip.</p>"""
        ))
        self.setToolTip(
            self.tr("Repository status checking is switched off")
        )
        self.setColor(self.vcsMonitorLedColors["off"])
        
        # define a context menu
        self.__menu = QMenu(self)
        self.__checkAct = self.__menu.addAction(
            self.tr("Check status"), self.__checkStatus)
        self.__intervalAct = self.__menu.addAction(
            self.tr("Set interval..."), self.__setInterval)
        self.__menu.addSeparator()
        self.__onAct = self.__menu.addAction(
            self.tr("Switch on"), self.__switchOn)
        self.__offAct = self.__menu.addAction(
            self.tr("Switch off"), self.__switchOff)
        self.__checkActions()
        
        # connect signals to our slots
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showContextMenu)
        self.project.vcsStatusMonitorStatus.connect(
            self.__projectVcsMonitorStatus)
        self.project.getModel().vcsStateChanged.connect(self.__vcsStateChanged)
        self.clicked.connect(self.__ledClicked)
    
    def __checkActions(self):
        """
        Private method to set the enabled status of the context menu actions.
        """
        if self.project.pudata["VCSSTATUSMONITORINTERVAL"]:
            vcsStatusMonitorInterval = \
                self.project.pudata["VCSSTATUSMONITORINTERVAL"][0]
        else:
            vcsStatusMonitorInterval = \
                Preferences.getVCS("StatusMonitorInterval")
        self.__checkAct.setEnabled(self.__on)
        self.__intervalAct.setEnabled(self.__on)
        self.__onAct.setEnabled(
            (not self.__on) and vcsStatusMonitorInterval > 0)
        self.__offAct.setEnabled(self.__on)
        
    def __projectVcsMonitorStatus(self, status, statusMsg):
        """
        Private method to receive the status monitor status.
        
        @param status status of the monitoring thread (string, ok, nok or off)
        @param statusMsg explanotory text for the signaled status (string)
        """
        self.setColor(self.vcsMonitorLedColors[status])
        self.setToolTip(statusMsg)
        
        self.__on = status != 'off'
    
    def _showContextMenu(self, coord):
        """
        Protected slot to show the context menu.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        if not self.project.isOpen():
            return
        
        self.__checkActions()
        self.__menu.popup(self.mapToGlobal(coord))
    
    def __checkStatus(self):
        """
        Private slot to initiate a new status check.
        """
        self.project.checkVCSStatus()
    
    def __setInterval(self):
        """
        Private slot to change the status check interval.
        """
        interval, ok = QInputDialog.getInt(
            None,
            self.tr("VCS Status Monitor"),
            self.tr("Enter monitor interval [s]"),
            self.project.getStatusMonitorInterval(),
            0, 3600, 1)
        if ok:
            self.project.setStatusMonitorInterval(interval)
    
    def __switchOn(self):
        """
        Private slot to switch the status monitor thread to On.
        """
        self.project.startStatusMonitor()
    
    def __switchOff(self):
        """
        Private slot to switch the status monitor thread to Off.
        """
        self.project.stopStatusMonitor()
    
    def __vcsStateChanged(self, state):
        """
        Private slot to handle a change in the vcs state.
        
        @param state new vcs state (string)
        """
        self.__vcsClean = state == " "
    
    def __ledClicked(self, pos):
        """
        Private slot to react upon clicks on the LED.
        
        @param pos position of the click (QPoint)
        """
        if self.__on:
            vcs = self.project.getVcs()
            if vcs:
                if self.__vcsClean:
                    # call log browser dialog
                    vcs.vcsLogBrowser(self.project.getProjectPath())
                else:
                    # call status dialog
                    vcs.vcsStatus(self.project.getProjectPath())
