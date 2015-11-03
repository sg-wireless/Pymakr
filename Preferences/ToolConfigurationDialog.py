# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a configuration dialog for the tools menu.
"""

from __future__ import unicode_literals

import copy

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QDialog

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5MessageBox, E5FileDialog

from .Ui_ToolConfigurationDialog import Ui_ToolConfigurationDialog

import Utilities
import UI.PixmapCache


class ToolConfigurationDialog(QDialog, Ui_ToolConfigurationDialog):
    """
    Class implementing a configuration dialog for the tools menu.
    """
    def __init__(self, toollist, parent=None):
        """
        Constructor
        
        @param toollist list of configured tools
        @param parent parent widget (QWidget)
        """
        super(ToolConfigurationDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.iconButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.executableButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.iconCompleter = E5FileCompleter(self.iconEdit)
        self.executableCompleter = E5FileCompleter(self.executableEdit)
        
        self.redirectionModes = [
            ("no", self.tr("no redirection")),
            ("show", self.tr("show output")),
            ("insert", self.tr("insert into current editor")),
            ("replaceSelection",
             self.tr("replace selection of current editor")),
        ]
        
        self.toollist = copy.deepcopy(toollist)
        for tool in toollist:
            self.toolsList.addItem(tool['menutext'])
        
        for mode in self.redirectionModes:
            self.redirectCombo.addItem(mode[1])
        
        if len(toollist):
            self.toolsList.setCurrentRow(0)
            self.on_toolsList_currentRowChanged(0)
        
        t = self.argumentsEdit.whatsThis()
        if t:
            t += Utilities.getPercentReplacementHelp()
            self.argumentsEdit.setWhatsThis(t)
        
    def __findModeIndex(self, shortName):
        """
        Private method to find the mode index by its short name.
        
        @param shortName short name of the mode (string)
        @return index of the mode (integer)
        """
        ind = 0
        for mode in self.redirectionModes:
            if mode[0] == shortName:
                return ind
            ind += 1
        return 1    # default is "show output"
        
    @pyqtSlot()
    def on_newButton_clicked(self):
        """
        Private slot to clear all entry fields.
        """
        self.executableEdit.clear()
        self.menuEdit.clear()
        self.iconEdit.clear()
        self.argumentsEdit.clear()
        self.redirectCombo.setCurrentIndex(1)
        
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add a new entry.
        """
        menutext = self.menuEdit.text()
        icon = self.iconEdit.text()
        executable = self.executableEdit.text()
        arguments = self.argumentsEdit.text()
        redirect = self.redirectionModes[self.redirectCombo.currentIndex()][0]
        
        if not executable:
            E5MessageBox.critical(
                self,
                self.tr("Add tool entry"),
                self.tr(
                    "You have to set an executable to add to the"
                    " Tools-Menu first."))
            return
        
        if not menutext:
            E5MessageBox.critical(
                self,
                self.tr("Add tool entry"),
                self.tr(
                    "You have to insert a menuentry text to add the"
                    " selected program to the Tools-Menu first."))
            return
        
        if not Utilities.isinpath(executable):
            E5MessageBox.critical(
                self,
                self.tr("Add tool entry"),
                self.tr(
                    "The selected file could not be found or"
                    " is not an executable."
                    " Please choose an executable filename."))
            return
        
        if len(self.toolsList.findItems(
                menutext, Qt.MatchFlags(Qt.MatchExactly))):
            E5MessageBox.critical(
                self,
                self.tr("Add tool entry"),
                self.tr("An entry for the menu text {0} already exists.")
                .format(menutext))
            return
        
        self.toolsList.addItem(menutext)
        tool = {
            'menutext': menutext,
            'icon': icon,
            'executable': executable,
            'arguments': arguments,
            'redirect': redirect,
        }
        self.toollist.append(tool)
        
    @pyqtSlot()
    def on_changeButton_clicked(self):
        """
        Private slot to change an entry.
        """
        row = self.toolsList.currentRow()
        if row < 0:
            return
        
        menutext = self.menuEdit.text()
        icon = self.iconEdit.text()
        executable = self.executableEdit.text()
        arguments = self.argumentsEdit.text()
        redirect = self.redirectionModes[self.redirectCombo.currentIndex()][0]
        
        if not executable:
            E5MessageBox.critical(
                self,
                self.tr("Change tool entry"),
                self.tr(
                    "You have to set an executable to change the"
                    " Tools-Menu entry."))
            return
            
        if not menutext:
            E5MessageBox.critical(
                self,
                self.tr("Change tool entry"),
                self.tr(
                    "You have to insert a menuentry text to change the"
                    " selected Tools-Menu entry."))
            return
            
        if not Utilities.isinpath(executable):
            E5MessageBox.critical(
                self,
                self.tr("Change tool entry"),
                self.tr(
                    "The selected file could not be found or"
                    " is not an executable."
                    " Please choose an existing executable filename."))
            return
            
        self.toollist[row] = {
            'menutext': menutext,
            'icon': icon,
            'executable': executable,
            'arguments': arguments,
            'redirect': redirect,
        }
        self.toolsList.currentItem().setText(menutext)
        self.changeButton.setEnabled(False)
        
    @pyqtSlot()
    def on_deleteButton_clicked(self):
        """
        Private slot to delete the selected entry.
        """
        row = self.toolsList.currentRow()
        if row < 0:
            return
        
        del self.toollist[row]
        itm = self.toolsList.takeItem(row)
        del itm
        if row >= len(self.toollist):
            row -= 1
        self.toolsList.setCurrentRow(row)
        self.on_toolsList_currentRowChanged(row)
        
    @pyqtSlot()
    def on_downButton_clicked(self):
        """
        Private slot to move an entry down in the list.
        """
        curr = self.toolsList.currentRow()
        self.__swap(curr, curr + 1)
        self.toolsList.clear()
        for tool in self.toollist:
            self.toolsList.addItem(tool['menutext'])
        self.toolsList.setCurrentRow(curr + 1)
        if curr + 1 == len(self.toollist):
            self.downButton.setEnabled(False)
        self.upButton.setEnabled(True)
        
    @pyqtSlot()
    def on_upButton_clicked(self):
        """
        Private slot to move an entry up in the list.
        """
        curr = self.toolsList.currentRow()
        self.__swap(curr - 1, curr)
        self.toolsList.clear()
        for tool in self.toollist:
            self.toolsList.addItem(tool['menutext'])
        self.toolsList.setCurrentRow(curr - 1)
        if curr - 1 == 0:
            self.upButton.setEnabled(False)
        self.downButton.setEnabled(True)
        
    @pyqtSlot()
    def on_separatorButton_clicked(self):
        """
        Private slot to add a menu separator.
        """
        self.toolsList.addItem('--')
        tool = {
            'menutext': '--',
            'icon': '',
            'executable': '',
            'arguments': '',
            'redirect': 'no',
        }
        self.toollist.append(tool)
        
    @pyqtSlot()
    def on_executableButton_clicked(self):
        """
        Private slot to handle the executable selection via a file selection
        dialog.
        """
        execfile = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select executable"),
            self.executableEdit.text(),
            "")
        if execfile:
            execfile = Utilities.toNativeSeparators(execfile)
            if not Utilities.isinpath(execfile):
                E5MessageBox.critical(
                    self,
                    self.tr("Select executable"),
                    self.tr(
                        "The selected file is not an executable."
                        " Please choose an executable filename."))
                return
            
            self.executableEdit.setText(execfile)
        
    @pyqtSlot()
    def on_iconButton_clicked(self):
        """
        Private slot to handle the icon selection via a file selection dialog.
        """
        icon = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select icon file"),
            self.iconEdit.text(),
            self.tr("Icon files (*.png)"))
        if icon:
            self.iconEdit.setText(icon)
    
    def on_toolsList_currentRowChanged(self, row):
        """
        Private slot to set the lineedits depending on the selected entry.
        
        @param row the row of the selected entry (integer)
        """
        if row >= 0 and row < len(self.toollist):
            if self.toollist[row]['menutext'] == '--':
                self.executableEdit.clear()
                self.menuEdit.clear()
                self.iconEdit.clear()
                self.argumentsEdit.clear()
                self.redirectCombo.setCurrentIndex(0)
            else:
                tool = self.toollist[row]
                self.menuEdit.setText(tool['menutext'])
                self.iconEdit.setText(tool['icon'])
                self.executableEdit.setText(tool['executable'])
                self.argumentsEdit.setText(tool['arguments'])
                self.redirectCombo.setCurrentIndex(
                    self.__findModeIndex(tool['redirect']))
            
            self.changeButton.setEnabled(False)
            self.deleteButton.setEnabled(True)
            
            if row != 0:
                self.upButton.setEnabled(True)
            else:
                self.upButton.setEnabled(False)
            
            if row + 1 != len(self.toollist):
                self.downButton.setEnabled(True)
            else:
                self.downButton.setEnabled(False)
        else:
            self.executableEdit.clear()
            self.menuEdit.clear()
            self.iconEdit.clear()
            self.argumentsEdit.clear()
            self.downButton.setEnabled(False)
            self.upButton.setEnabled(False)
            self.deleteButton.setEnabled(False)
            self.changeButton.setEnabled(False)
        
    def __toolEntryChanged(self):
        """
        Private slot to perform actions when a tool entry was changed.
        """
        row = self.toolsList.currentRow()
        if row >= 0 and \
           row < len(self.toollist) and \
           self.toollist[row]['menutext'] != '--':
            self.changeButton.setEnabled(True)
        
    def on_menuEdit_textChanged(self, text):
        """
        Private slot called, when the menu text was changed.
        
        @param text the new text (string) (ignored)
        """
        self.__toolEntryChanged()
        
    def on_iconEdit_textChanged(self, text):
        """
        Private slot called, when the icon path was changed.
        
        @param text the new text (string) (ignored)
        """
        self.__toolEntryChanged()
        
    def on_executableEdit_textChanged(self, text):
        """
        Private slot called, when the executable was changed.
        
        @param text the new text (string) (ignored)
        """
        self.__toolEntryChanged()
        
    def on_argumentsEdit_textChanged(self, text):
        """
        Private slot called, when the arguments string was changed.
        
        @param text the new text (string) (ignored)
        """
        self.__toolEntryChanged()
        
    @pyqtSlot(int)
    def on_redirectCombo_currentIndexChanged(self, index):
        """
        Private slot called, when the redirection mode was changed.
        
        @param index the selected mode index (integer) (ignored)
        """
        self.__toolEntryChanged()
        
    def getToollist(self):
        """
        Public method to retrieve the tools list.
        
        @return a list of tuples containing the menu text, the executable,
            the executables arguments and a redirection flag
        """
        return self.toollist[:]
        
    def __swap(self, itm1, itm2):
        """
        Private method used two swap two list entries given by their index.
        
        @param itm1 index of first entry (int)
        @param itm2 index of second entry (int)
        """
        tmp = self.toollist[itm1]
        self.toollist[itm1] = self.toollist[itm2]
        self.toollist[itm2] = tmp
