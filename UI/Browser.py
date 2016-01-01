# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a browser with class browsing capabilities.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QModelIndex, pyqtSignal, QUrl, Qt, qVersion, \
    QCoreApplication, QItemSelectionModel
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QTreeView, QApplication, QMenu, QAbstractItemView

from E5Gui.E5Application import e5App
from E5Gui import E5FileDialog, E5MessageBox

from Project.ProjectBrowserModel import ProjectBrowserSimpleDirectoryItem
from .BrowserModel import BrowserModel, BrowserDirectoryItem, \
    BrowserFileItem, BrowserClassItem, BrowserMethodItem, \
    BrowserClassAttributeItem, BrowserImportItem, BrowserImportsItem, \
    BrowserSysPathItem, BrowserGlobalsItem
from .BrowserSortFilterProxyModel import BrowserSortFilterProxyModel

import UI.PixmapCache
import Preferences
import Utilities
import Utilities.MimeTypes


class Browser(QTreeView):
    """
    Class used to display a file system tree.
    
    Via the context menu that
    is displayed by a right click the user can select various actions on
    the selected file.
    
    @signal sourceFile(str, int = 0, str = "") emitted to open a Python file
        at a line
    @signal sourceFile(str, list) emitted to open a Python file giving a list
        of lines
    @signal designerFile(str) emitted to open a Qt-Designer file
    @signal linguistFile(str) emitted to open a Qt-Linguist (*.ts) file
    @signal trpreview(list of str, bool = False) emitted to preview a
        Qt-Linguist (*.qm) file
    @signal projectFile(str) emitted to open an eric4/5 project file
    @signal multiProjectFile(str) emitted to open an eric4/5 multi project file
    @signal pixmapFile(str) emitted to open a pixmap file
    @signal pixmapEditFile(str) emitted to edit a pixmap file
    @signal svgFile(str) emitted to open a SVG file
    @signal unittestOpen(str) emitted to open a Python file for a unittest
    """
    sourceFile = pyqtSignal((str, ), (str, int), (str, list), (str, int, str))
    designerFile = pyqtSignal(str)
    linguistFile = pyqtSignal(str)
    trpreview = pyqtSignal((list, ), (list, bool))
    projectFile = pyqtSignal(str)
    multiProjectFile = pyqtSignal(str)
    pixmapFile = pyqtSignal(str)
    pixmapEditFile = pyqtSignal(str)
    svgFile = pyqtSignal(str)
    unittestOpen = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        """
        super(Browser, self).__init__(parent)
        
        self.setWindowTitle(QCoreApplication.translate('Browser',
                                                       'File-Browser'))
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        
        self.__embeddedBrowser = Preferences.getUI("LayoutFileBrowserEmbedded")
        
        self.__model = BrowserModel()
        self.__sortModel = BrowserSortFilterProxyModel()
        self.__sortModel.setSourceModel(self.__model)
        self.setModel(self.__sortModel)
        
        self.selectedItemsFilter = [BrowserFileItem]
        
        self._activating = False
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._contextMenuRequested)
        self.activated.connect(self._openItem)
        self.expanded.connect(self._resizeColumns)
        self.collapsed.connect(self._resizeColumns)
        
        self.setWhatsThis(QCoreApplication.translate(
            'Browser',
            """<b>The Browser Window</b>"""
            """<p>This allows you to easily navigate the hierarchy of"""
            """ directories and files on your system, identify the Python"""
            """ programs and open them up in a Source Viewer window. The"""
            """ window displays several separate hierarchies.</p>"""
            """<p>The first hierarchy is only shown if you have opened a"""
            """ program for debugging and its root is the directory"""
            """ containing that program. Usually all of the separate files"""
            """ that make up a Python application are held in the same"""
            """ directory, so this hierarchy gives you easy access to most"""
            """ of what you will need.</p>"""
            """<p>The next hierarchy is used to easily navigate the"""
            """ directories that are specified in the Python"""
            """ <tt>sys.path</tt> variable.</p>"""
            """<p>The remaining hierarchies allow you navigate your system"""
            """ as a whole. On a UNIX system there will be a hierarchy with"""
            """ <tt>/</tt> at its root and another with the user home"""
            """ directory. On a Windows system there will be a hierarchy for"""
            """ each drive on the"""
            """ system.</p>"""
            """<p>Python programs (i.e. those with a <tt>.py</tt> file name"""
            """ suffix) are identified in the hierarchies with a Python"""
            """ icon. The right mouse button will popup a menu which lets"""
            """ you open the file in a Source Viewer window, open the file"""
            """ for debugging or use it for a unittest run.</p>"""
            """<p>The context menu of a class, function or method allows you"""
            """ to open the file defining this class, function or method and"""
            """ will ensure, that the correct source line is visible.</p>"""
            """<p>Qt-Designer files (i.e. those with a <tt>.ui</tt> file"""
            """ name suffix) are shown with a Designer icon. The context"""
            """ menu of these files allows you to start Qt-Designer with"""
            """ that file.</p>"""
            """<p>Qt-Linguist files (i.e. those with a <tt>.ts</tt> file"""
            """ name suffix) are shown with a Linguist icon. The context"""
            """ menu of these files allows you to start Qt-Linguist with"""
            """ that file.</p>"""
        ))
        
        self.__createPopupMenus()
        
        self._init()    # perform common initialization tasks
        
    def _init(self):
        """
        Protected method to perform initialization tasks common to this
        base class and all derived classes.
        """
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        
        header = self.header()
        header.setSortIndicator(0, Qt.AscendingOrder)
        header.setSortIndicatorShown(True)
        if qVersion() >= "5.0.0":
            header.setSectionsClickable(True)
        else:
            header.setClickable(True)
        
        self.setSortingEnabled(True)
        
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        self.header().setStretchLastSection(True)
        self.headerSize0 = 0
        self.layoutDisplay()
        
    def layoutDisplay(self):
        """
        Public slot to perform a layout operation.
        """
        self._resizeColumns(QModelIndex())
        self._resort()
        
    def _resizeColumns(self, index):
        """
        Protected slot to resize the view when items get expanded or collapsed.
        
        @param index index of item (QModelIndex)
        """
        w = max(100, self.sizeHintForColumn(0))
        if w != self.headerSize0:
            self.header().resizeSection(0, w)
            self.headerSize0 = w
    
    def _resort(self):
        """
        Protected slot to resort the tree.
        """
        self.model().sort(self.header().sortIndicatorSection(),
                          self.header().sortIndicatorOrder())
        
    def __createPopupMenus(self):
        """
        Private method to generate the various popup menus.
        """
        # create the popup menu for source files
        self.sourceMenu = QMenu(self)
        self.sourceMenu.addAction(
            QCoreApplication.translate('Browser', 'Open'), self._openItem)
        self.unittestAct = self.sourceMenu.addAction(
            QCoreApplication.translate('Browser', 'Run unittest...'),
            self.handleUnittest)
        self.sourceMenu.addSeparator()
        self.mimeTypeAct = self.sourceMenu.addAction(
            self.tr('Show Mime-Type'), self.__showMimeType)
        self.sourceMenu.addSeparator()
        self.sourceMenu.addAction(
            QCoreApplication.translate('Browser', 'Copy Path to Clipboard'),
            self._copyToClipboard)
        
        # create the popup menu for general use
        self.menu = QMenu(self)
        self.menu.addAction(
            QCoreApplication.translate('Browser', 'Open'), self._openItem)
        self.editPixmapAct = self.menu.addAction(
            QCoreApplication.translate('Browser', 'Open in Icon Editor'),
            self._editPixmap)
        self.menu.addSeparator()
        self.mimeTypeAct = self.menu.addAction(
            self.tr('Show Mime-Type'), self.__showMimeType)
        self.menu.addSeparator()
        self.menu.addAction(
            QCoreApplication.translate('Browser', 'Copy Path to Clipboard'),
            self._copyToClipboard)
        if self.__embeddedBrowser in [1, 2]:
            self.menu.addSeparator()
            self.menu.addAction(
                QCoreApplication.translate('Browser', 'Configure...'),
                self.__configure)

        # create the menu for multiple selected files
        self.multiMenu = QMenu(self)
        self.multiMenu.addAction(
            QCoreApplication.translate('Browser', 'Open'), self._openItem)
        if self.__embeddedBrowser in [1, 2]:
            self.multiMenu.addSeparator()
            self.multiMenu.addAction(
                QCoreApplication.translate('Browser', 'Configure...'),
                self.__configure)
        
        # create the directory menu
        self.dirMenu = QMenu(self)
        self.dirMenu.addAction(
            QCoreApplication.translate('Browser', 'New toplevel directory...'),
            self.__newToplevelDir)
        self.addAsTopLevelAct = self.dirMenu.addAction(
            QCoreApplication.translate('Browser', 'Add as toplevel directory'),
            self.__addAsToplevelDir)
        self.removeFromToplevelAct = self.dirMenu.addAction(
            QCoreApplication.translate('Browser', 'Remove from toplevel'),
            self.__removeToplevel)
        self.dirMenu.addSeparator()
        self.dirMenu.addAction(
            QCoreApplication.translate('Browser', 'Refresh directory'),
            self.__refreshDirectory)
        self.dirMenu.addSeparator()
        self.dirMenu.addAction(
            QCoreApplication.translate('Browser', 'Find in this directory'),
            self.__findInDirectory)
        self.dirMenu.addAction(
            QCoreApplication.translate(
                'Browser', 'Find&&Replace in this directory'),
            self.__replaceInDirectory)
        self.dirMenu.addAction(
            QCoreApplication.translate('Browser', 'Copy Path to Clipboard'),
            self._copyToClipboard)
        if self.__embeddedBrowser in [1, 2]:
            self.dirMenu.addSeparator()
            self.dirMenu.addAction(
                QCoreApplication.translate('Browser', 'Configure...'),
                self.__configure)
        
        # create the attribute menu
        self.gotoMenu = QMenu(self.tr("Goto"), self)
        self.gotoMenu.aboutToShow.connect(self._showGotoMenu)
        self.gotoMenu.triggered.connect(self._gotoAttribute)
        
        self.attributeMenu = QMenu(self)
        self.attributeMenu.addAction(
            QCoreApplication.translate('Browser', 'New toplevel directory...'),
            self.__newToplevelDir)
        self.attributeMenu.addSeparator()
        self.attributeMenu.addMenu(self.gotoMenu)
        if self.__embeddedBrowser in [1, 2]:
            self.attributeMenu.addSeparator()
            self.attributeMenu.addAction(
                QCoreApplication.translate('Browser', 'Configure...'),
                self.__configure)
        
        # create the background menu
        self.backMenu = QMenu(self)
        self.backMenu.addAction(
            QCoreApplication.translate('Browser', 'New toplevel directory...'),
            self.__newToplevelDir)
        if self.__embeddedBrowser in [1, 2]:
            self.backMenu.addSeparator()
            self.backMenu.addAction(
                QCoreApplication.translate('Browser', 'Configure...'),
                self.__configure)

    def mouseDoubleClickEvent(self, mouseEvent):
        """
        Protected method of QAbstractItemView.
        
        Reimplemented to disable expanding/collapsing of items when
        double-clicking. Instead the double-clicked entry is opened.
        
        @param mouseEvent the mouse event (QMouseEvent)
        """
        index = self.indexAt(mouseEvent.pos())
        if index.isValid():
            itm = self.model().item(index)
            if isinstance(itm, (
                    BrowserDirectoryItem, BrowserImportsItem,
                    ProjectBrowserSimpleDirectoryItem, BrowserSysPathItem,
                    BrowserGlobalsItem)):
                self.setExpanded(index, not self.isExpanded(index))
            else:
                self._openItem()

    def _contextMenuRequested(self, coord):
        """
        Protected slot to show the context menu of the listview.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        categories = self.getSelectedItemsCountCategorized(
            [BrowserDirectoryItem, BrowserFileItem,
             BrowserClassItem, BrowserMethodItem])
        cnt = categories["sum"]
        bfcnt = categories[str(BrowserFileItem)]
        if cnt > 1 and cnt == bfcnt:
            self.multiMenu.popup(self.mapToGlobal(coord))
        else:
            index = self.indexAt(coord)
            
            if index.isValid():
                self.setCurrentIndex(index)
                flags = QItemSelectionModel.SelectionFlags(
                    QItemSelectionModel.ClearAndSelect |
                    QItemSelectionModel.Rows)
                self.selectionModel().select(index, flags)
                
                itm = self.model().item(index)
                coord = self.mapToGlobal(coord)
                if isinstance(itm, BrowserFileItem):
                    if itm.isPython3File():
                        if itm.fileName().endswith('.py'):
                            self.unittestAct.setEnabled(True)
                        else:
                            self.unittestAct.setEnabled(False)
                        self.sourceMenu.popup(coord)
                    else:
                        self.editPixmapAct.setVisible(itm.isPixmapFile())
                        self.menu.popup(coord)
                elif isinstance(itm, BrowserClassItem) or \
                    isinstance(itm, BrowserMethodItem) or \
                        isinstance(itm, BrowserImportItem):
                    self.editPixmapAct.setVisible(False)
                    self.menu.popup(coord)
                elif isinstance(itm, BrowserClassAttributeItem):
                    self.attributeMenu.popup(coord)
                elif isinstance(itm, BrowserDirectoryItem):
                    if not index.parent().isValid():
                        self.removeFromToplevelAct.setEnabled(True)
                        self.addAsTopLevelAct.setEnabled(False)
                    else:
                        self.removeFromToplevelAct.setEnabled(False)
                        self.addAsTopLevelAct.setEnabled(True)
                    self.dirMenu.popup(coord)
                else:
                    self.backMenu.popup(coord)
            else:
                self.backMenu.popup(self.mapToGlobal(coord))
        
    def _showGotoMenu(self):
        """
        Protected slot to prepare the goto submenu of the attribute menu.
        """
        self.gotoMenu.clear()
        
        itm = self.model().item(self.currentIndex())
        linenos = itm.linenos()
        fileName = itm.fileName()
        
        for lineno in sorted(linenos):
            act = self.gotoMenu.addAction(
                self.tr("Line {0}".format(lineno)))
            act.setData([fileName, lineno])
        
    def _gotoAttribute(self, act):
        """
        Protected slot to handle the selection of the goto menu.
        
        @param act reference to the action (E5Action)
        """
        fileName, lineno = act.data()
        self.sourceFile[str, int].emit(fileName, lineno)
        
    def handlePreferencesChanged(self):
        """
        Public slot used to handle the preferencesChanged signal.
        """
        self.model().preferencesChanged()
        self._resort()
        
    def _openItem(self):
        """
        Protected slot to handle the open popup menu entry.
        """
        itmList = self.getSelectedItems(
            [BrowserFileItem, BrowserClassItem,
             BrowserMethodItem, BrowserClassAttributeItem,
             BrowserImportItem])
        
        if not self._activating:
            self._activating = True
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
                    elif itm.isDesignerFile():
                        self.designerFile.emit(itm.fileName())
                    elif itm.isLinguistFile():
                        if itm.fileExt() == '.ts':
                            self.linguistFile.emit(itm.fileName())
                        else:
                            self.trpreview.emit([itm.fileName()])
                    elif itm.isProjectFile():
                        self.projectFile.emit(itm.fileName())
                    elif itm.isMultiProjectFile():
                        self.multiProjectFile.emit(itm.fileName())
                    elif itm.isIdlFile():
                        self.sourceFile[str].emit(itm.fileName())
                    elif itm.isResourcesFile():
                        self.sourceFile[str].emit(itm.fileName())
                    elif itm.isSvgFile():
                        self.svgFile.emit(itm.fileName())
                    elif itm.isPixmapFile():
                        self.pixmapFile.emit(itm.fileName())
                    else:
                        if Utilities.MimeTypes.isTextFile(itm.fileName()):
                            self.sourceFile[str].emit(itm.fileName())
                        else:
                            QDesktopServices.openUrl(QUrl(itm.fileName()))
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
            self._activating = False
        
    def __showMimeType(self):
        """
        Private slot to show the mime type of the selected entry.
        """
        itmList = self.getSelectedItems(
            [BrowserFileItem, BrowserClassItem,
             BrowserMethodItem, BrowserClassAttributeItem,
             BrowserImportItem])
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
        
    def _editPixmap(self):
        """
        Protected slot to handle the open in icon editor popup menu entry.
        """
        itmList = self.getSelectedItems([BrowserFileItem])
        
        for itm in itmList:
            if isinstance(itm, BrowserFileItem):
                if itm.isPixmapFile():
                    self.pixmapEditFile.emit(itm.fileName())
        
    def _copyToClipboard(self):
        """
        Protected method to copy the text shown for an entry to the clipboard.
        """
        itm = self.model().item(self.currentIndex())
        try:
            fn = itm.fileName()
        except AttributeError:
            try:
                fn = itm.dirName()
            except AttributeError:
                fn = ""
        
        if fn:
            cb = QApplication.clipboard()
            cb.setText(fn)
        
    def handleUnittest(self):
        """
        Public slot to handle the unittest popup menu entry.
        """
        try:
            index = self.currentIndex()
            itm = self.model().item(index)
            pyfn = itm.fileName()
        except AttributeError:
            pyfn = None

        if pyfn is not None:
            self.unittestOpen.emit(pyfn)
        
    def __newToplevelDir(self):
        """
        Private slot to handle the New toplevel directory popup menu entry.
        """
        dname = E5FileDialog.getExistingDirectory(
            None,
            QCoreApplication.translate('Browser', "New toplevel directory"),
            "",
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
        if dname:
            dname = os.path.abspath(Utilities.toNativeSeparators(dname))
            self.__model.addTopLevelDir(dname)
        
    def __removeToplevel(self):
        """
        Private slot to handle the Remove from toplevel popup menu entry.
        """
        index = self.currentIndex()
        sindex = self.model().mapToSource(index)
        self.__model.removeToplevelDir(sindex)
        
    def __addAsToplevelDir(self):
        """
        Private slot to handle the Add as toplevel directory popup menu entry.
        """
        index = self.currentIndex()
        dname = self.model().item(index).dirName()
        self.__model.addTopLevelDir(dname)
        
    def __refreshDirectory(self):
        """
        Private slot to refresh a directory entry.
        """
        index = self.currentIndex()
        refreshDir = self.model().item(index).dirName()
        self.__model.directoryChanged(refreshDir)
        
    def __findInDirectory(self):
        """
        Private slot to handle the Find in directory popup menu entry.
        """
        index = self.currentIndex()
        searchDir = self.model().item(index).dirName()
        
        e5App().getObject("UserInterface")\
            .showFindFilesDialog(searchDir=searchDir)
        
    def __replaceInDirectory(self):
        """
        Private slot to handle the Find&Replace in directory popup menu entry.
        """
        index = self.currentIndex()
        searchDir = self.model().item(index).dirName()
        
        e5App().getObject("UserInterface")\
            .showReplaceFilesDialog(searchDir=searchDir)
        
    def handleProgramChange(self, fn):
        """
        Public slot to handle the programChange signal.
        
        @param fn file name (string)
        """
        self.__model.programChange(os.path.dirname(fn))
        
    def handleInterpreterChanged(self, interpreter):
        """
        Public slot to handle a change of the debug client's interpreter.
        
        @param interpreter interpreter of the debug client (string)
        """
        self.__model.interpreterChanged(interpreter)
        
    def wantedItem(self, itm, filter=None):
        """
        Public method to check type of an item.
        
        @param itm the item to check (BrowserItem)
        @param filter list of classes to check against
        @return flag indicating item is a valid type (boolean)
        """
        if filter is None:
            filter = self.selectedItemsFilter
        for typ in filter:
            if isinstance(itm, typ):
                return True
        return False
        
    def getSelectedItems(self, filter=None):
        """
        Public method to get the selected items.
        
        @param filter list of classes to check against
        @return list of selected items (list of BroweserItem)
        """
        selectedItems = []
        indexes = self.selectedIndexes()
        for index in indexes:
            if index.column() == 0:
                itm = self.model().item(index)
                if self.wantedItem(itm, filter):
                    selectedItems.append(itm)
        return selectedItems
        
    def getSelectedItemsCount(self, filter=None):
        """
        Public method to get the count of items selected.
        
        @param filter list of classes to check against
        @return count of items selected (integer)
        """
        count = 0
        indexes = self.selectedIndexes()
        for index in indexes:
            if index.column() == 0:
                itm = self.model().item(index)
                if self.wantedItem(itm, filter):
                    count += 1
        return count
        
    def getSelectedItemsCountCategorized(self, filter=None):
        """
        Public method to get a categorized count of selected items.
        
        @param filter list of classes to check against
        @return a dictionary containing the counts of items belonging
            to the individual filter classes. The keys of the dictionary
            are the string representation of the classes given in the
            filter (i.e. str(filterClass)). The dictionary contains
            an additional entry with key "sum", that stores the sum of
            all selected entries fulfilling the filter criteria.
        """
        if filter is None:
            filter = self.selectedItemsFilter
        categories = {}
        categories["sum"] = 0
        for typ in filter:
            categories[str(typ)] = 0
        
        indexes = self.selectedIndexes()
        for index in indexes:
            if index.column() == 0:
                itm = self.model().item(index)
                for typ in filter:
                    if isinstance(itm, typ):
                        categories["sum"] += 1
                        categories[str(typ)] += 1
        
        return categories
        
    def saveToplevelDirs(self):
        """
        Public slot to save the toplevel directories.
        """
        self.__model.saveToplevelDirs()
    
    def __configure(self):
        """
        Private method to open the configuration dialog.
        """
        if self.__embeddedBrowser == 1:
            e5App().getObject("UserInterface")\
                .showPreferences("debuggerGeneralPage")
        elif self.__embeddedBrowser == 2:
            e5App().getObject("UserInterface")\
                .showPreferences("projectBrowserPage")
