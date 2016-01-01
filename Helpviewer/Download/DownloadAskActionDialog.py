# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to ask for a download action.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_DownloadAskActionDialog import Ui_DownloadAskActionDialog

import Preferences


class DownloadAskActionDialog(QDialog, Ui_DownloadAskActionDialog):
    """
    Class implementing a dialog to ask for a download action.
    """
    def __init__(self, fileName, mimeType, baseUrl, parent=None):
        """
        Constructor
        
        @param fileName file name (string)
        @param mimeType mime type (string)
        @param baseUrl URL (string)
        @param parent reference to the parent widget (QWidget)
        """
        super(DownloadAskActionDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.infoLabel.setText("<b>{0}</b>".format(fileName))
        self.typeLabel.setText(mimeType)
        self.siteLabel.setText(baseUrl)
        
        if not Preferences.getHelp("VirusTotalEnabled") or \
           Preferences.getHelp("VirusTotalServiceKey") == "":
            self.scanButton.setHidden(True)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    def getAction(self):
        """
        Public method to get the selected action.
        
        @return selected action ("save", "open", "scan" or "cancel")
        """
        if self.openButton.isChecked():
            return "open"
        elif self.scanButton.isChecked():
            return "scan"
        elif self.saveButton.isChecked():
            return "save"
        else:
            # should not happen, but keep it safe
            return "cancel"
