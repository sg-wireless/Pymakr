# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an importer for Chrome bookmarks.
"""

from __future__ import unicode_literals

import os
import json

from PyQt5.QtCore import QCoreApplication, QDate, Qt

from .BookmarksImporter import BookmarksImporter

import UI.PixmapCache
import Globals


def getImporterInfo(id):
    """
    Module function to get information for the given source id.
    
    @param id id of the browser ("chrome" or "chromium")
    @return tuple with an icon (QPixmap), readable name (string), name of
        the default bookmarks file (string), an info text (string),
        a prompt (string) and the default directory of the bookmarks file
        (string)
    @exception ValueError raised to indicate an invalid browser ID
    """
    if id == "chrome":
        if Globals.isWindowsPlatform():
            standardDir = os.path.expandvars(
                "%USERPROFILE%\\AppData\\Local\\Google\\Chrome\\"
                "User Data\\Default")
        elif Globals.isMacPlatform():
            standardDir = os.path.expanduser(
                "~/Library/Application Support/Google/Chrome/Default")
        else:
            standardDir = os.path.expanduser("~/.config/google-chrome/Default")
        return (
            UI.PixmapCache.getPixmap("chrome.png"),
            "Google Chrome",
            "Bookmarks",
            QCoreApplication.translate(
                "ChromeImporter",
                """Google Chrome stores its bookmarks in the"""
                """ <b>Bookmarks</b> text file. This file is usually"""
                """ located in"""),
            QCoreApplication.translate(
                "ChromeImporter",
                """Please choose the file to begin importing bookmarks."""),
            standardDir,
        )
    elif id == "chromium":
        if Globals.isWindowsPlatform():
            standardDir = os.path.expandvars(
                "%USERPROFILE%\\AppData\\Local\\Google\\Chrome\\"
                "User Data\\Default")
        else:
            standardDir = os.path.expanduser("~/.config/chromium/Default")
        return (
            UI.PixmapCache.getPixmap("chromium.png"),
            "Chromium",
            "Bookmarks",
            QCoreApplication.translate(
                "ChromeImporter",
                """Chromium stores its bookmarks in the <b>Bookmarks</b>"""
                """ text file. This file is usually located in"""),
            QCoreApplication.translate(
                "ChromeImporter",
                """Please choose the file to begin importing bookmarks."""),
            standardDir,
        )
    else:
        raise ValueError("Unsupported browser ID given ({0}).".format(id))


class ChromeImporter(BookmarksImporter):
    """
    Class implementing the Chrome bookmarks importer.
    """
    def __init__(self, id="", parent=None):
        """
        Constructor
        
        @param id source ID (string)
        @param parent reference to the parent object (QObject)
        """
        super(ChromeImporter, self).__init__(id, parent)
        
        self.__fileName = ""
    
    def setPath(self, path):
        """
        Public method to set the path of the bookmarks file or directory.
        
        @param path bookmarks file or directory (string)
        """
        self.__fileName = path
    
    def open(self):
        """
        Public method to open the bookmarks file.
        
        @return flag indicating success (boolean)
        """
        if not os.path.exists(self.__fileName):
            self._error = True
            self._errorString = self.tr(
                "File '{0}' does not exist.").format(self.__fileName)
            return False
        return True
    
    def importedBookmarks(self):
        """
        Public method to get the imported bookmarks.
        
        @return imported bookmarks (BookmarkNode)
        """
        try:
            f = open(self.__fileName, "r", encoding="utf-8")
            contents = json.load(f)
            f.close()
        except IOError as err:
            self._error = True
            self._errorString = self.tr(
                "File '{0}' cannot be read.\nReason: {1}")\
                .format(self.__fileName, str(err))
            return None
        
        from ..BookmarkNode import BookmarkNode
        importRootNode = BookmarkNode(BookmarkNode.Folder)
        if contents["version"] == 1:
            self.__processRoots(contents["roots"], importRootNode)
        
        if self._id == "chrome":
            importRootNode.title = self.tr("Google Chrome Import")
        elif self._id == "chromium":
            importRootNode.title = self.tr("Chromium Import")
        else:
            importRootNode.title = self.tr("Imported {0}")\
                .format(QDate.currentDate().toString(Qt.SystemLocaleShortDate))
        return importRootNode
    
    def __processRoots(self, data, rootNode):
        """
        Private method to process the bookmark roots.
        
        @param data dictionary with the bookmarks data (dict)
        @param rootNode node to add the bookmarks to (BookmarkNode)
        """
        for node in data.values():
            if node["type"] == "folder":
                self.__generateFolderNode(node, rootNode)
            elif node["type"] == "url":
                self.__generateUrlNode(node, rootNode)
    
    def __generateFolderNode(self, data, rootNode):
        """
        Private method to process a bookmarks folder.
        
        @param data dictionary with the bookmarks data (dict)
        @param rootNode node to add the bookmarks to (BookmarkNode)
        """
        from ..BookmarkNode import BookmarkNode
        folder = BookmarkNode(BookmarkNode.Folder, rootNode)
        folder.title = data["name"].replace("&", "&&")
        for node in data["children"]:
            if node["type"] == "folder":
                self.__generateFolderNode(node, folder)
            elif node["type"] == "url":
                self.__generateUrlNode(node, folder)
    
    def __generateUrlNode(self, data, rootNode):
        """
        Private method to process a bookmarks node.
        
        @param data dictionary with the bookmarks data (dict)
        @param rootNode node to add the bookmarks to (BookmarkNode)
        """
        from ..BookmarkNode import BookmarkNode
        bookmark = BookmarkNode(BookmarkNode.Bookmark, rootNode)
        bookmark.url = data["url"]
        bookmark.title = data["name"].replace("&", "&&")
