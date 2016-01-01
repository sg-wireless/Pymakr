# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class for reading an XML tasks file.
"""

from __future__ import unicode_literals

import time

from E5Gui.E5Application import e5App

from .Config import tasksFileFormatVersion
from .XMLStreamReaderBase import XMLStreamReaderBase

from Tasks.Task import Task

import Utilities


class TasksReader(XMLStreamReaderBase):
    """
    Class for reading an XML tasks file.
    """
    supportedVersions = ["4.2", "5.0", "5.1", "6.0"]
    
    def __init__(self, device, forProject=False, viewer=None):
        """
        Constructor
        
        @param device reference to the I/O device to read from (QIODevice)
        @param forProject flag indicating project related mode (boolean)
        @param viewer reference to the task viewer (TaskViewer)
        """
        XMLStreamReaderBase.__init__(self, device)
        
        self.viewer = viewer
        
        self.forProject = forProject
        if viewer:
            self.viewer = viewer
        else:
            self.viewer = e5App().getObject("TaskViewer")
        
        self.version = ""
        self.tasks = []
    
    def readXML(self):
        """
        Public method to read and parse the XML document.
        """
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Tasks":
                for task, expanded in self.tasks:
                    task.setExpanded(expanded)
                break
            
            if self.isStartElement():
                if self.name() == "Tasks":
                    self.version = self.attribute(
                        "version", tasksFileFormatVersion)
                    if self.version not in self.supportedVersions:
                        self.raiseUnsupportedFormatVersion(self.version)
                elif self.name() == "Task":
                    self.__readTask()
                elif self.name() == "ProjectScanFilter":
                    filter = self.readElementText()
                    if self.forProject:
                        self.viewer.projectTasksScanFilter = filter
                else:
                    self.raiseUnexpectedStartTag(self.name())
        
        self.showErrorMessage()
    
    def __readTask(self):
        """
        Private method to read the task info.
        """
        task = {"summary": "",
                "priority": 1,
                "completed": False,
                "created": 0,
                "filename": "",
                "linenumber": 0,
                "type": Task.TypeTodo,
                "description": "",
                "uid": "",
                }
        task["priority"] = int(self.attribute("priority", "1"))
        task["completed"] = self.toBool(self.attribute("completed", "False"))
        if self.version in ["4.2", "5.0"]:
            isBugfix = self.toBool(self.attribute("bugfix", "False"))
            if isBugfix:
                task["type"] = Task.TypeFixme
        else:
            task["type"] = int(self.attribute("type", str(Task.TypeTodo)))
        uid = self.attribute("uid", "")
        if uid:
            task["uid"] = uid
        else:
            # upgrade from pre 6.0 format
            from PyQt5.QtCore import QUuid
            task["uid"] = QUuid.createUuid().toString()
        parentUid = self.attribute("parent_uid", "")
        expanded = self.toBool(self.attribute("expanded", "True"))
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Task":
                parentTask = self.viewer.findParentTask(parentUid)
                addedTask = self.viewer.addTask(
                    task["summary"], priority=task["priority"],
                    filename=task["filename"], lineno=task["linenumber"],
                    completed=task["completed"], _time=task["created"],
                    isProjectTask=self.forProject, taskType=task["type"],
                    description=task["description"], uid=task["uid"],
                    parentTask=parentTask)
                self.tasks.append((addedTask, expanded))
                break
            
            if self.isStartElement():
                if self.name() == "Summary":
                    task["summary"] = self.readElementText()
                elif self.name() == "Description":
                    task["description"] = self.readElementText()
                elif self.name() == "Created":
                    task["created"] = time.mktime(time.strptime(
                        self.readElementText(), "%Y-%m-%d, %H:%M:%S"))
                elif self.name() == "Resource":
                    continue    # handle but ignore this tag
                elif self.name() == "Filename":
                    task["filename"] = \
                        Utilities.toNativeSeparators(self.readElementText())
                elif self.name() == "Linenumber":
                    try:
                        task["linenumber"] = int(self.readElementText())
                    except ValueError:
                        pass
                else:
                    self.raiseUnexpectedStartTag(self.name())
