# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Ericapi plugin.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QObject, QCoreApplication
from PyQt5.QtWidgets import QDialog

from E5Gui.E5Application import e5App

from E5Gui.E5Action import E5Action

import Utilities

from eric6config import getConfig

# Start-Of-Header
name = "Ericapi Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = True
deactivateable = True
version = "6.1.0"
className = "EricapiPlugin"
packageName = "__core__"
shortDescription = "Show the Ericapi dialogs."
longDescription = """This plugin implements the Ericapi dialogs.""" \
    """ Ericapi is used to generate a QScintilla API file for Python and""" \
    """ Ruby projects."""
pyqtApi = 2
python2Compatible = True
# End-Of-Header

error = ""


def exeDisplayData():
    """
    Public method to support the display of some executable info.
    
    @return dictionary containing the data to query the presence of
        the executable
    """
    exe = 'eric6_api'
    if Utilities.isWindowsPlatform():
        exe = os.path.join(getConfig("bindir"), exe + '.bat')
    
    data = {
        "programEntry": True,
        "header": QCoreApplication.translate(
            "EricapiPlugin", "Eric6 API File Generator"),
        "exe": exe,
        "versionCommand": '--version',
        "versionStartsWith": 'eric6_',
        "versionPosition": -3,
        "version": "",
        "versionCleanup": None,
    }
    
    return data


class EricapiPlugin(QObject):
    """
    Class implementing the Ericapi plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        super(EricapiPlugin, self).__init__(ui)
        self.__ui = ui
        self.__initialize()
        
    def __initialize(self):
        """
        Private slot to (re)initialize the plugin.
        """
        self.__projectAct = None

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        menu = e5App().getObject("Project").getMenu("Apidoc")
        if menu:
            self.__projectAct = E5Action(
                self.tr('Generate API file (eric6_api)'),
                self.tr('Generate &API file (eric6_api)'), 0, 0,
                self, 'doc_eric6_api')
            self.__projectAct.setStatusTip(self.tr(
                'Generate an API file using eric6_api'))
            self.__projectAct.setWhatsThis(self.tr(
                """<b>Generate API file</b>"""
                """<p>Generate an API file using eric6_api.</p>"""
            ))
            self.__projectAct.triggered.connect(self.__doEricapi)
            e5App().getObject("Project").addE5Actions([self.__projectAct])
            menu.addAction(self.__projectAct)
        
        e5App().getObject("Project").showMenu.connect(self.__projectShowMenu)
        
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        e5App().getObject("Project").showMenu.disconnect(
            self.__projectShowMenu)
        
        menu = e5App().getObject("Project").getMenu("Apidoc")
        if menu:
            menu.removeAction(self.__projectAct)
            e5App().getObject("Project").removeE5Actions([self.__projectAct])
        self.__initialize()
    
    def __projectShowMenu(self, menuName, menu):
        """
        Private slot called, when the the project menu or a submenu is
        about to be shown.
        
        @param menuName name of the menu to be shown (string)
        @param menu reference to the menu (QMenu)
        """
        if menuName == "Apidoc":
            if self.__projectAct is not None:
                self.__projectAct.setEnabled(
                    e5App().getObject("Project").getProjectLanguage() in
                    ["Python", "Python2", "Python3", "Ruby"])
    
    def __doEricapi(self):
        """
        Private slot to perform the eric6_api api generation.
        """
        from DocumentationPlugins.Ericapi.EricapiConfigDialog import \
            EricapiConfigDialog
        eolTranslation = {
            '\r': 'cr',
            '\n': 'lf',
            '\r\n': 'crlf',
        }
        project = e5App().getObject("Project")
        parms = project.getData('DOCUMENTATIONPARMS', "ERIC4API")
        dlg = EricapiConfigDialog(project, parms)
        if dlg.exec_() == QDialog.Accepted:
            args, parms = dlg.generateParameters()
            project.setData('DOCUMENTATIONPARMS', "ERIC4API", parms)
            
            # add parameter for the eol setting
            if not project.useSystemEol():
                args.append(
                    "--eol={0}".format(eolTranslation[project.getEolString()]))
            
            # now do the call
            from DocumentationPlugins.Ericapi.EricapiExecDialog import \
                EricapiExecDialog
            dia = EricapiExecDialog("Ericapi")
            res = dia.start(args, project.ppath)
            if res:
                dia.exec_()
            
            outputFileName = Utilities.toNativeSeparators(parms['outputFile'])
            
            # add output files to the project data, if they aren't in already
            for progLanguage in parms['languages']:
                if "%L" in outputFileName:
                    outfile = outputFileName.replace("%L", progLanguage)
                else:
                    if len(parms['languages']) == 1:
                        outfile = outputFileName
                    else:
                        root, ext = os.path.splitext(outputFileName)
                        outfile = "{0}-{1}{2}".format(
                            root, progLanguage.lower(), ext)
                
                outfile = project.getRelativePath(outfile)
                if outfile not in project.pdata['OTHERS']:
                    project.pdata['OTHERS'].append(outfile)
                    project.setDirty(True)
                    project.othersAdded(outfile)
