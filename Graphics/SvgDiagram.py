# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog showing a SVG graphic.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QSize, QEvent, qVersion
from PyQt5.QtGui import QPalette, QPainter, QFont, QColor
from PyQt5.QtWidgets import QSizePolicy, QScrollArea, QAction, QMenu, QToolBar
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtSvg import QSvgWidget

from E5Gui.E5MainWindow import E5MainWindow
from E5Gui.E5ZoomWidget import E5ZoomWidget

import UI.Config

import Preferences


class SvgDiagram(E5MainWindow):
    """
    Class implementing a dialog showing a SVG graphic.
    """
    ZoomLevels = [
        1, 3, 5, 7, 9,
        10, 20, 30, 50, 67, 80, 90,
        100,
        110, 120, 133, 150, 170, 200, 240, 300, 400,
        500, 600, 700, 800, 900, 1000,
    ]
    ZoomLevelDefault = 100
    
    def __init__(self, svgFile, parent=None, name=None):
        """
        Constructor
        
        @param svgFile filename of a SVG graphics file to show (string)
        @param parent parent widget of the view (QWidget)
        @param name name of the view widget (string)
        """
        super(SvgDiagram, self).__init__(parent)
        if name:
            self.setObjectName(name)
        else:
            self.setObjectName("SvgDiagram")
        self.setWindowTitle(self.tr("SVG-Viewer"))
        
        self.svgWidget = QSvgWidget()
        self.svgWidget.setObjectName("svgWidget")
        self.svgWidget.setBackgroundRole(QPalette.Base)
        self.svgWidget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        
        self.svgView = QScrollArea()
        self.svgView.setObjectName("svgView")
        self.svgView.setBackgroundRole(QPalette.Dark)
        self.svgView.setWidget(self.svgWidget)
        
        self.setCentralWidget(self.svgView)
        
        self.__zoomWidget = E5ZoomWidget(
            UI.PixmapCache.getPixmap("zoomOut.png"),
            UI.PixmapCache.getPixmap("zoomIn.png"),
            UI.PixmapCache.getPixmap("zoomReset.png"), self)
        self.statusBar().addPermanentWidget(self.__zoomWidget)
        self.__zoomWidget.setMapping(
            SvgDiagram.ZoomLevels, SvgDiagram.ZoomLevelDefault)
        self.__zoomWidget.valueChanged.connect(self.__doZoom)
        
        # polish up the dialog
        self.resize(QSize(800, 600).expandedTo(self.minimumSizeHint()))
        
        self.zoom = 1.0
        self.svgFile = svgFile
        self.svgWidget.load(self.svgFile)
        self.svgWidget.resize(self.svgWidget.renderer().defaultSize())
        
        self.__initActions()
        self.__initContextMenu()
        self.__initToolBars()
        
        self.grabGesture(Qt.PinchGesture)
        
    def __initActions(self):
        """
        Private method to initialize the view actions.
        """
        self.closeAct = \
            QAction(UI.PixmapCache.getIcon("close.png"),
                    self.tr("Close"), self)
        self.closeAct.triggered.connect(self.close)
        
        self.printAct = \
            QAction(UI.PixmapCache.getIcon("print.png"),
                    self.tr("Print"), self)
        self.printAct.triggered.connect(self.__printDiagram)
        
        self.printPreviewAct = \
            QAction(UI.PixmapCache.getIcon("printPreview.png"),
                    self.tr("Print Preview"), self)
        self.printPreviewAct.triggered.connect(self.__printPreviewDiagram)
        
    def __initContextMenu(self):
        """
        Private method to initialize the context menu.
        """
        self.__menu = QMenu(self)
        self.__menu.addAction(self.closeAct)
        self.__menu.addSeparator()
        self.__menu.addAction(self.printPreviewAct)
        self.__menu.addAction(self.printAct)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__showContextMenu)
        
    def __showContextMenu(self, coord):
        """
        Private slot to show the context menu of the listview.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        self.__menu.popup(self.mapToGlobal(coord))
        
    def __initToolBars(self):
        """
        Private method to populate the toolbars with our actions.
        """
        self.windowToolBar = QToolBar(self.tr("Window"), self)
        self.windowToolBar.setIconSize(UI.Config.ToolBarIconSize)
        self.windowToolBar.addAction(self.closeAct)
        
        self.graphicsToolBar = QToolBar(self.tr("Graphics"), self)
        self.graphicsToolBar.setIconSize(UI.Config.ToolBarIconSize)
        self.graphicsToolBar.addAction(self.printPreviewAct)
        self.graphicsToolBar.addAction(self.printAct)
        
        self.addToolBar(Qt.TopToolBarArea, self.windowToolBar)
        self.addToolBar(Qt.TopToolBarArea, self.graphicsToolBar)
        
    def getDiagramName(self):
        """
        Public method to retrieve a name for the diagram.
        
        @return name for the diagram
        """
        return self.svgFile
    
    def wheelEvent(self, evt):
        """
        Protected method to handle wheel events.
        
        @param evt reference to the wheel event (QWheelEvent)
        """
        if evt.modifiers() & Qt.ControlModifier:
            if qVersion() >= "5.0.0":
                delta = evt.angleDelta().y()
            else:
                delta = evt.delta()
            if delta < 0:
                self.__zoomOut()
            else:
                self.__zoomIn()
            evt.accept()
            return
        
        super(SvgDiagram, self).wheelEvent(evt)
    
    def event(self, evt):
        """
        Public method handling events.
        
        @param evt reference to the event (QEvent)
        @return flag indicating, if the event was handled (boolean)
        """
        if evt.type() == QEvent.Gesture:
            self.gestureEvent(evt)
            return True
        
        return super(SvgDiagram, self).event(evt)
    
    def gestureEvent(self, evt):
        """
        Protected method handling gesture events.
        
        @param evt reference to the gesture event (QGestureEvent
        """
        pinch = evt.gesture(Qt.PinchGesture)
        if pinch:
            if pinch.state() == Qt.GestureStarted:
                pinch.setScaleFactor(self.__zoom() / 100)
            else:
                self.__doZoom(int(pinch.scaleFactor() * 100))
            evt.accept()
    
    ###########################################################################
    ## Private menu handling methods below.
    ###########################################################################
    
    def __adjustScrollBar(self, scrollBar, factor):
        """
        Private method to adjust a scrollbar by a certain factor.
        
        @param scrollBar reference to the scrollbar object (QScrollBar)
        @param factor factor to adjust by (float)
        """
        scrollBar.setValue(
            int(factor * scrollBar.value() +
                ((factor - 1) * scrollBar.pageStep() / 2)))
        
    def __levelForZoom(self, zoom):
        """
        Private method determining the zoom level index given a zoom factor.
        
        @param zoom zoom factor (integer)
        @return index of zoom factor (integer)
        """
        try:
            index = SvgDiagram.ZoomLevels.index(zoom)
        except ValueError:
            for index in range(len(SvgDiagram.ZoomLevels)):
                if zoom <= SvgDiagram.ZoomLevels[index]:
                    break
        return index
    
    def __doZoom(self, value):
        """
        Private method to set the zoom value in percent.
        
        @param value zoom value in percent (integer)
        """
        oldValue = self.__zoom()
        if value != oldValue:
            self.svgWidget.resize(value / 100 * self.svgWidget.sizeHint())
            
            factor = value / oldValue
            self.__adjustScrollBar(self.svgView.horizontalScrollBar(), factor)
            self.__adjustScrollBar(self.svgView.verticalScrollBar(), factor)
            
            self.__zoomWidget.setValue(value)
        
    def __zoomIn(self):
        """
        Private method to zoom into the SVG.
        """
        index = self.__levelForZoom(self.__zoom())
        if index < len(SvgDiagram.ZoomLevels) - 1:
            self.__doZoom(SvgDiagram.ZoomLevels[index + 1])
        
    def __zoomOut(self):
        """
        Private method to zoom out of the SVG.
        """
        index = self.__levelForZoom(self.__zoom())
        if index > 0:
            self.__doZoom(SvgDiagram.ZoomLevels[index - 1])
        
    def __zoomReset(self):
        """
        Private method to reset the zoom value.
        """
        self.__doZoom(SvgDiagram.ZoomLevels[SvgDiagram.ZoomLevelDefault])
        
    def __zoom(self):
        """
        Private method to get the current zoom factor in percent.
        
        @return current zoom factor in percent (integer)
        """
        return int(self.svgWidget.width() /
                   self.svgWidget.sizeHint().width() * 100.0)
        
    def __printDiagram(self):
        """
        Private slot called to print the diagram.
        """
        printer = QPrinter(mode=QPrinter.ScreenResolution)
        printer.setFullPage(True)
        if Preferences.getPrinter("ColorMode"):
            printer.setColorMode(QPrinter.Color)
        else:
            printer.setColorMode(QPrinter.GrayScale)
        if Preferences.getPrinter("FirstPageFirst"):
            printer.setPageOrder(QPrinter.FirstPageFirst)
        else:
            printer.setPageOrder(QPrinter.LastPageFirst)
        printerName = Preferences.getPrinter("PrinterName")
        if printerName:
            printer.setPrinterName(printerName)
        
        printDialog = QPrintDialog(printer, self)
        if printDialog.exec_():
            self.__print(printer)
        
    def __printPreviewDiagram(self):
        """
        Private slot called to show a print preview of the diagram.
        """
        from PyQt5.QtPrintSupport import QPrintPreviewDialog
        
        printer = QPrinter(mode=QPrinter.ScreenResolution)
        printer.setFullPage(True)
        if Preferences.getPrinter("ColorMode"):
            printer.setColorMode(QPrinter.Color)
        else:
            printer.setColorMode(QPrinter.GrayScale)
        if Preferences.getPrinter("FirstPageFirst"):
            printer.setPageOrder(QPrinter.FirstPageFirst)
        else:
            printer.setPageOrder(QPrinter.LastPageFirst)
        printer.setPageMargins(
            Preferences.getPrinter("LeftMargin") * 10,
            Preferences.getPrinter("TopMargin") * 10,
            Preferences.getPrinter("RightMargin") * 10,
            Preferences.getPrinter("BottomMargin") * 10,
            QPrinter.Millimeter
        )
        printerName = Preferences.getPrinter("PrinterName")
        if printerName:
            printer.setPrinterName(printerName)
        
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested[QPrinter].connect(self.__print)
        preview.exec_()
        
    def __print(self, printer):
        """
        Private slot to the actual printing.
        
        @param printer reference to the printer object (QPrinter)
        """
        painter = QPainter()
        painter.begin(printer)

        # calculate margin and width of printout
        font = QFont("times", 10)
        painter.setFont(font)
        fm = painter.fontMetrics()
        fontHeight = fm.lineSpacing()
        marginX = printer.pageRect().x() - printer.paperRect().x()
        marginX = Preferences.getPrinter("LeftMargin") * \
            int(printer.resolution() / 2.54) - marginX
        marginY = printer.pageRect().y() - printer.paperRect().y()
        marginY = Preferences.getPrinter("TopMargin") * \
            int(printer.resolution() / 2.54) - marginY

        width = printer.width() - marginX - \
            Preferences.getPrinter("RightMargin") * \
            int(printer.resolution() / 2.54)
        height = printer.height() - fontHeight - 4 - marginY - \
            Preferences.getPrinter("BottomMargin") * \
            int(printer.resolution() / 2.54)

        # write a foot note
        s = self.tr("Diagram: {0}").format(self.getDiagramName())
        tc = QColor(50, 50, 50)
        painter.setPen(tc)
        painter.drawRect(marginX, marginY, width, height)
        painter.drawLine(marginX, marginY + height + 2,
                         marginX + width, marginY + height + 2)
        painter.setFont(font)
        painter.drawText(marginX, marginY + height + 4, width,
                         fontHeight, Qt.AlignRight, s)

        # render the diagram
        painter.setViewport(marginX, marginY, width, height)
        self.svgWidget.renderer().render(painter)
        painter.end()
