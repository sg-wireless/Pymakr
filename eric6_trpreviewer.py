#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric6 TR Previewer.

This is the main Python script that performs the necessary initialization
of the tr previewer and starts the Qt event loop. This is a standalone version
of the integrated tr previewer.
"""

from __future__ import unicode_literals

import Toolbox.PyQt4ImportHook  # __IGNORE_WARNING__

try:  # Only for Py2
    import Globals.compatibility_fixes     # __IGNORE_WARNING__
except (ImportError):
    pass

import sys
import os

for arg in sys.argv[:]:
    if arg.startswith("--config="):
        import Globals
        configDir = arg.replace("--config=", "")
        Globals.setConfigDir(configDir)
        sys.argv.remove(arg)
    elif arg.startswith("--settings="):
        from PyQt5.QtCore import QSettings
        settingsDir = os.path.expanduser(arg.replace("--settings=", ""))
        if not os.path.isdir(settingsDir):
            os.makedirs(settingsDir)
        QSettings.setPath(QSettings.IniFormat, QSettings.UserScope,
                          settingsDir)
        sys.argv.remove(arg)

from E5Gui.E5Application import E5Application

from Tools.TRSingleApplication import TRSingleApplicationClient
from Globals import AppInfo

from Toolbox import Startup


def createMainWidget(argv):
    """
    Function to create the main widget.
    
    @param argv list of commandline parameters (list of strings)
    @return reference to the main widget (QWidget)
    """
    from Tools.TRPreviewer import TRPreviewer
    
    if len(argv) > 1:
        files = argv[1:]
    else:
        files = []
    
    previewer = TRPreviewer(files, None, 'TRPreviewer')
    return previewer


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
                                  "Eric6 TR Previewer",
                                  "file",
                                  "TR file previewer",
                                  options)
    
    # set the library paths for plugins
    Startup.setLibraryPaths()
    
    app = E5Application(sys.argv)
    client = TRSingleApplicationClient()
    res = client.connect()
    if res > 0:
        if len(sys.argv) > 1:
            client.processArgs(sys.argv[1:])
        sys.exit(0)
    elif res < 0:
        print("eric6_trpreviewer: {0}".format(client.errstr()))
        sys.exit(res)
    else:
        res = Startup.simpleAppStartup(sys.argv,
                                       appinfo,
                                       createMainWidget,
                                       app=app)
        sys.exit(res)

if __name__ == '__main__':
    main()
