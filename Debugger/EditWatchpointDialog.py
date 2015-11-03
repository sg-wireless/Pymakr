# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to edit watch expression properties.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_EditWatchpointDialog import Ui_EditWatchpointDialog


class EditWatchpointDialog(QDialog, Ui_EditWatchpointDialog):
    """
    Class implementing a dialog to edit watch expression properties.
    """
    def __init__(self, properties, parent=None, name=None, modal=False):
        """
        Constructor
        
        @param properties properties for the watch expression (tuple)
            (expression, temporary flag, enabled flag, ignore count,
            special condition)
        @param parent the parent of this dialog
        @param name the widget name of this dialog
        @param modal flag indicating a modal dialog
        """
        super(EditWatchpointDialog, self).__init__(parent)
        self.setupUi(self)
        if name:
            self.setObjectName(name)
        self.setModal(modal)
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        
        # connect our widgets
        self.conditionEdit.textChanged.connect(self.__textChanged)
        self.specialEdit.textChanged.connect(self.__textChanged)
        
        cond, temp, enabled, count, special = properties
        
        # set the condition
        if not special:
            self.conditionButton.setChecked(True)
            self.conditionEdit.setText(cond)
        else:
            self.specialButton.setChecked(True)
            self.specialEdit.setText(cond)
            ind = self.specialCombo.findText(special)
            if ind == -1:
                ind = 0
            self.specialCombo.setCurrentIndex(ind)
        
        # set the ignore count
        self.ignoreSpinBox.setValue(count)
        
        # set the checkboxes
        self.temporaryCheckBox.setChecked(temp)
        self.enabledCheckBox.setChecked(enabled)
        
        if not special:
            self.conditionEdit.setFocus()
        else:
            self.specialEdit.setFocus()
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    def __textChanged(self, txt):
        """
        Private slot to handle the text changed signal of the condition line
        edit.
        
        @param txt text of the line edit (string)
        """
        if self.conditionButton.isChecked():
            self.buttonBox.button(QDialogButtonBox.Ok)\
                .setEnabled(self.conditionEdit.text() != "")
        elif self.specialButton.isChecked():
            self.buttonBox.button(QDialogButtonBox.Ok)\
                .setEnabled(self.specialEdit.text() != "")
        else:
            # should not happen
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        
    def getData(self):
        """
        Public method to retrieve the entered data.
        
        @return a tuple containing the watch expressions new properties
            (expression, temporary flag, enabled flag, ignore count,
            special condition)
        """
        if self.conditionButton.isChecked():
            return (self.conditionEdit.text(),
                    self.temporaryCheckBox.isChecked(),
                    self.enabledCheckBox.isChecked(),
                    self.ignoreSpinBox.value(),
                    "")
        elif self.specialButton.isChecked():
            return (self.specialEdit.text(),
                    self.temporaryCheckBox.isChecked(),
                    self.enabledCheckBox.isChecked(),
                    self.ignoreSpinBox.value(),
                    self.specialCombo.currentText())
        else:
            # should not happen
            return ("", False, False, 0, "")
