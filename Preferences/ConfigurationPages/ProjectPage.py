# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Project configuration page.
"""

from __future__ import unicode_literals

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_ProjectPage import Ui_ProjectPage

import Preferences


class ProjectPage(ConfigurationPageBase, Ui_ProjectPage):
    """
    Class implementing the Project configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(ProjectPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("ProjectPage")
        
        # set initial values
        self.projectSearchNewFilesRecursiveCheckBox.setChecked(
            Preferences.getProject("SearchNewFilesRecursively"))
        self.projectSearchNewFilesCheckBox.setChecked(
            Preferences.getProject("SearchNewFiles"))
        self.projectAutoIncludeNewFilesCheckBox.setChecked(
            Preferences.getProject("AutoIncludeNewFiles"))
        self.projectLoadSessionCheckBox.setChecked(
            Preferences.getProject("AutoLoadSession"))
        self.projectSaveSessionCheckBox.setChecked(
            Preferences.getProject("AutoSaveSession"))
        self.projectSessionAllBpCheckBox.setChecked(
            Preferences.getProject("SessionAllBreakpoints"))
        self.projectLoadDebugPropertiesCheckBox.setChecked(
            Preferences.getProject("AutoLoadDbgProperties"))
        self.projectSaveDebugPropertiesCheckBox.setChecked(
            Preferences.getProject("AutoSaveDbgProperties"))
        self.projectAutoCompileFormsCheckBox.setChecked(
            Preferences.getProject("AutoCompileForms"))
        self.projectAutoCompileResourcesCheckBox.setChecked(
            Preferences.getProject("AutoCompileResources"))
        self.projectTimestampCheckBox.setChecked(
            Preferences.getProject("XMLTimestamp"))
        self.projectRecentSpinBox.setValue(
            Preferences.getProject("RecentNumber"))
        self.pythonVariantCheckBox.setChecked(
            Preferences.getProject("DeterminePyFromProject"))
        
        self.autosaveTasksCheckBox.setChecked(
            Preferences.getTasks("TasksProjectAutoSave"))
        
    def save(self):
        """
        Public slot to save the Project configuration.
        """
        Preferences.setProject(
            "SearchNewFilesRecursively",
            self.projectSearchNewFilesRecursiveCheckBox.isChecked())
        Preferences.setProject(
            "SearchNewFiles",
            self.projectSearchNewFilesCheckBox.isChecked())
        Preferences.setProject(
            "AutoIncludeNewFiles",
            self.projectAutoIncludeNewFilesCheckBox.isChecked())
        Preferences.setProject(
            "AutoLoadSession",
            self.projectLoadSessionCheckBox.isChecked())
        Preferences.setProject(
            "AutoSaveSession",
            self.projectSaveSessionCheckBox.isChecked())
        Preferences.setProject(
            "SessionAllBreakpoints",
            self.projectSessionAllBpCheckBox.isChecked())
        Preferences.setProject(
            "AutoLoadDbgProperties",
            self.projectLoadDebugPropertiesCheckBox.isChecked())
        Preferences.setProject(
            "AutoSaveDbgProperties",
            self.projectSaveDebugPropertiesCheckBox.isChecked())
        Preferences.setProject(
            "AutoCompileForms",
            self.projectAutoCompileFormsCheckBox.isChecked())
        Preferences.setProject(
            "AutoCompileResources",
            self.projectAutoCompileResourcesCheckBox.isChecked())
        Preferences.setProject(
            "XMLTimestamp",
            self.projectTimestampCheckBox.isChecked())
        Preferences.setProject(
            "RecentNumber",
            self.projectRecentSpinBox.value())
        Preferences.setProject(
            "DeterminePyFromProject",
            self.pythonVariantCheckBox.isChecked())
        
        Preferences.setTasks(
            "TasksProjectAutoSave",
            self.autosaveTasksCheckBox.isChecked())
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = ProjectPage()
    return page
