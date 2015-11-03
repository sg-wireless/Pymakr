# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the revisions for the hg diff command.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_HgRevisionsSelectionDialog import Ui_HgRevisionsSelectionDialog


class HgRevisionsSelectionDialog(QDialog, Ui_HgRevisionsSelectionDialog):
    """
    Class implementing a dialog to enter the revisions for the hg diff command.
    """
    def __init__(self, tagsList, branchesList, bookmarksList=None,
                 parent=None):
        """
        Constructor
        
        @param tagsList list of tags (list of strings)
        @param branchesList list of branches (list of strings)
        @param bookmarksList list of bookmarks (list of strings)
        @param parent parent widget of the dialog (QWidget)
        """
        super(HgRevisionsSelectionDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        
        self.tag1Combo.addItems(sorted(tagsList))
        self.tag2Combo.addItems(sorted(tagsList))
        self.branch1Combo.addItems(["default"] + sorted(branchesList))
        self.branch2Combo.addItems(["default"] + sorted(branchesList))
        if bookmarksList is not None:
            self.bookmark1Combo.addItems(sorted(bookmarksList))
            self.bookmark2Combo.addItems(sorted(bookmarksList))
        else:
            self.bookmark1Button.setHidden(True)
            self.bookmark1Combo.setHidden(True)
            self.bookmark2Button.setHidden(True)
            self.bookmark2Combo.setHidden(True)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    def __updateOK(self):
        """
        Private slot to update the OK button.
        """
        enabled = True
        if self.id1Button.isChecked():
            enabled = enabled and self.id1Edit.text() != ""
        elif self.tag1Button.isChecked():
            enabled = enabled and self.tag1Combo.currentText() != ""
        elif self.branch1Button.isChecked():
            enabled = enabled and self.branch1Combo.currentText() != ""
        elif self.bookmark1Button.isChecked():
            enabled = enabled and self.bookmark1Combo.currentText() != ""
        
        if self.id2Button.isChecked():
            enabled = enabled and self.id2Edit.text() != ""
        elif self.tag2Button.isChecked():
            enabled = enabled and self.tag2Combo.currentText() != ""
        elif self.branch2Button.isChecked():
            enabled = enabled and self.branch2Combo.currentText() != ""
        elif self.bookmark2Button.isChecked():
            enabled = enabled and self.bookmark2Combo.currentText() != ""
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enabled)
    
    @pyqtSlot(bool)
    def on_id1Button_toggled(self, checked):
        """
        Private slot to handle changes of the ID1 select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_id2Button_toggled(self, checked):
        """
        Private slot to handle changes of the ID2 select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_tag1Button_toggled(self, checked):
        """
        Private slot to handle changes of the Tag1 select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_tag2Button_toggled(self, checked):
        """
        Private slot to handle changes of the Tag2 select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_branch1Button_toggled(self, checked):
        """
        Private slot to handle changes of the Branch1 select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_branch2Button_toggled(self, checked):
        """
        Private slot to handle changes of the Branch2 select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_bookmark1Button_toggled(self, checked):
        """
        Private slot to handle changes of the Bookmark1 select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_bookmark2Button_toggled(self, checked):
        """
        Private slot to handle changes of the Bookmark2 select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_id1Edit_textChanged(self, txt):
        """
        Private slot to handle changes of the ID1 edit.
        
        @param txt text of the edit (string)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_id2Edit_textChanged(self, txt):
        """
        Private slot to handle changes of the ID2 edit.
        
        @param txt text of the edit (string)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_tag1Combo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the Tag1 combo.
        
        @param txt text of the combo (string)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_tag2Combo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the Tag2 combo.
        
        @param txt text of the combo (string)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_branch1Combo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the Branch1 combo.
        
        @param txt text of the combo (string)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_branch2Combo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the Branch2 combo.
        
        @param txt text of the combo (string)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_bookmark1Combo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the Bookmark1 combo.
        
        @param txt text of the combo (string)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_bookmark2Combo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the Bookmark2 combo.
        
        @param txt text of the combo (string)
        """
        self.__updateOK()
    
    def __getRevision(self, no):
        """
        Private method to generate the revision.
        
        @param no revision number to generate (1 or 2)
        @return revision (string)
        """
        if no == 1:
            numberButton = self.number1Button
            numberSpinBox = self.number1SpinBox
            idButton = self.id1Button
            idEdit = self.id1Edit
            tagButton = self.tag1Button
            tagCombo = self.tag1Combo
            branchButton = self.branch1Button
            branchCombo = self.branch1Combo
            bookmarkButton = self.bookmark1Button
            bookmarkCombo = self.bookmark1Combo
            tipButton = self.tip1Button
            prevButton = self.prev1Button
            noneButton = self.none1Button
        else:
            numberButton = self.number2Button
            numberSpinBox = self.number2SpinBox
            idButton = self.id2Button
            idEdit = self.id2Edit
            tagButton = self.tag2Button
            tagCombo = self.tag2Combo
            branchButton = self.branch2Button
            branchCombo = self.branch2Combo
            bookmarkButton = self.bookmark2Button
            bookmarkCombo = self.bookmark2Combo
            tipButton = self.tip2Button
            prevButton = self.prev2Button
            noneButton = self.none2Button
        
        if numberButton.isChecked():
            return "rev({0})".format(numberSpinBox.value())
        elif idButton.isChecked():
            return "id({0})".format(idEdit.text())
        elif tagButton.isChecked():
            return tagCombo.currentText()
        elif branchButton.isChecked():
            return branchCombo.currentText()
        elif bookmarkButton.isChecked():
            return bookmarkCombo.currentText()
        elif tipButton.isChecked():
            return "tip"
        elif prevButton.isChecked():
            return "."
        elif noneButton.isChecked():
            return ""
    
    def getRevisions(self):
        """
        Public method to get the revisions.
        
        @return list two strings
        """
        rev1 = self.__getRevision(1)
        rev2 = self.__getRevision(2)
        
        return [rev1, rev2]
