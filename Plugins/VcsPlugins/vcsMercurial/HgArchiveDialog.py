# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the archive data.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, QFileInfo
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from E5Gui.E5Completers import E5FileCompleter, E5DirCompleter
from E5Gui import E5FileDialog

from .Ui_HgArchiveDialog import Ui_HgArchiveDialog

import Utilities
import UI.PixmapCache


class HgArchiveDialog(QDialog, Ui_HgArchiveDialog):
    """
    Class implementing a dialog to enter the archive data.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the Mercurial object (Hg)
        @param parent reference to the parent widget (QWidget)
        """
        super(HgArchiveDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.archiveButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.__archiveFileCompleter = E5FileCompleter()
        self.__archiveDirCompleter = E5DirCompleter()
        self.__activeCompleter = self.__archiveFileCompleter
        self.archiveEdit.setCompleter(self.__activeCompleter)
        self.__activeCompleter.model().setNameFilters([])
        
        self.typeComboBox.addItem(
            self.tr("Detect Automatically"), "")
        self.typeComboBox.addItem(
            self.tr("Directory of Files"), "files")
        self.typeComboBox.addItem(
            self.tr("Uncompressed TAR-Archive"), "tar")
        self.typeComboBox.addItem(
            self.tr("Bzip2 compressed TAR-Archive"), "tbz2")
        self.typeComboBox.addItem(
            self.tr("Gzip compressed TAR-Archive"), "tgz")
        self.typeComboBox.addItem(
            self.tr("Uncompressed ZIP-Archive"), "uzip")
        self.typeComboBox.addItem(
            self.tr("Compressed ZIP-Archive"), "zip")
        
        self.__unixFileFilters = [
            self.tr("Bzip2 compressed TAR-Archive (*.tar.bz2)"),
            self.tr("Gzip compressed TAR-Archive (*.tar.gz)"),
            self.tr("Uncompressed TAR-Archive (*.tar)"),
        ]
        self.__windowsFileFilters = [
            self.tr("Compressed ZIP-Archive (*.zip)"),
            self.tr("Uncompressed ZIP-Archive (*.uzip)")
        ]
        if Utilities.isWindowsPlatform():
            self.__fileFilters = ";;".join(
                self.__windowsFileFilters + self.__unixFileFilters)
        else:
            self.__fileFilters = ";;".join(
                self.__unixFileFilters + self.__windowsFileFilters)
        self.__fileFilters += ";;" + self.tr("All Files (*)")
        
        self.__typeFilters = {
            "tar": ["*.tar"],
            "tbz2": ["*.tar.bz2", "*.tbz2"],
            "tgz": ["*.tar.gz", "*.tgz"],
            "uzip": ["*.uzip", "*.zip"],
            "zip": ["*.zip"],
        }
        
        self.subReposCheckBox.setEnabled(vcs.hasSubrepositories())
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        
        self.__projectPath = \
            vcs.getPlugin().getProjectHelper().getProject().getProjectPath()
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    @pyqtSlot(str)
    def on_archiveEdit_textChanged(self, archive):
        """
        Private slot to handle changes of the archive name.
        
        @param archive name of the archive (string)
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(archive != "")
    
    @pyqtSlot()
    def on_archiveButton_clicked(self):
        """
        Private slot to select the archive name via a file selection dialog.
        """
        type_ = self.typeComboBox.itemData(self.typeComboBox.currentIndex())
        
        archive = Utilities.fromNativeSeparators(self.archiveEdit.text())
        if not archive:
            archive = self.__projectPath
        
        if type_ == "files":
            archive = E5FileDialog.getExistingDirectory(
                self,
                self.tr("Select Archive Directory"),
                archive,
                E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
        else:
            archive, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
                self,
                self.tr("Select Archive File"),
                archive,
                self.__fileFilters,
                None,
                E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
            if archive:
                ext = QFileInfo(archive).suffix()
                if not ext:
                    ex = selectedFilter.split("(*")[1].split(")")[0]
                    if ex:
                        archive += ex
        
        if archive:
            self.archiveEdit.setText(Utilities.toNativeSeparators(archive))
    
    @pyqtSlot(int)
    def on_typeComboBox_activated(self, index):
        """
        Private slot to react on changes of the selected archive type.
        
        @param index index of the selected type (integer)
        """
        type_ = self.typeComboBox.itemData(index)
        if type_ == "files":
            if self.__activeCompleter != self.__archiveDirCompleter:
                self.__activeCompleter = self.__archiveDirCompleter
                self.archiveEdit.setCompleter(self.__activeCompleter)
        else:
            if self.__activeCompleter != self.__archiveFileCompleter:
                self.__activeCompleter = self.__archiveFileCompleter
                self.archiveEdit.setCompleter(self.__activeCompleter)
            if type_ in self.__typeFilters:
                self.__activeCompleter.model().setNameFilters(
                    self.__typeFilters[type_])
            else:
                self.__activeCompleter.model().setNameFilters([])
    
    def getData(self):
        """
        Public method to retrieve the data.
        
        @return tuple giving the archive name (string), the archive type
            (string), the directory prefix 8string) and a flag indicating
            to recurse into subrepositories (boolean)
        """
        return (
            self.archiveEdit.text(),
            self.typeComboBox.itemData(self.typeComboBox.currentIndex()),
            self.prefixEdit.text(),
            self.subReposCheckBox.isChecked(),
        )
