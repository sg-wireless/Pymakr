# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for a shelve operation.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QDateTime
from PyQt5.QtWidgets import QDialog

from .Ui_HgShelveDataDialog import Ui_HgShelveDataDialog


class HgShelveDataDialog(QDialog, Ui_HgShelveDataDialog):
    """
    Class implementing a dialog to enter the data for a shelve operation.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(HgShelveDataDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__initialDateTime = QDateTime.currentDateTime()
        self.dateTimeEdit.setDateTime(self.__initialDateTime)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    def getData(self):
        """
        Public method to get the user data.
        
        @return tuple containing the name (string), date (QDateTime),
            message (string) and a flag indicating to add/remove
            new/missing files (boolean)
        """
        if self.dateTimeEdit.dateTime() != self.__initialDateTime:
            dateTime = self.dateTimeEdit.dateTime()
        else:
            dateTime = QDateTime()
        return (
            self.nameEdit.text().replace(" ", "_"),
            dateTime,
            self.messageEdit.text(),
            self.addRemoveCheckBox.isChecked(),
        )
