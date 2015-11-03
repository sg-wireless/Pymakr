# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Programs page.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os
import re

from PyQt5.QtCore import pyqtSlot, Qt, QProcess
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem, QHeaderView, \
    QDialog, QDialogButtonBox

from E5Gui.E5Application import e5App

from .Ui_ProgramsDialog import Ui_ProgramsDialog

import Preferences
import Utilities


class ProgramsDialog(QDialog, Ui_ProgramsDialog):
    """
    Class implementing the Programs page.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent The parent widget of this dialog. (QWidget)
        """
        super(ProgramsDialog, self).__init__(parent)
        self.setupUi(self)
        self.setObjectName("ProgramsDialog")
        self.setWindowFlags(Qt.Window)
        
        self.__hasSearched = False
        
        self.programsList.headerItem().setText(
            self.programsList.columnCount(), "")
        
        self.searchButton = self.buttonBox.addButton(
            self.tr("Search"), QDialogButtonBox.ActionRole)
        self.searchButton.setToolTip(
            self.tr("Press to search for programs"))
        
    def show(self):
        """
        Public slot to show the dialog.
        """
        QDialog.show(self)
        if not self.__hasSearched:
            self.on_programsSearchButton_clicked()
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.searchButton:
            self.on_programsSearchButton_clicked()
        
    @pyqtSlot()
    def on_programsSearchButton_clicked(self):
        """
        Private slot to search for all supported/required programs.
        """
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        
        self.programsList.clear()
        header = self.programsList.header()
        header.setSortIndicator(0, Qt.AscendingOrder)
        header.setSortIndicatorShown(False)
        
        # 1. do the Qt4/Qt5 programs
        # 1a. Translation Converter
        exe = Utilities.isWindowsPlatform() and \
            "{0}.exe".format(Utilities.generateQtToolName("lrelease")) or \
            Utilities.generateQtToolName("lrelease")
        exe = os.path.join(Utilities.getQtBinariesPath(), exe)
        version = self.__createProgramEntry(
            self.tr("Translation Converter (Qt)"), exe, '-version',
            'lrelease', -1)
        # 1b. Qt Designer
        if Utilities.isWindowsPlatform():
            exe = os.path.join(
                Utilities.getQtBinariesPath(),
                "{0}.exe".format(Utilities.generateQtToolName("designer")))
        elif Utilities.isMacPlatform():
            exe = Utilities.getQtMacBundle("designer")
        else:
            exe = os.path.join(
                Utilities.getQtBinariesPath(),
                Utilities.generateQtToolName("designer"))
        self.__createProgramEntry(
            self.tr("Qt Designer"), exe, version=version)
        # 1c. Qt Linguist
        if Utilities.isWindowsPlatform():
            exe = os.path.join(
                Utilities.getQtBinariesPath(),
                "{0}.exe".format(Utilities.generateQtToolName("linguist")))
        elif Utilities.isMacPlatform():
            exe = Utilities.getQtMacBundle("linguist")
        else:
            exe = os.path.join(
                Utilities.getQtBinariesPath(),
                Utilities.generateQtToolName("linguist"))
        self.__createProgramEntry(
            self.tr("Qt Linguist"), exe, version=version)
        # 1d. Qt Assistant
        if Utilities.isWindowsPlatform():
            exe = os.path.join(
                Utilities.getQtBinariesPath(),
                "{0}.exe".format(Utilities.generateQtToolName("assistant")))
        elif Utilities.isMacPlatform():
            exe = Utilities.getQtMacBundle("assistant")
        else:
            exe = os.path.join(
                Utilities.getQtBinariesPath(),
                Utilities.generateQtToolName("assistant"))
        self.__createProgramEntry(
            self.tr("Qt Assistant"), exe, version=version)
        
        # 2. do the PyQt programs
        # 2a. Translation Extractor PyQt4
        self.__createProgramEntry(
            self.tr("Translation Extractor (Python, PyQt4)"),
            Utilities.isWindowsPlatform() and "pylupdate4.exe" or "pylupdate4",
            '-version', 'pylupdate', -1)
        # 2b. Forms Compiler PyQt4
        self.__createProgramEntry(
            self.tr("Forms Compiler (Python, PyQt4)"),
            Utilities.isWindowsPlatform() and "pyuic4.bat" or "pyuic4",
            '--version', 'Python User', 4)
        # 2c. Resource Compiler PyQt4
        self.__createProgramEntry(
            self.tr("Resource Compiler (Python, PyQt4)"),
            Utilities.isWindowsPlatform() and "pyrcc4.exe" or "pyrcc4",
            '-version', 'Resource Compiler', -1)
        # 2d. Translation Extractor PyQt5
        self.__createProgramEntry(
            self.tr("Translation Extractor (Python, PyQt5)"),
            Utilities.isWindowsPlatform() and "pylupdate5.exe" or "pylupdate5",
            '-version', 'pylupdate', -1)
        # 2e. Forms Compiler PyQt5
        self.__createProgramEntry(
            self.tr("Forms Compiler (Python, PyQt5)"),
            Utilities.isWindowsPlatform() and "pyuic5.bat" or "pyuic5",
            '--version', 'Python User', 4)
        # 2f. Resource Compiler PyQt5
        self.__createProgramEntry(
            self.tr("Resource Compiler (Python, PyQt5)"),
            Utilities.isWindowsPlatform() and "pyrcc5.exe" or "pyrcc5",
            '-version', 'Resource Compiler', -1)
        
        # 3. do the PySide programs
        # 3a. Translation Extractor PySide
        self.__createProgramEntry(
            self.tr("Translation Extractor (Python, PySide)"),
            Utilities.generatePySideToolPath("pyside-lupdate"),
            '-version', '', -1, versionRe='lupdate')
        # 3b. Forms Compiler PySide
        self.__createProgramEntry(
            self.tr("Forms Compiler (Python, PySide)"),
            Utilities.generatePySideToolPath("pyside-uic"),
            '--version', 'PySide User', 5, versionCleanup=(0, -1))
        # 3.c Resource Compiler PySide
        self.__createProgramEntry(
            self.tr("Resource Compiler (Python, PySide)"),
            Utilities.generatePySideToolPath("pyside-rcc"),
            '-version', 'Resource Compiler', -1)
        
        # 4. do the Ruby programs
        # 4a. Forms Compiler for Qt4
        self.__createProgramEntry(
            self.tr("Forms Compiler (Ruby, Qt4)"),
            Utilities.isWindowsPlatform() and "rbuic4.exe" or "rbuic4",
            '-version', 'Qt', -1)
        # 4b. Resource Compiler for Qt4
        self.__createProgramEntry(
            self.tr("Resource Compiler (Ruby, Qt4)"),
            Utilities.isWindowsPlatform() and "rbrcc.exe" or "rbrcc",
            '-version', 'Ruby Resource Compiler', -1)
        
        # 5. do the CORBA programs
        # 5a. omniORB
        exe = Preferences.getCorba("omniidl")
        if Utilities.isWindowsPlatform():
            exe += ".exe"
        self.__createProgramEntry(
            self.tr("CORBA IDL Compiler"), exe, '-V', 'omniidl', -1)
        
        # 6. do the spell checking entry
        try:
            import enchant
            try:
                text = os.path.dirname(enchant.__file__)
            except AttributeError:
                text = "enchant"
            try:
                version = enchant.__version__
            except AttributeError:
                version = self.tr("(unknown)")
        except (ImportError, AttributeError, OSError):
            text = "enchant"
            version = ""
        self.__createEntry(
            self.tr("Spell Checker - PyEnchant"), text, version)
        
        # 7. do the pygments entry
        try:
            import pygments
            try:
                text = os.path.dirname(pygments.__file__)
            except AttributeError:
                text = "pygments"
            try:
                version = pygments.__version__
            except AttributeError:
                version = self.tr("(unknown)")
        except (ImportError, AttributeError, OSError):
            text = "pygments"
            version = ""
        self.__createEntry(
            self.tr("Source Highlighter - Pygments"), text, version)
        
        # do the plugin related programs
        pm = e5App().getObject("PluginManager")
        for info in pm.getPluginExeDisplayData():
            if info["programEntry"]:
                self.__createProgramEntry(
                    info["header"],
                    info["exe"],
                    versionCommand=info["versionCommand"],
                    versionStartsWith=info["versionStartsWith"],
                    versionPosition=info["versionPosition"],
                    version=info["version"],
                    versionCleanup=info["versionCleanup"],
                )
            else:
                self.__createEntry(
                    info["header"],
                    info["text"],
                    info["version"]
                )
        
        self.programsList.sortByColumn(0, Qt.AscendingOrder)
        QApplication.restoreOverrideCursor()
        
        self.__hasSearched = True

    def __createProgramEntry(self, description, exe,
                             versionCommand="", versionStartsWith="",
                             versionPosition=0, version="",
                             versionCleanup=None, versionRe=None):
        """
        Private method to generate a program entry.
        
        @param description descriptive text (string)
        @param exe name of the executable program (string)
        @param versionCommand command line switch to get the version info
            (string) if this is empty, the given version will be shown.
        @param versionStartsWith start of line identifying version info
            (string)
        @param versionPosition index of part containing the version info
            (integer)
        @keyparam version version string to show (string)
        @keyparam versionCleanup tuple of two integers giving string positions
            start and stop for the version string (tuple of integers)
        @keyparam versionRe regexp to determine the line identifying version
            info (string). Takes precedence over versionStartsWith.
        @return version string of detected or given version (string)
        """
        itmList = self.programsList.findItems(
            description, Qt.MatchCaseSensitive)
        if itmList:
            itm = itmList[0]
        else:
            itm = QTreeWidgetItem(self.programsList, [description])
        font = itm.font(0)
        font.setBold(True)
        itm.setFont(0, font)
        if not exe:
            itm.setText(1, self.tr("(not configured)"))
        else:
            if os.path.isabs(exe):
                if not Utilities.isExecutable(exe):
                    exe = ""
            else:
                exe = Utilities.getExecutablePath(exe)
            if exe:
                if versionCommand and \
                   (versionStartsWith != "" or
                    (versionRe is not None and versionRe != "")) and \
                   versionPosition:
                    proc = QProcess()
                    proc.setProcessChannelMode(QProcess.MergedChannels)
                    proc.start(exe, [versionCommand])
                    finished = proc.waitForFinished(10000)
                    if finished:
                        output = str(proc.readAllStandardOutput(),
                                     Preferences.getSystem("IOEncoding"),
                                     'replace')
                        if versionRe is None:
                            versionRe = "^{0}".format(
                                re.escape(versionStartsWith))
                        versionRe = re.compile(versionRe, re.UNICODE)
                        for line in output.splitlines():
                            if versionRe.search(line):
                                try:
                                    version = line.split()[versionPosition]
                                    if versionCleanup:
                                        version = version[
                                            versionCleanup[0]:versionCleanup[1]
                                        ]
                                    break
                                except IndexError:
                                    version = self.tr("(unknown)")
                        else:
                            version = self.tr("(unknown)")
                    else:
                        version = self.tr("(not executable)")
                QTreeWidgetItem(itm, [exe, version])
                itm.setExpanded(True)
            else:
                itm.setText(1, self.tr("(not found)"))
        QApplication.processEvents()
        self.programsList.header().resizeSections(QHeaderView.ResizeToContents)
        self.programsList.header().setStretchLastSection(True)
        return version
        
    def __createEntry(self, description, entryText, entryVersion):
        """
        Private method to generate a program entry.
        
        @param description descriptive text (string)
        @param entryText text to show (string)
        @param entryVersion version string to show (string).
        """
        itm = QTreeWidgetItem(self.programsList, [description])
        font = itm.font(0)
        font.setBold(True)
        itm.setFont(0, font)
        
        if len(entryVersion):
            QTreeWidgetItem(itm, [entryText, entryVersion])
            itm.setExpanded(True)
        else:
            itm.setText(1, self.tr("(not found)"))
        QApplication.processEvents()
        self.programsList.header().resizeSections(QHeaderView.ResizeToContents)
        self.programsList.header().setStretchLastSection(True)
