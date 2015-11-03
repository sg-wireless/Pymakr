# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing some startup helper funcions.
"""

from __future__ import unicode_literals

import os
import sys

from PyQt5.QtCore import QTranslator, QLocale, QLibraryInfo, QDir, \
    QTextCodec, qVersion
from PyQt5.QtWidgets import QApplication

from E5Gui.E5Application import E5Application

import Globals

import UI.PixmapCache

from eric6config import getConfig


def usage(appinfo, optlen=12):
    """
    Module function to show the usage information.
    
    @param appinfo dictionary describing the application
    @param optlen length of the field for the commandline option (integer)
    """
    options = [
        ("--version", "show the program's version number and exit"),
        ("-h, --help", "show this help message and exit")
    ]
    options.extend(appinfo["options"])
    
    print("""\n"""
          """Usage: {bin} [OPTIONS] {arg}\n"""
          """\n"""
          """{name} - {description}\n"""
          """\n"""
          """Options:""".format(**appinfo))
    for opt in options:
        print("  {0}  {1}".format(opt[0].ljust(optlen), opt[1]))
    sys.exit(0)


def version(appinfo):
    """
    Module function to show the version information.
    
    @param appinfo dictionary describing the application
    """
    print("""\n"""
          """{name} {version}\n"""
          """\n"""
          """{description}\n"""
          """\n"""
          """Copyright (c) 2002 - 2015 Detlev Offenbach"""
          """ <detlev@die-offenbachs.de>\n"""
          """This is free software; see LICENSE.GPL3 for copying"""
          """ conditions.\n"""
          """There is NO warranty; not even for MERCHANTABILITY or FITNESS"""
          """ FOR A\n"""
          """PARTICULAR PURPOSE.""".format(**appinfo))
    sys.exit(0)


def handleArgs(argv, appinfo):
    """
    Module function to handle the always present commandline options.
    
    @param argv list of commandline parameters (list of strings)
    @param appinfo dictionary describing the application
    @return index of the '--' option (integer). This is used to tell
        the application, that all additional options don't belong to
        the application.
    """
    ddindex = 30000     # arbitrarily large number
    args = {
        "--version": version,
        "--help": usage,
        "-h": usage
    }
    if '--' in argv:
        ddindex = argv.index("--")
    for a in args:
        if a in argv and argv.index(a) < ddindex:
            args[a](appinfo)
    return ddindex


def loadTranslatorForLocale(dirs, tn):
    """
    Module function to find and load a specific translation.

    @param dirs Searchpath for the translations. (list of strings)
    @param tn The translation to be loaded. (string)
    @return Tuple of a status flag and the loaded translator
        (int, QTranslator)
    """
    trans = QTranslator(None)
    for dir in dirs:
        loaded = trans.load(tn, dir)
        if loaded:
            return (trans, True)
    
    print("Warning: translation file '" + tn + "'could not be loaded.")
    print("Using default.")
    return (None, False)


def initializeResourceSearchPath():
    """
    Module function to initialize the default mime source factory.
    """
    import Preferences
    
    defaultIconPaths = [
        os.path.join(getConfig('ericIconDir'), "default"),
        os.path.join(getConfig('ericIconDir'), "default", "languages"),
    ]
    iconPaths = Preferences.getIcons("Path")
    for iconPath in iconPaths:
        if iconPath:
            UI.PixmapCache.addSearchPath(iconPath)
    for defaultIconPath in defaultIconPaths:
        if defaultIconPath not in iconPaths:
            UI.PixmapCache.addSearchPath(defaultIconPath)


def setLibraryPaths():
    """
    Module function to set the Qt library paths correctly for windows systems.
    """
    if Globals.isWindowsPlatform():
        libPath = os.path.join(Globals.getPyQt5ModulesDirectory(), "plugins")
        if os.path.exists(libPath):
            libPath = QDir.fromNativeSeparators(libPath)
            libraryPaths = QApplication.libraryPaths()
            if libPath not in libraryPaths:
                libraryPaths.insert(0, libPath)
                QApplication.setLibraryPaths(libraryPaths)

# the translator must not be deleted, therefore we save them here
loaded_translators = {}


def loadTranslators(qtTransDir, app, translationFiles=()):
    """
    Module function to load all required translations.
    
    @param qtTransDir directory of the Qt translations files (string)
    @param app reference to the application object (QApplication)
    @param translationFiles tuple of additional translations to
        be loaded (tuple of strings)
    @return the requested locale (string)
    """
    import Preferences
    
    global loaded_translators
    
    if qVersion() < "5.0.0":
        # set the default encoding for tr()
        QTextCodec.setCodecForTr(QTextCodec.codecForName("utf-8"))
    
    translations = ("qt", "eric6") + translationFiles
    loc = Preferences.getUILanguage()
    if loc is None:
        return

    if loc == "System":
        loc = QLocale.system().name()
    if loc != "C":
        dirs = [getConfig('ericTranslationsDir'), Globals.getConfigDir()]
        if qtTransDir is not None:
            dirs.append(qtTransDir)

        loca = loc
        for tf in ["{0}_{1}".format(tr, loc) for tr in translations]:
            translator, ok = loadTranslatorForLocale(dirs, tf)
            loaded_translators[tf] = translator
            if ok:
                app.installTranslator(translator)
            else:
                if tf.startswith("eric6"):
                    loca = None
        loc = loca
    else:
        loc = None
    return loc


def simpleAppStartup(argv, appinfo, mwFactory, quitOnLastWindowClosed=True,
                     app=None, raiseIt=True, installErrorHandler=False):
    """
    Module function to start up an application that doesn't need a specialized
    start up.
    
    This function is used by all of eric6's helper programs.
    
    @param argv list of commandline parameters (list of strings)
    @param appinfo dictionary describing the application
    @param mwFactory factory function generating the main widget. This
        function must accept the following parameter.
        <dl>
            <dt>argv</dt>
            <dd>list of commandline parameters (list of strings)</dd>
        </dl>
    @keyparam quitOnLastWindowClosed flag indicating to quit the application,
        if the last window was closed (boolean)
    @keyparam app reference to the application object (QApplication or None)
    @keyparam raiseIt flag indicating to raise the generated application
        window (boolean)
    @keyparam installErrorHandler flag indicating to install an error
        handler dialog (boolean)
    @return exit result (integer)
    """
    handleArgs(argv, appinfo)
    if app is None:
        # set the library paths for plugins
        setLibraryPaths()
        app = E5Application(argv)
    app.setQuitOnLastWindowClosed(quitOnLastWindowClosed)
    
    # the following code depends upon a valid application object
    import Preferences
    
    initializeResourceSearchPath()
    QApplication.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
    
    qt4TransDir = Preferences.getQt4TranslationsDir()
    if not qt4TransDir:
        qt4TransDir = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    loadTranslators(qt4TransDir, app)
    
    w = mwFactory(argv)
    if quitOnLastWindowClosed:
        app.lastWindowClosed.connect(app.quit)
    w.show()
    if raiseIt:
        w.raise_()
    
    if installErrorHandler:
        # generate a graphical error handler
        from E5Gui import E5ErrorMessage
        eMsg = E5ErrorMessage.qtHandler()
        eMsg.setMinimumSize(600, 400)
    
    return app.exec_()
