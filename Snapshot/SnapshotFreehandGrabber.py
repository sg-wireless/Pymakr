# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a grabber widget for a freehand snapshot region.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt, QRect, QPoint, QTimer, qVersion
from PyQt5.QtGui import QPixmap, QColor, QRegion, QPainter, QPalette, \
    QPolygon, QPen, QBrush, QPaintEngine
from PyQt5.QtWidgets import QWidget, QApplication, QToolTip


def drawPolygon(painter, polygon, outline, fill=QColor()):
    """
    Module function to draw a polygon with the given parameters.
    
    @param painter reference to the painter to be used (QPainter)
    @param polygon polygon to be drawn (QPolygon)
    @param outline color of the outline (QColor)
    @param fill fill color (QColor)
    """
    clip = QRegion(polygon)
    clip = clip - QRegion(polygon)
    pen = QPen(outline, 1, Qt.SolidLine, Qt.SquareCap, Qt.BevelJoin)
    
    painter.save()
    painter.setClipRegion(clip)
    painter.setPen(pen)
    painter.drawPolygon(QPolygon(polygon))
    if fill.isValid():
        painter.setClipping(False)
        painter.setBrush(fill)
        painter.drawPolygon(QPolygon(polygon))
    painter.restore()


class SnapshotFreehandGrabber(QWidget):
    """
    Class implementing a grabber widget for a freehand snapshot region.
    
    @signal grabbed(QPixmap) emitted after the region was grabbed
    """
    grabbed = pyqtSignal(QPixmap)
    
    def __init__(self):
        """
        Constructor
        """
        super(SnapshotFreehandGrabber, self).__init__(
            None,
            Qt.X11BypassWindowManagerHint | Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint | Qt.Tool)
        
        self.__selection = QPolygon()
        self.__mouseDown = False
        self.__newSelection = False
        self.__handleSize = 10
        self.__showHelp = True
        self.__grabbing = False
        self.__dragStartPoint = QPoint()
        self.__selectionBeforeDrag = QPolygon()
        
        self.__helpTextRect = QRect()
        self.__helpText = self.tr(
            "Select a region using the mouse. To take the snapshot,"
            " press the Enter key or double click. Press Esc to quit.")
        
        self.__pixmap = QPixmap()
        self.__pBefore = QPoint()
        
        self.setMouseTracking(True)
        
        QTimer.singleShot(200, self.__initialize)
    
    def __initialize(self):
        """
        Private slot to initialize the rest of the widget.
        """
        self.__desktop = QApplication.desktop()
        x = self.__desktop.x()
        y = self.__desktop.y()
        if qVersion() >= "5.0.0":
            self.__pixmap = QApplication.screens()[0].grabWindow(
                self.__desktop.winId(), x, y,
                self.__desktop.width(), self.__desktop.height())
        else:
            self.__pixmap = QPixmap.grabWindow(
                self.__desktop.winId(), x, y,
                self.__desktop.width(), self.__desktop.height())
        self.resize(self.__pixmap.size())
        self.move(x, y)
        self.setCursor(Qt.CrossCursor)
        self.show()

        self.grabMouse()
        self.grabKeyboard()
    
    def paintEvent(self, evt):
        """
        Protected method handling paint events.
        
        @param evt paint event (QPaintEvent)
        """
        if self.__grabbing:     # grabWindow() should just get the background
            return
        
        painter = QPainter(self)
        pal = QPalette(QToolTip.palette())
        font = QToolTip.font()
        
        handleColor = pal.color(QPalette.Active, QPalette.Highlight)
        handleColor.setAlpha(160)
        overlayColor = QColor(0, 0, 0, 160)
        textColor = pal.color(QPalette.Active, QPalette.Text)
        textBackgroundColor = pal.color(QPalette.Active, QPalette.Base)
        painter.drawPixmap(0, 0, self.__pixmap)
        painter.setFont(font)
        
        pol = QPolygon(self.__selection)
        if not self.__selection.boundingRect().isNull():
            # Draw outline around selection.
            # Important: the 1px-wide outline is *also* part of the
            # captured free-region
            pen = QPen(handleColor, 1, Qt.SolidLine, Qt.SquareCap,
                       Qt.BevelJoin)
            painter.setPen(pen)
            painter.drawPolygon(pol)
            
            # Draw the grey area around the selection.
            grey = QRegion(self.rect())
            grey = grey - QRegion(pol)
            painter.setClipRegion(grey)
            painter.setPen(Qt.NoPen)
            painter.setBrush(overlayColor)
            painter.drawRect(self.rect())
            painter.setClipRect(self.rect())
            drawPolygon(painter, pol, handleColor)
        
        if self.__showHelp:
            painter.setPen(textColor)
            painter.setBrush(textBackgroundColor)
            self.__helpTextRect = painter.boundingRect(
                self.rect().adjusted(2, 2, -2, -2),
                Qt.TextWordWrap, self.__helpText).translated(
                -self.__desktop.x(), -self.__desktop.y())
            self.__helpTextRect.adjust(-2, -2, 4, 2)
            drawPolygon(painter, self.__helpTextRect, textColor,
                        textBackgroundColor)
            painter.drawText(
                self.__helpTextRect.adjusted(3, 3, -3, -3),
                Qt.TextWordWrap, self.__helpText)
        
        if self.__selection.isEmpty():
            return
        
        # The grabbed region is everything which is covered by the drawn
        # rectangles (border included). This means that there is no 0px
        # selection, since a 0px wide rectangle will always be drawn as a line.
        boundingRect = self.__selection.boundingRect()
        txt = "{0:n}, {1:n} ({2:n} x {3:n})".format(
            boundingRect.x(), boundingRect.y(),
            boundingRect.width(), boundingRect.height())
        textRect = painter.boundingRect(self.rect(), Qt.AlignLeft, txt)
        boundingRect = textRect.adjusted(-4, 0, 0, 0)
        
        polBoundingRect = pol.boundingRect()
        if (textRect.width() <
            polBoundingRect.width() - 2 * self.__handleSize) and \
           (textRect.height() <
            polBoundingRect.height() - 2 * self.__handleSize) and \
           polBoundingRect.width() > 100 and \
           polBoundingRect.height() > 100:
            # center, unsuitable for small selections
            boundingRect.moveCenter(polBoundingRect.center())
            textRect.moveCenter(polBoundingRect.center())
        elif polBoundingRect.y() - 3 > textRect.height() and \
                polBoundingRect.x() + textRect.width() < self.rect().width():
            # on top, left aligned
            boundingRect.moveBottomLeft(
                QPoint(polBoundingRect.x(), polBoundingRect.y() - 3))
            textRect.moveBottomLeft(
                QPoint(polBoundingRect.x() + 2, polBoundingRect.y() - 3))
        elif polBoundingRect.x() - 3 > textRect.width():
            # left, top aligned
            boundingRect.moveTopRight(
                QPoint(polBoundingRect.x() - 3, polBoundingRect.y()))
            textRect.moveTopRight(
                QPoint(polBoundingRect.x() - 5, polBoundingRect.y()))
        elif (polBoundingRect.bottom() + 3 + textRect.height() <
              self.rect().bottom()) and \
                polBoundingRect.right() > textRect.width():
            # at bottom, right aligned
            boundingRect.moveTopRight(
                QPoint(polBoundingRect.right(), polBoundingRect.bottom() + 3))
            textRect.moveTopRight(
                QPoint(polBoundingRect.right() - 2,
                       polBoundingRect.bottom() + 3))
        elif polBoundingRect.right() + textRect.width() + 3 < \
                self.rect().width():
            # right, bottom aligned
            boundingRect.moveBottomLeft(
                QPoint(polBoundingRect.right() + 3, polBoundingRect.bottom()))
            textRect.moveBottomLeft(
                QPoint(polBoundingRect.right() + 5, polBoundingRect.bottom()))
        
        # If the above didn't catch it, you are running on a very
        # tiny screen...
        drawPolygon(painter, boundingRect, textColor, textBackgroundColor)
        painter.drawText(textRect, Qt.AlignHCenter, txt)
        
        if (polBoundingRect.height() > self.__handleSize * 2 and
            polBoundingRect.width() > self.__handleSize * 2) or \
           not self.__mouseDown:
            painter.setBrush(Qt.transparent)
            painter.setClipRegion(QRegion(pol))
            painter.drawPolygon(QPolygon(self.rect()))
    
    def mousePressEvent(self, evt):
        """
        Protected method to handle mouse button presses.
        
        @param evt mouse press event (QMouseEvent)
        """
        self.__pBefore = evt.pos()
        
        self.__showHelp = not self.__helpTextRect.contains(evt.pos())
        if evt.button() == Qt.LeftButton:
            self.__mouseDown = True
            self.__dragStartPoint = evt.pos()
            self.__selectionBeforeDrag = QPolygon(self.__selection)
            if not self.__selection.containsPoint(evt.pos(), Qt.WindingFill):
                self.__newSelection = True
                self.__selection = QPolygon()
            else:
                self.setCursor(Qt.ClosedHandCursor)
        elif evt.button() == Qt.RightButton:
            self.__newSelection = False
            self.__selection = QPolygon()
            self.setCursor(Qt.CrossCursor)
        self.update()
    
    def mouseMoveEvent(self, evt):
        """
        Protected method to handle mouse movements.
        
        @param evt mouse move event (QMouseEvent)
        """
        shouldShowHelp = not self.__helpTextRect.contains(evt.pos())
        if shouldShowHelp != self.__showHelp:
            self.__showHelp = shouldShowHelp
            self.update()
        
        if self.__mouseDown:
            if self.__newSelection:
                p = evt.pos()
                self.__selection.append(p)
            else:
                # moving the whole selection
                p = evt.pos() - self.__pBefore  # Offset
                self.__pBefore = evt.pos()  # save position for next iteration
                self.__selection.translate(p)
            
            self.update()
        else:
            if self.__selection.boundingRect().isEmpty():
                return
            
            if self.__selection.containsPoint(evt.pos(), Qt.WindingFill):
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.CrossCursor)
    
    def mouseReleaseEvent(self, evt):
        """
        Protected method to handle mouse button releases.
        
        @param evt mouse release event (QMouseEvent)
        """
        self.__mouseDown = False
        self.__newSelection = False
        if self.__selection.containsPoint(evt.pos(), Qt.WindingFill):
            self.setCursor(Qt.OpenHandCursor)
        self.update()
    
    def mouseDoubleClickEvent(self, evt):
        """
        Protected method to handle mouse double clicks.
        
        @param evt mouse double click event (QMouseEvent)
        """
        self.__grabRegion()
    
    def keyPressEvent(self, evt):
        """
        Protected method to handle key presses.
        
        @param evt key press event (QKeyEvent)
        """
        if evt.key() == Qt.Key_Escape:
            self.grabbed.emit(QPixmap())
        elif evt.key() in [Qt.Key_Enter, Qt.Key_Return]:
            self.__grabRegion()
        else:
            evt.ignore()
    
    def __grabRegion(self):
        """
        Private method to grab the selected region (i.e. do the snapshot).
        """
        pol = QPolygon(self.__selection)
        if not pol.isEmpty():
            self.__grabbing = True
            
            xOffset = self.__pixmap.rect().x() - pol.boundingRect().x()
            yOffset = self.__pixmap.rect().y() - pol.boundingRect().y()
            translatedPol = pol.translated(xOffset, yOffset)
            
            pixmap2 = QPixmap(pol.boundingRect().size())
            pixmap2.fill(Qt.transparent)
            
            pt = QPainter()
            pt.begin(pixmap2)
            if pt.paintEngine().hasFeature(QPaintEngine.PorterDuff):
                pt.setRenderHints(
                    QPainter.Antialiasing |
                    QPainter.HighQualityAntialiasing |
                    QPainter.SmoothPixmapTransform,
                    True)
                pt.setBrush(Qt.black)
                pt.setPen(QPen(QBrush(Qt.black), 0.5))
                pt.drawPolygon(translatedPol)
                pt.setCompositionMode(QPainter.CompositionMode_SourceIn)
            else:
                pt.setClipRegion(QRegion(translatedPol))
                pt.setCompositionMode(QPainter.CompositionMode_Source)
            
            pt.drawPixmap(pixmap2.rect(), self.__pixmap, pol.boundingRect())
            pt.end()
            
            self.grabbed.emit(pixmap2)
