# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an UML like class item.
"""

from __future__ import unicode_literals

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QStyle

from .UMLItem import UMLModel, UMLItem

import Utilities


class ClassModel(UMLModel):
    """
    Class implementing the class model.
    """
    def __init__(self, name, methods=[], attributes=[]):
        """
        Constructor
        
        @param name the class name (string)
        @param methods list of method names of the class
            (list of strings)
        @param attributes list of attribute names of the class
            (list of strings)
        """
        super(ClassModel, self).__init__(name)
        
        self.methods = methods
        self.attributes = attributes
    
    def addMethod(self, method):
        """
        Public method to add a method to the class model.
        
        @param method method name to be added (string)
        """
        self.methods.append(method)
    
    def addAttribute(self, attribute):
        """
        Public method to add an attribute to the class model.
        
        @param attribute attribute name to be added (string)
        """
        self.attributes.append(attribute)
    
    def getMethods(self):
        """
        Public method to retrieve the methods of the class.
        
        @return list of class methods (list of strings)
        """
        return self.methods[:]
    
    def getAttributes(self):
        """
        Public method to retrieve the attributes of the class.
        
        @return list of class attributes (list of strings)
        """
        return self.attributes[:]
    

class ClassItem(UMLItem):
    """
    Class implementing an UML like class item.
    """
    ItemType = "class"
    
    def __init__(self, model=None, external=False, x=0, y=0,
                 rounded=False, noAttrs=False, parent=None, scene=None):
        """
        Constructor
        
        @param model class model containing the class data (ClassModel)
        @param external flag indicating a class defined outside our scope
            (boolean)
        @param x x-coordinate (integer)
        @param y y-coordinate (integer)
        @keyparam rounded flag indicating a rounded corner (boolean)
        @keyparam noAttrs flag indicating, that no attributes should be shown
            (boolean)
        @keyparam parent reference to the parent object (QGraphicsItem)
        @keyparam scene reference to the scene object (QGraphicsScene)
        """
        UMLItem.__init__(self, model, x, y, rounded, parent)
        
        self.external = external
        self.noAttrs = noAttrs
        
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
        
        attrs = self.model.getAttributes()
        meths = self.model.getMethods()
        
        x = self.margin + self.rect().x()
        y = self.margin + self.rect().y()
        self.header = QGraphicsSimpleTextItem(self)
        self.header.setFont(boldFont)
        self.header.setText(self.model.getName())
        self.header.setPos(x, y)
        y += self.header.boundingRect().height() + self.margin
        if not self.noAttrs and not self.external:
            if attrs:
                txt = "\n".join(attrs)
            else:
                txt = " "
            self.attrs = QGraphicsSimpleTextItem(self)
            self.attrs.setFont(self.font)
            self.attrs.setText(txt)
            self.attrs.setPos(x, y)
            y += self.attrs.boundingRect().height() + self.margin
        else:
            self.attrs = None
        if meths:
            txt = "\n".join(meths)
        else:
            txt = " "
        self.meths = QGraphicsSimpleTextItem(self)
        self.meths.setFont(self.font)
        self.meths.setText(txt)
        self.meths.setPos(x, y)
        
    def __calculateSize(self):
        """
        Private method to calculate the size of the class item.
        """
        if self.model is None:
            return
        
        width = self.header.boundingRect().width()
        height = self.header.boundingRect().height()
        if self.attrs:
            width = max(width, self.attrs.boundingRect().width())
            height = height + self.attrs.boundingRect().height() + self.margin
        if self.meths:
            width = max(width, self.meths.boundingRect().width())
            height = height + self.meths.boundingRect().height()
        self.setSize(width + 2 * self.margin, height + 2 * self.margin)
        
    def setModel(self, model):
        """
        Public method to set the class model.
        
        @param model class model containing the class data (ClassModel)
        """
        self.scene().removeItem(self.header)
        self.header = None
        if self.attrs:
            self.scene().removeItem(self.attrs)
            self.attrs = None
        if self.meths:
            self.scene().removeItem(self.meths)
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
        if self.attrs:
            y += self.margin + self.attrs.boundingRect().height()
            painter.drawLine(offsetX, offsetY + y,
                             offsetX + w - 1, offsetY + y)
        
        self.adjustAssociations()
        
    def isExternal(self):
        """
        Public method returning the external state.
        
        @return external state (boolean)
        """
        return self.external
    
    def buildItemDataString(self):
        """
        Public method to build a string to persist the specific item data.
        
        This string must start with ", " and should be built like
        "attribute=value" with pairs separated by ", ". value must not
        contain ", " or newlines.
        
        @return persistence data (string)
        """
        entries = [
            "is_external={0}".format(self.external),
            "no_attributes={0}".format(self.noAttrs),
            "name={0}".format(self.model.getName()),
        ]
        attributes = self.model.getAttributes()
        if attributes:
            entries.append("attributes={0}".format("||".join(attributes)))
        methods = self.model.getMethods()
        if methods:
            entries.append("methods={0}".format("||".join(methods)))
        
        return ", " + ", ".join(entries)
    
    def parseItemDataString(self, version, data):
        """
        Public method to parse the given persistence data.
        
        @param version version of the data (string)
        @param data persisted data to be parsed (string)
        @return flag indicating success (boolean)
        """
        parts = data.split(", ")
        if len(parts) < 3:
            return False
        
        name = ""
        attributes = []
        methods = []
        
        for part in parts:
            key, value = part.split("=", 1)
            if key == "is_external":
                self.external = Utilities.toBool(value.strip())
            elif key == "no_attributes":
                self.noAttrs = Utilities.toBool(value.strip())
            elif key == "name":
                name = value.strip()
            elif key == "attributes":
                attributes = value.strip().split("||")
            elif key == "methods":
                methods = value.strip().split("||")
            else:
                return False
        
        self.model = ClassModel(name, methods, attributes)
        self.__createTexts()
        self.__calculateSize()
        
        return True
