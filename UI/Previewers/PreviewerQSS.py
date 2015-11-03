# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a previewer widget for Qt style sheet files.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import qVersion
from PyQt5.QtWidgets import QWidget, QMenu, QLabel, QHeaderView, \
    QListWidgetItem

from .Ui_PreviewerQSS import Ui_PreviewerQSS

import Preferences
import UI.PixmapCache


class PreviewerQSS(QWidget, Ui_PreviewerQSS):
    """
    Class implementing a previewer widget for Qt style sheet files.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(PreviewerQSS, self).__init__(parent)
        self.setupUi(self)
        
        # menu for the tool button
        self.__toolButtonMenu = QMenu(self)
        self.__toolButtonMenu.addAction(self.tr("Action 1"))
        self.__toolButtonMenu.addSeparator()
        self.__toolButtonMenu.addAction(self.tr("Action 2"))
        self.toolButton.setMenu(self.__toolButtonMenu)
        
        # a MDI window
        self.__mdi = self.mdiArea.addSubWindow(QLabel(self.tr("MDI")))
        self.__mdi.resize(160, 80)
        
        # tree and table widgets
        if qVersion() >= "5.0.0":
            self.tree.header().setSectionResizeMode(
                QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeToContents)
        else:
            self.tree.header().setResizeMode(
                QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setResizeMode(
                QHeaderView.ResizeToContents)
        self.tree.topLevelItem(0).setExpanded(True)
        
        # icon list widget
        for iconName, labelText in (
            ("filePython.png", self.tr("Python")),
            ("fileRuby.png", self.tr("Ruby")),
            ("fileJavascript.png", self.tr("JavaScript")),
        ):
            self.iconsListWidget.addItem(QListWidgetItem(
                UI.PixmapCache.getIcon(iconName), labelText))
    
    def processEditor(self, editor=None):
        """
        Public slot to process an editor's text.
        
        @param editor editor to be processed (Editor)
        """
        if editor is not None:
            fn = editor.getFileName()
            
            if fn:
                extension = os.path.normcase(os.path.splitext(fn)[1][1:])
            else:
                extension = ""
            if extension in \
                    Preferences.getEditor("PreviewQssFileNameExtensions"):
                styleSheet = editor.text()
                if styleSheet:
                    self.scrollAreaWidgetContents.setStyleSheet(styleSheet)
                else:
                    self.scrollAreaWidgetContents.setStyleSheet("")
                self.toolButton.menu().setStyleSheet(
                    self.scrollAreaWidgetContents.styleSheet())
