# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the transplant extension interface.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtWidgets import QDialog

from ..HgExtension import HgExtension
from ..HgDialog import HgDialog


class Transplant(HgExtension):
    """
    Class implementing the transplant extension interface.
    """
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        super(Transplant, self).__init__(vcs)
    
    def hgTransplant(self, path):
        """
        Public method to transplant changesets from another branch.
        
        @param path directory name of the project (string)
        @return flag indicating that the project should be reread (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(path)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        from .TransplantDialog import TransplantDialog
        res = False
        dlg = TransplantDialog(self.vcs.hgGetBranchesList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            revs, sourceRepo, branch, all, pruneRevs, mergeRevs, log = \
                dlg.getData()
            
            args = self.vcs.initCommand("transplant")
            args.append("--verbose")
            if sourceRepo:
                args.append("--source")
                args.append(sourceRepo)
            if branch:
                args.append("--branch")
                args.append(branch)
                if all:
                    args.append("--all")
            for pruneRev in pruneRevs:
                args.append("--prune")
                args.append(pruneRev)
            for mergeRev in mergeRevs:
                args.append("--merge")
                args.append(mergeRev)
            if log:
                args.append("--log")
            args.extend(revs)
            
            dia = HgDialog(self.tr('Transplant Changesets'), self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.hasAddOrDelete()
                self.vcs.checkVCSStatus()
        return res
    
    def hgTransplantContinue(self, path):
        """
        Public method to continue transplanting changesets from another branch.
        
        @param path directory name of the project (string)
        @return flag indicating that the project should be reread (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(path)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.vcs.initCommand("transplant")
        args.append("--continue")
        args.append("--verbose")
        
        dia = HgDialog(
            self.tr('Transplant Changesets (Continue)'), self.vcs)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            res = dia.hasAddOrDelete()
            self.vcs.checkVCSStatus()
        return res
