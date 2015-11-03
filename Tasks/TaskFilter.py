# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class to store task data.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QRegExp

from .Task import Task


class TaskFilter(object):
    """
    Class implementing a filter for tasks.
    """
    def __init__(self):
        """
        Constructor
        """
        self.active = False
        
        self.summaryFilter = None
        self.filenameFilter = None
        self.typeFilter = Task.TypeNone
        # task type
        
        self.scopeFilter = None
        # global (False) or project (True)
        
        self.statusFilter = None
        # uncompleted (False) or completed (True)
        
        self.prioritiesFilter = None
        # list of priorities [0 (high), 1 (normal), 2 (low)]
    
    def setActive(self, enabled):
        """
        Public method to activate the filter.
        
        @param enabled flag indicating the activation state (boolean)
        """
        self.active = enabled
    
    def setSummaryFilter(self, filter):
        """
        Public method to set the description filter.
        
        @param filter a regular expression for the description filter
            to set (string) or None
        """
        if not filter:
            self.summaryFilter = None
        else:
            self.summaryFilter = QRegExp(filter)
    
    def setFileNameFilter(self, filter):
        """
        Public method to set the filename filter.
        
        @param filter a wildcard expression for the filename filter
            to set (string) or None
        """
        if not filter:
            self.filenameFilter = None
        else:
            self.filenameFilter = QRegExp(filter)
            self.filenameFilter.setPatternSyntax(QRegExp.Wildcard)
    
    def setTypeFilter(self, taskType):
        """
        Public method to set the type filter.
        
        @param taskType type of the task (one of Task.TypeNone, Task.TypeFixme,
            Task.TypeTodo, Task.TypeWarning, Task.TypeNote)
        """
        self.typeFilter = taskType
        
    def setScopeFilter(self, scope):
        """
        Public method to set the scope filter.
        
        @param scope flag indicating a project task (boolean) or None
        """
        self.scopeFilter = scope
        
    def setStatusFilter(self, status):
        """
        Public method to set the status filter.
        
        @param status flag indicating a completed task (boolean) or None
        """
        self.statusFilter = status
        
    def setPrioritiesFilter(self, priorities):
        """
        Public method to set the priorities filter.
        
        @param priorities list of task priorities (list of integer) or None
        """
        self.prioritiesFilter = priorities
        
    def hasActiveFilter(self):
        """
        Public method to check for active filters.
        
        @return flag indicating an active filter was found (boolean)
        """
        return self.summaryFilter is not None or \
            self.filenameFilter is not None or \
            self.typeFilter != Task.TypeNone or \
            self.scopeFilter is not None or \
            self.statusFilter is not None or \
            self.prioritiesFilter is not None
        
    def showTask(self, task):
        """
        Public method to check, if a task should be shown.
        
        @param task reference to the task object to check (Task)
        @return flag indicating whether the task should be shown (boolean)
        """
        if not self.active:
            return True
        
        if self.summaryFilter and \
           self.summaryFilter.indexIn(task.summary) == -1:
            return False
        
        if self.filenameFilter and \
           not self.filenameFilter.exactMatch(task.filename):
            return False
        
        if self.typeFilter != Task.TypeNone and \
           self.typeFilter != task.taskType:
            return False
        
        if self.scopeFilter is not None and \
           self.scopeFilter != task._isProjectTask:
            return False
        
        if self.statusFilter is not None and \
           self.statusFilter != task.completed:
            return False
        
        if self.prioritiesFilter is not None and \
           task.priority not in self.prioritiesFilter:
            return False
        
        return True
