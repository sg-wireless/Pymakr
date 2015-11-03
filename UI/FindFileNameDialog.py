# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to search for files.
"""

from __future__ import unicode_literals

import os
import sys

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QHeaderView, QApplication, \
    QDialogButtonBox, QTreeWidgetItem

from E5Gui.E5Completers import E5DirCompleter
from E5Gui import E5FileDialog

from .Ui_FindFileNameDialog import Ui_FindFileNameDialog

from Utilities import direntries
import Utilities
import UI.PixmapCache


class FindFileNameDialog(QWidget, Ui_FindFileNameDialog):
    """
    Class implementing a dialog to search for files.
    
    The occurrences found are displayed in a QTreeWidget showing the
    filename and the pathname. The file will be opened upon a double click
    onto the respective entry of the list.
    
    @signal sourceFile(str) emitted to open a file in the editor
    @signal designerFile(str) emitted to open a Qt-Designer file
    """
    sourceFile = pyqtSignal(str)
    designerFile = pyqtSignal(str)
    
    def __init__(self, project, parent=None):
        """
        Constructor
        
        @param project reference to the project object
        @param parent parent widget of this dialog (QWidget)
        """
        super(FindFileNameDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.searchDirButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.searchDirCompleter = E5DirCompleter(self.searchDirEdit)
        
        self.fileList.headerItem().setText(self.fileList.columnCount(), "")
        
        self.stopButton = self.buttonBox.addButton(
            self.tr("Stop"), QDialogButtonBox.ActionRole)
        self.stopButton.setToolTip(self.tr("Press to stop the search"))
        self.stopButton.setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Open).setToolTip(
            self.tr("Opens the selected file"))
        self.buttonBox.button(QDialogButtonBox.Open).setEnabled(False)
        
        self.project = project
        self.extsepLabel.setText(os.extsep)
        
        self.shouldStop = False

    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.stopButton:
            self.shouldStop = True
        elif button == self.buttonBox.button(QDialogButtonBox.Open):
            self.__openFile()
    
    def __openFile(self, itm=None):
        """
        Private slot to open a file.
        
        It emits the signal sourceFile or designerFile depending on the
        file extension.
        
        @param itm item to be opened (QTreeWidgetItem)
        """
        if itm is None:
            itm = self.fileList.currentItem()
        if itm is not None:
            fileName = itm.text(0)
            filePath = itm.text(1)
            
            if fileName.endswith('.ui'):
                self.designerFile.emit(os.path.join(filePath, fileName))
            else:
                self.sourceFile.emit(os.path.join(filePath, fileName))

    def __searchFile(self):
        """
        Private slot to handle the search.
        """
        fileName = self.fileNameEdit.text()
        if not fileName:
            self.fileList.clear()
            return
        fileExt = self.fileExtEdit.text()
        if not fileExt and Utilities.isWindowsPlatform():
            self.fileList.clear()
            return
        
        patternFormat = fileExt and "{0}{1}{2}" or "{0}*{1}{2}"
        fileNamePattern = patternFormat.format(
            fileName, os.extsep, fileExt and fileExt or '*')
        
        searchPaths = []
        if self.searchDirCheckBox.isChecked() and \
           self.searchDirEdit.text() != "":
            searchPaths.append(self.searchDirEdit.text())
        if self.projectCheckBox.isChecked():
            searchPaths.append(self.project.ppath)
        if self.syspathCheckBox.isChecked():
            searchPaths.extend(sys.path)
        
        found = False
        self.fileList.clear()
        locations = {}
        self.shouldStop = False
        self.stopButton.setEnabled(True)
        QApplication.processEvents()
        
        for path in searchPaths:
            if os.path.isdir(path):
                files = direntries(path, True, fileNamePattern,
                                   False, self.checkStop)
                if files:
                    found = True
                    for file in files:
                        fp, fn = os.path.split(file)
                        if fn in locations:
                            if fp in locations[fn]:
                                continue
                            else:
                                locations[fn].append(fp)
                        else:
                            locations[fn] = [fp]
                        QTreeWidgetItem(self.fileList, [fn, fp])
                    QApplication.processEvents()
            
        del locations
        self.stopButton.setEnabled(False)
        self.fileList.header().resizeSections(QHeaderView.ResizeToContents)
        self.fileList.header().setStretchLastSection(True)
        
        if found:
            self.fileList.setCurrentItem(self.fileList.topLevelItem(0))

    def checkStop(self):
        """
        Public method to check, if the search should be stopped.
        
        @return flag indicating the search should be stopped (boolean)
        """
        QApplication.processEvents()
        return self.shouldStop
        
    def on_fileNameEdit_textChanged(self, text):
        """
        Private slot to handle the textChanged signal of the file name edit.
        
        @param text (ignored)
        """
        self.__searchFile()
        
    def on_fileExtEdit_textChanged(self, text):
        """
        Private slot to handle the textChanged signal of the file extension
        edit.
        
        @param text (ignored)
        """
        self.__searchFile()
        
    def on_searchDirEdit_textChanged(self, text):
        """
        Private slot to handle the textChanged signal of the search directory
        edit.
        
        @param text text of the search dir edit (string)
        """
        self.searchDirCheckBox.setEnabled(text != "")
        if self.searchDirCheckBox.isChecked():
            self.__searchFile()
        
    @pyqtSlot()
    def on_searchDirButton_clicked(self):
        """
        Private slot to handle the clicked signal of the search directory
        selection button.
        """
        searchDir = E5FileDialog.getExistingDirectory(
            None,
            self.tr("Select search directory"),
            self.searchDirEdit.text(),
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
        
        if searchDir:
            self.searchDirEdit.setText(Utilities.toNativeSeparators(searchDir))
        
    def on_searchDirCheckBox_toggled(self, checked):
        """
        Private slot to handle the toggled signal of the search directory
        checkbox.
        
        @param checked flag indicating the state of the checkbox (boolean)
        """
        if self.searchDirEdit.text():
            self.__searchFile()
        
    def on_projectCheckBox_toggled(self, checked):
        """
        Private slot to handle the toggled signal of the project checkbox.
        
        @param checked flag indicating the state of the checkbox (boolean)
        """
        self.__searchFile()
        
    def on_syspathCheckBox_toggled(self, checked):
        """
        Private slot to handle the toggled signal of the sys.path checkbox.
        
        @param checked flag indicating the state of the checkbox (boolean)
        """
        self.__searchFile()
        
    def on_fileList_itemActivated(self, itm, column):
        """
        Private slot to handle the double click on a file item.
        
        It emits the signal sourceFile or designerFile depending on the
        file extension.
        
        @param itm the double clicked listview item (QTreeWidgetItem)
        @param column column that was double clicked (integer) (ignored)
        """
        self.__openFile(itm)
        
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_fileList_currentItemChanged(self, current, previous):
        """
        Private slot handling a change of the current item.
        
        @param current current item (QTreeWidgetItem)
        @param previous prevoius current item (QTreeWidgetItem)
        """
        self.buttonBox.button(QDialogButtonBox.Open).setEnabled(
            current is not None)
        
    def show(self):
        """
        Public method to enable/disable the project checkbox.
        """
        if self.project and self.project.isOpen():
            self.projectCheckBox.setEnabled(True)
            self.projectCheckBox.setChecked(True)
        else:
            self.projectCheckBox.setEnabled(False)
            self.projectCheckBox.setChecked(False)
        
        self.fileNameEdit.selectAll()
        self.fileNameEdit.setFocus()
        
        super(FindFileNameDialog, self).show()
