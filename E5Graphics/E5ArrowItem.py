# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a graphics item subclass for an arrow.
"""

from __future__ import unicode_literals

import math

from PyQt5.QtCore import QPointF, QRectF, QSizeF, QLineF, Qt
from PyQt5.QtGui import QPen, QPolygonF
from PyQt5.QtWidgets import QAbstractGraphicsShapeItem, QGraphicsItem, QStyle

NormalArrow = 1
WideArrow = 2

ArrowheadAngleFactor = 0.26179938779914941
# 0.5 * math.atan(math.sqrt(3.0) / 3.0)


class E5ArrowItem(QAbstractGraphicsShapeItem):
    """
    Class implementing an arrow graphics item subclass.
    """
    def __init__(self, origin=QPointF(), end=QPointF(),
                 filled=False, type=NormalArrow, parent=None):
        """
        Constructor
        
        @param origin origin of the arrow (QPointF)
        @param end end point of the arrow (QPointF)
        @param filled flag indicating a filled arrow head (boolean)
        @param type arrow type (NormalArrow, WideArrow)
        @keyparam parent reference to the parent object (QGraphicsItem)
        """
        super(E5ArrowItem, self).__init__(parent)
        
        self._origin = origin
        self._end = end
        self._filled = filled
        self._type = type
        
        self._halfLength = 13.0
        
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
    def setPoints(self, xa, ya, xb, yb):
        """
        Public method to set the start and end points of the line.
        
        <b>Note:</b> This method does not redraw the item.
        
        @param xa x-coordinate of the start point (float)
        @param ya y-coordinate of the start point (float)
        @param xb x-coordinate of the end point (float)
        @param yb y-coordinate of the end point (float)
        """
        self._origin = QPointF(xa, ya)
        self._end = QPointF(xb, yb)
        
    def setStartPoint(self, x, y):
        """
        Public method to set the start point.
        
        <b>Note:</b> This method does not redraw the item.
        
        @param x x-coordinate of the start point (float)
        @param y y-coordinate of the start point (float)
        """
        self._origin = QPointF(x, y)
        
    def setEndPoint(self, x, y):
        """
        Public method to set the end point.
        
        <b>Note:</b> This method does not redraw the item.
        
        @param x x-coordinate of the end point (float)
        @param y y-coordinate of the end point (float)
        """
        self._end = QPointF(x, y)
        
    def boundingRect(self):
        """
        Public method to return the bounding rectangle.
        
        @return bounding rectangle (QRectF)
        """
        extra = self._halfLength / 2.0
        return QRectF(self._origin, QSizeF(self._end.x() - self._origin.x(),
                                           self._end.y() - self._origin.y()))\
            .normalized()\
            .adjusted(-extra, -extra, extra, extra)
        
    def paint(self, painter, option, widget=None):
        """
        Public method to paint the item in local coordinates.
        
        @param painter reference to the painter object (QPainter)
        @param option style options (QStyleOptionGraphicsItem)
        @param widget optional reference to the widget painted on (QWidget)
        """
        if (option.state & QStyle.State_Selected) == \
                QStyle.State(QStyle.State_Selected):
            width = 2
        else:
            width = 1
        
        # draw the line first
        line = QLineF(self._origin, self._end)
        painter.setPen(
            QPen(Qt.black, width, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin))
        painter.drawLine(line)
        
        # draw the arrow head
        arrowAngle = self._type * ArrowheadAngleFactor
        slope = math.atan2(line.dy(), line.dx())
        
        # Calculate left arrow point
        arrowSlope = slope + arrowAngle
        a1 = QPointF(self._end.x() - self._halfLength * math.cos(arrowSlope),
                     self._end.y() - self._halfLength * math.sin(arrowSlope))
        
        # Calculate right arrow point
        arrowSlope = slope - arrowAngle
        a2 = QPointF(self._end.x() - self._halfLength * math.cos(arrowSlope),
                     self._end.y() - self._halfLength * math.sin(arrowSlope))
        
        if self._filled:
            painter.setBrush(Qt.black)
        else:
            painter.setBrush(Qt.white)
        polygon = QPolygonF()
        polygon.append(line.p2())
        polygon.append(a1)
        polygon.append(a2)
        painter.drawPolygon(polygon)
