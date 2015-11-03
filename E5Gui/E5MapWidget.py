# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a base class for showing a document map.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QSize, QRect, QCoreApplication, qVersion
from PyQt5.QtGui import QColor, QBrush, QPainter
from PyQt5.QtWidgets import QWidget, QAbstractScrollArea


class E5MapWidget(QWidget):
    """
    Class implementing a base class for showing a document map.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(E5MapWidget, self).__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        
        self.__width = 14
        self.__lineBorder = 1
        self.__lineHeight = 2
        self.__backgroundColor = QColor("#e7e7e7")
        self.__setSliderColor()
        
        self._master = None
        self.__enabled = False
        
        if parent is not None and isinstance(parent, QAbstractScrollArea):
            self.setMaster(parent)
    
    def __setSliderColor(self):
        """
        Private method to set the slider color depending upon the background
        color.
        """
        if self.__backgroundColor.toHsv().value() < 128:
            # dark background, use white slider
            self.__sliderColor = Qt.white
        else:
            # light background, use black slider
            self.__sliderColor = Qt.black
    
    def __updateMasterViewportWidth(self):
        """
        Private method to update the master's viewport width.
        """
        if self._master:
            if self.__enabled:
                width = self.__width
            else:
                width = 0
            self._master.setViewportMargins(0, 0, width, 0)
    
    def setMaster(self, master):
        """
        Public method to set the map master widget.
        
        @param master map master widget (QAbstractScrollArea)
        """
        self._master = master
        self._master.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self._master.verticalScrollBar().valueChanged.connect(self.repaint)
        self.__updateMasterViewportWidth()
    
    def setWidth(self, width):
        """
        Public method to set the widget width.
        
        @param width widget width (integer)
        """
        if width != self.__width:
            self.__width = max(6, width)    # minimum width 6 pixels
            self.__updateMasterViewportWidth()
            self.update()
    
    def width(self):
        """
        Public method to get the widget's width.
        
        @return widget width (integer)
        """
        return self.__width
    
    def setLineDimensions(self, border, height):
        """
        Public method to set the line (indicator) dimensions.
        
        @param border border width on each side in x-direction (integer)
        @param height height of the line in pixels (integer)
        """
        if border != self.__lineBorder or height != self.__lineHeight:
            self.__lineBorder = max(1, border)  # min border 1 pixel
            self.__lineHeight = max(1, height)  # min height 1 pixel
            self.update()
    
    def lineDimensions(self):
        """
        Public method to get the line (indicator) dimensions.
        
        @return tuple with border width (integer) and line height (integer)
        """
        return self.__lineBorder, self.__lineHeight
    
    def setEnabled(self, enable):
        """
        Public method to set the enabled state.
        
        @param enable flag indicating the enabled state (boolean)
        """
        if enable != self.__enabled:
            self.__enabled = enable
            self.setVisible(enable)
            self.__updateMasterViewportWidth()
    
    def isEnabled(self):
        """
        Public method to check the enabled state.
        
        @return flag indicating the enabled state (boolean)
        """
        return self.__enabled
    
    def setBackgroundColor(self, color):
        """
        Public method to set the widget background color.
        
        @param color color for the background (QColor)
        """
        if color != self.__backgroundColor:
            self.__backgroundColor = color
            self.__setSliderColor()
            self.update()
    
    def backgroundColor(self):
        """
        Public method to get the background color.
        
        @return background color (QColor)
        """
        return QColor(self.__backgroundColor)
    
    def sizeHint(self):
        """
        Public method to give an indication about the preferred size.
        
        @return preferred size (QSize)
        """
        return QSize(self.__width, 0)
    
    def paintEvent(self, event):
        """
        Protected method to handle a paint event.
        
        @param event paint event (QPaintEvent)
        """
        # step 1: fill the whole painting area
        painter = QPainter(self)
        painter.fillRect(event.rect(), self.__backgroundColor)
        
        # step 2: paint the indicators
        self._paintIt(painter)
        
        # step 3: paint the slider
        if self._master:
            penColor = self.__sliderColor
            painter.setPen(penColor)
            brushColor = Qt.transparent
            painter.setBrush(QBrush(brushColor))
            painter.drawRect(self.__generateSliderRange(
                self._master.verticalScrollBar()))
    
    def _paintIt(self, painter):
        """
        Protected method for painting the widget's indicators.
        
        Note: This method should be implemented by subclasses.
        
        @param painter reference to the painter object (QPainter)
        """
        pass
    
    def mousePressEvent(self, event):
        """
        Protected method to handle a mouse button press.
        
        @param event reference to the mouse event (QMouseEvent)
        """
        if event.button() == Qt.LeftButton and self._master:
            vsb = self._master.verticalScrollBar()
            value = self.position2Value(event.pos().y() - 1)
            vsb.setValue(value - 0.5 * vsb.pageStep())  # center on page
        self.__mousePressPos = None
    
    def mouseMoveEvent(self, event):
        """
        Protected method to handle a mouse moves.
        
        @param event reference to the mouse event (QMouseEvent)
        """
        if event.buttons() & Qt.LeftButton and self._master:
            vsb = self._master.verticalScrollBar()
            value = self.position2Value(event.pos().y() - 1)
            vsb.setValue(value - 0.5 * vsb.pageStep())  # center on page
    
    def wheelEvent(self, event):
        """
        Protected slot handling mouse wheel events.
        
        @param event reference to the wheel event (QWheelEvent)
        """
        if qVersion() >= "5.0.0":
            isVertical = event.angleDelta().x() == 0
        else:
            isVertical = event.orientation() == Qt.Vertical
        if self._master and \
            event.modifiers() == Qt.NoModifier and \
                isVertical:
            QCoreApplication.sendEvent(self._master.verticalScrollBar(), event)
    
    def calculateGeometry(self):
        """
        Public method to recalculate the map widget's geometry.
        """
        if self._master:
            cr = self._master.contentsRect()
            vsb = self._master.verticalScrollBar()
            if vsb.isVisible():
                vsbw = vsb.contentsRect().width()
            else:
                vsbw = 0
            left, top, right, bottom = self._master.getContentsMargins()
            if right > vsbw:
                vsbw = 0
            self.setGeometry(QRect(cr.right() - self.__width - vsbw, cr.top(),
                                   self.__width, cr.height()))
            self.update()
    
    def scaleFactor(self, slider=False):
        """
        Public method to determine the scrollbar's scale factor.
        
        @param slider flag indicating to calculate the result for the slider
            (boolean)
        @return scale factor (float)
        """
        if self._master:
            delta = 0 if slider else 2
            vsb = self._master.verticalScrollBar()
            posHeight = vsb.height() - delta - 1
            valHeight = vsb.maximum() - vsb.minimum() + vsb.pageStep()
            return float(posHeight) / valHeight
        else:
            return 1.0
    
    def value2Position(self, value, slider=False):
        """
        Public method to convert a scrollbar value into a position.
        
        @param value value to convert (integer)
        @param slider flag indicating to calculate the result for the slider
            (boolean)
        @return position (integer)
        """
        if self._master:
            offset = 0 if slider else 1
            vsb = self._master.verticalScrollBar()
            return (value - vsb.minimum()) * self.scaleFactor(slider) + offset
        else:
            return value
    
    def position2Value(self, position, slider=False):
        """
        Public method to convert a position into a scrollbar value.
        
        @param position scrollbar position to convert (integer)
        @param slider flag indicating to calculate the result for the slider
            (boolean)
        @return scrollbar value (integer)
        """
        if self._master:
            offset = 0 if slider else 1
            vsb = self._master.verticalScrollBar()
            return vsb.minimum() + max(
                0, (position - offset) / self.scaleFactor(slider))
        else:
            return position
    
    def generateIndicatorRect(self, position):
        """
        Public method to generate an indicator rectangle.
        
        @param position indicator position (integer)
        @return indicator rectangle (QRect)
        """
        return QRect(self.__lineBorder, position - self.__lineHeight // 2,
                     self.__width - self.__lineBorder, self.__lineHeight)
    
    def __generateSliderRange(self, scrollbar):
        """
        Private method to generate the slider rectangle.
        
        @param scrollbar reference to the vertical scrollbar (QScrollBar)
        @return slider rectangle (QRect)
        """
        pos1 = self.value2Position(scrollbar.value(), slider=True)
        pos2 = self.value2Position(scrollbar.value() + scrollbar.pageStep(),
                                   slider=True)
        return QRect(0, pos1, self.__width - 1, pos2 - pos1)
