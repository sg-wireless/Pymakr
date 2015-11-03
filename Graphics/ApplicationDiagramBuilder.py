# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog showing an imports diagram of the application.
"""

from __future__ import unicode_literals

import os
import glob

from PyQt5.QtWidgets import QApplication

from E5Gui import E5MessageBox
from E5Gui.E5ProgressDialog import E5ProgressDialog

from .UMLDiagramBuilder import UMLDiagramBuilder

import Utilities
import Preferences


class ApplicationDiagramBuilder(UMLDiagramBuilder):
    """
    Class implementing a builder for imports diagrams of the application.
    """
    def __init__(self, dialog, view, project, noModules=False):
        """
        Constructor
        
        @param dialog reference to the UML dialog (UMLDialog)
        @param view reference to the view object (UMLGraphicsView)
        @param project reference to the project object (Project)
        @keyparam noModules flag indicating, that no module names should be
            shown (boolean)
        """
        super(ApplicationDiagramBuilder, self).__init__(dialog, view, project)
        self.setObjectName("ApplicationDiagram")
        
        self.noModules = noModules
        
        self.umlView.setDiagramName(
            self.tr("Application Diagram {0}").format(
                self.project.getProjectName()))
        
    def __buildModulesDict(self):
        """
        Private method to build a dictionary of modules contained in the
        application.
        
        @return dictionary of modules contained in the application.
        """
        import Utilities.ModuleParser
        extensions = Preferences.getPython("PythonExtensions") + \
            Preferences.getPython("Python3Extensions") + ['.rb']
        moduleDict = {}
        mods = self.project.pdata["SOURCES"]
        modules = []
        for module in mods:
            modules.append(Utilities.normabsjoinpath(
                self.project.ppath, module))
        tot = len(modules)
        progress = E5ProgressDialog(
            self.tr("Parsing modules..."),
            None, 0, tot, self.tr("%v/%m Modules"), self.parent())
        progress.setWindowTitle(self.tr("Application Diagram"))
        try:
            prog = 0
            progress.show()
            QApplication.processEvents()
            
            for module in modules:
                progress.setValue(prog)
                QApplication.processEvents()
                prog += 1
                if module.endswith("__init__.py"):
                    continue
                try:
                    mod = Utilities.ModuleParser.readModule(
                        module, extensions=extensions, caching=False)
                except ImportError:
                    continue
                else:
                    name = mod.name
                    moduleDict[name] = mod
        finally:
            progress.setValue(tot)
            progress.deleteLater()
        return moduleDict
        
    def buildDiagram(self):
        """
        Public method to build the packages shapes of the diagram.
        """
        project = os.path.splitdrive(self.project.getProjectPath())[1]\
            .replace(os.sep, '.')[1:]
        packages = {}
        shapes = {}
        p = 10
        y = 10
        maxHeight = 0
        sceneRect = self.umlView.sceneRect()
        
        modules = self.__buildModulesDict()
        sortedkeys = sorted(modules.keys())
        
        # step 1: build a dictionary of packages
        for module in sortedkeys:
            li = module.split('.')
            package = '.'.join(li[:-1])
            if package in packages:
                packages[package][0].append(li[-1])
            else:
                packages[package] = ([li[-1]], [])
                
        # step 2: assign modules to dictionaries and update import relationship
        for module in sortedkeys:
            li = module.split('.')
            package = '.'.join(li[:-1])
            impLst = []
            for i in modules[module].imports:
                if i in modules:
                    impLst.append(i)
                else:
                    if i.find('.') == -1:
                        n = "{0}.{1}".format(modules[module].package, i)
                        if n in modules:
                            impLst.append(n)
                        else:
                            n = "{0}.{1}".format(project, i)
                            if n in modules:
                                impLst.append(n)
                            elif n in packages:
                                n = "{0}.<<Dummy>>".format(n)
                                impLst.append(n)
                    else:
                        n = "{0}.{1}".format(project, i)
                        if n in modules:
                            impLst.append(n)
            for i in list(modules[module].from_imports.keys()):
                if i.startswith('.'):
                    dots = len(i) - len(i.lstrip('.'))
                    if dots == 1:
                        i = i[1:]
                    elif dots > 1:
                        packagePath = os.path.dirname(modules[module].file)
                        hasInit = True
                        ppath = packagePath
                        while hasInit:
                            ppath = os.path.dirname(ppath)
                            hasInit = len(glob.glob(os.path.join(
                                ppath, '__init__.*'))) > 0
                        shortPackage = packagePath.replace(ppath, '')\
                            .replace(os.sep, '.')[1:]
                        packageList = shortPackage.split('.')[1:]
                        packageListLen = len(packageList)
                        i = '.'.join(
                            packageList[:packageListLen - dots + 1] +
                            [i[dots:]])
                
                if i in modules:
                    impLst.append(i)
                else:
                    if i.find('.') == -1:
                        n = "{0}.{1}".format(modules[module].package, i)
                        if n in modules:
                            impLst.append(n)
                        else:
                            n = "{0}.{1}".format(project, i)
                            if n in modules:
                                impLst.append(n)
                            elif n in packages:
                                n = "{0}.<<Dummy>>".format(n)
                                impLst.append(n)
                    else:
                        n = "{0}.{1}".format(project, i)
                        if n in modules:
                            impLst.append(n)
            for imp in impLst:
                impPackage = '.'.join(imp.split('.')[:-1])
                if impPackage not in packages[package][1] and \
                   not impPackage == package:
                    packages[package][1].append(impPackage)
                    
        sortedkeys = sorted(packages.keys())
        for package in sortedkeys:
            if package:
                relPackage = package.replace(project, '')
                if relPackage and relPackage[0] == '.':
                    relPackage = relPackage[1:]
                else:
                    relPackage = self.tr("<<Application>>")
            else:
                relPackage = self.tr("<<Others>>")
            shape = self.__addPackage(
                relPackage, packages[package][0], 0.0, 0.0)
            shapeRect = shape.sceneBoundingRect()
            shapes[package] = (shape, packages[package][1])
            pn = p + shapeRect.width() + 10
            maxHeight = max(maxHeight, shapeRect.height())
            if pn > sceneRect.width():
                p = 10
                y += maxHeight + 10
                maxHeight = shapeRect.height()
                shape.setPos(p, y)
                p += shapeRect.width() + 10
            else:
                shape.setPos(p, y)
                p = pn
        
        rect = self.umlView._getDiagramRect(10)
        sceneRect = self.umlView.sceneRect()
        if rect.width() > sceneRect.width():
            sceneRect.setWidth(rect.width())
        if rect.height() > sceneRect.height():
            sceneRect.setHeight(rect.height())
        self.umlView.setSceneSize(sceneRect.width(), sceneRect.height())
        
        self.__createAssociations(shapes)
        self.umlView.autoAdjustSceneSize(limit=True)
        
    def __addPackage(self, name, modules, x, y):
        """
        Private method to add a package to the diagram.
        
        @param name package name to be shown (string)
        @param modules list of module names contained in the package
            (list of strings)
        @param x x-coordinate (float)
        @param y y-coordinate (float)
        @return reference to the package item (PackageItem)
        """
        from .PackageItem import PackageItem, PackageModel
        modules.sort()
        pm = PackageModel(name, modules)
        pw = PackageItem(pm, x, y, noModules=self.noModules, scene=self.scene)
        pw.setId(self.umlView.getItemId())
        return pw
        
    def __createAssociations(self, shapes):
        """
        Private method to generate the associations between the package shapes.
        
        @param shapes list of shapes
        """
        from .AssociationItem import AssociationItem, Imports
        for package in shapes:
            for rel in shapes[package][1]:
                assoc = AssociationItem(
                    shapes[package][0], shapes[rel][0],
                    Imports)
                self.scene.addItem(assoc)
    
    def getPersistenceData(self):
        """
        Public method to get a string for data to be persisted.
        
        @return persisted data string (string)
        """
        return "project={0}, no_modules={1}".format(
            self.project.getProjectFile(), self.noModules)
    
    def parsePersistenceData(self, version, data):
        """
        Public method to parse persisted data.
        
        @param version version of the data (string)
        @param data persisted data to be parsed (string)
        @return flag indicating success (boolean)
        """
        parts = data.split(", ")
        if len(parts) != 2 or \
           not parts[0].startswith("project=") or \
           not parts[1].startswith("no_modules="):
            return False
        
        projectFile = parts[0].split("=", 1)[1].strip()
        if projectFile != self.project.getProjectFile():
            res = E5MessageBox.yesNo(
                None,
                self.tr("Load Diagram"),
                self.tr(
                    """<p>The diagram belongs to the project <b>{0}</b>."""
                    """ Shall this project be opened?</p>""").format(
                    projectFile))
            if res:
                self.project.openProject(projectFile)
            
        self.noModules = Utilities.toBool(parts[1].split("=", 1)[1].strip())
        
        self.initialize()
        
        return True
