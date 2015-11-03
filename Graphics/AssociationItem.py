# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a graphics item for an association between two items.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QPointF, QRectF, QLineF
from PyQt5.QtWidgets import QGraphicsItem

from E5Graphics.E5ArrowItem import E5ArrowItem, NormalArrow, WideArrow

import Utilities


Normal = 0
Generalisation = 1
Imports = 2


NoRegion = 0
West = 1
North = 2
East = 3
South = 4
NorthWest = 5
NorthEast = 6
SouthEast = 7
SouthWest = 8
Center = 9


class AssociationItem(E5ArrowItem):
    """
    Class implementing a graphics item for an association between two items.
    
    The association is drawn as an arrow starting at the first items and
    ending at the second.
    """
    def __init__(self, itemA, itemB, type=Normal, topToBottom=False,
                 parent=None):
        """
        Constructor
        
        @param itemA first widget of the association
        @param itemB second widget of the association
        @param type type of the association. This must be one of
            <ul>
            <li>Normal (default)</li>
            <li>Generalisation</li>
            <li>Imports</li>
            </ul>
        @keyparam topToBottom flag indicating to draw the association
            from item A top to item B bottom (boolean)
        @keyparam parent reference to the parent object (QGraphicsItem)
        """
        if type == Normal:
            arrowType = NormalArrow
            arrowFilled = True
        elif type == Imports:
            arrowType = NormalArrow
            arrowFilled = True
        elif type == Generalisation:
            arrowType = WideArrow
            arrowFilled = False
        
        E5ArrowItem.__init__(self, QPointF(0, 0), QPointF(100, 100),
                             arrowFilled, arrowType, parent)
        
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        
        if topToBottom:
            self.calculateEndingPoints = \
                self.__calculateEndingPoints_topToBottom
        else:
            ## self.calculateEndingPoints = self.__calculateEndingPoints_center
            self.calculateEndingPoints = self.__calculateEndingPoints_rectangle
        
        self.itemA = itemA
        self.itemB = itemB
        self.assocType = type
        self.topToBottom = topToBottom
        
        self.regionA = NoRegion
        self.regionB = NoRegion
        
        self.calculateEndingPoints()
        
        self.itemA.addAssociation(self)
        self.itemB.addAssociation(self)
        
    def __mapRectFromItem(self, item):
        """
        Private method to map item's rectangle to this item's coordinate
        system.
        
        @param item reference to the item to be mapped (QGraphicsRectItem)
        @return item's rectangle in local coordinates (QRectF)
        """
        rect = item.rect()
        tl = self.mapFromItem(item, rect.topLeft())
        return QRectF(tl.x(), tl.y(), rect.width(), rect.height())
        
    def __calculateEndingPoints_topToBottom(self):
        """
        Private method to calculate the ending points of the association item.
        
        The ending points are calculated from the top center of the lower item
        to the bottom center of the upper item.
        """
        if self.itemA is None or self.itemB is None:
            return
        
        self.prepareGeometryChange()
        
        rectA = self.__mapRectFromItem(self.itemA)
        rectB = self.__mapRectFromItem(self.itemB)
        midA = QPointF(rectA.x() + rectA.width() / 2.0,
                       rectA.y() + rectA.height() / 2.0)
        midB = QPointF(rectB.x() + rectB.width() / 2.0,
                       rectB.y() + rectB.height() / 2.0)
        if midA.y() > midB.y():
            startP = QPointF(rectA.x() + rectA.width() / 2.0, rectA.y())
            endP = QPointF(rectB.x() + rectB.width() / 2.0,
                           rectB.y() + rectB.height())
        else:
            startP = QPointF(rectA.x() + rectA.width() / 2.0,
                             rectA.y() + rectA.height())
            endP = QPointF(rectB.x() + rectB.width() / 2.0, rectB.y())
        self.setPoints(startP.x(), startP.y(), endP.x(), endP.y())
    
    def __calculateEndingPoints_center(self):
        """
        Private method to calculate the ending points of the association item.
        
        The ending points are calculated from the centers of the
        two associated items.
        """
        if self.itemA is None or self.itemB is None:
            return
        
        self.prepareGeometryChange()
        
        rectA = self.__mapRectFromItem(self.itemA)
        rectB = self.__mapRectFromItem(self.itemB)
        midA = QPointF(rectA.x() + rectA.width() / 2.0,
                       rectA.y() + rectA.height() / 2.0)
        midB = QPointF(rectB.x() + rectB.width() / 2.0,
                       rectB.y() + rectB.height() / 2.0)
        startP = self.__findRectIntersectionPoint(self.itemA, midA, midB)
        endP = self.__findRectIntersectionPoint(self.itemB, midB, midA)
        
        if startP.x() != -1 and startP.y() != -1 and \
           endP.x() != -1 and endP.y() != -1:
            self.setPoints(startP.x(), startP.y(), endP.x(), endP.y())
        
    def __calculateEndingPoints_rectangle(self):
        r"""
        Private method to calculate the ending points of the association item.
        
        The ending points are calculated by the following method.
        
        For each item the diagram is divided in four Regions by its diagonals
        as indicated below
        <pre>
                   \  Region 2  /
                    \          /
                     |--------|
                     | \    / |
                     |  \  /  |
                     |   \/   |
            Region 1 |   /\   | Region 3
                     |  /  \  |
                     | /    \ |
                     |--------|
                    /          \
                   /  Region 4  \
        </pre>
        
        Each diagonal is defined by two corners of the bounding rectangle
        
        To calculate the start point  we have to find out in which
        region (defined by itemA's diagonals) is itemB's TopLeft corner
        (lets call it region M). After that the start point will be
        the middle point of rectangle's side contained in region M.
        
        To calculate the end point we repeat the above but in the opposite
        direction (from itemB to itemA)
        """
        if self.itemA is None or self.itemB is None:
            return
        
        self.prepareGeometryChange()
        
        rectA = self.__mapRectFromItem(self.itemA)
        rectB = self.__mapRectFromItem(self.itemB)
        
        xA = rectA.x() + rectA.width() / 2.0
        yA = rectA.y() + rectA.height() / 2.0
        xB = rectB.x() + rectB.width() / 2.0
        yB = rectB.y() + rectB.height() / 2.0
        
        # find itemA region
        rc = QRectF(xA, yA, rectA.width(), rectA.height())
        self.regionA = self.__findPointRegion(rc, xB, yB)
        # move some regions to the standard ones
        if self.regionA == NorthWest:
            self.regionA = North
        elif self.regionA == NorthEast:
            self.regionA = East
        elif self.regionA == SouthEast:
            self.regionA = South
        elif self.regionA == SouthWest:
            self.regionA = West
        elif self.regionA == Center:
            self.regionA = West
        
        self.__updateEndPoint(self.regionA, True)
        
        # now do the same for itemB
        rc = QRectF(xB, yB, rectB.width(), rectB.height())
        self.regionB = self.__findPointRegion(rc, xA, yA)
        # move some regions to the standard ones
        if self.regionB == NorthWest:
            self.regionB = North
        elif self.regionB == NorthEast:
            self.regionB = East
        elif self.regionB == SouthEast:
            self.regionB = South
        elif self.regionB == SouthWest:
            self.regionB = West
        elif self.regionB == Center:
            self.regionB = West
        
        self.__updateEndPoint(self.regionB, False)
        
    def __findPointRegion(self, rect, posX, posY):
        """
        Private method to find out, which region of rectangle rect contains
        the point (PosX, PosY) and returns the region number.
        
        @param rect rectangle to calculate the region for (QRectF)
        @param posX x position of point (float)
        @param posY y position of point (float)
        @return the calculated region number<br />
            West = Region 1<br />
            North = Region 2<br />
            East = Region 3<br />
            South = Region 4<br />
            NorthWest = On diagonal 2 between Region 1 and 2<br />
            NorthEast = On diagonal 1 between Region 2 and 3<br />
            SouthEast = On diagonal 2 between Region 3 and 4<br />
            SouthWest = On diagonal 1 between Region4 and 1<br />
            Center = On diagonal 1 and On diagonal 2 (the center)<br />
        """
        w = rect.width()
        h = rect.height()
        x = rect.x()
        y = rect.y()
        slope2 = w / h
        slope1 = -slope2
        b1 = x + w / 2.0 - y * slope1
        b2 = x + w / 2.0 - y * slope2
        
        eval1 = slope1 * posY + b1
        eval2 = slope2 * posY + b2
        
        result = NoRegion
        
        # inside region 1
        if eval1 > posX and eval2 > posX:
            result = West
        
        #inside region 2
        elif eval1 > posX and eval2 < posX:
            result = North
        
        # inside region 3
        elif eval1 < posX and eval2 < posX:
            result = East
        
        # inside region 4
        elif eval1 < posX and eval2 > posX:
            result = South
        
        # inside region 5
        elif eval1 == posX and eval2 < posX:
            result = NorthWest
        
        # inside region 6
        elif eval1 < posX and eval2 == posX:
            result = NorthEast
        
        # inside region 7
        elif eval1 == posX and eval2 > posX:
            result = SouthEast
        
        # inside region 8
        elif eval1 > posX and eval2 == posX:
            result = SouthWest
        
        # inside region 9
        elif eval1 == posX and eval2 == posX:
            result = Center
        
        return result
        
    def __updateEndPoint(self, region, isWidgetA):
        """
        Private method to update an endpoint.
        
        @param region the region for the endpoint (integer)
        @param isWidgetA flag indicating update for itemA is done (boolean)
        """
        if region == NoRegion:
            return
        
        if isWidgetA:
            rect = self.__mapRectFromItem(self.itemA)
        else:
            rect = self.__mapRectFromItem(self.itemB)
        x = rect.x()
        y = rect.y()
        ww = rect.width()
        wh = rect.height()
        ch = wh / 2.0
        cw = ww / 2.0
        
        if region == West:
            px = x
            py = y + ch
        elif region == North:
            px = x + cw
            py = y
        elif region == East:
            px = x + ww
            py = y + ch
        elif region == South:
            px = x + cw
            py = y + wh
        elif region == Center:
            px = x + cw
            py = y + wh
        
        if isWidgetA:
            self.setStartPoint(px, py)
        else:
            self.setEndPoint(px, py)
        
    def __findRectIntersectionPoint(self, item, p1, p2):
        """
        Private method to find the intersetion point of a line with a
        rectangle.
        
        @param item item to check against
        @param p1 first point of the line (QPointF)
        @param p2 second point of the line (QPointF)
        @return the intersection point (QPointF)
        """
        rect = self.__mapRectFromItem(item)
        lines = [
            QLineF(rect.topLeft(), rect.topRight()),
            QLineF(rect.topLeft(), rect.bottomLeft()),
            QLineF(rect.bottomRight(), rect.bottomLeft()),
            QLineF(rect.bottomRight(), rect.topRight())
        ]
        intersectLine = QLineF(p1, p2)
        intersectPoint = QPointF(0, 0)
        for line in lines:
            if intersectLine.intersect(line, intersectPoint) == \
               QLineF.BoundedIntersection:
                return intersectPoint
        return QPointF(-1.0, -1.0)
        
    def __findIntersection(self, p1, p2, p3, p4):
        """
        Private method to calculate the intersection point of two lines.
        
        The first line is determined by the points p1 and p2, the second
        line by p3 and p4. If the intersection point is not contained in
        the segment p1p2, then it returns (-1.0, -1.0).
        
        For the function's internal calculations remember:<br />
        QT coordinates start with the point (0,0) as the topleft corner
        and x-values increase from left to right and y-values increase
        from top to bottom; it means the visible area is quadrant I in
        the regular XY coordinate system
        
        <pre>
            Quadrant II     |   Quadrant I
           -----------------|-----------------
            Quadrant III    |   Quadrant IV
        </pre>
        
        In order for the linear function calculations to work in this method
        we must switch x and y values (x values become y values and viceversa)
        
        @param p1 first point of first line (QPointF)
        @param p2 second point of first line (QPointF)
        @param p3 first point of second line (QPointF)
        @param p4 second point of second line (QPointF)
        @return the intersection point (QPointF)
        """
        x1 = p1.y()
        y1 = p1.x()
        x2 = p2.y()
        y2 = p2.x()
        x3 = p3.y()
        y3 = p3.x()
        x4 = p4.y()
        y4 = p4.x()
        
        # line 1 is the line between (x1, y1) and (x2, y2)
        # line 2 is the line between (x3, y3) and (x4, y4)
        no_line1 = True    # it is false, if line 1 is a linear function
        no_line2 = True    # it is false, if line 2 is a linear function
        slope1 = 0.0
        slope2 = 0.0
        b1 = 0.0
        b2 = 0.0
        
        if x2 != x1:
            slope1 = (y2 - y1) / (x2 - x1)
            b1 = y1 - slope1 * x1
            no_line1 = False
        if x4 != x3:
            slope2 = (y4 - y3) / (x4 - x3)
            b2 = y3 - slope2 * x3
            no_line2 = False
        
        pt = QPointF()
        # if either line is not a function
        if no_line1 and no_line2:
            # if the lines are not the same one
            if x1 != x3:
                return QPointF(-1.0, -1.0)
            # if the lines are the same ones
            if y3 <= y4:
                if y3 <= y1 and y1 <= y4:
                    return QPointF(y1, x1)
                else:
                    return QPointF(y2, x2)
            else:
                if y4 <= y1 and y1 <= y3:
                    return QPointF(y1, x1)
                else:
                    return QPointF(y2, x2)
        elif no_line1:
            pt.setX(slope2 * x1 + b2)
            pt.setY(x1)
            if y1 >= y2:
                if not (y2 <= pt.x() and pt.x() <= y1):
                    pt.setX(-1.0)
                    pt.setY(-1.0)
            else:
                if not (y1 <= pt.x() and pt.x() <= y2):
                    pt.setX(-1.0)
                    pt.setY(-1.0)
            return pt
        elif no_line2:
            pt.setX(slope1 * x3 + b1)
            pt.setY(x3)
            if y3 >= y4:
                if not (y4 <= pt.x() and pt.x() <= y3):
                    pt.setX(-1.0)
                    pt.setY(-1.0)
            else:
                if not (y3 <= pt.x() and pt.x() <= y4):
                    pt.setX(-1.0)
                    pt.setY(-1.0)
            return pt
        
        if slope1 == slope2:
            pt.setX(-1.0)
            pt.setY(-1.0)
            return pt
        
        pt.setY((b2 - b1) / (slope1 - slope2))
        pt.setX(slope1 * pt.y() + b1)
        # the intersection point must be inside the segment (x1, y1) (x2, y2)
        if x2 >= x1 and y2 >= y1:
            if not ((x1 <= pt.y() and pt.y() <= x2) and
                    (y1 <= pt.x() and pt.x() <= y2)):
                pt.setX(-1.0)
                pt.setY(-1.0)
        elif x2 < x1 and y2 >= y1:
            if not ((x2 <= pt.y() and pt.y() <= x1) and
                    (y1 <= pt.x() and pt.x() <= y2)):
                pt.setX(-1.0)
                pt.setY(-1.0)
        elif x2 >= x1 and y2 < y1:
            if not ((x1 <= pt.y() and pt.y() <= x2) and
                    (y2 <= pt.x() and pt.x() <= y1)):
                pt.setX(-1.0)
                pt.setY(-1.0)
        else:
            if not ((x2 <= pt.y() and pt.y() <= x1) and
                    (y2 <= pt.x() and pt.x() <= y1)):
                pt.setX(-1.0)
                pt.setY(-1.0)
        
        return pt
        
    def widgetMoved(self):
        """
        Public method to recalculate the association after a widget was moved.
        """
        self.calculateEndingPoints()
        
    def unassociate(self):
        """
        Public method to unassociate from the widgets.
        """
        self.itemA.removeAssociation(self)
        self.itemB.removeAssociation(self)
    
    def buildAssociationItemDataString(self):
        """
        Public method to build a string to persist the specific item data.
        
        This string should be built like "attribute=value" with pairs separated
        by ", ". value must not contain ", " or newlines.
        
        @return persistence data (string)
        """
        entries = [
            "src={0}".format(self.itemA.getId()),
            "dst={0}".format(self.itemB.getId()),
            "type={0}".format(self.assocType),
            "topToBottom={0}".format(self.topToBottom)
        ]
        return ", ".join(entries)
    
    @classmethod
    def parseAssociationItemDataString(cls, data):
        """
        Class method to parse the given persistence data.
        
        @param data persisted data to be parsed (string)
        @return tuple with the IDs of the source and destination items,
            the association type and a flag indicating to associate from top
            to bottom (integer, integer, integer, boolean)
        """
        src = -1
        dst = -1
        assocType = Normal
        topToBottom = False
        for entry in data.split(", "):
            if "=" in entry:
                key, value = entry.split("=", 1)
                if key == "src":
                    src = int(value)
                elif key == "dst":
                    dst = int(value)
                elif key == "type":
                    assocType = int(value)
                elif key == "topToBottom":
                    topToBottom = Utilities.toBool(value)
        
        return src, dst, assocType, topToBottom
