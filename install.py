#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#
# This is the install script for eric6.

"""
Installation script for the eric6 IDE and all eric6 related tools.
"""

from __future__ import unicode_literals, print_function
try:
    import cStringIO as io
    import sip
    sip.setapi('QString', 2)
    sip.setapi('QVariant', 2)
    sip.setapi('QTextStream', 2)
except (ImportError):
    import io    # __IGNORE_WARNING__

import sys
import os
import re
import compileall
import py_compile
import glob
import shutil
import fnmatch
import distutils.sysconfig
import codecs
import subprocess

# Define the globals.
progName = None
currDir = os.getcwd()
modDir = None
pyModDir = None
platBinDir = None
platBinDirOld = None
distDir = None
apisDir = None
installApis = True
doCleanup = True
doCompile = True
includePythonVariant = False
cfg = {}
progLanguages = ["Python", "Ruby", "QSS"]
sourceDir = "eric"
configName = 'eric6config.py'
defaultMacAppBundleName = "eric6.app"
defaultMacAppBundlePath = "/Applications"
defaultMacPythonExe = "{0}/Resources/Python.app/Contents/MacOS/Python".format(
    sys.exec_prefix)
macAppBundleName = defaultMacAppBundleName
macAppBundlePath = defaultMacAppBundlePath
macPythonExe = defaultMacPythonExe
pyqtVariant = ""
pyqtOverride = False

# Define blacklisted versions of the prerequisites
BlackLists = {
    "sip": ["4.11", "4.12.3"],
    "PyQt4": [],
    "PyQt5": [],
    "QScintilla2": [],
}
PlatformsBlackLists = {
    "windows": {
        "sip": [],
        "PyQt4": [],
        "PyQt5": [],
        "QScintilla2": [],
    },
    
    "linux": {
        "sip": [],
        "PyQt4": [],
        "PyQt5": [],
        "QScintilla2": [],
    },
    
    "mac": {
        "sip": [],
        "PyQt4": [],
        "PyQt5": [],
        "QScintilla2": [],
    },
}

# Define file name markers for Python variants
PythonMarkers = {
    2: "_py2",
    3: "_py3",
}
# Define a mapping of markers to full text
PythonTextMarkers = {
    "_py2": "Python 2",
    "_py3": "Python 3",
}


def exit(rcode=0):
    """
    Exit the install script.
    
    @param rcode result code to report back (integer)
    """
    global currDir
    
    if sys.platform.startswith("win"):
        # different meaning of input between Py2 and Py3
        try:
            input("Press enter to continue...")
        except (EOFError, SyntaxError):
            pass
    
    os.chdir(currDir)
    
    sys.exit(rcode)


def usage(rcode=2):
    """
    Display a usage message and exit.

    @param rcode the return code passed back to the calling process.
    """
    global progName, modDir, distDir, apisDir
    global macAppBundleName, macAppBundlePath, macPythonExe
    global pyqtVariant

    print()
    print("Usage:")
    if sys.platform == "darwin":
        print("    {0} [-chxyz] [-a dir] [-b dir] [-d dir] [-f file] [-i dir]"
              " [-m name] [-p python] [--pyqt=version]".format(progName))
    elif sys.platform.startswith("win"):
        print("    {0} [-chxyz] [-a dir] [-b dir] [-d dir] [-f file]"
              " [--pyqt=version]"
              .format(progName))
    else:
        print("    {0} [-chxyz] [-a dir] [-b dir] [-d dir] [-f file] [-i dir]"
              " [--pyqt=version]"
              .format(progName))
    print("where:")
    print("    -h, --help display this help message")
    print("    -a dir     where the API files will be installed")
    if apisDir:
        print("               (default: {0})".format(apisDir))
    else:
        print("               (no default value)")
    print("    --noapis   don't install API files")
    print("    -b dir     where the binaries will be installed")
    print("               (default: {0})".format(platBinDir))
    print("    -d dir     where eric6 python files will be installed")
    print("               (default: {0})".format(modDir))
    print("    -f file    configuration file naming the various installation"
          " paths")
    if not sys.platform.startswith("win"):
        print("    -i dir     temporary install prefix")
        print("               (default: {0})".format(distDir))
    if sys.platform == "darwin":
        print("    -m name    name of the Mac app bundle")
        print("               (default: {0})".format(macAppBundleName))
        print("    -n path    path of the directory the Mac app bundle will")
        print("               be created in")
        print("               (default: {0})".format(macAppBundlePath))
        print("    -p python  path of the python executable")
        print("               (default: {0})".format(macPythonExe))
    print("    -c         don't cleanup old installation first")
    print("    -x         don't perform dependency checks (use on your own"
          " risk)")
    print("    -y         add the Python variant to the executable names")
    print("    -z         don't compile the installed python files")
    print("    --pyqt=version version of PyQt to be used (one of 4 or 5)")
    if pyqtVariant:
        print("                   (default: {0})".format(pyqtVariant[-1]))
    else:
        print("                   (no PyQt variant found)")
    print()
    print("The file given to the -f option must be valid Python code"
          " defining a")
    print("dictionary called 'cfg' with the keys 'ericDir', 'ericPixDir',"
          " 'ericIconDir',")
    print("'ericDTDDir', 'ericCSSDir', 'ericStylesDir', 'ericDocDir',"
          " 'ericExamplesDir',")
    print("'ericTranslationsDir', 'ericTemplatesDir', 'ericCodeTemplatesDir',")
    print("'ericOthersDir','bindir', 'mdir' and 'apidir.")
    print("These define the directories for the installation of the various"
          " parts of eric6.")

    exit(rcode)


def determinePyQtVariant():
    """
    Module function to determine the PyQt variant to be used.
    """
    global pyqtVariant, pyqtOverride
    
    pyqtVariant = ""
    # need to handle the --pyqt= option here
    if "--pyqt=4" in sys.argv:
        pyqtVariant = "PyQt4"
        pyqtOverride = True
    elif "--pyqt=5" in sys.argv:
        pyqtVariant = "PyQt5"
        pyqtOverride = True
    else:
        try:
            import PyQt5        # __IGNORE_WARNING__
            pyqtVariant = "PyQt5"
            del sys.modules["PyQt5"]
        except ImportError:
            try:
                import PyQt4    # __IGNORE_WARNING__
                pyqtVariant = "PyQt4"
                del sys.modules["PyQt4"]
            except ImportError:
                pyqtVariant = ""


def initGlobals():
    """
    Module function to set the values of globals that need more than a
    simple assignment.
    """
    global platBinDir, modDir, pyModDir, apisDir, pyqtVariant, platBinDirOld

    if sys.platform.startswith("win"):
        platBinDir = sys.exec_prefix
        if platBinDir.endswith("\\"):
            platBinDir = platBinDir[:-1]
        platBinDirOld = platBinDir
        platBinDir = os.path.join(platBinDir, "Scripts")
        if not os.path.exists(platBinDir):
            platBinDir = platBinDirOld
    else:
        platBinDir = "/usr/local/bin"

    modDir = distutils.sysconfig.get_python_lib(True)
    pyModDir = modDir
    
    pyqtDataDir = os.path.join(modDir, pyqtVariant)
    if os.path.exists(os.path.join(pyqtDataDir, "qsci")):
        # it's the installer
        qtDataDir = pyqtDataDir
    else:
        try:
            if pyqtVariant == "PyQt4":
                from PyQt4.QtCore import QLibraryInfo
            else:
                from PyQt5.QtCore import QLibraryInfo
            qtDataDir = QLibraryInfo.location(QLibraryInfo.DataPath)
        except ImportError:
            qtDataDir = None
    if qtDataDir:
        apisDir = os.path.join(qtDataDir, "qsci", "api")
    else:
        apisDir = None


def copyToFile(name, text):
    """
    Copy a string to a file.

    @param name the name of the file.
    @param text the contents to copy to the file.
    """
    f = open(name, "w")
    if sys.version_info[0] == 2:
        text = codecs.encode(text, "utf-8")
    f.write(text)
    f.close()


def copyDesktopFile(src, dst, marker):
    """
    Modify a desktop file and write it to its destination.
    
    @param src source file name (string)
    @param dst destination file name (string)
    @param marker marker to be used (string)
    """
    if sys.version_info[0] == 2:
        f = codecs.open(src, "r", "utf-8")
    else:
        f = open(src, "r", encoding="utf-8")
    text = f.read()
    f.close()
    
    text = text.replace("@MARKER@", marker)
    if marker:
        t_marker = " ({0})".format(PythonTextMarkers[marker])
    else:
        t_marker = ""
    text = text.replace("@PY_MARKER@", t_marker)
    
    if sys.version_info[0] == 2:
        f = codecs.open(dst, "w", "utf-8")
    else:
        f = open(dst, "w", encoding="utf-8")
    f.write(text)
    f.close()
    os.chmod(dst, 0o644)


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


def createPyWrapper(pydir, wfile, isGuiScript=True):
    """
    Create an executable wrapper for a Python script.

    @param pydir the name of the directory where the Python script will
        eventually be installed (string)
    @param wfile the basename of the wrapper (string)
    @param isGuiScript flag indicating a wrapper script for a GUI
        application (boolean)
    @return the platform specific name of the wrapper (string)
    """
    global includePythonVariant, pyqtVariant, pyqtOverride
    
    if includePythonVariant:
        marker = PythonMarkers[sys.version_info.major]
    else:
        marker = ""
    
    if pyqtOverride and pyqtVariant == "PyQt4":
        pyqt4opt = " --pyqt4"
    else:
        pyqt4opt = ""
    
    # all kinds of Windows systems
    if sys.platform.startswith("win"):
        wname = wfile + marker + ".bat"
        if isGuiScript:
            wrapper = \
                '''@echo off\n''' \
                '''start "" "{2}\\pythonw.exe"''' \
                ''' "{0}\\{1}.pyw"{3}''' \
                ''' %1 %2 %3 %4 %5 %6 %7 %8 %9\n'''.format(
                    pydir, wfile, sys.exec_prefix, pyqt4opt)
        else:
            wrapper = \
                '''@"{0}\\python" "{1}\\{2}.py"{3}''' \
                ''' %1 %2 %3 %4 %5 %6 %7 %8 %9\n'''.format(
                    sys.exec_prefix, pydir, wfile, pyqt4opt)

    # Mac OS X
    elif sys.platform == "darwin":
        major = sys.version_info.major
        pyexec = "{0}/bin/pythonw{1}".format(sys.exec_prefix, major)
        if not os.path.exists(pyexec):
            pyexec = "{0}/bin/python{1}".format(sys.exec_prefix, major)
        wname = wfile + marker
        wrapper = ('''#!/bin/sh\n'''
                   '''\n'''
                   '''exec "{0}" "{1}/{2}.py"{3} "$@"\n'''
                   .format(pyexec, pydir, wfile, pyqt4opt))

    # *nix systems
    else:
        wname = wfile + marker
        wrapper = ('''#!/bin/sh\n'''
                   '''\n'''
                   '''exec "{0}" "{1}/{2}.py"{3} "$@"\n'''
                   .format(sys.executable, pydir, wfile, pyqt4opt))

    copyToFile(wname, wrapper)
    os.chmod(wname, 0o755)

    return wname


def copyTree(src, dst, filters, excludeDirs=[], excludePatterns=[]):
    """
    Copy Python, translation, documentation, wizards configuration,
    designer template files and DTDs of a directory tree.
    
    @param src name of the source directory
    @param dst name of the destination directory
    @param filters list of filter pattern determining the files to be copied
    @param excludeDirs list of (sub)directories to exclude from copying
    @keyparam excludePatterns list of filter pattern determining the files to
        be skipped
    """
    try:
        names = os.listdir(src)
    except OSError:
        # ignore missing directories (most probably the i18n directory)
        return
    
    for name in names:
        skipIt = False
        for excludePattern in excludePatterns:
            if fnmatch.fnmatch(name, excludePattern):
                skipIt = True
                break
        if not skipIt:
            srcname = os.path.join(src, name)
            dstname = os.path.join(dst, name)
            for filter in filters:
                if fnmatch.fnmatch(srcname, filter):
                    if not os.path.isdir(dst):
                        os.makedirs(dst)
                    shutil.copy2(srcname, dstname)
                    os.chmod(dstname, 0o644)
                    break
            else:
                if os.path.isdir(srcname) and srcname not in excludeDirs:
                    copyTree(srcname, dstname, filters,
                             excludePatterns=excludePatterns)


def createGlobalPluginsDir():
    """
    Create the global plugins directory, if it doesn't exist.
    """
    global cfg, distDir
    
    pdir = os.path.join(cfg['mdir'], "eric6plugins")
    fname = os.path.join(pdir, "__init__.py")
    if not os.path.exists(fname):
        if not os.path.exists(pdir):
            os.mkdir(pdir, 0o755)
        f = open(fname, "w")
        f.write(
'''# -*- coding: utf-8 -*-

"""
Package containing the global plugins.
"""
'''
        )
        f.close()
        os.chmod(fname, 0o644)


def cleanupSource(dirName):
    """
    Cleanup the sources directory to get rid of leftover files
    and directories.
    
    @param dirName name of the directory to prune (string)
    """
    # step 1: delete all Ui_*.py files without a corresponding
    #         *.ui file
    dirListing = os.listdir(dirName)
    for formName, sourceName in [
        (f.replace('Ui_', "").replace(".py", ".ui"), f)
            for f in dirListing if fnmatch.fnmatch(f, "Ui_*.py")]:
        if not os.path.exists(os.path.join(dirName, formName)):
            os.remove(os.path.join(dirName, sourceName))
            if os.path.exists(os.path.join(dirName, sourceName + "c")):
                os.remove(os.path.join(dirName, sourceName + "c"))
    
    # step 2: delete the __pycache__ directory and all *.pyc files
    if os.path.exists(os.path.join(dirName, "__pycache__")):
        shutil.rmtree(os.path.join(dirName, "__pycache__"))
    for name in [f for f in dirListing if fnmatch.fnmatch(f, "*.pyc")]:
        os.remove(os.path.join(dirName, name))
    
    # step 3: descent into subdirectories and delete them if empty
    for name in os.listdir(dirName):
        name = os.path.join(dirName, name)
        if os.path.isdir(name):
            cleanupSource(name)
            if len(os.listdir(name)) == 0:
                os.rmdir(name)


def cleanUp():
    """
    Uninstall the old eric files.
    """
    global platBinDir, platBinDirOld, includePythonVariant
    
    try:
        from eric6config import getConfig
    except ImportError:
        # eric6 wasn't installed previously
        return
    
    global pyModDir, progLanguages
    
    # Remove the menu entry for Linux systems
    if sys.platform.startswith("linux") and os.getuid() == 0:
        for name in ["/usr/share/pixmaps/eric.png",
                     "/usr/share/pixmaps/ericWeb.png"]:
            if os.path.exists(name):
                os.remove(name)
        if includePythonVariant:
            marker = PythonMarkers[sys.version_info.major]
        else:
            marker = ""
        for name in ["/usr/share/applications/eric6" + marker + ".desktop",
                     "/usr/share/appdata/eric6" + marker + ".appdata.xml",
                     "/usr/share/applications/eric6_webbrowser" + marker +
                     ".desktop"]:
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
        "eric6_webbrowser", "eric6_iconeditor",
        "eric6_snap",
    ]
    if includePythonVariant:
        marker = PythonMarkers[sys.version_info.major]
        rem_wnames = [n + marker for n in rem_wnames]
    
    try:
        dirs = [platBinDir, getConfig('bindir')]
        if platBinDirOld:
            dirs.append(platBinDirOld)
        for rem_wname in rem_wnames:
            for d in dirs:
                rwname = wrapperName(d, rem_wname)
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
            if os.path.exists(getConfig(name)):
                shutil.rmtree(getConfig(name), True)
        
        # Cleanup translations
        for name in glob.glob(
                os.path.join(getConfig('ericTranslationsDir'), 'eric6_*.qm')):
            if os.path.exists(name):
                os.remove(name)
        
        # Cleanup API files
        try:
            apidir = getConfig('apidir')
            for progLanguage in progLanguages:
                for name in getConfig('apis'):
                    apiname = os.path.join(apidir, progLanguage.lower(), name)
                    if os.path.exists(apiname):
                        os.remove(apiname)
                for apiname in glob.glob(
                        os.path.join(apidir, progLanguage.lower(), "*.bas")):
                    if os.path.basename(apiname) != "eric6.bas":
                        os.remove(apiname)
        except AttributeError:
            pass
        
        if sys.platform == "darwin":
            # delete the Mac app bundle
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
    except (IOError, OSError) as msg:
        sys.stderr.write(
            'Error: {0}\nTry install with admin rights.\n'.format(msg))
        exit(7)


def shutilCopy(src, dst, perm=0o644):
    """
    Wrapper function around shutil.copy() to ensure the permissions.
    
    @param src source file name (string)
    @param dst destination file name or directory name (string)
    @keyparam perm permissions to be set (integer)
    """
    shutil.copy(src, dst)
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    os.chmod(dst, perm)


def installEric():
    """
    Actually perform the installation steps.
    
    @return result code (integer)
    """
    global distDir, doCleanup, cfg, progLanguages, sourceDir, configName
    global includePythonVariant, installApis
    
    # Create the platform specific wrappers.
    wnames = []
    for name in ["eric6_api", "eric6_doc"]:
        wnames.append(createPyWrapper(cfg['ericDir'], name, False))
    for name in ["eric6_compare", "eric6_configure", "eric6_diff",
                 "eric6_editor", "eric6_iconeditor", "eric6_plugininstall",
                 "eric6_pluginrepository", "eric6_pluginuninstall",
                 "eric6_qregexp", "eric6_qregularexpression", "eric6_re",
                 "eric6_snap", "eric6_sqlbrowser", "eric6_tray",
                 "eric6_trpreviewer", "eric6_uipreviewer", "eric6_unittest",
                 "eric6_webbrowser", "eric6"]:
        wnames.append(createPyWrapper(cfg['ericDir'], name))
    
    # set install prefix, if not None
    if distDir:
        for key in list(cfg.keys()):
            cfg[key] = os.path.normpath(distDir + os.sep + cfg[key])
    
    try:
        # Install the files
        # make the install directories
        for key in cfg.keys():
            if cfg[key] and not os.path.isdir(cfg[key]):
                os.makedirs(cfg[key])
        
        # copy the eric6 config file
        if distDir:
            shutilCopy(configName, cfg['mdir'])
            if os.path.exists(configName + 'c'):
                shutilCopy(configName + 'c', cfg['mdir'])
        else:
            shutilCopy(configName, modDir)
            if os.path.exists(configName + 'c'):
                shutilCopy(configName + 'c', modDir)
        
        # copy the various parts of eric6
        copyTree(
            sourceDir, cfg['ericDir'],
            ['*.py', '*.pyc', '*.pyo', '*.pyw'],
            ['{1}{0}Examples'.format(os.sep, sourceDir),
             '{1}{0}.ropeproject'.format(os.sep, sourceDir)],
            excludePatterns=["eric6config.py*"])
        copyTree(
            sourceDir, cfg['ericDir'], ['*.rb'],
            ['{1}{0}Examples'.format(os.sep, sourceDir)])
        copyTree(
            '{1}{0}Plugins'.format(os.sep, sourceDir),
            '{0}{1}Plugins'.format(cfg['ericDir'], os.sep),
            ['*.png', '*.style', '*.tmpl'])
        copyTree(
            '{1}{0}Documentation'.format(os.sep, sourceDir), cfg['ericDocDir'],
            ['*.html', '*.qch'])
        copyTree(
            '{1}{0}DTDs'.format(os.sep, sourceDir), cfg['ericDTDDir'],
            ['*.dtd'])
        copyTree(
            '{1}{0}CSSs'.format(os.sep, sourceDir), cfg['ericCSSDir'],
            ['*.css'])
        copyTree(
            '{1}{0}Styles'.format(os.sep, sourceDir), cfg['ericStylesDir'],
            ['*.qss'])
        copyTree(
            '{1}{0}i18n'.format(os.sep, sourceDir), cfg['ericTranslationsDir'],
            ['*.qm'])
        copyTree(
            '{1}{0}icons'.format(os.sep, sourceDir), cfg['ericIconDir'],
            ['*.png', 'LICENSE*.*', 'readme.txt'])
        copyTree(
            '{1}{0}pixmaps'.format(os.sep, sourceDir), cfg['ericPixDir'],
            ['*.png', '*.xpm', '*.ico', '*.gif'])
        copyTree(
            '{1}{0}DesignerTemplates'.format(os.sep, sourceDir),
            cfg['ericTemplatesDir'],
            ['*.tmpl'])
        copyTree(
            '{1}{0}CodeTemplates'.format(os.sep, sourceDir),
            cfg['ericCodeTemplatesDir'],
            ['*.tmpl'])
        copyTree(
            '{1}{0}Examples'.format(os.sep, sourceDir), cfg['ericExamplesDir'],
            ['*.py', '*.pyc', '*.pyo'])
        
        # copy the wrappers
        for wname in wnames:
            shutilCopy(wname, cfg['bindir'], perm=0o755)
            os.remove(wname)
        
        # copy the license file
        shutilCopy(
            '{1}{0}LICENSE.GPL3'.format(os.sep, sourceDir), cfg['ericDir'])
        
        # create the global plugins directory
        createGlobalPluginsDir()
        
    except (IOError, OSError) as msg:
        sys.stderr.write(
            'Error: {0}\nTry install with admin rights.\n'.format(msg))
        return(7)
    
    # copy some text files to the doc area
    for name in ["LICENSE.GPL3", "THANKS", "changelog"]:
        try:
            shutilCopy(
                '{2}{0}{1}'.format(os.sep, name, sourceDir), cfg['ericDocDir'])
        except EnvironmentError:
            print("Could not install '{2}{0}{1}'.".format(
                os.sep, name, sourceDir))
    for name in glob.glob(os.path.join(sourceDir, 'README*.*')):
        try:
            shutilCopy(name, cfg['ericDocDir'])
        except EnvironmentError:
            print("Could not install '{0}'.".format(name))
   
    # copy some more stuff
    for name in ['default.e4k', 'default_Mac.e4k']:
        try:
            shutilCopy(
                '{2}{0}{1}'.format(os.sep, name, sourceDir),
                cfg['ericOthersDir'])
        except EnvironmentError:
            print("Could not install '{2}{0}{1}'.".format(
                os.sep, name, sourceDir))
    
    # install the API file
    if installApis:
        for progLanguage in progLanguages:
            apidir = os.path.join(cfg['apidir'], progLanguage.lower())
            if not os.path.exists(apidir):
                os.makedirs(apidir)
            for apiName in glob.glob(os.path.join(sourceDir, "APIs",
                                                  progLanguage, "*.api")):
                try:
                    shutilCopy(apiName, apidir)
                except EnvironmentError:
                    print("Could not install '{0}'.".format(apiName))
            for apiName in glob.glob(os.path.join(sourceDir, "APIs",
                                                  progLanguage, "*.bas")):
                try:
                    shutilCopy(apiName, apidir)
                except EnvironmentError:
                    print("Could not install '{0}'.".format(apiName))
            if progLanguage == "Python":
                # copy Python3 API files to the same destination
                for apiName in glob.glob(os.path.join(sourceDir, "APIs",
                                                      "Python3", "*.api")):
                    try:
                        shutilCopy(apiName, apidir)
                    except EnvironmentError:
                        print("Could not install '{0}'.".format(apiName))
                for apiName in glob.glob(os.path.join(sourceDir, "APIs",
                                                      "Python3", "*.bas")):
                    if os.path.exists(os.path.join(
                        apidir, os.path.basename(
                            apiName.replace(".bas", ".api")))):
                        try:
                            shutilCopy(apiName, apidir)
                        except EnvironmentError:
                            print("Could not install '{0}'.".format(apiName))
    
    # create menu entry for Linux systems
    if sys.platform.startswith("linux"):
        if includePythonVariant:
            marker = PythonMarkers[sys.version_info.major]
        else:
            marker = ""
    
        if distDir:
            dst = os.path.normpath(os.path.join(distDir, "usr/share/pixmaps"))
            if not os.path.exists(dst):
                os.makedirs(dst)
            shutilCopy(
                os.path.join(sourceDir, "icons", "default", "eric.png"),
                os.path.join(dst, "eric" + marker + ".png"))
            shutilCopy(
                os.path.join(sourceDir, "icons", "default", "ericWeb48.png"),
                os.path.join(dst, "ericWeb" + marker + ".png"))
            dst = os.path.normpath(
                os.path.join(distDir, "usr/share/applications"))
            if not os.path.exists(dst):
                os.makedirs(dst)
            copyDesktopFile(os.path.join(sourceDir, "eric6.desktop"),
                            os.path.join(dst, "eric6" + marker + ".desktop"),
                            marker)
            copyDesktopFile(
                os.path.join(sourceDir, "eric6_webbrowser.desktop"),
                os.path.join(dst, "eric6_webbrowser" + marker + ".desktop"),
                marker)
            dst = os.path.normpath(
                os.path.join(distDir, "usr/share/appdata"))
            if not os.path.exists(dst):
                os.makedirs(dst)
            copyDesktopFile(
                os.path.join(sourceDir, "eric6.appdata.xml"),
                os.path.join(dst, "eric6" + marker + ".appdata.xml"),
                marker)
        elif os.getuid() == 0:
            shutilCopy(os.path.join(
                sourceDir, "icons", "default", "eric.png"),
                "/usr/share/pixmaps/eric" + marker + ".png")
            copyDesktopFile(
                os.path.join(sourceDir, "eric6.desktop"),
                "/usr/share/applications/eric6" + marker + ".desktop",
                marker)
            if os.path.exists("/usr/share/appdata"):
                copyDesktopFile(
                    os.path.join(sourceDir, "eric6.appdata.xml"),
                    "/usr/share/appdata/eric6" + marker + ".appdata.xml",
                    marker)
            shutilCopy(os.path.join(
                sourceDir, "icons", "default", "ericWeb48.png"),
                "/usr/share/pixmaps/ericWeb" + marker + ".png")
            copyDesktopFile(
                os.path.join(sourceDir, "eric6_webbrowser.desktop"),
                "/usr/share/applications/eric6_webbrowser" + marker +
                ".desktop",
                marker)
    
    # Create a Mac application bundle
    if sys.platform == "darwin":
        createMacAppBundle(cfg['ericDir'])
    
    return 0


def createMacAppBundle(pydir):
    """
    Create a Mac application bundle.

    @param pydir the name of the directory where the Python script will
        eventually be installed (string)
    """
    global cfg, sourceDir, macAppBundleName, macPythonExe, macAppBundlePath, \
        pyqtVariant
    
    dirs = {
        "contents": "{0}/{1}/Contents/".format(
            macAppBundlePath, macAppBundleName),
        "exe": "{0}/{1}/Contents/MacOS".format(
            macAppBundlePath, macAppBundleName),
        "icns": "{0}/{1}/Contents/Resources".format(
            macAppBundlePath, macAppBundleName)
    }
    os.makedirs(dirs["contents"])
    os.makedirs(dirs["exe"])
    os.makedirs(dirs["icns"])
    
    if macPythonExe == defaultMacPythonExe:
        starter = os.path.join(dirs["exe"], "eric")
        os.symlink(macPythonExe, starter)
    else:
        starter = "python{0}".format(sys.version_info.major)
    
    wname = os.path.join(dirs["exe"], "eric6")
    
    # determine entry for DYLD_FRAMEWORK_PATH
    dyldLine = ""
    try:
        if pyqtVariant == "PyQt4":
            from PyQt4.QtCore import QLibraryInfo
        else:
            from PyQt5.QtCore import QLibraryInfo
        qtLibraryDir = QLibraryInfo.location(QLibraryInfo.LibrariesPath)
    except ImportError:
        qtLibraryDir = ""
    if qtLibraryDir:
        dyldLine = "DYLD_FRAMEWORK_PATH={0}\n".format(qtLibraryDir)
    
    # determine entry for PATH
    pathLine = ""
    path = os.getenv("PATH", "")
    if path:
        pybin = os.path.join(sys.exec_prefix, "bin")
        pathlist = path.split(os.pathsep)
        if pybin not in pathlist:
            pathLine = "PATH={0}{1}{2}\n".format(pybin, os.pathsep, path)
        else:
            pathLine = "PATH={0}\n".format(path)
    wrapper = ('''#!/bin/sh\n'''
               '''\n'''
               '''{0}'''
               '''{1}'''
               '''exec "{2}" "{3}/{4}.py" "$@"\n'''
               .format(pathLine, dyldLine, starter, pydir, "eric6"))
    copyToFile(wname, wrapper)
    os.chmod(wname, 0o755)
    
    shutilCopy(os.path.join(sourceDir, "pixmaps", "eric_2.icns"),
               os.path.join(dirs["icns"], "eric.icns"))
    
    copyToFile(
        os.path.join(dirs["contents"], "Info.plist"),
        '''<?xml version="1.0" encoding="UTF-8"?>\n'''
        '''<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"\n'''
        '''          "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'''
        '''<plist version="1.0">\n'''
        '''<dict>\n'''
        '''    <key>CFBundleExecutable</key>\n'''
        '''    <string>eric6</string>\n'''
        '''    <key>CFBundleIconFile</key>\n'''
        '''    <string>eric.icns</string>\n'''
        '''    <key>CFBundleInfoDictionaryVersion</key>\n'''
        '''    <string>1.0</string>\n'''
        '''    <key>CFBundleName</key>\n'''
        '''    <string>{0}</string>\n'''
        '''    <key>CFBundleDisplayName</key>\n'''
        '''    <string>{0}</string>\n'''
        '''    <key>CFBundlePackageType</key>\n'''
        '''    <string>APPL</string>\n'''
        '''    <key>CFBundleSignature</key>\n'''
        '''    <string>????</string>\n'''
        '''    <key>CFBundleVersion</key>\n'''
        '''    <string>1.0</string>\n'''
        '''    <key>CFBundleIdentifier</key>\n'''
        '''    <string>org.python-projects.eric-ide</string>\n'''
        '''</dict>\n'''
        '''</plist>\n'''.format(macAppBundleName.replace(".app", "")))


def createInstallConfig():
    """
    Create the installation config dictionary.
    """
    global modDir, platBinDir, cfg, apisDir, installApis
        
    ericdir = os.path.join(modDir, "eric6")
    cfg = {
        'ericDir': ericdir,
        'ericPixDir': os.path.join(ericdir, "pixmaps"),
        'ericIconDir': os.path.join(ericdir, "icons"),
        'ericDTDDir': os.path.join(ericdir, "DTDs"),
        'ericCSSDir': os.path.join(ericdir, "CSSs"),
        'ericStylesDir': os.path.join(ericdir, "Styles"),
        'ericDocDir': os.path.join(ericdir, "Documentation"),
        'ericExamplesDir': os.path.join(ericdir, "Examples"),
        'ericTranslationsDir': os.path.join(ericdir, "i18n"),
        'ericTemplatesDir': os.path.join(ericdir, "DesignerTemplates"),
        'ericCodeTemplatesDir': os.path.join(ericdir, 'CodeTemplates'),
        'ericOthersDir': ericdir,
        'bindir': platBinDir,
        'mdir': modDir,
    }
    if installApis:
        if apisDir:
            cfg['apidir'] = apisDir
        else:
            cfg['apidir'] = os.path.join(ericdir, "api")
    else:
        cfg['apidir'] = ""
configLength = 15
    

def createConfig():
    """
    Create a config file with the respective config entries.
    """
    global cfg, sourceDir, macAppBundlePath
    
    apis = []
    if installApis:
        for progLanguage in progLanguages:
            for apiName in glob.glob(
                    os.path.join(sourceDir, "APIs", progLanguage, "*.api")):
                apis.append(os.path.basename(apiName))
            if progLanguage == "Python":
                # treat Python3 API files the same as Python API files
                for apiName in glob.glob(
                        os.path.join(sourceDir, "APIs", "Python3", "*.api")):
                    apis.append(os.path.basename(apiName))
    
    fn = 'eric6config.py'
    config = (
        """# -*- coding: utf-8 -*-\n"""
        """#\n"""
        """# This module contains the configuration of the individual eric6"""
        """ installation\n"""
        """#\n"""
        """\n"""
        """_pkg_config = {{\n"""
        """    'ericDir': r'{0}',\n"""
        """    'ericPixDir': r'{1}',\n"""
        """    'ericIconDir': r'{2}',\n"""
        """    'ericDTDDir': r'{3}',\n"""
        """    'ericCSSDir': r'{4}',\n"""
        """    'ericStylesDir': r'{5}',\n"""
        """    'ericDocDir': r'{6}',\n"""
        """    'ericExamplesDir': r'{7}',\n"""
        """    'ericTranslationsDir': r'{8}',\n"""
        """    'ericTemplatesDir': r'{9}',\n"""
        """    'ericCodeTemplatesDir': r'{10}',\n"""
        """    'ericOthersDir': r'{11}',\n"""
        """    'bindir': r'{12}',\n"""
        """    'mdir': r'{13}',\n"""
        """    'apidir': r'{14}',\n"""
        """    'apis': {15},\n"""
        """    'macAppBundlePath': r'{16}',\n"""
        """    'macAppBundleName': r'{17}',\n"""
        """}}\n"""
        """\n"""
        """def getConfig(name):\n"""
        """    '''\n"""
        """    Module function to get a configuration value.\n"""
        """\n"""
        """    @param name name of the configuration value (string)\n"""
        """    '''\n"""
        """    try:\n"""
        """        return _pkg_config[name]\n"""
        """    except KeyError:\n"""
        """        pass\n"""
        """\n"""
        """    raise AttributeError('"{{0}}" is not a valid configuration"""
        """ value'.format(name))\n"""
    ).format(
        cfg['ericDir'], cfg['ericPixDir'], cfg['ericIconDir'],
        cfg['ericDTDDir'], cfg['ericCSSDir'],
        cfg['ericStylesDir'], cfg['ericDocDir'],
        cfg['ericExamplesDir'], cfg['ericTranslationsDir'],
        cfg['ericTemplatesDir'],
        cfg['ericCodeTemplatesDir'], cfg['ericOthersDir'],
        cfg['bindir'], cfg['mdir'],
        cfg['apidir'], apis,
        macAppBundlePath, macAppBundleName,
    )
    copyToFile(fn, config)


def doDependancyChecks():
    """
    Perform some dependency checks.
    """
    print('Checking dependencies')
    
    # perform dependency checks
    print("Python Version: {0:d}.{1:d}.{2:d}".format(*sys.version_info[:3]))
    if sys.version_info < (2, 7, 0):
        print('Sorry, you must have Python 2.7.0 or higher or '
              'Python 3.3.0 or higher.')
        exit(5)
    elif sys.version_info < (3, 3, 0) and sys.version_info[0] == 3:
        print('Sorry, you must have Python 3.3.0 or higher.')
        exit(5)
    if sys.version_info > (3, 9, 9):
        print('Sorry, eric6 requires Python 3 or Python 2 for running.')
        exit(5)
    
    try:
        import xml.etree            # __IGNORE_WARNING__
    except ImportError as msg:
        print('Your Python installation is missing the XML module.')
        print('Please install it and try again.')
        exit(5)
    
    if pyqtVariant == "PyQt4":
        try:
            from PyQt4.QtCore import qVersion
        except ImportError as msg:
            print('Sorry, please install PyQt4.')
            print('Error: {0}'.format(msg))
            exit(1)
        print("Found PyQt4")
    else:
        try:
            from PyQt5.QtCore import qVersion
        except ImportError as msg:
            print('Sorry, please install PyQt5.')
            print('Error: {0}'.format(msg))
            exit(1)
        print("Found PyQt5")
    
    try:
        if pyqtVariant == "PyQt4":
            from PyQt4 import Qsci      # __IGNORE_WARNING__
        else:
            from PyQt5 import Qsci      # __IGNORE_WARNING__
    except ImportError as msg:
        print("Sorry, please install QScintilla2 and")
        print("its PyQt5/PyQt4 wrapper.")
        print('Error: {0}'.format(msg))
        exit(1)
    print("Found QScintilla2")
    
    if pyqtVariant == "PyQt4":
        impModulesList = [
            "PyQt4.QtGui", "PyQt4.QtNetwork", "PyQt4.QtSql",
            "PyQt4.QtSvg", "PyQt4.QtWebKit",
        ]
    else:
        impModulesList = [
            "PyQt5.QtGui", "PyQt5.QtNetwork", "PyQt5.QtPrintSupport",
            "PyQt5.QtSql", "PyQt5.QtSvg", "PyQt5.QtWebKit",
            "PyQt5.QtWebKitWidgets", "PyQt5.QtWidgets",
        ]
    modulesOK = True
    for impModule in impModulesList:
        name = impModule.split(".")[1]
        try:
            __import__(impModule)
            print("Found", name)
        except ImportError as msg:
            print('Sorry, please install {0}.'.format(name))
            print('Error: {0}'.format(msg))
            modulesOK = False
    if not modulesOK:
        exit(1)
    
    # determine the platform dependent black list
    if sys.platform.startswith("win"):
        PlatformBlackLists = PlatformsBlackLists["windows"]
    elif sys.platform.startswith("linux"):
        PlatformBlackLists = PlatformsBlackLists["linux"]
    else:
        PlatformBlackLists = PlatformsBlackLists["mac"]
    
    # check version of Qt
    qtMajor = int(qVersion().split('.')[0])
    qtMinor = int(qVersion().split('.')[1])
    print("Qt Version: {0}".format(qVersion().strip()))
    if qtMajor < 4 or \
        (qtMajor == 4 and qtMinor < 8) or \
            (qtMajor == 5 and qtMinor < 3):
        print('Sorry, you must have Qt version 4.8.0 or better or')
        print('5.3.0 or better.')
        exit(2)
    
    # check version of sip
    try:
        import sip
        sipVersion = sip.SIP_VERSION_STR
        print("sip Version:", sipVersion.strip())
        # always assume, that snapshots are new enough
        if "snapshot" not in sipVersion:
            while sipVersion.count('.') < 2:
                sipVersion += '.0'
            (maj, min, pat) = sipVersion.split('.')
            maj = int(maj)
            min = int(min)
            pat = int(pat)
            if maj < 4 or (maj == 4 and min < 14) or \
                    (maj == 4 and min == 14 and pat < 2):
                print('Sorry, you must have sip 4.14.2 or higher or'
                      ' a recent snapshot release.')
                exit(3)
            # check for blacklisted versions
            for vers in BlackLists["sip"] + PlatformBlackLists["sip"]:
                if vers == sipVersion:
                    print(
                        'Sorry, sip version {0} is not compatible with eric6.'
                        .format(vers))
                    print('Please install another version.')
                    exit(3)
    except (ImportError, AttributeError):
        pass
    
    # check version of PyQt
    if pyqtVariant == "PyQt4":
        from PyQt4.QtCore import PYQT_VERSION_STR
    else:
        from PyQt5.QtCore import PYQT_VERSION_STR
    pyqtVersion = PYQT_VERSION_STR
    print("PyQt Version:", pyqtVersion.strip())
    # always assume, that snapshots are new enough
    if "snapshot" not in pyqtVersion:
        while pyqtVersion.count('.') < 2:
            pyqtVersion += '.0'
        (maj, min, pat) = pyqtVersion.split('.')
        maj = int(maj)
        min = int(min)
        pat = int(pat)
        if maj < 4 or \
            (maj == 4 and min < 10) or \
                (maj == 5 and min < 3):
            print('Sorry, you must have PyQt 4.10.0 or better or')
            print('PyQt 5.3.0 or better or'
                  ' a recent snapshot release.')
            exit(4)
        # check for blacklisted versions
        for vers in BlackLists[pyqtVariant] + PlatformBlackLists[pyqtVariant]:
            if vers == pyqtVersion:
                print('Sorry, PyQt version {0} is not compatible with eric6.'
                      .format(vers))
                print('Please install another version.')
                exit(4)
    
    # check version of QScintilla
    if pyqtVariant == "PyQt4":
        from PyQt4.Qsci import QSCINTILLA_VERSION_STR
    else:
        from PyQt5.Qsci import QSCINTILLA_VERSION_STR
    scintillaVersion = QSCINTILLA_VERSION_STR
    print("QScintilla Version:", QSCINTILLA_VERSION_STR.strip())
    # always assume, that snapshots are new enough
    if "snapshot" not in scintillaVersion:
        while scintillaVersion.count('.') < 2:
            scintillaVersion += '.0'
        (maj, min, pat) = scintillaVersion.split('.')
        maj = int(maj)
        min = int(min)
        pat = int(pat)
        if maj < 2 or (maj == 2 and min < 8):
            print('Sorry, you must have QScintilla 2.8.0 or higher or'
                  ' a recent snapshot release.')
            exit(5)
        # check for blacklisted versions
        for vers in BlackLists["QScintilla2"] + \
                PlatformBlackLists["QScintilla2"]:
            if vers == scintillaVersion:
                print(
                    'Sorry, QScintilla2 version {0} is not compatible with'
                    ' eric6.'.format(vers))
                print('Please install another version.')
                exit(5)
    
    print("All dependencies ok.")
    print()


def __pyName(py_dir, py_file):
    """
    Local function to create the Python source file name for the compiled
    .ui file.
    
    @param py_dir suggested name of the directory (string)
    @param py_file suggested name for the compile source file (string)
    @return tuple of directory name (string) and source file name (string)
    """
    return py_dir, "Ui_{0}".format(py_file)


def compileUiFiles():
    """
    Compile the .ui files to Python sources.
    """
    global sourceDir
    if pyqtVariant == "PyQt4":
        from PyQt4.uic import compileUiDir
    else:
        from PyQt5.uic import compileUiDir
    compileUiDir(sourceDir, True, __pyName)


def prepareInfoFile(fileName):
    """
    Function to prepare an Info.py file when installing from source.
    
    @param fileName name of the Python file containing the info (string)
    """
    if not fileName:
        return
    
    try:
        os.rename(fileName, fileName + ".orig")
    except EnvironmentError:
        pass
    try:
        hgOut = subprocess.check_output(["hg", "identify", "-i"])
        if sys.version_info[0] == 3:
            hgOut = hgOut.decode()
    except (OSError, subprocess.CalledProcessError):
        hgOut = ""
    if hgOut:
        hgOut = hgOut.strip()
        if hgOut.endswith("+"):
            hgOut = hgOut[:-1]
        if sys.version_info[0] == 2:
            f = codecs.open(fileName + ".orig", "r", "utf-8")
        else:
            f = open(fileName + ".orig", "r", encoding="utf-8")
        text = f.read()
        f.close()
        text = text.replace("@@REVISION@@", hgOut)\
            .replace("@@VERSION@@", "rev_" + hgOut)
        copyToFile(fileName, text)
    else:
        shutil.copy(fileName + ".orig", fileName)


def main(argv):
    """
    The main function of the script.

    @param argv the list of command line arguments.
    """
    import getopt

    # Parse the command line.
    global progName, modDir, doCleanup, doCompile, distDir, cfg, apisDir
    global sourceDir, configName, includePythonVariant
    global macAppBundlePath, macAppBundleName, macPythonExe
    global pyqtVariant, pyqtOverride, installApis
    
    if sys.version_info < (2, 7, 0) or sys.version_info > (3, 9, 9):
        print('Sorry, eric6 requires at least Python 2.7 or '
              'Python 3 for running.')
        exit(5)
    
    progName = os.path.basename(argv[0])
    
    if os.path.dirname(argv[0]):
        os.chdir(os.path.dirname(argv[0]))
    
    determinePyQtVariant()
    initGlobals()

    try:
        if sys.platform.startswith("win"):
            optlist, args = getopt.getopt(
                argv[1:], "chxyza:b:d:f:", ["help", "pyqt=", "noapis"])
        elif sys.platform == "darwin":
            optlist, args = getopt.getopt(
                argv[1:], "chxyza:b:d:f:i:m:n:p:", ["help", "pyqt=", "noapis"])
        else:
            optlist, args = getopt.getopt(
                argv[1:], "chxyza:b:d:f:i:", ["help", "pyqt=", "noapis"])
    except getopt.GetoptError as err:
        print(err)
        usage()

    global platBinDir
    
    depChecks = True

    for opt, arg in optlist:
        if opt in ["-h", "--help"]:
            usage(0)
        elif opt == "-a":
            apisDir = arg
        elif opt == "-b":
            platBinDir = arg
        elif opt == "-d":
            modDir = arg
        elif opt == "-i":
            distDir = os.path.normpath(arg)
        elif opt == "-x":
            depChecks = False
        elif opt == "-c":
            doCleanup = False
        elif opt == "-z":
            doCompile = False
        elif opt == "-y":
            includePythonVariant = True
        elif opt == "-f":
            try:
                exec(compile(open(arg).read(), arg, 'exec'), globals())
                if len(cfg) != configLength:
                    print("The configuration dictionary in '{0}' is incorrect."
                          " Aborting".format(arg))
                    exit(6)
            except:
                cfg = {}
        elif opt == "-m":
            macAppBundleName = arg
        elif opt == "-n":
            macAppBundlePath = arg
        elif opt == "-p":
            macPythonExe = arg
        elif opt == "--pyqt":
            if arg not in ["4", "5"]:
                print("Invalid PyQt version given; should be 4 or 5. Aborting")
                exit(6)
            pyqtVariant = "PyQt{0}".format(arg)
            pyqtOverride = True
        elif "--noapis":
            installApis = False
    
    infoName = ""
    installFromSource = not os.path.isdir(sourceDir)
    if installFromSource:
        sourceDir = os.path.dirname(__file__) or "."
        configName = os.path.join(sourceDir, "eric6config.py")
        if os.path.exists(os.path.join(sourceDir, ".hg")):
            # we are installing from source with repo
            infoName = os.path.join(sourceDir, "UI", "Info.py")
            prepareInfoFile(infoName)
    
    if len(cfg) == 0:
        createInstallConfig()
    
    if depChecks:
        doDependancyChecks()
    
    # get rid of development config file, if it exists
    try:
        if installFromSource:
            os.rename(configName, configName + ".orig")
            configNameC = configName + 'c'
            if os.path.exists(configNameC):
                os.remove(configNameC)
        os.remove(configName)
    except EnvironmentError:
        pass
    
    # cleanup source if installing from source
    if installFromSource:
        print("Cleaning up source ...")
        cleanupSource(sourceDir)
        print()
    
    # cleanup old installation
    print("Cleaning up old installation ...")
    try:
        if doCleanup:
            if distDir:
                shutil.rmtree(distDir, True)
            else:
                cleanUp()
    except (IOError, OSError) as msg:
        sys.stderr.write('Error: {0}\nTry install as root.\n'.format(msg))
        exit(7)

    # Create a config file and delete the default one
    print("\nCreating configuration file ...")
    createConfig()

    # Compile .ui files
    print("\nCompiling user interface files ...")
    # step 1: remove old Ui_*.py files
    for root, _, files in os.walk(sourceDir):
        for file in [f for f in files if fnmatch.fnmatch(f, 'Ui_*.py')]:
            os.remove(os.path.join(root, file))
    # step 2: compile the forms
    compileUiFiles()
    
    if doCompile:
        print("\nCompiling source files ...")
        # Hide compile errors (mainly because of Py2/Py3 differences)
        sys.stdout = io.StringIO()
        if distDir:
            compileall.compile_dir(
                sourceDir,
                ddir=os.path.join(distDir, modDir, cfg['ericDir']),
                rx=re.compile(r"DebugClients[\\/]Python[\\/]"),
                quiet=True)
            py_compile.compile(
                configName,
                dfile=os.path.join(distDir, modDir, "eric6config.py"))
        else:
            compileall.compile_dir(
                sourceDir,
                ddir=os.path.join(modDir, cfg['ericDir']),
                rx=re.compile(r"DebugClients[\\/]Python[\\/]"),
                quiet=True)
            py_compile.compile(configName,
                               dfile=os.path.join(modDir, "eric6config.py"))
        sys.stdout = sys.__stdout__
    print("\nInstalling eric6 ...")
    res = installEric()
    
    # do some cleanup
    try:
        if installFromSource:
            os.remove(configName)
            configNameC = configName + 'c'
            if os.path.exists(configNameC):
                os.remove(configNameC)
            os.rename(configName + ".orig", configName)
    except EnvironmentError:
        pass
    try:
        if installFromSource and infoName:
            os.remove(infoName)
            infoNameC = infoName + 'c'
            if os.path.exists(infoNameC):
                os.remove(infoNameC)
            os.rename(infoName + ".orig", infoName)
    except EnvironmentError:
        pass
    
    print("\nInstallation complete.")
    print()
    
    exit(res)
    
    
if __name__ == "__main__":
    try:
        main(sys.argv)
    except SystemExit:
        raise
    except:
        print("""An internal error occured.  Please report all the output"""
              """ of the program,\nincluding the following traceback, to"""
              """ eric-bugs@eric-ide.python-projects.org.\n""")
        raise
