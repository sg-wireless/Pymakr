# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog showing the cookie data.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

from .Ui_CookieDetailsDialog import Ui_CookieDetailsDialog


class CookieDetailsDialog(QDialog, Ui_CookieDetailsDialog):
    """
    Class implementing a dialog showing the cookie data.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QWidget)
        """
        super(CookieDetailsDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
    
    def setData(self, domain, name, path, secure, expires, value):
        """
        Public method to set the data to be shown.
        
        @param domain domain of the cookie (string)
        @param name name of the cookie (string)
        @param path path of the cookie (string)
        @param secure flag indicating a secure cookie (boolean)
        @param expires expiration time of the cookie (string)
        @param value value of the cookie (string)
        """
        self.domainEdit.setText(domain)
        self.nameEdit.setText(name)
        self.pathEdit.setText(path)
        self.secureCheckBox.setChecked(secure)
        self.expirationEdit.setText(expires)
        self.valueEdit.setPlainText(value)
