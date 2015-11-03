# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an importer for Opera bookmarks.
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
    if id == "opera":
        if Globals.isWindowsPlatform():
            standardDir = os.path.expandvars("%APPDATA%\\Opera\\Opera")
        elif Globals.isMacPlatform():
            standardDir = os.path.expanduser(
                "~/Library/Opera")
        else:
            standardDir = os.path.expanduser("~/.opera")
        return (
            UI.PixmapCache.getPixmap("opera.png"),
            "Opera",
            "bookmarks.adr",
            QCoreApplication.translate(
                "OperaImporter",
                """Opera stores its bookmarks in the <b>bookmarks.adr</b> """
                """text file. This file is usually located in"""),
            QCoreApplication.translate(
                "OperaImporter",
                """Please choose the file to begin importing bookmarks."""),
            standardDir,
        )
    else:
        raise ValueError("Unsupported browser ID given ({0}).".format(id))


class OperaImporter(BookmarksImporter):
    """
    Class implementing the Opera bookmarks importer.
    """
    def __init__(self, id="", parent=None):
        """
        Constructor
        
        @param id source ID (string)
        @param parent reference to the parent object (QObject)
        """
        super(OperaImporter, self).__init__(id, parent)
        
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
            self._errorString = self.tr("File '{0}' does not exist.")\
                .format(self.__fileName)
            return False
        return True
    
    def importedBookmarks(self):
        """
        Public method to get the imported bookmarks.
        
        @return imported bookmarks (BookmarkNode)
        """
        try:
            f = open(self.__fileName, "r", encoding="utf-8")
            contents = f.read()
            f.close()
        except IOError as err:
            self._error = True
            self._errorString = self.tr(
                "File '{0}' cannot be read.\nReason: {1}")\
                .format(self.__fileName, str(err))
            return None
        
        folderStack = []
        
        from ..BookmarkNode import BookmarkNode
        importRootNode = BookmarkNode(BookmarkNode.Folder)
        folderStack.append(importRootNode)
        
        for line in contents.splitlines():
            line = line.strip()
            if line == "#FOLDER":
                node = BookmarkNode(BookmarkNode.Folder, folderStack[-1])
                folderStack.append(node)
            elif line == "#URL":
                node = BookmarkNode(BookmarkNode.Bookmark, folderStack[-1])
            elif line == "-":
                folderStack.pop()
            elif line.startswith("NAME="):
                node.title = line.replace("NAME=", "").replace("&", "&&")
            elif line.startswith("URL="):
                node.url = line.replace("URL=", "")
        
        if self._id == "opera":
            importRootNode.title = self.tr("Opera Import")
        else:
            importRootNode.title = self.tr("Imported {0}")\
                .format(QDate.currentDate().toString(Qt.SystemLocaleShortDate))
        return importRootNode
