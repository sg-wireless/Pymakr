# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to search for text in files.
"""

from __future__ import unicode_literals

import os
import re

from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QDialog, QApplication, QMenu, QDialogButtonBox, \
    QTreeWidgetItem

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox, E5FileDialog

from .Ui_FindFileDialog import Ui_FindFileDialog

import Utilities
import Preferences
import UI.PixmapCache


class FindFileDialog(QDialog, Ui_FindFileDialog):
    """
    Class implementing a dialog to search for text in files.
    
    The occurrences found are displayed in a QTreeWidget showing the filename,
    the linenumber and the found text. The file will be opened upon a double
    click onto the respective entry of the list.
    
    @signal sourceFile(str, int, str, int, int) emitted to open a source file
        at a line
    @signal designerFile(str) emitted to open a Qt-Designer file
    """
    sourceFile = pyqtSignal(str, int, str, int, int)
    designerFile = pyqtSignal(str)
    
    lineRole = Qt.UserRole + 1
    startRole = Qt.UserRole + 2
    endRole = Qt.UserRole + 3
    replaceRole = Qt.UserRole + 4
    md5Role = Qt.UserRole + 5
    
    def __init__(self, project, replaceMode=False, parent=None):
        """
        Constructor
        
        @param project reference to the project object
        @param replaceMode flag indicating the replace dialog mode (boolean)
        @param parent parent widget of this dialog (QWidget)
        """
        super(FindFileDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.dirSelectButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.__replaceMode = replaceMode
        
        self.stopButton = \
            self.buttonBox.addButton(self.tr("Stop"),
                                     QDialogButtonBox.ActionRole)
        self.stopButton.setEnabled(False)
        
        self.findButton = \
            self.buttonBox.addButton(self.tr("Find"),
                                     QDialogButtonBox.ActionRole)
        self.findButton.setEnabled(False)
        self.findButton.setDefault(True)
        
        if self.__replaceMode:
            self.replaceButton.setEnabled(False)
            self.setWindowTitle(self.tr("Replace in Files"))
        else:
            self.replaceLabel.hide()
            self.replacetextCombo.hide()
            self.replaceButton.hide()
        
        self.findProgressLabel.setMaximumWidth(550)
        
        self.findtextCombo.setCompleter(None)
        self.replacetextCombo.setCompleter(None)
        
        self.searchHistory = Preferences.toList(
            Preferences.Prefs.settings.value(
                "FindFileDialog/SearchHistory"))
        self.replaceHistory = Preferences.toList(
            Preferences.Prefs.settings.value(
                "FindFileDialog/ReplaceHistory"))
        self.dirHistory = Preferences.toList(
            Preferences.Prefs.settings.value(
                "FindFileDialog/DirectoryHistory"))
        self.findtextCombo.addItems(self.searchHistory)
        self.replacetextCombo.addItems(self.replaceHistory)
        self.dirCombo.addItems(self.dirHistory)
        
        self.project = project
        
        self.findList.headerItem().setText(self.findList.columnCount(), "")
        self.findList.header().setSortIndicator(0, Qt.AscendingOrder)
        self.__section0Size = self.findList.header().sectionSize(0)
        self.findList.setExpandsOnDoubleClick(False)
        if self.__replaceMode:
            font = Preferences.getEditorOtherFonts("MonospacedFont")
            self.findList.setFont(font)

        # Qt Designer form files
        self.filterForms = r'.*\.ui$'
        self.formsExt = ['*.ui']
        
        # Corba interface files
        self.filterInterfaces = r'.*\.idl$'
        self.interfacesExt = ['*.idl']
        
        # Qt resources files
        self.filterResources = r'.*\.qrc$'
        self.resourcesExt = ['*.qrc']
        
        self.__cancelSearch = False
        self.__lastFileItem = None
        self.__populating = False
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__contextMenuRequested)
        
    def __createItem(self, file, line, text, start, end, replTxt="", md5=""):
        """
        Private method to create an entry in the file list.
        
        @param file filename of file (string)
        @param line line number (integer)
        @param text text found (string)
        @param start start position of match (integer)
        @param end end position of match (integer)
        @param replTxt text with replacements applied (string)
        @keyparam md5 MD5 hash of the file (string)
        """
        if self.__lastFileItem is None:
            # It's a new file
            self.__lastFileItem = QTreeWidgetItem(self.findList, [file])
            self.__lastFileItem.setFirstColumnSpanned(True)
            self.__lastFileItem.setExpanded(True)
            if self.__replaceMode:
                self.__lastFileItem.setFlags(
                    self.__lastFileItem.flags() |
                    Qt.ItemFlags(Qt.ItemIsUserCheckable | Qt.ItemIsTristate))
                # Qt bug:
                # item is not user checkable if setFirstColumnSpanned
                # is True (< 4.5.0)
            self.__lastFileItem.setData(0, self.md5Role, md5)
        
        itm = QTreeWidgetItem(self.__lastFileItem)
        itm.setTextAlignment(0, Qt.AlignRight)
        itm.setData(0, Qt.DisplayRole, line)
        itm.setData(1, Qt.DisplayRole, text)
        itm.setData(0, self.lineRole, line)
        itm.setData(0, self.startRole, start)
        itm.setData(0, self.endRole, end)
        itm.setData(0, self.replaceRole, replTxt)
        if self.__replaceMode:
            itm.setFlags(itm.flags() | Qt.ItemFlags(Qt.ItemIsUserCheckable))
            itm.setCheckState(0, Qt.Checked)
            self.replaceButton.setEnabled(True)
        
    def show(self, txt=""):
        """
        Public method to enable/disable the project button.
        
        @param txt text to be shown in the searchtext combo (string)
        """
        if self.project and self.project.isOpen():
            self.projectButton.setEnabled(True)
        else:
            self.projectButton.setEnabled(False)
            self.dirButton.setChecked(True)
            
        self.findtextCombo.setEditText(txt)
        self.findtextCombo.lineEdit().selectAll()
        self.findtextCombo.setFocus()
        
        if self.__replaceMode:
            self.findList.clear()
            self.replacetextCombo.setEditText("")
        
        super(FindFileDialog, self).show()
        
    def on_findtextCombo_editTextChanged(self, text):
        """
        Private slot to handle the editTextChanged signal of the find
        text combo.
        
        @param text (ignored)
        """
        self.__enableFindButton()
        
    def on_replacetextCombo_editTextChanged(self, text):
        """
        Private slot to handle the editTextChanged signal of the replace
        text combo.
        
        @param text (ignored)
        """
        self.__enableFindButton()
        
    def on_dirCombo_editTextChanged(self, text):
        """
        Private slot to handle the textChanged signal of the directory
        combo box.
        
        @param text (ignored)
        """
        self.__enableFindButton()
        
    @pyqtSlot()
    def on_projectButton_clicked(self):
        """
        Private slot to handle the selection of the project radio button.
        """
        self.__enableFindButton()
        
    @pyqtSlot()
    def on_dirButton_clicked(self):
        """
        Private slot to handle the selection of the project radio button.
        """
        self.__enableFindButton()
        
    @pyqtSlot()
    def on_filterCheckBox_clicked(self):
        """
        Private slot to handle the selection of the file filter check box.
        """
        self.__enableFindButton()
        
    @pyqtSlot(str)
    def on_filterEdit_textEdited(self, text):
        """
        Private slot to handle the textChanged signal of the file filter edit.
        
        @param text (ignored)
        """
        self.__enableFindButton()
        
    def __enableFindButton(self):
        """
        Private slot called to enable the find button.
        """
        if self.findtextCombo.currentText() == "" or \
           (self.__replaceMode and
            self.replacetextCombo.currentText() == "") or \
           (self.dirButton.isChecked() and
            (self.dirCombo.currentText() == "" or
             not os.path.exists(os.path.abspath(
                self.dirCombo.currentText())))) or \
           (self.filterCheckBox.isChecked() and self.filterEdit.text() == ""):
            self.findButton.setEnabled(False)
            self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        else:
            self.findButton.setEnabled(True)
            self.findButton.setDefault(True)
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.findButton:
            self.__doSearch()
        elif button == self.stopButton:
            self.__stopSearch()
        
    def __stripEol(self, txt):
        """
        Private method to strip the eol part.
        
        @param txt line of text that should be treated (string)
        @return text with eol stripped (string)
        """
        return txt.replace("\r", "").replace("\n", "")
        
    def __stopSearch(self):
        """
        Private slot to handle the stop button being pressed.
        """
        self.__cancelSearch = True
        
    def __doSearch(self):
        """
        Private slot to handle the find button being pressed.
        """
        if self.__replaceMode and \
           not e5App().getObject("ViewManager").checkAllDirty():
            return
        
        self.__cancelSearch = False
        
        if self.filterCheckBox.isChecked():
            fileFilter = self.filterEdit.text()
            fileFilterList = \
                ["^{0}$".format(filter.replace(".", "\.").replace("*", ".*"))
                 for filter in fileFilter.split(";")]
            filterRe = re.compile("|".join(fileFilterList))
        
        if self.projectButton.isChecked():
            if self.filterCheckBox.isChecked():
                files = [self.project.getRelativePath(file)
                         for file in
                         self.__getFileList(
                             self.project.getProjectPath(), filterRe)]
            else:
                files = []
                if self.sourcesCheckBox.isChecked():
                    files += self.project.pdata["SOURCES"]
                if self.formsCheckBox.isChecked():
                    files += self.project.pdata["FORMS"]
                if self.interfacesCheckBox.isChecked():
                    files += self.project.pdata["INTERFACES"]
                if self.resourcesCheckBox.isChecked():
                    files += self.project.pdata["RESOURCES"]
        elif self.dirButton.isChecked():
            if not self.filterCheckBox.isChecked():
                filters = []
                if self.sourcesCheckBox.isChecked():
                    filters.extend(
                        ["^{0}$".format(
                            assoc.replace(".", "\.").replace("*", ".*"))
                         for assoc in list(
                             Preferences.getEditorLexerAssocs().keys())
                         if assoc not in self.formsExt + self.interfacesExt])
                if self.formsCheckBox.isChecked():
                    filters.append(self.filterForms)
                if self.interfacesCheckBox.isChecked():
                    filters.append(self.filterInterfaces)
                if self.resourcesCheckBox.isChecked():
                    filters.append(self.filterResources)
                filterString = "|".join(filters)
                filterRe = re.compile(filterString)
            files = self.__getFileList(
                os.path.abspath(self.dirCombo.currentText()),
                filterRe)
        elif self.openFilesButton.isChecked():
            vm = e5App().getObject("ViewManager")
            vm.checkAllDirty()
            files = vm.getOpenFilenames()
        
        self.findList.clear()
        QApplication.processEvents()
        QApplication.processEvents()
        self.findProgress.setMaximum(len(files))
        
        # retrieve the values
        reg = self.regexpCheckBox.isChecked()
        wo = self.wordCheckBox.isChecked()
        cs = self.caseCheckBox.isChecked()
        ct = self.findtextCombo.currentText()
        if reg:
            txt = ct
        else:
            txt = re.escape(ct)
        if wo:
            txt = "\\b{0}\\b".format(txt)
        flags = re.UNICODE | re.LOCALE
        if not cs:
            flags |= re.IGNORECASE
        try:
            search = re.compile(txt, flags)
        except re.error as why:
            E5MessageBox.critical(
                self,
                self.tr("Invalid search expression"),
                self.tr("""<p>The search expression is not valid.</p>"""
                        """<p>Error: {0}</p>""").format(str(why)))
            self.stopButton.setEnabled(False)
            self.findButton.setEnabled(True)
            self.findButton.setDefault(True)
            return
        # reset the findtextCombo
        if ct in self.searchHistory:
            self.searchHistory.remove(ct)
        self.searchHistory.insert(0, ct)
        self.findtextCombo.clear()
        self.findtextCombo.addItems(self.searchHistory)
        Preferences.Prefs.settings.setValue(
            "FindFileDialog/SearchHistory",
            self.searchHistory[:30])
        
        if self.__replaceMode:
            replTxt = self.replacetextCombo.currentText()
            if replTxt in self.replaceHistory:
                self.replaceHistory.remove(replTxt)
            self.replaceHistory.insert(0, replTxt)
            self.replacetextCombo.clear()
            self.replacetextCombo.addItems(self.replaceHistory)
            Preferences.Prefs.settings.setValue(
                "FindFileDialog/ReplaceHistory",
                self.replaceHistory[:30])
        
        if self.dirButton.isChecked():
            searchDir = self.dirCombo.currentText()
            if searchDir in self.dirHistory:
                self.dirHistory.remove(searchDir)
            self.dirHistory.insert(0, searchDir)
            self.dirCombo.clear()
            self.dirCombo.addItems(self.dirHistory)
            Preferences.Prefs.settings.setValue(
                "FindFileDialog/DirectoryHistory",
                self.dirHistory[:30])
        
        # set the button states
        self.stopButton.setEnabled(True)
        self.stopButton.setDefault(True)
        self.findButton.setEnabled(False)
        
        # now go through all the files
        self.__populating = True
        self.findList.setUpdatesEnabled(False)
        progress = 0
        breakSearch = False
        occurrences = 0
        fileOccurrences = 0
        for file in files:
            self.__lastFileItem = None
            found = False
            if self.__cancelSearch or breakSearch:
                break
            
            self.findProgressLabel.setPath(file)
            
            if self.projectButton.isChecked():
                fn = os.path.join(self.project.ppath, file)
            else:
                fn = file
            # read the file and split it into textlines
            try:
                text, encoding, hash = Utilities.readEncodedFileWithHash(fn)
                lines = text.splitlines(True)
            except (UnicodeError, IOError):
                progress += 1
                self.findProgress.setValue(progress)
                continue
            
            # now perform the search and display the lines found
            count = 0
            for line in lines:
                if self.__cancelSearch:
                    break
                
                count += 1
                contains = search.search(line)
                if contains:
                    occurrences += 1
                    found = True
                    start = contains.start()
                    end = contains.end()
                    if self.__replaceMode:
                        rline = search.sub(replTxt, line)
                    else:
                        rline = ""
                    line = self.__stripEol(line)
                    if len(line) > 1024:
                        line = "{0} ...".format(line[:1024])
                    if self.__replaceMode:
                        if len(rline) > 1024:
                            rline = "{0} ...".format(line[:1024])
                        line = "- {0}\n+ {1}".format(
                            line, self.__stripEol(rline))
                    self.__createItem(file, count, line, start, end,
                                      rline, hash)
                    
                    if self.feelLikeCheckBox.isChecked():
                        fn = os.path.join(self.project.ppath, file)
                        self.sourceFile.emit(fn, count, "", start, end)
                        QApplication.processEvents()
                        breakSearch = True
                        break
                
                QApplication.processEvents()
            
            if found:
                fileOccurrences += 1
            progress += 1
            self.findProgress.setValue(progress)
        
        if not files:
            self.findProgress.setMaximum(1)
            self.findProgress.setValue(1)
        
        resultFormat = self.tr("{0} / {1}", "occurrences / files")
        self.findProgressLabel.setPath(resultFormat.format(
            self.tr("%n occurrence(s)", "", occurrences),
            self.tr("%n file(s)", "", fileOccurrences)))
        
        self.findList.setUpdatesEnabled(True)
        self.findList.sortItems(self.findList.sortColumn(),
                                self.findList.header().sortIndicatorOrder())
        self.findList.resizeColumnToContents(1)
        if self.__replaceMode:
            self.findList.header().resizeSection(0, self.__section0Size + 30)
        self.findList.header().setStretchLastSection(True)
        self.__populating = False
        
        self.stopButton.setEnabled(False)
        self.findButton.setEnabled(True)
        self.findButton.setDefault(True)
        
        if breakSearch:
            self.close()
        
    def on_findList_itemDoubleClicked(self, itm, column):
        """
        Private slot to handle the double click on a file item.
        
        It emits the signal
        sourceFile or designerFile depending on the file extension.
        
        @param itm the double clicked tree item (QTreeWidgetItem)
        @param column column that was double clicked (integer) (ignored)
        """
        if itm.parent():
            file = itm.parent().text(0)
            line = itm.data(0, self.lineRole)
            start = itm.data(0, self.startRole)
            end = itm.data(0, self.endRole)
        else:
            file = itm.text(0)
            line = 1
            start = 0
            end = 0
        
        if self.project:
            fn = os.path.join(self.project.ppath, file)
        else:
            fn = file
        if fn.endswith('.ui'):
            self.designerFile.emit(fn)
        else:
            self.sourceFile.emit(fn, line, "", start, end)
        
    @pyqtSlot()
    def on_dirSelectButton_clicked(self):
        """
        Private slot to display a directory selection dialog.
        """
        directory = E5FileDialog.getExistingDirectory(
            self,
            self.tr("Select directory"),
            self.dirCombo.currentText(),
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
            
        if directory:
            self.dirCombo.setEditText(Utilities.toNativeSeparators(directory))
        
    def __getFileList(self, path, filterRe):
        """
        Private method to get a list of files to search.
        
        @param path the root directory to search in (string)
        @param filterRe regular expression defining the filter
            criteria (regexp object)
        @return list of files to be processed (list of strings)
        """
        path = os.path.abspath(path)
        files = []
        for dirname, _, names in os.walk(path):
            files.extend([os.path.join(dirname, f)
                          for f in names
                          if re.match(filterRe, f)]
                         )
        return files
        
    def setSearchDirectory(self, searchDir):
        """
        Public slot to set the name of the directory to search in.
        
        @param searchDir name of the directory to search in (string)
        """
        self.dirButton.setChecked(True)
        self.dirCombo.setEditText(Utilities.toNativeSeparators(searchDir))
        
    def setOpenFiles(self):
        """
        Public slot to set the mode to search in open files.
        """
        self.openFilesButton.setChecked(True)
        
    @pyqtSlot()
    def on_replaceButton_clicked(self):
        """
        Private slot to perform the requested replace actions.
        """
        self.findProgress.setMaximum(self.findList.topLevelItemCount())
        self.findProgress.setValue(0)
        
        progress = 0
        for index in range(self.findList.topLevelItemCount()):
            itm = self.findList.topLevelItem(index)
            if itm.checkState(0) in [Qt.PartiallyChecked, Qt.Checked]:
                file = itm.text(0)
                origHash = itm.data(0, self.md5Role)
                
                self.findProgressLabel.setPath(file)
                
                if self.projectButton.isChecked():
                    fn = os.path.join(self.project.ppath, file)
                else:
                    fn = file
                
                # read the file and split it into textlines
                try:
                    text, encoding, hash = \
                        Utilities.readEncodedFileWithHash(fn)
                    lines = text.splitlines(True)
                except (UnicodeError, IOError) as err:
                    E5MessageBox.critical(
                        self,
                        self.tr("Replace in Files"),
                        self.tr(
                            """<p>Could not read the file <b>{0}</b>."""
                            """ Skipping it.</p><p>Reason: {1}</p>""")
                        .format(fn, str(err))
                    )
                    progress += 1
                    self.findProgress.setValue(progress)
                    continue
                
                # Check the original and the current hash. Skip the file,
                # if hashes are different.
                if origHash != hash:
                    E5MessageBox.critical(
                        self,
                        self.tr("Replace in Files"),
                        self.tr(
                            """<p>The current and the original hash of the"""
                            """ file <b>{0}</b> are different. Skipping it."""
                            """</p><p>Hash 1: {1}</p><p>Hash 2: {2}</p>""")
                        .format(fn, origHash, hash)
                    )
                    progress += 1
                    self.findProgress.setValue(progress)
                    continue
                
                # replace the lines authorized by the user
                for cindex in range(itm.childCount()):
                    citm = itm.child(cindex)
                    if citm.checkState(0) == Qt.Checked:
                        line = citm.data(0, self.lineRole)
                        rline = citm.data(0, self.replaceRole)
                        lines[line - 1] = rline
                
                # write the file
                txt = "".join(lines)
                try:
                    Utilities.writeEncodedFile(fn, txt, encoding)
                except (IOError, Utilities.CodingError, UnicodeError) as err:
                    E5MessageBox.critical(
                        self,
                        self.tr("Replace in Files"),
                        self.tr(
                            """<p>Could not save the file <b>{0}</b>."""
                            """ Skipping it.</p><p>Reason: {1}</p>""")
                        .format(fn, str(err))
                    )
            
            progress += 1
            self.findProgress.setValue(progress)
        
        self.findProgressLabel.setPath("")
        
        self.findList.clear()
        self.replaceButton.setEnabled(False)
        self.findButton.setEnabled(True)
        self.findButton.setDefault(True)
        
    def __contextMenuRequested(self, pos):
        """
        Private slot to handle the context menu request.
        
        @param pos position the context menu shall be shown (QPoint)
        """
        menu = QMenu(self)
        
        menu.addAction(self.tr("Open"), self.__openFile)
        menu.addAction(self.tr("Copy Path to Clipboard"),
                       self.__copyToClipboard)
        
        menu.exec_(QCursor.pos())
        
    def __openFile(self):
        """
        Private slot to open the currently selected entry.
        """
        itm = self.findList.selectedItems()[0]
        self.on_findList_itemDoubleClicked(itm, 0)
        
    def __copyToClipboard(self):
        """
        Private method to copy the path of an entry to the clipboard.
        """
        itm = self.findList.selectedItems()[0]
        if itm.parent():
            fn = itm.parent().text(0)
        else:
            fn = itm.text(0)
        
        cb = QApplication.clipboard()
        cb.setText(fn)
