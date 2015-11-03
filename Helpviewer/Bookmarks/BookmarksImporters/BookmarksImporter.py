# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a base class for the bookmarks importers.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject


class BookmarksImporter(QObject):
    """
    Class implementing the base class for the bookmarks importers.
    """
    def __init__(self, id="", parent=None):
        """
        Constructor
        
        @param id source ID (string)
        @param parent reference to the parent object (QObject)
        """
        super(BookmarksImporter, self).__init__(parent)
        
        self._path = ""
        self._file = ""
        self._error = False
        self._errorString = ""
        self._id = id
    
    def setPath(self, path):
        """
        Public method to set the path of the bookmarks file or directory.
        
        @param path bookmarks file or directory (string)
        @exception NotImplementedError raised to indicate this method must
            be implemented by a subclass
        """
        raise NotImplementedError
    
    def open(self):
        """
        Public method to open the bookmarks file.
        
        It must return a flag indicating success (boolean).
        
        @exception NotImplementedError raised to indicate this method must
            be implemented by a subclass
        """
        raise NotImplementedError
    
    def importedBookmarks(self):
        """
        Public method to get the imported bookmarks.
        
        It must return the imported bookmarks (BookmarkNode).
        
        @exception NotImplementedError raised to indicate this method must
            be implemented by a subclass
        """
        raise NotImplementedError
    
    def error(self):
        """
        Public method to check for an error.
        
        @return flag indicating an error (boolean)
        """
        return self._error
    
    def errorString(self):
        """
        Public method to get the error description.
        
        @return error description (string)
        """
        return self._errorString
