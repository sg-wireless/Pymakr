# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the input dialog wizard dialog.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QLineEdit, QDialog, QInputDialog, QDialogButtonBox

from .Ui_InputDialogWizardDialog import Ui_InputDialogWizardDialog


class InputDialogWizardDialog(QDialog, Ui_InputDialogWizardDialog):
    """
    Class implementing the input dialog wizard dialog.
    
    It displays a dialog for entering the parameters
    for the QInputDialog code generator.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        """
        super(InputDialogWizardDialog, self).__init__(parent)
        self.setupUi(self)
        
        # set the validators for the double line edots
        self.eDoubleDefault.setValidator(
            QDoubleValidator(-2147483647, 2147483647, 99, self.eDoubleDefault))
        self.eDoubleFrom.setValidator(
            QDoubleValidator(-2147483647, 2147483647, 99, self.eDoubleFrom))
        self.eDoubleTo.setValidator(
            QDoubleValidator(-2147483647, 2147483647, 99, self.eDoubleTo))
        
        self.bTest = self.buttonBox.addButton(
            self.tr("Test"), QDialogButtonBox.ActionRole)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    @pyqtSlot(bool)
    def on_rItem_toggled(self, checked):
        """
        Private slot to perform actions dependant on the item type selection.
        
        @param checked flag indicating the checked state (boolean)
        """
        self.bTest.setEnabled(not checked)
        
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
        if self.rText.isChecked():
            if self.rEchoNormal.isChecked():
                echomode = QLineEdit.Normal
            elif self.rEchoNoEcho.isChecked():
                echomode = QLineEdit.NoEcho
            else:
                echomode = QLineEdit.Password
            QInputDialog.getText(
                None,
                self.eCaption.text(),
                self.eLabel.text(),
                echomode,
                self.eTextDefault.text())
        elif self.rInteger.isChecked():
            QInputDialog.getInt(
                None,
                self.eCaption.text(),
                self.eLabel.text(),
                self.sIntDefault.value(),
                self.sIntFrom.value(),
                self.sIntTo.value(),
                self.sIntStep.value())
        elif self.rDouble.isChecked():
            try:
                doubleDefault = float(self.eDoubleDefault.text())
            except ValueError:
                doubleDefault = 0
            try:
                doubleFrom = float(self.eDoubleFrom.text())
            except ValueError:
                doubleFrom = -2147483647
            try:
                doubleTo = float(self.eDoubleTo.text())
            except ValueError:
                doubleTo = 2147483647
            QInputDialog.getDouble(
                None,
                self.eCaption.text(),
                self.eLabel.text(),
                doubleDefault,
                doubleFrom,
                doubleTo,
                self.sDoubleDecimals.value())
        
    def getCode(self, indLevel, indString):
        """
        Public method to get the source code for Qt4/Qt5.
        
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
            resvar = "result"
        code = '{0}, ok = QInputDialog.'.format(resvar)
        if self.rText.isChecked():
            code += 'getText({0}{1}'.format(os.linesep, istring)
            code += '{0},{1}{2}'.format(parent, os.linesep, istring)
            code += 'self.tr("{0}"),{1}{2}'.format(
                self.eCaption.text(), os.linesep, istring)
            code += 'self.tr("{0}"),{1}{2}'.format(
                self.eLabel.text(), os.linesep, istring)
            if self.rEchoNormal.isChecked():
                code += 'QLineEdit.Normal'
            elif self.rEchoNoEcho.isChecked():
                code += 'QLineEdit.NoEcho'
            else:
                code += 'QLineEdit.Password'
            if self.eTextDefault.text():
                code += ',{0}{1}self.tr("{2}")'.format(
                    os.linesep, istring, self.eTextDefault.text())
            code += '){0}'.format(estring)
        elif self.rInteger.isChecked():
            code += 'getInt({0}{1}'.format(os.linesep, istring)
            code += '{0},{1}{2}'.format(parent, os.linesep, istring)
            code += 'self.tr("{0}"),{1}{2}'.format(
                self.eCaption.text(), os.linesep, istring)
            code += 'self.tr("{0}"),{1}{2}'.format(
                self.eLabel.text(), os.linesep, istring)
            code += '{0:d}, {1:d}, {2:d}, {3:d}){4}'.format(
                self.sIntDefault.value(), self.sIntFrom.value(),
                self.sIntTo.value(), self.sIntStep.value(), estring)
        elif self.rDouble.isChecked():
            try:
                doubleDefault = float(self.eDoubleDefault.text())
            except ValueError:
                doubleDefault = 0
            try:
                doubleFrom = float(self.eDoubleFrom.text())
            except ValueError:
                doubleFrom = -2147483647
            try:
                doubleTo = float(self.eDoubleTo.text())
            except ValueError:
                doubleTo = 2147483647
            code += 'getDouble({0}{1}'.format(os.linesep, istring)
            code += '{0},{1}{2}'.format(parent, os.linesep, istring)
            code += 'self.tr("{0}"),{1}{2}'.format(
                self.eCaption.text(), os.linesep, istring)
            code += 'self.tr("{0}"),{1}{2}'.format(
                self.eLabel.text(), os.linesep, istring)
            code += '{0}, {1}, {2}, {3:d}){4}'.format(
                doubleDefault, doubleFrom, doubleTo,
                self.sDoubleDecimals.value(), estring)
        elif self.rItem.isChecked():
            code += 'getItem({0}{1}'.format(os.linesep, istring)
            code += '{0},{1}{2}'.format(parent, os.linesep, istring)
            code += 'self.tr("{0}"),{1}{2}'.format(
                self.eCaption.text(), os.linesep, istring)
            code += 'self.tr("{0}"),{1}{2}'.format(
                self.eLabel.text(), os.linesep, istring)
            code += '{0},{1}{2}'.format(
                self.eVariable.text(), os.linesep, istring)
            code += '{0:d}, {1}){2}'.format(
                self.sCurrentItem.value(), self.cEditable.isChecked(), estring)
            
        return code
