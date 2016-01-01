# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the VCS project helper for Mercurial.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtWidgets import QMenu, QToolBar

from E5Gui import E5MessageBox
from E5Gui.E5Application import e5App

from VCS.ProjectHelper import VcsProjectHelper

from E5Gui.E5Action import E5Action

import UI.PixmapCache
import Preferences


class HgProjectHelper(VcsProjectHelper):
    """
    Class implementing the VCS project helper for Mercurial.
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
        
        # instantiate the extensions
        from .QueuesExtension.ProjectHelper import QueuesProjectHelper
        from .FetchExtension.ProjectHelper import FetchProjectHelper
        from .PurgeExtension.ProjectHelper import PurgeProjectHelper
        from .GpgExtension.ProjectHelper import GpgProjectHelper
        from .TransplantExtension.ProjectHelper import TransplantProjectHelper
        from .RebaseExtension.ProjectHelper import RebaseProjectHelper
        from .ShelveExtension.ProjectHelper import ShelveProjectHelper
        from .LargefilesExtension.ProjectHelper import LargefilesProjectHelper
        self.__extensions = {
            "mq": QueuesProjectHelper(),
            "fetch": FetchProjectHelper(),
            "purge": PurgeProjectHelper(),
            "gpg": GpgProjectHelper(),
            "transplant": TransplantProjectHelper(),
            "rebase": RebaseProjectHelper(),
            "shelve": ShelveProjectHelper(),
            "largefiles": LargefilesProjectHelper(),
        }
        
        self.__extensionMenuTitles = {}
        for extension in self.__extensions:
            self.__extensionMenuTitles[
                self.__extensions[extension].menuTitle()] = extension
    
    def setObjects(self, vcsObject, projectObject):
        """
        Public method to set references to the vcs and project objects.
        
        @param vcsObject reference to the vcs object
        @param projectObject reference to the project object
        """
        self.vcs = vcsObject
        self.project = projectObject
        
        for extension in self.__extensions.values():
            extension.setObjects(vcsObject, projectObject)
        
        self.vcs.iniFileChanged.connect(self.__checkActions)
    
    def getProject(self):
        """
        Public method to get a reference to the project object.
        
        @return reference to the project object (Project)
        """
        return self.project
    
    def getActions(self):
        """
        Public method to get a list of all actions.
        
        @return list of all actions (list of E5Action)
        """
        actions = self.actions[:]
        for extension in self.__extensions.values():
            actions.extend(extension.getActions())
        return actions
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.vcsNewAct = E5Action(
            self.tr('New from repository'),
            UI.PixmapCache.getIcon("vcsCheckout.png"),
            self.tr('&New from repository...'), 0, 0,
            self, 'mercurial_new')
        self.vcsNewAct.setStatusTip(self.tr(
            'Create (clone) a new project from a Mercurial repository'
        ))
        self.vcsNewAct.setWhatsThis(self.tr(
            """<b>New from repository</b>"""
            """<p>This creates (clones) a new local project from """
            """a Mercurial repository.</p>"""
        ))
        self.vcsNewAct.triggered.connect(self._vcsCheckout)
        self.actions.append(self.vcsNewAct)
        
        self.hgIncomingAct = E5Action(
            self.tr('Show incoming log'),
            UI.PixmapCache.getIcon("vcsUpdate.png"),
            self.tr('Show incoming log'),
            0, 0, self, 'mercurial_incoming')
        self.hgIncomingAct.setStatusTip(self.tr(
            'Show the log of incoming changes'
        ))
        self.hgIncomingAct.setWhatsThis(self.tr(
            """<b>Show incoming log</b>"""
            """<p>This shows the log of changes coming into the"""
            """ repository.</p>"""
        ))
        self.hgIncomingAct.triggered.connect(self.__hgIncoming)
        self.actions.append(self.hgIncomingAct)
        
        self.hgPullAct = E5Action(
            self.tr('Pull changes'),
            UI.PixmapCache.getIcon("vcsUpdate.png"),
            self.tr('Pull changes'),
            0, 0, self, 'mercurial_pull')
        self.hgPullAct.setStatusTip(self.tr(
            'Pull changes from a remote repository'
        ))
        self.hgPullAct.setWhatsThis(self.tr(
            """<b>Pull changes</b>"""
            """<p>This pulls changes from a remote repository into the """
            """local repository.</p>"""
        ))
        self.hgPullAct.triggered.connect(self.__hgPull)
        self.actions.append(self.hgPullAct)
        
        self.vcsUpdateAct = E5Action(
            self.tr('Update from repository'),
            UI.PixmapCache.getIcon("vcsUpdate.png"),
            self.tr('&Update from repository'), 0, 0, self,
            'mercurial_update')
        self.vcsUpdateAct.setStatusTip(self.tr(
            'Update the local project from the Mercurial repository'
        ))
        self.vcsUpdateAct.setWhatsThis(self.tr(
            """<b>Update from repository</b>"""
            """<p>This updates the local project from the Mercurial"""
            """ repository.</p>"""
        ))
        self.vcsUpdateAct.triggered.connect(self._vcsUpdate)
        self.actions.append(self.vcsUpdateAct)
        
        self.vcsCommitAct = E5Action(
            self.tr('Commit changes to repository'),
            UI.PixmapCache.getIcon("vcsCommit.png"),
            self.tr('&Commit changes to repository...'), 0, 0, self,
            'mercurial_commit')
        self.vcsCommitAct.setStatusTip(self.tr(
            'Commit changes to the local project to the Mercurial repository'
        ))
        self.vcsCommitAct.setWhatsThis(self.tr(
            """<b>Commit changes to repository</b>"""
            """<p>This commits changes to the local project to the """
            """Mercurial repository.</p>"""
        ))
        self.vcsCommitAct.triggered.connect(self._vcsCommit)
        self.actions.append(self.vcsCommitAct)
        
        self.hgOutgoingAct = E5Action(
            self.tr('Show outgoing log'),
            UI.PixmapCache.getIcon("vcsCommit.png"),
            self.tr('Show outgoing log'),
            0, 0, self, 'mercurial_outgoing')
        self.hgOutgoingAct.setStatusTip(self.tr(
            'Show the log of outgoing changes'
        ))
        self.hgOutgoingAct.setWhatsThis(self.tr(
            """<b>Show outgoing log</b>"""
            """<p>This shows the log of changes outgoing out of the"""
            """ repository.</p>"""
        ))
        self.hgOutgoingAct.triggered.connect(self.__hgOutgoing)
        self.actions.append(self.hgOutgoingAct)
        
        self.hgPushAct = E5Action(
            self.tr('Push changes'),
            UI.PixmapCache.getIcon("vcsCommit.png"),
            self.tr('Push changes'),
            0, 0, self, 'mercurial_push')
        self.hgPushAct.setStatusTip(self.tr(
            'Push changes to a remote repository'
        ))
        self.hgPushAct.setWhatsThis(self.tr(
            """<b>Push changes</b>"""
            """<p>This pushes changes from the local repository to a """
            """remote repository.</p>"""
        ))
        self.hgPushAct.triggered.connect(self.__hgPush)
        self.actions.append(self.hgPushAct)
        
        self.hgPushForcedAct = E5Action(
            self.tr('Push changes (force)'),
            UI.PixmapCache.getIcon("vcsCommit.png"),
            self.tr('Push changes (force)'),
            0, 0, self, 'mercurial_push_forced')
        self.hgPushForcedAct.setStatusTip(self.tr(
            'Push changes to a remote repository with force option'
        ))
        self.hgPushForcedAct.setWhatsThis(self.tr(
            """<b>Push changes (force)</b>"""
            """<p>This pushes changes from the local repository to a """
            """remote repository using the 'force' option.</p>"""
        ))
        self.hgPushForcedAct.triggered.connect(self.__hgPushForced)
        self.actions.append(self.hgPushForcedAct)
        
        self.vcsExportAct = E5Action(
            self.tr('Export from repository'),
            UI.PixmapCache.getIcon("vcsExport.png"),
            self.tr('&Export from repository...'),
            0, 0, self, 'mercurial_export_repo')
        self.vcsExportAct.setStatusTip(self.tr(
            'Export a project from the repository'
        ))
        self.vcsExportAct.setWhatsThis(self.tr(
            """<b>Export from repository</b>"""
            """<p>This exports a project from the repository.</p>"""
        ))
        self.vcsExportAct.triggered.connect(self._vcsExport)
        self.actions.append(self.vcsExportAct)
        
        self.vcsLogAct = E5Action(
            self.tr('Show log'),
            UI.PixmapCache.getIcon("vcsLog.png"),
            self.tr('Show &log'),
            0, 0, self, 'mercurial_log')
        self.vcsLogAct.setStatusTip(self.tr(
            'Show the log of the local project'
        ))
        self.vcsLogAct.setWhatsThis(self.tr(
            """<b>Show log</b>"""
            """<p>This shows the log of the local project.</p>"""
        ))
        self.vcsLogAct.triggered.connect(self._vcsLog)
        self.actions.append(self.vcsLogAct)
        
        self.hgLogBrowserAct = E5Action(
            self.tr('Show log browser'),
            UI.PixmapCache.getIcon("vcsLog.png"),
            self.tr('Show log browser'),
            0, 0, self, 'mercurial_log_browser')
        self.hgLogBrowserAct.setStatusTip(self.tr(
            'Show a dialog to browse the log of the local project'
        ))
        self.hgLogBrowserAct.setWhatsThis(self.tr(
            """<b>Show log browser</b>"""
            """<p>This shows a dialog to browse the log of the local"""
            """ project. A limited number of entries is shown first."""
            """ More can be retrieved later on.</p>"""
        ))
        self.hgLogBrowserAct.triggered.connect(self._vcsLogBrowser)
        self.actions.append(self.hgLogBrowserAct)
        
        self.vcsDiffAct = E5Action(
            self.tr('Show differences'),
            UI.PixmapCache.getIcon("vcsDiff.png"),
            self.tr('Show &difference'),
            0, 0, self, 'mercurial_diff')
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
        
        self.hgExtDiffAct = E5Action(
            self.tr('Show differences (extended)'),
            UI.PixmapCache.getIcon("vcsDiff.png"),
            self.tr('Show differences (extended)'),
            0, 0, self, 'mercurial_extendeddiff')
        self.hgExtDiffAct.setStatusTip(self.tr(
            'Show the difference of revisions of the project to the repository'
        ))
        self.hgExtDiffAct.setWhatsThis(self.tr(
            """<b>Show differences (extended)</b>"""
            """<p>This shows differences of selectable revisions of the"""
            """ project.</p>"""
        ))
        self.hgExtDiffAct.triggered.connect(self.__hgExtendedDiff)
        self.actions.append(self.hgExtDiffAct)
        
        self.vcsStatusAct = E5Action(
            self.tr('Show status'),
            UI.PixmapCache.getIcon("vcsStatus.png"),
            self.tr('Show &status...'),
            0, 0, self, 'mercurial_status')
        self.vcsStatusAct.setStatusTip(self.tr(
            'Show the status of the local project'
        ))
        self.vcsStatusAct.setWhatsThis(self.tr(
            """<b>Show status</b>"""
            """<p>This shows the status of the local project.</p>"""
        ))
        self.vcsStatusAct.triggered.connect(self._vcsStatus)
        self.actions.append(self.vcsStatusAct)
        
        self.hgSummaryAct = E5Action(
            self.tr('Show Summary'),
            UI.PixmapCache.getIcon("vcsSummary.png"),
            self.tr('Show summary...'),
            0, 0, self, 'mercurial_summary')
        self.hgSummaryAct.setStatusTip(self.tr(
            'Show summary information of the working directory status'
        ))
        self.hgSummaryAct.setWhatsThis(self.tr(
            """<b>Show summary</b>"""
            """<p>This shows some summary information of the working"""
            """ directory status.</p>"""
        ))
        self.hgSummaryAct.triggered.connect(self.__hgSummary)
        self.actions.append(self.hgSummaryAct)
        
        self.hgHeadsAct = E5Action(
            self.tr('Show heads'),
            self.tr('Show heads'),
            0, 0, self, 'mercurial_heads')
        self.hgHeadsAct.setStatusTip(self.tr(
            'Show the heads of the repository'
        ))
        self.hgHeadsAct.setWhatsThis(self.tr(
            """<b>Show heads</b>"""
            """<p>This shows the heads of the repository.</p>"""
        ))
        self.hgHeadsAct.triggered.connect(self.__hgHeads)
        self.actions.append(self.hgHeadsAct)
        
        self.hgParentsAct = E5Action(
            self.tr('Show parents'),
            self.tr('Show parents'),
            0, 0, self, 'mercurial_parents')
        self.hgParentsAct.setStatusTip(self.tr(
            'Show the parents of the repository'
        ))
        self.hgParentsAct.setWhatsThis(self.tr(
            """<b>Show parents</b>"""
            """<p>This shows the parents of the repository.</p>"""
        ))
        self.hgParentsAct.triggered.connect(self.__hgParents)
        self.actions.append(self.hgParentsAct)
        
        self.hgTipAct = E5Action(
            self.tr('Show tip'),
            self.tr('Show tip'),
            0, 0, self, 'mercurial_tip')
        self.hgTipAct.setStatusTip(self.tr(
            'Show the tip of the repository'
        ))
        self.hgTipAct.setWhatsThis(self.tr(
            """<b>Show tip</b>"""
            """<p>This shows the tip of the repository.</p>"""
        ))
        self.hgTipAct.triggered.connect(self.__hgTip)
        self.actions.append(self.hgTipAct)
        
        self.vcsRevertAct = E5Action(
            self.tr('Revert changes'),
            UI.PixmapCache.getIcon("vcsRevert.png"),
            self.tr('Re&vert changes'),
            0, 0, self, 'mercurial_revert')
        self.vcsRevertAct.setStatusTip(self.tr(
            'Revert all changes made to the local project'
        ))
        self.vcsRevertAct.setWhatsThis(self.tr(
            """<b>Revert changes</b>"""
            """<p>This reverts all changes made to the local project.</p>"""
        ))
        self.vcsRevertAct.triggered.connect(self.__hgRevert)
        self.actions.append(self.vcsRevertAct)
        
        self.vcsMergeAct = E5Action(
            self.tr('Merge'),
            UI.PixmapCache.getIcon("vcsMerge.png"),
            self.tr('Mer&ge changes...'),
            0, 0, self, 'mercurial_merge')
        self.vcsMergeAct.setStatusTip(self.tr(
            'Merge changes of a revision into the local project'
        ))
        self.vcsMergeAct.setWhatsThis(self.tr(
            """<b>Merge</b>"""
            """<p>This merges changes of a revision into the local"""
            """ project.</p>"""
        ))
        self.vcsMergeAct.triggered.connect(self._vcsMerge)
        self.actions.append(self.vcsMergeAct)
        
        self.hgCancelMergeAct = E5Action(
            self.tr('Cancel uncommitted merge'),
            self.tr('Cancel uncommitted merge'),
            0, 0, self, 'mercurial_cancel_merge')
        self.hgCancelMergeAct.setStatusTip(self.tr(
            'Cancel an uncommitted merge and lose all changes'
        ))
        self.hgCancelMergeAct.setWhatsThis(self.tr(
            """<b>Cancel uncommitted merge</b>"""
            """<p>This cancels an uncommitted merge causing all changes"""
            """ to be lost.</p>"""
        ))
        self.hgCancelMergeAct.triggered.connect(self.__hgCancelMerge)
        self.actions.append(self.hgCancelMergeAct)
        
        self.hgReMergeAct = E5Action(
            self.tr('Re-Merge'),
            UI.PixmapCache.getIcon("vcsMerge.png"),
            self.tr('Re-Merge'),
            0, 0, self, 'mercurial_remerge')
        self.hgReMergeAct.setStatusTip(self.tr(
            'Re-Merge all conflicting, unresolved files of the project'
        ))
        self.hgReMergeAct.setWhatsThis(self.tr(
            """<b>Re-Merge</b>"""
            """<p>This re-merges all conflicting, unresolved files of the"""
            """ project discarding any previous merge attempt.</p>"""
        ))
        self.hgReMergeAct.triggered.connect(self.__hgReMerge)
        self.actions.append(self.hgReMergeAct)
        
        self.hgShowConflictsAct = E5Action(
            self.tr('Show conflicts'),
            self.tr('Show conflicts...'),
            0, 0, self, 'mercurial_show_conflicts')
        self.hgShowConflictsAct.setStatusTip(self.tr(
            'Show a dialog listing all files with conflicts'
        ))
        self.hgShowConflictsAct.setWhatsThis(self.tr(
            """<b>Show conflicts</b>"""
            """<p>This shows a dialog listing all files which had or still"""
            """ have conflicts.</p>"""
        ))
        self.hgShowConflictsAct.triggered.connect(self.__hgShowConflicts)
        self.actions.append(self.hgShowConflictsAct)
        
        self.vcsResolveAct = E5Action(
            self.tr('Conflicts resolved'),
            self.tr('Con&flicts resolved'),
            0, 0, self, 'mercurial_resolve')
        self.vcsResolveAct.setStatusTip(self.tr(
            'Mark all conflicts of the local project as resolved'
        ))
        self.vcsResolveAct.setWhatsThis(self.tr(
            """<b>Conflicts resolved</b>"""
            """<p>This marks all conflicts of the local project as"""
            """ resolved.</p>"""
        ))
        self.vcsResolveAct.triggered.connect(self.__hgResolved)
        self.actions.append(self.vcsResolveAct)
        
        self.hgUnresolveAct = E5Action(
            self.tr('Conflicts unresolved'),
            self.tr('Conflicts unresolved'),
            0, 0, self, 'mercurial_unresolve')
        self.hgUnresolveAct.setStatusTip(self.tr(
            'Mark all conflicts of the local project as unresolved'
        ))
        self.hgUnresolveAct.setWhatsThis(self.tr(
            """<b>Conflicts unresolved</b>"""
            """<p>This marks all conflicts of the local project as"""
            """ unresolved.</p>"""
        ))
        self.hgUnresolveAct.triggered.connect(self.__hgUnresolved)
        self.actions.append(self.hgUnresolveAct)
        
        self.vcsTagAct = E5Action(
            self.tr('Tag in repository'),
            UI.PixmapCache.getIcon("vcsTag.png"),
            self.tr('&Tag in repository...'),
            0, 0, self, 'mercurial_tag')
        self.vcsTagAct.setStatusTip(self.tr(
            'Tag the local project in the repository'
        ))
        self.vcsTagAct.setWhatsThis(self.tr(
            """<b>Tag in repository</b>"""
            """<p>This tags the local project in the repository.</p>"""
        ))
        self.vcsTagAct.triggered.connect(self._vcsTag)
        self.actions.append(self.vcsTagAct)
        
        self.hgTagListAct = E5Action(
            self.tr('List tags'),
            self.tr('List tags...'),
            0, 0, self, 'mercurial_list_tags')
        self.hgTagListAct.setStatusTip(self.tr(
            'List tags of the project'
        ))
        self.hgTagListAct.setWhatsThis(self.tr(
            """<b>List tags</b>"""
            """<p>This lists the tags of the project.</p>"""
        ))
        self.hgTagListAct.triggered.connect(self.__hgTagList)
        self.actions.append(self.hgTagListAct)
        
        self.hgBranchListAct = E5Action(
            self.tr('List branches'),
            self.tr('List branches...'),
            0, 0, self, 'mercurial_list_branches')
        self.hgBranchListAct.setStatusTip(self.tr(
            'List branches of the project'
        ))
        self.hgBranchListAct.setWhatsThis(self.tr(
            """<b>List branches</b>"""
            """<p>This lists the branches of the project.</p>"""
        ))
        self.hgBranchListAct.triggered.connect(self.__hgBranchList)
        self.actions.append(self.hgBranchListAct)
        
        self.hgBranchAct = E5Action(
            self.tr('Create branch'),
            UI.PixmapCache.getIcon("vcsBranch.png"),
            self.tr('Create &branch...'),
            0, 0, self, 'mercurial_branch')
        self.hgBranchAct.setStatusTip(self.tr(
            'Create a new branch for the local project in the repository'
        ))
        self.hgBranchAct.setWhatsThis(self.tr(
            """<b>Create branch</b>"""
            """<p>This creates a new branch for the local project """
            """in the repository.</p>"""
        ))
        self.hgBranchAct.triggered.connect(self.__hgBranch)
        self.actions.append(self.hgBranchAct)
        
        self.hgPushBranchAct = E5Action(
            self.tr('Push new branch'),
            self.tr('Push new branch'),
            0, 0, self, 'mercurial_push_branch')
        self.hgPushBranchAct.setStatusTip(self.tr(
            'Push the current branch of the local project as a new named'
            ' branch'
        ))
        self.hgPushBranchAct.setWhatsThis(self.tr(
            """<b>Push new branch</b>"""
            """<p>This pushes the current branch of the local project"""
            """ as a new named branch.</p>"""
        ))
        self.hgPushBranchAct.triggered.connect(self.__hgPushNewBranch)
        self.actions.append(self.hgPushBranchAct)
        
        self.hgCloseBranchAct = E5Action(
            self.tr('Close branch'),
            self.tr('Close branch'),
            0, 0, self, 'mercurial_close_branch')
        self.hgCloseBranchAct.setStatusTip(self.tr(
            'Close the current branch of the local project'
        ))
        self.hgCloseBranchAct.setWhatsThis(self.tr(
            """<b>Close branch</b>"""
            """<p>This closes the current branch of the local project.</p>"""
        ))
        self.hgCloseBranchAct.triggered.connect(self.__hgCloseBranch)
        self.actions.append(self.hgCloseBranchAct)
        
        self.hgShowBranchAct = E5Action(
            self.tr('Show current branch'),
            self.tr('Show current branch'),
            0, 0, self, 'mercurial_show_branch')
        self.hgShowBranchAct.setStatusTip(self.tr(
            'Show the current branch of the project'
        ))
        self.hgShowBranchAct.setWhatsThis(self.tr(
            """<b>Show current branch</b>"""
            """<p>This shows the current branch of the project.</p>"""
        ))
        self.hgShowBranchAct.triggered.connect(self.__hgShowBranch)
        self.actions.append(self.hgShowBranchAct)
        
        self.vcsSwitchAct = E5Action(
            self.tr('Switch'),
            UI.PixmapCache.getIcon("vcsSwitch.png"),
            self.tr('S&witch...'),
            0, 0, self, 'mercurial_switch')
        self.vcsSwitchAct.setStatusTip(self.tr(
            'Switch the working directory to another revision'
        ))
        self.vcsSwitchAct.setWhatsThis(self.tr(
            """<b>Switch</b>"""
            """<p>This switches the working directory to another"""
            """ revision.</p>"""
        ))
        self.vcsSwitchAct.triggered.connect(self._vcsSwitch)
        self.actions.append(self.vcsSwitchAct)
        
        self.vcsCleanupAct = E5Action(
            self.tr('Cleanup'),
            self.tr('Cleanu&p'),
            0, 0, self, 'mercurial_cleanup')
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
            0, 0, self, 'mercurial_command')
        self.vcsCommandAct.setStatusTip(self.tr(
            'Execute an arbitrary Mercurial command'
        ))
        self.vcsCommandAct.setWhatsThis(self.tr(
            """<b>Execute command</b>"""
            """<p>This opens a dialog to enter an arbitrary Mercurial"""
            """ command.</p>"""
        ))
        self.vcsCommandAct.triggered.connect(self._vcsCommand)
        self.actions.append(self.vcsCommandAct)
        
        self.hgConfigAct = E5Action(
            self.tr('Configure'),
            self.tr('Configure...'),
            0, 0, self, 'mercurial_configure')
        self.hgConfigAct.setStatusTip(self.tr(
            'Show the configuration dialog with the Mercurial page selected'
        ))
        self.hgConfigAct.setWhatsThis(self.tr(
            """<b>Configure</b>"""
            """<p>Show the configuration dialog with the Mercurial page"""
            """ selected.</p>"""
        ))
        self.hgConfigAct.triggered.connect(self.__hgConfigure)
        self.actions.append(self.hgConfigAct)
        
        self.hgEditUserConfigAct = E5Action(
            self.tr('Edit user configuration'),
            self.tr('Edit user configuration...'),
            0, 0, self, 'mercurial_user_configure')
        self.hgEditUserConfigAct.setStatusTip(self.tr(
            'Show an editor to edit the user configuration file'
        ))
        self.hgEditUserConfigAct.setWhatsThis(self.tr(
            """<b>Edit user configuration</b>"""
            """<p>Show an editor to edit the user configuration file.</p>"""
        ))
        self.hgEditUserConfigAct.triggered.connect(self.__hgEditUserConfig)
        self.actions.append(self.hgEditUserConfigAct)
        
        self.hgRepoConfigAct = E5Action(
            self.tr('Edit repository configuration'),
            self.tr('Edit repository configuration...'),
            0, 0, self, 'mercurial_repo_configure')
        self.hgRepoConfigAct.setStatusTip(self.tr(
            'Show an editor to edit the repository configuration file'
        ))
        self.hgRepoConfigAct.setWhatsThis(self.tr(
            """<b>Edit repository configuration</b>"""
            """<p>Show an editor to edit the repository configuration"""
            """ file.</p>"""
        ))
        self.hgRepoConfigAct.triggered.connect(self.__hgEditRepoConfig)
        self.actions.append(self.hgRepoConfigAct)
        
        self.hgShowConfigAct = E5Action(
            self.tr('Show combined configuration settings'),
            self.tr('Show combined configuration settings...'),
            0, 0, self, 'mercurial_show_config')
        self.hgShowConfigAct.setStatusTip(self.tr(
            'Show the combined configuration settings from all configuration'
            ' files'
        ))
        self.hgShowConfigAct.setWhatsThis(self.tr(
            """<b>Show combined configuration settings</b>"""
            """<p>This shows the combined configuration settings"""
            """ from all configuration files.</p>"""
        ))
        self.hgShowConfigAct.triggered.connect(self.__hgShowConfig)
        self.actions.append(self.hgShowConfigAct)
        
        self.hgShowPathsAct = E5Action(
            self.tr('Show paths'),
            self.tr('Show paths...'),
            0, 0, self, 'mercurial_show_paths')
        self.hgShowPathsAct.setStatusTip(self.tr(
            'Show the aliases for remote repositories'
        ))
        self.hgShowPathsAct.setWhatsThis(self.tr(
            """<b>Show paths</b>"""
            """<p>This shows the aliases for remote repositories.</p>"""
        ))
        self.hgShowPathsAct.triggered.connect(self.__hgShowPaths)
        self.actions.append(self.hgShowPathsAct)
        
        self.hgVerifyAct = E5Action(
            self.tr('Verify repository'),
            self.tr('Verify repository...'),
            0, 0, self, 'mercurial_verify')
        self.hgVerifyAct.setStatusTip(self.tr(
            'Verify the integrity of the repository'
        ))
        self.hgVerifyAct.setWhatsThis(self.tr(
            """<b>Verify repository</b>"""
            """<p>This verifies the integrity of the repository.</p>"""
        ))
        self.hgVerifyAct.triggered.connect(self.__hgVerify)
        self.actions.append(self.hgVerifyAct)
        
        self.hgRecoverAct = E5Action(
            self.tr('Recover'),
            self.tr('Recover...'),
            0, 0, self, 'mercurial_recover')
        self.hgRecoverAct.setStatusTip(self.tr(
            'Recover from an interrupted transaction'
        ))
        self.hgRecoverAct.setWhatsThis(self.tr(
            """<b>Recover</b>"""
            """<p>This recovers from an interrupted transaction.</p>"""
        ))
        self.hgRecoverAct.triggered.connect(self.__hgRecover)
        self.actions.append(self.hgRecoverAct)
        
        self.hgIdentifyAct = E5Action(
            self.tr('Identify'),
            self.tr('Identify...'),
            0, 0, self, 'mercurial_identify')
        self.hgIdentifyAct.setStatusTip(self.tr(
            'Identify the project directory'
        ))
        self.hgIdentifyAct.setWhatsThis(self.tr(
            """<b>Identify</b>"""
            """<p>This identifies the project directory.</p>"""
        ))
        self.hgIdentifyAct.triggered.connect(self.__hgIdentify)
        self.actions.append(self.hgIdentifyAct)
        
        self.hgCreateIgnoreAct = E5Action(
            self.tr('Create .hgignore'),
            self.tr('Create .hgignore'),
            0, 0, self, 'mercurial_create ignore')
        self.hgCreateIgnoreAct.setStatusTip(self.tr(
            'Create a .hgignore file with default values'
        ))
        self.hgCreateIgnoreAct.setWhatsThis(self.tr(
            """<b>Create .hgignore</b>"""
            """<p>This creates a .hgignore file with default values.</p>"""
        ))
        self.hgCreateIgnoreAct.triggered.connect(self.__hgCreateIgnore)
        self.actions.append(self.hgCreateIgnoreAct)
        
        self.hgBundleAct = E5Action(
            self.tr('Create changegroup'),
            self.tr('Create changegroup...'),
            0, 0, self, 'mercurial_bundle')
        self.hgBundleAct.setStatusTip(self.tr(
            'Create changegroup file collecting changesets'
        ))
        self.hgBundleAct.setWhatsThis(self.tr(
            """<b>Create changegroup</b>"""
            """<p>This creates a changegroup file collecting selected"""
            """ changesets (hg bundle).</p>"""
        ))
        self.hgBundleAct.triggered.connect(self.__hgBundle)
        self.actions.append(self.hgBundleAct)
        
        self.hgPreviewBundleAct = E5Action(
            self.tr('Preview changegroup'),
            self.tr('Preview changegroup...'),
            0, 0, self, 'mercurial_preview_bundle')
        self.hgPreviewBundleAct.setStatusTip(self.tr(
            'Preview a changegroup file containing a collection of changesets'
        ))
        self.hgPreviewBundleAct.setWhatsThis(self.tr(
            """<b>Preview changegroup</b>"""
            """<p>This previews a changegroup file containing a collection"""
            """ of changesets.</p>"""
        ))
        self.hgPreviewBundleAct.triggered.connect(self.__hgPreviewBundle)
        self.actions.append(self.hgPreviewBundleAct)
        
        self.hgUnbundleAct = E5Action(
            self.tr('Apply changegroups'),
            self.tr('Apply changegroups...'),
            0, 0, self, 'mercurial_unbundle')
        self.hgUnbundleAct.setStatusTip(self.tr(
            'Apply one or several changegroup files'
        ))
        self.hgUnbundleAct.setWhatsThis(self.tr(
            """<b>Apply changegroups</b>"""
            """<p>This applies one or several changegroup files generated by"""
            """ the 'Create changegroup' action (hg unbundle).</p>"""
        ))
        self.hgUnbundleAct.triggered.connect(self.__hgUnbundle)
        self.actions.append(self.hgUnbundleAct)
        
        self.hgBisectGoodAct = E5Action(
            self.tr('Mark as "good"'),
            self.tr('Mark as "good"...'),
            0, 0, self, 'mercurial_bisect_good')
        self.hgBisectGoodAct.setStatusTip(self.tr(
            'Mark a selectable changeset as good'
        ))
        self.hgBisectGoodAct.setWhatsThis(self.tr(
            """<b>Mark as good</b>"""
            """<p>This marks a selectable changeset as good.</p>"""
        ))
        self.hgBisectGoodAct.triggered.connect(self.__hgBisectGood)
        self.actions.append(self.hgBisectGoodAct)
        
        self.hgBisectBadAct = E5Action(
            self.tr('Mark as "bad"'),
            self.tr('Mark as "bad"...'),
            0, 0, self, 'mercurial_bisect_bad')
        self.hgBisectBadAct.setStatusTip(self.tr(
            'Mark a selectable changeset as bad'
        ))
        self.hgBisectBadAct.setWhatsThis(self.tr(
            """<b>Mark as bad</b>"""
            """<p>This marks a selectable changeset as bad.</p>"""
        ))
        self.hgBisectBadAct.triggered.connect(self.__hgBisectBad)
        self.actions.append(self.hgBisectBadAct)
        
        self.hgBisectSkipAct = E5Action(
            self.tr('Skip'),
            self.tr('Skip...'),
            0, 0, self, 'mercurial_bisect_skip')
        self.hgBisectSkipAct.setStatusTip(self.tr(
            'Skip a selectable changeset'
        ))
        self.hgBisectSkipAct.setWhatsThis(self.tr(
            """<b>Skip</b>"""
            """<p>This skips a selectable changeset.</p>"""
        ))
        self.hgBisectSkipAct.triggered.connect(self.__hgBisectSkip)
        self.actions.append(self.hgBisectSkipAct)
        
        self.hgBisectResetAct = E5Action(
            self.tr('Reset'),
            self.tr('Reset'),
            0, 0, self, 'mercurial_bisect_reset')
        self.hgBisectResetAct.setStatusTip(self.tr(
            'Reset the bisect search data'
        ))
        self.hgBisectResetAct.setWhatsThis(self.tr(
            """<b>Reset</b>"""
            """<p>This resets the bisect search data.</p>"""
        ))
        self.hgBisectResetAct.triggered.connect(self.__hgBisectReset)
        self.actions.append(self.hgBisectResetAct)
        
        self.hgBackoutAct = E5Action(
            self.tr('Back out changeset'),
            self.tr('Back out changeset'),
            0, 0, self, 'mercurial_backout')
        self.hgBackoutAct.setStatusTip(self.tr(
            'Back out changes of an earlier changeset'
        ))
        self.hgBackoutAct.setWhatsThis(self.tr(
            """<b>Back out changeset</b>"""
            """<p>This backs out changes of an earlier changeset.</p>"""
        ))
        self.hgBackoutAct.triggered.connect(self.__hgBackout)
        self.actions.append(self.hgBackoutAct)
        
        self.hgRollbackAct = E5Action(
            self.tr('Rollback last transaction'),
            self.tr('Rollback last transaction'),
            0, 0, self, 'mercurial_rollback')
        self.hgRollbackAct.setStatusTip(self.tr(
            'Rollback the last transaction'
        ))
        self.hgRollbackAct.setWhatsThis(self.tr(
            """<b>Rollback last transaction</b>"""
            """<p>This performs a rollback of the last transaction."""
            """ Transactions are used to encapsulate the effects of all"""
            """ commands that create new changesets or propagate existing"""
            """ changesets into a repository. For example, the following"""
            """ commands are transactional, and their effects can be"""
            """ rolled back:<ul>"""
            """<li>commit</li>"""
            """<li>import</li>"""
            """<li>pull</li>"""
            """<li>push (with this repository as the destination)</li>"""
            """<li>unbundle</li>"""
            """</ul>"""
            """</p><p><strong>This command is dangerous. Please use with"""
            """ care. </strong></p>"""
        ))
        self.hgRollbackAct.triggered.connect(self.__hgRollback)
        self.actions.append(self.hgRollbackAct)
        
        self.hgServeAct = E5Action(
            self.tr('Serve project repository'),
            self.tr('Serve project repository...'),
            0, 0, self, 'mercurial_serve')
        self.hgServeAct.setStatusTip(self.tr(
            'Serve the project repository'
        ))
        self.hgServeAct.setWhatsThis(self.tr(
            """<b>Serve project repository</b>"""
            """<p>This serves the project repository.</p>"""
        ))
        self.hgServeAct.triggered.connect(self.__hgServe)
        self.actions.append(self.hgServeAct)
        
        self.hgImportAct = E5Action(
            self.tr('Import Patch'),
            self.tr('Import Patch...'),
            0, 0, self, 'mercurial_import')
        self.hgImportAct.setStatusTip(self.tr(
            'Import a patch from a patch file'
        ))
        self.hgImportAct.setWhatsThis(self.tr(
            """<b>Import Patch</b>"""
            """<p>This imports a patch from a patch file into the"""
            """ project.</p>"""
        ))
        self.hgImportAct.triggered.connect(self.__hgImport)
        self.actions.append(self.hgImportAct)
        
        self.hgExportAct = E5Action(
            self.tr('Export Patches'),
            self.tr('Export Patches...'),
            0, 0, self, 'mercurial_export')
        self.hgExportAct.setStatusTip(self.tr(
            'Export revisions to patch files'
        ))
        self.hgExportAct.setWhatsThis(self.tr(
            """<b>Export Patches</b>"""
            """<p>This exports revisions of the project to patch files.</p>"""
        ))
        self.hgExportAct.triggered.connect(self.__hgExport)
        self.actions.append(self.hgExportAct)
        
        self.hgPhaseAct = E5Action(
            self.tr('Change Phase'),
            self.tr('Change Phase...'),
            0, 0, self, 'mercurial_change_phase')
        self.hgPhaseAct.setStatusTip(self.tr(
            'Change the phase of revisions'
        ))
        self.hgPhaseAct.setWhatsThis(self.tr(
            """<b>Change Phase</b>"""
            """<p>This changes the phase of revisions.</p>"""
        ))
        self.hgPhaseAct.triggered.connect(self.__hgPhase)
        self.actions.append(self.hgPhaseAct)
        
        self.hgGraftAct = E5Action(
            self.tr('Copy Changesets'),
            UI.PixmapCache.getIcon("vcsGraft.png"),
            self.tr('Copy Changesets'),
            0, 0, self, 'mercurial_graft')
        self.hgGraftAct.setStatusTip(self.tr(
            'Copies changesets from another branch'
        ))
        self.hgGraftAct.setWhatsThis(self.tr(
            """<b>Copy Changesets</b>"""
            """<p>This copies changesets from another branch on top of the"""
            """ current working directory with the user, date and"""
            """ description of the original changeset.</p>"""
        ))
        self.hgGraftAct.triggered.connect(self.__hgGraft)
        self.actions.append(self.hgGraftAct)
        
        self.hgGraftContinueAct = E5Action(
            self.tr('Continue Copying Session'),
            self.tr('Continue Copying Session'),
            0, 0, self, 'mercurial_graft_continue')
        self.hgGraftContinueAct.setStatusTip(self.tr(
            'Continue the last copying session after conflicts were resolved'
        ))
        self.hgGraftContinueAct.setWhatsThis(self.tr(
            """<b>Continue Copying Session</b>"""
            """<p>This continues the last copying session after conflicts"""
            """ were resolved.</p>"""
        ))
        self.hgGraftContinueAct.triggered.connect(self.__hgGraftContinue)
        self.actions.append(self.hgGraftContinueAct)
        
        self.hgAddSubrepoAct = E5Action(
            self.tr('Add'),
            UI.PixmapCache.getIcon("vcsAdd.png"),
            self.tr('Add...'),
            0, 0, self, 'mercurial_add_subrepo')
        self.hgAddSubrepoAct.setStatusTip(self.tr(
            'Add a sub-repository'
        ))
        self.hgAddSubrepoAct.setWhatsThis(self.tr(
            """<b>Add...</b>"""
            """<p>Add a sub-repository to the project.</p>"""
        ))
        self.hgAddSubrepoAct.triggered.connect(self.__hgAddSubrepository)
        self.actions.append(self.hgAddSubrepoAct)
        
        self.hgRemoveSubreposAct = E5Action(
            self.tr('Remove'),
            UI.PixmapCache.getIcon("vcsRemove.png"),
            self.tr('Remove...'),
            0, 0, self, 'mercurial_remove_subrepos')
        self.hgRemoveSubreposAct.setStatusTip(self.tr(
            'Remove sub-repositories'
        ))
        self.hgRemoveSubreposAct.setWhatsThis(self.tr(
            """<b>Remove...</b>"""
            """<p>Remove sub-repositories from the project.</p>"""
        ))
        self.hgRemoveSubreposAct.triggered.connect(
            self.__hgRemoveSubrepositories)
        self.actions.append(self.hgRemoveSubreposAct)
        
        self.hgArchiveAct = E5Action(
            self.tr('Create unversioned archive'),
            UI.PixmapCache.getIcon("vcsExport.png"),
            self.tr('Create unversioned archive...'),
            0, 0, self, 'mercurial_archive')
        self.hgArchiveAct.setStatusTip(self.tr(
            'Create an unversioned archive from the repository'
        ))
        self.hgArchiveAct.setWhatsThis(self.tr(
            """<b>Create unversioned archive...</b>"""
            """<p>This creates an unversioned archive from the"""
            """ repository.</p>"""
        ))
        self.hgArchiveAct.triggered.connect(self.__hgArchive)
        self.actions.append(self.hgArchiveAct)
        
        self.hgBookmarksListAct = E5Action(
            self.tr('List bookmarks'),
            UI.PixmapCache.getIcon("listBookmarks.png"),
            self.tr('List bookmarks...'),
            0, 0, self, 'mercurial_list_bookmarks')
        self.hgBookmarksListAct.setStatusTip(self.tr(
            'List bookmarks of the project'
        ))
        self.hgBookmarksListAct.setWhatsThis(self.tr(
            """<b>List bookmarks</b>"""
            """<p>This lists the bookmarks of the project.</p>"""
        ))
        self.hgBookmarksListAct.triggered.connect(self.__hgBookmarksList)
        self.actions.append(self.hgBookmarksListAct)
    
        self.hgBookmarkDefineAct = E5Action(
            self.tr('Define bookmark'),
            UI.PixmapCache.getIcon("addBookmark.png"),
            self.tr('Define bookmark...'),
            0, 0, self, 'mercurial_define_bookmark')
        self.hgBookmarkDefineAct.setStatusTip(self.tr(
            'Define a bookmark for the project'
        ))
        self.hgBookmarkDefineAct.setWhatsThis(self.tr(
            """<b>Define bookmark</b>"""
            """<p>This defines a bookmark for the project.</p>"""
        ))
        self.hgBookmarkDefineAct.triggered.connect(self.__hgBookmarkDefine)
        self.actions.append(self.hgBookmarkDefineAct)
    
        self.hgBookmarkDeleteAct = E5Action(
            self.tr('Delete bookmark'),
            UI.PixmapCache.getIcon("deleteBookmark.png"),
            self.tr('Delete bookmark...'),
            0, 0, self, 'mercurial_delete_bookmark')
        self.hgBookmarkDeleteAct.setStatusTip(self.tr(
            'Delete a bookmark of the project'
        ))
        self.hgBookmarkDeleteAct.setWhatsThis(self.tr(
            """<b>Delete bookmark</b>"""
            """<p>This deletes a bookmark of the project.</p>"""
        ))
        self.hgBookmarkDeleteAct.triggered.connect(self.__hgBookmarkDelete)
        self.actions.append(self.hgBookmarkDeleteAct)
    
        self.hgBookmarkRenameAct = E5Action(
            self.tr('Rename bookmark'),
            UI.PixmapCache.getIcon("renameBookmark.png"),
            self.tr('Rename bookmark...'),
            0, 0, self, 'mercurial_rename_bookmark')
        self.hgBookmarkRenameAct.setStatusTip(self.tr(
            'Rename a bookmark of the project'
        ))
        self.hgBookmarkRenameAct.setWhatsThis(self.tr(
            """<b>Rename bookmark</b>"""
            """<p>This renames a bookmark of the project.</p>"""
        ))
        self.hgBookmarkRenameAct.triggered.connect(self.__hgBookmarkRename)
        self.actions.append(self.hgBookmarkRenameAct)
    
        self.hgBookmarkMoveAct = E5Action(
            self.tr('Move bookmark'),
            UI.PixmapCache.getIcon("moveBookmark.png"),
            self.tr('Move bookmark...'),
            0, 0, self, 'mercurial_move_bookmark')
        self.hgBookmarkMoveAct.setStatusTip(self.tr(
            'Move a bookmark of the project'
        ))
        self.hgBookmarkMoveAct.setWhatsThis(self.tr(
            """<b>Move bookmark</b>"""
            """<p>This moves a bookmark of the project to another"""
            """ changeset.</p>"""
        ))
        self.hgBookmarkMoveAct.triggered.connect(self.__hgBookmarkMove)
        self.actions.append(self.hgBookmarkMoveAct)
        
        self.hgBookmarkIncomingAct = E5Action(
            self.tr('Show incoming bookmarks'),
            UI.PixmapCache.getIcon("incomingBookmark.png"),
            self.tr('Show incoming bookmarks'),
            0, 0, self, 'mercurial_incoming_bookmarks')
        self.hgBookmarkIncomingAct.setStatusTip(self.tr(
            'Show a list of incoming bookmarks'
        ))
        self.hgBookmarkIncomingAct.setWhatsThis(self.tr(
            """<b>Show incoming bookmarks</b>"""
            """<p>This shows a list of new bookmarks available at the remote"""
            """ repository.</p>"""
        ))
        self.hgBookmarkIncomingAct.triggered.connect(
            self.__hgBookmarkIncoming)
        self.actions.append(self.hgBookmarkIncomingAct)
        
        self.hgBookmarkPullAct = E5Action(
            self.tr('Pull bookmark'),
            UI.PixmapCache.getIcon("pullBookmark.png"),
            self.tr('Pull bookmark'),
            0, 0, self, 'mercurial_pull_bookmark')
        self.hgBookmarkPullAct.setStatusTip(self.tr(
            'Pull a bookmark from a remote repository'
        ))
        self.hgBookmarkPullAct.setWhatsThis(self.tr(
            """<b>Pull bookmark</b>"""
            """<p>This pulls a bookmark from a remote repository into the """
            """local repository.</p>"""
        ))
        self.hgBookmarkPullAct.triggered.connect(self.__hgBookmarkPull)
        self.actions.append(self.hgBookmarkPullAct)
        
        self.hgBookmarkOutgoingAct = E5Action(
            self.tr('Show outgoing bookmarks'),
            UI.PixmapCache.getIcon("outgoingBookmark.png"),
            self.tr('Show outgoing bookmarks'),
            0, 0, self, 'mercurial_outgoing_bookmarks')
        self.hgBookmarkOutgoingAct.setStatusTip(self.tr(
            'Show a list of outgoing bookmarks'
        ))
        self.hgBookmarkOutgoingAct.setWhatsThis(self.tr(
            """<b>Show outgoing bookmarks</b>"""
            """<p>This shows a list of new bookmarks available at the local"""
            """ repository.</p>"""
        ))
        self.hgBookmarkOutgoingAct.triggered.connect(
            self.__hgBookmarkOutgoing)
        self.actions.append(self.hgBookmarkOutgoingAct)
        
        self.hgBookmarkPushAct = E5Action(
            self.tr('Push bookmark'),
            UI.PixmapCache.getIcon("pushBookmark.png"),
            self.tr('Push bookmark'),
            0, 0, self, 'mercurial_push_bookmark')
        self.hgBookmarkPushAct.setStatusTip(self.tr(
            'Push a bookmark to a remote repository'
        ))
        self.hgBookmarkPushAct.setWhatsThis(self.tr(
            """<b>Push bookmark</b>"""
            """<p>This pushes a bookmark from the local repository to a """
            """remote repository.</p>"""
        ))
        self.hgBookmarkPushAct.triggered.connect(self.__hgBookmarkPush)
        self.actions.append(self.hgBookmarkPushAct)
    
    def __checkActions(self):
        """
        Private slot to set the enabled status of actions.
        """
        self.hgPullAct.setEnabled(self.vcs.canPull())
        self.hgIncomingAct.setEnabled(self.vcs.canPull())
        self.hgBookmarkPullAct.setEnabled(self.vcs.canPull())
        self.hgBookmarkIncomingAct.setEnabled(self.vcs.canPull())
        
        self.hgPushAct.setEnabled(self.vcs.canPush())
        self.hgPushBranchAct.setEnabled(self.vcs.canPush())
        self.hgPushForcedAct.setEnabled(self.vcs.canPush())
        self.hgOutgoingAct.setEnabled(self.vcs.canPush())
        self.hgBookmarkPushAct.setEnabled(self.vcs.canPush())
        self.hgBookmarkOutgoingAct.setEnabled(self.vcs.canPush())
    
    def initMenu(self, menu):
        """
        Public method to generate the VCS menu.
        
        @param menu reference to the menu to be populated (QMenu)
        """
        menu.clear()
        
        self.subMenus = []
        
        adminMenu = QMenu(self.tr("Administration"), menu)
        adminMenu.setTearOffEnabled(True)
        adminMenu.addAction(self.hgHeadsAct)
        adminMenu.addAction(self.hgParentsAct)
        adminMenu.addAction(self.hgTipAct)
        adminMenu.addAction(self.hgShowBranchAct)
        adminMenu.addAction(self.hgIdentifyAct)
        adminMenu.addSeparator()
        adminMenu.addAction(self.hgShowPathsAct)
        adminMenu.addSeparator()
        adminMenu.addAction(self.hgShowConfigAct)
        adminMenu.addAction(self.hgRepoConfigAct)
        adminMenu.addSeparator()
        adminMenu.addAction(self.hgCreateIgnoreAct)
        adminMenu.addSeparator()
        adminMenu.addAction(self.hgRecoverAct)
        adminMenu.addSeparator()
        adminMenu.addAction(self.hgBackoutAct)
        adminMenu.addAction(self.hgRollbackAct)
        adminMenu.addSeparator()
        adminMenu.addAction(self.hgVerifyAct)
        self.subMenus.append(adminMenu)
        
        specialsMenu = QMenu(self.tr("Specials"), menu)
        specialsMenu.setTearOffEnabled(True)
        specialsMenu.addAction(self.hgArchiveAct)
        specialsMenu.addSeparator()
        specialsMenu.addAction(self.hgPushForcedAct)
        specialsMenu.addSeparator()
        specialsMenu.addAction(self.hgServeAct)
        self.subMenus.append(specialsMenu)
        
        bundleMenu = QMenu(self.tr("Changegroup Management"), menu)
        bundleMenu.setTearOffEnabled(True)
        bundleMenu.addAction(self.hgBundleAct)
        bundleMenu.addAction(self.hgPreviewBundleAct)
        bundleMenu.addAction(self.hgUnbundleAct)
        self.subMenus.append(bundleMenu)
        
        patchMenu = QMenu(self.tr("Patch Management"), menu)
        patchMenu.setTearOffEnabled(True)
        patchMenu.addAction(self.hgImportAct)
        patchMenu.addAction(self.hgExportAct)
        self.subMenus.append(patchMenu)
        
        bisectMenu = QMenu(self.tr("Bisect"), menu)
        bisectMenu.setTearOffEnabled(True)
        bisectMenu.addAction(self.hgBisectGoodAct)
        bisectMenu.addAction(self.hgBisectBadAct)
        bisectMenu.addAction(self.hgBisectSkipAct)
        bisectMenu.addAction(self.hgBisectResetAct)
        self.subMenus.append(bisectMenu)
        
        tagsMenu = QMenu(self.tr("Tags"), menu)
        tagsMenu.setIcon(UI.PixmapCache.getIcon("vcsTag.png"))
        tagsMenu.setTearOffEnabled(True)
        tagsMenu.addAction(self.vcsTagAct)
        tagsMenu.addAction(self.hgTagListAct)
        self.subMenus.append(tagsMenu)
        
        branchesMenu = QMenu(self.tr("Branches"), menu)
        branchesMenu.setIcon(UI.PixmapCache.getIcon("vcsBranch.png"))
        branchesMenu.setTearOffEnabled(True)
        branchesMenu.addAction(self.hgBranchAct)
        branchesMenu.addAction(self.hgPushBranchAct)
        branchesMenu.addAction(self.hgCloseBranchAct)
        branchesMenu.addAction(self.hgBranchListAct)
        self.subMenus.append(branchesMenu)
        
        bookmarksMenu = QMenu(self.tr("Bookmarks"), menu)
        bookmarksMenu.setIcon(UI.PixmapCache.getIcon("bookmark22.png"))
        bookmarksMenu.setTearOffEnabled(True)
        bookmarksMenu.addAction(self.hgBookmarkDefineAct)
        bookmarksMenu.addAction(self.hgBookmarkDeleteAct)
        bookmarksMenu.addAction(self.hgBookmarkRenameAct)
        bookmarksMenu.addAction(self.hgBookmarkMoveAct)
        bookmarksMenu.addSeparator()
        bookmarksMenu.addAction(self.hgBookmarksListAct)
        bookmarksMenu.addSeparator()
        bookmarksMenu.addAction(self.hgBookmarkIncomingAct)
        bookmarksMenu.addAction(self.hgBookmarkPullAct)
        bookmarksMenu.addSeparator()
        bookmarksMenu.addAction(self.hgBookmarkOutgoingAct)
        bookmarksMenu.addAction(self.hgBookmarkPushAct)
        self.subMenus.append(bookmarksMenu)
        
        self.__extensionsMenu = QMenu(self.tr("Extensions"), menu)
        self.__extensionsMenu.setTearOffEnabled(True)
        self.__extensionsMenu.aboutToShow.connect(self.__showExtensionMenu)
        self.extensionMenus = {}
        for extensionMenuTitle in sorted(self.__extensionMenuTitles):
            extensionName = self.__extensionMenuTitles[extensionMenuTitle]
            self.extensionMenus[extensionName] = self.__extensionsMenu.addMenu(
                self.__extensions[extensionName].initMenu(
                    self.__extensionsMenu))
        self.vcs.activeExtensionsChanged.connect(self.__showExtensionMenu)
        
        if self.vcs.version >= (2, 0):
            graftMenu = QMenu(self.tr("Graft"), menu)
            graftMenu.setIcon(UI.PixmapCache.getIcon("vcsGraft.png"))
            graftMenu.setTearOffEnabled(True)
            graftMenu.addAction(self.hgGraftAct)
            graftMenu.addAction(self.hgGraftContinueAct)
        else:
            graftMenu = None
        
        subrepoMenu = QMenu(self.tr("Sub-Repository"), menu)
        subrepoMenu.setTearOffEnabled(True)
        subrepoMenu.addAction(self.hgAddSubrepoAct)
        subrepoMenu.addAction(self.hgRemoveSubreposAct)
        
        changesMenu = QMenu(self.tr("Manage Changes"), menu)
        changesMenu.setTearOffEnabled(True)
        changesMenu.addAction(self.vcsRevertAct)
        changesMenu.addSeparator()
        changesMenu.addAction(self.vcsMergeAct)
        changesMenu.addAction(self.hgShowConflictsAct)
        changesMenu.addAction(self.vcsResolveAct)
        changesMenu.addAction(self.hgUnresolveAct)
        changesMenu.addAction(self.hgReMergeAct)
        changesMenu.addAction(self.hgCancelMergeAct)
        if self.vcs.version >= (2, 1):
            changesMenu.addSeparator()
            changesMenu.addAction(self.hgPhaseAct)
        
        act = menu.addAction(
            UI.PixmapCache.getIcon(
                os.path.join("VcsPlugins", "vcsMercurial", "icons",
                             "mercurial.png")),
            self.vcs.vcsName(), self._vcsInfoDisplay)
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        menu.addSeparator()
        
        menu.addAction(self.hgIncomingAct)
        menu.addAction(self.hgPullAct)
        menu.addAction(self.vcsUpdateAct)
        menu.addSeparator()
        menu.addAction(self.vcsCommitAct)
        menu.addAction(self.hgOutgoingAct)
        menu.addAction(self.hgPushAct)
        menu.addSeparator()
        menu.addMenu(changesMenu)
        menu.addSeparator()
        if graftMenu is not None:
            menu.addMenu(graftMenu)
            menu.addSeparator()
        menu.addMenu(bundleMenu)
        menu.addMenu(patchMenu)
        menu.addSeparator()
        menu.addMenu(tagsMenu)
        menu.addMenu(branchesMenu)
        menu.addMenu(bookmarksMenu)
        menu.addSeparator()
        menu.addAction(self.vcsLogAct)
        menu.addAction(self.hgLogBrowserAct)
        menu.addSeparator()
        menu.addAction(self.vcsStatusAct)
        menu.addAction(self.hgSummaryAct)
        menu.addSeparator()
        menu.addAction(self.vcsDiffAct)
        menu.addAction(self.hgExtDiffAct)
        menu.addSeparator()
        menu.addMenu(self.__extensionsMenu)
        menu.addSeparator()
        menu.addAction(self.vcsSwitchAct)
        menu.addSeparator()
        menu.addMenu(subrepoMenu)
        menu.addSeparator()
        menu.addMenu(bisectMenu)
        menu.addSeparator()
        menu.addAction(self.vcsCleanupAct)
        menu.addSeparator()
        menu.addAction(self.vcsCommandAct)
        menu.addSeparator()
        menu.addMenu(adminMenu)
        menu.addMenu(specialsMenu)
        menu.addSeparator()
        menu.addAction(self.hgEditUserConfigAct)
        menu.addAction(self.hgConfigAct)
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
        self.__toolbar = QToolBar(self.tr("Mercurial"), ui)
        self.__toolbar.setIconSize(UI.Config.ToolBarIconSize)
        self.__toolbar.setObjectName("MercurialToolbar")
        self.__toolbar.setToolTip(self.tr('Mercurial'))
        
        self.__toolbar.addAction(self.hgLogBrowserAct)
        self.__toolbar.addAction(self.vcsStatusAct)
        self.__toolbar.addSeparator()
        self.__toolbar.addAction(self.vcsDiffAct)
        self.__toolbar.addSeparator()
        self.__toolbar.addAction(self.vcsNewAct)
        self.__toolbar.addAction(self.vcsExportAct)
        self.__toolbar.addSeparator()
        
        title = self.__toolbar.windowTitle()
        toolbarManager.addToolBar(self.__toolbar, title)
        toolbarManager.addAction(self.hgPullAct, title)
        toolbarManager.addAction(self.vcsUpdateAct, title)
        toolbarManager.addAction(self.vcsCommitAct, title)
        toolbarManager.addAction(self.hgPushAct, title)
        toolbarManager.addAction(self.hgPushForcedAct, title)
        toolbarManager.addAction(self.vcsLogAct, title)
        toolbarManager.addAction(self.hgExtDiffAct, title)
        toolbarManager.addAction(self.hgSummaryAct, title)
        toolbarManager.addAction(self.vcsRevertAct, title)
        toolbarManager.addAction(self.vcsMergeAct, title)
        toolbarManager.addAction(self.hgReMergeAct, title)
        toolbarManager.addAction(self.vcsTagAct, title)
        toolbarManager.addAction(self.hgBranchAct, title)
        toolbarManager.addAction(self.vcsSwitchAct, title)
        toolbarManager.addAction(self.hgGraftAct, title)
        toolbarManager.addAction(self.hgAddSubrepoAct, title)
        toolbarManager.addAction(self.hgRemoveSubreposAct, title)
        toolbarManager.addAction(self.hgArchiveAct, title)
        toolbarManager.addAction(self.hgBookmarksListAct, title)
        toolbarManager.addAction(self.hgBookmarkDefineAct, title)
        toolbarManager.addAction(self.hgBookmarkDeleteAct, title)
        toolbarManager.addAction(self.hgBookmarkRenameAct, title)
        toolbarManager.addAction(self.hgBookmarkMoveAct, title)
        toolbarManager.addAction(self.hgBookmarkPullAct, title)
        toolbarManager.addAction(self.hgBookmarkPushAct, title)
        
        self.__toolbar.setEnabled(False)
        self.__toolbar.setVisible(False)
        
        ui.registerToolbar("mercurial", self.__toolbar.windowTitle(),
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
        ui.unregisterToolbar("mercurial")
        
        title = self.__toolbar.windowTitle()
        toolbarManager.removeCategoryActions(title)
        toolbarManager.removeToolBar(self.__toolbar)
        
        self.__toolbar.deleteLater()
        self.__toolbar = None
    
    def showMenu(self):
        """
        Public slot called before the vcs menu is shown.
        """
        super(HgProjectHelper, self).showMenu()
        
        self.__checkActions()
    
    def shutdown(self):
        """
        Public method to perform shutdown actions.
        """
        self.vcs.activeExtensionsChanged.disconnect(self.__showExtensionMenu)
        self.vcs.iniFileChanged.disconnect(self.__checkActions)
        
        # close torn off sub menus
        for menu in self.subMenus:
            if menu.isTearOffMenuVisible():
                menu.hideTearOffMenu()
        
        # close torn off extension menus
        for extensionName in self.extensionMenus:
            self.__extensions[extensionName].shutdown()
            menu = self.extensionMenus[extensionName].menu()
            if menu.isTearOffMenuVisible():
                menu.hideTearOffMenu()
        
        if self.__extensionsMenu.isTearOffMenuVisible():
            self.__extensionsMenu.hideTearOffMenu()
    
    def __showExtensionMenu(self):
        """
        Private slot showing the extensions menu.
        """
        for extensionName in self.extensionMenus:
            self.extensionMenus[extensionName].setEnabled(
                self.vcs.isExtensionActive(extensionName))
            if not self.extensionMenus[extensionName].isEnabled() and \
                    self.extensionMenus[extensionName].menu()\
                        .isTearOffMenuVisible():
                self.extensionMenus[extensionName].menu().hideTearOffMenu()
    
    def __hgExtendedDiff(self):
        """
        Private slot used to perform a hg diff with the selection of revisions.
        """
        self.vcs.hgExtendedDiff(self.project.ppath)
    
    def __hgIncoming(self):
        """
        Private slot used to show the log of changes coming into the
        repository.
        """
        self.vcs.hgIncoming(self.project.ppath)
    
    def __hgOutgoing(self):
        """
        Private slot used to show the log of changes going out of the
        repository.
        """
        self.vcs.hgOutgoing(self.project.ppath)
    
    def __hgPull(self):
        """
        Private slot used to pull changes from a remote repository.
        """
        shouldReopen = self.vcs.hgPull(self.project.ppath)
        if shouldReopen:
            res = E5MessageBox.yesNo(
                self.parent(),
                self.tr("Pull"),
                self.tr("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgPush(self):
        """
        Private slot used to push changes to a remote repository.
        """
        self.vcs.hgPush(self.project.ppath)
    
    def __hgPushForced(self):
        """
        Private slot used to push changes to a remote repository using
        the force option.
        """
        self.vcs.hgPush(self.project.ppath, force=True)
    
    def __hgHeads(self):
        """
        Private slot used to show the heads of the repository.
        """
        self.vcs.hgInfo(self.project.ppath, mode="heads")
    
    def __hgParents(self):
        """
        Private slot used to show the parents of the repository.
        """
        self.vcs.hgInfo(self.project.ppath, mode="parents")
    
    def __hgTip(self):
        """
        Private slot used to show the tip of the repository.
        """
        self.vcs.hgInfo(self.project.ppath, mode="tip")
    
    def __hgResolved(self):
        """
        Private slot used to mark conflicts of the local project as being
        resolved.
        """
        self.vcs.hgResolved(self.project.ppath)
    
    def __hgUnresolved(self):
        """
        Private slot used to mark conflicts of the local project as being
        unresolved.
        """
        self.vcs.hgResolved(self.project.ppath, unresolve=True)
    
    def __hgCancelMerge(self):
        """
        Private slot used to cancel an uncommitted merge.
        """
        self.vcs.hgCancelMerge(self.project.ppath)
    
    def __hgShowConflicts(self):
        """
        Private slot used to list all files with conflicts.
        """
        self.vcs.hgConflicts(self.project.ppath)
    
    def __hgReMerge(self):
        """
        Private slot used to list all files with conflicts.
        """
        self.vcs.hgReMerge(self.project.ppath)
    
    def __hgTagList(self):
        """
        Private slot used to list the tags of the project.
        """
        self.vcs.hgListTagBranch(self.project.ppath, True)
    
    def __hgBranchList(self):
        """
        Private slot used to list the branches of the project.
        """
        self.vcs.hgListTagBranch(self.project.ppath, False)
    
    def __hgBranch(self):
        """
        Private slot used to create a new branch for the project.
        """
        self.vcs.hgBranch(self.project.ppath)
    
    def __hgShowBranch(self):
        """
        Private slot used to show the current branch for the project.
        """
        self.vcs.hgShowBranch(self.project.ppath)
    
    def __hgConfigure(self):
        """
        Private method to open the configuration dialog.
        """
        e5App().getObject("UserInterface").showPreferences("zzz_mercurialPage")
    
    def __hgCloseBranch(self):
        """
        Private slot used to close the current branch of the local project.
        """
        if Preferences.getVCS("AutoSaveProject"):
            self.project.saveProject()
        if Preferences.getVCS("AutoSaveFiles"):
            self.project.saveAllScripts()
        self.vcs.vcsCommit(self.project.ppath, '', closeBranch=True)
    
    def __hgPushNewBranch(self):
        """
        Private slot to push a new named branch.
        """
        self.vcs.hgPush(self.project.ppath, newBranch=True)
    
    def __hgEditUserConfig(self):
        """
        Private slot used to edit the user configuration file.
        """
        self.vcs.hgEditUserConfig()
    
    def __hgEditRepoConfig(self):
        """
        Private slot used to edit the repository configuration file.
        """
        self.vcs.hgEditConfig(self.project.ppath)
    
    def __hgShowConfig(self):
        """
        Private slot used to show the combined configuration.
        """
        self.vcs.hgShowConfig(self.project.ppath)
    
    def __hgVerify(self):
        """
        Private slot used to verify the integrity of the repository.
        """
        self.vcs.hgVerify(self.project.ppath)
    
    def __hgShowPaths(self):
        """
        Private slot used to show the aliases for remote repositories.
        """
        self.vcs.hgShowPaths(self.project.ppath)
    
    def __hgRecover(self):
        """
        Private slot used to recover from an interrupted transaction.
        """
        self.vcs.hgRecover(self.project.ppath)
    
    def __hgIdentify(self):
        """
        Private slot used to identify the project directory.
        """
        self.vcs.hgIdentify(self.project.ppath)
    
    def __hgCreateIgnore(self):
        """
        Private slot used to create a .hgignore file for the project.
        """
        self.vcs.hgCreateIgnoreFile(self.project.ppath, autoAdd=True)
    
    def __hgBundle(self):
        """
        Private slot used to create a changegroup file.
        """
        self.vcs.hgBundle(self.project.ppath)
    
    def __hgPreviewBundle(self):
        """
        Private slot used to preview a changegroup file.
        """
        self.vcs.hgPreviewBundle(self.project.ppath)
    
    def __hgUnbundle(self):
        """
        Private slot used to apply changegroup files.
        """
        shouldReopen = self.vcs.hgUnbundle(self.project.ppath)
        if shouldReopen:
            res = E5MessageBox.yesNo(
                self.parent(),
                self.tr("Apply changegroups"),
                self.tr("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgBisectGood(self):
        """
        Private slot used to execute the bisect --good command.
        """
        self.vcs.hgBisect(self.project.ppath, "good")
    
    def __hgBisectBad(self):
        """
        Private slot used to execute the bisect --bad command.
        """
        self.vcs.hgBisect(self.project.ppath, "bad")
    
    def __hgBisectSkip(self):
        """
        Private slot used to execute the bisect --skip command.
        """
        self.vcs.hgBisect(self.project.ppath, "skip")
    
    def __hgBisectReset(self):
        """
        Private slot used to execute the bisect --reset command.
        """
        self.vcs.hgBisect(self.project.ppath, "reset")
    
    def __hgBackout(self):
        """
        Private slot used to back out changes of a changeset.
        """
        self.vcs.hgBackout(self.project.ppath)
    
    def __hgRollback(self):
        """
        Private slot used to rollback the last transaction.
        """
        self.vcs.hgRollback(self.project.ppath)
    
    def __hgServe(self):
        """
        Private slot used to serve the project.
        """
        self.vcs.hgServe(self.project.ppath)
    
    def __hgImport(self):
        """
        Private slot used to import a patch file.
        """
        shouldReopen = self.vcs.hgImport(self.project.ppath)
        if shouldReopen:
            res = E5MessageBox.yesNo(
                self.parent(),
                self.tr("Import Patch"),
                self.tr("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgExport(self):
        """
        Private slot used to export revisions to patch files.
        """
        self.vcs.hgExport(self.project.ppath)
    
    def __hgRevert(self):
        """
        Private slot used to revert changes made to the local project.
        """
        shouldReopen = self.vcs.hgRevert(self.project.ppath)
        if shouldReopen:
            res = E5MessageBox.yesNo(
                self.parent(),
                self.tr("Revert Changes"),
                self.tr("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgPhase(self):
        """
        Private slot used to change the phase of revisions.
        """
        self.vcs.hgPhase(self.project.ppath)
    
    def __hgGraft(self):
        """
        Private slot used to copy changesets from another branch.
        """
        shouldReopen = self.vcs.hgGraft(self.project.getProjectPath())
        if shouldReopen:
            res = E5MessageBox.yesNo(
                None,
                self.tr("Copy Changesets"),
                self.tr("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgGraftContinue(self):
        """
        Private slot used to continue the last copying session after conflicts
        were resolved.
        """
        shouldReopen = self.vcs.hgGraftContinue(self.project.getProjectPath())
        if shouldReopen:
            res = E5MessageBox.yesNo(
                None,
                self.tr("Copy Changesets (Continue)"),
                self.tr("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgAddSubrepository(self):
        """
        Private slot used to add a sub-repository.
        """
        self.vcs.hgAddSubrepository()
    
    def __hgRemoveSubrepositories(self):
        """
        Private slot used to remove sub-repositories.
        """
        self.vcs.hgRemoveSubrepositories()
    
    def __hgSummary(self):
        """
        Private slot to show a working directory summary.
        """
        self.vcs.hgSummary()
    
    def __hgArchive(self):
        """
        Private slot to create an unversioned archive from the repository.
        """
        self.vcs.hgArchive()
    
    def __hgBookmarksList(self):
        """
        Private slot used to list the bookmarks.
        """
        self.vcs.hgListBookmarks(self.project.getProjectPath())
    
    def __hgBookmarkDefine(self):
        """
        Private slot used to define a bookmark.
        """
        self.vcs.hgBookmarkDefine(self.project.getProjectPath())
    
    def __hgBookmarkDelete(self):
        """
        Private slot used to delete a bookmark.
        """
        self.vcs.hgBookmarkDelete(self.project.getProjectPath())
    
    def __hgBookmarkRename(self):
        """
        Private slot used to rename a bookmark.
        """
        self.vcs.hgBookmarkRename(self.project.getProjectPath())
    
    def __hgBookmarkMove(self):
        """
        Private slot used to move a bookmark.
        """
        self.vcs.hgBookmarkMove(self.project.getProjectPath())
    
    def __hgBookmarkIncoming(self):
        """
        Private slot used to show a list of incoming bookmarks.
        """
        self.vcs.hgBookmarkIncoming(self.project.getProjectPath())
    
    def __hgBookmarkOutgoing(self):
        """
        Private slot used to show a list of outgoing bookmarks.
        """
        self.vcs.hgBookmarkOutgoing(self.project.getProjectPath())
    
    def __hgBookmarkPull(self):
        """
        Private slot used to pull a bookmark from a remote repository.
        """
        self.vcs.hgBookmarkPull(self.project.getProjectPath())
    
    def __hgBookmarkPush(self):
        """
        Private slot used to push a bookmark to a remote repository.
        """
        self.vcs.hgBookmarkPush(self.project.getProjectPath())
