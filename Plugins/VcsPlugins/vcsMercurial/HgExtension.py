# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the base class for Mercurial extension interfaces.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject


class HgExtension(QObject):
    """
    Class implementing the base class for Mercurial extension interfaces.
    """
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        super(HgExtension, self).__init__(vcs)
        
        self.vcs = vcs
    
    def shutdown(self):
        """
        Public method used to shutdown the extension interface.
        
        The method of this base class does nothing.
        """
        pass
