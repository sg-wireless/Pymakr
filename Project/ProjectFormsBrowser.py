# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class used to display the forms part of the project.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os
import sys
import shutil

from PyQt5.QtCore import PYQT_VERSION, QThread, QFileInfo, pyqtSignal, QProcess
from PyQt5.QtWidgets import QDialog, QInputDialog, QApplication, QMenu

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox, E5FileDialog
from E5Gui.E5ProgressDialog import E5ProgressDialog

from .ProjectBrowserModel import ProjectBrowserFileItem, \
    ProjectBrowserSimpleDirectoryItem, ProjectBrowserDirectoryItem, \
    ProjectBrowserFormType
from .ProjectBaseBrowser import ProjectBaseBrowser

import UI.PixmapCache

import Preferences
import Utilities

from eric6config import getConfig


class ProjectFormsBrowser(ProjectBaseBrowser):
    """
    A class used to display the forms part of the project.
    
    @signal appendStderr(str) emitted after something was received from
        a QProcess on stderr
    @signal sourceFile(str) emitted to open a forms file in an editor
    @signal uipreview(str) emitted to preview a forms file
    @signal trpreview(list of str) emitted to preview form files in the
        translations previewer
    @signal closeSourceWindow(str) emitted after a file has been
        removed/deleted from the project
    @signal showMenu(str, QMenu) emitted when a menu is about to be shown. The
        name of the menu and a reference to the menu are given.
    @signal menusAboutToBeCreated() emitted when the context menus are about to
        be created. This is the right moment to add or remove hook methods.
    """
    appendStderr = pyqtSignal(str)
    uipreview = pyqtSignal(str)
    showMenu = pyqtSignal(str, QMenu)
    menusAboutToBeCreated = pyqtSignal()
    
    PyuicIndentDefault = 4
    
    def __init__(self, project, parent=None):
        """
        Constructor
        
        @param project reference to the project object
        @param parent parent widget of this browser (QWidget)
        """
        ProjectBaseBrowser.__init__(self, project, ProjectBrowserFormType,
                                    parent)
        
        self.selectedItemsFilter = \
            [ProjectBrowserFileItem, ProjectBrowserSimpleDirectoryItem]
        
        self.setWindowTitle(self.tr('Forms'))

        self.setWhatsThis(self.tr(
            """<b>Project Forms Browser</b>"""
            """<p>This allows to easily see all forms contained in the"""
            """ current project. Several actions can be executed via the"""
            """ context menu.</p>"""
        ))
        
        # templates for Qt4
        # these two lists have to stay in sync
        self.templates4 = [
            'dialog4.tmpl', 'widget4.tmpl', 'mainwindow4.tmpl',
            'dialogbuttonboxbottom4.tmpl', 'dialogbuttonboxright4.tmpl',
            'dialogbuttonsbottom4.tmpl', 'dialogbuttonsbottomcenter4.tmpl',
            'dialogbuttonsright4.tmpl', '', 'wizard4.tmpl', 'wizardpage4.tmpl',
            'qdockwidget4.tmpl', 'qframe4.tmpl', 'qgroupbox4.tmpl',
            'qscrollarea4.tmpl', 'qmdiarea4.tmpl', 'qtabwidget4.tmpl',
            'qtoolbox4.tmpl', 'qstackedwidget4.tmpl'
        ]
        self.templateTypes4 = [
            self.tr("Dialog"),
            self.tr("Widget"),
            self.tr("Main Window"),
            self.tr("Dialog with Buttonbox (Bottom)"),
            self.tr("Dialog with Buttonbox (Right)"),
            self.tr("Dialog with Buttons (Bottom)"),
            self.tr("Dialog with Buttons (Bottom-Center)"),
            self.tr("Dialog with Buttons (Right)"),
            '',
            self.tr("QWizard"),
            self.tr("QWizardPage"),
            self.tr("QDockWidget"),
            self.tr("QFrame"),
            self.tr("QGroupBox"),
            self.tr("QScrollArea"),
            self.tr("QMdiArea"),
            self.tr("QTabWidget"),
            self.tr("QToolBox"),
            self.tr("QStackedWidget"),
        ]
        
        self.compileProc = None
        
    def _createPopupMenus(self):
        """
        Protected overloaded method to generate the popup menu.
        """
        self.menuActions = []
        self.multiMenuActions = []
        self.dirMenuActions = []
        self.dirMultiMenuActions = []
        
        self.menusAboutToBeCreated.emit()
        
        self.menu = QMenu(self)
        if self.project.getProjectType() in \
                ["Qt4", "PyQt5", "E6Plugin", "PySide"]:
            self.menu.addAction(
                self.tr('Compile form'), self.__compileForm)
            self.menu.addAction(
                self.tr('Compile all forms'),
                self.__compileAllForms)
            self.menu.addAction(
                self.tr('Generate Dialog Code...'),
                self.__generateDialogCode)
            self.menu.addSeparator()
            self.menu.addAction(
                self.tr('Open in Qt-Designer'), self.__openFile)
            self.menu.addAction(
                self.tr('Open in Editor'), self.__openFileInEditor)
            self.menu.addSeparator()
            self.menu.addAction(self.tr('Preview form'), self.__UIPreview)
            self.menu.addAction(
                self.tr('Preview translations'), self.__TRPreview)
        else:
            if self.hooks["compileForm"] is not None:
                self.menu.addAction(
                    self.hooksMenuEntries.get(
                        "compileForm",
                        self.tr('Compile form')), self.__compileForm)
            if self.hooks["compileAllForms"] is not None:
                self.menu.addAction(
                    self.hooksMenuEntries.get(
                        "compileAllForms",
                        self.tr('Compile all forms')),
                    self.__compileAllForms)
            if self.hooks["generateDialogCode"] is not None:
                self.menu.addAction(
                    self.hooksMenuEntries.get(
                        "generateDialogCode",
                        self.tr('Generate Dialog Code...')),
                    self.__generateDialogCode)
            if self.hooks["compileForm"] is not None or \
               self.hooks["compileAllForms"] is not None or \
               self.hooks["generateDialogCode"] is not None:
                self.menu.addSeparator()
            if self.hooks["open"] is not None:
                self.menu.addAction(
                    self.hooksMenuEntries.get("open", self.tr('Open')),
                    self.__openFile)
            self.menu.addAction(self.tr('Open'), self.__openFileInEditor)
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
                ["Qt4", "PyQt5", "E6Plugin", "PySide"]:
            self.menu.addAction(self.tr('New form...'), self.__newForm)
        else:
            if self.hooks["newForm"] is not None:
                self.menu.addAction(
                    self.hooksMenuEntries.get(
                        "newForm", self.tr('New form...')), self.__newForm)
        self.menu.addAction(self.tr('Add forms...'), self.__addFormFiles)
        self.menu.addAction(
            self.tr('Add forms directory...'), self.__addFormsDirectory)
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
                ["Qt4", "PyQt5", "E6Plugin", "PySide"] or \
                self.hooks["compileAllForms"] is not None:
            self.backMenu.addAction(
                self.tr('Compile all forms'), self.__compileAllForms)
            self.backMenu.addSeparator()
            self.backMenu.addAction(self.tr('New form...'), self.__newForm)
        else:
            if self.hooks["newForm"] is not None:
                self.backMenu.addAction(
                    self.hooksMenuEntries.get(
                        "newForm", self.tr('New form...')), self.__newForm)
        self.backMenu.addAction(
            self.tr('Add forms...'), self.project.addUiFiles)
        self.backMenu.addAction(
            self.tr('Add forms directory...'), self.project.addUiDir)
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
                ["Qt4", "PyQt5", "E6Plugin", "PySide"]:
            act = self.multiMenu.addAction(
                self.tr('Compile forms'), self.__compileSelectedForms)
            self.multiMenu.addSeparator()
            self.multiMenu.addAction(
                self.tr('Open in Qt-Designer'), self.__openFile)
            self.multiMenu.addAction(
                self.tr('Open in Editor'), self.__openFileInEditor)
            self.multiMenu.addSeparator()
            self.multiMenu.addAction(
                self.tr('Preview translations'), self.__TRPreview)
        else:
            if self.hooks["compileSelectedForms"] is not None:
                act = self.multiMenu.addAction(
                    self.hooksMenuEntries.get(
                        "compileSelectedForms",
                        self.tr('Compile forms')),
                    self.__compileSelectedForms)
                self.multiMenu.addSeparator()
            if self.hooks["open"] is not None:
                self.multiMenu.addAction(
                    self.hooksMenuEntries.get("open", self.tr('Open')),
                    self.__openFile)
            self.multiMenu.addAction(
                self.tr('Open'), self.__openFileInEditor)
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
                ["Qt4", "PyQt5", "E6Plugin", "PySide"]:
            self.dirMenu.addAction(
                self.tr('Compile all forms'), self.__compileAllForms)
            self.dirMenu.addSeparator()
        else:
            if self.hooks["compileAllForms"] is not None:
                self.dirMenu.addAction(
                    self.hooksMenuEntries.get(
                        "compileAllForms",
                        self.tr('Compile all forms')),
                    self.__compileAllForms)
                self.dirMenu.addSeparator()
        act = self.dirMenu.addAction(
            self.tr('Remove from project'), self._removeDir)
        self.dirMenuActions.append(act)
        act = self.dirMenu.addAction(
            self.tr('Delete'), self._deleteDirectory)
        self.dirMenuActions.append(act)
        self.dirMenu.addSeparator()
        if self.project.getProjectType() in \
                ["Qt4", "PyQt5", "E6Plugin", "PySide"]:
            self.dirMenu.addAction(self.tr('New form...'), self.__newForm)
        else:
            if self.hooks["newForm"] is not None:
                self.dirMenu.addAction(
                    self.hooksMenuEntries.get(
                        "newForm",
                        self.tr('New form...')), self.__newForm)
        self.dirMenu.addAction(
            self.tr('Add forms...'), self.__addFormFiles)
        self.dirMenu.addAction(
            self.tr('Add forms directory...'), self.__addFormsDirectory)
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
                ["Qt4", "PyQt5", "E6Plugin", "PySide"]:
            self.dirMultiMenu.addAction(
                self.tr('Compile all forms'), self.__compileAllForms)
            self.dirMultiMenu.addSeparator()
        else:
            if self.hooks["compileAllForms"] is not None:
                self.dirMultiMenu.addAction(
                    self.hooksMenuEntries.get(
                        "compileAllForms",
                        self.tr('Compile all forms')),
                    self.__compileAllForms)
                self.dirMultiMenu.addSeparator()
        self.dirMultiMenu.addAction(
            self.tr('Add forms...'), self.project.addUiFiles)
        self.dirMultiMenu.addAction(
            self.tr('Add forms directory...'), self.project.addUiDir)
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
        
    def __addFormFiles(self):
        """
        Private method to add form files to the project.
        """
        itm = self.model().item(self.currentIndex())
        if isinstance(itm, ProjectBrowserFileItem):
            dn = os.path.dirname(itm.fileName())
        elif isinstance(itm, ProjectBrowserSimpleDirectoryItem) or \
                isinstance(itm, ProjectBrowserDirectoryItem):
            dn = itm.dirName()
        else:
            dn = None
        self.project.addFiles('form', dn)
        
    def __addFormsDirectory(self):
        """
        Private method to add form files of a directory to the project.
        """
        itm = self.model().item(self.currentIndex())
        if isinstance(itm, ProjectBrowserFileItem):
            dn = os.path.dirname(itm.fileName())
        elif isinstance(itm, ProjectBrowserSimpleDirectoryItem) or \
                isinstance(itm, ProjectBrowserDirectoryItem):
            dn = itm.dirName()
        else:
            dn = None
        self.project.addDirectory('form', dn)
        
    def __openFile(self):
        """
        Private slot to handle the Open menu action.
        """
        itmList = self.getSelectedItems()
        for itm in itmList[:]:
            try:
                if isinstance(itm, ProjectBrowserFileItem):
                    # hook support
                    if self.hooks["open"] is not None:
                        self.hooks["open"](itm.fileName())
                    else:
                        self.designerFile.emit(itm.fileName())
            except:
                pass
        
    def __openFileInEditor(self):
        """
        Private slot to handle the Open in Editor menu action.
        """
        itmList = self.getSelectedItems()
        for itm in itmList[:]:
            self.sourceFile.emit(itm.fileName())
        
    def _openItem(self):
        """
        Protected slot to handle the open popup menu entry.
        """
        itmList = self.getSelectedItems()
        for itm in itmList:
            if isinstance(itm, ProjectBrowserFileItem):
                if itm.isDesignerFile():
                    self.designerFile.emit(itm.fileName())
                else:
                    self.sourceFile.emit(itm.fileName())
        
    def __UIPreview(self):
        """
        Private slot to handle the Preview menu action.
        """
        itmList = self.getSelectedItems()
        self.uipreview.emit(itmList[0].fileName())
        
    def __TRPreview(self):
        """
        Private slot to handle the Preview translations action.
        """
        fileNames = []
        for itm in self.getSelectedItems():
            fileNames.append(itm.fileName())
        trfiles = sorted(self.project.pdata["TRANSLATIONS"][:])
        fileNames.extend([os.path.join(self.project.ppath, trfile)
                          for trfile in trfiles
                          if trfile.endswith('.qm')])
        self.trpreview[list].emit(fileNames)
        
    def __newForm(self):
        """
        Private slot to handle the New Form menu action.
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
        
        if self.hooks["newForm"] is not None:
            self.hooks["newForm"](path)
        else:
            if self.project.getProjectType() in \
                    ["Qt4", "PyQt5", "E6Plugin", "PySide"]:
                self.__newUiForm(path)
        
    def __newUiForm(self, path):
        """
        Private slot to handle the New Form menu action for Qt-related
        projects.
        
        @param path full directory path for the new form file (string)
        """
        selectedForm, ok = QInputDialog.getItem(
            None,
            self.tr("New Form"),
            self.tr("Select a form type:"),
            self.templateTypes4,
            0, False)
        if not ok or not selectedForm:
            # user pressed cancel
            return
        
        templateIndex = self.templateTypes4.index(selectedForm)
        templateFile = os.path.join(
            getConfig('ericTemplatesDir'), self.templates4[templateIndex])
        
        fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            self,
            self.tr("New Form"),
            path,
            self.tr("Qt User-Interface Files (*.ui);;All Files (*)"),
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
                self.tr("New Form"),
                self.tr("The file already exists! Overwrite it?"),
                icon=E5MessageBox.Warning)
            if not res:
                # user selected to not overwrite
                return
        
        try:
            shutil.copy(templateFile, fname)
        except IOError as e:
            E5MessageBox.critical(
                self,
                self.tr("New Form"),
                self.tr(
                    "<p>The new form file <b>{0}</b> could not be created.<br>"
                    "Problem: {1}</p>").format(fname, str(e)))
            return
        
        self.project.appendFile(fname)
        self.designerFile.emit(fname)
        
    def __deleteFile(self):
        """
        Private method to delete a form file from the project.
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
            self.tr("Delete forms"),
            self.tr(
                "Do you really want to delete these forms from the project?"),
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
        pyuic/rbuic process.
        """
        if self.compileProc is None:
            return
        self.compileProc.setReadChannel(QProcess.StandardOutput)
        
        while self.compileProc and self.compileProc.canReadLine():
            self.buf += str(self.compileProc.readLine(),
                            "utf-8", 'replace')
        
    def __readStderr(self):
        """
        Private slot to handle the readyReadStandardError signal of the
        pyuic/rbuic process.
        """
        if self.compileProc is None:
            return
        
        ioEncoding = Preferences.getSystem("IOEncoding")
        
        self.compileProc.setReadChannel(QProcess.StandardError)
        while self.compileProc and self.compileProc.canReadLine():
            s = self.uicompiler + ': '
            error = str(self.compileProc.readLine(),
                        ioEncoding, 'replace')
            s += error
            self.appendStderr.emit(s)
        
    def __compileUIDone(self, exitCode, exitStatus):
        """
        Private slot to handle the finished signal of the pyuic/rbuic process.
        
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
                        self.tr("Form Compilation"),
                        self.tr("The compilation of the form file"
                                " was successful."))
                else:
                    ui.showNotification(
                        UI.PixmapCache.getPixmap("designer48.png"),
                        self.tr("Form Compilation"),
                        self.tr("The compilation of the form file"
                                " was successful."))
                self.project.projectFormCompiled.emit(self.compiledFile)
            except IOError as msg:
                if not self.noDialog:
                    E5MessageBox.information(
                        self,
                        self.tr("Form Compilation"),
                        self.tr(
                            "<p>The compilation of the form file failed.</p>"
                            "<p>Reason: {0}</p>").format(str(msg)))
                else:
                    ui.showNotification(
                        UI.PixmapCache.getPixmap("designer48.png"),
                        self.tr("Form Compilation"),
                        self.tr(
                            "<p>The compilation of the form file failed.</p>"
                            "<p>Reason: {0}</p>").format(str(msg)))
        else:
            if not self.noDialog:
                E5MessageBox.information(
                    self,
                    self.tr("Form Compilation"),
                    self.tr("The compilation of the form file failed."))
            else:
                ui.showNotification(
                    UI.PixmapCache.getPixmap("designer48.png"),
                    self.tr("Form Compilation"),
                    self.tr("The compilation of the form file failed."))
        self.compileProc = None
        
    def __compileUI(self, fn, noDialog=False, progress=None):
        """
        Private method to compile a .ui file to a .py/.rb file.
        
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
            if self.project.getProjectType() in ["Qt4", ]:
                self.uicompiler = 'pyuic4'
                if Utilities.isWindowsPlatform():
                    uic = self.uicompiler + '.bat'
                else:
                    uic = self.uicompiler
            elif self.project.getProjectType() in ["PyQt5"]:
                self.uicompiler = 'pyuic5'
                if Utilities.isWindowsPlatform():
                    uic = self.uicompiler + '.bat'
                else:
                    uic = self.uicompiler
            elif self.project.getProjectType() in ["E6Plugin"]:
                if PYQT_VERSION < 0x050000:
                    self.uicompiler = 'pyuic4'
                else:
                    self.uicompiler = 'pyuic5'
                if Utilities.isWindowsPlatform():
                    uic = self.uicompiler + '.bat'
                else:
                    uic = self.uicompiler
            elif self.project.getProjectType() == "PySide":
                self.uicompiler = 'pyside-uic'
                uic = Utilities.generatePySideToolPath(self.uicompiler)
            else:
                return None
        elif self.project.pdata["PROGLANGUAGE"][0] == "Ruby":
            if self.project.getProjectType() == "Qt4":
                self.uicompiler = 'rbuic4'
                if Utilities.isWindowsPlatform():
                    uic = self.uicompiler + '.exe'
                else:
                    uic = self.uicompiler
            else:
                return None
        else:
            return None
        
        ofn, ext = os.path.splitext(fn)
        fn = os.path.join(self.project.ppath, fn)
        
        if self.project.pdata["PROGLANGUAGE"][0] in \
                ["Python", "Python2", "Python3"]:
            dirname, filename = os.path.split(ofn)
            self.compiledFile = os.path.join(dirname, "Ui_" + filename + ".py")
            args.append("-x")
            indentWidth = Preferences.getQt("PyuicIndent")
            if indentWidth != self.PyuicIndentDefault:
                args.append("--indent={0}".format(indentWidth))
            if Preferences.getQt("PyuicFromImports"):
                args.append("--from-imports")
        elif self.project.pdata["PROGLANGUAGE"][0] == "Ruby":
            self.compiledFile = ofn + '.rb'
            args.append('-x')
        
        args.append(fn)
        self.compileProc.finished.connect(self.__compileUIDone)
        self.compileProc.readyReadStandardOutput.connect(self.__readStdout)
        self.compileProc.readyReadStandardError.connect(self.__readStderr)
        
        self.noDialog = noDialog
        self.compileProc.start(uic, args)
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
                ).format(self.uicompiler))
            return None
        
    def __generateDialogCode(self):
        """
        Private method to generate dialog code for the form (Qt4 only).
        """
        itm = self.model().item(self.currentIndex())
        fn = itm.fileName()
        
        if self.hooks["generateDialogCode"] is not None:
            self.hooks["generateDialogCode"](fn)
        else:
            from .CreateDialogCodeDialog import CreateDialogCodeDialog
            
            # change environment
            sys.path.insert(0, self.project.getProjectPath())
            cwd = os.getcwd()
            os.chdir(os.path.dirname(os.path.abspath(fn)))
            
            dlg = CreateDialogCodeDialog(fn, self.project, self)
            if not dlg.initError():
                dlg.exec_()
            
            # reset the environment
            os.chdir(cwd)
            del sys.path[0]
        
    def __compileForm(self):
        """
        Private method to compile a form to a source file.
        """
        itm = self.model().item(self.currentIndex())
        fn2 = itm.fileName()
        fn = self.project.getRelativePath(fn2)
        if self.hooks["compileForm"] is not None:
            self.hooks["compileForm"](fn)
        else:
            self.__compileUI(fn)
        
    def __compileAllForms(self):
        """
        Private method to compile all forms to source files.
        """
        if self.hooks["compileAllForms"] is not None:
            self.hooks["compileAllForms"](self.project.pdata["FORMS"])
        else:
            numForms = len(self.project.pdata["FORMS"])
            progress = E5ProgressDialog(
                self.tr("Compiling forms..."),
                self.tr("Abort"), 0, numForms,
                self.tr("%v/%m Forms"), self)
            progress.setModal(True)
            progress.setMinimumDuration(0)
            progress.setWindowTitle(self.tr("Forms"))
            i = 0
            
            for fn in self.project.pdata["FORMS"]:
                progress.setValue(i)
                if progress.wasCanceled():
                    break
                
                proc = self.__compileUI(fn, True, progress)
                if proc is not None:
                    while proc.state() == QProcess.Running:
                        QApplication.processEvents()
                        QThread.msleep(300)
                        QApplication.processEvents()
                else:
                    break
                i += 1
                
            progress.setValue(numForms)
        
    def __compileSelectedForms(self):
        """
        Private method to compile selected forms to source files.
        """
        items = self.getSelectedItems()
        files = [self.project.getRelativePath(itm.fileName())
                 for itm in items]
        
        if self.hooks["compileSelectedForms"] is not None:
            self.hooks["compileSelectedForms"](files)
        else:
            numForms = len(files)
            progress = E5ProgressDialog(
                self.tr("Compiling forms..."),
                self.tr("Abort"), 0, numForms,
                self.tr("%v/%m Forms"), self)
            progress.setModal(True)
            progress.setMinimumDuration(0)
            progress.setWindowTitle(self.tr("Forms"))
            i = 0
            
            for fn in files:
                progress.setValue(i)
                if progress.wasCanceled():
                    break
                
                proc = self.__compileUI(fn, True, progress)
                if proc is not None:
                    while proc.state() == QProcess.Running:
                        QApplication.processEvents()
                        QThread.msleep(300)
                        QApplication.processEvents()
                else:
                    break
                i += 1
                
            progress.setValue(numForms)
        
    def compileChangedForms(self):
        """
        Public method to compile all changed forms to source files.
        """
        if self.hooks["compileChangedForms"] is not None:
            self.hooks["compileChangedForms"](self.project.pdata["FORMS"])
        else:
            if self.project.getProjectType() not in \
               ["Qt4", "PyQt5", "E6Plugin", "PySide"]:
                # ignore the request for non Qt GUI projects
                return
            
            progress = E5ProgressDialog(
                self.tr("Determining changed forms..."),
                None, 0, 100, self.tr("%v/%m Forms"))
            progress.setMinimumDuration(0)
            progress.setWindowTitle(self.tr("Forms"))
            i = 0
            
            # get list of changed forms
            changedForms = []
            progress.setMaximum(len(self.project.pdata["FORMS"]))
            for fn in self.project.pdata["FORMS"]:
                progress.setValue(i)
                QApplication.processEvents()
                
                ifn = os.path.join(self.project.ppath, fn)
                if self.project.pdata["PROGLANGUAGE"][0] in \
                   ["Python", "Python2", "Python3"]:
                    dirname, filename = os.path.split(os.path.splitext(ifn)[0])
                    ofn = os.path.join(dirname, "Ui_" + filename + ".py")
                elif self.project.pdata["PROGLANGUAGE"][0] == "Ruby":
                    ofn = os.path.splitext(ifn)[0] + '.rb'
                if not os.path.exists(ofn) or \
                   os.stat(ifn).st_mtime > os.stat(ofn).st_mtime:
                    changedForms.append(fn)
                i += 1
            progress.setValue(i)
            QApplication.processEvents()
            
            if changedForms:
                progress.setLabelText(
                    self.tr("Compiling changed forms..."))
                progress.setMaximum(len(changedForms))
                i = 0
                progress.setValue(i)
                QApplication.processEvents()
                for fn in changedForms:
                    progress.setValue(i)
                    proc = self.__compileUI(fn, True, progress)
                    if proc is not None:
                        while proc.state() == QProcess.Running:
                            QApplication.processEvents()
                            QThread.msleep(300)
                            QApplication.processEvents()
                    else:
                        break
                    i += 1
                progress.setValue(len(changedForms))
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
        <li>compileForm: takes filename as parameter</li>
        <li>compileAllForms: takes list of filenames as parameter</li>
        <li>compileSelectedForms: takes list of filenames as parameter</li>
        <li>compileChangedForms: takes list of filenames as parameter</li>
        <li>generateDialogCode: takes filename as parameter</li>
        <li>newForm: takes full directory path of new file as parameter</li>
        <li>open: takes a filename as parameter</li>
        </ul>
        
        <b>Note</b>: Filenames are relative to the project directory, if not
        specified differently.
        """
        self.hooks = {
            "compileForm": None,
            "compileAllForms": None,
            "compileChangedForms": None,
            "compileSelectedForms": None,
            "generateDialogCode": None,
            "newForm": None,
            "open": None,
        }
