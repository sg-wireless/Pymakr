# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for the configuration of cookie exceptions.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, QSortFilterProxyModel
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import QDialog, QCompleter

from .CookieExceptionsModel import CookieExceptionsModel
from .CookieModel import CookieModel

from .Ui_CookiesExceptionsDialog import Ui_CookiesExceptionsDialog


class CookiesExceptionsDialog(QDialog, Ui_CookiesExceptionsDialog):
    """
    Class implementing a dialog for the configuration of cookie exceptions.
    """
    def __init__(self, cookieJar, parent=None):
        """
        Constructor
        
        @param cookieJar reference to the cookie jar (CookieJar)
        @param parent reference to the parent widget (QWidget)
        """
        super(CookiesExceptionsDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__cookieJar = cookieJar
        
        self.removeButton.clicked.connect(
            self.exceptionsTable.removeSelected)
        self.removeAllButton.clicked.connect(
            self.exceptionsTable.removeAll)
        
        self.exceptionsTable.verticalHeader().hide()
        self.__exceptionsModel = CookieExceptionsModel(cookieJar)
        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setSourceModel(self.__exceptionsModel)
        self.searchEdit.textChanged.connect(
            self.__proxyModel.setFilterFixedString)
        self.exceptionsTable.setModel(self.__proxyModel)
        
        cookieModel = CookieModel(cookieJar, self)
        self.domainEdit.setCompleter(QCompleter(cookieModel, self.domainEdit))
        
        f = QFont()
        f.setPointSize(10)
        fm = QFontMetrics(f)
        height = fm.height() + fm.height() // 3
        self.exceptionsTable.verticalHeader().setDefaultSectionSize(height)
        self.exceptionsTable.verticalHeader().setMinimumSectionSize(-1)
        for section in range(self.__exceptionsModel.columnCount()):
            header = self.exceptionsTable.horizontalHeader()\
                .sectionSizeHint(section)
            if section == 0:
                header = fm.width("averagebiglonghost.averagedomain.info")
            elif section == 1:
                header = fm.width(self.tr("Allow For Session"))
            buffer = fm.width("mm")
            header += buffer
            self.exceptionsTable.horizontalHeader()\
                .resizeSection(section, header)
    
    def setDomainName(self, domain):
        """
        Public method to set the domain to be displayed.
        
        @param domain domain name to be displayed (string)
        """
        self.domainEdit.setText(domain)
    
    @pyqtSlot(str)
    def on_domainEdit_textChanged(self, txt):
        """
        Private slot to handle a change of the domain edit text.
        
        @param txt current text of the edit (string)
        """
        enabled = txt != ""
        self.blockButton.setEnabled(enabled)
        self.allowButton.setEnabled(enabled)
        self.allowForSessionButton.setEnabled(enabled)
    
    @pyqtSlot()
    def on_blockButton_clicked(self):
        """
        Private slot to block cookies of a domain.
        """
        from .CookieJar import CookieJar
        self.__exceptionsModel.addRule(self.domainEdit.text(), CookieJar.Block)
    
    @pyqtSlot()
    def on_allowForSessionButton_clicked(self):
        """
        Private slot to allow cookies of a domain for the current session only.
        """
        from .CookieJar import CookieJar
        self.__exceptionsModel.addRule(self.domainEdit.text(),
                                       CookieJar.AllowForSession)
    
    @pyqtSlot()
    def on_allowButton_clicked(self):
        """
        Private slot to allow cookies of a domain.
        """
        from .CookieJar import CookieJar
        self.__exceptionsModel.addRule(self.domainEdit.text(), CookieJar.Allow)
