# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#


"""
Module implementing a dialog for adding GreaseMonkey scripts..
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSlot, QDir, QFile
from PyQt5.QtWidgets import QDialog

from E5Gui import E5MessageBox

from .Ui_GreaseMonkeyAddScriptDialog import Ui_GreaseMonkeyAddScriptDialog

import UI.PixmapCache


class GreaseMonkeyAddScriptDialog(QDialog, Ui_GreaseMonkeyAddScriptDialog):
    """
    Class implementing a dialog for adding GreaseMonkey scripts..
    """
    def __init__(self, manager, script, parent=None):
        """
        Constructor
        
        @param manager reference to the GreaseMonkey manager
            (GreaseMonkeyManager)
        @param script GreaseMonkey script to be added (GreaseMonkeyScript)
        @param parent reference to the parent widget (QWidget)
        """
        super(GreaseMonkeyAddScriptDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.iconLabel.setPixmap(
            UI.PixmapCache.getPixmap("greaseMonkey48.png"))
        
        self.__manager = manager
        self.__script = script
        
        runsAt = ""
        doesNotRunAt = ""
        
        include = script.include()
        exclude = script.exclude()
        
        if include:
            runsAt = self.tr("<p>runs at:<br/><i>{0}</i></p>").format(
                "<br/>".join(include))
        
        if exclude:
            doesNotRunAt = self.tr(
                "<p>does not run at:<br/><i>{0}</i></p>").format(
                "<br/>".join(exclude))
        
        scriptInfoTxt = "<p><b>{0}</b> {1}<br/>{2}</p>{3}{4}".format(
            script.name(), script.version(), script.description(), runsAt,
            doesNotRunAt)
        self.scriptInfo.setHtml(scriptInfoTxt)
        
        self.accepted.connect(self.__accepted)
    
    @pyqtSlot()
    def on_showScriptSourceButton_clicked(self):
        """
        Private slot to show an editor window with the source code.
        """
        from Helpviewer import HelpUtilities
        
        tmpFileName = HelpUtilities.ensureUniqueFilename(
            os.path.join(QDir.tempPath(), "tmp-userscript.js"))
        if QFile.copy(self.__script.fileName(), tmpFileName):
            from QScintilla.MiniEditor import MiniEditor
            editor = MiniEditor(tmpFileName, "JavaScript", self)
            editor.show()
    
    def __accepted(self):
        """
        Private slot handling the accepted signal.
        """
        if self.__manager.addScript(self.__script):
            msg = self.tr(
                "<p><b>{0}</b> installed successfully.</p>").format(
                self.__script.name())
            success = True
        else:
            msg = self.tr("<p>Cannot install script.</p>")
            success = False
        
        import Helpviewer.HelpWindow
        if success and Helpviewer.HelpWindow.HelpWindow.notificationsEnabled():
            Helpviewer.HelpWindow.HelpWindow.showNotification(
                UI.PixmapCache.getPixmap("greaseMonkey48.png"),
                self.tr("GreaseMonkey Script Installation"),
                msg)
        else:
            E5MessageBox.information(
                self,
                self.tr("GreaseMonkey Script Installation"),
                msg)
