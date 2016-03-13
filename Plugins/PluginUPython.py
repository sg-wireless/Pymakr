import os
from PyQt5.QtCore import QObject, QCoreApplication

import UI
from E5Gui.E5Application import e5App
import Preferences
from UPython.Shell import ShellAssembly
from UPython.DebugServer import DebugServer

# Start-Of-Header
name = "MicroPython Console"
author = "Pycom"
autoactivate = True
deactivateable = False
version = "1.0.0"
className = "PluginUPython"
packageName = "PluginUPython"
shortDescription = "Implement the MicroPython console"
longDescription = "Allow users to connect to MicroPython devices from within Pymakr"

pyqtApi = 2
python2Compatible = True

uPythonPluginObject = None

def getConfigData():
    """
    Module function returning data as required by the configuration dialog.

    @return dictionary with key "MicroPython" containing the relevant
        data
    """
    path = os.path.dirname(os.path.realpath(__file__))
    return {
        "MicroPython":
        [QCoreApplication.translate("MicroPythonPlugin", "MicroPython"),
        path + "/UPython/img/chip.png", createConfigurationPage,
        None, None]
    }

def createConfigurationPage(configDlg):
    """
    Module function to create the configuration page.

    @param configDlg reference to the configuration dialog (QDialog)
    @return reference to the configuration page
    """
    global uPythonPluginObject
    from UPython.ConfigurationPage.MicroPythonPage import MicroPythonPage
    return MicroPythonPage(uPythonPluginObject)

class PluginUPython(QObject):
    def __init__(self,  ui):
        global uPythonPluginObject

        super(PluginUPython, self).__init__(ui)
        uPythonPluginObject = self

        self.__ui = ui
        self.__oldShowEvent = self.__ui.showEvent
        self.__ui.showEvent = self.__onWindowLoad
        self.__oldCloseEvent = self.__ui.closeEvent
        self.__ui.closeEvent = self.__onWindowUnload

        self.__windowLoaded = False
        self.__path = os.path.dirname(os.path.realpath(__file__))
        UI.PixmapCache.addSearchPath(self.__path + "/UPython/img")

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        self.__active = True
        if self.__windowLoaded == True:
            self.__initializeShell()
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        self.__dbs.disconnect()


    def __onWindowLoad(self, event):
        # I must run only once
        self.__ui.showEvent = self.__oldShowEvent
        self.__ui.showEvent(event)

        if self.__active == True:
            self.__initializeShell()
        self.__windowLoaded = True

    def __onWindowUnload(self, event):
        self.__ui.closeEvent = self.__oldCloseEvent
        self.__dbs.disconnect()
        self.__ui.closeEvent(event)

    def __initializeShell(self):
        self.__dbs = DebugServer()
        self.loadSettings()

        self.__shell = ShellAssembly(self.__dbs,
            e5App().getObject("ViewManager"))

        self.__ui.bottomSidebar.insertTab(0, self.__shell,
            UI.PixmapCache.getIcon("chip.png"), "MicroPython Console")

        self.__ui.bottomSidebar.setTabText(1, self.tr("Local Shell"))

        self.__ui.bottomSidebar.setCurrentIndex(0)

    def loadSettings(self):
        self.__dbs.setConnectionParameters(
            self.getPreferences("address"),
            self.getPreferences("username"),
            self.getPreferences("password")
            )

    def getPreferences(self, name, default=None):
        return Preferences.Prefs.settings.value("MicroPython/" + name, default)

    def setPreferences(self, name, value):
        Preferences.Prefs.settings.setValue("MicroPython/" + name, value)

    def preferencesChanged(self):
        self.loadSettings()
        self.__dbs.restart()