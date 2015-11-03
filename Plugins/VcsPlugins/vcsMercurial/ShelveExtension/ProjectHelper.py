# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the shelve extension project helper.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QMenu

from E5Gui.E5Action import E5Action
from E5Gui import E5MessageBox

from ..HgExtensionProjectHelper import HgExtensionProjectHelper


class ShelveProjectHelper(HgExtensionProjectHelper):
    """
    Class implementing the shelve extension project helper.
    """
    def __init__(self):
        """
        Constructor
        """
        super(ShelveProjectHelper, self).__init__()
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.hgShelveAct = E5Action(
            self.tr('Shelve changes'),
            self.tr('Shelve changes...'),
            0, 0, self, 'mercurial_shelve')
        self.hgShelveAct.setStatusTip(self.tr(
            'Shelve all current changes of the project'
        ))
        self.hgShelveAct.setWhatsThis(self.tr(
            """<b>Shelve changes</b>"""
            """<p>This shelves all current changes of the project.</p>"""
        ))
        self.hgShelveAct.triggered.connect(self.__hgShelve)
        self.actions.append(self.hgShelveAct)
        
        self.hgShelveBrowserAct = E5Action(
            self.tr('Show shelve browser'),
            self.tr('Show shelve browser...'),
            0, 0, self, 'mercurial_shelve_browser')
        self.hgShelveBrowserAct.setStatusTip(self.tr(
            'Show a dialog with all shelves'
        ))
        self.hgShelveBrowserAct.setWhatsThis(self.tr(
            """<b>Show shelve browser...</b>"""
            """<p>This shows a dialog listing all available shelves."""
            """ Actions on these shelves may be executed via the"""
            """ context menu.</p>"""
        ))
        self.hgShelveBrowserAct.triggered.connect(
            self.__hgShelveBrowser)
        self.actions.append(self.hgShelveBrowserAct)
        
        self.hgUnshelveAct = E5Action(
            self.tr('Restore shelved change'),
            self.tr('Restore shelved change...'),
            0, 0, self, 'mercurial_unshelve')
        self.hgUnshelveAct.setStatusTip(self.tr(
            'Restore a shelved change to the project directory'
        ))
        self.hgUnshelveAct.setWhatsThis(self.tr(
            """<b>Restore shelved change</b>"""
            """<p>This restore a shelved change to the project directory."""
            """</p>"""
        ))
        self.hgUnshelveAct.triggered.connect(self.__hgUnshelve)
        self.actions.append(self.hgUnshelveAct)
        
        self.hgUnshelveAbortAct = E5Action(
            self.tr('Abort restore'),
            self.tr('Abort restore...'),
            0, 0, self, 'mercurial_unshelve_abort')
        self.hgUnshelveAbortAct.setStatusTip(self.tr(
            'Abort the restore operation in progress'
        ))
        self.hgUnshelveAbortAct.setWhatsThis(self.tr(
            """<b>Abort restore</b>"""
            """<p>This aborts the restore operation in progress and reverts"""
            """ already applied changes.</p>"""
        ))
        self.hgUnshelveAbortAct.triggered.connect(self.__hgUnshelveAbort)
        self.actions.append(self.hgUnshelveAbortAct)
        
        self.hgUnshelveContinueAct = E5Action(
            self.tr('Continue restore'),
            self.tr('Continue restore...'),
            0, 0, self, 'mercurial_unshelve_continue')
        self.hgUnshelveContinueAct.setStatusTip(self.tr(
            'Continue the restore operation in progress'
        ))
        self.hgUnshelveContinueAct.setWhatsThis(self.tr(
            """<b>Continue restore</b>"""
            """<p>This continues the restore operation in progress.</p>"""
        ))
        self.hgUnshelveContinueAct.triggered.connect(
            self.__hgUnshelveContinue)
        self.actions.append(self.hgUnshelveContinueAct)
        
        self.hgShelveDeleteAct = E5Action(
            self.tr('Delete shelved changes'),
            self.tr('Delete shelved changes...'),
            0, 0, self, 'mercurial_shelve_delete')
        self.hgShelveDeleteAct.setWhatsThis(self.tr(
            """<b>Delete shelved changes...</b>"""
            """<p>This opens a dialog to select the shelved changes to"""
            """ delete and deletes the selected ones.</p>"""
        ))
        self.hgShelveDeleteAct.triggered.connect(
            self.__hgDeleteShelves)
        self.actions.append(self.hgShelveDeleteAct)
        
        self.hgShelveCleanupAct = E5Action(
            self.tr('Delete ALL shelved changes'),
            self.tr('Delete ALL shelved changes'),
            0, 0, self, 'mercurial_shelve_cleanup')
        self.hgShelveCleanupAct.setWhatsThis(self.tr(
            """<b>Delete ALL shelved changes</b>"""
            """<p>This deletes all shelved changes.</p>"""
        ))
        self.hgShelveCleanupAct.triggered.connect(
            self.__hgCleanupShelves)
        self.actions.append(self.hgShelveCleanupAct)
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the extension menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.menuTitle(), mainMenu)
        menu.setTearOffEnabled(True)
        
        menu.addAction(self.hgShelveAct)
        menu.addSeparator()
        menu.addAction(self.hgShelveBrowserAct)
        menu.addSeparator()
        menu.addAction(self.hgUnshelveAct)
        menu.addAction(self.hgUnshelveContinueAct)
        menu.addAction(self.hgUnshelveAbortAct)
        menu.addSeparator()
        menu.addAction(self.hgShelveDeleteAct)
        menu.addAction(self.hgShelveCleanupAct)
        
        return menu
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        
        @return title of the menu (string)
        """
        return self.tr("Shelve")
    
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
        shouldReopen = self.vcs.getExtensionObject("shelve")\
            .hgShelve(self.project.getProjectPath())
        self.__reopenProject(shouldReopen, self.tr("Shelve"))
    
    def __hgShelveBrowser(self):
        """
        Private slot to show the shelve browser dialog.
        """
        self.vcs.getExtensionObject("shelve")\
            .hgShelveBrowser(self.project.getProjectPath())
    
    def __hgUnshelve(self):
        """
        Private slot used to restore a shelved change.
        """
        shouldReopen = self.vcs.getExtensionObject("shelve")\
            .hgUnshelve(self.project.getProjectPath())
        self.__reopenProject(shouldReopen, self.tr("Unshelve"))
    
    def __hgUnshelveAbort(self):
        """
        Private slot used to abort an ongoing restore operation.
        """
        shouldReopen = self.vcs.getExtensionObject("shelve")\
            .hgUnshelveAbort(self.project.getProjectPath())
        self.__reopenProject(shouldReopen, self.tr("Abort Unshelve"))
    
    def __hgUnshelveContinue(self):
        """
        Private slot used to continue an ongoing restore operation.
        """
        shouldReopen = self.vcs.getExtensionObject("shelve")\
            .hgUnshelveContinue(self.project.getProjectPath())
        self.__reopenProject(shouldReopen, self.tr("Continue Unshelve"))
    
    def __hgDeleteShelves(self):
        """
        Private slot to delete selected shelves.
        """
        self.vcs.getExtensionObject("shelve").hgDeleteShelves(
            self.project.getProjectPath())
    
    def __hgCleanupShelves(self):
        """
        Private slot to delete all shelves.
        """
        self.vcs.getExtensionObject("shelve").hgCleanupShelves(
            self.project.getProjectPath())
