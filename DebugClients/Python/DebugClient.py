# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a Qt free version of the debug client.
"""

from AsyncIO import AsyncIO
from DebugBase import DebugBase
import DebugClientBase


class DebugClient(DebugClientBase.DebugClientBase, AsyncIO, DebugBase):
    """
    Class implementing the client side of the debugger.
    
    This variant of the debugger implements the standard debugger client
    by subclassing all relevant base classes.
    """
    def __init__(self):
        """
        Constructor
        """
        AsyncIO.__init__(self)
        
        DebugClientBase.DebugClientBase.__init__(self)
        
        DebugBase.__init__(self, self)
        
        self.variant = 'Standard'

# We are normally called by the debugger to execute directly.

if __name__ == '__main__':
    debugClient = DebugClient()
    debugClient.main()

#
# eflag: FileType = Python2
