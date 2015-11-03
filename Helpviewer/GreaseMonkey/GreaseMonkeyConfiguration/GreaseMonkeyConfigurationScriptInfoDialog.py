# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show GreaseMonkey script information.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog

from .Ui_GreaseMonkeyConfigurationScriptInfoDialog import \
    Ui_GreaseMonkeyConfigurationScriptInfoDialog

from ..GreaseMonkeyScript import GreaseMonkeyScript

import UI.PixmapCache


class GreaseMonkeyConfigurationScriptInfoDialog(
        QDialog, Ui_GreaseMonkeyConfigurationScriptInfoDialog):
    """
    Class implementing a dialog to show GreaseMonkey script information.
    """
    def __init__(self, script, parent=None):
        """
        Constructor
        
        @param script reference to the script (GreaseMonkeyScript)
        @param parent reference to the parent widget (QWidget)
        """
        super(GreaseMonkeyConfigurationScriptInfoDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.iconLabel.setPixmap(
            UI.PixmapCache.getPixmap("greaseMonkey48.png"))
        
        self.__scriptFileName = script.fileName()
        
        self.setWindowTitle(
            self.tr("Script Details of {0}").format(script.name()))
        
        self.nameLabel.setText(script.fullName())
        self.versionLabel.setText(script.version())
        self.urlLabel.setText(script.downloadUrl().toString())
        if script.startAt() == GreaseMonkeyScript.DocumentStart:
            self.startAtLabel.setText("document-start")
        else:
            self.startAtLabel.setText("document-end")
        self.descriptionBrowser.setHtml(script.description())
        self.runsAtBrowser.setHtml("<br/>".join(script.include()))
        self.doesNotRunAtBrowser.setHtml("<br/>".join(script.exclude()))
    
    @pyqtSlot()
    def on_showScriptSourceButton_clicked(self):
        """
        Private slot to show an editor window with the script source code.
        """
        from QScintilla.MiniEditor import MiniEditor
        editor = MiniEditor(self.__scriptFileName, "JavaScript", self)
        editor.show()
