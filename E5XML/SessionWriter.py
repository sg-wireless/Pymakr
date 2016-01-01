# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the writer class for writing an XML session file.
"""

from __future__ import unicode_literals

import time

from E5Gui.E5Application import e5App

from .XMLStreamWriterBase import XMLStreamWriterBase
from .Config import sessionFileFormatVersion

import Preferences


class SessionWriter(XMLStreamWriterBase):
    """
    Class implementing the writer class for writing an XML session file.
    """
    def __init__(self, device, projectName):
        """
        Constructor
        
        @param device reference to the I/O device to write to (QIODevice)
        @param projectName name of the project (string) or None for the
            global session
        """
        XMLStreamWriterBase.__init__(self, device)
        
        self.name = projectName
        self.project = e5App().getObject("Project")
        self.projectBrowser = e5App().getObject("ProjectBrowser")
        self.multiProject = e5App().getObject("MultiProject")
        self.vm = e5App().getObject("ViewManager")
        self.dbg = e5App().getObject("DebugUI")
        self.dbs = e5App().getObject("DebugServer")
        
    def writeXML(self):
        """
        Public method to write the XML to the file.
        """
        isGlobal = self.name is None
        
        XMLStreamWriterBase.writeXML(self)
        
        self.writeDTD('<!DOCTYPE Session SYSTEM "Session-{0}.dtd">'.format(
            sessionFileFormatVersion))
        
        # add some generation comments
        if not isGlobal:
            self.writeComment(
                " eric6 session file for project {0} ".format(self.name))
        self.writeComment(
            " This file was generated automatically, do not edit. ")
        if Preferences.getProject("XMLTimestamp") or isGlobal:
            self.writeComment(
                " Saved: {0} ".format(time.strftime('%Y-%m-%d, %H:%M:%S')))
        
        # add the main tag
        self.writeStartElement("Session")
        self.writeAttribute("version", sessionFileFormatVersion)
        
        # step 0: save open multi project and project for the global session
        if isGlobal:
            if self.multiProject.isOpen():
                self.writeTextElement(
                    "MultiProject", self.multiProject.getMultiProjectFile())
            if self.project.isOpen():
                self.writeTextElement("Project", self.project.getProjectFile())
        
        # step 1: save all open (project) filenames and the active window
        allOpenFiles = self.vm.getOpenFilenames()
        self.writeStartElement("Filenames")
        for of in allOpenFiles:
            if isGlobal or of.startswith(self.project.ppath):
                ed = self.vm.getOpenEditor(of)
                if ed is not None:
                    line, index = ed.getCursorPosition()
                    folds = ','.join(
                        [str(i + 1) for i in ed.contractedFolds()])
                    zoom = ed.getZoom()
                else:
                    line, index = 0, 0
                    folds = ''
                    zoom = -9999
                self.writeStartElement("Filename")
                self.writeAttribute("cline", str(line))
                self.writeAttribute("cindex", str(index))
                self.writeAttribute("folds", folds)
                self.writeAttribute("zoom", str(zoom))
                self.writeCharacters(of)
                self.writeEndElement()
        self.writeEndElement()
        
        aw = self.vm.getActiveName()
        if aw and aw.startswith(self.project.ppath):
            ed = self.vm.getOpenEditor(aw)
            if ed is not None:
                line, index = ed.getCursorPosition()
            else:
                line, index = 0, 0
            self.writeStartElement("ActiveWindow")
            self.writeAttribute("cline", str(line))
            self.writeAttribute("cindex", str(index))
            self.writeCharacters(aw)
            self.writeEndElement()
        
        # step 2a: save all breakpoints
        allBreaks = Preferences.getProject("SessionAllBreakpoints")
        projectFiles = self.project.getSources(True)
        bpModel = self.dbs.getBreakPointModel()
        self.writeStartElement("Breakpoints")
        for row in range(bpModel.rowCount()):
            index = bpModel.index(row, 0)
            fname, lineno, cond, temp, enabled, count = \
                bpModel.getBreakPointByIndex(index)[:6]
            if isGlobal or allBreaks or fname in projectFiles:
                self.writeStartElement("Breakpoint")
                self.writeTextElement("BpFilename", fname)
                self.writeEmptyElement("Linenumber")
                self.writeAttribute("value", str(lineno))
                self.writeTextElement("Condition", str(cond))
                self.writeEmptyElement("Temporary")
                self.writeAttribute("value", str(temp))
                self.writeEmptyElement("Enabled")
                self.writeAttribute("value", str(enabled))
                self.writeEmptyElement("Count")
                self.writeAttribute("value", str(count))
                self.writeEndElement()
        self.writeEndElement()
        
        # step 2b: save all watch expressions
        self.writeStartElement("Watchexpressions")
        wpModel = self.dbs.getWatchPointModel()
        for row in range(wpModel.rowCount()):
            index = wpModel.index(row, 0)
            cond, special, temp, enabled, count = \
                wpModel.getWatchPointByIndex(index)[:5]
            self.writeStartElement("Watchexpression")
            self.writeTextElement("Condition", str(cond))
            self.writeEmptyElement("Temporary")
            self.writeAttribute("value", str(temp))
            self.writeEmptyElement("Enabled")
            self.writeAttribute("value", str(enabled))
            self.writeEmptyElement("Count")
            self.writeAttribute("value", str(count))
            self.writeTextElement("Special", special)
            self.writeEndElement()
        self.writeEndElement()
        
        # step 3: save the debug info
        self.writeStartElement("DebugInfo")
        if isGlobal:
            if len(self.dbg.argvHistory):
                dbgCmdline = str(self.dbg.argvHistory[0])
            else:
                dbgCmdline = ""
            if len(self.dbg.wdHistory):
                dbgWd = self.dbg.wdHistory[0]
            else:
                dbgWd = ""
            if len(self.dbg.envHistory):
                dbgEnv = self.dbg.envHistory[0]
            else:
                dbgEnv = ""
            self.writeTextElement("CommandLine", dbgCmdline)
            self.writeTextElement("WorkingDirectory", dbgWd)
            self.writeTextElement("Environment", dbgEnv)
            self.writeEmptyElement("ReportExceptions")
            self.writeAttribute("value", str(self.dbg.exceptions))
            self.writeStartElement("Exceptions")
            for exc in self.dbg.excList:
                self.writeTextElement("Exception", exc)
            self.writeEndElement()
            self.writeStartElement("IgnoredExceptions")
            for iexc in self.dbg.excIgnoreList:
                self.writeTextElement("IgnoredException", iexc)
            self.writeEndElement()
            self.writeEmptyElement("AutoClearShell")
            self.writeAttribute("value", str(self.dbg.autoClearShell))
            self.writeEmptyElement("TracePython")
            self.writeAttribute("value", str(self.dbg.tracePython))
            self.writeEmptyElement("AutoContinue")
            self.writeAttribute("value", str(self.dbg.autoContinue))
            self.writeEmptyElement("CovexcPattern")    # kept for compatibility
        else:
            self.writeTextElement("CommandLine", self.project.dbgCmdline)
            self.writeTextElement("WorkingDirectory", self.project.dbgWd)
            self.writeTextElement("Environment", self.project.dbgEnv)
            self.writeEmptyElement("ReportExceptions")
            self.writeAttribute("value", str(self.project.dbgReportExceptions))
            self.writeStartElement("Exceptions")
            for exc in self.project.dbgExcList:
                self.writeTextElement("Exception", exc)
            self.writeEndElement()
            self.writeStartElement("IgnoredExceptions")
            for iexc in self.project.dbgExcIgnoreList:
                self.writeTextElement("IgnoredException", iexc)
            self.writeEndElement()
            self.writeEmptyElement("AutoClearShell")
            self.writeAttribute("value", str(self.project.dbgAutoClearShell))
            self.writeEmptyElement("TracePython")
            self.writeAttribute("value", str(self.project.dbgTracePython))
            self.writeEmptyElement("AutoContinue")
            self.writeAttribute("value", str(self.project.dbgAutoContinue))
            self.writeEmptyElement("CovexcPattern")    # kept for compatibility
        self.writeEndElement()
        
        # step 4: save bookmarks of all open (project) files
        self.writeStartElement("Bookmarks")
        for of in allOpenFiles:
            if isGlobal or of.startswith(self.project.ppath):
                editor = self.vm.getOpenEditor(of)
                for bookmark in editor.getBookmarks():
                    self.writeStartElement("Bookmark")
                    self.writeTextElement("BmFilename", of)
                    self.writeEmptyElement("Linenumber")
                    self.writeAttribute("value", str(bookmark))
                    self.writeEndElement()
        self.writeEndElement()
        
        # step 5: save state of the various project browsers
        if not isGlobal:
            self.writeStartElement("ProjectBrowserStates")
            for browserName in self.projectBrowser.getProjectBrowserNames():
                self.writeStartElement("ProjectBrowserState")
                self.writeAttribute("name", browserName)
                # get the names of expanded files and directories
                names = self.projectBrowser\
                    .getProjectBrowser(browserName).getExpandedItemNames()
                for name in names:
                    self.writeTextElement("ExpandedItemName", name)
                self.writeEndElement()
            self.writeEndElement()
        
        # add the main end tag
        self.writeEndElement()
        self.writeEndDocument()
