# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Translations Properties dialog.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QListWidgetItem, QDialog, QDialogButtonBox

from E5Gui.E5Completers import E5FileCompleter, E5DirCompleter
from E5Gui import E5FileDialog

from .Ui_TranslationPropertiesDialog import Ui_TranslationPropertiesDialog

import Utilities
import UI.PixmapCache


class TranslationPropertiesDialog(QDialog, Ui_TranslationPropertiesDialog):
    """
    Class implementing the Translations Properties dialog.
    """
    def __init__(self, project, new, parent):
        """
        Constructor
        
        @param project reference to the project object
        @param new flag indicating the generation of a new project
        @param parent parent widget of this dialog (QWidget)
        """
        super(TranslationPropertiesDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.transBinPathButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.transPatternButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.project = project
        self.parent = parent
        
        self.transPatternCompleter = E5FileCompleter(self.transPatternEdit)
        self.transBinPathCompleter = E5DirCompleter(self.transBinPathEdit)
        self.exceptionCompleter = E5FileCompleter(self.exceptionEdit)
        
        self.initFilters()
        if not new:
            self.initDialog()
        
    def initFilters(self):
        """
        Public method to initialize the filters.
        """
        patterns = {
            "SOURCES": [],
            "FORMS": [],
        }
        for pattern, filetype in list(self.project.pdata["FILETYPES"].items()):
            if filetype in patterns:
                patterns[filetype].append(pattern)
        self.filters = self.tr("Source Files ({0});;")\
            .format(" ".join(patterns["SOURCES"]))
        self.filters += self.tr("Forms Files ({0});;")\
            .format(" ".join(patterns["FORMS"]))
        self.filters += self.tr("All Files (*)")
        
    def initDialog(self):
        """
        Public method to initialize the dialogs data.
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        try:
            self.transPatternEdit.setText(Utilities.toNativeSeparators(
                self.project.pdata["TRANSLATIONPATTERN"][0]))
        except IndexError:
            pass
        try:
            self.transBinPathEdit.setText(Utilities.toNativeSeparators(
                self.project.pdata["TRANSLATIONSBINPATH"][0]))
        except IndexError:
            pass
        self.exceptionsList.clear()
        for texcept in self.project.pdata["TRANSLATIONEXCEPTIONS"]:
            if texcept:
                self.exceptionsList.addItem(texcept)
        
    @pyqtSlot()
    def on_transPatternButton_clicked(self):
        """
        Private slot to display a file selection dialog.
        """
        tp = Utilities.fromNativeSeparators(self.transPatternEdit.text())
        if "%language%" in tp:
            tp = tp.split("%language%")[0]
        if not os.path.isabs(tp):
            tp = Utilities.fromNativeSeparators(
                os.path.join(self.project.ppath, tp))
        tsfile = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select translation file"),
            tp,
            "")
        
        if tsfile:
            self.transPatternEdit.setText(self.project.getRelativePath(
                Utilities.toNativeSeparators(tsfile)))
        
    @pyqtSlot(str)
    def on_transPatternEdit_textChanged(self, txt):
        """
        Private slot to check the translation pattern for correctness.
        
        @param txt text of the transPatternEdit lineedit (string)
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            "%language%" in txt)
        
    @pyqtSlot()
    def on_transBinPathButton_clicked(self):
        """
        Private slot to display a directory selection dialog.
        """
        tbp = Utilities.fromNativeSeparators(self.transBinPathEdit.text())
        if not os.path.isabs(tbp):
            tbp = Utilities.fromNativeSeparators(
                os.path.join(self.project.ppath, tbp))
        directory = E5FileDialog.getExistingDirectory(
            self,
            self.tr("Select directory for binary translations"),
            tbp)
        
        if directory:
            self.transBinPathEdit.setText(self.project.getRelativePath(
                Utilities.toNativeSeparators(directory)))
        
    @pyqtSlot()
    def on_deleteExceptionButton_clicked(self):
        """
        Private slot to delete the currently selected entry of the listwidget.
        """
        row = self.exceptionsList.currentRow()
        itm = self.exceptionsList.takeItem(row)
        del itm
        row = self.exceptionsList.currentRow()
        self.on_exceptionsList_currentRowChanged(row)
        
    @pyqtSlot()
    def on_addExceptionButton_clicked(self):
        """
        Private slot to add the shown exception to the listwidget.
        """
        texcept = self.exceptionEdit.text()
        if self.project.ppath == '':
            texcept = texcept.replace(self.parent.getPPath() + os.sep, "")
        else:
            texcept = self.project.getRelativePath(texcept)
        if texcept.endswith(os.sep):
            texcept = texcept[:-1]
        if texcept:
            QListWidgetItem(texcept, self.exceptionsList)
            self.exceptionEdit.clear()
        row = self.exceptionsList.currentRow()
        self.on_exceptionsList_currentRowChanged(row)
        
    @pyqtSlot()
    def on_exceptFileButton_clicked(self):
        """
        Private slot to select a file to exempt from translation.
        """
        texcept = E5FileDialog.getOpenFileName(
            self,
            self.tr("Exempt file from translation"),
            self.project.ppath,
            self.filters)
        if texcept:
            self.exceptionEdit.setText(Utilities.toNativeSeparators(texcept))
        
    @pyqtSlot()
    def on_exceptDirButton_clicked(self):
        """
        Private slot to select a file to exempt from translation.
        """
        texcept = E5FileDialog.getExistingDirectory(
            self,
            self.tr("Exempt directory from translation"),
            self.project.ppath,
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
        if texcept:
            self.exceptionEdit.setText(Utilities.toNativeSeparators(texcept))
        
    def on_exceptionsList_currentRowChanged(self, row):
        """
        Private slot to handle the currentRowChanged signal of the exceptions
        list.
        
        @param row the current row (integer)
        """
        if row == -1:
            self.deleteExceptionButton.setEnabled(False)
        else:
            self.deleteExceptionButton.setEnabled(True)
        
    def on_exceptionEdit_textChanged(self, txt):
        """
        Private slot to handle the textChanged signal of the exception edit.
        
        @param txt the text of the exception edit (string)
        """
        self.addExceptionButton.setEnabled(txt != "")
        
    def storeData(self):
        """
        Public method to store the entered/modified data.
        """
        tp = Utilities.toNativeSeparators(self.transPatternEdit.text())
        if tp:
            tp = self.project.getRelativePath(tp)
            self.project.pdata["TRANSLATIONPATTERN"] = [tp]
            self.project.translationsRoot = tp.split("%language%")[0]
        else:
            self.project.pdata["TRANSLATIONPATTERN"] = []
        tp = Utilities.toNativeSeparators(self.transBinPathEdit.text())
        if tp:
            tp = self.project.getRelativePath(tp)
            self.project.pdata["TRANSLATIONSBINPATH"] = [tp]
        else:
            self.project.pdata["TRANSLATIONSBINPATH"] = []
        exceptList = []
        for i in range(self.exceptionsList.count()):
            exceptList.append(self.exceptionsList.item(i).text())
        self.project.pdata["TRANSLATIONEXCEPTIONS"] = exceptList[:]
