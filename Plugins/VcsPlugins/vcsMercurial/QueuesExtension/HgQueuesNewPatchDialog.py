# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to get the data for a new patch.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, QDateTime
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_HgQueuesNewPatchDialog import Ui_HgQueuesNewPatchDialog


class HgQueuesNewPatchDialog(QDialog, Ui_HgQueuesNewPatchDialog):
    """
    Class implementing a dialog to get the data for a new patch.
    """
    NEW_MODE = 0
    REFRESH_MODE = 1
    
    def __init__(self, mode, message="", parent=None):
        """
        Constructor
        
        @param mode mode of the dialog (HgQueuesNewPatchDialog.NEW_MODE,
            HgQueuesNewPatchDialog.REFRESH_MODE)
        @param message text to set as the commit message (string)
        @param parent reference to the parent widget (QWidget)
        @exception ValueError raised to indicate an invalid dialog mode
        """
        super(HgQueuesNewPatchDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__mode = mode
        if self.__mode == HgQueuesNewPatchDialog.REFRESH_MODE:
            self.nameLabel.hide()
            self.nameEdit.hide()
        elif self.__mode == HgQueuesNewPatchDialog.NEW_MODE:
            # nothing special here
            pass
        else:
            raise ValueError("invalid value for mode")
        
        if message:
            self.messageEdit.setPlainText(message)
        
        self.dateTimeEdit.setDateTime(QDateTime.currentDateTime())
        
        self.__updateUI()
    
    def __updateUI(self):
        """
        Private slot to update the UI.
        """
        if self.__mode == HgQueuesNewPatchDialog.REFRESH_MODE:
            enable = self.messageEdit.toPlainText() != ""
        else:
            enable = self.nameEdit.text() != "" and \
                self.messageEdit.toPlainText() != ""
        if self.userGroup.isChecked():
            enable = enable and \
                (self.currentUserCheckBox.isChecked() or
                 self.userEdit.text() != "")
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enable)
    
    @pyqtSlot(str)
    def on_nameEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the patch name.
        
        @param txt text of the edit (string)
        """
        self.__updateUI()
    
    @pyqtSlot()
    def on_messageEdit_textChanged(self):
        """
        Private slot to handle changes of the patch message.
        """
        self.__updateUI()
    
    @pyqtSlot(bool)
    def on_userGroup_toggled(self, checked):
        """
        Private slot to handle changes of the user group state.
        
        @param checked flag giving the checked state (boolean)
        """
        self.__updateUI()
    
    @pyqtSlot(bool)
    def on_currentUserCheckBox_toggled(self, checked):
        """
        Private slot to handle changes of the currentuser state.
        
        @param checked flag giving the checked state (boolean)
        """
        self.__updateUI()
    
    @pyqtSlot(str)
    def on_userEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the user name.
        
        @param txt text of the edit (string)
        """
        self.__updateUI()
    
    def getData(self):
        """
        Public method to retrieve the entered data.
        
        @return tuple giving the patch name and message, a tuple giving a
            flag indicating to set the user, a flag indicating to use the
            current user and the user name and another tuple giving a flag
            indicating to set the date, a flag indicating to use the
            current date and the date (string, string, (boolean, boolean,
            string), (boolean, boolean, string))
        """
        userData = (self.userGroup.isChecked(),
                    self.currentUserCheckBox.isChecked(),
                    self.userEdit.text())
        dateData = (self.dateGroup.isChecked(),
                    self.currentDateCheckBox.isChecked(),
                    self.dateTimeEdit.dateTime().toString("yyyy-MM-dd hh:mm"))
        return (self.nameEdit.text().replace(" ", "_"),
                self.messageEdit.toPlainText(), userData, dateData)
