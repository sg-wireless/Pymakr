# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the version control systems interface to Mercurial.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os
import shutil
import re

from PyQt5.QtCore import QProcess, pyqtSignal, QFileInfo, QFileSystemWatcher, \
    QCoreApplication
from PyQt5.QtWidgets import QApplication, QDialog, QInputDialog

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox, E5FileDialog

from QScintilla.MiniEditor import MiniEditor

from VCS.VersionControl import VersionControl
from VCS.RepositoryInfoDialog import VcsRepositoryInfoDialog

from .HgDialog import HgDialog

import Utilities


class Hg(VersionControl):
    """
    Class implementing the version control systems interface to Mercurial.
    
    @signal committed() emitted after the commit action has completed
    @signal activeExtensionsChanged() emitted when the list of active
        extensions has changed
    @signal iniFileChanged() emitted when a Mercurial/repo configuration file
        has changed
    """
    committed = pyqtSignal()
    activeExtensionsChanged = pyqtSignal()
    iniFileChanged = pyqtSignal()
    
    IgnoreFileName = ".hgignore"
    
    def __init__(self, plugin, parent=None, name=None):
        """
        Constructor
        
        @param plugin reference to the plugin object
        @param parent parent widget (QWidget)
        @param name name of this object (string)
        """
        VersionControl.__init__(self, parent, name)
        self.defaultOptions = {
            'global': [''],
            'commit': [''],
            'checkout': [''],
            'update': [''],
            'add': [''],
            'remove': [''],
            'diff': [''],
            'log': [''],
            'history': [''],
            'status': [''],
            'tag': [''],
            'export': ['']
        }
        
        self.__plugin = plugin
        self.__ui = parent
        
        self.options = self.defaultOptions
        self.tagsList = []
        self.branchesList = []
        self.allTagsBranchesList = []
        self.bookmarksList = []
        self.showedTags = False
        self.showedBranches = False
        
        self.tagTypeList = [
            'tags',
            'branches',
        ]
        
        self.commandHistory = []
        
        if "HG_ASP_DOT_NET_HACK" in os.environ:
            self.adminDir = '_hg'
        else:
            self.adminDir = '.hg'
        
        self.log = None
        self.logBrowser = None
        self.logBrowserIncoming = None
        self.logBrowserOutgoing = None
        self.diff = None
        self.sbsDiff = None
        self.status = None
        self.summary = None
        self.tagbranchList = None
        self.annotate = None
        self.repoEditor = None
        self.userEditor = None
        self.serveDlg = None
        self.bookmarksListDlg = None
        self.bookmarksInOutDlg = None
        self.conflictsDlg = None
        
        self.bundleFile = None
        self.__lastChangeGroupPath = None
        
        self.statusCache = {}
        
        self.__commitData = {}
        self.__commitDialog = None
        
        self.__forgotNames = []
        
        self.__activeExtensions = []
        
        from .HgUtilities import getConfigPath
        self.__iniWatcher = QFileSystemWatcher(self)
        self.__iniWatcher.fileChanged.connect(self.__iniFileChanged)
        cfgFile = getConfigPath()
        if os.path.exists(cfgFile):
            self.__iniWatcher.addPath(cfgFile)
        
        self.__client = None
        
        self.__repoDir = ""
        self.__repoIniFile = ""
        self.__defaultConfigured = False
        self.__defaultPushConfigured = False
        
        # instantiate the extensions
        from .QueuesExtension.queues import Queues
        from .FetchExtension.fetch import Fetch
        from .PurgeExtension.purge import Purge
        from .GpgExtension.gpg import Gpg
        from .TransplantExtension.transplant import Transplant
        from .RebaseExtension.rebase import Rebase
        from .ShelveExtension.shelve import Shelve
        from .LargefilesExtension.largefiles import Largefiles
        self.__extensions = {
            "mq": Queues(self),
            "fetch": Fetch(self),
            "purge": Purge(self),
            "gpg": Gpg(self),
            "transplant": Transplant(self),
            "rebase": Rebase(self),
            "shelve": Shelve(self),
            "largefiles": Largefiles(self)
        }
    
    def getPlugin(self):
        """
        Public method to get a reference to the plugin object.
        
        @return reference to the plugin object (VcsMercurialPlugin)
        """
        return self.__plugin
    
    def getEncoding(self):
        """
        Public method to get the encoding to be used by Mercurial.
        
        @return encoding (string)
        """
        return self.__plugin.getPreferences("Encoding")
    
    def vcsShutdown(self):
        """
        Public method used to shutdown the Mercurial interface.
        """
        if self.log is not None:
            self.log.close()
        if self.logBrowser is not None:
            self.logBrowser.close()
        if self.logBrowserIncoming is not None:
            self.logBrowserIncoming.close()
        if self.logBrowserOutgoing is not None:
            self.logBrowserOutgoing.close()
        if self.diff is not None:
            self.diff.close()
        if self.sbsDiff is not None:
            self.sbsDiff.close()
        if self.status is not None:
            self.status.close()
        if self.summary is not None:
            self.summary.close()
        if self.tagbranchList is not None:
            self.tagbranchList.close()
        if self.annotate is not None:
            self.annotate.close()
        if self.serveDlg is not None:
            self.serveDlg.close()
        
        if self.bookmarksListDlg is not None:
            self.bookmarksListDlg.close()
        if self.bookmarksInOutDlg is not None:
            self.bookmarksInOutDlg.close()
        
        if self.conflictsDlg is not None:
            self.conflictsDlg.close()
        
        if self.bundleFile and os.path.exists(self.bundleFile):
            os.remove(self.bundleFile)
        
        # shut down the project helpers
        self.__projectHelper.shutdown()
        
        # shut down the extensions
        for extension in self.__extensions.values():
            extension.shutdown()
        
        # shut down the client
        self.__client and self.__client.stopServer()
    
    def getClient(self):
        """
        Public method to get a reference to the command server interface.
        
        @return reference to the client (HgClient)
        """
        return self.__client
    
    def initCommand(self, command):
        """
        Public method to initialize a command arguments list.
        
        @param command command name (string)
        @return list of command options (list of string)
        """
        args = [command]
        self.addArguments(args, self.__plugin.getGlobalOptions())
        return args
    
    def vcsExists(self):
        """
        Public method used to test for the presence of the hg executable.
        
        @return flag indicating the existance (boolean) and an error message
            (string)
        """
        self.versionStr = ''
        errMsg = ""
        
        args = self.initCommand("version")
        process = QProcess()
        process.start('hg', args)
        procStarted = process.waitForStarted(5000)
        if procStarted:
            finished = process.waitForFinished(30000)
            if finished and process.exitCode() == 0:
                output = str(process.readAllStandardOutput(),
                             self.getEncoding(), 'replace')
                self.versionStr = output.splitlines()[0].split()[-1][0:-1]
                v = list(re.match(r'.*?(\d+)\.(\d+)\.?(\d+)?(\+[0-9a-f-]+)?',
                                  self.versionStr).groups())
                for i in range(3):
                    try:
                        v[i] = int(v[i])
                    except TypeError:
                        v[i] = 0
                    except IndexError:
                        v.append(0)
                self.version = tuple(v)
                self.__getExtensionsInfo()
                return True, errMsg
            else:
                if finished:
                    errMsg = self.tr(
                        "The hg process finished with the exit code {0}")\
                        .format(process.exitCode())
                else:
                    errMsg = self.tr(
                        "The hg process did not finish within 30s.")
        else:
            errMsg = self.tr("Could not start the hg executable.")
        
        return False, errMsg
    
    def vcsInit(self, vcsDir, noDialog=False):
        """
        Public method used to initialize the mercurial repository.
        
        The initialization is done, when a project is converted into a
        Mercurial controlled project. Therefore we always return TRUE without
        doing anything.
        
        @param vcsDir name of the VCS directory (string)
        @param noDialog flag indicating quiet operations (boolean)
        @return always TRUE
        """
        return True
    
    def vcsConvertProject(self, vcsDataDict, project):
        """
        Public method to convert an uncontrolled project to a version
        controlled project.
        
        @param vcsDataDict dictionary of data required for the conversion
        @param project reference to the project object
        """
        success = self.vcsImport(vcsDataDict, project.ppath)[0]
        if not success:
            E5MessageBox.critical(
                self.__ui,
                self.tr("Create project repository"),
                self.tr(
                    """The project repository could not be created."""))
        else:
            pfn = project.pfile
            if not os.path.isfile(pfn):
                pfn += "z"
            project.closeProject()
            project.openProject(pfn)
    
    def vcsImport(self, vcsDataDict, projectDir, noDialog=False):
        """
        Public method used to import the project into the Mercurial repository.
        
        @param vcsDataDict dictionary of data required for the import
        @param projectDir project directory (string)
        @param noDialog flag indicating quiet operations
        @return flag indicating an execution without errors (boolean)
            and a flag indicating the version controll status (boolean)
        """
        msg = vcsDataDict["message"]
        if not msg:
            msg = '***'
        
        args = self.initCommand("init")
        args.append(projectDir)
        # init is not possible with the command server
        dia = HgDialog(self.tr('Creating Mercurial repository'), self)
        res = dia.startProcess(args)
        if res:
            dia.exec_()
        status = dia.normalExit()
        
        if status:
            ignoreName = os.path.join(projectDir, Hg.IgnoreFileName)
            if not os.path.exists(ignoreName):
                status = self.hgCreateIgnoreFile(projectDir)
            
            if status:
                args = self.initCommand("commit")
                args.append('--addremove')
                args.append('--message')
                args.append(msg)
                dia = HgDialog(
                    self.tr('Initial commit to Mercurial repository'),
                    self)
                res = dia.startProcess(args, projectDir)
                if res:
                    dia.exec_()
                status = dia.normalExit()
        
        return status, False
    
    def vcsCheckout(self, vcsDataDict, projectDir, noDialog=False):
        """
        Public method used to check the project out of a Mercurial repository
        (clone).
        
        @param vcsDataDict dictionary of data required for the checkout
        @param projectDir project directory to create (string)
        @param noDialog flag indicating quiet operations
        @return flag indicating an execution without errors (boolean)
        """
        noDialog = False
        try:
            rev = vcsDataDict["revision"]
        except KeyError:
            rev = None
        vcsUrl = self.hgNormalizeURL(vcsDataDict["url"])
        if vcsUrl.startswith('/'):
            vcsUrl = 'file://{0}'.format(vcsUrl)
        elif vcsUrl[1] in ['|', ':']:
            vcsUrl = 'file:///{0}'.format(vcsUrl)
        
        args = self.initCommand("clone")
        if rev:
            args.append("--rev")
            args.append(rev)
        if vcsDataDict["largefiles"]:
            args.append("--all-largefiles")
        args.append(self.__hgURL(vcsUrl))
        args.append(projectDir)
        
        if noDialog:
            if self.__client is None:
                return self.startSynchronizedProcess(QProcess(), 'hg', args)
            else:
                out, err = self.__client.runcommand(args)
                return err == ""
        else:
            dia = HgDialog(
                self.tr('Cloning project from a Mercurial repository'),
                self)
            res = dia.startProcess(args)
            if res:
                dia.exec_()
            return dia.normalExit()
    
    def vcsExport(self, vcsDataDict, projectDir):
        """
        Public method used to export a directory from the Mercurial repository.
        
        @param vcsDataDict dictionary of data required for the checkout
        @param projectDir project directory to create (string)
        @return flag indicating an execution without errors (boolean)
        """
        status = self.vcsCheckout(vcsDataDict, projectDir)
        shutil.rmtree(os.path.join(projectDir, self.adminDir), True)
        if os.path.exists(os.path.join(projectDir, Hg.IgnoreFileName)):
            os.remove(os.path.join(projectDir, Hg.IgnoreFileName))
        return status
    
    def vcsCommit(self, name, message, noDialog=False, closeBranch=False,
                  mq=False):
        """
        Public method used to make the change of a file/directory permanent
        in the Mercurial repository.
        
        @param name file/directory name to be committed (string or list of
            strings)
        @param message message for this operation (string)
        @param noDialog flag indicating quiet operations
        @keyparam closeBranch flag indicating a close branch commit (boolean)
        @keyparam mq flag indicating a queue commit (boolean)
        """
        msg = message
        
        if mq:
            # ensure dialog is shown for a queue commit
            noDialog = False
        
        if not noDialog:
            # call CommitDialog and get message from there
            if self.__commitDialog is None:
                from .HgCommitDialog import HgCommitDialog
                self.__commitDialog = HgCommitDialog(self, msg, mq, self.__ui)
                self.__commitDialog.accepted.connect(self.__vcsCommit_Step2)
            self.__commitDialog.show()
            self.__commitDialog.raise_()
            self.__commitDialog.activateWindow()
        
        self.__commitData["name"] = name
        self.__commitData["msg"] = msg
        self.__commitData["noDialog"] = noDialog
        self.__commitData["closeBranch"] = closeBranch
        self.__commitData["mq"] = mq
        
        if noDialog:
            self.__vcsCommit_Step2()
    
    def __vcsCommit_Step2(self):
        """
        Private slot performing the second step of the commit action.
        """
        name = self.__commitData["name"]
        msg = self.__commitData["msg"]
        noDialog = self.__commitData["noDialog"]
        closeBranch = self.__commitData["closeBranch"]
        mq = self.__commitData["mq"]
        
        if not noDialog:
            # check, if there are unsaved changes, that should be committed
            if isinstance(name, list):
                nameList = name
            else:
                nameList = [name]
            ok = True
            for nam in nameList:
                # check for commit of the project
                if os.path.isdir(nam):
                    project = e5App().getObject("Project")
                    if nam == project.getProjectPath():
                        ok &= \
                            project.checkAllScriptsDirty(
                                reportSyntaxErrors=True) and \
                            project.checkDirty()
                        continue
                elif os.path.isfile(nam):
                    editor = \
                        e5App().getObject("ViewManager").getOpenEditor(nam)
                    if editor:
                        ok &= editor.checkDirty()
                if not ok:
                    break
            
            if not ok:
                res = E5MessageBox.yesNo(
                    self.__ui,
                    self.tr("Commit Changes"),
                    self.tr(
                        """The commit affects files, that have unsaved"""
                        """ changes. Shall the commit be continued?"""),
                    icon=E5MessageBox.Warning)
                if not res:
                    return
        
        if isinstance(name, list):
            dname, fnames = self.splitPathList(name)
        else:
            dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        if self.__commitDialog is not None:
            msg = self.__commitDialog.logMessage()
            amend = self.__commitDialog.amend()
            commitSubrepositories = self.__commitDialog.commitSubrepositories()
            self.__commitDialog.deleteLater()
            self.__commitDialog = None
            if amend and not msg:
                msg = self.__getMostRecentCommitMessage(repodir)
        else:
            amend = False
            commitSubrepositories = False
        
        if not msg and not amend:
            msg = '***'
        
        args = self.initCommand("commit")
        args.append("-v")
        if mq:
            args.append("--mq")
        else:
            if closeBranch:
                args.append("--close-branch")
            if amend:
                args.append("--amend")
            if commitSubrepositories:
                args.append("--subrepos")
        if msg:
            args.append("--message")
            args.append(msg)
        if self.__client:
            if isinstance(name, list):
                self.addArguments(args, name)
            else:
                if dname != repodir or fname != ".":
                    args.append(name)
        else:
            if isinstance(name, list):
                self.addArguments(args, fnames)
            else:
                if dname != repodir or fname != ".":
                    args.append(fname)
        
        if noDialog:
            self.startSynchronizedProcess(QProcess(), "hg", args, dname)
        else:
            dia = HgDialog(
                self.tr('Committing changes to Mercurial repository'),
                self)
            res = dia.startProcess(args, dname)
            if res:
                dia.exec_()
        self.committed.emit()
        if self.__forgotNames:
            model = e5App().getObject("Project").getModel()
            for name in self.__forgotNames:
                model.updateVCSStatus(name)
            self.__forgotNames = []
        self.checkVCSStatus()
    
    def __getMostRecentCommitMessage(self, repodir):
        """
        Private method to get the most recent commit message.
        
        Note: This message is extracted from the parent commit of the
        working directory.
        
        @param repodir path containing the repository
        @type str
        @return most recent commit message
        @rtype str
        """
        args = self.initCommand("log")
        args.append("--rev")
        args.append(".")
        args.append('--template')
        args.append('{desc}')
        
        output = ""
        if self.__client is None:
            process = QProcess()
            process.setWorkingDirectory(repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.getEncoding(), 'replace')
        else:
            output, error = self.__client.runcommand(args)
        
        return output
    
    def vcsUpdate(self, name, noDialog=False, revision=None):
        """
        Public method used to update a file/directory with the Mercurial
        repository.
        
        @param name file/directory name to be updated (string or list of
            strings)
        @param noDialog flag indicating quiet operations (boolean)
        @keyparam revision revision to update to (string)
        @return flag indicating, that the update contained an add
            or delete (boolean)
        """
        args = self.initCommand("update")
        if "-v" not in args and "--verbose" not in args:
            args.append("-v")
        if revision:
            args.append("-r")
            args.append(revision)
        
        if isinstance(name, list):
            dname, fnames = self.splitPathList(name)
        else:
            dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        if noDialog:
            if self.__client is None:
                self.startSynchronizedProcess(QProcess(), 'hg', args, repodir)
            else:
                out, err = self.__client.runcommand(args)
            res = False
        else:
            dia = HgDialog(self.tr(
                'Synchronizing with the Mercurial repository'),
                self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.hasAddOrDelete()
        self.checkVCSStatus()
        return res
    
    def vcsAdd(self, name, isDir=False, noDialog=False):
        """
        Public method used to add a file/directory to the Mercurial repository.
        
        @param name file/directory name to be added (string)
        @param isDir flag indicating name is a directory (boolean)
        @param noDialog flag indicating quiet operations
        """
        args = self.initCommand("add")
        args.append("-v")
        
        if isinstance(name, list):
            if isDir:
                dname, fname = os.path.split(name[0])
            else:
                dname, fnames = self.splitPathList(name)
        else:
            if isDir:
                dname, fname = os.path.split(name)
            else:
                dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        if isinstance(name, list):
            self.addArguments(args, name)
        else:
            args.append(name)
        
        if noDialog:
            if self.__client is None:
                self.startSynchronizedProcess(QProcess(), 'hg', args, repodir)
            else:
                out, err = self.__client.runcommand(args)
        else:
            dia = HgDialog(
                self.tr(
                    'Adding files/directories to the Mercurial repository'),
                self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def vcsAddBinary(self, name, isDir=False):
        """
        Public method used to add a file/directory in binary mode to the
        Mercurial repository.
        
        @param name file/directory name to be added (string)
        @param isDir flag indicating name is a directory (boolean)
        """
        self.vcsAdd(name, isDir)
    
    def vcsAddTree(self, path):
        """
        Public method to add a directory tree rooted at path to the Mercurial
        repository.
        
        @param path root directory of the tree to be added (string or list of
            strings))
        """
        self.vcsAdd(path, isDir=False)
    
    def vcsRemove(self, name, project=False, noDialog=False):
        """
        Public method used to remove a file/directory from the Mercurial
        repository.
        
        The default operation is to remove the local copy as well.
        
        @param name file/directory name to be removed (string or list of
            strings))
        @param project flag indicating deletion of a project tree (boolean)
            (not needed)
        @param noDialog flag indicating quiet operations
        @return flag indicating successfull operation (boolean)
        """
        args = self.initCommand("remove")
        args.append("-v")
        if noDialog and '--force' not in args:
            args.append('--force')
        
        if isinstance(name, list):
            dname, fnames = self.splitPathList(name)
            self.addArguments(args, name)
        else:
            dname, fname = self.splitPath(name)
            args.append(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        if noDialog:
            if self.__client is None:
                res = self.startSynchronizedProcess(
                    QProcess(), 'hg', args, repodir)
            else:
                out, err = self.__client.runcommand(args)
                res = err == ""
        else:
            dia = HgDialog(
                self.tr(
                    'Removing files/directories from the Mercurial'
                    ' repository'),
                self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.normalExitWithoutErrors()
        
        return res
    
    def vcsMove(self, name, project, target=None, noDialog=False):
        """
        Public method used to move a file/directory.
        
        @param name file/directory name to be moved (string)
        @param project reference to the project object
        @param target new name of the file/directory (string)
        @param noDialog flag indicating quiet operations
        @return flag indicating successfull operation (boolean)
        """
        isDir = os.path.isdir(name)
        
        res = False
        if noDialog:
            if target is None:
                return False
            force = True
            accepted = True
        else:
            from .HgCopyDialog import HgCopyDialog
            dlg = HgCopyDialog(name, None, True)
            accepted = dlg.exec_() == QDialog.Accepted
            if accepted:
                target, force = dlg.getData()
        
        if accepted:
            args = self.initCommand("rename")
            args.append("-v")
            if force:
                args.append('--force')
            args.append(name)
            args.append(target)
            
            dname, fname = self.splitPath(name)
            # find the root of the repo
            repodir = dname
            while not os.path.isdir(os.path.join(repodir, self.adminDir)):
                repodir = os.path.dirname(repodir)
                if os.path.splitdrive(repodir)[1] == os.sep:
                    return False
            
            if noDialog:
                if self.__client is None:
                    res = self.startSynchronizedProcess(
                        QProcess(), 'hg', args, repodir)
                else:
                    out, err = self.__client.runcommand(args)
                    res = err == ""
            else:
                dia = HgDialog(self.tr('Renaming {0}').format(name), self)
                res = dia.startProcess(args, repodir)
                if res:
                    dia.exec_()
                    res = dia.normalExit()
            if res:
                if target.startswith(project.getProjectPath()):
                    if isDir:
                        project.moveDirectory(name, target)
                    else:
                        project.renameFileInPdata(name, target)
                else:
                    if isDir:
                        project.removeDirectory(name)
                    else:
                        project.removeFile(name)
        return res
    
    def vcsLog(self, name):
        """
        Public method used to view the log of a file/directory from the
        Mercurial repository.
        
        @param name file/directory name to show the log of (string)
        """
        dname, fname = self.splitPath(name)
        isFile = os.path.isfile(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgMultiRevisionSelectionDialog import \
            HgMultiRevisionSelectionDialog
        dlg = HgMultiRevisionSelectionDialog(
            self.hgGetTagsList(repodir),
            self.hgGetBranchesList(repodir),
            self.hgGetBookmarksList(repodir),
            emptyRevsOk=True,
            showLimit=True,
            limitDefault=self.getPlugin().getPreferences("LogLimit"))
        if dlg.exec_() == QDialog.Accepted:
            revs, noEntries = dlg.getRevisions()
            from .HgLogDialog import HgLogDialog
            self.log = HgLogDialog(self, isFile=isFile)
            self.log.show()
            self.log.start(name, noEntries=noEntries, revisions=revs)
    
    def vcsDiff(self, name):
        """
        Public method used to view the difference of a file/directory to the
        Mercurial repository.
        
        If name is a directory and is the project directory, all project files
        are saved first. If name is a file (or list of files), which is/are
        being edited and has unsaved modification, they can be saved or the
        operation may be aborted.
        
        @param name file/directory name to be diffed (string)
        """
        if isinstance(name, list):
            names = name[:]
        else:
            names = [name]
        for nam in names:
            if os.path.isfile(nam):
                editor = e5App().getObject("ViewManager").getOpenEditor(nam)
                if editor and not editor.checkDirty():
                    return
            else:
                project = e5App().getObject("Project")
                if nam == project.ppath and not project.saveAllScripts():
                    return
        if self.diff is None:
            from .HgDiffDialog import HgDiffDialog
            self.diff = HgDiffDialog(self)
        self.diff.show()
        self.diff.raise_()
        QApplication.processEvents()
        self.diff.start(name, refreshable=True)
    
    def vcsStatus(self, name):
        """
        Public method used to view the status of files/directories in the
        Mercurial repository.
        
        @param name file/directory name(s) to show the status of
            (string or list of strings)
        """
        if self.status is None:
            from .HgStatusDialog import HgStatusDialog
            self.status = HgStatusDialog(self)
        self.status.show()
        self.status.raise_()
        self.status.start(name)
    
    def hgSummary(self, mq=False, largefiles=False):
        """
        Public method used to show some summary information of the
        working directory state.
        
        @param mq flag indicating to show the queue status as well (boolean)
        @param largefiles flag indicating to show the largefiles status as
            well (boolean)
        """
        if self.summary is None:
            from .HgSummaryDialog import HgSummaryDialog
            self.summary = HgSummaryDialog(self)
        self.summary.show()
        self.summary.raise_()
        self.summary.start(self.__projectHelper.getProject().getProjectPath(),
                           mq=mq, largefiles=largefiles)
    
    def vcsTag(self, name, revision=None, tagName=None):
        """
        Public method used to set/remove a tag in the Mercurial repository.
        
        @param name file/directory name to determine the repo root from
            (string)
        @param revision revision to set tag for (string)
        @param tagName name of the tag (string)
        @return flag indicating a performed tag action (boolean)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgTagDialog import HgTagDialog
        dlg = HgTagDialog(self.hgGetTagsList(repodir, withType=True),
                          revision, tagName)
        if dlg.exec_() == QDialog.Accepted:
            tag, revision, tagOp = dlg.getParameters()
        else:
            return False
        
        args = self.initCommand("tag")
        msgPart = ""
        if tagOp in [HgTagDialog.CreateLocalTag, HgTagDialog.DeleteLocalTag]:
            args.append('--local')
            msgPart = "local "
        else:
            msgPart = "global "
        if tagOp in [HgTagDialog.DeleteGlobalTag, HgTagDialog.DeleteLocalTag]:
            args.append('--remove')
        if tagOp in [HgTagDialog.CreateGlobalTag, HgTagDialog.CreateLocalTag]:
            if revision:
                args.append("--rev")
                args.append(revision)
        args.append('--message')
        if tagOp in [HgTagDialog.CreateGlobalTag, HgTagDialog.CreateLocalTag]:
            tag = tag.strip().replace(" ", "_")
            args.append("Created {1}tag <{0}>.".format(tag, msgPart))
        else:
            args.append("Removed {1}tag <{0}>.".format(tag, msgPart))
        args.append(tag)
        
        dia = HgDialog(self.tr('Tagging in the Mercurial repository'),
                       self)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
        
        return True
    
    def hgRevert(self, name):
        """
        Public method used to revert changes made to a file/directory.
        
        @param name file/directory name to be reverted (string)
        @return flag indicating, that the update contained an add
            or delete (boolean)
        """
        args = self.initCommand("revert")
        if not self.getPlugin().getPreferences("CreateBackup"):
            args.append("--no-backup")
        args.append("-v")
        if isinstance(name, list):
            dname, fnames = self.splitPathList(name)
            self.addArguments(args, name)
            names = name[:]
        else:
            dname, fname = self.splitPath(name)
            args.append(name)
            names = [name]
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        project = e5App().getObject("Project")
        names = [project.getRelativePath(nam) for nam in names]
        if names[0]:
            from UI.DeleteFilesConfirmationDialog import \
                DeleteFilesConfirmationDialog
            dlg = DeleteFilesConfirmationDialog(
                self.parent(),
                self.tr("Revert changes"),
                self.tr(
                    "Do you really want to revert all changes to these files"
                    " or directories?"),
                names)
            yes = dlg.exec_() == QDialog.Accepted
        else:
            yes = E5MessageBox.yesNo(
                None,
                self.tr("Revert changes"),
                self.tr("""Do you really want to revert all changes of"""
                        """ the project?"""))
        if yes:
            dia = HgDialog(self.tr('Reverting changes'), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.hasAddOrDelete()
            self.checkVCSStatus()
        else:
            res = False
        
        return res
    
    def vcsMerge(self, name):
        """
        Public method used to merge a URL/revision into the local project.
        
        @param name file/directory name to be merged (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgMergeDialog import HgMergeDialog
        dlg = HgMergeDialog(self.hgGetTagsList(repodir),
                            self.hgGetBranchesList(repodir),
                            self.hgGetBookmarksList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            rev, force = dlg.getParameters()
        else:
            return
        
        args = self.initCommand("merge")
        if force:
            args.append("--force")
        if self.getPlugin().getPreferences("InternalMerge"):
            args.append("--tool")
            args.append("internal:merge")
        if rev:
            args.append("--rev")
            args.append(rev)
        
        dia = HgDialog(self.tr('Merging').format(name), self)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
        self.checkVCSStatus()
    
    def hgReMerge(self, name):
        """
        Public method used to merge a URL/revision into the local project.
        
        @param name file/directory name to be merged (string)
        """
        args = self.initCommand("resolve")
        if self.getPlugin().getPreferences("InternalMerge"):
            args.append("--tool")
            args.append("internal:merge")
        if isinstance(name, list):
            dname, fnames = self.splitPathList(name)
            self.addArguments(args, name)
            names = name[:]
        else:
            dname, fname = self.splitPath(name)
            args.append(name)
            names = [name]
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        project = e5App().getObject("Project")
        names = [project.getRelativePath(nam) for nam in names]
        if names[0]:
            from UI.DeleteFilesConfirmationDialog import \
                DeleteFilesConfirmationDialog
            dlg = DeleteFilesConfirmationDialog(
                self.parent(),
                self.tr("Re-Merge"),
                self.tr(
                    "Do you really want to re-merge these files"
                    " or directories?"),
                names)
            yes = dlg.exec_() == QDialog.Accepted
        else:
            yes = E5MessageBox.yesNo(
                None,
                self.tr("Re-Merge"),
                self.tr("""Do you really want to re-merge the project?"""))
        if yes:
            dia = HgDialog(self.tr('Re-Merging').format(name), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
            self.checkVCSStatus()
    
    def vcsSwitch(self, name):
        """
        Public method used to switch a working directory to a different
        revision.
        
        @param name directory name to be switched (string)
        @return flag indicating, that the switch contained an add
            or delete (boolean)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        from .HgRevisionSelectionDialog import HgRevisionSelectionDialog
        dlg = HgRevisionSelectionDialog(self.hgGetTagsList(repodir),
                                        self.hgGetBranchesList(repodir),
                                        self.hgGetBookmarksList(repodir),
                                        self.tr("Current branch tip"))
        if dlg.exec_() == QDialog.Accepted:
            rev = dlg.getRevision()
            return self.vcsUpdate(name, revision=rev)
        
        return False

    def vcsRegisteredState(self, name):
        """
        Public method used to get the registered state of a file in the vcs.
        
        @param name filename to check (string)
        @return a combination of canBeCommited and canBeAdded
        """
        if name.endswith(os.sep):
            name = name[:-1]
        name = os.path.normcase(name)
        dname, fname = self.splitPath(name)
        
        if fname == '.' and os.path.isdir(os.path.join(dname, self.adminDir)):
            return self.canBeCommitted
        
        if name in self.statusCache:
            return self.statusCache[name]
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return 0
        
        args = self.initCommand("status")
        args.append('--all')
        args.append('--noninteractive')
        
        output = ""
        if self.__client is None:
            process = QProcess()
            process.setWorkingDirectory(repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.getEncoding(), 'replace')
        else:
            output, error = self.__client.runcommand(args)
        
        if output:
            for line in output.splitlines():
                if line and line[0] in "MARC!?I":
                    flag, path = line.split(" ", 1)
                    absname = os.path.join(repodir, os.path.normcase(path))
                    if flag not in "?I":
                        if fname == '.':
                            if absname.startswith(dname + os.path.sep):
                                return self.canBeCommitted
                            if absname == dname:
                                return self.canBeCommitted
                        else:
                            if absname == name:
                                return self.canBeCommitted
        
        return self.canBeAdded
    
    def vcsAllRegisteredStates(self, names, dname, shortcut=True):
        """
        Public method used to get the registered states of a number of files
        in the vcs.
        
        <b>Note:</b> If a shortcut is to be taken, the code will only check,
        if the named directory has been scanned already. If so, it is assumed,
        that the states for all files have been populated by the previous run.
        
        @param names dictionary with all filenames to be checked as keys
        @param dname directory to check in (string)
        @param shortcut flag indicating a shortcut should be taken (boolean)
        @return the received dictionary completed with a combination of
            canBeCommited and canBeAdded or None in order to signal an error
        """
        if dname.endswith(os.sep):
            dname = dname[:-1]
        dname = os.path.normcase(dname)
        
        found = False
        for name in list(self.statusCache.keys()):
            if name in names:
                found = True
                names[name] = self.statusCache[name]
        
        if not found:
            # find the root of the repo
            repodir = dname
            while not os.path.isdir(os.path.join(repodir, self.adminDir)):
                repodir = os.path.dirname(repodir)
                if os.path.splitdrive(repodir)[1] == os.sep:
                    return names
        
            args = self.initCommand("status")
            args.append('--all')
            args.append('--noninteractive')
            
            output = ""
            if self.__client is None:
                process = QProcess()
                process.setWorkingDirectory(dname)
                process.start('hg', args)
                procStarted = process.waitForStarted(5000)
                if procStarted:
                    finished = process.waitForFinished(30000)
                    if finished and process.exitCode() == 0:
                        output = str(process.readAllStandardOutput(),
                                     self.getEncoding(), 'replace')
            else:
                output, error = self.__client.runcommand(args)
            
            if output:
                dirs = [x for x in names.keys() if os.path.isdir(x)]
                for line in output.splitlines():
                    if line and line[0] in "MARC!?I":
                        flag, path = line.split(" ", 1)
                        name = os.path.normcase(os.path.join(repodir, path))
                        dirName = os.path.dirname(name)
                        if name.startswith(dname):
                            if flag not in "?I":
                                if name in names:
                                    names[name] = self.canBeCommitted
                                if dirName in names:
                                    names[dirName] = self.canBeCommitted
                                if dirs:
                                    for d in dirs:
                                        if name.startswith(d):
                                            names[d] = self.canBeCommitted
                                            dirs.remove(d)
                                            break
                        if flag not in "?I":
                            self.statusCache[name] = self.canBeCommitted
                            self.statusCache[dirName] = self.canBeCommitted
                        else:
                            self.statusCache[name] = self.canBeAdded
                            if dirName not in self.statusCache:
                                self.statusCache[dirName] = self.canBeAdded
        
        return names
    
    def clearStatusCache(self):
        """
        Public method to clear the status cache.
        """
        self.statusCache = {}
    
    def vcsName(self):
        """
        Public method returning the name of the vcs.
        
        @return always 'Mercurial' (string)
        """
        return "Mercurial"
    
    def vcsInitConfig(self, project):
        """
        Public method to initialize the VCS configuration.
        
        This method ensures, that an ignore file exists.
        
        @param project reference to the project (Project)
        """
        ppath = project.getProjectPath()
        if ppath:
            ignoreName = os.path.join(ppath, Hg.IgnoreFileName)
            if not os.path.exists(ignoreName):
                self.hgCreateIgnoreFile(project.getProjectPath(), autoAdd=True)
    
    def vcsCleanup(self, name):
        """
        Public method used to cleanup the working directory.
        
        @param name directory name to be cleaned up (string)
        """
        patterns = self.getPlugin().getPreferences("CleanupPatterns").split()
        
        entries = []
        for pat in patterns:
            entries.extend(Utilities.direntries(name, True, pat))
        
        for entry in entries:
            try:
                os.remove(entry)
            except OSError:
                pass
    
    def vcsCommandLine(self, name):
        """
        Public method used to execute arbitrary mercurial commands.
        
        @param name directory name of the working directory (string)
        """
        from .HgCommandDialog import HgCommandDialog
        dlg = HgCommandDialog(self.commandHistory, name)
        if dlg.exec_() == QDialog.Accepted:
            command = dlg.getData()
            commandList = Utilities.parseOptionString(command)
            
            # This moves any previous occurrence of these arguments to the head
            # of the list.
            if command in self.commandHistory:
                self.commandHistory.remove(command)
            self.commandHistory.insert(0, command)
            
            args = []
            self.addArguments(args, commandList)
            
            # find the root of the repo
            repodir = name
            while not os.path.isdir(os.path.join(repodir, self.adminDir)):
                repodir = os.path.dirname(repodir)
                if os.path.splitdrive(repodir)[1] == os.sep:
                    return
            
            dia = HgDialog(self.tr('Mercurial command'), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def vcsOptionsDialog(self, project, archive, editable=False, parent=None):
        """
        Public method to get a dialog to enter repository info.
        
        @param project reference to the project object
        @param archive name of the project in the repository (string)
        @param editable flag indicating that the project name is editable
            (boolean)
        @param parent parent widget (QWidget)
        @return reference to the instantiated options dialog (HgOptionsDialog)
        """
        from .HgOptionsDialog import HgOptionsDialog
        return HgOptionsDialog(self, project, parent)
    
    def vcsNewProjectOptionsDialog(self, parent=None):
        """
        Public method to get a dialog to enter repository info for getting a
        new project.
        
        @param parent parent widget (QWidget)
        @return reference to the instantiated options dialog
            (HgNewProjectOptionsDialog)
        """
        from .HgNewProjectOptionsDialog import HgNewProjectOptionsDialog
        return HgNewProjectOptionsDialog(self, parent)
    
    def vcsRepositoryInfos(self, ppath):
        """
        Public method to retrieve information about the repository.
        
        @param ppath local path to get the repository infos (string)
        @return string with ready formated info for display (string)
        """
        args = self.initCommand("parents")
        args.append('--template')
        args.append('{rev}:{node|short}@@@{tags}@@@{author|xmlescape}@@@'
                    '{date|isodate}@@@{branches}@@@{bookmarks}\n')
        
        output = ""
        if self.__client is None:
            process = QProcess()
            process.setWorkingDirectory(ppath)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.getEncoding(), 'replace')
        else:
            output, error = self.__client.runcommand(args)
        
        infoBlock = []
        if output:
            index = 0
            for line in output.splitlines():
                index += 1
                changeset, tags, author, date, branches, bookmarks = \
                    line.split("@@@")
                cdate, ctime = date.split()[:2]
                info = []
                info.append(QCoreApplication.translate(
                    "mercurial",
                    """<tr><td><b>Parent #{0}</b></td><td></td></tr>\n"""
                    """<tr><td><b>Changeset</b></td><td>{1}</td></tr>""")
                    .format(index, changeset))
                if tags:
                    info.append(QCoreApplication.translate(
                        "mercurial",
                        """<tr><td><b>Tags</b></td><td>{0}</td></tr>""")
                        .format('<br/>'.join(tags.split())))
                if bookmarks:
                    info.append(QCoreApplication.translate(
                        "mercurial",
                        """<tr><td><b>Bookmarks</b></td><td>{0}</td></tr>""")
                        .format('<br/>'.join(bookmarks.split())))
                if branches:
                    info.append(QCoreApplication.translate(
                        "mercurial",
                        """<tr><td><b>Branches</b></td><td>{0}</td></tr>""")
                        .format('<br/>'.join(branches.split())))
                info.append(QCoreApplication.translate(
                    "mercurial",
                    """<tr><td><b>Last author</b></td><td>{0}</td></tr>\n"""
                    """<tr><td><b>Committed date</b></td><td>{1}</td></tr>\n"""
                    """<tr><td><b>Committed time</b></td><td>{2}</td></tr>""")
                    .format(author, cdate, ctime))
                infoBlock.append("\n".join(info))
        if infoBlock:
            infoStr = """<tr></tr>{0}""".format("<tr></tr>".join(infoBlock))
        else:
            infoStr = ""
        
        url = ""
        args = self.initCommand("showconfig")
        args.append('paths.default')
        
        output = ""
        if self.__client is None:
            process.setWorkingDirectory(ppath)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.getEncoding(), 'replace')
        else:
            output, error = self.__client.runcommand(args)
        
        if output:
            url = output.splitlines()[0].strip()
        else:
            url = ""
        
        return QCoreApplication.translate(
            'mercurial',
            """<h3>Repository information</h3>\n"""
            """<p><table>\n"""
            """<tr><td><b>Mercurial V.</b></td><td>{0}</td></tr>\n"""
            """<tr></tr>\n"""
            """<tr><td><b>URL</b></td><td>{1}</td></tr>\n"""
            """{2}"""
            """</table></p>\n"""
        ).format(self.versionStr, url, infoStr)
    
    def vcsSupportCommandOptions(self):
        """
        Public method to signal the support of user settable command options.
        
        @return flag indicating the support  of user settable command options
            (boolean)
        """
        return False
    
    ###########################################################################
    ## Private Mercurial specific methods are below.
    ###########################################################################
    
    def __hgURL(self, url):
        """
        Private method to format a url for Mercurial.
        
        @param url unformatted url string (string)
        @return properly formated url for mercurial (string)
        """
        url = self.hgNormalizeURL(url)
        url = url.split(':', 2)
        if len(url) == 4:
            scheme = url[0]
            user = url[1]
            host = url[2]
            port, path = url[3].split("/", 1)
            return "{0}:{1}:{2}:{3}/{4}".format(
                scheme, user, host, port, Utilities.quote(path))
        elif len(url) == 3:
            scheme = url[0]
            host = url[1]
            port, path = url[2].split("/", 1)
            return "{0}:{1}:{2}/{3}".format(
                scheme, host, port, Utilities.quote(path))
        else:
            scheme = url[0]
            if scheme == "file":
                return "{0}:{1}".format(scheme, Utilities.quote(url[1]))
            else:
                host, path = url[1][2:].split("/", 1)
                return "{0}://{1}/{2}".format(
                    scheme, host, Utilities.quote(path))

    def hgNormalizeURL(self, url):
        """
        Public method to normalize a url for Mercurial.
        
        @param url url string (string)
        @return properly normalized url for mercurial (string)
        """
        url = url.replace('\\', '/')
        if url.endswith('/'):
            url = url[:-1]
        urll = url.split('//')
        return "{0}//{1}".format(urll[0], '/'.join(urll[1:]))
    
    def hgCopy(self, name, project):
        """
        Public method used to copy a file/directory.
        
        @param name file/directory name to be copied (string)
        @param project reference to the project object
        @return flag indicating successful operation (boolean)
        """
        from .HgCopyDialog import HgCopyDialog
        dlg = HgCopyDialog(name)
        res = False
        if dlg.exec_() == QDialog.Accepted:
            target, force = dlg.getData()
            
            args = self.initCommand("copy")
            args.append("-v")
            args.append(name)
            args.append(target)
            
            dname, fname = self.splitPath(name)
            # find the root of the repo
            repodir = dname
            while not os.path.isdir(os.path.join(repodir, self.adminDir)):
                repodir = os.path.dirname(repodir)
                if os.path.splitdrive(repodir)[1] == os.sep:
                    return False
            
            dia = HgDialog(
                self.tr('Copying {0}').format(name), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.normalExit()
                if res and \
                   target.startswith(project.getProjectPath()):
                    if os.path.isdir(name):
                        project.copyDirectory(name, target)
                    else:
                        project.appendFile(target)
        return res
    
    def hgGetTagsList(self, repodir, withType=False):
        """
        Public method to get the list of tags.
        
        @param repodir directory name of the repository (string)
        @param withType flag indicating to get the tag type as well (boolean)
        @return list of tags (list of string) or list of tuples of
            tag name and flag indicating a local tag (list of tuple of string
            and boolean), if withType is True
        """
        args = self.initCommand("tags")
        args.append('--verbose')
        
        output = ""
        if self.__client is None:
            process = QProcess()
            process.setWorkingDirectory(repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.getEncoding(), 'replace')
        else:
            output, error = self.__client.runcommand(args)
        
        tagsList = []
        if output:
            for line in output.splitlines():
                li = line.strip().split()
                if li[-1][0] in "1234567890":
                    # last element is a rev:changeset
                    del li[-1]
                    isLocal = False
                else:
                    del li[-2:]
                    isLocal = True
                name = " ".join(li)
                if name not in ["tip", "default"]:
                    if withType:
                        tagsList.append((name, isLocal))
                    else:
                        tagsList.append(name)
        
        if withType:
            return tagsList
        else:
            if tagsList:
                self.tagsList = tagsList
            return self.tagsList[:]
    
    def hgGetBranchesList(self, repodir):
        """
        Public method to get the list of branches.
        
        @param repodir directory name of the repository (string)
        @return list of branches (list of string)
        """
        args = self.initCommand("branches")
        args.append('--closed')
        
        output = ""
        if self.__client is None:
            process = QProcess()
            process.setWorkingDirectory(repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.getEncoding(), 'replace')
        else:
            output, error = self.__client.runcommand(args)
        
        if output:
            self.branchesList = []
            for line in output.splitlines():
                li = line.strip().split()
                if li[-1][0] in "1234567890":
                    # last element is a rev:changeset
                    del li[-1]
                else:
                    del li[-2:]
                name = " ".join(li)
                if name not in ["tip", "default"]:
                    self.branchesList.append(name)
        
        return self.branchesList[:]
    
    def hgListTagBranch(self, path, tags=True):
        """
        Public method used to list the available tags or branches.
        
        @param path directory name of the project (string)
        @param tags flag indicating listing of branches or tags
                (False = branches, True = tags)
        """
        from .HgTagBranchListDialog import HgTagBranchListDialog
        self.tagbranchList = HgTagBranchListDialog(self)
        self.tagbranchList.show()
        if tags:
            if not self.showedTags:
                self.showedTags = True
                allTagsBranchesList = self.allTagsBranchesList
            else:
                self.tagsList = []
                allTagsBranchesList = None
            self.tagbranchList.start(path, tags,
                                     self.tagsList, allTagsBranchesList)
        else:
            if not self.showedBranches:
                self.showedBranches = True
                allTagsBranchesList = self.allTagsBranchesList
            else:
                self.branchesList = []
                allTagsBranchesList = None
            self.tagbranchList.start(path, tags,
                                     self.branchesList,
                                     self.allTagsBranchesList)
    
    def hgAnnotate(self, name):
        """
        Public method to show the output of the hg annotate command.
        
        @param name file name to show the annotations for (string)
        """
        if self.annotate is None:
            from .HgAnnotateDialog import HgAnnotateDialog
            self.annotate = HgAnnotateDialog(self)
        self.annotate.show()
        self.annotate.raise_()
        self.annotate.start(name)
    
    def hgExtendedDiff(self, name):
        """
        Public method used to view the difference of a file/directory to the
        Mercurial repository.
        
        If name is a directory and is the project directory, all project files
        are saved first. If name is a file (or list of files), which is/are
        being edited and has unsaved modification, they can be saved or the
        operation may be aborted.
        
        This method gives the chance to enter the revisions to be compared.
        
        @param name file/directory name to be diffed (string)
        """
        if isinstance(name, list):
            dname, fnames = self.splitPathList(name)
            names = name[:]
        else:
            dname, fname = self.splitPath(name)
            names = [name]
        for nam in names:
            if os.path.isfile(nam):
                editor = e5App().getObject("ViewManager").getOpenEditor(nam)
                if editor and not editor.checkDirty():
                    return
            else:
                project = e5App().getObject("Project")
                if nam == project.ppath and not project.saveAllScripts():
                    return
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgRevisionsSelectionDialog import HgRevisionsSelectionDialog
        dlg = HgRevisionsSelectionDialog(self.hgGetTagsList(repodir),
                                         self.hgGetBranchesList(repodir),
                                         self.hgGetBookmarksList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            revisions = dlg.getRevisions()
            if self.diff is None:
                from .HgDiffDialog import HgDiffDialog
                self.diff = HgDiffDialog(self)
            self.diff.show()
            self.diff.raise_()
            self.diff.start(name, revisions)
    
    def __hgGetFileForRevision(self, name, rev=""):
        """
        Private method to get a file for a specific revision from the
        repository.
        
        @param name file name to get from the repository (string)
        @keyparam rev revision to retrieve (string)
        @return contents of the file (string) and an error message (string)
        """
        args = self.initCommand("cat")
        if rev:
            args.append("--rev")
            args.append(rev)
        args.append(name)
        
        if self.__client is None:
            output = ""
            error = ""
            
            # find the root of the repo
            repodir = self.splitPath(name)[0]
            while not os.path.isdir(os.path.join(repodir, self.adminDir)):
                repodir = os.path.dirname(repodir)
                if os.path.splitdrive(repodir)[1] == os.sep:
                    return
            
            process = QProcess()
            process.setWorkingDirectory(repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished:
                    if process.exitCode() == 0:
                        output = str(process.readAllStandardOutput(),
                                     self.getEncoding(), 'replace')
                    else:
                        error = str(process.readAllStandardError(),
                                    self.getEncoding(), 'replace')
                else:
                    error = self.tr(
                        "The hg process did not finish within 30s.")
            else:
                error = self.tr(
                    'The process {0} could not be started. '
                    'Ensure, that it is in the search path.').format('hg')
        else:
            output, error = self.__client.runcommand(args)
        
        # return file contents with 'universal newlines'
        return output.replace('\r\n', '\n').replace('\r', '\n'), error
    
    def hgSbsDiff(self, name, extended=False, revisions=None):
        """
        Public method used to view the difference of a file to the Mercurial
        repository side-by-side.
        
        @param name file name to be diffed (string)
        @keyparam extended flag indicating the extended variant (boolean)
        @keyparam revisions tuple of two revisions (tuple of strings)
        @exception ValueError raised to indicate an invalid name parameter
        """
        if isinstance(name, list):
            raise ValueError("Wrong parameter type")
        
        if extended:
            # find the root of the repo
            repodir = self.splitPath(name)[0]
            while not os.path.isdir(os.path.join(repodir, self.adminDir)):
                repodir = os.path.dirname(repodir)
                if os.path.splitdrive(repodir)[1] == os.sep:
                    return
            
            from .HgRevisionsSelectionDialog import HgRevisionsSelectionDialog
            dlg = HgRevisionsSelectionDialog(self.hgGetTagsList(repodir),
                                             self.hgGetBranchesList(repodir),
                                             self.hgGetBookmarksList(repodir))
            if dlg.exec_() == QDialog.Accepted:
                rev1, rev2 = dlg.getRevisions()
        elif revisions:
            rev1, rev2 = revisions[0], revisions[1]
        else:
            rev1, rev2 = "", ""
        
        output1, error = self.__hgGetFileForRevision(name, rev=rev1)
        if error:
            E5MessageBox.critical(
                self.__ui,
                self.tr("Mercurial Side-by-Side Difference"),
                error)
            return
        name1 = "{0} (rev. {1})".format(name, rev1 and rev1 or ".")
        
        if rev2:
            output2, error = self.__hgGetFileForRevision(name, rev=rev2)
            if error:
                E5MessageBox.critical(
                    self.__ui,
                    self.tr("Mercurial Side-by-Side Difference"),
                    error)
                return
            name2 = "{0} (rev. {1})".format(name, rev2)
        else:
            try:
                f1 = open(name, "r", encoding="utf-8")
                output2 = f1.read()
                f1.close()
                name2 = "{0} (Work)".format(name)
            except IOError:
                E5MessageBox.critical(
                    self.__ui,
                    self.tr("Mercurial Side-by-Side Difference"),
                    self.tr(
                        """<p>The file <b>{0}</b> could not be read.</p>""")
                    .format(name))
                return
        
        if self.sbsDiff is None:
            from UI.CompareDialog import CompareDialog
            self.sbsDiff = CompareDialog()
        self.sbsDiff.show()
        self.sbsDiff.raise_()
        self.sbsDiff.compare(output1, output2, name1, name2)
    
    def vcsLogBrowser(self, name, isFile=False):
        """
        Public method used to browse the log of a file/directory from the
        Mercurial repository.
        
        @param name file/directory name to show the log of (string)
        @keyparam isFile flag indicating log for a file is to be shown
            (boolean)
        """
        if self.logBrowser is None:
            from .HgLogBrowserDialog import HgLogBrowserDialog
            self.logBrowser = HgLogBrowserDialog(self)
        self.logBrowser.show()
        self.logBrowser.raise_()
        self.logBrowser.start(name, isFile=isFile)
    
    def hgIncoming(self, name):
        """
        Public method used to view the log of incoming changes from the
        Mercurial repository.
        
        @param name file/directory name to show the log of (string)
        """
        if self.getPlugin().getPreferences("UseLogBrowser"):
            if self.logBrowserIncoming is None:
                from .HgLogBrowserDialog import HgLogBrowserDialog
                self.logBrowserIncoming = HgLogBrowserDialog(
                    self, mode="incoming")
            self.logBrowserIncoming.show()
            self.logBrowserIncoming.raise_()
            self.logBrowserIncoming.start(name)
        else:
            from .HgLogDialog import HgLogDialog
            self.log = HgLogDialog(self, mode="incoming")
            self.log.show()
            self.log.start(name)
    
    def hgOutgoing(self, name):
        """
        Public method used to view the log of outgoing changes from the
        Mercurial repository.
        
        @param name file/directory name to show the log of (string)
        """
        if self.getPlugin().getPreferences("UseLogBrowser"):
            if self.logBrowserOutgoing is None:
                from .HgLogBrowserDialog import HgLogBrowserDialog
                self.logBrowserOutgoing = HgLogBrowserDialog(
                    self, mode="outgoing")
            self.logBrowserOutgoing.show()
            self.logBrowserOutgoing.raise_()
            self.logBrowserOutgoing.start(name)
        else:
            from .HgLogDialog import HgLogDialog
            self.log = HgLogDialog(self, mode="outgoing")
            self.log.show()
            self.log.start(name)
    
    def hgPull(self, name):
        """
        Public method used to pull changes from a remote Mercurial repository.
        
        @param name directory name of the project to be pulled to (string)
        @return flag indicating, that the update contained an add
            or delete (boolean)
        """
        if self.getPlugin().getPreferences("PreferUnbundle") and \
           self.bundleFile and \
           os.path.exists(self.bundleFile):
            command = "unbundle"
            title = self.tr('Apply changegroups')
        else:
            command = "pull"
            title = self.tr('Pulling from a remote Mercurial repository')
        
        args = self.initCommand(command)
        args.append('-v')
        if self.getPlugin().getPreferences("PullUpdate"):
            args.append('--update')
        if command == "unbundle":
            args.append(self.bundleFile)
        
        # find the root of the repo
        repodir = self.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        dia = HgDialog(title, self)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            res = dia.hasAddOrDelete()
        if self.bundleFile and \
           os.path.exists(self.bundleFile):
            os.remove(self.bundleFile)
            self.bundleFile = None
        self.checkVCSStatus()
        return res
    
    def hgPush(self, name, force=False, newBranch=False, rev=None):
        """
        Public method used to push changes to a remote Mercurial repository.
        
        @param name directory name of the project to be pushed from (string)
        @keyparam force flag indicating a forced push (boolean)
        @keyparam newBranch flag indicating to push a new branch (boolean)
        @keyparam rev revision to be pushed (including all ancestors) (string)
        """
        args = self.initCommand("push")
        args.append('-v')
        if force:
            args.append('-f')
        if newBranch:
            args.append('--new-branch')
        if rev:
            args.append('--rev')
            args.append(rev)
        
        # find the root of the repo
        repodir = self.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        dia = HgDialog(
            self.tr('Pushing to a remote Mercurial repository'), self)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
        self.checkVCSStatus()
    
    def hgInfo(self, ppath, mode="heads"):
        """
        Public method to show information about the heads of the repository.
        
        @param ppath local path to get the repository infos (string)
        @keyparam mode mode of the operation (string, one of heads, parents,
            tip)
        """
        if mode not in ("heads", "parents", "tip"):
            mode = "heads"
        
        info = []
        
        args = self.initCommand(mode)
        args.append('--template')
        args.append('{rev}:{node|short}@@@{tags}@@@{author|xmlescape}@@@'
                    '{date|isodate}@@@{branches}@@@{parents}@@@{bookmarks}\n')
        
        output = ""
        if self.__client is None:
            # find the root of the repo
            repodir = self.splitPath(ppath)[0]
            while not os.path.isdir(os.path.join(repodir, self.adminDir)):
                repodir = os.path.dirname(repodir)
                if os.path.splitdrive(repodir)[1] == os.sep:
                    return
            
            process = QProcess()
            process.setWorkingDirectory(repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.getEncoding(), 'replace')
        else:
            output, error = self.__client.runcommand(args)
        
        if output:
            index = 0
            for line in output.splitlines():
                index += 1
                changeset, tags, author, date, branches, parents, bookmarks = \
                    line.split("@@@")
                cdate, ctime = date.split()[:2]
                info.append("""<p><table>""")
                if mode == "heads":
                    info.append(QCoreApplication.translate(
                        "mercurial",
                        """<tr><td><b>Head #{0}</b></td><td></td></tr>\n""")
                        .format(index))
                elif mode == "parents":
                    info.append(QCoreApplication.translate(
                        "mercurial",
                        """<tr><td><b>Parent #{0}</b></td><td></td></tr>\n""")
                        .format(index))
                elif mode == "tip":
                    info.append(QCoreApplication.translate(
                        "mercurial",
                        """<tr><td><b>Tip</b></td><td></td></tr>\n"""))
                info.append(QCoreApplication.translate(
                    "mercurial",
                    """<tr><td><b>Changeset</b></td><td>{0}</td></tr>""")
                    .format(changeset))
                if tags:
                    info.append(QCoreApplication.translate(
                        "mercurial",
                        """<tr><td><b>Tags</b></td><td>{0}</td></tr>""")
                        .format('<br/>'.join(tags.split())))
                if bookmarks:
                    info.append(QCoreApplication.translate(
                        "mercurial",
                        """<tr><td><b>Bookmarks</b></td><td>{0}</td></tr>""")
                        .format('<br/>'.join(bookmarks.split())))
                if branches:
                    info.append(QCoreApplication.translate(
                        "mercurial",
                        """<tr><td><b>Branches</b></td><td>{0}</td></tr>""")
                        .format('<br/>'.join(branches.split())))
                if parents:
                    info.append(QCoreApplication.translate(
                        "mercurial",
                        """<tr><td><b>Parents</b></td><td>{0}</td></tr>""")
                        .format('<br/>'.join(parents.split())))
                info.append(QCoreApplication.translate(
                    "mercurial",
                    """<tr><td><b>Last author</b></td><td>{0}</td></tr>\n"""
                    """<tr><td><b>Committed date</b></td><td>{1}</td></tr>\n"""
                    """<tr><td><b>Committed time</b></td><td>{2}</td></tr>\n"""
                    """</table></p>""")
                    .format(author, cdate, ctime))
            
            dlg = VcsRepositoryInfoDialog(None, "\n".join(info))
            dlg.exec_()
    
    def hgConflicts(self, name):
        """
        Public method used to show a list of files containing conflicts.
        
        @param name file/directory name to be resolved (string)
        """
        if self.conflictsDlg is None:
            from .HgConflictsListDialog import HgConflictsListDialog
            self.conflictsDlg = HgConflictsListDialog(self)
        self.conflictsDlg.show()
        self.conflictsDlg.raise_()
        self.conflictsDlg.start(name)
    
    def hgResolved(self, name, unresolve=False):
        """
        Public method used to resolve conflicts of a file/directory.
        
        @param name file/directory name to be resolved (string)
        @param unresolve flag indicating to mark the file/directory as
            unresolved (boolean)
        """
        args = self.initCommand("resolve")
        if unresolve:
            args.append("--unmark")
        else:
            args.append("--mark")
        
        if isinstance(name, list):
            dname, fnames = self.splitPathList(name)
            self.addArguments(args, name)
        else:
            dname, fname = self.splitPath(name)
            args.append(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        if unresolve:
            title = self.tr("Marking as 'unresolved'")
        else:
            title = self.tr("Marking as 'resolved'")
        dia = HgDialog(title, self)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
        self.checkVCSStatus()
    
    def hgCancelMerge(self, name):
        """
        Public method to cancel an uncommitted merge.
        
        @param name file/directory name (string)
        @return flag indicating, that the cancellation contained an add
            or delete (boolean)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.initCommand("update")
        args.append("--clean")
        
        dia = HgDialog(
            self.tr('Cancelling uncommitted merge'),
            self)
        res = dia.startProcess(args, repodir, False)
        if res:
            dia.exec_()
            res = dia.hasAddOrDelete()
        self.checkVCSStatus()
        return res
    
    def hgBranch(self, name):
        """
        Public method used to create a branch in the Mercurial repository.
        
        @param name file/directory name to be branched (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgBranchInputDialog import HgBranchInputDialog
        dlg = HgBranchInputDialog(self.hgGetBranchesList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            name, commit = dlg.getData()
            name = name.strip().replace(" ", "_")
            args = self.initCommand("branch")
            args.append(name)
            
            dia = HgDialog(
                self.tr('Creating branch in the Mercurial repository'),
                self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                if commit:
                    self.vcsCommit(
                        repodir,
                        self.tr("Created new branch <{0}>.").format(
                            name))
    
    def hgShowBranch(self, name):
        """
        Public method used to show the current branch of the working directory.
        
        @param name file/directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.initCommand("branch")
        
        dia = HgDialog(self.tr('Showing current branch'), self)
        res = dia.startProcess(args, repodir, False)
        if res:
            dia.exec_()
    
    def hgEditUserConfig(self):
        """
        Public method used to edit the user configuration file.
        """
        from .HgUtilities import getConfigPath
        cfgFile = getConfigPath()
        if not os.path.exists(cfgFile):
            # open dialog to enter the initial data
            from .HgUserConfigDataDialog import HgUserConfigDataDialog
            dlg = HgUserConfigDataDialog(version=self.version)
            if dlg.exec_() == QDialog.Accepted:
                firstName, lastName, email, extensions, extensionsData = \
                    dlg.getData()
            else:
                firstName, lastName, email, extensions, extensionsData = (
                    "Firstname", "Lastname", "email_address", [], {})
            try:
                f = open(cfgFile, "w")
                f.write("[ui]\n")
                f.write("username = {0} {1} <{2}>\n".format(
                    firstName, lastName, email))
                if extensions:
                    f.write("\n[extensions]\n")
                    f.write(" =\n".join(extensions))
                    f.write(" =\n")     # complete the last line
                if "largefiles" in extensionsData:
                    dataDict = extensionsData["largefiles"]
                    f.write("\n[largefiles]\n")
                    if "minsize" in dataDict:
                        f.write("minsize = {0}\n".format(dataDict["minsize"]))
                    if "patterns" in dataDict:
                        f.write("patterns =\n")
                        f.write("  {0}\n".format(
                            "\n  ".join(dataDict["patterns"])))
                f.close()
            except (IOError, OSError):
                # ignore these
                pass
        self.userEditor = MiniEditor(cfgFile, "Properties")
        self.userEditor.show()
    
    def hgEditConfig(self, name, withLargefiles=True, largefilesData=None):
        """
        Public method used to edit the repository configuration file.
        
        @param name file/directory name (string)
        @param withLargefiles flag indicating to configure the largefiles
            section (boolean)
        @param largefilesData dictionary with data for the largefiles
            section of the data dialog (dict)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        cfgFile = os.path.join(repodir, self.adminDir, "hgrc")
        if not os.path.exists(cfgFile):
            # open dialog to enter the initial data
            withLargefiles = (self.isExtensionActive("largefiles") and
                              withLargefiles)
            from .HgRepoConfigDataDialog import HgRepoConfigDataDialog
            dlg = HgRepoConfigDataDialog(withLargefiles=withLargefiles,
                                         largefilesData=largefilesData)
            if dlg.exec_() == QDialog.Accepted:
                createContents = True
                defaultUrl, defaultPushUrl = dlg.getData()
                if withLargefiles:
                    lfMinSize, lfPattern = dlg.getLargefilesData()
            else:
                createContents = False
            try:
                cfg = open(cfgFile, "w")
                if createContents:
                    # write the data entered
                    cfg.write("[paths]\n")
                    if defaultUrl:
                        cfg.write("default = {0}\n".format(defaultUrl))
                    if defaultPushUrl:
                        cfg.write("default-push = {0}\n".format(
                            defaultPushUrl))
                    if withLargefiles and \
                            (lfMinSize, lfPattern) != (None, None):
                        cfg.write("\n[largefiles]\n")
                        if lfMinSize is not None:
                            cfg.write("minsize = {0}\n".format(lfMinSize))
                        if lfPattern is not None:
                            cfg.write("patterns =\n")
                            cfg.write("  {0}\n".format(
                                "\n  ".join(lfPattern)))
                cfg.close()
                self.__monitorRepoIniFile(repodir)
                self.__iniFileChanged(cfgFile)
            except IOError:
                pass
        self.repoEditor = MiniEditor(cfgFile, "Properties")
        self.repoEditor.show()
    
    def hgVerify(self, name):
        """
        Public method to verify the integrity of the repository.
        
        @param name file/directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.initCommand("verify")
        
        dia = HgDialog(
            self.tr('Verifying the integrity of the Mercurial repository'),
            self)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
    
    def hgShowConfig(self, name):
        """
        Public method to show the combined configuration.
        
        @param name file/directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.initCommand("showconfig")
        args.append("--untrusted")
        
        dia = HgDialog(
            self.tr('Showing the combined configuration settings'),
            self)
        res = dia.startProcess(args, repodir, False)
        if res:
            dia.exec_()
    
    def hgShowPaths(self, name):
        """
        Public method to show the path aliases for remote repositories.
        
        @param name file/directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.initCommand("paths")
        
        dia = HgDialog(
            self.tr('Showing aliases for remote repositories'),
            self)
        res = dia.startProcess(args, repodir, False)
        if res:
            dia.exec_()
    
    def hgRecover(self, name):
        """
        Public method to recover an interrupted transaction.
        
        @param name file/directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.initCommand("recover")
        
        dia = HgDialog(
            self.tr('Recovering from interrupted transaction'),
            self)
        res = dia.startProcess(args, repodir, False)
        if res:
            dia.exec_()
    
    def hgIdentify(self, name):
        """
        Public method to identify the current working directory.
        
        @param name file/directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.initCommand("identify")
        
        dia = HgDialog(self.tr('Identifying project directory'), self)
        res = dia.startProcess(args, repodir, False)
        if res:
            dia.exec_()
    
    def hgCreateIgnoreFile(self, name, autoAdd=False):
        """
        Public method to create the ignore file.
        
        @param name directory name to create the ignore file in (string)
        @param autoAdd flag indicating to add it automatically (boolean)
        @return flag indicating success
        """
        status = False
        ignorePatterns = [
            "glob:.eric6project",
            "glob:_eric6project",
            "glob:.eric5project",
            "glob:_eric5project",
            "glob:.eric4project",
            "glob:_eric4project",
            "glob:.ropeproject",
            "glob:_ropeproject",
            "glob:.directory",
            "glob:**.pyc",
            "glob:**.pyo",
            "glob:**.orig",
            "glob:**.bak",
            "glob:**.rej",
            "glob:**~",
            "glob:cur",
            "glob:tmp",
            "glob:__pycache__",
            "glob:**.DS_Store",
        ]
        
        ignoreName = os.path.join(name, Hg.IgnoreFileName)
        if os.path.exists(ignoreName):
            res = E5MessageBox.yesNo(
                self.__ui,
                self.tr("Create .hgignore file"),
                self.tr("""<p>The file <b>{0}</b> exists already."""
                        """ Overwrite it?</p>""").format(ignoreName),
                icon=E5MessageBox.Warning)
        else:
            res = True
        if res:
            try:
                # create a .hgignore file
                ignore = open(ignoreName, "w")
                ignore.write("\n".join(ignorePatterns))
                ignore.write("\n")
                ignore.close()
                status = True
            except IOError:
                status = False
            
            if status and autoAdd:
                self.vcsAdd(ignoreName, noDialog=True)
                project = e5App().getObject("Project")
                project.appendFile(ignoreName)
        
        return status
    
    def hgBundle(self, name):
        """
        Public method to create a changegroup file.
        
        @param name file/directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgBundleDialog import HgBundleDialog
        dlg = HgBundleDialog(self.hgGetTagsList(repodir),
                             self.hgGetBranchesList(repodir),
                             self.hgGetBookmarksList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            revs, baseRevs, compression, all = dlg.getParameters()
            
            fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
                None,
                self.tr("Create changegroup"),
                self.__lastChangeGroupPath or repodir,
                self.tr("Mercurial Changegroup Files (*.hg)"),
                None,
                E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
            
            if not fname:
                return  # user aborted
            
            ext = QFileInfo(fname).suffix()
            if not ext:
                ex = selectedFilter.split("(*")[1].split(")")[0]
                if ex:
                    fname += ex
            if QFileInfo(fname).exists():
                res = E5MessageBox.yesNo(
                    self.__ui,
                    self.tr("Create changegroup"),
                    self.tr("<p>The Mercurial changegroup file <b>{0}</b> "
                            "already exists. Overwrite it?</p>")
                        .format(fname),
                    icon=E5MessageBox.Warning)
                if not res:
                    return
            fname = Utilities.toNativeSeparators(fname)
            self.__lastChangeGroupPath = os.path.dirname(fname)
            
            args = self.initCommand("bundle")
            if all:
                args.append("--all")
            for rev in revs:
                args.append("--rev")
                args.append(rev)
            for baseRev in baseRevs:
                args.append("--base")
                args.append(baseRev)
            if compression:
                args.append("--type")
                args.append(compression)
            args.append(fname)
            
            dia = HgDialog(self.tr('Create changegroup'), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgPreviewBundle(self, name):
        """
        Public method used to view the log of incoming changes from a
        changegroup file.
        
        @param name directory name on which to base the changegroup (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        file = E5FileDialog.getOpenFileName(
            None,
            self.tr("Preview changegroup"),
            self.__lastChangeGroupPath or repodir,
            self.tr("Mercurial Changegroup Files (*.hg);;All Files (*)"))
        if file:
            self.__lastChangeGroupPath = os.path.dirname(file)
            
            if self.getPlugin().getPreferences("UseLogBrowser"):
                if self.logBrowserIncoming is None:
                    from .HgLogBrowserDialog import HgLogBrowserDialog
                    self.logBrowserIncoming = \
                        HgLogBrowserDialog(self, mode="incoming")
                self.logBrowserIncoming.show()
                self.logBrowserIncoming.raise_()
                self.logBrowserIncoming.start(name, bundle=file)
            else:
                from .HgLogDialog import HgLogDialog
                self.log = HgLogDialog(self, mode="incoming", bundle=file)
                self.log.show()
                self.log.start(name)
    
    def hgUnbundle(self, name):
        """
        Public method to apply changegroup files.
        
        @param name directory name (string)
        @return flag indicating, that the update contained an add
            or delete (boolean)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        res = False
        files = E5FileDialog.getOpenFileNames(
            None,
            self.tr("Apply changegroups"),
            self.__lastChangeGroupPath or repodir,
            self.tr("Mercurial Changegroup Files (*.hg);;All Files (*)"))
        if files:
            self.__lastChangeGroupPath = os.path.dirname(files[0])
            
            update = E5MessageBox.yesNo(
                self.__ui,
                self.tr("Apply changegroups"),
                self.tr("""Shall the working directory be updated?"""),
                yesDefault=True)
            
            args = self.initCommand("unbundle")
            if update:
                args.append("--update")
                args.append("--verbose")
            args.extend(files)
            
            dia = HgDialog(self.tr('Apply changegroups'), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.hasAddOrDelete()
            self.checkVCSStatus()
        return res
    
    def hgBisect(self, name, subcommand):
        """
        Public method to perform bisect commands.
        
        @param name file/directory name (string)
        @param subcommand name of the subcommand (string, one of 'good', 'bad',
            'skip' or 'reset')
        @exception ValueError raised to indicate an invalid bisect subcommand
        """
        if subcommand not in ("good", "bad", "skip", "reset"):
            raise ValueError(
                self.tr("Bisect subcommand ({0}) invalid.")
                    .format(subcommand))
        
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        rev = ""
        if subcommand in ("good", "bad", "skip"):
            from .HgRevisionSelectionDialog import HgRevisionSelectionDialog
            dlg = HgRevisionSelectionDialog(self.hgGetTagsList(repodir),
                                            self.hgGetBranchesList(repodir),
                                            self.hgGetBookmarksList(repodir))
            if dlg.exec_() == QDialog.Accepted:
                rev = dlg.getRevision()
            else:
                return
        
        args = self.initCommand("bisect")
        args.append("--{0}".format(subcommand))
        if rev:
            args.append(rev)
        
        dia = HgDialog(
            self.tr('Mercurial Bisect ({0})').format(subcommand), self)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
    
    def hgForget(self, name):
        """
        Public method used to remove a file from the Mercurial repository.
        
        This will not remove the file from the project directory.
        
        @param name file/directory name to be removed (string or list of
            strings))
        """
        args = self.initCommand("forget")
        args.append('-v')
        
        if isinstance(name, list):
            dname, fnames = self.splitPathList(name)
            self.addArguments(args, name)
        else:
            dname, fname = self.splitPath(name)
            args.append(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        dia = HgDialog(
            self.tr('Removing files from the Mercurial repository only'),
            self)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            if isinstance(name, list):
                self.__forgotNames.extend(name)
            else:
                self.__forgotNames.append(name)
    
    def hgBackout(self, name):
        """
        Public method used to backout an earlier changeset from the Mercurial
        repository.
        
        @param name directory name (string or list of strings)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgBackoutDialog import HgBackoutDialog
        dlg = HgBackoutDialog(self.hgGetTagsList(repodir),
                              self.hgGetBranchesList(repodir),
                              self.hgGetBookmarksList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            rev, merge, date, user, message = dlg.getParameters()
            if not rev:
                E5MessageBox.warning(
                    self.__ui,
                    self.tr("Backing out changeset"),
                    self.tr("""No revision given. Aborting..."""))
                return
            
            args = self.initCommand("backout")
            args.append('-v')
            if merge:
                args.append('--merge')
            if date:
                args.append('--date')
                args.append(date)
            if user:
                args.append('--user')
                args.append(user)
            args.append('--message')
            args.append(message)
            args.append(rev)
            
            dia = HgDialog(self.tr('Backing out changeset'), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgRollback(self, name):
        """
        Public method used to rollback the last transaction.
        
        @param name directory name (string or list of strings)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        res = E5MessageBox.yesNo(
            None,
            self.tr("Rollback last transaction"),
            self.tr("""Are you sure you want to rollback the last"""
                    """ transaction?"""),
            icon=E5MessageBox.Warning)
        if res:
            dia = HgDialog(self.tr('Rollback last transaction'), self)
            res = dia.startProcess(["rollback"], repodir)
            if res:
                dia.exec_()

    def hgServe(self, name):
        """
        Public method used to serve the project.
        
        @param name directory name (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgServeDialog import HgServeDialog
        self.serveDlg = HgServeDialog(self, repodir)
        self.serveDlg.show()
    
    def hgImport(self, name):
        """
        Public method to import a patch file.
        
        @param name directory name of the project to import into (string)
        @return flag indicating, that the import contained an add, a delete
            or a change to the project file (boolean)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgImportDialog import HgImportDialog
        dlg = HgImportDialog()
        if dlg.exec_() == QDialog.Accepted:
            patchFile, noCommit, message, date, user, stripCount, force = \
                dlg.getParameters()
            
            args = self.initCommand("import")
            args.append("--verbose")
            if noCommit:
                args.append("--no-commit")
            else:
                if message:
                    args.append('--message')
                    args.append(message)
                if date:
                    args.append('--date')
                    args.append(date)
                if user:
                    args.append('--user')
                    args.append(user)
            if stripCount != 1:
                args.append("--strip")
                args.append(str(stripCount))
            if force:
                args.append("--force")
            args.append(patchFile)
            
            dia = HgDialog(self.tr("Import Patch"), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.hasAddOrDelete()
            self.checkVCSStatus()
        else:
            res = False
        
        return res
    
    def hgExport(self, name):
        """
        Public method to export patches to files.
        
        @param name directory name of the project to export from (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgExportDialog import HgExportDialog
        dlg = HgExportDialog()
        if dlg.exec_() == QDialog.Accepted:
            filePattern, revisions, switchParent, allText, noDates, git = \
                dlg.getParameters()
            
            args = self.initCommand("export")
            args.append("--output")
            args.append(filePattern)
            args.append("--verbose")
            if switchParent:
                args.append("--switch-parent")
            if allText:
                args.append("--text")
            if noDates:
                args.append("--nodates")
            if git:
                args.append("--git")
            for rev in revisions:
                args.append(rev)
            
            dia = HgDialog(self.tr("Export Patches"), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgPhase(self, name, data=None):
        """
        Public method to change the phase of revisions.
        
        @param name directory name of the project to export from (string)
        @param data tuple giving phase data (list of revisions, phase, flag
            indicating a forced operation) (list of strings, string, boolean)
        @return flag indicating success (boolean)
        @exception ValueError raised to indicate an invalid phase
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        if data is None:
            from .HgPhaseDialog import HgPhaseDialog
            dlg = HgPhaseDialog()
            if dlg.exec_() == QDialog.Accepted:
                data = dlg.getData()
        
        if data:
            revs, phase, force = data
            
            args = self.initCommand("phase")
            if phase == "p":
                args.append("--public")
            elif phase == "d":
                args.append("--draft")
            elif phase == "s":
                args.append("--secret")
            else:
                raise ValueError("Invalid phase given.")
            if force:
                args.append("--force")
            for rev in revs:
                args.append(rev)
            
            dia = HgDialog(self.tr("Change Phase"), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.normalExitWithoutErrors()
        else:
            res = False
        
        return res
    
    def hgGraft(self, path, revs=None):
        """
        Public method to copy changesets from another branch.
        
        @param path directory name of the project (string)
        @param revs list of revisions to show in the revisions pane (list of
            strings)
        @return flag indicating that the project should be reread (boolean)
        """
        # find the root of the repo
        repodir = self.splitPath(path)[0]
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        from .HgGraftDialog import HgGraftDialog
        res = False
        dlg = HgGraftDialog(self, revs)
        if dlg.exec_() == QDialog.Accepted:
            revs, (userData, currentUser, userName), \
                (dateData, currentDate, dateStr), log, dryrun = dlg.getData()
            
            args = self.initCommand("graft")
            args.append("--verbose")
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
            if log:
                args.append("--log")
            if dryrun:
                args.append("--dry-run")
            args.extend(revs)
            
            dia = HgDialog(self.tr('Copy Changesets'), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.hasAddOrDelete()
                self.checkVCSStatus()
        return res
    
    def hgGraftContinue(self, path):
        """
        Public method to continue copying changesets from another branch.
        
        @param path directory name of the project (string)
        @return flag indicating that the project should be reread (boolean)
        """
        # find the root of the repo
        repodir = self.splitPath(path)[0]
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        args = self.initCommand("graft")
        args.append("--continue")
        args.append("--verbose")
        
        dia = HgDialog(self.tr('Copy Changesets (Continue)'), self)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            res = dia.hasAddOrDelete()
            self.checkVCSStatus()
        return res
    
    def hgArchive(self):
        """
        Public method to create an unversioned archive from the repository.
        """
        # find the root of the repo
        repodir = self.__projectHelper.getProject().getProjectPath()
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgArchiveDialog import HgArchiveDialog
        dlg = HgArchiveDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            archive, type_, prefix, subrepos = dlg.getData()
            
            args = self.initCommand("archive")
            if type_:
                args.append("--type")
                args.append(type_)
            if prefix:
                args.append("--prefix")
                args.append(prefix)
            if subrepos:
                args.append("--subrepos")
            args.append(archive)
            
            dia = HgDialog(self.tr("Create Unversioned Archive"), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    ###########################################################################
    ## Methods to deal with subrepositories are below.
    ###########################################################################
    
    def getHgSubPath(self):
        """
        Public method to get the path to the .hgsub file containing the
        definitions of sub-repositories.
        
        @return full path of the .hgsub file (string)
        """
        ppath = self.__projectHelper.getProject().getProjectPath()
        return os.path.join(ppath, ".hgsub")
    
    def hasSubrepositories(self):
        """
        Public method to check, if the project might have sub-repositories.
        
        @return flag indicating the existence of sub-repositories (boolean)
        """
        hgsub = self.getHgSubPath()
        return os.path.isfile(hgsub) and os.stat(hgsub).st_size > 0
    
    def hgAddSubrepository(self):
        """
        Public method to add a sub-repository.
        """
        from .HgAddSubrepositoryDialog import HgAddSubrepositoryDialog
        ppath = self.__projectHelper.getProject().getProjectPath()
        hgsub = self.getHgSubPath()
        dlg = HgAddSubrepositoryDialog(ppath)
        if dlg.exec_() == QDialog.Accepted:
            relPath, subrepoType, subrepoUrl = dlg.getData()
            if subrepoType == "hg":
                url = subrepoUrl
            else:
                url = "[{0}]{1}".format(subrepoType, subrepoUrl)
            entry = "{0} = {1}\n".format(relPath, url)
            
            contents = []
            if os.path.isfile(hgsub):
                # file exists; check, if such an entry exists already
                needsAdd = False
                try:
                    f = open(hgsub, "r")
                    contents = f.readlines()
                    f.close()
                except IOError as err:
                    E5MessageBox.critical(
                        self.__ui,
                        self.tr("Add Sub-repository"),
                        self.tr(
                            """<p>The sub-repositories file .hgsub could not"""
                            """ be read.</p><p>Reason: {0}</p>""")
                        .format(str(err)))
                    return
                
                if entry in contents:
                    E5MessageBox.critical(
                        self.__ui,
                        self.tr("Add Sub-repository"),
                        self.tr(
                            """<p>The sub-repositories file .hgsub already"""
                            """ contains an entry <b>{0}</b>."""
                            """ Aborting...</p>""").format(entry))
                    return
            else:
                needsAdd = True
            
            if contents and not contents[-1].endswith("\n"):
                contents[-1] = contents[-1] + "\n"
            contents.append(entry)
            try:
                f = open(hgsub, "w")
                f.writelines(contents)
                f.close()
            except IOError as err:
                E5MessageBox.critical(
                    self.__ui,
                    self.tr("Add Sub-repository"),
                    self.tr(
                        """<p>The sub-repositories file .hgsub could not"""
                        """ be written to.</p><p>Reason: {0}</p>""")
                    .format(str(err)))
                return
            
            if needsAdd:
                self.vcsAdd(hgsub)
                self.__projectHelper.getProject().appendFile(hgsub)
    
    def hgRemoveSubrepositories(self):
        """
        Public method to remove sub-repositories.
        """
        hgsub = self.getHgSubPath()
        
        subrepositories = []
        if not os.path.isfile(hgsub):
            E5MessageBox.critical(
                self.__ui,
                self.tr("Remove Sub-repositories"),
                self.tr("""<p>The sub-repositories file .hgsub does not"""
                        """ exist. Aborting...</p>"""))
            return
            
        try:
            f = open(hgsub, "r")
            subrepositories = [line.strip() for line in f.readlines()]
            f.close()
        except IOError as err:
            E5MessageBox.critical(
                self.__ui,
                self.tr("Remove Sub-repositories"),
                self.tr("""<p>The sub-repositories file .hgsub could not"""
                        """ be read.</p><p>Reason: {0}</p>""")
                .format(str(err)))
            return
        
        from .HgRemoveSubrepositoriesDialog import \
            HgRemoveSubrepositoriesDialog
        dlg = HgRemoveSubrepositoriesDialog(subrepositories)
        if dlg.exec_() == QDialog.Accepted:
            subrepositories, removedSubrepos, deleteSubrepos = dlg.getData()
            contents = "\n".join(subrepositories) + "\n"
            try:
                f = open(hgsub, "w")
                f.write(contents)
                f.close()
            except IOError as err:
                E5MessageBox.critical(
                    self.__ui,
                    self.tr("Remove Sub-repositories"),
                    self.tr(
                        """<p>The sub-repositories file .hgsub could not"""
                        """ be written to.</p><p>Reason: {0}</p>""")
                    .format(str(err)))
                return
            
            if deleteSubrepos:
                ppath = self.__projectHelper.getProject().getProjectPath()
                for removedSubrepo in removedSubrepos:
                    subrepoPath = removedSubrepo.split("=", 1)[0].strip()
                    subrepoAbsPath = os.path.join(ppath, subrepoPath)
                    shutil.rmtree(subrepoAbsPath, True)
    
    ###########################################################################
    ## Methods to handle configuration dependent stuff are below.
    ###########################################################################
    
    def __checkDefaults(self):
        """
        Private method to check, if the default and default-push URLs
        have been configured.
        """
        args = self.initCommand("showconfig")
        args.append('paths')
        
        output = ""
        if self.__client is None:
            process = QProcess()
            self.__repoDir and process.setWorkingDirectory(self.__repoDir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.getEncoding(), 'replace')
        else:
            output, error = self.__client.runcommand(args)
        
        self.__defaultConfigured = False
        self.__defaultPushConfigured = False
        if output:
            for line in output.splitlines():
                if line.startswith("paths.default=") and \
                        not line.strip().endswith("="):
                    self.__defaultConfigured = True
                if line.startswith("paths.default-push=") and \
                        not line.strip().endswith("="):
                    self.__defaultPushConfigured = True
    
    def canPull(self):
        """
        Public method to check, if pull is possible.
        
        @return flag indicating pull capability (boolean)
        """
        return self.__defaultConfigured
    
    def canPush(self):
        """
        Public method to check, if push is possible.
        
        @return flag indicating push capability (boolean)
        """
        return self.__defaultPushConfigured or self.__defaultConfigured
    
    def __iniFileChanged(self, path):
        """
        Private slot to handle a change of the Mercurial configuration file.
        
        @param path name of the changed file (string)
        """
        if self.__client:
            ok, err = self.__client.restartServer()
            if not ok:
                E5MessageBox.warning(
                    None,
                    self.tr("Mercurial Command Server"),
                    self.tr(
                        """<p>The Mercurial Command Server could not be"""
                        """ restarted.</p><p>Reason: {0}</p>""").format(err))
                self.__client = None
        
        self.__getExtensionsInfo()
        
        if self.__repoIniFile and path == self.__repoIniFile:
            self.__checkDefaults()
        
        self.iniFileChanged.emit()
    
    def __monitorRepoIniFile(self, name):
        """
        Private slot to add a repository configuration file to the list of
        monitored files.
        
        @param name directory name pointing into the repository (string)
        """
        dname, fname = self.splitPath(name)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if not repodir or os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        cfgFile = os.path.join(repodir, self.adminDir, "hgrc")
        if os.path.exists(cfgFile):
            self.__iniWatcher.addPath(cfgFile)
            self.__repoIniFile = cfgFile
            self.__checkDefaults()
    
    ###########################################################################
    ## Methods to handle extensions are below.
    ###########################################################################
    
    def __getExtensionsInfo(self):
        """
        Private method to get the active extensions from Mercurial.
        """
        activeExtensions = sorted(self.__activeExtensions)
        self.__activeExtensions = []
        
        args = self.initCommand("showconfig")
        args.append('extensions')
        
        output = ""
        if self.__client is None:
            process = QProcess()
            self.__repoDir and process.setWorkingDirectory(self.__repoDir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.getEncoding(), 'replace')
        else:
            output, error = self.__client.runcommand(args)
        
        if output:
            for line in output.splitlines():
                extensionName = \
                    line.split("=", 1)[0].strip().split(".")[-1].strip()
                self.__activeExtensions.append(extensionName)
        
        if activeExtensions != sorted(self.__activeExtensions):
            self.activeExtensionsChanged.emit()
    
    def isExtensionActive(self, extensionName):
        """
        Public method to check, if an extension is active.
        
        @param extensionName name of the extension to check for (string)
        @return flag indicating an active extension (boolean)
        """
        extensionName = extensionName.strip()
        isActive = extensionName in self.__activeExtensions
        if isActive and \
            extensionName == "transplant" and \
                self.version >= (2, 3):
            # transplant extension is deprecated as of Mercurial 2.3.0
            isActive = False
        if isActive and \
            extensionName == "shelve" and \
                self.version < (2, 8):
            # shelve extension was added as of Mercurial 2.8.0
            isActive = False
        if isActive and \
            extensionName == "largefiles" and \
                self.version < (2, 0):
            # largefiles extension was added as of Mercurial 2.0.0
            isActive = False
        
        return isActive
    
    def getExtensionObject(self, extensionName):
        """
        Public method to get a reference to an extension object.
        
        @param extensionName name of the extension (string)
        @return reference to the extension object (boolean)
        """
        return self.__extensions[extensionName]
    
    ###########################################################################
    ## Methods to get the helper objects are below.
    ###########################################################################
    
    def vcsGetProjectBrowserHelper(self, browser, project,
                                   isTranslationsBrowser=False):
        """
        Public method to instantiate a helper object for the different
        project browsers.
        
        @param browser reference to the project browser object
        @param project reference to the project object
        @param isTranslationsBrowser flag indicating, the helper is requested
            for the translations browser (this needs some special treatment)
        @return the project browser helper object
        """
        from .ProjectBrowserHelper import HgProjectBrowserHelper
        return HgProjectBrowserHelper(self, browser, project,
                                      isTranslationsBrowser)
        
    def vcsGetProjectHelper(self, project):
        """
        Public method to instantiate a helper object for the project.
        
        @param project reference to the project object
        @return the project helper object
        """
        # find the root of the repo
        repodir = project.getProjectPath()
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if not repodir or os.path.splitdrive(repodir)[1] == os.sep:
                repodir = ""
                break
        if repodir:
            self.__repoDir = repodir
        
        self.__projectHelper = self.__plugin.getProjectHelper()
        self.__projectHelper.setObjects(self, project)
        self.__monitorRepoIniFile(project.getProjectPath())
        
        if repodir:
            from .HgClient import HgClient
            client = HgClient(repodir, "utf-8", self)
            ok, err = client.startServer()
            if ok:
                self.__client = client
            else:
                E5MessageBox.warning(
                    None,
                    self.tr("Mercurial Command Server"),
                    self.tr(
                        """<p>The Mercurial Command Server could not be"""
                        """ started.</p><p>Reason: {0}</p>""").format(err))
        
        return self.__projectHelper

    ###########################################################################
    ##  Status Monitor Thread methods
    ###########################################################################

    def _createStatusMonitorThread(self, interval, project):
        """
        Protected method to create an instance of the VCS status monitor
        thread.
        
        @param interval check interval for the monitor thread in seconds
            (integer)
        @param project reference to the project object (Project)
        @return reference to the monitor thread (QThread)
        """
        from .HgStatusMonitorThread import HgStatusMonitorThread
        return HgStatusMonitorThread(interval, project, self)

    ###########################################################################
    ##  Bookmarks methods
    ###########################################################################

    def hgListBookmarks(self, path):
        """
        Public method used to list the available bookmarks.
        
        @param path directory name of the project (string)
        """
        self.bookmarksList = []
        
        if self.bookmarksListDlg is None:
            from .HgBookmarksListDialog import HgBookmarksListDialog
            self.bookmarksListDlg = HgBookmarksListDialog(self)
        self.bookmarksListDlg.show()
        self.bookmarksListDlg.raise_()
        self.bookmarksListDlg.start(path, self.bookmarksList)
    
    def hgGetBookmarksList(self, repodir):
        """
        Public method to get the list of bookmarks.
        
        @param repodir directory name of the repository (string)
        @return list of bookmarks (list of string)
        """
        args = self.initCommand("bookmarks")
        
        client = self.getClient()
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
                                 self.getEncoding(), 'replace')
        
        self.bookmarksList = []
        for line in output.splitlines():
            li = line.strip().split()
            if li[-1][0] in "1234567890":
                # last element is a rev:changeset
                del li[-1]
                if li[0] == "*":
                    del li[0]
                name = " ".join(li)
                self.bookmarksList.append(name)
        
        return self.bookmarksList[:]
    
    def hgBookmarkDefine(self, name):
        """
        Public method to define a bookmark.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgBookmarkDialog import HgBookmarkDialog
        dlg = HgBookmarkDialog(HgBookmarkDialog.DEFINE_MODE,
                               self.hgGetTagsList(repodir),
                               self.hgGetBranchesList(repodir),
                               self.hgGetBookmarksList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            rev, bookmark = dlg.getData()
            
            args = self.initCommand("bookmarks")
            if rev:
                args.append("--rev")
                args.append(rev)
            args.append(bookmark)
            
            dia = HgDialog(self.tr('Mercurial Bookmark'), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgBookmarkDelete(self, name):
        """
        Public method to delete a bookmark.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        bookmark, ok = QInputDialog.getItem(
            None,
            self.tr("Delete Bookmark"),
            self.tr("Select the bookmark to be deleted:"),
            [""] + sorted(self.hgGetBookmarksList(repodir)),
            0, True)
        if ok and bookmark:
            args = self.initCommand("bookmarks")
            args.append("--delete")
            args.append(bookmark)
            
            dia = HgDialog(self.tr('Delete Mercurial Bookmark'), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgBookmarkRename(self, name):
        """
        Public method to rename a bookmark.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgBookmarkRenameDialog import HgBookmarkRenameDialog
        dlg = HgBookmarkRenameDialog(self.hgGetBookmarksList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            newName, oldName = dlg.getData()
            
            args = self.initCommand("bookmarks")
            args.append("--rename")
            args.append(oldName)
            args.append(newName)
            
            dia = HgDialog(self.tr('Rename Mercurial Bookmark'), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgBookmarkMove(self, name):
        """
        Public method to move a bookmark.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgBookmarkDialog import HgBookmarkDialog
        dlg = HgBookmarkDialog(HgBookmarkDialog.MOVE_MODE,
                               self.hgGetTagsList(repodir),
                               self.hgGetBranchesList(repodir),
                               self.hgGetBookmarksList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            rev, bookmark = dlg.getData()
            
            args = self.initCommand("bookmarks")
            args.append("--force")
            if rev:
                args.append("--rev")
                args.append(rev)
            args.append(bookmark)
            
            dia = HgDialog(self.tr('Move Mercurial Bookmark'), self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgBookmarkIncoming(self, name):
        """
        Public method to show a list of incoming bookmarks.
        
        @param name file/directory name (string)
        """
        from .HgBookmarksInOutDialog import HgBookmarksInOutDialog
        self.bookmarksInOutDlg = HgBookmarksInOutDialog(
            self, HgBookmarksInOutDialog.INCOMING)
        self.bookmarksInOutDlg.show()
        self.bookmarksInOutDlg.start(name)
    
    def hgBookmarkOutgoing(self, name):
        """
        Public method to show a list of outgoing bookmarks.
        
        @param name file/directory name (string)
        """
        from .HgBookmarksInOutDialog import HgBookmarksInOutDialog
        self.bookmarksInOutDlg = HgBookmarksInOutDialog(
            self, HgBookmarksInOutDialog.OUTGOING)
        self.bookmarksInOutDlg.show()
        self.bookmarksInOutDlg.start(name)
    
    def __getInOutBookmarks(self, repodir, incoming):
        """
        Private method to get the list of incoming or outgoing bookmarks.
        
        @param repodir directory name of the repository (string)
        @param incoming flag indicating to get incoming bookmarks (boolean)
        @return list of bookmarks (list of string)
        """
        bookmarksList = []
        
        if incoming:
            args = self.initCommand("incoming")
        else:
            args = self.initCommand("outgoing")
        args.append('--bookmarks')
        
        client = self.getClient()
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
                                 self.getEncoding(), 'replace')
        
        for line in output.splitlines():
            if line.startswith(" "):
                li = line.strip().split()
                del li[-1]
                name = " ".join(li)
                bookmarksList.append(name)
        
        return bookmarksList
    
    def hgBookmarkPull(self, name):
        """
        Public method to pull a bookmark from a remote repository.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        bookmarks = self.__getInOutBookmarks(repodir, True)
        
        bookmark, ok = QInputDialog.getItem(
            None,
            self.tr("Pull Bookmark"),
            self.tr("Select the bookmark to be pulled:"),
            [""] + sorted(bookmarks),
            0, True)
        if ok and bookmark:
            args = self.initCommand("pull")
            args.append('--bookmark')
            args.append(bookmark)
            
            dia = HgDialog(self.tr(
                'Pulling bookmark from a remote Mercurial repository'),
                self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgBookmarkPush(self, name):
        """
        Public method to push a bookmark to a remote repository.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        bookmarks = self.__getInOutBookmarks(repodir, False)
        
        bookmark, ok = QInputDialog.getItem(
            None,
            self.tr("Push Bookmark"),
            self.tr("Select the bookmark to be push:"),
            [""] + sorted(bookmarks),
            0, True)
        if ok and bookmark:
            args = self.initCommand("push")
            args.append('--bookmark')
            args.append(bookmark)
            
            dia = HgDialog(self.tr(
                'Pushing bookmark to a remote Mercurial repository'),
                self)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
