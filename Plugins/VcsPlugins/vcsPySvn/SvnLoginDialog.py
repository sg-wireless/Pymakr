# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the login dialog for pysvn.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_SvnLoginDialog import Ui_SvnLoginDialog


class SvnLoginDialog(QDialog, Ui_SvnLoginDialog):
    """
    Class implementing the login dialog for pysvn.
    """
    def __init__(self, realm, username, may_save, parent=None):
        """
        Constructor
        
        @param realm name of the realm of the requested credentials (string)
        @param username username as supplied by subversion (string)
        @param may_save flag indicating, that subversion is willing to save
            the answers returned (boolean)
        @param parent reference to the parent widget (QWidget)
        """
        super(SvnLoginDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.realmLabel.setText(
            self.tr("<b>Enter login data for realm {0}.</b>")
            .format(realm))
        self.usernameEdit.setText(username)
        self.saveCheckBox.setEnabled(may_save)
        if not may_save:
            self.saveCheckBox.setChecked(False)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    def getData(self):
        """
        Public method to retrieve the login data.
        
        @return tuple of three values (username, password, save)
        """
        return (self.usernameEdit.text(),
                self.passwordEdit.text(),
                self.saveCheckBox.isChecked())
