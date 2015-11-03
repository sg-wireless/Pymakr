# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to configure the offline storage.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWebKit import QWebSettings

from .Ui_OfflineStorageConfigDialog import Ui_OfflineStorageConfigDialog

import Preferences


class OfflineStorageConfigDialog(QDialog, Ui_OfflineStorageConfigDialog):
    """
    Class implementing a dialog to configure the offline storage.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(OfflineStorageConfigDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.databaseEnabledCheckBox.setChecked(
            Preferences.getHelp("OfflineStorageDatabaseEnabled"))
        self.databaseQuotaSpinBox.setValue(
            Preferences.getHelp("OfflineStorageDatabaseQuota"))
        
        if hasattr(QWebSettings, "OfflineWebApplicationCacheEnabled"):
            self.applicationCacheEnabledCheckBox.setChecked(
                Preferences.getHelp("OfflineWebApplicationCacheEnabled"))
            self.applicationCacheQuotaSpinBox.setValue(
                Preferences.getHelp("OfflineWebApplicationCacheQuota"))
        else:
            self.applicationCacheGroup.setEnabled(False)
        
        if hasattr(QWebSettings, "LocalStorageEnabled"):
            self.localStorageEnabledCheckBox.setChecked(
                Preferences.getHelp("LocalStorageEnabled"))
        else:
            self.localStorageGroup.setEnabled(False)
        
        if hasattr(QWebSettings, "LocalContentCanAccessRemoteUrls"):
            self.localRemoteUrlsCheckBox.setChecked(
                Preferences.getHelp("LocalContentCanAccessRemoteUrls"))
        else:
            self.localRemoteUrlsCheckBox.setVisible(False)
        
        if hasattr(QWebSettings, "LocalContentCanAccessFileUrls"):
            self.localFileUrlsCheckBox.setChecked(
                Preferences.getHelp("LocalContentCanAccessFileUrls"))
        else:
            self.localFileUrlsCheckBox.setVisible(False)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    def storeData(self):
        """
        Public slot to store the configuration data.
        """
        Preferences.setHelp(
            "OfflineStorageDatabaseEnabled",
            self.databaseEnabledCheckBox.isChecked())
        Preferences.setHelp(
            "OfflineStorageDatabaseQuota",
            self.databaseQuotaSpinBox.value())
        
        if self.applicationCacheGroup.isEnabled():
            Preferences.setHelp(
                "OfflineWebApplicationCacheEnabled",
                self.applicationCacheEnabledCheckBox.isChecked())
            Preferences.setHelp(
                "OfflineWebApplicationCacheQuota",
                self.applicationCacheQuotaSpinBox.value())
        
        if self.localStorageGroup.isEnabled():
            Preferences.setHelp(
                "LocalStorageEnabled",
                self.localStorageEnabledCheckBox.isChecked())
            if self.localRemoteUrlsCheckBox.isVisible():
                Preferences.setHelp(
                    "LocalContentCanAccessRemoteUrls",
                    self.localRemoteUrlsCheckBox.isChecked())
            if self.localFileUrlsCheckBox.isVisible():
                Preferences.setHelp(
                    "LocalContentCanAccessFileUrls",
                    self.localFileUrlsCheckBox.isChecked())
    
    @pyqtSlot()
    def on_showDatabasesButton_clicked(self):
        """
        Private slot to show a dialog with all databases.
        """
        from .WebDatabasesDialog import WebDatabasesDialog
        dlg = WebDatabasesDialog(self)
        dlg.exec_()
