# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the user specific project properties dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from E5Gui.E5Application import e5App

import Preferences

from .Ui_UserPropertiesDialog import Ui_UserPropertiesDialog


class UserPropertiesDialog(QDialog, Ui_UserPropertiesDialog):
    """
    Class implementing the user specific project properties dialog.
    """
    def __init__(self, project, parent=None, name=None):
        """
        Constructor
        
        @param project reference to the project object
        @param parent parent widget of this dialog (QWidget)
        @param name name of this dialog (string)
        """
        super(UserPropertiesDialog, self).__init__(parent)
        if name:
            self.setObjectName(name)
        self.setupUi(self)
        
        self.project = project
        
        if self.project.pudata["VCSSTATUSMONITORINTERVAL"]:
            self.vcsStatusMonitorIntervalSpinBox.setValue(
                self.project.pudata["VCSSTATUSMONITORINTERVAL"][0])
        else:
            self.vcsStatusMonitorIntervalSpinBox.setValue(
                Preferences.getVCS("StatusMonitorInterval"))
        
        enableVcsGroup = False
        if self.project.pdata["VCS"]:
            found = False
            for indicator, vcsData in \
                    e5App().getObject("PluginManager")\
                    .getVcsSystemIndicators().items():
                for vcsSystem, vcsSystemDisplay in vcsData:
                    if vcsSystem == self.project.pdata["VCS"][0]:
                        found = True
                        break
                
                if found:
                    for vcsSystem, vcsSystemDisplay in vcsData:
                        self.vcsInterfaceCombo.addItem(
                            vcsSystemDisplay, vcsSystem)
                    enableVcsGroup = len(vcsData) > 1
                    break
        self.vcsGroup.setEnabled(enableVcsGroup)
        
        if self.vcsGroup.isEnabled():
            if self.project.pudata["VCSOVERRIDE"]:
                vcsSystem = self.project.pudata["VCSOVERRIDE"][0]
            else:
                vcsSystem = self.project.pdata["VCS"][0]
            index = self.vcsInterfaceCombo.findData(vcsSystem)
            if index == -1:
                index = 0
            self.vcsInterfaceCombo.setCurrentIndex(index)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())

    def storeData(self):
        """
        Public method to store the entered/modified data.
        """
        vcsStatusMonitorInterval = self.vcsStatusMonitorIntervalSpinBox.value()
        if vcsStatusMonitorInterval != \
                Preferences.getVCS("StatusMonitorInterval"):
            self.project.pudata["VCSSTATUSMONITORINTERVAL"] = \
                [vcsStatusMonitorInterval]
        else:
            self.project.pudata["VCSSTATUSMONITORINTERVAL"] = []
        
        if self.vcsGroup.isEnabled():
            vcsSystem = self.vcsInterfaceCombo\
                .itemData(self.vcsInterfaceCombo.currentIndex())
            if self.vcsInterfaceDefaultCheckBox.isChecked():
                if vcsSystem != self.project.pdata["VCS"][0]:
                    self.project.pdata["VCS"] = [vcsSystem]
                    self.project.pudata["VCSOVERRIDE"] = []
                    self.project.setDirty(True)
            else:
                if vcsSystem != self.project.pdata["VCS"][0]:
                    self.project.pudata["VCSOVERRIDE"] = [vcsSystem]
                else:
                    self.project.pudata["VCSOVERRIDE"] = []
