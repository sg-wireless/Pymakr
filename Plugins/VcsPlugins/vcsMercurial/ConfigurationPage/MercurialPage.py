# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Mercurial configuration page.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog

from Preferences.ConfigurationPages.ConfigurationPageBase import \
    ConfigurationPageBase
from .Ui_MercurialPage import Ui_MercurialPage

from Utilities import supportedCodecs


class MercurialPage(ConfigurationPageBase, Ui_MercurialPage):
    """
    Class implementing the Mercurial configuration page.
    """
    def __init__(self, plugin):
        """
        Constructor
        
        @param plugin reference to the plugin object
        """
        super(MercurialPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("MercurialPage")
        
        self.__plugin = plugin
        
        self.encodingComboBox.addItems(sorted(supportedCodecs))
        self.encodingModeComboBox.addItems(["strict", "ignore", "replace"])
        
        # set initial values
        # global options
        index = self.encodingComboBox.findText(
            self.__plugin.getPreferences("Encoding"))
        self.encodingComboBox.setCurrentIndex(index)
        index = self.encodingModeComboBox.findText(
            self.__plugin.getPreferences("EncodingMode"))
        self.encodingModeComboBox.setCurrentIndex(index)
        self.hiddenChangesetsCheckBox.setChecked(
            self.__plugin.getPreferences("ConsiderHidden"))
        # log
        self.logSpinBox.setValue(
            self.__plugin.getPreferences("LogLimit"))
        # commit
        self.commitSpinBox.setValue(
            self.__plugin.getPreferences("CommitMessages"))
        # incoming/outgoing
        self.logBrowserCheckBox.setChecked(
            self.__plugin.getPreferences("UseLogBrowser"))
        # pull
        self.pullUpdateCheckBox.setChecked(
            self.__plugin.getPreferences("PullUpdate"))
        self.preferUnbundleCheckBox.setChecked(
            self.__plugin.getPreferences("PreferUnbundle"))
        # cleanup
        self.cleanupPatternEdit.setText(
            self.__plugin.getPreferences("CleanupPatterns"))
        # revert
        self.backupCheckBox.setChecked(
            self.__plugin.getPreferences("CreateBackup"))
        # merge
        self.internalMergeCheckBox.setChecked(
            self.__plugin.getPreferences("InternalMerge"))
    
    def save(self):
        """
        Public slot to save the Mercurial configuration.
        """
        # global options
        self.__plugin.setPreferences(
            "Encoding", self.encodingComboBox.currentText())
        self.__plugin.setPreferences(
            "EncodingMode", self.encodingModeComboBox.currentText())
        self.__plugin.setPreferences(
            "ConsiderHidden", self.hiddenChangesetsCheckBox.isChecked())
        # log
        self.__plugin.setPreferences(
            "LogLimit", self.logSpinBox.value())
        # commit
        self.__plugin.setPreferences(
            "CommitMessages", self.commitSpinBox.value())
        # incoming/outgoing
        self.__plugin.setPreferences(
            "UseLogBrowser", self.logBrowserCheckBox.isChecked())
        # pull
        self.__plugin.setPreferences(
            "PullUpdate", self.pullUpdateCheckBox.isChecked())
        self.__plugin.setPreferences(
            "PreferUnbundle", self.preferUnbundleCheckBox.isChecked())
        # cleanup
        self.__plugin.setPreferences(
            "CleanupPatterns", self.cleanupPatternEdit.text())
        # revert
        self.__plugin.setPreferences(
            "CreateBackup", self.backupCheckBox.isChecked())
        # merge
        self.__plugin.setPreferences(
            "InternalMerge", self.internalMergeCheckBox.isChecked())
    
    @pyqtSlot()
    def on_configButton_clicked(self):
        """
        Private slot to edit the (per user) Mercurial configuration file.
        """
        from QScintilla.MiniEditor import MiniEditor
        cfgFile = self.__plugin.getConfigPath()
        if not os.path.exists(cfgFile):
            from ..HgUserConfigDataDialog import HgUserConfigDataDialog
            dlg = HgUserConfigDataDialog()
            if dlg.exec_() == QDialog.Accepted:
                firstName, lastName, email, extensions, extensionsData = \
                    dlg.getData()
            else:
                firstName, lastName, email, extensions, extensionsData = (
                    "Firstname", "Lastname", "email_address", [], {})
            try:
                f = open(cfgFile, "w")
                f.write("[ui]\n")
                f.write("username = {0} {1} <{2}>\n".format(
                    firstName, lastName, email))
                if extensions:
                    f.write("\n[extensions]\n")
                    f.write(" =\n".join(extensions))
                    f.write(" =\n")     # complete the last line
                if "largefiles" in extensionsData:
                    dataDict = extensionsData["largefiles"]
                    f.write("\n[largefiles]\n")
                    if "minsize" in dataDict:
                        f.write("minsize = {0}\n".format(dataDict["minsize"]))
                    if "patterns" in dataDict:
                        f.write("patterns =\n")
                        f.write("  {0}\n".format(
                            "\n  ".join(dataDict["patterns"])))
                f.close()
            except (IOError, OSError):
                # ignore these
                pass
        editor = MiniEditor(cfgFile, "Properties", self)
        editor.show()
