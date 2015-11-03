# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the shelve extension interface.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import QDialog

from E5Gui import E5MessageBox

from ..HgExtension import HgExtension
from ..HgDialog import HgDialog


class Shelve(HgExtension):
    """
    Class implementing the shelve extension interface.
    """
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        super(Shelve, self).__init__(vcs)
        
        self.__unshelveKeep = False
        
        self.__shelveBrowserDialog = None
    
    def shutdown(self):
        """
        Public method used to shutdown the shelve interface.
        """
        if self.__shelveBrowserDialog is not None:
            self.__shelveBrowserDialog.close()
    
    def __hgGetShelveNamesList(self, repodir):
        """
        Private method to get the list of shelved changes.
        
        @param repodir directory name of the repository (string)
        @return list of shelved changes (list of string)
        """
        args = self.vcs.initCommand("shelve")
        args.append('--list')
        args.append('--quiet')
        
        client = self.vcs.getClient()
        output = ""
        if client:
            output = client.runcommand(args)[0]
        else:
            process = QProcess()
            process.setWorkingDirectory(repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.vcs.getEncoding(), 'replace')
        
        shelveNamesList = []
        for line in output.splitlines():
            shelveNamesList.append(line.strip())
        
        return shelveNamesList[:]
    
    def hgShelve(self, name):
        """
        Public method to shelve current changes of files or directories.
        
        @param name directory or file name (string) or list of directory
            or file names (list of string)
        @return flag indicating that the project should be reread (boolean)
        """
        if isinstance(name, list):
            dname = self.vcs.splitPathList(name)[0]
        else:
            dname = self.vcs.splitPath(name)[0]
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        res = False
        from .HgShelveDataDialog import HgShelveDataDialog
        dlg = HgShelveDataDialog()
        if dlg.exec_() == QDialog.Accepted:
            shelveName, dateTime, message, addRemove = dlg.getData()
            
            args = self.vcs.initCommand("shelve")
            if shelveName:
                args.append("--name")
                args.append(shelveName)
            if message:
                args.append("--message")
                args.append(message)
            if addRemove:
                args.append("--addRemove")
            if dateTime.isValid():
                args.append("--date")
                args.append(dateTime.toString("yyyy-MM-dd hh:mm:ss"))
            args.append("-v")
            
            if isinstance(name, list):
                self.vcs.addArguments(args, name)
            else:
                args.append(name)
            
            dia = HgDialog(self.tr('Shelve current changes'), self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.hasAddOrDelete()
                self.vcs.checkVCSStatus()
        return res
    
    def hgShelveBrowser(self, projectDir):
        """
        Public method to show the shelve browser dialog.
        
        @param projectDir name of the project directory (string)
        """
        if self.__shelveBrowserDialog is None:
            from .HgShelveBrowserDialog import HgShelveBrowserDialog
            self.__shelveBrowserDialog = HgShelveBrowserDialog(
                self.vcs)
        self.__shelveBrowserDialog.show()
        self.__shelveBrowserDialog.start(projectDir)
    
    def hgUnshelve(self, name, shelveName=""):
        """
        Public method to restore shelved changes to the project directory.
        
        @param name name of the project directory (string)
        @keyparam shelveName name of the shelve to restore (string)
        @return flag indicating that the project should be reread (boolean)
        """
        # find the root of the repo
        repodir = name
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        res = False
        from .HgUnshelveDataDialog import HgUnshelveDataDialog
        dlg = HgUnshelveDataDialog(self.__hgGetShelveNamesList(repodir),
                                   shelveName=shelveName)
        if dlg.exec_() == QDialog.Accepted:
            shelveName, keep = dlg.getData()
            self.__unshelveKeep = keep  # store for potential continue
            
            args = self.vcs.initCommand("unshelve")
            if keep:
                args.append("--keep")
            if shelveName:
                args.append(shelveName)
            
            dia = HgDialog(self.tr('Restore shelved changes'), self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.hasAddOrDelete()
                self.vcs.checkVCSStatus()
        return res
    
    def hgUnshelveAbort(self, name):
        """
        Public method to abort the ongoing restore operation.
        
        @param name name of the project directory (string)
        @return flag indicating that the project should be reread (boolean)
        """
        # find the root of the repo
        repodir = name
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        args = self.vcs.initCommand("unshelve")
        args.append("--abort")
        
        dia = HgDialog(self.tr('Abort restore operation'), self.vcs)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            res = dia.hasAddOrDelete()
            self.vcs.checkVCSStatus()
        return res
    
    def hgUnshelveContinue(self, name):
        """
        Public method to continue the ongoing restore operation.
        
        @param name name of the project directory (string)
        @return flag indicating that the project should be reread (boolean)
        """
        # find the root of the repo
        repodir = name
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        args = self.vcs.initCommand("unshelve")
        if self.__unshelveKeep:
            args.append("--keep")
        args.append("--continue")
        
        dia = HgDialog(self.tr('Continue restore operation'), self.vcs)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            res = dia.hasAddOrDelete()
            self.vcs.checkVCSStatus()
        return res
    
    def hgDeleteShelves(self, name, shelveNames=None):
        """
        Public method to delete named shelves.
        
        @param name name of the project directory (string)
        @param shelveNames name of shelves to delete (list of string)
        """
        # find the root of the repo
        repodir = name
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        if not shelveNames:
            from .HgShelvesSelectionDialog import HgShelvesSelectionDialog
            dlg = HgShelvesSelectionDialog(
                self.tr("Select the shelves to be deleted:"),
                self.__hgGetShelveNamesList(repodir))
            if dlg.exec_() == QDialog.Accepted:
                shelveNames = dlg.getSelectedShelves()
            else:
                return
        
        from UI.DeleteFilesConfirmationDialog import \
            DeleteFilesConfirmationDialog
        dlg = DeleteFilesConfirmationDialog(
            None,
            self.tr("Delete shelves"),
            self.tr("Do you really want to delete these shelves?"),
            shelveNames)
        if dlg.exec_() == QDialog.Accepted:
            args = self.vcs.initCommand("shelve")
            args.append("--delete")
            args.extend(shelveNames)
            
            dia = HgDialog(self.tr('Delete shelves'), self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgCleanupShelves(self, name):
        """
        Public method to delete all shelves.
        
        @param name name of the project directory (string)
        """
        # find the root of the repo
        repodir = name
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        res = E5MessageBox.yesNo(
            None,
            self.tr("Delete all shelves"),
            self.tr("""Do you really want to delete all shelved changes?"""))
        if res:
            args = self.vcs.initCommand("shelve")
            args.append("--cleanup")
            
            dia = HgDialog(self.tr('Delete all shelves'), self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
