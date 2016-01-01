# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the task properties dialog.
"""

from __future__ import unicode_literals

import time

from PyQt5.QtWidgets import QDialog

from E5Gui.E5Completers import E5FileCompleter

from .Ui_TaskPropertiesDialog import Ui_TaskPropertiesDialog


class TaskPropertiesDialog(QDialog, Ui_TaskPropertiesDialog):
    """
    Class implementing the task properties dialog.
    """
    def __init__(self, task=None, parent=None, projectOpen=False):
        """
        Constructor
        
        @param task the task object to be shown
        @param parent the parent widget (QWidget)
        @param projectOpen flag indicating status of the project (boolean)
        """
        super(TaskPropertiesDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.filenameCompleter = E5FileCompleter(self.filenameEdit)
        
        if not projectOpen:
            self.projectCheckBox.setEnabled(False)
        if task is not None:
            self.summaryEdit.setText(task.summary)
            self.descriptionEdit.setText(task.description)
            self.creationLabel.setText(
                time.strftime("%Y-%m-%d, %H:%M:%S",
                              time.localtime(task.created)))
            self.priorityCombo.setCurrentIndex(task.priority)
            self.projectCheckBox.setChecked(task._isProjectTask)
            self.completedCheckBox.setChecked(task.completed)
            self.filenameEdit.setText(task.filename)
            if task.lineno:
                self.linenoEdit.setText(str(task.lineno))
        else:
            self.projectCheckBox.setChecked(projectOpen)
    
    def setReadOnly(self):
        """
        Public slot to set the dialog to read only mode.
        """
        self.summaryEdit.setReadOnly(True)
        self.completedCheckBox.setEnabled(False)
        self.priorityCombo.setEnabled(False)
        self.projectCheckBox.setEnabled(False)
        self.descriptionEdit.setEnabled(False)
    
    def setSubTaskMode(self, projectTask):
        """
        Public slot to set the sub-task mode.
        
        @param projectTask flag indicating a project related task (boolean)
        """
        self.projectCheckBox.setChecked(projectTask)
        self.projectCheckBox.setEnabled(False)
    
    def getData(self):
        """
        Public method to retrieve the dialogs data.
        
        @return tuple of description, priority, completion flag,
                project flag and long text (string, string, boolean,
                boolean, string)
        """
        return (self.summaryEdit.text(),
                self.priorityCombo.currentIndex(),
                self.completedCheckBox.isChecked(),
                self.projectCheckBox.isChecked(),
                self.descriptionEdit.toPlainText())
