# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module defining common data to be used by all modules.
"""

#
# Note: Do not import any eric stuff in here!!!!!!!
#

from __future__ import unicode_literals

import sys
import os

from PyQt5.QtCore import QDir, QLibraryInfo, QByteArray

# names of the various settings objects
settingsNameOrganization = "Eric6"
settingsNameGlobal = "eric6"
settingsNameRecent = "eric6recent"

# key names of the various recent entries
recentNameMultiProject = "MultiProjects"
recentNameProject = "Projects"
recentNameFiles = "Files"
recentNameHosts = "Hosts6"

configDir = None


def isWindowsPlatform():
    """
    Function to check, if this is a Windows platform.
    
    @return flag indicating Windows platform (boolean)
    """
    return sys.platform.startswith("win")


def isMacPlatform():
    """
    Function to check, if this is a Mac platform.
    
    @return flag indicating Mac platform (boolean)
    """
    return sys.platform == "darwin"


def isLinuxPlatform():
    """
    Function to check, if this is a Linux platform.
    
    @return flag indicating Linux platform (boolean)
    """
    return sys.platform.startswith("linux")


def checkBlacklistedVersions():
    """
    Module functions to check for blacklisted versions of the prerequisites.
    
    @return flag indicating good versions were found (boolean)
    """
    from install import BlackLists, PlatformsBlackLists
    
    # determine the platform dependent black list
    if isWindowsPlatform():
        PlatformBlackLists = PlatformsBlackLists["windows"]
    elif isLinuxPlatform():
        PlatformBlackLists = PlatformsBlackLists["linux"]
    else:
        PlatformBlackLists = PlatformsBlackLists["mac"]
    
    # check version of sip
    try:
        import sipconfig
        sipVersion = sipconfig.Configuration().sip_version_str
        # always assume, that snapshots are good
        if "snapshot" not in sipVersion:
            # check for blacklisted versions
            for vers in BlackLists["sip"] + PlatformBlackLists["sip"]:
                if vers == sipVersion:
                    print(
                        'Sorry, sip version {0} is not compatible with eric6.'
                        .format(vers))
                    print('Please install another version.')
                    return False
    except ImportError:
        pass
    
    # check version of PyQt
    from PyQt5.QtCore import PYQT_VERSION_STR
    pyqtVersion = PYQT_VERSION_STR
    # always assume, that snapshots are good
    if "snapshot" not in pyqtVersion:
        # check for blacklisted versions
        pyqtVariant = "PyQt{0}".format(pyqtVersion[0])
        for vers in BlackLists[pyqtVariant] + PlatformBlackLists[pyqtVariant]:
            if vers == pyqtVersion:
                print('Sorry, PyQt version {0} is not compatible with eric6.'
                      .format(vers))
                print('Please install another version.')
                return False
    
    # check version of QScintilla
    from PyQt5.Qsci import QSCINTILLA_VERSION_STR
    scintillaVersion = QSCINTILLA_VERSION_STR
    # always assume, that snapshots are new enough
    if "snapshot" not in scintillaVersion:
        # check for blacklisted versions
        for vers in BlackLists["QScintilla2"] + \
                PlatformBlackLists["QScintilla2"]:
            if vers == scintillaVersion:
                print(
                    'Sorry, QScintilla2 version {0} is not compatible'
                    ' with eric6.'.format(vers))
                print('Please install another version.')
                return False
    
    return True


def getConfigDir():
    """
    Module function to get the name of the directory storing the config data.
    
    @return directory name of the config dir (string)
    """
    if configDir is not None and os.path.exists(configDir):
        hp = configDir
    else:
        if isWindowsPlatform():
            cdn = "_eric6"
        else:
            cdn = ".eric6"
            
        hp = QDir.homePath()
        dn = QDir(hp)
        dn.mkdir(cdn)
        hp += "/" + cdn
    return QDir.toNativeSeparators(hp)


def setConfigDir(d):
    """
    Module function to set the name of the directory storing the config data.
    
    @param d name of an existing directory (string)
    """
    global configDir
    configDir = os.path.expanduser(d)


def getPythonModulesDirectory():
    """
    Function to determine the path to Python's modules directory.
    
    @return path to the Python modules directory (string)
    """
    import distutils.sysconfig
    return distutils.sysconfig.get_python_lib(True)


def getPyQt5ModulesDirectory():
    """
    Function to determine the path to PyQt5's (or PyQt4's) modules directory.
    
    @return path to the PyQt5/PyQt4 modules directory (string)
    """
    import distutils.sysconfig
    for pyqt in ["PyQt5", "PyQt4"]:
        pyqtPath = os.path.join(distutils.sysconfig.get_python_lib(True), pyqt)
        if os.path.exists(pyqtPath):
            return pyqtPath
    
    return ""
    

def getQtBinariesPath():
    """
    Module function to get the path of the Qt binaries.
    
    @return path of the Qt binaries (string)
    """
    path = ""
    if isWindowsPlatform():
        # check for PyQt5 installer first (designer is test object)
        modDir = getPyQt5ModulesDirectory()
        if os.path.exists(os.path.join(modDir, "bin", "designer.exe")):
            path = os.path.join(modDir, "bin")
        elif os.path.exists(os.path.join(modDir, "designer.exe")):
            path = modDir
    
    if not path:
        path = QLibraryInfo.location(QLibraryInfo.BinariesPath)
        if not os.path.exists(path):
            path = ""
    
    return QDir.toNativeSeparators(path)


###############################################################################
## functions for searching a Python2/3 interpreter
###############################################################################


def findPythonInterpreters(pyVersion):
    """
    Module function for searching a Python interpreter.
    
    @param pyVersion major Python version
    @return list of interpreters found (list of strings)
    """
    if pyVersion == 2:
        winPathList = ["C:\\Python25", "C:\\Python26",
                       "C:\\Python27", "C:\\Python28"]
        posixVersionsList = ["2.5", "2.6", "2.7", "2.8"]
    else:
        winPathList = ["C:\\Python3{0}".format(x) for x in range(5)]
        posixVersionsList = ["3.{0}".format(x) for x in range(5)]
    posixPathList = ["/usr/bin", "/usr/local/bin"]
    
    interpreters = []
    if isWindowsPlatform():
        # search the interpreters on Windows platforms
        for path in winPathList:
            exeList = [
                "python.exe",
                "python{0}.{1}.exe".format(path[-2], path[-1]),
            ]
            for exe in exeList:
                interpreter = os.path.join(path, exe)
                if os.path.isfile(interpreter):
                    interpreters.append(interpreter)
    else:
        # search interpreters on Posix and Mac platforms
        for path in posixPathList:
            for version in posixVersionsList:
                interpreter = os.path.join(path, "python{0}".format(version))
                if os.path.isfile(interpreter):
                    interpreters.append(interpreter)
    
    return interpreters


###############################################################################
## functions for converting QSetting return types to valid types
###############################################################################


def toBool(value):
    """
    Module function to convert a value to bool.
    
    @param value value to be converted
    @return converted data
    """
    if value in ["true", "1", "True"]:
        return True
    elif value in ["false", "0", "False"]:
        return False
    else:
        return bool(value)


def toList(value):
    """
    Module function to convert a value to a list.
    
    @param value value to be converted
    @return converted data
    """
    if value is None:
        return []
    elif not isinstance(value, list):
        return [value]
    else:
        return value


def toByteArray(value):
    """
    Module function to convert a value to a byte array.
    
    @param value value to be converted
    @return converted data
    """
    if value is None:
        return QByteArray()
    else:
        return value


def toDict(value):
    """
    Module function to convert a value to a dictionary.
    
    @param value value to be converted
    @return converted data
    """
    if value is None:
        return {}
    else:
        return value
