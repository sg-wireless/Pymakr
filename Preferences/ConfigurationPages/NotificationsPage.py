# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Notifications configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, QPoint
from PyQt5.QtWidgets import QApplication

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_NotificationsPage import Ui_NotificationsPage

import Preferences
import UI.PixmapCache


class NotificationsPage(ConfigurationPageBase, Ui_NotificationsPage):
    """
    Class implementing the Notifications configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(NotificationsPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("NotificationsPage")
        
        minX, maxX = self.xSpinBox.maximum(), self.xSpinBox.minimum()
        minY, maxY = self.ySpinBox.maximum(), self.ySpinBox.minimum()
        desk = QApplication.desktop()
        for screen in range(desk.screenCount()):
            geom = desk.availableGeometry(screen)
            minX = min(minX, geom.x())
            maxX = max(maxX, geom.x() + geom.width())
            minY = min(minY, geom.y())
            maxY = max(maxY, geom.y() + geom.height())
        self.xSpinBox.setMinimum(minX)
        self.xSpinBox.setMaximum(maxX)
        self.ySpinBox.setMinimum(minY)
        self.ySpinBox.setMaximum(maxY)
        
        self.__notification = None
        
        # set initial values
        self.enableCheckBox.setChecked(
            Preferences.getUI("NotificationsEnabled"))
        self.timeoutSpinBox.setValue(Preferences.getUI("NotificationTimeout"))
        point = Preferences.getUI("NotificationPosition")
        self.xSpinBox.setValue(point.x())
        self.ySpinBox.setValue(point.y())
    
    def save(self):
        """
        Public slot to save the Notifications configuration.
        """
        Preferences.setUI(
            "NotificationsEnabled", self.enableCheckBox.isChecked())
        Preferences.setUI("NotificationTimeout", self.timeoutSpinBox.value())
        Preferences.setUI("NotificationPosition", QPoint(
            self.xSpinBox.value(), self.ySpinBox.value()))
    
    @pyqtSlot(bool)
    def on_visualButton_clicked(self, checked):
        """
        Private slot to select the position visually.
        
        @param checked state of the button (boolean)
        """
        if checked:
            from UI.NotificationWidget import NotificationWidget
            self.__notification = NotificationWidget(
                parent=self, setPosition=True)
            self.__notification.setPixmap(
                UI.PixmapCache.getPixmap("notification48.png"))
            self.__notification.setHeading(self.tr("Visual Selection"))
            self.__notification.setText(
                self.tr("Drag the notification window to"
                        " the desired place and release the button."))
            self.__notification.move(
                QPoint(self.xSpinBox.value(), self.ySpinBox.value()))
            self.__notification.show()
        else:
            # retrieve the position
            point = self.__notification.frameGeometry().topLeft()
            self.xSpinBox.setValue(point.x())
            self.ySpinBox.setValue(point.y())
            self.__notification.close()
            self.__notification = None
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = NotificationsPage()
    return page
