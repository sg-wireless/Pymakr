# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog mixin class providing common callback methods for
the pysvn client.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QWidget


class SvnDialogMixin(object):
    """
    Class implementing a dialog mixin providing common callback methods for
    the pysvn client.
    """
    def __init__(self, log=""):
        """
        Constructor
        
        @param log optional log message (string)
        """
        self.shouldCancel = False
        self.logMessage = log
        
    def _cancel(self):
        """
        Protected method to request a cancellation of the current action.
        """
        self.shouldCancel = True
        
    def _reset(self):
        """
        Protected method to reset the internal state of the dialog.
        """
        self.shouldCancel = False
        
    def _clientCancelCallback(self):
        """
        Protected method called by the client to check for cancellation.
        
        @return flag indicating a cancellation
        """
        QApplication.processEvents()
        return self.shouldCancel
        
    def _clientLoginCallback(self, realm, username, may_save):
        """
        Protected method called by the client to get login information.
        
        @param realm name of the realm of the requested credentials (string)
        @param username username as supplied by subversion (string)
        @param may_save flag indicating, that subversion is willing to save
            the answers returned (boolean)
        @return tuple of four values (retcode, username, password, save).
            Retcode should be True, if username and password should be used
            by subversion, username and password contain the relevant data
            as strings and save is a flag indicating, that username and
            password should be saved.
        """
        from .SvnLoginDialog import SvnLoginDialog
        cursor = QApplication.overrideCursor()
        if cursor is not None:
            QApplication.restoreOverrideCursor()
        parent = isinstance(self, QWidget) and self or None
        dlg = SvnLoginDialog(realm, username, may_save, parent)
        res = dlg.exec_()
        if cursor is not None:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        if res == QDialog.Accepted:
            loginData = dlg.getData()
            return (True, loginData[0], loginData[1], loginData[2])
        else:
            return (False, "", "", False)
        
    def _clientSslServerTrustPromptCallback(self, trust_dict):
        """
        Protected method called by the client to request acceptance for a
        ssl server certificate.
        
        @param trust_dict dictionary containing the trust data
        @return tuple of three values (retcode, acceptedFailures, save).
            Retcode should be true, if the certificate should be accepted,
            acceptedFailures should indicate the accepted certificate failures
            and save should be True, if subversion should save the certificate.
        """
        from E5Gui import E5MessageBox

        cursor = QApplication.overrideCursor()
        if cursor is not None:
            QApplication.restoreOverrideCursor()
        parent = isinstance(self, QWidget) and self or None
        msgBox = E5MessageBox.E5MessageBox(
            E5MessageBox.Question,
            self.tr("Subversion SSL Server Certificate"),
            self.tr("""<p>Accept the following SSL certificate?</p>"""
                    """<table>"""
                    """<tr><td>Realm:</td><td>{0}</td></tr>"""
                    """<tr><td>Hostname:</td><td>{1}</td></tr>"""
                    """<tr><td>Fingerprint:</td><td>{2}</td></tr>"""
                    """<tr><td>Valid from:</td><td>{3}</td></tr>"""
                    """<tr><td>Valid until:</td><td>{4}</td></tr>"""
                    """<tr><td>Issuer name:</td><td>{5}</td></tr>"""
                    """</table>""")
                .format(trust_dict["realm"],
                        trust_dict["hostname"],
                        trust_dict["finger_print"],
                        trust_dict["valid_from"],
                        trust_dict["valid_until"],
                        trust_dict["issuer_dname"]),
            modal=True, parent=parent)
        permButton = msgBox.addButton(self.tr("&Permanent accept"),
                                      E5MessageBox.AcceptRole)
        tempButton = msgBox.addButton(self.tr("&Temporary accept"),
                                      E5MessageBox.AcceptRole)
        msgBox.addButton(self.tr("&Reject"), E5MessageBox.RejectRole)
        msgBox.exec_()
        if cursor is not None:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        if msgBox.clickedButton() == permButton:
            return (True, trust_dict["failures"], True)
        elif msgBox.clickedButton() == tempButton:
            return (True, trust_dict["failures"], False)
        else:
            return (False, 0, False)
        
    def _clientLogCallback(self):
        """
        Protected method called by the client to request a log message.
        
        @return a flag indicating success and the log message (string)
        """
        from .SvnCommitDialog import SvnCommitDialog
        if self.logMessage:
            return True, self.logMessage
        else:
            # call CommitDialog and get message from there
            dlg = SvnCommitDialog(self)
            if dlg.exec_() == QDialog.Accepted:
                msg = dlg.logMessage()
                if msg:
                    return True, msg
                else:
                    return True, "***"  # always supply a valid log message
            else:
                return False, ""
