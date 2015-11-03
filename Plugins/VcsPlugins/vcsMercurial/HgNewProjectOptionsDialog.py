# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Mercurial Options Dialog for a new project from the
repository.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot, QDir
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from E5Gui.E5Completers import E5DirCompleter
from E5Gui import E5FileDialog

from .Ui_HgNewProjectOptionsDialog import Ui_HgNewProjectOptionsDialog
from .Config import ConfigHgProtocols

import Utilities
import Preferences
import UI.PixmapCache


class HgNewProjectOptionsDialog(QDialog, Ui_HgNewProjectOptionsDialog):
    """
    Class implementing the Options Dialog for a new project from the
    repository.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the version control object
        @param parent parent widget (QWidget)
        """
        super(HgNewProjectOptionsDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.projectDirButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.vcsUrlButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.vcsDirectoryCompleter = E5DirCompleter(self.vcsUrlEdit)
        self.vcsProjectDirCompleter = E5DirCompleter(self.vcsProjectDirEdit)
        
        self.protocolCombo.addItems(ConfigHgProtocols)
        
        hd = Utilities.toNativeSeparators(QDir.homePath())
        hd = os.path.join(hd, 'hgroot')
        self.vcsUrlEdit.setText(hd)
        
        self.vcs = vcs
        
        self.localPath = hd
        self.networkPath = "localhost/"
        self.localProtocol = True
        
        ipath = Preferences.getMultiProject("Workspace") or \
            Utilities.getHomeDir()
        self.__initPaths = [
            Utilities.fromNativeSeparators(ipath),
            Utilities.fromNativeSeparators(ipath) + "/",
        ]
        self.vcsProjectDirEdit.setText(
            Utilities.toNativeSeparators(self.__initPaths[0]))
        
        self.lfNoteLabel.setVisible(self.vcs.isExtensionActive("largefiles"))
        self.largeCheckBox.setVisible(self.vcs.isExtensionActive("largefiles"))
        
        self.resize(self.width(), self.minimumSizeHint().height())
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    @pyqtSlot(str)
    def on_vcsProjectDirEdit_textChanged(self, txt):
        """
        Private slot to handle a change of the project directory.
        
        @param txt name of the project directory (string)
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            bool(txt) and
            Utilities.fromNativeSeparators(txt) not in self.__initPaths)
    
    @pyqtSlot()
    def on_vcsUrlButton_clicked(self):
        """
        Private slot to display a selection dialog.
        """
        if self.protocolCombo.currentText() == "file://":
            directory = E5FileDialog.getExistingDirectory(
                self,
                self.tr("Select Repository-Directory"),
                self.vcsUrlEdit.text(),
                E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
            
            if directory:
                self.vcsUrlEdit.setText(
                    Utilities.toNativeSeparators(directory))
    
    @pyqtSlot()
    def on_projectDirButton_clicked(self):
        """
        Private slot to display a directory selection dialog.
        """
        directory = E5FileDialog.getExistingDirectory(
            self,
            self.tr("Select Project Directory"),
            self.vcsProjectDirEdit.text(),
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
        
        if directory:
            self.vcsProjectDirEdit.setText(
                Utilities.toNativeSeparators(directory))
    
    @pyqtSlot(str)
    def on_protocolCombo_activated(self, protocol):
        """
        Private slot to switch the status of the directory selection button.
        
        @param protocol name of the selected protocol (string)
        """
        self.vcsUrlButton.setEnabled(protocol == "file://")
        if protocol == "file://":
            self.networkPath = self.vcsUrlEdit.text()
            self.vcsUrlEdit.setText(self.localPath)
            self.localProtocol = True
        else:
            if self.localProtocol:
                self.localPath = self.vcsUrlEdit.text()
                self.vcsUrlEdit.setText(self.networkPath)
                self.localProtocol = False
    
    @pyqtSlot(str)
    def on_vcsUrlEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the URL.
        
        @param txt current text of the line edit (string)
        """
        enable = "://" not in txt
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enable)
    
    def getData(self):
        """
        Public slot to retrieve the data entered into the dialog.
        
        @return a tuple of a string (project directory) and a dictionary
            containing the data entered.
        """
        scheme = self.protocolCombo.currentText()
        url = self.vcsUrlEdit.text()
        if scheme == "file://" and url[0] not in ["\\", "/"]:
            url = "/{0}".format(url)
        vcsdatadict = {
            "url": '{0}{1}'.format(scheme, url),
            "revision": self.vcsRevisionEdit.text(),
            "largefiles": self.largeCheckBox.isChecked(),
        }
        return (self.vcsProjectDirEdit.text(), vcsdatadict)
