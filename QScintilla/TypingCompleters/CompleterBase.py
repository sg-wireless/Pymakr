# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a base class for all typing completers.

Typing completers are classes that implement some convenience actions,
that are performed while the user is typing (e.g. insert ')' when the
user types '(').
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject


class CompleterBase(QObject):
    """
    Class implementing the base class for all completers.
    """
    def __init__(self, editor, parent=None):
        """
        Constructor
        
        @param editor reference to the editor object (QScintilla.Editor)
        @param parent reference to the parent object (QObject)
            If parent is None, we set the editor as the parent.
        """
        if parent is None:
            parent = editor
        
        super(CompleterBase, self).__init__(parent)
        
        self.editor = editor
        self.enabled = False
    
    def setEnabled(self, enable):
        """
        Public slot to set the enabled state.
        
        @param enable flag indicating the new enabled state (boolean)
        """
        if enable:
            if not self.enabled:
                self.editor.SCN_CHARADDED.connect(self.charAdded)
        else:
            if self.enabled:
                self.editor.SCN_CHARADDED.disconnect(self.charAdded)
        self.enabled = enable
    
    def isEnabled(self):
        """
        Public method to get the enabled state.
        
        @return enabled state (boolean)
        """
        return self.enabled
    
    def charAdded(self, charNumber):
        """
        Public slot called to handle the user entering a character.
        
        Note 1: this slot must be overridden by subclasses implementing the
        specific behavior for the language.
        
        Note 2: charNumber can be greater than 255 because the editor is
        in UTF-8 mode by default.
        
        @param charNumber value of the character entered (integer)
        """
        pass    # just do nothing
    
    def readSettings(self):
        """
        Public slot called to reread the configuration parameters.
        
        Note: this slot should be overridden by subclasses having
        configurable parameters.
        """
        pass    # just do nothing
