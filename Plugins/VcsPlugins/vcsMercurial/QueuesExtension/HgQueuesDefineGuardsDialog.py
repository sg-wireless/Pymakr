# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to define guards for patches.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import pyqtSlot, Qt, QProcess, QCoreApplication
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QAbstractButton, \
    QListWidgetItem

from E5Gui import E5MessageBox

from .Ui_HgQueuesDefineGuardsDialog import Ui_HgQueuesDefineGuardsDialog

import UI.PixmapCache


class HgQueuesDefineGuardsDialog(QDialog, Ui_HgQueuesDefineGuardsDialog):
    """
    Class implementing a dialog to define guards for patches.
    """
    def __init__(self, vcs, extension, patchesList, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param extension reference to the extension module (Queues)
        @param patchesList list of patches (list of strings)
        @param parent reference to the parent widget (QWidget)
        """
        super(HgQueuesDefineGuardsDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.vcs = vcs
        self.extension = extension
        self.__hgClient = vcs.getClient()
        
        self.__patches = patchesList[:]
        self.patchSelector.addItems([""] + self.__patches)
        
        self.plusButton.setIcon(UI.PixmapCache.getIcon("plus.png"))
        self.minusButton.setIcon(UI.PixmapCache.getIcon("minus.png"))
        
        self.__dirtyList = False
        self.__currentPatch = ""
        
        self.show()
        QCoreApplication.processEvents()
    
    def closeEvent(self, e):
        """
        Protected slot implementing a close event handler.
        
        @param e close event (QCloseEvent)
        """
        if self.__hgClient:
            if self.__hgClient.isExecuting():
                self.__hgClient.cancel()
        
        if self.__dirtyList:
            res = E5MessageBox.question(
                self,
                self.tr("Unsaved Changes"),
                self.tr("""The guards list has been changed."""
                        """ Shall the changes be applied?"""),
                E5MessageBox.StandardButtons(
                    E5MessageBox.Apply |
                    E5MessageBox.Discard),
                E5MessageBox.Apply)
            if res == E5MessageBox.Apply:
                self.__applyGuards()
            else:
                self.__dirtyList = False
        
        e.accept()
    
    def start(self, path):
        """
        Public slot to start the list command.
        
        @param path name of directory to be listed (string)
        """
        dname, fname = self.vcs.splitPath(path)
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        self.__repodir = repodir
        self.on_patchSelector_activated("")
    
    @pyqtSlot(str)
    def on_patchSelector_activated(self, patch):
        """
        Private slot to get the list of guards defined for the given patch
        name.
        
        @param patch selected patch name (empty for current patch)
        """
        if self.__dirtyList:
            res = E5MessageBox.question(
                self,
                self.tr("Unsaved Changes"),
                self.tr("""The guards list has been changed."""
                        """ Shall the changes be applied?"""),
                E5MessageBox.StandardButtons(
                    E5MessageBox.Apply |
                    E5MessageBox.Discard),
                E5MessageBox.Apply)
            if res == E5MessageBox.Apply:
                self.__applyGuards()
            else:
                self.__dirtyList = False
        
        self.guardsList.clear()
        self.patchNameLabel.setText("")
        
        self.guardCombo.clear()
        guardsList = self.extension.getGuardsList(self.__repodir)
        self.guardCombo.addItems(guardsList)
        self.guardCombo.setEditText("")
        
        args = self.vcs.initCommand("qguard")
        if patch:
            args.append(patch)
        
        output = ""
        if self.__hgClient:
            output = self.__hgClient.runcommand(args)[0]
        else:
            process = QProcess()
            process.setWorkingDirectory(self.__repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.vcs.getEncoding(), 'replace').strip()
        
        if output:
            patchName, guards = output.split(":", 1)
            self.patchNameLabel.setText(patchName)
            guardsList = guards.strip().split()
            for guard in guardsList:
                if guard.startswith("+"):
                    icon = UI.PixmapCache.getIcon("plus.png")
                    guard = guard[1:]
                    sign = "+"
                elif guard.startswith("-"):
                    icon = UI.PixmapCache.getIcon("minus.png")
                    guard = guard[1:]
                    sign = "-"
                else:
                    continue
                itm = QListWidgetItem(icon, guard, self.guardsList)
                itm.setData(Qt.UserRole, sign)
        
        self.on_guardsList_itemSelectionChanged()
    
    @pyqtSlot()
    def on_guardsList_itemSelectionChanged(self):
        """
        Private slot to handle changes of the selection of guards.
        """
        self.removeButton.setEnabled(
            len(self.guardsList.selectedItems()) > 0)
    
    def __getGuard(self, guard):
        """
        Private method to get a reference to a named guard.
        
        @param guard name of the guard (string)
        @return reference to the guard item (QListWidgetItem)
        """
        items = self.guardsList.findItems(guard, Qt.MatchCaseSensitive)
        if items:
            return items[0]
        else:
            return None
    
    @pyqtSlot(str)
    def on_guardCombo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the text of the guard combo.
        
        @param txt contents of the guard combo line edit (string)
        """
        self.addButton.setEnabled(txt != "")
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add a guard definition to the list or change it.
        """
        guard = self.guardCombo.currentText()
        if self.plusButton.isChecked():
            sign = "+"
            icon = UI.PixmapCache.getIcon("plus.png")
        else:
            sign = "-"
            icon = UI.PixmapCache.getIcon("minus.png")
        
        guardItem = self.__getGuard(guard)
        if guardItem:
            # guard already exists, remove it first
            row = self.guardsList.row(guardItem)
            itm = self.guardsList.takeItem(row)
            del itm
        
        itm = QListWidgetItem(icon, guard, self.guardsList)
        itm.setData(Qt.UserRole, sign)
        self.guardsList.sortItems()
        
        self.__dirtyList = True
    
    @pyqtSlot()
    def on_removeButton_clicked(self):
        """
        Private slot to remove guard definitions from the list.
        """
        res = E5MessageBox.yesNo(
            self,
            self.tr("Remove Guards"),
            self.tr(
                """Do you really want to remove the selected guards?"""))
        if res:
            for guardItem in self.guardsList.selectedItems():
                row = self.guardsList.row(guardItem)
                itm = self.guardsList.takeItem(row)
                del itm
        
        self.__dirtyList = True
    
    @pyqtSlot(QAbstractButton)
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Apply):
            self.__applyGuards()
        elif button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
    
    @pyqtSlot()
    def __applyGuards(self):
        """
        Private slot to apply the defined guards to the current patch.
        """
        if self.__dirtyList:
            guardsList = []
            for row in range(self.guardsList.count()):
                itm = self.guardsList.item(row)
                guard = itm.data(Qt.UserRole) + itm.text()
                guardsList.append(guard)
            
            args = self.vcs.initCommand("qguard")
            args.append(self.patchNameLabel.text())
            if guardsList:
                args.append("--")
                args.extend(guardsList)
            else:
                args.append("--none")
            
            error = ""
            if self.__hgClient:
                error = self.__hgClient.runcommand(args)[1]
            else:
                process = QProcess()
                process.setWorkingDirectory(self.__repodir)
                process.start('hg', args)
                procStarted = process.waitForStarted(5000)
                if procStarted:
                    finished = process.waitForFinished(30000)
                    if finished:
                        if process.exitCode() != 0:
                            error = str(process.readAllStandardError(),
                                        self.vcs.getEncoding(), 'replace')
                    else:
                        E5MessageBox.warning(
                            self,
                            self.tr("Apply Guard Definitions"),
                            self.tr(
                                """The Mercurial process did not finish"""
                                """ in time."""))
            
            if error:
                E5MessageBox.warning(
                    self,
                    self.tr("Apply Guard Definitions"),
                    self.tr("""<p>The defined guards could not be"""
                            """ applied.</p><p>Reason: {0}</p>""")
                    .format(error))
            else:
                            self.__dirtyList = False
                            self.on_patchSelector_activated(
                                self.patchNameLabel.text())
