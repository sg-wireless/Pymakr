# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to select revisions.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_HgMultiRevisionSelectionDialog import \
    Ui_HgMultiRevisionSelectionDialog


class HgMultiRevisionSelectionDialog(
        QDialog, Ui_HgMultiRevisionSelectionDialog):
    """
    Class implementing a dialog to select revisions.
    """
    def __init__(self, tagsList, branchesList, bookmarksList=None,
                 emptyRevsOk=False, showLimit=False, limitDefault=100,
                 parent=None):
        """
        Constructor
        
        @param tagsList list of tags (list of strings)
        @param branchesList list of branches (list of strings)
        @param bookmarksList list of bookmarks (list of strings)
        @param emptyRevsOk flag indicating that it is ok to not enter
            revisions (boolean)
        @param showLimit flag indicating to show the limit entry (boolean)
        @param limitDefault default value for the limit (integer)
        @param parent parent widget (QWidget)
        """
        super(HgMultiRevisionSelectionDialog, self).__init__(parent)
        self.setupUi(self)
       
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        
        self.__emptyRevsOk = emptyRevsOk
        
        self.tagCombo.addItems(sorted(tagsList))
        self.branchCombo.addItems(["default"] + sorted(branchesList))
        if bookmarksList is not None:
            self.bookmarkCombo.addItems(sorted(bookmarksList))
        else:
            self.bookmarkButton.setHidden(True)
            self.bookmarkCombo.setHidden(True)
        
        self.limitSpinBox.setValue(limitDefault)
        self.limitGroup.setVisible(showLimit)
    
    def __updateOK(self):
        """
        Private slot to update the OK button.
        """
        enabled = True
        if self.changesetsButton.isChecked():
            enabled = self.changesetsEdit.toPlainText() != ""
        elif self.tagButton.isChecked():
            enabled = self.tagCombo.currentText() != ""
        elif self.branchButton.isChecked():
            enabled = self.branchCombo.currentText() != ""
        elif self.bookmarkButton.isChecked():
            enabled = self.bookmarkCombo.currentText() != ""
        if not enabled and self.__emptyRevsOk:
            enabled = self.limitGroup.isChecked()
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enabled)
    
    @pyqtSlot(bool)
    def on_changesetsButton_toggled(self, checked):
        """
        Private slot to handle changes of the Changesets select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_tagButton_toggled(self, checked):
        """
        Private slot to handle changes of the Tag select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_branchButton_toggled(self, checked):
        """
        Private slot to handle changes of the Branch select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_bookmarkButton_toggled(self, checked):
        """
        Private slot to handle changes of the Bookmark select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot()
    def on_changesetsEdit_textChanged(self):
        """
        Private slot to handle changes of the Changesets edit.
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_tagCombo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the Tag combo.
        
        @param txt text of the combo (string)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_branchCombo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the Branch combo.
        
        @param txt text of the combo (string)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_bookmarkCombo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the Bookmark combo.
        
        @param txt text of the combo (string)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_limitGroup_toggled(self, checked):
        """
        Private slot to handle changes of the Limit Results group status.
        
        @param checked state of the group (boolean)
        """
        self.__updateOK()
    
    def getRevisions(self):
        """
        Public method to retrieve the selected revisions.
        
        @return tuple of selected revisions (list of strings) and number
            of entries to be shown (integer)
        """
        if self.changesetsButton.isChecked():
            revs = self.changesetsEdit.toPlainText().strip().splitlines()
        elif self.tagButton.isChecked():
            revs = [self.tagCombo.currentText()]
        elif self.branchButton.isChecked():
            revs = [self.branchCombo.currentText()]
        elif self.bookmarkButton.isChecked():
            revs = [self.bookmarkCombo.currentText()]
        else:
            revs = []
        
        if self.limitGroup.isChecked():
            limit = self.limitSpinBox.value()
        else:
            limit = 0
        
        return revs, limit
