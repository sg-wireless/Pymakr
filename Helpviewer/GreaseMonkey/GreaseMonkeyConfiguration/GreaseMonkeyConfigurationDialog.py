# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the GreaseMonkey scripts configuration dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QDialog, QListWidgetItem

from E5Gui import E5MessageBox

from .Ui_GreaseMonkeyConfigurationDialog import \
    Ui_GreaseMonkeyConfigurationDialog

import UI.PixmapCache


class GreaseMonkeyConfigurationDialog(
        QDialog, Ui_GreaseMonkeyConfigurationDialog):
    """
    Class implementing the GreaseMonkey scripts configuration dialog.
    """
    ScriptVersionRole = Qt.UserRole
    ScriptDescriptionRole = Qt.UserRole + 1
    ScriptRole = Qt.UserRole + 2
    
    def __init__(self, manager, parent=None):
        """
        Constructor
        
        @param manager reference to the manager object (GreaseMonkeyManager)
        @param parent reference to the parent widget (QWidget)
        """
        super(GreaseMonkeyConfigurationDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.iconLabel.setPixmap(
            UI.PixmapCache.getPixmap("greaseMonkey48.png"))
        
        self.__manager = manager
        
        self.__loadScripts()
        
        self.scriptsList.removeItemRequested.connect(self.__removeItem)
        self.scriptsList.itemChanged.connect(self.__itemChanged)
    
    @pyqtSlot()
    def on_openDirectoryButton_clicked(self):
        """
        Private slot to open the GreaseMonkey scripts directory.
        """
        QDesktopServices.openUrl(
            QUrl.fromLocalFile(self.__manager.scriptsDirectory()))
    
    @pyqtSlot(str)
    def on_downloadLabel_linkActivated(self, link):
        """
        Private slot to open the greasyfork.org web site.
        
        @param link URL (string)
        """
        import Helpviewer.HelpWindow
        if not link or "userscript.org" in link:
            # userscript.org is down, default to Greasy Fork.
            link = "https://greasyfork.org/"
        Helpviewer.HelpWindow.HelpWindow.mainWindow().newTab(
            QUrl(link))
        self.close()
    
    @pyqtSlot(QListWidgetItem)
    def on_scriptsList_itemDoubleClicked(self, item):
        """
        Private slot to show information about the selected script.
        
        @param item reference to the double clicked item (QListWidgetItem)
        """
        script = self.__getScript(item)
        if script is not None:
            from .GreaseMonkeyConfigurationScriptInfoDialog import \
                GreaseMonkeyConfigurationScriptInfoDialog
            infoDlg = GreaseMonkeyConfigurationScriptInfoDialog(script, self)
            infoDlg.exec_()
    
    def __loadScripts(self):
        """
        Private method to load all the available scripts.
        """
        for script in self.__manager.allScripts():
            itm = QListWidgetItem(
                UI.PixmapCache.getIcon("greaseMonkeyScript.png"),
                script.name(), self.scriptsList)
            itm.setData(
                GreaseMonkeyConfigurationDialog.ScriptVersionRole,
                script.version())
            itm.setData(
                GreaseMonkeyConfigurationDialog.ScriptDescriptionRole,
                script.description())
            itm.setFlags(itm.flags() | Qt.ItemIsUserCheckable)
            if script.isEnabled():
                itm.setCheckState(Qt.Checked)
            else:
                itm.setCheckState(Qt.Unchecked)
            itm.setData(GreaseMonkeyConfigurationDialog.ScriptRole, script)
            self.scriptsList.addItem(itm)
        
        self.scriptsList.sortItems()
        
        itemMoved = True
        while itemMoved:
            itemMoved = False
            for row in range(self.scriptsList.count()):
                topItem = self.scriptsList.item(row)
                bottomItem = self.scriptsList.item(row + 1)
                if topItem is None or bottomItem is None:
                    continue
                
                if topItem.checkState() == Qt.Unchecked and \
                   bottomItem.checkState == Qt.Checked:
                    itm = self.scriptsList.takeItem(row + 1)
                    self.scriptsList.insertItem(row, itm)
                    itemMoved = True
    
    def __getScript(self, itm):
        """
        Private method to get the script for the given item.
        
        @param itm item to get script for (QListWidgetItem)
        @return reference to the script object (GreaseMonkeyScript)
        """
        if itm is None:
            return None
        
        script = itm.data(GreaseMonkeyConfigurationDialog.ScriptRole)
        return script
    
    def __removeItem(self, itm):
        """
        Private slot to remove a script item.
        
        @param itm item to be removed (QListWidgetItem)
        """
        script = self.__getScript(itm)
        if script is None:
            return
        
        removeIt = E5MessageBox.yesNo(
            self,
            self.tr("Remove Script"),
            self.tr(
                """<p>Are you sure you want to remove <b>{0}</b>?</p>""")
            .format(script.name()))
        if removeIt and self.__manager.removeScript(script):
            self.scriptsList.takeItem(self.scriptsList.row(itm))
            del itm
    
    def __itemChanged(self, itm):
        """
        Private slot to handle changes of a script item.
        
        @param itm changed item (QListWidgetItem)
        """
        script = self.__getScript(itm)
        if script is None:
            return
        
        if itm.checkState() == Qt.Checked:
            self.__manager.enableScript(script)
        else:
            self.__manager.disableScript(script)
