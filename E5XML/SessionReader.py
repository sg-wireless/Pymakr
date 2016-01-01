# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class for reading an XML session file.
"""

from __future__ import unicode_literals

from E5Gui.E5Application import e5App

from .Config import sessionFileFormatVersion
from .XMLStreamReaderBase import XMLStreamReaderBase


class SessionReader(XMLStreamReaderBase):
    """
    Class for reading an XML session file.
    """
    supportedVersions = ["4.3", "4.4", "5.0"]
    
    def __init__(self, device, isGlobal):
        """
        Constructor
        
        @param device reference to the I/O device to read from (QIODevice)
        @param isGlobal flag indicating to read the global session (boolean).
        """
        XMLStreamReaderBase.__init__(self, device)
        
        self.version = ""
        self.isGlobal = isGlobal
        
        self.project = e5App().getObject("Project")
        self.projectBrowser = e5App().getObject("ProjectBrowser")
        self.multiProject = e5App().getObject("MultiProject")
        self.vm = e5App().getObject("ViewManager")
        self.dbg = e5App().getObject("DebugUI")
        self.dbs = e5App().getObject("DebugServer")
        
        if not self.isGlobal:
            # clear all breakpoints and bookmarks first
            # (in case we are rereading a session file)
            files = self.project.getSources(True)
            for file in files:
                editor = self.vm.getOpenEditor(file)
                if editor is not None:
                    editor.clearBookmarks()
            self.dbs.getBreakPointModel().deleteAll()
            self.dbs.getWatchPointModel().deleteAll()
    
    def readXML(self, quiet=False):
        """
        Public method to read and parse the XML document.
        
        @param quiet flag indicating quiet operations.
                If this flag is true, no errors are reported.
        """
        while not self.atEnd():
            self.readNext()
            if self.isStartElement():
                if self.name() == "Session":
                    self.version = self.attribute(
                        "version", sessionFileFormatVersion)
                    if self.version not in self.supportedVersions:
                        self.raiseUnsupportedFormatVersion(self.version)
                elif self.name() == "MultiProject":
                    self.multiProject.openMultiProject(
                        self.readElementText(), False)
                elif self.name() == "Project":
                    self.project.openProject(self.readElementText(), False)
                elif self.name() == "Filenames":
                    self.__readFilenames()
                elif self.name() == "ActiveWindow":
                    cline = int(self.attribute("cline", "0"))
                    cindex = int(self.attribute("cindex", "0"))
                    filename = self.readElementText()
                    self.vm.openFiles(filename)
                    ed = self.vm.getOpenEditor(filename)
                    if ed is not None:
                        ed.setCursorPosition(cline, cindex)
                        ed.ensureCursorVisible()
                elif self.name() == "Breakpoints":
                    self.__readBreakpoints()
                elif self.name() == "Watchexpressions":
                    self.__readWatchexpressions()
                elif self.name() == "DebugInfo":
                    self.__readDebugInfo()
                elif self.name() == "Bookmarks":
                    self.__readBookmarks()
                elif self.name() == "ProjectBrowserStates":
                    self.__readProjectBrowserStates()
                else:
                    self.raiseUnexpectedStartTag(self.name())
        
        if not quiet:
            self.showErrorMessage()
    
    def __readFilenames(self):
        """
        Private method to read the file name infos.
        """
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Filenames":
                break
            
            if self.isStartElement():
                if self.name() == "Filename":
                    cline = int(self.attribute("cline", "0"))
                    cindex = int(self.attribute("cindex", "0"))
                    folds = self.attribute("folds")
                    if folds:
                        folds = [int(f) - 1 for f in folds.split(',')]
                    else:
                        folds = []
                    zoom = int(self.attribute("zoom", "-9999"))
                    filename = self.readElementText()
                    
                    self.vm.openFiles(filename)
                    ed = self.vm.getOpenEditor(filename)
                    if ed is not None:
                        if zoom > -9999:
                            ed.zoomTo(zoom)
                        if folds:
                            ed.recolor()
                            ed.setContractedFolds(folds)
                        ed.setCursorPosition(cline, cindex)
                        ed.ensureCursorVisible()
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def __readBreakpoints(self):
        """
        Private method to read the break point infos.
        """
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Breakpoints":
                break
            
            if self.isStartElement():
                if self.name() == "Breakpoint":
                    self.__readBreakpoint()
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def __readBreakpoint(self):
        """
        Private method to read the break point info.
        """
        filename = ""
        lineno = 0
        bpCond = ""
        bpTemp = False
        bpEnabled = True
        bpCount = 0
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Breakpoint":
                self.dbs.getBreakPointModel().addBreakPoint(
                    filename, lineno, (bpCond, bpTemp, bpEnabled, bpCount))
                break
            
            if self.isStartElement():
                if self.name() == "BpFilename":
                    filename = self.readElementText()
                elif self.name() == "Linenumber":
                    lineno = int(self.attribute("value", "0"))
                elif self.name() == "Condition":
                    bpCond = self.readElementText()
                    if bpCond == 'None':
                        bpCond = ''
                elif self.name() == "Temporary":
                    bpTemp = self.toBool(self.attribute("value", "False"))
                elif self.name() == "Enabled":
                    bpEnabled = self.toBool(self.attribute("value", "True"))
                elif self.name() == "Count":
                    bpCount = int(self.attribute("value", "0"))
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def __readWatchexpressions(self):
        """
        Private method to read watch expression infos.
        """
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Watchexpressions":
                break
            
            if self.isStartElement():
                if self.name() == "Watchexpression":
                    self.__readWatchexpression()
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def __readWatchexpression(self):
        """
        Private method to read the watch expression info.
        """
        weCond = ""
        weTemp = False
        weEnabled = True
        weCount = 0
        weSpecialCond = ""
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Watchexpression":
                self.dbs.getWatchPointModel().addWatchPoint(
                    weCond, weSpecialCond, (weTemp, weEnabled, weCount))
                break
            
            if self.isStartElement():
                if self.name() == "Condition":
                    weCond = self.readElementText()
                    if weCond == 'None':
                        weCond = ''
                elif self.name() == "Temporary":
                    weTemp = self.toBool(self.attribute("value", "False"))
                elif self.name() == "Enabled":
                    weEnabled = self.toBool(self.attribute("value", "True"))
                elif self.name() == "Count":
                    weCount = int(self.attribute("value", "0"))
                elif self.name() == "Special":
                    weSpecialCond = self.readElementText()
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def __readDebugInfo(self):
        """
        Private method to read the debug infos.
        """
        dbgExcList = []
        dbgExcIgnoreList = []
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement():
                if self.name() == "DebugInfo":
                    break
                elif self.name() == "Exceptions":
                    self.dbg.setExcList(dbgExcList)
                    if not self.isGlobal:
                        self.project.dbgExcList = dbgExcList[:]
                elif self.name() == "IgnoredExceptions":
                    self.dbg.setExcIgnoreList(dbgExcIgnoreList)
                    if not self.isGlobal:
                        self.project.dbgExcIgnoreList = dbgExcIgnoreList[:]
            
            if self.isStartElement():
                if self.name() == "CommandLine":
                    txt = self.readElementText()
                    self.dbg.setArgvHistory(txt)
                    if not self.isGlobal:
                        self.project.dbgCmdline = txt
                elif self.name() == "WorkingDirectory":
                    txt = self.readElementText()
                    self.dbg.setWdHistory(txt)
                    if not self.isGlobal:
                        self.project.dbgWd = txt
                elif self.name() == "Environment":
                    txt = self.readElementText()
                    self.dbg.setEnvHistory(txt)
                    if not self.isGlobal:
                        self.project.dbgEnv = txt
                elif self.name() == "ReportExceptions":
                    exc = self.toBool(self.attribute("value", "True"))
                    self.dbg.setExceptionReporting(exc)
                    if not self.isGlobal:
                        self.project.dbgReportExceptions = exc
                elif self.name() == "Exceptions":
                    pass    # ignore this start tag
                elif self.name() == "Exception":
                    dbgExcList.append(self.readElementText())
                elif self.name() == "IgnoredExceptions":
                    pass    # ignore this start tag
                elif self.name() == "IgnoredException":
                    dbgExcIgnoreList.append(self.readElementText())
                elif self.name() == "AutoClearShell":
                    val = self.toBool(self.attribute("value"))
                    self.dbg.setAutoClearShell(val)
                    if not self.isGlobal:
                        self.project.dbgAutoClearShell = val
                elif self.name() == "TracePython":
                    val = self.toBool(self.attribute("value"))
                    self.dbg.setTracePython(val)
                    if not self.isGlobal:
                        self.project.dbgTracePython = val
                elif self.name() == "AutoContinue":
                    val = self.toBool(self.attribute("value"))
                    self.dbg.setAutoContinue(val)
                    if not self.isGlobal:
                        self.project.dbgAutoContinue = val
                elif self.name() == "CovexcPattern":
                    pass    # ignore this start tag
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def __readBookmarks(self):
        """
        Private method to read the bookmark infos.
        """
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Bookmarks":
                break
            
            if self.isStartElement():
                if self.name() == "Bookmark":
                    self.__readBookmark()
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def __readBookmark(self):
        """
        Private method to read the bookmark info.
        """
        filename = ""
        lineno = 0
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Bookmark":
                editor = self.vm.getOpenEditor(filename)
                if editor is not None:
                    editor.toggleBookmark(lineno)
                break
            
            if self.isStartElement():
                if self.name() == "BmFilename":
                    filename = self.readElementText()
                elif self.name() == "Linenumber":
                    lineno = int(self.attribute("value", "0"))
                else:
                    self.raiseUnexpectedStartTag(self.name())
    
    def __readProjectBrowserStates(self):
        """
        Private method to read the project browser state infos.
        """
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "ProjectBrowserStates":
                break
            
            if self.isStartElement():
                if self.name() == "ProjectBrowserState":
                    browserName = self.attribute("name", "")
                    if not browserName:
                        self.raiseBadValue("ProjectBrowserState.name")
                    self.__readProjectBrowserState(browserName)
                else:
                    self.raiseUnexpectedStartTag(self.name())
        
    def __readProjectBrowserState(self, browserName):
        """
        Private method to read the project browser state info.
        
        @param browserName name of the project browser (string)
        """
        expandedNames = []
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "ProjectBrowserState":
                projectBrowser = \
                    self.projectBrowser.getProjectBrowser(browserName)
                if projectBrowser is not None:
                    projectBrowser.expandItemsByName(expandedNames)
                break
            
            if self.isStartElement():
                if self.name() == "ExpandedItemName":
                    itemName = self.readElementText()
                    if itemName:
                        expandedNames.append(itemName)
                else:
                    self.raiseUnexpectedStartTag(self.name())
