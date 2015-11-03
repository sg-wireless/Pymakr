# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the rebase extension interface.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtWidgets import QDialog

from ..HgExtension import HgExtension
from ..HgDialog import HgDialog


class Rebase(HgExtension):
    """
    Class implementing the rebase extension interface.
    """
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        super(Rebase, self).__init__(vcs)
    
    def hgRebase(self, path):
        """
        Public method to rebase changesets to a different branch.
        
        @param path directory name of the project (string)
        @return flag indicating that the project should be reread (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(path)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        res = False
        from .HgRebaseDialog import HgRebaseDialog
        dlg = HgRebaseDialog(self.vcs.hgGetTagsList(repodir),
                             self.vcs.hgGetBranchesList(repodir),
                             self.vcs.hgGetBookmarksList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            (indicator, sourceRev, destRev, collapse, keep, keepBranches,
             detach) = dlg.getData()
            
            args = self.vcs.initCommand("rebase")
            if indicator == "S":
                args.append("--source")
                args.append(sourceRev)
            elif indicator == "B":
                args.append("--base")
                args.append(sourceRev)
            if destRev:
                args.append("--dest")
                args.append(destRev)
            if collapse:
                args.append("--collapse")
            if keep:
                args.append("--keep")
            if keepBranches:
                args.append("--keepbranches")
            if detach:
                args.append("--detach")
            args.append("--verbose")
            
            dia = HgDialog(self.tr('Rebase Changesets'), self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.hasAddOrDelete()
                self.vcs.checkVCSStatus()
        return res
    
    def hgRebaseContinue(self, path):
        """
        Public method to continue rebasing changesets from another branch.
        
        @param path directory name of the project (string)
        @return flag indicating that the project should be reread (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(path)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        args = self.vcs.initCommand("rebase")
        args.append("--continue")
        args.append("--verbose")
        
        dia = HgDialog(self.tr('Rebase Changesets (Continue)'), self.vcs)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            res = dia.hasAddOrDelete()
            self.vcs.checkVCSStatus()
        return res
    
    def hgRebaseAbort(self, path):
        """
        Public method to abort rebasing changesets from another branch.
        
        @param path directory name of the project (string)
        @return flag indicating that the project should be reread (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(path)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        args = self.vcs.initCommand("rebase")
        args.append("--abort")
        args.append("--verbose")
        
        dia = HgDialog(self.tr('Rebase Changesets (Abort)'), self.vcs)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            res = dia.hasAddOrDelete()
            self.vcs.checkVCSStatus()
        return res
