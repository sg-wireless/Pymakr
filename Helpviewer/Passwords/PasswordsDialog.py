# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show all saved logins.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, QSortFilterProxyModel
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import QDialog

from E5Gui import E5MessageBox

from .Ui_PasswordsDialog import Ui_PasswordsDialog


class PasswordsDialog(QDialog, Ui_PasswordsDialog):
    """
    Class implementing a dialog to show all saved logins.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(PasswordsDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__showPasswordsText = self.tr("Show Passwords")
        self.__hidePasswordsText = self.tr("Hide Passwords")
        self.passwordsButton.setText(self.__showPasswordsText)
        
        self.removeButton.clicked.connect(
            self.passwordsTable.removeSelected)
        self.removeAllButton.clicked.connect(self.passwordsTable.removeAll)
        
        import Helpviewer.HelpWindow
        from .PasswordModel import PasswordModel
        
        self.passwordsTable.verticalHeader().hide()
        self.__passwordModel = PasswordModel(
            Helpviewer.HelpWindow.HelpWindow.passwordManager(), self)
        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setSourceModel(self.__passwordModel)
        self.searchEdit.textChanged.connect(
            self.__proxyModel.setFilterFixedString)
        self.passwordsTable.setModel(self.__proxyModel)
        
        fm = QFontMetrics(QFont())
        height = fm.height() + fm.height() // 3
        self.passwordsTable.verticalHeader().setDefaultSectionSize(height)
        self.passwordsTable.verticalHeader().setMinimumSectionSize(-1)
        
        self.__calculateHeaderSizes()
    
    def __calculateHeaderSizes(self):
        """
        Private method to calculate the section sizes of the horizontal header.
        """
        fm = QFontMetrics(QFont())
        for section in range(self.__passwordModel.columnCount()):
            header = self.passwordsTable.horizontalHeader()\
                .sectionSizeHint(section)
            if section == 0:
                header = fm.width("averagebiglongsitename")
            elif section == 1:
                header = fm.width("averagelongusername")
            elif section == 2:
                header = fm.width("averagelongpassword")
            buffer = fm.width("mm")
            header += buffer
            self.passwordsTable.horizontalHeader()\
                .resizeSection(section, header)
        self.passwordsTable.horizontalHeader().setStretchLastSection(True)
    
    @pyqtSlot()
    def on_passwordsButton_clicked(self):
        """
        Private slot to switch the password display mode.
        """
        if self.__passwordModel.showPasswords():
            self.__passwordModel.setShowPasswords(False)
            self.passwordsButton.setText(self.__showPasswordsText)
        else:
            res = E5MessageBox.yesNo(
                self,
                self.tr("Saved Passwords"),
                self.tr("""Do you really want to show passwords?"""))
            if res:
                self.__passwordModel.setShowPasswords(True)
                self.passwordsButton.setText(self.__hidePasswordsText)
        self.__calculateHeaderSizes()
