# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Tabnanny plugin.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QObject, pyqtSignal

from E5Gui.E5Application import e5App
from E5Gui.E5Action import E5Action
from Project.ProjectBrowserModel import ProjectBrowserFileItem
from Utilities import determinePythonVersion

import Preferences

# Start-Of-Header
name = "Tabnanny Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = True
deactivateable = True
version = "6.1.0"
className = "TabnannyPlugin"
packageName = "__core__"
shortDescription = "Show the Tabnanny dialog."
longDescription = """This plugin implements the Tabnanny dialog.""" \
    """ Tabnanny is used to check Python source files for correct""" \
    """ indentations."""
pyqtApi = 2
python2Compatible = True
# End-Of-Header

error = ""


class TabnannyPlugin(QObject):
    """
    Class implementing the Tabnanny plugin.
    
    @signal indentChecked(str, bool, str, str) emitted when the indent
        check was done.
    @signal batchFinished() emitted when a style check batch is done
    @signal error(str, str) emitted in case of an error
    """
    indentChecked = pyqtSignal(str, bool, str, str)
    batchFinished = pyqtSignal()
    error = pyqtSignal(str, str)
    
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        super(TabnannyPlugin, self).__init__(ui)
        self.__ui = ui
        self.__initialize()
        
        self.backgroundService = e5App().getObject("BackgroundService")
        
        path = os.path.join(
            os.path.dirname(__file__), 'CheckerPlugins', 'Tabnanny')
        self.backgroundService.serviceConnect(
            'indent', 'Python2', path, 'Tabnanny',
            lambda *args: self.indentChecked.emit(*args),
            onErrorCallback=self.serviceErrorPy2,
            onBatchDone=self.batchJobDone)
        self.backgroundService.serviceConnect(
            'indent', 'Python3', path, 'Tabnanny',
            lambda *args: self.indentChecked.emit(*args),
            onErrorCallback=self.serviceErrorPy3,
            onBatchDone=self.batchJobDone)
        
        self.queuedBatches = []
        self.batchesFinished = True
    
    def __serviceError(self, fn, msg):
        """
        Private slot handling service errors.
        
        @param fn file name (string)
        @param msg message text (string)
        """
        self.error.emit(fn, msg)
    
    def serviceErrorPy2(self, fx, lang, fn, msg):
        """
        Public slot handling service errors for Python 2.
        
        @param fx service name (string)
        @param lang language (string)
        @param fn file name (string)
        @param msg message text (string)
        """
        if fx in ['indent', 'batch_indent'] and lang == 'Python2':
            if fx == 'indent':
                self.__serviceError(fn, msg)
            else:
                self.__serviceError(self.tr("Python 2 batch check"), msg)
                self.batchJobDone(fx, lang)
    
    def serviceErrorPy3(self, fx, lang, fn, msg):
        """
        Public slot handling service errors for Python 2.
        
        @param fx service name (string)
        @param lang language (string)
        @param fn file name (string)
        @param msg message text (string)
        """
        if fx in ['indent', 'batch_indent'] and lang == 'Python3':
            if fx == 'indent':
                self.__serviceError(fn, msg)
            else:
                self.__serviceError(self.tr("Python 3 batch check"), msg)
                self.batchJobDone(fx, lang)
    
    def batchJobDone(self, fx, lang):
        """
        Public slot handling the completion of a batch job.
        
        @param fx service name (string)
        @param lang language (string)
        """
        if fx in ['indent', 'batch_indent']:
            if lang in self.queuedBatches:
                self.queuedBatches.remove(lang)
            # prevent sending the signal multiple times
            if len(self.queuedBatches) == 0 and not self.batchesFinished:
                self.batchFinished.emit()
                self.batchesFinished = True
    
    def __initialize(self):
        """
        Private slot to (re)initialize the plugin.
        """
        self.__projectAct = None
        self.__projectTabnannyDialog = None
        
        self.__projectBrowserAct = None
        self.__projectBrowserMenu = None
        self.__projectBrowserTabnannyDialog = None
        
        self.__editors = []
        self.__editorAct = None
        self.__editorTabnannyDialog = None

    def indentCheck(self, lang, filename, source):
        """
        Public method to prepare an indentation check on one Python source
        file.

        @param lang language of the file or None to determine by internal
            algorithm (str or None)
        @param filename source filename (string)
        @param source string containing the code to check (string)
        """
        if lang is None:
            lang = 'Python{0}'.format(determinePythonVersion(filename, source))
        if lang not in ['Python2', 'Python3']:
            return
        
        self.backgroundService.enqueueRequest(
            'indent', lang, filename, [source])

    def indentBatchCheck(self, argumentsList):
        """
        Public method to prepare an indentation check on multiple Python
        source files.
        
        @param argumentsList list of arguments tuples with each tuple
            containing filename and source (string, string)
        """
        data = {
            "Python2": [],
            "Python3": [],
        }
        for filename, source in argumentsList:
            lang = 'Python{0}'.format(determinePythonVersion(filename, source))
            if lang not in ['Python2', 'Python3']:
                continue
            else:
                data[lang].append((filename, source))
        
        self.queuedBatches = []
        for lang in ['Python2', 'Python3']:
            if data[lang]:
                self.queuedBatches.append(lang)
                self.backgroundService.enqueueRequest('batch_indent', lang, "",
                                                      data[lang])
                self.batchesFinished = False
    
    def cancelIndentBatchCheck(self):
        """
        Public method to cancel all batch jobs.
        """
        for lang in ['Python2', 'Python3']:
            self.backgroundService.requestCancel('batch_style', lang)
    
    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        menu = e5App().getObject("Project").getMenu("Checks")
        if menu:
            self.__projectAct = E5Action(
                self.tr('Check Indentations'),
                self.tr('&Indentations...'), 0, 0,
                self, 'project_check_indentations')
            self.__projectAct.setStatusTip(
                self.tr('Check indentations using tabnanny.'))
            self.__projectAct.setWhatsThis(self.tr(
                """<b>Check Indentations...</b>"""
                """<p>This checks Python files"""
                """ for bad indentations using tabnanny.</p>"""
            ))
            self.__projectAct.triggered.connect(self.__projectTabnanny)
            e5App().getObject("Project").addE5Actions([self.__projectAct])
            menu.addAction(self.__projectAct)
        
        self.__editorAct = E5Action(
            self.tr('Check Indentations'),
            self.tr('&Indentations...'), 0, 0,
            self, "")
        self.__editorAct.setWhatsThis(self.tr(
            """<b>Check Indentations...</b>"""
            """<p>This checks Python files"""
            """ for bad indentations using tabnanny.</p>"""
        ))
        self.__editorAct.triggered.connect(self.__editorTabnanny)
        
        e5App().getObject("Project").showMenu.connect(self.__projectShowMenu)
        e5App().getObject("ProjectBrowser").getProjectBrowser("sources")\
            .showMenu.connect(self.__projectBrowserShowMenu)
        e5App().getObject("ViewManager").editorOpenedEd.connect(
            self.__editorOpened)
        e5App().getObject("ViewManager").editorClosedEd.connect(
            self.__editorClosed)
        
        for editor in e5App().getObject("ViewManager").getOpenEditors():
            self.__editorOpened(editor)
        
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        e5App().getObject("Project").showMenu.disconnect(
            self.__projectShowMenu)
        e5App().getObject("ProjectBrowser").getProjectBrowser("sources")\
            .showMenu.disconnect(self.__projectBrowserShowMenu)
        e5App().getObject("ViewManager").editorOpenedEd.disconnect(
            self.__editorOpened)
        e5App().getObject("ViewManager").editorClosedEd.disconnect(
            self.__editorClosed)
        
        menu = e5App().getObject("Project").getMenu("Checks")
        if menu:
            menu.removeAction(self.__projectAct)
        
        if self.__projectBrowserMenu:
            if self.__projectBrowserAct:
                self.__projectBrowserMenu.removeAction(
                    self.__projectBrowserAct)
        
        for editor in self.__editors:
            editor.showMenu.disconnect(self.__editorShowMenu)
            menu = editor.getMenu("Checks")
            if menu is not None:
                menu.removeAction(self.__editorAct)
        
        self.__initialize()
    
    def __projectShowMenu(self, menuName, menu):
        """
        Private slot called, when the the project menu or a submenu is
        about to be shown.
        
        @param menuName name of the menu to be shown (string)
        @param menu reference to the menu (QMenu)
        """
        if menuName == "Checks" and self.__projectAct is not None:
            self.__projectAct.setEnabled(
                e5App().getObject("Project").getProjectLanguage() in
                ["Python3", "Python2", "Python"])
    
    def __projectBrowserShowMenu(self, menuName, menu):
        """
        Private slot called, when the the project browser context menu or a
        submenu is about to be shown.
        
        @param menuName name of the menu to be shown (string)
        @param menu reference to the menu (QMenu)
        """
        if menuName == "Checks" and \
           e5App().getObject("Project").getProjectLanguage() in \
                ["Python3", "Python2", "Python"]:
            self.__projectBrowserMenu = menu
            if self.__projectBrowserAct is None:
                self.__projectBrowserAct = E5Action(
                    self.tr('Check Indentations'),
                    self.tr('&Indentations...'), 0, 0,
                    self, "")
                self.__projectBrowserAct.setWhatsThis(self.tr(
                    """<b>Check Indentations...</b>"""
                    """<p>This checks Python files"""
                    """ for bad indentations using tabnanny.</p>"""
                ))
                self.__projectBrowserAct.triggered.connect(
                    self.__projectBrowserTabnanny)
            if self.__projectBrowserAct not in menu.actions():
                menu.addAction(self.__projectBrowserAct)
    
    def __projectTabnanny(self):
        """
        Private slot used to check the project files for bad indentations.
        """
        project = e5App().getObject("Project")
        project.saveAllScripts()
        ppath = project.getProjectPath()
        files = [os.path.join(ppath, file)
                 for file in project.pdata["SOURCES"]
                 if file.endswith(
                     tuple(Preferences.getPython("Python3Extensions")) +
                     tuple(Preferences.getPython("PythonExtensions")))]
        
        from CheckerPlugins.Tabnanny.TabnannyDialog import TabnannyDialog
        self.__projectTabnannyDialog = TabnannyDialog(self)
        self.__projectTabnannyDialog.show()
        self.__projectTabnannyDialog.prepare(files, project)
    
    def __projectBrowserTabnanny(self):
        """
        Private method to handle the tabnanny context menu action of the
        project sources browser.
        """
        browser = e5App().getObject("ProjectBrowser").getProjectBrowser(
            "sources")
        if browser.getSelectedItemsCount([ProjectBrowserFileItem]) > 1:
            fn = []
            for itm in browser.getSelectedItems([ProjectBrowserFileItem]):
                fn.append(itm.fileName())
        else:
            itm = browser.model().item(browser.currentIndex())
            try:
                fn = itm.fileName()
            except AttributeError:
                fn = itm.dirName()
        
        from CheckerPlugins.Tabnanny.TabnannyDialog import TabnannyDialog
        self.__projectBrowserTabnannyDialog = TabnannyDialog(self)
        self.__projectBrowserTabnannyDialog.show()
        self.__projectBrowserTabnannyDialog.start(fn)
    
    def __editorOpened(self, editor):
        """
        Private slot called, when a new editor was opened.
        
        @param editor reference to the new editor (QScintilla.Editor)
        """
        menu = editor.getMenu("Checks")
        if menu is not None:
            menu.addAction(self.__editorAct)
            editor.showMenu.connect(self.__editorShowMenu)
            self.__editors.append(editor)
    
    def __editorClosed(self, editor):
        """
        Private slot called, when an editor was closed.
        
        @param editor reference to the editor (QScintilla.Editor)
        """
        try:
            self.__editors.remove(editor)
        except ValueError:
            pass
    
    def __editorShowMenu(self, menuName, menu, editor):
        """
        Private slot called, when the the editor context menu or a submenu is
        about to be shown.
        
        @param menuName name of the menu to be shown (string)
        @param menu reference to the menu (QMenu)
        @param editor reference to the editor
        """
        if menuName == "Checks":
            if self.__editorAct not in menu.actions():
                menu.addAction(self.__editorAct)
            self.__editorAct.setEnabled(editor.isPyFile())
    
    def __editorTabnanny(self):
        """
        Private slot to handle the tabnanny context menu action of the editors.
        """
        editor = e5App().getObject("ViewManager").activeWindow()
        if editor is not None:
            if editor.checkDirty() and editor.getFileName() is not None:
                from CheckerPlugins.Tabnanny.TabnannyDialog import \
                    TabnannyDialog
                self.__editorTabnannyDialog = TabnannyDialog(self)
                self.__editorTabnannyDialog.show()
                self.__editorTabnannyDialog.start(editor.getFileName())
