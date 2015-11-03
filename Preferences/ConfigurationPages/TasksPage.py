# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Tasks configuration page.
"""

from __future__ import unicode_literals

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_TasksPage import Ui_TasksPage

import Preferences


class TasksPage(ConfigurationPageBase, Ui_TasksPage):
    """
    Class implementing the Tasks configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(TasksPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("TasksPage")
        
        # set initial values
        self.tasksMarkerFixmeEdit.setText(
            Preferences.getTasks("TasksFixmeMarkers"))
        self.tasksMarkerWarningEdit.setText(
            Preferences.getTasks("TasksWarningMarkers"))
        self.tasksMarkerTodoEdit.setText(
            Preferences.getTasks("TasksTodoMarkers"))
        self.tasksMarkerNoteEdit.setText(
            Preferences.getTasks("TasksNoteMarkers"))
        
        self.initColour(
            "TasksFixmeColor", self.tasksFixmeColourButton,
            Preferences.getTasks)
        self.initColour(
            "TasksWarningColor", self.tasksWarningColourButton,
            Preferences.getTasks)
        self.initColour(
            "TasksTodoColor", self.tasksTodoColourButton,
            Preferences.getTasks)
        self.initColour(
            "TasksNoteColor", self.tasksNoteColourButton,
            Preferences.getTasks)
        
        self.clearCheckBox.setChecked(Preferences.getTasks("ClearOnFileClose"))
        
    def save(self):
        """
        Public slot to save the Tasks configuration.
        """
        Preferences.setTasks(
            "TasksFixmeMarkers", self.tasksMarkerFixmeEdit.text())
        Preferences.setTasks(
            "TasksWarningMarkers", self.tasksMarkerWarningEdit.text())
        Preferences.setTasks(
            "TasksTodoMarkers", self.tasksMarkerTodoEdit.text())
        Preferences.setTasks(
            "TasksNoteMarkers", self.tasksMarkerNoteEdit.text())
        Preferences.setTasks(
            "ClearOnFileClose", self.clearCheckBox.isChecked())
        
        self.saveColours(Preferences.setTasks)
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = TasksPage()
    return page
