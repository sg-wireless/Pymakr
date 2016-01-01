# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class to generate the output of the hg diff command.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import pyqtSignal, QProcess, QTimer, QObject


class HgDiffGenerator(QObject):
    """
    Class implementing the generation of output of the hg diff command.
    
    @signal finished() emitted when all processes have finished
    """
    finished = pyqtSignal()
    
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super(HgDiffGenerator, self).__init__(parent)
        
        self.vcs = vcs
        
        self.__hgClient = self.vcs.getClient()
        if self.__hgClient:
            self.process = None
        else:
            self.process = QProcess()
            self.process.finished.connect(self.__finish)
            self.process.readyReadStandardOutput.connect(self.__readStdout)
            self.process.readyReadStandardError.connect(self.__readStderr)
    
    def stopProcess(self):
        """
        Public slot to stop the diff process.
        """
        if self.__hgClient:
            if self.__hgClient.isExecuting():
                self.__hgClient.cancel()
        else:
            if self.process is not None and \
               self.process.state() != QProcess.NotRunning:
                self.process.terminate()
                QTimer.singleShot(2000, self.process.kill)
                self.process.waitForFinished(3000)
    
    def __getVersionArg(self, version):
        """
        Private method to get a hg revision argument for the given revision.
        
        @param version revision (integer or string)
        @return version argument (string)
        """
        if version == "WORKING":
            return None
        else:
            return str(version)
    
    def start(self, fn, versions=None, bundle=None, qdiff=False):
        """
        Public slot to start the hg diff command.
        
        @param fn filename to be diffed (string)
        @keyparam versions list of versions to be diffed (list of up to
            2 strings or None)
        @keyparam bundle name of a bundle file (string)
        @keyparam qdiff flag indicating qdiff command shall be used (boolean)
        @return flag indicating a successful start of the diff command
            (boolean)
        """
        if qdiff:
            args = self.vcs.initCommand("qdiff")
        else:
            args = self.vcs.initCommand("diff")
            
            if self.vcs.hasSubrepositories():
                args.append("--subrepos")
            
            if bundle:
                args.append('--repository')
                args.append(bundle)
            elif self.vcs.bundleFile and os.path.exists(self.vcs.bundleFile):
                args.append('--repository')
                args.append(self.vcs.bundleFile)
            
            if versions is not None:
                rev1 = self.__getVersionArg(versions[0])
                rev2 = None
                if len(versions) == 2:
                    rev2 = self.__getVersionArg(versions[1])
                
                if rev1 is not None or rev2 is not None:
                    args.append('-r')
                    if rev1 is not None and rev2 is not None:
                        args.append('{0}:{1}'.format(rev1, rev2))
                    elif rev2 is None:
                        args.append(rev1)
                    elif rev1 is None:
                        args.append(':{0}'.format(rev2))
        
        if isinstance(fn, list):
            dname, fnames = self.vcs.splitPathList(fn)
            self.vcs.addArguments(args, fn)
        else:
            dname, fname = self.vcs.splitPath(fn)
            args.append(fn)
        
        self.__oldFile = ""
        self.__oldFileLine = -1
        self.__fileSeparators = []
        self.__output = []
        self.__errors = []
        
        if self.__hgClient:
            out, err = self.__hgClient.runcommand(args)
            
            if err:
                self.__errors = err.splitlines(True)
            
            if out:
                for line in out.splitlines(True):
                    self.__processOutputLine(line)
                    if self.__hgClient.wasCanceled():
                        break
            
            self.__finish()
        else:
            # find the root of the repo
            repodir = dname
            while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
                repodir = os.path.dirname(repodir)
                if os.path.splitdrive(repodir)[1] == os.sep:
                    return
            
            self.process.kill()
            self.process.setWorkingDirectory(repodir)
            
            self.process.start('hg', args)
            procStarted = self.process.waitForStarted(5000)
            if not procStarted:
                return False
        
        return True
    
    def __finish(self):
        """
        Private slot called when the process finished or the user pressed
        the button.
        """
        self.finished.emit()
    
    def getResult(self):
        """
        Public method to return the result data.
        
        @return tuple of lists of string containing lines of the diff, the
            list of errors and a list of tuples of filenames and the line
            into the diff output.
        """
        return (self.__output, self.__errors, self.__fileSeparators)
    
    def __extractFileName(self, line):
        """
        Private method to extract the file name out of a file separator line.
        
        @param line line to be processed (string)
        @return extracted file name (string)
        """
        f = line.split(None, 1)[1]
        f = f.rsplit(None, 6)[0]
        if f == "/dev/null":
            f = "__NULL__"
        else:
            f = f.split("/", 1)[1]
        return f
    
    def __processFileLine(self, line):
        """
        Private slot to process a line giving the old/new file.
        
        @param line line to be processed (string)
        """
        if line.startswith('---'):
            self.__oldFileLine = len(self.__output)
            self.__oldFile = self.__extractFileName(line)
        else:
            newFile = self.__extractFileName(line)
            if self.__oldFile == "__NULL__":
                self.__fileSeparators.append(
                    (newFile, newFile, self.__oldFileLine))
            else:
                self.__fileSeparators.append(
                    (self.__oldFile, newFile, self.__oldFileLine))
    
    def __processOutputLine(self, line):
        """
        Private method to process the lines of output.
        
        @param line output line to be processed (string)
        """
        if line.startswith("--- ") or \
           line.startswith("+++ "):
            self.__processFileLine(line)
        
        self.__output.append(line)
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStandardOutput signal.
        
        It reads the output of the process, formats it and inserts it into
        the contents pane.
        """
        self.process.setReadChannel(QProcess.StandardOutput)
        
        while self.process.canReadLine():
            line = str(self.process.readLine(), self.vcs.getEncoding(),
                       'replace')
            self.__processOutputLine(line)
    
    def __readStderr(self):
        """
        Private slot to handle the readyReadStandardError signal.
        
        It reads the error output of the process and inserts it into the
        error pane.
        """
        if self.process is not None:
            s = str(self.process.readAllStandardError(),
                    self.vcs.getEncoding(), 'replace')
            self.__errors.append(s)
