# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the base class of the VCS project helper.
"""

from __future__ import unicode_literals

import os
import shutil
import copy

from PyQt5.QtCore import pyqtSlot, QDir, QFileInfo, QObject
from PyQt5.QtWidgets import QDialog, QInputDialog, QToolBar

from E5Gui.E5Action import E5Action
from E5Gui import E5MessageBox
from E5Gui.E5Application import e5App

import Preferences
import UI.PixmapCache
import UI.Config


class VcsProjectHelper(QObject):
    """
    Class implementing the base class of the VCS project helper.
    """
    def __init__(self, vcsObject, projectObject, parent=None, name=None):
        """
        Constructor
        
        @param vcsObject reference to the vcs object
        @param projectObject reference to the project object
        @param parent parent widget (QWidget)
        @param name name of this object (string)
        """
        super(VcsProjectHelper, self).__init__(parent)
        if name:
            self.setObjectName(name)
        
        self.vcs = vcsObject
        self.project = projectObject
        
        self.actions = []
        
        self.vcsAddAct = None
        
        self.initActions()
        
    def setObjects(self, vcsObject, projectObject):
        """
        Public method to set references to the vcs and project objects.
        
        @param vcsObject reference to the vcs object
        @param projectObject reference to the project object
        """
        self.vcs = vcsObject
        self.project = projectObject
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.vcsNewAct = E5Action(
            self.tr('New from repository'),
            UI.PixmapCache.getIcon("vcsCheckout.png"),
            self.tr('&New from repository...'),
            0, 0, self, 'vcs_new')
        self.vcsNewAct.setStatusTip(self.tr(
            'Create a new project from the VCS repository'
        ))
        self.vcsNewAct.setWhatsThis(self.tr(
            """<b>New from repository</b>"""
            """<p>This creates a new local project from the VCS"""
            """ repository.</p>"""
        ))
        self.vcsNewAct.triggered.connect(self._vcsCheckout)
        self.actions.append(self.vcsNewAct)
        
        self.vcsExportAct = E5Action(
            self.tr('Export from repository'),
            UI.PixmapCache.getIcon("vcsExport.png"),
            self.tr('&Export from repository...'),
            0, 0, self, 'vcs_export')
        self.vcsExportAct.setStatusTip(self.tr(
            'Export a project from the repository'
        ))
        self.vcsExportAct.setWhatsThis(self.tr(
            """<b>Export from repository</b>"""
            """<p>This exports a project from the repository.</p>"""
        ))
        self.vcsExportAct.triggered.connect(self._vcsExport)
        self.actions.append(self.vcsExportAct)
        
        self.vcsAddAct = E5Action(
            self.tr('Add to repository'),
            UI.PixmapCache.getIcon("vcsCommit.png"),
            self.tr('&Add to repository...'),
            0, 0, self, 'vcs_add')
        self.vcsAddAct.setStatusTip(self.tr(
            'Add the local project to the VCS repository'
        ))
        self.vcsAddAct.setWhatsThis(self.tr(
            """<b>Add to repository</b>"""
            """<p>This adds (imports) the local project to the VCS"""
            """ repository.</p>"""
        ))
        self.vcsAddAct.triggered.connect(self._vcsImport)
        self.actions.append(self.vcsAddAct)
    
    def initMenu(self, menu):
        """
        Public method to generate the VCS menu.
        
        @param menu reference to the menu to be populated (QMenu)
        """
        menu.clear()
        
        menu.addAction(self.vcsNewAct)
        menu.addAction(self.vcsExportAct)
        menu.addSeparator()
        menu.addAction(self.vcsAddAct)
        menu.addSeparator()

    def initToolbar(self, ui, toolbarManager):
        """
        Public slot to initialize the VCS toolbar.
        
        @param ui reference to the main window (UserInterface)
        @param toolbarManager reference to a toolbar manager object
            (E5ToolBarManager)
        @return the toolbar generated (QToolBar)
        """
        return None
    
    def initBasicToolbar(self, ui, toolbarManager):
        """
        Public slot to initialize the basic VCS toolbar.
        
        @param ui reference to the main window (UserInterface)
        @param toolbarManager reference to a toolbar manager object
            (E5ToolBarManager)
        @return the toolbar generated (QToolBar)
        """
        tb = QToolBar(self.tr("VCS"), ui)
        tb.setIconSize(UI.Config.ToolBarIconSize)
        tb.setObjectName("VersionControlToolbar")
        tb.setToolTip(self.tr('VCS'))
        
        tb.addAction(self.vcsNewAct)
        tb.addAction(self.vcsExportAct)
        tb.addSeparator()
        tb.addAction(self.vcsAddAct)
        
        toolbarManager.addToolBar(tb, tb.windowTitle())
        
        return tb
    
    def showMenu(self):
        """
        Public slot called before the vcs menu is shown.
        """
        if self.vcsAddAct:
            self.vcsAddAct.setEnabled(self.project.isOpen())
    
    @pyqtSlot()
    def _vcsCheckout(self, export=False):
        """
        Protected slot used to create a local project from the repository.
        
        @param export flag indicating whether an export or a checkout
                should be performed
        """
        if not self.project.checkDirty():
            return
        
        vcsSystemsDict = e5App().getObject("PluginManager")\
            .getPluginDisplayStrings("version_control")
        if not vcsSystemsDict:
            # no version control system found
            return
        
        vcsSystemsDisplay = []
        keys = sorted(vcsSystemsDict.keys())
        for key in keys:
            vcsSystemsDisplay.append(vcsSystemsDict[key])
        vcsSelected, ok = QInputDialog.getItem(
            None,
            self.tr("New Project"),
            self.tr("Select version control system for the project"),
            vcsSystemsDisplay,
            0, False)
        if not ok:
            return
        for vcsSystem, vcsSystemDisplay in list(vcsSystemsDict.items()):
            if vcsSystemDisplay == vcsSelected:
                break
        
        if not self.project.closeProject():
            return
        
        self.project.pdata["VCS"] = [vcsSystem]
        self.project.vcs = self.project.initVCS(vcsSystem)
        if self.project.vcs is not None:
            vcsdlg = self.project.vcs.vcsNewProjectOptionsDialog()
            if vcsdlg.exec_() == QDialog.Accepted:
                projectdir, vcsDataDict = vcsdlg.getData()
                self.project.pdata["VCS"] = [vcsSystem]
                self.project.vcs = self.project.initVCS(vcsSystem)
                # edit VCS command options
                if self.project.vcs.vcsSupportCommandOptions():
                    vcores = E5MessageBox.yesNo(
                        self.parent(),
                        self.tr("New Project"),
                        self.tr(
                            """Would you like to edit the VCS command"""
                            """ options?"""))
                else:
                    vcores = False
                if vcores:
                    from .CommandOptionsDialog import VcsCommandOptionsDialog
                    codlg = VcsCommandOptionsDialog(self.project.vcs)
                    if codlg.exec_() == QDialog.Accepted:
                        self.project.vcs.vcsSetOptions(codlg.getOptions())
                
                # create the project directory if it doesn't exist already
                if not os.path.isdir(projectdir):
                    try:
                        os.makedirs(projectdir)
                    except EnvironmentError:
                        E5MessageBox.critical(
                            self.parent(),
                            self.tr("Create project directory"),
                            self.tr(
                                "<p>The project directory <b>{0}</b> could not"
                                " be created.</p>").format(projectdir))
                        self.project.pdata["VCS"] = ['None']
                        self.project.vcs = self.project.initVCS()
                        return
                
                # create the project from the VCS
                self.project.vcs.vcsSetDataFromDict(vcsDataDict)
                if export:
                    ok = self.project.vcs.vcsExport(vcsDataDict, projectdir)
                else:
                    ok = self.project.vcs.vcsCheckout(vcsDataDict, projectdir,
                                                      False)
                if ok:
                    projectdir = os.path.normpath(projectdir)
                    filters = ["*.e4p"]
                    d = QDir(projectdir)
                    plist = d.entryInfoList(filters)
                    if len(plist):
                        if len(plist) == 1:
                            self.project.openProject(
                                plist[0].absoluteFilePath())
                            self.project.newProject.emit()
                        else:
                            pfilenamelist = d.entryList(filters)
                            pfilename, ok = QInputDialog.getItem(
                                None,
                                self.tr("New project from repository"),
                                self.tr("Select a project file to open."),
                                pfilenamelist, 0, False)
                            if ok:
                                self.project.openProject(
                                    QFileInfo(d, pfilename).absoluteFilePath())
                                self.project.newProject.emit()
                        if export:
                            self.project.pdata["VCS"] = ['None']
                            self.project.vcs = self.project.initVCS()
                            self.project.setDirty(True)
                            self.project.saveProject()
                    else:
                        res = E5MessageBox.yesNo(
                            self.parent(),
                            self.tr("New project from repository"),
                            self.tr(
                                "The project retrieved from the repository"
                                " does not contain an eric project file"
                                " (*.e4p). Create it?"),
                            yesDefault=True)
                        if res:
                            self.project.ppath = projectdir
                            self.project.opened = True
                            
                            from Project.PropertiesDialog import \
                                PropertiesDialog
                            dlg = PropertiesDialog(self.project, False)
                            if dlg.exec_() == QDialog.Accepted:
                                dlg.storeData()
                                self.project.initFileTypes()
                                self.project.setDirty(True)
                                try:
                                    ms = os.path.join(
                                        self.project.ppath,
                                        self.project.pdata["MAINSCRIPT"][0])
                                    if os.path.exists(ms):
                                        self.project.appendFile(ms)
                                except IndexError:
                                    ms = ""
                                self.project.newProjectAddFiles(ms)
                                self.project.createProjectManagementDir()
                                self.project.saveProject()
                                self.project.openProject(self.project.pfile)
                                if not export:
                                    res = E5MessageBox.yesNo(
                                        self.parent(),
                                        self.tr(
                                            "New project from repository"),
                                        self.tr(
                                            "Shall the project file be added"
                                            " to the repository?"),
                                        yesDefault=True)
                                    if res:
                                        self.project.vcs.vcsAdd(
                                            self.project.pfile)
                else:
                    E5MessageBox.critical(
                        self.parent(),
                        self.tr("New project from repository"),
                        self.tr(
                            """The project could not be retrieved from"""
                            """ the repository."""))
                    self.project.pdata["VCS"] = ['None']
                    self.project.vcs = self.project.initVCS()
            else:
                self.project.pdata["VCS"] = ['None']
                self.project.vcs = self.project.initVCS()

    def _vcsExport(self):
        """
        Protected slot used to export a project from the repository.
        """
        self._vcsCheckout(True)

    def _vcsImport(self):
        """
        Protected slot used to import the local project into the repository.
        
        <b>NOTE</b>:
            This does not necessarily make the local project a vcs controlled
            project. You may have to checkout the project from the repository
            in order to accomplish that.
        """
        def revertChanges():
            """
            Local function to revert the changes made to the project object.
            """
            self.project.pdata["VCS"] = pdata_vcs[:]
            self.project.pdata["VCSOPTIONS"] = copy.deepcopy(pdata_vcsoptions)
            self.project.pdata["VCSOTHERDATA"] = copy.deepcopy(pdata_vcsother)
            self.project.vcs = vcs
            self.project.vcsProjectHelper = vcsHelper
            self.project.vcsBasicHelper = vcs is None
            self.initMenu(self.project.vcsMenu)
            self.project.setDirty(True)
            self.project.saveProject()
        
        pdata_vcs = self.project.pdata["VCS"][:]
        pdata_vcsoptions = copy.deepcopy(self.project.pdata["VCSOPTIONS"])
        pdata_vcsother = copy.deepcopy(self.project.pdata["VCSOTHERDATA"])
        vcs = self.project.vcs
        vcsHelper = self.project.vcsProjectHelper
        vcsSystemsDict = e5App().getObject("PluginManager")\
            .getPluginDisplayStrings("version_control")
        if not vcsSystemsDict:
            # no version control system found
            return
        
        vcsSystemsDisplay = []
        keys = sorted(list(vcsSystemsDict.keys()))
        for key in keys:
            vcsSystemsDisplay.append(vcsSystemsDict[key])
        vcsSelected, ok = QInputDialog.getItem(
            None,
            self.tr("Import Project"),
            self.tr("Select version control system for the project"),
            vcsSystemsDisplay,
            0, False)
        if not ok:
            return
        for vcsSystem, vcsSystemDisplay in list(vcsSystemsDict.items()):
            if vcsSystemDisplay == vcsSelected:
                break
        
        self.project.pdata["VCS"] = [vcsSystem]
        self.project.vcs = self.project.initVCS(vcsSystem)
        if self.project.vcs is not None:
            vcsdlg = self.project.vcs.vcsOptionsDialog(self.project,
                                                       self.project.name, 1)
            if vcsdlg.exec_() == QDialog.Accepted:
                vcsDataDict = vcsdlg.getData()
                # edit VCS command options
                if self.project.vcs.vcsSupportCommandOptions():
                    vcores = E5MessageBox.yesNo(
                        self.parent(),
                        self.tr("Import Project"),
                        self.tr(
                            """Would you like to edit the VCS command"""
                            """ options?"""))
                else:
                    vcores = False
                if vcores:
                    from .CommandOptionsDialog import VcsCommandOptionsDialog
                    codlg = VcsCommandOptionsDialog(self.project.vcs)
                    if codlg.exec_() == QDialog.Accepted:
                        self.project.vcs.vcsSetOptions(codlg.getOptions())
                self.project.setDirty(True)
                self.project.vcs.vcsSetDataFromDict(vcsDataDict)
                self.project.saveProject()
                isVcsControlled = self.project.vcs.vcsImport(
                    vcsDataDict, self.project.ppath)[0]
                if isVcsControlled:
                    # reopen the project
                    self.project.openProject(self.project.pfile)
                else:
                    # revert the changes to the local project
                    # because the project dir is not a VCS directory
                    revertChanges()
            else:
                # revert the changes because user cancelled
                revertChanges()

    def _vcsUpdate(self):
        """
        Protected slot used to update the local project from the repository.
        """
        shouldReopen = self.vcs.vcsUpdate(self.project.ppath)
        if shouldReopen:
            res = E5MessageBox.yesNo(
                self.parent(),
                self.tr("Update"),
                self.tr("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
        
    def _vcsCommit(self):
        """
        Protected slot used to commit changes to the local project to the
        repository.
        """
        if Preferences.getVCS("AutoSaveProject"):
            self.project.saveProject()
        if Preferences.getVCS("AutoSaveFiles"):
            self.project.saveAllScripts()
        self.vcs.vcsCommit(self.project.ppath, '')
        
    def _vcsRemove(self):
        """
        Protected slot used to remove the local project from the repository.
        
        Depending on the parameters set in the vcs object the project
        may be removed from the local disk as well.
        """
        res = E5MessageBox.yesNo(
            self.parent(),
            self.tr("Remove project from repository"),
            self.tr(
                "Dou you really want to remove this project from"
                " the repository (and disk)?"))
        if res:
            self.vcs.vcsRemove(self.project.ppath, True)
            self._vcsCommit()
            if not os.path.exists(self.project.pfile):
                ppath = self.project.ppath
                self.setDirty(False)
                self.project.closeProject()
                shutil.rmtree(ppath, True)
        
    def _vcsCommandOptions(self):
        """
        Protected slot to edit the VCS command options.
        """
        if self.vcs.vcsSupportCommandOptions():
            from .CommandOptionsDialog import VcsCommandOptionsDialog
            codlg = VcsCommandOptionsDialog(self.vcs)
            if codlg.exec_() == QDialog.Accepted:
                self.vcs.vcsSetOptions(codlg.getOptions())
                self.project.setDirty(True)
        
    def _vcsLog(self):
        """
        Protected slot used to show the log of the local project.
        """
        self.vcs.vcsLog(self.project.ppath)
        
    def _vcsLogBrowser(self):
        """
        Protected slot used to show the log of the local project with a
        log browser dialog.
        """
        self.vcs.vcsLogBrowser(self.project.ppath)
        
    def _vcsDiff(self):
        """
        Protected slot used to show the difference of the local project to
        the repository.
        """
        self.vcs.vcsDiff(self.project.ppath)
        
    def _vcsStatus(self):
        """
        Protected slot used to show the status of the local project.
        """
        self.vcs.vcsStatus(self.project.ppath)
        
    def _vcsTag(self):
        """
        Protected slot used to tag the local project in the repository.
        """
        self.vcs.vcsTag(self.project.ppath)
        
    def _vcsRevert(self):
        """
        Protected slot used to revert changes made to the local project.
        """
        self.vcs.vcsRevert(self.project.ppath)
        
    def _vcsSwitch(self):
        """
        Protected slot used to switch the local project to another tag/branch.
        """
        shouldReopen = self.vcs.vcsSwitch(self.project.ppath)
        if shouldReopen:
            res = E5MessageBox.yesNo(
                self.parent(),
                self.tr("Switch"),
                self.tr("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
        
    def _vcsMerge(self):
        """
        Protected slot used to merge changes of a tag/revision into the local
        project.
        """
        self.vcs.vcsMerge(self.project.ppath)
        
    def _vcsCleanup(self):
        """
        Protected slot used to cleanup the local project.
        """
        self.vcs.vcsCleanup(self.project.ppath)
        
    def _vcsCommand(self):
        """
        Protected slot used to execute an arbitrary vcs command.
        """
        self.vcs.vcsCommandLine(self.project.ppath)

    def _vcsInfoDisplay(self):
        """
        Protected slot called to show some vcs information.
        """
        from .RepositoryInfoDialog import VcsRepositoryInfoDialog
        info = self.vcs.vcsRepositoryInfos(self.project.ppath)
        dlg = VcsRepositoryInfoDialog(None, info)
        dlg.exec_()
