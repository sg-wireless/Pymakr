# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the purge extension interface.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import QDialog

from ..HgExtension import HgExtension
from ..HgDialog import HgDialog


class Purge(HgExtension):
    """
    Class implementing the purge extension interface.
    """
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        super(Purge, self).__init__(vcs)
        
        self.purgeListDialog = None
    
    def shutdown(self):
        """
        Public method used to shutdown the purge interface.
        """
        if self.purgeListDialog is not None:
            self.purgeListDialog.close()
    
    def __getEntries(self, repodir, all):
        """
        Private method to get a list of files/directories being purged.
        
        @param repodir directory name of the repository (string)
        @param all flag indicating to delete all files including ignored ones
            (boolean)
        @return name of the current patch (string)
        """
        purgeEntries = []
        
        args = self.vcs.initCommand("purge")
        args.append("--print")
        if all:
            args.append("--all")
        
        client = self.vcs.getClient()
        if client:
            out, err = client.runcommand(args)
            if out:
                purgeEntries = out.strip().split()
        else:
            process = QProcess()
            process.setWorkingDirectory(repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    purgeEntries = str(
                        process.readAllStandardOutput(),
                        self.vcs.getEncoding(), 'replace').strip().split()
        
        return purgeEntries
    
    def hgPurge(self, name, all=False):
        """
        Public method to purge files and directories not tracked by Mercurial.
        
        @param name file/directory name (string)
        @param all flag indicating to delete all files including ignored ones
            (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        if all:
            title = self.tr("Purge All Files")
            message = self.tr(
                """Do really want to delete all files not tracked by"""
                """ Mercurial (including ignored ones)?""")
        else:
            title = self.tr("Purge Files")
            message = self.tr(
                """Do really want to delete files not tracked by Mercurial?""")
        entries = self.__getEntries(repodir, all)
        from UI.DeleteFilesConfirmationDialog import \
            DeleteFilesConfirmationDialog
        dlg = DeleteFilesConfirmationDialog(None, title, message, entries)
        if dlg.exec_() == QDialog.Accepted:
            args = self.vcs.initCommand("purge")
            if all:
                args.append("--all")
            args.append("-v")
            
            dia = HgDialog(title, self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgPurgeList(self, name, all=False):
        """
        Public method to list files and directories not tracked by Mercurial.
        
        @param name file/directory name (string)
        @param all flag indicating to list all files including ignored ones
            (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        entries = self.__getEntries(repodir, all)
        from .HgPurgeListDialog import HgPurgeListDialog
        self.purgeListDialog = HgPurgeListDialog(entries)
        self.purgeListDialog.show()
