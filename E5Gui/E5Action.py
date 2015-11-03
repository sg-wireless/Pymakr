# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an Action class extending QAction.

This extension is necessary in order to support alternate keyboard
shortcuts.
"""

from __future__ import unicode_literals

from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import QAction, QActionGroup, qApp


class ArgumentsError(RuntimeError):
    """
    Class implementing an exception, which is raised, if the wrong number of
    arguments are given.
    """
    def __init__(self, error):
        """
        Constructor
        
        @param error error message of the exception (string)
        """
        self.errorMessage = str(error)
        
    def __repr__(self):
        """
        Special method returning a representation of the exception.
        
        @return string representing the error message
        """
        return str(self.errorMessage)
        
    def __str__(self):
        """
        Special method returning a string representation of the exception.
        
        @return string representing the error message
        """
        return str(self.errorMessage)


class E5Action(QAction):
    """
    Class implementing an Action class extending QAction.
    """
    def __init__(self, *args):
        """
        Constructor
        
        @param args argument list of the constructor. This list is one of
            <ul>
            <li>text (string), icon (QIcon), menu text (string),
                accelarator (QKeySequence), alternative accelerator
                (QKeySequence), parent (QObject), name (string), toggle
                (boolean)</li>
            <li>text (string), icon (QIcon), menu text (string),
                accelarator (QKeySequence), alternative accelerator
                (QKeySequence), parent (QObject), name (string)</li>
            <li>text (string), menu text (string),
                accelarator (QKeySequence), alternative accelerator
                (QKeySequence), parent (QObject), name (string), toggle
                (boolean)</li>
            <li>text (string), menu text (string),
                accelarator (QKeySequence), alternative accelerator
                (QKeySequence), parent (QObject), name (string)</li>
            </ul>
        @exception ArgumentsError raised to indicate invalid arguments
        """
        if isinstance(args[1], QIcon):
            icon = args[1]
            incr = 1
        else:
            icon = None
            incr = 0
        if len(args) < 6 + incr:
            raise ArgumentsError(
                "Not enough arguments, {0:d} expected, got {1:d}".format(
                    6 + incr, len(args)))
        elif len(args) > 7 + incr:
            raise ArgumentsError(
                "Too many arguments, max. {0:d} expected, got {1:d}".format(
                    7 + incr, len(args)))
            
        parent = args[4 + incr]
        super(E5Action, self).__init__(parent)
        name = args[5 + incr]
        if name:
            self.setObjectName(name)
        
        if args[1 + incr]:
            self.setText(args[1 + incr])
        
        if args[0]:
            self.setIconText(args[0])
        if args[2 + incr]:
            self.setShortcut(QKeySequence(args[2 + incr]))
        
        if args[3 + incr]:
            self.setAlternateShortcut(QKeySequence(args[3 + incr]))
        
        if icon:
            self.setIcon(icon)
        
        if len(args) == 7 + incr:
            self.setCheckable(args[6 + incr])
        
        self.__ammendToolTip()
        
    def setAlternateShortcut(self, shortcut, removeEmpty=False):
        """
        Public slot to set the alternative keyboard shortcut.
        
        @param shortcut the alternative accelerator (QKeySequence)
        @param removeEmpty flag indicating to remove the alternate shortcut,
            if it is empty (boolean)
        """
        if not shortcut.isEmpty():
            shortcuts = self.shortcuts()
            if len(shortcuts) > 0:
                if len(shortcuts) == 1:
                    shortcuts.append(shortcut)
                else:
                    shortcuts[1] = shortcut
                self.setShortcuts(shortcuts)
        elif removeEmpty:
            shortcuts = self.shortcuts()
            if len(shortcuts) == 2:
                del shortcuts[1]
                self.setShortcuts(shortcuts)
        
    def alternateShortcut(self):
        """
        Public method to retrieve the alternative keyboard shortcut.
        
        @return the alternative accelerator (QKeySequence)
        """
        shortcuts = self.shortcuts()
        if len(shortcuts) < 2:
            return QKeySequence()
        else:
            return shortcuts[1]
        
    def setShortcut(self, shortcut):
        """
        Public slot to set the keyboard shortcut.
        
        @param shortcut the accelerator (QKeySequence)
        """
        super(E5Action, self).setShortcut(shortcut)
        self.__ammendToolTip()
        
    def setShortcuts(self, shortcuts):
        """
        Public slot to set the list of keyboard shortcuts.
        
        @param shortcuts list of keyboard accelerators (list of QKeySequence)
            or key for a platform dependent list of accelerators
            (QKeySequence.StandardKey)
        """
        super(E5Action, self).setShortcuts(shortcuts)
        self.__ammendToolTip()
        
    def setIconText(self, text):
        """
        Public slot to set the icon text of the action.
        
        @param text new icon text (string)
        """
        super(E5Action, self).setIconText(text)
        self.__ammendToolTip()
        
    def __ammendToolTip(self):
        """
        Private slot to add the primary keyboard accelerator to the tooltip.
        """
        shortcut = self.shortcut().toString(QKeySequence.NativeText)
        if shortcut:
            if qApp.isLeftToRight():
                fmt = "{0} ({1})"
            else:
                fmt = "({1}) {0}"
            self.setToolTip(fmt.format(self.iconText(), shortcut))


def addActions(target, actions):
    """
    Module function to add a list of actions to a widget.
    
    @param target reference to the target widget (QWidget)
    @param actions list of actions to be added to the target. A
        None indicates a separator (list of QActions)
    """
    if target is None:
        return
    
    for action in actions:
        if action is None:
            target.addSeparator()
        else:
            target.addAction(action)


def createActionGroup(parent, name=None, exclusive=False):
    """
    Module function to create an action group.
    
    @param parent parent object of the action group (QObject)
    @param name name of the action group object (string)
    @param exclusive flag indicating an exclusive action group (boolean)
    @return reference to the created action group (QActionGroup)
    """
    actGrp = QActionGroup(parent)
    if name:
        actGrp.setObjectName(name)
    actGrp.setExclusive(exclusive)
    return actGrp
