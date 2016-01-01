# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class used to display the parts of the project, that
don't fit the other categories.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QModelIndex, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QDialog, QMenu

from E5Gui import E5MessageBox

from .ProjectBrowserModel import ProjectBrowserFileItem, \
    ProjectBrowserSimpleDirectoryItem, ProjectBrowserDirectoryItem, \
    ProjectBrowserOthersType
from .ProjectBaseBrowser import ProjectBaseBrowser

import Utilities.MimeTypes
import Preferences


class ProjectOthersBrowser(ProjectBaseBrowser):
    """
    A class used to display the parts of the project, that don't fit the
    other categories.
    
    @signal sourceFile(str) emitted to open a file
    @signal pixmapFile(str) emitted to open a pixmap file
    @signal pixmapEditFile(str) emitted to edit a pixmap file
    @signal svgFile(str) emitted to open a SVG file
    @signal closeSourceWindow(str) emitted after a file has been
        removed/deleted from the project
    @signal showMenu(str, QMenu) emitted when a menu is about to be shown.
        The name of the menu and a reference to the menu are given.
    """
    showMenu = pyqtSignal(str, QMenu)
    
    def __init__(self, project, parent=None):
        """
        Constructor
        
        @param project reference to the project object
        @param parent parent widget of this browser (QWidget)
        """
        ProjectBaseBrowser.__init__(self, project, ProjectBrowserOthersType,
                                    parent)
    
        self.selectedItemsFilter = [ProjectBrowserFileItem,
                                    ProjectBrowserDirectoryItem]
        self.specialMenuEntries = [1]

        self.setWindowTitle(self.tr('Others'))

        self.setWhatsThis(self.tr(
            """<b>Project Others Browser</b>"""
            """<p>This allows to easily see all other files and directories"""
            """ contained in the current project. Several actions can be"""
            """ executed via the context menu. The entry which is registered"""
            """ in the project is shown in a different colour.</p>"""
        ))
        
        project.prepareRepopulateItem.connect(self._prepareRepopulateItem)
        project.completeRepopulateItem.connect(self._completeRepopulateItem)
        
    def _createPopupMenus(self):
        """
        Protected overloaded method to generate the popup menu.
        """
        ProjectBaseBrowser._createPopupMenus(self)
        
        self.editPixmapAct = self.menu.addAction(
            self.tr('Open in Icon Editor'), self._editPixmap)
        self.menu.addSeparator()
        self.mimeTypeAct = self.menu.addAction(
            self.tr('Show Mime-Type'), self.__showMimeType)
        self.menu.addSeparator()
        self.renameFileAct = self.menu.addAction(
            self.tr('Rename file'), self._renameFile)
        self.menuActions.append(self.renameFileAct)
        act = self.menu.addAction(
            self.tr('Remove from project'), self.__removeItem)
        self.menuActions.append(act)
        act = self.menu.addAction(self.tr('Delete'), self.__deleteItem)
        self.menuActions.append(act)
        self.menu.addSeparator()
        self.menu.addAction(
            self.tr('Add files...'), self.project.addOthersFiles)
        self.menu.addAction(
            self.tr('Add directory...'), self.project.addOthersDir)
        self.menu.addSeparator()
        self.menu.addAction(self.tr('Refresh'), self.__refreshItem)
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
        self.backMenu.addAction(
            self.tr('Add files...'), self.project.addOthersFiles)
        self.backMenu.addAction(
            self.tr('Add directory...'), self.project.addOthersDir)
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
            self.tr('Remove from project'), self.__removeItem)
        self.multiMenuActions.append(act)
        act = self.multiMenu.addAction(
            self.tr('Delete'), self.__deleteItem)
        self.multiMenuActions.append(act)
        self.multiMenu.addSeparator()
        self.multiMenu.addAction(
            self.tr('Expand all directories'), self._expandAllDirs)
        self.multiMenu.addAction(
            self.tr('Collapse all directories'), self._collapseAllDirs)
        self.multiMenu.addSeparator()
        self.multiMenu.addAction(self.tr('Configure...'), self._configure)
        
        self.menu.aboutToShow.connect(self.__showContextMenu)
        self.multiMenu.aboutToShow.connect(self.__showContextMenuMulti)
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
            cnt = self.getSelectedItemsCount()
            if cnt <= 1:
                index = self.indexAt(coord)
                if index.isValid():
                    self._selectSingleItem(index)
                    cnt = self.getSelectedItemsCount()
            
            if cnt > 1:
                self.multiMenu.popup(self.mapToGlobal(coord))
            else:
                index = self.indexAt(coord)
                if cnt == 1 and index.isValid():
                    itm = self.model().item(index)
                    if isinstance(itm, ProjectBrowserFileItem):
                        self.editPixmapAct.setVisible(itm.isPixmapFile())
                        self.mimeTypeAct.setVisible(True)
                        self.menu.popup(self.mapToGlobal(coord))
                    elif isinstance(itm, ProjectBrowserDirectoryItem):
                        self.editPixmapAct.setVisible(False)
                        self.mimeTypeAct.setVisible(False)
                        self.menu.popup(self.mapToGlobal(coord))
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
        self._showContextMenu(self.menu)
        
        self.showMenu.emit("Main", self.menu)
        
    def __showContextMenuMulti(self):
        """
        Private slot called by the multiMenu aboutToShow signal.
        """
        ProjectBaseBrowser._showContextMenuMulti(self, self.multiMenu)
        
        self.showMenu.emit("MainMulti", self.multiMenu)
        
    def __showContextMenuBack(self):
        """
        Private slot called by the backMenu aboutToShow signal.
        """
        ProjectBaseBrowser._showContextMenuBack(self, self.backMenu)
        
        self.showMenu.emit("MainBack", self.backMenu)
        
    def _showContextMenu(self, menu):
        """
        Protected slot called before the context menu is shown.
        
        It enables/disables the VCS menu entries depending on the overall
        VCS status and the file status.
        
        @param menu Reference to the popup menu (QPopupMenu)
        """
        if self.project.vcs is None:
            for act in self.menuActions:
                act.setEnabled(True)
            itm = self.model().item(self.currentIndex())
            if isinstance(itm, ProjectBrowserSimpleDirectoryItem) or \
               isinstance(itm, ProjectBrowserDirectoryItem):
                self.renameFileAct.setEnabled(False)
        else:
            self.vcsHelper.showContextMenu(menu, self.menuActions)
        
    def _editPixmap(self):
        """
        Protected slot to handle the open in icon editor popup menu entry.
        """
        itmList = self.getSelectedItems()
        
        for itm in itmList:
            if isinstance(itm, ProjectBrowserFileItem):
                if itm.isPixmapFile():
                    self.pixmapEditFile.emit(itm.fileName())
        
    def _openItem(self):
        """
        Protected slot to handle the open popup menu entry.
        """
        itmList = self.getSelectedItems()
        
        for itm in itmList:
            if isinstance(itm, ProjectBrowserFileItem):
                if itm.isPixmapFile():
                    self.pixmapFile.emit(itm.fileName())
                elif itm.isSvgFile():
                    self.svgFile.emit(itm.fileName())
                else:
                    if Utilities.MimeTypes.isTextFile(itm.fileName()):
                        self.sourceFile.emit(itm.fileName())
                    else:
                        QDesktopServices.openUrl(QUrl(itm.fileName()))
        
    def __showMimeType(self):
        """
        Private slot to show the mime type of the selected entry.
        """
        itmList = self.getSelectedItems()
        if itmList:
            mimetype = Utilities.MimeTypes.mimeType(itmList[0].fileName())
            if mimetype is None:
                E5MessageBox.warning(
                    self,
                    self.tr("Show Mime-Type"),
                    self.tr("""The mime type of the file could not be"""
                            """ determined."""))
            elif mimetype.split("/")[0] == "text":
                E5MessageBox.information(
                    self,
                    self.tr("Show Mime-Type"),
                    self.tr("""The file has the mime type <b>{0}</b>.""")
                    .format(mimetype))
            else:
                textMimeTypesList = Preferences.getUI("TextMimeTypes")
                if mimetype in textMimeTypesList:
                    E5MessageBox.information(
                        self,
                        self.tr("Show Mime-Type"),
                        self.tr("""The file has the mime type <b>{0}</b>.""")
                        .format(mimetype))
                else:
                    ok = E5MessageBox.yesNo(
                        self,
                        self.tr("Show Mime-Type"),
                        self.tr("""The file has the mime type <b>{0}</b>."""
                                """<br/> Shall it be added to the list of"""
                                """ text mime types?""").format(mimetype))
                    if ok:
                        textMimeTypesList.append(mimetype)
                        Preferences.setUI("TextMimeTypes", textMimeTypesList)
        
    def __removeItem(self):
        """
        Private slot to remove the selected entry from the OTHERS project
        data area.
        """
        itmList = self.getSelectedItems()
        
        for itm in itmList[:]:
            if isinstance(itm, ProjectBrowserFileItem):
                fn = itm.fileName()
                self.closeSourceWindow.emit(fn)
                self.project.removeFile(fn)
            else:
                dn = itm.dirName()
                self.project.removeDirectory(dn)
        
    def __deleteItem(self):
        """
        Private method to delete the selected entry from the OTHERS project
        data area.
        """
        itmList = self.getSelectedItems()
        
        items = []
        names = []
        fullNames = []
        dirItems = []
        dirNames = []
        dirFullNames = []
        for itm in itmList:
            if isinstance(itm, ProjectBrowserFileItem):
                fn2 = itm.fileName()
                fn = self.project.getRelativePath(fn2)
                items.append(itm)
                fullNames.append(fn2)
                names.append(fn)
            else:
                dn2 = itm.dirName()
                dn = self.project.getRelativePath(dn2)
                dirItems.append(itm)
                dirFullNames.append(dn2)
                dirNames.append(dn)
        items.extend(dirItems)
        fullNames.extend(dirFullNames)
        names.extend(dirNames)
        del itmList
        del dirFullNames
        del dirNames
        
        from UI.DeleteFilesConfirmationDialog import \
            DeleteFilesConfirmationDialog
        dlg = DeleteFilesConfirmationDialog(
            self.parent(),
            self.tr("Delete files/directories"),
            self.tr(
                "Do you really want to delete these entries from the"
                " project?"),
            names)
        
        if dlg.exec_() == QDialog.Accepted:
            for itm, fn2, fn in zip(items[:], fullNames, names):
                if isinstance(itm, ProjectBrowserFileItem):
                    self.closeSourceWindow.emit(fn2)
                    self.project.deleteFile(fn)
                elif isinstance(itm, ProjectBrowserDirectoryItem):
                    self.project.deleteDirectory(fn2)
        
    def __refreshItem(self):
        """
        Private slot to refresh (repopulate) an item.
        """
        itm = self.model().item(self.currentIndex())
        if isinstance(itm, ProjectBrowserFileItem):
            name = itm.fileName()
            self.project.repopulateItem(name)
        elif isinstance(itm, ProjectBrowserDirectoryItem):
            name = itm.dirName()
            self._model.directoryChanged(name)
        else:
            name = ''
        
        self._resizeColumns(QModelIndex())
