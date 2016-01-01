#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Eric6 Python IDE.

This is the main Python script that performs the necessary initialization
of the IDE and starts the Qt event loop.
"""

from __future__ import unicode_literals

import sys

# generate list of arguments to be remembered for a restart
restartArgsList = ["--nosplash", "--plugin", "--debug", "--config", "--pyqt4"
                   "--settings"]
restartArgs = [arg for arg in sys.argv[1:]
               if arg.split("=", 1)[0] in restartArgsList]

import Toolbox.PyQt4ImportHook  # __IGNORE_WARNING__

try:  # Only for Py2
    import StringIO as io   # __IGNORE_EXCEPTION__
    import Globals.compatibility_fixes     # __IGNORE_WARNING__
    import locale
    coverage = 'Python'
except ImportError:
    import io       # __IGNORE_WARNING__
    basestring = str
    coverage = 'Python3'

try:
    import sip
    sip.setdestroyonexit(False)
except AttributeError:
    pass


import os
import traceback
import time
import logging

try:
    from PyQt5.QtCore import qWarning, QLibraryInfo, QTimer, QCoreApplication
except ImportError:
    try:    # Py2
        import tkMessageBox as messagebox
    except ImportError:
        try:    # Py3
            from tkinter import messagebox
        except ImportError:
            sys.exit(100)
    messagebox.showerror(
        "eric6 Error",
        "PyQt could not be imported. Please make sure"
        " it is installed and accessible.")
    sys.exit(100)

# some global variables needed to start the application
args = None
mainWindow = None
splash = None
inMainLoop = None

if "--debug" in sys.argv:
    del sys.argv[sys.argv.index("--debug")]
    logging.basicConfig(level=logging.DEBUG)

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

# make Third-Party package available as a packages repository
sys.path.insert(2, os.path.join(os.path.dirname(__file__),
                                "ThirdParty", "Pygments"))
sys.path.insert(2, os.path.join(os.path.dirname(__file__),
                                "ThirdParty", "Jasy"))
sys.path.insert(2, os.path.join(os.path.dirname(__file__),
                                "DebugClients", coverage))

from E5Gui.E5Application import E5Application


def handleSingleApplication(ddindex):
    """
    Global function to handle the single application mode.
    
    @param ddindex index of a '--' option in the options list
    """
    from E5Gui.E5SingleApplication import E5SingleApplicationClient
    
    client = E5SingleApplicationClient()
    res = client.connect()
    if res > 0:
        if "--nosplash" in sys.argv and sys.argv.index("--nosplash") < ddindex:
            del sys.argv[sys.argv.index("--nosplash")]
        if "--noopen" in sys.argv and sys.argv.index("--noopen") < ddindex:
            del sys.argv[sys.argv.index("--noopen")]
        if "--debug" in sys.argv and sys.argv.index("--debug") < ddindex:
            del sys.argv[sys.argv.index("--debug")]
        for arg in sys.argv:
            if arg.startswith("--config="):
                sys.argv.remove(arg)
                break
        if len(sys.argv) > 1:
            client.processArgs(sys.argv[1:])
        sys.exit(0)
    elif res < 0:
        print("eric6: {0}".format(client.errstr()))
        sys.exit(res)


def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.
    
    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    import xml.sax.saxutils
    from UI.Info import BugAddress
    import Utilities
    import Globals
    
    separator = '-' * 80
    logFile = os.path.join(Globals.getConfigDir(), "eric6_error.log")
    notice = \
        """An unhandled exception occurred. Please report the problem\n"""\
        """using the error reporting dialog or via email to <{0}>.\n"""\
        """A log has been written to "{1}".\n\nError information:\n""".format(
            BugAddress, logFile)
    timeString = time.strftime("%Y-%m-%d, %H:%M:%S")
    
    versionInfo = "\n{0}\n{1}".format(
        separator, Utilities.generateVersionInfo())
    pluginVersionInfo = Utilities.generatePluginsVersionInfo()
    if pluginVersionInfo:
        versionInfo += "{0}\n{1}".format(separator, pluginVersionInfo)
    distroInfo = Utilities.generateDistroInfo()
    if distroInfo:
        versionInfo += "{0}\n{1}".format(separator, distroInfo)
    
    if isinstance(excType, basestring):
        tbinfo = tracebackobj
    else:
        tbinfofile = io.StringIO()
        traceback.print_tb(tracebackobj, None, tbinfofile)
        tbinfofile.seek(0)
        tbinfo = tbinfofile.read()
        if sys.version_info[0] == 2:
            tbinfo = tbinfo.decode(locale.getpreferredencoding())
    errmsg = '{0}: \n{1}'.format(str(excType), str(excValue))
    sections = [separator, timeString, separator, errmsg, separator, tbinfo]
    msg = '\n'.join(sections)
    try:
        f = open(logFile, "w", encoding="utf-8")
        f.write(msg)
        f.write(versionInfo)
        f.close()
    except IOError:
        pass
    
    if inMainLoop is None:
        if sys.version_info[0] == 2:
            notice = notice.encode(sys.stdout.encoding, 'replace')
            msg = msg.encode(sys.stdout.encoding, 'replace')
            versionInfo = versionInfo.encode(sys.stdout.encoding, 'replace')
        warning = notice + msg + versionInfo
        print(warning)
    else:
        warning = notice + msg + versionInfo
        # Escape &<> otherwise it's not visible in the error dialog
        warning = xml.sax.saxutils.escape(warning)
        if sys.version_info[0] == 2:
            warning = warning.encode('utf-8', 'replace')
        qWarning(warning)


def uiStartUp():
    """
    Global function to finalize the start up of the main UI.
    
    Note: It is activated by a zero timeout single-shot timer.
    """
    global args, mainWindow, splash
    
    if splash:
        splash.finish(mainWindow)
        del splash
    
    mainWindow.checkForErrorLog()
    mainWindow.processArgs(args)
    mainWindow.checkProjectsWorkspace()
    mainWindow.checkConfigurationStatus()
    mainWindow.performVersionCheck(False)
    mainWindow.checkPluginUpdatesAvailable()
    mainWindow.autoConnectIrc()


def main():
    """
    Main entry point into the application.
    """
    from Globals import AppInfo
    import Globals
    
    global args, mainWindow, splash, restartArgs, inMainLoop
    
    sys.excepthook = excepthook
    
    options = [
        ("--config=configDir",
         "use the given directory as the one containing the config files"),
        ("--debug", "activate debugging output to the console"),
        ("--nosplash", "don't show the splash screen"),
        ("--noopen",
         "don't open anything at startup except that given in command"),
        ("--plugin=plugin-file",
         "load the given plugin file (plugin development)"),
        ("--settings=settingsDir",
         "use the given directory to store the settings files"),
        ("--start-file", "load the most recently opened file"),
        ("--start-multi", "load the most recently opened multi-project"),
        ("--start-project", "load the most recently opened project"),
        ("--start-session", "load the global session file"),
        ("--",
         "indicate that there are options for the program to be debugged"),
        ("",
         "(everything after that is considered arguments for this program)")
    ]
    appinfo = AppInfo.makeAppInfo(sys.argv,
                                  "Eric6",
                                  "[project | files... [--] [debug-options]]",
                                  "A Python IDE",
                                  options)
    
    if not Globals.checkBlacklistedVersions():
        sys.exit(100)
    
    from Toolbox import Startup
    # set the library paths for plugins
    Startup.setLibraryPaths()

    app = E5Application(sys.argv)
    ddindex = Startup.handleArgs(sys.argv, appinfo)
    
    logging.debug("Importing Preferences")
    import Preferences
    
    if Preferences.getUI("SingleApplicationMode"):
        handleSingleApplication(ddindex)
    
    # set the search path for icons
    Startup.initializeResourceSearchPath()

    # generate and show a splash window, if not suppressed
    from UI.SplashScreen import SplashScreen, NoneSplashScreen
    if "--nosplash" in sys.argv and sys.argv.index("--nosplash") < ddindex:
        del sys.argv[sys.argv.index("--nosplash")]
        splash = NoneSplashScreen()
    elif not Preferences.getUI("ShowSplash"):
        splash = NoneSplashScreen()
    else:
        splash = SplashScreen()
    QCoreApplication.processEvents()

    # modify the executable search path for the PyQt5 installer
    if Globals.isWindowsPlatform():
        pyqtDataDir = Globals.getPyQt5ModulesDirectory()
        if os.path.exists(os.path.join(pyqtDataDir, "bin")):
            path = os.path.join(pyqtDataDir, "bin")
        else:
            path = pyqtDataDir
        if sys.version_info[0] == 2:
            path = path.encode(sys.getfilesystemencoding())
        os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
    
    pluginFile = None
    noopen = False
    if "--noopen" in sys.argv and sys.argv.index("--noopen") < ddindex:
        del sys.argv[sys.argv.index("--noopen")]
        noopen = True
    for arg in sys.argv:
        if arg.startswith("--plugin=") and sys.argv.index(arg) < ddindex:
            import Utilities
            # extract the plugin development option
            pluginFile = arg.replace("--plugin=", "").replace('"', "")
            sys.argv.remove(arg)
            pluginFile = os.path.expanduser(pluginFile)
            pluginFile = Utilities.normabspath(pluginFile)
            break
    
    # is there a set of filenames or options on the command line,
    # if so, pass them to the UI
    if len(sys.argv) > 1:
        args = sys.argv[1:]
    
    # get the Qt4 translations directory
    qt4TransDir = Preferences.getQt4TranslationsDir()
    if not qt4TransDir:
        qt4TransDir = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    
    # Load translation files and install them
    loc = Startup.loadTranslators(qt4TransDir, app, ("qscintilla",))
    
    # Initialize SSL stuff
    from E5Network.E5SslUtilities import initSSL
    initSSL()
    
    splash.showMessage(QCoreApplication.translate("eric6", "Starting..."))
    # We can only import these after creating the E5Application because they
    # make Qt calls that need the E5Application to exist.
    from UI.UserInterface import UserInterface

    splash.showMessage(
        QCoreApplication.translate("eric6", "Generating Main Window..."))
    mainWindow = UserInterface(app, loc, splash, pluginFile, noopen,
                               restartArgs)
    app.lastWindowClosed.connect(app.quit)
    mainWindow.show()
    
    QTimer.singleShot(0, uiStartUp)
    
    # generate a graphical error handler
    from E5Gui import E5ErrorMessage
    eMsg = E5ErrorMessage.qtHandler()
    eMsg.setMinimumSize(600, 400)
    
    # start the event loop
    inMainLoop = True
    res = app.exec_()
    logging.debug("Shutting down, result {0:d}".format(res))
    logging.shutdown()
    sys.exit(res)

if __name__ == '__main__':
    main()
