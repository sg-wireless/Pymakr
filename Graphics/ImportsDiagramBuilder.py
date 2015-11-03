# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog showing an imports diagram of a package.
"""

from __future__ import unicode_literals

import glob
import os

from PyQt5.QtWidgets import QApplication, QGraphicsTextItem

from E5Gui.E5ProgressDialog import E5ProgressDialog

from .UMLDiagramBuilder import UMLDiagramBuilder

import Utilities
import Preferences


class ImportsDiagramBuilder(UMLDiagramBuilder):
    """
    Class implementing a builder for imports diagrams of a package.
    
    Note: Only package internal imports are shown in order to maintain
    some readability.
    """
    def __init__(self, dialog, view, project, package,
                 showExternalImports=False):
        """
        Constructor
        
        @param dialog reference to the UML dialog (UMLDialog)
        @param view reference to the view object (UMLGraphicsView)
        @param project reference to the project object (Project)
        @param package name of a python package to show the import
            relationships (string)
        @keyparam showExternalImports flag indicating to show exports from
            outside the package (boolean)
        """
        super(ImportsDiagramBuilder, self).__init__(dialog, view, project)
        self.setObjectName("ImportsDiagram")
        
        self.showExternalImports = showExternalImports
        self.packagePath = Utilities.normabspath(package)
    
    def initialize(self):
        """
        Public method to initialize the object.
        """
        self.package = os.path.splitdrive(self.packagePath)[1].replace(
            os.sep, '.')[1:]
        hasInit = True
        ppath = self.packagePath
        while hasInit:
            ppath = os.path.dirname(ppath)
            hasInit = len(glob.glob(os.path.join(ppath, '__init__.*'))) > 0
        self.shortPackage = self.packagePath.replace(ppath, '').replace(
            os.sep, '.')[1:]
        
        pname = self.project.getProjectName()
        if pname:
            name = self.tr("Imports Diagramm {0}: {1}").format(
                pname, self.project.getRelativePath(self.packagePath))
        else:
            name = self.tr("Imports Diagramm: {0}").format(
                self.packagePath)
        self.umlView.setDiagramName(name)
    
    def __buildModulesDict(self):
        """
        Private method to build a dictionary of modules contained in the
        package.
        
        @return dictionary of modules contained in the package.
        """
        import Utilities.ModuleParser
        extensions = Preferences.getPython("PythonExtensions") + \
            Preferences.getPython("Python3Extensions")
        moduleDict = {}
        modules = []
        for ext in Preferences.getPython("PythonExtensions") + \
                Preferences.getPython("Python3Extensions"):
            modules.extend(glob.glob(Utilities.normjoinpath(
                self.packagePath, '*{0}'.format(ext))))
        
        tot = len(modules)
        progress = E5ProgressDialog(
            self.tr("Parsing modules..."),
            None, 0, tot, self.tr("%v/%m Modules"), self.parent())
        progress.setWindowTitle(self.tr("Imports Diagramm"))
        try:
            prog = 0
            progress.show()
            QApplication.processEvents()
            for module in modules:
                progress.setValue(prog)
                QApplication.processEvents()
                prog = prog + 1
                try:
                    mod = Utilities.ModuleParser.readModule(
                        module, extensions=extensions, caching=False)
                except ImportError:
                    continue
                else:
                    name = mod.name
                    if name.startswith(self.package):
                        name = name[len(self.package) + 1:]
                    moduleDict[name] = mod
        finally:
            progress.setValue(tot)
            progress.deleteLater()
        return moduleDict
    
    def buildDiagram(self):
        """
        Public method to build the modules shapes of the diagram.
        """
        initlist = glob.glob(os.path.join(self.packagePath, '__init__.*'))
        if len(initlist) == 0:
            ct = QGraphicsTextItem(None)
            ct.setHtml(
                self.tr(
                    "The directory <b>'{0}'</b> is not a Python package.")
                .format(self.package))
            self.scene.addItem(ct)
            return
        
        shapes = {}
        p = 10
        y = 10
        maxHeight = 0
        sceneRect = self.umlView.sceneRect()
        
        modules = self.__buildModulesDict()
        sortedkeys = sorted(modules.keys())
        externalMods = []
        packageList = self.shortPackage.split('.')
        packageListLen = len(packageList)
        for module in sortedkeys:
            impLst = []
            for i in modules[module].imports:
                if i.startswith(self.package):
                    n = i[len(self.package) + 1:]
                else:
                    n = i
                if i in modules:
                    impLst.append(n)
                elif self.showExternalImports:
                    impLst.append(n)
                    if n not in externalMods:
                        externalMods.append(n)
            for i in list(modules[module].from_imports.keys()):
                if i.startswith('.'):
                    dots = len(i) - len(i.lstrip('.'))
                    if dots == 1:
                        n = i[1:]
                        i = n
                    else:
                        if self.showExternalImports:
                            n = '.'.join(
                                packageList[:packageListLen - dots + 1] +
                                [i[dots:]])
                        else:
                            n = i
                elif i.startswith(self.package):
                    n = i[len(self.package) + 1:]
                else:
                    n = i
                if i in modules:
                    impLst.append(n)
                elif self.showExternalImports:
                    impLst.append(n)
                    if n not in externalMods:
                        externalMods.append(n)
            classNames = []
            for cls in list(modules[module].classes.keys()):
                className = modules[module].classes[cls].name
                if className not in classNames:
                    classNames.append(className)
            shape = self.__addModule(module, classNames, 0.0, 0.0)
            shapeRect = shape.sceneBoundingRect()
            shapes[module] = (shape, impLst)
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
        
        for module in externalMods:
            shape = self.__addModule(module, [], 0.0, 0.0)
            shapeRect = shape.sceneBoundingRect()
            shapes[module] = (shape, [])
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
    
    def __addModule(self, name, classes, x, y):
        """
        Private method to add a module to the diagram.
        
        @param name module name to be shown (string)
        @param classes list of class names contained in the module
            (list of strings)
        @param x x-coordinate (float)
        @param y y-coordinate (float)
        @return reference to the imports item (ModuleItem)
        """
        from .ModuleItem import ModuleItem, ModuleModel
        classes.sort()
        impM = ModuleModel(name, classes)
        impW = ModuleItem(impM, x, y, scene=self.scene)
        impW.setId(self.umlView.getItemId())
        return impW
    
    def __createAssociations(self, shapes):
        """
        Private method to generate the associations between the module shapes.
        
        @param shapes list of shapes
        """
        from .AssociationItem import AssociationItem, Imports
        for module in list(shapes.keys()):
            for rel in shapes[module][1]:
                assoc = AssociationItem(
                    shapes[module][0], shapes[rel][0],
                    Imports)
                self.scene.addItem(assoc)
    
    def getPersistenceData(self):
        """
        Public method to get a string for data to be persisted.
        
        @return persisted data string (string)
        """
        return "package={0}, show_external={1}".format(
            self.packagePath, self.showExternalImports)
    
    def parsePersistenceData(self, version, data):
        """
        Public method to parse persisted data.
        
        @param version version of the data (string)
        @param data persisted data to be parsed (string)
        @return flag indicating success (boolean)
        """
        parts = data.split(", ")
        if len(parts) != 2 or \
           not parts[0].startswith("package=") or \
           not parts[1].startswith("show_external="):
            return False
        
        self.packagePath = parts[0].split("=", 1)[1].strip()
        self.showExternalImports = Utilities.toBool(
            parts[1].split("=", 1)[1].strip())
        
        self.initialize()
        
        return True
