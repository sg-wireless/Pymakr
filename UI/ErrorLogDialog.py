# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to display an error log.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QDialog, QStyle

from .Ui_ErrorLogDialog import Ui_ErrorLogDialog


class ErrorLogDialog(QDialog, Ui_ErrorLogDialog):
    """
    Class implementing a dialog to display an error log.
    """
    def __init__(self, logFile, showMode, parent=None):
        """
        Constructor
        
        @param logFile name of the log file containing the error info (string)
        @param showMode flag indicating to just show the error log message
            (boolean)
        @param parent reference to the parent widget (QWidget)
        """
        super(ErrorLogDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        pixmap = self.style().standardIcon(QStyle.SP_MessageBoxQuestion)\
            .pixmap(32, 32)
        self.icon.setPixmap(pixmap)
        
        if showMode:
            self.icon.hide()
            self.label.hide()
            self.deleteButton.setText(self.tr("Delete"))
            self.keepButton.setText(self.tr("Close"))
            self.setWindowTitle(self.tr("Error Log"))
        
        self.__ui = parent
        self.__logFile = logFile
        
        try:
            f = open(logFile, "r", encoding="utf-8")
            txt = f.read()
            f.close()
            self.logEdit.setPlainText(txt)
        except IOError:
            pass
    
    @pyqtSlot()
    def on_emailButton_clicked(self):
        """
        Private slot to send an email.
        """
        self.accept()
        self.__ui.showEmailDialog(
            "bug", attachFile=self.__logFile, deleteAttachFile=True)
    
    @pyqtSlot()
    def on_deleteButton_clicked(self):
        """
        Private slot to delete the log file.
        """
        if os.path.exists(self.__logFile):
            os.remove(self.__logFile)
        self.accept()
    
    @pyqtSlot()
    def on_keepButton_clicked(self):
        """
        Private slot to just do nothing.
        """
        self.accept()
