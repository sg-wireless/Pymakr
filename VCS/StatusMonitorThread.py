# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the VCS status monitor thread base class.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QThread, QMutex, QWaitCondition, pyqtSignal


class VcsStatusMonitorThread(QThread):
    """
    Class implementing the VCS status monitor thread base class.
    
    @signal vcsStatusMonitorData(list of str) emitted to update the VCS status
    @signal vcsStatusMonitorStatus(str, str) emitted to signal the status of
        the monitoring thread (ok, nok, op) and a status message
    """
    vcsStatusMonitorData = pyqtSignal(list)
    vcsStatusMonitorStatus = pyqtSignal(str, str)
    
    def __init__(self, interval, project, vcs, parent=None):
        """
        Constructor
        
        @param interval new interval in seconds (integer)
        @param project reference to the project object (Project)
        @param vcs reference to the version control object
        @param parent reference to the parent object (QObject)
        """
        super(VcsStatusMonitorThread, self).__init__(parent)
        self.setObjectName("VcsStatusMonitorThread")
        
        self.setTerminationEnabled(True)
        
        self.projectDir = project.getProjectPath()
        self.project = project
        self.vcs = vcs
        
        self.interval = interval
        self.autoUpdate = False
        
        self.statusList = []
        self.reportedStates = {}
        self.shouldUpdate = False
        
        self.monitorMutex = QMutex()
        self.monitorCondition = QWaitCondition()
        self.__stopIt = False
    
    def run(self):
        """
        Public method implementing the tasks action.
        """
        while not self.__stopIt:
            # perform the checking task
            self.statusList = []
            self.vcsStatusMonitorStatus.emit(
                "wait", self.tr("Waiting for lock"))
            try:
                locked = self.vcs.vcsExecutionMutex.tryLock(5000)
            except TypeError:
                locked = self.vcs.vcsExecutionMutex.tryLock()
            if locked:
                try:
                    self.vcsStatusMonitorStatus.emit(
                        "op", self.tr("Checking repository status"))
                    res, statusMsg = self._performMonitor()
                finally:
                    self.vcs.vcsExecutionMutex.unlock()
                if res:
                    status = "ok"
                else:
                    status = "nok"
                self.vcsStatusMonitorStatus.emit(
                    "send", self.tr("Sending data"))
                self.vcsStatusMonitorData.emit(self.statusList)
                self.vcsStatusMonitorStatus.emit(status, statusMsg)
            else:
                self.vcsStatusMonitorStatus.emit(
                    "timeout", self.tr("Timed out waiting for lock"))
            
            if self.autoUpdate and self.shouldUpdate:
                self.vcs.vcsUpdate(self.projectDir, True)
                continue    # check again
                self.shouldUpdate = False
            
            # wait until interval has expired checking for a stop condition
            self.monitorMutex.lock()
            if not self.__stopIt:
                self.monitorCondition.wait(
                    self.monitorMutex, self.interval * 1000)
            self.monitorMutex.unlock()
        
        self._shutdown()
        self.exit()
    
    def setInterval(self, interval):
        """
        Public method to change the monitor interval.
        
        @param interval new interval in seconds (integer)
        """
        locked = self.monitorMutex.tryLock()
        self.interval = interval
        self.monitorCondition.wakeAll()
        if locked:
            self.monitorMutex.unlock()
    
    def getInterval(self):
        """
        Public method to get the monitor interval.
        
        @return interval in seconds (integer)
        """
        return self.interval
    
    def setAutoUpdate(self, auto):
        """
        Public method to enable the auto update function.
        
        @param auto status of the auto update function (boolean)
        """
        self.autoUpdate = auto
    
    def getAutoUpdate(self):
        """
        Public method to retrieve the status of the auto update function.
        
        @return status of the auto update function (boolean)
        """
        return self.autoUpdate
    
    def checkStatus(self):
        """
        Public method to wake up the status monitor thread.
        """
        locked = self.monitorMutex.tryLock()
        self.monitorCondition.wakeAll()
        if locked:
            self.monitorMutex.unlock()
    
    def stop(self):
        """
        Public method to stop the monitor thread.
        """
        locked = self.monitorMutex.tryLock()
        self.__stopIt = True
        self.monitorCondition.wakeAll()
        if locked:
            self.monitorMutex.unlock()

    def clearCachedState(self, name):
        """
        Public method to clear the cached VCS state of a file/directory.
        
        @param name name of the entry to be cleared (string)
        """
        key = self.project.getRelativePath(name)
        try:
            del self.reportedStates[key]
        except KeyError:
            pass

    def _performMonitor(self):
        """
        Protected method implementing the real monitoring action.
        
        This method must be overridden and populate the statusList member
        variable with a list of strings giving the status in the first column
        and the path relative to the project directory starting with the
        third column. The allowed status flags are:
        <ul>
            <li>"A" path was added but not yet comitted</li>
            <li>"M" path has local changes</li>
            <li>"O" path was removed</li>
            <li>"R" path was deleted and then re-added</li>
            <li>"U" path needs an update</li>
            <li>"Z" path contains a conflict</li>
            <li>" " path is back at normal</li>
        </ul>
        
        @ireturn tuple of flag indicating successful operation (boolean) and
            a status message in case of non successful operation (string)
        @exception RuntimeError to indicate that this method must be
            implemented by a subclass
        """
        raise RuntimeError('Not implemented')
    
    def _shutdown(self):
        """
        Protected method performing shutdown actions.
        
        The default implementation does nothing.
        """
        pass
