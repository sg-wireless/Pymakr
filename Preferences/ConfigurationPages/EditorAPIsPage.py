# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor APIs configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QDir, pyqtSlot, QFileInfo
from PyQt5.QtWidgets import QInputDialog

from E5Gui.E5Application import e5App
from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5FileDialog, E5MessageBox

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorAPIsPage import Ui_EditorAPIsPage

import Preferences
import Utilities
import UI.PixmapCache


class EditorAPIsPage(ConfigurationPageBase, Ui_EditorAPIsPage):
    """
    Class implementing the Editor APIs configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(EditorAPIsPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("EditorAPIsPage")
        
        self.apiFileButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.prepareApiButton.setText(self.tr("Compile APIs"))
        self.__currentAPI = None
        self.__inPreparation = False
        
        self.apiFileCompleter = E5FileCompleter(self.apiFileEdit)
        
        # set initial values
        self.pluginManager = e5App().getObject("PluginManager")
        self.apiAutoPrepareCheckBox.setChecked(
            Preferences.getEditor("AutoPrepareAPIs"))
        
        import QScintilla.Lexers
        self.apis = {}
        apiLanguages = sorted(
            [''] + list(QScintilla.Lexers.getSupportedLanguages().keys()))
        for lang in apiLanguages:
            if lang != "Guessed":
                self.apiLanguageComboBox.addItem(lang)
        self.currentApiLanguage = ''
        self.on_apiLanguageComboBox_activated(self.currentApiLanguage)
        
        for lang in apiLanguages[1:]:
            self.apis[lang] = Preferences.getEditorAPI(lang)[:]
        
    def save(self):
        """
        Public slot to save the Editor APIs configuration.
        """
        Preferences.setEditor(
            "AutoPrepareAPIs",
            self.apiAutoPrepareCheckBox.isChecked())
        
        lang = self.apiLanguageComboBox.currentText()
        self.apis[lang] = self.__editorGetApisFromApiList()
        
        for lang, apis in list(self.apis.items()):
            Preferences.setEditorAPI(lang, apis)
        
    @pyqtSlot(str)
    def on_apiLanguageComboBox_activated(self, language):
        """
        Private slot to fill the api listbox of the api page.
        
        @param language selected API language (string)
        """
        if self.currentApiLanguage == language:
            return
            
        self.apis[self.currentApiLanguage] = self.__editorGetApisFromApiList()
        self.currentApiLanguage = language
        self.apiList.clear()
        
        if not language:
            self.apiGroup.setEnabled(False)
            return
            
        self.apiGroup.setEnabled(True)
        self.deleteApiFileButton.setEnabled(False)
        self.addApiFileButton.setEnabled(False)
        self.apiFileEdit.clear()
        
        for api in self.apis[self.currentApiLanguage]:
            if api:
                self.apiList.addItem(api)
        self.prepareApiButton.setEnabled(self.apiList.count() > 0)
        
        from QScintilla.APIsManager import APIsManager
        self.__currentAPI = APIsManager().getAPIs(self.currentApiLanguage)
        if self.__currentAPI is not None:
            self.__currentAPI.apiPreparationFinished.connect(
                self.__apiPreparationFinished)
            self.__currentAPI.apiPreparationCancelled.connect(
                self.__apiPreparationCancelled)
            self.__currentAPI.apiPreparationStarted.connect(
                self.__apiPreparationStarted)
            self.addInstalledApiFileButton.setEnabled(
                len(self.__currentAPI.installedAPIFiles()) > 0)
        else:
            self.addInstalledApiFileButton.setEnabled(False)
        
        self.addPluginApiFileButton.setEnabled(
            len(self.pluginManager.getPluginApiFiles(self.currentApiLanguage))
            > 0)
        
    def __editorGetApisFromApiList(self):
        """
        Private slot to retrieve the api filenames from the list.
        
        @return list of api filenames (list of strings)
        """
        apis = []
        for row in range(self.apiList.count()):
            apis.append(self.apiList.item(row).text())
        return apis
        
    @pyqtSlot()
    def on_apiFileButton_clicked(self):
        """
        Private method to select an api file.
        """
        file = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select API file"),
            self.apiFileEdit.text(),
            self.tr("API File (*.api);;All Files (*)"))
            
        if file:
            self.apiFileEdit.setText(Utilities.toNativeSeparators(file))
        
    @pyqtSlot()
    def on_addApiFileButton_clicked(self):
        """
        Private slot to add the api file displayed to the listbox.
        """
        file = self.apiFileEdit.text()
        if file:
            self.apiList.addItem(Utilities.toNativeSeparators(file))
            self.apiFileEdit.clear()
        self.prepareApiButton.setEnabled(self.apiList.count() > 0)
        
    @pyqtSlot()
    def on_deleteApiFileButton_clicked(self):
        """
        Private slot to delete the currently selected file of the listbox.
        """
        crow = self.apiList.currentRow()
        if crow >= 0:
            itm = self.apiList.takeItem(crow)
            del itm
        self.prepareApiButton.setEnabled(self.apiList.count() > 0)
        
    @pyqtSlot()
    def on_addInstalledApiFileButton_clicked(self):
        """
        Private slot to add an API file from the list of installed API files
        for the selected lexer language.
        """
        installedAPIFiles = self.__currentAPI.installedAPIFiles()
        if installedAPIFiles:
            installedAPIFilesPath = QFileInfo(installedAPIFiles[0]).path()
            installedAPIFilesShort = []
            for installedAPIFile in installedAPIFiles:
                installedAPIFilesShort.append(
                    QFileInfo(installedAPIFile).fileName())
            file, ok = QInputDialog.getItem(
                self,
                self.tr("Add from installed APIs"),
                self.tr("Select from the list of installed API files"),
                installedAPIFilesShort,
                0, False)
            if ok:
                self.apiList.addItem(Utilities.toNativeSeparators(
                    QFileInfo(QDir(installedAPIFilesPath), file)
                    .absoluteFilePath()))
        else:
            E5MessageBox.warning(
                self,
                self.tr("Add from installed APIs"),
                self.tr("""There are no APIs installed yet."""
                        """ Selection is not available."""))
            self.addInstalledApiFileButton.setEnabled(False)
        self.prepareApiButton.setEnabled(self.apiList.count() > 0)
        
    @pyqtSlot()
    def on_addPluginApiFileButton_clicked(self):
        """
        Private slot to add an API file from the list of API files installed
        by plugins for the selected lexer language.
        """
        pluginAPIFiles = self.pluginManager.getPluginApiFiles(
            self.currentApiLanguage)
        pluginAPIFilesDict = {}
        for apiFile in pluginAPIFiles:
            pluginAPIFilesDict[QFileInfo(apiFile).fileName()] = apiFile
        file, ok = QInputDialog.getItem(
            self,
            self.tr("Add from Plugin APIs"),
            self.tr(
                "Select from the list of API files installed by plugins"),
            sorted(pluginAPIFilesDict.keys()),
            0, False)
        if ok:
            self.apiList.addItem(Utilities.toNativeSeparators(
                pluginAPIFilesDict[file]))
        self.prepareApiButton.setEnabled(self.apiList.count() > 0)
        
    @pyqtSlot()
    def on_prepareApiButton_clicked(self):
        """
        Private slot to prepare the API file for the currently selected
            language.
        """
        if self.__inPreparation:
            self.__currentAPI and self.__currentAPI.cancelPreparation()
        else:
            if self.__currentAPI is not None:
                self.__currentAPI.prepareAPIs(
                    ondemand=True,
                    rawList=self.__editorGetApisFromApiList())
        
    def __apiPreparationFinished(self):
        """
        Private method called after the API preparation has finished.
        """
        self.prepareApiProgressBar.reset()
        self.prepareApiProgressBar.setRange(0, 100)
        self.prepareApiProgressBar.setValue(0)
        self.prepareApiButton.setText(self.tr("Compile APIs"))
        self.__inPreparation = False
    
    def __apiPreparationCancelled(self):
        """
        Private slot called after the API preparation has been cancelled.
        """
        self.__apiPreparationFinished()
    
    def __apiPreparationStarted(self):
        """
        Private method called after the API preparation has started.
        """
        self.prepareApiProgressBar.setRange(0, 0)
        self.prepareApiProgressBar.setValue(0)
        self.prepareApiButton.setText(self.tr("Cancel compilation"))
        self.__inPreparation = True
        
    def saveState(self):
        """
        Public method to save the current state of the widget.
        
        @return index of the selected lexer language (integer)
        """
        return self.apiLanguageComboBox.currentIndex()
        
    def setState(self, state):
        """
        Public method to set the state of the widget.
        
        @param state state data generated by saveState
        """
        self.apiLanguageComboBox.setCurrentIndex(state)
        self.on_apiLanguageComboBox_activated(
            self.apiLanguageComboBox.currentText())
    
    @pyqtSlot()
    def on_apiList_itemSelectionChanged(self):
        """
        Private slot to react on changes of API selections.
        """
        self.deleteApiFileButton.setEnabled(
            len(self.apiList.selectedItems()) > 0)
    
    @pyqtSlot(str)
    def on_apiFileEdit_textChanged(self, txt):
        """
        Private slot to handle the entering of an API file name.
        
        @param txt text of the line edit (string)
        """
        enable = txt != ""
        
        if enable:
            # check for already added file
            for row in range(self.apiList.count()):
                if txt == self.apiList.item(row).text():
                    enable = False
                    break
        
        self.addApiFileButton.setEnabled(enable)
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = EditorAPIsPage()
    return page
