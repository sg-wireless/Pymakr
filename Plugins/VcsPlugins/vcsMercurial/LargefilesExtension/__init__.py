# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Package implementing the largefiles extension support interface.
"""


from __future__ import unicode_literals


def getDefaults():
    """
    Function to get the default values of the extension.
    
    @return dictionary with default values and parameter as key (dict)
    """
    return {
        'minsize': 10,      # minimum size in MB
        'pattern': [],      # file name patterns
    }
