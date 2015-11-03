# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for the configuration of search engines.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSlot

from E5Gui import E5MessageBox, E5FileDialog

from .OpenSearchEngineModel import OpenSearchEngineModel

from .Ui_OpenSearchDialog import Ui_OpenSearchDialog


class OpenSearchDialog(QDialog, Ui_OpenSearchDialog):
    """
    Class implementing a dialog for the configuration of search engines.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QWidget)
        """
        super(OpenSearchDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.setModal(True)
        
        self.__mw = parent
        
        self.__model = \
            OpenSearchEngineModel(self.__mw.openSearchManager(), self)
        self.enginesTable.setModel(self.__model)
        self.enginesTable.horizontalHeader().resizeSection(0, 200)
        self.enginesTable.horizontalHeader().setStretchLastSection(True)
        self.enginesTable.verticalHeader().hide()
        self.enginesTable.verticalHeader().setDefaultSectionSize(
            1.2 * self.fontMetrics().height())
        
        self.enginesTable.selectionModel().selectionChanged.connect(
            self.__selectionChanged)
        self.editButton.setEnabled(False)
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add a new search engine.
        """
        fileNames = E5FileDialog.getOpenFileNames(
            self,
            self.tr("Add search engine"),
            "",
            self.tr("OpenSearch (*.xml);;All Files (*)"))
        
        osm = self.__mw.openSearchManager()
        for fileName in fileNames:
            if not osm.addEngine(fileName):
                E5MessageBox.critical(
                    self,
                    self.tr("Add search engine"),
                    self.tr(
                        """{0} is not a valid OpenSearch 1.1 description or"""
                        """ is already on your list.""").format(fileName))
    
    @pyqtSlot()
    def on_deleteButton_clicked(self):
        """
        Private slot to delete the selected search engines.
        """
        if self.enginesTable.model().rowCount() == 1:
            E5MessageBox.critical(
                self,
                self.tr("Delete selected engines"),
                self.tr("""You must have at least one search engine."""))
        
        self.enginesTable.removeSelected()
    
    @pyqtSlot()
    def on_restoreButton_clicked(self):
        """
        Private slot to restore the default search engines.
        """
        self.__mw.openSearchManager().restoreDefaults()
    
    @pyqtSlot()
    def on_editButton_clicked(self):
        """
        Private slot to edit the data of the current search engine.
        """
        from .OpenSearchEditDialog import OpenSearchEditDialog
        
        rows = self.enginesTable.selectionModel().selectedRows()
        if len(rows) == 0:
            row = self.enginesTable.selectionModel().currentIndex().row()
        else:
            row = rows[0].row()
        
        osm = self.__mw.openSearchManager()
        engineName = osm.allEnginesNames()[row]
        engine = osm.engine(engineName)
        dlg = OpenSearchEditDialog(engine, self)
        if dlg.exec_() == QDialog.Accepted:
            osm.enginesChanged()
    
    def __selectionChanged(self, selected, deselected):
        """
        Private slot to handle a change of the selection.
        
        @param selected item selection of selected items (QItemSelection)
        @param deselected item selection of deselected items (QItemSelection)
        """
        self.editButton.setEnabled(
            len(self.enginesTable.selectionModel().selectedRows()) <= 1)
