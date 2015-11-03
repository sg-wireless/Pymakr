# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an auto saver class.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject, QBasicTimer, QTime


class AutoSaver(QObject):
    """
    Class implementing the auto saver.
    """
    AUTOSAVE_IN = 1000 * 3
    MAXWAIT = 1000 * 15
    
    def __init__(self, parent, save):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        @param save slot to be called to perform the save operation
        @exception RuntimeError raised, if no parent is given
        """
        super(AutoSaver, self).__init__(parent)
        
        if parent is None:
            raise RuntimeError("AutoSaver: parent must not be None.")
        
        self.__save = save
        
        self.__timer = QBasicTimer()
        self.__firstChange = QTime()
    
    def changeOccurred(self):
        """
        Public slot handling a change.
        """
        if self.__firstChange.isNull():
            self.__firstChange.start()
        
        if self.__firstChange.elapsed() > self.MAXWAIT:
            self.saveIfNeccessary()
        else:
            self.__timer.start(self.AUTOSAVE_IN, self)
    
    def timerEvent(self, evt):
        """
        Protected method handling timer events.
        
        @param evt reference to the timer event (QTimerEvent)
        """
        if evt.timerId() == self.__timer.timerId():
            self.saveIfNeccessary()
        else:
            super(AutoSaver, self).timerEvent(evt)
    
    def saveIfNeccessary(self):
        """
        Public method to activate the save operation.
        """
        if not self.__timer.isActive():
            return
        
        self.__timer.stop()
        self.__firstChange = QTime()
        self.__save()
