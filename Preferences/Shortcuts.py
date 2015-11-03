# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing functions dealing with keyboard shortcuts.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QFile, QIODevice, QCoreApplication
from PyQt5.QtGui import QKeySequence

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox

from Preferences import Prefs, syncPreferences


def __readShortcut(act, category, prefClass):
    """
    Private function to read a single keyboard shortcut from the settings.
    
    @param act reference to the action object (E5Action)
    @param category category the action belongs to (string)
    @param prefClass preferences class used as the storage area
    """
    if act.objectName():
        accel = prefClass.settings.value(
            "Shortcuts/{0}/{1}/Accel".format(category, act.objectName()))
        if accel is not None:
            act.setShortcut(QKeySequence(accel))
        accel = prefClass.settings.value(
            "Shortcuts/{0}/{1}/AltAccel".format(category, act.objectName()))
        if accel is not None:
            act.setAlternateShortcut(QKeySequence(accel), removeEmpty=True)


def readShortcuts(prefClass=Prefs, helpViewer=None, pluginName=None):
    """
    Module function to read the keyboard shortcuts for the defined QActions.
    
    @keyparam prefClass preferences class used as the storage area
    @keyparam helpViewer reference to the help window object
    @keyparam pluginName name of the plugin for which to load shortcuts
        (string)
    """
    if helpViewer is None and pluginName is None:
        for act in e5App().getObject("Project").getActions():
            __readShortcut(act, "Project", prefClass)
        
        for act in e5App().getObject("UserInterface").getActions('ui'):
            __readShortcut(act, "General", prefClass)
        
        for act in e5App().getObject("UserInterface").getActions('wizards'):
            __readShortcut(act, "Wizards", prefClass)
        
        for act in e5App().getObject("DebugUI").getActions():
            __readShortcut(act, "Debug", prefClass)
        
        for act in e5App().getObject("ViewManager").getActions('edit'):
            __readShortcut(act, "Edit", prefClass)
        
        for act in e5App().getObject("ViewManager").getActions('file'):
            __readShortcut(act, "File", prefClass)
        
        for act in e5App().getObject("ViewManager").getActions('search'):
            __readShortcut(act, "Search", prefClass)
        
        for act in e5App().getObject("ViewManager").getActions('view'):
            __readShortcut(act, "View", prefClass)
        
        for act in e5App().getObject("ViewManager").getActions('macro'):
            __readShortcut(act, "Macro", prefClass)
        
        for act in e5App().getObject("ViewManager").getActions('bookmark'):
            __readShortcut(act, "Bookmarks", prefClass)
        
        for act in e5App().getObject("ViewManager").getActions('spelling'):
            __readShortcut(act, "Spelling", prefClass)
        
        actions = e5App().getObject("ViewManager").getActions('window')
        if actions:
            for act in actions:
                __readShortcut(act, "Window", prefClass)
        
        for category, ref in e5App().getPluginObjects():
            if hasattr(ref, "getActions"):
                actions = ref.getActions()
                for act in actions:
                    __readShortcut(act, category, prefClass)
    
    if helpViewer is not None:
        for act in helpViewer.getActions():
            __readShortcut(act, "HelpViewer", prefClass)
    
    if pluginName is not None:
        try:
            ref = e5App().getPluginObject(pluginName)
            if hasattr(ref, "getActions"):
                actions = ref.getActions()
                for act in actions:
                    __readShortcut(act, pluginName, prefClass)
        except KeyError:
            # silently ignore non available plugins
            pass
    

def __saveShortcut(act, category, prefClass):
    """
    Private function to write a single keyboard shortcut to the settings.
    
    @param act reference to the action object (E5Action)
    @param category category the action belongs to (string)
    @param prefClass preferences class used as the storage area
    """
    if act.objectName():
        prefClass.settings.setValue(
            "Shortcuts/{0}/{1}/Accel".format(category, act.objectName()),
            act.shortcut().toString())
        prefClass.settings.setValue(
            "Shortcuts/{0}/{1}/AltAccel".format(category, act.objectName()),
            act.alternateShortcut().toString())


def saveShortcuts(prefClass=Prefs):
    """
    Module function to write the keyboard shortcuts for the defined QActions.
    
    @param prefClass preferences class used as the storage area
    """
    # step 1: clear all previously saved shortcuts
    prefClass.settings.beginGroup("Shortcuts")
    prefClass.settings.remove("")
    prefClass.settings.endGroup()
    
    # step 2: save the various shortcuts
    for act in e5App().getObject("Project").getActions():
        __saveShortcut(act, "Project", prefClass)
    
    for act in e5App().getObject("UserInterface").getActions('ui'):
        __saveShortcut(act, "General", prefClass)
    
    for act in e5App().getObject("UserInterface").getActions('wizards'):
        __saveShortcut(act, "Wizards", prefClass)
    
    for act in e5App().getObject("DebugUI").getActions():
        __saveShortcut(act, "Debug", prefClass)
    
    for act in e5App().getObject("ViewManager").getActions('edit'):
        __saveShortcut(act, "Edit", prefClass)
    
    for act in e5App().getObject("ViewManager").getActions('file'):
        __saveShortcut(act, "File", prefClass)
    
    for act in e5App().getObject("ViewManager").getActions('search'):
        __saveShortcut(act, "Search", prefClass)
    
    for act in e5App().getObject("ViewManager").getActions('view'):
        __saveShortcut(act, "View", prefClass)
    
    for act in e5App().getObject("ViewManager").getActions('macro'):
        __saveShortcut(act, "Macro", prefClass)
    
    for act in e5App().getObject("ViewManager").getActions('bookmark'):
        __saveShortcut(act, "Bookmarks", prefClass)
    
    for act in e5App().getObject("ViewManager").getActions('spelling'):
        __saveShortcut(act, "Spelling", prefClass)
    
    actions = e5App().getObject("ViewManager").getActions('window')
    if actions:
        for act in actions:
            __saveShortcut(act, "Window", prefClass)
    
    for category, ref in e5App().getPluginObjects():
        if hasattr(ref, "getActions"):
            actions = ref.getActions()
            for act in actions:
                __saveShortcut(act, category, prefClass)
    
    for act in e5App().getObject("DummyHelpViewer").getActions():
        __saveShortcut(act, "HelpViewer", prefClass)


def exportShortcuts(fn):
    """
    Module function to export the keyboard shortcuts for the defined QActions.
    
    @param fn filename of the export file (string)
    """
    # let the plugin manager create on demand plugin objects
    pm = e5App().getObject("PluginManager")
    pm.initOnDemandPlugins()
    
    f = QFile(fn)
    if f.open(QIODevice.WriteOnly):
        from E5XML.ShortcutsWriter import ShortcutsWriter
        ShortcutsWriter(f).writeXML()
        f.close()
    else:
        E5MessageBox.critical(
            None,
            QCoreApplication.translate(
                "Shortcuts", "Export Keyboard Shortcuts"),
            QCoreApplication.translate(
                "Shortcuts",
                "<p>The keyboard shortcuts could not be written to file"
                " <b>{0}</b>.</p>")
            .format(fn))


def importShortcuts(fn):
    """
    Module function to import the keyboard shortcuts for the defined E5Actions.
    
    @param fn filename of the import file (string)
    """
    # let the plugin manager create on demand plugin objects
    pm = e5App().getObject("PluginManager")
    pm.initOnDemandPlugins()
    
    f = QFile(fn)
    if f.open(QIODevice.ReadOnly):
        from E5XML.ShortcutsReader import ShortcutsReader
        reader = ShortcutsReader(f)
        reader.readXML()
        f.close()
        if not reader.hasError():
            shortcuts = reader.getShortcuts()
            setActions(shortcuts)
            saveShortcuts()
            syncPreferences()
    else:
        E5MessageBox.critical(
            None,
            QCoreApplication.translate(
                "Shortcuts", "Import Keyboard Shortcuts"),
            QCoreApplication.translate(
                "Shortcuts",
                "<p>The keyboard shortcuts could not be read from file"
                " <b>{0}</b>.</p>")
            .format(fn))
        return


def __setAction(actions, sdict):
    """
    Private function to write a single keyboard shortcut to the settings.
    
    @param actions list of actions to set (list of E5Action)
    @param sdict dictionary containg accelerator information for one category
    """
    for act in actions:
        if act.objectName():
            try:
                accel, altAccel = sdict[act.objectName()]
                act.setShortcut(QKeySequence(accel))
                act.setAlternateShortcut(QKeySequence(altAccel),
                                         removeEmpty=True)
            except KeyError:
                pass


def setActions(shortcuts):
    """
    Module function to set actions based on new format shortcuts file.
    
    @param shortcuts dictionary containing the accelerator information
        read from a XML file
    """
    if "Project" in shortcuts:
        __setAction(e5App().getObject("Project").getActions(),
                    shortcuts["Project"])
    
    if "General" in shortcuts:
        __setAction(e5App().getObject("UserInterface").getActions('ui'),
                    shortcuts["General"])
    
    if "Wizards" in shortcuts:
        __setAction(e5App().getObject("UserInterface").getActions('wizards'),
                    shortcuts["Wizards"])
    
    if "Debug" in shortcuts:
        __setAction(e5App().getObject("DebugUI").getActions(),
                    shortcuts["Debug"])
    
    if "Edit" in shortcuts:
        __setAction(e5App().getObject("ViewManager").getActions('edit'),
                    shortcuts["Edit"])
    
    if "File" in shortcuts:
        __setAction(e5App().getObject("ViewManager").getActions('file'),
                    shortcuts["File"])
    
    if "Search" in shortcuts:
        __setAction(e5App().getObject("ViewManager").getActions('search'),
                    shortcuts["Search"])
    
    if "View" in shortcuts:
        __setAction(e5App().getObject("ViewManager").getActions('view'),
                    shortcuts["View"])
    
    if "Macro" in shortcuts:
        __setAction(e5App().getObject("ViewManager").getActions('macro'),
                    shortcuts["Macro"])
    
    if "Bookmarks" in shortcuts:
        __setAction(e5App().getObject("ViewManager").getActions('bookmark'),
                    shortcuts["Bookmarks"])
    
    if "Spelling" in shortcuts:
        __setAction(e5App().getObject("ViewManager").getActions('spelling'),
                    shortcuts["Spelling"])
    
    if "Window" in shortcuts:
        actions = e5App().getObject("ViewManager").getActions('window')
        if actions:
            __setAction(actions, shortcuts["Window"])
    
    for category, ref in e5App().getPluginObjects():
        if category in shortcuts and hasattr(ref, "getActions"):
            actions = ref.getActions()
            __setAction(actions, shortcuts[category])
    
    if "HelpViewer" in shortcuts:
        __setAction(e5App().getObject("DummyHelpViewer").getActions(),
                    shortcuts["HelpViewer"])
