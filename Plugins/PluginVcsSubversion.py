# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Subversion version control plugin.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QObject, QCoreApplication

from E5Gui.E5Application import e5App

import Preferences
from Preferences.Shortcuts import readShortcuts

from VcsPlugins.vcsSubversion.SvnUtilities import getConfigPath, getServersPath

import Utilities

# Start-Of-Header
name = "Subversion Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = False
deactivateable = True
version = "6.1.0"
pluginType = "version_control"
pluginTypename = "Subversion"
className = "VcsSubversionPlugin"
packageName = "__core__"
shortDescription = "Implements the Subversion version control interface."
longDescription = \
    """This plugin provides the Subversion version control interface."""
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
    exe = 'svn'
    if Utilities.isWindowsPlatform():
        exe += '.exe'
    
    data = {
        "programEntry": True,
        "header": QCoreApplication.translate(
            "VcsSubversionPlugin", "Version Control - Subversion (svn)"),
        "exe": exe,
        "versionCommand": '--version',
        "versionStartsWith": 'svn',
        "versionPosition": 2,
        "version": "",
        "versionCleanup": None,
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
    exe = 'svn'
    if Utilities.isWindowsPlatform():
        exe += '.exe'
    if Utilities.isinpath(exe):
        data[".svn"] = (pluginTypename, displayString())
        data["_svn"] = (pluginTypename, displayString())
    return data


def displayString():
    """
    Public function to get the display string.
    
    @return display string (string)
    """
    exe = 'svn'
    if Utilities.isWindowsPlatform():
        exe += '.exe'
    if Utilities.isinpath(exe):
        return QCoreApplication.translate(
            'VcsSubversionPlugin', 'Subversion (svn)')
    else:
        return ""

subversionCfgPluginObject = None


def createConfigurationPage(configDlg):
    """
    Module function to create the configuration page.
    
    @param configDlg reference to the configuration dialog (QDialog)
    @return reference to the configuration page
    """
    global subversionCfgPluginObject
    from VcsPlugins.vcsSubversion.ConfigurationPage.SubversionPage import \
        SubversionPage
    if subversionCfgPluginObject is None:
        subversionCfgPluginObject = VcsSubversionPlugin(None)
    page = SubversionPage(subversionCfgPluginObject)
    return page
    

def getConfigData():
    """
    Module function returning data as required by the configuration dialog.
    
    @return dictionary with key "zzz_subversionPage" containing the relevant
    data
    """
    return {
        "zzz_subversionPage":
        [QCoreApplication.translate("VcsSubversionPlugin", "Subversion"),
         os.path.join("VcsPlugins", "vcsSubversion", "icons",
                      "preferences-subversion.png"),
         createConfigurationPage, "vcsPage", None],
    }
    

def prepareUninstall():
    """
    Module function to prepare for an uninstallation.
    """
    if not e5App().getObject("PluginManager").isPluginLoaded(
            "PluginVcsSubversion"):
        Preferences.Prefs.settings.remove("Subversion")
    

class VcsSubversionPlugin(QObject):
    """
    Class implementing the Subversion version control plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        super(VcsSubversionPlugin, self).__init__(ui)
        self.__ui = ui
        
        self.__subversionDefaults = {
            "StopLogOnCopy": True,
            "LogLimit": 20,
            "CommitMessages": 20,
        }
        
        from VcsPlugins.vcsSubversion.ProjectHelper import SvnProjectHelper
        self.__projectHelperObject = SvnProjectHelper(None, None)
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
        from VcsPlugins.vcsSubversion.subversion import Subversion
        self.__object = Subversion(self, self.__ui)
        
        tb = self.__ui.getToolbar("vcs")[1]
        tb.setVisible(False)
        tb.setEnabled(False)
        
        tb = self.__ui.getToolbar("subversion")[1]
        tb.setVisible(True)
        tb.setEnabled(True)
        
        return self.__object, True
    
    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        self.__object = None
        
        tb = self.__ui.getToolbar("subversion")[1]
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
        if key in ["StopLogOnCopy"]:
            return Preferences.toBool(Preferences.Prefs.settings.value(
                "Subversion/" + key, self.__subversionDefaults[key]))
        elif key in ["LogLimit", "CommitMessages"]:
            return int(Preferences.Prefs.settings.value(
                "Subversion/" + key,
                self.__subversionDefaults[key]))
        elif key in ["Commits"]:
            return Preferences.toList(Preferences.Prefs.settings.value(
                "Subversion/" + key))
        else:
            return Preferences.Prefs.settings.value("Subversion/" + key)
    
    def setPreferences(self, key, value):
        """
        Public method to store the various settings.
        
        @param key the key of the setting to be set
        @param value the value to be set
        """
        Preferences.Prefs.settings.setValue("Subversion/" + key, value)
    
    def getServersPath(self):
        """
        Public method to get the filename of the servers file.
        
        @return filename of the servers file (string)
        """
        return getServersPath()
    
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
