# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the writer class for writing an XML shortcuts file.
"""

from __future__ import unicode_literals

import time

from E5Gui.E5Application import e5App

from .XMLStreamWriterBase import XMLStreamWriterBase
from .Config import shortcutsFileFormatVersion

import Preferences


class ShortcutsWriter(XMLStreamWriterBase):
    """
    Class implementing the writer class for writing an XML shortcuts file.
    """
    def __init__(self, device):
        """
        Constructor
        
        @param device reference to the I/O device to write to (QIODevice)
        """
        XMLStreamWriterBase.__init__(self, device)
        
        self.email = Preferences.getUser("Email")
        
    def writeXML(self):
        """
        Public method to write the XML to the file.
        """
        XMLStreamWriterBase.writeXML(self)
        
        self.writeDTD('<!DOCTYPE Shortcuts SYSTEM "Shortcuts-{0}.dtd">'.format(
            shortcutsFileFormatVersion))
        
        # add some generation comments
        self.writeComment(" Eric6 keyboard shortcuts ")
        self.writeComment(
            " Saved: {0}".format(time.strftime('%Y-%m-%d, %H:%M:%S')))
        self.writeComment(" Author: {0} ".format(self.email))
        
        # add the main tag
        self.writeStartElement("Shortcuts")
        self.writeAttribute("version", shortcutsFileFormatVersion)
        
        self.__writeActions(
            "Project",
            e5App().getObject("Project").getActions())
        self.__writeActions(
            "General",
            e5App().getObject("UserInterface").getActions('ui'))
        self.__writeActions(
            "Wizards",
            e5App().getObject("UserInterface").getActions('wizards'))
        self.__writeActions(
            "Debug",
            e5App().getObject("DebugUI").getActions())
        self.__writeActions(
            "Edit",
            e5App().getObject("ViewManager").getActions('edit'))
        self.__writeActions(
            "File",
            e5App().getObject("ViewManager").getActions('file'))
        self.__writeActions(
            "Search",
            e5App().getObject("ViewManager").getActions('search'))
        self.__writeActions(
            "View",
            e5App().getObject("ViewManager").getActions('view'))
        self.__writeActions(
            "Macro",
            e5App().getObject("ViewManager").getActions('macro'))
        self.__writeActions(
            "Bookmarks",
            e5App().getObject("ViewManager").getActions('bookmark'))
        self.__writeActions(
            "Spelling",
            e5App().getObject("ViewManager").getActions('spelling'))
        self.__writeActions(
            "Window",
            e5App().getObject("ViewManager").getActions('window'))
        
        for category, ref in e5App().getPluginObjects():
            if hasattr(ref, "getActions"):
                self.__writeActions(category, ref.getActions())
    
        self.__writeActions(
            "HelpViewer",
            e5App().getObject("DummyHelpViewer").getActions())
    
        # add the main end tag
        self.writeEndElement()
        self.writeEndDocument()
    
    def __writeActions(self, category, actions):
        """
        Private method to write the shortcuts for the given actions.
        
        @param category category the actions belong to (string)
        @param actions list of actions to write (E5Action)
        """
        for act in actions:
            if act.objectName():
                # shortcuts are only exported, if their objectName is set
                self.writeStartElement("Shortcut")
                self.writeAttribute("category", category)
                self.writeTextElement("Name", act.objectName())
                self.writeTextElement("Accel", act.shortcut().toString())
                self.writeTextElement(
                    "AltAccel", act.alternateShortcut().toString())
                self.writeEndElement()
