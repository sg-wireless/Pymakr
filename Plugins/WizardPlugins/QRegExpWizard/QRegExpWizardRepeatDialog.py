# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for entering repeat counts.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog

from .Ui_QRegExpWizardRepeatDialog import Ui_QRegExpWizardRepeatDialog


class QRegExpWizardRepeatDialog(QDialog, Ui_QRegExpWizardRepeatDialog):
    """
    Class implementing a dialog for entering repeat counts.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        """
        super(QRegExpWizardRepeatDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.unlimitedButton.setChecked(True)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    @pyqtSlot(int)
    def on_lowerSpin_valueChanged(self, value):
        """
        Private slot to handle the lowerSpin valueChanged signal.
        
        @param value value of the spinbox (integer)
        """
        if self.upperSpin.value() < value:
            self.upperSpin.setValue(value)
        
    @pyqtSlot(int)
    def on_upperSpin_valueChanged(self, value):
        """
        Private slot to handle the upperSpin valueChanged signal.
        
        @param value value of the spinbox (integer)
        """
        if self.lowerSpin.value() > value:
            self.lowerSpin.setValue(value)
        
    def getRepeat(self):
        """
        Public method to retrieve the dialog's result.
        
        @return ready formatted repeat string (string)
        """
        if self.unlimitedButton.isChecked():
            return "*"
        elif self.minButton.isChecked():
            reps = self.minSpin.value()
            if reps == 1:
                return "+"
            else:
                return "{{{0:d},}}".format(reps)
        elif self.maxButton.isChecked():
            reps = self.maxSpin.value()
            if reps == 1:
                return "?"
            else:
                return "{{,{0:d}}}".format(reps)
        elif self.exactButton.isChecked():
            reps = self.exactSpin.value()
            return "{{{0:d}}}".format(reps)
        elif self.betweenButton.isChecked():
            repsMin = self.lowerSpin.value()
            repsMax = self.upperSpin.value()
            return "{{{0:d},{1:d}}}".format(repsMin, repsMax)
