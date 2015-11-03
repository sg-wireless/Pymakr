# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the message box wizard dialog.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMessageBox, QDialog, QDialogButtonBox

from .Ui_MessageBoxWizardDialog import Ui_MessageBoxWizardDialog


class MessageBoxWizardDialog(QDialog, Ui_MessageBoxWizardDialog):
    """
    Class implementing the message box wizard dialog.
    
    It displays a dialog for entering the parameters
    for the QMessageBox code generator.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        """
        super(MessageBoxWizardDialog, self).__init__(parent)
        self.setupUi(self)
        
        # keep the following three lists in sync
        self.buttonsList = [
            self.tr("No button"),
            self.tr("Abort"),
            self.tr("Apply"),
            self.tr("Cancel"),
            self.tr("Close"),
            self.tr("Discard"),
            self.tr("Help"),
            self.tr("Ignore"),
            self.tr("No"),
            self.tr("No to all"),
            self.tr("Ok"),
            self.tr("Open"),
            self.tr("Reset"),
            self.tr("Restore defaults"),
            self.tr("Retry"),
            self.tr("Save"),
            self.tr("Save all"),
            self.tr("Yes"),
            self.tr("Yes to all"),
        ]
        self.buttonsCodeListBinary = [
            QMessageBox.NoButton,
            QMessageBox.Abort,
            QMessageBox.Apply,
            QMessageBox.Cancel,
            QMessageBox.Close,
            QMessageBox.Discard,
            QMessageBox.Help,
            QMessageBox.Ignore,
            QMessageBox.No,
            QMessageBox.NoToAll,
            QMessageBox.Ok,
            QMessageBox.Open,
            QMessageBox.Reset,
            QMessageBox.RestoreDefaults,
            QMessageBox.Retry,
            QMessageBox.Save,
            QMessageBox.SaveAll,
            QMessageBox.Yes,
            QMessageBox.YesToAll,
        ]
        self.buttonsCodeListText = [
            "QMessageBox.NoButton",
            "QMessageBox.Abort",
            "QMessageBox.Apply",
            "QMessageBox.Cancel",
            "QMessageBox.Close",
            "QMessageBox.Discard",
            "QMessageBox.Help",
            "QMessageBox.Ignore",
            "QMessageBox.No",
            "QMessageBox.NoToAll",
            "QMessageBox.Ok",
            "QMessageBox.Open",
            "QMessageBox.Reset",
            "QMessageBox.RestoreDefaults",
            "QMessageBox.Retry",
            "QMessageBox.Save",
            "QMessageBox.SaveAll",
            "QMessageBox.Yes",
            "QMessageBox.YesToAll",
        ]
        
        self.defaultCombo.addItems(self.buttonsList)
        
        self.bTest = self.buttonBox.addButton(
            self.tr("Test"), QDialogButtonBox.ActionRole)
    
    def __testQt42(self):
        """
        Private method to test the selected options for Qt 4.2.0.
        """
        buttons = QMessageBox.NoButton
        if self.abortCheck.isChecked():
            buttons |= QMessageBox.Abort
        if self.applyCheck.isChecked():
            buttons |= QMessageBox.Apply
        if self.cancelCheck.isChecked():
            buttons |= QMessageBox.Cancel
        if self.closeCheck.isChecked():
            buttons |= QMessageBox.Close
        if self.discardCheck.isChecked():
            buttons |= QMessageBox.Discard
        if self.helpCheck.isChecked():
            buttons |= QMessageBox.Help
        if self.ignoreCheck.isChecked():
            buttons |= QMessageBox.Ignore
        if self.noCheck.isChecked():
            buttons |= QMessageBox.No
        if self.notoallCheck.isChecked():
            buttons |= QMessageBox.NoToAll
        if self.okCheck.isChecked():
            buttons |= QMessageBox.Ok
        if self.openCheck.isChecked():
            buttons |= QMessageBox.Open
        if self.resetCheck.isChecked():
            buttons |= QMessageBox.Reset
        if self.restoreCheck.isChecked():
            buttons |= QMessageBox.RestoreDefaults
        if self.retryCheck.isChecked():
            buttons |= QMessageBox.Retry
        if self.saveCheck.isChecked():
            buttons |= QMessageBox.Save
        if self.saveallCheck.isChecked():
            buttons |= QMessageBox.SaveAll
        if self.yesCheck.isChecked():
            buttons |= QMessageBox.Yes
        if self.yestoallCheck.isChecked():
            buttons |= QMessageBox.YesToAll
        if buttons == QMessageBox.NoButton:
            buttons = QMessageBox.Ok
        
        defaultButton = self.buttonsCodeListBinary[
            self.defaultCombo.currentIndex()]
        
        if self.rInformation.isChecked():
            QMessageBox.information(
                self,
                self.eCaption.text(),
                self.eMessage.toPlainText(),
                QMessageBox.StandardButtons(buttons),
                defaultButton
            )
        elif self.rQuestion.isChecked():
            QMessageBox.question(
                self,
                self.eCaption.text(),
                self.eMessage.toPlainText(),
                QMessageBox.StandardButtons(buttons),
                defaultButton
            )
        elif self.rWarning.isChecked():
            QMessageBox.warning(
                self,
                self.eCaption.text(),
                self.eMessage.toPlainText(),
                QMessageBox.StandardButtons(buttons),
                defaultButton
            )
        elif self.rCritical.isChecked():
            QMessageBox.critical(
                self,
                self.eCaption.text(),
                self.eMessage.toPlainText(),
                QMessageBox.StandardButtons(buttons),
                defaultButton
            )
    
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.bTest:
            self.on_bTest_clicked()
    
    @pyqtSlot()
    def on_bTest_clicked(self):
        """
        Private method to test the selected options.
        """
        if self.rAbout.isChecked():
            QMessageBox.about(
                None,
                self.eCaption.text(),
                self.eMessage.toPlainText()
            )
        elif self.rAboutQt.isChecked():
            QMessageBox.aboutQt(
                None,
                self.eCaption.text()
            )
        else:
            self.__testQt42()
    
    def __enabledGroups(self):
        """
        Private method to enable/disable some group boxes.
        """
        enable = not self.rAbout.isChecked() and not self.rAboutQt.isChecked()
        self.standardButtons.setEnabled(enable)
        self.lResultVar.setEnabled(enable)
        self.eResultVar.setEnabled(enable)
        
        self.eMessage.setEnabled(not self.rAboutQt.isChecked())
    
    def on_rAbout_toggled(self, on):
        """
        Private slot to handle the toggled signal of the rAbout radio button.
        
        @param on toggle state (boolean) (ignored)
        """
        self.__enabledGroups()
    
    def on_rAboutQt_toggled(self, on):
        """
        Private slot to handle the toggled signal of the rAboutQt radio button.
        
        @param on toggle state (boolean) (ignored)
        """
        self.__enabledGroups()
    
    def __getButtonCode(self, istring, indString):
        """
        Private method to generate the button code.
        
        @param istring indentation string (string)
        @param indString string used for indentation (space or tab) (string)
        @return the button code (string)
        """
        buttons = []
        if self.abortCheck.isChecked():
            buttons.append("QMessageBox.Abort")
        if self.applyCheck.isChecked():
            buttons.append("QMessageBox.Apply")
        if self.cancelCheck.isChecked():
            buttons.append("QMessageBox.Cancel")
        if self.closeCheck.isChecked():
            buttons.append("QMessageBox.Close")
        if self.discardCheck.isChecked():
            buttons.append("QMessageBox.Discard")
        if self.helpCheck.isChecked():
            buttons.append("QMessageBox.Help")
        if self.ignoreCheck.isChecked():
            buttons.append("QMessageBox.Ignore")
        if self.noCheck.isChecked():
            buttons.append("QMessageBox.No")
        if self.notoallCheck.isChecked():
            buttons.append("QMessageBox.NoToAll")
        if self.okCheck.isChecked():
            buttons.append("QMessageBox.Ok")
        if self.openCheck.isChecked():
            buttons.append("QMessageBox.Open")
        if self.resetCheck.isChecked():
            buttons.append("QMessageBox.Reset")
        if self.restoreCheck.isChecked():
            buttons.append("QMessageBox.RestoreDefaults")
        if self.retryCheck.isChecked():
            buttons.append("QMessageBox.Retry")
        if self.saveCheck.isChecked():
            buttons.append("QMessageBox.Save")
        if self.saveallCheck.isChecked():
            buttons.append("QMessageBox.SaveAll")
        if self.yesCheck.isChecked():
            buttons.append("QMessageBox.Yes")
        if self.yestoallCheck.isChecked():
            buttons.append("QMessageBox.YesToAll")
        if len(buttons) == 0:
            return ""
        
        istring2 = istring + indString
        joinstring = ' |{0}{1}'.format(os.linesep, istring2)
        btnCode = ',{0}{1}QMessageBox.StandardButtons('.format(
            os.linesep, istring)
        btnCode += '{0}{1}{2})'.format(
            os.linesep, istring2, joinstring.join(buttons))
        defaultIndex = self.defaultCombo.currentIndex()
        if defaultIndex:
            btnCode += ',{0}{1}{2}'.format(
                os.linesep, istring,
                self.buttonsCodeListText[defaultIndex])
        return btnCode
    
    def getCode(self, indLevel, indString):
        """
        Public method to get the source code.
        
        @param indLevel indentation level (int)
        @param indString string used for indentation (space or tab) (string)
        @return generated code (string)
        """
        # calculate our indentation level and the indentation string
        il = indLevel + 1
        istring = il * indString
        estring = os.linesep + indLevel * indString
        
        # now generate the code
        if self.parentSelf.isChecked():
            parent = "self"
        elif self.parentNone.isChecked():
            parent = "None"
        elif self.parentOther.isChecked():
            parent = self.parentEdit.text()
            if parent == "":
                parent = "None"
        
        resvar = self.eResultVar.text()
        if not resvar:
            resvar = "res"
        
        if self.rAbout.isChecked():
            msgdlg = "QMessageBox.about("
        elif self.rAboutQt.isChecked():
            msgdlg = "QMessageBox.aboutQt("
        elif self.rInformation.isChecked():
            msgdlg = "{0} = QMessageBox.information(".format(resvar)
        elif self.rQuestion.isChecked():
            msgdlg = "{0} = QMessageBox.question(".format(resvar)
        elif self.rWarning.isChecked():
            msgdlg = "{0} = QMessageBox.warning(".format(resvar)
        else:
            msgdlg = "{0} = QMessageBox.critical(".format(resvar)
        
        if self.rAboutQt.isChecked():
            if self.eCaption.text():
                msgdlg += '{0}{1}{2}'.format(os.linesep, istring, parent)
                msgdlg += ',{0}{1}self.tr("{2}")'.format(
                    os.linesep, istring, self.eCaption.text())
            else:
                msgdlg += parent
        else:
            msgdlg += '{0}{1}{2}'.format(os.linesep, istring, parent)
            msgdlg += ',{0}{1}self.tr("{2}")'.format(
                os.linesep, istring, self.eCaption.text())
            msgdlg += ',{0}{1}self.tr("""{2}""")'.format(
                os.linesep, istring, self.eMessage.toPlainText())
            if not self.rAbout.isChecked() and not self.rAboutQt.isChecked():
                msgdlg += self.__getButtonCode(istring, indString)
        msgdlg += '){0}'.format(estring)
        return msgdlg
