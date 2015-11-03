# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the VCS status monitor thread class for Subversion.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

from PyQt5.QtCore import QRegExp, QProcess

from VCS.StatusMonitorThread import VcsStatusMonitorThread

import Preferences


class SvnStatusMonitorThread(VcsStatusMonitorThread):
    """
    Class implementing the VCS status monitor thread class for Subversion.
    """
    def __init__(self, interval, project, vcs, parent=None):
        """
        Constructor
        
        @param interval new interval in seconds (integer)
        @param project reference to the project object (Project)
        @param vcs reference to the version control object
        @param parent reference to the parent object (QObject)
        """
        VcsStatusMonitorThread.__init__(self, interval, project, vcs, parent)
        
        self.__ioEncoding = Preferences.getSystem("IOEncoding")
        
        self.rx_status1 = \
            QRegExp('(.{8,9})\\s+([0-9-]+)\\s+(.+)\\s*')
        self.rx_status2 = QRegExp(
            '(.{8,9})\\s+([0-9-]+)\\s+([0-9?]+)\\s+(\\S+)\\s+(.+)\\s*')
    
    def _performMonitor(self):
        """
        Protected method implementing the monitoring action.
        
        This method populates the statusList member variable
        with a list of strings giving the status in the first column and the
        path relative to the project directory starting with the third column.
        The allowed status flags are:
        <ul>
            <li>"A" path was added but not yet comitted</li>
            <li>"M" path has local changes</li>
            <li>"O" path was removed</li>
            <li>"R" path was deleted and then re-added</li>
            <li>"U" path needs an update</li>
            <li>"Z" path contains a conflict</li>
            <li>" " path is back at normal</li>
        </ul>
        
        @return tuple of flag indicating successful operation (boolean) and
            a status message in case of non successful operation (string)
        """
        self.shouldUpdate = False
        
        process = QProcess()
        args = []
        args.append('status')
        if not Preferences.getVCS("MonitorLocalStatus"):
            args.append('--show-updates')
        args.append('--non-interactive')
        args.append('.')
        process.setWorkingDirectory(self.projectDir)
        process.start('svn', args)
        procStarted = process.waitForStarted(5000)
        if procStarted:
            finished = process.waitForFinished(300000)
            if finished and process.exitCode() == 0:
                output = str(process.readAllStandardOutput(),
                             self.__ioEncoding, 'replace')
                states = {}
                for line in output.splitlines():
                    if self.rx_status1.exactMatch(line):
                        flags = self.rx_status1.cap(1)
                        path = self.rx_status1.cap(3).strip()
                    elif self.rx_status2.exactMatch(line):
                        flags = self.rx_status2.cap(1)
                        path = self.rx_status2.cap(5).strip()
                    else:
                        continue
                    if flags[0] in "ACDMR" or \
                       (flags[0] == " " and flags[-1] == "*"):
                        if flags[-1] == "*":
                            status = "U"
                        else:
                            status = flags[0]
                        if status == "C":
                            status = "Z"    # give it highest priority
                        elif status == "D":
                            status = "O"
                        if status == "U":
                            self.shouldUpdate = True
                        name = path
                        states[name] = status
                        try:
                            if self.reportedStates[name] != status:
                                self.statusList.append(
                                    "{0} {1}".format(status, name))
                        except KeyError:
                            self.statusList.append(
                                "{0} {1}".format(status, name))
                for name in list(self.reportedStates.keys()):
                    if name not in states:
                        self.statusList.append("  {0}".format(name))
                self.reportedStates = states
                return True, self.tr(
                    "Subversion status checked successfully (using svn)")
            else:
                process.kill()
                process.waitForFinished()
                return False, \
                    str(process.readAllStandardError(),
                        Preferences.getSystem("IOEncoding"),
                        'replace')
        else:
            process.kill()
            process.waitForFinished()
            return False, self.tr(
                "Could not start the Subversion process.")
