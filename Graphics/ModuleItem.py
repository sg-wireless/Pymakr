# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a module item.
"""

from __future__ import unicode_literals

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QStyle

from .UMLItem import UMLModel, UMLItem


class ModuleModel(UMLModel):
    """
    Class implementing the module model.
    """
    def __init__(self, name, classlist=[]):
        """
        Constructor
        
        @param name the module name (string)
        @param classlist list of class names (list of strings)
        """
        super(ModuleModel, self).__init__(name)
        
        self.classlist = classlist
    
    def addClass(self, classname):
        """
        Public method to add a class to the module model.
        
        @param classname class name to be added (string)
        """
        self.classlist.append(classname)
    
    def getClasses(self):
        """
        Public method to retrieve the classes of the module.
        
        @return list of class names (list of strings)
        """
        return self.classlist[:]


class ModuleItem(UMLItem):
    """
    Class implementing a module item.
    """
    ItemType = "module"
    
    def __init__(self, model=None, x=0, y=0, rounded=False,
                 parent=None, scene=None):
        """
        Constructor
        
        @param model module model containing the module data (ModuleModel)
        @param x x-coordinate (integer)
        @param y y-coordinate (integer)
        @keyparam rounded flag indicating a rounded corner (boolean)
        @keyparam parent reference to the parent object (QGraphicsItem)
        @keyparam scene reference to the scene object (QGraphicsScene)
        """
        UMLItem.__init__(self, model, x, y, rounded, parent)
        
        scene.addItem(self)
        
        if self.model:
            self.__createTexts()
            self.__calculateSize()
        
    def __createTexts(self):
        """
        Private method to create the text items of the module item.
        """
        if self.model is None:
            return
        
        boldFont = QFont(self.font)
        boldFont.setBold(True)
        
        classes = self.model.getClasses()
        
        x = self.margin + self.rect().x()
        y = self.margin + self.rect().y()
        self.header = QGraphicsSimpleTextItem(self)
        self.header.setFont(boldFont)
        self.header.setText(self.model.getName())
        self.header.setPos(x, y)
        y += self.header.boundingRect().height() + self.margin
        if classes:
            txt = "\n".join(classes)
        else:
            txt = " "
        self.classes = QGraphicsSimpleTextItem(self)
        self.classes.setFont(self.font)
        self.classes.setText(txt)
        self.classes.setPos(x, y)
        
    def __calculateSize(self):
        """
        Private method to calculate the size of the module item.
        """
        if self.model is None:
            return
        
        width = self.header.boundingRect().width()
        height = self.header.boundingRect().height()
        if self.classes:
            width = max(width, self.classes.boundingRect().width())
            height = height + self.classes.boundingRect().height()
        self.setSize(width + 2 * self.margin, height + 2 * self.margin)
    
    def setModel(self, model):
        """
        Public method to set the module model.
        
        @param model module model containing the module data (ModuleModel)
        """
        self.scene().removeItem(self.header)
        self.header = None
        if self.classes:
            self.scene().removeItem(self.classes)
            self.meths = None
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
        
        painter.setPen(pen)
        painter.setBrush(self.brush())
        painter.setFont(self.font)
        
        offsetX = self.rect().x()
        offsetY = self.rect().y()
        w = self.rect().width()
        h = self.rect().height()
        
        painter.drawRect(offsetX, offsetY, w, h)
        y = self.margin + self.header.boundingRect().height()
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
            "name={0}".format(self.model.getName()),
        ]
        classes = self.model.getClasses()
        if classes:
            entries.append("classes={0}".format("||".join(classes)))
        
        return ", " + ", ".join(entries)
    
    def parseItemDataString(self, version, data):
        """
        Public method to parse the given persistence data.
        
        @param version version of the data (string)
        @param data persisted data to be parsed (string)
        @return flag indicating success (boolean)
        """
        parts = data.split(", ")
        if len(parts) < 1:
            return False
        
        name = ""
        classes = []
        
        for part in parts:
            key, value = part.split("=", 1)
            if key == "name":
                name = value.strip()
            elif key == "classes":
                classes = value.strip().split("||")
            else:
                return False
        
        self.model = ModuleModel(name, classes)
        self.__createTexts()
        self.__calculateSize()
        
        return True
