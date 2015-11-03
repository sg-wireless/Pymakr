# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Help Documentation configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, QUrl

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5FileDialog

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_HelpDocumentationPage import Ui_HelpDocumentationPage

import Preferences
import Utilities
import UI.PixmapCache


class HelpDocumentationPage(ConfigurationPageBase, Ui_HelpDocumentationPage):
    """
    Class implementing the Help Documentation configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(HelpDocumentationPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("HelpDocumentationPage")
        
        self.python2DocDirButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.pythonDocDirButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.qt4DocDirButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.qt5DocDirButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.pyqt4DocDirButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.pyqt5DocDirButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.pysideDocDirButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.python2DocDirCompleter = E5FileCompleter(self.python2DocDirEdit)
        self.pythonDocDirCompleter = E5FileCompleter(self.pythonDocDirEdit)
        self.qt4DocDirCompleter = E5FileCompleter(self.qt4DocDirEdit)
        self.qt5DocDirCompleter = E5FileCompleter(self.qt5DocDirEdit)
        self.pyqt4DocDirCompleter = E5FileCompleter(self.pyqt4DocDirEdit)
        self.pyqt5DocDirCompleter = E5FileCompleter(self.pyqt5DocDirEdit)
        self.pysideDocDirCompleter = E5FileCompleter(self.pysideDocDirEdit)
        
        try:
            import PyQt5        # __IGNORE_WARNING__
        except ImportError:
            self.pyqt5Group.setEnabled(False)
        
        pyside2, pyside3 = Utilities.checkPyside()
        if pyside2 or pyside3:
            self.pysideGroup.setEnabled(True)
        else:
            self.pysideGroup.setEnabled(False)
        
        # set initial values
        self.python2DocDirEdit.setText(
            Preferences.getHelp("Python2DocDir"))
        self.pythonDocDirEdit.setText(
            Preferences.getHelp("PythonDocDir"))
        self.qt4DocDirEdit.setText(
            Preferences.getHelp("Qt4DocDir"))
        self.qt5DocDirEdit.setText(
            Preferences.getHelp("Qt5DocDir"))
        self.pyqt4DocDirEdit.setText(
            Preferences.getHelp("PyQt4DocDir"))
        self.pyqt5DocDirEdit.setText(
            Preferences.getHelp("PyQt5DocDir"))
        self.pysideDocDirEdit.setText(
            Preferences.getHelp("PySideDocDir"))
        
    def save(self):
        """
        Public slot to save the Help Documentation configuration.
        """
        Preferences.setHelp(
            "Python2DocDir",
            self.python2DocDirEdit.text())
        Preferences.setHelp(
            "PythonDocDir",
            self.pythonDocDirEdit.text())
        Preferences.setHelp(
            "Qt4DocDir",
            self.qt4DocDirEdit.text())
        Preferences.setHelp(
            "Qt5DocDir",
            self.qt5DocDirEdit.text())
        Preferences.setHelp(
            "PyQt4DocDir",
            self.pyqt4DocDirEdit.text())
        Preferences.setHelp(
            "PyQt5DocDir",
            self.pyqt5DocDirEdit.text())
        Preferences.setHelp(
            "PySideDocDir",
            self.pysideDocDirEdit.text())
        
    @pyqtSlot()
    def on_python2DocDirButton_clicked(self):
        """
        Private slot to select the Python 2 documentation directory.
        """
        entry = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select Python 2 documentation entry"),
            QUrl(self.python2DocDirEdit.text()).path(),
            self.tr(
                "HTML Files (*.html *.htm);;"
                "Compressed Help Files (*.chm);;"
                "All Files (*)"))
        
        if entry:
            self.python2DocDirEdit.setText(Utilities.toNativeSeparators(entry))
        
    @pyqtSlot()
    def on_pythonDocDirButton_clicked(self):
        """
        Private slot to select the Python 3 documentation directory.
        """
        entry = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select Python 3 documentation entry"),
            QUrl(self.pythonDocDirEdit.text()).path(),
            self.tr(
                "HTML Files (*.html *.htm);;"
                "Compressed Help Files (*.chm);;"
                "All Files (*)"))
        
        if entry:
            self.pythonDocDirEdit.setText(Utilities.toNativeSeparators(entry))
        
    @pyqtSlot()
    def on_qt4DocDirButton_clicked(self):
        """
        Private slot to select the Qt4 documentation directory.
        """
        entry = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select Qt4 documentation entry"),
            QUrl(self.qt4DocDirEdit.text()).path(),
            self.tr("HTML Files (*.html *.htm);;All Files (*)"))
        
        if entry:
            self.qt4DocDirEdit.setText(Utilities.toNativeSeparators(entry))
        
    @pyqtSlot()
    def on_qt5DocDirButton_clicked(self):
        """
        Private slot to select the Qt5 documentation directory.
        """
        entry = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select Qt5 documentation entry"),
            QUrl(self.qt5DocDirEdit.text()).path(),
            self.tr("HTML Files (*.html *.htm);;All Files (*)"))
        
        if entry:
            self.qt5DocDirEdit.setText(Utilities.toNativeSeparators(entry))
        
    @pyqtSlot()
    def on_pyqt4DocDirButton_clicked(self):
        """
        Private slot to select the PyQt5 documentation directory.
        """
        entry = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select PyQt5 documentation entry"),
            QUrl(self.pyqt4DocDirEdit.text()).path(),
            self.tr("HTML Files (*.html *.htm);;All Files (*)"))
        
        if entry:
            self.pyqt4DocDirEdit.setText(Utilities.toNativeSeparators(entry))
        
    @pyqtSlot()
    def on_pyqt5DocDirButton_clicked(self):
        """
        Private slot to select the PyQt5 documentation directory.
        """
        entry = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select PyQt5 documentation entry"),
            QUrl(self.pyqt4DocDirEdit.text()).path(),
            self.tr("HTML Files (*.html *.htm);;All Files (*)"))
        
        if entry:
            self.pyqt5DocDirEdit.setText(Utilities.toNativeSeparators(entry))
        
    @pyqtSlot()
    def on_pysideDocDirButton_clicked(self):
        """
        Private slot to select the PySide documentation directory.
        """
        entry = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select PySide documentation entry"),
            QUrl(self.pysideDocDirEdit.text()).path(),
            self.tr("HTML Files (*.html *.htm);;All Files (*)"))
        
        if entry:
            self.pysideDocDirEdit.setText(Utilities.toNativeSeparators(entry))
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = HelpDocumentationPage()
    return page
