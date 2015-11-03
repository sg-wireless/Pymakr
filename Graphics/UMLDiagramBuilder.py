# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the UML diagram builder base class.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject


class UMLDiagramBuilder(QObject):
    """
    Class implementing the UML diagram builder base class.
    """
    def __init__(self, dialog, view, project):
        """
        Constructor
        
        @param dialog reference to the UML dialog (UMLDialog)
        @param view reference to the view object (UMLGraphicsView)
        @param project reference to the project object (Project)
        """
        super(UMLDiagramBuilder, self).__init__(dialog)
        
        self.umlView = view
        self.scene = self.umlView.scene()
        self.project = project
    
    def initialize(self):
        """
        Public method to initialize the object.
        """
        return
    
    def buildDiagram(self):
        """
        Public method to build the diagram.
        
        This class must be implemented in subclasses.
        
        @exception NotImplementedError raised to indicate that this class
            must be subclassed
        """
        raise NotImplementedError(
            "Method 'buildDiagram' must be implemented in subclasses.")
    
    def getPersistenceData(self):
        """
        Public method to get a string for data to be persisted.
        
        @return persisted data string (string)
        """
        return ""
    
    def parsePersistenceData(self, version, data):
        """
        Public method to parse persisted data.
        
        @param version version of the data (string)
        @param data persisted data to be parsed (string)
        @return flag indicating success (boolean)
        """
        return True
