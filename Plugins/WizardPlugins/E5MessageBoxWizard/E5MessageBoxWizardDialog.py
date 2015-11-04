# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the eric6 message box wizard dialog.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QAbstractButton

from E5Gui import E5MessageBox

from .Ui_E5MessageBoxWizardDialog import Ui_E5MessageBoxWizardDialog


class E5MessageBoxWizardDialog(QDialog, Ui_E5MessageBoxWizardDialog):
    """
    Class implementing the eric6 message box wizard dialog.
    
    It displays a dialog for entering the parameters
    for the E5MessageBox code generator.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(E5MessageBoxWizardDialog, self).__init__(parent)
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
            E5MessageBox.NoButton,
            E5MessageBox.Abort,
            E5MessageBox.Apply,
            E5MessageBox.Cancel,
            E5MessageBox.Close,
            E5MessageBox.Discard,
            E5MessageBox.Help,
            E5MessageBox.Ignore,
            E5MessageBox.No,
            E5MessageBox.NoToAll,
            E5MessageBox.Ok,
            E5MessageBox.Open,
            E5MessageBox.Reset,
            E5MessageBox.RestoreDefaults,
            E5MessageBox.Retry,
            E5MessageBox.Save,
            E5MessageBox.SaveAll,
            E5MessageBox.Yes,
            E5MessageBox.YesToAll,
        ]
        self.buttonsCodeListText = [
            "E5MessageBox.NoButton",
            "E5MessageBox.Abort",
            "E5MessageBox.Apply",
            "E5MessageBox.Cancel",
            "E5MessageBox.Close",
            "E5MessageBox.Discard",
            "E5MessageBox.Help",
            "E5MessageBox.Ignore",
            "E5MessageBox.No",
            "E5MessageBox.NoToAll",
            "E5MessageBox.Ok",
            "E5MessageBox.Open",
            "E5MessageBox.Reset",
            "E5MessageBox.RestoreDefaults",
            "E5MessageBox.Retry",
            "E5MessageBox.Save",
            "E5MessageBox.SaveAll",
            "E5MessageBox.Yes",
            "E5MessageBox.YesToAll",
        ]
        
        self.defaultCombo.addItems(self.buttonsList)
        
        self.bTest = self.buttonBox.addButton(
            self.tr("Test"), QDialogButtonBox.ActionRole)
        
        self.__enabledGroups()

    def __enabledGroups(self):
        """
        Private method to enable/disable some group boxes.
        """
        self.standardButtons.setEnabled(
            self.rInformation.isChecked() or
            self.rQuestion.isChecked() or
            self.rWarning.isChecked() or
            self.rCritical.isChecked() or
            self.rStandard.isChecked()
        )
        
        self.defaultButton.setEnabled(
            self.rInformation.isChecked() or
            self.rQuestion.isChecked() or
            self.rWarning.isChecked() or
            self.rCritical.isChecked()
        )
        
        self.iconBox.setEnabled(
            self.rYesNo.isChecked() or
            self.rRetryAbort.isChecked() or
            self.rStandard.isChecked()
        )
        
        self.bTest.setEnabled(not self.rStandard.isChecked())
        
        self.eMessage.setEnabled(not self.rAboutQt.isChecked())
    
    @pyqtSlot(bool)
    def on_rInformation_toggled(self, on):
        """
        Private slot to handle the toggled signal of the rInformation
        radio button.
        
        @param on toggle state (boolean) (ignored)
        """
        self.__enabledGroups()
    
    @pyqtSlot(bool)
    def on_rQuestion_toggled(self, on):
        """
        Private slot to handle the toggled signal of the rQuestion
        radio button.
        
        @param on toggle state (boolean) (ignored)
        """
        self.__enabledGroups()
    
    @pyqtSlot(bool)
    def on_rWarning_toggled(self, on):
        """
        Private slot to handle the toggled signal of the rWarning
        radio button.
        
        @param on toggle state (boolean) (ignored)
        """
        self.__enabledGroups()
    
    @pyqtSlot(bool)
    def on_rCritical_toggled(self, on):
        """
        Private slot to handle the toggled signal of the rCritical
        radio button.
        
        @param on toggle state (boolean) (ignored)
        """
        self.__enabledGroups()
    
    @pyqtSlot(bool)
    def on_rYesNo_toggled(self, on):
        """
        Private slot to handle the toggled signal of the rYesNo
        radio button.
        
        @param on toggle state (boolean) (ignored)
        """
        self.__enabledGroups()
    
    @pyqtSlot(bool)
    def on_rRetryAbort_toggled(self, on):
        """
        Private slot to handle the toggled signal of the rRetryAbort
        radio button.
        
        @param on toggle state (boolean) (ignored)
        """
        self.__enabledGroups()
    
    @pyqtSlot(bool)
    def on_rOkToClearData_toggled(self, on):
        """
        Private slot to handle the toggled signal of the rOkToClearData
        radio button.
        
        @param on toggle state (boolean) (ignored)
        """
        self.__enabledGroups()
    
    @pyqtSlot(bool)
    def on_rAbout_toggled(self, on):
        """
        Private slot to handle the toggled signal of the rAbout
        radio button.
        
        @param on toggle state (boolean) (ignored)
        """
        self.__enabledGroups()
    
    @pyqtSlot(bool)
    def on_rAboutQt_toggled(self, on):
        """
        Private slot to handle the toggled signal of the rAboutQt
        radio button.
        
        @param on toggle state (boolean) (ignored)
        """
        self.__enabledGroups()
    
    @pyqtSlot(bool)
    def on_rStandard_toggled(self, on):
        """
        Private slot to handle the toggled signal of the rStandard
        radio button.
        
        @param on toggle state (boolean) (ignored)
        """
        self.__enabledGroups()
    
    @pyqtSlot(QAbstractButton)
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
            E5MessageBox.about(
                None,
                self.eCaption.text(),
                self.eMessage.toPlainText()
            )
        elif self.rAboutQt.isChecked():
            E5MessageBox.aboutQt(
                None, self.eCaption.text()
            )
        elif self.rInformation.isChecked() or \
            self.rQuestion.isChecked() or \
            self.rWarning.isChecked() or \
                self.rCritical.isChecked():
            buttons = E5MessageBox.NoButton
            if self.abortCheck.isChecked():
                buttons |= E5MessageBox.Abort
            if self.applyCheck.isChecked():
                buttons |= E5MessageBox.Apply
            if self.cancelCheck.isChecked():
                buttons |= E5MessageBox.Cancel
            if self.closeCheck.isChecked():
                buttons |= E5MessageBox.Close
            if self.discardCheck.isChecked():
                buttons |= E5MessageBox.Discard
            if self.helpCheck.isChecked():
                buttons |= E5MessageBox.Help
            if self.ignoreCheck.isChecked():
                buttons |= E5MessageBox.Ignore
            if self.noCheck.isChecked():
                buttons |= E5MessageBox.No
            if self.notoallCheck.isChecked():
                buttons |= E5MessageBox.NoToAll
            if self.okCheck.isChecked():
                buttons |= E5MessageBox.Ok
            if self.openCheck.isChecked():
                buttons |= E5MessageBox.Open
            if self.resetCheck.isChecked():
                buttons |= E5MessageBox.Reset
            if self.restoreCheck.isChecked():
                buttons |= E5MessageBox.RestoreDefaults
            if self.retryCheck.isChecked():
                buttons |= E5MessageBox.Retry
            if self.saveCheck.isChecked():
                buttons |= E5MessageBox.Save
            if self.saveallCheck.isChecked():
                buttons |= E5MessageBox.SaveAll
            if self.yesCheck.isChecked():
                buttons |= E5MessageBox.Yes
            if self.yestoallCheck.isChecked():
                buttons |= E5MessageBox.YesToAll
            if buttons == E5MessageBox.NoButton:
                buttons = E5MessageBox.Ok
            
            defaultButton = self.buttonsCodeListBinary[
                self.defaultCombo.currentIndex()]
            
            if self.rInformation.isChecked():
                E5MessageBox.information(
                    self,
                    self.eCaption.text(),
                    self.eMessage.toPlainText(),
                    E5MessageBox.StandardButtons(buttons),
                    defaultButton
                )
            elif self.rQuestion.isChecked():
                E5MessageBox.question(
                    self,
                    self.eCaption.text(),
                    self.eMessage.toPlainText(),
                    E5MessageBox.StandardButtons(buttons),
                    defaultButton
                )
            elif self.rWarning.isChecked():
                E5MessageBox.warning(
                    self,
                    self.eCaption.text(),
                    self.eMessage.toPlainText(),
                    E5MessageBox.StandardButtons(buttons),
                    defaultButton
                )
            elif self.rCritical.isChecked():
                E5MessageBox.critical(
                    self,
                    self.eCaption.text(),
                    self.eMessage.toPlainText(),
                    E5MessageBox.StandardButtons(buttons),
                    defaultButton
                )
        elif self.rYesNo.isChecked() or \
                self.rRetryAbort.isChecked():
            if self.iconInformation.isChecked():
                icon = E5MessageBox.Information
            elif self.iconQuestion.isChecked():
                icon = E5MessageBox.Question
            elif self.iconWarning.isChecked():
                icon = E5MessageBox.Warning
            elif self.iconCritical.isChecked():
                icon = E5MessageBox.Critical
            
            if self.rYesNo.isChecked():
                E5MessageBox.yesNo(
                    self,
                    self.eCaption.text(),
                    self.eMessage.toPlainText(),
                    icon=icon,
                    yesDefault=self.yesDefaultCheck.isChecked()
                )
            elif self.rRetryAbort.isChecked():
                E5MessageBox.retryAbort(
                    self,
                    self.eCaption.text(),
                    self.eMessage.toPlainText(),
                    icon=icon
                )
        elif self.rOkToClearData.isChecked():
            E5MessageBox.okToClearData(
                self,
                self.eCaption.text(),
                self.eMessage.toPlainText(),
                lambda: True
            )
    
    def __getStandardButtonCode(self, istring, indString, withIntro=True):
        """
        Private method to generate the button code for the standard buttons.
        
        @param istring indentation string (string)
        @param indString string used for indentation (space or tab) (string)
        @keyparam withIntro flag indicating to generate a first line
            with introductory text (boolean)
        @return the button code (string)
        """
        buttons = []
        if self.abortCheck.isChecked():
            buttons.append("E5MessageBox.Abort")
        if self.applyCheck.isChecked():
            buttons.append("E5MessageBox.Apply")
        if self.cancelCheck.isChecked():
            buttons.append("E5MessageBox.Cancel")
        if self.closeCheck.isChecked():
            buttons.append("E5MessageBox.Close")
        if self.discardCheck.isChecked():
            buttons.append("E5MessageBox.Discard")
        if self.helpCheck.isChecked():
            buttons.append("E5MessageBox.Help")
        if self.ignoreCheck.isChecked():
            buttons.append("E5MessageBox.Ignore")
        if self.noCheck.isChecked():
            buttons.append("E5MessageBox.No")
        if self.notoallCheck.isChecked():
            buttons.append("E5MessageBox.NoToAll")
        if self.okCheck.isChecked():
            buttons.append("E5MessageBox.Ok")
        if self.openCheck.isChecked():
            buttons.append("E5MessageBox.Open")
        if self.resetCheck.isChecked():
            buttons.append("E5MessageBox.Reset")
        if self.restoreCheck.isChecked():
            buttons.append("E5MessageBox.RestoreDefaults")
        if self.retryCheck.isChecked():
            buttons.append("E5MessageBox.Retry")
        if self.saveCheck.isChecked():
            buttons.append("E5MessageBox.Save")
        if self.saveallCheck.isChecked():
            buttons.append("E5MessageBox.SaveAll")
        if self.yesCheck.isChecked():
            buttons.append("E5MessageBox.Yes")
        if self.yestoallCheck.isChecked():
            buttons.append("E5MessageBox.YesToAll")
        if len(buttons) == 0:
            return ""
        
        istring2 = istring + indString
        joinstring = ' |{0}{1}'.format(os.linesep, istring2)
        if withIntro:
            btnCode = ',{0}{1}E5MessageBox.StandardButtons('.format(
                os.linesep, istring)
        else:
            btnCode = 'E5MessageBox.StandardButtons('
        btnCode += '{0}{1}{2})'.format(
            os.linesep, istring2, joinstring.join(buttons))
        
        return btnCode
    
    def __getDefaultButtonCode(self, istring):
        """
        Private method to generate the button code for the default button.
        
        @param istring indentation string (string)
        @return the button code (string)
        """
        btnCode = ""
        defaultIndex = self.defaultCombo.currentIndex()
        if defaultIndex:
            btnCode = ',{0}{1}{2}'.format(
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
        
        if self.iconInformation.isChecked():
            icon = "E5MessageBox.Information"
        elif self.iconQuestion.isChecked():
            icon = "E5MessageBox.Question"
        elif self.iconWarning.isChecked():
            icon = "E5MessageBox.Warning"
        elif self.iconCritical.isChecked():
            icon = "E5MessageBox.Critical"
        
        if not self.rStandard.isChecked():
            resvar = self.eResultVar.text()
            if not resvar:
                resvar = "res"
            
            if self.rAbout.isChecked():
                msgdlg = "E5MessageBox.about({0}".format(os.linesep)
            elif self.rAboutQt.isChecked():
                msgdlg = "E5MessageBox.aboutQt({0}".format(os.linesep)
            elif self.rInformation.isChecked():
                msgdlg = "{0} = E5MessageBox.information({1}".format(
                    resvar, os.linesep)
            elif self.rQuestion.isChecked():
                msgdlg = "{0} = E5MessageBox.question({1}".format(
                    resvar, os.linesep)
            elif self.rWarning.isChecked():
                msgdlg = "{0} = E5MessageBox.warning({1}".format(
                    resvar, os.linesep)
            elif self.rCritical.isChecked():
                msgdlg = "{0} = E5MessageBox.critical({1}".format(
                    resvar, os.linesep)
            elif self.rYesNo.isChecked():
                msgdlg = "{0} = E5MessageBox.yesNo({1}".format(
                    resvar, os.linesep)
            elif self.rRetryAbort.isChecked():
                msgdlg = "{0} = E5MessageBox.retryAbort({1}".format(
                    resvar, os.linesep)
            elif self.rOkToClearData.isChecked():
                msgdlg = "{0} = E5MessageBox.okToClearData({1}".format(
                    resvar, os.linesep)
            
            msgdlg += '{0}{1},{2}'.format(istring, parent, os.linesep)
            msgdlg += '{0}self.tr("{1}")'.format(
                istring, self.eCaption.text())
            
            if not self.rAboutQt.isChecked():
                msgdlg += ',{0}{1}self.tr("""{2}""")'.format(
                    os.linesep, istring, self.eMessage.toPlainText())
            
            if self.rInformation.isChecked() or \
               self.rQuestion.isChecked() or \
               self.rWarning.isChecked() or \
               self.rCritical.isChecked():
                msgdlg += self.__getStandardButtonCode(istring, indString)
                msgdlg += self.__getDefaultButtonCode(istring)
            elif self.rYesNo.isChecked():
                if not self.iconQuestion.isChecked():
                    msgdlg += ',{0}{1}icon={2}'.format(
                        os.linesep, istring, icon)
                if self.yesDefaultCheck.isChecked():
                    msgdlg += ',{0}{1}yesDefault=True'.format(
                        os.linesep, istring)
            elif self.rRetryAbort.isChecked():
                if not self.iconQuestion.isChecked():
                    msgdlg += ',{0}{1}icon={2}'.format(
                        os.linesep, istring, icon)
            elif self.rOkToClearData.isChecked():
                saveFunc = self.saveFuncEdit.text()
                if saveFunc == "":
                    saveFunc = "lambda: True"
                msgdlg += ',{0}{1}{2}'.format(os.linesep, istring, saveFunc)
        else:
            resvar = self.eResultVar.text()
            if not resvar:
                resvar = "dlg"
            
            msgdlg = "{0} = E5MessageBox.E5MessageBox({1}".format(
                resvar, os.linesep)
            msgdlg += '{0}{1},{2}'.format(istring, icon, os.linesep)
            msgdlg += '{0}self.tr("{1}")'.format(
                istring, self.eCaption.text())
            msgdlg += ',{0}{1}self.tr("""{2}""")'.format(
                os.linesep, istring, self.eMessage.toPlainText())
            if self.modalCheck.isChecked():
                msgdlg += ',{0}{1}modal=True'.format(os.linesep, istring)
            btnCode = self.__getStandardButtonCode(
                istring, indString, withIntro=False)
            if btnCode:
                msgdlg += ',{0}{1}buttons={2}'.format(
                    os.linesep, istring, btnCode)
            if not self.parentNone.isChecked():
                msgdlg += ',{0}{1}parent={2}'.format(
                    os.linesep, istring, parent)
        
        msgdlg += '){0}'.format(estring)
        return msgdlg
