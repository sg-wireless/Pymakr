# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a structure to hold the data for a speed dial page.
"""


from __future__ import unicode_literals


class Page(object):
    """
    Class to hold the data for a speed dial page.
    """
    def __init__(self, url="", title="", broken=False):
        """
        Constructor
        
        @param url URL of the page (string)
        @param title title of the page (string)
        @param broken flag indicating a broken connection (boolean)
        """
        self.url = url
        self.title = title
        self.broken = broken
    
    def __eq__(self, other):
        """
        Special method implementing the equality operator.
        
        @param other reference to the other page object (Page)
        @return flag indicating equality (boolean)
        """
        return self.title == other.title and \
            self.url == other.url
