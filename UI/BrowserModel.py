# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the browser model.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os
import sys
import fnmatch
import json

from PyQt5.QtCore import QDir, QModelIndex, QAbstractItemModel, \
    QFileSystemWatcher, Qt, QProcess, QCoreApplication
from PyQt5.QtGui import QImageReader, QFont
from PyQt5.QtWidgets import QApplication

import UI.PixmapCache
import Preferences
import Utilities

BrowserItemRoot = 0
BrowserItemDirectory = 1
BrowserItemSysPath = 2
BrowserItemFile = 3
BrowserItemClass = 4
BrowserItemMethod = 5
BrowserItemAttributes = 6
BrowserItemAttribute = 7
BrowserItemCoding = 8
BrowserItemImports = 9
BrowserItemImport = 10


class BrowserModel(QAbstractItemModel):
    """
    Class implementing the browser model.
    """
    def __init__(self, parent=None, nopopulate=False):
        """
        Constructor
        
        @param parent reference to parent object (QObject)
        @keyparam nopopulate flag indicating to not populate the model
            (boolean)
        """
        super(BrowserModel, self).__init__(parent)
        
        self.progDir = None
        self.watchedItems = {}
        self.watcher = QFileSystemWatcher(self)
        self.watcher.directoryChanged.connect(self.directoryChanged)
        
        self.__sysPathInterpreter = ""
        self.__sysPathItem = None
        
        if not nopopulate:
            rootData = QCoreApplication.translate("BrowserModel", "Name")
            self.rootItem = BrowserItem(None, rootData)
            
            self.__populateModel()
    
    def columnCount(self, parent=QModelIndex()):
        """
        Public method to get the number of columns.
        
        @param parent index of parent item (QModelIndex)
        @return number of columns (integer)
        """
        if parent.isValid():
            item = parent.internalPointer()
        else:
            item = self.rootItem
        
        return item.columnCount() + 1
    
    def data(self, index, role):
        """
        Public method to get data of an item.
        
        @param index index of the data to retrieve (QModelIndex)
        @param role role of data (Qt.ItemDataRole)
        @return requested data
        """
        if not index.isValid():
            return None
        
        if role == Qt.DisplayRole:
            item = index.internalPointer()
            if index.column() < item.columnCount():
                return item.data(index.column())
            elif index.column() == item.columnCount() and \
                    index.column() < self.columnCount(self.parent(index)):
                # This is for the case where an item under a multi-column
                # parent doesn't have a value for all the columns
                return ""
        elif role == Qt.DecorationRole:
            if index.column() == 0:
                return index.internalPointer().getIcon()
        elif role == Qt.FontRole:
            item = index.internalPointer()
            if item.isSymlink():
                font = QFont(QApplication.font("QTreeView"))
                font.setItalic(True)
                return font
        
        return None
    
    def flags(self, index):
        """
        Public method to get the item flags.
        
        @param index index of the data to retrieve (QModelIndex)
        @return requested flags (Qt.ItemFlags)
        """
        if not index.isValid():
            return Qt.ItemIsEnabled
        
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Public method to get the header data.
        
        @param section number of section to get data for (integer)
        @param orientation header orientation (Qt.Orientation)
        @param role role of data (Qt.ItemDataRole)
        @return requested header data
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section >= self.rootItem.columnCount():
                return ""
            else:
                return self.rootItem.data(section)
        
        return None
    
    def index(self, row, column, parent=QModelIndex()):
        """
        Public method to create an index.
        
        @param row row number of the new index (integer)
        @param column column number of the new index (integer)
        @param parent index of parent item (QModelIndex)
        @return index object (QModelIndex)
        """
        # The model/view framework considers negative values out-of-bounds,
        # however in python they work when indexing into lists. So make sure
        # we return an invalid index for out-of-bounds row/col
        if row < 0 or column < 0 or \
           row >= self.rowCount(parent) or column >= self.columnCount(parent):
            return QModelIndex()
        
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        
        try:
            if not parentItem.isPopulated():
                self.populateItem(parentItem)
            childItem = parentItem.child(row)
        except IndexError:
            childItem = None
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()
    
    def parent(self, index):
        """
        Public method to get the index of the parent object.
        
        @param index index of the item (QModelIndex)
        @return index of parent item (QModelIndex)
        """
        if not index.isValid():
            return QModelIndex()
        
        childItem = index.internalPointer()
        parentItem = childItem.parent()
        
        if parentItem == self.rootItem:
            return QModelIndex()
        
        return self.createIndex(parentItem.row(), 0, parentItem)
    
    def rowCount(self, parent=QModelIndex()):
        """
        Public method to get the number of rows.
        
        @param parent index of parent item (QModelIndex)
        @return number of rows (integer)
        """
        # Only the first column should have children
        if parent.column() > 0:
            return 0
        
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
            if not parentItem.isPopulated():    # lazy population
                self.populateItem(parentItem)
        
        return parentItem.childCount()

    def hasChildren(self, parent=QModelIndex()):
        """
        Public method to check for the presence of child items.
        
        We always return True for normal items in order to do lazy
        population of the tree.
        
        @param parent index of parent item (QModelIndex)
        @return flag indicating the presence of child items (boolean)
        """
        # Only the first column should have children
        if parent.column() > 0:
            return 0
        
        if not parent.isValid():
            return self.rootItem.childCount() > 0
        
        if parent.internalPointer().isLazyPopulated():
            return True
        else:
            return parent.internalPointer().childCount() > 0

    def clear(self):
        """
        Public method to clear the model.
        """
        self.beginResetModel()
        self.rootItem.removeChildren()
        self.endResetModel()
    
    def item(self, index):
        """
        Public method to get a reference to an item.
        
        @param index index of the data to retrieve (QModelIndex)
        @return requested item reference (BrowserItem)
        """
        if not index.isValid():
            return None
        
        return index.internalPointer()
    
    def _addWatchedItem(self, itm):
        """
        Protected method to watch an item.
        
        @param itm item to be watched (BrowserDirectoryItem)
        """
        if isinstance(itm, BrowserDirectoryItem):
            dirName = itm.dirName()
            if dirName != "" and \
               not dirName.startswith("//") and \
               not dirName.startswith("\\\\"):
                if dirName not in self.watcher.directories():
                    self.watcher.addPath(dirName)
                if dirName in self.watchedItems:
                    if itm not in self.watchedItems[dirName]:
                        self.watchedItems[dirName].append(itm)
                else:
                    self.watchedItems[dirName] = [itm]
    
    def _removeWatchedItem(self, itm):
        """
        Protected method to remove a watched item.
        
        @param itm item to be removed (BrowserDirectoryItem)
        """
        if isinstance(itm, BrowserDirectoryItem):
            dirName = itm.dirName()
            if dirName in self.watchedItems:
                if itm in self.watchedItems[dirName]:
                    self.watchedItems[dirName].remove(itm)
                if len(self.watchedItems[dirName]) == 0:
                    del self.watchedItems[dirName]
                    self.watcher.removePath(dirName)
    
    def directoryChanged(self, path):
        """
        Public slot to handle the directoryChanged signal of the watcher.
        
        @param path path of the directory (string)
        """
        if path not in self.watchedItems:
            # just ignore the situation we don't have a reference to the item
            return
        
        if Preferences.getUI("BrowsersListHiddenFiles"):
            filter = QDir.Filters(
                QDir.AllEntries | QDir.Hidden | QDir.NoDotAndDotDot)
        else:
            filter = QDir.Filters(QDir.AllEntries | QDir.NoDot | QDir.NoDotDot)
        
        for itm in self.watchedItems[path]:
            oldCnt = itm.childCount()
            
            qdir = QDir(itm.dirName())
            
            entryInfoList = qdir.entryInfoList(filter)
            
            # step 1: check for new entries
            children = itm.children()
            for f in entryInfoList:
                fpath = Utilities.toNativeSeparators(f.absoluteFilePath())
                childFound = False
                for child in children:
                    if child.name() == fpath:
                        childFound = True
                        children.remove(child)
                        break
                if childFound:
                    continue
                
                cnt = itm.childCount()
                self.beginInsertRows(
                    self.createIndex(itm.row(), 0, itm), cnt, cnt)
                if f.isDir():
                    node = BrowserDirectoryItem(
                        itm,
                        Utilities.toNativeSeparators(f.absoluteFilePath()),
                        False)
                else:
                    node = BrowserFileItem(
                        itm,
                        Utilities.toNativeSeparators(f.absoluteFilePath()))
                self._addItem(node, itm)
                self.endInsertRows()
            
            # step 2: check for removed entries
            if len(entryInfoList) != itm.childCount():
                for row in range(oldCnt - 1, -1, -1):
                    child = itm.child(row)
                    childname = Utilities.fromNativeSeparators(child.name())
                    entryFound = False
                    for f in entryInfoList:
                        if f.absoluteFilePath() == childname:
                            entryFound = True
                            entryInfoList.remove(f)
                            break
                    if entryFound:
                        continue
                    
                    self._removeWatchedItem(child)
                    self.beginRemoveRows(
                        self.createIndex(itm.row(), 0, itm), row, row)
                    itm.removeChild(child)
                    self.endRemoveRows()
    
    def __populateModel(self):
        """
        Private method to populate the browser model.
        """
        self.toplevelDirs = []
        tdp = Preferences.Prefs.settings.value('BrowserModel/ToplevelDirs')
        if tdp:
            self.toplevelDirs = tdp
        else:
            self.toplevelDirs.append(
                Utilities.toNativeSeparators(QDir.homePath()))
            for d in QDir.drives():
                self.toplevelDirs.append(Utilities.toNativeSeparators(
                    d.absoluteFilePath()))
        
        for d in self.toplevelDirs:
            itm = BrowserDirectoryItem(self.rootItem, d)
            self._addItem(itm, self.rootItem)
    
    def interpreterChanged(self, interpreter):
        """
        Public method to handle a change of the debug client's interpreter.
        
        @param interpreter interpreter of the debug client (string)
        """
        if interpreter and "python" in interpreter.lower():
            if interpreter.endswith("w.exe"):
                interpreter = interpreter.replace("w.exe", ".exe")
            if self.__sysPathInterpreter != interpreter:
                self.__sysPathInterpreter = interpreter
                # step 1: remove sys.path entry
                if self.__sysPathItem is not None:
                    self.beginRemoveRows(
                        QModelIndex(), self.__sysPathItem.row(),
                        self.__sysPathItem.row())
                    self.rootItem.removeChild(self.__sysPathItem)
                    self.endRemoveRows()
                    self.__sysPathItem = None
                
                if self.__sysPathInterpreter:
                    # step 2: add a new one
                    self.__sysPathItem = BrowserSysPathItem(self.rootItem)
                    self.addItem(self.__sysPathItem)
        else:
            # remove sys.path entry
            if self.__sysPathItem is not None:
                self.beginRemoveRows(
                    QModelIndex(), self.__sysPathItem.row(),
                    self.__sysPathItem.row())
                self.rootItem.removeChild(self.__sysPathItem)
                self.endRemoveRows()
                self.__sysPathItem = None
            self.__sysPathInterpreter = ""
    
    def programChange(self, dirname):
        """
        Public method to change the entry for the directory of file being
        debugged.
        
        @param dirname name of the directory containing the file (string)
        """
        if self.progDir:
            if dirname == self.progDir.dirName():
                return
            
            # remove old entry
            self._removeWatchedItem(self.progDir)
            self.beginRemoveRows(
                QModelIndex(), self.progDir.row(), self.progDir.row())
            self.rootItem.removeChild(self.progDir)
            self.endRemoveRows()
            self.progDir = None
        
        itm = BrowserDirectoryItem(self.rootItem, dirname)
        self.addItem(itm)
        self.progDir = itm
    
    def addTopLevelDir(self, dirname):
        """
        Public method to add a new toplevel directory.
        
        @param dirname name of the new toplevel directory (string)
        """
        if dirname not in self.toplevelDirs:
            itm = BrowserDirectoryItem(self.rootItem, dirname)
            self.addItem(itm)
            self.toplevelDirs.append(itm.dirName())
    
    def removeToplevelDir(self, index):
        """
        Public method to remove a toplevel directory.
        
        @param index index of the toplevel directory to be removed
            (QModelIndex)
        """
        if not index.isValid():
            return
        
        item = index.internalPointer()
        self.beginRemoveRows(index.parent(), index.row(), index.row())
        self.rootItem.removeChild(item)
        self.endRemoveRows()
        
        self.toplevelDirs.remove(item.dirName())
        self._removeWatchedItem(item)
    
    def saveToplevelDirs(self):
        """
        Public slot to save the toplevel directories.
        """
        Preferences.Prefs.settings.setValue(
            'BrowserModel/ToplevelDirs', self.toplevelDirs)
    
    def _addItem(self, itm, parentItem):
        """
        Protected slot to add an item.
        
        @param itm reference to item to add (BrowserItem)
        @param parentItem reference to item to add to (BrowserItem)
        """
        parentItem.appendChild(itm)
    
    def addItem(self, itm, parent=QModelIndex()):
        """
        Public slot to add an item.
        
        @param itm item to add (BrowserItem)
        @param parent index of parent item (QModelIndex)
        """
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        
        cnt = parentItem.childCount()
        self.beginInsertRows(parent, cnt, cnt)
        self._addItem(itm, parentItem)
        self.endInsertRows()

    def populateItem(self, parentItem, repopulate=False):
        """
        Public method to populate an item's subtree.
        
        @param parentItem reference to the item to be populated
        @param repopulate flag indicating a repopulation (boolean)
        """
        if parentItem.type() == BrowserItemDirectory:
            self.populateDirectoryItem(parentItem, repopulate)
        elif parentItem.type() == BrowserItemSysPath:
            self.populateSysPathItem(parentItem, repopulate)
        elif parentItem.type() == BrowserItemFile:
            self.populateFileItem(parentItem, repopulate)
        elif parentItem.type() == BrowserItemClass:
            self.populateClassItem(parentItem, repopulate)
        elif parentItem.type() == BrowserItemMethod:
            self.populateMethodItem(parentItem, repopulate)
        elif parentItem.type() == BrowserItemAttributes:
            self.populateClassAttributesItem(parentItem, repopulate)

    def populateDirectoryItem(self, parentItem, repopulate=False):
        """
        Public method to populate a directory item's subtree.
        
        @param parentItem reference to the directory item to be populated
        @param repopulate flag indicating a repopulation (boolean)
        """
        self._addWatchedItem(parentItem)
        
        qdir = QDir(parentItem.dirName())
        
        if Preferences.getUI("BrowsersListHiddenFiles"):
            filter = QDir.Filters(
                QDir.AllEntries | QDir.Hidden | QDir.NoDotAndDotDot)
        else:
            filter = QDir.Filters(QDir.AllEntries | QDir.NoDot | QDir.NoDotDot)
        entryInfoList = qdir.entryInfoList(filter)
        if len(entryInfoList) > 0:
            if repopulate:
                self.beginInsertRows(
                    self.createIndex(parentItem.row(), 0, parentItem),
                    0, len(entryInfoList) - 1)
            for f in entryInfoList:
                if f.isDir():
                    node = BrowserDirectoryItem(
                        parentItem,
                        Utilities.toNativeSeparators(f.absoluteFilePath()),
                        False)
                else:
                    fileFilters = \
                        Preferences.getUI("BrowsersFileFilters").split(";")
                    if fileFilters:
                        fn = f.fileName()
                        if any([fnmatch.fnmatch(fn, ff.strip())
                                for ff in fileFilters]):
                            continue
                    node = BrowserFileItem(
                        parentItem,
                        Utilities.toNativeSeparators(f.absoluteFilePath()))
                self._addItem(node, parentItem)
            if repopulate:
                self.endInsertRows()

    def populateSysPathItem(self, parentItem, repopulate=False):
        """
        Public method to populate a sys.path item's subtree.
        
        @param parentItem reference to the sys.path item to be populated
        @param repopulate flag indicating a repopulation (boolean)
        """
        if self.__sysPathInterpreter:
            script = "import sys, json; print(json.dumps(sys.path))"
            proc = QProcess()
            proc.start(self.__sysPathInterpreter, ["-c", script])
            finished = proc.waitForFinished(3000)
            if finished:
                procOutput = str(proc.readAllStandardOutput(),
                                 Preferences.getSystem("IOEncoding"),
                                 'replace')
                syspath = [p for p in json.loads(procOutput) if p]
                if len(syspath) > 0:
                    if repopulate:
                        self.beginInsertRows(
                            self.createIndex(parentItem.row(), 0, parentItem),
                            0, len(syspath) - 1)
                    for p in syspath:
                        if os.path.isdir(p):
                            node = BrowserDirectoryItem(parentItem, p)
                        else:
                            node = BrowserFileItem(parentItem, p)
                        self._addItem(node, parentItem)
                    if repopulate:
                        self.endInsertRows()
            else:
                proc.kill()

    def populateFileItem(self, parentItem, repopulate=False):
        """
        Public method to populate a file item's subtree.
        
        @param parentItem reference to the file item to be populated
        @param repopulate flag indicating a repopulation (boolean)
        """
        import Utilities.ClassBrowsers
        moduleName = parentItem.moduleName()
        fileName = parentItem.fileName()
        try:
            dict = Utilities.ClassBrowsers.readmodule(
                moduleName, [parentItem.dirName()],
                parentItem.isPython2File() or parentItem.isPython3File())
        except ImportError:
            return
        
        keys = list(dict.keys())
        if len(keys) > 0:
            if repopulate:
                self.beginInsertRows(
                    self.createIndex(parentItem.row(), 0, parentItem),
                    0, len(keys) - 1)
            for key in keys:
                if key.startswith("@@"):
                    # special treatment done later
                    continue
                cl = dict[key]
                try:
                    if cl.module == moduleName:
                        node = BrowserClassItem(parentItem, cl, fileName)
                        self._addItem(node, parentItem)
                except AttributeError:
                    pass
            if "@@Coding@@" in keys:
                node = BrowserCodingItem(
                    parentItem,
                    QCoreApplication.translate("BrowserModel", "Coding: {0}")
                    .format(dict["@@Coding@@"].coding))
                self._addItem(node, parentItem)
            if "@@Globals@@" in keys:
                node = BrowserGlobalsItem(
                    parentItem,
                    dict["@@Globals@@"].globals,
                    QCoreApplication.translate("BrowserModel", "Globals"))
                self._addItem(node, parentItem)
            if "@@Import@@" in keys or "@@ImportFrom@@" in keys:
                node = BrowserImportsItem(
                    parentItem,
                    QCoreApplication.translate("BrowserModel", "Imports"))
                self._addItem(node, parentItem)
                if "@@Import@@" in keys:
                    for importedModule in \
                            dict["@@Import@@"].getImports().values():
                        m_node = BrowserImportItem(
                            node,
                            importedModule.importedModuleName,
                            importedModule.file,
                            importedModule.linenos)
                        self._addItem(m_node, node)
                        for importedName, linenos in \
                                importedModule.importedNames.items():
                            mn_node = BrowserImportItem(
                                m_node,
                                importedName,
                                importedModule.file,
                                linenos,
                                isModule=False)
                            self._addItem(mn_node, m_node)
            if repopulate:
                self.endInsertRows()
        parentItem._populated = True

    def populateClassItem(self, parentItem, repopulate=False):
        """
        Public method to populate a class item's subtree.
        
        @param parentItem reference to the class item to be populated
        @param repopulate flag indicating a repopulation (boolean)
        """
        cl = parentItem.classObject()
        file_ = parentItem.fileName()
        
        if cl is None:
            return
        
        # build sorted list of names
        keys = []
        for name in list(cl.classes.keys()):
            keys.append((name, 'c'))
        for name in list(cl.methods.keys()):
            keys.append((name, 'm'))
        
        if len(keys) > 0:
            if repopulate:
                self.beginInsertRows(
                    self.createIndex(parentItem.row(), 0, parentItem),
                    0, len(keys) - 1)
            for key, kind in keys:
                if kind == 'c':
                    node = BrowserClassItem(parentItem, cl.classes[key], file_)
                elif kind == 'm':
                    node = BrowserMethodItem(parentItem, cl.methods[key],
                                             file_)
                self._addItem(node, parentItem)
            if repopulate:
                self.endInsertRows()
        
        if len(cl.attributes):
            node = BrowserClassAttributesItem(
                parentItem, cl.attributes,
                QCoreApplication.translate("BrowserModel", "Attributes"))
            if repopulate:
                self.addItem(
                    node, self.createIndex(parentItem.row(), 0, parentItem))
            else:
                self._addItem(node, parentItem)
        
        if len(cl.globals):
            node = BrowserClassAttributesItem(
                parentItem, cl.globals,
                QCoreApplication.translate("BrowserModel", "Class Attributes"),
                True)
            if repopulate:
                self.addItem(
                    node, self.createIndex(parentItem.row(), 0, parentItem))
            else:
                self._addItem(node, parentItem)

    def populateMethodItem(self, parentItem, repopulate=False):
        """
        Public method to populate a method item's subtree.
        
        @param parentItem reference to the method item to be populated
        @param repopulate flag indicating a repopulation (boolean)
        """
        fn = parentItem.functionObject()
        file_ = parentItem.fileName()
        
        if fn is None:
            return
        
        # build sorted list of names
        keys = []
        for name in list(fn.classes.keys()):
            keys.append((name, 'c'))
        for name in list(fn.methods.keys()):
            keys.append((name, 'm'))
        
        if len(keys) > 0:
            if repopulate:
                self.beginInsertRows(
                    self.createIndex(parentItem.row(), 0, parentItem),
                    0, len(keys) - 1)
            for key, kind in keys:
                if kind == 'c':
                    node = BrowserClassItem(parentItem, fn.classes[key], file_)
                elif kind == 'm':
                    node = BrowserMethodItem(parentItem, fn.methods[key],
                                             file_)
                self._addItem(node, parentItem)
            if repopulate:
                self.endInsertRows()

    def populateClassAttributesItem(self, parentItem, repopulate=False):
        """
        Public method to populate a class attributes item's subtree.
        
        @param parentItem reference to the class attributes item to be
            populated
        @param repopulate flag indicating a repopulation (boolean)
        """
        classAttributes = parentItem.isClassAttributes()
        attributes = parentItem.attributes()
        if not attributes:
            return
        
        keys = list(attributes.keys())
        if len(keys) > 0:
            if repopulate:
                self.beginInsertRows(
                    self.createIndex(parentItem.row(), 0, parentItem),
                    0, len(keys) - 1)
            for key in keys:
                node = BrowserClassAttributeItem(parentItem, attributes[key],
                                                 classAttributes)
                self._addItem(node, parentItem)
            if repopulate:
                self.endInsertRows()


class BrowserItem(object):
    """
    Class implementing the data structure for browser items.
    """
    def __init__(self, parent, data):
        """
        Constructor
        
        @param parent reference to the parent item
        @param data single data of the item
        """
        self.childItems = []
        
        self.parentItem = parent
        self.itemData = [data]
        self.type_ = BrowserItemRoot
        self.icon = UI.PixmapCache.getIcon("empty.png")
        self._populated = True
        self._lazyPopulation = False
        self.symlink = False
    
    def appendChild(self, child):
        """
        Public method to add a child to this item.
        
        @param child reference to the child item to add (BrowserItem)
        """
        self.childItems.append(child)
        self._populated = True
    
    def removeChild(self, child):
        """
        Public method to remove a child.
        
        @param child reference to the child to remove (BrowserItem)
        """
        self.childItems.remove(child)
    
    def removeChildren(self):
        """
        Public method to remove all children.
        """
        self.childItems = []
    
    def child(self, row):
        """
        Public method to get a child id.
        
        @param row number of child to get the id of (integer)
        @return reference to the child item (BrowserItem)
        """
        return self.childItems[row]
    
    def children(self):
        """
        Public method to get the ids of all child items.
        
        @return references to all child items (list of BrowserItem)
        """
        return self.childItems[:]
    
    def childCount(self):
        """
        Public method to get the number of available child items.
        
        @return number of child items (integer)
        """
        return len(self.childItems)
    
    def columnCount(self):
        """
        Public method to get the number of available data items.
        
        @return number of data items (integer)
        """
        return len(self.itemData)
    
    def data(self, column):
        """
        Public method to get a specific data item.
        
        @param column number of the requested data item (integer)
        @return stored data item
        """
        try:
            return self.itemData[column]
        except IndexError:
            return ""
    
    def parent(self):
        """
        Public method to get the reference to the parent item.
        
        @return reference to the parent item
        """
        return self.parentItem
    
    def row(self):
        """
        Public method to get the row number of this item.
        
        @return row number (integer)
        """
        return self.parentItem.childItems.index(self)
    
    def type(self):
        """
        Public method to get the item type.
        
        @return type of the item
        """
        return self.type_
    
    def isPublic(self):
        """
        Public method returning the public visibility status.
        
        @return flag indicating public visibility (boolean)
        """
        return True
    
    def getIcon(self):
        """
        Public method to get the items icon.
        
        @return the icon (QIcon)
        """
        return self.icon
    
    def isPopulated(self):
        """
        Public method to chek, if this item is populated.
        
        @return population status (boolean)
        """
        return self._populated
    
    def isLazyPopulated(self):
        """
        Public method to check, if this item should be populated lazyly.
        
        @return lazy population flag (boolean)
        """
        return self._lazyPopulation
    
    def lessThan(self, other, column, order):
        """
        Public method to check, if the item is less than the other one.
        
        @param other reference to item to compare against (BrowserItem)
        @param column column number to use for the comparison (integer)
        @param order sort order (Qt.SortOrder) (for special sorting)
        @return true, if this item is less than other (boolean)
        """
        try:
            return self.itemData[column] < other.itemData[column]
        except IndexError:
            return False
    
    def isSymlink(self):
        """
        Public method to check, if the items is a symbolic link.
        
        @return flag indicating a symbolic link (boolean)
        """
        return self.symlink


class BrowserDirectoryItem(BrowserItem):
    """
    Class implementing the data structure for browser directory items.
    """
    def __init__(self, parent, dinfo, full=True):
        """
        Constructor
        
        @param parent parent item
        @param dinfo dinfo is the string for the directory (string)
        @param full flag indicating full pathname should be displayed (boolean)
        """
        self._dirName = os.path.abspath(dinfo)
        
        if full:
            dn = self._dirName
        else:
            dn = os.path.basename(self._dirName)
        
        BrowserItem.__init__(self, parent, dn)
        
        self.type_ = BrowserItemDirectory
        if os.path.lexists(self._dirName) and os.path.islink(self._dirName):
            self.symlink = True
            self.icon = UI.PixmapCache.getSymlinkIcon("dirClosed.png")
        else:
            self.icon = UI.PixmapCache.getIcon("dirClosed.png")
        self._populated = False
        self._lazyPopulation = True

    def setName(self, dinfo, full=True):
        """
        Public method to set the directory name.
        
        @param dinfo dinfo is the string for the directory (string)
        @param full flag indicating full pathname should be displayed (boolean)
        """
        self._dirName = os.path.abspath(dinfo)
        
        if full:
            dn = self._dirName
        else:
            dn = os.path.basename(self._dirName)
        self.itemData[0] = dn
    
    def dirName(self):
        """
        Public method returning the directory name.
        
        @return directory name (string)
        """
        return self._dirName
    
    def name(self):
        """
        Public method to return the name of the item.
        
        @return name of the item (string)
        """
        return self._dirName
    
    def lessThan(self, other, column, order):
        """
        Public method to check, if the item is less than the other one.
        
        @param other reference to item to compare against (BrowserItem)
        @param column column number to use for the comparison (integer)
        @param order sort order (Qt.SortOrder) (for special sorting)
        @return true, if this item is less than other (boolean)
        """
        if issubclass(other.__class__, BrowserFileItem):
            if Preferences.getUI("BrowsersListFoldersFirst"):
                return order == Qt.AscendingOrder
        
        return BrowserItem.lessThan(self, other, column, order)


class BrowserSysPathItem(BrowserItem):
    """
    Class implementing the data structure for browser sys.path items.
    """
    def __init__(self, parent):
        """
        Constructor
        
        @param parent parent item
        """
        BrowserItem.__init__(self, parent, "sys.path")
        
        self.type_ = BrowserItemSysPath
        self.icon = UI.PixmapCache.getIcon("filePython.png")
        self._populated = False
        self._lazyPopulation = True
    
    def name(self):
        """
        Public method to return the name of the item.
        
        @return name of the item (string)
        """
        return "sys.path"


class BrowserFileItem(BrowserItem):
    """
    Class implementing the data structure for browser file items.
    """
    def __init__(self, parent, finfo, full=True, sourceLanguage=""):
        """
        Constructor
        
        @param parent parent item
        @param finfo the string for the file (string)
        @param full flag indicating full pathname should be displayed (boolean)
        @param sourceLanguage source code language of the project (string)
        """
        BrowserItem.__init__(self, parent, os.path.basename(finfo))
        
        self.type_ = BrowserItemFile
        self.fileext = os.path.splitext(finfo)[1].lower()
        self._filename = os.path.abspath(finfo)
        self._dirName = os.path.dirname(finfo)
        self.sourceLanguage = sourceLanguage
        
        self._moduleName = ''
        
        pixName = ""
        if self.isPython2File():
            if self.fileext == '.py':
                pixName = "filePython.png"
            else:
                pixName = "filePython2.png"
            self._populated = False
            self._lazyPopulation = True
            self._moduleName = os.path.basename(finfo)
        elif self.isPython3File():
            pixName = "filePython.png"
            self._populated = False
            self._lazyPopulation = True
            self._moduleName = os.path.basename(finfo)
        elif self.isRubyFile():
            pixName = "fileRuby.png"
            self._populated = False
            self._lazyPopulation = True
            self._moduleName = os.path.basename(finfo)
        elif self.isDesignerFile():
            pixName = "fileDesigner.png"
        elif self.isLinguistFile():
            if self.fileext == '.ts':
                pixName = "fileLinguist.png"
            else:
                pixName = "fileLinguist2.png"
        elif self.isResourcesFile():
            pixName = "fileResource.png"
        elif self.isProjectFile():
            pixName = "fileProject.png"
        elif self.isMultiProjectFile():
            pixName = "fileMultiProject.png"
        elif self.isIdlFile():
            pixName = "fileIDL.png"
            self._populated = False
            self._lazyPopulation = True
            self._moduleName = os.path.basename(finfo)
        elif self.isSvgFile():
            pixName = "fileSvg.png"
        elif self.isPixmapFile():
            pixName = "filePixmap.png"
        elif self.isDFile():
            pixName = "fileD.png"
        elif self.isJavaScriptFile():
            pixName = "fileJavascript.png"
            self._populated = False
            self._lazyPopulation = sys.version_info[0] == 3
            self._moduleName = os.path.basename(finfo)
        else:
            pixName = "fileMisc.png"
        
        if os.path.lexists(self._filename) and os.path.islink(self._filename):
            self.symlink = True
            self.icon = UI.PixmapCache.getSymlinkIcon(pixName)
        else:
            self.icon = UI.PixmapCache.getIcon(pixName)
    
    def setName(self, finfo, full=True):
        """
        Public method to set the directory name.
        
        @param finfo the string for the file (string)
        @param full flag indicating full pathname should be displayed (boolean)
        """
        self._filename = os.path.abspath(finfo)
        self.itemData[0] = os.path.basename(finfo)
        if self.isPython2File() or self.isPython3File() or \
           self.isRubyFile() or self.isIdlFile():
            self._dirName = os.path.dirname(finfo)
            self._moduleName = os.path.basename(finfo)
    
    def fileName(self):
        """
        Public method returning the filename.
        
        @return filename (string)
        """
        return self._filename
    
    def name(self):
        """
        Public method to return the name of the item.
        
        @return name of the item (string)
        """
        return self._filename
    
    def fileExt(self):
        """
        Public method returning the file extension.
        
        @return file extension (string)
        """
        return self.fileext
    
    def dirName(self):
        """
        Public method returning the directory name.
        
        @return directory name (string)
        """
        return self._dirName
    
    def moduleName(self):
        """
        Public method returning the module name.
        
        @return module name (string)
        """
        return self._moduleName
    
    def isPython2File(self):
        """
        Public method to check, if this file is a Python script.
        
        @return flag indicating a Python file (boolean)
        """
        return self.fileext in Preferences.getPython("PythonExtensions") or \
            (self.fileext == "" and
             self.sourceLanguage in ["Python", "Python2"])
    
    def isPython3File(self):
        """
        Public method to check, if this file is a Python3 script.
        
        @return flag indicating a Python file (boolean)
        """
        return self.fileext in Preferences.getPython("Python3Extensions") or \
            (self.fileext == "" and self.sourceLanguage == "Python3")
    
    def isRubyFile(self):
        """
        Public method to check, if this file is a Ruby script.
        
        @return flag indicating a Ruby file (boolean)
        """
        return self.fileext == '.rb' or \
            (self.fileext == "" and self.sourceLanguage == "Ruby")
    
    def isDesignerFile(self):
        """
        Public method to check, if this file is a Qt-Designer file.
        
        @return flag indicating a Qt-Designer file (boolean)
        """
        return self.fileext == '.ui'
    
    def isLinguistFile(self):
        """
        Public method to check, if this file is a Qt-Linguist file.
        
        @return flag indicating a Qt-Linguist file (boolean)
        """
        return self.fileext in ['.ts', '.qm']
    
    def isResourcesFile(self):
        """
        Public method to check, if this file is a Qt-Resources file.
        
        @return flag indicating a Qt-Resources file (boolean)
        """
        return self.fileext == '.qrc'
    
    def isProjectFile(self):
        """
        Public method to check, if this file is an eric project file.
        
        @return flag indicating an eric project file (boolean)
        """
        return self.fileext in ['.e4p']
    
    def isMultiProjectFile(self):
        """
        Public method to check, if this file is an eric multi project file.
        
        @return flag indicating an eric project file (boolean)
        """
        return self.fileext in ['.e4m', '.e5m']
    
    def isIdlFile(self):
        """
        Public method to check, if this file is a CORBA IDL file.
        
        @return flag indicating a CORBA IDL file (boolean)
        """
        return self.fileext == '.idl'
    
    def isJavaScriptFile(self):
        """
        Public method to check, if this file is a JavaScript file.
        
        @return flag indicating a JavaScript file (boolean)
        """
        return self.fileext == '.js'
    
    def isPixmapFile(self):
        """
        Public method to check, if this file is a pixmap file.
        
        @return flag indicating a pixmap file (boolean)
        """
        return self.fileext[1:] in QImageReader.supportedImageFormats()
    
    def isSvgFile(self):
        """
        Public method to check, if this file is a SVG file.
        
        @return flag indicating a SVG file (boolean)
        """
        return self.fileext == '.svg'
    
    def isDFile(self):
        """
        Public method to check, if this file is a D file.
        
        @return flag indicating a D file (boolean)
        """
        return self.fileext in ['.d', '.di'] or \
            (self.fileext == "" and self.sourceLanguage == "D")
    
    def lessThan(self, other, column, order):
        """
        Public method to check, if the item is less than the other one.
        
        @param other reference to item to compare against (BrowserItem)
        @param column column number to use for the comparison (integer)
        @param order sort order (Qt.SortOrder) (for special sorting)
        @return true, if this item is less than other (boolean)
        """
        if not issubclass(other.__class__, BrowserFileItem):
            if Preferences.getUI("BrowsersListFoldersFirst"):
                return order == Qt.DescendingOrder
        
        if issubclass(other.__class__, BrowserFileItem):
            sinit = os.path.basename(self._filename).startswith('__init__.py')
            oinit = \
                os.path.basename(other.fileName()).startswith('__init__.py')
            if sinit and not oinit:
                return order == Qt.AscendingOrder
            if not sinit and oinit:
                return order == Qt.DescendingOrder
        
        return BrowserItem.lessThan(self, other, column, order)


class BrowserClassItem(BrowserItem):
    """
    Class implementing the data structure for browser class items.
    """
    def __init__(self, parent, cl, filename):
        """
        Constructor
        
        @param parent parent item
        @param cl Class object to be shown
        @param filename filename of the file defining this class
        """
        name = cl.name
        if hasattr(cl, 'super') and cl.super:
            supers = []
            for sup in cl.super:
                try:
                    sname = sup.name
                    if sup.module != cl.module:
                        sname = "{0}.{1}".format(sup.module, sname)
                except AttributeError:
                    sname = sup
                supers.append(sname)
            name = name + "({0})".format(", ".join(supers))
        
        BrowserItem.__init__(self, parent, name)
        
        self.type_ = BrowserItemClass
        self._name = name
        self._classObject = cl
        self._filename = filename
        
        import Utilities.ClassBrowsers.ClbrBaseClasses
        self.isfunction = isinstance(
            self._classObject,
            Utilities.ClassBrowsers.ClbrBaseClasses.Function)
        self.ismodule = isinstance(
            self._classObject,
            Utilities.ClassBrowsers.ClbrBaseClasses.Module)
        if self.isfunction:
            if cl.isPrivate():
                self.icon = UI.PixmapCache.getIcon("method_private.png")
            elif cl.isProtected():
                self.icon = UI.PixmapCache.getIcon("method_protected.png")
            else:
                self.icon = UI.PixmapCache.getIcon("method.png")
            self.itemData[0] = "{0}({1})".format(
                name, ", ".join(self._classObject.parameters))
            if self._classObject.annotation:
                self.itemData[0] = "{0} {1}".format(
                    self.itemData[0], self._classObject.annotation)
            # if no defaults are wanted
            # ....format(name,
            #            ", ".join([e.split('=')[0].strip() \
            #                       for e in self._classObject.parameters]))
        elif self.ismodule:
            self.icon = UI.PixmapCache.getIcon("module.png")
        else:
            if cl.isPrivate():
                self.icon = UI.PixmapCache.getIcon("class_private.png")
            elif cl.isProtected():
                self.icon = UI.PixmapCache.getIcon("class_protected.png")
            else:
                self.icon = UI.PixmapCache.getIcon("class.png")
        if self._classObject and \
           (self._classObject.methods or
            self._classObject.classes or
                self._classObject.attributes):
            self._populated = False
            self._lazyPopulation = True
    
    def name(self):
        """
        Public method to return the name of the item.
        
        @return name of the item (string)
        """
        return '{0}@@{1}'.format(self._filename, self.lineno())
    
    def fileName(self):
        """
        Public method returning the filename.
        
        @return filename (string)
        """
        return self._filename
    
    def classObject(self):
        """
        Public method returning the class object.
        
        @return reference to the class object
        """
        return self._classObject
    
    def lineno(self):
        """
        Public method returning the line number defining this object.
        
        @return line number defining the object (integer)
        """
        return self._classObject.lineno
    
    def boundaries(self):
        """
        Public method returning the boundaries of the method definition.
        
        @return tuple with start end end line number (integer, integer)
        """
        return (self._classObject.lineno, self._classObject.endlineno)
    
    def lessThan(self, other, column, order):
        """
        Public method to check, if the item is less than the other one.
        
        @param other reference to item to compare against (BrowserItem)
        @param column column number to use for the comparison (integer)
        @param order sort order (Qt.SortOrder) (for special sorting)
        @return true, if this item is less than other (boolean)
        """
        if issubclass(other.__class__, BrowserCodingItem) or \
           issubclass(other.__class__, BrowserClassAttributesItem):
            return order == Qt.DescendingOrder
        
        if Preferences.getUI("BrowsersListContentsByOccurrence") and \
                column == 0:
            if order == Qt.AscendingOrder:
                return self.lineno() < other.lineno()
            else:
                return self.lineno() > other.lineno()
        
        return BrowserItem.lessThan(self, other, column, order)
    
    def isPublic(self):
        """
        Public method returning the public visibility status.
        
        @return flag indicating public visibility (boolean)
        """
        return self._classObject.isPublic()


class BrowserMethodItem(BrowserItem):
    """
    Class implementing the data structure for browser method items.
    """
    def __init__(self, parent, fn, filename):
        """
        Constructor
        
        @param parent parent item
        @param fn Function object to be shown
        @param filename filename of the file defining this class (string)
        """
        name = fn.name
        BrowserItem.__init__(self, parent, name)
        
        import Utilities.ClassBrowsers.ClbrBaseClasses
        self.type_ = BrowserItemMethod
        self._name = name
        self._functionObject = fn
        self._filename = filename
        if self._functionObject.modifier == \
           Utilities.ClassBrowsers.ClbrBaseClasses.Function.Static:
            self.icon = UI.PixmapCache.getIcon("method_static.png")
        elif self._functionObject.modifier == \
                Utilities.ClassBrowsers.ClbrBaseClasses.Function.Class:
            self.icon = UI.PixmapCache.getIcon("method_class.png")
        elif self._functionObject.isPrivate():
            self.icon = UI.PixmapCache.getIcon("method_private.png")
        elif self._functionObject.isProtected():
            self.icon = UI.PixmapCache.getIcon("method_protected.png")
        else:
            self.icon = UI.PixmapCache.getIcon("method.png")
        self.itemData[0] = "{0}({1})".format(
            name, ", ".join(self._functionObject.parameters))
        if self._functionObject.annotation:
            self.itemData[0] = "{0} {1}".format(
                self.itemData[0], self._functionObject.annotation)
        # if no defaults are wanted
        # ....format(name,
        #            ", ".join([e.split('=')[0].strip()
        #                       for e in self._functionObject.parameters]))
        if self._functionObject and \
           (self._functionObject.methods or self._functionObject.classes):
            self._populated = False
            self._lazyPopulation = True
    
    def name(self):
        """
        Public method to return the name of the item.
        
        @return name of the item (string)
        """
        return '{0}@@{1}'.format(self._filename, self.lineno())
    
    def fileName(self):
        """
        Public method returning the filename.
        
        @return filename (string)
        """
        return self._filename
    
    def functionObject(self):
        """
        Public method returning the function object.
        
        @return reference to the function object
        """
        return self._functionObject
    
    def lineno(self):
        """
        Public method returning the line number defining this object.
        
        @return line number defining the object (integer)
        """
        return self._functionObject.lineno
    
    def boundaries(self):
        """
        Public method returning the boundaries of the method definition.
        
        @return tuple with start end end line number (integer, integer)
        """
        return (self._functionObject.lineno, self._functionObject.endlineno)
    
    def lessThan(self, other, column, order):
        """
        Public method to check, if the item is less than the other one.
        
        @param other reference to item to compare against (BrowserItem)
        @param column column number to use for the comparison (integer)
        @param order sort order (Qt.SortOrder) (for special sorting)
        @return true, if this item is less than other (boolean)
        """
        if issubclass(other.__class__, BrowserMethodItem):
            if self._name.startswith('__init__'):
                return order == Qt.AscendingOrder
            if other._name.startswith('__init__'):
                return order == Qt.DescendingOrder
        elif issubclass(other.__class__, BrowserClassAttributesItem):
            return order == Qt.DescendingOrder
        
        if Preferences.getUI("BrowsersListContentsByOccurrence") and \
                column == 0:
            if order == Qt.AscendingOrder:
                return self.lineno() < other.lineno()
            else:
                return self.lineno() > other.lineno()
        
        return BrowserItem.lessThan(self, other, column, order)
    
    def isPublic(self):
        """
        Public method returning the public visibility status.
        
        @return flag indicating public visibility (boolean)
        """
        return self._functionObject.isPublic()


class BrowserClassAttributesItem(BrowserItem):
    """
    Class implementing the data structure for browser class attributes items.
    """
    def __init__(self, parent, attributes, text, isClass=False):
        """
        Constructor
        
        @param parent parent item
        @param attributes list of attributes
        @param text text to be shown by this item (string)
        @param isClass flag indicating class attributes (boolean)
        """
        BrowserItem.__init__(self, parent, text)
        
        self.type_ = BrowserItemAttributes
        self._attributes = attributes.copy()
        self._populated = False
        self._lazyPopulation = True
        if isClass:
            self.icon = UI.PixmapCache.getIcon("attributes_class.png")
        else:
            self.icon = UI.PixmapCache.getIcon("attributes.png")
        self.__isClass = isClass
    
    def name(self):
        """
        Public method to return the name of the item.
        
        @return name of the item (string)
        """
        return '{0}@@{1}'.format(self.parentItem.name(), self.data(0))
    
    def attributes(self):
        """
        Public method returning the attribute list.
        
        @return reference to the list of attributes
        """
        return self._attributes
    
    def isClassAttributes(self):
        """
        Public method returning the attributes type.
        
        @return flag indicating class attributes (boolean)
        """
        return self.__isClass
    
    def lessThan(self, other, column, order):
        """
        Public method to check, if the item is less than the other one.
        
        @param other reference to item to compare against (BrowserItem)
        @param column column number to use for the comparison (integer)
        @param order sort order (Qt.SortOrder) (for special sorting)
        @return true, if this item is less than other (boolean)
        """
        if issubclass(other.__class__, BrowserCodingItem):
            return order == Qt.DescendingOrder
        elif issubclass(other.__class__, BrowserClassItem) or \
                issubclass(other.__class__, BrowserMethodItem):
            return order == Qt.AscendingOrder
        
        return BrowserItem.lessThan(self, other, column, order)


class BrowserClassAttributeItem(BrowserItem):
    """
    Class implementing the data structure for browser class attribute items.
    """
    def __init__(self, parent, attribute, isClass=False):
        """
        Constructor
        
        @param parent parent item
        @param attribute reference to the attribute object
        @param isClass flag indicating a class attribute (boolean)
        """
        BrowserItem.__init__(self, parent, attribute.name)
        
        self.type_ = BrowserItemAttribute
        self._attributeObject = attribute
        self.__public = attribute.isPublic()
        if isClass:
            self.icon = UI.PixmapCache.getIcon("attribute_class.png")
        elif attribute.isPrivate():
            self.icon = UI.PixmapCache.getIcon("attribute_private.png")
        elif attribute.isProtected():
            self.icon = UI.PixmapCache.getIcon("attribute_protected.png")
        else:
            self.icon = UI.PixmapCache.getIcon("attribute.png")
    
    def isPublic(self):
        """
        Public method returning the public visibility status.
        
        @return flag indicating public visibility (boolean)
        """
        return self.__public
    
    def attributeObject(self):
        """
        Public method returning the class object.
        
        @return reference to the class object
        """
        return self._attributeObject
    
    def fileName(self):
        """
        Public method returning the filename.
        
        @return filename (string)
        """
        return self._attributeObject.file
    
    def lineno(self):
        """
        Public method returning the line number defining this object.
        
        @return line number defining the object (integer)
        """
        return self._attributeObject.lineno
    
    def linenos(self):
        """
        Public method returning the line numbers this object is assigned to.
        
        @return line number the object is assigned to (list of integers)
        """
        return self._attributeObject.linenos[:]
    
    def lessThan(self, other, column, order):
        """
        Public method to check, if the item is less than the other one.
        
        @param other reference to item to compare against (BrowserItem)
        @param column column number to use for the comparison (integer)
        @param order sort order (Qt.SortOrder) (for special sorting)
        @return true, if this item is less than other (boolean)
        """
        if Preferences.getUI("BrowsersListContentsByOccurrence") and \
                column == 0:
            if order == Qt.AscendingOrder:
                return self.lineno() < other.lineno()
            else:
                return self.lineno() > other.lineno()
        
        return BrowserItem.lessThan(self, other, column, order)


class BrowserGlobalsItem(BrowserClassAttributesItem):
    """
    Class implementing the data structure for browser globals items.
    """
    def __init__(self, parent, attributes, text):
        """
        Constructor
        
        @param parent parent item
        @param attributes list of attributes
        @param text text to be shown by this item (string)
        """
        BrowserClassAttributesItem.__init__(self, parent, attributes, text)


class BrowserCodingItem(BrowserItem):
    """
    Class implementing the data structure for browser coding items.
    """
    def __init__(self, parent, text):
        """
        Constructor
        
        @param parent parent item
        @param text text to be shown by this item (string)
        """
        BrowserItem.__init__(self, parent, text)
        
        self.type_ = BrowserItemCoding
        self.icon = UI.PixmapCache.getIcon("textencoding.png")
    
    def lessThan(self, other, column, order):
        """
        Public method to check, if the item is less than the other one.
        
        @param other reference to item to compare against (BrowserItem)
        @param column column number to use for the comparison (integer)
        @param order sort order (Qt.SortOrder) (for special sorting)
        @return true, if this item is less than other (boolean)
        """
        if issubclass(other.__class__, BrowserClassItem) or \
           issubclass(other.__class__, BrowserClassAttributesItem) or \
           issubclass(other.__class__, BrowserImportItem):
            return order == Qt.AscendingOrder
        
        return BrowserItem.lessThan(self, other, column, order)


class BrowserImportsItem(BrowserItem):
    """
    Class implementing the data structure for browser import items.
    """
    def __init__(self, parent, text):
        """
        Constructor
        
        @param parent parent item
        @param text text to be shown by this item (string)
        """
        BrowserItem.__init__(self, parent, text)
        
        self.type_ = BrowserItemImports
        self.icon = UI.PixmapCache.getIcon("imports.png")
    
    def lessThan(self, other, column, order):
        """
        Public method to check, if the item is less than the other one.
        
        @param other reference to item to compare against (BrowserItem)
        @param column column number to use for the comparison (integer)
        @param order sort order (Qt.SortOrder) (for special sorting)
        @return true, if this item is less than other (boolean)
        """
        if issubclass(other.__class__, BrowserClassItem) or \
           issubclass(other.__class__, BrowserClassAttributesItem):
            return order == Qt.AscendingOrder
        
        return BrowserItem.lessThan(self, other, column, order)


class BrowserImportItem(BrowserItem):
    """
    Class implementing the data structure for browser imported module and
    imported names items.
    """
    def __init__(self, parent, text, filename, lineNumbers, isModule=True):
        """
        Constructor
        
        @param parent parent item
        @param text text to be shown by this item (string)
        @param filename name of the file (string)
        @param lineNumbers list of line numbers of the import statement
            (list of integer)
        @param isModule flag indicating a module item entry (boolean)
        """
        BrowserItem.__init__(self, parent, text)
        
        self.__filename = filename
        self.__linenos = lineNumbers[:]
        
        self.type_ = BrowserItemImport
        if isModule:
            self.icon = UI.PixmapCache.getIcon("importedModule.png")
        else:
            self.icon = UI.PixmapCache.getIcon("importedName.png")
    
    def fileName(self):
        """
        Public method returning the filename.
        
        @return filename (string)
        """
        return self.__filename
    
    def lineno(self):
        """
        Public method returning the line number of the first import.
        
        @return line number of the first import (integer)
        """
        return self.__linenos[0]
    
    def linenos(self):
        """
        Public method returning the line numbers of all imports.
        
        @return line numbers of all imports (list of integers)
        """
        return self.__linenos[:]
    
    def lessThan(self, other, column, order):
        """
        Public method to check, if the item is less than the other one.
        
        @param other reference to item to compare against (BrowserItem)
        @param column column number to use for the comparison (integer)
        @param order sort order (Qt.SortOrder) (for special sorting)
        @return true, if this item is less than other (boolean)
        """
        if Preferences.getUI("BrowsersListContentsByOccurrence") and \
                column == 0:
            if order == Qt.AscendingOrder:
                return self.lineno() < other.lineno()
            else:
                return self.lineno() > other.lineno()
        
        return BrowserItem.lessThan(self, other, column, order)
