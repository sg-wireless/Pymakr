# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the a class used to display the interfaces (IDL) part
of the project.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os
import glob

from PyQt5.QtCore import QThread, pyqtSignal, QProcess
from PyQt5.QtWidgets import QDialog, QApplication, QMenu

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox
from E5Gui.E5ProgressDialog import E5ProgressDialog

from .ProjectBrowserModel import ProjectBrowserFileItem, \
    ProjectBrowserSimpleDirectoryItem, ProjectBrowserDirectoryItem, \
    ProjectBrowserInterfaceType
from .ProjectBaseBrowser import ProjectBaseBrowser

from UI.BrowserModel import BrowserFileItem, BrowserClassItem, \
    BrowserMethodItem, BrowserClassAttributeItem
import UI.PixmapCache

import Preferences
import Utilities


class ProjectInterfacesBrowser(ProjectBaseBrowser):
    """
    A class used to display the interfaces (IDL) part of the project.
    
    @signal sourceFile(str, int = 0) emitted to open a file
    @signal closeSourceWindow(str) emitted after a file has been
        removed/deleted from the project
    @signal appendStdout(str) emitted after something was received from
        a QProcess on stdout
    @signal appendStderr(str) emitted after something was received from
        a QProcess on stderr
    @signal showMenu(str, QMenu) emitted when a menu is about to be shown.
        The name of the menu and a reference to the menu are given.
    """
    appendStdout = pyqtSignal(str)
    appendStderr = pyqtSignal(str)
    showMenu = pyqtSignal(str, QMenu)
    
    def __init__(self, project, parent=None):
        """
        Constructor
        
        @param project reference to the project object
        @param parent parent widget of this browser (QWidget)
        """
        self.omniidl = Preferences.getCorba("omniidl")
        if self.omniidl == "":
            self.omniidl = Utilities.isWindowsPlatform() and \
                "omniidl.exe" or "omniidl"
        if not Utilities.isinpath(self.omniidl):
            self.omniidl = None
        
        ProjectBaseBrowser.__init__(self, project,
                                    ProjectBrowserInterfaceType, parent)
        
        self.selectedItemsFilter = \
            [ProjectBrowserFileItem, ProjectBrowserSimpleDirectoryItem]
        
        self.setWindowTitle(self.tr('Interfaces (IDL)'))
        
        self.setWhatsThis(self.tr(
            """<b>Project Interfaces Browser</b>"""
            """<p>This allows to easily see all interfaces (CORBA IDL files)"""
            """ contained in the current project. Several actions can be"""
            """ executed via the context menu.</p>"""
        ))
        
        project.prepareRepopulateItem.connect(self._prepareRepopulateItem)
        project.completeRepopulateItem.connect(self._completeRepopulateItem)
        
    def _createPopupMenus(self):
        """
        Protected overloaded method to generate the popup menu.
        """
        self.menuActions = []
        self.multiMenuActions = []
        self.dirMenuActions = []
        self.dirMultiMenuActions = []
        
        self.sourceMenu = QMenu(self)
        if self.omniidl is not None:
            self.sourceMenu.addAction(
                self.tr('Compile interface'), self.__compileInterface)
            self.sourceMenu.addAction(
                self.tr('Compile all interfaces'),
                self.__compileAllInterfaces)
        self.sourceMenu.addAction(self.tr('Open'), self._openItem)
        self.sourceMenu.addSeparator()
        act = self.sourceMenu.addAction(
            self.tr('Rename file'), self._renameFile)
        self.menuActions.append(act)
        act = self.sourceMenu.addAction(
            self.tr('Remove from project'), self._removeFile)
        self.menuActions.append(act)
        act = self.sourceMenu.addAction(
            self.tr('Delete'), self.__deleteFile)
        self.menuActions.append(act)
        self.sourceMenu.addSeparator()
        self.sourceMenu.addAction(
            self.tr('Add interfaces...'), self.__addInterfaceFiles)
        self.sourceMenu.addAction(
            self.tr('Add interfaces directory...'),
            self.__addInterfacesDirectory)
        self.sourceMenu.addSeparator()
        self.sourceMenu.addAction(
            self.tr('Copy Path to Clipboard'), self._copyToClipboard)
        self.sourceMenu.addSeparator()
        self.sourceMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.sourceMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.sourceMenu.addSeparator()
        self.sourceMenu.addAction(self.tr('Configure...'), self._configure)
        self.sourceMenu.addAction(
            self.tr('Configure CORBA...'), self.__configureCorba)

        self.menu = QMenu(self)
        if self.omniidl is not None:
            self.menu.addAction(
                self.tr('Compile interface'), self.__compileInterface)
            self.menu.addAction(
                self.tr('Compile all interfaces'),
                self.__compileAllInterfaces)
        self.menu.addAction(self.tr('Open'), self._openItem)
        self.menu.addSeparator()
        self.menu.addAction(
            self.tr('Add interfaces...'), self.__addInterfaceFiles)
        self.menu.addAction(
            self.tr('Add interfaces directory...'),
            self.__addInterfacesDirectory)
        self.menu.addSeparator()
        self.menu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.menu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.menu.addSeparator()
        self.menu.addAction(self.tr('Configure...'), self._configure)
        self.menu.addAction(
            self.tr('Configure CORBA...'), self.__configureCorba)

        self.backMenu = QMenu(self)
        if self.omniidl is not None:
            self.backMenu.addAction(
                self.tr('Compile all interfaces'),
                self.__compileAllInterfaces)
            self.backMenu.addSeparator()
        self.backMenu.addAction(
            self.tr('Add interfaces...'), self.project.addIdlFiles)
        self.backMenu.addAction(
            self.tr('Add interfaces directory...'), self.project.addIdlDir)
        self.backMenu.addSeparator()
        self.backMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.backMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.backMenu.addSeparator()
        self.backMenu.addAction(self.tr('Configure...'), self._configure)
        self.backMenu.addAction(
            self.tr('Configure CORBA...'), self.__configureCorba)
        self.backMenu.setEnabled(False)

        # create the menu for multiple selected files
        self.multiMenu = QMenu(self)
        if self.omniidl is not None:
            self.multiMenu.addAction(
                self.tr('Compile interfaces'),
                self.__compileSelectedInterfaces)
        self.multiMenu.addAction(self.tr('Open'), self._openItem)
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
        self.multiMenu.addAction(
            self.tr('Configure CORBA...'), self.__configureCorba)

        self.dirMenu = QMenu(self)
        if self.omniidl is not None:
            self.dirMenu.addAction(
                self.tr('Compile all interfaces'),
                self.__compileAllInterfaces)
            self.dirMenu.addSeparator()
        act = self.dirMenu.addAction(
            self.tr('Remove from project'), self._removeFile)
        self.dirMenuActions.append(act)
        act = self.dirMenu.addAction(
            self.tr('Delete'), self._deleteDirectory)
        self.dirMenuActions.append(act)
        self.dirMenu.addSeparator()
        self.dirMenu.addAction(
            self.tr('Add interfaces...'), self.__addInterfaceFiles)
        self.dirMenu.addAction(
            self.tr('Add interfaces directory...'),
            self.__addInterfacesDirectory)
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
        self.dirMenu.addAction(
            self.tr('Configure CORBA...'), self.__configureCorba)
        
        self.dirMultiMenu = QMenu(self)
        if self.omniidl is not None:
            self.dirMultiMenu.addAction(
                self.tr('Compile all interfaces'),
                self.__compileAllInterfaces)
            self.dirMultiMenu.addSeparator()
        self.dirMultiMenu.addAction(
            self.tr('Add interfaces...'), self.project.addIdlFiles)
        self.dirMultiMenu.addAction(
            self.tr('Add interfaces directory...'), self.project.addIdlDir)
        self.dirMultiMenu.addSeparator()
        self.dirMultiMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.dirMultiMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.dirMultiMenu.addSeparator()
        self.dirMultiMenu.addAction(
            self.tr('Configure...'), self._configure)
        self.dirMultiMenu.addAction(self.tr('Configure CORBA...'),
                                    self.__configureCorba)
        
        self.sourceMenu.aboutToShow.connect(self.__showContextMenu)
        self.multiMenu.aboutToShow.connect(self.__showContextMenuMulti)
        self.dirMenu.aboutToShow.connect(self.__showContextMenuDir)
        self.dirMultiMenu.aboutToShow.connect(self.__showContextMenuDirMulti)
        self.backMenu.aboutToShow.connect(self.__showContextMenuBack)
        self.mainMenu = self.sourceMenu
        
    def _contextMenuRequested(self, coord):
        """
        Protected slot to show the context menu.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        if not self.project.isOpen():
            return
        
        try:
            categories = self.getSelectedItemsCountCategorized(
                [ProjectBrowserFileItem, BrowserClassItem,
                 BrowserMethodItem, ProjectBrowserSimpleDirectoryItem])
            cnt = categories["sum"]
            if cnt <= 1:
                index = self.indexAt(coord)
                if index.isValid():
                    self._selectSingleItem(index)
                    categories = self.getSelectedItemsCountCategorized(
                        [ProjectBrowserFileItem, BrowserClassItem,
                         BrowserMethodItem, ProjectBrowserSimpleDirectoryItem])
                    cnt = categories["sum"]
            
            bfcnt = categories[str(ProjectBrowserFileItem)]
            cmcnt = categories[str(BrowserClassItem)] + \
                categories[str(BrowserMethodItem)]
            sdcnt = categories[str(ProjectBrowserSimpleDirectoryItem)]
            if cnt > 1 and cnt == bfcnt:
                self.multiMenu.popup(self.mapToGlobal(coord))
            elif cnt > 1 and cnt == sdcnt:
                self.dirMultiMenu.popup(self.mapToGlobal(coord))
            else:
                index = self.indexAt(coord)
                if cnt == 1 and index.isValid():
                    if bfcnt == 1 or cmcnt == 1:
                        itm = self.model().item(index)
                        if isinstance(itm, ProjectBrowserFileItem):
                            self.sourceMenu.popup(self.mapToGlobal(coord))
                        elif isinstance(itm, BrowserClassItem) or \
                                isinstance(itm, BrowserMethodItem):
                            self.menu.popup(self.mapToGlobal(coord))
                        else:
                            self.backMenu.popup(self.mapToGlobal(coord))
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
        
    def _openItem(self):
        """
        Protected slot to handle the open popup menu entry.
        """
        itmList = self.getSelectedItems(
            [BrowserFileItem, BrowserClassItem, BrowserMethodItem,
             BrowserClassAttributeItem])
        
        for itm in itmList:
            if isinstance(itm, BrowserFileItem):
                self.sourceFile[str].emit(itm.fileName())
            elif isinstance(itm, BrowserClassItem):
                self.sourceFile[str, int].emit(
                    itm.fileName(), itm.classObject().lineno)
            elif isinstance(itm, BrowserMethodItem):
                self.sourceFile[str, int].emit(
                    itm.fileName(), itm.functionObject().lineno)
            elif isinstance(itm, BrowserClassAttributeItem):
                self.sourceFile[str, int].emit(
                    itm.fileName(), itm.attributeObject().lineno)
        
    def __addInterfaceFiles(self):
        """
        Private method to add interface files to the project.
        """
        itm = self.model().item(self.currentIndex())
        if isinstance(itm, ProjectBrowserFileItem) or \
           isinstance(itm, BrowserClassItem) or \
           isinstance(itm, BrowserMethodItem):
            dn = os.path.dirname(itm.fileName())
        elif isinstance(itm, ProjectBrowserSimpleDirectoryItem) or \
                isinstance(itm, ProjectBrowserDirectoryItem):
            dn = itm.dirName()
        else:
            dn = None
        self.project.addFiles('interface', dn)
        
    def __addInterfacesDirectory(self):
        """
        Private method to add interface files of a directory to the project.
        """
        itm = self.model().item(self.currentIndex())
        if isinstance(itm, ProjectBrowserFileItem) or \
           isinstance(itm, BrowserClassItem) or \
           isinstance(itm, BrowserMethodItem):
            dn = os.path.dirname(itm.fileName())
        elif isinstance(itm, ProjectBrowserSimpleDirectoryItem) or \
                isinstance(itm, ProjectBrowserDirectoryItem):
            dn = itm.dirName()
        else:
            dn = None
        self.project.addDirectory('interface', dn)
        
    def __deleteFile(self):
        """
        Private method to delete files from the project.
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
            self.tr("Delete interfaces"),
            self.tr("Do you really want to delete these interfaces from"
                    " the project?"),
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
        omniidl process.
        """
        if self.compileProc is None:
            return
        
        ioEncoding = Preferences.getSystem("IOEncoding")
        
        self.compileProc.setReadChannel(QProcess.StandardOutput)
        while self.compileProc and self.compileProc.canReadLine():
            s = 'omniidl: '
            output = str(self.compileProc.readLine(), ioEncoding, 'replace')
            s += output
            self.appendStdout.emit(s)
        
    def __readStderr(self):
        """
        Private slot to handle the readyReadStandardError signal of the
        omniidl process.
        """
        if self.compileProc is None:
            return
        
        ioEncoding = Preferences.getSystem("IOEncoding")
        
        self.compileProc.setReadChannel(QProcess.StandardError)
        while self.compileProc and self.compileProc.canReadLine():
            s = 'omniidl: '
            error = str(self.compileProc.readLine(), ioEncoding, 'replace')
            s += error
            self.appendStderr.emit(s)
        
    def __compileIDLDone(self, exitCode, exitStatus):
        """
        Private slot to handle the finished signal of the omniidl process.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.compileRunning = False
        ui = e5App().getObject("UserInterface")
        if exitStatus == QProcess.NormalExit and exitCode == 0:
            path = os.path.dirname(self.idlFile)
            poaList = glob.glob(os.path.join(path, "*__POA"))
            npoaList = [f.replace("__POA", "") for f in poaList]
            fileList = glob.glob(os.path.join(path, "*_idl.py"))
            for dir in poaList + npoaList:
                fileList += Utilities.direntries(dir, True, "*.py")
            for file in fileList:
                self.project.appendFile(file)
            if not self.noDialog and not ui.notificationsEnabled():
                E5MessageBox.information(
                    self,
                    self.tr("Interface Compilation"),
                    self.tr(
                        "The compilation of the interface file was"
                        " successful."))
            else:
                ui.showNotification(
                    UI.PixmapCache.getPixmap("corba48.png"),
                    self.tr("Interface Compilation"),
                    self.tr(
                        "The compilation of the interface file was"
                        " successful."))
        else:
            if not self.noDialog:
                E5MessageBox.information(
                    self,
                    self.tr("Interface Compilation"),
                    self.tr(
                        "The compilation of the interface file failed."))
            else:
                ui.showNotification(
                    UI.PixmapCache.getPixmap("corba48.png"),
                    self.tr("Interface Compilation"),
                    self.tr(
                        "The compilation of the interface file failed."))
        self.compileProc = None
        
    def __compileIDL(self, fn, noDialog=False, progress=None):
        """
        Private method to compile a .idl file to python.

        @param fn filename of the .idl file to be compiled (string)
        @param noDialog flag indicating silent operations (boolean)
        @param progress reference to the progress dialog (E5ProgressDialog)
        @return reference to the compile process (QProcess)
        """
        self.compileProc = QProcess()
        args = []
        
        args.append("-bpython")
        args.append("-I.")
        
        fn = os.path.join(self.project.ppath, fn)
        self.idlFile = fn
        args.append("-C{0}".format(os.path.dirname(fn)))
        args.append(fn)
        
        self.compileProc.finished.connect(self.__compileIDLDone)
        self.compileProc.readyReadStandardOutput.connect(self.__readStdout)
        self.compileProc.readyReadStandardError.connect(self.__readStderr)
        
        self.noDialog = noDialog
        self.compileProc.start(self.omniidl, args)
        procStarted = self.compileProc.waitForStarted(5000)
        if procStarted:
            self.compileRunning = True
            return self.compileProc
        else:
            self.compileRunning = False
            if progress is not None:
                progress.cancel()
            E5MessageBox.critical(
                self,
                self.tr('Process Generation Error'),
                self.tr(
                    '<p>Could not start {0}.<br>'
                    'Ensure that it is in the search path.</p>'
                ).format(self.omniidl))
            return None
        
    def __compileInterface(self):
        """
        Private method to compile an interface to python.
        """
        if self.omniidl is not None:
            itm = self.model().item(self.currentIndex())
            fn2 = itm.fileName()
            fn = self.project.getRelativePath(fn2)
            self.__compileIDL(fn)
        
    def __compileAllInterfaces(self):
        """
        Private method to compile all interfaces to python.
        """
        if self.omniidl is not None:
            numIDLs = len(self.project.pdata["INTERFACES"])
            progress = E5ProgressDialog(
                self.tr("Compiling interfaces..."),
                self.tr("Abort"), 0, numIDLs,
                self.tr("%v/%m Interfaces"), self)
            progress.setModal(True)
            progress.setMinimumDuration(0)
            progress.setWindowTitle(self.tr("Interfaces"))
            i = 0
            
            for fn in self.project.pdata["INTERFACES"]:
                progress.setValue(i)
                if progress.wasCanceled():
                    break
                proc = self.__compileIDL(fn, True, progress)
                if proc is not None:
                    while proc.state() == QProcess.Running:
                        QApplication.processEvents()
                        QThread.msleep(300)
                        QApplication.processEvents()
                else:
                    break
                i += 1
            
            progress.setValue(numIDLs)
        
    def __compileSelectedInterfaces(self):
        """
        Private method to compile selected interfaces to python.
        """
        if self.omniidl is not None:
            items = self.getSelectedItems()
            
            files = [self.project.getRelativePath(itm.fileName())
                     for itm in items]
            numIDLs = len(files)
            progress = E5ProgressDialog(
                self.tr("Compiling interfaces..."),
                self.tr("Abort"), 0, numIDLs,
                self.tr("%v/%m Interfaces"), self)
            progress.setModal(True)
            progress.setMinimumDuration(0)
            progress.setWindowTitle(self.tr("Interfaces"))
            i = 0
            
            for fn in files:
                progress.setValue(i)
                if progress.wasCanceled():
                    break
                proc = self.__compileIDL(fn, True, progress)
                if proc is not None:
                    while proc.state() == QProcess.Running:
                        QApplication.processEvents()
                        QThread.msleep(300)
                        QApplication.processEvents()
                else:
                    break
                i += 1
                
            progress.setValue(numIDLs)
        
    def __configureCorba(self):
        """
        Private method to open the configuration dialog.
        """
        e5App().getObject("UserInterface").showPreferences("corbaPage")
