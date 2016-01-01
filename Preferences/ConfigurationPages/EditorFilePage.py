# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor File Handling configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QListWidgetItem, QInputDialog, QLineEdit
from PyQt5.Qsci import QsciScintilla

from E5Gui import E5MessageBox

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorFilePage import Ui_EditorFilePage

from Utilities import supportedCodecs
import Preferences


class EditorFilePage(ConfigurationPageBase, Ui_EditorFilePage):
    """
    Class implementing the Editor File Handling configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(EditorFilePage, self).__init__()
        self.setupUi(self)
        self.setObjectName("EditorFilePage")
        
        self.__showsOpenFilters = True
        self.openFileFilters = \
            Preferences.getEditor("AdditionalOpenFilters")[:]
        self.saveFileFilters = \
            Preferences.getEditor("AdditionalSaveFilters")[:]
        self.fileFiltersList.addItems(self.openFileFilters)
        
        self.__setDefaultFiltersLists()
        
        self.defaultEncodingComboBox.addItems(sorted(supportedCodecs))
        
        # set initial values
        self.autosaveSlider.setValue(
            Preferences.getEditor("AutosaveInterval"))
        self.createBackupFileCheckBox.setChecked(
            Preferences.getEditor("CreateBackupFile"))
        self.defaultEncodingComboBox.setCurrentIndex(
            self.defaultEncodingComboBox.findText(
                Preferences.getEditor("DefaultEncoding")))
        self.advEncodingCheckBox.setChecked(
            Preferences.getEditor("AdvancedEncodingDetection"))
        self.warnFilesizeSpinBox.setValue(
            Preferences.getEditor("WarnFilesize"))
        self.clearBreakpointsCheckBox.setChecked(
            Preferences.getEditor("ClearBreaksOnClose"))
        self.automaticReopenCheckBox.setChecked(
            Preferences.getEditor("AutoReopen"))
        self.stripWhitespaceCheckBox.setChecked(
            Preferences.getEditor("StripTrailingWhitespace"))
        self.openFilesFilterComboBox.setCurrentIndex(
            self.openFilesFilterComboBox.findText(
                Preferences.getEditor("DefaultOpenFilter")))
        self.saveFilesFilterComboBox.setCurrentIndex(
            self.saveFilesFilterComboBox.findText(
                Preferences.getEditor("DefaultSaveFilter")))
        self.automaticEolConversionCheckBox.setChecked(
            Preferences.getEditor("AutomaticEOLConversion"))
        
        eolMode = Preferences.getEditor("EOLMode")
        if eolMode == QsciScintilla.EolWindows:
            self.crlfRadioButton.setChecked(True)
        elif eolMode == QsciScintilla.EolMac:
            self.crRadioButton.setChecked(True)
        elif eolMode == QsciScintilla.EolUnix:
            self.lfRadioButton.setChecked(True)
        
        self.previewHtmlExtensionsEdit.setText(
            " ".join(Preferences.getEditor("PreviewHtmlFileNameExtensions")))
        self.previewMarkdownExtensionsEdit.setText(
            " ".join(
                Preferences.getEditor("PreviewMarkdownFileNameExtensions")))
        self.previewRestExtensionsEdit.setText(
            " ".join(Preferences.getEditor("PreviewRestFileNameExtensions")))
        self.previewQssExtensionsEdit.setText(
            " ".join(Preferences.getEditor("PreviewQssFileNameExtensions")))
        self.previewRestSphinxCheckBox.setChecked(
            Preferences.getEditor("PreviewRestUseSphinx"))
        
    def save(self):
        """
        Public slot to save the Editor File Handling configuration.
        """
        Preferences.setEditor(
            "AutosaveInterval",
            self.autosaveSlider.value())
        Preferences.setEditor(
            "CreateBackupFile",
            self.createBackupFileCheckBox.isChecked())
        enc = self.defaultEncodingComboBox.currentText()
        if not enc:
            enc = "utf-8"
        Preferences.setEditor("DefaultEncoding", enc)
        Preferences.setEditor(
            "AdvancedEncodingDetection",
            self.advEncodingCheckBox.isChecked())
        Preferences.setEditor(
            "WarnFilesize",
            self.warnFilesizeSpinBox.value())
        Preferences.setEditor(
            "ClearBreaksOnClose",
            self.clearBreakpointsCheckBox.isChecked())
        Preferences.setEditor(
            "AutoReopen",
            self.automaticReopenCheckBox.isChecked())
        Preferences.setEditor(
            "StripTrailingWhitespace",
            self.stripWhitespaceCheckBox.isChecked())
        Preferences.setEditor(
            "DefaultOpenFilter",
            self.openFilesFilterComboBox.currentText())
        Preferences.setEditor(
            "DefaultSaveFilter",
            self.saveFilesFilterComboBox.currentText())
        Preferences.setEditor(
            "AutomaticEOLConversion",
            self.automaticEolConversionCheckBox.isChecked())
        
        if self.crlfRadioButton.isChecked():
            Preferences.setEditor("EOLMode", QsciScintilla.EolWindows)
        elif self.crRadioButton.isChecked():
            Preferences.setEditor("EOLMode", QsciScintilla.EolMac)
        elif self.lfRadioButton.isChecked():
            Preferences.setEditor("EOLMode", QsciScintilla.EolUnix)
        
        self.__extractFileFilters()
        Preferences.setEditor("AdditionalOpenFilters", self.openFileFilters)
        Preferences.setEditor("AdditionalSaveFilters", self.saveFileFilters)
        
        Preferences.setEditor(
            "PreviewHtmlFileNameExtensions",
            [ext.strip() for ext in
             self.previewHtmlExtensionsEdit.text().split()])
        Preferences.setEditor(
            "PreviewMarkdownFileNameExtensions",
            [ext.strip() for ext in
             self.previewMarkdownExtensionsEdit.text().split()])
        Preferences.setEditor(
            "PreviewRestFileNameExtensions",
            [ext.strip() for ext in
             self.previewRestExtensionsEdit.text().split()])
        Preferences.setEditor(
            "PreviewQssFileNameExtensions",
            [ext.strip() for ext in
             self.previewQssExtensionsEdit.text().split()])
        Preferences.setEditor(
            "PreviewRestUseSphinx",
            self.previewRestSphinxCheckBox.isChecked())
    
    def __setDefaultFiltersLists(self, keepSelection=False):
        """
        Private slot to set the default file filter combo boxes.
        
        @param keepSelection flag indicating to keep the current selection
            if possible (boolean)
        """
        if keepSelection:
            selectedOpenFilter = self.openFilesFilterComboBox.currentText()
            selectedSaveFilter = self.saveFilesFilterComboBox.currentText()
        
        import QScintilla.Lexers
        openFileFiltersList = QScintilla.Lexers.getOpenFileFiltersList(
            False, withAdditional=False) + self.openFileFilters
        openFileFiltersList.sort()
        self.openFilesFilterComboBox.clear()
        self.openFilesFilterComboBox.addItems(openFileFiltersList)
        saveFileFiltersList = QScintilla.Lexers.getSaveFileFiltersList(
            False, withAdditional=False) + self.saveFileFilters
        saveFileFiltersList.sort()
        self.saveFilesFilterComboBox.clear()
        self.saveFilesFilterComboBox.addItems(saveFileFiltersList)
        
        if keepSelection:
            self.openFilesFilterComboBox.setCurrentIndex(
                self.openFilesFilterComboBox.findText(selectedOpenFilter))
            self.saveFilesFilterComboBox.setCurrentIndex(
                self.saveFilesFilterComboBox.findText(selectedSaveFilter))
    
    def __extractFileFilters(self):
        """
        Private method to extract the file filters.
        """
        filters = []
        for row in range(self.fileFiltersList.count()):
            filters.append(self.fileFiltersList.item(row).text())
        if self.__showsOpenFilters:
            self.openFileFilters = filters
        else:
            self.saveFileFilters = filters
    
    def __checkFileFilter(self, filter):
        """
        Private method to check a file filter for validity.
        
        @param filter file filter pattern to check (string)
        @return flag indicating validity (boolean)
        """
        if not self.__showsOpenFilters and \
           filter.count("*") != 1:
            E5MessageBox.critical(
                self,
                self.tr("Add File Filter"),
                self.tr("""A Save File Filter must contain exactly one"""
                        """ wildcard pattern. Yours contains {0}.""")
                .format(filter.count("*")))
            return False
        
        if filter.count("*") == 0:
            E5MessageBox.critical(
                self,
                self.tr("Add File Filter"),
                self.tr("""A File Filter must contain at least one"""
                        """ wildcard pattern."""))
            return False
        
        return True
    
    @pyqtSlot()
    def on_addFileFilterButton_clicked(self):
        """
        Private slot to add a file filter to the list.
        """
        filter, ok = QInputDialog.getText(
            self,
            self.tr("Add File Filter"),
            self.tr("Enter the file filter entry:"),
            QLineEdit.Normal)
        if ok and filter:
            if self.__checkFileFilter(filter):
                self.fileFiltersList.addItem(filter)
                self.__extractFileFilters()
                self.__setDefaultFiltersLists(keepSelection=True)
    
    @pyqtSlot()
    def on_editFileFilterButton_clicked(self):
        """
        Private slot called to edit a file filter entry.
        """
        filter = self.fileFiltersList.currentItem().text()
        filter, ok = QInputDialog.getText(
            self,
            self.tr("Add File Filter"),
            self.tr("Enter the file filter entry:"),
            QLineEdit.Normal,
            filter)
        if ok and filter:
            if self.__checkFileFilter(filter):
                self.fileFiltersList.currentItem().setText(filter)
                self.__extractFileFilters()
                self.__setDefaultFiltersLists(keepSelection=True)
    
    @pyqtSlot()
    def on_deleteFileFilterButton_clicked(self):
        """
        Private slot called to delete a file filter entry.
        """
        self.fileFiltersList.takeItem(self.fileFiltersList.currentRow())
        self.__extractFileFilters()
        self.__setDefaultFiltersLists(keepSelection=True)
    
    @pyqtSlot(bool)
    def on_openFiltersButton_toggled(self, checked):
        """
        Private slot to switch the list of file filters.
        
        @param checked flag indicating the check state of the button (boolean)
        """
        self.__extractFileFilters()
        self.__showsOpenFilters = checked
        self.fileFiltersList.clear()
        if checked:
            self.fileFiltersList.addItems(self.openFileFilters)
        else:
            self.fileFiltersList.addItems(self.saveFileFilters)
    
    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def on_fileFiltersList_currentItemChanged(self, current, previous):
        """
        Private slot to set the state of the edit and delete buttons.
        
        @param current new current item (QListWidgetItem)
        @param previous previous current item (QListWidgetItem)
        """
        self.editFileFilterButton.setEnabled(current is not None)
        self.deleteFileFilterButton.setEnabled(current is not None)
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = EditorFilePage()
    return page
