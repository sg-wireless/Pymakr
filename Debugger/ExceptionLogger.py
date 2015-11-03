# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Exception Logger widget.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu

from E5Gui.E5Application import e5App


class ExceptionLogger(QTreeWidget):
    """
    Class implementing the Exception Logger widget.
    
    This class displays a log of all exceptions having occured during
    a debugging session.
    
    @signal sourceFile(string, int) emitted to open a source file at a line
    """
    sourceFile = pyqtSignal(str, int)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent the parent widget of this widget
        """
        super(ExceptionLogger, self).__init__(parent)
        self.setObjectName("ExceptionLogger")
        
        self.setWindowTitle(self.tr("Exceptions"))
        
        self.setWordWrap(True)
        self.setRootIsDecorated(True)
        self.setHeaderLabels([self.tr("Exception")])
        self.setSortingEnabled(False)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__showContextMenu)
        self.itemDoubleClicked.connect(self.__itemDoubleClicked)

        self.setWhatsThis(self.tr(
            """<b>Exceptions Logger</b>"""
            """<p>This windows shows a trace of all exceptions, that have"""
            """ occured during the last debugging session. Initially only"""
            """ the exception type and exception message are shown. After"""
            """ the expansion of this entry, the complete call stack as"""
            """ reported by the client is show with the most recent call"""
            """ first.</p>"""
        ))
        
        self.menu = QMenu(self)
        self.menu.addAction(self.tr("Show source"), self.__openSource)
        self.menu.addAction(self.tr("Clear"), self.clear)
        self.menu.addSeparator()
        self.menu.addAction(self.tr("Configure..."), self.__configure)
        
        self.backMenu = QMenu(self)
        self.backMenu.addAction(self.tr("Clear"), self.clear)
        self.backMenu.addSeparator()
        self.backMenu.addAction(self.tr("Configure..."), self.__configure)
        
    def __itemDoubleClicked(self, itm):
        """
        Private slot to handle the double click of an item.
        
        @param itm the item that was double clicked(QTreeWidgetItem), ignored
        """
        self.__openSource()

    def __showContextMenu(self, coord):
        """
        Private slot to show the context menu of the listview.
        
        @param coord the global coordinates of the mouse pointer (QPoint)
        """
        itm = self.itemAt(coord)
        coord = self.mapToGlobal(coord)
        if itm is None:
            self.backMenu.popup(coord)
        else:
            self.menu.popup(coord)
            
    def addException(self, exceptionType, exceptionMessage, stackTrace):
        """
        Public slot to handle the arrival of a new exception.
        
        @param exceptionType type of exception raised (string)
        @param exceptionMessage message given by the exception (string)
        @param stackTrace list of stack entries.
        """
        itm = QTreeWidgetItem(self)
        if exceptionType is None:
            itm.setText(
                0, self.tr('An unhandled exception occured.'
                           ' See the shell window for details.'))
            return
        
        if exceptionMessage == '':
            itm.setText(0, "{0}".format(exceptionType))
        else:
            itm.setText(0, "{0}, {1}".format(exceptionType, exceptionMessage))
        
        # now add the call stack, most recent call first
        for entry in stackTrace:
            excitm = QTreeWidgetItem(itm)
            excitm.setText(0, "{0}, {1:d}".format(entry[0], entry[1]))
            
    def debuggingStarted(self):
        """
        Public slot to clear the listview upon starting a new debugging
        session.
        """
        self.clear()
        
    def __openSource(self):
        """
        Private slot to handle a double click on an entry.
        """
        itm = self.currentItem()
        
        if itm.parent() is None:
            return
            
        entry = itm.text(0)
        entryList = entry.split(",")
        try:
            self.sourceFile.emit(entryList[0], int(entryList[1]))
        except (IndexError, ValueError):
            pass
        
    def __configure(self):
        """
        Private method to open the configuration dialog.
        """
        e5App().getObject("UserInterface")\
            .showPreferences("debuggerGeneralPage")
