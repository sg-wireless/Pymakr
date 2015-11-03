# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the VCS project browser helper for Mercurial.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtWidgets import QMenu, QDialog

from E5Gui.E5Application import e5App

from Project.ProjectBrowserModel import ProjectBrowserFileItem

from VCS.ProjectBrowserHelper import VcsProjectBrowserHelper

import UI.PixmapCache


class HgProjectBrowserHelper(VcsProjectBrowserHelper):
    """
    Class implementing the VCS project browser helper for Mercurial.
    """
    def __init__(self, vcsObject, browserObject, projectObject,
                 isTranslationsBrowser, parent=None, name=None):
        """
        Constructor
        
        @param vcsObject reference to the vcs object
        @param browserObject reference to the project browser object
        @param projectObject reference to the project object
        @param isTranslationsBrowser flag indicating, the helper is requested
            for the translations browser (this needs some special treatment)
        @param parent parent widget (QWidget)
        @param name name of this object (string)
        """
        VcsProjectBrowserHelper.__init__(self, vcsObject, browserObject,
                                         projectObject, isTranslationsBrowser,
                                         parent, name)
        
        # instantiate the extensions
        from .ShelveExtension.ProjectBrowserHelper import \
            ShelveProjectBrowserHelper
        from .LargefilesExtension.ProjectBrowserHelper import \
            LargefilesProjectBrowserHelper
        self.__extensions = {
            "shelve": ShelveProjectBrowserHelper(
                vcsObject, browserObject, projectObject),
            "largefiles": LargefilesProjectBrowserHelper(
                vcsObject, browserObject, projectObject),
        }
        
        self.__extensionMenuTitles = {}
        for extension in self.__extensions:
            self.__extensionMenuTitles[
                self.__extensions[extension].menuTitle()] = extension
        self.__extensionMenus = {}
        for extension in self.__extensions:
            self.__extensionMenus[extension] = \
                self.__extensions[extension].initMenus()
    
    def __showExtensionMenu(self, key, controlled):
        """
        Private slot showing the extensions menu.
        
        @param key menu key (string, one of 'mainMenu', 'multiMenu',
            'backMenu', 'dirMenu' or 'dirMultiMenu')
        @param controlled flag indicating to show the menu for a
            version controlled entry or a non-version controlled entry
            (boolean)
        """
        for extensionName in self.__extensionMenus:
            if key in self.__extensionMenus[extensionName]:
                self.__extensionMenus[extensionName][key].setEnabled(
                    self.vcs.isExtensionActive(extensionName))
                if self.__extensionMenus[extensionName][key].isEnabled():
                    # adjust individual extension menu entries
                    self.__extensions[extensionName].showExtensionMenu(
                        key, controlled)
                if (not self.__extensionMenus[extensionName][key].isEnabled()
                    and self.__extensionMenus[extensionName][key]
                        .isTearOffMenuVisible()):
                    self.__extensionMenus[extensionName][key].hideTearOffMenu()
    
    def showContextMenu(self, menu, standardItems):
        """
        Public slot called before the context menu is shown.
        
        It enables/disables the VCS menu entries depending on the overall
        VCS status and the file status.
        
        @param menu reference to the menu to be shown
        @param standardItems array of standard items that need
            activation/deactivation depending on the overall VCS status
        """
        if self.browser.currentItem().data(1) == self.vcs.vcsName():
            controlled = True
            for act in self.vcsMenuActions:
                act.setEnabled(True)
            for act in self.vcsAddMenuActions:
                act.setEnabled(False)
            for act in standardItems:
                act.setEnabled(False)
            if not hasattr(self.browser.currentItem(), 'fileName'):
                self.annotateAct.setEnabled(False)
        else:
            controlled = False
            for act in self.vcsMenuActions:
                act.setEnabled(False)
            for act in self.vcsAddMenuActions:
                act.setEnabled(True)
            for act in standardItems:
                act.setEnabled(True)
        self.__showExtensionMenu("mainMenu", controlled)
    
    def showContextMenuMulti(self, menu, standardItems):
        """
        Public slot called before the context menu (multiple selections) is
        shown.
        
        It enables/disables the VCS menu entries depending on the overall
        VCS status and the files status.
        
        @param menu reference to the menu to be shown
        @param standardItems array of standard items that need
            activation/deactivation depending on the overall VCS status
        """
        vcsName = self.vcs.vcsName()
        items = self.browser.getSelectedItems()
        vcsItems = 0
        # determine number of selected items under VCS control
        for itm in items:
            if itm.data(1) == vcsName:
                vcsItems += 1
        
        if vcsItems > 0:
            controlled = True
            if vcsItems != len(items):
                for act in self.vcsMultiMenuActions:
                    act.setEnabled(False)
            else:
                for act in self.vcsMultiMenuActions:
                    act.setEnabled(True)
            for act in self.vcsAddMultiMenuActions:
                act.setEnabled(False)
            for act in standardItems:
                act.setEnabled(False)
        else:
            controlled = False
            for act in self.vcsMultiMenuActions:
                act.setEnabled(False)
            for act in self.vcsAddMultiMenuActions:
                act.setEnabled(True)
            for act in standardItems:
                act.setEnabled(True)
        self.__showExtensionMenu("multiMenu", controlled)
    
    def showContextMenuDir(self, menu, standardItems):
        """
        Public slot called before the context menu is shown.
        
        It enables/disables the VCS menu entries depending on the overall
        VCS status and the directory status.
        
        @param menu reference to the menu to be shown
        @param standardItems array of standard items that need
            activation/deactivation depending on the overall VCS status
        """
        if self.browser.currentItem().data(1) == self.vcs.vcsName():
            controlled = True
            for act in self.vcsDirMenuActions:
                act.setEnabled(True)
            for act in self.vcsAddDirMenuActions:
                act.setEnabled(False)
            for act in standardItems:
                act.setEnabled(False)
        else:
            controlled = False
            for act in self.vcsDirMenuActions:
                act.setEnabled(False)
            for act in self.vcsAddDirMenuActions:
                act.setEnabled(True)
            for act in standardItems:
                act.setEnabled(True)
        self.__showExtensionMenu("dirMenu", controlled)
    
    def showContextMenuDirMulti(self, menu, standardItems):
        """
        Public slot called before the context menu is shown.
        
        It enables/disables the VCS menu entries depending on the overall
        VCS status and the directory status.
        
        @param menu reference to the menu to be shown
        @param standardItems array of standard items that need
            activation/deactivation depending on the overall VCS status
        """
        vcsName = self.vcs.vcsName()
        items = self.browser.getSelectedItems()
        vcsItems = 0
        # determine number of selected items under VCS control
        for itm in items:
            if itm.data(1) == vcsName:
                vcsItems += 1
        
        if vcsItems > 0:
            controlled = True
            if vcsItems != len(items):
                for act in self.vcsDirMultiMenuActions:
                    act.setEnabled(False)
            else:
                for act in self.vcsDirMultiMenuActions:
                    act.setEnabled(True)
            for act in self.vcsAddDirMultiMenuActions:
                act.setEnabled(False)
            for act in standardItems:
                act.setEnabled(False)
        else:
            controlled = False
            for act in self.vcsDirMultiMenuActions:
                act.setEnabled(False)
            for act in self.vcsAddDirMultiMenuActions:
                act.setEnabled(True)
            for act in standardItems:
                act.setEnabled(True)
        self.__showExtensionMenu("dirMultiMenu", controlled)
    
    ###########################################################################
    ## Private menu generation methods below
    ###########################################################################
    
    def __addExtensionsMenu(self, menu, key):
        """
        Private method to add an extension menu entry.
        
        @param menu menu to add it to (QMenu)
        @param key menu key (string, one of 'mainMenu', 'multiMenu',
            'backMenu', 'dirMenu' or 'dirMultiMenu')
        @return reference to the menu action (QAction)
        """
        act = None
        if key in ['mainMenu', 'multiMenu', 'backMenu', 'dirMenu',
                   'dirMultiMenu']:
            extensionsMenu = QMenu(self.tr("Extensions"), menu)
            extensionsMenu.setTearOffEnabled(True)
            for extensionMenuTitle in sorted(self.__extensionMenuTitles):
                extensionName = self.__extensionMenuTitles[extensionMenuTitle]
                if key in self.__extensionMenus[extensionName]:
                    extensionsMenu.addMenu(
                        self.__extensionMenus[extensionName][key])
            if not extensionsMenu.isEmpty():
                if not menu.isEmpty():
                    menu.addSeparator()
                act = menu.addMenu(extensionsMenu)
        return act
    
    ###########################################################################
    ## Protected menu generation methods below
    ###########################################################################
    
    def _addVCSMenu(self, mainMenu):
        """
        Protected method used to add the VCS menu to all project browsers.
        
        @param mainMenu reference to the menu to be amended
        """
        self.vcsMenuActions = []
        self.vcsAddMenuActions = []
        
        menu = QMenu(self.tr("Version Control"))
        
        act = menu.addAction(
            UI.PixmapCache.getIcon(
                os.path.join("VcsPlugins", "vcsMercurial", "icons",
                             "mercurial.png")),
            self.vcs.vcsName(), self._VCSInfoDisplay)
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        menu.addSeparator()
        
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsCommit.png"),
            self.tr('Commit changes to repository...'),
            self._VCSCommit)
        self.vcsMenuActions.append(act)
        self.__addExtensionsMenu(menu, 'mainMenu')
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsAdd.png"),
            self.tr('Add to repository'),
            self._VCSAdd)
        self.vcsAddMenuActions.append(act)
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsRemove.png"),
            self.tr('Remove from repository (and disk)'),
            self._VCSRemove)
        self.vcsMenuActions.append(act)
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsRemove.png"),
            self.tr('Remove from repository only'),
            self.__HgForget)
        self.vcsMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(self.tr('Copy'), self.__HgCopy)
        self.vcsMenuActions.append(act)
        act = menu.addAction(self.tr('Move'), self.__HgMove)
        self.vcsMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsLog.png"),
            self.tr('Show log'), self._VCSLog)
        self.vcsMenuActions.append(act)
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsLog.png"),
            self.tr('Show log browser'), self._VCSLogBrowser)
        self.vcsMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsStatus.png"),
            self.tr('Show status'), self._VCSStatus)
        self.vcsMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsDiff.png"),
            self.tr('Show differences'), self._VCSDiff)
        self.vcsMenuActions.append(act)
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsSbsDiff.png"),
            self.tr('Show differences side-by-side'), self.__HgSbsDiff)
        self.vcsMenuActions.append(act)
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsDiff.png"),
            self.tr('Show differences (extended)'),
            self.__HgExtendedDiff)
        self.vcsMenuActions.append(act)
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsSbsDiff.png"),
            self.tr('Show differences side-by-side (extended)'),
            self.__HgSbsExtendedDiff)
        self.vcsMenuActions.append(act)
        self.annotateAct = menu.addAction(
            self.tr('Show annotated file'),
            self.__HgAnnotate)
        self.vcsMenuActions.append(self.annotateAct)
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsRevert.png"),
            self.tr('Revert changes'), self.__HgRevert)
        self.vcsMenuActions.append(act)
        act = menu.addAction(
            self.tr('Conflicts resolved'), self.__HgResolved)
        self.vcsMenuActions.append(act)
        act = menu.addAction(
            self.tr('Conflicts unresolved'), self.__HgUnresolved)
        self.vcsMenuActions.append(act)
        act = menu.addAction(
            self.tr('Re-Merge'), self.__HgReMerge)
        self.vcsMenuActions.append(act)
        menu.addSeparator()
        menu.addAction(self.tr('Select all local file entries'),
                       self.browser.selectLocalEntries)
        menu.addAction(self.tr('Select all versioned file entries'),
                       self.browser.selectVCSEntries)
        menu.addAction(self.tr('Select all local directory entries'),
                       self.browser.selectLocalDirEntries)
        menu.addAction(self.tr('Select all versioned directory entries'),
                       self.browser.selectVCSDirEntries)
        menu.addSeparator()
        menu.addAction(self.tr("Configure..."), self.__HgConfigure)
        
        mainMenu.addSeparator()
        mainMenu.addMenu(menu)
        self.menu = menu
    
    def _addVCSMenuMulti(self, mainMenu):
        """
        Protected method used to add the VCS menu for multi selection to all
        project browsers.
        
        @param mainMenu reference to the menu to be amended
        """
        self.vcsMultiMenuActions = []
        self.vcsAddMultiMenuActions = []
        
        menu = QMenu(self.tr("Version Control"))
        
        act = menu.addAction(
            UI.PixmapCache.getIcon(
                os.path.join("VcsPlugins", "vcsMercurial", "icons",
                             "mercurial.png")),
            self.vcs.vcsName(), self._VCSInfoDisplay)
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        menu.addSeparator()
        
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsCommit.png"),
            self.tr('Commit changes to repository...'),
            self._VCSCommit)
        self.vcsMultiMenuActions.append(act)
        self.__addExtensionsMenu(menu, 'multiMenu')
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsAdd.png"),
            self.tr('Add to repository'), self._VCSAdd)
        self.vcsAddMultiMenuActions.append(act)
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsRemove.png"),
            self.tr('Remove from repository (and disk)'),
            self._VCSRemove)
        self.vcsMultiMenuActions.append(act)
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsRemove.png"),
            self.tr('Remove from repository only'),
            self.__HgForget)
        self.vcsMultiMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsStatus.png"),
            self.tr('Show status'), self._VCSStatus)
        self.vcsMultiMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsDiff.png"),
            self.tr('Show differences'), self._VCSDiff)
        self.vcsMultiMenuActions.append(act)
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsDiff.png"),
            self.tr('Show differences (extended)'),
            self.__HgExtendedDiff)
        self.vcsMultiMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsRevert.png"),
            self.tr('Revert changes'), self.__HgRevert)
        self.vcsMultiMenuActions.append(act)
        act = menu.addAction(
            self.tr('Conflicts resolved'), self.__HgResolved)
        self.vcsMultiMenuActions.append(act)
        act = menu.addAction(
            self.tr('Conflicts unresolved'), self.__HgUnresolved)
        self.vcsMultiMenuActions.append(act)
        act = menu.addAction(
            self.tr('Re-Merge'), self.__HgReMerge)
        self.vcsMultiMenuActions.append(act)
        menu.addSeparator()
        menu.addAction(self.tr('Select all local file entries'),
                       self.browser.selectLocalEntries)
        menu.addAction(self.tr('Select all versioned file entries'),
                       self.browser.selectVCSEntries)
        menu.addAction(self.tr('Select all local directory entries'),
                       self.browser.selectLocalDirEntries)
        menu.addAction(self.tr('Select all versioned directory entries'),
                       self.browser.selectVCSDirEntries)
        menu.addSeparator()
        menu.addAction(self.tr("Configure..."), self.__HgConfigure)
        
        mainMenu.addSeparator()
        mainMenu.addMenu(menu)
        self.menuMulti = menu
    
    def _addVCSMenuBack(self, mainMenu):
        """
        Protected method used to add the VCS menu to all project browsers.
        
        @param mainMenu reference to the menu to be amended
        """
        menu = QMenu(self.tr("Version Control"))
        
        act = menu.addAction(
            UI.PixmapCache.getIcon(
                os.path.join("VcsPlugins", "vcsMercurial", "icons",
                             "mercurial.png")),
            self.vcs.vcsName(), self._VCSInfoDisplay)
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        menu.addSeparator()
        
        menu.addAction(self.tr('Select all local file entries'),
                       self.browser.selectLocalEntries)
        menu.addAction(self.tr('Select all versioned file entries'),
                       self.browser.selectVCSEntries)
        menu.addAction(self.tr('Select all local directory entries'),
                       self.browser.selectLocalDirEntries)
        menu.addAction(self.tr('Select all versioned directory entries'),
                       self.browser.selectVCSDirEntries)
        menu.addSeparator()
        menu.addAction(self.tr("Configure..."), self.__HgConfigure)
        
        mainMenu.addSeparator()
        mainMenu.addMenu(menu)
        self.menuBack = menu
    
    def _addVCSMenuDir(self, mainMenu):
        """
        Protected method used to add the VCS menu to all project browsers.
        
        @param mainMenu reference to the menu to be amended
        """
        if mainMenu is None:
            return
        
        self.vcsDirMenuActions = []
        self.vcsAddDirMenuActions = []
        
        menu = QMenu(self.tr("Version Control"))
        
        act = menu.addAction(
            UI.PixmapCache.getIcon(
                os.path.join("VcsPlugins", "vcsMercurial", "icons",
                             "mercurial.png")),
            self.vcs.vcsName(), self._VCSInfoDisplay)
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        menu.addSeparator()
        
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsCommit.png"),
            self.tr('Commit changes to repository...'),
            self._VCSCommit)
        self.vcsDirMenuActions.append(act)
        self.__addExtensionsMenu(menu, 'dirMenu')
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsAdd.png"),
            self.tr('Add to repository'), self._VCSAdd)
        self.vcsAddDirMenuActions.append(act)
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsRemove.png"),
            self.tr('Remove from repository (and disk)'),
            self._VCSRemove)
        self.vcsDirMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(self.tr('Copy'), self.__HgCopy)
        self.vcsDirMenuActions.append(act)
        act = menu.addAction(self.tr('Move'), self.__HgMove)
        self.vcsDirMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsLog.png"),
            self.tr('Show log'), self._VCSLog)
        self.vcsDirMenuActions.append(act)
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsLog.png"),
            self.tr('Show log browser'), self._VCSLogBrowser)
        self.vcsDirMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsStatus.png"),
            self.tr('Show status'), self._VCSStatus)
        self.vcsDirMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsDiff.png"),
            self.tr('Show differences'), self._VCSDiff)
        self.vcsDirMenuActions.append(act)
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsDiff.png"),
            self.tr('Show differences (extended)'),
            self.__HgExtendedDiff)
        self.vcsDirMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsRevert.png"),
            self.tr('Revert changes'), self.__HgRevert)
        self.vcsDirMenuActions.append(act)
        act = menu.addAction(
            self.tr('Conflicts resolved'), self.__HgResolved)
        self.vcsDirMenuActions.append(act)
        act = menu.addAction(
            self.tr('Conflicts unresolved'), self.__HgUnresolved)
        self.vcsDirMenuActions.append(act)
        act = menu.addAction(
            self.tr('Re-Merge'), self.__HgReMerge)
        self.vcsDirMenuActions.append(act)
        menu.addSeparator()
        menu.addAction(self.tr('Select all local file entries'),
                       self.browser.selectLocalEntries)
        menu.addAction(self.tr('Select all versioned file entries'),
                       self.browser.selectVCSEntries)
        menu.addAction(self.tr('Select all local directory entries'),
                       self.browser.selectLocalDirEntries)
        menu.addAction(self.tr('Select all versioned directory entries'),
                       self.browser.selectVCSDirEntries)
        menu.addSeparator()
        menu.addAction(self.tr("Configure..."), self.__HgConfigure)
        
        mainMenu.addSeparator()
        mainMenu.addMenu(menu)
        self.menuDir = menu
    
    def _addVCSMenuDirMulti(self, mainMenu):
        """
        Protected method used to add the VCS menu to all project browsers.
        
        @param mainMenu reference to the menu to be amended
        """
        if mainMenu is None:
            return
        
        self.vcsDirMultiMenuActions = []
        self.vcsAddDirMultiMenuActions = []
        
        menu = QMenu(self.tr("Version Control"))
        
        act = menu.addAction(
            UI.PixmapCache.getIcon(
                os.path.join("VcsPlugins", "vcsMercurial", "icons",
                             "mercurial.png")),
            self.vcs.vcsName(), self._VCSInfoDisplay)
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        menu.addSeparator()
        
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsCommit.png"),
            self.tr('Commit changes to repository...'),
            self._VCSCommit)
        self.vcsDirMultiMenuActions.append(act)
        self.__addExtensionsMenu(menu, 'dirMultiMenu')
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsAdd.png"),
            self.tr('Add to repository'), self._VCSAdd)
        self.vcsAddDirMultiMenuActions.append(act)
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsRemove.png"),
            self.tr('Remove from repository (and disk)'),
            self._VCSRemove)
        self.vcsDirMultiMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsStatus.png"),
            self.tr('Show status'), self._VCSStatus)
        self.vcsDirMultiMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsDiff.png"),
            self.tr('Show differences'), self._VCSDiff)
        self.vcsDirMultiMenuActions.append(act)
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsDiff.png"),
            self.tr('Show differences (extended)'),
            self.__HgExtendedDiff)
        self.vcsDirMultiMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(
            UI.PixmapCache.getIcon("vcsRevert.png"),
            self.tr('Revert changes'), self.__HgRevert)
        self.vcsDirMultiMenuActions.append(act)
        act = menu.addAction(
            self.tr('Conflicts resolved'), self.__HgResolved)
        self.vcsDirMultiMenuActions.append(act)
        act = menu.addAction(
            self.tr('Conflicts unresolved'), self.__HgUnresolved)
        self.vcsDirMultiMenuActions.append(act)
        act = menu.addAction(
            self.tr('Re-Merge'), self.__HgReMerge)
        self.vcsDirMultiMenuActions.append(act)
        menu.addSeparator()
        menu.addAction(self.tr('Select all local file entries'),
                       self.browser.selectLocalEntries)
        menu.addAction(self.tr('Select all versioned file entries'),
                       self.browser.selectVCSEntries)
        menu.addAction(self.tr('Select all local directory entries'),
                       self.browser.selectLocalDirEntries)
        menu.addAction(self.tr('Select all versioned directory entries'),
                       self.browser.selectVCSDirEntries)
        menu.addSeparator()
        menu.addAction(self.tr("Configure..."), self.__HgConfigure)
        
        mainMenu.addSeparator()
        mainMenu.addMenu(menu)
        self.menuDirMulti = menu
    
    ###########################################################################
    ## Menu handling methods below
    ###########################################################################
    
    def __HgRevert(self):
        """
        Private slot called by the context menu to revert changes made.
        """
        names = []
        for itm in self.browser.getSelectedItems():
            try:
                name = itm.fileName()
            except AttributeError:
                name = itm.dirName()
            names.append(name)
        self.vcs.hgRevert(names)
    
    def __HgCopy(self):
        """
        Private slot called by the context menu to copy the selected file.
        """
        itm = self.browser.currentItem()
        try:
            fn = itm.fileName()
        except AttributeError:
            fn = itm.dirName()
        self.vcs.hgCopy(fn, self.project)
    
    def __HgMove(self):
        """
        Private slot called by the context menu to move the selected file.
        """
        itm = self.browser.currentItem()
        try:
            fn = itm.fileName()
        except AttributeError:
            fn = itm.dirName()
        isFile = os.path.isfile(fn)
        movefiles = self.browser.project.getFiles(fn)
        if self.vcs.vcsMove(fn, self.project):
            if isFile:
                self.browser.closeSourceWindow.emit(fn)
            else:
                for mf in movefiles:
                    self.browser.closeSourceWindow.emit(mf)
    
    def __HgExtendedDiff(self):
        """
        Private slot called by the context menu to show the difference of a
        file to the repository.
        
        This gives the chance to enter the revisions to compare.
        """
        names = []
        for itm in self.browser.getSelectedItems():
            try:
                names.append(itm.fileName())
            except AttributeError:
                names.append(itm.dirName())
        self.vcs.hgExtendedDiff(names)
    
    def __HgSbsDiff(self):
        """
        Private slot called by the context menu to show the difference of a
        file to the repository side-by-side.
        """
        itm = self.browser.currentItem()
        fn = itm.fileName()
        self.vcs.hgSbsDiff(fn)
    
    def __HgSbsExtendedDiff(self):
        """
        Private slot called by the context menu to show the difference of a
        file to the repository side-by-side.
       
        It allows the selection of revisions to compare.
        """
        itm = self.browser.currentItem()
        fn = itm.fileName()
        self.vcs.hgSbsDiff(fn, extended=True)
    
    def __HgAnnotate(self):
        """
        Private slot called by the context menu to show the annotations of a
        file.
        """
        itm = self.browser.currentItem()
        fn = itm.fileName()
        self.vcs.hgAnnotate(fn)
    
    def __HgResolved(self):
        """
        Private slot called by the context menu to mark conflicts of a file
        as being resolved.
        """
        names = []
        for itm in self.browser.getSelectedItems():
            try:
                names.append(itm.fileName())
            except AttributeError:
                names.append(itm.dirName())
        self.vcs.hgResolved(names)
    
    def __HgUnresolved(self):
        """
        Private slot called by the context menu to mark conflicts of a file
        as being unresolved.
        """
        names = []
        for itm in self.browser.getSelectedItems():
            try:
                names.append(itm.fileName())
            except AttributeError:
                names.append(itm.dirName())
        self.vcs.hgResolved(names, unresolve=True)
    
    def __HgReMerge(self):
        """
        Private slot called by the context menu to re-merge a file.
        """
        names = []
        for itm in self.browser.getSelectedItems():
            try:
                names.append(itm.fileName())
            except AttributeError:
                names.append(itm.dirName())
        self.vcs.hgReMerge(names)
    
    def __HgForget(self):
        """
        Private slot called by the context menu to remove the selected file
        from the Mercurial repository leaving a copy in the project directory.
        """
        from UI.DeleteFilesConfirmationDialog import \
            DeleteFilesConfirmationDialog
        if self.isTranslationsBrowser:
            items = self.browser.getSelectedItems([ProjectBrowserFileItem])
            names = [itm.fileName() for itm in items]
            
            dlg = DeleteFilesConfirmationDialog(
                self.parent(),
                self.tr("Remove from repository only"),
                self.tr(
                    "Do you really want to remove these files"
                    " from the repository?"),
                names)
        else:
            items = self.browser.getSelectedItems()
            names = [itm.fileName() for itm in items]
            files = [self.browser.project.getRelativePath(name)
                     for name in names]
            
            dlg = DeleteFilesConfirmationDialog(
                self.parent(),
                self.tr("Remove from repository only"),
                self.tr(
                    "Do you really want to remove these files"
                    " from the repository?"),
                files)
        
        if dlg.exec_() == QDialog.Accepted:
            self.vcs.hgForget(names)
        
        for fn in names:
            self._updateVCSStatus(fn)
    
    def __HgConfigure(self):
        """
        Private method to open the configuration dialog.
        """
        e5App().getObject("UserInterface")\
            .showPreferences("zzz_mercurialPage")
