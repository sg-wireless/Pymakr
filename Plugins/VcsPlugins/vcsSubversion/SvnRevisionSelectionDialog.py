# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the revisions for the svn diff command.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QDate, QDateTime, Qt
from PyQt5.QtWidgets import QDialog

from .Ui_SvnRevisionSelectionDialog import Ui_SvnRevisionSelectionDialog


class SvnRevisionSelectionDialog(QDialog, Ui_SvnRevisionSelectionDialog):
    """
    Class implementing a dialog to enter the revisions for the svn diff
    command.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget of the dialog (QWidget)
        """
        super(SvnRevisionSelectionDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.date1Edit.setDate(QDate.currentDate())
        self.date2Edit.setDate(QDate.currentDate())
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    def __getRevision(self, no):
        """
        Private method to generate the revision.
        
        @param no revision number to generate (1 or 2)
        @return revision (integer or string)
        """
        if no == 1:
            numberButton = self.number1Button
            numberSpinBox = self.number1SpinBox
            dateButton = self.date1Button
            dateEdit = self.date1Edit
            timeEdit = self.time1Edit
            headButton = self.head1Button
            workingButton = self.working1Button
            baseButton = self.base1Button
            committedButton = self.committed1Button
            prevButton = self.prev1Button
        else:
            numberButton = self.number2Button
            numberSpinBox = self.number2SpinBox
            dateButton = self.date2Button
            dateEdit = self.date2Edit
            timeEdit = self.time2Edit
            headButton = self.head2Button
            workingButton = self.working2Button
            baseButton = self.base2Button
            committedButton = self.committed2Button
            prevButton = self.prev2Button
        
        if numberButton.isChecked():
            return numberSpinBox.value()
        elif dateButton.isChecked():
            return "{{{0}}}".format(
                QDateTime(dateEdit.date(), timeEdit.time())
                .toString(Qt.ISODate))
        elif headButton.isChecked():
            return "HEAD"
        elif workingButton.isChecked():
            return "WORKING"
        elif baseButton.isChecked():
            return "BASE"
        elif committedButton.isChecked():
            return "COMMITTED"
        elif prevButton.isChecked():
            return "PREV"
        
    def getRevisions(self):
        """
        Public method to get the revisions.
        
        @return list two integers or strings
        """
        rev1 = self.__getRevision(1)
        rev2 = self.__getRevision(2)
        
        return [rev1, rev2]
