# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a package item.
"""

from __future__ import unicode_literals

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QStyle

from .UMLItem import UMLModel, UMLItem

import Utilities


class PackageModel(UMLModel):
    """
    Class implementing the package model.
    """
    def __init__(self, name, moduleslist=[]):
        """
        Constructor
        
        @param name package name (string)
        @param moduleslist list of module names (list of strings)
        """
        super(PackageModel, self).__init__(name)
        
        self.moduleslist = moduleslist
    
    def addModule(self, modulename):
        """
        Public method to add a module to the package model.
        
        @param modulename module name to be added (string)
        """
        self.moduleslist.append(modulename)
    
    def getModules(self):
        """
        Public method to retrieve the modules of the package.
        
        @return list of module names (list of strings)
        """
        return self.moduleslist[:]


class PackageItem(UMLItem):
    """
    Class implementing a package item.
    """
    ItemType = "package"
    
    def __init__(self, model=None, x=0, y=0, rounded=False,
                 noModules=False, parent=None, scene=None):
        """
        Constructor
        
        @param model package model containing the package data (PackageModel)
        @param x x-coordinate (integer)
        @param y y-coordinate (integer)
        @param rounded flag indicating a rounded corner (boolean)
        @keyparam noModules flag indicating, that no module names should be
            shown (boolean)
        @keyparam parent reference to the parent object (QGraphicsItem)
        @keyparam scene reference to the scene object (QGraphicsScene)
        """
        UMLItem.__init__(self, model, x, y, rounded, parent)
        self.noModules = noModules
        
        scene.addItem(self)
        
        if self.model:
            self.__createTexts()
            self.__calculateSize()
        
    def __createTexts(self):
        """
        Private method to create the text items of the class item.
        """
        if self.model is None:
            return
        
        boldFont = QFont(self.font)
        boldFont.setBold(True)
        
        modules = self.model.getModules()
        
        x = self.margin + self.rect().x()
        y = self.margin + self.rect().y()
        self.header = QGraphicsSimpleTextItem(self)
        self.header.setFont(boldFont)
        self.header.setText(self.model.getName())
        self.header.setPos(x, y)
        y += self.header.boundingRect().height() + self.margin
        
        if not self.noModules:
            if modules:
                txt = "\n".join(modules)
            else:
                txt = " "
            self.modules = QGraphicsSimpleTextItem(self)
            self.modules.setFont(self.font)
            self.modules.setText(txt)
            self.modules.setPos(x, y)
        else:
            self.modules = None
        
    def __calculateSize(self):
        """
        Private method to calculate the size of the package widget.
        """
        if self.model is None:
            return
        
        width = self.header.boundingRect().width()
        height = self.header.boundingRect().height()
        if self.modules:
            width = max(width, self.modules.boundingRect().width())
            height = height + self.modules.boundingRect().height()
        latchW = width / 3.0
        latchH = min(15.0, latchW)
        self.setSize(width + 2 * self.margin,
                     height + latchH + 2 * self.margin)
        
        x = self.margin + self.rect().x()
        y = self.margin + self.rect().y() + latchH
        self.header.setPos(x, y)
        y += self.header.boundingRect().height() + self.margin
        if self.modules:
            self.modules.setPos(x, y)
       
    def setModel(self, model):
        """
        Public method to set the package model.
        
        @param model package model containing the package data (PackageModel)
        """
        self.scene().removeItem(self.header)
        self.header = None
        if self.modules:
            self.scene().removeItem(self.modules)
            self.modules = None
        self.model = model
        self.__createTexts()
        self.__calculateSize()
        
    def paint(self, painter, option, widget=None):
        """
        Public method to paint the item in local coordinates.
        
        @param painter reference to the painter object (QPainter)
        @param option style options (QStyleOptionGraphicsItem)
        @param widget optional reference to the widget painted on (QWidget)
        """
        pen = self.pen()
        if (option.state & QStyle.State_Selected) == \
                QStyle.State(QStyle.State_Selected):
            pen.setWidth(2)
        else:
            pen.setWidth(1)
        
        offsetX = self.rect().x()
        offsetY = self.rect().y()
        w = self.rect().width()
        latchW = w / 3.0
        latchH = min(15.0, latchW)
        h = self.rect().height() - latchH + 1
        
        painter.setPen(pen)
        painter.setBrush(self.brush())
        painter.setFont(self.font)
        
        painter.drawRect(offsetX, offsetY, latchW, latchH)
        painter.drawRect(offsetX, offsetY + latchH, w, h)
        y = self.margin + self.header.boundingRect().height() + latchH
        painter.drawLine(offsetX, offsetY + y, offsetX + w - 1, offsetY + y)
        
        self.adjustAssociations()
    
    def buildItemDataString(self):
        """
        Public method to build a string to persist the specific item data.
        
        This string must start with ", " and should be built like
        "attribute=value" with pairs separated by ", ". value must not
        contain ", " or newlines.
        
        @return persistence data (string)
        """
        entries = [
            "no_modules={0}".format(self.noModules),
            "name={0}".format(self.model.getName()),
        ]
        modules = self.model.getModules()
        if modules:
            entries.append("modules={0}".format("||".join(modules)))
        
        return ", " + ", ".join(entries)
    
    def parseItemDataString(self, version, data):
        """
        Public method to parse the given persistence data.
        
        @param version version of the data (string)
        @param data persisted data to be parsed (string)
        @return flag indicating success (boolean)
        """
        parts = data.split(", ")
        if len(parts) < 2:
            return False
        
        name = ""
        modules = []
        
        for part in parts:
            key, value = part.split("=", 1)
            if key == "no_modules":
                self.external = Utilities.toBool(value.strip())
            elif key == "name":
                name = value.strip()
            elif key == "modules":
                modules = value.strip().split("||")
            else:
                return False
        
        self.model = PackageModel(name, modules)
        self.__createTexts()
        self.__calculateSize()
        
        return True
