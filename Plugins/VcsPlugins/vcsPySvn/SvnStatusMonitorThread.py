# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the VCS status monitor thread class for Subversion.
"""

from __future__ import unicode_literals

import os

import pysvn

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
        
        client = pysvn.Client()
        client.exception_style = 1
        client.callback_get_login = \
            self.__clientLoginCallback
        client.callback_ssl_server_trust_prompt = \
            self.__clientSslServerTrustPromptCallback
        
        cwd = os.getcwd()
        os.chdir(self.projectDir)
        try:
            allFiles = client.status(
                '.', recurse=True, get_all=True, ignore=True,
                update=not Preferences.getVCS("MonitorLocalStatus"))
            states = {}
            for file in allFiles:
                uptodate = True
                if file.repos_text_status != pysvn.wc_status_kind.none:
                    uptodate = uptodate and \
                        file.repos_text_status != pysvn.wc_status_kind.modified
                if file.repos_prop_status != pysvn.wc_status_kind.none:
                    uptodate = uptodate and \
                        file.repos_prop_status != pysvn.wc_status_kind.modified
                
                status = ""
                if not uptodate:
                    status = "U"
                    self.shouldUpdate = True
                elif file.text_status == pysvn.wc_status_kind.conflicted or \
                        file.prop_status == pysvn.wc_status_kind.conflicted:
                    status = "Z"
                elif file.text_status == pysvn.wc_status_kind.deleted or \
                        file.prop_status == pysvn.wc_status_kind.deleted:
                    status = "O"
                elif file.text_status == pysvn.wc_status_kind.modified or \
                        file.prop_status == pysvn.wc_status_kind.modified:
                    status = "M"
                elif file.text_status == pysvn.wc_status_kind.added or \
                        file.prop_status == pysvn.wc_status_kind.added:
                    status = "A"
                elif file.text_status == pysvn.wc_status_kind.replaced or \
                        file.prop_status == pysvn.wc_status_kind.replaced:
                    status = "R"
                if status:
                    states[file.path] = status
                    try:
                        if self.reportedStates[file.path] != status:
                            self.statusList.append(
                                "{0} {1}".format(status, file.path))
                    except KeyError:
                        self.statusList.append(
                            "{0} {1}".format(status, file.path))
            for name in list(self.reportedStates.keys()):
                if name not in states:
                    self.statusList.append("  {0}".format(name))
            self.reportedStates = states
            res = True
            statusStr = self.tr(
                "Subversion status checked successfully (using pysvn)")
        except pysvn.ClientError as e:
            res = False
            statusStr = e.args[0]
        os.chdir(cwd)
        return res, statusStr
    
    def __clientLoginCallback(self, realm, username, may_save):
        """
        Private method called by the client to get login information.
        
        @param realm name of the realm of the requested credentials (string)
        @param username username as supplied by subversion (string)
        @param may_save flag indicating, that subversion is willing to save
            the answers returned (boolean)
        @return tuple of four values (retcode, username, password, save).
            Retcode should be True, if username and password should be used
            by subversion, username and password contain the relevant data
            as strings and save is a flag indicating, that username and
            password should be saved. Always returns (False, "", "", False).
        """
        return (False, "", "", False)
    
    def __clientSslServerTrustPromptCallback(self, trust_dict):
        """
        Private method called by the client to request acceptance for a
        ssl server certificate.
        
        @param trust_dict dictionary containing the trust data
        @return tuple of three values (retcode, acceptedFailures, save).
            Retcode should be true, if the certificate should be accepted,
            acceptedFailures should indicate the accepted certificate failures
            and save should be True, if subversion should save the certificate.
            Always returns (False, 0, False).
        """
        return (False, 0, False)
