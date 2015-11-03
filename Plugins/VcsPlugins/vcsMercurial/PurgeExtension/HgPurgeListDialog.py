# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to list all files not tracked by Mercurial.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

from .Ui_HgPurgeListDialog import Ui_HgPurgeListDialog


class HgPurgeListDialog(QDialog, Ui_HgPurgeListDialog):
    """
    Class implementing a dialog to list all files not tracked by Mercurial.
    """
    def __init__(self, entries, parent=None):
        """
        Constructor
        
        @param entries list of entries to be shown (list of strings)
        @param parent reference to the parent widget (QWidget)
        """
        super(HgPurgeListDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.purgeList.addItems(sorted(entries))
