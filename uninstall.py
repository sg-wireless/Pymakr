#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#
# This is the uninstall script for eric6.
#

"""
Uninstallation script for the eric6 IDE and all eric6 related tools.
"""

from __future__ import unicode_literals, print_function

import sys
import os
import shutil
import glob
import distutils.sysconfig

if sys.version_info[0] == 2:
    import sip
    sip.setapi('QString', 2)

# get a local eric6config.py out of the way
if os.path.exists("eric6config.py"):
    os.rename("eric6config.py", "eric6config.py.orig")
from eric6config import getConfig

# Define the globals.
progName = None
pyModDir = None
progLanguages = ["Python", "Ruby", "QSS"]
includePythonVariant = False
defaultMacAppBundleName = "pymakr.app"
defaultMacAppBundlePath = "/Applications"
settingsNameOrganization = "Pycom"
settingsNameGlobal = "pymakr"

# Define file name markers for Python variants
PythonMarkers = {
    2: "_py2",
    3: "_py3",
}


def exit(rcode=0):
    """
    Exit the uninstall script.
    
    @param rcode result code to report back (integer)
    """
    # restore the local eric6config.py
    if os.path.exists("eric6config.py.orig"):
        if os.path.exists("eric6config.py"):
            os.remove("eric6config.py")
        os.rename("eric6config.py.orig", "eric6config.py")


def usage(rcode=2):
    """
    Display a usage message and exit.

    @param rcode return code passed back to the calling process (integer)
    """
    global progName

    print("Usage:")
    print("    {0} [-h]".format(progName))
    print("where:")
    print("    -h             display this help message")
    print("    -y             remove executables with Python variant in name")

    exit(rcode)


def initGlobals():
    """
    Set the values of globals that need more than a simple assignment.
    """
    global pyModDir

    pyModDir = distutils.sysconfig.get_python_lib(True)


def wrapperName(dname, wfile):
    """
    Create the platform specific name for the wrapper script.
    
    @param dname name of the directory to place the wrapper into
    @param wfile basename (without extension) of the wrapper script
    @return the name of the wrapper script
    """
    if sys.platform.startswith("win"):
        wname = dname + "\\" + wfile + ".bat"
    else:
        wname = dname + "/" + wfile

    return wname


def uninstallEric():
    """
    Uninstall the eric files.
    """
    global pyModDir
    
    # Remove the menu entry for Linux systems
    if sys.platform.startswith("linux") and os.getuid() == 0:
        if includePythonVariant:
            marker = PythonMarkers[sys.version_info.major]
        else:
            marker = ""
        for name in ["/usr/share/applications/pymakr" + marker + ".desktop",
                     "/usr/share/appdata/pymakr" + marker + ".appdata.xml",
                     "/usr/share/applications/pymakr_webbrowser" + marker +
                     ".desktop",
                     "/usr/share/pixmaps/pymakr" + marker + ".png",
                     "/usr/share/pixmaps/ericWeb" + marker + ".png"]:
            if os.path.exists(name):
                os.remove(name)
    
    # Remove the wrapper scripts
    rem_wnames = [
        "eric6_api", "eric6_compare",
        "eric6_configure", "eric6_diff",
        "eric6_doc", "eric6_qregularexpression",
        "eric6_qregexp", "eric6_re",
        "eric6_trpreviewer", "eric6_uipreviewer",
        "eric6_unittest", "eric6",
        "eric6_tray", "eric6_editor",
        "eric6_plugininstall", "eric6_pluginuninstall",
        "eric6_pluginrepository", "eric6_sqlbrowser",
        "pymakr_webbrowser", "eric6_iconeditor",
        "eric6_snap",
    ]
    if includePythonVariant:
        marker = PythonMarkers[sys.version_info.major]
        rem_wnames = [n + marker for n in rem_wnames]
    
    try:
        for rem_wname in rem_wnames:
            rwname = wrapperName(getConfig('bindir'), rem_wname)
            if os.path.exists(rwname):
                os.remove(rwname)
        
        # Cleanup our config file(s)
        for name in ['eric6config.py', 'eric6config.pyc', 'eric6.pth']:
            e5cfile = os.path.join(pyModDir, name)
            if os.path.exists(e5cfile):
                os.remove(e5cfile)
            e5cfile = os.path.join(pyModDir, "__pycache__", name)
            path, ext = os.path.splitext(e5cfile)
            for f in glob.glob("{0}.*{1}".format(path, ext)):
                os.remove(f)
        
        # Cleanup the install directories
        for name in ['ericExamplesDir', 'ericDocDir', 'ericDTDDir',
                     'ericCSSDir', 'ericIconDir', 'ericPixDir',
                     'ericTemplatesDir', 'ericCodeTemplatesDir',
                     'ericOthersDir', 'ericStylesDir', 'ericDir']:
            dirpath = getConfig(name)
            if os.path.exists(dirpath):
                shutil.rmtree(dirpath, True)
        
        # Cleanup translations
        for name in glob.glob(
                os.path.join(getConfig('ericTranslationsDir'), 'eric6_*.qm')):
            if os.path.exists(name):
                os.remove(name)
        
        # Cleanup API files
        apidir = getConfig('apidir')
        if apidir:
            for progLanguage in progLanguages:
                for name in getConfig('apis'):
                    apiname = os.path.join(apidir, progLanguage.lower(), name)
                    if os.path.exists(apiname):
                        os.remove(apiname)
                for apiname in glob.glob(
                        os.path.join(apidir, progLanguage.lower(), "*.bas")):
                    if os.path.basename(apiname) != "eric6.bas":
                        os.remove(apiname)
        
        if sys.platform == "darwin":
            # delete the Mac app bundle
            if os.path.exists("/Developer/Applications/pymakr"):
                shutil.rmtree("/Developer/Applications/pymakr")
            try:
                macAppBundlePath = getConfig("macAppBundlePath")
                macAppBundleName = getConfig("macAppBundleName")
            except AttributeError:
                macAppBundlePath = defaultMacAppBundlePath
                macAppBundleName = defaultMacAppBundleName
            for bundlePath in [os.path.join(defaultMacAppBundlePath,
                                            macAppBundleName),
                               os.path.join(macAppBundlePath,
                                            macAppBundleName),
                               ]:
                if os.path.exists(bundlePath):
                    shutil.rmtree(bundlePath)
        
        # remove plug-in directories
        removePluginDirectories()
        
        # remove the eric data directory
        removeDataDirectory()
        
        # remove the eric configuration directory
        removeConfigurationData()
        
        print("\nUninstallation completed")
    except (IOError, OSError) as msg:
        sys.stderr.write(
            'Error: {0}\nTry uninstall with admin rights.\n'.format(msg))
        exit(7)


def removePluginDirectories():
    """
    Remove the plug-in directories.
    """
    pathsToRemove = []
    
    globalPluginsDir = os.path.join(getConfig('mdir'), "eric6plugins")
    if os.path.exists(globalPluginsDir):
        pathsToRemove.append(globalPluginsDir)
    
    localPluginsDir = os.path.join(getConfigDir(), "eric6plugins")
    if os.path.exists(localPluginsDir):
        pathsToRemove.append(localPluginsDir)
    
    if pathsToRemove:
        print("Found these plug-in directories")
        for path in pathsToRemove:
            print("  - {0}".format(path))
        answer = "c"
        while answer not in ["y", "Y", "n", "N", ""]:
            if sys.version_info[0] == 2:
                answer = raw_input(
                    "Shall these directories be removed (y/N)? ")
            else:
                answer = input(
                    "Shall these directories be removed (y/N)? ")
        if answer in ["y", "Y"]:
            for path in pathsToRemove:
                shutil.rmtree(path)


def removeDataDirectory():
    """
    Remove the eric data directory.
    """
    cfg = getConfigDir()
    if os.path.exists(cfg):
        print("Found the Pymakr data directory")
        print("  - {0}".format(cfg))
        answer = "c"
        while answer not in ["y", "Y", "n", "N", ""]:
            if sys.version_info[0] == 2:
                answer = raw_input(
                    "Shall this directory be removed (y/N)? ")
            else:
                answer = input(
                    "Shall this directory be removed (y/N)? ")
        if answer in ["y", "Y"]:
            shutil.rmtree(cfg)


def removeConfigurationData():
    """
    Remove the eric configuration directory.
    """
    try:
        from PyQt5.QtCore import QSettings
    except ImportError:
        try:
            from PyQt4.QtCore import QSettings
        except ImportError:
            print("No PyQt variant installed. The configuration directory")
            print("cannot be determined. You have to remove it manually.\n")
            return
    
    settings = QSettings(QSettings.IniFormat, QSettings.UserScope,
                         settingsNameOrganization, settingsNameGlobal)
    settingsDir = os.path.dirname(settings.fileName())
    if os.path.exists(settingsDir):
        print("Found the Pymakr configuration directory")
        print("  - {0}".format(settingsDir))
        answer = "c"
        while answer not in ["y", "Y", "n", "N", ""]:
            if sys.version_info[0] == 2:
                answer = raw_input(
                    "Shall this directory be removed (y/N)? ")
            else:
                answer = input(
                    "Shall this directory be removed (y/N)? ")
        if answer in ["y", "Y"]:
            shutil.rmtree(settingsDir)


def getConfigDir():
    """
    Module function to get the name of the directory storing the config data.
    
    @return directory name of the config dir (string)
    """
    if sys.platform.startswith("win"):
        cdn = "_pymakr"
        return os.path.join(os.path.expanduser("~"), cdn)
    else:
        cdn = ".pymakr"
        return os.path.join(
            os.path.expanduser("~{0}".format(os.getlogin())), cdn)


def main(argv):
    """
    The main function of the script.

    @param argv list of command line arguments
    """
    import getopt

    global includePythonVariant
    
    initGlobals()

    # Parse the command line.
    global progName
    progName = os.path.basename(argv[0])

    try:
        optlist, args = getopt.getopt(argv[1:], "hy")
    except getopt.GetoptError:
        usage()

    global platBinDir

    for opt, arg in optlist:
        if opt == "-h":
            usage(0)
        if opt == "-y":
            includePythonVariant = True
    
    try:
        uninstallEric()
    except IOError as msg:
        sys.stderr.write(
            'IOError: {0}\nTry uninstall with admin rights.\n'.format(msg))
    except OSError as msg:
        sys.stderr.write(
            'OSError: {0}\nTry uninstall with admin rights.\n'.format(msg))
    
    exit(0)


if __name__ == "__main__":
    try:
        main(sys.argv)
    except SystemExit:
        raise
    except Exception:
        print("""An internal error occured.  Please report all the output of"""
              """ the program,\n"""
              """including the following traceback, to"""
              """ support@pycom.io.\n""")
        raise
