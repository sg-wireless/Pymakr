# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the GreaseMonkey script.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QUrl, QRegExp

from .GreaseMonkeyUrlMatcher import GreaseMonkeyUrlMatcher


class GreaseMonkeyScript(object):
    """
    Class implementing the GreaseMonkey script.
    """
    DocumentStart = 0
    DocumentEnd = 1
    
    def __init__(self, manager, path):
        """
        Constructor
        
        @param manager reference to the manager object (GreaseMonkeyManager)
        @param path path of the Javascript file (string)
        """
        self.__manager = manager
        
        self.__name = ""
        self.__namespace = "GreaseMonkeyNS"
        self.__description = ""
        self.__version = ""
        
        self.__include = []
        self.__exclude = []
        
        self.__downloadUrl = QUrl()
        self.__startAt = GreaseMonkeyScript.DocumentEnd
        
        self.__script = ""
        self.__fileName = path
        self.__enabled = True
        self.__valid = False
        
        self.__parseScript(path)
    
    def isValid(self):
        """
        Public method to check the validity of the script.
        
        @return flag indicating a valid script (boolean)
        """
        return self.__valid
    
    def name(self):
        """
        Public method to get the name of the script.
        
        @return name of the script (string)
        """
        return self.__name
    
    def nameSpace(self):
        """
        Public method to get the name space of the script.
        
        @return name space of the script (string)
        """
        return self.__namespace
    
    def fullName(self):
        """
        Public method to get the full name of the script.
        
        @return full name of the script (string)
        """
        return "{0}/{1}".format(self.__namespace, self.__name)
    
    def description(self):
        """
        Public method to get the description of the script.
        
        @return description of the script (string)
        """
        return self.__description
    
    def version(self):
        """
        Public method to get the version of the script.
        
        @return version of the script (string)
        """
        return self.__version
    
    def downloadUrl(self):
        """
        Public method to get the download URL of the script.
        
        @return download URL of the script (QUrl)
        """
        return QUrl(self.__downloadUrl)
    
    def startAt(self):
        """
        Public method to get the start point of the script.
        
        @return start point of the script (DocumentStart or DocumentEnd)
        """
        return self.__startAt
    
    def isEnabled(self):
        """
        Public method to check, if the script is enabled.
        
        @return flag indicating an enabled state (boolean)
        """
        return self.__enabled
    
    def setEnabled(self, enable):
        """
        Public method to enable a script.
        
        @param enable flag indicating the new enabled state (boolean)
        """
        self.__enabled = enable
    
    def include(self):
        """
        Public method to get the list of included URLs.
        
        @return list of included URLs (list of strings)
        """
        list = []
        for matcher in self.__include:
            list.append(matcher.pattern())
        return list
    
    def exclude(self):
        """
        Public method to get the list of excluded URLs.
        
        @return list of excluded URLs (list of strings)
        """
        list = []
        for matcher in self.__exclude:
            list.append(matcher.pattern())
        return list
    
    def script(self):
        """
        Public method to get the Javascript source.
        
        @return Javascript source (string)
        """
        return self.__script
    
    def fileName(self):
        """
        Public method to get the path of the Javascript file.
        
        @return path path of the Javascript file (string)
        """
        return self.__fileName
    
    def match(self, urlString):
        """
        Public method to check, if the script matches the given URL.
        
        @param urlString URL (string)
        @return flag indicating a match (boolean)
        """
        if not self.__enabled:
            return False
        
        for matcher in self.__exclude:
            if matcher.match(urlString):
                return False
        
        for matcher in self.__include:
            if matcher.match(urlString):
                return True
        
        return False
    
    def __parseScript(self, path):
        """
        Private method to parse the given script and populate the data
        structure.
        
        @param path path of the Javascript file (string)
        """
        try:
            f = open(path, "r", encoding="utf-8")
            fileData = f.read()
            f.close()
        except (IOError, OSError):
            # silently ignore because it shouldn't happen
            return
        
        rx = QRegExp("// ==UserScript==(.*)// ==/UserScript==")
        rx.indexIn(fileData)
        metaDataBlock = rx.cap(1).strip()
        
        if metaDataBlock == "":
            # invalid script file
            return
        
        requireList = []
        for line in metaDataBlock.splitlines():
            if not line.startswith("// @"):
                continue
            
            line = line[3:].replace("\t", " ")
            index = line.find(" ")
            if index < 0:
                continue
            
            key = line[:index].strip()
            value = line[index + 1:].strip()
            
            # Ignored values: @resource, @unwrap
            
            if not key or not value:
                continue
            
            if key == "@name":
                self.__name = value
            
            elif key == "@namespace":
                self.__namespace = value
            
            elif key == "@description":
                self.__description = value
            
            elif key == "@version":
                self.__version = value
            
            elif key == "@updateURL":
                self.__downloadUrl = QUrl(value)
            
            elif key in ["@include", "@match"]:
                self.__include.append(GreaseMonkeyUrlMatcher(value))
            
            elif key in ["@exclude", "@exclude_match"]:
                self.__exclude.append(GreaseMonkeyUrlMatcher(value))
            
            elif key == "@require":
                requireList.append(value)
            
            elif key == "@run-at":
                if value == "document-end":
                    self.__startAt = GreaseMonkeyScript.DocumentEnd
                elif value == "document-start":
                    self.__startAt = GreaseMonkeyScript.DocumentStart
            
            elif key == "@downloadURL" and self.__downloadUrl.isEmpty():
                self.__downloadUrl = QUrl(value)
        
        if not self.__include:
            self.__include.append(GreaseMonkeyUrlMatcher("*"))
        
        marker = "// ==/UserScript=="
        index = fileData.find(marker) + len(marker)
        script = fileData[index:].strip()
        script = "{0}{1}".format(
            self.__manager.requireScripts(requireList),
            script)
        self.__script = "(function(){{{0}}})();".format(script)
        self.__valid = len(script) > 0
