# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Printer configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_PrinterPage import Ui_PrinterPage

import Preferences


class PrinterPage(ConfigurationPageBase, Ui_PrinterPage):
    """
    Class implementing the Printer configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(PrinterPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("PrinterPage")
        
        # set initial values
        self.printerNameEdit.setText(
            Preferences.getPrinter("PrinterName"))
        if Preferences.getPrinter("ColorMode"):
            self.printerColorButton.setChecked(True)
        else:
            self.printerGrayscaleButton.setChecked(True)
        if Preferences.getPrinter("FirstPageFirst"):
            self.printFirstPageFirstButton.setChecked(True)
        else:
            self.printFirstPageLastButton.setChecked(True)
        self.printMagnificationSpinBox.setValue(
            Preferences.getPrinter("Magnification"))
        self.printheaderFont = Preferences.getPrinter("HeaderFont")
        self.printheaderFontSample.setFont(self.printheaderFont)
        self.leftMarginSpinBox.setValue(
            Preferences.getPrinter("LeftMargin"))
        self.rightMarginSpinBox.setValue(
            Preferences.getPrinter("RightMargin"))
        self.topMarginSpinBox.setValue(
            Preferences.getPrinter("TopMargin"))
        self.bottomMarginSpinBox.setValue(
            Preferences.getPrinter("BottomMargin"))
        
    def save(self):
        """
        Public slot to save the Printer configuration.
        """
        Preferences.setPrinter(
            "PrinterName",
            self.printerNameEdit.text())
        if self.printerColorButton.isChecked():
            Preferences.setPrinter("ColorMode", 1)
        else:
            Preferences.setPrinter("ColorMode", 0)
        if self.printFirstPageFirstButton.isChecked():
            Preferences.setPrinter("FirstPageFirst", 1)
        else:
            Preferences.setPrinter("FirstPageFirst", 0)
        Preferences.setPrinter(
            "Magnification",
            self.printMagnificationSpinBox.value())
        Preferences.setPrinter("HeaderFont", self.printheaderFont)
        Preferences.setPrinter(
            "LeftMargin",
            self.leftMarginSpinBox.value())
        Preferences.setPrinter(
            "RightMargin",
            self.rightMarginSpinBox.value())
        Preferences.setPrinter(
            "TopMargin",
            self.topMarginSpinBox.value())
        Preferences.setPrinter(
            "BottomMargin",
            self.bottomMarginSpinBox.value())
        
    @pyqtSlot()
    def on_printheaderFontButton_clicked(self):
        """
        Private method used to select the font for the page header.
        """
        self.printheaderFont = \
            self.selectFont(self.printheaderFontSample, self.printheaderFont)
        
    def polishPage(self):
        """
        Public slot to perform some polishing actions.
        """
        self.printheaderFontSample.setFont(self.printheaderFont)
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = PrinterPage()
    return page
