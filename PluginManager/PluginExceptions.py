# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the exceptions raised by the plugin system.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QCoreApplication


class PluginError(Exception):
    """
    Class defining a special error for the plugin classes.
    """
    def __init__(self):
        """
        Constructor
        """
        self._errorMessage = QCoreApplication.translate(
            "PluginError", "Unspecific plugin error.")
        
    def __repr__(self):
        """
        Special method returning a representation of the exception.
        
        @return string representing the error message
        """
        return str(self._errorMessage)
        
    def __str__(self):
        """
        Special method returning a string representation of the exception.
        
        @return string representing the error message
        """
        return str(self._errorMessage)


class PluginPathError(PluginError):
    """
    Class defining an error raised, when the plugin paths were not found and
    could not be created.
    """
    def __init__(self, msg=None):
        """
        Constructor
        
        @param msg message to be used by the exception (string)
        """
        if msg:
            self._errorMessage = msg
        else:
            self._errorMessage = QCoreApplication.translate(
                "PluginError",
                "Plugin paths not found or not creatable.")


class PluginModulesError(PluginError):
    """
    Class defining an error raised, when no plugin modules were found.
    """
    def __init__(self):
        """
        Constructor
        """
        self._errorMessage = QCoreApplication.translate(
            "PluginError", "No plugin modules found.")


class PluginLoadError(PluginError):
    """
    Class defining an error raised, when there was an error during plugin
    loading.
    """
    def __init__(self, name):
        """
        Constructor
        
        @param name name of the plugin module (string)
        """
        self._errorMessage = \
            QCoreApplication.translate(
                "PluginError",
                "Error loading plugin module: {0}")\
            .format(name)


class PluginActivationError(PluginError):
    """
    Class defining an error raised, when there was an error during plugin
    activation.
    """
    def __init__(self, name):
        """
        Constructor
        
        @param name name of the plugin module (string)
        """
        self._errorMessage = \
            QCoreApplication.translate(
                "PluginError",
                "Error activating plugin module: {0}")\
            .format(name)


class PluginModuleFormatError(PluginError):
    """
    Class defining an error raised, when the plugin module is invalid.
    """
    def __init__(self, name, missing):
        """
        Constructor
        
        @param name name of the plugin module (string)
        @param missing description of the missing element (string)
        """
        self._errorMessage = \
            QCoreApplication.translate(
                "PluginError",
                "The plugin module {0} is missing {1}.")\
            .format(name, missing)


class PluginClassFormatError(PluginError):
    """
    Class defining an error raised, when the plugin module's class is invalid.
    """
    def __init__(self, name, class_, missing):
        """
        Constructor
        
        @param name name of the plugin module (string)
        @param class_ name of the class not satisfying the requirements
            (string)
        @param missing description of the missing element (string)
        """
        self._errorMessage = \
            QCoreApplication.translate(
                "PluginError",
                "The plugin class {0} of module {1} is missing {2}.")\
            .format(class_, name, missing)


class PluginPy2IncompatibleError(PluginError):
    """
    Class defining an error raised, when the plugin is incompatible
    with Python2.
    """
    def __init__(self, name):
        """
        Constructor
        
        @param name name of the plugin module (string)
        """
        self._errorMessage = \
            QCoreApplication.translate(
                "PluginError",
                "The plugin module {0} is not compatible with Python2.")\
            .format(name)
