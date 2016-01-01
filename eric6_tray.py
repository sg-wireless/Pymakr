#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric6 Tray.

This is the main Python script that performs the necessary initialization
of the system-tray application. This acts as a quickstarter by providing a
context menu to start the eric6 IDE and the eric6 tools.
"""

from __future__ import unicode_literals

import sys
import os

PyQt4Option = "--pyqt4" in sys.argv
SettingsDir = None

import Toolbox.PyQt4ImportHook  # __IGNORE_WARNING__

try:  # Only for Py2
    import Globals.compatibility_fixes     # __IGNORE_WARNING__
except (ImportError):
    pass

for arg in sys.argv[:]:
    if arg.startswith("--config="):
        import Globals
        configDir = arg.replace("--config=", "")
        Globals.setConfigDir(configDir)
        sys.argv.remove(arg)
    elif arg.startswith("--settings="):
        from PyQt5.QtCore import QSettings
        SettingsDir = os.path.expanduser(arg.replace("--settings=", ""))
        if not os.path.isdir(SettingsDir):
            os.makedirs(SettingsDir)
        QSettings.setPath(QSettings.IniFormat, QSettings.UserScope,
                          SettingsDir)
        sys.argv.remove(arg)

from Globals import AppInfo

from Toolbox import Startup


def createMainWidget(argv):
    """
    Function to create the main widget.
    
    @param argv list of commandline parameters (list of strings)
    @return reference to the main widget (QWidget)
    """
    global PyQt4Option
    
    from Tools.TrayStarter import TrayStarter
    return TrayStarter(PyQt4Option, SettingsDir)


def main():
    """
    Main entry point into the application.
    """
    options = [
        ("--config=configDir",
         "use the given directory as the one containing the config files"),
        ("--settings=settingsDir",
         "use the given directory to store the settings files"),
    ]
    appinfo = AppInfo.makeAppInfo(sys.argv,
                                  "Eric6 Tray",
                                  "",
                                  "Traystarter for eric6",
                                  options)
    res = Startup.simpleAppStartup(sys.argv,
                                   appinfo,
                                   createMainWidget,
                                   quitOnLastWindowClosed=False,
                                   raiseIt=False)
    sys.exit(res)

if __name__ == '__main__':
    main()
