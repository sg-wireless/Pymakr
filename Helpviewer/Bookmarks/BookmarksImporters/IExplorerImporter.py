# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an importer for Internet Explorer bookmarks.
"""

from __future__ import unicode_literals

import os

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
    if id == "ie":
        if Globals.isWindowsPlatform():
            standardDir = os.path.expandvars(
                "%USERPROFILE%\\Favorites")
        else:
            standardDir = ""
        return (
            UI.PixmapCache.getPixmap("internet_explorer.png"),
            "Internet Explorer",
            "",
            QCoreApplication.translate(
                "IExplorerImporter",
                """Internet Explorer stores its bookmarks in the"""
                """ <b>Favorites</b> folder This folder is usually"""
                """ located in"""),
            QCoreApplication.translate(
                "IExplorerImporter",
                """Please choose the folder to begin importing bookmarks."""),
            standardDir,
        )
    else:
        raise ValueError("Unsupported browser ID given ({0}).".format(id))


class IExplorerImporter(BookmarksImporter):
    """
    Class implementing the Chrome bookmarks importer.
    """
    def __init__(self, id="", parent=None):
        """
        Constructor
        
        @param id source ID (string)
        @param parent reference to the parent object (QObject)
        """
        super(IExplorerImporter, self).__init__(id, parent)
        
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
            self._errorString = self.tr("Folder '{0}' does not exist.")\
                .format(self.__fileName)
            return False
        if not os.path.isdir(self.__fileName):
            self._error = True
            self._errorString = self.tr("'{0}' is not a folder.")\
                .format(self.__fileName)
        return True
    
    def importedBookmarks(self):
        """
        Public method to get the imported bookmarks.
        
        @return imported bookmarks (BookmarkNode)
        """
        from ..BookmarkNode import BookmarkNode
        
        folders = {}
        
        importRootNode = BookmarkNode(BookmarkNode.Folder)
        folders[self.__fileName] = importRootNode
        
        for dir, subdirs, files in os.walk(self.__fileName):
            for subdir in subdirs:
                path = os.path.join(dir, subdir)
                if dir in folders:
                    folder = BookmarkNode(BookmarkNode.Folder, folders[dir])
                else:
                    folder = BookmarkNode(BookmarkNode.Folder, importRootNode)
                folder.title = subdir.replace("&", "&&")
                folders[path] = folder
            
            for file in files:
                name, ext = os.path.splitext(file)
                if ext.lower() == ".url":
                    path = os.path.join(dir, file)
                    try:
                        f = open(path, "r")
                        contents = f.read()
                        f.close()
                    except IOError:
                        continue
                    url = ""
                    for line in contents.splitlines():
                        if line.startswith("URL="):
                            url = line.replace("URL=", "")
                            break
                    if url:
                        if dir in folders:
                            bookmark = BookmarkNode(BookmarkNode.Bookmark,
                                                    folders[dir])
                        else:
                            bookmark = BookmarkNode(BookmarkNode.Bookmark,
                                                    importRootNode)
                        bookmark.url = url
                        bookmark.title = name.replace("&", "&&")
        
        if self._id == "ie":
            importRootNode.title = self.tr("Internet Explorer Import")
        else:
            importRootNode.title = self.tr("Imported {0}")\
                .format(QDate.currentDate().toString(Qt.SystemLocaleShortDate))
        return importRootNode
