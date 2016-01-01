# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class used to display the Sources part of the project.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog, QInputDialog, QMenu

from E5Gui import E5MessageBox

from UI.BrowserModel import BrowserFileItem, BrowserClassItem, \
    BrowserMethodItem, BrowserClassAttributeItem, BrowserImportItem

from .ProjectBrowserModel import ProjectBrowserFileItem, \
    ProjectBrowserSimpleDirectoryItem, ProjectBrowserDirectoryItem, \
    ProjectBrowserSourceType
from .ProjectBaseBrowser import ProjectBaseBrowser

import Utilities
import UI.PixmapCache


class ProjectSourcesBrowser(ProjectBaseBrowser):
    """
    A class used to display the Sources part of the project.
    
    @signal closeSourceWindow(str) emitted after a file has been
        removed/deleted from the project
    @signal showMenu(str, QMenu) emitted when a menu is about to be shown.
        The name of the menu and a reference to the menu are given.
    @signal sourceFile(str) emitted to open the given file.
    @signal sourceFile(str, int) emitted to open the given file at the given
        line.
    @signal sourceFile(str, int, str) emitted to open the given file as the
        given type at the given line.
    @signal sourceFile(str, list) emitted to open a Python file giving a list
        of lines
    """
    showMenu = pyqtSignal(str, QMenu)
    
    def __init__(self, project, parent=None):
        """
        Constructor
        
        @param project reference to the project object
        @param parent parent widget of this browser (QWidget)
        """
        ProjectBaseBrowser.__init__(self, project, ProjectBrowserSourceType,
                                    parent)
        
        self.selectedItemsFilter = \
            [ProjectBrowserFileItem, ProjectBrowserSimpleDirectoryItem]
        
        self.setWindowTitle(self.tr('Sources'))

        self.setWhatsThis(self.tr(
            """<b>Project Sources Browser</b>"""
            """<p>This allows to easily see all sources contained in the"""
            """ current project. Several actions can be executed via the"""
            """ context menu.</p>"""
        ))
        
        project.prepareRepopulateItem.connect(self._prepareRepopulateItem)
        project.completeRepopulateItem.connect(self._completeRepopulateItem)
        
        self.codemetrics = None
        self.codecoverage = None
        self.profiledata = None
        self.classDiagram = None
        self.importsDiagram = None
        self.packageDiagram = None
        self.applicationDiagram = None
        self.loadedDiagram = None
        
    def __closeAllWindows(self):
        """
        Private method to close all project related windows.
        """
        self.codemetrics and self.codemetrics.close()
        self.codecoverage and self.codecoverage.close()
        self.profiledata and self.profiledata.close()
        self.classDiagram and self.classDiagram.close()
        self.importsDiagram and self.importsDiagram.close()
        self.packageDiagram and self.packageDiagram.close()
        self.applicationDiagram and self.applicationDiagram.close()
        self.loadedDiagram and self.loadedDiagram.close()
        
    def _projectClosed(self):
        """
        Protected slot to handle the projectClosed signal.
        """
        self.__closeAllWindows()
        ProjectBaseBrowser._projectClosed(self)
        
    def _createPopupMenus(self):
        """
        Protected overloaded method to generate the popup menu.
        """
        ProjectBaseBrowser._createPopupMenus(self)
        self.sourceMenuActions = {}
        
        if self.project.isPythonProject():
            self.__createPythonPopupMenus()
        elif self.project.isRubyProject():
            self.__createRubyPopupMenus()
        elif self.project.isJavaScriptProject():
            self.__createJavaScriptPopupMenus()
        
    def __createPythonPopupMenus(self):
        """
        Private method to generate the popup menus for a Python project.
        """
        self.checksMenu = QMenu(self.tr('Check'))
        self.checksMenu.aboutToShow.connect(self.__showContextMenuCheck)
        
        self.menuShow = QMenu(self.tr('Show'))
        self.menuShow.addAction(
            self.tr('Code metrics...'), self.__showCodeMetrics)
        self.coverageMenuAction = self.menuShow.addAction(
            self.tr('Code coverage...'), self.__showCodeCoverage)
        self.profileMenuAction = self.menuShow.addAction(
            self.tr('Profile data...'), self.__showProfileData)
        self.menuShow.aboutToShow.connect(self.__showContextMenuShow)
        
        self.graphicsMenu = QMenu(self.tr('Diagrams'))
        self.classDiagramAction = self.graphicsMenu.addAction(
            self.tr("Class Diagram..."), self.__showClassDiagram)
        self.graphicsMenu.addAction(
            self.tr("Package Diagram..."), self.__showPackageDiagram)
        self.importsDiagramAction = self.graphicsMenu.addAction(
            self.tr("Imports Diagram..."), self.__showImportsDiagram)
        self.graphicsMenu.addAction(
            self.tr("Application Diagram..."),
            self.__showApplicationDiagram)
        self.graphicsMenu.addSeparator()
        self.graphicsMenu.addAction(
            UI.PixmapCache.getIcon("open.png"),
            self.tr("Load Diagram..."), self.__loadDiagram)
        self.graphicsMenu.aboutToShow.connect(self.__showContextMenuGraphics)
        
        self.unittestAction = self.sourceMenu.addAction(
            self.tr('Run unittest...'), self.handleUnittest)
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
            self.tr('New package...'), self.__addNewPackage)
        self.sourceMenu.addAction(
            self.tr('Add source files...'), self.__addSourceFiles)
        self.sourceMenu.addAction(
            self.tr('Add source directory...'), self.__addSourceDirectory)
        self.sourceMenu.addSeparator()
        act = self.sourceMenu.addMenu(self.graphicsMenu)
        self.sourceMenu.addSeparator()
        self.sourceMenu.addMenu(self.checksMenu)
        self.sourceMenu.addSeparator()
        self.sourceMenuActions["Show"] = self.sourceMenu.addMenu(self.menuShow)
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

        self.menu.addSeparator()
        self.menu.addAction(
            self.tr('New package...'), self.__addNewPackage)
        self.menu.addAction(
            self.tr('Add source files...'), self.__addSourceFiles)
        self.menu.addAction(
            self.tr('Add source directory...'), self.__addSourceDirectory)
        self.menu.addSeparator()
        self.menu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.menu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.menu.addSeparator()
        self.menu.addAction(self.tr('Configure...'), self._configure)

        # create the attribute menu
        self.gotoMenu = QMenu(self.tr("Goto"), self)
        self.gotoMenu.aboutToShow.connect(self._showGotoMenu)
        self.gotoMenu.triggered.connect(self._gotoAttribute)
        
        self.attributeMenu = QMenu(self)
        self.attributeMenu.addMenu(self.gotoMenu)
        self.attributeMenu.addSeparator()
        self.attributeMenu.addAction(
            self.tr('New package...'), self.__addNewPackage)
        self.attributeMenu.addAction(
            self.tr('Add source files...'), self.project.addSourceFiles)
        self.attributeMenu.addAction(
            self.tr('Add source directory...'), self.project.addSourceDir)
        self.attributeMenu.addSeparator()
        self.attributeMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.attributeMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.attributeMenu.addSeparator()
        self.attributeMenu.addAction(
            self.tr('Configure...'), self._configure)
        
        self.backMenu = QMenu(self)
        self.backMenu.addAction(
            self.tr('New package...'), self.__addNewPackage)
        self.backMenu.addAction(
            self.tr('Add source files...'), self.project.addSourceFiles)
        self.backMenu.addAction(
            self.tr('Add source directory...'), self.project.addSourceDir)
        self.backMenu.addSeparator()
        self.backMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.backMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.backMenu.addSeparator()
        self.backMenu.addAction(self.tr('Configure...'), self._configure)
        self.backMenu.setEnabled(False)
        
        self.multiMenu.addSeparator()
        act = self.multiMenu.addAction(
            self.tr('Remove from project'), self._removeFile)
        self.multiMenuActions.append(act)
        act = self.multiMenu.addAction(
            self.tr('Delete'), self.__deleteFile)
        self.multiMenuActions.append(act)
        self.multiMenu.addSeparator()
        self.multiMenu.addMenu(self.checksMenu)
        self.multiMenu.addSeparator()
        self.multiMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.multiMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.multiMenu.addSeparator()
        self.multiMenu.addAction(self.tr('Configure...'), self._configure)
        
        self.dirMenu = QMenu(self)
        act = self.dirMenu.addAction(
            self.tr('Remove from project'), self._removeDir)
        self.dirMenuActions.append(act)
        act = self.dirMenu.addAction(
            self.tr('Delete'), self._deleteDirectory)
        self.dirMenuActions.append(act)
        self.dirMenu.addSeparator()
        self.dirMenu.addAction(
            self.tr('New package...'), self.__addNewPackage)
        self.dirMenu.addAction(
            self.tr('Add source files...'), self.__addSourceFiles)
        self.dirMenu.addAction(
            self.tr('Add source directory...'), self.__addSourceDirectory)
        self.dirMenu.addSeparator()
        act = self.dirMenu.addMenu(self.graphicsMenu)
        self.dirMenu.addSeparator()
        self.dirMenu.addMenu(self.checksMenu)
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
        self.dirMultiMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.dirMultiMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.dirMultiMenu.addSeparator()
        self.dirMultiMenu.addAction(
            self.tr('Configure...'), self._configure)
        
        self.sourceMenu.aboutToShow.connect(self.__showContextMenu)
        self.multiMenu.aboutToShow.connect(self.__showContextMenuMulti)
        self.dirMenu.aboutToShow.connect(self.__showContextMenuDir)
        self.dirMultiMenu.aboutToShow.connect(self.__showContextMenuDirMulti)
        self.backMenu.aboutToShow.connect(self.__showContextMenuBack)
        self.mainMenu = self.sourceMenu
        
    def __createRubyPopupMenus(self):
        """
        Private method to generate the popup menus for a Ruby project.
        """
        self.graphicsMenu = QMenu(self.tr('Diagrams'))
        self.classDiagramAction = self.graphicsMenu.addAction(
            self.tr("Class Diagram..."), self.__showClassDiagram)
        self.graphicsMenu.addAction(
            self.tr("Package Diagram..."), self.__showPackageDiagram)
        self.graphicsMenu.addAction(
            self.tr("Application Diagram..."),
            self.__showApplicationDiagram)
        self.graphicsMenu.addSeparator()
        self.graphicsMenu.addAction(
            UI.PixmapCache.getIcon("fileOpen.png"),
            self.tr("Load Diagram..."), self.__loadDiagram)
        
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
            self.tr('Add source files...'), self.__addSourceFiles)
        self.sourceMenu.addAction(
            self.tr('Add source directory...'), self.__addSourceDirectory)
        self.sourceMenu.addSeparator()
        act = self.sourceMenu.addMenu(self.graphicsMenu)
        self.sourceMenu.addSeparator()
        self.sourceMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.sourceMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.sourceMenu.addSeparator()
        self.sourceMenu.addAction(self.tr('Configure...'), self._configure)

        self.menu.addSeparator()
        self.menu.addAction(
            self.tr('Add source files...'), self.__addSourceFiles)
        self.menu.addAction(
            self.tr('Add source directory...'), self.__addSourceDirectory)
        self.menu.addSeparator()
        self.menu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.menu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.menu.addSeparator()
        self.menu.addAction(self.tr('Configure...'), self._configure)

        # create the attribute menu
        self.gotoMenu = QMenu(self.tr("Goto"), self)
        self.gotoMenu.aboutToShow.connect(self._showGotoMenu)
        self.gotoMenu.triggered.connect(self._gotoAttribute)
        
        self.attributeMenu = QMenu(self)
        self.attributeMenu.addMenu(self.gotoMenu)
        self.attributeMenu.addSeparator()
        self.attributeMenu.addAction(
            self.tr('Add source files...'), self.project.addSourceFiles)
        self.attributeMenu.addAction(
            self.tr('Add source directory...'), self.project.addSourceDir)
        self.attributeMenu.addSeparator()
        self.attributeMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.attributeMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.attributeMenu.addSeparator()
        self.attributeMenu.addAction(
            self.tr('Configure...'), self._configure)
        
        self.backMenu = QMenu(self)
        self.backMenu.addAction(
            self.tr('Add source files...'), self.project.addSourceFiles)
        self.backMenu.addAction(
            self.tr('Add source directory...'), self.project.addSourceDir)
        self.backMenu.addSeparator()
        self.backMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.backMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.backMenu.setEnabled(False)
        self.backMenu.addSeparator()
        self.backMenu.addAction(self.tr('Configure...'), self._configure)
        
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
        act = self.dirMenu.addAction(
            self.tr('Remove from project'), self._removeDir)
        self.dirMenuActions.append(act)
        self.dirMenu.addSeparator()
        self.dirMenu.addAction(
            self.tr('Add source files...'), self.__addSourceFiles)
        self.dirMenu.addAction(
            self.tr('Add source directory...'), self.__addSourceDirectory)
        self.dirMenu.addSeparator()
        act = self.dirMenu.addMenu(self.graphicsMenu)
        self.dirMenu.addSeparator()
        self.dirMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.dirMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.dirMenu.addSeparator()
        self.dirMenu.addAction(self.tr('Configure...'), self._configure)
        
        self.dirMultiMenu = QMenu(self)
        self.dirMultiMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.dirMultiMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.dirMultiMenu.addSeparator()
        self.dirMultiMenu.addAction(
            self.tr('Configure...'), self._configure)
        
        self.sourceMenu.aboutToShow.connect(self.__showContextMenu)
        self.multiMenu.aboutToShow.connect(self.__showContextMenuMulti)
        self.dirMenu.aboutToShow.connect(self.__showContextMenuDir)
        self.dirMultiMenu.aboutToShow.connect(self.__showContextMenuDirMulti)
        self.backMenu.aboutToShow.connect(self.__showContextMenuBack)
        self.mainMenu = self.sourceMenu
        
    def __createJavaScriptPopupMenus(self):
        """
        Private method to generate the popup menus for a Python project.
        """
        self.checksMenu = QMenu(self.tr('Check'))
        self.checksMenu.aboutToShow.connect(self.__showContextMenuCheck)
        
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
            self.tr('Add source files...'), self.__addSourceFiles)
        self.sourceMenu.addAction(
            self.tr('Add source directory...'), self.__addSourceDirectory)
        self.sourceMenu.addSeparator()
        self.sourceMenu.addMenu(self.checksMenu)
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

        self.menu.addSeparator()
        self.menu.addAction(
            self.tr('Add source files...'), self.__addSourceFiles)
        self.menu.addAction(
            self.tr('Add source directory...'), self.__addSourceDirectory)
        self.menu.addSeparator()
        self.menu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.menu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.menu.addSeparator()
        self.menu.addAction(self.tr('Configure...'), self._configure)

        # create the attribute menu
        self.gotoMenu = QMenu(self.tr("Goto"), self)
        self.gotoMenu.aboutToShow.connect(self._showGotoMenu)
        self.gotoMenu.triggered.connect(self._gotoAttribute)
        
        self.attributeMenu = QMenu(self)
        self.attributeMenu.addMenu(self.gotoMenu)
        self.attributeMenu.addSeparator()
        self.attributeMenu.addAction(
            self.tr('Add source files...'), self.project.addSourceFiles)
        self.attributeMenu.addAction(
            self.tr('Add source directory...'), self.project.addSourceDir)
        self.attributeMenu.addSeparator()
        self.attributeMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.attributeMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.attributeMenu.addSeparator()
        self.attributeMenu.addAction(
            self.tr('Configure...'), self._configure)
        
        self.backMenu = QMenu(self)
        self.backMenu.addAction(
            self.tr('Add source files...'), self.project.addSourceFiles)
        self.backMenu.addAction(
            self.tr('Add source directory...'), self.project.addSourceDir)
        self.backMenu.addSeparator()
        self.backMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.backMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.backMenu.addSeparator()
        self.backMenu.addAction(self.tr('Configure...'), self._configure)
        self.backMenu.setEnabled(False)
        
        self.multiMenu.addSeparator()
        act = self.multiMenu.addAction(
            self.tr('Remove from project'), self._removeFile)
        self.multiMenuActions.append(act)
        act = self.multiMenu.addAction(
            self.tr('Delete'), self.__deleteFile)
        self.multiMenuActions.append(act)
        self.multiMenu.addSeparator()
        self.multiMenu.addMenu(self.checksMenu)
        self.multiMenu.addSeparator()
        self.multiMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.multiMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.multiMenu.addSeparator()
        self.multiMenu.addAction(self.tr('Configure...'), self._configure)
        
        self.dirMenu = QMenu(self)
        act = self.dirMenu.addAction(
            self.tr('Remove from project'), self._removeDir)
        self.dirMenuActions.append(act)
        act = self.dirMenu.addAction(
            self.tr('Delete'), self._deleteDirectory)
        self.dirMenuActions.append(act)
        self.dirMenu.addSeparator()
        self.dirMenu.addAction(
            self.tr('Add source files...'), self.__addSourceFiles)
        self.dirMenu.addAction(
            self.tr('Add source directory...'), self.__addSourceDirectory)
        self.dirMenu.addSeparator()
        self.dirMenu.addMenu(self.checksMenu)
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
        self.dirMultiMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.dirMultiMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.dirMultiMenu.addSeparator()
        self.dirMultiMenu.addAction(
            self.tr('Configure...'), self._configure)
        
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
                 BrowserMethodItem, ProjectBrowserSimpleDirectoryItem,
                 BrowserClassAttributeItem, BrowserImportItem])
            cnt = categories["sum"]
            if cnt <= 1:
                index = self.indexAt(coord)
                if index.isValid():
                    self._selectSingleItem(index)
                    categories = self.getSelectedItemsCountCategorized(
                        [ProjectBrowserFileItem, BrowserClassItem,
                         BrowserMethodItem, ProjectBrowserSimpleDirectoryItem,
                         BrowserClassAttributeItem, BrowserImportItem])
                    cnt = categories["sum"]
            
            bfcnt = categories[str(ProjectBrowserFileItem)]
            cmcnt = categories[str(BrowserClassItem)] + \
                categories[str(BrowserMethodItem)] + \
                categories[str(BrowserClassAttributeItem)] + \
                categories[str(BrowserImportItem)]
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
                            fn = itm.fileName()
                            if self.project.isPythonProject():
                                if fn.endswith('.ptl'):
                                    for act in self.sourceMenuActions.values():
                                        act.setEnabled(False)
                                    self.classDiagramAction.setEnabled(True)
                                    self.importsDiagramAction.setEnabled(True)
                                    self.unittestAction.setEnabled(False)
                                    self.checksMenu.menuAction().setEnabled(
                                        False)
                                elif fn.endswith('.rb'):
                                    # entry for mixed mode programs
                                    for act in self.sourceMenuActions.values():
                                        act.setEnabled(False)
                                    self.classDiagramAction.setEnabled(True)
                                    self.importsDiagramAction.setEnabled(False)
                                    self.unittestAction.setEnabled(False)
                                    self.checksMenu.menuAction().setEnabled(
                                        False)
                                elif fn.endswith('.js'):
                                    # entry for mixed mode programs
                                    for act in self.sourceMenuActions.values():
                                        act.setEnabled(False)
                                    self.unittestAction.setEnabled(False)
                                    self.checksMenu.menuAction().setEnabled(
                                        False)
                                    self.graphicsMenu.menuAction().setEnabled(
                                        False)
                                else:
                                    # assume the source file is a Python file
                                    for act in self.sourceMenuActions.values():
                                        act.setEnabled(True)
                                    self.classDiagramAction.setEnabled(True)
                                    self.importsDiagramAction.setEnabled(True)
                                    self.unittestAction.setEnabled(True)
                                    self.checksMenu.menuAction().setEnabled(
                                        True)
                            self.sourceMenu.popup(self.mapToGlobal(coord))
                        elif isinstance(itm, BrowserClassItem) or \
                            isinstance(itm, BrowserMethodItem) or \
                                isinstance(itm, BrowserImportItem):
                            self.menu.popup(self.mapToGlobal(coord))
                        elif isinstance(itm, BrowserClassAttributeItem):
                            self.attributeMenu.popup(self.mapToGlobal(coord))
                        else:
                            self.backMenu.popup(self.mapToGlobal(coord))
                    elif sdcnt == 1:
                        self.classDiagramAction.setEnabled(False)
                        self.dirMenu.popup(self.mapToGlobal(coord))
                    else:
                        self.backMenu.popup(self.mapToGlobal(coord))
                else:
                    self.backMenu.popup(self.mapToGlobal(coord))
        except:
            pass
        
    def __showContextMenu(self):
        """
        Private slot called by the sourceMenu aboutToShow signal.
        """
        ProjectBaseBrowser._showContextMenu(self, self.sourceMenu)
        
        self.showMenu.emit("Main", self.sourceMenu)
        
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
        
    def __showContextMenuShow(self):
        """
        Private slot called before the show menu is shown.
        """
        prEnable = False
        coEnable = False
        
        # first check if the file belongs to a project and there is
        # a project coverage file
        fn = self.project.getMainScript(True)
        if fn is not None:
            tfn = Utilities.getTestFileName(fn)
            basename = os.path.splitext(fn)[0]
            tbasename = os.path.splitext(tfn)[0]
            prEnable = prEnable or \
                os.path.isfile("{0}.profile".format(basename)) or \
                os.path.isfile("{0}.profile".format(tbasename))
            coEnable = (coEnable or
                        os.path.isfile("{0}.coverage".format(basename)) or
                        os.path.isfile("{0}.coverage".format(tbasename))) and \
                (self.project.isPy3Project() or self.project.isPy2Project())
        
        # now check the selected item
        itm = self.model().item(self.currentIndex())
        fn = itm.fileName()
        if fn is not None:
            basename = os.path.splitext(fn)[0]
            prEnable = prEnable or \
                os.path.isfile("{0}.profile".format(basename))
            coEnable = (coEnable or
                        os.path.isfile("{0}.coverage".format(basename))) and \
                (itm.isPython3File() or itm.isPython2File())
        
        self.profileMenuAction.setEnabled(prEnable)
        self.coverageMenuAction.setEnabled(coEnable)
        
        self.showMenu.emit("Show", self.menuShow)
        
    def _openItem(self):
        """
        Protected slot to handle the open popup menu entry.
        """
        itmList = self.getSelectedItems(
            [BrowserFileItem, BrowserClassItem, BrowserMethodItem,
             BrowserClassAttributeItem, BrowserImportItem])
        
        for itm in itmList:
            if isinstance(itm, BrowserFileItem):
                if itm.isPython2File():
                    self.sourceFile[str].emit(itm.fileName())
                elif itm.isPython3File():
                    self.sourceFile[str].emit(itm.fileName())
                elif itm.isRubyFile():
                    self.sourceFile[str, int, str].emit(
                        itm.fileName(), -1, "Ruby")
                elif itm.isDFile():
                    self.sourceFile[str, int, str].emit(
                        itm.fileName(), -1, "D")
                else:
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
            elif isinstance(itm, BrowserImportItem):
                self.sourceFile[str, list].emit(
                    itm.fileName(), itm.linenos())
        
    def __addNewPackage(self):
        """
        Private method to add a new package to the project.
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
            dn = ""
        
        dn = self.project.getRelativePath(dn)
        if dn.startswith(os.sep):
            dn = dn[1:]
        from .NewPythonPackageDialog import NewPythonPackageDialog
        dlg = NewPythonPackageDialog(dn, self)
        if dlg.exec_() == QDialog.Accepted:
            packageName = dlg.getData()
            nameParts = packageName.split(".")
            packagePath = self.project.ppath
            packageFile = ""
            for name in nameParts:
                packagePath = os.path.join(packagePath, name)
                if not os.path.exists(packagePath):
                    try:
                        os.mkdir(packagePath)
                    except OSError as err:
                        E5MessageBox.critical(
                            self,
                            self.tr("Add new Python package"),
                            self.tr(
                                """<p>The package directory <b>{0}</b> could"""
                                """ not be created. Aborting...</p>"""
                                """<p>Reason: {1}</p>""")
                            .format(packagePath, str(err)))
                        return
                packageFile = os.path.join(packagePath, "__init__.py")
                if not os.path.exists(packageFile):
                    try:
                        f = open(packageFile, "w", encoding="utf-8")
                        f.close()
                    except IOError as err:
                        E5MessageBox.critical(
                            self,
                            self.tr("Add new Python package"),
                            self.tr(
                                """<p>The package file <b>{0}</b> could"""
                                """ not be created. Aborting...</p>"""
                                """<p>Reason: {1}</p>""")
                            .format(packageFile, str(err)))
                        return
                self.project.appendFile(packageFile)
            if packageFile:
                self.sourceFile[str].emit(packageFile)
        
    def __addSourceFiles(self):
        """
        Private method to add a source file to the project.
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
        self.project.addFiles('source', dn)
        
    def __addSourceDirectory(self):
        """
        Private method to add source files of a directory to the project.
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
        self.project.addDirectory('source', dn)
        
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
            self.tr("Delete files"),
            self.tr(
                "Do you really want to delete these files from the project?"),
            files)
        
        if dlg.exec_() == QDialog.Accepted:
            for fn2, fn in zip(fullNames, files):
                self.closeSourceWindow.emit(fn2)
                self.project.deleteFile(fn)
    
    ###########################################################################
    ## Methods for the Checks submenu
    ###########################################################################
    
    def __showContextMenuCheck(self):
        """
        Private slot called before the checks menu is shown.
        """
        self.showMenu.emit("Checks", self.checksMenu)
    
    ###########################################################################
    ## Methods for the Show submenu
    ###########################################################################
    
    def __showCodeMetrics(self):
        """
        Private method to handle the code metrics context menu action.
        """
        itm = self.model().item(self.currentIndex())
        fn = itm.fileName()
        
        from DataViews.CodeMetricsDialog import CodeMetricsDialog
        self.codemetrics = CodeMetricsDialog()
        self.codemetrics.show()
        self.codemetrics.start(fn)
    
    def __showCodeCoverage(self):
        """
        Private method to handle the code coverage context menu action.
        """
        itm = self.model().item(self.currentIndex())
        fn = itm.fileName()
        pfn = self.project.getMainScript(True)
        
        files = []
        
        if pfn is not None:
            tpfn = Utilities.getTestFileName(pfn)
            basename = os.path.splitext(pfn)[0]
            tbasename = os.path.splitext(tpfn)[0]
            
            f = "{0}.coverage".format(basename)
            tf = "{0}.coverage".format(tbasename)
            if os.path.isfile(f):
                files.append(f)
            if os.path.isfile(tf):
                files.append(tf)
        
        if fn is not None:
            tfn = Utilities.getTestFileName(fn)
            basename = os.path.splitext(fn)[0]
            tbasename = os.path.splitext(tfn)[0]
            
            f = "{0}.coverage".format(basename)
            tf = "{0}.coverage".format(tbasename)
            if os.path.isfile(f) and f not in files:
                files.append(f)
            if os.path.isfile(tf) and tf not in files:
                files.append(tf)
        
        if files:
            if len(files) > 1:
                pfn, ok = QInputDialog.getItem(
                    None,
                    self.tr("Code Coverage"),
                    self.tr("Please select a coverage file"),
                    files,
                    0, False)
                if not ok:
                    return
            else:
                pfn = files[0]
        else:
            return
        
        from DataViews.PyCoverageDialog import PyCoverageDialog
        self.codecoverage = PyCoverageDialog()
        self.codecoverage.show()
        self.codecoverage.start(pfn, fn)
    
    def __showProfileData(self):
        """
        Private method to handle the show profile data context menu action.
        """
        itm = self.model().item(self.currentIndex())
        fn = itm.fileName()
        pfn = self.project.getMainScript(True)
        
        files = []
        
        if pfn is not None:
            tpfn = Utilities.getTestFileName(pfn)
            basename = os.path.splitext(pfn)[0]
            tbasename = os.path.splitext(tpfn)[0]
            
            f = "{0}.profile".format(basename)
            tf = "{0}.profile".format(tbasename)
            if os.path.isfile(f):
                files.append(f)
            if os.path.isfile(tf):
                files.append(tf)
        
        if fn is not None:
            tfn = Utilities.getTestFileName(fn)
            basename = os.path.splitext(fn)[0]
            tbasename = os.path.splitext(tfn)[0]
            
            f = "{0}.profile".format(basename)
            tf = "{0}.profile".format(tbasename)
            if os.path.isfile(f) and f not in files:
                files.append(f)
            if os.path.isfile(tf) and tf not in files:
                files.append(tf)
                
        if files:
            if len(files) > 1:
                pfn, ok = QInputDialog.getItem(
                    None,
                    self.tr("Profile Data"),
                    self.tr("Please select a profile file"),
                    files,
                    0, False)
                if not ok:
                    return
            else:
                pfn = files[0]
        else:
            return
            
        from DataViews.PyProfileDialog import PyProfileDialog
        self.profiledata = PyProfileDialog()
        self.profiledata.show()
        self.profiledata.start(pfn, fn)
    
    ###########################################################################
    ## Methods for the Graphics submenu
    ###########################################################################
    
    def __showContextMenuGraphics(self):
        """
        Private slot called before the checks menu is shown.
        """
        self.showMenu.emit("Graphics", self.graphicsMenu)
    
    def __showClassDiagram(self):
        """
        Private method to handle the class diagram context menu action.
        """
        itm = self.model().item(self.currentIndex())
        try:
            fn = itm.fileName()
        except AttributeError:
            fn = itm.dirName()
        res = E5MessageBox.yesNo(
            self,
            self.tr("Class Diagram"),
            self.tr("""Include class attributes?"""),
            yesDefault=True)
        from Graphics.UMLDialog import UMLDialog
        self.classDiagram = UMLDialog(UMLDialog.ClassDiagram, self.project, fn,
                                      self, noAttrs=not res)
        self.classDiagram.show()
        
    def __showImportsDiagram(self):
        """
        Private method to handle the imports diagram context menu action.
        """
        itm = self.model().item(self.currentIndex())
        try:
            fn = itm.fileName()
        except AttributeError:
            fn = itm.dirName()
        package = os.path.isdir(fn) and fn or os.path.dirname(fn)
        res = E5MessageBox.yesNo(
            self,
            self.tr("Imports Diagram"),
            self.tr("""Include imports from external modules?"""))
        from Graphics.UMLDialog import UMLDialog
        self.importsDiagram = UMLDialog(
            UMLDialog.ImportsDiagram, self.project, package,
            self, showExternalImports=res)
        self.importsDiagram.show()
        
    def __showPackageDiagram(self):
        """
        Private method to handle the package diagram context menu action.
        """
        itm = self.model().item(self.currentIndex())
        try:
            fn = itm.fileName()
        except AttributeError:
            fn = itm.dirName()
        package = os.path.isdir(fn) and fn or os.path.dirname(fn)
        res = E5MessageBox.yesNo(
            self,
            self.tr("Package Diagram"),
            self.tr("""Include class attributes?"""),
            yesDefault=True)
        from Graphics.UMLDialog import UMLDialog
        self.packageDiagram = UMLDialog(
            UMLDialog.PackageDiagram, self.project, package,
            self, noAttrs=not res)
        self.packageDiagram.show()
        
    def __showApplicationDiagram(self):
        """
        Private method to handle the application diagram context menu action.
        """
        res = E5MessageBox.yesNo(
            self,
            self.tr("Application Diagram"),
            self.tr("""Include module names?"""),
            yesDefault=True)
        from Graphics.UMLDialog import UMLDialog
        self.applicationDiagram = UMLDialog(
            UMLDialog.ApplicationDiagram, self.project,
            self, noModules=not res)
        self.applicationDiagram.show()
    
    def __loadDiagram(self):
        """
        Private slot to load a diagram from file.
        """
        from Graphics.UMLDialog import UMLDialog
        self.loadedDiagram = None
        loadedDiagram = UMLDialog(
            UMLDialog.NoDiagram, self.project, parent=self)
        if loadedDiagram.load():
            self.loadedDiagram = loadedDiagram
            self.loadedDiagram.show(fromFile=True)
