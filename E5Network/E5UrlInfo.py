# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class replacing QUrlInfo.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QDateTime


class E5UrlInfo(object):
    """
    Class implementing a replacement for QUrlInfo.
    """
    ReadOwner = 0o0400
    WriteOwner = 0o0200
    ExeOwner = 0o0100
    ReadGroup = 0o0040
    WriteGroup = 0o0020
    ExeGroup = 0o0010
    ReadOther = 0o0004
    WriteOther = 0o0002
    ExeOther = 0o0001
    
    def __init__(self):
        """
        Constructor
        """
        self.__valid = False
        
        self.__permissions = 0
        self.__size = 0
        self.__isDir = False
        self.__isFile = True
        self.__isSymlink = False
        self.__isWritable = True
        self.__isReadable = True
        self.__isExecutable = False
        self.__name = ""
        self.__owner = ""
        self.__group = ""
        self.__lastModified = QDateTime()
        self.__lastRead = QDateTime()
    
    def isValid(self):
        """
        Public method to check the validity of the object.
        
        @return flag indicating validity (boolean)
        """
        return self.__valid
    
    def setName(self, name):
        """
        Public method to set the name.
        
        @param name name to be set (string)
        """
        self.__name = name
        self.__valid = True
    
    def setPermissions(self, permissions):
        """
        Public method to set the permissions.
        
        @param permissions permissions to be set (integer)
        """
        self.__permissions = permissions
        self.__valid = True
    
    def setDir(self, isDir):
        """
        Public method to indicate a directory.
        
        @param isDir flag indicating a directory (boolean)
        """
        self.__isDir = isDir
        self.__valid = True
    
    def setFile(self, isFile):
        """
        Public method to indicate a file.
        
        @param isFile flag indicating a file (boolean)
        """
        self.__isFile = isFile
        self.__valid = True
    
    def setSymLink(self, isSymLink):
        """
        Public method to indicate a symbolic link.
        
        @param isSymLink flag indicating a symbolic link (boolean)
        """
        self.__isSymLink = isSymLink
        self.__valid = True
    
    def setOwner(self, owner):
        """
        Public method to set the owner.
        
        @param owner owner to be set (string)
        """
        self.__owner = owner
        self.__valid = True
    
    def setGroup(self, group):
        """
        Public method to set the group.
        
        @param group group to be set (string)
        """
        self.__group = group
        self.__valid = True
    
    def setSize(self, size):
        """
        Public method to set the size.
        
        @param size size to be set (integer)
        """
        self.__size = size
        self.__valid = True
    
    def setWritable(self, isWritable):
        """
        Public method to a writable entry.
        
        @param isWritable flag indicating a writable entry (boolean)
        """
        self.__isWritable = isWritable
        self.__valid = True
    
    def setReadable(self, isReadable):
        """
        Public method to a readable entry.
        
        @param isReadable flag indicating a readable entry (boolean)
        """
        self.__isReadable = isReadable
        self.__valid = True
    
    def setLastModified(self, dt):
        """
        Public method to set the last modified date and time.
        
        @param dt date and time to set (QDateTime)
        """
        self.__lastModified = QDateTime(dt)
        self.__valid = True
    
    def setLastRead(self, dt):
        """
        Public method to set the last read date and time.
        
        @param dt date and time to set (QDateTime)
        """
        self.__lastRead = QDateTime(dt)
        self.__valid = True
    
    def name(self):
        """
        Public method to get the name.
        
        @return name (string)
        """
        return self.__name
    
    def permissions(self):
        """
        Public method to get the permissions.
        
        @return permissions (integer)
        """
        return self.__permissions
    
    def owner(self):
        """
        Public method to get the owner.
        
        @return owner (string)
        """
        return self.__owner
    
    def group(self):
        """
        Public method to get the group.
        
        @return group (string)
        """
        return self.__group
    
    def size(self):
        """
        Public method to get the size.
        
        @return size (integer)
        """
        return self.__size
    
    def lastModified(self):
        """
        Public method to get the last modified date and time.
        
        @return last modified date and time (QDateTime)
        """
        return QDateTime(self.__lastModified)
    
    def lastRead(self):
        """
        Public method to get the last read date and time.
        
        @return last read date and time (QDateTime)
        """
        return QDateTime(self.__lastRead)
    
    def isDir(self):
        """
        Public method to test, if the entry is a directory.
        
        @return flag indicating a directory (boolean)
        """
        return self.__isDir
    
    def isFile(self):
        """
        Public method to test, if the entry is a file.
        
        @return flag indicating a file (boolean)
        """
        return self.__isFile
    
    def isSymLink(self):
        """
        Public method to test, if the entry is a symbolic link.
        
        @return flag indicating a symbolic link (boolean)
        """
        return self.__isSymlink
    
    def isWritable(self):
        """
        Public method to test, if the entry is writable.
        
        @return flag indicating writable (boolean)
        """
        return self.__isWritable
    
    def isReadable(self):
        """
        Public method to test, if the entry is readable.
        
        @return flag indicating readable (boolean)
        """
        return self.__isReadable
    
    def isExecutable(self):
        """
        Public method to test, if the entry is executable.
        
        @return flag indicating executable (boolean)
        """
        return self.__isExecutable
