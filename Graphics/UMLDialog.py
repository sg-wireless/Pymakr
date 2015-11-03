# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog showing UML like diagrams.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, Qt, QFileInfo
from PyQt5.QtWidgets import QAction, QToolBar, QGraphicsScene

from E5Gui import E5MessageBox, E5FileDialog
from E5Gui.E5MainWindow import E5MainWindow

import UI.Config
import UI.PixmapCache


class UMLDialog(E5MainWindow):
    """
    Class implementing a dialog showing UML like diagrams.
    """
    NoDiagram = 255
    ClassDiagram = 0
    PackageDiagram = 1
    ImportsDiagram = 2
    ApplicationDiagram = 3
    
    FileVersions = ["1.0"]
    
    def __init__(self, diagramType, project, path="", parent=None,
                 initBuilder=True, **kwargs):
        """
        Constructor
        
        @param diagramType type of the diagram (one of ApplicationDiagram,
            ClassDiagram, ImportsDiagram, NoDiagram, PackageDiagram)
        @param project reference to the project object (Project)
        @param path file or directory path to build the diagram from (string)
        @param parent parent widget of the dialog (QWidget)
        @keyparam initBuilder flag indicating to initialize the diagram
            builder (boolean)
        @keyparam kwargs diagram specific data
        """
        super(UMLDialog, self).__init__(parent)
        self.setObjectName("UMLDialog")
        
        self.__diagramType = diagramType
        self.__project = project
        
        from .UMLGraphicsView import UMLGraphicsView
        self.scene = QGraphicsScene(0.0, 0.0, 800.0, 600.0)
        self.umlView = UMLGraphicsView(self.scene, parent=self)
        self.builder = self.__diagramBuilder(
            self.__diagramType, path, **kwargs)
        if self.builder and initBuilder:
            self.builder.initialize()
        
        self.__fileName = ""
        
        self.__initActions()
        self.__initToolBars()
        
        self.setCentralWidget(self.umlView)
        
        self.umlView.relayout.connect(self.__relayout)
        
        self.setWindowTitle(self.__diagramTypeString())
    
    def __initActions(self):
        """
        Private slot to initialize the actions.
        """
        self.closeAct = \
            QAction(UI.PixmapCache.getIcon("close.png"),
                    self.tr("Close"), self)
        self.closeAct.triggered.connect(self.close)
        
        self.openAct = \
            QAction(UI.PixmapCache.getIcon("open.png"),
                    self.tr("Load"), self)
        self.openAct.triggered.connect(self.load)
        
        self.saveAct = \
            QAction(UI.PixmapCache.getIcon("fileSave.png"),
                    self.tr("Save"), self)
        self.saveAct.triggered.connect(self.__save)
        
        self.saveAsAct = \
            QAction(UI.PixmapCache.getIcon("fileSaveAs.png"),
                    self.tr("Save As..."), self)
        self.saveAsAct.triggered.connect(self.__saveAs)
        
        self.saveImageAct = \
            QAction(UI.PixmapCache.getIcon("fileSavePixmap.png"),
                    self.tr("Save as Image"), self)
        self.saveImageAct.triggered.connect(self.umlView.saveImage)
        
        self.printAct = \
            QAction(UI.PixmapCache.getIcon("print.png"),
                    self.tr("Print"), self)
        self.printAct.triggered.connect(self.umlView.printDiagram)
        
        self.printPreviewAct = \
            QAction(UI.PixmapCache.getIcon("printPreview.png"),
                    self.tr("Print Preview"), self)
        self.printPreviewAct.triggered.connect(
            self.umlView.printPreviewDiagram)
    
    def __initToolBars(self):
        """
        Private slot to initialize the toolbars.
        """
        self.windowToolBar = QToolBar(self.tr("Window"), self)
        self.windowToolBar.setIconSize(UI.Config.ToolBarIconSize)
        self.windowToolBar.addAction(self.closeAct)
        
        self.fileToolBar = QToolBar(self.tr("File"), self)
        self.fileToolBar.setIconSize(UI.Config.ToolBarIconSize)
        self.fileToolBar.addAction(self.openAct)
        self.fileToolBar.addSeparator()
        self.fileToolBar.addAction(self.saveAct)
        self.fileToolBar.addAction(self.saveAsAct)
        self.fileToolBar.addAction(self.saveImageAct)
        self.fileToolBar.addSeparator()
        self.fileToolBar.addAction(self.printPreviewAct)
        self.fileToolBar.addAction(self.printAct)
        
        self.umlToolBar = self.umlView.initToolBar()
        
        self.addToolBar(Qt.TopToolBarArea, self.fileToolBar)
        self.addToolBar(Qt.TopToolBarArea, self.windowToolBar)
        self.addToolBar(Qt.TopToolBarArea, self.umlToolBar)
    
    def show(self, fromFile=False):
        """
        Public method to show the dialog.
        
        @keyparam fromFile flag indicating, that the diagram was loaded
            from file (boolean)
        """
        if not fromFile and self.builder:
            self.builder.buildDiagram()
        super(UMLDialog, self).show()
    
    def __relayout(self):
        """
        Private method to relayout the diagram.
        """
        if self.builder:
            self.builder.buildDiagram()
    
    def __diagramBuilder(self, diagramType, path, **kwargs):
        """
        Private method to instantiate a diagram builder object.
        
        @param diagramType type of the diagram
            (one of ApplicationDiagram, ClassDiagram, ImportsDiagram,
            PackageDiagram)
        @param path file or directory path to build the diagram from (string)
        @keyparam kwargs diagram specific data
        @return reference to the instantiated diagram builder
        @exception ValueError raised to indicate an illegal diagram type
        """
        if diagramType == UMLDialog.ClassDiagram:
            from .UMLClassDiagramBuilder import UMLClassDiagramBuilder
            return UMLClassDiagramBuilder(
                self, self.umlView, self.__project, path, **kwargs)
        elif diagramType == UMLDialog.PackageDiagram:
            from .PackageDiagramBuilder import PackageDiagramBuilder
            return PackageDiagramBuilder(
                self, self.umlView, self.__project, path, **kwargs)
        elif diagramType == UMLDialog.ImportsDiagram:
            from .ImportsDiagramBuilder import ImportsDiagramBuilder
            return ImportsDiagramBuilder(
                self, self.umlView, self.__project, path, **kwargs)
        elif diagramType == UMLDialog.ApplicationDiagram:
            from .ApplicationDiagramBuilder import ApplicationDiagramBuilder
            return ApplicationDiagramBuilder(
                self, self.umlView, self.__project, **kwargs)
        elif diagramType == UMLDialog.NoDiagram:
            return None
        else:
            raise ValueError(self.tr(
                "Illegal diagram type '{0}' given.").format(diagramType))
    
    def __diagramTypeString(self):
        """
        Private method to generate a readable string for the diagram type.
        
        @return readable type string (string)
        """
        if self.__diagramType == UMLDialog.ClassDiagram:
            return "Class Diagram"
        elif self.__diagramType == UMLDialog.PackageDiagram:
            return "Package Diagram"
        elif self.__diagramType == UMLDialog.ImportsDiagram:
            return "Imports Diagram"
        elif self.__diagramType == UMLDialog.ApplicationDiagram:
            return "Application Diagram"
        else:
            return "Illegal Diagram Type"
    
    def __save(self):
        """
        Private slot to save the diagram with the current name.
        """
        self.__saveAs(self.__fileName)
    
    @pyqtSlot()
    def __saveAs(self, filename=""):
        """
        Private slot to save the diagram.
        
        @param filename name of the file to write to (string)
        """
        if not filename:
            fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
                self,
                self.tr("Save Diagram"),
                "",
                self.tr("Eric Graphics File (*.e5g);;All Files (*)"),
                "",
                E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
            if not fname:
                return
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
            filename = fname
        
        lines = [
            "version: 1.0",
            "diagram_type: {0} ({1})".format(
                self.__diagramType, self.__diagramTypeString()),
            "scene_size: {0};{1}".format(self.scene.width(),
                                         self.scene.height()),
        ]
        persistenceData = self.builder.getPersistenceData()
        if persistenceData:
            lines.append("builder_data: {0}".format(persistenceData))
        lines.extend(self.umlView.getPersistenceData())
        
        try:
            f = open(filename, "w", encoding="utf-8")
            f.write("\n".join(lines))
            f.close()
        except (IOError, OSError) as err:
            E5MessageBox.critical(
                self,
                self.tr("Save Diagram"),
                self.tr(
                    """<p>The file <b>{0}</b> could not be saved.</p>"""
                    """<p>Reason: {1}</p>""").format(filename, str(err)))
            return
        
        self.__fileName = filename
    
    def load(self):
        """
        Public method to load a diagram from a file.
        
        @return flag indicating success (boolean)
        """
        filename = E5FileDialog.getOpenFileName(
            self,
            self.tr("Load Diagram"),
            "",
            self.tr("Eric Graphics File (*.e5g);;All Files (*)"))
        if not filename:
            # Cancelled by user
            return False
        
        try:
            f = open(filename, "r", encoding="utf-8")
            data = f.read()
            f.close()
        except (IOError, OSError) as err:
            E5MessageBox.critical(
                self,
                self.tr("Load Diagram"),
                self.tr(
                    """<p>The file <b>{0}</b> could not be read.</p>"""
                    """<p>Reason: {1}</p>""").format(filename, str(err)))
            return False
        
        lines = data.splitlines()
        if len(lines) < 3:
            self.__showInvalidDataMessage(filename)
            return False
        
        try:
            # step 1: check version
            linenum = 0
            key, value = lines[linenum].split(": ", 1)
            if key.strip() != "version" or \
                    value.strip() not in UMLDialog.FileVersions:
                self.__showInvalidDataMessage(filename, linenum)
                return False
            else:
                version = value
            
            # step 2: extract diagram type
            linenum += 1
            key, value = lines[linenum].split(": ", 1)
            if key.strip() != "diagram_type":
                self.__showInvalidDataMessage(filename, linenum)
                return False
            try:
                self.__diagramType = int(value.strip().split(None, 1)[0])
            except ValueError:
                self.__showInvalidDataMessage(filename, linenum)
                return False
            self.scene.clear()
            self.builder = self.__diagramBuilder(self.__diagramType, "")
            
            # step 3: extract scene size
            linenum += 1
            key, value = lines[linenum].split(": ", 1)
            if key.strip() != "scene_size":
                self.__showInvalidDataMessage(filename, linenum)
                return False
            try:
                width, height = [float(v.strip()) for v in value.split(";")]
            except ValueError:
                self.__showInvalidDataMessage(filename, linenum)
                return False
            self.umlView.setSceneSize(width, height)
            
            # step 4: extract builder data if available
            linenum += 1
            key, value = lines[linenum].split(": ", 1)
            if key.strip() == "builder_data":
                ok = self.builder.parsePersistenceData(version, value)
                if not ok:
                    self.__showInvalidDataMessage(filename, linenum)
                    return False
                linenum += 1
            
            # step 5: extract the graphics items
            ok, vlinenum = self.umlView.parsePersistenceData(
                version, lines[linenum:])
            if not ok:
                self.__showInvalidDataMessage(filename, linenum + vlinenum)
                return False
        
        except IndexError:
            self.__showInvalidDataMessage(filename)
            return False
        
        # everything worked fine, so remember the file name
        self.__fileName = filename
        return True
    
    def __showInvalidDataMessage(self, filename, linenum=-1):
        """
        Private slot to show a message dialog indicating an invalid data file.
        
        @param filename name of the file containing the invalid data (string)
        @param linenum number of the invalid line (integer)
        """
        if linenum < 0:
            msg = self.tr("""<p>The file <b>{0}</b> does not contain"""
                          """ valid data.</p>""").format(filename)
        else:
            msg = self.tr("""<p>The file <b>{0}</b> does not contain"""
                          """ valid data.</p><p>Invalid line: {1}</p>"""
                          ).format(filename, linenum + 1)
        E5MessageBox.critical(self, self.tr("Load Diagram"), msg)
