# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Plugin installation dialog.
"""

from __future__ import unicode_literals

import os
import sys
import shutil
import zipfile
import compileall
import glob
try:  # Py3
    import urllib.parse as parse
except (ImportError):
    import urlparse as parse    # __IGNORE_WARNING__

from PyQt5.QtCore import pyqtSlot, Qt, QDir, QFileInfo
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QAbstractButton, \
    QApplication, QDialog, QVBoxLayout

from E5Gui import E5FileDialog
from E5Gui.E5MainWindow import E5MainWindow

from .Ui_PluginInstallDialog import Ui_PluginInstallDialog

import Utilities
import Preferences

from Utilities.uic import compileUiFiles


class PluginInstallWidget(QWidget, Ui_PluginInstallDialog):
    """
    Class implementing the Plugin installation dialog.
    """
    def __init__(self, pluginManager, pluginFileNames, parent=None):
        """
        Constructor
        
        @param pluginManager reference to the plugin manager object
        @param pluginFileNames list of plugin files suggested for
            installation (list of strings)
        @param parent parent of this dialog (QWidget)
        """
        super(PluginInstallWidget, self).__init__(parent)
        self.setupUi(self)
        
        if pluginManager is None:
            # started as external plugin installer
            from .PluginManager import PluginManager
            self.__pluginManager = PluginManager(doLoadPlugins=False)
            self.__external = True
        else:
            self.__pluginManager = pluginManager
            self.__external = False
        
        self.__backButton = self.buttonBox.addButton(
            self.tr("< Back"), QDialogButtonBox.ActionRole)
        self.__nextButton = self.buttonBox.addButton(
            self.tr("Next >"), QDialogButtonBox.ActionRole)
        self.__finishButton = self.buttonBox.addButton(
            self.tr("Install"), QDialogButtonBox.ActionRole)
        
        self.__closeButton = self.buttonBox.button(QDialogButtonBox.Close)
        self.__cancelButton = self.buttonBox.button(QDialogButtonBox.Cancel)
        
        userDir = self.__pluginManager.getPluginDir("user")
        if userDir is not None:
            self.destinationCombo.addItem(
                self.tr("User plugins directory"),
                userDir)
        
        globalDir = self.__pluginManager.getPluginDir("global")
        if globalDir is not None and os.access(globalDir, os.W_OK):
            self.destinationCombo.addItem(
                self.tr("Global plugins directory"),
                globalDir)
        
        self.__installedDirs = []
        self.__installedFiles = []
        
        self.__restartNeeded = False
        
        downloadDir = QDir(Preferences.getPluginManager("DownloadPath"))
        for pluginFileName in pluginFileNames:
            fi = QFileInfo(pluginFileName)
            if fi.isRelative():
                pluginFileName = QFileInfo(
                    downloadDir, fi.fileName()).absoluteFilePath()
            self.archivesList.addItem(pluginFileName)
            self.archivesList.sortItems()
        
        self.__currentIndex = 0
        self.__selectPage()
    
    def restartNeeded(self):
        """
        Public method to check, if a restart of the IDE is required.
        
        @return flag indicating a restart is required (boolean)
        """
        return self.__restartNeeded
    
    def __createArchivesList(self):
        """
        Private method to create a list of plugin archive names.
        
        @return list of plugin archive names (list of strings)
        """
        archivesList = []
        for row in range(self.archivesList.count()):
            archivesList.append(self.archivesList.item(row).text())
        return archivesList

    def __selectPage(self):
        """
        Private method to show the right wizard page.
        """
        self.wizard.setCurrentIndex(self.__currentIndex)
        if self.__currentIndex == 0:
            self.__backButton.setEnabled(False)
            self.__nextButton.setEnabled(self.archivesList.count() > 0)
            self.__finishButton.setEnabled(False)
            self.__closeButton.hide()
            self.__cancelButton.show()
        elif self.__currentIndex == 1:
            self.__backButton.setEnabled(True)
            self.__nextButton.setEnabled(self.destinationCombo.count() > 0)
            self.__finishButton.setEnabled(False)
            self.__closeButton.hide()
            self.__cancelButton.show()
        else:
            self.__backButton.setEnabled(True)
            self.__nextButton.setEnabled(False)
            self.__finishButton.setEnabled(True)
            self.__closeButton.hide()
            self.__cancelButton.show()
            
            msg = self.tr(
                "Plugin ZIP-Archives:\n{0}\n\nDestination:\n{1} ({2})")\
                .format("\n".join(self.__createArchivesList()),
                        self.destinationCombo.currentText(),
                        self.destinationCombo.itemData(
                            self.destinationCombo.currentIndex())
                        )
            self.summaryEdit.setPlainText(msg)
    
    @pyqtSlot()
    def on_addArchivesButton_clicked(self):
        """
        Private slot to select plugin ZIP-archives via a file selection dialog.
        """
        dn = Preferences.getPluginManager("DownloadPath")
        archives = E5FileDialog.getOpenFileNames(
            self,
            self.tr("Select plugin ZIP-archives"),
            dn,
            self.tr("Plugin archive (*.zip)"))
        
        if archives:
            matchflags = Qt.MatchFixedString
            if not Utilities.isWindowsPlatform():
                matchflags |= Qt.MatchCaseSensitive
            for archive in archives:
                if len(self.archivesList.findItems(archive, matchflags)) == 0:
                    # entry not in list already
                    self.archivesList.addItem(archive)
            self.archivesList.sortItems()
        
        self.__nextButton.setEnabled(self.archivesList.count() > 0)
    
    @pyqtSlot()
    def on_archivesList_itemSelectionChanged(self):
        """
        Private slot called, when the selection of the archives list changes.
        """
        self.removeArchivesButton.setEnabled(
            len(self.archivesList.selectedItems()) > 0)
    
    @pyqtSlot()
    def on_removeArchivesButton_clicked(self):
        """
        Private slot to remove archives from the list.
        """
        for archiveItem in self.archivesList.selectedItems():
            itm = self.archivesList.takeItem(
                self.archivesList.row(archiveItem))
            del itm
        
        self.__nextButton.setEnabled(self.archivesList.count() > 0)
    
    @pyqtSlot(QAbstractButton)
    def on_buttonBox_clicked(self, button):
        """
        Private slot to handle the click of a button of the button box.
        
        @param button reference to the button pressed (QAbstractButton)
        """
        if button == self.__backButton:
            self.__currentIndex -= 1
            self.__selectPage()
        elif button == self.__nextButton:
            self.__currentIndex += 1
            self.__selectPage()
        elif button == self.__finishButton:
            self.__finishButton.setEnabled(False)
            self.__installPlugins()
            if not Preferences.getPluginManager("ActivateExternal"):
                Preferences.setPluginManager("ActivateExternal", True)
                self.__restartNeeded = True
            self.__closeButton.show()
            self.__cancelButton.hide()
    
    def __installPlugins(self):
        """
        Private method to install the selected plugin archives.
        
        @return flag indicating success (boolean)
        """
        res = True
        self.summaryEdit.clear()
        for archive in self.__createArchivesList():
            self.summaryEdit.append(
                self.tr("Installing {0} ...").format(archive))
            ok, msg, restart = self.__installPlugin(archive)
            res = res and ok
            if ok:
                self.summaryEdit.append(self.tr("  ok"))
            else:
                self.summaryEdit.append(msg)
            if restart:
                self.__restartNeeded = True
        self.summaryEdit.append("\n")
        if res:
            self.summaryEdit.append(self.tr(
                """The plugins were installed successfully."""))
        else:
            self.summaryEdit.append(self.tr(
                """Some plugins could not be installed."""))
        
        return res
    
    def __installPlugin(self, archiveFilename):
        """
        Private slot to install the selected plugin.
        
        @param archiveFilename name of the plugin archive
            file (string)
        @return flag indicating success (boolean), error message
            upon failure (string) and flag indicating a restart
            of the IDE is required (boolean)
        """
        installedPluginName = ""
        
        archive = archiveFilename
        destination = self.destinationCombo.itemData(
            self.destinationCombo.currentIndex())
        
        # check if archive is a local url
        url = parse.urlparse(archive)
        if url[0].lower() == 'file':
            archive = url[2]

        # check, if the archive exists
        if not os.path.exists(archive):
            return False, \
                self.tr(
                    """<p>The archive file <b>{0}</b> does not exist. """
                    """Aborting...</p>""").format(archive), \
                False
        
        # check, if the archive is a valid zip file
        if not zipfile.is_zipfile(archive):
            return False, \
                self.tr(
                    """<p>The file <b>{0}</b> is not a valid plugin """
                    """ZIP-archive. Aborting...</p>""").format(archive), \
                False
        
        # check, if the destination is writeable
        if not os.access(destination, os.W_OK):
            return False, \
                self.tr(
                    """<p>The destination directory <b>{0}</b> is not """
                    """writeable. Aborting...</p>""").format(destination), \
                False
        
        zip = zipfile.ZipFile(archive, "r")
        
        # check, if the archive contains a valid plugin
        pluginFound = False
        pluginFileName = ""
        for name in zip.namelist():
            if self.__pluginManager.isValidPluginName(name):
                installedPluginName = name[:-3]
                pluginFound = True
                pluginFileName = name
                break
        
        if not pluginFound:
            return False, \
                self.tr(
                    """<p>The file <b>{0}</b> is not a valid plugin """
                    """ZIP-archive. Aborting...</p>""").format(archive), \
                False
        
        # parse the plugin module's plugin header
        pluginSource = Utilities.decode(zip.read(pluginFileName))[0]
        packageName = ""
        internalPackages = []
        needsRestart = False
        pyqtApi = 0
        doCompile = True
        for line in pluginSource.splitlines():
            if line.startswith("packageName"):
                tokens = line.split("=")
                if tokens[0].strip() == "packageName" and \
                   tokens[1].strip()[1:-1] != "__core__":
                    if tokens[1].strip()[0] in ['"', "'"]:
                        packageName = tokens[1].strip()[1:-1]
                    else:
                        if tokens[1].strip() == "None":
                            packageName = "None"
            elif line.startswith("internalPackages"):
                tokens = line.split("=")
                token = tokens[1].strip()[1:-1]
                # it is a comma separated string
                internalPackages = [p.strip() for p in token.split(",")]
            elif line.startswith("needsRestart"):
                tokens = line.split("=")
                needsRestart = tokens[1].strip() == "True"
            elif line.startswith("pyqtApi"):
                tokens = line.split("=")
                try:
                    pyqtApi = int(tokens[1].strip())
                except ValueError:
                    pass
            elif line.startswith("doNotCompile"):
                tokens = line.split("=")
                if tokens[1].strip() == "True":
                    doCompile = False
            elif line.startswith("# End-Of-Header"):
                break
        
        if not packageName:
            return False, \
                self.tr(
                    """<p>The plugin module <b>{0}</b> does not contain """
                    """a 'packageName' attribute. Aborting...</p>""")\
                .format(pluginFileName), \
                False
        
        if pyqtApi < 2:
            return False, \
                self.tr(
                    """<p>The plugin module <b>{0}</b> does not conform"""
                    """ with the PyQt v2 API. Aborting...</p>""")\
                .format(pluginFileName), \
                False
        
        # check, if it is a plugin, that collides with others
        if not os.path.exists(os.path.join(destination, pluginFileName)) and \
           packageName != "None" and \
           os.path.exists(os.path.join(destination, packageName)):
            return False, \
                self.tr("""<p>The plugin package <b>{0}</b> exists. """
                        """Aborting...</p>""")\
                    .format(os.path.join(destination, packageName)), \
                False
        
        if os.path.exists(os.path.join(destination, pluginFileName)) and \
           packageName != "None" and \
           not os.path.exists(os.path.join(destination, packageName)):
            return False, \
                self.tr("""<p>The plugin module <b>{0}</b> exists. """
                        """Aborting...</p>""")\
                    .format(os.path.join(destination, pluginFileName)), \
                False
        
        activatePlugin = False
        if not self.__external:
            activatePlugin = \
                not self.__pluginManager.isPluginLoaded(
                    installedPluginName) or \
                (self.__pluginManager.isPluginLoaded(installedPluginName) and
                 self.__pluginManager.isPluginActive(installedPluginName))
            # try to unload a plugin with the same name
            self.__pluginManager.unloadPlugin(installedPluginName)
        
        # uninstall existing plugin first to get clean conditions
        self.__uninstallPackage(destination, pluginFileName, packageName)
        
        # clean sys.modules
        reload_ = self.__pluginManager.removePluginFromSysModules(
            installedPluginName, packageName, internalPackages)
        
        # now do the installation
        self.__installedDirs = []
        self.__installedFiles = []
        try:
            if packageName != "None":
                namelist = sorted(zip.namelist())
                tot = len(namelist)
                prog = 0
                self.progress.setMaximum(tot)
                QApplication.processEvents()
                for name in namelist:
                    self.progress.setValue(prog)
                    QApplication.processEvents()
                    prog += 1
                    if name == pluginFileName or \
                       name.startswith("{0}/".format(packageName)) or \
                       name.startswith("{0}\\".format(packageName)):
                        outname = name.replace("/", os.sep)
                        outname = os.path.join(destination, outname)
                        if outname.endswith("/") or outname.endswith("\\"):
                            # it is a directory entry
                            outname = outname[:-1]
                            if not os.path.exists(outname):
                                self.__makedirs(outname)
                        else:
                            # it is a file
                            d = os.path.dirname(outname)
                            if not os.path.exists(d):
                                self.__makedirs(d)
                            f = open(outname, "wb")
                            f.write(zip.read(name))
                            f.close()
                            self.__installedFiles.append(outname)
                self.progress.setValue(tot)
                # now compile user interface files
                compileUiFiles(os.path.join(destination, packageName), True)
            else:
                outname = os.path.join(destination, pluginFileName)
                f = open(outname, "w", encoding="utf-8")
                f.write(pluginSource)
                f.close()
                self.__installedFiles.append(outname)
        except os.error as why:
            self.__rollback()
            return False, \
                self.tr(
                    "Error installing plugin. Reason: {0}").format(str(why)), \
                False
        except IOError as why:
            self.__rollback()
            return False, \
                self.tr(
                    "Error installing plugin. Reason: {0}").format(str(why)), \
                False
        except OSError as why:
            self.__rollback()
            return False, \
                self.tr(
                    "Error installing plugin. Reason: {0}").format(str(why)), \
                False
        except:
            sys.stderr.write("Unspecific exception installing plugin.\n")
            self.__rollback()
            return False, \
                self.tr("Unspecific exception installing plugin."), \
                False
        
        # now compile the plugins
        if doCompile:
            dir = os.path.join(destination, packageName)
            files = os.path.join(destination, pluginFileName)
            if sys.version_info[0] == 2:
                dir = dir.encode(sys.getfilesystemencoding())
                files = files.encode(sys.getfilesystemencoding())
            os.path.join_unicode = False
            compileall.compile_dir(dir, quiet=True)
            compileall.compile_file(files, quiet=True)
            os.path.join_unicode = True
        
        if not self.__external:
            # now load and activate the plugin
            self.__pluginManager.loadPlugin(installedPluginName, destination,
                                            reload_)
            if activatePlugin:
                self.__pluginManager.activatePlugin(installedPluginName)
        
        return True, "", needsRestart
    
    def __rollback(self):
        """
        Private method to rollback a failed installation.
        """
        for fname in self.__installedFiles:
            if os.path.exists(fname):
                os.remove(fname)
        for dname in self.__installedDirs:
            if os.path.exists(dname):
                shutil.rmtree(dname)
    
    def __makedirs(self, name, mode=0o777):
        """
        Private method to create a directory and all intermediate ones.
        
        This is an extended version of the Python one in order to
        record the created directories.
        
        @param name name of the directory to create (string)
        @param mode permission to set for the new directory (integer)
        """
        head, tail = os.path.split(name)
        if not tail:
            head, tail = os.path.split(head)
        if head and tail and not os.path.exists(head):
            self.__makedirs(head, mode)
            if tail == os.curdir:
                # xxx/newdir/. exists if xxx/newdir exists
                return
        os.mkdir(name, mode)
        self.__installedDirs.append(name)
    
    def __uninstallPackage(self, destination, pluginFileName, packageName):
        """
        Private method to uninstall an already installed plugin to prepare
        the update.
        
        @param destination name of the plugin directory (string)
        @param pluginFileName name of the plugin file (string)
        @param packageName name of the plugin package (string)
        """
        if packageName == "" or packageName == "None":
            packageDir = None
        else:
            packageDir = os.path.join(destination, packageName)
        pluginFile = os.path.join(destination, pluginFileName)
        
        try:
            if packageDir and os.path.exists(packageDir):
                shutil.rmtree(packageDir)
            
            fnameo = "{0}o".format(pluginFile)
            if os.path.exists(fnameo):
                os.remove(fnameo)
            
            fnamec = "{0}c".format(pluginFile)
            if os.path.exists(fnamec):
                os.remove(fnamec)
            
            pluginDirCache = os.path.join(
                os.path.dirname(pluginFile), "__pycache__")
            if os.path.exists(pluginDirCache):
                pluginFileName = os.path.splitext(
                    os.path.basename(pluginFile))[0]
                for fnameo in glob.glob(
                    os.path.join(pluginDirCache,
                                 "{0}*.pyo".format(pluginFileName))):
                    os.remove(fnameo)
                for fnamec in glob.glob(
                    os.path.join(pluginDirCache,
                                 "{0}*.pyc".format(pluginFileName))):
                    os.remove(fnamec)
            
            os.remove(pluginFile)
        except (IOError, OSError, os.error):
            # ignore some exceptions
            pass


class PluginInstallDialog(QDialog):
    """
    Class for the dialog variant.
    """
    def __init__(self, pluginManager, pluginFileNames, parent=None):
        """
        Constructor
        
        @param pluginManager reference to the plugin manager object
        @param pluginFileNames list of plugin files suggested for
            installation (list of strings)
        @param parent reference to the parent widget (QWidget)
        """
        super(PluginInstallDialog, self).__init__(parent)
        self.setSizeGripEnabled(True)
        
        self.__layout = QVBoxLayout(self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__layout)
        
        self.cw = PluginInstallWidget(pluginManager, pluginFileNames, self)
        size = self.cw.size()
        self.__layout.addWidget(self.cw)
        self.resize(size)
        self.setWindowTitle(self.cw.windowTitle())
        
        self.cw.buttonBox.accepted.connect(self.accept)
        self.cw.buttonBox.rejected.connect(self.reject)
    
    def restartNeeded(self):
        """
        Public method to check, if a restart of the IDE is required.
        
        @return flag indicating a restart is required (boolean)
        """
        return self.cw.restartNeeded()


class PluginInstallWindow(E5MainWindow):
    """
    Main window class for the standalone dialog.
    """
    def __init__(self, pluginFileNames, parent=None):
        """
        Constructor
        
        @param pluginFileNames list of plugin files suggested for
            installation (list of strings)
        @param parent reference to the parent widget (QWidget)
        """
        super(PluginInstallWindow, self).__init__(parent)
        self.cw = PluginInstallWidget(None, pluginFileNames, self)
        size = self.cw.size()
        self.setCentralWidget(self.cw)
        self.resize(size)
        self.setWindowTitle(self.cw.windowTitle())
        
        self.setStyle(Preferences.getUI("Style"),
                      Preferences.getUI("StyleSheet"))
        
        self.cw.buttonBox.accepted.connect(self.close)
        self.cw.buttonBox.rejected.connect(self.close)
