# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class used to display the resources part of the project.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import QThread, QFileInfo, pyqtSignal, PYQT_VERSION, QProcess
from PyQt5.QtWidgets import QDialog, QApplication, QMenu

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox, E5FileDialog
from E5Gui.E5ProgressDialog import E5ProgressDialog

from .ProjectBrowserModel import ProjectBrowserFileItem, \
    ProjectBrowserSimpleDirectoryItem, ProjectBrowserDirectoryItem, \
    ProjectBrowserResourceType
from .ProjectBaseBrowser import ProjectBaseBrowser

import UI.PixmapCache

import Preferences
import Utilities


class ProjectResourcesBrowser(ProjectBaseBrowser):
    """
    A class used to display the resources part of the project.
    
    @signal appendStderr(str) emitted after something was received from
        a QProcess on stderr
    @signal sourceFile(str) emitted to open a resources file in an editor
    @signal closeSourceWindow(str) emitted after a file has been
        removed/deleted from the project
    @signal showMenu(str, QMenu) emitted when a menu is about to be shown.
        The name of the menu and a reference to the menu are given.
    """
    appendStderr = pyqtSignal(str)
    showMenu = pyqtSignal(str, QMenu)
    
    RCFilenameFormatPython = "{0}_rc.py"
    RCFilenameFormatRuby = "{0}_rc.rb"
    
    def __init__(self, project, parent=None):
        """
        Constructor
        
        @param project reference to the project object
        @param parent parent widget of this browser (QWidget)
        """
        ProjectBaseBrowser.__init__(self, project, ProjectBrowserResourceType,
                                    parent)
        
        self.selectedItemsFilter = \
            [ProjectBrowserFileItem, ProjectBrowserSimpleDirectoryItem]
        
        self.setWindowTitle(self.tr('Resources'))

        self.setWhatsThis(self.tr(
            """<b>Project Resources Browser</b>"""
            """<p>This allows to easily see all resources contained in the"""
            """ current project. Several actions can be executed via the"""
            """ context menu.</p>"""
        ))
        
        self.compileProc = None
        
    def _createPopupMenus(self):
        """
        Protected overloaded method to generate the popup menu.
        """
        self.menuActions = []
        self.multiMenuActions = []
        self.dirMenuActions = []
        self.dirMultiMenuActions = []
        
        self.menu = QMenu(self)
        if self.project.getProjectType() in \
                ["Qt4", "Qt4C", "PyQt5", "PyQt5C", "E6Plugin",
                 "PySide", "PySideC"]:
            self.menu.addAction(
                self.tr('Compile resource'),
                self.__compileResource)
            self.menu.addAction(
                self.tr('Compile all resources'),
                self.__compileAllResources)
            self.menu.addSeparator()
        else:
            if self.hooks["compileResource"] is not None:
                self.menu.addAction(
                    self.hooksMenuEntries.get(
                        "compileResource",
                        self.tr('Compile resource')),
                    self.__compileResource)
            if self.hooks["compileAllResources"] is not None:
                self.menu.addAction(
                    self.hooksMenuEntries.get(
                        "compileAllResources",
                        self.tr('Compile all resources')),
                    self.__compileAllResources)
            if self.hooks["compileResource"] is not None or \
               self.hooks["compileAllResources"] is not None:
                self.menu.addSeparator()
        self.menu.addAction(self.tr('Open'), self.__openFile)
        self.menu.addSeparator()
        act = self.menu.addAction(self.tr('Rename file'), self._renameFile)
        self.menuActions.append(act)
        act = self.menu.addAction(
            self.tr('Remove from project'), self._removeFile)
        self.menuActions.append(act)
        act = self.menu.addAction(self.tr('Delete'), self.__deleteFile)
        self.menuActions.append(act)
        self.menu.addSeparator()
        if self.project.getProjectType() in \
                ["Qt4", "Qt4C", "PyQt5", "PyQt5C", "E6Plugin",
                 "PySide", "PySideC"]:
            self.menu.addAction(
                self.tr('New resource...'), self.__newResource)
        else:
            if self.hooks["newResource"] is not None:
                self.menu.addAction(
                    self.hooksMenuEntries.get(
                        "newResource",
                        self.tr('New resource...')), self.__newResource)
        self.menu.addAction(
            self.tr('Add resources...'), self.__addResourceFiles)
        self.menu.addAction(
            self.tr('Add resources directory...'),
            self.__addResourcesDirectory)
        self.menu.addSeparator()
        self.menu.addAction(
            self.tr('Copy Path to Clipboard'), self._copyToClipboard)
        self.menu.addSeparator()
        self.menu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.menu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.menu.addSeparator()
        self.menu.addAction(self.tr('Configure...'), self._configure)

        self.backMenu = QMenu(self)
        if self.project.getProjectType() in \
                ["Qt4", "Qt4C", "PyQt5", "PyQt5C", "E6Plugin",
                 "PySide", "PySideC"]:
            self.backMenu.addAction(
                self.tr('Compile all resources'),
                self.__compileAllResources)
            self.backMenu.addSeparator()
            self.backMenu.addAction(
                self.tr('New resource...'), self.__newResource)
        else:
            if self.hooks["compileAllResources"] is not None:
                self.backMenu.addAction(
                    self.hooksMenuEntries.get(
                        "compileAllResources",
                        self.tr('Compile all resources')),
                    self.__compileAllResources)
                self.backMenu.addSeparator()
            if self.hooks["newResource"] is not None:
                self.backMenu.addAction(
                    self.hooksMenuEntries.get(
                        "newResource",
                        self.tr('New resource...')), self.__newResource)
        self.backMenu.addAction(
            self.tr('Add resources...'), self.project.addResourceFiles)
        self.backMenu.addAction(
            self.tr('Add resources directory...'),
            self.project.addResourceDir)
        self.backMenu.addSeparator()
        self.backMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.backMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.backMenu.addSeparator()
        self.backMenu.addAction(self.tr('Configure...'), self._configure)
        self.backMenu.setEnabled(False)

        # create the menu for multiple selected files
        self.multiMenu = QMenu(self)
        if self.project.getProjectType() in \
                ["Qt4", "Qt4C", "PyQt5", "PyQt5C", "E6Plugin",
                 "PySide", "PySideC"]:
            act = self.multiMenu.addAction(
                self.tr('Compile resources'),
                self.__compileSelectedResources)
            self.multiMenu.addSeparator()
        else:
            if self.hooks["compileSelectedResources"] is not None:
                act = self.multiMenu.addAction(
                    self.hooksMenuEntries.get(
                        "compileSelectedResources",
                        self.tr('Compile resources')),
                    self.__compileSelectedResources)
                self.multiMenu.addSeparator()
        self.multiMenu.addAction(self.tr('Open'), self.__openFile)
        self.multiMenu.addSeparator()
        act = self.multiMenu.addAction(
            self.tr('Remove from project'), self._removeFile)
        self.multiMenuActions.append(act)
        act = self.multiMenu.addAction(
            self.tr('Delete'), self.__deleteFile)
        self.multiMenuActions.append(act)
        self.multiMenu.addSeparator()
        self.multiMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.multiMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.multiMenu.addSeparator()
        self.multiMenu.addAction(self.tr('Configure...'), self._configure)

        self.dirMenu = QMenu(self)
        if self.project.getProjectType() in \
                ["Qt4", "Qt4C", "PyQt5", "PyQt5C", "E6Plugin",
                 "PySide", "PySideC"]:
            self.dirMenu.addAction(
                self.tr('Compile all resources'),
                self.__compileAllResources)
            self.dirMenu.addSeparator()
        else:
            if self.hooks["compileAllResources"] is not None:
                self.dirMenu.addAction(
                    self.hooksMenuEntries.get(
                        "compileAllResources",
                        self.tr('Compile all resources')),
                    self.__compileAllResources)
                self.dirMenu.addSeparator()
        act = self.dirMenu.addAction(
            self.tr('Remove from project'), self._removeDir)
        self.dirMenuActions.append(act)
        act = self.dirMenu.addAction(
            self.tr('Delete'), self._deleteDirectory)
        self.dirMenuActions.append(act)
        self.dirMenu.addSeparator()
        self.dirMenu.addAction(
            self.tr('New resource...'), self.__newResource)
        self.dirMenu.addAction(
            self.tr('Add resources...'), self.__addResourceFiles)
        self.dirMenu.addAction(
            self.tr('Add resources directory...'),
            self.__addResourcesDirectory)
        self.dirMenu.addSeparator()
        self.dirMenu.addAction(
            self.tr('Copy Path to Clipboard'), self._copyToClipboard)
        self.dirMenu.addSeparator()
        self.dirMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.dirMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.dirMenu.addSeparator()
        self.dirMenu.addAction(self.tr('Configure...'), self._configure)
        
        self.dirMultiMenu = QMenu(self)
        if self.project.getProjectType() in \
                ["Qt4", "Qt4C", "PyQt5", "PyQt5C", "E6Plugin",
                 "PySide", "PySideC"]:
            self.dirMultiMenu.addAction(
                self.tr('Compile all resources'),
                self.__compileAllResources)
            self.dirMultiMenu.addSeparator()
        else:
            if self.hooks["compileAllResources"] is not None:
                self.dirMultiMenu.addAction(
                    self.hooksMenuEntries.get(
                        "compileAllResources",
                        self.tr('Compile all resources')),
                    self.__compileAllResources)
                self.dirMultiMenu.addSeparator()
        self.dirMultiMenu.addAction(
            self.tr('Add resources...'),
            self.project.addResourceFiles)
        self.dirMultiMenu.addAction(
            self.tr('Add resources directory...'),
            self.project.addResourceDir)
        self.dirMultiMenu.addSeparator()
        self.dirMultiMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.dirMultiMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.dirMultiMenu.addSeparator()
        self.dirMultiMenu.addAction(
            self.tr('Configure...'), self._configure)
        
        self.menu.aboutToShow.connect(self.__showContextMenu)
        self.multiMenu.aboutToShow.connect(self.__showContextMenuMulti)
        self.dirMenu.aboutToShow.connect(self.__showContextMenuDir)
        self.dirMultiMenu.aboutToShow.connect(self.__showContextMenuDirMulti)
        self.backMenu.aboutToShow.connect(self.__showContextMenuBack)
        self.mainMenu = self.menu
        
    def _contextMenuRequested(self, coord):
        """
        Protected slot to show the context menu.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        if not self.project.isOpen():
            return
        
        try:
            categories = self.getSelectedItemsCountCategorized(
                [ProjectBrowserFileItem, ProjectBrowserSimpleDirectoryItem])
            cnt = categories["sum"]
            if cnt <= 1:
                index = self.indexAt(coord)
                if index.isValid():
                    self._selectSingleItem(index)
                    categories = self.getSelectedItemsCountCategorized(
                        [ProjectBrowserFileItem,
                         ProjectBrowserSimpleDirectoryItem])
                    cnt = categories["sum"]
                        
            bfcnt = categories[str(ProjectBrowserFileItem)]
            sdcnt = categories[str(ProjectBrowserSimpleDirectoryItem)]
            if cnt > 1 and cnt == bfcnt:
                self.multiMenu.popup(self.mapToGlobal(coord))
            elif cnt > 1 and cnt == sdcnt:
                self.dirMultiMenu.popup(self.mapToGlobal(coord))
            else:
                index = self.indexAt(coord)
                if cnt == 1 and index.isValid():
                    if bfcnt == 1:
                        self.menu.popup(self.mapToGlobal(coord))
                    elif sdcnt == 1:
                        self.dirMenu.popup(self.mapToGlobal(coord))
                    else:
                        self.backMenu.popup(self.mapToGlobal(coord))
                else:
                    self.backMenu.popup(self.mapToGlobal(coord))
        except:
            pass
        
    def __showContextMenu(self):
        """
        Private slot called by the menu aboutToShow signal.
        """
        ProjectBaseBrowser._showContextMenu(self, self.menu)
        
        self.showMenu.emit("Main", self.menu)
        
    def __showContextMenuMulti(self):
        """
        Private slot called by the multiMenu aboutToShow signal.
        """
        ProjectBaseBrowser._showContextMenuMulti(self, self.multiMenu)
        
        self.showMenu.emit("MainMulti", self.multiMenu)
        
    def __showContextMenuDir(self):
        """
        Private slot called by the dirMenu aboutToShow signal.
        """
        ProjectBaseBrowser._showContextMenuDir(self, self.dirMenu)
        
        self.showMenu.emit("MainDir", self.dirMenu)
        
    def __showContextMenuDirMulti(self):
        """
        Private slot called by the dirMultiMenu aboutToShow signal.
        """
        ProjectBaseBrowser._showContextMenuDirMulti(self, self.dirMultiMenu)
        
        self.showMenu.emit("MainDirMulti", self.dirMultiMenu)
        
    def __showContextMenuBack(self):
        """
        Private slot called by the backMenu aboutToShow signal.
        """
        ProjectBaseBrowser._showContextMenuBack(self, self.backMenu)
        
        self.showMenu.emit("MainBack", self.backMenu)
        
    def __addResourceFiles(self):
        """
        Private method to add resource files to the project.
        """
        itm = self.model().item(self.currentIndex())
        if isinstance(itm, ProjectBrowserFileItem):
            dn = os.path.dirname(itm.fileName())
        elif isinstance(itm, ProjectBrowserSimpleDirectoryItem) or \
                isinstance(itm, ProjectBrowserDirectoryItem):
            dn = itm.dirName()
        else:
            dn = None
        self.project.addFiles('resource', dn)
        
    def __addResourcesDirectory(self):
        """
        Private method to add resource files of a directory to the project.
        """
        itm = self.model().item(self.currentIndex())
        if isinstance(itm, ProjectBrowserFileItem):
            dn = os.path.dirname(itm.fileName())
        elif isinstance(itm, ProjectBrowserSimpleDirectoryItem) or \
                isinstance(itm, ProjectBrowserDirectoryItem):
            dn = itm.dirName()
        else:
            dn = None
        self.project.addDirectory('resource', dn)
        
    def _openItem(self):
        """
        Protected slot to handle the open popup menu entry.
        """
        self.__openFile()
        
    def __openFile(self):
        """
        Private slot to handle the Open menu action.
        """
        itmList = self.getSelectedItems()
        for itm in itmList[:]:
            if isinstance(itm, ProjectBrowserFileItem):
                self.sourceFile.emit(itm.fileName())
        
    def __newResource(self):
        """
        Private slot to handle the New Resource menu action.
        """
        itm = self.model().item(self.currentIndex())
        if itm is None:
            path = self.project.ppath
        else:
            try:
                path = os.path.dirname(itm.fileName())
            except AttributeError:
                try:
                    path = itm.dirName()
                except AttributeError:
                    path = os.path.join(self.project.ppath, itm.data(0))
        
        if self.hooks["newResource"] is not None:
            self.hooks["newResource"](path)
        else:
            fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
                self,
                self.tr("New Resource"),
                path,
                self.tr("Qt Resource Files (*.qrc)"),
                "",
                E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
            
            if not fname:
                # user aborted or didn't enter a filename
                return
            
            ext = QFileInfo(fname).suffix()
            if not ext:
                ex = selectedFilter.split("(*")[1].split(")")[0]
                if ex:
                    fname += ex
            
            if os.path.exists(fname):
                res = E5MessageBox.yesNo(
                    self,
                    self.tr("New Resource"),
                    self.tr("The file already exists! Overwrite it?"),
                    icon=E5MessageBox.Warning)
                if not res:
                    # user selected to not overwrite
                    return
            
            try:
                if self.project.useSystemEol():
                    newline = None
                else:
                    newline = self.project.getEolString()
                rcfile = open(fname, 'w', encoding="utf-8", newline=newline)
                rcfile.write('<!DOCTYPE RCC>\n')
                rcfile.write('<RCC version="1.0">\n')
                rcfile.write('<qresource>\n')
                rcfile.write('</qresource>\n')
                rcfile.write('</RCC>\n')
                rcfile.close()
            except IOError as e:
                E5MessageBox.critical(
                    self,
                    self.tr("New Resource"),
                    self.tr(
                        "<p>The new resource file <b>{0}</b> could not"
                        " be created.<br>Problem: {1}</p>")
                    .format(fname, str(e)))
                return
            
            self.project.appendFile(fname)
            self.sourceFile.emit(fname)
        
    def __deleteFile(self):
        """
        Private method to delete a resource file from the project.
        """
        itmList = self.getSelectedItems()
        
        files = []
        fullNames = []
        for itm in itmList:
            fn2 = itm.fileName()
            fullNames.append(fn2)
            fn = self.project.getRelativePath(fn2)
            files.append(fn)
        
        from UI.DeleteFilesConfirmationDialog import \
            DeleteFilesConfirmationDialog
        dlg = DeleteFilesConfirmationDialog(
            self.parent(),
            self.tr("Delete resources"),
            self.tr(
                "Do you really want to delete these resources from the"
                " project?"),
            files)
        
        if dlg.exec_() == QDialog.Accepted:
            for fn2, fn in zip(fullNames, files):
                self.closeSourceWindow.emit(fn2)
                self.project.deleteFile(fn)
    
    ###########################################################################
    ##  Methods to handle the various compile commands
    ###########################################################################
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStandardOutput signal of the
        pyrcc4/rbrcc process.
        """
        if self.compileProc is None:
            return
        self.compileProc.setReadChannel(QProcess.StandardOutput)
        
        while self.compileProc and self.compileProc.canReadLine():
            self.buf += str(self.compileProc.readLine(),
                            Preferences.getSystem("IOEncoding"),
                            'replace')
        
    def __readStderr(self):
        """
        Private slot to handle the readyReadStandardError signal of the
        pyrcc4/rbrcc process.
        """
        if self.compileProc is None:
            return
        
        ioEncoding = Preferences.getSystem("IOEncoding")
        
        self.compileProc.setReadChannel(QProcess.StandardError)
        while self.compileProc and self.compileProc.canReadLine():
            s = self.rccCompiler + ': '
            error = str(self.compileProc.readLine(),
                        ioEncoding, 'replace')
            s += error
            self.appendStderr.emit(s)
        
    def __compileQRCDone(self, exitCode, exitStatus):
        """
        Private slot to handle the finished signal of the compile process.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.compileRunning = False
        e5App().getObject("ViewManager").enableEditorsCheckFocusIn(True)
        ui = e5App().getObject("UserInterface")
        if exitStatus == QProcess.NormalExit and exitCode == 0 and self.buf:
            ofn = os.path.join(self.project.ppath, self.compiledFile)
            try:
                if self.project.useSystemEol():
                    newline = None
                else:
                    newline = self.project.getEolString()
                f = open(ofn, "w", encoding="utf-8", newline=newline)
                for line in self.buf.splitlines():
                    f.write(line + "\n")
                f.close()
                if self.compiledFile not in self.project.pdata["SOURCES"]:
                    self.project.appendFile(ofn)
                if not self.noDialog and not ui.notificationsEnabled():
                    E5MessageBox.information(
                        self,
                        self.tr("Resource Compilation"),
                        self.tr("The compilation of the resource file"
                                " was successful."))
                else:
                    ui.showNotification(
                        UI.PixmapCache.getPixmap("resourcesCompiler48.png"),
                        self.tr("Resource Compilation"),
                        self.tr("The compilation of the resource file"
                                " was successful."))
            except IOError as msg:
                if not self.noDialog:
                    E5MessageBox.information(
                        self,
                        self.tr("Resource Compilation"),
                        self.tr(
                            "<p>The compilation of the resource file"
                            " failed.</p><p>Reason: {0}</p>").format(str(msg)))
        else:
            if not self.noDialog:
                E5MessageBox.information(
                    self,
                    self.tr("Resource Compilation"),
                    self.tr(
                        "The compilation of the resource file failed."))
            else:
                ui.showNotification(
                    UI.PixmapCache.getPixmap("resourcesCompiler48.png"),
                    self.tr("Resource Compilation"),
                    self.tr(
                        "The compilation of the resource file failed."))
        self.compileProc = None
        
    def __compileQRC(self, fn, noDialog=False, progress=None):
        """
        Private method to compile a .qrc file to a .py file.
        
        @param fn filename of the .ui file to be compiled
        @param noDialog flag indicating silent operations
        @param progress reference to the progress dialog
        @return reference to the compile process (QProcess)
        """
        self.compileProc = QProcess()
        args = []
        self.buf = ""
        
        if self.project.pdata["PROGLANGUAGE"][0] in \
                ["Python", "Python2", "Python3"]:
            if self.project.getProjectType() in ["Qt4", "Qt4C"]:
                self.rccCompiler = 'pyrcc4'
                if Utilities.isWindowsPlatform():
                    self.rccCompiler += '.exe'
                if PYQT_VERSION >= 0x040500:
                    if self.project.pdata["PROGLANGUAGE"][0] in \
                            ["Python", "Python2"]:
                        args.append("-py2")
                    else:
                        args.append("-py3")
            elif self.project.getProjectType() in ["PyQt5", "PyQt5C"]:
                self.rccCompiler = 'pyrcc5'
                if Utilities.isWindowsPlatform():
                    self.rccCompiler += '.exe'
            elif self.project.getProjectType() in ["E6Plugin"]:
                if PYQT_VERSION < 0x050000:
                    self.rccCompiler = 'pyrcc4'
                    if self.project.pdata["PROGLANGUAGE"][0] in \
                            ["Python", "Python2"]:
                        args.append("-py2")
                    else:
                        args.append("-py3")
                else:
                    self.rccCompiler = 'pyrcc5'
                if Utilities.isWindowsPlatform():
                    self.rccCompiler += '.exe'
            elif self.project.getProjectType() in ["PySide", "PySideC"]:
                self.rccCompiler = Utilities.generatePySideToolPath(
                    'pyside-rcc')
                if self.project.pdata["PROGLANGUAGE"][0] in \
                        ["Python", "Python2"]:
                    args.append("-py2")
                else:
                    args.append("-py3")
            else:
                return None
        elif self.project.pdata["PROGLANGUAGE"][0] == "Ruby":
            if self.project.getProjectType() == "Qt4":
                self.rccCompiler = 'rbrcc'
                if Utilities.isWindowsPlatform():
                    self.rccCompiler += '.exe'
            else:
                return None
        else:
            return None
        
        rcc = self.rccCompiler
        
        ofn, ext = os.path.splitext(fn)
        fn = os.path.join(self.project.ppath, fn)
        
        dirname, filename = os.path.split(ofn)
        if self.project.pdata["PROGLANGUAGE"][0] in \
                ["Python", "Python2", "Python3"]:
            self.compiledFile = os.path.join(
                dirname, self.RCFilenameFormatPython.format(filename))
        elif self.project.pdata["PROGLANGUAGE"][0] == "Ruby":
            self.compiledFile = os.path.join(
                dirname, self.RCFilenameFormatRuby.format(filename))
        
        args.append(fn)
        self.compileProc.finished.connect(self.__compileQRCDone)
        self.compileProc.readyReadStandardOutput.connect(self.__readStdout)
        self.compileProc.readyReadStandardError.connect(self.__readStderr)
        
        self.noDialog = noDialog
        self.compileProc.start(rcc, args)
        procStarted = self.compileProc.waitForStarted(5000)
        if procStarted:
            self.compileRunning = True
            e5App().getObject("ViewManager").enableEditorsCheckFocusIn(False)
            return self.compileProc
        else:
            self.compileRunning = False
            if progress is not None:
                progress.cancel()
            E5MessageBox.critical(
                self,
                self.tr('Process Generation Error'),
                self.tr(
                    'Could not start {0}.<br>'
                    'Ensure that it is in the search path.'
                ).format(self.rccCompiler))
            return None
        
    def __compileResource(self):
        """
        Private method to compile a resource to a source file.
        """
        itm = self.model().item(self.currentIndex())
        fn2 = itm.fileName()
        fn = self.project.getRelativePath(fn2)
        if self.hooks["compileResource"] is not None:
            self.hooks["compileResource"](fn)
        else:
            self.__compileQRC(fn)
        
    def __compileAllResources(self):
        """
        Private method to compile all resources to source files.
        """
        if self.hooks["compileAllResources"] is not None:
            self.hooks["compileAllResources"](self.project.pdata["RESOURCES"])
        else:
            numResources = len(self.project.pdata["RESOURCES"])
            progress = E5ProgressDialog(
                self.tr("Compiling resources..."),
                self.tr("Abort"), 0, numResources,
                self.tr("%v/%m Resources"), self)
            progress.setModal(True)
            progress.setMinimumDuration(0)
            progress.setWindowTitle(self.tr("Resources"))
            i = 0
            
            for fn in self.project.pdata["RESOURCES"]:
                progress.setValue(i)
                if progress.wasCanceled():
                    break
                proc = self.__compileQRC(fn, True, progress)
                if proc is not None:
                    while proc.state() == QProcess.Running:
                        QApplication.processEvents()
                        QThread.msleep(300)
                        QApplication.processEvents()
                else:
                    break
                i += 1
                
            progress.setValue(numResources)
        
    def __compileSelectedResources(self):
        """
        Private method to compile selected resources to source files.
        """
        items = self.getSelectedItems()
        files = [self.project.getRelativePath(itm.fileName())
                 for itm in items]
        
        if self.hooks["compileSelectedResources"] is not None:
            self.hooks["compileSelectedResources"](files)
        else:
            numResources = len(files)
            progress = E5ProgressDialog(
                self.tr("Compiling resources..."),
                self.tr("Abort"), 0, numResources,
                self.tr("%v/%m Resources"), self)
            progress.setModal(True)
            progress.setMinimumDuration(0)
            progress.setWindowTitle(self.tr("Resources"))
            i = 0
            
            for fn in files:
                progress.setValue(i)
                if progress.wasCanceled():
                    break
                if not fn.endswith('.ui.h'):
                    proc = self.__compileQRC(fn, True, progress)
                    if proc is not None:
                        while proc.state() == QProcess.Running:
                            QApplication.processEvents()
                            QThread.msleep(300)
                            QApplication.processEvents()
                    else:
                        break
                i += 1
                
            progress.setValue(numResources)
        
    def __checkResourcesNewer(self, filename, mtime):
        """
        Private method to check, if any file referenced in a resource
        file is newer than a given time.
        
        @param filename filename of the resource file (string)
        @param mtime modification time to check against
        @return flag indicating some file is newer (boolean)
        """
        try:
            f = open(filename, "r", encoding="utf-8")
            buf = f.read()
            f.close()
        except IOError:
            return False
        
        qrcDirName = os.path.dirname(filename)
        lbuf = ""
        for line in buf.splitlines():
            line = line.strip()
            if line.lower().startswith("<file>") or \
                    line.lower().startswith("<file "):
                lbuf = line
            elif lbuf:
                lbuf = "{0}{1}".format(lbuf, line)
            if lbuf.lower().endswith("</file>"):
                rfile = lbuf.split(">", 1)[1].split("<", 1)[0]
                if not os.path.isabs(rfile):
                    rfile = os.path.join(qrcDirName, rfile)
                if os.path.exists(rfile) and \
                   os.stat(rfile).st_mtime > mtime:
                    return True
                
                lbuf = ""
        
        return False
        
    def compileChangedResources(self):
        """
        Public method to compile all changed resources to source files.
        """
        if self.hooks["compileChangedResources"] is not None:
            self.hooks["compileChangedResources"](
                self.project.pdata["RESOURCES"])
        else:
            progress = E5ProgressDialog(
                self.tr("Determining changed resources..."),
                None, 0, 100, self.tr("%v/%m Resources"))
            progress.setMinimumDuration(0)
            progress.setWindowTitle(self.tr("Resources"))
            i = 0
            
            # get list of changed resources
            changedResources = []
            progress.setMaximum(len(self.project.pdata["RESOURCES"]))
            for fn in self.project.pdata["RESOURCES"]:
                progress.setValue(i)
                QApplication.processEvents()
                ifn = os.path.join(self.project.ppath, fn)
                if self.project.pdata["PROGLANGUAGE"][0] in \
                   ["Python", "Python2", "Python3"]:
                    dirname, filename = os.path.split(os.path.splitext(ifn)[0])
                    ofn = os.path.join(
                        dirname, self.RCFilenameFormatPython.format(filename))
                elif self.project.pdata["PROGLANGUAGE"][0] == "Ruby":
                    dirname, filename = os.path.split(os.path.splitext(ifn)[0])
                    ofn = os.path.join(
                        dirname, self.RCFilenameFormatRuby.format(filename))
                else:
                    return
                if not os.path.exists(ofn) or \
                   os.stat(ifn).st_mtime > os.stat(ofn).st_mtime:
                    changedResources.append(fn)
                elif self.__checkResourcesNewer(ifn, os.stat(ofn).st_mtime):
                    changedResources.append(fn)
                i += 1
            progress.setValue(i)
            QApplication.processEvents()
            
            if changedResources:
                progress.setLabelText(
                    self.tr("Compiling changed resources..."))
                progress.setMaximum(len(changedResources))
                i = 0
                progress.setValue(i)
                QApplication.processEvents()
                for fn in changedResources:
                    progress.setValue(i)
                    proc = self.__compileQRC(fn, True, progress)
                    if proc is not None:
                        while proc.state() == QProcess.Running:
                            QApplication.processEvents()
                            QThread.msleep(300)
                            QApplication.processEvents()
                    else:
                        break
                    i += 1
                progress.setValue(len(changedResources))
                QApplication.processEvents()
        
    def handlePreferencesChanged(self):
        """
        Public slot used to handle the preferencesChanged signal.
        """
        ProjectBaseBrowser.handlePreferencesChanged(self)
    
    ###########################################################################
    ## Support for hooks below
    ###########################################################################
    
    def _initHookMethods(self):
        """
        Protected method to initialize the hooks dictionary.
        
        Supported hook methods are:
        <ul>
        <li>compileResource: takes filename as parameter</li>
        <li>compileAllResources: takes list of filenames as parameter</li>
        <li>compileChangedResources: takes list of filenames as parameter</li>
        <li>compileSelectedResources: takes list of all form filenames as
            parameter</li>
        <li>newResource: takes full directory path of new file as
            parameter</li>
        </ul>
        
        <b>Note</b>: Filenames are relative to the project directory, if not
        specified differently.
        """
        self.hooks = {
            "compileResource": None,
            "compileAllResources": None,
            "compileChangedResources": None,
            "compileSelectedResources": None,
            "newResource": None,
        }
