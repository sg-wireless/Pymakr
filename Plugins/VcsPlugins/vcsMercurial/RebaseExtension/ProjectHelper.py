# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the rebase extension project helper.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QMenu

from E5Gui.E5Action import E5Action
from E5Gui import E5MessageBox

from ..HgExtensionProjectHelper import HgExtensionProjectHelper

import UI.PixmapCache


class RebaseProjectHelper(HgExtensionProjectHelper):
    """
    Class implementing the rebase extension project helper.
    """
    def __init__(self):
        """
        Constructor
        """
        super(RebaseProjectHelper, self).__init__()
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.hgRebaseAct = E5Action(
            self.tr('Rebase Changesets'),
            UI.PixmapCache.getIcon("vcsRebase.png"),
            self.tr('Rebase Changesets'),
            0, 0, self, 'mercurial_rebase')
        self.hgRebaseAct.setStatusTip(self.tr(
            'Rebase changesets to another branch'
        ))
        self.hgRebaseAct.setWhatsThis(self.tr(
            """<b>Rebase Changesets</b>"""
            """<p>This rebases changesets to another branch.</p>"""
        ))
        self.hgRebaseAct.triggered.connect(self.__hgRebase)
        self.actions.append(self.hgRebaseAct)
        
        self.hgRebaseContinueAct = E5Action(
            self.tr('Continue Rebase Session'),
            self.tr('Continue Rebase Session'),
            0, 0, self, 'mercurial_rebase_continue')
        self.hgRebaseContinueAct.setStatusTip(self.tr(
            'Continue the last rebase session after repair'
        ))
        self.hgRebaseContinueAct.setWhatsThis(self.tr(
            """<b>Continue Rebase Session</b>"""
            """<p>This continues the last rebase session after repair.</p>"""
        ))
        self.hgRebaseContinueAct.triggered.connect(self.__hgRebaseContinue)
        self.actions.append(self.hgRebaseContinueAct)
        
        self.hgRebaseAbortAct = E5Action(
            self.tr('Abort Rebase Session'),
            self.tr('Abort Rebase Session'),
            0, 0, self, 'mercurial_rebase_abort')
        self.hgRebaseAbortAct.setStatusTip(self.tr(
            'Abort the last rebase session'
        ))
        self.hgRebaseAbortAct.setWhatsThis(self.tr(
            """<b>Abort Rebase Session</b>"""
            """<p>This aborts the last rebase session.</p>"""
        ))
        self.hgRebaseAbortAct.triggered.connect(self.__hgRebaseAbort)
        self.actions.append(self.hgRebaseAbortAct)
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the extension menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.menuTitle(), mainMenu)
        menu.setIcon(UI.PixmapCache.getIcon("vcsRebase.png"))
        menu.setTearOffEnabled(True)
        
        menu.addAction(self.hgRebaseAct)
        menu.addAction(self.hgRebaseContinueAct)
        menu.addAction(self.hgRebaseAbortAct)
        
        return menu
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        
        @return title of the menu (string)
        """
        return self.tr("Rebase")
    
    def __hgRebase(self):
        """
        Private slot used to rebase changesets to another branch.
        """
        shouldReopen = self.vcs.getExtensionObject("rebase")\
            .hgRebase(self.project.getProjectPath())
        if shouldReopen:
            res = E5MessageBox.yesNo(
                None,
                self.tr("Rebase Changesets"),
                self.tr("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgRebaseContinue(self):
        """
        Private slot used to continue the last rebase session after repair.
        """
        shouldReopen = self.vcs.getExtensionObject("rebase")\
            .hgRebaseContinue(self.project.getProjectPath())
        if shouldReopen:
            res = E5MessageBox.yesNo(
                None,
                self.tr("Rebase Changesets (Continue)"),
                self.tr("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgRebaseAbort(self):
        """
        Private slot used to abort the last rebase session.
        """
        shouldReopen = self.vcs.getExtensionObject("rebase")\
            .hgRebaseAbort(self.project.getProjectPath())
        if shouldReopen:
            res = E5MessageBox.yesNo(
                None,
                self.tr("Rebase Changesets (Abort)"),
                self.tr("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
