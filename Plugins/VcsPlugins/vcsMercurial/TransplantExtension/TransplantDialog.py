# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for a transplant session.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QValidator
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_TransplantDialog import Ui_TransplantDialog


class RevisionsValidator(QValidator):
    """
    Class implementing a validator for the revisions line edit.
    """
    def __init__(self, multiRevsAllowed, parent=None):
        """
        Constructor
        
        @param multiRevsAllowed flag indicating, if multi revs are allowed
            (boolean)
        @param parent reference to the parent object (QObject)
        """
        super(RevisionsValidator, self).__init__(parent)
        
        self.__multiRevsAllowed = multiRevsAllowed
    
    def validate(self, input, pos):
        """
        Public method to validate the given input.
        
        @param input input to be validated (string)
        @param pos position of the cursor (integer)
        @return tuple with validation result, input and position
            (QValidator.State, string, integer)
        """
        state = QValidator.Invalid
        
        if input == "":
            state = QValidator.Intermediate
        else:
            state = QValidator.Acceptable
            revs = input.strip().split()
            for rev in revs:
                if ":" in rev:
                    if self.__multiRevsAllowed:
                        # it is a revision range
                        revList = rev.split(":")
                        if len(revList) != 2:
                            state = QValidator.Invalid
                            break
                        for r in revList:
                            if r != "" and not r.isdigit():
                                state = QValidator.Invalid
                                break
                    else:
                        state = QValidator.Invalid
                        break
                else:
                    if not rev.isdigit():
                        state = QValidator.Invalid
                        break
        
        return state, input, pos


class TransplantDialog(QDialog, Ui_TransplantDialog):
    """
    Class implementing a dialog to enter the data for a transplant session.
    """
    def __init__(self, branchesList, parent=None):
        """
        Constructor
        
        @param branchesList list of available branch names (list of strings)
        @param parent reference to the parent widget (QWidget)
        """
        super(TransplantDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.branchesCombo.addItems(["", "default"] + sorted(branchesList))
        
        self.__mergeRevisionsValidator = RevisionsValidator(False, self)
        self.mergeEdit.setValidator(self.__mergeRevisionsValidator)
       
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
    
    def __updateOk(self):
        """
        Private slot to update the state of the OK button.
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            self.revisionsEdit.toPlainText() != "" or
            self.allCheckBox.isChecked())
    
    @pyqtSlot()
    def on_revisionsEdit_textChanged(self):
        """
        Private slot to react upon changes of revisions.
        """
        self.__updateOk()
    
    @pyqtSlot(str)
    def on_branchesCombo_editTextChanged(self, txt):
        """
        Private slot to react upon changes of the branch name.
        
        @param txt contents of the branches combo (string)
        """
        self.allCheckBox.setEnabled(txt != "")
    
    @pyqtSlot(bool)
    def on_allCheckBox_clicked(self, checked):
        """
        Private slot to react upon selection of the all check box.
        
        @param checked state of the check box (boolean)
        """
        self.__updateOk()
    
    def getData(self):
        """
        Public method to retrieve the entered data.
        
        @return tuple with list of revisions, source repo, branch name, a flag
            indicating to transplant all, list of revisions to skip, list of
            revisions to merge and a flag indicating to append  transplant info
            (list of strings, string, string, boolean, list of strings,
            list of strings, boolean)
        """
        return (
            self.revisionsEdit.toPlainText().strip().splitlines(),
            self.repoEdit.text().strip(),
            self.branchesCombo.currentText().strip(),
            self.allCheckBox.isChecked(),
            self.pruneEdit.toPlainText().strip().splitlines(),
            self.mergeEdit.text().strip().split(),
            self.logCheckBox.isChecked()
        )
