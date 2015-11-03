# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the project helper base for Mercurial extension interfaces.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject


class HgExtensionProjectHelper(QObject):
    """
    Class implementing the project helper base for Mercurial extension
    interfaces.
    
    Note: The methods initActions(), initMenu(mainMenu) and menuTitle() have
    to be reimplemented by derived classes.
    """
    def __init__(self):
        """
        Constructor
        """
        super(HgExtensionProjectHelper, self).__init__()
        
        self.actions = []
        
        self.initActions()
    
    def setObjects(self, vcsObject, projectObject):
        """
        Public method to set references to the vcs and project objects.
        
        @param vcsObject reference to the vcs object
        @param projectObject reference to the project object
        """
        self.vcs = vcsObject
        self.project = projectObject
    
    def getActions(self):
        """
        Public method to get a list of all actions.
        
        @return list of all actions (list of E5Action)
        """
        return self.actions[:]
    
    def initActions(self):
        """
        Public method to generate the action objects.
        
        Note: Derived class must implement this method.
        
        @exception NotImplementedError raised if the class has not been
            reimplemented
        """
        raise NotImplementedError
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the extension menu.
        
        Note: Derived class must implement this method.
        
        @param mainMenu reference to the main menu (QMenu)
        @ireturn populated menu (QMenu)
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
    
    def shutdown(self):
        """
        Public method to perform shutdown actions.
        
        Note: Derived class may implement this method if needed.
        """
        pass
