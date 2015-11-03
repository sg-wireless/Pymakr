# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the icon editor grid.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QPoint, QRect, QSize
from PyQt5.QtGui import QImage, QColor, QPixmap, qRgba, QPainter, QCursor, \
    QBrush, qGray, qAlpha
from PyQt5.QtWidgets import QUndoCommand, QWidget, QSizePolicy, QUndoStack, \
    QApplication, QDialog

from E5Gui import E5MessageBox

from .cursors import cursors_rc     # __IGNORE_WARNING__


class IconEditCommand(QUndoCommand):
    """
    Class implementing an undo command for the icon editor.
    """
    def __init__(self, grid, text, oldImage, parent=None):
        """
        Constructor
        
        @param grid reference to the icon editor grid (IconEditorGrid)
        @param text text for the undo command (string)
        @param oldImage copy of the icon before the changes were applied
            (QImage)
        @param parent reference to the parent command (QUndoCommand)
        """
        super(IconEditCommand, self).__init__(text, parent)
        
        self.__grid = grid
        self.__imageBefore = QImage(oldImage)
        self.__imageAfter = None
    
    def setAfterImage(self, image):
        """
        Public method to set the image after the changes were applied.
        
        @param image copy of the icon after the changes were applied (QImage)
        """
        self.__imageAfter = QImage(image)
    
    def undo(self):
        """
        Public method to perform the undo.
        """
        self.__grid.setIconImage(self.__imageBefore, undoRedo=True)
    
    def redo(self):
        """
        Public method to perform the redo.
        """
        if self.__imageAfter:
            self.__grid.setIconImage(self.__imageAfter, undoRedo=True)
    

class IconEditorGrid(QWidget):
    """
    Class implementing the icon editor grid.
    
    @signal canRedoChanged(bool) emitted after the redo status has changed
    @signal canUndoChanged(bool) emitted after the undo status has changed
    @signal clipboardImageAvailable(bool) emitted to signal the availability
        of an image to be pasted
    @signal colorChanged(QColor) emitted after the drawing color was changed
    @signal imageChanged(bool) emitted after the image was modified
    @signal positionChanged(int, int) emitted after the cursor poition was
        changed
    @signal previewChanged(QPixmap) emitted to signal a new preview pixmap
    @signal selectionAvailable(bool) emitted to signal a change of the
        selection
    @signal sizeChanged(int, int) emitted after the size has been changed
    @signal zoomChanged(int) emitted to signal a change of the zoom value
    """
    canRedoChanged = pyqtSignal(bool)
    canUndoChanged = pyqtSignal(bool)
    clipboardImageAvailable = pyqtSignal(bool)
    colorChanged = pyqtSignal(QColor)
    imageChanged = pyqtSignal(bool)
    positionChanged = pyqtSignal(int, int)
    previewChanged = pyqtSignal(QPixmap)
    selectionAvailable = pyqtSignal(bool)
    sizeChanged = pyqtSignal(int, int)
    zoomChanged = pyqtSignal(int)
    
    Pencil = 1
    Rubber = 2
    Line = 3
    Rectangle = 4
    FilledRectangle = 5
    Circle = 6
    FilledCircle = 7
    Ellipse = 8
    FilledEllipse = 9
    Fill = 10
    ColorPicker = 11
    
    RectangleSelection = 20
    CircleSelection = 21
    
    MarkColor = QColor(255, 255, 255, 255)
    NoMarkColor = QColor(0, 0, 0, 0)
    
    ZoomMinimum = 100
    ZoomMaximum = 10000
    ZoomStep = 100
    ZoomDefault = 1200
    ZoomPercent = True
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(IconEditorGrid, self).__init__(parent)
        
        self.setAttribute(Qt.WA_StaticContents)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        
        self.__curColor = Qt.black
        self.__zoom = 12
        self.__curTool = self.Pencil
        self.__startPos = QPoint()
        self.__endPos = QPoint()
        self.__dirty = False
        self.__selecting = False
        self.__selRect = QRect()
        self.__isPasting = False
        self.__clipboardSize = QSize()
        self.__pasteRect = QRect()
        
        self.__undoStack = QUndoStack(self)
        self.__currentUndoCmd = None
        
        self.__image = QImage(32, 32, QImage.Format_ARGB32)
        self.__image.fill(qRgba(0, 0, 0, 0))
        self.__markImage = QImage(self.__image)
        self.__markImage.fill(self.NoMarkColor.rgba())
        
        self.__compositingMode = QPainter.CompositionMode_SourceOver
        self.__lastPos = (-1, -1)
        
        self.__gridEnabled = True
        self.__selectionAvailable = False
        
        self.__initCursors()
        self.__initUndoTexts()
        
        self.setMouseTracking(True)
        
        self.__undoStack.canRedoChanged.connect(self.canRedoChanged)
        self.__undoStack.canUndoChanged.connect(self.canUndoChanged)
        self.__undoStack.cleanChanged.connect(self.__cleanChanged)
        
        self.imageChanged.connect(self.__updatePreviewPixmap)
        QApplication.clipboard().dataChanged.connect(self.__checkClipboard)
        
        self.__checkClipboard()
    
    def __initCursors(self):
        """
        Private method to initialize the various cursors.
        """
        self.__normalCursor = QCursor(Qt.ArrowCursor)
        
        pix = QPixmap(":colorpicker-cursor.xpm")
        mask = pix.createHeuristicMask()
        pix.setMask(mask)
        self.__colorPickerCursor = QCursor(pix, 1, 21)
        
        pix = QPixmap(":paintbrush-cursor.xpm")
        mask = pix.createHeuristicMask()
        pix.setMask(mask)
        self.__paintCursor = QCursor(pix, 0, 19)
        
        pix = QPixmap(":fill-cursor.xpm")
        mask = pix.createHeuristicMask()
        pix.setMask(mask)
        self.__fillCursor = QCursor(pix, 3, 20)
        
        pix = QPixmap(":aim-cursor.xpm")
        mask = pix.createHeuristicMask()
        pix.setMask(mask)
        self.__aimCursor = QCursor(pix, 10, 10)
        
        pix = QPixmap(":eraser-cursor.xpm")
        mask = pix.createHeuristicMask()
        pix.setMask(mask)
        self.__rubberCursor = QCursor(pix, 1, 16)
    
    def __initUndoTexts(self):
        """
        Private method to initialize texts to be associated with undo commands
        for the various drawing tools.
        """
        self.__undoTexts = {
            self.Pencil: self.tr("Set Pixel"),
            self.Rubber: self.tr("Erase Pixel"),
            self.Line: self.tr("Draw Line"),
            self.Rectangle: self.tr("Draw Rectangle"),
            self.FilledRectangle: self.tr("Draw Filled Rectangle"),
            self.Circle: self.tr("Draw Circle"),
            self.FilledCircle: self.tr("Draw Filled Circle"),
            self.Ellipse: self.tr("Draw Ellipse"),
            self.FilledEllipse: self.tr("Draw Filled Ellipse"),
            self.Fill: self.tr("Fill Region"),
        }
    
    def isDirty(self):
        """
        Public method to check the dirty status.
        
        @return flag indicating a modified status (boolean)
        """
        return self.__dirty
    
    def setDirty(self, dirty, setCleanState=False):
        """
        Public slot to set the dirty flag.
        
        @param dirty flag indicating the new modification status (boolean)
        @param setCleanState flag indicating to set the undo stack to clean
            (boolean)
        """
        self.__dirty = dirty
        self.imageChanged.emit(dirty)
        
        if not dirty and setCleanState:
            self.__undoStack.setClean()
    
    def sizeHint(self):
        """
        Public method to report the size hint.
        
        @return size hint (QSize)
        """
        size = self.__zoom * self.__image.size()
        if self.__zoom >= 3 and self.__gridEnabled:
            size += QSize(1, 1)
        return size
    
    def setPenColor(self, newColor):
        """
        Public method to set the drawing color.
        
        @param newColor reference to the new color (QColor)
        """
        self.__curColor = QColor(newColor)
        self.colorChanged.emit(QColor(newColor))
    
    def penColor(self):
        """
        Public method to get the current drawing color.
        
        @return current drawing color (QColor)
        """
        return QColor(self.__curColor)
    
    def setCompositingMode(self, mode):
        """
        Public method to set the compositing mode.
        
        @param mode compositing mode to set (QPainter.CompositionMode)
        """
        self.__compositingMode = mode
    
    def compositingMode(self):
        """
        Public method to get the compositing mode.
        
        @return compositing mode (QPainter.CompositionMode)
        """
        return self.__compositingMode
    
    def setTool(self, tool):
        """
        Public method to set the current drawing tool.
        
        @param tool drawing tool to be used
            (IconEditorGrid.Pencil ... IconEditorGrid.CircleSelection)
        """
        self.__curTool = tool
        self.__lastPos = (-1, -1)
        
        if self.__curTool in [self.RectangleSelection, self.CircleSelection]:
            self.__selecting = True
        else:
            self.__selecting = False
        
        if self.__curTool in [self.RectangleSelection, self.CircleSelection,
                              self.Line, self.Rectangle, self.FilledRectangle,
                              self.Circle, self.FilledCircle,
                              self.Ellipse, self.FilledEllipse]:
            self.setCursor(self.__aimCursor)
        elif self.__curTool == self.Fill:
            self.setCursor(self.__fillCursor)
        elif self.__curTool == self.ColorPicker:
            self.setCursor(self.__colorPickerCursor)
        elif self.__curTool == self.Pencil:
            self.setCursor(self.__paintCursor)
        elif self.__curTool == self.Rubber:
            self.setCursor(self.__rubberCursor)
        else:
            self.setCursor(self.__normalCursor)
    
    def tool(self):
        """
        Public method to get the current drawing tool.
        
        @return current drawing tool
            (IconEditorGrid.Pencil ... IconEditorGrid.CircleSelection)
        """
        return self.__curTool
    
    def setIconImage(self, newImage, undoRedo=False, clearUndo=False):
        """
        Public method to set a new icon image.
        
        @param newImage reference to the new image (QImage)
        @keyparam undoRedo flag indicating an undo or redo operation (boolean)
        @keyparam clearUndo flag indicating to clear the undo stack (boolean)
        """
        if newImage != self.__image:
            self.__image = newImage.convertToFormat(QImage.Format_ARGB32)
            self.update()
            self.updateGeometry()
            self.resize(self.sizeHint())
            
            self.__markImage = QImage(self.__image)
            self.__markImage.fill(self.NoMarkColor.rgba())
            
            if undoRedo:
                self.setDirty(not self.__undoStack.isClean())
            else:
                self.setDirty(False)
            
            if clearUndo:
                self.__undoStack.clear()
            
            self.sizeChanged.emit(*self.iconSize())
    
    def iconImage(self):
        """
        Public method to get a copy of the icon image.
        
        @return copy of the icon image (QImage)
        """
        return QImage(self.__image)
    
    def iconSize(self):
        """
        Public method to get the size of the icon.
        
        @return width and height of the image as a tuple (integer, integer)
        """
        return self.__image.width(), self.__image.height()
    
    def setZoomFactor(self, newZoom):
        """
        Public method to set the zoom factor in percent.
        
        @param newZoom zoom factor (integer >= 100)
        """
        newZoom = max(100, newZoom)   # must not be less than 100
        if newZoom != self.__zoom:
            self.__zoom = newZoom // 100
            self.update()
            self.updateGeometry()
            self.resize(self.sizeHint())
            self.zoomChanged.emit(int(self.__zoom * 100))
    
    def zoomFactor(self):
        """
        Public method to get the current zoom factor in percent.
        
        @return zoom factor (integer)
        """
        return self.__zoom * 100
    
    def setGridEnabled(self, enable):
        """
        Public method to enable the display of grid lines.
        
        @param enable enabled status of the grid lines (boolean)
        """
        if enable != self.__gridEnabled:
            self.__gridEnabled = enable
            self.update()
    
    def isGridEnabled(self):
        """
        Public method to get the grid lines status.
        
        @return enabled status of the grid lines (boolean)
        """
        return self.__gridEnabled
    
    def paintEvent(self, evt):
        """
        Protected method called to repaint some of the widget.
        
        @param evt reference to the paint event object (QPaintEvent)
        """
        painter = QPainter(self)
        
        if self.__zoom >= 3 and self.__gridEnabled:
            painter.setPen(self.palette().windowText().color())
            i = 0
            while i <= self.__image.width():
                painter.drawLine(
                    self.__zoom * i, 0,
                    self.__zoom * i, self.__zoom * self.__image.height())
                i += 1
            j = 0
            while j <= self.__image.height():
                painter.drawLine(
                    0, self.__zoom * j,
                    self.__zoom * self.__image.width(), self.__zoom * j)
                j += 1
        
        col = QColor("#aaa")
        painter.setPen(Qt.DashLine)
        for i in range(0, self.__image.width()):
            for j in range(0, self.__image.height()):
                rect = self.__pixelRect(i, j)
                if evt.region().intersects(rect):
                    color = QColor.fromRgba(self.__image.pixel(i, j))
                    painter.fillRect(rect, QBrush(Qt.white))
                    painter.fillRect(QRect(rect.topLeft(), rect.center()), col)
                    painter.fillRect(QRect(rect.center(), rect.bottomRight()),
                                     col)
                    painter.fillRect(rect, QBrush(color))
                
                    if self.__isMarked(i, j):
                        painter.drawRect(rect.adjusted(0, 0, -1, -1))
        
        painter.end()
    
    def __pixelRect(self, i, j):
        """
        Private method to determine the rectangle for a given pixel coordinate.
        
        @param i x-coordinate of the pixel in the image (integer)
        @param j y-coordinate of the pixel in the image (integer)
        @return rectangle for the given pixel coordinates (QRect)
        """
        if self.__zoom >= 3 and self.__gridEnabled:
            return QRect(self.__zoom * i + 1, self.__zoom * j + 1,
                         self.__zoom - 1, self.__zoom - 1)
        else:
            return QRect(self.__zoom * i, self.__zoom * j,
                         self.__zoom, self.__zoom)
    
    def mousePressEvent(self, evt):
        """
        Protected method to handle mouse button press events.
        
        @param evt reference to the mouse event object (QMouseEvent)
        """
        if evt.button() == Qt.LeftButton:
            if self.__isPasting:
                self.__isPasting = False
                self.editPaste(True)
                self.__markImage.fill(self.NoMarkColor.rgba())
                self.update(self.__pasteRect)
                self.__pasteRect = QRect()
                return
            
            if self.__curTool == self.Pencil:
                cmd = IconEditCommand(self, self.__undoTexts[self.__curTool],
                                      self.__image)
                self.__setImagePixel(evt.pos(), True)
                self.setDirty(True)
                self.__undoStack.push(cmd)
                self.__currentUndoCmd = cmd
            elif self.__curTool == self.Rubber:
                cmd = IconEditCommand(self, self.__undoTexts[self.__curTool],
                                      self.__image)
                self.__setImagePixel(evt.pos(), False)
                self.setDirty(True)
                self.__undoStack.push(cmd)
                self.__currentUndoCmd = cmd
            elif self.__curTool == self.Fill:
                i, j = self.__imageCoordinates(evt.pos())
                col = QColor()
                col.setRgba(self.__image.pixel(i, j))
                cmd = IconEditCommand(self, self.__undoTexts[self.__curTool],
                                      self.__image)
                self.__drawFlood(i, j, col)
                self.setDirty(True)
                self.__undoStack.push(cmd)
                cmd.setAfterImage(self.__image)
            elif self.__curTool == self.ColorPicker:
                i, j = self.__imageCoordinates(evt.pos())
                col = QColor()
                col.setRgba(self.__image.pixel(i, j))
                self.setPenColor(col)
            else:
                self.__unMark()
                self.__startPos = evt.pos()
                self.__endPos = evt.pos()
    
    def mouseMoveEvent(self, evt):
        """
        Protected method to handle mouse move events.
        
        @param evt reference to the mouse event object (QMouseEvent)
        """
        self.positionChanged.emit(*self.__imageCoordinates(evt.pos()))
        
        if self.__isPasting and not (evt.buttons() & Qt.LeftButton):
            self.__drawPasteRect(evt.pos())
            return
        
        if evt.buttons() & Qt.LeftButton:
            if self.__curTool == self.Pencil:
                self.__setImagePixel(evt.pos(), True)
                self.setDirty(True)
            elif self.__curTool == self.Rubber:
                self.__setImagePixel(evt.pos(), False)
                self.setDirty(True)
            elif self.__curTool in [self.Fill, self.ColorPicker]:
                pass    # do nothing
            else:
                self.__drawTool(evt.pos(), True)
    
    def mouseReleaseEvent(self, evt):
        """
        Protected method to handle mouse button release events.
        
        @param evt reference to the mouse event object (QMouseEvent)
        """
        if evt.button() == Qt.LeftButton:
            if self.__curTool in [self.Pencil, self.Rubber]:
                if self.__currentUndoCmd:
                    self.__currentUndoCmd.setAfterImage(self.__image)
                    self.__currentUndoCmd = None
            
            if self.__curTool not in [self.Pencil, self.Rubber,
                                      self.Fill, self.ColorPicker,
                                      self.RectangleSelection,
                                      self.CircleSelection]:
                cmd = IconEditCommand(self, self.__undoTexts[self.__curTool],
                                      self.__image)
                if self.__drawTool(evt.pos(), False):
                    self.__undoStack.push(cmd)
                    cmd.setAfterImage(self.__image)
                    self.setDirty(True)
    
    def __setImagePixel(self, pos, opaque):
        """
        Private slot to set or erase a pixel.
        
        @param pos position of the pixel in the widget (QPoint)
        @param opaque flag indicating a set operation (boolean)
        """
        i, j = self.__imageCoordinates(pos)
        
        if self.__image.rect().contains(i, j) and (i, j) != self.__lastPos:
            if opaque:
                painter = QPainter(self.__image)
                painter.setPen(self.penColor())
                painter.setCompositionMode(self.__compositingMode)
                painter.drawPoint(i, j)
            else:
                self.__image.setPixel(i, j, qRgba(0, 0, 0, 0))
            self.__lastPos = (i, j)
        
            self.update(self.__pixelRect(i, j))
    
    def __imageCoordinates(self, pos):
        """
        Private method to convert from widget to image coordinates.
        
        @param pos widget coordinate (QPoint)
        @return tuple with the image coordinates (tuple of two integers)
        """
        i = pos.x() // self.__zoom
        j = pos.y() // self.__zoom
        return i, j
    
    def __drawPasteRect(self, pos):
        """
        Private slot to draw a rectangle for signaling a paste operation.
        
        @param pos widget position of the paste rectangle (QPoint)
        """
        self.__markImage.fill(self.NoMarkColor.rgba())
        if self.__pasteRect.isValid():
            self.__updateImageRect(
                self.__pasteRect.topLeft(),
                self.__pasteRect.bottomRight() + QPoint(1, 1))
        
        x, y = self.__imageCoordinates(pos)
        isize = self.__image.size()
        if x + self.__clipboardSize.width() <= isize.width():
            sx = self.__clipboardSize.width()
        else:
            sx = isize.width() - x
        if y + self.__clipboardSize.height() <= isize.height():
            sy = self.__clipboardSize.height()
        else:
            sy = isize.height() - y
        
        self.__pasteRect = QRect(QPoint(x, y), QSize(sx - 1, sy - 1))
        
        painter = QPainter(self.__markImage)
        painter.setPen(self.MarkColor)
        painter.drawRect(self.__pasteRect)
        painter.end()
        
        self.__updateImageRect(self.__pasteRect.topLeft(),
                               self.__pasteRect.bottomRight() + QPoint(1, 1))
    
    def __drawTool(self, pos, mark):
        """
        Private method to perform a draw operation depending of the current
        tool.
        
        @param pos widget coordinate to perform the draw operation at (QPoint)
        @param mark flag indicating a mark operation (boolean)
        @return flag indicating a successful draw (boolean)
        """
        self.__unMark()
        
        if mark:
            self.__endPos = QPoint(pos)
            drawColor = self.MarkColor
            img = self.__markImage
        else:
            drawColor = self.penColor()
            img = self.__image
        
        start = QPoint(*self.__imageCoordinates(self.__startPos))
        end = QPoint(*self.__imageCoordinates(pos))
        
        painter = QPainter(img)
        painter.setPen(drawColor)
        painter.setCompositionMode(self.__compositingMode)
        
        if self.__curTool == self.Line:
            painter.drawLine(start, end)
        
        elif self.__curTool in [self.Rectangle, self.FilledRectangle,
                                self.RectangleSelection]:
            left = min(start.x(), end.x())
            top = min(start.y(), end.y())
            right = max(start.x(), end.x())
            bottom = max(start.y(), end.y())
            if self.__curTool == self.RectangleSelection:
                painter.setBrush(QBrush(drawColor))
            if self.__curTool == self.FilledRectangle:
                for y in range(top, bottom + 1):
                    painter.drawLine(left, y, right, y)
            else:
                painter.drawRect(left, top, right - left, bottom - top)
            if self.__selecting:
                self.__selRect = QRect(
                    left, top, right - left + 1, bottom - top + 1)
                self.__selectionAvailable = True
                self.selectionAvailable.emit(True)
        
        elif self.__curTool in [self.Circle, self.FilledCircle,
                                self.CircleSelection]:
            r = max(abs(start.x() - end.x()), abs(start.y() - end.y()))
            if self.__curTool in [self.FilledCircle, self.CircleSelection]:
                painter.setBrush(QBrush(drawColor))
            painter.drawEllipse(start, r, r)
            if self.__selecting:
                self.__selRect = QRect(start.x() - r, start.y() - r,
                                       2 * r + 1, 2 * r + 1)
                self.__selectionAvailable = True
                self.selectionAvailable.emit(True)
        
        elif self.__curTool in [self.Ellipse, self.FilledEllipse]:
            r1 = abs(start.x() - end.x())
            r2 = abs(start.y() - end.y())
            if r1 == 0 or r2 == 0:
                return False
            if self.__curTool == self.FilledEllipse:
                painter.setBrush(QBrush(drawColor))
            painter.drawEllipse(start, r1, r2)
        
        painter.end()
        
        if self.__curTool in [self.Circle, self.FilledCircle,
                              self.Ellipse, self.FilledEllipse]:
            self.update()
        else:
            self.__updateRect(self.__startPos, pos)
        
        return True
    
    def __drawFlood(self, i, j, oldColor, doUpdate=True):
        """
        Private method to perform a flood fill operation.
        
        @param i x-value in image coordinates (integer)
        @param j y-value in image coordinates (integer)
        @param oldColor reference to the color at position i, j (QColor)
        @param doUpdate flag indicating an update is requested (boolean)
            (used for speed optimizations)
        """
        if not self.__image.rect().contains(i, j) or \
           self.__image.pixel(i, j) != oldColor.rgba() or \
           self.__image.pixel(i, j) == self.penColor().rgba():
            return
        
        self.__image.setPixel(i, j, self.penColor().rgba())
        
        self.__drawFlood(i, j - 1, oldColor, False)
        self.__drawFlood(i, j + 1, oldColor, False)
        self.__drawFlood(i - 1, j, oldColor, False)
        self.__drawFlood(i + 1, j, oldColor, False)
        
        if doUpdate:
            self.update()
    
    def __updateRect(self, pos1, pos2):
        """
        Private slot to update parts of the widget.
        
        @param pos1 top, left position for the update in widget coordinates
            (QPoint)
        @param pos2 bottom, right position for the update in widget
            coordinates (QPoint)
        """
        self.__updateImageRect(QPoint(*self.__imageCoordinates(pos1)),
                               QPoint(*self.__imageCoordinates(pos2)))
    
    def __updateImageRect(self, ipos1, ipos2):
        """
        Private slot to update parts of the widget.
        
        @param ipos1 top, left position for the update in image coordinates
            (QPoint)
        @param ipos2 bottom, right position for the update in image
            coordinates (QPoint)
        """
        r1 = self.__pixelRect(ipos1.x(), ipos1.y())
        r2 = self.__pixelRect(ipos2.x(), ipos2.y())
        
        left = min(r1.x(), r2.x())
        top = min(r1.y(), r2.y())
        right = max(r1.x() + r1.width(), r2.x() + r2.width())
        bottom = max(r1.y() + r1.height(), r2.y() + r2.height())
        self.update(left, top, right - left + 1, bottom - top + 1)
    
    def __unMark(self):
        """
        Private slot to remove the mark indicator.
        """
        self.__markImage.fill(self.NoMarkColor.rgba())
        if self.__curTool in [self.Circle, self.FilledCircle,
                              self.Ellipse, self.FilledEllipse,
                              self.CircleSelection]:
            self.update()
        else:
            self.__updateRect(self.__startPos, self.__endPos)
        
        if self.__selecting:
            self.__selRect = QRect()
            self.__selectionAvailable = False
            self.selectionAvailable.emit(False)
    
    def __isMarked(self, i, j):
        """
        Private method to check, if a pixel is marked.
        
        @param i x-value in image coordinates (integer)
        @param j y-value in image coordinates (integer)
        @return flag indicating a marked pixel (boolean)
        """
        return self.__markImage.pixel(i, j) == self.MarkColor.rgba()
    
    def __updatePreviewPixmap(self):
        """
        Private slot to generate and signal an updated preview pixmap.
        """
        p = QPixmap.fromImage(self.__image)
        self.previewChanged.emit(p)
    
    def previewPixmap(self):
        """
        Public method to generate a preview pixmap.
        
        @return preview pixmap (QPixmap)
        """
        p = QPixmap.fromImage(self.__image)
        return p
    
    def __checkClipboard(self):
        """
        Private slot to check, if the clipboard contains a valid image, and
        signal the result.
        """
        ok = self.__clipboardImage()[1]
        self.__clipboardImageAvailable = ok
        self.clipboardImageAvailable.emit(ok)
    
    def canPaste(self):
        """
        Public slot to check the availability of the paste operation.
        
        @return flag indicating availability of paste (boolean)
        """
        return self.__clipboardImageAvailable
    
    def __clipboardImage(self):
        """
        Private method to get an image from the clipboard.
        
        @return tuple with the image (QImage) and a flag indicating a
            valid image (boolean)
        """
        img = QApplication.clipboard().image()
        ok = not img.isNull()
        if ok:
            img = img.convertToFormat(QImage.Format_ARGB32)
        
        return img, ok
    
    def __getSelectionImage(self, cut):
        """
        Private method to get an image from the selection.
        
        @param cut flag indicating to cut the selection (boolean)
        @return image of the selection (QImage)
        """
        if cut:
            cmd = IconEditCommand(self, self.tr("Cut Selection"),
                                  self.__image)
        
        img = QImage(self.__selRect.size(), QImage.Format_ARGB32)
        img.fill(qRgba(0, 0, 0, 0))
        for i in range(0, self.__selRect.width()):
            for j in range(0, self.__selRect.height()):
                if self.__image.rect().contains(self.__selRect.x() + i,
                                                self.__selRect.y() + j):
                    if self.__isMarked(
                            self.__selRect.x() + i, self.__selRect.y() + j):
                        img.setPixel(i, j, self.__image.pixel(
                            self.__selRect.x() + i, self.__selRect.y() + j))
                        if cut:
                            self.__image.setPixel(self.__selRect.x() + i,
                                                  self.__selRect.y() + j,
                                                  qRgba(0, 0, 0, 0))
        
        if cut:
            self.__undoStack.push(cmd)
            cmd.setAfterImage(self.__image)
        
        self.__unMark()
        
        if cut:
            self.update(self.__selRect)
        
        return img
    
    def editCopy(self):
        """
        Public slot to copy the selection.
        """
        if self.__selRect.isValid():
            img = self.__getSelectionImage(False)
            QApplication.clipboard().setImage(img)
    
    def editCut(self):
        """
        Public slot to cut the selection.
        """
        if self.__selRect.isValid():
            img = self.__getSelectionImage(True)
            QApplication.clipboard().setImage(img)
    
    @pyqtSlot()
    def editPaste(self, pasting=False):
        """
        Public slot to paste an image from the clipboard.
        
        @param pasting flag indicating part two of the paste operation
            (boolean)
        """
        img, ok = self.__clipboardImage()
        if ok:
            if img.width() > self.__image.width() or \
                    img.height() > self.__image.height():
                res = E5MessageBox.yesNo(
                    self,
                    self.tr("Paste"),
                    self.tr(
                        """<p>The clipboard image is larger than the"""
                        """ current image.<br/>Paste as new image?</p>"""))
                if res:
                    self.editPasteAsNew()
                return
            elif not pasting:
                self.__isPasting = True
                self.__clipboardSize = img.size()
            else:
                cmd = IconEditCommand(self, self.tr("Paste Clipboard"),
                                      self.__image)
                self.__markImage.fill(self.NoMarkColor.rgba())
                painter = QPainter(self.__image)
                painter.setPen(self.penColor())
                painter.setCompositionMode(self.__compositingMode)
                painter.drawImage(
                    self.__pasteRect.x(), self.__pasteRect.y(), img, 0, 0,
                    self.__pasteRect.width() + 1,
                    self.__pasteRect.height() + 1)
                
                self.__undoStack.push(cmd)
                cmd.setAfterImage(self.__image)
                
                self.__updateImageRect(
                    self.__pasteRect.topLeft(),
                    self.__pasteRect.bottomRight() + QPoint(1, 1))
        else:
            E5MessageBox.warning(
                self,
                self.tr("Pasting Image"),
                self.tr("""Invalid image data in clipboard."""))
    
    def editPasteAsNew(self):
        """
        Public slot to paste the clipboard as a new image.
        """
        img, ok = self.__clipboardImage()
        if ok:
            cmd = IconEditCommand(
                self, self.tr("Paste Clipboard as New Image"),
                self.__image)
            self.setIconImage(img)
            self.setDirty(True)
            self.__undoStack.push(cmd)
            cmd.setAfterImage(self.__image)
    
    def editSelectAll(self):
        """
        Public slot to select the complete image.
        """
        self.__unMark()
        
        self.__startPos = QPoint(0, 0)
        self.__endPos = QPoint(self.rect().bottomRight())
        self.__markImage.fill(self.MarkColor.rgba())
        self.__selRect = self.__image.rect()
        self.__selectionAvailable = True
        self.selectionAvailable.emit(True)
        
        self.update()
    
    def editClear(self):
        """
        Public slot to clear the image.
        """
        self.__unMark()
        
        cmd = IconEditCommand(self, self.tr("Clear Image"), self.__image)
        self.__image.fill(qRgba(0, 0, 0, 0))
        self.update()
        self.setDirty(True)
        self.__undoStack.push(cmd)
        cmd.setAfterImage(self.__image)
    
    def editResize(self):
        """
        Public slot to resize the image.
        """
        from .IconSizeDialog import IconSizeDialog
        dlg = IconSizeDialog(self.__image.width(), self.__image.height())
        res = dlg.exec_()
        if res == QDialog.Accepted:
            newWidth, newHeight = dlg.getData()
            if newWidth != self.__image.width() or \
                    newHeight != self.__image.height():
                cmd = IconEditCommand(self, self.tr("Resize Image"),
                                      self.__image)
                img = self.__image.scaled(
                    newWidth, newHeight, Qt.IgnoreAspectRatio,
                    Qt.SmoothTransformation)
                self.setIconImage(img)
                self.setDirty(True)
                self.__undoStack.push(cmd)
                cmd.setAfterImage(self.__image)
    
    def editNew(self):
        """
        Public slot to generate a new, empty image.
        """
        from .IconSizeDialog import IconSizeDialog
        dlg = IconSizeDialog(self.__image.width(), self.__image.height())
        res = dlg.exec_()
        if res == QDialog.Accepted:
            width, height = dlg.getData()
            img = QImage(width, height, QImage.Format_ARGB32)
            img.fill(qRgba(0, 0, 0, 0))
            self.setIconImage(img)
    
    def grayScale(self):
        """
        Public slot to convert the image to gray preserving transparency.
        """
        cmd = IconEditCommand(self, self.tr("Convert to Grayscale"),
                              self.__image)
        for x in range(self.__image.width()):
            for y in range(self.__image.height()):
                col = self.__image.pixel(x, y)
                if col != qRgba(0, 0, 0, 0):
                    gray = qGray(col)
                    self.__image.setPixel(
                        x, y, qRgba(gray, gray, gray, qAlpha(col)))
        self.update()
        self.setDirty(True)
        self.__undoStack.push(cmd)
        cmd.setAfterImage(self.__image)

    def editUndo(self):
        """
        Public slot to perform an undo operation.
        """
        if self.__undoStack.canUndo():
            self.__undoStack.undo()
    
    def editRedo(self):
        """
        Public slot to perform a redo operation.
        """
        if self.__undoStack.canRedo():
            self.__undoStack.redo()
    
    def canUndo(self):
        """
        Public method to return the undo status.
        
        @return flag indicating the availability of undo (boolean)
        """
        return self.__undoStack.canUndo()
    
    def canRedo(self):
        """
        Public method to return the redo status.
        
        @return flag indicating the availability of redo (boolean)
        """
        return self.__undoStack.canRedo()
    
    def __cleanChanged(self, clean):
        """
        Private slot to handle the undo stack clean state change.
        
        @param clean flag indicating the clean state (boolean)
        """
        self.setDirty(not clean)
    
    def shutdown(self):
        """
        Public slot to perform some shutdown actions.
        """
        self.__undoStack.canRedoChanged.disconnect(self.canRedoChanged)
        self.__undoStack.canUndoChanged.disconnect(self.canUndoChanged)
        self.__undoStack.cleanChanged.disconnect(self.__cleanChanged)
    
    def isSelectionAvailable(self):
        """
        Public method to check the availability of a selection.
        
        @return flag indicating the availability of a selection (boolean)
        """
        return self.__selectionAvailable
