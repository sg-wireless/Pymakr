# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the multi project browser.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QDialog, QMenu

from E5Gui.E5Application import e5App

import UI.PixmapCache


class MultiProjectBrowser(QTreeWidget):
    """
    Class implementing the multi project browser.
    """
    def __init__(self, multiProject, parent=None):
        """
        Constructor
        
        @param multiProject reference to the multi project object
        @param parent parent widget (QWidget)
        """
        super(MultiProjectBrowser, self).__init__(parent)
        self.multiProject = multiProject
        
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        self.setAlternatingRowColors(True)
        self.setHeaderHidden(True)
        self.setItemsExpandable(False)
        self.setRootIsDecorated(False)
        self.setSortingEnabled(True)
        
        self.__openingProject = False
        
        self.multiProject.newMultiProject.connect(
            self.__newMultiProject)
        self.multiProject.multiProjectOpened.connect(
            self.__multiProjectOpened)
        self.multiProject.multiProjectClosed.connect(
            self.__multiProjectClosed)
        self.multiProject.projectDataChanged.connect(
            self.__projectDataChanged)
        self.multiProject.projectAdded.connect(
            self.__projectAdded)
        self.multiProject.projectRemoved.connect(
            self.__projectRemoved)
        self.multiProject.projectOpened.connect(
            self.__projectOpened)
        
        self.__createPopupMenu()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__contextMenuRequested)
        self.itemActivated.connect(self.__openItem)
        
        self.setEnabled(False)
    
    ###########################################################################
    ## Slot handling methods below
    ###########################################################################
    
    def __newMultiProject(self):
        """
        Private slot to handle the creation of a new multi project.
        """
        self.clear()
        self.setEnabled(True)
    
    def __multiProjectOpened(self):
        """
        Private slot to handle the opening of a multi project.
        """
        for project in self.multiProject.getProjects():
            self.__addProject(project)
        
        self.sortItems(0, Qt.AscendingOrder)
        
        self.setEnabled(True)
    
    def __multiProjectClosed(self):
        """
        Private slot to handle the closing of a multi project.
        """
        self.clear()
        self.setEnabled(False)
    
    def __projectAdded(self, project):
        """
        Private slot to handle the addition of a project to the multi project.
        
        @param project reference to the project data dictionary
        """
        self.__addProject(project)
        self.sortItems(0, Qt.AscendingOrder)
    
    def __projectRemoved(self, project):
        """
        Private slot to handle the removal of a project from the multi project.
        
        @param project reference to the project data dictionary
        """
        itm = self.__findProjectItem(project)
        if itm:
            parent = itm.parent()
            parent.removeChild(itm)
            del itm
            if parent.childCount() == 0:
                top = self.takeTopLevelItem(self.indexOfTopLevelItem(parent))
                del top
    
    def __projectDataChanged(self, project):
        """
        Private slot to handle the change of a project of the multi project.
        
        @param project reference to the project data dictionary
        """
        itm = self.__findProjectItem(project)
        if itm:
            parent = itm.parent()
            if parent.text(0) != project["category"]:
                self.__projectRemoved(project)
                self.__addProject(project)
            else:
                self.__setItemData(itm, project)
            
        self.sortItems(0, Qt.AscendingOrder)
    
    def __projectOpened(self, projectfile):
        """
        Private slot to handle the opening of a project.
        
        @param projectfile file name of the opened project file (string)
        """
        project = {
            'name': "",
            'file': projectfile,
            'master': False,
            'description': "",
            'category': "",
        }
        itm = self.__findProjectItem(project)
        if itm:
            itm.setSelected(True)
    
    def __contextMenuRequested(self, coord):
        """
        Private slot to show the context menu.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        itm = self.itemAt(coord)
        if itm is None or itm.parent() is None:
            self.__backMenu.popup(self.mapToGlobal(coord))
        else:
            self.__menu.popup(self.mapToGlobal(coord))
    
    def __openItem(self, itm=None):
        """
        Private slot to open a project.
        
        @param itm reference to the project item to be opened (QTreeWidgetItem)
        """
        if itm is None:
            itm = self.currentItem()
            if itm is None or itm.parent() is None:
                return
        
        if not self.__openingProject:
            filename = itm.data(0, Qt.UserRole)
            if filename:
                self.__openingProject = True
                self.multiProject.openProject(filename)
                self.__openingProject = False
    
    ###########################################################################
    ## Private methods below
    ###########################################################################
    
    def __findCategoryItem(self, category):
        """
        Private method to find the item for a category.
        
        @param category category to search for (string)
        @return reference to the category item or None, if there is
            no such item (QTreeWidgetItem or None)
        """
        if category == "":
            category = self.tr("Not categorized")
        for index in range(self.topLevelItemCount()):
            itm = self.topLevelItem(index)
            if itm.text(0) == category:
                return itm
        
        return None
    
    def __addProject(self, project):
        """
        Private method to add a project to the list.
        
        @param project reference to the project data dictionary
        """
        parent = self.__findCategoryItem(project['category'])
        if parent is None:
            if project['category']:
                parent = QTreeWidgetItem(self, [project['category']])
            else:
                parent = QTreeWidgetItem(self, [self.tr("Not categorized")])
            parent.setExpanded(True)
        itm = QTreeWidgetItem(parent)
        self.__setItemData(itm, project)
    
    def __setItemData(self, itm, project):
        """
        Private method to set the data of a project item.
        
        @param itm reference to the item to be set (QTreeWidgetItem)
        @param project reference to the project data dictionary
        """
        itm.setText(0, project['name'])
        if project['master']:
            itm.setIcon(0, UI.PixmapCache.getIcon("masterProject.png"))
        else:
            itm.setIcon(0, UI.PixmapCache.getIcon("empty.png"))
        itm.setToolTip(0, project['file'])
        itm.setData(0, Qt.UserRole, project['file'])
    
    def __findProjectItem(self, project):
        """
        Private method to search a specific project item.
        
        @param project reference to the project data dictionary
        @return reference to the item (QTreeWidgetItem) or None
        """
        for topIndex in range(self.topLevelItemCount()):
            topItm = self.topLevelItem(topIndex)
            for childIndex in range(topItm.childCount()):
                itm = topItm.child(childIndex)
                data = itm.data(0, Qt.UserRole)
                if data == project['file']:
                    return itm
        
        return None
    
    def __removeProject(self):
        """
        Private method to handle the Remove context menu entry.
        """
        itm = self.currentItem()
        if itm is not None and itm.parent() is not None:
            filename = itm.data(0, Qt.UserRole)
            if filename:
                self.multiProject.removeProject(filename)
    
    def __showProjectProperties(self):
        """
        Private method to show the data of a project entry.
        """
        itm = self.currentItem()
        if itm is not None and itm.parent() is not None:
            filename = itm.data(0, Qt.UserRole)
            if filename:
                project = self.multiProject.getProject(filename)
                if project is not None:
                    from .AddProjectDialog import AddProjectDialog
                    dlg = AddProjectDialog(
                        self, project=project,
                        categories=self.multiProject.getCategories())
                    if dlg.exec_() == QDialog.Accepted:
                        (name, filename, isMaster, description, category,
                         uid) = dlg.getData()
                        project = {
                            'name': name,
                            'file': filename,
                            'master': isMaster,
                            'description': description,
                            'category': category,
                            'uid': uid,
                        }
                        self.multiProject.changeProjectProperties(project)
    
    def __addNewProject(self):
        """
        Private method to add a new project entry.
        """
        self.multiProject.addProject()
    
    def __createPopupMenu(self):
        """
        Private method to create the popup menu.
        """
        self.__menu = QMenu(self)
        self.__menu.addAction(self.tr("Open"), self.__openItem)
        self.__menu.addAction(self.tr("Remove"), self.__removeProject)
        self.__menu.addAction(self.tr("Properties"),
                              self.__showProjectProperties)
        self.__menu.addSeparator()
        self.__menu.addAction(self.tr("Add Project..."),
                              self.__addNewProject)
        self.__menu.addSeparator()
        self.__menu.addAction(self.tr("Configure..."), self.__configure)
        
        self.__backMenu = QMenu(self)
        self.__backMenu.addAction(self.tr("Add Project..."),
                                  self.__addNewProject)
        self.__backMenu.addSeparator()
        self.__backMenu.addAction(self.tr("Configure..."),
                                  self.__configure)
    
    def __configure(self):
        """
        Private method to open the configuration dialog.
        """
        e5App().getObject("UserInterface").showPreferences("multiProjectPage")
