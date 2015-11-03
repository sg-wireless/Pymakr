# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to manage the ClickToFlash whitelist.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, Qt, QSortFilterProxyModel, QStringListModel
from PyQt5.QtWidgets import QDialog, QInputDialog, QLineEdit

from .Ui_ClickToFlashWhitelistDialog import Ui_ClickToFlashWhitelistDialog

import UI.PixmapCache


class ClickToFlashWhitelistDialog(QDialog, Ui_ClickToFlashWhitelistDialog):
    """
    Class implementing a dialog to manage the ClickToFlash whitelist.
    """
    def __init__(self, whitelist, parent=None):
        """
        Constructor
        
        @param whitelist list of whitelisted hosts (list of string)
        @param parent reference to the parent widget (QWidget)
        """
        super(ClickToFlashWhitelistDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.iconLabel.setPixmap(UI.PixmapCache.getPixmap("flashBlock48.png"))
        
        self.__model = QStringListModel(whitelist[:], self)
        self.__model.sort(0)
        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.__proxyModel.setSourceModel(self.__model)
        self.whitelist.setModel(self.__proxyModel)
        
        self.searchEdit.textChanged.connect(
            self.__proxyModel.setFilterFixedString)
        
        self.removeButton.clicked.connect(self.whitelist.removeSelected)
        self.removeAllButton.clicked.connect(self.whitelist.removeAll)
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add an entry to the whitelist.
        """
        host, ok = QInputDialog.getText(
            self,
            self.tr("ClickToFlash Whitelist"),
            self.tr("Enter host name to add to whitelist:"),
            QLineEdit.Normal)
        if ok and host != "" and host not in self.__model.stringList():
            self.__model.insertRow(self.__model.rowCount())
            self.__model.setData(
                self.__model.index(self.__model.rowCount() - 1), host)
            self.__model.sort(0)
    
    def getWhitelist(self):
        """
        Public method to get the whitelisted hosts.
        
        @return list of whitelisted hosts (list of string)
        """
        return self.__model.stringList()
