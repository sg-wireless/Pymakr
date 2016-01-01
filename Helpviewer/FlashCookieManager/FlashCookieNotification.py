# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the feature permission bar widget.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QLabel, QHBoxLayout, QPushButton

from E5Gui.E5AnimatedWidget import E5AnimatedWidget

import UI.PixmapCache


class FlashCookieNotification(E5AnimatedWidget):
    """
    Class implementing the feature permission bar widget.
    """
    DefaultHeight = 30
    
    def __init__(self, view, manager, noCookies):
        """
        Constructor
        
        @param view reference to the web view
        @type QWebView
        @param manager reference to the Flash cookie manager object
        @type FlashCookieManager
        @param noCookies number of newly detected Flash cookies
        @type int
        """
        super(FlashCookieNotification, self).__init__(parent=view)
        
        self.__manager = manager
        
        if noCookies == 1:
            msg = self.tr("A new flash cookie was detected.")
        else:
            msg = self.tr("{0} new flash cookies were detected.")\
                .format(noCookies)
        self.setAutoFillBackground(True)
        self.__layout = QHBoxLayout()
        self.setLayout(self.__layout)
        self.__layout.setContentsMargins(9, 0, 0, 0)
        self.__iconLabel = QLabel(self)
        self.__iconLabel.setPixmap(UI.PixmapCache.getPixmap("flashCookie.png"))
        self.__layout.addWidget(self.__iconLabel)
        self.__messageLabel = QLabel(msg, self)
        self.__layout.addWidget(self.__messageLabel)
        self.__viewButton = QPushButton(self.tr("View"), self)
        self.__layout.addWidget(self.__viewButton)
        self.__layout.addStretch()
        self.__discardButton = QPushButton(UI.PixmapCache.getIcon("close.png"),
                                           "", self)
        self.__layout.addWidget(self.__discardButton)
        
        self.__viewButton.clicked.connect(manager.showFlashCookieManagerDialog)
        self.__viewButton.clicked.connect(self.hide)
        self.__discardButton.clicked.connect(self.hide)
        
        self.resize(view.width(), self.height())
        self.startAnimation()
