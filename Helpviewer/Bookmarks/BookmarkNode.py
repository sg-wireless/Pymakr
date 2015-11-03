# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the bookmark node.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QDateTime


class BookmarkNode(object):
    """
    Class implementing the bookmark node type.
    """
    # possible bookmark node types
    Root = 0
    Folder = 1
    Bookmark = 2
    Separator = 3
    
    # possible timestamp types
    TsAdded = 0
    TsModified = 1
    TsVisited = 2
    
    def __init__(self, type_=Root, parent=None):
        """
        Constructor
        
        @param type_ type of the bookmark node (BookmarkNode.Type)
        @param parent reference to the parent node (BookmarkNode)
        """
        self.url = ""
        self.title = ""
        self.desc = ""
        self.expanded = False
        self.added = QDateTime()
        self.modified = QDateTime()
        self.visited = QDateTime()
        
        self._children = []
        self._parent = parent
        self._type = type_
        
        if parent is not None:
            parent.add(self)
    
    def type(self):
        """
        Public method to get the bookmark's type.
        
        @return bookmark type (BookmarkNode.Type)
        """
        return self._type
    
    def setType(self, type_):
        """
        Public method to set the bookmark's type.
        
        @param type_ type of the bookmark node (BookmarkNode.Type)
        """
        self._type = type_
    
    def children(self):
        """
        Public method to get the list of child nodes.
        
        @return list of all child nodes (list of BookmarkNode)
        """
        return self._children[:]
    
    def parent(self):
        """
        Public method to get a reference to the parent node.
        
        @return reference to the parent node (BookmarkNode)
        """
        return self._parent
    
    def add(self, child, offset=-1):
        """
        Public method to add/insert a child node.
        
        @param child reference to the node to add (BookmarkNode)
        @param offset position where to insert child (integer, -1 = append)
        """
        if child._type == BookmarkNode.Root:
            return
        
        if child._parent is not None:
            child._parent.remove(child)
        
        child._parent = self
        if offset == -1:
            self._children.append(child)
        else:
            self._children.insert(offset, child)
    
    def remove(self, child):
        """
        Public method to remove a child node.
        
        @param child reference to the child node (BookmarkNode)
        """
        child._parent = None
        if child in self._children:
            self._children.remove(child)
