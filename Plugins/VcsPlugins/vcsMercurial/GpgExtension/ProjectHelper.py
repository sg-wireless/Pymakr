# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the gpg extension project helper.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QMenu

from E5Gui.E5Action import E5Action

from ..HgExtensionProjectHelper import HgExtensionProjectHelper

import UI.PixmapCache


class GpgProjectHelper(HgExtensionProjectHelper):
    """
    Class implementing the gpg extension project helper.
    """
    def __init__(self):
        """
        Constructor
        """
        super(GpgProjectHelper, self).__init__()
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.hgGpgListAct = E5Action(
            self.tr('List Signed Changesets'),
            UI.PixmapCache.getIcon("changesetSignList.png"),
            self.tr('List Signed Changesets...'),
            0, 0, self, 'mercurial_gpg_list')
        self.hgGpgListAct.setStatusTip(self.tr(
            'List signed changesets'
        ))
        self.hgGpgListAct.setWhatsThis(self.tr(
            """<b>List Signed Changesets</b>"""
            """<p>This opens a dialog listing all signed changesets.</p>"""
        ))
        self.hgGpgListAct.triggered.connect(self.__hgGpgSignatures)
        self.actions.append(self.hgGpgListAct)
        
        self.hgGpgVerifyAct = E5Action(
            self.tr('Verify Signatures'),
            UI.PixmapCache.getIcon("changesetSignVerify.png"),
            self.tr('Verify Signatures'),
            0, 0, self, 'mercurial_gpg_verify')
        self.hgGpgVerifyAct.setStatusTip(self.tr(
            'Verify all signatures there may be for a particular revision'
        ))
        self.hgGpgVerifyAct.setWhatsThis(self.tr(
            """<b>Verify Signatures</b>"""
            """<p>This verifies all signatures there may be for a particular"""
            """ revision.</p>"""
        ))
        self.hgGpgVerifyAct.triggered.connect(self.__hgGpgVerifySignatures)
        self.actions.append(self.hgGpgVerifyAct)
        
        self.hgGpgSignAct = E5Action(
            self.tr('Sign Revision'),
            UI.PixmapCache.getIcon("changesetSign.png"),
            self.tr('Sign Revision'),
            0, 0, self, 'mercurial_gpg_sign')
        self.hgGpgSignAct.setStatusTip(self.tr(
            'Add a signature for a selected revision'
        ))
        self.hgGpgSignAct.setWhatsThis(self.tr(
            """<b>Sign Revision</b>"""
            """<p>This adds a signature for a selected revision.</p>"""
        ))
        self.hgGpgSignAct.triggered.connect(self.__hgGpgSign)
        self.actions.append(self.hgGpgSignAct)
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the extension menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.menuTitle(), mainMenu)
        menu.setIcon(UI.PixmapCache.getIcon("changesetSign.png"))
        menu.setTearOffEnabled(True)
        
        menu.addAction(self.hgGpgListAct)
        menu.addAction(self.hgGpgVerifyAct)
        menu.addAction(self.hgGpgSignAct)
        
        return menu
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        
        @return title of the menu (string)
        """
        return self.tr("GPG")
    
    def __hgGpgSignatures(self):
        """
        Private slot used to list all signed changesets.
        """
        self.vcs.getExtensionObject("gpg")\
            .hgGpgSignatures(self.project.getProjectPath())
    
    def __hgGpgVerifySignatures(self):
        """
        Private slot used to verify the signatures of a revision.
        """
        self.vcs.getExtensionObject("gpg")\
            .hgGpgVerifySignatures(self.project.getProjectPath())
    
    def __hgGpgSign(self):
        """
        Private slot used to sign a revision.
        """
        self.vcs.getExtensionObject("gpg")\
            .hgGpgSign(self.project.getProjectPath())
