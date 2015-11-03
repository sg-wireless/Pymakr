# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an importer for XBEL files.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QCoreApplication, QXmlStreamReader, QDate, Qt

from .BookmarksImporter import BookmarksImporter

import UI.PixmapCache


def getImporterInfo(id):
    """
    Module function to get information for the given XBEL source id.
    
    @param id id of the browser ("chrome" or "chromium")
    @return tuple with an icon (QPixmap), readable name (string), name of
        the default bookmarks file (string), an info text (string),
        a prompt (string) and the default directory of the bookmarks file
        (string)
    @exception ValueError raised to indicate an invalid browser ID
    """
    if id == "e5browser":
        from ..BookmarksManager import BookmarksManager
        bookmarksFile = BookmarksManager.getFileName()
        return (
            UI.PixmapCache.getPixmap("ericWeb48.png"),
            "eric6 Web Browser",
            os.path.basename(bookmarksFile),
            QCoreApplication.translate(
                "XbelImporter",
                """eric6 Web Browser stores its bookmarks in the"""
                """ <b>{0}</b> XML file. This file is usually located in"""
            ).format(os.path.basename(bookmarksFile)),
            QCoreApplication.translate(
                "XbelImporter",
                """Please choose the file to begin importing bookmarks."""),
            os.path.dirname(bookmarksFile),
        )
    elif id == "konqueror":
        if os.path.exists(os.path.expanduser("~/.kde4")):
            standardDir = os.path.expanduser("~/.kde4/share/apps/konqueror")
        elif os.path.exists(os.path.expanduser("~/.kde")):
            standardDir = os.path.expanduser("~/.kde/share/apps/konqueror")
        else:
            standardDir = ""
        return (
            UI.PixmapCache.getPixmap("konqueror.png"),
            "Konqueror",
            "bookmarks.xml",
            QCoreApplication.translate(
                "XbelImporter",
                """Konqueror stores its bookmarks in the"""
                """ <b>bookmarks.xml</b> XML file. This file is usually"""
                """ located in"""),
            QCoreApplication.translate(
                "XbelImporter",
                """Please choose the file to begin importing bookmarks."""),
            standardDir,
        )
    elif id == "xbel":
        return (
            UI.PixmapCache.getPixmap("xbel.png"),
            "XBEL Bookmarks",
            QCoreApplication.translate(
                "XbelImporter", "XBEL Bookmarks") + " (*.xbel *.xml)",
            QCoreApplication.translate(
                "XbelImporter",
                """You can import bookmarks from any browser that supports"""
                """ XBEL exporting. This file has usually the extension"""
                """ .xbel or .xml."""),
            QCoreApplication.translate(
                "XbelImporter",
                """Please choose the file to begin importing bookmarks."""),
            "",
        )
    else:
        raise ValueError("Unsupported browser ID given ({0}).".format(id))


class XbelImporter(BookmarksImporter):
    """
    Class implementing the XBEL bookmarks importer.
    """
    def __init__(self, id="", parent=None):
        """
        Constructor
        
        @param id source ID (string)
        @param parent reference to the parent object (QObject)
        """
        super(XbelImporter, self).__init__(id, parent)
        
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
        from ..XbelReader import XbelReader
        
        reader = XbelReader()
        importRootNode = reader.read(self.__fileName)
        
        if reader.error() != QXmlStreamReader.NoError:
            self._error = True
            self._errorString = self.tr(
                """Error when importing bookmarks on line {0},"""
                """ column {1}:\n{2}""")\
                .format(reader.lineNumber(),
                        reader.columnNumber(),
                        reader.errorString())
            return None
        
        from ..BookmarkNode import BookmarkNode
        importRootNode.setType(BookmarkNode.Folder)
        if self._id == "e5browser":
            importRootNode.title = self.tr("eric6 Web Browser Import")
        elif self._id == "konqueror":
            importRootNode.title = self.tr("Konqueror Import")
        elif self._id == "xbel":
            importRootNode.title = self.tr("XBEL Import")
        else:
            importRootNode.title = self.tr("Imported {0}")\
                .format(QDate.currentDate().toString(Qt.SystemLocaleShortDate))
        return importRootNode
