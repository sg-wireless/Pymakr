# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the cookies configuration dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog

from .CookieJar import CookieJar

from .Ui_CookiesConfigurationDialog import Ui_CookiesConfigurationDialog


class CookiesConfigurationDialog(QDialog, Ui_CookiesConfigurationDialog):
    """
    Class implementing the cookies configuration dialog.
    """
    def __init__(self, parent):
        """
        Constructor
        
        @param parent reference to the parent object (QWidget)
        """
        super(CookiesConfigurationDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__mw = parent
        
        jar = self.__mw.cookieJar()
        acceptPolicy = jar.acceptPolicy()
        if acceptPolicy == CookieJar.AcceptAlways:
            self.acceptCombo.setCurrentIndex(0)
        elif acceptPolicy == CookieJar.AcceptNever:
            self.acceptCombo.setCurrentIndex(1)
        elif acceptPolicy == CookieJar.AcceptOnlyFromSitesNavigatedTo:
            self.acceptCombo.setCurrentIndex(2)
        
        keepPolicy = jar.keepPolicy()
        if keepPolicy == CookieJar.KeepUntilExpire:
            self.keepUntilCombo.setCurrentIndex(0)
        elif keepPolicy == CookieJar.KeepUntilExit:
            self.keepUntilCombo.setCurrentIndex(1)
        elif keepPolicy == CookieJar.KeepUntilTimeLimit:
            self.keepUntilCombo.setCurrentIndex(2)
        
        self.filterTrackingCookiesCheckbox.setChecked(
            jar.filterTrackingCookies())
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    def accept(self):
        """
        Public slot to accept the dialog.
        """
        acceptSelection = self.acceptCombo.currentIndex()
        if acceptSelection == 0:
            acceptPolicy = CookieJar.AcceptAlways
        elif acceptSelection == 1:
            acceptPolicy = CookieJar.AcceptNever
        elif acceptSelection == 2:
            acceptPolicy = CookieJar.AcceptOnlyFromSitesNavigatedTo
        
        keepSelection = self.keepUntilCombo.currentIndex()
        if keepSelection == 0:
            keepPolicy = CookieJar.KeepUntilExpire
        elif keepSelection == 1:
            keepPolicy = CookieJar.KeepUntilExit
        elif keepSelection == 2:
            keepPolicy = CookieJar.KeepUntilTimeLimit
        
        jar = self.__mw.cookieJar()
        jar.setAcceptPolicy(acceptPolicy)
        jar.setKeepPolicy(keepPolicy)
        jar.setFilterTrackingCookies(
            self.filterTrackingCookiesCheckbox.isChecked())
        
        super(CookiesConfigurationDialog, self).accept()
    
    @pyqtSlot()
    def on_exceptionsButton_clicked(self):
        """
        Private slot to show the cookies exceptions dialog.
        """
        from .CookiesExceptionsDialog import CookiesExceptionsDialog
        dlg = CookiesExceptionsDialog(self.__mw.cookieJar())
        dlg.exec_()
    
    @pyqtSlot()
    def on_cookiesButton_clicked(self):
        """
        Private slot to show the cookies dialog.
        """
        from .CookiesDialog import CookiesDialog
        dlg = CookiesDialog(self.__mw.cookieJar())
        dlg.exec_()
