# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the queues extension interface.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import QDialog, QApplication, QInputDialog

from E5Gui import E5MessageBox

from ..HgExtension import HgExtension
from ..HgDialog import HgDialog


class Queues(HgExtension):
    """
    Class implementing the queues extension interface.
    """
    APPLIED_LIST = 0
    UNAPPLIED_LIST = 1
    SERIES_LIST = 2
    
    POP = 0
    PUSH = 1
    GOTO = 2
    
    QUEUE_DELETE = 0
    QUEUE_PURGE = 1
    QUEUE_ACTIVATE = 2
    
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        super(Queues, self).__init__(vcs)
        
        self.qdiffDialog = None
        self.qheaderDialog = None
        self.queuesListDialog = None
        self.queuesListGuardsDialog = None
        self.queuesListAllGuardsDialog = None
        self.queuesDefineGuardsDialog = None
        self.queuesListQueuesDialog = None
        self.queueStatusDialog = None
    
    def shutdown(self):
        """
        Public method used to shutdown the queues interface.
        """
        if self.qdiffDialog is not None:
            self.qdiffDialog.close()
        if self.qheaderDialog is not None:
            self.qheaderDialog.close()
        if self.queuesListDialog is not None:
            self.queuesListDialog.close()
        if self.queuesListGuardsDialog is not None:
            self.queuesListGuardsDialog.close()
        if self.queuesListAllGuardsDialog is not None:
            self.queuesListAllGuardsDialog.close()
        if self.queuesDefineGuardsDialog is not None:
            self.queuesDefineGuardsDialog.close()
        if self.queuesListQueuesDialog is not None:
            self.queuesListQueuesDialog.close()
        if self.queueStatusDialog is not None:
            self.queueStatusDialog.close()
    
    def __getPatchesList(self, repodir, listType, withSummary=False):
        """
        Private method to get a list of patches of a given type.
        
        @param repodir directory name of the repository (string)
        @param listType type of patches list to get
            (Queues.APPLIED_LIST, Queues.UNAPPLIED_LIST, Queues.SERIES_LIST)
        @param withSummary flag indicating to get a summary as well (boolean)
        @return list of patches (list of string)
        @exception ValueError raised to indicate an invalid patch list type
        """
        patchesList = []
        
        if listType == Queues.APPLIED_LIST:
            args = self.vcs.initCommand("qapplied")
        elif listType == Queues.UNAPPLIED_LIST:
            args = self.vcs.initCommand("qunapplied")
        elif listType == Queues.SERIES_LIST:
            args = self.vcs.initCommand("qseries")
        else:
            raise ValueError("illegal value for listType")
        if withSummary:
            args.append("--summary")
        
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
        
        for line in output.splitlines():
            if withSummary:
                li = line.strip().split(": ")
                if len(li) == 1:
                    patch, summary = li[0][:-1], ""
                else:
                    patch, summary = li[0], li[1]
                patchesList.append("{0}@@{1}".format(patch, summary))
            else:
                patchesList.append(line.strip())
        
        return patchesList
    
    def __getCurrentPatch(self, repodir):
        """
        Private method to get the name of the current patch.
        
        @param repodir directory name of the repository (string)
        @return name of the current patch (string)
        """
        currentPatch = ""
        
        args = self.vcs.initCommand("qtop")
        
        client = self.vcs.getClient()
        if client:
            currentPatch = client.runcommand(args)[0].strip()
        else:
            process = QProcess()
            process.setWorkingDirectory(repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    currentPatch = str(process.readAllStandardOutput(),
                                       self.vcs.getEncoding(),
                                       'replace').strip()
        
        return currentPatch
    
    def __getCommitMessage(self, repodir):
        """
        Private method to get the commit message of the current patch.
        
        @param repodir directory name of the repository (string)
        @return name of the current patch (string)
        """
        message = ""
        
        args = self.vcs.initCommand("qheader")
        
        client = self.vcs.getClient()
        if client:
            message = client.runcommand(args)[0]
        else:
            process = QProcess()
            process.setWorkingDirectory(repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    message = str(process.readAllStandardOutput(),
                                  self.vcs.getEncoding(), 'replace')
        
        return message
    
    def getGuardsList(self, repodir, all=True):
        """
        Public method to get a list of all guards defined.
        
        @param repodir directory name of the repository (string)
        @param all flag indicating to get all guards (boolean)
        @return sorted list of guards (list of strings)
        """
        guardsList = []
        
        args = self.vcs.initCommand("qselect")
        if all:
            args.append("--series")
        
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
        
        for guard in output.splitlines():
            guard = guard.strip()
            if all:
                guard = guard[1:]
            if guard not in guardsList:
                guardsList.append(guard)
        
        return sorted(guardsList)
    
    def hgQueueNewPatch(self, name):
        """
        Public method to create a new named patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgQueuesNewPatchDialog import HgQueuesNewPatchDialog
        dlg = HgQueuesNewPatchDialog(HgQueuesNewPatchDialog.NEW_MODE)
        if dlg.exec_() == QDialog.Accepted:
            name, message, (userData, currentUser, userName), \
                (dateData, currentDate, dateStr) = dlg.getData()
            
            args = self.vcs.initCommand("qnew")
            if message != "":
                args.append("--message")
                args.append(message)
            if userData:
                if currentUser:
                    args.append("--currentuser")
                else:
                    args.append("--user")
                    args.append(userName)
            if dateData:
                if currentDate:
                    args.append("--currentdate")
                else:
                    args.append("--date")
                    args.append(dateStr)
            args.append(name)
            
            dia = HgDialog(self.tr('New Patch'), self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                self.vcs.checkVCSStatus()
    
    def hgQueueRefreshPatch(self, name, editMessage=False):
        """
        Public method to refresh the current patch.
        
        @param name file/directory name (string)
        @param editMessage flag indicating to edit the current
            commit message (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.vcs.initCommand("qrefresh")
        
        if editMessage:
            currentMessage = self.__getCommitMessage(repodir)
            from .HgQueuesNewPatchDialog import HgQueuesNewPatchDialog
            dlg = HgQueuesNewPatchDialog(HgQueuesNewPatchDialog.REFRESH_MODE,
                                         currentMessage)
            if dlg.exec_() == QDialog.Accepted:
                name, message, (userData, currentUser, userName), \
                    (dateData, currentDate, dateStr) = dlg.getData()
                if message != "" and message != currentMessage:
                    args.append("--message")
                    args.append(message)
                if userData:
                    if currentUser:
                        args.append("--currentuser")
                    else:
                        args.append("--user")
                        args.append(userName)
                if dateData:
                    if currentDate:
                        args.append("--currentdate")
                    else:
                        args.append("--date")
                        args.append(dateStr)
            else:
                return
        
        dia = HgDialog(self.tr('Update Current Patch'), self.vcs)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            self.vcs.checkVCSStatus()
    
    def hgQueueShowPatch(self, name):
        """
        Public method to show the contents of the current patch.
        
        @param name file/directory name (string)
        """
        from ..HgDiffDialog import HgDiffDialog
        self.qdiffDialog = HgDiffDialog(self.vcs)
        self.qdiffDialog.show()
        QApplication.processEvents()
        self.qdiffDialog.start(name, qdiff=True)
    
    def hgQueueShowHeader(self, name):
        """
        Public method to show the commit message of the current patch.
        
        @param name file/directory name (string)
        """
        from .HgQueuesHeaderDialog import HgQueuesHeaderDialog
        self.qheaderDialog = HgQueuesHeaderDialog(self.vcs)
        self.qheaderDialog.show()
        QApplication.processEvents()
        self.qheaderDialog.start(name)
    
    def hgQueuePushPopPatches(self, name, operation, all=False, named=False,
                              force=False):
        """
        Public method to push patches onto the stack or pop patches off the
        stack.
        
        @param name file/directory name (string)
        @param operation operation type to be performed (Queues.POP,
            Queues.PUSH, Queues.GOTO)
        @keyparam all flag indicating to push/pop all (boolean)
        @keyparam named flag indicating to push/pop until a named patch
            is at the top of the stack (boolean)
        @keyparam force flag indicating a forceful pop (boolean)
        @return flag indicating that the project should be reread (boolean)
        @exception ValueError raised to indicate an invalid operation
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        if operation == Queues.POP:
            args = self.vcs.initCommand("qpop")
            title = self.tr("Pop Patches")
            listType = Queues.APPLIED_LIST
        elif operation == Queues.PUSH:
            args = self.vcs.initCommand("qpush")
            title = self.tr("Push Patches")
            listType = Queues.UNAPPLIED_LIST
        elif operation == Queues.GOTO:
            args = self.vcs.initCommand("qgoto")
            title = self.tr("Go to Patch")
            listType = Queues.SERIES_LIST
        else:
            raise ValueError("illegal value for operation")
        args.append("-v")
        if force:
            args.append("--force")
        if all and operation in (Queues.POP, Queues.PUSH):
            args.append("--all")
        elif named or operation == Queues.GOTO:
            patchnames = self.__getPatchesList(repodir, listType)
            if patchnames:
                patch, ok = QInputDialog.getItem(
                    None,
                    self.tr("Select Patch"),
                    self.tr("Select the target patch name:"),
                    patchnames,
                    0, False)
                if ok and patch:
                    args.append(patch)
                else:
                    return False
            else:
                E5MessageBox.information(
                    None,
                    self.tr("Select Patch"),
                    self.tr("""No patches to select from."""))
                return False
        
        dia = HgDialog(title, self.vcs)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            res = dia.hasAddOrDelete()
            self.vcs.checkVCSStatus()
        return res
    
    def hgQueueListPatches(self, name):
        """
        Public method to show a list of all patches.
        
        @param name file/directory name (string)
        """
        from .HgQueuesListDialog import HgQueuesListDialog
        self.queuesListDialog = HgQueuesListDialog(self.vcs)
        self.queuesListDialog.show()
        self.queuesListDialog.start(name)
    
    def hgQueueFinishAppliedPatches(self, name):
        """
        Public method to finish all applied patches.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.vcs.initCommand("qfinish")
        args.append("--applied")
        
        dia = HgDialog(self.tr('Finish Applied Patches'), self.vcs)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            self.vcs.checkVCSStatus()
    
    def hgQueueRenamePatch(self, name):
        """
        Public method to rename the current or a selected patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.vcs.initCommand("qrename")
        patchnames = sorted(self.__getPatchesList(repodir, Queues.SERIES_LIST))
        if patchnames:
            currentPatch = self.__getCurrentPatch(repodir)
            if currentPatch:
                from .HgQueuesRenamePatchDialog import \
                    HgQueuesRenamePatchDialog
                dlg = HgQueuesRenamePatchDialog(currentPatch, patchnames)
                if dlg.exec_() == QDialog.Accepted:
                    newName, selectedPatch = dlg.getData()
                    if selectedPatch:
                        args.append(selectedPatch)
                    args.append(newName)
                    
                    dia = HgDialog(self.tr("Rename Patch"), self.vcs)
                    res = dia.startProcess(args, repodir)
                    if res:
                        dia.exec_()
    
    def hgQueueDeletePatch(self, name):
        """
        Public method to delete a selected unapplied patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.vcs.initCommand("qdelete")
        patchnames = sorted(self.__getPatchesList(repodir,
                                                  Queues.UNAPPLIED_LIST))
        if patchnames:
            patch, ok = QInputDialog.getItem(
                None,
                self.tr("Select Patch"),
                self.tr("Select the patch to be deleted:"),
                patchnames,
                0, False)
            if ok and patch:
                args.append(patch)
                
                dia = HgDialog(self.tr("Delete Patch"), self.vcs)
                res = dia.startProcess(args, repodir)
                if res:
                    dia.exec_()
        else:
            E5MessageBox.information(
                None,
                self.tr("Select Patch"),
                self.tr("""No patches to select from."""))
    
    def hgQueueFoldUnappliedPatches(self, name):
        """
        Public method to fold patches into the current patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.vcs.initCommand("qfold")
        patchnames = sorted(
            self.__getPatchesList(repodir, Queues.UNAPPLIED_LIST,
                                  withSummary=True))
        if patchnames:
            from .HgQueuesFoldDialog import HgQueuesFoldDialog
            dlg = HgQueuesFoldDialog(patchnames)
            if dlg.exec_() == QDialog.Accepted:
                message, patchesList = dlg.getData()
                if message:
                    args.append("--message")
                    args.append(message)
                if patchesList:
                    args.extend(patchesList)
                    
                    dia = HgDialog(self.tr("Fold Patches"), self.vcs)
                    res = dia.startProcess(args, repodir)
                    if res:
                        dia.exec_()
                else:
                    E5MessageBox.information(
                        None,
                        self.tr("Fold Patches"),
                        self.tr("""No patches selected."""))
        else:
            E5MessageBox.information(
                None,
                self.tr("Fold Patches"),
                self.tr("""No patches available to be folded."""))
    
    def hgQueueGuardsList(self, name):
        """
        Public method to list the guards for the current or a named patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        patchnames = sorted(
            self.__getPatchesList(repodir, Queues.SERIES_LIST))
        if patchnames:
            from .HgQueuesListGuardsDialog import HgQueuesListGuardsDialog
            self.queuesListGuardsDialog = \
                HgQueuesListGuardsDialog(self.vcs, patchnames)
            self.queuesListGuardsDialog.show()
            self.queuesListGuardsDialog.start(name)
        else:
            E5MessageBox.information(
                None,
                self.tr("List Guards"),
                self.tr("""No patches available to list guards for."""))
    
    def hgQueueGuardsListAll(self, name):
        """
        Public method to list all guards of all patches.
        
        @param name file/directory name (string)
        """
        from .HgQueuesListAllGuardsDialog import HgQueuesListAllGuardsDialog
        self.queuesListAllGuardsDialog = HgQueuesListAllGuardsDialog(self.vcs)
        self.queuesListAllGuardsDialog.show()
        self.queuesListAllGuardsDialog.start(name)
    
    def hgQueueGuardsDefine(self, name):
        """
        Public method to define guards for the current or a named patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        patchnames = sorted(
            self.__getPatchesList(repodir, Queues.SERIES_LIST))
        if patchnames:
            from .HgQueuesDefineGuardsDialog import HgQueuesDefineGuardsDialog
            self.queuesDefineGuardsDialog = HgQueuesDefineGuardsDialog(
                self.vcs, self, patchnames)
            self.queuesDefineGuardsDialog.show()
            self.queuesDefineGuardsDialog.start(name)
        else:
            E5MessageBox.information(
                None,
                self.tr("Define Guards"),
                self.tr("""No patches available to define guards for."""))
    
    def hgQueueGuardsDropAll(self, name):
        """
        Public method to drop all guards of the current or a named patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        patchnames = sorted(
            self.__getPatchesList(repodir, Queues.SERIES_LIST))
        if patchnames:
            patch, ok = QInputDialog.getItem(
                None,
                self.tr("Drop All Guards"),
                self.tr("Select the patch to drop guards for"
                        " (leave empty for the current patch):"),
                [""] + patchnames,
                0, False)
            if ok:
                args = self.vcs.initCommand("qguard")
                if patch:
                    args.append(patch)
                args.append("--none")
                
                client = self.vcs.getClient()
                if client:
                    client.runcommand(args)
                else:
                    process = QProcess()
                    process.setWorkingDirectory(repodir)
                    process.start('hg', args)
                    procStarted = process.waitForStarted(5000)
                    if procStarted:
                        process.waitForFinished(30000)
        else:
            E5MessageBox.information(
                None,
                self.tr("Drop All Guards"),
                self.tr("""No patches available to define guards for."""))
    
    def hgQueueGuardsSetActive(self, name):
        """
        Public method to set the active guards.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        guardsList = self.getGuardsList(repodir)
        if guardsList:
            activeGuardsList = self.getGuardsList(repodir, all=False)
            from .HgQueuesGuardsSelectionDialog import \
                HgQueuesGuardsSelectionDialog
            dlg = HgQueuesGuardsSelectionDialog(
                guardsList, activeGuards=activeGuardsList, listOnly=False)
            if dlg.exec_() == QDialog.Accepted:
                guards = dlg.getData()
                if guards:
                    args = self.vcs.initCommand("qselect")
                    args.extend(guards)
                    
                    dia = HgDialog(self.tr('Set Active Guards'), self.vcs)
                    res = dia.startProcess(args, repodir)
                    if res:
                        dia.exec_()
        else:
            E5MessageBox.information(
                None,
                self.tr("Set Active Guards"),
                self.tr("""No guards available to select from."""))
            return
    
    def hgQueueGuardsDeactivate(self, name):
        """
        Public method to deactivate all active guards.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.vcs.initCommand("qselect")
        args.append("--none")
        
        dia = HgDialog(self.tr('Deactivate Guards'), self.vcs)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
    
    def hgQueueGuardsIdentifyActive(self, name):
        """
        Public method to list all active guards.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        guardsList = self.getGuardsList(repodir, all=False)
        if guardsList:
            from .HgQueuesGuardsSelectionDialog import \
                HgQueuesGuardsSelectionDialog
            dlg = HgQueuesGuardsSelectionDialog(guardsList, listOnly=True)
            dlg.exec_()
    
    def hgQueueCreateRenameQueue(self, name, isCreate):
        """
        Public method to create a new queue or rename the active queue.
        
        @param name file/directory name (string)
        @param isCreate flag indicating to create a new queue (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        if isCreate:
            title = self.tr("Create New Queue")
        else:
            title = self.tr("Rename Active Queue")
        from .HgQueuesQueueManagementDialog import \
            HgQueuesQueueManagementDialog
        dlg = HgQueuesQueueManagementDialog(
            HgQueuesQueueManagementDialog.NAME_INPUT,
            title, False, repodir, self.vcs)
        if dlg.exec_() == QDialog.Accepted:
            queueName = dlg.getData()
            if queueName:
                args = self.vcs.initCommand("qqueue")
                if isCreate:
                    args.append("--create")
                else:
                    args.append("--rename")
                args.append(queueName)
                
                client = self.vcs.getClient()
                error = ""
                if client:
                    error = client.runcommand(args)[1]
                else:
                    process = QProcess()
                    process.setWorkingDirectory(repodir)
                    process.start('hg', args)
                    procStarted = process.waitForStarted(5000)
                    if procStarted:
                        finished = process.waitForFinished(30000)
                        if finished:
                            if process.exitCode() != 0:
                                error = str(process.readAllStandardError(),
                                            self.vcs.getEncoding(), 'replace')
                
                if error:
                    if isCreate:
                        errMsg = self.tr(
                            "Error while creating a new queue.")
                    else:
                        errMsg = self.tr(
                            "Error while renaming the active queue.")
                    E5MessageBox.warning(
                        None,
                        title,
                        """<p>{0}</p><p>{1}</p>""".format(errMsg, error))
                else:
                    if self.queuesListQueuesDialog is not None and \
                       self.queuesListQueuesDialog.isVisible():
                        self.queuesListQueuesDialog.refresh()
    
    def hgQueueDeletePurgeActivateQueue(self, name, operation):
        """
        Public method to delete the reference to a queue and optionally
        remove the patch directory or set the active queue.
        
        @param name file/directory name (string)
        @param operation operation to be performed (Queues.QUEUE_DELETE,
            Queues.QUEUE_PURGE, Queues.QUEUE_ACTIVATE)
        @exception ValueError raised to indicate an invalid operation
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        if operation == Queues.QUEUE_PURGE:
            title = self.tr("Purge Queue")
        elif operation == Queues.QUEUE_DELETE:
            title = self.tr("Delete Queue")
        elif operation == Queues.QUEUE_ACTIVATE:
            title = self.tr("Activate Queue")
        else:
            raise ValueError("illegal value for operation")
        
        from .HgQueuesQueueManagementDialog import \
            HgQueuesQueueManagementDialog
        dlg = HgQueuesQueueManagementDialog(
            HgQueuesQueueManagementDialog.QUEUE_INPUT,
            title, True, repodir, self.vcs)
        if dlg.exec_() == QDialog.Accepted:
            queueName = dlg.getData()
            if queueName:
                args = self.vcs.initCommand("qqueue")
                if operation == Queues.QUEUE_PURGE:
                    args.append("--purge")
                elif operation == Queues.QUEUE_DELETE:
                    args.append("--delete")
                args.append(queueName)
                
                client = self.vcs.getClient()
                error = ""
                if client:
                    error = client.runcommand(args)[1]
                else:
                    process = QProcess()
                    process.setWorkingDirectory(repodir)
                    process.start('hg', args)
                    procStarted = process.waitForStarted(5000)
                    if procStarted:
                        finished = process.waitForFinished(30000)
                        if finished:
                            if process.exitCode() != 0:
                                error = str(process.readAllStandardError(),
                                            self.vcs.getEncoding(), 'replace')
                
                if error:
                    if operation == Queues.QUEUE_PURGE:
                        errMsg = self.tr("Error while purging the queue.")
                    elif operation == Queues.QUEUE_DELETE:
                        errMsg = self.tr("Error while deleting the queue.")
                    elif operation == Queues.QUEUE_ACTIVATE:
                        errMsg = self.tr(
                            "Error while setting the active queue.")
                    E5MessageBox.warning(
                        None,
                        title,
                        """<p>{0}</p><p>{1}</p>""".format(errMsg, error))
                else:
                    if self.queuesListQueuesDialog is not None and \
                       self.queuesListQueuesDialog.isVisible():
                        self.queuesListQueuesDialog.refresh()
    
    def hgQueueListQueues(self, name):
        """
        Public method to list available queues.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgQueuesQueueManagementDialog import \
            HgQueuesQueueManagementDialog
        self.queuesListQueuesDialog = HgQueuesQueueManagementDialog(
            HgQueuesQueueManagementDialog.NO_INPUT,
            self.tr("Available Queues"),
            False, repodir, self.vcs)
        self.queuesListQueuesDialog.show()
    
    def hgQueueInit(self, name):
        """
        Public method to initialize a new queue repository.
        
        @param name directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.vcs.initCommand("init")
        args.append('--mq')
        args.append(repodir)
        # init is not possible with the command server
        dia = HgDialog(
            self.tr('Initializing new queue repository'), self.vcs)
        res = dia.startProcess(args)
        if res:
            dia.exec_()
    
    def hgQueueStatus(self, name):
        """
        Public method used to view the status of a queue repository.
        
        @param name directory name (string)
        """
        from ..HgStatusDialog import HgStatusDialog
        self.queueStatusDialog = HgStatusDialog(self.vcs, mq=True)
        self.queueStatusDialog.show()
        self.queueStatusDialog.start(name)
