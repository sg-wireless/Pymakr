#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric6 QRegularExpression.

This is the main Python script that performs the necessary initialization
of the QRegularExpression wizard module and starts the Qt event loop. This is
a standalone version of the integrated QRegularExpression wizard.
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

from Globals import AppInfo

from Toolbox import Startup


def createMainWidget(argv):
    """
    Function to create the main widget.
    
    @param argv list of commandline parameters (list of strings)
    @return reference to the main widget (QWidget)
    """
    from Plugins.WizardPlugins.QRegularExpressionWizard\
        .QRegularExpressionWizardDialog import QRegularExpressionWizardWindow
    return QRegularExpressionWizardWindow()


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
    appinfo = AppInfo.makeAppInfo(
        sys.argv,
        "Eric6 QRegularExpression",
        "",
        "Regexp editor for Qt's QRegularExpression class",
        options)
    res = Startup.simpleAppStartup(sys.argv,
                                   appinfo,
                                   createMainWidget)
    sys.exit(res)

if __name__ == '__main__':
    main()
