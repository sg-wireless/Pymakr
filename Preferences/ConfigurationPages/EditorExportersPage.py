# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor Exporters configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFontDialog

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorExportersPage import Ui_EditorExportersPage

import Preferences


class EditorExportersPage(ConfigurationPageBase, Ui_EditorExportersPage):
    """
    Class implementing the Editor Typing configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(EditorExportersPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("EditorExportersPage")
        
        # set initial values
        self.pageIds = {}
        self.pageIds[' '] = self.stackedWidget.indexOf(self.emptyPage)
        self.pageIds['HTML'] = self.stackedWidget.indexOf(self.htmlPage)
        self.pageIds['ODT'] = self.stackedWidget.indexOf(self.odtPage)
        self.pageIds['PDF'] = self.stackedWidget.indexOf(self.pdfPage)
        self.pageIds['RTF'] = self.stackedWidget.indexOf(self.rtfPage)
        self.pageIds['TeX'] = self.stackedWidget.indexOf(self.texPage)
        exporters = sorted(list(self.pageIds.keys()))
        for exporter in exporters:
            self.exportersCombo.addItem(exporter, self.pageIds[exporter])
        
        self.pdfFontCombo.addItem(self.tr("Courier"), "Courier")
        self.pdfFontCombo.addItem(self.tr("Helvetica"), "Helvetica")
        self.pdfFontCombo.addItem(self.tr("Times"), "Times")
        
        self.pdfPageSizeCombo.addItem(self.tr("A4"), "A4")
        self.pdfPageSizeCombo.addItem(self.tr("Letter"), "Letter")
        
        # HTML
        self.htmlWysiwygCheckBox.setChecked(
            Preferences.getEditorExporter("HTML/WYSIWYG"))
        self.htmlFoldingCheckBox.setChecked(
            Preferences.getEditorExporter("HTML/Folding"))
        self.htmlStylesCheckBox.setChecked(
            Preferences.getEditorExporter("HTML/OnlyStylesUsed"))
        self.htmlTitleCheckBox.setChecked(
            Preferences.getEditorExporter("HTML/FullPathAsTitle"))
        self.htmlTabsCheckBox.setChecked(
            Preferences.getEditorExporter("HTML/UseTabs"))
        
        # ODT
        self.odtWysiwygCheckBox.setChecked(
            Preferences.getEditorExporter("ODT/WYSIWYG"))
        self.odtStylesCheckBox.setChecked(
            Preferences.getEditorExporter("ODT/OnlyStylesUsed"))
        self.odtTabsCheckBox.setChecked(
            Preferences.getEditorExporter("ODT/UseTabs"))
        
        # PDF
        self.pdfMagnificationSlider.setValue(
            Preferences.getEditorExporter("PDF/Magnification"))
        ind = self.pdfFontCombo.findData(
            Preferences.getEditorExporter("PDF/Font"))
        self.pdfFontCombo.setCurrentIndex(ind)
        ind = self.pdfPageSizeCombo.findData(
            Preferences.getEditorExporter("PDF/PageSize"))
        self.pdfPageSizeCombo.setCurrentIndex(ind)
        self.pdfMarginTopSpin.setValue(
            Preferences.getEditorExporter("PDF/MarginTop"))
        self.pdfMarginBottomSpin.setValue(
            Preferences.getEditorExporter("PDF/MarginBottom"))
        self.pdfMarginLeftSpin.setValue(
            Preferences.getEditorExporter("PDF/MarginLeft"))
        self.pdfMarginRightSpin.setValue(
            Preferences.getEditorExporter("PDF/MarginRight"))
        
        # RTF
        self.rtfWysiwygCheckBox.setChecked(
            Preferences.getEditorExporter("RTF/WYSIWYG"))
        self.rtfTabsCheckBox.setChecked(
            Preferences.getEditorExporter("RTF/UseTabs"))
        self.rtfFont = Preferences.getEditorExporter("RTF/Font")
        self.rtfFontSample.setFont(self.rtfFont)
        
        # TeX
        self.texStylesCheckBox.setChecked(
            Preferences.getEditorExporter("TeX/OnlyStylesUsed"))
        self.texTitleCheckBox.setChecked(
            Preferences.getEditorExporter("TeX/FullPathAsTitle"))
        
        self.on_exportersCombo_activated(' ')
    
    def save(self):
        """
        Public slot to save the Editor Typing configuration.
        """
        # HTML
        Preferences.setEditorExporter(
            "HTML/WYSIWYG",
            self.htmlWysiwygCheckBox.isChecked())
        Preferences.setEditorExporter(
            "HTML/Folding",
            self.htmlFoldingCheckBox.isChecked())
        Preferences.setEditorExporter(
            "HTML/OnlyStylesUsed",
            self.htmlStylesCheckBox.isChecked())
        Preferences.setEditorExporter(
            "HTML/FullPathAsTitle",
            self.htmlTitleCheckBox.isChecked())
        Preferences.setEditorExporter(
            "HTML/UseTabs",
            self.htmlTabsCheckBox.isChecked())
        
        # ODT
        Preferences.setEditorExporter(
            "ODT/WYSIWYG",
            self.odtWysiwygCheckBox.isChecked())
        Preferences.setEditorExporter(
            "ODT/OnlyStylesUsed",
            self.odtStylesCheckBox.isChecked())
        Preferences.setEditorExporter(
            "ODT/UseTabs",
            self.odtTabsCheckBox.isChecked())
        
        # PDF
        Preferences.setEditorExporter(
            "PDF/Magnification",
            self.pdfMagnificationSlider.value())
        Preferences.setEditorExporter(
            "PDF/Font",
            self.pdfFontCombo.itemData(self.pdfFontCombo.currentIndex()))
        Preferences.setEditorExporter(
            "PDF/PageSize",
            self.pdfPageSizeCombo.itemData(
                self.pdfPageSizeCombo.currentIndex()))
        Preferences.setEditorExporter(
            "PDF/MarginTop",
            self.pdfMarginTopSpin.value())
        Preferences.setEditorExporter(
            "PDF/MarginBottom",
            self.pdfMarginBottomSpin.value())
        Preferences.setEditorExporter(
            "PDF/MarginLeft",
            self.pdfMarginLeftSpin.value())
        Preferences.setEditorExporter(
            "PDF/MarginRight",
            self.pdfMarginRightSpin.value())
        
        # RTF
        Preferences.setEditorExporter(
            "RTF/WYSIWYG",
            self.rtfWysiwygCheckBox.isChecked())
        Preferences.setEditorExporter(
            "RTF/UseTabs",
            self.rtfTabsCheckBox.isChecked())
        Preferences.setEditorExporter("RTF/Font", self.rtfFont)
        
        # TeX
        Preferences.setEditorExporter(
            "TeX/OnlyStylesUsed",
            self.texStylesCheckBox.isChecked())
        Preferences.setEditorExporter(
            "TeX/FullPathAsTitle",
            self.texTitleCheckBox.isChecked())
    
    @pyqtSlot(str)
    def on_exportersCombo_activated(self, exporter):
        """
        Private slot to select the page related to the selected exporter.
        
        @param exporter name of the selected exporter (string)
        """
        try:
            index = self.pageIds[exporter]
        except KeyError:
            index = self.pageIds[' ']
        self.stackedWidget.setCurrentIndex(index)
    
    @pyqtSlot()
    def on_rtfFontButton_clicked(self):
        """
        Private method used to select the font for the RTF export.
        """
        font, ok = QFontDialog.getFont(self.rtfFont)
        if ok:
            self.rtfFontSample.setFont(font)
            self.rtfFont = font


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = EditorExportersPage()
    return page
