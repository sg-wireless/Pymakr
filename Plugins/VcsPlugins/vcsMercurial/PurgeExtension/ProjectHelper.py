# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the purge extension project helper.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QMenu

from E5Gui.E5Action import E5Action

from ..HgExtensionProjectHelper import HgExtensionProjectHelper

import UI.PixmapCache


class PurgeProjectHelper(HgExtensionProjectHelper):
    """
    Class implementing the purge extension project helper.
    """
    def __init__(self):
        """
        Constructor
        """
        super(PurgeProjectHelper, self).__init__()
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.hgPurgeAct = E5Action(
            self.tr('Purge Files'),
            UI.PixmapCache.getIcon("fileDelete.png"),
            self.tr('Purge Files'),
            0, 0, self, 'mercurial_purge')
        self.hgPurgeAct.setStatusTip(self.tr(
            'Delete files and directories not known to Mercurial'
        ))
        self.hgPurgeAct.setWhatsThis(self.tr(
            """<b>Purge Files</b>"""
            """<p>This deletes files and directories not known to Mercurial."""
            """ That means that purge will delete:<ul>"""
            """<li>unknown files (marked with "not tracked" in the status"""
            """ dialog)</li>"""
            """<li>empty directories</li>"""
            """</ul>Note that ignored files will be left untouched.</p>"""
        ))
        self.hgPurgeAct.triggered.connect(self.__hgPurge)
        self.actions.append(self.hgPurgeAct)
        
        self.hgPurgeAllAct = E5Action(
            self.tr('Purge All Files'),
            self.tr('Purge All Files'),
            0, 0, self, 'mercurial_purge_all')
        self.hgPurgeAllAct.setStatusTip(self.tr(
            'Delete files and directories not known to Mercurial including'
            ' ignored ones'
        ))
        self.hgPurgeAllAct.setWhatsThis(self.tr(
            """<b>Purge All Files</b>"""
            """<p>This deletes files and directories not known to Mercurial."""
            """ That means that purge will delete:<ul>"""
            """<li>unknown files (marked with "not tracked" in the status"""
            """ dialog)</li>"""
            """<li>empty directories</li>"""
            """<li>ignored files and directories</li>"""
            """</ul></p>"""
        ))
        self.hgPurgeAllAct.triggered.connect(self.__hgPurgeAll)
        self.actions.append(self.hgPurgeAllAct)
        
        self.hgPurgeListAct = E5Action(
            self.tr('List Files to be Purged'),
            UI.PixmapCache.getIcon("fileDeleteList.png"),
            self.tr('List Files to be Purged...'),
            0, 0, self, 'mercurial_purge_list')
        self.hgPurgeListAct.setStatusTip(self.tr(
            'List files and directories not known to Mercurial'
        ))
        self.hgPurgeListAct.setWhatsThis(self.tr(
            """<b>List Files to be Purged</b>"""
            """<p>This lists files and directories not known to Mercurial."""
            """ These would be deleted by the "Purge Files" menu entry.</p>"""
        ))
        self.hgPurgeListAct.triggered.connect(self.__hgPurgeList)
        self.actions.append(self.hgPurgeListAct)
        
        self.hgPurgeAllListAct = E5Action(
            self.tr('List All Files to be Purged'),
            self.tr('List All Files to be Purged...'),
            0, 0, self, 'mercurial_purge_all_list')
        self.hgPurgeAllListAct.setStatusTip(self.tr(
            'List files and directories not known to Mercurial including'
            ' ignored ones'
        ))
        self.hgPurgeAllListAct.setWhatsThis(self.tr(
            """<b>List All Files to be Purged</b>"""
            """<p>This lists files and directories not known to Mercurial"""
            """ including ignored ones. These would be deleted by the"""
            """ "Purge All Files" menu entry.</p>"""
        ))
        self.hgPurgeAllListAct.triggered.connect(self.__hgPurgeAllList)
        self.actions.append(self.hgPurgeAllListAct)
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the extension menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.menuTitle(), mainMenu)
        menu.setIcon(UI.PixmapCache.getIcon("fileDelete.png"))
        menu.setTearOffEnabled(True)
        
        menu.addAction(self.hgPurgeAct)
        menu.addAction(self.hgPurgeAllAct)
        menu.addSeparator()
        menu.addAction(self.hgPurgeListAct)
        menu.addAction(self.hgPurgeAllListAct)
        
        return menu
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        
        @return title of the menu (string)
        """
        return self.tr("Purge")
    
    def __hgPurge(self):
        """
        Private slot used to remove files not tracked by Mercurial.
        """
        self.vcs.getExtensionObject("purge")\
            .hgPurge(self.project.getProjectPath(), all=False)
    
    def __hgPurgeAll(self):
        """
        Private slot used to remove all files not tracked by Mercurial.
        """
        self.vcs.getExtensionObject("purge")\
            .hgPurge(self.project.getProjectPath(), all=True)
    
    def __hgPurgeList(self):
        """
        Private slot used to list files not tracked by Mercurial.
        """
        self.vcs.getExtensionObject("purge")\
            .hgPurgeList(self.project.getProjectPath(), all=False)
    
    def __hgPurgeAllList(self):
        """
        Private slot used to list all files not tracked by Mercurial.
        """
        self.vcs.getExtensionObject("purge")\
            .hgPurgeList(self.project.getProjectPath(), all=True)
