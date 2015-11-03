# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the transplant extension project helper.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QMenu

from E5Gui.E5Action import E5Action
from E5Gui import E5MessageBox

from ..HgExtensionProjectHelper import HgExtensionProjectHelper

import UI.PixmapCache


class TransplantProjectHelper(HgExtensionProjectHelper):
    """
    Class implementing the transplant extension project helper.
    """
    def __init__(self):
        """
        Constructor
        """
        super(TransplantProjectHelper, self).__init__()
    
    def setObjects(self, vcsObject, projectObject):
        """
        Public method to set references to the vcs and project objects.
        
        @param vcsObject reference to the vcs object
        @param projectObject reference to the project object
        """
        super(TransplantProjectHelper, self).setObjects(
            vcsObject, projectObject)
        
        if self.vcs.version >= (2, 3):
            # transplant is deprecated as of Mercurial 2.3
            for act in self.actions:
                act.setEnabled(False)
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.hgTransplantAct = E5Action(
            self.tr('Transplant Changesets'),
            UI.PixmapCache.getIcon("vcsTransplant.png"),
            self.tr('Transplant Changesets'),
            0, 0, self, 'mercurial_transplant')
        self.hgTransplantAct.setStatusTip(self.tr(
            'Transplant changesets from another branch'
        ))
        self.hgTransplantAct.setWhatsThis(self.tr(
            """<b>Transplant Changesets</b>"""
            """<p>This transplants changesets from another branch on top"""
            """ of the current working directory with the log of the"""
            """ original changeset.</p>"""
        ))
        self.hgTransplantAct.triggered.connect(self.__hgTransplant)
        self.actions.append(self.hgTransplantAct)
        
        self.hgTransplantContinueAct = E5Action(
            self.tr('Continue Transplant Session'),
            self.tr('Continue Transplant Session'),
            0, 0, self, 'mercurial_transplant_continue')
        self.hgTransplantContinueAct.setStatusTip(self.tr(
            'Continue the last transplant session after repair'
        ))
        self.hgTransplantContinueAct.setWhatsThis(self.tr(
            """<b>Continue Transplant Session</b>"""
            """<p>This continues the last transplant session after"""
            """ repair.</p>"""
        ))
        self.hgTransplantContinueAct.triggered.connect(
            self.__hgTransplantContinue)
        self.actions.append(self.hgTransplantContinueAct)
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the extension menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.menuTitle(), mainMenu)
        menu.setIcon(UI.PixmapCache.getIcon("vcsTransplant.png"))
        if self.vcs.version >= (2, 3):
            # transplant is deprecated as of Mercurial 2.3
            menu.addAction(
                self.tr("Transplant is deprecated")).setEnabled(False)
        else:
            menu.setTearOffEnabled(True)
            
            menu.addAction(self.hgTransplantAct)
            menu.addAction(self.hgTransplantContinueAct)
        
        return menu
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        
        @return title of the menu (string)
        """
        return self.tr("Transplant")
    
    def __hgTransplant(self):
        """
        Private slot used to transplant changesets from another branch.
        """
        shouldReopen = self.vcs.getExtensionObject("transplant")\
            .hgTransplant(self.project.getProjectPath())
        if shouldReopen:
            res = E5MessageBox.yesNo(
                None,
                self.tr("Transplant Changesets"),
                self.tr("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgTransplantContinue(self):
        """
        Private slot used to continue the last transplant session after repair.
        """
        shouldReopen = self.vcs.getExtensionObject("transplant")\
            .hgTransplantContinue(self.project.getProjectPath())
        if shouldReopen:
            res = E5MessageBox.yesNo(
                None,
                self.tr("Transplant Changesets (Continue)"),
                self.tr("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
