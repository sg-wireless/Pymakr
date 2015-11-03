# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show all cookies.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, Qt, QDateTime, QByteArray, \
    QSortFilterProxyModel
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import QDialog

from .CookieModel import CookieModel

from .Ui_CookiesDialog import Ui_CookiesDialog


class CookiesDialog(QDialog, Ui_CookiesDialog):
    """
    Class implementing a dialog to show all cookies.
    """
    def __init__(self, cookieJar, parent=None):
        """
        Constructor
        
        @param cookieJar reference to the cookie jar (CookieJar)
        @param parent reference to the parent widget (QWidget)
        """
        super(CookiesDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.addButton.setEnabled(False)
        
        self.__cookieJar = cookieJar
        
        self.removeButton.clicked.connect(self.cookiesTable.removeSelected)
        self.removeAllButton.clicked.connect(self.cookiesTable.removeAll)
        
        self.cookiesTable.verticalHeader().hide()
        model = CookieModel(cookieJar, self)
        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setSourceModel(model)
        self.searchEdit.textChanged.connect(
            self.__proxyModel.setFilterFixedString)
        self.cookiesTable.setModel(self.__proxyModel)
        self.cookiesTable.doubleClicked.connect(self.__showCookieDetails)
        self.cookiesTable.selectionModel().selectionChanged.connect(
            self.__tableSelectionChanged)
        self.cookiesTable.model().modelReset.connect(self.__tableModelReset)
        
        fm = QFontMetrics(QFont())
        height = fm.height() + fm.height() // 3
        self.cookiesTable.verticalHeader().setDefaultSectionSize(height)
        self.cookiesTable.verticalHeader().setMinimumSectionSize(-1)
        for section in range(model.columnCount()):
            header = self.cookiesTable.horizontalHeader()\
                .sectionSizeHint(section)
            if section == 0:
                header = fm.width("averagebiglonghost.averagedomain.info")
            elif section == 1:
                header = fm.width("_session_id")
            elif section == 4:
                header = fm.width(
                    QDateTime.currentDateTime().toString(Qt.LocalDate))
            buffer = fm.width("mm")
            header += buffer
            self.cookiesTable.horizontalHeader().resizeSection(section, header)
        self.cookiesTable.horizontalHeader().setStretchLastSection(True)
        self.cookiesTable.model().sort(
            self.cookiesTable.horizontalHeader().sortIndicatorSection(),
            Qt.AscendingOrder)
        
        self.__detailsDialog = None
    
    def __showCookieDetails(self, index):
        """
        Private slot to show a dialog with the cookie details.
        
        @param index index of the entry to show (QModelIndex)
        """
        if not index.isValid():
            return
        
        cookiesTable = self.sender()
        if cookiesTable is None:
            return
        
        model = cookiesTable.model()
        row = index.row()
        
        domain = model.data(model.index(row, 0))
        name = model.data(model.index(row, 1))
        path = model.data(model.index(row, 2))
        secure = model.data(model.index(row, 3))
        expires = model.data(model.index(row, 4)).toString("yyyy-MM-dd hh:mm")
        value = bytes(
            QByteArray.fromPercentEncoding(
                model.data(model.index(row, 5)))).decode()
        
        if self.__detailsDialog is None:
            from .CookieDetailsDialog import CookieDetailsDialog
            self.__detailsDialog = CookieDetailsDialog(self)
        self.__detailsDialog.setData(domain, name, path, secure, expires,
                                     value)
        self.__detailsDialog.show()
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add a new exception.
        """
        selection = self.cookiesTable.selectionModel().selectedRows()
        if len(selection) == 0:
            return
        
        from .CookiesExceptionsDialog import CookiesExceptionsDialog
        
        firstSelected = selection[0]
        domainSelection = firstSelected.sibling(firstSelected.row(), 0)
        domain = self.__proxyModel.data(domainSelection, Qt.DisplayRole)
        dlg = CookiesExceptionsDialog(self.__cookieJar, self)
        dlg.setDomainName(domain)
        dlg.exec_()
    
    def __tableSelectionChanged(self, selected, deselected):
        """
        Private slot to handle a change of selected items.
        
        @param selected selected indexes (QItemSelection)
        @param deselected deselected indexes (QItemSelection)
        """
        self.addButton.setEnabled(len(selected.indexes()) > 0)
    
    def __tableModelReset(self):
        """
        Private slot to handle a reset of the cookies table.
        """
        self.addButton.setEnabled(False)
