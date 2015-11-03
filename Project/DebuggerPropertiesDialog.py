# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for entering project specific debugger settings.
"""

from __future__ import unicode_literals

import os
import sys

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog

from E5Gui.E5Completers import E5FileCompleter, E5DirCompleter
from E5Gui import E5FileDialog

from .Ui_DebuggerPropertiesDialog import Ui_DebuggerPropertiesDialog

import Utilities
import UI.PixmapCache

from eric6config import getConfig


class DebuggerPropertiesDialog(QDialog, Ui_DebuggerPropertiesDialog):
    """
    Class implementing a dialog for entering project specific debugger
    settings.
    """
    def __init__(self, project, parent=None, name=None):
        """
        Constructor
        
        @param project reference to the project object
        @param parent parent widget of this dialog (QWidget)
        @param name name of this dialog (string)
        """
        super(DebuggerPropertiesDialog, self).__init__(parent)
        if name:
            self.setObjectName(name)
        self.setupUi(self)
        
        self.debugClientButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.interpreterButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.debugClientCompleter = E5FileCompleter(self.debugClientEdit)
        self.interpreterCompleter = E5FileCompleter(self.interpreterEdit)
        self.translationLocalCompleter = E5DirCompleter(
            self.translationLocalEdit)
        
        self.project = project
        
        if self.project.debugProperties["INTERPRETER"]:
            self.interpreterEdit.setText(
                self.project.debugProperties["INTERPRETER"])
        else:
            if self.project.pdata["PROGLANGUAGE"][0] in \
                    ["Python", "Python2", "Python3"]:
                self.interpreterEdit.setText(sys.executable)
            elif self.project.pdata["PROGLANGUAGE"][0] == "Ruby":
                self.interpreterEdit.setText("/usr/bin/ruby")
        if self.project.debugProperties["DEBUGCLIENT"]:
            self.debugClientEdit.setText(
                self.project.debugProperties["DEBUGCLIENT"])
        else:
            if self.project.pdata["PROGLANGUAGE"][0] in ["Python", "Python2"]:
                debugClient = os.path.join(
                    getConfig('ericDir'),
                    "DebugClients", "Python", "DebugClient.py")
            elif self.project.pdata["PROGLANGUAGE"][0] == "Python3":
                debugClient = os.path.join(
                    getConfig('ericDir'),
                    "DebugClients", "Python3", "DebugClient.py")
            elif self.project.pdata["PROGLANGUAGE"][0] == "Ruby":
                debugClient = os.path.join(
                    getConfig('ericDir'),
                    "DebugClients", "Ruby", "DebugClient.rb")
            else:
                debugClient = ""
            self.debugClientEdit.setText(debugClient)
        self.debugEnvironmentOverrideCheckBox.setChecked(
            self.project.debugProperties["ENVIRONMENTOVERRIDE"])
        self.debugEnvironmentEdit.setText(
            self.project.debugProperties["ENVIRONMENTSTRING"])
        self.remoteDebuggerGroup.setChecked(
            self.project.debugProperties["REMOTEDEBUGGER"])
        self.remoteHostEdit.setText(
            self.project.debugProperties["REMOTEHOST"])
        self.remoteCommandEdit.setText(
            self.project.debugProperties["REMOTECOMMAND"])
        self.pathTranslationGroup.setChecked(
            self.project.debugProperties["PATHTRANSLATION"])
        self.translationRemoteEdit.setText(
            self.project.debugProperties["REMOTEPATH"])
        self.translationLocalEdit.setText(
            self.project.debugProperties["LOCALPATH"])
        self.consoleDebuggerGroup.setChecked(
            self.project.debugProperties["CONSOLEDEBUGGER"])
        self.consoleCommandEdit.setText(
            self.project.debugProperties["CONSOLECOMMAND"])
        self.redirectCheckBox.setChecked(
            self.project.debugProperties["REDIRECT"])
        self.noEncodingCheckBox.setChecked(
            self.project.debugProperties["NOENCODING"])
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    @pyqtSlot()
    def on_interpreterButton_clicked(self):
        """
        Private slot to handle the interpreter selection.
        """
        file = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select interpreter for Debug Client"),
            self.interpreterEdit.text(),
            "")
            
        if file:
            self.interpreterEdit.setText(Utilities.toNativeSeparators(file))

    @pyqtSlot()
    def on_debugClientButton_clicked(self):
        """
        Private slot to handle the Debug Client selection.
        """
        filters = self.project.dbgFilters[
            self.project.pdata["PROGLANGUAGE"][0]]
        filters += self.tr("All Files (*)")
        file = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select Debug Client"),
            self.debugClientEdit.text(),
            filters)
            
        if file:
            self.debugClientEdit.setText(Utilities.toNativeSeparators(file))

    def storeData(self):
        """
        Public method to store the entered/modified data.
        """
        self.project.debugProperties["INTERPRETER"] = \
            self.interpreterEdit.text()
        if not self.project.debugProperties["INTERPRETER"]:
            if self.project.pdata["PROGLANGUAGE"][0] in \
                    ["Python", "Python2", "Python3"]:
                self.project.debugProperties["INTERPRETER"] = sys.executable
            elif self.project.pdata["PROGLANGUAGE"][0] == "Ruby":
                self.project.debugProperties["INTERPRETER"] = "/usr/bin/ruby"
        
        self.project.debugProperties["DEBUGCLIENT"] = \
            self.debugClientEdit.text()
        if not self.project.debugProperties["DEBUGCLIENT"]:
            if self.project.pdata["PROGLANGUAGE"][0] in ["Python", "Python2"]:
                debugClient = os.path.join(
                    getConfig('ericDir'),
                    "DebugClients", "Python", "DebugClient.py")
            elif self.project.pdata["PROGLANGUAGE"][0] == "Python3":
                debugClient = os.path.join(
                    getConfig('ericDir'),
                    "DebugClients", "Python3", "DebugClient.py")
            elif self.project.pdata["PROGLANGUAGE"][0] == "Ruby":
                debugClient = os.path.join(
                    getConfig('ericDir'),
                    "DebugClients", "Ruby", "DebugClient.rb")
            else:
                debugClient = ""
            self.project.debugProperties["DEBUGCLIENT"] = debugClient
        
        self.project.debugProperties["ENVIRONMENTOVERRIDE"] = \
            self.debugEnvironmentOverrideCheckBox.isChecked()
        self.project.debugProperties["ENVIRONMENTSTRING"] = \
            self.debugEnvironmentEdit.text()
        self.project.debugProperties["REMOTEDEBUGGER"] = \
            self.remoteDebuggerGroup.isChecked()
        self.project.debugProperties["REMOTEHOST"] = \
            self.remoteHostEdit.text()
        self.project.debugProperties["REMOTECOMMAND"] = \
            self.remoteCommandEdit.text()
        self.project.debugProperties["PATHTRANSLATION"] = \
            self.pathTranslationGroup.isChecked()
        self.project.debugProperties["REMOTEPATH"] = \
            self.translationRemoteEdit.text()
        self.project.debugProperties["LOCALPATH"] = \
            self.translationLocalEdit.text()
        self.project.debugProperties["CONSOLEDEBUGGER"] = \
            self.consoleDebuggerGroup.isChecked()
        self.project.debugProperties["CONSOLECOMMAND"] = \
            self.consoleCommandEdit.text()
        self.project.debugProperties["REDIRECT"] = \
            self.redirectCheckBox.isChecked()
        self.project.debugProperties["NOENCODING"] = \
            self.noEncodingCheckBox.isChecked()
        self.project.debugPropertiesLoaded = True
