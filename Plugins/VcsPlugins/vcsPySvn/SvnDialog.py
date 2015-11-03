# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of a pysvn action.
"""

from __future__ import unicode_literals

import pysvn

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QApplication, QDialogButtonBox

from .SvnConst import svnNotifyActionMap

from .SvnDialogMixin import SvnDialogMixin
from .Ui_SvnDialog import Ui_SvnDialog

import Preferences


class SvnDialog(QDialog, SvnDialogMixin, Ui_SvnDialog):
    """
    Class implementing a dialog to show the output of a pysvn action.
    """
    def __init__(self, text, command, pysvnClient, parent=None, log=""):
        """
        Constructor
        
        @param text text to be shown by the label (string)
        @param command svn command to be executed (display purposes only)
            (string)
        @param pysvnClient reference to the pysvn client object (pysvn.Client)
        @keyparam parent parent widget (QWidget)
        @keyparam log optional log message (string)
        """
        super(SvnDialog, self).__init__(parent)
        self.setupUi(self)
        SvnDialogMixin.__init__(self, log)
        self.setWindowFlags(Qt.Window)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.outputGroup.setTitle(text)
        self.errorGroup.hide()
        
        pysvnClient.callback_cancel = \
            self._clientCancelCallback
        
        pysvnClient.callback_notify = \
            self._clientNotifyCallback
        pysvnClient.callback_get_login = \
            self._clientLoginCallback
        pysvnClient.callback_ssl_server_trust_prompt = \
            self._clientSslServerTrustPromptCallback
        pysvnClient.callback_get_log_message = \
            self._clientLogCallback
        
        self.__hasAddOrDelete = False
        
        if command:
            self.resultbox.append(command)
            self.resultbox.append('')
        
        self.show()
        QApplication.processEvents()
        
    def _clientNotifyCallback(self, eventDict):
        """
        Protected method called by the client to send events.
        
        @param eventDict dictionary containing the notification event
        """
        msg = ""
        if eventDict["action"] == pysvn.wc_notify_action.update_completed:
            msg = self.tr("Revision {0}.\n").format(
                eventDict["revision"].number)
        elif eventDict["path"] != "" and \
            eventDict["action"] in svnNotifyActionMap and \
                svnNotifyActionMap[eventDict["action"]] is not None:
            mime = eventDict["mime_type"] == "application/octet-stream" and \
                self.tr(" (binary)") or ""
            msg = self.tr("{0} {1}{2}\n")\
                .format(self.tr(svnNotifyActionMap[eventDict["action"]]),
                        eventDict["path"],
                        mime)
            if '.e4p' in eventDict["path"]:
                self.__hasAddOrDelete = True
            if eventDict["action"] in [pysvn.wc_notify_action.add,
                                       pysvn.wc_notify_action.commit_added,
                                       pysvn.wc_notify_action.commit_deleted,
                                       pysvn.wc_notify_action.delete,
                                       pysvn.wc_notify_action.update_add,
                                       pysvn.wc_notify_action.update_delete]:
                self.__hasAddOrDelete = True
        if msg:
            self.showMessage(msg)
        
    def showMessage(self, msg):
        """
        Public slot to show a message.
        
        @param msg message to show (string)
        """
        self.resultbox.insertPlainText(msg)
        self.resultbox.ensureCursorVisible()
        QApplication.processEvents()
        
    def showError(self, msg):
        """
        Public slot to show an error message.
        
        @param msg error message to show (string)
        """
        self.errorGroup.show()
        self.errors.insertPlainText(msg)
        self.errors.ensureCursorVisible()
        QApplication.processEvents()
        
    def finish(self):
        """
        Public slot called when the process finished or the user pressed the
        button.
        """
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self._cancel()
        
        if Preferences.getVCS("AutoClose"):
            self.accept()
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.finish()
        
    def hasAddOrDelete(self):
        """
        Public method to check, if the last action contained an add or delete.
        
        @return flag indicating the presence of an add or delete (boolean)
        """
        return self.__hasAddOrDelete
