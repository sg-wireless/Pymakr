# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Email configuration page.
"""

from __future__ import unicode_literals

import smtplib
import socket

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication

from E5Gui import E5MessageBox

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EmailPage import Ui_EmailPage

import Preferences


class EmailPage(ConfigurationPageBase, Ui_EmailPage):
    """
    Class implementing the Email configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(EmailPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("EmailPage")
        
        # set initial values
        self.mailServerEdit.setText(Preferences.getUser("MailServer"))
        self.portSpin.setValue(Preferences.getUser("MailServerPort"))
        self.emailEdit.setText(Preferences.getUser("Email"))
        self.signatureEdit.setPlainText(Preferences.getUser("Signature"))
        self.mailAuthenticationCheckBox.setChecked(
            Preferences.getUser("MailServerAuthentication"))
        self.mailUserEdit.setText(Preferences.getUser("MailServerUser"))
        self.mailPasswordEdit.setText(
            Preferences.getUser("MailServerPassword"))
        self.useTlsCheckBox.setChecked(
            Preferences.getUser("MailServerUseTLS"))
        
    def save(self):
        """
        Public slot to save the Email configuration.
        """
        Preferences.setUser(
            "MailServer",
            self.mailServerEdit.text())
        Preferences.setUser(
            "MailServerPort",
            self.portSpin.value())
        Preferences.setUser(
            "Email",
            self.emailEdit.text())
        Preferences.setUser(
            "Signature",
            self.signatureEdit.toPlainText())
        Preferences.setUser(
            "MailServerAuthentication",
            self.mailAuthenticationCheckBox.isChecked())
        Preferences.setUser(
            "MailServerUser",
            self.mailUserEdit.text())
        Preferences.setUser(
            "MailServerPassword",
            self.mailPasswordEdit.text())
        Preferences.setUser(
            "MailServerUseTLS",
            self.useTlsCheckBox.isChecked())
    
    def __updateTestButton(self):
        """
        Private slot to update the enabled state of the test button.
        """
        self.testButton.setEnabled(
            self.mailAuthenticationCheckBox.isChecked() and
            self.mailUserEdit.text() != "" and
            self.mailPasswordEdit.text() != "" and
            self.mailServerEdit.text() != ""
        )
    
    @pyqtSlot(bool)
    def on_mailAuthenticationCheckBox_toggled(self, checked):
        """
        Private slot to handle a change of the state of the authentication
        selector.
        
        @param checked state of the checkbox (boolean)
        """
        self.__updateTestButton()
    
    @pyqtSlot(str)
    def on_mailUserEdit_textChanged(self, txt):
        """
        Private slot to handle a change of the text of the user edit.
        
        @param txt current text of the edit (string)
        """
        self.__updateTestButton()
    
    @pyqtSlot(str)
    def on_mailPasswordEdit_textChanged(self, txt):
        """
        Private slot to handle a change of the text of the user edit.
        
        @param txt current text of the edit (string)
        """
        self.__updateTestButton()
    
    @pyqtSlot()
    def on_testButton_clicked(self):
        """
        Private slot to test the mail server login data.
        """
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        try:
            server = smtplib.SMTP(self.mailServerEdit.text(),
                                  self.portSpin.value(),
                                  timeout=10)
            if self.useTlsCheckBox.isChecked():
                server.starttls()
            try:
                server.login(self.mailUserEdit.text(),
                             self.mailPasswordEdit.text())
                QApplication.restoreOverrideCursor()
                E5MessageBox.information(
                    self,
                    self.tr("Login Test"),
                    self.tr("""The login test succeeded."""))
            except (smtplib.SMTPException, socket.error) as e:
                QApplication.restoreOverrideCursor()
                if isinstance(e, smtplib.SMTPResponseException):
                    errorStr = e.smtp_error.decode()
                elif isinstance(e, socket.timeout):
                    errorStr = str(e)
                elif isinstance(e, socket.error):
                    try:
                        errorStr = e[1]
                    except TypeError:
                        errorStr = str(e)
                else:
                    errorStr = str(e)
                E5MessageBox.critical(
                    self,
                    self.tr("Login Test"),
                    self.tr(
                        """<p>The login test failed.<br>Reason: {0}</p>""")
                    .format(errorStr))
            server.quit()
        except (smtplib.SMTPException, socket.error) as e:
            QApplication.restoreOverrideCursor()
            if isinstance(e, smtplib.SMTPResponseException):
                errorStr = e.smtp_error.decode()
            elif isinstance(e, socket.timeout):
                errorStr = str(e)
            elif isinstance(e, socket.error):
                try:
                    errorStr = e[1]
                except TypeError:
                    errorStr = str(e)
            else:
                errorStr = str(e)
            E5MessageBox.critical(
                self,
                self.tr("Login Test"),
                self.tr("""<p>The login test failed.<br>Reason: {0}</p>""")
                .format(errorStr))


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = EmailPage()
    return page
