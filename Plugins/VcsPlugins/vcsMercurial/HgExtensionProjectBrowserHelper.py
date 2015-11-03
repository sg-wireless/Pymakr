# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the project browser helper base for Mercurial extension
interfaces.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject


class HgExtensionProjectBrowserHelper(QObject):
    """
    Class implementing the project browser helper base for Mercurial extension
    interfaces.
    
    Note: The methods initMenus() and menuTitle() have to be reimplemented by
    derived classes.
    """
    def __init__(self, vcsObject, browserObject, projectObject):
        """
        Constructor
        
        @param vcsObject reference to the vcs object
        @param browserObject reference to the project browser object
        @param projectObject reference to the project object
        """
        super(HgExtensionProjectBrowserHelper, self).__init__()
        
        self.vcs = vcsObject
        self.browser = browserObject
        self.project = projectObject
    
    def initMenus(self):
        """
        Public method to generate the extension menus.
        
        Note: Derived class must implement this method.
        
        @ireturn dictionary of populated menu (dict of QMenu). The dict
            must have the keys 'mainMenu', 'multiMenu', 'backMenu', 'dirMenu'
            and 'dirMultiMenu'.
        @exception NotImplementedError raised if the class has not been
            reimplemented
        """
        raise NotImplementedError
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        
        Note: Derived class must implement this method.
        
        @ireturn title of the menu (string)
        @exception NotImplementedError raised if the class has not been
            reimplemented
        """
        raise NotImplementedError
    
    def showExtensionMenu(self, key, controlled):
        """
        Public method to prepare the extension menu for display.
        
        Note: Derived class must implement this method to adjust the
        enabled states of its menus.
        
        @param key menu key (string, one of 'mainMenu', 'multiMenu',
            'backMenu', 'dirMenu' or 'dirMultiMenu')
        @param controlled flag indicating to prepare the menu for a
            version controlled entry or a non-version controlled entry
            (boolean)
        @exception NotImplementedError raised if the class has not been
            reimplemented
        """
        raise NotImplementedError

    def _updateVCSStatus(self, name):
        """
        Protected method to update the VCS status of an item.
        
        @param name filename or directoryname of the item to be updated
            (string)
        """
        self.project.getModel().updateVCSStatus(name)
