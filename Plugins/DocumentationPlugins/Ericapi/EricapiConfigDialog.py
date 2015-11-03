# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the parameters for eric6_api.
"""

from __future__ import unicode_literals

import sys
import os
import copy

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from E5Gui.E5Completers import E5FileCompleter, E5DirCompleter
from E5Gui import E5FileDialog

from .Ui_EricapiConfigDialog import Ui_EricapiConfigDialog
import Utilities
import UI.PixmapCache
import DocumentationTools

from eric6config import getConfig


class EricapiConfigDialog(QDialog, Ui_EricapiConfigDialog):
    """
    Class implementing a dialog to enter the parameters for eric6_api.
    """
    def __init__(self, project, parms=None, parent=None):
        """
        Constructor
        
        @param project reference to the project object (Project.Project)
        @param parms parameters to set in the dialog
        @param parent parent widget of this dialog
        """
        super(EricapiConfigDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.outputFileButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.ignoreDirButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        for language in sorted(
                DocumentationTools.supportedExtensionsDictForApis.keys()):
            self.languagesList.addItem(language)
        
        self.ppath = project.getProjectPath()
        self.project = project
        
        self.__initializeDefaults()
        
        # get a copy of the defaults to store the user settings
        self.parameters = copy.deepcopy(self.defaults)
        
        # combine it with the values of parms
        if parms is not None:
            for key, value in list(parms.items()):
                self.parameters[key] = parms[key]
        self.parameters['outputFile'] = \
            Utilities.toNativeSeparators(self.parameters['outputFile'])
        
        self.outputFileCompleter = E5FileCompleter(self.outputFileEdit)
        self.ignoreDirCompleter = E5DirCompleter(self.ignoreDirEdit)
        
        self.recursionCheckBox.setChecked(self.parameters['useRecursion'])
        self.includePrivateCheckBox.setChecked(
            self.parameters['includePrivate'])
        self.outputFileEdit.setText(self.parameters['outputFile'])
        self.baseEdit.setText(self.parameters['basePackage'])
        self.ignoreDirsList.clear()
        for d in self.parameters['ignoreDirectories']:
            self.ignoreDirsList.addItem(d)
        self.sourceExtEdit.setText(
            ", ".join(self.parameters['sourceExtensions']))
        self.excludeFilesEdit.setText(
            ", ".join(self.parameters['ignoreFilePatterns']))
        for language in self.parameters['languages']:
            if language == "Python":
                # convert Python to the more specific Python2
                language = "Python2"
            items = self.languagesList.findItems(
                language, Qt.MatchFlags(Qt.MatchExactly))
            items and items[0].setSelected(True)
    
    def __initializeDefaults(self):
        """
        Private method to set the default values.
        
        These are needed later on to generate the commandline
        parameters.
        """
        self.defaults = {
            'useRecursion': False,
            'includePrivate': False,
            'outputFile': '',
            'basePackage': '',
            'ignoreDirectories': [],
            'ignoreFilePatterns': [],
            'sourceExtensions': [],
        }
        
        lang = self.project.getProjectLanguage()
        if lang in DocumentationTools.supportedExtensionsDictForApis:
            self.defaults['languages'] = [lang]
        else:
            self.defaults['languages'] = ["Python3"]
    
    def generateParameters(self):
        """
        Public method that generates the commandline parameters.
        
        It generates a list of strings to be used
        to set the QProcess arguments for the ericapi call and
        a dictionary containing the non default parameters. This
        dictionary can be passed back upon object generation to overwrite
        the default settings.
        
        @return a tuple of the commandline parameters and non default
            parameters (list of strings, dictionary)
        """
        parms = {}
        args = []
        
        # 1. the program name
        args.append(sys.executable)
        args.append(
            Utilities.normabsjoinpath(getConfig('ericDir'), "eric6_api.py"))
        
        # 2. the commandline options
        if self.parameters['outputFile'] != self.defaults['outputFile']:
            parms['outputFile'] = Utilities.fromNativeSeparators(
                self.project.getRelativePath(self.parameters['outputFile']))
            args.append('-o')
            if os.path.isabs(self.parameters['outputFile']):
                args.append(self.parameters['outputFile'])
            else:
                args.append(
                    os.path.join(self.ppath, self.parameters['outputFile']))
        else:
            self.parameters['outputFile'] = self.defaults['outputFile']
        if self.parameters['basePackage'] != self.defaults['basePackage']:
            parms['basePackage'] = self.parameters['basePackage']
            args.append('-b')
            args.append(self.parameters['basePackage'])
        if self.parameters['ignoreDirectories'] != \
                self.defaults['ignoreDirectories']:
            parms['ignoreDirectories'] = \
                self.parameters['ignoreDirectories'][:]
            for d in self.parameters['ignoreDirectories']:
                args.append('-x')
                args.append(d)
        if self.parameters['ignoreFilePatterns'] != \
                self.defaults['ignoreFilePatterns']:
            parms['ignoreFilePatterns'] = \
                self.parameters['ignoreFilePatterns'][:]
            for pattern in self.parameters['ignoreFilePatterns']:
                args.append("--exclude-file={0}".format(pattern))
        if self.parameters['useRecursion'] != self.defaults['useRecursion']:
            parms['useRecursion'] = self.parameters['useRecursion']
            args.append('-r')
        if self.parameters['sourceExtensions'] != \
                self.defaults['sourceExtensions']:
            parms['sourceExtensions'] = self.parameters['sourceExtensions'][:]
            for ext in self.parameters['sourceExtensions']:
                args.append('-t')
                args.append(ext)
        if self.parameters['includePrivate'] != \
                self.defaults['includePrivate']:
            parms['includePrivate'] = self.parameters['includePrivate']
            args.append('-p')
        parms['languages'] = self.parameters['languages'][:]
        for lang in self.parameters['languages']:
            args.append('--language={0}'.format(lang))
        
        return (args, parms)

    @pyqtSlot()
    def on_outputFileButton_clicked(self):
        """
        Private slot to select the output file.
        
        It displays a file selection dialog to
        select the file the api is written to.
        """
        startFile = Utilities.fromNativeSeparators(self.outputFileEdit.text())
        if not startFile:
            startPath = Utilities.fromNativeSeparators(
                self.project.getProjectPath())
            startFile = (startPath + "/" +
                         self.project.getProjectName() + ".api")
        filename = E5FileDialog.getSaveFileName(
            self,
            self.tr("Select output file"),
            startFile,
            self.tr("API files (*.api);;All files (*)"))
            
        if filename:
            # make it relative, if it is in a subdirectory of the project path
            fn = Utilities.toNativeSeparators(filename)
            fn = self.project.getRelativePath(fn)
            self.outputFileEdit.setText(fn)

    def on_outputFileEdit_textChanged(self, filename):
        """
        Private slot to enable/disable the "OK" button.
        
        @param filename name of the file (string)
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(filename != "")

    @pyqtSlot()
    def on_ignoreDirButton_clicked(self):
        """
        Private slot to select a directory to be ignored.
        
        It displays a directory selection dialog to
        select a directory to be ignored.
        """
        startDir = Utilities.fromNativeSeparators(self.ignoreDirEdit.text())
        if not startDir:
            startDir = self.ppath
        directory = E5FileDialog.getExistingDirectory(
            self,
            self.tr("Select directory to exclude"),
            startDir,
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
            
        if directory:
            # make it relative, if it is a subdirectory of the project path
            dn = Utilities.toNativeSeparators(directory)
            dn = self.project.getRelativePath(dn)
            while dn.endswith(os.sep):
                dn = dn[:-1]
            self.ignoreDirEdit.setText(dn)
    
    @pyqtSlot()
    def on_addButton_clicked(self):
        """
        Private slot to add the directory displayed to the listview.
        
        The directory in the ignore directories
        line edit is moved to the listbox above and the edit is cleared.
        """
        basename = os.path.basename(self.ignoreDirEdit.text())
        if basename:
            self.ignoreDirsList.addItem(basename)
            self.ignoreDirEdit.clear()

    @pyqtSlot()
    def on_deleteButton_clicked(self):
        """
        Private slot to delete the currently selected directory of the listbox.
        """
        itm = self.ignoreDirsList.takeItem(self.ignoreDirsList.currentRow())
        del itm

    def accept(self):
        """
        Public slot called by the Ok button.
        
        It saves the values in the parameters dictionary.
        """
        self.parameters['useRecursion'] = self.recursionCheckBox.isChecked()
        self.parameters['includePrivate'] = \
            self.includePrivateCheckBox.isChecked()
        outfile = self.outputFileEdit.text()
        if outfile != '':
            outfile = os.path.normpath(outfile)
        self.parameters['outputFile'] = outfile
        self.parameters['basePackage'] = self.baseEdit.text()
        self.parameters['ignoreDirectories'] = []
        for row in range(0, self.ignoreDirsList.count()):
            itm = self.ignoreDirsList.item(row)
            self.parameters['ignoreDirectories'].append(
                os.path.normpath(itm.text()))
        extensions = self.sourceExtEdit.text().split(',')
        self.parameters['sourceExtensions'] = \
            [ext.strip() for ext in extensions if len(ext) > 0]
        patterns = self.excludeFilesEdit.text().split(',')
        self.parameters['ignoreFilePatterns'] = \
            [pattern.strip() for pattern in patterns]
        self.parameters['languages'] = []
        for itm in self.languagesList.selectedItems():
            self.parameters['languages'].append(itm.text())
        
        # call the accept slot of the base class
        super(EricapiConfigDialog, self).accept()
