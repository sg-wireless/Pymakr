# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Mercurial version control plugin.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QObject, QCoreApplication

from E5Gui.E5Application import e5App

import Preferences
from Preferences.Shortcuts import readShortcuts

from VcsPlugins.vcsMercurial.HgUtilities import getConfigPath

import Utilities

# Start-Of-Header
name = "Mercurial Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = False
deactivateable = True
version = "6.1.0"
pluginType = "version_control"
pluginTypename = "Mercurial"
className = "VcsMercurialPlugin"
packageName = "__core__"
shortDescription = "Implements the Mercurial version control interface."
longDescription = \
    """This plugin provides the Mercurial version control interface."""
pyqtApi = 2
python2Compatible = True
# End-Of-Header

error = ""


def exeDisplayData():
    """
    Public method to support the display of some executable info.
    
    @return dictionary containing the data to query the presence of
        the executable
    """
    exe = 'hg'
    if Utilities.isWindowsPlatform():
        exe += '.exe'
    
    data = {
        "programEntry": True,
        "header": QCoreApplication.translate(
            "VcsMercurialPlugin", "Version Control - Mercurial"),
        "exe": exe,
        "versionCommand": 'version',
        "versionStartsWith": 'Mercurial',
        "versionPosition": -1,
        "version": "",
        "versionCleanup": (0, -1),
    }
    
    return data


def getVcsSystemIndicator():
    """
    Public function to get the indicators for this version control system.
    
    @return dictionary with indicator as key and a tuple with the vcs name
        (string) and vcs display string (string)
    """
    global pluginTypename
    data = {}
    exe = 'hg'
    if Utilities.isWindowsPlatform():
        exe += '.exe'
    if Utilities.isinpath(exe):
        data[".hg"] = (pluginTypename, displayString())
        data["_hg"] = (pluginTypename, displayString())
    return data


def displayString():
    """
    Public function to get the display string.
    
    @return display string (string)
    """
    exe = 'hg'
    if Utilities.isWindowsPlatform():
        exe += '.exe'
    if Utilities.isinpath(exe):
        return QCoreApplication.translate('VcsMercurialPlugin', 'Mercurial')
    else:
        return ""

mercurialCfgPluginObject = None


def createConfigurationPage(configDlg):
    """
    Module function to create the configuration page.
    
    @param configDlg reference to the configuration dialog (QDialog)
    @return reference to the configuration page
    """
    global mercurialCfgPluginObject
    from VcsPlugins.vcsMercurial.ConfigurationPage.MercurialPage import \
        MercurialPage
    if mercurialCfgPluginObject is None:
        mercurialCfgPluginObject = VcsMercurialPlugin(None)
    page = MercurialPage(mercurialCfgPluginObject)
    return page
    

def getConfigData():
    """
    Module function returning data as required by the configuration dialog.
    
    @return dictionary with key "zzz_mercurialPage" containing the relevant
        data
    """
    return {
        "zzz_mercurialPage":
        [QCoreApplication.translate("VcsMercurialPlugin", "Mercurial"),
            os.path.join("VcsPlugins", "vcsMercurial", "icons",
                         "preferences-mercurial.png"),
            createConfigurationPage, "vcsPage", None],
    }


def prepareUninstall():
    """
    Module function to prepare for an uninstallation.
    """
    if not e5App().getObject("PluginManager").isPluginLoaded(
            "PluginVcsMercurial"):
        Preferences.Prefs.settings.remove("Mercurial")
    

class VcsMercurialPlugin(QObject):
    """
    Class implementing the Mercurial version control plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        super(VcsMercurialPlugin, self).__init__(ui)
        self.__ui = ui
        
        self.__mercurialDefaults = {
            "StopLogOnCopy": True,  # used in log browser
            "UseLogBrowser": True,
            "LogLimit": 20,
            "CommitMessages": 20,
            "PullUpdate": False,
            "PreferUnbundle": False,
            "ServerPort": 8000,
            "ServerStyle": "",
            "CleanupPatterns": "*.orig *.rej *~",
            "CreateBackup": False,
            "InternalMerge": False,
            "Encoding": "utf-8",
            "EncodingMode": "strict",
            "ConsiderHidden": False,
        }
        
        from VcsPlugins.vcsMercurial.ProjectHelper import HgProjectHelper
        self.__projectHelperObject = HgProjectHelper(None, None)
        try:
            e5App().registerPluginObject(
                pluginTypename, self.__projectHelperObject, pluginType)
        except KeyError:
            pass    # ignore duplicate registration
        readShortcuts(pluginName=pluginTypename)
    
    def getProjectHelper(self):
        """
        Public method to get a reference to the project helper object.
        
        @return reference to the project helper object
        """
        return self.__projectHelperObject

    def initToolbar(self, ui, toolbarManager):
        """
        Public slot to initialize the VCS toolbar.
        
        @param ui reference to the main window (UserInterface)
        @param toolbarManager reference to a toolbar manager object
            (E5ToolBarManager)
        """
        if self.__projectHelperObject:
            self.__projectHelperObject.initToolbar(ui, toolbarManager)
    
    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of reference to instantiated viewmanager and
            activation status (boolean)
        """
        from VcsPlugins.vcsMercurial.hg import Hg
        self.__object = Hg(self, self.__ui)
        
        tb = self.__ui.getToolbar("vcs")[1]
        tb.setVisible(False)
        tb.setEnabled(False)
        
        tb = self.__ui.getToolbar("mercurial")[1]
        tb.setVisible(True)
        tb.setEnabled(True)
        
        return self.__object, True
    
    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        self.__object = None
        
        tb = self.__ui.getToolbar("mercurial")[1]
        tb.setVisible(False)
        tb.setEnabled(False)
        
        tb = self.__ui.getToolbar("vcs")[1]
        tb.setVisible(True)
        tb.setEnabled(True)
    
    def getPreferences(self, key):
        """
        Public method to retrieve the various settings.
        
        @param key the key of the value to get
        @return the requested setting
        """
        if key in ["StopLogOnCopy", "UseLogBrowser", "PullUpdate",
                   "PreferUnbundle", "CreateBackup", "InternalMerge",
                   "ConsiderHidden"]:
            return Preferences.toBool(Preferences.Prefs.settings.value(
                "Mercurial/" + key, self.__mercurialDefaults[key]))
        elif key in ["LogLimit", "CommitMessages", "ServerPort"]:
            return int(Preferences.Prefs.settings.value(
                "Mercurial/" + key, self.__mercurialDefaults[key]))
        elif key in ["Commits"]:
            return Preferences.toList(Preferences.Prefs.settings.value(
                "Mercurial/" + key))
        else:
            return Preferences.Prefs.settings.value(
                "Mercurial/" + key, self.__mercurialDefaults[key])
    
    def setPreferences(self, key, value):
        """
        Public method to store the various settings.
        
        @param key the key of the setting to be set
        @param value the value to be set
        """
        Preferences.Prefs.settings.setValue("Mercurial/" + key, value)

    def getGlobalOptions(self):
        """
        Public method to build a list of global options.
        
        @return list of global options (list of string)
        """
        args = []
        if self.getPreferences("Encoding") != \
                self.__mercurialDefaults["Encoding"]:
            args.append("--encoding")
            args.append(self.getPreferences("Encoding"))
        if self.getPreferences("EncodingMode") != \
                self.__mercurialDefaults["EncodingMode"]:
            args.append("--encodingmode")
            args.append(self.getPreferences("EncodingMode"))
        if self.getPreferences("ConsiderHidden"):
            args.append("--hidden")
        return args
    
    def getConfigPath(self):
        """
        Public method to get the filename of the config file.
        
        @return filename of the config file (string)
        """
        return getConfigPath()
    
    def prepareUninstall(self):
        """
        Public method to prepare for an uninstallation.
        """
        e5App().unregisterPluginObject(pluginTypename)
    
    def prepareUnload(self):
        """
        Public method to prepare for an unload.
        """
        if self.__projectHelperObject:
            self.__projectHelperObject.removeToolbar(
                self.__ui, e5App().getObject("ToolbarManager"))
        e5App().unregisterPluginObject(pluginTypename)
