# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the shelve extension project helper.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QMenu

from E5Gui.E5Action import E5Action

from ..HgExtensionProjectHelper import HgExtensionProjectHelper

import UI.PixmapCache


class LargefilesProjectHelper(HgExtensionProjectHelper):
    """
    Class implementing the queues extension project helper.
    """
    def __init__(self):
        """
        Constructor
        """
        super(LargefilesProjectHelper, self).__init__()
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.hgConvertToLargefilesAct = E5Action(
            self.tr('Convert repository to largefiles'),
            self.tr('Convert repository to largefiles...'),
            0, 0, self, 'mercurial_convert_to_largefiles')
        self.hgConvertToLargefilesAct.setStatusTip(self.tr(
            'Convert the repository of the project to a largefiles repository.'
        ))
        self.hgConvertToLargefilesAct.setWhatsThis(self.tr(
            """<b>Convert repository to largefiles</b>"""
            """<p>This converts the repository of the project to a"""
            """ largefiles repository. A new project  is created. The"""
            """ current one is kept as a backup.</p>"""
        ))
        self.hgConvertToLargefilesAct.triggered.connect(
            lambda: self.__hgLfconvert("largefiles"))
        self.actions.append(self.hgConvertToLargefilesAct)
        
        self.hgConvertToNormalAct = E5Action(
            self.tr('Convert repository to normal'),
            self.tr('Convert repository to normal...'),
            0, 0, self, 'mercurial_convert_to_normal')
        self.hgConvertToNormalAct.setStatusTip(self.tr(
            'Convert the repository of the project to a normal repository.'
        ))
        self.hgConvertToNormalAct.setWhatsThis(self.tr(
            """<b>Convert repository to normal</b>"""
            """<p>This converts the repository of the project to a"""
            """ normal repository. A new project is created. The current"""
            """ one is kept as a backup.</p>"""
        ))
        self.hgConvertToNormalAct.triggered.connect(
            lambda: self.__hgLfconvert("normal"))
        self.actions.append(self.hgConvertToNormalAct)
        
        self.hgLfPullAct = E5Action(
            self.tr('Pull Large Files'),
            UI.PixmapCache.getIcon("vcsUpdate.png"),
            self.tr('Pull Large Files'),
            0, 0, self, 'mercurial_pull_largefiles')
        self.hgLfPullAct.setStatusTip(self.tr(
            'Pull large files from a remote repository'
        ))
        self.hgLfPullAct.setWhatsThis(self.tr(
            """<b>Pull Large Files</b>"""
            """<p>This pulls missing large files from a remote repository"""
            """ into the local repository.</p>"""
        ))
        self.hgLfPullAct.triggered.connect(self.__hgLfPull)
        self.actions.append(self.hgLfPullAct)
        
        self.hgLfSummaryAct = E5Action(
            self.tr('Show Summary'),
            UI.PixmapCache.getIcon("vcsSummary.png"),
            self.tr('Show summary...'),
            0, 0, self, 'mercurial_summary_largefiles')
        self.hgLfSummaryAct.setStatusTip(self.tr(
            'Show summary information of the working directory status'
        ))
        self.hgLfSummaryAct.setWhatsThis(self.tr(
            """<b>Show summary</b>"""
            """<p>This shows some summary information of the working"""
            """ directory status.</p>"""
        ))
        self.hgLfSummaryAct.triggered.connect(self.__hgLfSummary)
        self.actions.append(self.hgLfSummaryAct)
        
        self.hgVerifyLargeAct = E5Action(
            self.tr('Verify large files of current revision'),
            self.tr('Verify large files of current revision...'),
            0, 0, self, 'mercurial_verify_large')
        self.hgVerifyLargeAct.setStatusTip(self.tr(
            'Verify that all large files in the current revision exist'
        ))
        self.hgVerifyLargeAct.setWhatsThis(self.tr(
            """<b>Verify large files of current revision</b>"""
            """<p>This verifies that all large files in the current"""
            """ revision exist.</p>"""
        ))
        self.hgVerifyLargeAct.triggered.connect(
            lambda: self.__hgLfVerify("large"))
        self.actions.append(self.hgVerifyLargeAct)
        
        self.hgVerifyLfaAct = E5Action(
            self.tr('Verify large files of all revision'),
            self.tr('Verify large files of all revision...'),
            0, 0, self, 'mercurial_verify_lfa')
        self.hgVerifyLfaAct.setStatusTip(self.tr(
            'Verify that all large files in all revisions exist'
        ))
        self.hgVerifyLfaAct.setWhatsThis(self.tr(
            """<b>Verify large files of all revision</b>"""
            """<p>This verifies that all large files in all"""
            """ revisions exist.</p>"""
        ))
        self.hgVerifyLfaAct.triggered.connect(
            lambda: self.__hgLfVerify("lfa"))
        self.actions.append(self.hgVerifyLfaAct)
        
        self.hgVerifyLfcAct = E5Action(
            self.tr('Verify large files contents'),
            self.tr('Verify large files contents...'),
            0, 0, self, 'mercurial_verify_lfc')
        self.hgVerifyLfcAct.setStatusTip(self.tr(
            'Verify the contents of all large files'
        ))
        self.hgVerifyLfcAct.setWhatsThis(self.tr(
            """<b>Verify large files contents</b>"""
            """<p>This verifies the contents of all large files.</p>"""
        ))
        self.hgVerifyLfcAct.triggered.connect(
            lambda: self.__hgLfVerify("lfc"))
        self.actions.append(self.hgVerifyLfcAct)
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the extension menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.menuTitle(), mainMenu)
        menu.setTearOffEnabled(True)
        
        self.__adminMenu = QMenu(self.tr("Administration"), menu)
        self.__adminMenu.setTearOffEnabled(True)
        self.__adminMenu.addAction(self.hgVerifyLargeAct)
        self.__adminMenu.addAction(self.hgVerifyLfaAct)
        self.__adminMenu.addAction(self.hgVerifyLfcAct)
        
        menu.addAction(self.hgConvertToLargefilesAct)
        menu.addAction(self.hgConvertToNormalAct)
        menu.addSeparator()
        menu.addAction(self.hgLfPullAct)
        menu.addSeparator()
        menu.addAction(self.hgLfSummaryAct)
        menu.addSeparator()
        menu.addMenu(self.__adminMenu)
        
        return menu
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        
        @return title of the menu (string)
        """
        return self.tr("Large Files")
    
    def shutdown(self):
        """
        Public method to perform shutdown actions.
        
        Note: Derived class may implement this method if needed.
        """
        if self.__adminMenu.isTearOffMenuVisible():
            self.__adminMenu.hideTearOffMenu()
    
    def __hgLfconvert(self, direction):
        """
        Private slot to convert the repository format of the current project.
        
        @param direction direction of the conversion (string; one of
            'largefiles' or 'normal')
        """
        assert direction in ["largefiles", "normal"]
        
        self.vcs.getExtensionObject("largefiles").hgLfconvert(
            direction, self.project.getProjectFile())
    
    def __hgLfPull(self):
        """
        Private slot to pull missing large files into the local repository.
        """
        self.vcs.getExtensionObject("largefiles").hgLfPull(
            self.project.getProjectPath())
    
    def __hgLfSummary(self):
        """
        Private slot to show a working directory summary.
        """
        self.vcs.hgSummary(largefiles=True)
    
    def __hgLfVerify(self, mode):
        """
        Private slot to verify large files integrity.
        
        @param mode verify mode (string; one of 'large', 'lfa' or 'lfc')
        """
        assert mode in ['large', 'lfa', 'lfc']
        
        self.vcs.getExtensionObject("largefiles").hgLfVerify(
            self.project.getProjectPath(), mode)
