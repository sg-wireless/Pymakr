# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Package implementing the viewmanager of the eric6 IDE.

The viewmanager is responsible for the layout of the editor windows. This is
the central part of the IDE. In additon to this, the viewmanager provides all
editor related actions, menus and toolbars.

View managers are provided as plugins and loaded via the factory function. If
the requested view manager type is not available, tabview will be used by
default.
"""

from __future__ import unicode_literals

import Preferences

######################################################################
## Below is the factory function to instantiate the appropriate
## viewmanager depending on the configuration settings
######################################################################


def factory(parent, ui, dbs, pluginManager):
    """
    Modul factory function to generate the right viewmanager type.
    
    The viewmanager is instantiated depending on the data set in
    the current preferences.
    
    @param parent parent widget (QWidget)
    @param ui reference to the main UI object
    @param dbs reference to the debug server object
    @param pluginManager reference to the plugin manager object
    @return the instantiated viewmanager
    @exception RuntimeError raised if no view manager could be created
    """
    viewManagerStr = Preferences.getViewManager()
    vm = pluginManager.getPluginObject("viewmanager", viewManagerStr)
    if vm is None:
        # load tabview view manager as default
        vm = pluginManager.getPluginObject("viewmanager", "tabview")
        if vm is None:
            raise RuntimeError("Could not create a viemanager object.")
        Preferences.setViewManager("tabview")
    vm.setReferences(ui, dbs)
    return vm
