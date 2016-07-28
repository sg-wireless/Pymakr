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
autoactivate = False
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
        self.__ui = ui

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

    def createToolbar(self,ui, toolbarManager):
        self.__toolbar = QToolBar(self.tr("Pycom Sync"), ui)
        self.__toolbar.setIconSize(UI.Config.ToolBarIconSize)
        self.__toolbar.setObjectName("PycomSync")
        self.__toolbar.setToolTip(self.tr('Pycom Sync'))

        self.__toolbar.addAction(self.syncAct)

        title = self.__toolbar.windowTitle()
        toolbarManager.addToolBar(self.__toolbar, title)
        toolbarManager.addAction(self.syncAct, title)

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
        resources = list(e5App().getObject("Project").getSources())

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
        return e5App().getObject("Project").getProjectPath()

    def __syncAct(self):
        if e5App().getObject("Project").isOpen():
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

