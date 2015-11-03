# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the UMLItem base class.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QSizeF
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, QStyle

import Preferences


class UMLModel(object):
    """
    Class implementing the UMLModel base class.
    """
    def __init__(self, name):
        """
        Constructor
        
        @param name package name (string)
        """
        self.name = name
    
    def getName(self):
        """
        Public method to retrieve the model name.
        
        @return model name (string)
        """
        return self.name


class UMLItem(QGraphicsRectItem):
    """
    Class implementing the UMLItem base class.
    """
    ItemType = "UMLItem"
    
    def __init__(self, model=None, x=0, y=0, rounded=False, parent=None):
        """
        Constructor
        
        @param model UML model containing the item data (UMLModel)
        @param x x-coordinate (integer)
        @param y y-coordinate (integer)
        @param rounded flag indicating a rounded corner (boolean)
        @keyparam parent reference to the parent object (QGraphicsItem)
        """
        super(UMLItem, self).__init__(parent)
        self.model = model
        
        self.font = Preferences.getGraphics("Font")
        self.margin = 5
        self.associations = []
        self.shouldAdjustAssociations = False
        self.__id = -1
        
        self.setRect(x, y, 60, 30)
        
        if rounded:
            p = self.pen()
            p.setCapStyle(Qt.RoundCap)
            p.setJoinStyle(Qt.RoundJoin)
        
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        try:
            self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        except AttributeError:
            # only available for Qt 4.6.0 and newer
            pass
    
    def getName(self):
        """
        Public method to retrieve the item name.
        
        @return item name (string)
        """
        if self.model:
            return self.model.name
        else:
            return ""
    
    def setSize(self, width, height):
        """
        Public method to set the rectangles size.
        
        @param width width of the rectangle (float)
        @param height height of the rectangle (float)
        """
        rect = self.rect()
        rect.setSize(QSizeF(width, height))
        self.setRect(rect)
    
    def addAssociation(self, assoc):
        """
        Public method to add an association to this widget.
        
        @param assoc association to be added (AssociationWidget)
        """
        if assoc and assoc not in self.associations:
            self.associations.append(assoc)
    
    def removeAssociation(self, assoc):
        """
        Public method to remove an association to this widget.
        
        @param assoc association to be removed (AssociationWidget)
        """
        if assoc and assoc in self.associations:
            self.associations.remove(assoc)
    
    def removeAssociations(self):
        """
        Public method to remove all associations of this widget.
        """
        for assoc in self.associations[:]:
            assoc.unassociate()
            assoc.hide()
            del assoc
    
    def adjustAssociations(self):
        """
        Public method to adjust the associations to widget movements.
        """
        if self.shouldAdjustAssociations:
            for assoc in self.associations:
                assoc.widgetMoved()
            self.shouldAdjustAssociations = False
    
    def moveBy(self, dx, dy):
        """
        Public overriden method to move the widget relative.
        
        @param dx relative movement in x-direction (float)
        @param dy relative movement in y-direction (float)
        """
        super(UMLItem, self).moveBy(dx, dy)
        self.adjustAssociations()
    
    def setPos(self, x, y):
        """
        Public overriden method to set the items position.
        
        @param x absolute x-position (float)
        @param y absolute y-position (float)
        """
        super(UMLItem, self).setPos(x, y)
        self.adjustAssociations()
    
    def itemChange(self, change, value):
        """
        Public method called when an items state changes.
        
        @param change the item's change (QGraphicsItem.GraphicsItemChange)
        @param value the value of the change
        @return adjusted values
        """
        if change == QGraphicsItem.ItemPositionChange:
            # 1. remember to adjust associations
            self.shouldAdjustAssociations = True
            
            # 2. ensure the new position is inside the scene
            rect = self.scene().sceneRect()
            if not rect.contains(value):
                # keep the item inside the scene
                value.setX(min(rect.right(), max(value.x(), rect.left())))
                value.setY(min(rect.bottom(), max(value.y(), rect.top())))
                return value
            
        return QGraphicsItem.itemChange(self, change, value)
    
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
        painter.drawRect(self.rect())
        self.adjustAssociations()
    
    def setId(self, id):
        """
        Public method to assign an ID to the item.
        
        @param id assigned ID (integer)
        """
        self.__id = id
    
    def getId(self):
        """
        Public method to get the item ID.
        
        @return ID of the item (integer)
        """
        return self.__id
    
    def getItemType(self):
        """
        Public method to get the item's type.
        
        @return item type (string)
        """
        return self.ItemType
    
    def buildItemDataString(self):
        """
        Public method to build a string to persist the specific item data.
        
        This string must start with ", " and should be built like
        "attribute=value" with pairs separated by ", ". value must not
        contain ", " or newlines.
        
        @return persistence data (string)
        """
        return ""
    
    def parseItemDataString(self, version, data):
        """
        Public method to parse the given persistence data.
        
        @param version version of the data (string)
        @param data persisted data to be parsed (string)
        @return flag indicating success (boolean)
        """
        return True
