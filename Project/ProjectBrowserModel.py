# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the browser model.
"""

from __future__ import unicode_literals

import os
import re

from PyQt5.QtCore import QDir, QModelIndex, pyqtSignal, QFileSystemWatcher, Qt
from PyQt5.QtGui import QColor

from UI.BrowserModel import BrowserModel, BrowserItem, BrowserDirectoryItem, \
    BrowserFileItem

import UI.PixmapCache
import Preferences
import Utilities

import Utilities.ModuleParser

ProjectBrowserItemSimpleDirectory = 100
ProjectBrowserItemDirectory = 101
ProjectBrowserItemFile = 102

ProjectBrowserNoType = 0
ProjectBrowserSourceType = 1
ProjectBrowserFormType = 2
ProjectBrowserInterfaceType = 3
ProjectBrowserTranslationType = 4
ProjectBrowserOthersType = 5
ProjectBrowserResourceType = 6


class ProjectBrowserItemMixin(object):
    """
    Class implementing common methods of project browser items.
    
    It is meant to be used as a mixin class.
    """
    def __init__(self, type_, bold=False):
        """
        Constructor
        
        @param type_ type of file/directory in the project
        @param bold flag indicating a highlighted font
        """
        self._projectTypes = [type_]
        self.bold = bold
        self.vcsState = " "
    
    def getTextColor(self):
        """
        Public method to get the items text color.
        
        @return text color (QColor)
        """
        if self.bold:
            return Preferences.getProjectBrowserColour("Highlighted")
        else:
            return None
    
    def setVcsState(self, state):
        """
        Public method to set the items VCS state.
        
        @param state VCS state (one of A, C, M, U or " ") (string)
        """
        self.vcsState = state
    
    def addVcsStatus(self, vcsStatus):
        """
        Public method to add the VCS status.
        
        @param vcsStatus VCS status text (string)
        """
        self.itemData.append(vcsStatus)
    
    def setVcsStatus(self, vcsStatus):
        """
        Public method to set the VCS status.
        
        @param vcsStatus VCS status text (string)
        """
        self.itemData[1] = vcsStatus
    
    def getProjectTypes(self):
        """
        Public method to get the project type.
        
        @return project type
        """
        return self._projectTypes[:]
    
    def addProjectType(self, type_):
        """
        Public method to add a type to the list.
        
        @param type_ type to add to the list
        """
        self._projectTypes.append(type_)


class ProjectBrowserSimpleDirectoryItem(BrowserItem, ProjectBrowserItemMixin):
    """
    Class implementing the data structure for project browser simple directory
    items.
    """
    def __init__(self, parent, projectType, text, path=""):
        """
        Constructor
        
        @param parent parent item
        @param projectType type of file/directory in the project
        @param text text to be displayed (string)
        @param path path of the directory (string)
        """
        BrowserItem.__init__(self, parent, text)
        ProjectBrowserItemMixin.__init__(self, projectType)
        
        self._dirName = path
        if not os.path.isdir(self._dirName):
            self._dirName = os.path.dirname(self._dirName)
        
        self.type_ = ProjectBrowserItemSimpleDirectory
        if os.path.lexists(self._dirName) and os.path.islink(self._dirName):
            self.symlink = True
            self.icon = UI.PixmapCache.getSymlinkIcon("dirClosed.png")
        else:
            self.icon = UI.PixmapCache.getIcon("dirClosed.png")
    
    def setName(self, dinfo, full=True):
        """
        Public method to set the directory name.
        
        @param dinfo dinfo is the string for the directory (string)
        @param full flag indicating full pathname should be displayed (boolean)
        """
        self._dirName = os.path.abspath(dinfo)
        self.itemData[0] = os.path.basename(self._dirName)
    
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


class ProjectBrowserDirectoryItem(BrowserDirectoryItem,
                                  ProjectBrowserItemMixin):
    """
    Class implementing the data structure for project browser directory items.
    """
    def __init__(self, parent, dinfo, projectType, full=True, bold=False):
        """
        Constructor
        
        @param parent parent item
        @param dinfo dinfo is the string for the directory (string)
        @param projectType type of file/directory in the project
        @param full flag indicating full pathname should be displayed (boolean)
        @param bold flag indicating a highlighted font (boolean)
        """
        BrowserDirectoryItem.__init__(self, parent, dinfo, full)
        ProjectBrowserItemMixin.__init__(self, projectType, bold)
        
        self.type_ = ProjectBrowserItemDirectory


class ProjectBrowserFileItem(BrowserFileItem, ProjectBrowserItemMixin):
    """
    Class implementing the data structure for project browser file items.
    """
    def __init__(self, parent, finfo, projectType, full=True, bold=False,
                 sourceLanguage=""):
        """
        Constructor
        
        @param parent parent item
        @param finfo the string for the file (string)
        @param projectType type of file/directory in the project
        @param full flag indicating full pathname should be displayed (boolean)
        @param bold flag indicating a highlighted font (boolean)
        @param sourceLanguage source code language of the project (string)
        """
        BrowserFileItem.__init__(self, parent, finfo, full, sourceLanguage)
        ProjectBrowserItemMixin.__init__(self, projectType, bold)
        
        self.type_ = ProjectBrowserItemFile


class ProjectBrowserModel(BrowserModel):
    """
    Class implementing the project browser model.
    
    @signal vcsStateChanged(str) emitted after the VCS state has changed
    """
    vcsStateChanged = pyqtSignal(str)
    
    def __init__(self, parent):
        """
        Constructor
        
        @param parent reference to parent object (Project.Project)
        """
        super(ProjectBrowserModel, self).__init__(parent, nopopulate=True)
        
        rootData = self.tr("Name")
        self.rootItem = BrowserItem(None, rootData)
        self.rootItem.itemData.append(self.tr("VCS Status"))
        
        self.progDir = None
        self.project = parent
        
        self.watchedItems = {}
        self.watcher = QFileSystemWatcher(self)
        self.watcher.directoryChanged.connect(self.directoryChanged)
        
        self.inRefresh = False
        
        self.projectBrowserTypes = {
            "SOURCES": ProjectBrowserSourceType,
            "FORMS": ProjectBrowserFormType,
            "RESOURCES": ProjectBrowserResourceType,
            "INTERFACES": ProjectBrowserInterfaceType,
            "TRANSLATIONS": ProjectBrowserTranslationType,
            "OTHERS": ProjectBrowserOthersType,
        }
        
        self.colorNames = {
            "A": "VcsAdded",
            "M": "VcsModified",
            "O": "VcsRemoved",
            "R": "VcsReplaced",
            "U": "VcsUpdate",
            "Z": "VcsConflict",
        }
        self.itemBackgroundColors = {
            " ": QColor(),
            "A": Preferences.getProjectBrowserColour(self.colorNames["A"]),
            "M": Preferences.getProjectBrowserColour(self.colorNames["M"]),
            "O": Preferences.getProjectBrowserColour(self.colorNames["O"]),
            "R": Preferences.getProjectBrowserColour(self.colorNames["R"]),
            "U": Preferences.getProjectBrowserColour(self.colorNames["U"]),
            "Z": Preferences.getProjectBrowserColour(self.colorNames["Z"]),
        }
        
        self.highLightColor = \
            Preferences.getProjectBrowserColour("Highlighted")
        # needed by preferencesChanged()
        
        self.vcsStatusReport = {}
    
    def data(self, index, role):
        """
        Public method to get data of an item.
        
        @param index index of the data to retrieve (QModelIndex)
        @param role role of data (Qt.ItemDataRole)
        @return requested data
        """
        if not index.isValid():
            return None
        
        if role == Qt.TextColorRole:
            if index.column() == 0:
                try:
                    return index.internalPointer().getTextColor()
                except AttributeError:
                    return None
        elif role == Qt.BackgroundColorRole:
            try:
                col = self.itemBackgroundColors[
                    index.internalPointer().vcsState]
                if col.isValid():
                    return col
                else:
                    return None
            except AttributeError:
                return None
            except KeyError:
                return None
        
        return BrowserModel.data(self, index, role)
    
    def populateItem(self, parentItem, repopulate=False):
        """
        Public method to populate an item's subtree.
        
        @param parentItem reference to the item to be populated
        @param repopulate flag indicating a repopulation (boolean)
        """
        if parentItem.type() == ProjectBrowserItemSimpleDirectory:
            return  # nothing to do
        elif parentItem.type() == ProjectBrowserItemDirectory:
            self.populateProjectDirectoryItem(parentItem, repopulate)
        elif parentItem.type() == ProjectBrowserItemFile:
            self.populateFileItem(parentItem, repopulate)
        else:
            BrowserModel.populateItem(self, parentItem, repopulate)

    def populateProjectDirectoryItem(self, parentItem, repopulate=False):
        """
        Public method to populate a directory item's subtree.
        
        @param parentItem reference to the directory item to be populated
        @param repopulate flag indicating a repopulation (boolean)
        """
        self._addWatchedItem(parentItem)
        
        qdir = QDir(parentItem.dirName())
        
        if Preferences.getUI("BrowsersListHiddenFiles"):
            filter = QDir.Filters(QDir.AllEntries |
                                  QDir.Hidden |
                                  QDir.NoDotAndDotDot)
        else:
            filter = QDir.Filters(QDir.AllEntries | QDir.NoDot | QDir.NoDotDot)
        entryInfoList = qdir.entryInfoList(filter)
        
        if len(entryInfoList) > 0:
            if repopulate:
                self.beginInsertRows(self.createIndex(
                    parentItem.row(), 0, parentItem),
                    0, len(entryInfoList) - 1)
            states = {}
            if self.project.vcs is not None:
                for f in entryInfoList:
                    fname = f.absoluteFilePath()
                    states[os.path.normcase(fname)] = 0
                dname = parentItem.dirName()
                self.project.vcs.clearStatusCache()
                states = self.project.vcs.vcsAllRegisteredStates(states, dname)
            
            for f in entryInfoList:
                if f.isDir():
                    node = ProjectBrowserDirectoryItem(
                        parentItem,
                        Utilities.toNativeSeparators(f.absoluteFilePath()),
                        parentItem.getProjectTypes()[0], False)
                else:
                    node = ProjectBrowserFileItem(
                        parentItem,
                        Utilities.toNativeSeparators(f.absoluteFilePath()),
                        parentItem.getProjectTypes()[0])
                if self.project.vcs is not None:
                    fname = f.absoluteFilePath()
                    if states[os.path.normcase(fname)] == \
                            self.project.vcs.canBeCommitted:
                        node.addVcsStatus(self.project.vcs.vcsName())
                        self.project.clearStatusMonitorCachedState(
                            f.absoluteFilePath())
                    else:
                        node.addVcsStatus(self.tr("local"))
                self._addItem(node, parentItem)
            if repopulate:
                self.endInsertRows()

    def projectClosed(self):
        """
        Public method called after a project has been closed.
        """
        self.__vcsStatus = {}
        
        self.watchedItems = {}
        watchedDirs = self.watcher.directories()
        if watchedDirs:
            self.watcher.removePaths(watchedDirs)
        
        self.rootItem.removeChildren()
        self.beginResetModel()
        self.endResetModel()
        
        # reset the module parser cache
        Utilities.ModuleParser.resetParsedModules()
        
    def projectOpened(self):
        """
        Public method used to populate the model after a project has been
        opened.
        """
        self.__vcsStatus = {}
        states = {}
        keys = list(self.projectBrowserTypes.keys())[:]
        
        if self.project.vcs is not None:
            for key in keys:
                for fn in self.project.pdata[key]:
                    states[os.path.normcase(
                        os.path.join(self.project.ppath, fn))] = 0
            
            self.project.vcs.clearStatusCache()
            states = self.project.vcs.vcsAllRegisteredStates(
                states, self.project.ppath)
        
        self.inRefresh = True
        for key in keys:
            # Show the entry in bold in the others browser to make it more
            # distinguishable
            if key == "OTHERS":
                bold = True
            else:
                bold = False
            
            if key == "SOURCES":
                sourceLanguage = self.project.pdata["PROGLANGUAGE"][0]
            else:
                sourceLanguage = ""
            
            for fn in self.project.pdata[key]:
                fname = os.path.join(self.project.ppath, fn)
                parentItem, dt = self.findParentItemByName(
                    self.projectBrowserTypes[key], fn)
                if os.path.isdir(fname):
                    itm = ProjectBrowserDirectoryItem(
                        parentItem, fname, self.projectBrowserTypes[key],
                        False, bold)
                else:
                    itm = ProjectBrowserFileItem(
                        parentItem, fname, self.projectBrowserTypes[key],
                        False, bold, sourceLanguage=sourceLanguage)
                self._addItem(itm, parentItem)
                if self.project.vcs is not None:
                    if states[os.path.normcase(fname)] == \
                            self.project.vcs.canBeCommitted:
                        itm.addVcsStatus(self.project.vcs.vcsName())
                    else:
                        itm.addVcsStatus(self.tr("local"))
                else:
                    itm.addVcsStatus("")
        self.inRefresh = False
        self.beginResetModel()
        self.endResetModel()

    def findParentItemByName(self, type_, name, dontSplit=False):
        """
        Public method to find an item given its name.
        
        <b>Note</b>: This method creates all necessary parent items, if they
        don't exist.
        
        @param type_ type of the item
        @param name name of the item (string)
        @param dontSplit flag indicating the name should not be split (boolean)
        @return reference to the item found and the new display name (string)
        """
        if dontSplit:
            pathlist = []
            pathlist.append(name)
            pathlist.append("ignore_me")
        else:
            pathlist = re.split(r'/|\\', name)
        
        if len(pathlist) > 1:
            olditem = self.rootItem
            path = self.project.ppath
            for p in pathlist[:-1]:
                itm = self.findChildItem(p, 0, olditem)
                path = os.path.join(path, p)
                if itm is None:
                    itm = ProjectBrowserSimpleDirectoryItem(
                        olditem, type_, p, path)
                    self.__addVCSStatus(itm, path)
                    if self.inRefresh:
                        self._addItem(itm, olditem)
                    else:
                        if olditem == self.rootItem:
                            oldindex = QModelIndex()
                        else:
                            oldindex = self.createIndex(
                                olditem.row(), 0, olditem)
                        self.addItem(itm, oldindex)
                else:
                    if type_ and type_ not in itm.getProjectTypes():
                        itm.addProjectType(type_)
                        index = self.createIndex(itm.row(), 0, itm)
                        self.dataChanged.emit(index, index)
                olditem = itm
            return (itm, pathlist[-1])
        else:
            return (self.rootItem, name)
    
    def findChildItem(self, text, column, parentItem=None):
        """
        Public method to find a child item given some text.
        
        @param text text to search for (string)
        @param column column to search in (integer)
        @param parentItem reference to parent item
        @return reference to the item found
        """
        if parentItem is None:
            parentItem = self.rootItem
        
        for itm in parentItem.children():
            if itm.data(column) == text:
                return itm
        
        return None
        
    def addNewItem(self, typeString, name, additionalTypeStrings=[]):
        """
        Public method to add a new item to the model.
        
        @param typeString string denoting the type of the new item (string)
        @param name name of the new item (string)
        @param additionalTypeStrings names of additional types (list of string)
        """
        # Show the entry in bold in the others browser to make it more
        # distinguishable
        if typeString == "OTHERS":
            bold = True
        else:
            bold = False
        
        fname = os.path.join(self.project.ppath, name)
        parentItem, dt = self.findParentItemByName(
            self.projectBrowserTypes[typeString], name)
        if parentItem == self.rootItem:
            parentIndex = QModelIndex()
        else:
            parentIndex = self.createIndex(parentItem.row(), 0, parentItem)
        if os.path.isdir(fname):
            itm = ProjectBrowserDirectoryItem(
                parentItem, fname, self.projectBrowserTypes[typeString],
                False, bold)
        else:
            if typeString == "SOURCES":
                sourceLanguage = self.project.pdata["PROGLANGUAGE"][0]
            else:
                sourceLanguage = ""
            itm = ProjectBrowserFileItem(
                parentItem, fname, self.projectBrowserTypes[typeString],
                False, bold, sourceLanguage=sourceLanguage)
        self.__addVCSStatus(itm, fname)
        if additionalTypeStrings:
            for additionalTypeString in additionalTypeStrings:
                type_ = self.projectBrowserTypes[additionalTypeString]
                itm.addProjectType(type_)
        self.addItem(itm, parentIndex)
    
    def renameItem(self, name, newFilename):
        """
        Public method to rename an item.
        
        @param name the old display name (string)
        @param newFilename new filename of the item (string)
        """
        itm = self.findItem(name)
        if itm is None:
            return
        
        index = self.createIndex(itm.row(), 0, itm)
        itm.setName(newFilename)
        self.dataChanged.emit(index, index)
        self.repopulateItem(newFilename)
    
    def findItem(self, name):
        """
        Public method to find an item given its name.
        
        @param name name of the item (string)
        @return reference to the item found
        """
        if QDir.isAbsolutePath(name):
            name = self.project.getRelativePath(name)
        pathlist = re.split(r'/|\\', name)
        if len(pathlist) > 0:
            olditem = self.rootItem
            for p in pathlist:
                itm = self.findChildItem(p, 0, olditem)
                if itm is None:
                    return None
                olditem = itm
            return itm
        else:
            return None
    
    def itemIndexByName(self, name):
        """
        Public method to find an item's index given its name.
        
        @param name name of the item (string)
        @return index of the item found (QModelIndex)
        """
        itm = self.findItem(name)
        if itm is None:
            index = QModelIndex()
        else:
            index = self.createIndex(itm.row(), 0, itm)
        return index
    
    def itemIndexByNameAndLine(self, name, lineno):
        """
        Public method to find an item's index given its name.
        
        @param name name of the item (string)
        @param lineno one based line number of the item (integer)
        @return index of the item found (QModelIndex)
        """
        index = QModelIndex()
        itm = self.findItem(name)
        if itm is not None and \
           isinstance(itm, ProjectBrowserFileItem):
            olditem = itm
            autoPopulate = Preferences.getProject("AutoPopulateItems")
            while itm is not None:
                if not itm.isPopulated():
                    if itm.isLazyPopulated() and autoPopulate:
                        self.populateItem(itm)
                    else:
                        break
                for child in itm.children():
                    try:
                        start, end = child.boundaries()
                        if end == -1:
                            end = 1000000   # assume end of file
                        if start <= lineno <= end:
                            itm = child
                            break
                    except AttributeError:
                        pass
                else:
                    itm = None
                if itm:
                    olditem = itm
            index = self.createIndex(olditem.row(), 0, olditem)
        
        return index
    
    def directoryChanged(self, path):
        """
        Public slot to handle the directoryChanged signal of the watcher.
        
        @param path path of the directory (string)
        """
        if path not in self.watchedItems:
            # just ignore the situation we don't have a reference to the item
            return
        
        if Preferences.getUI("BrowsersListHiddenFiles"):
            filter = QDir.Filters(QDir.AllEntries |
                                  QDir.Hidden |
                                  QDir.NoDotAndDotDot)
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
                    node = ProjectBrowserDirectoryItem(
                        itm,
                        Utilities.toNativeSeparators(f.absoluteFilePath()),
                        itm.getProjectTypes()[0],
                        False)
                else:
                    node = ProjectBrowserFileItem(
                        itm,
                        Utilities.toNativeSeparators(f.absoluteFilePath()),
                        itm.getProjectTypes()[0])
                self._addItem(node, itm)
                if self.project.vcs is not None:
                    self.project.vcs.clearStatusCache()
                    state = self.project.vcs.vcsRegisteredState(node.name())
                    if state == self.project.vcs.canBeCommitted:
                        node.addVcsStatus(self.project.vcs.vcsName())
                    else:
                        node.addVcsStatus(self.tr("local"))
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
    
    def __addVCSStatus(self, item, name):
        """
        Private method used to set the vcs status of a node.
        
        @param item item to work on
        @param name filename belonging to this item (string)
        """
        if self.project.vcs is not None:
            state = self.project.vcs.vcsRegisteredState(name)
            if state == self.project.vcs.canBeCommitted:
                item.addVcsStatus(self.project.vcs.vcsName())
            else:
                item.addVcsStatus(self.tr("local"))
        else:
            item.addVcsStatus("")
    
    def __updateVCSStatus(self, item, name, recursive=True):
        """
        Private method used to update the vcs status of a node.
        
        @param item item to work on
        @param name filename belonging to this item (string)
        @keyparam recursive flag indicating a recursive update (boolean)
        """
        if self.project.vcs is not None:
            self.project.vcs.clearStatusCache()
            state = self.project.vcs.vcsRegisteredState(name)
            if state == self.project.vcs.canBeCommitted:
                item.setVcsStatus(self.project.vcs.vcsName())
            else:
                item.setVcsStatus(self.tr("local"))
            if recursive:
                name = os.path.dirname(name)
                parentItem = item.parent()
                if name and parentItem is not self.rootItem:
                    self.__updateVCSStatus(parentItem, name, recursive)
        else:
            item.setVcsStatus("")
        
        index = self.createIndex(item.row(), 0, item)
        self.dataChanged.emit(index, index)
    
    def updateVCSStatus(self, name, recursive=True):
        """
        Public method used to update the vcs status of a node.
        
        @param name filename belonging to this item (string)
        @param recursive flag indicating a recursive update (boolean)
        """
        item = self.findItem(name)
        if item:
            self.__updateVCSStatus(item, name, recursive)
    
    def removeItem(self, name):
        """
        Public method to remove a named item.
        
        @param name file or directory name of the item (string).
        """
        fname = os.path.basename(name)
        parentItem = self.findParentItemByName(0, name)[0]
        if parentItem == self.rootItem:
            parentIndex = QModelIndex()
        else:
            parentIndex = self.createIndex(parentItem.row(), 0, parentItem)
        childItem = self.findChildItem(fname, 0, parentItem)
        if childItem is not None:
            self.beginRemoveRows(parentIndex, childItem.row(), childItem.row())
            parentItem.removeChild(childItem)
            self.endRemoveRows()
    
    def repopulateItem(self, name):
        """
        Public method to repopulate an item.
        
        @param name name of the file relative to the project root (string)
        """
        itm = self.findItem(name)
        if itm is None:
            return
        
        if itm.isLazyPopulated():
            if not itm.isPopulated():
                # item is not populated yet, nothing to do
                return
            
            if itm.childCount():
                index = self.createIndex(itm.row(), 0, itm)
                self.beginRemoveRows(index, 0, itm.childCount() - 1)
                itm.removeChildren()
                self.endRemoveRows()
            Utilities.ModuleParser.resetParsedModule(
                os.path.join(self.project.ppath, name))
            
            self.populateItem(itm, True)
    
    def projectPropertiesChanged(self):
        """
        Public method to react on a change of the project properties.
        """
        # nothing to do for now
        return

    def changeVCSStates(self, statesList):
        """
        Public slot to record the (non normal) VCS states.
        
        @param statesList list of VCS state entries (list of strings) giving
            the states in the first column and the path relative to the project
            directory starting with the third column. The allowed status flags
            are:
            <ul>
                <li>"A" path was added but not yet comitted</li>
                <li>"M" path has local changes</li>
                <li>"O" path was removed</li>
                <li>"R" path was deleted and then re-added</li>
                <li>"U" path needs an update</li>
                <li>"Z" path contains a conflict</li>
                <li>" " path is back at normal</li>
            </ul>
        """
        statesList.sort()
        lastHead = ""
        itemCache = {}
        if len(statesList) == 1 and statesList[0] == '--RESET--':
            statesList = []
            for name in list(self.__vcsStatus.keys()):
                statesList.append(" {0}".format(name))
        
        for name in statesList:
            state = name[0]
            name = name[1:].strip()
            if state == ' ':
                if name in self.__vcsStatus:
                    del self.__vcsStatus[name]
            else:
                self.__vcsStatus[name] = state
            
            try:
                itm = itemCache[name]
            except KeyError:
                itm = self.findItem(name)
                if itm:
                    itemCache[name] = itm
            if itm:
                itm.setVcsState(state)
                itm.setVcsStatus(self.project.vcs.vcsName())
                index1 = self.createIndex(itm.row(), 0, itm)
                index2 = self.createIndex(
                    itm.row(), self.rootItem.columnCount(), itm)
                self.dataChanged.emit(index1, index2)
            
            head, tail = os.path.split(name)
            if head != lastHead:
                if lastHead:
                    self.__changeParentsVCSState(lastHead, itemCache)
                lastHead = head
        if lastHead:
            self.__changeParentsVCSState(lastHead, itemCache)
        try:
            globalVcsStatus = sorted(self.__vcsStatus.values())[-1]
        except IndexError:
            globalVcsStatus = ' '
        self.vcsStateChanged.emit(globalVcsStatus)

    def __changeParentsVCSState(self, path, itemCache):
        """
        Private method to recursively change the parents VCS state.
        
        @param path pathname of parent item (string)
        @param itemCache reference to the item cache used to store
            references to named items
        """
        while path:
            try:
                itm = itemCache[path]
            except KeyError:
                itm = self.findItem(path)
                if itm:
                    itemCache[path] = itm
            if itm:
                state = " "
                for id_ in itm.children():
                    if state < id_.vcsState:
                        state = id_.vcsState
                if state != itm.vcsState:
                    itm.setVcsState(state)
                    index1 = self.createIndex(itm.row(), 0, itm)
                    index2 = self.createIndex(
                        itm.row(), self.rootItem.columnCount(), itm)
                    self.dataChanged.emit(index1, index2)
            path, tail = os.path.split(path)
    
    def preferencesChanged(self):
        """
        Public method used to handle a change in preferences.
        """
        for code in list(self.colorNames.keys()):
            color = Preferences.getProjectBrowserColour(self.colorNames[code])
            if color.name() == self.itemBackgroundColors[code].name():
                continue
            
            self.itemBackgroundColors[code] = color
        
        color = Preferences.getProjectBrowserColour("Highlighted")
        if self.highLightColor.name() != color.name():
            self.highLightColor = color
