# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the font dialog wizard dialog.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFontDialog

from .Ui_FontDialogWizardDialog import Ui_FontDialogWizardDialog


class FontDialogWizardDialog(QDialog, Ui_FontDialogWizardDialog):
    """
    Class implementing the font dialog wizard dialog.
    
    It displays a dialog for entering the parameters
    for the QFontDialog code generator.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        """
        super(FontDialogWizardDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.bTest = self.buttonBox.addButton(
            self.tr("Test"), QDialogButtonBox.ActionRole)
        
        self.font = None
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
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
        if self.font is None:
            QFontDialog.getFont()
        else:
            QFontDialog.getFont(self.font)
        
    def on_eVariable_textChanged(self, text):
        """
        Private slot to handle the textChanged signal of eVariable.
        
        @param text the new text (string)
        """
        if not text:
            self.bTest.setEnabled(True)
        else:
            self.bTest.setEnabled(False)
        
    @pyqtSlot()
    def on_fontButton_clicked(self):
        """
        Private slot to handle the button press to select a font via a
        font selection dialog.
        """
        if self.font is None:
            font, ok = QFontDialog.getFont()
        else:
            font, ok = QFontDialog.getFont(self.font)
        if ok:
            self.font = font
        else:
            self.font = None
        
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
        
        # generate the code
        resvar = self.eResultVar.text()
        if not resvar:
            resvar = "font"
        title = self.eCaption.text()
        if self.parentSelf.isChecked():
            parent = "self"
        elif self.parentNone.isChecked():
            parent = "None"
        elif self.parentOther.isChecked():
            parent = self.parentEdit.text()
            if parent == "":
                parent = "None"
        
        code = '{0}, ok = QFontDialog.getFont('.format(resvar)
        if self.eVariable.text() or self.font is not None:
            if title or parent != "None":
                code += '{0}{1}'.format(os.linesep, istring)
            if not self.eVariable.text():
                if self.font is not None:
                    code += 'QFont("{0}", {1:d}, {2:d}, {3:d})'.format(
                        self.font.family(), self.font.pointSize(),
                        self.font.weight(), self.font.italic())
            else:
                code += self.eVariable.text()
            if title:
                code += ',{0}{1}{2}'.format(
                    os.linesep, istring, parent)
                code += ',{0}{1}self.tr("{2}")'.format(
                    os.linesep, istring, title)
            elif parent != "None":
                code += ',{0}{1}{2}'.format(
                    os.linesep, istring, parent)
        code += '){0}'.format(estring)
        
        return code
