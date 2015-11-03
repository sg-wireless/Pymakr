# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a subclass of E5GraphicsView for our diagrams.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt, QSignalMapper, QFileInfo, QEvent, \
    QRectF, qVersion
from PyQt5.QtWidgets import QGraphicsView, QAction, QToolBar, QDialog
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

from E5Graphics.E5GraphicsView import E5GraphicsView

from E5Gui import E5MessageBox, E5FileDialog
from E5Gui.E5ZoomWidget import E5ZoomWidget

from .UMLItem import UMLItem

import UI.Config
import UI.PixmapCache

import Preferences


class UMLGraphicsView(E5GraphicsView):
    """
    Class implementing a specialized E5GraphicsView for our diagrams.
    
    @signal relayout() emitted to indicate a relayout of the diagram
        is requested
    """
    relayout = pyqtSignal()
    
    def __init__(self, scene, parent=None):
        """
        Constructor
        
        @param scene reference to the scene object (QGraphicsScene)
        @param parent parent widget of the view (QWidget)
        """
        E5GraphicsView.__init__(self, scene, parent)
        self.setObjectName("UMLGraphicsView")
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        self.diagramName = "Unnamed"
        self.__itemId = -1
        
        self.border = 10
        self.deltaSize = 100.0
        
        self.__zoomWidget = E5ZoomWidget(
            UI.PixmapCache.getPixmap("zoomOut.png"),
            UI.PixmapCache.getPixmap("zoomIn.png"),
            UI.PixmapCache.getPixmap("zoomReset.png"), self)
        parent.statusBar().addPermanentWidget(self.__zoomWidget)
        self.__zoomWidget.setMapping(
            E5GraphicsView.ZoomLevels, E5GraphicsView.ZoomLevelDefault)
        self.__zoomWidget.valueChanged.connect(self.setZoom)
        self.zoomValueChanged.connect(self.__zoomWidget.setValue)
        
        self.__initActions()
        
        scene.changed.connect(self.__sceneChanged)
        
        self.grabGesture(Qt.PinchGesture)
        
    def __initActions(self):
        """
        Private method to initialize the view actions.
        """
        self.alignMapper = QSignalMapper(self)
        self.alignMapper.mapped[int].connect(self.__alignShapes)
        
        self.deleteShapeAct = \
            QAction(UI.PixmapCache.getIcon("deleteShape.png"),
                    self.tr("Delete shapes"), self)
        self.deleteShapeAct.triggered.connect(self.__deleteShape)
        
        self.incWidthAct = \
            QAction(UI.PixmapCache.getIcon("sceneWidthInc.png"),
                    self.tr("Increase width by {0} points").format(
                        self.deltaSize),
                    self)
        self.incWidthAct.triggered.connect(self.__incWidth)
        
        self.incHeightAct = \
            QAction(UI.PixmapCache.getIcon("sceneHeightInc.png"),
                    self.tr("Increase height by {0} points").format(
                        self.deltaSize),
                    self)
        self.incHeightAct.triggered.connect(self.__incHeight)
        
        self.decWidthAct = \
            QAction(UI.PixmapCache.getIcon("sceneWidthDec.png"),
                    self.tr("Decrease width by {0} points").format(
                        self.deltaSize),
                    self)
        self.decWidthAct.triggered.connect(self.__decWidth)
        
        self.decHeightAct = \
            QAction(UI.PixmapCache.getIcon("sceneHeightDec.png"),
                    self.tr("Decrease height by {0} points").format(
                        self.deltaSize),
                    self)
        self.decHeightAct.triggered.connect(self.__decHeight)
        
        self.setSizeAct = \
            QAction(UI.PixmapCache.getIcon("sceneSize.png"),
                    self.tr("Set size"), self)
        self.setSizeAct.triggered.connect(self.__setSize)
        
        self.rescanAct = \
            QAction(UI.PixmapCache.getIcon("rescan.png"),
                    self.tr("Re-Scan"), self)
        self.rescanAct.triggered.connect(self.__rescan)
        
        self.relayoutAct = \
            QAction(UI.PixmapCache.getIcon("relayout.png"),
                    self.tr("Re-Layout"), self)
        self.relayoutAct.triggered.connect(self.__relayout)
        
        self.alignLeftAct = \
            QAction(UI.PixmapCache.getIcon("shapesAlignLeft.png"),
                    self.tr("Align Left"), self)
        self.alignMapper.setMapping(self.alignLeftAct, Qt.AlignLeft)
        self.alignLeftAct.triggered.connect(self.alignMapper.map)
        
        self.alignHCenterAct = \
            QAction(UI.PixmapCache.getIcon("shapesAlignHCenter.png"),
                    self.tr("Align Center Horizontal"), self)
        self.alignMapper.setMapping(self.alignHCenterAct, Qt.AlignHCenter)
        self.alignHCenterAct.triggered.connect(self.alignMapper.map)
        
        self.alignRightAct = \
            QAction(UI.PixmapCache.getIcon("shapesAlignRight.png"),
                    self.tr("Align Right"), self)
        self.alignMapper.setMapping(self.alignRightAct, Qt.AlignRight)
        self.alignRightAct.triggered.connect(self.alignMapper.map)
        
        self.alignTopAct = \
            QAction(UI.PixmapCache.getIcon("shapesAlignTop.png"),
                    self.tr("Align Top"), self)
        self.alignMapper.setMapping(self.alignTopAct, Qt.AlignTop)
        self.alignTopAct.triggered.connect(self.alignMapper.map)
        
        self.alignVCenterAct = \
            QAction(UI.PixmapCache.getIcon("shapesAlignVCenter.png"),
                    self.tr("Align Center Vertical"), self)
        self.alignMapper.setMapping(self.alignVCenterAct, Qt.AlignVCenter)
        self.alignVCenterAct.triggered.connect(self.alignMapper.map)
        
        self.alignBottomAct = \
            QAction(UI.PixmapCache.getIcon("shapesAlignBottom.png"),
                    self.tr("Align Bottom"), self)
        self.alignMapper.setMapping(self.alignBottomAct, Qt.AlignBottom)
        self.alignBottomAct.triggered.connect(self.alignMapper.map)
        
    def __checkSizeActions(self):
        """
        Private slot to set the enabled state of the size actions.
        """
        diagramSize = self._getDiagramSize(10)
        sceneRect = self.scene().sceneRect()
        if (sceneRect.width() - self.deltaSize) < diagramSize.width():
            self.decWidthAct.setEnabled(False)
        else:
            self.decWidthAct.setEnabled(True)
        if (sceneRect.height() - self.deltaSize) < diagramSize.height():
            self.decHeightAct.setEnabled(False)
        else:
            self.decHeightAct.setEnabled(True)
        
    def __sceneChanged(self, areas):
        """
        Private slot called when the scene changes.
        
        @param areas list of rectangles that contain changes (list of QRectF)
        """
        if len(self.scene().selectedItems()) > 0:
            self.deleteShapeAct.setEnabled(True)
        else:
            self.deleteShapeAct.setEnabled(False)
        
        sceneRect = self.scene().sceneRect()
        newWidth = width = sceneRect.width()
        newHeight = height = sceneRect.height()
        rect = self.scene().itemsBoundingRect()
        # calculate with 10 pixel border on each side
        if sceneRect.right() - 10 < rect.right():
            newWidth = rect.right() + 10
        if sceneRect.bottom() - 10 < rect.bottom():
            newHeight = rect.bottom() + 10
        
        if newHeight != height or newWidth != width:
            self.setSceneSize(newWidth, newHeight)
            self.__checkSizeActions()
        
    def initToolBar(self):
        """
        Public method to populate a toolbar with our actions.
        
        @return the populated toolBar (QToolBar)
        """
        toolBar = QToolBar(self.tr("Graphics"), self)
        toolBar.setIconSize(UI.Config.ToolBarIconSize)
        toolBar.addAction(self.deleteShapeAct)
        toolBar.addSeparator()
        toolBar.addAction(self.alignLeftAct)
        toolBar.addAction(self.alignHCenterAct)
        toolBar.addAction(self.alignRightAct)
        toolBar.addAction(self.alignTopAct)
        toolBar.addAction(self.alignVCenterAct)
        toolBar.addAction(self.alignBottomAct)
        toolBar.addSeparator()
        toolBar.addAction(self.incWidthAct)
        toolBar.addAction(self.incHeightAct)
        toolBar.addAction(self.decWidthAct)
        toolBar.addAction(self.decHeightAct)
        toolBar.addAction(self.setSizeAct)
        toolBar.addSeparator()
        toolBar.addAction(self.rescanAct)
        toolBar.addAction(self.relayoutAct)
        
        return toolBar
        
    def filteredItems(self, items, itemType=UMLItem):
        """
        Public method to filter a list of items.
        
        @param items list of items as returned by the scene object
            (QGraphicsItem)
        @param itemType type to be filtered (class)
        @return list of interesting collision items (QGraphicsItem)
        """
        return [itm for itm in items if isinstance(itm, itemType)]
        
    def selectItems(self, items):
        """
        Public method to select the given items.
        
        @param items list of items to be selected (list of QGraphicsItemItem)
        """
        # step 1: deselect all items
        self.unselectItems()
        
        # step 2: select all given items
        for itm in items:
            if isinstance(itm, UMLItem):
                itm.setSelected(True)
        
    def selectItem(self, item):
        """
        Public method to select an item.
        
        @param item item to be selected (QGraphicsItemItem)
        """
        if isinstance(item, UMLItem):
            item.setSelected(not item.isSelected())
        
    def __deleteShape(self):
        """
        Private method to delete the selected shapes from the display.
        """
        for item in self.scene().selectedItems():
            item.removeAssociations()
            item.setSelected(False)
            self.scene().removeItem(item)
            del item
        
    def __incWidth(self):
        """
        Private method to handle the increase width context menu entry.
        """
        self.resizeScene(self.deltaSize, True)
        self.__checkSizeActions()
        
    def __incHeight(self):
        """
        Private method to handle the increase height context menu entry.
        """
        self.resizeScene(self.deltaSize, False)
        self.__checkSizeActions()
        
    def __decWidth(self):
        """
        Private method to handle the decrease width context menu entry.
        """
        self.resizeScene(-self.deltaSize, True)
        self.__checkSizeActions()
        
    def __decHeight(self):
        """
        Private method to handle the decrease height context menu entry.
        """
        self.resizeScene(-self.deltaSize, False)
        self.__checkSizeActions()
        
    def __setSize(self):
        """
        Private method to handle the set size context menu entry.
        """
        from .UMLSceneSizeDialog import UMLSceneSizeDialog
        rect = self._getDiagramRect(10)
        sceneRect = self.scene().sceneRect()
        dlg = UMLSceneSizeDialog(sceneRect.width(), sceneRect.height(),
                                 rect.width(), rect.height(), self)
        if dlg.exec_() == QDialog.Accepted:
            width, height = dlg.getData()
            self.setSceneSize(width, height)
        self.__checkSizeActions()
        
    def autoAdjustSceneSize(self, limit=False):
        """
        Public method to adjust the scene size to the diagram size.
        
        @param limit flag indicating to limit the scene to the
            initial size (boolean)
        """
        super(UMLGraphicsView, self).autoAdjustSceneSize(limit=limit)
        self.__checkSizeActions()
        
    def saveImage(self):
        """
        Public method to handle the save context menu entry.
        """
        fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            self,
            self.tr("Save Diagram"),
            "",
            self.tr("Portable Network Graphics (*.png);;"
                    "Scalable Vector Graphics (*.svg)"),
            "",
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        if fname:
            ext = QFileInfo(fname).suffix()
            if not ext:
                ex = selectedFilter.split("(*")[1].split(")")[0]
                if ex:
                    fname += ex
            if QFileInfo(fname).exists():
                res = E5MessageBox.yesNo(
                    self,
                    self.tr("Save Diagram"),
                    self.tr("<p>The file <b>{0}</b> already exists."
                            " Overwrite it?</p>").format(fname),
                    icon=E5MessageBox.Warning)
                if not res:
                    return
            
            success = super(UMLGraphicsView, self).saveImage(
                fname, QFileInfo(fname).suffix().upper())
            if not success:
                E5MessageBox.critical(
                    self,
                    self.tr("Save Diagram"),
                    self.tr(
                        """<p>The file <b>{0}</b> could not be saved.</p>""")
                    .format(fname))
        
    def __relayout(self):
        """
        Private slot to handle the re-layout context menu entry.
        """
        self.__itemId = -1
        self.scene().clear()
        self.relayout.emit()
        
    def __rescan(self):
        """
        Private slot to handle the re-scan context menu entry.
        """
        # 1. save positions of all items and names of selected items
        itemPositions = {}
        selectedItems = []
        for item in self.filteredItems(self.scene().items(), UMLItem):
            name = item.getName()
            if name:
                itemPositions[name] = (item.x(), item.y())
                if item.isSelected():
                    selectedItems.append(name)
        
        # 2. save
        
        # 2. re-layout the diagram
        self.__relayout()
        
        # 3. move known items to the saved positions
        for item in self.filteredItems(self.scene().items(), UMLItem):
            name = item.getName()
            if name in itemPositions:
                item.setPos(*itemPositions[name])
            if name in selectedItems:
                item.setSelected(True)
        
    def printDiagram(self):
        """
        Public slot called to print the diagram.
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
        
        printDialog = QPrintDialog(printer, self)
        if printDialog.exec_():
            super(UMLGraphicsView, self).printDiagram(
                printer, self.diagramName)
        
    def printPreviewDiagram(self):
        """
        Public slot called to show a print preview of the diagram.
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
        preview.paintRequested[QPrinter].connect(self.__printPreviewPrint)
        preview.exec_()
        
    def __printPreviewPrint(self, printer):
        """
        Private slot to generate a print preview.
        
        @param printer reference to the printer object (QPrinter)
        """
        super(UMLGraphicsView, self).printDiagram(printer, self.diagramName)
        
    def setDiagramName(self, name):
        """
        Public slot to set the diagram name.
        
        @param name diagram name (string)
        """
        self.diagramName = name
        
    def __alignShapes(self, alignment):
        """
        Private slot to align the selected shapes.
        
        @param alignment alignment type (Qt.AlignmentFlag)
        """
        # step 1: get all selected items
        items = self.scene().selectedItems()
        if len(items) <= 1:
            return
        
        # step 2: find the index of the item to align in relation to
        amount = None
        for i, item in enumerate(items):
            rect = item.sceneBoundingRect()
            if alignment == Qt.AlignLeft:
                if amount is None or rect.x() < amount:
                    amount = rect.x()
                    index = i
            elif alignment == Qt.AlignRight:
                if amount is None or rect.x() + rect.width() > amount:
                    amount = rect.x() + rect.width()
                    index = i
            elif alignment == Qt.AlignHCenter:
                if amount is None or rect.width() > amount:
                    amount = rect.width()
                    index = i
            elif alignment == Qt.AlignTop:
                if amount is None or rect.y() < amount:
                    amount = rect.y()
                    index = i
            elif alignment == Qt.AlignBottom:
                if amount is None or rect.y() + rect.height() > amount:
                    amount = rect.y() + rect.height()
                    index = i
            elif alignment == Qt.AlignVCenter:
                if amount is None or rect.height() > amount:
                    amount = rect.height()
                    index = i
        rect = items[index].sceneBoundingRect()
        
        # step 3: move the other items
        for i, item in enumerate(items):
            if i == index:
                continue
            itemrect = item.sceneBoundingRect()
            xOffset = yOffset = 0
            if alignment == Qt.AlignLeft:
                xOffset = rect.x() - itemrect.x()
            elif alignment == Qt.AlignRight:
                xOffset = (rect.x() + rect.width()) - \
                          (itemrect.x() + itemrect.width())
            elif alignment == Qt.AlignHCenter:
                xOffset = (rect.x() + rect.width() // 2) - \
                          (itemrect.x() + itemrect.width() // 2)
            elif alignment == Qt.AlignTop:
                yOffset = rect.y() - itemrect.y()
            elif alignment == Qt.AlignBottom:
                yOffset = (rect.y() + rect.height()) - \
                          (itemrect.y() + itemrect.height())
            elif alignment == Qt.AlignVCenter:
                yOffset = (rect.y() + rect.height() // 2) - \
                          (itemrect.y() + itemrect.height() // 2)
            item.moveBy(xOffset, yOffset)
        
        self.scene().update()
    
    def __itemsBoundingRect(self, items):
        """
        Private method to calculate the bounding rectangle of the given items.
        
        @param items list of items to operate on (list of UMLItem)
        @return bounding rectangle (QRectF)
        """
        rect = self.scene().sceneRect()
        right = rect.left()
        bottom = rect.top()
        left = rect.right()
        top = rect.bottom()
        for item in items:
            rect = item.sceneBoundingRect()
            left = min(rect.left(), left)
            right = max(rect.right(), right)
            top = min(rect.top(), top)
            bottom = max(rect.bottom(), bottom)
        return QRectF(left, top, right - left, bottom - top)
    
    def keyPressEvent(self, evt):
        """
        Protected method handling key press events.
        
        @param evt reference to the key event (QKeyEvent)
        """
        key = evt.key()
        if key in [Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right]:
            items = self.filteredItems(self.scene().selectedItems())
            if items:
                if evt.modifiers() & Qt.ControlModifier:
                    stepSize = 50
                else:
                    stepSize = 5
                if key == Qt.Key_Up:
                    dx = 0
                    dy = -stepSize
                elif key == Qt.Key_Down:
                    dx = 0
                    dy = stepSize
                elif key == Qt.Key_Left:
                    dx = -stepSize
                    dy = 0
                else:
                    dx = stepSize
                    dy = 0
                for item in items:
                    item.moveBy(dx, dy)
                evt.accept()
                return
        
        super(UMLGraphicsView, self).keyPressEvent(evt)
    
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
                self.zoomOut()
            else:
                self.zoomIn()
            evt.accept()
            return
        
        super(UMLGraphicsView, self).wheelEvent(evt)
    
    def event(self, evt):
        """
        Public method handling events.
        
        @param evt reference to the event (QEvent)
        @return flag indicating, if the event was handled (boolean)
        """
        if evt.type() == QEvent.Gesture:
            self.gestureEvent(evt)
            return True
        
        return super(UMLGraphicsView, self).event(evt)
    
    def gestureEvent(self, evt):
        """
        Protected method handling gesture events.
        
        @param evt reference to the gesture event (QGestureEvent
        """
        pinch = evt.gesture(Qt.PinchGesture)
        if pinch:
            if pinch.state() == Qt.GestureStarted:
                pinch.setScaleFactor(self.zoom() / 100.0)
            else:
                self.setZoom(int(pinch.scaleFactor() * 100))
            evt.accept()
    
    def getItemId(self):
        """
        Public method to get the ID to be assigned to an item.
        
        @return item ID (integer)
        """
        self.__itemId += 1
        return self.__itemId

    def findItem(self, id):
        """
        Public method to find an UML item based on the ID.
        
        @param id of the item to search for (integer)
        @return item found (UMLItem) or None
        """
        for item in self.scene().items():
            try:
                if item.getId() == id:
                    return item
            except AttributeError:
                continue
        
        return None
    
    def findItemByName(self, name):
        """
        Public method to find an UML item based on its name.
        
        @param name name to look for (string)
        @return item found (UMLItem) or None
        """
        for item in self.scene().items():
            try:
                if item.getName() == name:
                    return item
            except AttributeError:
                continue
        
        return None
    
    def getPersistenceData(self):
        """
        Public method to get a list of data to be persisted.
        
        @return list of data to be persisted (list of strings)
        """
        lines = [
            "diagram_name: {0}".format(self.diagramName),
        ]
        
        for item in self.filteredItems(self.scene().items(), UMLItem):
            lines.append("item: id={0}, x={1}, y={2}, item_type={3}{4}".format(
                item.getId(), item.x(), item.y(), item.getItemType(),
                item.buildItemDataString()))
        
        from .AssociationItem import AssociationItem
        for item in self.filteredItems(self.scene().items(), AssociationItem):
            lines.append("association: {0}".format(
                item.buildAssociationItemDataString()))
        
        return lines
    
    def parsePersistenceData(self, version, data):
        """
        Public method to parse persisted data.
        
        @param version version of the data (string)
        @param data persisted data to be parsed (list of string)
        @return tuple of flag indicating success (boolean) and faulty line
            number (integer)
        """
        umlItems = {}
        
        if not data[0].startswith("diagram_name:"):
            return False, 0
        self.diagramName = data[0].split(": ", 1)[1].strip()
        
        from .ClassItem import ClassItem
        from .ModuleItem import ModuleItem
        from .PackageItem import PackageItem
        from .AssociationItem import AssociationItem
        
        linenum = 0
        for line in data[1:]:
            linenum += 1
            if not line.startswith(("item:", "association:")):
                return False, linenum
            
            key, value = line.split(": ", 1)
            if key == "item":
                id, x, y, itemType, itemData = value.split(", ", 4)
                try:
                    id = int(id.split("=", 1)[1].strip())
                    x = float(x.split("=", 1)[1].strip())
                    y = float(y.split("=", 1)[1].strip())
                    itemType = itemType.split("=", 1)[1].strip()
                    if itemType == ClassItem.ItemType:
                        itm = ClassItem(x=x, y=y, scene=self.scene())
                    elif itemType == ModuleItem.ItemType:
                        itm = ModuleItem(x=x, y=y, scene=self.scene())
                    elif itemType == PackageItem.ItemType:
                        itm = PackageItem(x=x, y=y, scene=self.scene())
                    itm.setId(id)
                    umlItems[id] = itm
                    if not itm.parseItemDataString(version, itemData):
                        return False, linenum
                except ValueError:
                    return False, linenum
            elif key == "association":
                srcId, dstId, assocType, topToBottom = \
                    AssociationItem.parseAssociationItemDataString(
                        value.strip())
                assoc = AssociationItem(umlItems[srcId], umlItems[dstId],
                                        assocType, topToBottom)
                self.scene().addItem(assoc)
        
        return True, -1
