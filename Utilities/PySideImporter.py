# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module to check for the presence of PySide by importing it.
"""

import sys

if __name__ == "__main__":
    try:
        import PySide       # __IGNORE_EXCEPTION__ __IGNORE_WARNING__
        ret = 0
    except ImportError:
        ret = 1
    
    sys.exit(ret)
    
#
# eflag: FileType = Python2
