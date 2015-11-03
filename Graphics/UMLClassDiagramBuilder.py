# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog showing a UML like class diagram.
"""

from __future__ import unicode_literals
try:  # Py3
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest    # __IGNORE_WARNING__

from PyQt5.QtWidgets import QGraphicsTextItem

import Utilities
import Preferences

from .UMLDiagramBuilder import UMLDiagramBuilder


class UMLClassDiagramBuilder(UMLDiagramBuilder):
    """
    Class implementing a builder for UML like class diagrams.
    """
    def __init__(self, dialog, view, project, file, noAttrs=False):
        """
        Constructor
        
        @param dialog reference to the UML dialog (UMLDialog)
        @param view reference to the view object (UMLGraphicsView)
        @param project reference to the project object (Project)
        @param file file name of a python module to be shown (string)
        @keyparam noAttrs flag indicating, that no attributes should be shown
            (boolean)
        """
        super(UMLClassDiagramBuilder, self).__init__(dialog, view, project)
        self.setObjectName("UMLClassDiagramBuilder")
        
        self.file = file
        self.noAttrs = noAttrs
    
    def initialize(self):
        """
        Public method to initialize the object.
        """
        pname = self.project.getProjectName()
        if pname and self.project.isProjectSource(self.file):
            name = self.tr("Class Diagram {0}: {1}").format(
                pname, self.project.getRelativePath(self.file))
        else:
            name = self.tr("Class Diagram: {0}").format(self.file)
        self.umlView.setDiagramName(name)
        
    def __getCurrentShape(self, name):
        """
        Private method to get the named shape.
        
        @param name name of the shape (string)
        @return shape (QGraphicsItem)
        """
        return self.allClasses.get(name)
        
    def buildDiagram(self):
        """
        Public method to build the class shapes of the class diagram.
        
        The algorithm is borrowed from Boa Constructor.
        """
        import Utilities.ModuleParser
        
        self.allClasses = {}
        self.allModules = {}
        
        try:
            extensions = Preferences.getPython("PythonExtensions") + \
                Preferences.getPython("Python3Extensions") + ['.rb']
            module = Utilities.ModuleParser.readModule(
                self.file, extensions=extensions, caching=False)
        except ImportError:
            ct = QGraphicsTextItem(None)
            ct.setHtml(
                self.tr("The module <b>'{0}'</b> could not be found.")
                    .format(self.file))
            self.scene.addItem(ct)
            return
        
        if self.file not in self.allModules:
            self.allModules[self.file] = []
        
        routes = []
        nodes = []
        todo = [module.createHierarchy()]
        classesFound = False
        while todo:
            hierarchy = todo[0]
            for className in hierarchy:
                classesFound = True
                cw = self.__getCurrentShape(className)
                if not cw and className.find('.') >= 0:
                    cw = self.__getCurrentShape(className.split('.')[-1])
                    if cw:
                        self.allClasses[className] = cw
                        if className not in self.allModules[self.file]:
                            self.allModules[self.file].append(className)
                if cw and cw.noAttrs != self.noAttrs:
                    cw = None
                if cw and not (cw.external and
                               (className in module.classes or
                                className in module.modules)):
                    if cw.scene() != self.scene:
                        self.scene.addItem(cw)
                        cw.setPos(10, 10)
                        if className not in nodes:
                            nodes.append(className)
                else:
                    if className in module.classes:
                        # this is a local class (defined in this module)
                        self.__addLocalClass(
                            className, module.classes[className], 0, 0)
                    elif className in module.modules:
                        # this is a local module (defined in this module)
                        self.__addLocalClass(
                            className, module.modules[className], 0, 0, True)
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
        
        if classesFound:
            self.__arrangeClasses(nodes, routes[:])
            self.__createAssociations(routes)
            self.umlView.autoAdjustSceneSize(limit=True)
        else:
            ct = QGraphicsTextItem(None)
            ct.setHtml(self.tr(
                "The module <b>'{0}'</b> does not contain any classes.")
                .format(self.file))
            self.scene.addItem(ct)
        
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
        if _class.name not in self.allModules[self.file]:
            self.allModules[self.file].append(_class.name)
        
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
        if _class not in self.allModules[self.file]:
            self.allModules[self.file].append(_class)
        
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
        return "file={0}, no_attributes={1}".format(self.file, self.noAttrs)
    
    def parsePersistenceData(self, version, data):
        """
        Public method to parse persisted data.
        
        @param version version of the data (string)
        @param data persisted data to be parsed (string)
        @return flag indicating success (boolean)
        """
        parts = data.split(", ")
        if len(parts) != 2 or \
           not parts[0].startswith("file=") or \
           not parts[1].startswith("no_attributes="):
            return False
        
        self.file = parts[0].split("=", 1)[1].strip()
        self.noAttrs = Utilities.toBool(parts[1].split("=", 1)[1].strip())
        
        self.initialize()
        
        return True
