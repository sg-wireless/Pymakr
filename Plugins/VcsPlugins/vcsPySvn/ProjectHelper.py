# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the VCS project helper for Subversion.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtWidgets import QToolBar

from VCS.ProjectHelper import VcsProjectHelper

from E5Gui.E5Action import E5Action
from E5Gui.E5Application import e5App

import UI.PixmapCache


class PySvnProjectHelper(VcsProjectHelper):
    """
    Class implementing the VCS project helper for Subversion.
    """
    def __init__(self, vcsObject, projectObject, parent=None, name=None):
        """
        Constructor
        
        @param vcsObject reference to the vcs object
        @param projectObject reference to the project object
        @param parent parent widget (QWidget)
        @param name name of this object (string)
        """
        VcsProjectHelper.__init__(self, vcsObject, projectObject, parent, name)
    
    def getActions(self):
        """
        Public method to get a list of all actions.
        
        @return list of all actions (list of E5Action)
        """
        return self.actions[:]
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.vcsNewAct = E5Action(
            self.tr('New from repository'),
            UI.PixmapCache.getIcon("vcsCheckout.png"),
            self.tr('&New from repository...'), 0, 0, self,
            'pysvn_new')
        self.vcsNewAct.setStatusTip(self.tr(
            'Create a new project from the VCS repository'
        ))
        self.vcsNewAct.setWhatsThis(self.tr(
            """<b>New from repository</b>"""
            """<p>This creates a new local project from the VCS"""
            """ repository.</p>"""
        ))
        self.vcsNewAct.triggered.connect(self._vcsCheckout)
        self.actions.append(self.vcsNewAct)
        
        self.vcsUpdateAct = E5Action(
            self.tr('Update from repository'),
            UI.PixmapCache.getIcon("vcsUpdate.png"),
            self.tr('&Update from repository'), 0, 0, self,
            'pysvn_update')
        self.vcsUpdateAct.setStatusTip(self.tr(
            'Update the local project from the VCS repository'
        ))
        self.vcsUpdateAct.setWhatsThis(self.tr(
            """<b>Update from repository</b>"""
            """<p>This updates the local project from the VCS"""
            """ repository.</p>"""
        ))
        self.vcsUpdateAct.triggered.connect(self._vcsUpdate)
        self.actions.append(self.vcsUpdateAct)
        
        self.vcsCommitAct = E5Action(
            self.tr('Commit changes to repository'),
            UI.PixmapCache.getIcon("vcsCommit.png"),
            self.tr('&Commit changes to repository...'), 0, 0, self,
            'pysvn_commit')
        self.vcsCommitAct.setStatusTip(self.tr(
            'Commit changes to the local project to the VCS repository'
        ))
        self.vcsCommitAct.setWhatsThis(self.tr(
            """<b>Commit changes to repository</b>"""
            """<p>This commits changes to the local project to the VCS"""
            """ repository.</p>"""
        ))
        self.vcsCommitAct.triggered.connect(self._vcsCommit)
        self.actions.append(self.vcsCommitAct)
        
        self.vcsLogAct = E5Action(
            self.tr('Show log'),
            UI.PixmapCache.getIcon("vcsLog.png"),
            self.tr('Show &log'),
            0, 0, self, 'pysvn_log')
        self.vcsLogAct.setStatusTip(self.tr(
            'Show the log of the local project'
        ))
        self.vcsLogAct.setWhatsThis(self.tr(
            """<b>Show log</b>"""
            """<p>This shows the log of the local project.</p>"""
        ))
        self.vcsLogAct.triggered.connect(self._vcsLog)
        self.actions.append(self.vcsLogAct)
        
        self.svnLogBrowserAct = E5Action(
            self.tr('Show log browser'),
            UI.PixmapCache.getIcon("vcsLog.png"),
            self.tr('Show log browser'),
            0, 0, self, 'pysvn_log_browser')
        self.svnLogBrowserAct.setStatusTip(self.tr(
            'Show a dialog to browse the log of the local project'
        ))
        self.svnLogBrowserAct.setWhatsThis(self.tr(
            """<b>Show log browser</b>"""
            """<p>This shows a dialog to browse the log of the local"""
            """ project. A limited number of entries is shown first. More"""
            """ can be retrieved later on.</p>"""
        ))
        self.svnLogBrowserAct.triggered.connect(self._vcsLogBrowser)
        self.actions.append(self.svnLogBrowserAct)
        
        self.vcsDiffAct = E5Action(
            self.tr('Show differences'),
            UI.PixmapCache.getIcon("vcsDiff.png"),
            self.tr('Show &difference'),
            0, 0, self, 'pysvn_diff')
        self.vcsDiffAct.setStatusTip(self.tr(
            'Show the difference of the local project to the repository'
        ))
        self.vcsDiffAct.setWhatsThis(self.tr(
            """<b>Show differences</b>"""
            """<p>This shows differences of the local project to the"""
            """ repository.</p>"""
        ))
        self.vcsDiffAct.triggered.connect(self._vcsDiff)
        self.actions.append(self.vcsDiffAct)
        
        self.svnExtDiffAct = E5Action(
            self.tr('Show differences (extended)'),
            UI.PixmapCache.getIcon("vcsDiff.png"),
            self.tr('Show differences (extended)'),
            0, 0, self, 'pysvn_extendeddiff')
        self.svnExtDiffAct.setStatusTip(self.tr(
            'Show the difference of revisions of the project to the repository'
        ))
        self.svnExtDiffAct.setWhatsThis(self.tr(
            """<b>Show differences (extended)</b>"""
            """<p>This shows differences of selectable revisions of"""
            """ the project.</p>"""
        ))
        self.svnExtDiffAct.triggered.connect(self.__svnExtendedDiff)
        self.actions.append(self.svnExtDiffAct)
        
        self.svnUrlDiffAct = E5Action(
            self.tr('Show differences (URLs)'),
            UI.PixmapCache.getIcon("vcsDiff.png"),
            self.tr('Show differences (URLs)'),
            0, 0, self, 'pysvn_urldiff')
        self.svnUrlDiffAct.setStatusTip(self.tr(
            'Show the difference of the project between two repository URLs'
        ))
        self.svnUrlDiffAct.setWhatsThis(self.tr(
            """<b>Show differences (URLs)</b>"""
            """<p>This shows differences of the project between"""
            """ two repository URLs.</p>"""
        ))
        self.svnUrlDiffAct.triggered.connect(self.__svnUrlDiff)
        self.actions.append(self.svnUrlDiffAct)
        
        self.vcsStatusAct = E5Action(
            self.tr('Show status'),
            UI.PixmapCache.getIcon("vcsStatus.png"),
            self.tr('Show &status'),
            0, 0, self, 'pysvn_status')
        self.vcsStatusAct.setStatusTip(self.tr(
            'Show the status of the local project'
        ))
        self.vcsStatusAct.setWhatsThis(self.tr(
            """<b>Show status</b>"""
            """<p>This shows the status of the local project.</p>"""
        ))
        self.vcsStatusAct.triggered.connect(self._vcsStatus)
        self.actions.append(self.vcsStatusAct)
        
        self.svnChangeListsAct = E5Action(
            self.tr('Show change lists'),
            UI.PixmapCache.getIcon("vcsChangeLists.png"),
            self.tr('Show change lists'),
            0, 0, self, 'pysvn_changelists')
        self.svnChangeListsAct.setStatusTip(self.tr(
            'Show the change lists and associated files of the local project'
        ))
        self.svnChangeListsAct.setWhatsThis(self.tr(
            """<b>Show change lists</b>"""
            """<p>This shows the change lists and associated files of the"""
            """ local project.</p>"""
        ))
        self.svnChangeListsAct.triggered.connect(self.__svnChangeLists)
        self.actions.append(self.svnChangeListsAct)
        
        self.svnRepoInfoAct = E5Action(
            self.tr('Show repository info'),
            UI.PixmapCache.getIcon("vcsRepo.png"),
            self.tr('Show repository info'),
            0, 0, self, 'pysvn_repoinfo')
        self.svnRepoInfoAct.setStatusTip(self.tr(
            'Show some repository related information for the local project'
        ))
        self.svnRepoInfoAct.setWhatsThis(self.tr(
            """<b>Show repository info</b>"""
            """<p>This shows some repository related information for"""
            """ the local project.</p>"""
        ))
        self.svnRepoInfoAct.triggered.connect(self.__svnInfo)
        self.actions.append(self.svnRepoInfoAct)
        
        self.vcsTagAct = E5Action(
            self.tr('Tag in repository'),
            UI.PixmapCache.getIcon("vcsTag.png"),
            self.tr('&Tag in repository...'),
            0, 0, self, 'pysvn_tag')
        self.vcsTagAct.setStatusTip(self.tr(
            'Tag the local project in the repository'
        ))
        self.vcsTagAct.setWhatsThis(self.tr(
            """<b>Tag in repository</b>"""
            """<p>This tags the local project in the repository.</p>"""
        ))
        self.vcsTagAct.triggered.connect(self._vcsTag)
        self.actions.append(self.vcsTagAct)
        
        self.vcsExportAct = E5Action(
            self.tr('Export from repository'),
            UI.PixmapCache.getIcon("vcsExport.png"),
            self.tr('&Export from repository...'),
            0, 0, self, 'pysvn_export')
        self.vcsExportAct.setStatusTip(self.tr(
            'Export a project from the repository'
        ))
        self.vcsExportAct.setWhatsThis(self.tr(
            """<b>Export from repository</b>"""
            """<p>This exports a project from the repository.</p>"""
        ))
        self.vcsExportAct.triggered.connect(self._vcsExport)
        self.actions.append(self.vcsExportAct)
        
        self.vcsPropsAct = E5Action(
            self.tr('Command options'),
            self.tr('Command &options...'), 0, 0, self,
            'pysvn_options')
        self.vcsPropsAct.setStatusTip(self.tr(
            'Show the VCS command options'))
        self.vcsPropsAct.setWhatsThis(self.tr(
            """<b>Command options...</b>"""
            """<p>This shows a dialog to edit the VCS command options.</p>"""
        ))
        self.vcsPropsAct.triggered.connect(self._vcsCommandOptions)
        self.actions.append(self.vcsPropsAct)
        
        self.vcsRevertAct = E5Action(
            self.tr('Revert changes'),
            UI.PixmapCache.getIcon("vcsRevert.png"),
            self.tr('Re&vert changes'),
            0, 0, self, 'pysvn_revert')
        self.vcsRevertAct.setStatusTip(self.tr(
            'Revert all changes made to the local project'
        ))
        self.vcsRevertAct.setWhatsThis(self.tr(
            """<b>Revert changes</b>"""
            """<p>This reverts all changes made to the local project.</p>"""
        ))
        self.vcsRevertAct.triggered.connect(self._vcsRevert)
        self.actions.append(self.vcsRevertAct)
        
        self.vcsMergeAct = E5Action(
            self.tr('Merge'),
            UI.PixmapCache.getIcon("vcsMerge.png"),
            self.tr('Mer&ge changes...'),
            0, 0, self, 'pysvn_merge')
        self.vcsMergeAct.setStatusTip(self.tr(
            'Merge changes of a tag/revision into the local project'
        ))
        self.vcsMergeAct.setWhatsThis(self.tr(
            """<b>Merge</b>"""
            """<p>This merges changes of a tag/revision into the local"""
            """ project.</p>"""
        ))
        self.vcsMergeAct.triggered.connect(self._vcsMerge)
        self.actions.append(self.vcsMergeAct)
        
        self.vcsSwitchAct = E5Action(
            self.tr('Switch'),
            UI.PixmapCache.getIcon("vcsSwitch.png"),
            self.tr('S&witch...'),
            0, 0, self, 'pysvn_switch')
        self.vcsSwitchAct.setStatusTip(self.tr(
            'Switch the local copy to another tag/branch'
        ))
        self.vcsSwitchAct.setWhatsThis(self.tr(
            """<b>Switch</b>"""
            """<p>This switches the local copy to another tag/branch.</p>"""
        ))
        self.vcsSwitchAct.triggered.connect(self._vcsSwitch)
        self.actions.append(self.vcsSwitchAct)
        
        self.vcsResolveAct = E5Action(
            self.tr('Conflicts resolved'),
            self.tr('Con&flicts resolved'),
            0, 0, self, 'pysvn_resolve')
        self.vcsResolveAct.setStatusTip(self.tr(
            'Mark all conflicts of the local project as resolved'
        ))
        self.vcsResolveAct.setWhatsThis(self.tr(
            """<b>Conflicts resolved</b>"""
            """<p>This marks all conflicts of the local project as"""
            """ resolved.</p>"""
        ))
        self.vcsResolveAct.triggered.connect(self.__svnResolve)
        self.actions.append(self.vcsResolveAct)
        
        self.vcsCleanupAct = E5Action(
            self.tr('Cleanup'),
            self.tr('Cleanu&p'),
            0, 0, self, 'pysvn_cleanup')
        self.vcsCleanupAct.setStatusTip(self.tr(
            'Cleanup the local project'
        ))
        self.vcsCleanupAct.setWhatsThis(self.tr(
            """<b>Cleanup</b>"""
            """<p>This performs a cleanup of the local project.</p>"""
        ))
        self.vcsCleanupAct.triggered.connect(self._vcsCleanup)
        self.actions.append(self.vcsCleanupAct)
        
        self.vcsCommandAct = E5Action(
            self.tr('Execute command'),
            self.tr('E&xecute command...'),
            0, 0, self, 'pysvn_command')
        self.vcsCommandAct.setStatusTip(self.tr(
            'Execute an arbitrary VCS command'
        ))
        self.vcsCommandAct.setWhatsThis(self.tr(
            """<b>Execute command</b>"""
            """<p>This opens a dialog to enter an arbitrary VCS command.</p>"""
        ))
        self.vcsCommandAct.triggered.connect(self._vcsCommand)
        self.actions.append(self.vcsCommandAct)
        
        self.svnTagListAct = E5Action(
            self.tr('List tags'),
            self.tr('List tags...'),
            0, 0, self, 'pysvn_list_tags')
        self.svnTagListAct.setStatusTip(self.tr(
            'List tags of the project'
        ))
        self.svnTagListAct.setWhatsThis(self.tr(
            """<b>List tags</b>"""
            """<p>This lists the tags of the project.</p>"""
        ))
        self.svnTagListAct.triggered.connect(self.__svnTagList)
        self.actions.append(self.svnTagListAct)
        
        self.svnBranchListAct = E5Action(
            self.tr('List branches'),
            self.tr('List branches...'),
            0, 0, self, 'pysvn_list_branches')
        self.svnBranchListAct.setStatusTip(self.tr(
            'List branches of the project'
        ))
        self.svnBranchListAct.setWhatsThis(self.tr(
            """<b>List branches</b>"""
            """<p>This lists the branches of the project.</p>"""
        ))
        self.svnBranchListAct.triggered.connect(self.__svnBranchList)
        self.actions.append(self.svnBranchListAct)
        
        self.svnListAct = E5Action(
            self.tr('List repository contents'),
            self.tr('List repository contents...'),
            0, 0, self, 'pysvn_contents')
        self.svnListAct.setStatusTip(self.tr(
            'Lists the contents of the repository'
        ))
        self.svnListAct.setWhatsThis(self.tr(
            """<b>List repository contents</b>"""
            """<p>This lists the contents of the repository.</p>"""
        ))
        self.svnListAct.triggered.connect(self.__svnTagList)
        self.actions.append(self.svnListAct)
        
        self.svnPropSetAct = E5Action(
            self.tr('Set Property'),
            self.tr('Set Property...'),
            0, 0, self, 'pysvn_property_set')
        self.svnPropSetAct.setStatusTip(self.tr(
            'Set a property for the project files'
        ))
        self.svnPropSetAct.setWhatsThis(self.tr(
            """<b>Set Property</b>"""
            """<p>This sets a property for the project files.</p>"""
        ))
        self.svnPropSetAct.triggered.connect(self.__svnPropSet)
        self.actions.append(self.svnPropSetAct)
        
        self.svnPropListAct = E5Action(
            self.tr('List Properties'),
            self.tr('List Properties...'),
            0, 0, self, 'pysvn_property_list')
        self.svnPropListAct.setStatusTip(self.tr(
            'List properties of the project files'
        ))
        self.svnPropListAct.setWhatsThis(self.tr(
            """<b>List Properties</b>"""
            """<p>This lists the properties of the project files.</p>"""
        ))
        self.svnPropListAct.triggered.connect(self.__svnPropList)
        self.actions.append(self.svnPropListAct)
        
        self.svnPropDelAct = E5Action(
            self.tr('Delete Property'),
            self.tr('Delete Property...'),
            0, 0, self, 'pysvn_property_delete')
        self.svnPropDelAct.setStatusTip(self.tr(
            'Delete a property for the project files'
        ))
        self.svnPropDelAct.setWhatsThis(self.tr(
            """<b>Delete Property</b>"""
            """<p>This deletes a property for the project files.</p>"""
        ))
        self.svnPropDelAct.triggered.connect(self.__svnPropDel)
        self.actions.append(self.svnPropDelAct)
        
        self.svnRelocateAct = E5Action(
            self.tr('Relocate'),
            UI.PixmapCache.getIcon("vcsSwitch.png"),
            self.tr('Relocate...'),
            0, 0, self, 'pysvn_relocate')
        self.svnRelocateAct.setStatusTip(self.tr(
            'Relocate the working copy to a new repository URL'
        ))
        self.svnRelocateAct.setWhatsThis(self.tr(
            """<b>Relocate</b>"""
            """<p>This relocates the working copy to a new repository"""
            """ URL.</p>"""
        ))
        self.svnRelocateAct.triggered.connect(self.__svnRelocate)
        self.actions.append(self.svnRelocateAct)
        
        self.svnRepoBrowserAct = E5Action(
            self.tr('Repository Browser'),
            UI.PixmapCache.getIcon("vcsRepoBrowser.png"),
            self.tr('Repository Browser...'),
            0, 0, self, 'pysvn_repo_browser')
        self.svnRepoBrowserAct.setStatusTip(self.tr(
            'Show the Repository Browser dialog'
        ))
        self.svnRepoBrowserAct.setWhatsThis(self.tr(
            """<b>Repository Browser</b>"""
            """<p>This shows the Repository Browser dialog.</p>"""
        ))
        self.svnRepoBrowserAct.triggered.connect(self.__svnRepoBrowser)
        self.actions.append(self.svnRepoBrowserAct)
        
        self.svnConfigAct = E5Action(
            self.tr('Configure'),
            self.tr('Configure...'),
            0, 0, self, 'pysvn_configure')
        self.svnConfigAct.setStatusTip(self.tr(
            'Show the configuration dialog with the Subversion page selected'
        ))
        self.svnConfigAct.setWhatsThis(self.tr(
            """<b>Configure</b>"""
            """<p>Show the configuration dialog with the Subversion page"""
            """ selected.</p>"""
        ))
        self.svnConfigAct.triggered.connect(self.__svnConfigure)
        self.actions.append(self.svnConfigAct)
        
        self.svnUpgradeAct = E5Action(
            self.tr('Upgrade'),
            self.tr('Upgrade...'),
            0, 0, self, 'pysvn_upgrade')
        self.svnUpgradeAct.setStatusTip(self.tr(
            'Upgrade the working copy to the current format'
        ))
        self.svnUpgradeAct.setWhatsThis(self.tr(
            """<b>Upgrade</b>"""
            """<p>Upgrades the working copy to the current format.</p>"""
        ))
        self.svnUpgradeAct.triggered.connect(self.__svnUpgrade)
        self.actions.append(self.svnUpgradeAct)
    
    def initMenu(self, menu):
        """
        Public method to generate the VCS menu.
        
        @param menu reference to the menu to be populated (QMenu)
        """
        menu.clear()
        
        act = menu.addAction(
            UI.PixmapCache.getIcon(
                os.path.join("VcsPlugins", "vcsPySvn", "icons", "pysvn.png")),
            self.vcs.vcsName(), self._vcsInfoDisplay)
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        menu.addSeparator()
        
        menu.addAction(self.vcsUpdateAct)
        menu.addAction(self.vcsCommitAct)
        menu.addSeparator()
        menu.addAction(self.vcsTagAct)
        if self.vcs.otherData["standardLayout"]:
            menu.addAction(self.svnTagListAct)
            menu.addAction(self.svnBranchListAct)
        else:
            menu.addAction(self.svnListAct)
        menu.addSeparator()
        menu.addAction(self.vcsLogAct)
        menu.addAction(self.svnLogBrowserAct)
        menu.addSeparator()
        menu.addAction(self.vcsStatusAct)
        menu.addAction(self.svnChangeListsAct)
        menu.addAction(self.svnRepoInfoAct)
        menu.addSeparator()
        menu.addAction(self.vcsDiffAct)
        menu.addAction(self.svnExtDiffAct)
        menu.addAction(self.svnUrlDiffAct)
        menu.addSeparator()
        menu.addAction(self.vcsRevertAct)
        menu.addAction(self.vcsMergeAct)
        menu.addAction(self.vcsResolveAct)
        menu.addSeparator()
        menu.addAction(self.vcsSwitchAct)
        menu.addAction(self.svnRelocateAct)
        menu.addSeparator()
        menu.addAction(self.svnPropSetAct)
        menu.addAction(self.svnPropListAct)
        menu.addAction(self.svnPropDelAct)
        menu.addSeparator()
        menu.addAction(self.vcsCleanupAct)
        menu.addSeparator()
        menu.addAction(self.vcsCommandAct)
        menu.addAction(self.svnRepoBrowserAct)
        menu.addAction(self.svnUpgradeAct)
        menu.addSeparator()
        menu.addAction(self.vcsPropsAct)
        menu.addSeparator()
        menu.addAction(self.svnConfigAct)
        menu.addSeparator()
        menu.addAction(self.vcsNewAct)
        menu.addAction(self.vcsExportAct)
    
    def initToolbar(self, ui, toolbarManager):
        """
        Public slot to initialize the VCS toolbar.
        
        @param ui reference to the main window (UserInterface)
        @param toolbarManager reference to a toolbar manager object
            (E5ToolBarManager)
        """
        self.__toolbar = QToolBar(self.tr("Subversion (pysvn)"), ui)
        self.__toolbar.setIconSize(UI.Config.ToolBarIconSize)
        self.__toolbar.setObjectName("PySvnToolbar")
        self.__toolbar.setToolTip(self.tr('Subversion (pysvn)'))
        
        self.__toolbar.addAction(self.svnLogBrowserAct)
        self.__toolbar.addAction(self.vcsStatusAct)
        self.__toolbar.addSeparator()
        self.__toolbar.addAction(self.vcsDiffAct)
        self.__toolbar.addSeparator()
        self.__toolbar.addAction(self.svnRepoBrowserAct)
        self.__toolbar.addAction(self.vcsNewAct)
        self.__toolbar.addAction(self.vcsExportAct)
        self.__toolbar.addSeparator()
        
        title = self.__toolbar.windowTitle()
        toolbarManager.addToolBar(self.__toolbar, title)
        toolbarManager.addAction(self.vcsUpdateAct, title)
        toolbarManager.addAction(self.vcsCommitAct, title)
        toolbarManager.addAction(self.vcsLogAct, title)
        toolbarManager.addAction(self.svnExtDiffAct, title)
        toolbarManager.addAction(self.svnUrlDiffAct, title)
        toolbarManager.addAction(self.svnChangeListsAct, title)
        toolbarManager.addAction(self.svnRepoInfoAct, title)
        toolbarManager.addAction(self.vcsTagAct, title)
        toolbarManager.addAction(self.vcsRevertAct, title)
        toolbarManager.addAction(self.vcsMergeAct, title)
        toolbarManager.addAction(self.vcsSwitchAct, title)
        toolbarManager.addAction(self.svnRelocateAct, title)
        
        self.__toolbar.setEnabled(False)
        self.__toolbar.setVisible(False)
        
        ui.registerToolbar("pysvn", self.__toolbar.windowTitle(),
                           self.__toolbar)
        ui.addToolBar(self.__toolbar)
    
    def removeToolbar(self, ui, toolbarManager):
        """
        Public method to remove a toolbar created by initToolbar().
        
        @param ui reference to the main window (UserInterface)
        @param toolbarManager reference to a toolbar manager object
            (E5ToolBarManager)
        """
        ui.removeToolBar(self.__toolbar)
        ui.unregisterToolbar("pysvn")
        
        title = self.__toolbar.windowTitle()
        toolbarManager.removeCategoryActions(title)
        toolbarManager.removeToolBar(self.__toolbar)
        
        self.__toolbar.deleteLater()
        self.__toolbar = None
    
    def __svnResolve(self):
        """
        Private slot used to resolve conflicts of the local project.
        """
        self.vcs.svnResolve(self.project.ppath)
        
    def __svnPropList(self):
        """
        Private slot used to list the properties of the project files.
        """
        self.vcs.svnListProps(self.project.ppath, True)
        
    def __svnPropSet(self):
        """
        Private slot used to set a property for the project files.
        """
        self.vcs.svnSetProp(self.project.ppath, True)
        
    def __svnPropDel(self):
        """
        Private slot used to delete a property for the project files.
        """
        self.vcs.svnDelProp(self.project.ppath, True)
        
    def __svnTagList(self):
        """
        Private slot used to list the tags of the project.
        """
        self.vcs.svnListTagBranch(self.project.ppath, True)
        
    def __svnBranchList(self):
        """
        Private slot used to list the branches of the project.
        """
        self.vcs.svnListTagBranch(self.project.ppath, False)
        
    def __svnExtendedDiff(self):
        """
        Private slot used to perform a svn diff with the selection of
        revisions.
        """
        self.vcs.svnExtendedDiff(self.project.ppath)
        
    def __svnUrlDiff(self):
        """
        Private slot used to perform a svn diff with the selection of
        repository URLs.
        """
        self.vcs.svnUrlDiff(self.project.ppath)
        
    def __svnInfo(self):
        """
        Private slot used to show repository information for the local project.
        """
        self.vcs.svnInfo(self.project.ppath, ".")
        
    def __svnRelocate(self):
        """
        Private slot used to relocate the working copy to a new repository URL.
        """
        self.vcs.svnRelocate(self.project.ppath)
        
    def __svnRepoBrowser(self):
        """
        Private slot to open the repository browser.
        """
        self.vcs.svnRepoBrowser(projectPath=self.project.ppath)
        
    def __svnConfigure(self):
        """
        Private slot to open the configuration dialog.
        """
        e5App().getObject("UserInterface")\
            .showPreferences("zzz_subversionPage")
    
    def __svnChangeLists(self):
        """
        Private slot used to show a list of change lists.
        """
        self.vcs.svnShowChangelists(self.project.ppath)
    
    def __svnUpgrade(self):
        """
        Private slot used to upgrade the working copy format.
        """
        self.vcs.svnUpgrade(self.project.ppath)
