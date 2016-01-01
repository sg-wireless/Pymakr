# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the feature permission manager object.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWebKitWidgets import QWebPage

import Globals
import Preferences


class FeaturePermissionManager(QObject):
    """
    Class implementing the feature permission manager object.
    """
    SettingsKeyFormat = "Help/FeaturePermissions/{0}"
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object
        @type QObject
        """
        super(FeaturePermissionManager, self).__init__(parent)
        
        self.__featurePermissions = {
            QWebPage.Notifications: {
                QWebPage.PermissionGrantedByUser: [],
                QWebPage.PermissionDeniedByUser: [],
            },
            QWebPage.Geolocation: {
                QWebPage.PermissionGrantedByUser: [],
                QWebPage.PermissionDeniedByUser: [],
            },
        }
        self.__featurePermissionsKeys = {
            (QWebPage.Notifications, QWebPage.PermissionGrantedByUser):
                "NotificationsGranted",
            (QWebPage.Notifications, QWebPage.PermissionDeniedByUser):
                "NotificationsDenied",
            (QWebPage.Geolocation, QWebPage.PermissionGrantedByUser):
                "GeolocationGranted",
            (QWebPage.Geolocation, QWebPage.PermissionDeniedByUser):
                "GeolocationDenied",
        }
        
        self.__loaded = False

    def requestFeaturePermission(self, page, frame, feature):
        """
        Public method to request a feature permission.
        
        @param page reference to the requesting web page
        @type QWebPage
        @param frame frame sending the request
        @type QWebFrame
        @param feature requested feature
        @type QWebPage.Feature
        """
        if page is None or frame is None:
            return
        
        if not self.__loaded:
            self.__loadSettings()
        
        host = page.url().host()
        
        if feature in self.__featurePermissions:
            for permission in self.__featurePermissions[feature]:
                if host in self.__featurePermissions[feature][permission]:
                    page.setFeaturePermission(frame, feature, permission)
                    return
        
        view = page.view()
        if view is not None:
            from .FeaturePermissionBar import FeaturePermissionBar
            bar = FeaturePermissionBar(view, frame, feature)
            bar.show()
    
    def rememberFeaturePermission(self, host, feature, permission):
        """
        Public method to remember a user decision for a feature permission.
        
        @param host host name to remember the decision for
        @type str
        @param feature feature to be remembered
        @type QWebPage.Feature
        @param permission feature permission to be remembered
        @type QWebPage.PermissionPolicy
        """
        if feature in self.__featurePermissions:
            if host not in self.__featurePermissions[feature][permission]:
                self.__featurePermissions[feature][permission].append(host)
                self.__saveSettings()
    
    def __loadSettings(self):
        """
        Private method to load the remembered feature permissions.
        """
        if self.__loaded:
            # no reloading allowed
            return
        
        for (feature, permission), key in \
                self.__featurePermissionsKeys.items():
            self.__featurePermissions[feature][permission] = \
                Globals.toList(Preferences.Prefs.settings.value(
                    FeaturePermissionManager.SettingsKeyFormat.format(key),
                    []
                ))
        
        self.__loaded = True
    
    def __saveSettings(self):
        """
        Private method to save the remembered feature permissions.
        """
        if not self.__loaded:
            return
        
        for (feature, permission), key in \
                self.__featurePermissionsKeys.items():
            Preferences.Prefs.settings.setValue(
                FeaturePermissionManager.SettingsKeyFormat.format(key),
                self.__featurePermissions[feature][permission])
    
    def showFeaturePermissionsDialog(self):
        """
        Public method to show a dialog to manage the remembered feature
        permissions.
        """
        if not self.__loaded:
            self.__loadSettings()
        
        from .FeaturePermissionsDialog import FeaturePermissionsDialog
        dlg = FeaturePermissionsDialog(self.__featurePermissions)
        if dlg.exec_() == QDialog.Accepted:
            newFeaturePermissions = dlg.getData()
            self.__featurePermissions = newFeaturePermissions
            self.__saveSettings()
