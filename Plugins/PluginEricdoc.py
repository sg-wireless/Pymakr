# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Ericdoc plugin.
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
name = "Ericdoc Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = True
deactivateable = True
version = "6.1.0"
className = "EricdocPlugin"
packageName = "__core__"
shortDescription = "Show the Ericdoc dialogs."
longDescription = """This plugin implements the Ericdoc dialogs.""" \
    """ Ericdoc is used to generate a source code documentation""" \
    """ for Python and Ruby projects."""
pyqtApi = 2
python2Compatible = True
# End-Of-Header

error = ""


def exeDisplayDataList():
    """
    Public method to support the display of some executable info.
    
    @return dictionary containing the data to query the presence of
        the executable
    """
    dataList = []
    
    # 1. eric6_doc
    exe = 'eric6_doc'
    if Utilities.isWindowsPlatform():
        exe = os.path.join(getConfig("bindir"), exe + '.bat')
    dataList.append({
        "programEntry": True,
        "header": QCoreApplication.translate(
            "EricdocPlugin", "Eric6 Documentation Generator"),
        "exe": exe,
        "versionCommand": '--version',
        "versionStartsWith": 'eric6_',
        "versionPosition": -3,
        "version": "",
        "versionCleanup": None,
    })
    
    # 2. Qt Help Generator
    exe = os.path.join(Utilities.getQtBinariesPath(), 'qhelpgenerator')
    if Utilities.isWindowsPlatform():
        exe += '.exe'
    dataList.append({
        "programEntry": True,
        "header": QCoreApplication.translate(
            "EricdocPlugin", "Qt Help Tools"),
        "exe": exe,
        "versionCommand": '-v',
        "versionStartsWith": 'Qt',
        "versionPosition": -1,
        "version": "",
        "versionCleanup": (0, -1),
    })
    
    # 3. Qt Collection Generator
    exe = os.path.join(Utilities.getQtBinariesPath(), 'qcollectiongenerator')
    if Utilities.isWindowsPlatform():
        exe += '.exe'
    dataList.append({
        "programEntry": True,
        "header": QCoreApplication.translate(
            "EricdocPlugin", "Qt Help Tools"),
        "exe": exe,
        "versionCommand": '-v',
        "versionStartsWith": 'Qt',
        "versionPosition": -1,
        "version": "",
        "versionCleanup": (0, -1),
    })
    
    return dataList


class EricdocPlugin(QObject):
    """
    Class implementing the Ericdoc plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        super(EricdocPlugin, self).__init__(ui)
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
            self.__projectAct = \
                E5Action(
                    self.tr('Generate documentation (eric6_doc)'),
                    self.tr('Generate &documentation (eric6_doc)'), 0, 0,
                    self, 'doc_eric6_doc')
            self.__projectAct.setStatusTip(
                self.tr('Generate API documentation using eric6_doc'))
            self.__projectAct.setWhatsThis(self.tr(
                """<b>Generate documentation</b>"""
                """<p>Generate API documentation using eric6_doc.</p>"""
            ))
            self.__projectAct.triggered.connect(self.__doEricdoc)
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
    
    def __doEricdoc(self):
        """
        Private slot to perform the eric6_doc api documentation generation.
        """
        from DocumentationPlugins.Ericdoc.EricdocConfigDialog import \
            EricdocConfigDialog
        eolTranslation = {
            '\r': 'cr',
            '\n': 'lf',
            '\r\n': 'crlf',
        }
        project = e5App().getObject("Project")
        parms = project.getData('DOCUMENTATIONPARMS', "ERIC4DOC")
        dlg = EricdocConfigDialog(project, parms)
        if dlg.exec_() == QDialog.Accepted:
            args, parms = dlg.generateParameters()
            project.setData('DOCUMENTATIONPARMS', "ERIC4DOC", parms)
            
            # add parameter for the eol setting
            if not project.useSystemEol():
                args.append(
                    "--eol={0}".format(eolTranslation[project.getEolString()]))
            
            # now do the call
            from DocumentationPlugins.Ericdoc.EricdocExecDialog import \
                EricdocExecDialog
            dia = EricdocExecDialog("Ericdoc")
            res = dia.start(args, project.ppath)
            if res:
                dia.exec_()
            
            outdir = Utilities.toNativeSeparators(parms['outputDirectory'])
            if outdir == '':
                outdir = 'doc'      # that is eric6_docs default output dir
                
            # add it to the project data, if it isn't in already
            outdir = project.getRelativePath(outdir)
            if outdir not in project.pdata['OTHERS']:
                project.pdata['OTHERS'].append(outdir)
                project.setDirty(True)
                project.othersAdded(outdir)
            
            if parms['qtHelpEnabled']:
                outdir = Utilities.toNativeSeparators(
                    parms['qtHelpOutputDirectory'])
                if outdir == '':
                    outdir = 'help'
                    # that is eric6_docs default QtHelp output dir
                    
                # add it to the project data, if it isn't in already
                outdir = project.getRelativePath(outdir)
                if outdir not in project.pdata['OTHERS']:
                    project.pdata['OTHERS'].append(outdir)
                    project.setDirty(True)
                    project.othersAdded(outdir)
