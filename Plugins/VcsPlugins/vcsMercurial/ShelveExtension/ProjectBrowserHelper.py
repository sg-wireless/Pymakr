# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the shelve extension project browser helper.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QMenu

from E5Gui import E5MessageBox

from ..HgExtensionProjectBrowserHelper import HgExtensionProjectBrowserHelper


class ShelveProjectBrowserHelper(HgExtensionProjectBrowserHelper):
    """
    Class implementing the shelve extension project browser helper.
    """
    def __init__(self, vcsObject, browserObject, projectObject):
        """
        Constructor
        
        @param vcsObject reference to the vcs object
        @param browserObject reference to the project browser object
        @param projectObject reference to the project object
        """
        super(ShelveProjectBrowserHelper, self).__init__(
            vcsObject, browserObject, projectObject)
    
    def initMenus(self):
        """
        Public method to generate the extension menus.
        
        @return dictionary of populated menu (dict of QMenu). The dict
            must have the keys 'mainMenu', 'multiMenu', 'backMenu', 'dirMenu'
            and 'dirMultiMenu'.
        """
        self.__menus = {}
        
        menu = QMenu(self.menuTitle())
        menu.setTearOffEnabled(True)
        menu.addAction(self.tr("Shelve changes"), self.__hgShelve)
        self.__menus['mainMenu'] = menu
        
        menu = QMenu(self.menuTitle())
        menu.setTearOffEnabled(True)
        menu.addAction(self.tr("Shelve changes"), self.__hgShelve)
        self.__menus['multiMenu'] = menu
        
        menu = QMenu(self.menuTitle())
        menu.setTearOffEnabled(True)
        menu.addAction(self.tr("Shelve changes"), self.__hgShelve)
        self.__menus['dirMenu'] = menu
        
        menu = QMenu(self.menuTitle())
        menu.setTearOffEnabled(True)
        menu.addAction(self.tr("Shelve changes"), self.__hgShelve)
        self.__menus['dirMultiMenu'] = menu
        
        return self.__menus
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        
        @return title of the menu (string)
        """
        return self.tr("Shelve")
    
    def showExtensionMenu(self, key, controlled):
        """
        Public method to prepare the extension menu for display.
        
        @param key menu key (string, one of 'mainMenu', 'multiMenu',
            'backMenu', 'dirMenu' or 'dirMultiMenu')
        @param controlled flag indicating to prepare the menu for a
            version controlled entry or a non-version controlled entry
            (boolean)
        """
        if key in self.__menus:
            self.__menus[key].setEnabled(controlled)
    
    def __reopenProject(self, shouldReopen, title):
        """
        Private method to reopen the project if needed and wanted.
        
        @param shouldReopen flag indicating that the project should
            be reopened (boolean)
        @param title title of the message box (string)
        """
        if shouldReopen:
            res = E5MessageBox.yesNo(
                None,
                title,
                self.tr("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgShelve(self):
        """
        Private slot used to shelve all current changes.
        """
        names = []
        for itm in self.browser.getSelectedItems():
            try:
                name = itm.fileName()
            except AttributeError:
                name = itm.dirName()
            names.append(name)
        shouldReopen = self.vcs.getExtensionObject("shelve")\
            .hgShelve(names)
        self.__reopenProject(shouldReopen, self.tr("Shelve"))
