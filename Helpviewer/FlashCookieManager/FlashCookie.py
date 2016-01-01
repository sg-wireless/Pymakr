# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Flash cookie class.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QDateTime


class FlashCookie(object):
    """
    Class implementing the Flash cookie.
    """
    def __init__(self):
        """
        Constructor
        """
        self.name = ""
        self.origin = ""
        self.size = 0
        self.path = ""
        self.contents = ""
        self.lastModified = QDateTime()
    
    def __eq__(self, other):
        """
        Special method to compare to another Flash cookie.
        
        @param other reference to the other Flash cookie
        @type FlashCookie
        @return flag indicating equality of the two cookies
        @rtype bool
        """
        return (self.name == other.name and
                self.path == other.path)
