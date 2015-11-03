# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an importer for Firefox bookmarks.
"""

from __future__ import unicode_literals

import os
import sqlite3

from PyQt5.QtCore import QCoreApplication, QDate, Qt, QUrl

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
    if id == "firefox":
        if Globals.isWindowsPlatform():
            standardDir = os.path.expandvars(
                "%APPDATA%\\Mozilla\\Firefox\\Profiles")
        elif Globals.isMacPlatform():
            standardDir = os.path.expanduser(
                "~/Library/Application Support/Firefox/Profiles")
        else:
            standardDir = os.path.expanduser("~/.mozilla/firefox")
        return (
            UI.PixmapCache.getPixmap("chrome.png"),
            "Mozilla Firefox",
            "places.sqlite",
            QCoreApplication.translate(
                "FirefoxImporter",
                """Mozilla Firefox stores its bookmarks in the"""
                """ <b>places.sqlite</b> SQLite database. This file is"""
                """ usually located in"""),
            QCoreApplication.translate(
                "FirefoxImporter",
                """Please choose the file to begin importing bookmarks."""),
            standardDir,
        )
    else:
        raise ValueError("Unsupported browser ID given ({0}).".format(id))


class FirefoxImporter(BookmarksImporter):
    """
    Class implementing the Chrome bookmarks importer.
    """
    def __init__(self, id="", parent=None):
        """
        Constructor
        
        @param id source ID (string)
        @param parent reference to the parent object (QObject)
        """
        super(FirefoxImporter, self).__init__(id, parent)
        
        self.__fileName = ""
        self.__db = None
    
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
            self._errorString = self.tr("File '{0}' does not exist.")\
                .format(self.__fileName)
            return False
        
        try:
            self.__db = sqlite3.connect(self.__fileName)
        except sqlite3.DatabaseError as err:
            self._error = True
            self._errorString = self.tr(
                "Unable to open database.\nReason: {0}").format(str(err))
            return False
        
        return True
    
    def importedBookmarks(self):
        """
        Public method to get the imported bookmarks.
        
        @return imported bookmarks (BookmarkNode)
        """
        from ..BookmarkNode import BookmarkNode
        importRootNode = BookmarkNode(BookmarkNode.Root)
        
        # step 1: build the hierarchy of bookmark folders
        folders = {}
        
        try:
            cursor = self.__db.cursor()
            cursor.execute(
                "SELECT id, parent, title FROM moz_bookmarks "
                "WHERE type = 2 and title !=''")
            for row in cursor:
                id_ = row[0]
                parent = row[1]
                title = row[2]
                if parent in folders:
                    folder = BookmarkNode(BookmarkNode.Folder, folders[parent])
                else:
                    folder = BookmarkNode(BookmarkNode.Folder, importRootNode)
                folder.title = title.replace("&", "&&")
                folders[id_] = folder
        except sqlite3.DatabaseError as err:
            self._error = True
            self._errorString = self.tr(
                "Unable to open database.\nReason: {0}").format(str(err))
            return None
        
        try:
            cursor = self.__db.cursor()
            cursor.execute(
                "SELECT parent, title, fk, position FROM moz_bookmarks"
                " WHERE type = 1 and title != '' ORDER BY position")
            for row in cursor:
                parent = row[0]
                title = row[1]
                placesId = row[2]
                
                cursor2 = self.__db.cursor()
                cursor2.execute(
                    "SELECT url FROM moz_places WHERE id = {0}"
                    .format(placesId))
                row2 = cursor2.fetchone()
                if row2:
                    url = QUrl(row2[0])
                    if not title or url.isEmpty() or \
                            url.scheme() in ["place", "about"]:
                        continue
                    
                    if parent in folders:
                        bookmark = BookmarkNode(BookmarkNode.Bookmark,
                                                folders[parent])
                    else:
                        bookmark = BookmarkNode(BookmarkNode.Bookmark,
                                                importRootNode)
                    bookmark.url = url.toString()
                    bookmark.title = title.replace("&", "&&")
        except sqlite3.DatabaseError as err:
            self._error = True
            self._errorString = self.tr(
                "Unable to open database.\nReason: {0}").format(str(err))
            return None
        
        importRootNode.setType(BookmarkNode.Folder)
        if self._id == "firefox":
            importRootNode.title = self.tr("Mozilla Firefox Import")
        else:
            importRootNode.title = self.tr("Imported {0}")\
                .format(QDate.currentDate().toString(Qt.SystemLocaleShortDate))
        return importRootNode
