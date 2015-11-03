# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implemting a dialog to show repository information.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_RepositoryInfoDialog import Ui_VcsRepositoryInfoDialog


class VcsRepositoryInfoDialog(QDialog, Ui_VcsRepositoryInfoDialog):
    """
    Class implemting a dialog to show repository information.
    """
    def __init__(self, parent, info):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        @param info info data to show (string)
        """
        super(VcsRepositoryInfoDialog, self).__init__(parent)
        self.setupUi(self)
        self.infoBrowser.setHtml(info)
