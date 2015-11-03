# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class to read Netscape HTML bookmark files.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

from PyQt5.QtCore import QObject, QIODevice, QFile, QRegExp, Qt, QDateTime

from .BookmarkNode import BookmarkNode

import Utilities


class NsHtmlReader(QObject):
    """
    Class implementing a reader object for Netscape HTML bookmark files.
    """
    indentSize = 4
    
    def __init__(self):
        """
        Constructor
        """
        super(NsHtmlReader, self).__init__()
        
        self.__folderRx = QRegExp("<DT><H3(.*)>(.*)</H3>", Qt.CaseInsensitive)
        self.__folderRx.setMinimal(True)
        
        self.__endFolderRx = QRegExp("</DL>", Qt.CaseInsensitive)
        
        self.__bookmarkRx = QRegExp("<DT><A(.*)>(.*)</A>", Qt.CaseInsensitive)
        self.__bookmarkRx.setMinimal(True)
        
        self.__descRx = QRegExp("<DD>(.*)", Qt.CaseInsensitive)
        
        self.__separatorRx = QRegExp("<HR>", Qt.CaseInsensitive)
        
        self.__urlRx = QRegExp('HREF="(.*)"', Qt.CaseInsensitive)
        self.__urlRx.setMinimal(True)
        
        self.__addedRx = QRegExp('ADD_DATE="(\d*)"', Qt.CaseInsensitive)
        self.__addedRx.setMinimal(True)
        
        self.__modifiedRx = QRegExp(
            'LAST_MODIFIED="(\d*)"', Qt.CaseInsensitive)
        self.__modifiedRx.setMinimal(True)
        
        self.__visitedRx = QRegExp('LAST_VISIT="(\d*)"', Qt.CaseInsensitive)
        self.__visitedRx.setMinimal(True)
        
        self.__foldedRx = QRegExp("FOLDED", Qt.CaseInsensitive)
    
    def read(self, fileNameOrDevice):
        """
        Public method to read a Netscape HTML bookmark file.
        
        @param fileNameOrDevice name of the file to read (string)
            or reference to the device to read (QIODevice)
        @return reference to the root node (BookmarkNode)
        """
        if isinstance(fileNameOrDevice, QIODevice):
            dev = fileNameOrDevice
        else:
            f = QFile(fileNameOrDevice)
            if not f.exists():
                return BookmarkNode(BookmarkNode.Root)
            f.open(QFile.ReadOnly)
            dev = f
        
        folders = []
        lastNode = None
        
        root = BookmarkNode(BookmarkNode.Root)
        folders.append(root)
        
        while not dev.atEnd():
            line = str(dev.readLine(), encoding="utf-8").rstrip()
            if self.__folderRx.indexIn(line) != -1:
                # folder definition
                arguments = self.__folderRx.cap(1)
                name = self.__folderRx.cap(2)
                node = BookmarkNode(BookmarkNode.Folder, folders[-1])
                node.title = Utilities.html_udecode(name)
                node.expanded = self.__foldedRx.indexIn(arguments) == -1
                if self.__addedRx.indexIn(arguments) != -1:
                    node.added = QDateTime.fromTime_t(
                        int(self.__addedRx.cap(1)))
                folders.append(node)
                lastNode = node
            
            elif self.__endFolderRx.indexIn(line) != -1:
                # end of folder definition
                folders.pop()
            
            elif self.__bookmarkRx.indexIn(line) != -1:
                # bookmark definition
                arguments = self.__bookmarkRx.cap(1)
                name = self.__bookmarkRx.cap(2)
                node = BookmarkNode(BookmarkNode.Bookmark, folders[-1])
                node.title = Utilities.html_udecode(name)
                if self.__urlRx.indexIn(arguments) != -1:
                    node.url = self.__urlRx.cap(1)
                if self.__addedRx.indexIn(arguments) != -1:
                    node.added = QDateTime.fromTime_t(
                        int(self.__addedRx.cap(1)))
                if self.__modifiedRx.indexIn(arguments) != -1:
                    node.modified = QDateTime.fromTime_t(
                        int(self.__modifiedRx.cap(1)))
                if self.__visitedRx.indexIn(arguments) != -1:
                    node.visited = QDateTime.fromTime_t(
                        int(self.__visitedRx.cap(1)))
                lastNode = node
            
            elif self.__descRx.indexIn(line) != -1:
                # description
                if lastNode:
                    lastNode.desc = Utilities.html_udecode(
                        self.__descRx.cap(1))
            
            elif self.__separatorRx.indexIn(line) != -1:
                # separator definition
                BookmarkNode(BookmarkNode.Separator, folders[-1])
        
        return root
