# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Plugin Manager.
"""

from __future__ import unicode_literals, print_function

import os
import sys
import imp
import zipfile

from PyQt5.QtCore import pyqtSignal, QObject, QDate, QFile, QFileInfo, QUrl, \
    QIODevice
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, \
    QNetworkReply

from E5Gui import E5MessageBox
from E5Gui.E5Application import e5App

from E5Network.E5NetworkProxyFactory import proxyAuthenticationRequired
try:
    from E5Network.E5SslErrorHandler import E5SslErrorHandler
    SSL_AVAILABLE = True
except ImportError:
    SSL_AVAILABLE = False

from .PluginExceptions import PluginPathError, PluginModulesError, \
    PluginLoadError, PluginActivationError, PluginModuleFormatError, \
    PluginClassFormatError, PluginPy2IncompatibleError

import UI.PixmapCache

import Utilities
import Preferences

from eric6config import getConfig


class PluginManager(QObject):
    """
    Class implementing the Plugin Manager.
    
    @signal shutdown() emitted at shutdown of the IDE
    @signal pluginAboutToBeActivated(modulName, pluginObject) emitted just
        before a plugin is activated
    @signal pluginActivated(moduleName, pluginObject) emitted just after
        a plugin was activated
    @signal allPlugginsActivated() emitted at startup after all plugins have
        been activated
    @signal pluginAboutToBeDeactivated(moduleName, pluginObject) emitted just
        before a plugin is deactivated
    @signal pluginDeactivated(moduleName, pluginObject) emitted just after
        a plugin was deactivated
    """
    shutdown = pyqtSignal()
    pluginAboutToBeActivated = pyqtSignal(str, object)
    pluginActivated = pyqtSignal(str, object)
    allPlugginsActivated = pyqtSignal()
    pluginAboutToBeDeactivated = pyqtSignal(str, object)
    pluginDeactivated = pyqtSignal(str, object)
    
    def __init__(self, parent=None, doLoadPlugins=True, develPlugin=None):
        """
        Constructor
        
        The Plugin Manager deals with three different plugin directories.
        The first is the one, that is part of eric6 (eric6/Plugins). The
        second one is the global plugin directory called 'eric6plugins',
        which is located inside the site-packages directory. The last one
        is the user plugin directory located inside the .eric6 directory
        of the users home directory.
        
        @param parent reference to the parent object (QObject)
        @keyparam doLoadPlugins flag indicating, that plugins should
            be loaded (boolean)
        @keyparam develPlugin filename of a plugin to be loaded for
            development (string)
        @exception PluginPathError raised to indicate an invalid plug-in path
        """
        super(PluginManager, self).__init__(parent)
        
        self.__ui = parent
        self.__develPluginFile = develPlugin
        self.__develPluginName = None
        
        self.__inactivePluginsKey = "PluginManager/InactivePlugins"
        
        self.pluginDirs = {
            "eric6": os.path.join(getConfig('ericDir'), "Plugins"),
            "global": os.path.join(Utilities.getPythonModulesDirectory(),
                                   "eric6plugins"),
            "user": os.path.join(Utilities.getConfigDir(), "eric6plugins"),
        }
        self.__priorityOrder = ["eric6", "global", "user"]
        
        self.__defaultDownloadDir = os.path.join(
            Utilities.getConfigDir(), "Downloads")
        
        self.__activePlugins = {}
        self.__inactivePlugins = {}
        self.__onDemandActivePlugins = {}
        self.__onDemandInactivePlugins = {}
        self.__activeModules = {}
        self.__inactiveModules = {}
        self.__onDemandActiveModules = {}
        self.__onDemandInactiveModules = {}
        self.__failedModules = {}
        
        self.__foundCoreModules = []
        self.__foundGlobalModules = []
        self.__foundUserModules = []
        
        self.__modulesCount = 0
        
        pdirsExist, msg = self.__pluginDirectoriesExist()
        if not pdirsExist:
            raise PluginPathError(msg)
        
        if doLoadPlugins:
            if not self.__pluginModulesExist():
                raise PluginModulesError
            
            self.__insertPluginsPaths()
            
            self.__loadPlugins()
        
        self.__checkPluginsDownloadDirectory()
        
        self.pluginRepositoryFile = \
            os.path.join(Utilities.getConfigDir(), "PluginRepository")
        
        # attributes for the network objects
        self.__networkManager = QNetworkAccessManager(self)
        self.__networkManager.proxyAuthenticationRequired.connect(
            proxyAuthenticationRequired)
        if SSL_AVAILABLE:
            self.__sslErrorHandler = E5SslErrorHandler(self)
            self.__networkManager.sslErrors.connect(self.__sslErrors)
        self.__replies = []
    
    def finalizeSetup(self):
        """
        Public method to finalize the setup of the plugin manager.
        """
        for module in list(self.__onDemandInactiveModules.values()) + \
                list(self.__onDemandActiveModules.values()):
            if hasattr(module, "moduleSetup"):
                module.moduleSetup()
        
    def getPluginDir(self, key):
        """
        Public method to get the path of a plugin directory.
        
        @param key key of the plug-in directory (string)
        @return path of the requested plugin directory (string)
        """
        if key not in ["global", "user"]:
            return None
        else:
            try:
                return self.pluginDirs[key]
            except KeyError:
                return None
    
    def __pluginDirectoriesExist(self):
        """
        Private method to check, if the plugin folders exist.
        
        If the plugin folders don't exist, they are created (if possible).
        
        @return tuple of a flag indicating existence of any of the plugin
            directories (boolean) and a message (string)
        """
        if self.__develPluginFile:
            path = Utilities.splitPath(self.__develPluginFile)[0]
            fname = os.path.join(path, "__init__.py")
            if not os.path.exists(fname):
                try:
                    f = open(fname, "w")
                    f.close()
                except IOError:
                    return (
                        False,
                        self.tr("Could not create a package for {0}.")
                            .format(self.__develPluginFile))
        
        fname = os.path.join(self.pluginDirs["user"], "__init__.py")
        if not os.path.exists(fname):
            if not os.path.exists(self.pluginDirs["user"]):
                os.mkdir(self.pluginDirs["user"], 0o755)
            try:
                f = open(fname, "w")
                f.close()
            except IOError:
                del self.pluginDirs["user"]
        
        if not os.path.exists(self.pluginDirs["global"]) and \
           os.access(Utilities.getPythonModulesDirectory(), os.W_OK):
            # create the global plugins directory
            os.mkdir(self.pluginDirs["global"], 0o755)
            fname = os.path.join(self.pluginDirs["global"], "__init__.py")
            f = open(fname, "w", encoding="utf-8")
            f.write('# -*- coding: utf-8 -*-' + "\n")
            f.write("\n")
            f.write('"""' + "\n")
            f.write('Package containing the global plugins.' + "\n")
            f.write('"""' + "\n")
            f.close()
        if not os.path.exists(self.pluginDirs["global"]):
            del self.pluginDirs["global"]
        
        if not os.path.exists(self.pluginDirs["eric6"]):
            return (
                False,
                self.tr(
                    "The internal plugin directory <b>{0}</b>"
                    " does not exits.").format(self.pluginDirs["eric6"]))
        
        return (True, "")
    
    def __pluginModulesExist(self):
        """
        Private method to check, if there are plugins available.
        
        @return flag indicating the availability of plugins (boolean)
        """
        if self.__develPluginFile and \
                not os.path.exists(self.__develPluginFile):
            return False
        
        self.__foundCoreModules = self.getPluginModules(
            self.pluginDirs["eric6"])
        if Preferences.getPluginManager("ActivateExternal"):
            if "global" in self.pluginDirs:
                self.__foundGlobalModules = \
                    self.getPluginModules(self.pluginDirs["global"])
            if "user" in self.pluginDirs:
                self.__foundUserModules = \
                    self.getPluginModules(self.pluginDirs["user"])
        
        return len(self.__foundCoreModules + self.__foundGlobalModules +
                   self.__foundUserModules) > 0
    
    def getPluginModules(self, pluginPath):
        """
        Public method to get a list of plugin modules.
        
        @param pluginPath name of the path to search (string)
        @return list of plugin module names (list of string)
        """
        pluginFiles = [f[:-3] for f in os.listdir(pluginPath)
                       if self.isValidPluginName(f)]
        return pluginFiles[:]
    
    def isValidPluginName(self, pluginName):
        """
        Public methode to check, if a file name is a valid plugin name.
        
        Plugin modules must start with "Plugin" and have the extension ".py".
        
        @param pluginName name of the file to be checked (string)
        @return flag indicating a valid plugin name (boolean)
        """
        return pluginName.startswith("Plugin") and pluginName.endswith(".py")
    
    def __insertPluginsPaths(self):
        """
        Private method to insert the valid plugin paths intos the search path.
        """
        for key in self.__priorityOrder:
            if key in self.pluginDirs:
                if not self.pluginDirs[key] in sys.path:
                    sys.path.insert(2, self.pluginDirs[key])
                UI.PixmapCache.addSearchPath(self.pluginDirs[key])
        
        if self.__develPluginFile:
            path = Utilities.splitPath(self.__develPluginFile)[0]
            if path not in sys.path:
                sys.path.insert(2, path)
            UI.PixmapCache.addSearchPath(path)
    
    def __loadPlugins(self):
        """
        Private method to load the plugins found.
        """
        develPluginName = ""
        if self.__develPluginFile:
            develPluginPath, develPluginName = \
                Utilities.splitPath(self.__develPluginFile)
            if self.isValidPluginName(develPluginName):
                develPluginName = develPluginName[:-3]
        
        for pluginName in self.__foundCoreModules:
            # global and user plugins have priority
            if pluginName not in self.__foundGlobalModules and \
               pluginName not in self.__foundUserModules and \
               pluginName != develPluginName:
                self.loadPlugin(pluginName, self.pluginDirs["eric6"])
        
        for pluginName in self.__foundGlobalModules:
            # user plugins have priority
            if pluginName not in self.__foundUserModules and \
               pluginName != develPluginName:
                self.loadPlugin(pluginName, self.pluginDirs["global"])
        
        for pluginName in self.__foundUserModules:
            if pluginName != develPluginName:
                self.loadPlugin(pluginName, self.pluginDirs["user"])
        
        if develPluginName:
            self.loadPlugin(develPluginName, develPluginPath)
            self.__develPluginName = develPluginName
    
    def loadPlugin(self, name, directory, reload_=False):
        """
        Public method to load a plugin module.
        
        Initially all modules are inactive. Modules that are requested on
        demand are sorted out and are added to the on demand list. Some
        basic validity checks are performed as well. Modules failing these
        checks are added to the failed modules list.
        
        @param name name of the module to be loaded (string)
        @param directory name of the plugin directory (string)
        @param reload_ flag indicating to reload the module (boolean)
        @exception PluginLoadError raised to indicate an issue loading
            the plug-in
        """
        try:
            fname = "{0}.py".format(os.path.join(directory, name))
            module = imp.load_source(name, fname)
            if not hasattr(module, "autoactivate"):
                module.error = self.tr(
                    "Module is missing the 'autoactivate' attribute.")
                self.__failedModules[name] = module
                raise PluginLoadError(name)
            if sys.version_info[0] < 3:
                if not hasattr(module, "python2Compatible"):
                    module.error = self.tr(
                        "Module is missing the Python2 compatibility flag."
                        " Please update.")
                    compatible = False
                elif not getattr(module, "python2Compatible"):
                    module.error = self.tr(
                        "Module is not Python2 compatible.")
                    compatible = False
                else:
                    compatible = True
                if not compatible:
                    self.__failedModules[name] = module
                    raise PluginPy2IncompatibleError(name)
            if getattr(module, "autoactivate"):
                self.__inactiveModules[name] = module
            else:
                if not hasattr(module, "pluginType") or \
                   not hasattr(module, "pluginTypename"):
                    module.error = \
                        self.tr("Module is missing the 'pluginType' "
                                "and/or 'pluginTypename' attributes.")
                    self.__failedModules[name] = module
                    raise PluginLoadError(name)
                else:
                    self.__onDemandInactiveModules[name] = module
            module.eric6PluginModuleName = name
            module.eric6PluginModuleFilename = fname
            self.__modulesCount += 1
            if reload_:
                imp.reload(module)
                self.initOnDemandPlugin(name)
                try:
                    pluginObject = self.__onDemandInactivePlugins[name]
                    pluginObject.initToolbar(
                        self.__ui, e5App().getObject("ToolbarManager"))
                except (KeyError, AttributeError):
                    pass
        except PluginLoadError:
            print("Error loading plug-in module:", name)
        except PluginPy2IncompatibleError:
            print("Error loading plug-in module:", name)
            print("The plug-in is not Python2 compatible.")
        except Exception as err:
            module = imp.new_module(name)
            module.error = self.tr(
                "Module failed to load. Error: {0}").format(str(err))
            self.__failedModules[name] = module
            print("Error loading plug-in module:", name)
            print(str(err))
    
    def unloadPlugin(self, name):
        """
        Public method to unload a plugin module.
        
        @param name name of the module to be unloaded (string)
        @return flag indicating success (boolean)
        """
        if name in self.__onDemandActiveModules:
            # cannot unload an ondemand plugin, that is in use
            return False
        
        if name in self.__activeModules:
            self.deactivatePlugin(name)
        
        if name in self.__inactiveModules:
            try:
                pluginObject = self.__inactivePlugins[name]
                try:
                    pluginObject.prepareUnload()
                except AttributeError:
                    pass
                del self.__inactivePlugins[name]
            except KeyError:
                pass
            del self.__inactiveModules[name]
        elif name in self.__onDemandInactiveModules:
            try:
                pluginObject = self.__onDemandInactivePlugins[name]
                try:
                    pluginObject.prepareUnload()
                except AttributeError:
                    pass
                del self.__onDemandInactivePlugins[name]
            except KeyError:
                pass
            del self.__onDemandInactiveModules[name]
        elif name in self.__failedModules:
            del self.__failedModules[name]
        
        self.__modulesCount -= 1
        return True
    
    def removePluginFromSysModules(self, pluginName, package,
                                   internalPackages):
        """
        Public method to remove a plugin and all related modules from
        sys.modules.
        
        @param pluginName name of the plugin module (string)
        @param package name of the plugin package (string)
        @param internalPackages list of intenal packages (list of string)
        @return flag indicating the plugin module was found in sys.modules
            (boolean)
        """
        packages = [package] + internalPackages
        found = False
        if not package:
            package = "__None__"
        for moduleName in list(sys.modules.keys())[:]:
            if moduleName == pluginName or \
                    moduleName.split(".")[0] in packages:
                found = True
                del sys.modules[moduleName]
        return found
    
    def initOnDemandPlugins(self):
        """
        Public method to create plugin objects for all on demand plugins.
        
        Note: The plugins are not activated.
        """
        names = sorted(self.__onDemandInactiveModules.keys())
        for name in names:
            self.initOnDemandPlugin(name)
    
    def initOnDemandPlugin(self, name):
        """
        Public method to create a plugin object for the named on demand plugin.
        
        Note: The plug-in is not activated.
        
        @param name name of the plug-in (string)
        @exception PluginActivationError raised to indicate an issue during the
            plug-in activation
        """
        try:
            try:
                module = self.__onDemandInactiveModules[name]
            except KeyError:
                return
            
            if not self.__canActivatePlugin(module):
                raise PluginActivationError(module.eric6PluginModuleName)
            version = getattr(module, "version")
            className = getattr(module, "className")
            pluginClass = getattr(module, className)
            pluginObject = None
            if name not in self.__onDemandInactivePlugins:
                pluginObject = pluginClass(self.__ui)
                pluginObject.eric6PluginModule = module
                pluginObject.eric6PluginName = className
                pluginObject.eric6PluginVersion = version
                self.__onDemandInactivePlugins[name] = pluginObject
        except PluginActivationError:
            return
    
    def initPluginToolbars(self, toolbarManager):
        """
        Public method to initialize plug-in toolbars.
        
        @param toolbarManager reference to the toolbar manager object
            (E5ToolBarManager)
        """
        self.initOnDemandPlugins()
        for pluginObject in self.__onDemandInactivePlugins.values():
            try:
                pluginObject.initToolbar(self.__ui, toolbarManager)
            except AttributeError:
                # ignore it
                pass
    
    def activatePlugins(self):
        """
        Public method to activate all plugins having the "autoactivate"
        attribute set to True.
        """
        savedInactiveList = Preferences.Prefs.settings.value(
            self.__inactivePluginsKey)
        if self.__develPluginName is not None and \
           savedInactiveList is not None and \
           self.__develPluginName in savedInactiveList:
            savedInactiveList.remove(self.__develPluginName)
        names = sorted(self.__inactiveModules.keys())
        for name in names:
            if savedInactiveList is None or name not in savedInactiveList:
                self.activatePlugin(name)
        self.allPlugginsActivated.emit()
    
    def activatePlugin(self, name, onDemand=False):
        """
        Public method to activate a plugin.
        
        @param name name of the module to be activated
        @keyparam onDemand flag indicating activation of an
            on demand plugin (boolean)
        @return reference to the initialized plugin object
        @exception PluginActivationError raised to indicate an issue during the
            plug-in activation
        """
        try:
            try:
                if onDemand:
                    module = self.__onDemandInactiveModules[name]
                else:
                    module = self.__inactiveModules[name]
            except KeyError:
                return None
            
            if not self.__canActivatePlugin(module):
                raise PluginActivationError(module.eric6PluginModuleName)
            version = getattr(module, "version")
            className = getattr(module, "className")
            pluginClass = getattr(module, className)
            pluginObject = None
            if onDemand and name in self.__onDemandInactivePlugins:
                pluginObject = self.__onDemandInactivePlugins[name]
            elif not onDemand and name in self.__inactivePlugins:
                pluginObject = self.__inactivePlugins[name]
            else:
                pluginObject = pluginClass(self.__ui)
            self.pluginAboutToBeActivated.emit(name, pluginObject)
            try:
                obj, ok = pluginObject.activate()
            except TypeError:
                module.error = self.tr(
                    "Incompatible plugin activation method.")
                obj = None
                ok = True
            except Exception as err:
                module.error = str(err)
                obj = None
                ok = False
            if not ok:
                return None
            
            self.pluginActivated.emit(name, pluginObject)
            pluginObject.eric6PluginModule = module
            pluginObject.eric6PluginName = className
            pluginObject.eric6PluginVersion = version
            
            if onDemand:
                self.__onDemandInactiveModules.pop(name)
                try:
                    self.__onDemandInactivePlugins.pop(name)
                except KeyError:
                    pass
                self.__onDemandActivePlugins[name] = pluginObject
                self.__onDemandActiveModules[name] = module
            else:
                self.__inactiveModules.pop(name)
                try:
                    self.__inactivePlugins.pop(name)
                except KeyError:
                    pass
                self.__activePlugins[name] = pluginObject
                self.__activeModules[name] = module
            return obj
        except PluginActivationError:
            return None
    
    def __canActivatePlugin(self, module):
        """
        Private method to check, if a plugin can be activated.
        
        @param module reference to the module to be activated
        @return flag indicating, if the module satisfies all requirements
            for being activated (boolean)
        @exception PluginModuleFormatError raised to indicate an invalid
            plug-in module format
        @exception PluginClassFormatError raised to indicate an invalid
            plug-in class format
        """
        try:
            if not hasattr(module, "version"):
                raise PluginModuleFormatError(
                    module.eric6PluginModuleName, "version")
            if not hasattr(module, "className"):
                raise PluginModuleFormatError(
                    module.eric6PluginModuleName, "className")
            className = getattr(module, "className")
            if not hasattr(module, className):
                raise PluginModuleFormatError(
                    module.eric6PluginModuleName, className)
            pluginClass = getattr(module, className)
            if not hasattr(pluginClass, "__init__"):
                raise PluginClassFormatError(
                    module.eric6PluginModuleName,
                    className, "__init__")
            if not hasattr(pluginClass, "activate"):
                raise PluginClassFormatError(
                    module.eric6PluginModuleName,
                    className, "activate")
            if not hasattr(pluginClass, "deactivate"):
                raise PluginClassFormatError(
                    module.eric6PluginModuleName,
                    className, "deactivate")
            return True
        except PluginModuleFormatError as e:
            print(repr(e))
            return False
        except PluginClassFormatError as e:
            print(repr(e))
            return False
    
    def deactivatePlugin(self, name, onDemand=False):
        """
        Public method to deactivate a plugin.
        
        @param name name of the module to be deactivated
        @keyparam onDemand flag indicating deactivation of an
            on demand plugin (boolean)
        """
        try:
            if onDemand:
                module = self.__onDemandActiveModules[name]
            else:
                module = self.__activeModules[name]
        except KeyError:
            return
        
        if self.__canDeactivatePlugin(module):
            pluginObject = None
            if onDemand and name in self.__onDemandActivePlugins:
                pluginObject = self.__onDemandActivePlugins[name]
            elif not onDemand and name in self.__activePlugins:
                pluginObject = self.__activePlugins[name]
            if pluginObject:
                self.pluginAboutToBeDeactivated.emit(name, pluginObject)
                pluginObject.deactivate()
                self.pluginDeactivated.emit(name, pluginObject)
                
                if onDemand:
                    self.__onDemandActiveModules.pop(name)
                    self.__onDemandActivePlugins.pop(name)
                    self.__onDemandInactivePlugins[name] = pluginObject
                    self.__onDemandInactiveModules[name] = module
                else:
                    self.__activeModules.pop(name)
                    try:
                        self.__activePlugins.pop(name)
                    except KeyError:
                        pass
                    self.__inactivePlugins[name] = pluginObject
                    self.__inactiveModules[name] = module
    
    def __canDeactivatePlugin(self, module):
        """
        Private method to check, if a plugin can be deactivated.
        
        @param module reference to the module to be deactivated
        @return flag indicating, if the module satisfies all requirements
            for being deactivated (boolean)
        """
        return getattr(module, "deactivateable", True)
    
    def getPluginObject(self, type_, typename, maybeActive=False):
        """
        Public method to activate an ondemand plugin given by type and
        typename.
        
        @param type_ type of the plugin to be activated (string)
        @param typename name of the plugin within the type category (string)
        @keyparam maybeActive flag indicating, that the plugin may be active
            already (boolean)
        @return reference to the initialized plugin object
        """
        for name, module in list(self.__onDemandInactiveModules.items()):
            if getattr(module, "pluginType") == type_ and \
               getattr(module, "pluginTypename") == typename:
                return self.activatePlugin(name, onDemand=True)
        
        if maybeActive:
            for name, module in list(self.__onDemandActiveModules.items()):
                if getattr(module, "pluginType") == type_ and \
                   getattr(module, "pluginTypename") == typename:
                    self.deactivatePlugin(name, onDemand=True)
                    return self.activatePlugin(name, onDemand=True)
        
        return None
    
    def getPluginInfos(self):
        """
        Public method to get infos about all loaded plugins.
        
        @return list of tuples giving module name (string), plugin name
            (string), version (string), autoactivate (boolean), active
            (boolean), short description (string), error flag (boolean)
        """
        infos = []
        
        for name in list(self.__activeModules.keys()):
            pname, shortDesc, error, version = \
                self.__getShortInfo(self.__activeModules[name])
            infos.append((name, pname, version, True, True, shortDesc, error))
        for name in list(self.__inactiveModules.keys()):
            pname, shortDesc, error, version = \
                self.__getShortInfo(self.__inactiveModules[name])
            infos.append(
                (name, pname, version, True, False, shortDesc, error))
        for name in list(self.__onDemandActiveModules.keys()):
            pname, shortDesc, error, version = \
                self.__getShortInfo(self.__onDemandActiveModules[name])
            infos.append(
                (name, pname, version, False, True, shortDesc, error))
        for name in list(self.__onDemandInactiveModules.keys()):
            pname, shortDesc, error, version = \
                self.__getShortInfo(self.__onDemandInactiveModules[name])
            infos.append(
                (name, pname, version, False, False, shortDesc, error))
        for name in list(self.__failedModules.keys()):
            pname, shortDesc, error, version = \
                self.__getShortInfo(self.__failedModules[name])
            infos.append(
                (name, pname, version, False, False, shortDesc, error))
        return infos
    
    def __getShortInfo(self, module):
        """
        Private method to extract the short info from a module.
        
        @param module module to extract short info from
        @return short info as a tuple giving plugin name (string),
            short description (string), error flag (boolean) and
            version (string)
        """
        name = getattr(module, "name", "")
        shortDesc = getattr(module, "shortDescription", "")
        version = getattr(module, "version", "")
        error = getattr(module, "error", "") != ""
        return name, shortDesc, error, version
    
    def getPluginDetails(self, name):
        """
        Public method to get detailed information about a plugin.
        
        @param name name of the module to get detailed infos about (string)
        @return details of the plugin as a dictionary
        """
        details = {}
        
        autoactivate = True
        active = True
        
        if name in self.__activeModules:
            module = self.__activeModules[name]
        elif name in self.__inactiveModules:
            module = self.__inactiveModules[name]
            active = False
        elif name in self.__onDemandActiveModules:
            module = self.__onDemandActiveModules[name]
            autoactivate = False
        elif name in self.__onDemandInactiveModules:
            module = self.__onDemandInactiveModules[name]
            autoactivate = False
            active = False
        elif name in self.__failedModules:
            module = self.__failedModules[name]
            autoactivate = False
            active = False
        else:
            # should not happen
            return None
        
        details["moduleName"] = name
        details["moduleFileName"] = getattr(
            module, "eric6PluginModuleFilename", "")
        details["pluginName"] = getattr(module, "name", "")
        details["version"] = getattr(module, "version", "")
        details["author"] = getattr(module, "author", "")
        details["description"] = getattr(module, "longDescription", "")
        details["autoactivate"] = autoactivate
        details["active"] = active
        details["error"] = getattr(module, "error", "")
        
        return details
    
    def doShutdown(self):
        """
        Public method called to perform actions upon shutdown of the IDE.
        """
        names = []
        for name in list(self.__inactiveModules.keys()):
            names.append(name)
        Preferences.Prefs.settings.setValue(self.__inactivePluginsKey, names)
        
        self.shutdown.emit()

    def getPluginDisplayStrings(self, type_):
        """
        Public method to get the display strings of all plugins of a specific
        type.
        
        @param type_ type of the plugins (string)
        @return dictionary with name as key and display string as value
            (dictionary of string)
        """
        pluginDict = {}
        
        for name, module in \
            list(self.__onDemandActiveModules.items()) + \
                list(self.__onDemandInactiveModules.items()):
            if getattr(module, "pluginType") == type_ and \
               getattr(module, "error", "") == "":
                plugin_name = getattr(module, "pluginTypename")
                if hasattr(module, "displayString"):
                    try:
                        disp = module.displayString()
                    except TypeError:
                        disp = getattr(module, "displayString")
                    if disp != "":
                        pluginDict[plugin_name] = disp
                else:
                    pluginDict[plugin_name] = plugin_name
        
        return pluginDict
        
    def getPluginPreviewPixmap(self, type_, name):
        """
        Public method to get a preview pixmap of a plugin of a specific type.
        
        @param type_ type of the plugin (string)
        @param name name of the plugin type (string)
        @return preview pixmap (QPixmap)
        """
        for modname, module in \
            list(self.__onDemandActiveModules.items()) + \
                list(self.__onDemandInactiveModules.items()):
            if getattr(module, "pluginType") == type_ and \
               getattr(module, "pluginTypename") == name:
                if hasattr(module, "previewPix"):
                    return module.previewPix()
                else:
                    return QPixmap()
        
        return QPixmap()
        
    def getPluginApiFiles(self, language):
        """
        Public method to get the list of API files installed by a plugin.
        
        @param language language of the requested API files (string)
        @return list of API filenames (list of string)
        """
        apis = []
        
        for module in list(self.__activeModules.values()) + \
                list(self.__onDemandActiveModules.values()):
            if hasattr(module, "apiFiles"):
                apis.extend(module.apiFiles(language))
        
        return apis
        
    def getPluginExeDisplayData(self):
        """
        Public method to get data to display information about a plugins
        external tool.
        
        @return list of dictionaries containing the data. Each dictionary must
            either contain data for the determination or the data to be
            displayed.<br />
            A dictionary of the first form must have the following entries:
            <ul>
                <li>programEntry - indicator for this dictionary form
                   (boolean), always True</li>
                <li>header - string to be diplayed as a header (string)</li>
                <li>exe - the executable (string)</li>
                <li>versionCommand - commandline parameter for the exe
                    (string)</li>
                <li>versionStartsWith - indicator for the output line
                    containing the version (string)</li>
                <li>versionPosition - number of element containing the
                    version (integer)</li>
                <li>version - version to be used as default (string)</li>
                <li>versionCleanup - tuple of two integers giving string
                    positions start and stop for the version string
                    (tuple of integers)</li>
            </ul>
            A dictionary of the second form must have the following entries:
            <ul>
                <li>programEntry - indicator for this dictionary form
                    (boolean), always False</li>
                <li>header - string to be diplayed as a header (string)</li>
                <li>text - entry text to be shown (string)</li>
                <li>version - version text to be shown (string)</li>
            </ul>
        """
        infos = []
        
        for module in list(self.__activeModules.values()) + \
                list(self.__inactiveModules.values()):
            if hasattr(module, "exeDisplayDataList"):
                infos.extend(module.exeDisplayDataList())
            elif hasattr(module, "exeDisplayData"):
                infos.append(module.exeDisplayData())
        for module in list(self.__onDemandActiveModules.values()) + \
                list(self.__onDemandInactiveModules.values()):
            if hasattr(module, "exeDisplayDataList"):
                infos.extend(module.exeDisplayDataList())
            elif hasattr(module, "exeDisplayData"):
                infos.append(module.exeDisplayData())
        
        return infos
        
    def getPluginConfigData(self):
        """
        Public method to get the config data of all active, non on-demand
        plugins used by the configuration dialog.
        
        Plugins supporting this functionality must provide the plugin module
        function 'getConfigData' returning a dictionary with unique keys
        of lists with the following list contents:
        <dl>
          <dt>display string</dt>
          <dd>string shown in the selection area of the configuration page.
              This should be a localized string</dd>
          <dt>pixmap name</dt>
          <dd>filename of the pixmap to be shown next to the display
              string</dd>
          <dt>page creation function</dt>
          <dd>plugin module function to be called to create the configuration
              page. The page must be subclasses from
              Preferences.ConfigurationPages.ConfigurationPageBase and must
              implement a method called 'save' to save the settings. A parent
              entry will be created in the selection list, if this value is
              None.</dd>
          <dt>parent key</dt>
          <dd>dictionary key of the parent entry or None, if this defines a
              toplevel entry.</dd>
          <dt>reference to configuration page</dt>
          <dd>This will be used by the configuration dialog and must always
              be None</dd>
        </dl>
        
        @return plug-in configuration data
        """
        configData = {}
        for module in list(self.__activeModules.values()) + \
            list(self.__onDemandActiveModules.values()) + \
                list(self.__onDemandInactiveModules.values()):
            if hasattr(module, 'getConfigData'):
                configData.update(module.getConfigData())
        return configData
        
    def isPluginLoaded(self, pluginName):
        """
        Public method to check, if a certain plugin is loaded.
        
        @param pluginName name of the plugin to check for (string)
        @return flag indicating, if the plugin is loaded (boolean)
        """
        return pluginName in self.__activeModules or \
            pluginName in self.__inactiveModules or \
            pluginName in self.__onDemandActiveModules or \
            pluginName in self.__onDemandInactiveModules
        
    def isPluginActive(self, pluginName):
        """
        Public method to check, if a certain plugin is active.
        
        @param pluginName name of the plugin to check for (string)
        @return flag indicating, if the plugin is active (boolean)
        """
        return pluginName in self.__activeModules or \
            pluginName in self.__onDemandActiveModules
    
    ###########################################################################
    ## Specialized plugin module handling methods below
    ###########################################################################
    
    ###########################################################################
    ## VCS related methods below
    ###########################################################################
    
    def getVcsSystemIndicators(self):
        """
        Public method to get the Vcs System indicators.
        
        Plugins supporting this functionality must support the module function
        getVcsSystemIndicator returning a dictionary with indicator as key and
        a tuple with the vcs name (string) and vcs display string (string).
        
        @return dictionary with indicator as key and a list of tuples as
            values. Each tuple contains the vcs name (string) and vcs display
            string (string).
        """
        vcsDict = {}
        
        for name, module in \
            list(self.__onDemandActiveModules.items()) + \
                list(self.__onDemandInactiveModules.items()):
            if getattr(module, "pluginType") == "version_control":
                if hasattr(module, "getVcsSystemIndicator"):
                    res = module.getVcsSystemIndicator()
                    for indicator, vcsData in list(res.items()):
                        if indicator in vcsDict:
                            vcsDict[indicator].append(vcsData)
                        else:
                            vcsDict[indicator] = [vcsData]
        
        return vcsDict
    
    def deactivateVcsPlugins(self):
        """
        Public method to deactivated all activated VCS plugins.
        """
        for name, module in list(self.__onDemandActiveModules.items()):
            if getattr(module, "pluginType") == "version_control":
                self.deactivatePlugin(name, True)
    
    ########################################################################
    ## Methods creation of the plug-ins download directory
    ########################################################################
    
    def __checkPluginsDownloadDirectory(self):
        """
        Private slot to check for the existence of the plugins download
        directory.
        """
        downloadDir = Preferences.getPluginManager("DownloadPath")
        if not downloadDir:
            downloadDir = self.__defaultDownloadDir
        
        if not os.path.exists(downloadDir):
            try:
                os.mkdir(downloadDir, 0o755)
            except (OSError, IOError) as err:
                # try again with (possibly) new default
                downloadDir = self.__defaultDownloadDir
                if not os.path.exists(downloadDir):
                    try:
                        os.mkdir(downloadDir, 0o755)
                    except (OSError, IOError) as err:
                        E5MessageBox.critical(
                            self.__ui,
                            self.tr("Plugin Manager Error"),
                            self.tr(
                                """<p>The plugin download directory"""
                                """ <b>{0}</b> could not be created. Please"""
                                """ configure it via the configuration"""
                                """ dialog.</p><p>Reason: {1}</p>""")
                            .format(downloadDir, str(err)))
                        downloadDir = ""
        
        Preferences.setPluginManager("DownloadPath", downloadDir)
    
    def preferencesChanged(self):
        """
        Public slot to react to changes in configuration.
        """
        self.__checkPluginsDownloadDirectory()
    
    ########################################################################
    ## Methods for automatic plug-in update check below
    ########################################################################
    
    def checkPluginUpdatesAvailable(self):
        """
        Public method to check the availability of updates of plug-ins.
        """
        period = Preferences.getPluginManager("UpdatesCheckInterval")
        if period == 0:
            return
        elif period in [1, 2, 3]:
            lastModified = QFileInfo(self.pluginRepositoryFile).lastModified()
            if lastModified.isValid() and lastModified.date().isValid():
                lastModifiedDate = lastModified.date()
                now = QDate.currentDate()
                if period == 1 and lastModifiedDate.day() == now.day():
                    # daily
                    return
                elif period == 2 and lastModifiedDate.daysTo(now) < 7:
                    # weekly
                    return
                elif period == 3 and \
                    (lastModifiedDate.daysTo(now) <
                     lastModifiedDate.daysInMonth()):
                    # monthly
                    return
        
        self.__updateAvailable = False
        
        request = QNetworkRequest(
            QUrl(Preferences.getUI("PluginRepositoryUrl6")))
        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute,
                             QNetworkRequest.AlwaysNetwork)
        reply = self.__networkManager.get(request)
        reply.finished.connect(self.__downloadRepositoryFileDone)
        self.__replies.append(reply)
    
    def __downloadRepositoryFileDone(self):
        """
        Private method called after the repository file was downloaded.
        """
        reply = self.sender()
        if reply in self.__replies:
            self.__replies.remove(reply)
        if reply.error() != QNetworkReply.NoError:
            E5MessageBox.warning(
                None,
                self.tr("Error downloading file"),
                self.tr(
                    """<p>Could not download the requested file"""
                    """ from {0}.</p><p>Error: {1}</p>"""
                ).format(Preferences.getUI("PluginRepositoryUrl6"),
                         reply.errorString())
            )
            reply.deleteLater()
            return
        
        ioDevice = QFile(self.pluginRepositoryFile + ".tmp")
        ioDevice.open(QIODevice.WriteOnly)
        ioDevice.write(reply.readAll())
        ioDevice.close()
        if QFile.exists(self.pluginRepositoryFile):
            QFile.remove(self.pluginRepositoryFile)
        ioDevice.rename(self.pluginRepositoryFile)
        reply.deleteLater()
        
        if os.path.exists(self.pluginRepositoryFile):
            f = QFile(self.pluginRepositoryFile)
            if f.open(QIODevice.ReadOnly):
                # save current URL
                url = Preferences.getUI("PluginRepositoryUrl6")
                
                # read the repository file
                from E5XML.PluginRepositoryReader import PluginRepositoryReader
                reader = PluginRepositoryReader(f, self.checkPluginEntry)
                reader.readXML()
                if url != Preferences.getUI("PluginRepositoryUrl6"):
                    # redo if it is a redirect
                    self.checkPluginUpdatesAvailable()
                    return
                
                if self.__updateAvailable:
                    res = E5MessageBox.information(
                        None,
                        self.tr("New plugin versions available"),
                        self.tr("<p>There are new plug-ins or plug-in"
                                " updates available. Use the plug-in"
                                " repository dialog to get them.</p>"),
                        E5MessageBox.StandardButtons(
                            E5MessageBox.Ignore |
                            E5MessageBox.Open),
                        E5MessageBox.Open)
                    if res == E5MessageBox.Open:
                        self.__ui.showPluginsAvailable()
    
    def checkPluginEntry(self, name, short, description, url, author, version,
                         filename, status):
        """
        Public method to check a plug-in's data for an update.
        
        @param name data for the name field (string)
        @param short data for the short field (string)
        @param description data for the description field (list of strings)
        @param url data for the url field (string)
        @param author data for the author field (string)
        @param version data for the version field (string)
        @param filename data for the filename field (string)
        @param status status of the plugin (string [stable, unstable, unknown])
        """
        # ignore hidden plug-ins
        pluginName = os.path.splitext(url.rsplit("/", 1)[1])[0]
        if pluginName in Preferences.getPluginManager("HiddenPlugins"):
            return
        
        archive = os.path.join(Preferences.getPluginManager("DownloadPath"),
                               filename)
        
        # Check against installed/loaded plug-ins
        pluginDetails = self.getPluginDetails(pluginName)
        if pluginDetails is None:
            if not Preferences.getPluginManager("CheckInstalledOnly"):
                self.__updateAvailable = True
            return
        
        if pluginDetails["version"] < version:
            self.__updateAvailable = True
            return
        
        if not Preferences.getPluginManager("CheckInstalledOnly"):
            # Check against downloaded plugin archives
            # 1. Check, if the archive file exists
            if not os.path.exists(archive):
                self.__updateAvailable = True
                return
            
            # 2. Check, if the archive is a valid zip file
            if not zipfile.is_zipfile(archive):
                self.__updateAvailable = True
                return
            
            # 3. Check the version of the archive file
            zip = zipfile.ZipFile(archive, "r")
            try:
                aversion = zip.read("VERSION").decode("utf-8")
            except KeyError:
                aversion = ""
            zip.close()
            
            if aversion != version:
                self.__updateAvailable = True
    
    def __sslErrors(self, reply, errors):
        """
        Private slot to handle SSL errors.
        
        @param reply reference to the reply object (QNetworkReply)
        @param errors list of SSL errors (list of QSslError)
        """
        ignored = self.__sslErrorHandler.sslErrorsReply(reply, errors)[0]
        if ignored == E5SslErrorHandler.NotIgnored:
            self.__downloadCancelled = True
