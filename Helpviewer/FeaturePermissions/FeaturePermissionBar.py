# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the feature permission bar widget.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QLabel, QHBoxLayout, QPushButton
from PyQt5.QtWebKitWidgets import QWebPage

from E5Gui.E5AnimatedWidget import E5AnimatedWidget

import Helpviewer

import UI.PixmapCache


class FeaturePermissionBar(E5AnimatedWidget):
    """
    Class implementing the feature permission bar widget.
    """
    DefaultHeight = 30
    
    def __init__(self, view, frame, feature):
        """
        Constructor
        
        @param view reference to the web view
        @type QWebView
        @param frame frame sending the request
        @type QWebFrame
        @param feature requested feature
        @type QWebPage.Feature
        """
        super(FeaturePermissionBar, self).__init__(parent=view)
        
        self.__frame = frame
        self.__feature = feature
        self.__view = view
        
        self.__permissionFeatureTexts = {
            QWebPage.Notifications:
                self.tr("{0} wants to use desktop notifications."),
            QWebPage.Geolocation:
                self.tr("{0} wants to use your position.")
        }
        self.__permissionFeatureIconNames = {
            QWebPage.Notifications: "notification.png",
            QWebPage.Geolocation: "geolocation.png",
        }
        
        self.setAutoFillBackground(True)
        self.__layout = QHBoxLayout()
        self.setLayout(self.__layout)
        self.__layout.setContentsMargins(9, 0, 0, 0)
        self.__iconLabel = QLabel(self)
        self.__layout.addWidget(self.__iconLabel)
        self.__messageLabel = QLabel(self)
        self.__layout.addWidget(self.__messageLabel)
        self.__layout.addStretch()
        self.__rememberButton = QPushButton(self.tr("Remember"), self)
        self.__rememberButton.setCheckable(True)
        self.__allowButton = QPushButton(self.tr("Allow"), self)
        self.__denyButton = QPushButton(self.tr("Deny"), self)
        self.__discardButton = QPushButton(UI.PixmapCache.getIcon("close.png"),
                                           "", self)
        self.__allowButton.clicked.connect(self.__permissionGranted)
        self.__denyButton.clicked.connect(self.__permissionDenied)
        self.__discardButton.clicked.connect(self.__permissionUnknown)
        self.__layout.addWidget(self.__rememberButton)
        self.__layout.addWidget(self.__allowButton)
        self.__layout.addWidget(self.__denyButton)
        self.__layout.addWidget(self.__discardButton)
        
        try:
            self.__iconLabel.setPixmap(UI.PixmapCache.getPixmap(
                self.__permissionFeatureIconNames[self.__feature]))
        except KeyError:
            pass
        
        try:
            self.__messageLabel.setText(
                self.__permissionFeatureTexts[self.__feature].format(
                    self.__frame.securityOrigin().host()))
        except KeyError:
            self.__messageLabel.setText(
                self.tr("{0} wants to use an unknown feature.").format(
                    self.__frame.securityOrigin().host()))
        
        self.__view.page().loadStarted.connect(self.hide)
        
        self.resize(view.width(), self.height())
        self.startAnimation()
    
    @pyqtSlot()
    def hide(self):
        """
        Public slot to hide the animated widget.
        """
        self.__view.page().loadStarted.disconnect(self.hide)
        super(FeaturePermissionBar, self).hide()
    
    def __permissionDenied(self):
        """
        Private slot handling the user pressing the deny button.
        """
        if self.__frame is None or self.__frame.page() is None:
            return
        
        page = self.__frame.page()
        page.setFeaturePermission(self.__frame, self.__feature,
                                  QWebPage.PermissionDeniedByUser)
        
        if self.__rememberButton.isChecked():
            Helpviewer.HelpWindow.HelpWindow.featurePermissionManager()\
                .rememberFeaturePermission(page.url().host(), self.__feature,
                                           QWebPage.PermissionDeniedByUser)
        
        self.hide()
    
    def __permissionGranted(self):
        """
        Private slot handling the user pressing the allow button.
        """
        if self.__frame is None or self.__frame.page() is None:
            return
        
        page = self.__frame.page()
        page.setFeaturePermission(self.__frame, self.__feature,
                                  QWebPage.PermissionGrantedByUser)
        
        if self.__rememberButton.isChecked():
            Helpviewer.HelpWindow.HelpWindow.featurePermissionManager()\
                .rememberFeaturePermission(page.url().host(), self.__feature,
                                           QWebPage.PermissionGrantedByUser)
        
        self.hide()
    
    def __permissionUnknown(self):
        """
        Private slot handling the user closing the dialog without.
        """
        if self.__frame is None or self.__frame.page() is None:
            return
        
        page = self.__frame.page()
        page.setFeaturePermission(self.__frame, self.__feature,
                                  QWebPage.PermissionUnknown)
        self.hide()
