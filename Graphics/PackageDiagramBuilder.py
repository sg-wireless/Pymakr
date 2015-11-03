# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog showing a UML like class diagram of a package.
"""

from __future__ import unicode_literals

import glob
import os.path
try:  # Py3
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest    # __IGNORE_WARNING__

from PyQt5.QtWidgets import QApplication, QGraphicsTextItem

from E5Gui.E5ProgressDialog import E5ProgressDialog

from .UMLDiagramBuilder import UMLDiagramBuilder

import Utilities
import Preferences


class PackageDiagramBuilder(UMLDiagramBuilder):
    """
    Class implementing a builder for UML like class diagrams of a package.
    """
    def __init__(self, dialog, view, project, package, noAttrs=False):
        """
        Constructor
        
        @param dialog reference to the UML dialog (UMLDialog)
        @param view reference to the view object (UMLGraphicsView)
        @param project reference to the project object (Project)
        @param package name of a python package to be shown (string)
        @keyparam noAttrs flag indicating, that no attributes should be shown
            (boolean)
        """
        super(PackageDiagramBuilder, self).__init__(dialog, view, project)
        self.setObjectName("PackageDiagram")
        
        self.package = Utilities.normabspath(package)
        self.noAttrs = noAttrs
    
    def initialize(self):
        """
        Public method to initialize the object.
        """
        pname = self.project.getProjectName()
        if pname:
            name = self.tr("Package Diagram {0}: {1}").format(
                pname, self.project.getRelativePath(self.package))
        else:
            name = self.tr("Package Diagram: {0}").format(self.package)
        self.umlView.setDiagramName(name)
    
    def __getCurrentShape(self, name):
        """
        Private method to get the named shape.
        
        @param name name of the shape (string)
        @return shape (QCanvasItem)
        """
        return self.allClasses.get(name)
    
    def __buildModulesDict(self):
        """
        Private method to build a dictionary of modules contained in the
        package.
        
        @return dictionary of modules contained in the package.
        """
        import Utilities.ModuleParser
        
        supportedExt = \
            ['*{0}'.format(ext) for ext in
             Preferences.getPython("PythonExtensions")] + \
            ['*{0}'.format(ext) for ext in
             Preferences.getPython("Python3Extensions")] + \
            ['*.rb']
        extensions = Preferences.getPython("PythonExtensions") + \
            Preferences.getPython("Python3Extensions") + ['.rb']
        
        moduleDict = {}
        modules = []
        for ext in supportedExt:
            modules.extend(glob.glob(
                Utilities.normjoinpath(self.package, ext)))
        tot = len(modules)
        progress = E5ProgressDialog(
            self.tr("Parsing modules..."),
            None, 0, tot, self.tr("%v/%m Modules"), self.parent())
        progress.setWindowTitle(self.tr("Package Diagram"))
        try:
            prog = 0
            progress.show()
            QApplication.processEvents()
            
            for module in modules:
                progress.setValue(prog)
                QApplication.processEvents()
                prog += 1
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
    
    def __buildSubpackagesDict(self):
        """
        Private method to build a dictionary of sub-packages contained in this
        package.
        
        @return dictionary of sub-packages contained in this package
        """
        import Utilities.ModuleParser
        
        supportedExt = \
            ['*{0}'.format(ext) for ext in
             Preferences.getPython("PythonExtensions")] + \
            ['*{0}'.format(ext) for ext in
             Preferences.getPython("Python3Extensions")] + \
            ['*.rb']
        extensions = Preferences.getPython("PythonExtensions") + \
            Preferences.getPython("Python3Extensions") + ['.rb']
        
        subpackagesDict = {}
        subpackagesList = []
        
        for subpackage in os.listdir(self.package):
            subpackagePath = os.path.join(self.package, subpackage)
            if os.path.isdir(subpackagePath) and \
               subpackage != "__pycache__" and \
               len(glob.glob(os.path.join(subpackagePath, "__init__.*"))) != 0:
                subpackagesList.append(subpackagePath)
        
        tot = 0
        for ext in supportedExt:
            for subpackage in subpackagesList:
                tot += len(glob.glob(Utilities.normjoinpath(subpackage, ext)))
        progress = E5ProgressDialog(
            self.tr("Parsing modules..."),
            None, 0, tot, self.tr("%v/%m Modules"), self.parent())
        progress.setWindowTitle(self.tr("Package Diagram"))
        try:
            prog = 0
            progress.show()
            QApplication.processEvents()
            
            for subpackage in subpackagesList:
                packageName = os.path.basename(subpackage)
                subpackagesDict[packageName] = []
                modules = []
                for ext in supportedExt:
                    modules.extend(glob.glob(
                        Utilities.normjoinpath(subpackage, ext)))
                for module in modules:
                    progress.setValue(prog)
                    QApplication.processEvents()
                    prog += 1
                    try:
                        mod = Utilities.ModuleParser.readModule(
                            module, extensions=extensions, caching=False)
                    except ImportError:
                        continue
                    else:
                        name = mod.name
                        if "." in name:
                            name = name.rsplit(".", 1)[1]
                        subpackagesDict[packageName].append(name)
                subpackagesDict[packageName].sort()
                # move __init__ to the front
                if "__init__" in subpackagesDict[packageName]:
                    subpackagesDict[packageName].remove("__init__")
                    subpackagesDict[packageName].insert(0, "__init__")
        finally:
            progress.setValue(tot)
            progress.deleteLater()
        return subpackagesDict
    
    def buildDiagram(self):
        """
        Public method to build the class shapes of the package diagram.
        
        The algorithm is borrowed from Boa Constructor.
        """
        self.allClasses = {}
        
        initlist = glob.glob(os.path.join(self.package, '__init__.*'))
        if len(initlist) == 0:
            ct = QGraphicsTextItem(None)
            self.scene.addItem(ct)
            ct.setHtml(
                self.tr("The directory <b>'{0}'</b> is not a package.")
                    .format(self.package))
            return
        
        modules = self.__buildModulesDict()
        if not modules:
            ct = QGraphicsTextItem(None)
            self.scene.addItem(ct)
            ct.setHtml(
                self.tr(
                    "The package <b>'{0}'</b> does not contain any modules.")
                .format(self.package))
            return
            
        # step 1: build all classes found in the modules
        classesFound = False
        
        for modName in list(modules.keys()):
            module = modules[modName]
            for cls in list(module.classes.keys()):
                classesFound = True
                self.__addLocalClass(cls, module.classes[cls], 0, 0)
        if not classesFound:
            ct = QGraphicsTextItem(None)
            self.scene.addItem(ct)
            ct.setHtml(
                self.tr(
                    "The package <b>'{0}'</b> does not contain any classes.")
                .format(self.package))
            return
        
        # step 2: build the class hierarchies
        routes = []
        nodes = []
        
        for modName in list(modules.keys()):
            module = modules[modName]
            todo = [module.createHierarchy()]
            while todo:
                hierarchy = todo[0]
                for className in list(hierarchy.keys()):
                    cw = self.__getCurrentShape(className)
                    if not cw and className.find('.') >= 0:
                        cw = self.__getCurrentShape(className.split('.')[-1])
                        if cw:
                            self.allClasses[className] = cw
                    if cw and cw.noAttrs != self.noAttrs:
                        cw = None
                    if cw and not (cw.external and
                                   (className in module.classes or
                                    className in module.modules)
                                   ):
                        if className not in nodes:
                            nodes.append(className)
                    else:
                        if className in module.classes:
                            # this is a local class (defined in this module)
                            self.__addLocalClass(
                                className, module.classes[className],
                                0, 0)
                        elif className in module.modules:
                            # this is a local module (defined in this module)
                            self.__addLocalClass(
                                className, module.modules[className],
                                0, 0, True)
                        else:
                            self.__addExternalClass(className, 0, 0)
                        nodes.append(className)
                    
                    if hierarchy.get(className):
                        todo.append(hierarchy.get(className))
                        children = list(hierarchy.get(className).keys())
                        for child in children:
                            if (className, child) not in routes:
                                routes.append((className, child))
                
                del todo[0]
        
        # step 3: build the subpackages
        subpackages = self.__buildSubpackagesDict()
        for subpackage in sorted(subpackages.keys()):
            self.__addPackage(subpackage, subpackages[subpackage], 0, 0)
            nodes.append(subpackage)
        
        self.__arrangeClasses(nodes, routes[:])
        self.__createAssociations(routes)
        self.umlView.autoAdjustSceneSize(limit=True)
    
    def __arrangeClasses(self, nodes, routes, whiteSpaceFactor=1.2):
        """
        Private method to arrange the shapes on the canvas.
        
        The algorithm is borrowed from Boa Constructor.
        
        @param nodes list of nodes to arrange
        @param routes list of routes
        @param whiteSpaceFactor factor to increase whitespace between
            items (float)
        """
        from . import GraphicsUtilities
        generations = GraphicsUtilities.sort(nodes, routes)
        
        # calculate width and height of all elements
        sizes = []
        for generation in generations:
            sizes.append([])
            for child in generation:
                sizes[-1].append(
                    self.__getCurrentShape(child).sceneBoundingRect())
                
        # calculate total width and total height
        width = 0
        height = 0
        widths = []
        heights = []
        for generation in sizes:
            currentWidth = 0
            currentHeight = 0
            
            for rect in generation:
                if rect.bottom() > currentHeight:
                    currentHeight = rect.bottom()
                currentWidth = currentWidth + rect.right()
                
            # update totals
            if currentWidth > width:
                width = currentWidth
            height = height + currentHeight
            
            # store generation info
            widths.append(currentWidth)
            heights.append(currentHeight)
            
        # add in some whitespace
        width = width * whiteSpaceFactor
##        rawHeight = height
        height = height * whiteSpaceFactor - 20
##        verticalWhiteSpace = max(
##            (height - rawHeight) / (len(generations) - 1.0 or 2.0),
##            40.0
##        )
        verticalWhiteSpace = 40.0
        
        sceneRect = self.umlView.sceneRect()
        width += 50.0
        height += 50.0
        swidth = width < sceneRect.width() and sceneRect.width() or width
        sheight = height < sceneRect.height() and sceneRect.height() or height
        self.umlView.setSceneSize(swidth, sheight)
        
        # distribute each generation across the width and the
        # generations across height
        y = 10.0
        for currentWidth, currentHeight, generation in \
                zip_longest(widths, heights, generations):
            x = 10.0
            # whiteSpace is the space between any two elements
            whiteSpace = (width - currentWidth - 20) / \
                (len(generation) - 1.0 or 2.0)
            for className in generation:
                cw = self.__getCurrentShape(className)
                cw.setPos(x, y)
                rect = cw.sceneBoundingRect()
                x = x + rect.width() + whiteSpace
            y = y + currentHeight + verticalWhiteSpace
    
    def __addLocalClass(self, className, _class, x, y, isRbModule=False):
        """
        Private method to add a class defined in the module.
        
        @param className name of the class to be as a dictionary key (string)
        @param _class class to be shown (ModuleParser.Class)
        @param x x-coordinate (float)
        @param y y-coordinate (float)
        @param isRbModule flag indicating a Ruby module (boolean)
        """
        from .ClassItem import ClassItem, ClassModel
        meths = sorted(_class.methods.keys())
        attrs = sorted(_class.attributes.keys())
        name = _class.name
        if isRbModule:
            name = "{0} (Module)".format(name)
        cl = ClassModel(name, meths[:], attrs[:])
        cw = ClassItem(cl, False, x, y, noAttrs=self.noAttrs, scene=self.scene)
        cw.setId(self.umlView.getItemId())
        self.allClasses[className] = cw
    
    def __addExternalClass(self, _class, x, y):
        """
        Private method to add a class defined outside the module.
        
        If the canvas is too small to take the shape, it
        is enlarged.
        
        @param _class class to be shown (string)
        @param x x-coordinate (float)
        @param y y-coordinate (float)
        """
        from .ClassItem import ClassItem, ClassModel
        cl = ClassModel(_class)
        cw = ClassItem(cl, True, x, y, noAttrs=self.noAttrs, scene=self.scene)
        cw.setId(self.umlView.getItemId())
        self.allClasses[_class] = cw
    
    def __addPackage(self, name, modules, x, y):
        """
        Private method to add a package to the diagram.
        
        @param name package name to be shown (string)
        @param modules list of module names contained in the package
            (list of strings)
        @param x x-coordinate (float)
        @param y y-coordinate (float)
        """
        from .PackageItem import PackageItem, PackageModel
        pm = PackageModel(name, modules)
        pw = PackageItem(pm, x, y, scene=self.scene)
        pw.setId(self.umlView.getItemId())
        self.allClasses[name] = pw
    
    def __createAssociations(self, routes):
        """
        Private method to generate the associations between the class shapes.
        
        @param routes list of relationsships
        """
        from .AssociationItem import AssociationItem, Generalisation
        for route in routes:
            if len(route) > 1:
                assoc = AssociationItem(
                    self.__getCurrentShape(route[1]),
                    self.__getCurrentShape(route[0]),
                    Generalisation,
                    topToBottom=True)
                self.scene.addItem(assoc)
    
    def getPersistenceData(self):
        """
        Public method to get a string for data to be persisted.
        
        @return persisted data string (string)
        """
        return "package={0}, no_attributes={1}".format(
            self.package, self.noAttrs)
    
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
           not parts[1].startswith("no_attributes="):
            return False
        
        self.package = parts[0].split("=", 1)[1].strip()
        self.noAttrs = Utilities.toBool(parts[1].split("=", 1)[1].strip())
        
        self.initialize()
        
        return True
