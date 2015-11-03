# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to send bug reports.
"""

from __future__ import unicode_literals

import os
import mimetypes
import smtplib
import socket

from PyQt5.QtCore import Qt, pyqtSlot, qVersion
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QHeaderView, QLineEdit, QDialog, QInputDialog, \
    QApplication, QDialogButtonBox, QTreeWidgetItem

from E5Gui import E5MessageBox, E5FileDialog

from .Ui_EmailDialog import Ui_EmailDialog

from .Info import BugAddress, FeatureAddress
import Preferences
import Utilities
from base64 import b64encode as _bencode

from email import encoders
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.header import Header


############################################################
## This code is to work around a bug in the Python email  ##
## package for Image and Audio mime messages.             ##
############################################################


def _encode_base64(msg):
    """
    Function to encode the message's payload in Base64.

    Note: It adds an appropriate Content-Transfer-Encoding header.
    
    @param msg reference to the message object (email.Message)
    """
    orig = msg.get_payload()
    encdata = str(_bencode(orig), "ASCII")
    msg.set_payload(encdata)
    msg['Content-Transfer-Encoding'] = 'base64'

encoders.encode_base64 = _encode_base64
# WORK AROUND: implement our corrected encoder


class EmailDialog(QDialog, Ui_EmailDialog):
    """
    Class implementing a dialog to send bug reports.
    """
    def __init__(self, mode="bug", parent=None):
        """
        Constructor
        
        @param mode mode of this dialog (string, "bug" or "feature")
        @param parent parent widget of this dialog (QWidget)
        """
        super(EmailDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.__mode = mode
        if self.__mode == "feature":
            self.setWindowTitle(self.tr("Send feature request"))
            self.msgLabel.setText(self.tr(
                "Enter your &feature request below."
                " Version information is added automatically."))
            self.__toAddress = FeatureAddress
        else:
            # default is bug
            self.msgLabel.setText(self.tr(
                "Enter your &bug description below."
                " Version information is added automatically."))
            self.__toAddress = BugAddress
        
        self.sendButton = self.buttonBox.addButton(
            self.tr("Send"), QDialogButtonBox.ActionRole)
        self.sendButton.setEnabled(False)
        self.sendButton.setDefault(True)
        
        height = self.height()
        self.mainSplitter.setSizes([int(0.7 * height), int(0.3 * height)])
        
        self.attachments.headerItem().setText(
            self.attachments.columnCount(), "")
        if qVersion() >= "5.0.0":
            self.attachments.header().setSectionResizeMode(
                QHeaderView.Interactive)
        else:
            self.attachments.header().setResizeMode(QHeaderView.Interactive)
        
        sig = Preferences.getUser("Signature")
        if sig:
            self.message.setPlainText(sig)
            cursor = self.message.textCursor()
            cursor.setPosition(0)
            self.message.setTextCursor(cursor)
            self.message.ensureCursorVisible()
        
        self.__deleteFiles = []
        
    def keyPressEvent(self, ev):
        """
        Protected method to handle the user pressing the escape key.
        
        @param ev key event (QKeyEvent)
        """
        if ev.key() == Qt.Key_Escape:
            res = E5MessageBox.yesNo(
                self,
                self.tr("Close dialog"),
                self.tr("""Do you really want to close the dialog?"""))
            if res:
                self.reject()
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.sendButton:
            self.on_sendButton_clicked()
        
    def on_buttonBox_rejected(self):
        """
        Private slot to handle the rejected signal of the button box.
        """
        res = E5MessageBox.yesNo(
            self,
            self.tr("Close dialog"),
            self.tr("""Do you really want to close the dialog?"""))
        if res:
            self.reject()
        
    @pyqtSlot()
    def on_sendButton_clicked(self):
        """
        Private slot to send the email message.
        """
        if self.attachments.topLevelItemCount():
            msg = self.__createMultipartMail()
        else:
            msg = self.__createSimpleMail()
            
        ok = self.__sendmail(msg)
        
        if ok:
            for f in self.__deleteFiles:
                try:
                    os.remove(f)
                except OSError:
                    pass
            self.accept()
        
    def __encodedText(self, txt):
        """
        Private method to create a MIMEText message with correct encoding.
        
        @param txt text to be put into the MIMEText object (string)
        @return MIMEText object
        """
        try:
            txt.encode("us-ascii")
            return MIMEText(txt)
        except UnicodeEncodeError:
            coding = Preferences.getSystem("StringEncoding")
            return MIMEText(txt.encode(coding), _charset=coding)
        
    def __encodedHeader(self, txt):
        """
        Private method to create a correctly encoded mail header.
        
        @param txt header text to encode (string)
        @return encoded header (email.header.Header)
        """
        try:
            txt.encode("us-ascii")
            return Header(txt)
        except UnicodeEncodeError:
            coding = Preferences.getSystem("StringEncoding")
            return Header(txt, coding)
        
    def __createSimpleMail(self):
        """
        Private method to create a simple mail message.
        
        @return string containing the mail message
        """
        msgtext = "{0}\r\n----\r\n{1}----\r\n{2}----\r\n{3}".format(
            self.message.toPlainText(),
            Utilities.generateVersionInfo("\r\n"),
            Utilities.generatePluginsVersionInfo("\r\n"),
            Utilities.generateDistroInfo("\r\n"))
        
        msg = self.__encodedText(msgtext)
        msg['From'] = Preferences.getUser("Email")
        msg['To'] = self.__toAddress
        subject = '[eric6] {0}'.format(self.subject.text())
        msg['Subject'] = self.__encodedHeader(subject)
        
        return msg.as_string()
        
    def __createMultipartMail(self):
        """
        Private method to create a multipart mail message.
        
        @return string containing the mail message
        """
        mpPreamble = ("This is a MIME-encoded message with attachments. "
                      "If you see this message, your mail client is not "
                      "capable of displaying the attachments.")
        
        msgtext = "{0}\r\n----\r\n{1}----\r\n{2}----\r\n{3}".format(
            self.message.toPlainText(),
            Utilities.generateVersionInfo("\r\n"),
            Utilities.generatePluginsVersionInfo("\r\n"),
            Utilities.generateDistroInfo("\r\n"))
        
        # first part of multipart mail explains format
        msg = MIMEMultipart()
        msg['From'] = Preferences.getUser("Email")
        msg['To'] = self.__toAddress
        subject = '[eric6] {0}'.format(self.subject.text())
        msg['Subject'] = self.__encodedHeader(subject)
        msg.preamble = mpPreamble
        msg.epilogue = ''
        
        # second part is intended to be read
        att = self.__encodedText(msgtext)
        msg.attach(att)
        
        # next parts contain the attachments
        for index in range(self.attachments.topLevelItemCount()):
            itm = self.attachments.topLevelItem(index)
            maintype, subtype = itm.text(1).split('/', 1)
            fname = itm.text(0)
            name = os.path.basename(fname)
            
            if maintype == 'text':
                txt = open(fname, 'r', encoding="utf-8").read()
                try:
                    txt.encode("us-ascii")
                    att = MIMEText(txt, _subtype=subtype)
                except UnicodeEncodeError:
                    att = MIMEText(
                        txt.encode("utf-8"), _subtype=subtype,
                        _charset="utf-8")
            elif maintype == 'image':
                att = MIMEImage(open(fname, 'rb').read(), _subtype=subtype)
            elif maintype == 'audio':
                att = MIMEAudio(open(fname, 'rb').read(), _subtype=subtype)
            else:
                att = MIMEApplication(open(fname, 'rb').read())
            att.add_header('Content-Disposition', 'attachment', filename=name)
            msg.attach(att)
            
        return msg.as_string()

    def __sendmail(self, msg):
        """
        Private method to actually send the message.
        
        @param msg the message to be sent (string)
        @return flag indicating success (boolean)
        """
        try:
            server = smtplib.SMTP(Preferences.getUser("MailServer"),
                                  Preferences.getUser("MailServerPort"))
            if Preferences.getUser("MailServerUseTLS"):
                server.starttls()
            if Preferences.getUser("MailServerAuthentication"):
                # mail server needs authentication
                password = Preferences.getUser("MailServerPassword")
                if not password:
                    password, ok = QInputDialog.getText(
                        self,
                        self.tr("Mail Server Password"),
                        self.tr("Enter your mail server password"),
                        QLineEdit.Password)
                    if not ok:
                        # abort
                        return False
                try:
                    server.login(Preferences.getUser("MailServerUser"),
                                 password)
                except (smtplib.SMTPException, socket.error) as e:
                    if isinstance(e, smtplib.SMTPResponseException):
                        errorStr = e.smtp_error.decode()
                    elif isinstance(e, socket.error):
                        errorStr = e[1]
                    else:
                        errorStr = str(e)
                    res = E5MessageBox.retryAbort(
                        self,
                        self.tr("Send bug report"),
                        self.tr(
                            """<p>Authentication failed.<br>Reason: {0}</p>""")
                        .format(errorStr),
                        E5MessageBox.Critical)
                    if res:
                        return self.__sendmail(msg)
                    else:
                        return False

            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            QApplication.processEvents()
            server.sendmail(Preferences.getUser("Email"), self.__toAddress,
                            msg)
            server.quit()
            QApplication.restoreOverrideCursor()
        except (smtplib.SMTPException, socket.error) as e:
            QApplication.restoreOverrideCursor()
            if isinstance(e, smtplib.SMTPResponseException):
                errorStr = e.smtp_error.decode()
            elif isinstance(e, socket.error):
                errorStr = e[1]
            else:
                errorStr = str(e)
            res = E5MessageBox.retryAbort(
                self,
                self.tr("Send bug report"),
                self.tr(
                    """<p>Message could not be sent.<br>Reason: {0}</p>""")
                .format(errorStr),
                E5MessageBox.Critical)
            if res:
                return self.__sendmail(msg)
            else:
                return False
        return True
        
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to handle the Add... button.
        """
        fname = E5FileDialog.getOpenFileName(
            self,
            self.tr("Attach file"))
        if fname:
            self.attachFile(fname, False)
        
    def attachFile(self, fname, deleteFile):
        """
        Public method to add an attachment.
        
        @param fname name of the file to be attached (string)
        @param deleteFile flag indicating to delete the file after it has
            been sent (boolean)
        """
        type = mimetypes.guess_type(fname)[0]
        if not type:
            type = "application/octet-stream"
        QTreeWidgetItem(self.attachments, [fname, type])
        self.attachments.header().resizeSections(QHeaderView.ResizeToContents)
        self.attachments.header().setStretchLastSection(True)
        
        if deleteFile:
            self.__deleteFiles.append(fname)
        
    @pyqtSlot()
    def on_deleteButton_clicked(self):
        """
        Private slot to handle the Delete button.
        """
        itm = self.attachments.currentItem()
        if itm is not None:
            itm = self.attachments.takeTopLevelItem(
                self.attachments.indexOfTopLevelItem(itm))
            del itm
        
    def on_subject_textChanged(self, txt):
        """
        Private slot to handle the textChanged signal of the subject edit.
        
        @param txt changed text (string)
        """
        self.sendButton.setEnabled(
            self.subject.text() != "" and
            self.message.toPlainText() != "")
        
    def on_message_textChanged(self):
        """
        Private slot to handle the textChanged signal of the message edit.
        """
        self.sendButton.setEnabled(
            self.subject.text() != "" and
            self.message.toPlainText() != "")
