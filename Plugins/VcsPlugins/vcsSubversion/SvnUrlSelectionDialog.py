# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the URLs for the svn diff command.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QRegExp, pyqtSlot
from PyQt5.QtWidgets import QDialog

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox

from .Ui_SvnUrlSelectionDialog import Ui_SvnUrlSelectionDialog

import Utilities


class SvnUrlSelectionDialog(QDialog, Ui_SvnUrlSelectionDialog):
    """
    Class implementing a dialog to enter the URLs for the svn diff command.
    """
    def __init__(self, vcs, tagsList, branchesList, path, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param tagsList list of tags (list of strings)
        @param branchesList list of branches (list of strings)
        @param path pathname to determine the repository URL from (string)
        @param parent parent widget of the dialog (QWidget)
        """
        super(SvnUrlSelectionDialog, self).__init__(parent)
        self.setupUi(self)
        
        if vcs.version < (1, 4, 0):
            self.summaryCheckBox.setEnabled(False)
            self.summaryCheckBox.setChecked(False)
        
        self.vcs = vcs
        self.tagsList = tagsList
        self.branchesList = branchesList
        
        self.typeCombo1.addItems(["trunk/", "tags/", "branches/"])
        self.typeCombo2.addItems(["trunk/", "tags/", "branches/"])
        
        reposURL = self.vcs.svnGetReposName(path)
        if reposURL is None:
            E5MessageBox.critical(
                self,
                self.tr("Subversion Error"),
                self.tr(
                    """The URL of the project repository could not be"""
                    """ retrieved from the working copy. The operation will"""
                    """ be aborted"""))
            self.reject()
            return
        
        if self.vcs.otherData["standardLayout"]:
            # determine the base path of the project in the repository
            rx_base = QRegExp('(.+/)(trunk|tags|branches).*')
            if not rx_base.exactMatch(reposURL):
                E5MessageBox.critical(
                    self,
                    self.tr("Subversion Error"),
                    self.tr(
                        """The URL of the project repository has an"""
                        """ invalid format. The list operation will"""
                        """ be aborted"""))
                self.reject()
                return
            
            reposRoot = rx_base.cap(1)
            self.repoRootLabel1.setText(reposRoot)
            self.repoRootLabel2.setText(reposRoot)
        else:
            project = e5App().getObject('Project')
            if Utilities.normcasepath(path) != \
               Utilities.normcasepath(project.getProjectPath()):
                path = project.getRelativePath(path)
                reposURL = reposURL.replace(path, '')
            self.repoRootLabel1.hide()
            self.typeCombo1.hide()
            self.labelCombo1.addItems([reposURL] + sorted(self.vcs.tagsList))
            self.labelCombo1.setEnabled(True)
            self.repoRootLabel2.hide()
            self.typeCombo2.hide()
            self.labelCombo2.addItems([reposURL] + sorted(self.vcs.tagsList))
            self.labelCombo2.setEnabled(True)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    def __changeLabelCombo(self, labelCombo, type_):
        """
        Private method used to change the label combo depending on the
        selected type.
        
        @param labelCombo reference to the labelCombo object (QComboBox)
        @param type_ type string (string)
        """
        if type_ == "trunk/":
            labelCombo.clear()
            labelCombo.setEditText("")
            labelCombo.setEnabled(False)
        elif type_ == "tags/":
            labelCombo.clear()
            labelCombo.clearEditText()
            labelCombo.addItems(sorted(self.tagsList))
            labelCombo.setEnabled(True)
        elif type_ == "branches/":
            labelCombo.clear()
            labelCombo.clearEditText()
            labelCombo.addItems(sorted(self.branchesList))
            labelCombo.setEnabled(True)
        
    @pyqtSlot(str)
    def on_typeCombo1_currentIndexChanged(self, type_):
        """
        Private slot called when the selected type was changed.
        
        @param type_ selected type (string)
        """
        self.__changeLabelCombo(self.labelCombo1, type_)
        
    @pyqtSlot(str)
    def on_typeCombo2_currentIndexChanged(self, type_):
        """
        Private slot called when the selected type was changed.
        
        @param type_ selected type (string)
        """
        self.__changeLabelCombo(self.labelCombo2, type_)
        
    def getURLs(self):
        """
        Public method to get the entered URLs.
        
        @return tuple of list of two URL strings (list of strings) and
            a flag indicating a diff summary (boolean)
        """
        if self.vcs.otherData["standardLayout"]:
            url1 = self.repoRootLabel1.text() + \
                self.typeCombo1.currentText() + \
                self.labelCombo1.currentText()
            url2 = self.repoRootLabel2.text() + \
                self.typeCombo2.currentText() + \
                self.labelCombo2.currentText()
        else:
            url1 = self.labelCombo1.currentText()
            url2 = self.labelCombo2.currentText()
        
        return [url1, url2], self.summaryCheckBox.isChecked()
