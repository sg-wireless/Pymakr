# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the gpg extension interface.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtWidgets import QDialog

from ..HgExtension import HgExtension
from ..HgDialog import HgDialog
from ..HgRevisionSelectionDialog import HgRevisionSelectionDialog


class Gpg(HgExtension):
    """
    Class implementing the fetch extension interface.
    """
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        super(Gpg, self).__init__(vcs)
        
        self.gpgSignaturesDialog = None
    
    def shutdown(self):
        """
        Public method used to shutdown the fetch interface.
        """
        if self.gpgSignaturesDialog is not None:
            self.gpgSignaturesDialog.close()
    
    def hgGpgSignatures(self, path):
        """
        Public method used to list all signed changesets.
        
        @param path directory name of the project (string)
        """
        from .HgGpgSignaturesDialog import HgGpgSignaturesDialog
        self.gpgSignaturesDialog = HgGpgSignaturesDialog(self.vcs)
        self.gpgSignaturesDialog.show()
        self.gpgSignaturesDialog.start(path)
    
    def hgGpgVerifySignatures(self, path, rev=None):
        """
        Public method used to verify the signatures of a revision.
        
        @param path directory name of the project (string)
        @param rev revision to check (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(path)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        if rev is None:
            dlg = HgRevisionSelectionDialog(
                self.vcs.hgGetTagsList(repodir),
                self.vcs.hgGetBranchesList(repodir),
                self.vcs.hgGetBookmarksList(repodir))
            if dlg.exec_() == QDialog.Accepted:
                rev = dlg.getRevision()
        
        if rev is not None:
            if rev == "":
                rev = "tip"
            args = self.vcs.initCommand("sigcheck")
            args.append(rev)
            
            dia = HgDialog(self.tr('Verify Signatures'), self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgGpgSign(self, path):
        """
        Public method used to list the available bookmarks.
        
        @param path directory name of the project (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(path)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgGpgSignDialog import HgGpgSignDialog
        dlg = HgGpgSignDialog(self.vcs.hgGetTagsList(repodir),
                              self.vcs.hgGetBranchesList(repodir),
                              self.vcs.hgGetBookmarksList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            revision, noCommit, message, keyId, local, force = dlg.getData()
            
            args = self.vcs.initCommand("sign")
            if noCommit:
                args.append("--no-commit")
            if message:
                args.append("--message")
                args.append(message)
            if keyId:
                args.append("--key")
                args.append(keyId)
            if local:
                args.append("--local")
            if force:
                args.append("--force")
            if revision:
                args.append(revision)
            
            dia = HgDialog(self.tr('Sign Revision'), self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
