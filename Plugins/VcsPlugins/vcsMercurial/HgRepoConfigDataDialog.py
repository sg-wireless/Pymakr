# -*- coding: utf-8 -*-

"""
Module implementing a dialog to enter data needed for the initial creation
of a repository configuration file (hgrc).
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, QUrl
from PyQt5.QtWidgets import QDialog, QLineEdit

from .Ui_HgRepoConfigDataDialog import Ui_HgRepoConfigDataDialog

import UI.PixmapCache

from .LargefilesExtension import getDefaults as getLargefilesDefaults


class HgRepoConfigDataDialog(QDialog, Ui_HgRepoConfigDataDialog):
    """
    Class implementing a dialog to enter data needed for the initial creation
    of a repository configuration file (hgrc).
    """
    def __init__(self, withLargefiles=False, largefilesData=None, parent=None):
        """
        Constructor
        
        @param withLargefiles flag indicating to configure the largefiles
            section (boolean)
        @param largefilesData dictionary with data for the largefiles
            section (dict)
        @param parent reference to the parent widget (QWidget)
        """
        super(HgRepoConfigDataDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.defaultShowPasswordButton.setIcon(
            UI.PixmapCache.getIcon("showPassword.png"))
        self.defaultPushShowPasswordButton.setIcon(
            UI.PixmapCache.getIcon("showPassword.png"))
        
        self.__withLargefiles = withLargefiles
        if withLargefiles:
            if largefilesData is None:
                largefilesData = getLargefilesDefaults()
            self.lfFileSizeSpinBox.setValue(largefilesData["minsize"])
            self.lfFilePatternsEdit.setText(
                " ".join(largefilesData["pattern"]))
        else:
            self.largefilesGroup.setVisible(False)
        
        self.resize(self.width(), self.minimumSizeHint().height())
    
    @pyqtSlot(bool)
    def on_defaultShowPasswordButton_clicked(self, checked):
        """
        Private slot to switch the default password visibility
        of the default password.
        
        @param checked state of the push button (boolean)
        """
        if checked:
            self.defaultPasswordEdit.setEchoMode(QLineEdit.Normal)
        else:
            self.defaultPasswordEdit.setEchoMode(QLineEdit.Password)
    
    @pyqtSlot(bool)
    def on_defaultPushShowPasswordButton_clicked(self, checked):
        """
        Private slot to switch the default password visibility
        of the default push password.
        
        @param checked state of the push button (boolean)
        """
        if checked:
            self.defaultPushPasswordEdit.setEchoMode(QLineEdit.Normal)
        else:
            self.defaultPushPasswordEdit.setEchoMode(QLineEdit.Password)
    
    def getData(self):
        """
        Public method to get the data entered into the dialog.
        
        @return tuple giving the default and default push URLs (tuple of
            two strings)
        """
        defaultUrl = QUrl.fromUserInput(self.defaultUrlEdit.text())
        username = self.defaultUserEdit.text()
        password = self.defaultPasswordEdit.text()
        if username:
            defaultUrl.setUserName(username)
        if password:
            defaultUrl.setPassword(password)
        if not defaultUrl.isValid():
            defaultUrl = ""
        else:
            defaultUrl = defaultUrl.toString()
        
        defaultPushUrl = QUrl.fromUserInput(self.defaultPushUrlEdit.text())
        username = self.defaultPushUserEdit.text()
        password = self.defaultPushPasswordEdit.text()
        if username:
            defaultPushUrl.setUserName(username)
        if password:
            defaultPushUrl.setPassword(password)
        if not defaultPushUrl.isValid():
            defaultPushUrl = ""
        else:
            defaultPushUrl = defaultPushUrl.toString()
        
        return defaultUrl, defaultPushUrl
    
    def getLargefilesData(self):
        """
        Public method to get the data for the largefiles extension.
        
        @return tuple with the minimum file size (integer) and file patterns
            (list of string). None as value denote to use the default value.
        """
        if self.__withLargefiles:
            lfDefaults = getLargefilesDefaults()
            if self.lfFileSizeSpinBox.value() == lfDefaults["minsize"]:
                minsize = None
            else:
                minsize = self.lfFileSizeSpinBox.value()
            patterns = self.lfFilePatternsEdit.text().split()
            if set(patterns) == set(lfDefaults["pattern"]):
                patterns = None
            
            return minsize, patterns
        else:
            return None, None
