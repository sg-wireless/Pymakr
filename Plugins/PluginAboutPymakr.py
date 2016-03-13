import os
from PyQt5.QtCore import QObject, QCoreApplication

import UI
from E5Gui.E5Application import e5App
import Preferences
from UPython.Shell import ShellAssembly
from UPython.DebugServer import DebugServer

# Start-Of-Header
name = "About Pymakr"
author = "Pycom"
autoactivate = True
deactivateable = False
version = "1.0.0"
className = "PluginAboutPymakr"
packageName = "PluginAboutPymakr"
shortDescription = "Display the Pymakr About dialog"
longDescription = shortDescription

pyqtApi = 2
python2Compatible = True

class PluginAboutPymakr(QObject):
    def __init__(self,  ui):

        super(PluginAboutPymakr, self).__init__(ui)

        self.__ui = ui

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        menu = self.__ui.getMenu("help")
        menu.addSeparator()
        self.aboutAct = menu.addAction(self.tr("About Pymakr..."))
        self.aboutAct.triggered.connect(self.__about)
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """

        pass

    def __about(self):
        """
        Private slot to handle the About dialog.
        """
        from AboutPymakr.AboutPymakr import AboutPymakr
        dlg = AboutPymakr(self.__ui)
        dlg.exec_()