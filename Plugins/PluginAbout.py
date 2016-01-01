# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the About plugin.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QAction

import UI.Info
import UI.PixmapCache

from E5Gui.E5Action import E5Action
from E5Gui import E5MessageBox

# Start-Of-Header
name = "About Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = True
deactivateable = True
version = "6.1.0"
className = "AboutPlugin"
packageName = "__core__"
shortDescription = "Show the About dialogs."
longDescription = """This plugin shows the About dialogs."""
pyqtApi = 2
python2Compatible = True
# End-Of-Header

error = ""


class AboutPlugin(QObject):
    """
    Class implementing the About plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        super(AboutPlugin, self).__init__(ui)
        self.__ui = ui

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        self.__initActions()
        self.__initMenu()
        
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        menu = self.__ui.getMenu("help")
        if menu:
            menu.removeAction(self.aboutAct)
            menu.removeAction(self.aboutQtAct)
        acts = [self.aboutAct, self.aboutQtAct]
        self.__ui.removeE5Actions(acts, 'ui')
    
    def __initActions(self):
        """
        Private method to initialize the actions.
        """
        acts = []
        
        self.aboutAct = E5Action(
            self.tr('About {0}').format(UI.Info.Program),
            UI.PixmapCache.getIcon("helpAbout.png"),
            self.tr('&About {0}').format(UI.Info.Program),
            0, 0, self, 'about_eric')
        self.aboutAct.setStatusTip(self.tr(
            'Display information about this software'))
        self.aboutAct.setWhatsThis(self.tr(
            """<b>About {0}</b>"""
            """<p>Display some information about this software.</p>"""
        ).format(UI.Info.Program))
        self.aboutAct.triggered.connect(self.__about)
        self.aboutAct.setMenuRole(QAction.AboutRole)
        acts.append(self.aboutAct)
        
        self.aboutQtAct = E5Action(
            self.tr('About Qt'),
            UI.PixmapCache.getIcon("helpAboutQt.png"),
            self.tr('About &Qt'), 0, 0, self, 'about_qt')
        self.aboutQtAct.setStatusTip(
            self.tr('Display information about the Qt toolkit'))
        self.aboutQtAct.setWhatsThis(self.tr(
            """<b>About Qt</b>"""
            """<p>Display some information about the Qt toolkit.</p>"""
        ))
        self.aboutQtAct.triggered.connect(self.__aboutQt)
        self.aboutQtAct.setMenuRole(QAction.AboutQtRole)
        acts.append(self.aboutQtAct)
        
        self.__ui.addE5Actions(acts, 'ui')

    def __initMenu(self):
        """
        Private method to add the actions to the right menu.
        """
        menu = self.__ui.getMenu("help")
        if menu:
            act = self.__ui.getMenuAction("help", "show_versions")
            if act:
                menu.insertAction(act, self.aboutAct)
                menu.insertAction(act, self.aboutQtAct)
            else:
                menu.addAction(self.aboutAct)
                menu.addAction(self.aboutQtAct)
    
    def __about(self):
        """
        Private slot to handle the About dialog.
        """
        from AboutPlugin.AboutDialog import AboutDialog
        dlg = AboutDialog(self.__ui)
        dlg.exec_()
        
    def __aboutQt(self):
        """
        Private slot to handle the About Qt dialog.
        """
        E5MessageBox.aboutQt(self.__ui, UI.Info.Program)
