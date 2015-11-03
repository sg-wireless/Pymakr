# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a data structure for login forms.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QUrl


class LoginForm(object):
    """
    Class implementing a data structure for login forms.
    """
    def __init__(self):
        """
        Constructor
        """
        self.url = QUrl()
        self.name = ""
        self.hasAPassword = False
        self.elements = []
        # list of tuples of element name and value (string, string)
        self.elementTypes = {}
        # dict of element name as key and type as value
    
    def isValid(self):
        """
        Public method to test for validity.
        
        @return flag indicating a valid form (boolean)
        """
        return len(self.elements) > 0
