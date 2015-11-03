# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to manage the QtHelp documentation database.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, Qt, QItemSelectionModel
from PyQt5.QtWidgets import QDialog
from PyQt5.QtHelp import QHelpEngineCore

from E5Gui import E5MessageBox, E5FileDialog

from .Ui_QtHelpDocumentationDialog import Ui_QtHelpDocumentationDialog


class QtHelpDocumentationDialog(QDialog, Ui_QtHelpDocumentationDialog):
    """
    Class implementing a dialog to manage the QtHelp documentation database.
    """
    def __init__(self, engine, parent):
        """
        Constructor
        
        @param engine reference to the help engine (QHelpEngine)
        @param parent reference to the parent widget (QWidget)
        """
        super(QtHelpDocumentationDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.removeButton.setEnabled(False)
        
        self.__engine = engine
        self.__mw = parent
        
        docs = self.__engine.registeredDocumentations()
        self.documentsList.addItems(docs)
        
        self.__registeredDocs = []
        self.__unregisteredDocs = []
        self.__tabsToClose = []
    
    @pyqtSlot()
    def on_documentsList_itemSelectionChanged(self):
        """
        Private slot handling a change of the documents selection.
        """
        self.removeButton.setEnabled(
            len(self.documentsList.selectedItems()) != 0)
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add documents to the help database.
        """
        fileNames = E5FileDialog.getOpenFileNames(
            self,
            self.tr("Add Documentation"),
            "",
            self.tr("Qt Compressed Help Files (*.qch)"))
        if not fileNames:
            return
        
        for fileName in fileNames:
            ns = QHelpEngineCore.namespaceName(fileName)
            if not ns:
                E5MessageBox.warning(
                    self,
                    self.tr("Add Documentation"),
                    self.tr(
                        """The file <b>{0}</b> is not a valid"""
                        """ Qt Help File.""").format(fileName)
                )
                continue
            
            if len(self.documentsList.findItems(ns, Qt.MatchFixedString)):
                E5MessageBox.warning(
                    self,
                    self.tr("Add Documentation"),
                    self.tr(
                        """The namespace <b>{0}</b> is already registered.""")
                    .format(ns)
                )
                continue
            
            self.__engine.registerDocumentation(fileName)
            self.documentsList.addItem(ns)
            self.__registeredDocs.append(ns)
            if ns in self.__unregisteredDocs:
                self.__unregisteredDocs.remove(ns)

    @pyqtSlot()
    def on_removeButton_clicked(self):
        """
        Private slot to remove a document from the help database.
        """
        res = E5MessageBox.yesNo(
            self,
            self.tr("Remove Documentation"),
            self.tr(
                """Do you really want to remove the selected documentation """
                """sets from the database?"""))
        if not res:
            return
        
        openedDocs = self.__mw.getSourceFileList()
        
        items = self.documentsList.selectedItems()
        for item in items:
            ns = item.text()
            if ns in list(openedDocs.values()):
                res = E5MessageBox.yesNo(
                    self,
                    self.tr("Remove Documentation"),
                    self.tr(
                        """Some documents currently opened reference the """
                        """documentation you are attempting to remove. """
                        """Removing the documentation will close those """
                        """documents. Remove anyway?"""),
                    icon=E5MessageBox.Warning)
                if not res:
                    return
            self.__unregisteredDocs.append(ns)
            for id in openedDocs:
                if openedDocs[id] == ns and id not in self.__tabsToClose:
                    self.__tabsToClose.append(id)
            itm = self.documentsList.takeItem(self.documentsList.row(item))
            del itm
            
            self.__engine.unregisterDocumentation(ns)
        
        if self.documentsList.count():
            self.documentsList.setCurrentRow(
                0, QItemSelectionModel.ClearAndSelect)
    
    def hasChanges(self):
        """
        Public slot to test the dialog for changes.
        
        @return flag indicating presence of changes
        """
        return len(self.__registeredDocs) > 0 or \
            len(self.__unregisteredDocs) > 0
    
    def getTabsToClose(self):
        """
        Public method to get the list of tabs to close.
        
        @return list of tab ids to be closed (list of integers)
        """
        return self.__tabsToClose
