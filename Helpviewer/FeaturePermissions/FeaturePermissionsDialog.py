# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the feature permission dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QDialog, QTreeWidgetItem
from PyQt5.QtWebKitWidgets import QWebPage

from .Ui_FeaturePermissionsDialog import Ui_FeaturePermissionsDialog


class FeaturePermissionsDialog(QDialog, Ui_FeaturePermissionsDialog):
    """
    Class implementing the feature permission dialog.
    """
    def __init__(self, featurePermissions, parent=None):
        """
        Constructor
        
        @param featurePermissions dictionary with remembered feature
            permissions
        @type dict of dict of list
        @param parent reference to the parent widget
        @type QWidget
        """
        super(FeaturePermissionsDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__permissionStrings = {
            QWebPage.PermissionGrantedByUser: self.tr("Allow"),
            QWebPage.PermissionDeniedByUser: self.tr("Deny"),
        }
        
        # Notifications
        for permission in featurePermissions[QWebPage.Notifications]:
            for host in featurePermissions[QWebPage.Notifications][permission]:
                itm = QTreeWidgetItem(
                    self.notifList,
                    [host, self.__permissionStrings[permission]])
                itm.setData(0, Qt.UserRole, permission)
        self.__updateNotifButtons()
        
        # Geolocation
        for permission in featurePermissions[QWebPage.Geolocation]:
            for host in featurePermissions[QWebPage.Geolocation][permission]:
                itm = QTreeWidgetItem(
                    self.geoList,
                    [host, self.__permissionStrings[permission]])
                itm.setData(0, Qt.UserRole, permission)
        self.__updateGeoButtons()
    
    def __updateNotifButtons(self):
        """
        Private method to update the notifications buttons.
        """
        self.notifRemoveAllButton.setEnabled(
            self.notifList.topLevelItemCount() > 0)
        self.notifRemoveButton.setEnabled(
            len(self.notifList.selectedItems()) > 0)
    
    def __updateGeoButtons(self):
        """
        Private method to update the geolocation buttons.
        """
        self.geoRemoveAllButton.setEnabled(
            self.geoList.topLevelItemCount() > 0)
        self.geoRemoveButton.setEnabled(
            len(self.geoList.selectedItems()) > 0)
    
    @pyqtSlot()
    def on_geoList_itemSelectionChanged(self):
        """
        Private slot handling changes in the list of selected geolocation
        items.
        """
        self.__updateGeoButtons()
    
    @pyqtSlot()
    def on_geoRemoveButton_clicked(self):
        """
        Private slot to remove selected geolocation entries.
        """
        for itm in self.geoList.selectedItems():
            row = self.geoList.indexOfTopLevelItem(itm)
            itm = self.geoList.takeTopLevelItem(row)
            del itm
        self.__updateGeoButtons()
    
    @pyqtSlot()
    def on_geoRemoveAllButton_clicked(self):
        """
        Private slot to remove all geolocation entries.
        """
        while self.geoList.topLevelItemCount() > 0:
            itm = self.geoList.takeTopLevelItem(0)
            del itm
        self.__updateGeoButtons()
    
    @pyqtSlot()
    def on_notifList_itemSelectionChanged(self):
        """
        Private slot handling changes in the list of selected notifications
        items.
        """
        self.__updateNotifButtons()
    
    @pyqtSlot()
    def on_notifRemoveButton_clicked(self):
        """
        Private slot to remove selected notification entries.
        """
        for itm in self.notifList.selectedItems():
            row = self.notifList.indexOfTopLevelItem(itm)
            itm = self.notifList.takeTopLevelItem(row)
            del itm
        self.__updateNotifButtons()
    
    @pyqtSlot()
    def on_notifRemoveAllButton_clicked(self):
        """
        Private slot to remove all notification entries.
        """
        while self.notifList.topLevelItemCount() > 0:
            itm = self.notifList.takeTopLevelItem(0)
            del itm
        self.__updateNotifButtons()
    
    def getData(self):
        """
        Public method to retrieve the dialog contents.
        
        @return new feature permission settings
        @rtype dict of dict of list
        """
        featurePermissions = {
            QWebPage.Notifications: {
                QWebPage.PermissionGrantedByUser: [],
                QWebPage.PermissionDeniedByUser: [],
            },
            QWebPage.Geolocation: {
                QWebPage.PermissionGrantedByUser: [],
                QWebPage.PermissionDeniedByUser: [],
            },
        }
        
        # Notifications
        for row in range(self.notifList.topLevelItemCount()):
            itm = self.notifList.topLevelItem(row)
            host = itm.text(0)
            permission = itm.data(0, Qt.UserRole)
            featurePermissions[QWebPage.Notifications][permission].append(host)
        
        # Geolocation
        for row in range(self.geoList.topLevelItemCount()):
            itm = self.geoList.topLevelItem(row)
            host = itm.text(0)
            permission = itm.data(0, Qt.UserRole)
            featurePermissions[QWebPage.Geolocation][permission].append(host)
        
        return featurePermissions
