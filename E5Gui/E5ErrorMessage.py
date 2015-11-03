# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a specialized error message dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import qInstallMessageHandler, QCoreApplication, \
    QtDebugMsg, QtWarningMsg, QtCriticalMsg, QtFatalMsg, QThread, \
    QMetaObject, Qt, Q_ARG, QSettings
from PyQt5.QtWidgets import QErrorMessage, qApp, QDialog

import Globals
import Utilities


__msgHandlerDialog = None
__origMsgHandler = None


class E5ErrorMessage(QErrorMessage):
    """
    Class implementing a specialized error message dialog.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(E5ErrorMessage, self).__init__(parent)
        
        self.settings = QSettings(
            QSettings.IniFormat,
            QSettings.UserScope,
            Globals.settingsNameOrganization,
            "eric6messagefilters")
        
        self.__defaultFilters = [
            "QFont::",
            "QCocoaMenu::removeMenuItem",
            "QCocoaMenu::insertNative",
            ",type id:"
        ]
    
    def __filterMessage(self, message):
        """
        Private method to filter messages.
        
        @param message message to be checked (string)
        @return flag indicating that the message should be filtered out
            (boolean)
        """
        for filter in Globals.toList(self.settings.value(
                "MessageFilters", self.__defaultFilters)):
            if filter in message:
                return True
        
        return False
    
    def showMessage(self, message, msgType=""):
        """
        Public method to show a message.
        
        @param message error message to be shown (string)
        @param msgType type of the error message (string)
        """
        if not self.__filterMessage(message):
            if msgType:
                super(E5ErrorMessage, self).showMessage(message, msgType)
            else:
                super(E5ErrorMessage, self).showMessage(message)
    
    def editMessageFilters(self):
        """
        Public method to edit the list of message filters.
        """
        from .E5ErrorMessageFilterDialog import E5ErrorMessageFilterDialog
        dlg = E5ErrorMessageFilterDialog(
            self.settings.value("MessageFilters", self.__defaultFilters))
        if dlg.exec_() == QDialog.Accepted:
            filters = dlg.getFilters()
            self.settings.setValue("MessageFilters", filters)


def messageHandler(msgType, *args):
    """
    Module function handling messages.
    
    @param msgType type of the message (integer, QtMsgType)
    @param args message handler arguments, for PyQt4 message to be shown
        (bytes), for PyQt5 context information (QMessageLogContext) and
        message to be shown (bytes)
    """
    if len(args) == 2:
        context = args[0]
        message = args[1]
    else:
        message = args[0]
    if __msgHandlerDialog:
        try:
            if msgType == QtDebugMsg:
                messageType = QCoreApplication.translate(
                    "E5ErrorMessage", "Debug Message:")
            elif msgType == QtWarningMsg:
                messageType = QCoreApplication.translate(
                    "E5ErrorMessage", "Warning:")
            elif msgType == QtCriticalMsg:
                messageType = QCoreApplication.translate(
                    "E5ErrorMessage", "Critical:")
            elif msgType == QtFatalMsg:
                messageType = QCoreApplication.translate(
                    "E5ErrorMessage", "Fatal Error:")
            if isinstance(message, bytes):
                message = Utilities.decodeBytes(message)
            message = message.replace("\r\n", "<br/>")\
                             .replace("\n", "<br/>")\
                             .replace("\r", "<br/>")
            if len(args) == 2:
                msg = "<p><b>{0}</b></p><p>{1}</p><p>File: {2}</p>" \
                    "<p>Line: {3}</p><p>Function: {4}</p>".format(
                        messageType, Utilities.html_uencode(message),
                        context.file, context.line, context.function)
            else:
                msg = "<p><b>{0}</b></p><p>{1}</p>".format(
                    messageType, Utilities.html_uencode(message))
            if QThread.currentThread() == qApp.thread():
                __msgHandlerDialog.showMessage(msg)
            else:
                QMetaObject.invokeMethod(
                    __msgHandlerDialog,
                    "showMessage",
                    Qt.QueuedConnection,
                    Q_ARG(str, msg))
            return
        except RuntimeError:
            pass
    elif __origMsgHandler:
        __origMsgHandler(msgType, message)
        return
    
    if msgType == QtDebugMsg:
        messageType = QCoreApplication.translate(
            "E5ErrorMessage", "Debug Message")
    elif msgType == QtWarningMsg:
        messageType = QCoreApplication.translate(
            "E5ErrorMessage", "Warning")
    elif msgType == QtCriticalMsg:
        messageType = QCoreApplication.translate(
            "E5ErrorMessage", "Critical")
    elif msgType == QtFatalMsg:
        messageType = QCoreApplication.translate(
            "E5ErrorMessage", "Fatal Error")
    if isinstance(message, bytes):
        message = message.decode()
    if len(args) == 2:
        print("{0}: {1} in {2} at line {3} ({4})".format(
            messageType, message, context.file, context.line,
            context.function))
    else:
        print("{0}: {1}".format(messageType, message))


def qtHandler():
    """
    Module function to install an E5ErrorMessage dialog as the global
    message handler.
    
    @return reference to the message handler dialog (E5ErrorMessage)
    """
    global __msgHandlerDialog, __origMsgHandler
    
    if __msgHandlerDialog is None:
        # Install an E5ErrorMessage dialog as the global message handler.
        __msgHandlerDialog = E5ErrorMessage()
        __origMsgHandler = qInstallMessageHandler(messageHandler)
    
    return __msgHandlerDialog


def editMessageFilters():
    """
    Module function to edit the list of message filters.
    """
    if __msgHandlerDialog:
        __msgHandlerDialog.editMessageFilters()
    else:
        print(QCoreApplication.translate(
            "E5ErrorMessage", "No message handler installed."))


def messageHandlerInstalled():
    """
    Module function to check, if a message handler was installed.
    
    @return flag indicating an installed message handler (boolean)
    """
    return __msgHandlerDialog is not None
