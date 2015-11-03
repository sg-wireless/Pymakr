# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the project properties dialog.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QDir, pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from E5Gui.E5Application import e5App
from E5Gui.E5Completers import E5FileCompleter, E5DirCompleter
from E5Gui import E5FileDialog

from .Ui_PropertiesDialog import Ui_PropertiesDialog

import Utilities
import Preferences
import UI.PixmapCache


class PropertiesDialog(QDialog, Ui_PropertiesDialog):
    """
    Class implementing the project properties dialog.
    """
    def __init__(self, project, new=True, parent=None, name=None):
        """
        Constructor
        
        @param project reference to the project object
        @param new flag indicating the generation of a new project
        @param parent parent widget of this dialog (QWidget)
        @param name name of this dialog (string)
        """
        super(PropertiesDialog, self).__init__(parent)
        if name:
            self.setObjectName(name)
        self.setupUi(self)
        
        self.dirButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.mainscriptButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.project = project
        self.newProject = new
        self.transPropertiesDlg = None
        self.spellPropertiesDlg = None
        
        self.dirCompleter = E5DirCompleter(self.dirEdit)
        self.mainscriptCompleter = E5FileCompleter(self.mainscriptEdit)
        
        self.languageComboBox.addItems(project.getProgrammingLanguages())
        
        projectTypes = project.getProjectTypes()
        self.projectTypeComboBox.clear()
        for projectType in sorted(projectTypes.keys()):
            self.projectTypeComboBox.addItem(
                projectTypes[projectType], projectType)
        
        ipath = Preferences.getMultiProject("Workspace") or \
            Utilities.getHomeDir()
        self.__initPaths = [
            Utilities.fromNativeSeparators(ipath),
            Utilities.fromNativeSeparators(ipath) + "/",
        ]
        
        if not new:
            name = os.path.splitext(self.project.pfile)[0]
            self.nameEdit.setText(os.path.basename(name))
            self.languageComboBox.setCurrentIndex(
                self.languageComboBox.findText(
                    self.project.pdata["PROGLANGUAGE"][0]))
            self.mixedLanguageCheckBox.setChecked(
                self.project.pdata["MIXEDLANGUAGE"][0])
            curIndex = self.projectTypeComboBox.findData(
                self.project.pdata["PROJECTTYPE"][0])
            if curIndex == -1:
                curIndex = self.projectTypeComboBox.findData("Qt4")
            self.projectTypeComboBox.setCurrentIndex(curIndex)
            self.dirEdit.setText(self.project.ppath)
            try:
                self.versionEdit.setText(self.project.pdata["VERSION"][0])
            except IndexError:
                pass
            try:
                self.mainscriptEdit.setText(
                    self.project.pdata["MAINSCRIPT"][0])
            except IndexError:
                pass
            try:
                self.authorEdit.setText(self.project.pdata["AUTHOR"][0])
            except IndexError:
                pass
            try:
                self.emailEdit.setText(self.project.pdata["EMAIL"][0])
            except IndexError:
                pass
            try:
                self.descriptionEdit.setPlainText(
                    self.project.pdata["DESCRIPTION"][0])
            except LookupError:
                pass
            try:
                self.eolComboBox.setCurrentIndex(self.project.pdata["EOL"][0])
            except IndexError:
                pass
            self.vcsLabel.show()
            if self.project.vcs is not None:
                vcsSystemsDict = e5App().getObject("PluginManager")\
                    .getPluginDisplayStrings("version_control")
                try:
                    vcsSystemDisplay = \
                        vcsSystemsDict[self.project.pdata["VCS"][0]]
                except KeyError:
                    vcsSystemDisplay = "None"
                self.vcsLabel.setText(
                    self.tr(
                        "The project is version controlled by <b>{0}</b>.")
                    .format(vcsSystemDisplay))
                self.vcsInfoButton.show()
            else:
                self.vcsLabel.setText(
                    self.tr("The project is not version controlled."))
                self.vcsInfoButton.hide()
            self.vcsCheckBox.hide()
        else:
            self.languageComboBox.setCurrentIndex(
                self.languageComboBox.findText("Python3"))
            self.projectTypeComboBox.setCurrentIndex(
                self.projectTypeComboBox.findData("PyQt5"))
            self.dirEdit.setText(self.__initPaths[0])
            self.versionEdit.setText('0.1')
            self.vcsLabel.hide()
            self.vcsInfoButton.hide()
            if not self.project.vcsSoftwareAvailable():
                self.vcsCheckBox.hide()
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            bool(self.dirEdit.text()) and
            Utilities.fromNativeSeparators(self.dirEdit.text()) not in
            self.__initPaths)
    
    @pyqtSlot(str)
    def on_languageComboBox_currentIndexChanged(self, language):
        """
        Private slot handling the selection of a programming language.
        
        @param language selected programming language (string)
        """
        curProjectType = self.getProjectType()
        
        self.projectTypeComboBox.clear()
        projectTypes = self.project.getProjectTypes(language)
        for projectType in sorted(projectTypes.keys()):
            self.projectTypeComboBox.addItem(
                projectTypes[projectType], projectType)
        
        index = self.projectTypeComboBox.findData(curProjectType)
        if index == -1:
            index = 0
        self.projectTypeComboBox.setCurrentIndex(index)
    
    @pyqtSlot(str)
    def on_dirEdit_textChanged(self, txt):
        """
        Private slot to handle a change of the project directory.
        
        @param txt name of the project directory (string)
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            bool(txt) and
            Utilities.fromNativeSeparators(txt) not in self.__initPaths)
    
    @pyqtSlot()
    def on_dirButton_clicked(self):
        """
        Private slot to display a directory selection dialog.
        """
        directory = E5FileDialog.getExistingDirectory(
            self,
            self.tr("Select project directory"),
            self.dirEdit.text(),
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
        
        if directory:
            self.dirEdit.setText(Utilities.toNativeSeparators(directory))
    
    @pyqtSlot()
    def on_spellPropertiesButton_clicked(self):
        """
        Private slot to display the spelling properties dialog.
        """
        if self.spellPropertiesDlg is None:
            from .SpellingPropertiesDialog import SpellingPropertiesDialog
            self.spellPropertiesDlg = \
                SpellingPropertiesDialog(self.project, self.newProject, self)
        res = self.spellPropertiesDlg.exec_()
        if res == QDialog.Rejected:
            self.spellPropertiesDlg.initDialog()  # reset the dialogs contents
    
    @pyqtSlot()
    def on_transPropertiesButton_clicked(self):
        """
        Private slot to display the translations properties dialog.
        """
        if self.transPropertiesDlg is None:
            from .TranslationPropertiesDialog import \
                TranslationPropertiesDialog
            self.transPropertiesDlg = \
                TranslationPropertiesDialog(self.project, self.newProject,
                                            self)
        else:
            self.transPropertiesDlg.initFilters()
        res = self.transPropertiesDlg.exec_()
        if res == QDialog.Rejected:
            self.transPropertiesDlg.initDialog()  # reset the dialogs contents
    
    @pyqtSlot()
    def on_mainscriptButton_clicked(self):
        """
        Private slot to display a file selection dialog.
        """
        dir = self.dirEdit.text()
        if not dir:
            dir = QDir.currentPath()
        patterns = []
        for pattern, filetype in list(self.project.pdata["FILETYPES"].items()):
            if filetype == "SOURCES":
                patterns.append(pattern)
        filters = self.tr("Source Files ({0});;All Files (*)")\
            .format(" ".join(patterns))
        fn = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select main script file"),
            dir,
            filters)
        
        if fn:
            ppath = self.dirEdit.text()
            if ppath:
                ppath = QDir(ppath).absolutePath() + QDir.separator()
                fn = fn.replace(ppath, "")
            self.mainscriptEdit.setText(Utilities.toNativeSeparators(fn))
    
    @pyqtSlot()
    def on_vcsInfoButton_clicked(self):
        """
        Private slot to display a vcs information dialog.
        """
        if self.project.vcs is None:
            return
            
        from VCS.RepositoryInfoDialog import VcsRepositoryInfoDialog
        info = self.project.vcs.vcsRepositoryInfos(self.project.ppath)
        dlg = VcsRepositoryInfoDialog(self, info)
        dlg.exec_()
    
    def getProjectType(self):
        """
        Public method to get the selected project type.
        
        @return selected UI type (string)
        """
        return self.projectTypeComboBox.itemData(
            self.projectTypeComboBox.currentIndex())
    
    def getPPath(self):
        """
        Public method to get the project path.
        
        @return data of the project directory edit (string)
        """
        return os.path.abspath(self.dirEdit.text())
    
    def storeData(self):
        """
        Public method to store the entered/modified data.
        """
        self.project.ppath = os.path.abspath(self.dirEdit.text())
        fn = self.nameEdit.text()
        if fn:
            self.project.name = fn
            fn = "{0}.e4p".format(fn)
            self.project.pfile = os.path.join(self.project.ppath, fn)
        else:
            self.project.pfile = ""
        self.project.pdata["VERSION"] = [self.versionEdit.text()]
        fn = self.mainscriptEdit.text()
        if fn:
            fn = self.project.getRelativePath(fn)
            self.project.pdata["MAINSCRIPT"] = [fn]
            self.project.translationsRoot = os.path.splitext(fn)[0]
        else:
            self.project.pdata["MAINSCRIPT"] = []
            self.project.translationsRoot = ""
        self.project.pdata["AUTHOR"] = [self.authorEdit.text()]
        self.project.pdata["EMAIL"] = [self.emailEdit.text()]
        self.project.pdata["DESCRIPTION"] = \
            [self.descriptionEdit.toPlainText()]
        self.project.pdata["PROGLANGUAGE"] = \
            [self.languageComboBox.currentText()]
        self.project.pdata["MIXEDLANGUAGE"] = \
            [self.mixedLanguageCheckBox.isChecked()]
        projectType = self.getProjectType()
        if projectType is not None:
            self.project.pdata["PROJECTTYPE"] = [projectType]
        self.project.pdata["EOL"] = [self.eolComboBox.currentIndex()]
        
        self.project.vcsRequested = self.vcsCheckBox.isChecked()
        
        if self.spellPropertiesDlg is not None:
            self.spellPropertiesDlg.storeData()
        
        if self.transPropertiesDlg is not None:
            self.transPropertiesDlg.storeData()
