# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the GreaseMonkey URL matcher.
"""

from __future__ import unicode_literals

import re

from PyQt5.QtCore import Qt, QRegExp


def wildcardMatch(string, pattern):
    """
    Module function implementing a special wildcard matcher.
    
    @param string string to match (string)
    @param pattern pattern to be used (string)
    @return flag indicating a successful match (boolean)
    """
    stringSize = len(string)
    
    startsWithWildcard = pattern.startswith("*")
    endsWithWildcard = pattern.endswith("*")
    
    parts = pattern.split("*")
    pos = 0
    
    if startsWithWildcard:
        pos = string.find(parts[1])
        if pos == -1:
            return False
    
    for part in parts:
        pos = string.find(part, pos)
        if pos == -1:
            return False
    
    if not endsWithWildcard and stringSize - pos != len(parts[-1]):
        return False
    
    return True


class GreaseMonkeyUrlMatcher(object):
    """
    Class implementing the GreaseMonkey URL matcher.
    """
    def __init__(self, pattern):
        """
        Constructor
        
        @param pattern pattern to be used for the matching (string)
        """
        self.__pattern = pattern
        self.__matchString = ""
        self.__regExp = QRegExp()
        self.__useRegExp = False
        
        self.__parsePattern(self.__pattern)
    
    def pattern(self):
        """
        Public method to get the match pattern.
        
        @return match pattern (string)
        """
        return self.__pattern
    
    def match(self, urlString):
        """
        Public method to match the given URL.
        
        @param urlString URL to match (string)
        @return flag indicating a successful match (boolean)
        """
        if self.__useRegExp:
            return self.__regExp.indexIn(urlString) != -1
        else:
            return wildcardMatch(urlString, self.__matchString)
    
    def __parsePattern(self, pattern):
        """
        Private method to parse the match pattern.
        
        @param pattern match pattern to be used (string)
        """
        if pattern.startswith("/") and pattern.endswith("/"):
            pattern = pattern[1:-1]
            
            self.__regExp = QRegExp(pattern, Qt.CaseInsensitive)
            self.__useRegExp = True
        elif ".tld" in pattern:
            # escape special symbols
            pattern = re.sub(r"(\W)", r"\\\1", pattern)
            # remove multiple wildcards
            pattern = re.sub(r"\*+", "*", pattern)
            # process anchor at expression start
            pattern = re.sub(r"^\\\|", "^", pattern)
            # process anchor at expression end
            pattern = re.sub(r"\\\|$", "$", pattern)
            # replace wildcards by .*
            pattern = re.sub(r"\\\*", ".*", pattern)
            # replace domain pattern
            pattern = re.sub(r"\.tld", r"\.[a-z.]{2,6}")
            
            self.__useRegExp = True
            self.__regExp = QRegExp(pattern, Qt.CaseInsensitive)
        else:
            self.__matchString = pattern
