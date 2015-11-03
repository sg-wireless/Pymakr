# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Package implementing bookmarks importers for various sources.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QCoreApplication

import UI.PixmapCache
import Globals


def getImporters():
    """
    Module function to get a list of supported importers.
    
    @return list of tuples with an icon (QIcon), readable name (string) and
        internal name (string)
    """
    importers = []
    importers.append(
        (UI.PixmapCache.getIcon("ericWeb48.png"), "eric6 Web Browser",
         "e5browser"))
    importers.append(
        (UI.PixmapCache.getIcon("firefox.png"), "Mozilla Firefox", "firefox"))
    importers.append(
        (UI.PixmapCache.getIcon("chrome.png"), "Google Chrome", "chrome"))
    if Globals.isLinuxPlatform():
        importers.append(
            (UI.PixmapCache.getIcon("chromium.png"), "Chromium", "chromium"))
        importers.append(
            (UI.PixmapCache.getIcon("konqueror.png"), "Konqueror",
             "konqueror"))
    importers.append(
        (UI.PixmapCache.getIcon("opera.png"), "Opera", "opera"))
    importers.append(
        (UI.PixmapCache.getIcon("safari.png"), "Apple Safari", "safari"))
    if Globals.isWindowsPlatform():
        importers.append(
            (UI.PixmapCache.getIcon("internet_explorer.png"),
             "Internet Explorer", "ie"))
    importers.append(
        (UI.PixmapCache.getIcon("xbel.png"),
         QCoreApplication.translate("BookmarksImporters", "XBEL File"),
         "xbel"))
    importers.append(
        (UI.PixmapCache.getIcon("html.png"),
         QCoreApplication.translate("BookmarksImporters", "HTML File"),
         "html"))
    return importers


def getImporterInfo(id):
    """
    Module function to get information for the given source id.
    
    @param id source id to get info for (string)
    @return tuple with an icon (QPixmap), readable name (string), name of
        the default bookmarks file (string), an info text (string),
        a prompt (string) and the default directory of the bookmarks
        file (string)
    @exception ValueError raised to indicate an unsupported importer
    """
    if id in ["e5browser", "xbel", "konqueror"]:
        from . import XbelImporter
        return XbelImporter.getImporterInfo(id)
    elif id == "html":
        from . import HtmlImporter
        return HtmlImporter.getImporterInfo(id)
    elif id in ["chrome", "chromium"]:
        from . import ChromeImporter
        return ChromeImporter.getImporterInfo(id)
    elif id == "opera":
        from . import OperaImporter
        return OperaImporter.getImporterInfo(id)
    elif id == "firefox":
        from . import FirefoxImporter
        return FirefoxImporter.getImporterInfo(id)
    elif id == "ie":
        from . import IExplorerImporter
        return IExplorerImporter.getImporterInfo(id)
    elif id == "safari":
        from . import SafariImporter
        return SafariImporter.getImporterInfo(id)
    else:
        raise ValueError("Invalid importer ID given ({0}).".format(id))


def getImporter(id, parent=None):
    """
    Module function to get an importer for the given source id.
    
    @param id source id to get an importer for (string)
    @param parent reference to the parent object (QObject)
    @return bookmarks importer (BookmarksImporter)
    @exception ValueError raised to indicate an unsupported importer
    """
    if id in ["e5browser", "xbel", "konqueror"]:
        from . import XbelImporter
        return XbelImporter.XbelImporter(id, parent)
    elif id == "html":
        from . import HtmlImporter
        return HtmlImporter.HtmlImporter(id, parent)
    elif id in ["chrome", "chromium"]:
        from . import ChromeImporter
        return ChromeImporter.ChromeImporter(id, parent)
    elif id == "opera":
        from . import OperaImporter
        return OperaImporter.OperaImporter(id, parent)
    elif id == "firefox":
        from . import FirefoxImporter
        return FirefoxImporter.FirefoxImporter(id, parent)
    elif id == "ie":
        from . import IExplorerImporter
        return IExplorerImporter.IExplorerImporter(id, parent)
    elif id == "safari":
        from . import SafariImporter
        return SafariImporter.SafariImporter(id, parent)
    else:
        raise ValueError("No importer for ID {0}.".format(id))
