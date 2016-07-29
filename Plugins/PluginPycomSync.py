import os
from PyQt5.QtCore import QObject, QCoreApplication
from PyQt5.QtWidgets import QToolBar


import UI
from E5Gui.E5Application import e5App
from E5Gui.E5Action import E5Action
import Preferences
from REPL.Shell import ShellAssembly
from PluginPycomDevice import PycomDeviceServer
from PycomSync.monitor_pc import Monitor_PC

# Start-Of-Header
name = "Pycom Sync"
author = "Pycom"
autoactivate = True
deactivateable = False
version = "1.0.0"
className = "PluginPycomSync"
packageName = "PluginPycomSync"
shortDescription = "Sync Pycom Devices"
longDescription = "Allow users to upload their projects to their Pycom boards"
displayString="Pycom Sync"
pluginType="viewmanager"
pluginTypename="pycomsync"
pyqtApi = 2
python2Compatible = True


class PluginPycomSync(QObject):
    def __init__(self,  ui):
        super(PluginPycomSync, self).__init__(ui)
        self.__deviceServer = None
        self.__ui = ui
        self.__project = e5App().getObject("Project")
        self.__viewManager = e5App().getObject("ViewManager")
        self.__project.projectOpened.connect(self.__projectOpened)
        self.__project.newProject.connect(self.__projectOpened)
        self.__project.projectClosed.connect(self.__projectClosed)
        self.__viewManager.editorOpened.connect(self.__editorOpened)
        self.__viewManager.lastEditorClosed.connect(self.__lastEditorClosed)

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        pass

    def initToolbar(self, ui, toolbarManager):
        self.createActions()
        self.createToolbar(ui, toolbarManager)


    def createActions(self):
        self.syncAct = E5Action(
            self.tr('Sync project'),
            UI.PixmapCache.getIcon("sync.png"),
            self.tr('Sync project'),
            0, 0, self, 'project_sync')
        self.syncAct.setStatusTip(self.tr(
            'Sync the project with a Pycom Device'
        ))
        self.syncAct.setWhatsThis(self.tr(
            """<b>Sync project</b>"""
            """<p>This syncs the project files into a """
            """Pycom device.</p>"""
        ))
        self.syncAct.triggered.connect(self.__syncAct)
        self.syncAct.setEnabled(False)

        self.runThisAct = E5Action(
            self.tr('Run this code'),
            UI.PixmapCache.getIcon("1rightarrow.png"),
            self.tr('Run this code'),
            0, 0, self, 'run_this')
        self.runThisAct.setStatusTip(self.tr(
            'Run current code within a Pycom Device'
        ))
        self.runThisAct.setWhatsThis(self.tr(
            """<b>Run this code</b>"""
            """<p>This makes the current code run into a """
            """Pycom device.</p>"""
        ))
        self.runThisAct.triggered.connect(self.__runThisAct)
        self.runThisAct.setEnabled(False)

    def createToolbar(self,ui, toolbarManager):
        self.__toolbar = QToolBar(self.tr("Pycom Sync"), ui)
        self.__toolbar.setIconSize(UI.Config.ToolBarIconSize)
        self.__toolbar.setObjectName("PycomSync")
        self.__toolbar.setToolTip(self.tr('Pycom Sync'))

        self.__toolbar.addAction(self.syncAct)
        self.__toolbar.addAction(self.runThisAct)

        title = self.__toolbar.windowTitle()
        toolbarManager.addToolBar(self.__toolbar, title)
        toolbarManager.addAction(self.syncAct, title)
        toolbarManager.addAction(self.runThisAct, title)

        ui.registerToolbar("sync", title, self.__toolbar)
        ui.addToolBar(self.__toolbar)


    def __splitSubdirectories(self, path):
        directories = []
        level = max(path.count('/'), path.count('\\')) #todo: detect when in Windows instead

        while 1:
            path = os.path.split(path)[0]
            if path == '' or path == '/':
                break
            directories.append((path, b'd', level))
            level -= 1
        return directories[::-1]

    def __getProjectFiles(self):
        directories = set()
        split_directories = set()
        resources = list(self.__project.getSources())

        for i in range(len(resources)):
            item = resources[i]
            directories.add(os.path.split(item)[0] + '/')
            resources[i] = (item, b'f')

        for el in directories:
            subdirs = self.__splitSubdirectories(el)
            split_directories.update(subdirs)

        resources.extend(split_directories)

        return resources

    def __getProjectPath(self):
        return self.__project.getProjectPath()

    def __syncAct(self):
        if self.__project.isOpen() and self.__deviceServer == None and PycomDeviceServer.getStatus() == True:
            self.__deviceServer = PycomDeviceServer()
            self.__deviceServer.emitStatusChange("uploadinit")
            self.__deviceServer.overrideControl(self.__continueSync)

    def __continueSync(self):
        pwd = os.getcwd()
        os.chdir(self.__getProjectPath())
        localFiles = self.__getProjectFiles()
        monitor = Monitor_PC(self.__deviceServer.channel)
        monitor.sync_pyboard(localFiles)
        monitor.destroy()
        os.chdir(pwd)
        self.__deviceServer.emitStatusChange("uploadend")
        self.__deviceServer = None

    def __runThisAct(self):
        editor = self.__viewManager.activeWindow()
        if editor != None and self.__deviceServer == None and PycomDeviceServer.getStatus() == True:
            self.__deviceServer = PycomDeviceServer()
            self.__deviceServer.overrideControl(self.__continueRun)

    def __continueRun(self):
        editor = self.__viewManager.activeWindow()
        if editor != None:
            code = editor.text()
            self.__deviceServer.exec_code(code)
        self.__deviceServer = None

    def __projectOpened(self):
        self.syncAct.setEnabled(True)

    def __projectClosed(self):
        self.syncAct.setEnabled(False)

    def __editorOpened(self):
        self.runThisAct.setEnabled(True)

    def __lastEditorClosed(self):
        self.runThisAct.setEnabled(False)
        