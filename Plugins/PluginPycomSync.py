import os
from PyQt5.QtCore import QObject, QCoreApplication, QSize
from PyQt5.QtWidgets import QToolBar
import hashlib

import UI
from E5Gui.E5Application import e5App
from E5Gui.E5Action import E5Action
import Preferences
from REPL.Shell import ShellAssembly
from PluginPycomDevice import PycomDeviceServer
from PycomSync.sync import Sync
from PycomDevice.monitor_pc import TransferError

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

pyqtApi = 2
python2Compatible = True

def sha256(fname):
    hash_sha = hashlib.sha256()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()

class PluginPycomSync(QObject):
    def __init__(self,  ui):
        super(PluginPycomSync, self).__init__(ui)
        self.__deviceServer = None
        self.__ui = ui
        self.__project = e5App().getObject("Project")
        self.__viewManager = e5App().getObject("ViewManager")
        self.__toolbars = e5App().getObject("ToolbarManager")
        self.__project.projectOpened.connect(self.__projectOpened)
        self.__project.newProject.connect(self.__projectOpened)
        self.__project.projectClosed.connect(self.__projectClosed)
        self.__viewManager.editorOpened.connect(self.__editorOpened)
        self.__viewManager.lastEditorClosed.connect(self.__lastEditorClosed)
        self.__busy = False

        # override window loaded event
        self.__oldShowEvent = self.__ui.showEvent
        self.__ui.showEvent = self.__windowLoaded

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

    def __windowLoaded(self, event):
        """
        Private method that gets called when the main window gets visible.
        """
        self.__oldShowEvent(event)
        self.__initToolbar(self.__ui, self.__toolbars)

        # I must run only once
        self.__ui.showEvent = self.__oldShowEvent

    def __initToolbar(self, ui, toolbarManager):
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
        self.__toolbar.setIconSize(QSize(32, 32))
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
            resources[i] = (item, b'f', sha256(item))

        for el in directories:
            subdirs = self.__splitSubdirectories(el)
            split_directories.update(subdirs)

        resources.extend(split_directories)
        return resources

    def __getProjectPath(self):
        return self.__project.getProjectPath()

    def __syncAct(self):
        if self.__project.isOpen() and PycomDeviceServer.getStatus() == True and not self.__busy:
            self.__busy = True
            PycomDeviceServer.overrideControl(self.__continueSync)

    def __continueSync(self, deviceServer):
        deviceServer.emitStatusChange("syncinit")
        pwd = os.getcwd()
        os.chdir(self.__getProjectPath())
        localFiles = self.__getProjectFiles()
        sync = Sync(localFiles, deviceServer.channel)
        try:
            sync.sync_pyboard()
            deviceServer.emitStatusChange("syncend")
        except:
            deviceServer.emitStatusChange("syncfailed")
        sync.finish_sync()
        os.chdir(pwd)
        self.__busy = False

    def __runThisAct(self):
        editor = self.__viewManager.activeWindow()
        if editor != None and PycomDeviceServer.getStatus() == True and not self.__busy:
            self.__busy = True
            PycomDeviceServer.overrideControl(self.__continueRun)

    def __continueRun(self, deviceServer):
        editor = self.__viewManager.activeWindow()
        if editor != None:
            code = editor.text()
            deviceServer.exec_code(code)
        self.__busy = False

    def __projectOpened(self):
        self.syncAct.setEnabled(True)

    def __projectClosed(self):
        self.syncAct.setEnabled(False)

    def __editorOpened(self):
        self.runThisAct.setEnabled(True)

    def __lastEditorClosed(self):
        self.runThisAct.setEnabled(False)
        