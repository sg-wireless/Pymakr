# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the web plug-in interface.
"""


from __future__ import unicode_literals


class WebPluginInterface(object):
    """
    Class implementing the web plug-in interface.
    """
    def metaPlugin(self):
        """
        Public method to create a meta plug-in object containing plug-in info.
        
        @ireturn meta plug-in object (QWebPluginFactory.Plugin)
        @exception NotImplementedError raised to indicate that this method
            must be implemented by subclasses
        """
        raise NotImplementedError
    
    def create(self, mimeType, url, argumentNames, argumentValues):
        """
        Public method to create a plug-in instance for the given data.
        
        @param mimeType MIME type for the plug-in (string)
        @param url URL for the plug-in (QUrl)
        @param argumentNames list of argument names (list of strings)
        @param argumentValues list of argument values (list of strings)
        @ireturn reference to the created object (QWidget)
        @exception NotImplementedError raised to indicate that this method
            must be implemented by subclasses
        """
        raise NotImplementedError
    
    def configure(self):
        """
        Public method to configure the plug-in.
        
        @exception NotImplementedError raised to indicate that this method
            must be implemented by subclasses
        """
        raise NotImplementedError
    
    def isAnonymous(self):
        """
        Public method to indicate an anonymous plug-in.
        
        @return flag indicating anonymous state (boolean)
        """
        return False
