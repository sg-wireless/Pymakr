# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the file dialog wizard dialog.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, \
    QButtonGroup

from E5Gui.E5Completers import E5FileCompleter, E5DirCompleter

from .Ui_FileDialogWizardDialog import Ui_FileDialogWizardDialog

import Globals


class FileDialogWizardDialog(QDialog, Ui_FileDialogWizardDialog):
    """
    Class implementing the color dialog wizard dialog.
    
    It displays a dialog for entering the parameters
    for the QFileDialog code generator.
    """
    def __init__(self, pyqtVariant, parent=None):
        """
        Constructor
        
        @param pyqtVariant variant of PyQt (integer; 0, 4 or 5)
        @param parent parent widget (QWidget)
        """
        super(FileDialogWizardDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.eStartWithCompleter = E5FileCompleter(self.eStartWith)
        self.eWorkDirCompleter = E5DirCompleter(self.eWorkDir)
        
        self.__pyqtVariant = pyqtVariant
        
        self.__typeButtonsGroup = QButtonGroup(self)
        self.__typeButtonsGroup.setExclusive(True)
        self.__typeButtonsGroup.addButton(self.rOpenFile, 1)
        self.__typeButtonsGroup.addButton(self.rOpenFiles, 2)
        self.__typeButtonsGroup.addButton(self.rSaveFile, 3)
        self.__typeButtonsGroup.addButton(self.rfOpenFile, 11)
        self.__typeButtonsGroup.addButton(self.rfOpenFiles, 12)
        self.__typeButtonsGroup.addButton(self.rfSaveFile, 13)
        self.__typeButtonsGroup.addButton(self.rDirectory, 20)
        self.__typeButtonsGroup.buttonClicked[int].connect(
            self.__toggleInitialFilterAndResult)
        self.__toggleInitialFilterAndResult(1)
        
        self.pyqtComboBox.addItems(["PyQt4", "PyQt5"])
        self.__pyqtVariant = pyqtVariant
        if self.__pyqtVariant == 5:
            self.pyqtComboBox.setCurrentIndex(1)
        else:
            self.pyqtComboBox.setCurrentIndex(0)
        
        self.rSaveFile.toggled[bool].connect(self.__toggleConfirmCheckBox)
        self.rfSaveFile.toggled[bool].connect(self.__toggleConfirmCheckBox)
        self.rDirectory.toggled[bool].connect(self.__toggleGroupsAndTest)
        self.cStartWith.toggled[bool].connect(self.__toggleGroupsAndTest)
        self.cWorkDir.toggled[bool].connect(self.__toggleGroupsAndTest)
        self.cFilters.toggled[bool].connect(self.__toggleGroupsAndTest)
        
        self.bTest = self.buttonBox.addButton(
            self.tr("Test"), QDialogButtonBox.ActionRole)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    def __adjustOptions(self, options):
        """
        Private method to adjust the file dialog options.
        
        @param options file dialog options (QFileDialog.Options)
        @return modified options (QFileDialog.Options)
        """
        if Globals.isLinuxPlatform():
            options |= QFileDialog.DontUseNativeDialog
        return options
    
    @pyqtSlot(str)
    def on_pyqtComboBox_currentIndexChanged(self, txt):
        """
        Private slot to setup the dialog for the selected PyQt variant.
        
        @param txt text of the selected combo box entry (string)
        """
        self.rfOpenFile.setEnabled(txt == "PyQt4")
        self.rfOpenFiles.setEnabled(txt == "PyQt4")
        self.rfSaveFile.setEnabled(txt == "PyQt4")
        
        if txt == "PyQt5":
            if self.rfOpenFile.isChecked():
                self.rOpenFile.setChecked(True)
            elif self.rfOpenFiles.isChecked():
                self.rOpenFiles.setChecked(True)
            elif self.rfSaveFile.isChecked():
                self.rSaveFile.setChecked(True)
        
        self.__pyqtVariant = 5 if txt == "PyQt5" else 4
        
        self.__toggleInitialFilterAndResult(
            self.__typeButtonsGroup.checkedId())
    
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
        if self.rOpenFile.isChecked() or self.rfOpenFile.isChecked():
            if not self.cSymlinks.isChecked():
                options = QFileDialog.Options(QFileDialog.DontResolveSymlinks)
            else:
                options = QFileDialog.Options()
            options = self.__adjustOptions(options)
            if self.rOpenFile.isChecked() and self.__pyqtVariant == 4:
                try:
                    QFileDialog.getOpenFileName(
                        None,
                        self.eCaption.text(),
                        self.eStartWith.text(),
                        self.eFilters.text(),
                        options)
                except TypeError:
                    QFileDialog.getOpenFileName(
                        None,
                        self.eCaption.text(),
                        self.eStartWith.text(),
                        self.eFilters.text(),
                        self.eInitialFilter.text(),
                        options)
            else:
                try:
                    QFileDialog.getOpenFileNameAndFilter(
                        None,
                        self.eCaption.text(),
                        self.eStartWith.text(),
                        self.eFilters.text(),
                        self.eInitialFilter.text(),
                        options)
                except AttributeError:
                    QFileDialog.getOpenFileName(
                        None,
                        self.eCaption.text(),
                        self.eStartWith.text(),
                        self.eFilters.text(),
                        self.eInitialFilter.text(),
                        options)
        elif self.rOpenFiles.isChecked() or self.rfOpenFiles.isChecked():
            if not self.cSymlinks.isChecked():
                options = QFileDialog.Options(QFileDialog.DontResolveSymlinks)
            else:
                options = QFileDialog.Options()
            options = self.__adjustOptions(options)
            if self.rOpenFiles.isChecked() and self.__pyqtVariant == 4:
                try:
                    QFileDialog.getOpenFileNames(
                        None,
                        self.eCaption.text(),
                        self.eStartWith.text(),
                        self.eFilters.text(),
                        options)
                except TypeError:
                    QFileDialog.getOpenFileNames(
                        None,
                        self.eCaption.text(),
                        self.eStartWith.text(),
                        self.eFilters.text(),
                        self.eInitialFilter.text(),
                        options)
            else:
                try:
                    QFileDialog.getOpenFileNamesAndFilter(
                        None,
                        self.eCaption.text(),
                        self.eStartWith.text(),
                        self.eFilters.text(),
                        self.eInitialFilter.text(),
                        options)
                except AttributeError:
                    QFileDialog.getOpenFileNames(
                        None,
                        self.eCaption.text(),
                        self.eStartWith.text(),
                        self.eFilters.text(),
                        self.eInitialFilter.text(),
                        options)
        elif self.rSaveFile.isChecked() or self.rfSaveFile.isChecked():
            if not self.cSymlinks.isChecked():
                options = QFileDialog.Options(QFileDialog.DontResolveSymlinks)
            else:
                options = QFileDialog.Options()
            options = self.__adjustOptions(options)
            if self.rSaveFile.isChecked() and self.__pyqtVariant == 4:
                try:
                    QFileDialog.getSaveFileName(
                        None,
                        self.eCaption.text(),
                        self.eStartWith.text(),
                        self.eFilters.text(),
                        options)
                except TypeError:
                    QFileDialog.getSaveFileName(
                        None,
                        self.eCaption.text(),
                        self.eStartWith.text(),
                        self.eFilters.text(),
                        self.eInitialFilter.text(),
                        options)
            else:
                try:
                    QFileDialog.getSaveFileNameAndFilter(
                        None,
                        self.eCaption.text(),
                        self.eStartWith.text(),
                        self.eFilters.text(),
                        self.eInitialFilter.text(),
                        options)
                except AttributeError:
                    QFileDialog.getSaveFileName(
                        None,
                        self.eCaption.text(),
                        self.eStartWith.text(),
                        self.eFilters.text(),
                        self.eInitialFilter.text(),
                        options)
        elif self.rDirectory.isChecked():
            options = QFileDialog.Options()
            if not self.cSymlinks.isChecked():
                options |= QFileDialog.Options(QFileDialog.DontResolveSymlinks)
            if self.cDirOnly.isChecked():
                options |= QFileDialog.Options(QFileDialog.ShowDirsOnly)
            else:
                options |= QFileDialog.Options(QFileDialog.Option(0))
            options = self.__adjustOptions(options)
            QFileDialog.getExistingDirectory(
                None,
                self.eCaption.text(),
                self.eWorkDir.text(),
                options)
    
    def __toggleConfirmCheckBox(self):
        """
        Private slot to enable/disable the confirmation check box.
        """
        self.cConfirmOverwrite.setEnabled(
            self.rSaveFile.isChecked() or self.rfSaveFile.isChecked())
    
    def __toggleGroupsAndTest(self):
        """
        Private slot to enable/disable certain groups and the test button.
        """
        if self.rDirectory.isChecked():
            self.filePropertiesGroup.setEnabled(False)
            self.dirPropertiesGroup.setEnabled(True)
            self.bTest.setDisabled(self.cWorkDir.isChecked())
        else:
            self.filePropertiesGroup.setEnabled(True)
            self.dirPropertiesGroup.setEnabled(False)
            self.bTest.setDisabled(
                self.cStartWith.isChecked() or self.cFilters.isChecked())
    
    def __toggleInitialFilterAndResult(self, id):
        """
        Private slot to enable/disable the initial filter elements and the
        results entries.
        
        @param id id of the clicked button (integer)
        """
        if (self.__pyqtVariant == 4 and id in [11, 12, 13]) or \
                (self.__pyqtVariant == 5 and id in [1, 2, 3]):
            enable = True
        else:
            enable = False
        self.lInitialFilter.setEnabled(enable)
        self.eInitialFilter.setEnabled(enable)
        self.cInitialFilter.setEnabled(enable)
        
        self.lFilterVariable.setEnabled(enable)
        self.eFilterVariable.setEnabled(enable)
    
    def getCode(self, indLevel, indString):
        """
        Public method to get the source code for Qt4 and Qt5.
        
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
        
        # prepare the result variables
        nameVariable = self.eNameVariable.text()
        if not nameVariable:
            if self.__typeButtonsGroup.checkedButton() in [
                    self.rOpenFile, self.rfOpenFile,
                    self.rSaveFile, self.rfSaveFile]:
                nameVariable = "fileName"
            elif self.__typeButtonsGroup.checkedButton() in [
                    self.rOpenFiles, self.rfOpenFiles]:
                nameVariable = "fileNames"
            elif self.__typeButtonsGroup.checkedButton() == self.rDirectory:
                nameVariable = "dirName"
            else:
                nameVariable = "res"
        filterVariable = self.eFilterVariable.text()
        if not filterVariable:
            if (self.__pyqtVariant == 4 and
                self.__typeButtonsGroup.checkedButton() in [
                    self.rfOpenFile, self.rfOpenFiles, self.rfSaveFile]) or \
                    (self.__pyqtVariant == 5 and
                        self.__typeButtonsGroup.checkedButton() in [
                            self.rOpenFile, self.rOpenFiles, self.rSaveFile]):
                filterVariable = ", selectedFilter"
            else:
                filterVariable = ""
        
        code = '{0}{1} = QFileDialog.'.format(nameVariable, filterVariable)
        if self.rOpenFile.isChecked() or self.rfOpenFile.isChecked():
            if self.rOpenFile.isChecked():
                code += 'getOpenFileName({0}{1}'.format(os.linesep, istring)
            else:
                code += 'getOpenFileNameAndFilter({0}{1}'.format(
                    os.linesep, istring)
            code += '{0},{1}{2}'.format(parent, os.linesep, istring)
            if not self.eCaption.text():
                code += '"",{0}{1}'.format(os.linesep, istring)
            else:
                code += 'self.tr("{0}"),{1}{2}'.format(
                    self.eCaption.text(), os.linesep, istring)
            if not self.eStartWith.text():
                code += '"",{0}{1}'.format(os.linesep, istring)
            else:
                if self.cStartWith.isChecked():
                    fmt = '{0},{1}{2}'
                else:
                    fmt = 'self.tr("{0}"),{1}{2}'
                code += fmt.format(self.eStartWith.text(), os.linesep, istring)
            if self.eFilters.text() == "":
                code += '""'
            else:
                if self.cFilters.isChecked():
                    fmt = '{0}'
                else:
                    fmt = 'self.tr("{0}")'
                code += fmt.format(self.eFilters.text())
            if self.rfOpenFile.isChecked() or self.__pyqtVariant == 5:
                if self.eInitialFilter.text() == "":
                    filter = "None"
                else:
                    if self.cInitialFilter.isChecked():
                        fmt = '{0}'
                    else:
                        fmt = 'self.tr("{0}")'
                    filter = fmt.format(self.eInitialFilter.text())
                code += ',{0}{1}{2}'.format(os.linesep, istring, filter)
            if not self.cSymlinks.isChecked():
                code += \
                    ',{0}{1}QFileDialog.Options(' \
                    'QFileDialog.DontResolveSymlinks)' \
                    .format(os.linesep, istring)
            code += '){0}'.format(estring)
        elif self.rOpenFiles.isChecked() or self.rfOpenFiles.isChecked():
            if self.rOpenFiles.isChecked():
                code += 'getOpenFileNames({0}{1}'.format(os.linesep, istring)
            else:
                code += 'getOpenFileNamesAndFilter({0}{1}'.format(
                    os.linesep, istring)
            code += '{0},{1}{2}'.format(parent, os.linesep, istring)
            if not self.eCaption.text():
                code += '"",{0}{1}'.format(os.linesep, istring)
            else:
                code += 'self.tr("{0}"),{1}{2}'.format(
                    self.eCaption.text(), os.linesep, istring)
            if not self.eStartWith.text():
                code += '"",{0}{1}'.format(os.linesep, istring)
            else:
                if self.cStartWith.isChecked():
                    fmt = '{0},{1}{2}'
                else:
                    fmt = 'self.tr("{0}"),{1}{2}'
                code += fmt.format(self.eStartWith.text(), os.linesep, istring)
            if not self.eFilters.text():
                code += '""'
            else:
                if self.cFilters.isChecked():
                    fmt = '{0}'
                else:
                    fmt = 'self.tr("{0}")'
                code += fmt.format(self.eFilters.text())
            if self.rfOpenFiles.isChecked() or self.__pyqtVariant == 5:
                if self.eInitialFilter.text() == "":
                    filter = "None"
                else:
                    if self.cInitialFilter.isChecked():
                        fmt = '{0}'
                    else:
                        fmt = 'self.tr("{0}")'
                    filter = fmt.format(self.eInitialFilter.text())
                code += ',{0}{1}{2}'.format(os.linesep, istring, filter)
            if not self.cSymlinks.isChecked():
                code += \
                    ',{0}{1}QFileDialog.Options(' \
                    'QFileDialog.DontResolveSymlinks)' \
                    .format(os.linesep, istring)
            code += '){0}'.format(estring)
        elif self.rSaveFile.isChecked() or self.rfSaveFile.isChecked():
            if self.rSaveFile.isChecked():
                code += 'getSaveFileName({0}{1}'.format(os.linesep, istring)
            else:
                code += 'getSaveFileNameAndFilter({0}{1}'.format(
                    os.linesep, istring)
            code += '{0},{1}{2}'.format(parent, os.linesep, istring)
            if not self.eCaption.text():
                code += '"",{0}{1}'.format(os.linesep, istring)
            else:
                code += 'self.tr("{0}"),{1}{2}'.format(
                    self.eCaption.text(), os.linesep, istring)
            if not self.eStartWith.text():
                code += '"",{0}{1}'.format(os.linesep, istring)
            else:
                if self.cStartWith.isChecked():
                    fmt = '{0},{1}{2}'
                else:
                    fmt = 'self.tr("{0}"),{1}{2}'
                code += fmt.format(self.eStartWith.text(), os.linesep, istring)
            if not self.eFilters.text():
                code += '""'
            else:
                if self.cFilters.isChecked():
                    fmt = '{0}'
                else:
                    fmt = 'self.tr("{0}")'
                code += fmt.format(self.eFilters.text())
            if self.rfSaveFile.isChecked() or self.__pyqtVariant == 5:
                if self.eInitialFilter.text() == "":
                    filter = "None"
                else:
                    if self.cInitialFilter.isChecked():
                        fmt = '{0}'
                    else:
                        fmt = 'self.tr("{0}")'
                    filter = fmt.format(self.eInitialFilter.text())
                code += ',{0}{1}{2}'.format(os.linesep, istring, filter)
            if (not self.cSymlinks.isChecked()) or \
               (not self.cConfirmOverwrite.isChecked()):
                code += ',{0}{1}QFileDialog.Options('.format(
                    os.linesep, istring)
                if not self.cSymlinks.isChecked():
                    code += 'QFileDialog.DontResolveSymlinks'
                if (not self.cSymlinks.isChecked()) and \
                   (not self.cConfirmOverwrite.isChecked()):
                    code += ' | '
                if not self.cConfirmOverwrite.isChecked():
                    code += 'QFileDialog.DontConfirmOverwrite'
                code += ')'
            code += '){0}'.format(estring)
        elif self.rDirectory.isChecked():
            code += 'getExistingDirectory({0}{1}'.format(os.linesep, istring)
            code += '{0},{1}{2}'.format(parent, os.linesep, istring)
            if not self.eCaption.text():
                code += '"",{0}{1}'.format(os.linesep, istring)
            else:
                code += 'self.tr("{0}"),{1}{2}'.format(
                    self.eCaption.text(), os.linesep, istring)
            if not self.eWorkDir.text():
                code += '""'
            else:
                if self.cWorkDir.isChecked():
                    fmt = '{0}'
                else:
                    fmt = 'self.tr("{0}")'
                code += fmt.format(self.eWorkDir.text())
            code += ',{0}{1}QFileDialog.Options('.format(os.linesep, istring)
            if not self.cSymlinks.isChecked():
                code += 'QFileDialog.DontResolveSymlinks | '
            if self.cDirOnly.isChecked():
                code += 'QFileDialog.ShowDirsOnly'
            else:
                code += 'QFileDialog.Option(0)'
            code += ')){0}'.format(estring)
            
        return code
