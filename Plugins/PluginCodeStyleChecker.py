# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the code style checker plug-in.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QObject, pyqtSignal, QCoreApplication

from E5Gui.E5Application import e5App
from E5Gui.E5Action import E5Action
from Project.ProjectBrowserModel import ProjectBrowserFileItem
from Utilities import determinePythonVersion

import Preferences

# Start-Of-Header
name = "Code Style Checker Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = True
deactivateable = True
version = "6.1.0"
className = "CodeStyleCheckerPlugin"
packageName = "__core__"
shortDescription = "Show the Python Code Style Checker dialog."
longDescription = """This plugin implements the Python Code Style""" \
    """ Checker dialog. A PEP-8 checker is used to check Python source""" \
    """ files for compliance to the code style conventions given in PEP-8.""" \
    """ A PEP-257 checker is used to check Python source files for""" \
    """ compliance to docstring conventions given in PEP-257 and an""" \
    """ eric6 variant is used to check against eric conventions."""
pyqtApi = 2
python2Compatible = True
# End-Of-Header


error = ""


class CodeStyleCheckerPlugin(QObject):
    """
    Class implementing the code style checker plug-in.
    
    @signal styleChecked(str, dict, int, list) emitted when the style check was
        done for a file.
    @signal batchFinished() emitted when a style check batch is done
    @signal error(str, str) emitted in case of an error
    """
    styleChecked = pyqtSignal(str, dict, int, list)
    batchFinished = pyqtSignal()
    error = pyqtSignal(str, str)
    
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        super(CodeStyleCheckerPlugin, self).__init__(ui)
        self.__ui = ui
        self.__initialize()
        
        self.backgroundService = e5App().getObject("BackgroundService")
        
        path = os.path.join(
            os.path.dirname(__file__), 'CheckerPlugins', 'CodeStyleChecker')
        self.backgroundService.serviceConnect(
            'style', 'Python2', path, 'CodeStyleChecker',
            self.__translateStyleCheck,
            onErrorCallback=self.serviceErrorPy2,
            onBatchDone=self.batchJobDone)
        self.backgroundService.serviceConnect(
            'style', 'Python3', path, 'CodeStyleChecker',
            self.__translateStyleCheck,
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
        if fx in ['style', 'batch_style'] and lang == 'Python2':
            if fx == 'style':
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
        if fx in ['style', 'batch_style'] and lang == 'Python3':
            if fx == 'style':
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
        if fx in ['style', 'batch_style']:
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
        self.__projectCodeStyleCheckerDialog = None
        
        self.__projectBrowserAct = None
        self.__projectBrowserMenu = None
        self.__projectBrowserCodeStyleCheckerDialog = None
        
        self.__editors = []
        self.__editorAct = None
        self.__editorCodeStyleCheckerDialog = None

    def styleCheck(self, lang, filename, source, args):
        """
        Public method to prepare a style check on one Python source file.

        @param lang language of the file or None to determine by internal
            algorithm (str or None)
        @param filename source filename (string)
        @param source string containing the code to check (string)
        @param args arguments used by the codeStyleCheck function (list of
            excludeMessages (str), includeMessages (str), repeatMessages
            (bool), fixCodes (str), noFixCodes (str), fixIssues (bool),
            maxLineLength (int), hangClosing (bool), docType (str), errors
            (list of str), eol (str), encoding (str))
        """
        if lang is None:
            lang = 'Python{0}'.format(determinePythonVersion(filename, source))
        if lang not in ['Python2', 'Python3']:
            return
        
        data = [source, args]
        self.backgroundService.enqueueRequest('style', lang, filename, data)
    
    def styleBatchCheck(self, argumentsList):
        """
        Public method to prepare a style check on multiple Python source files.
        
        @param argumentsList list of arguments tuples with each tuple
            containing filename, source and args as given in styleCheck()
            method
        """
        data = {
            "Python2": [],
            "Python3": [],
        }
        for filename, source, args in argumentsList:
            lang = 'Python{0}'.format(determinePythonVersion(filename, source))
            if lang not in ['Python2', 'Python3']:
                continue
            else:
                data[lang].append((filename, source, args))
        
        self.queuedBatches = []
        for lang in ['Python2', 'Python3']:
            if data[lang]:
                self.queuedBatches.append(lang)
                self.backgroundService.enqueueRequest('batch_style', lang, "",
                                                      data[lang])
                self.batchesFinished = False
    
    def cancelStyleBatchCheck(self):
        """
        Public method to cancel all batch jobs.
        """
        for lang in ['Python2', 'Python3']:
            self.backgroundService.requestCancel('batch_style', lang)
    
    def __translateStyleCheck(self, fn, codeStyleCheckerStats, results):
        """
        Private slot called after perfoming a style check on one file.
        
        @param fn filename of the just checked file (str)
        @param codeStyleCheckerStats stats of style and name check (dict)
        @param results tuple for each found violation of style (tuple of
            lineno (int), position (int), text (str), fixed (bool),
            autofixing (bool), fixedMsg (str))
        """
        from CheckerPlugins.CodeStyleChecker.translations import \
            getTranslatedMessage
        
        fixes = 0
        for result in results:
            msg = getTranslatedMessage(result[2])
        
            fixedMsg = result.pop()
            if fixedMsg:
                fixes += 1
                trFixedMsg = getTranslatedMessage(fixedMsg)
                
                msg += "\n" + QCoreApplication.translate(
                    'CodeStyleCheckerDialog', "Fix: {0}").format(trFixedMsg)
            
            result[2] = msg
        self.styleChecked.emit(fn, codeStyleCheckerStats, fixes, results)

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        menu = e5App().getObject("Project").getMenu("Checks")
        if menu:
            self.__projectAct = E5Action(
                self.tr('Check Code Style'),
                self.tr('&Code Style...'), 0, 0,
                self, 'project_check_pep8')
            self.__projectAct.setStatusTip(
                self.tr('Check code style.'))
            self.__projectAct.setWhatsThis(self.tr(
                """<b>Check Code Style...</b>"""
                """<p>This checks Python files for compliance to the"""
                """ code style conventions given in various PEPs.</p>"""
            ))
            self.__projectAct.triggered.connect(
                self.__projectCodeStyleCheck)
            e5App().getObject("Project").addE5Actions([self.__projectAct])
            menu.addAction(self.__projectAct)
        
        self.__editorAct = E5Action(
            self.tr('Check Code Style'),
            self.tr('&Code Style...'), 0, 0,
            self, "")
        self.__editorAct.setWhatsThis(self.tr(
            """<b>Check Code Style...</b>"""
            """<p>This checks Python files for compliance to the"""
            """ code style conventions given in various PEPs.</p>"""
        ))
        self.__editorAct.triggered.connect(self.__editorCodeStyleCheck)
        
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
        Private slot called, when the the project browser menu or a submenu is
        about to be shown.
        
        @param menuName name of the menu to be shown (string)
        @param menu reference to the menu (QMenu)
        """
        if menuName == "Checks" and \
           e5App().getObject("Project").getProjectLanguage() in \
                ["Python3", "Python2", "Python"]:
            self.__projectBrowserMenu = menu
            if self.__projectBrowserAct is None:
                self.__projectBrowserAct = E5Action(
                    self.tr('Check Code Style'),
                    self.tr('&Code Style...'), 0, 0,
                    self, "")
                self.__projectBrowserAct.setWhatsThis(self.tr(
                    """<b>Check Code Style...</b>"""
                    """<p>This checks Python files for compliance to the"""
                    """ code style conventions given in various PEPs.</p>"""
                ))
                self.__projectBrowserAct.triggered.connect(
                    self.__projectBrowserCodeStyleCheck)
            if self.__projectBrowserAct not in menu.actions():
                menu.addAction(self.__projectBrowserAct)
    
    def __projectCodeStyleCheck(self):
        """
        Private slot used to check the project files for code style.
        """
        project = e5App().getObject("Project")
        project.saveAllScripts()
        ppath = project.getProjectPath()
        files = [os.path.join(ppath, file)
                 for file in project.pdata["SOURCES"]
                 if file.endswith(
                     tuple(Preferences.getPython("Python3Extensions")) +
                     tuple(Preferences.getPython("PythonExtensions")))]
        
        from CheckerPlugins.CodeStyleChecker.CodeStyleCheckerDialog import \
            CodeStyleCheckerDialog
        self.__projectCodeStyleCheckerDialog = CodeStyleCheckerDialog(self)
        self.__projectCodeStyleCheckerDialog.show()
        self.__projectCodeStyleCheckerDialog.prepare(files, project)
    
    def __projectBrowserCodeStyleCheck(self):
        """
        Private method to handle the code style check context menu action of
        the project sources browser.
        """
        browser = e5App().getObject("ProjectBrowser")\
            .getProjectBrowser("sources")
        if browser.getSelectedItemsCount([ProjectBrowserFileItem]) > 1:
            fn = []
            for itm in browser.getSelectedItems([ProjectBrowserFileItem]):
                fn.append(itm.fileName())
            isDir = False
        else:
            itm = browser.model().item(browser.currentIndex())
            try:
                fn = itm.fileName()
                isDir = False
            except AttributeError:
                fn = itm.dirName()
                isDir = True
        
        from CheckerPlugins.CodeStyleChecker.CodeStyleCheckerDialog import \
            CodeStyleCheckerDialog
        self.__projectBrowserCodeStyleCheckerDialog = CodeStyleCheckerDialog(
            self)
        self.__projectBrowserCodeStyleCheckerDialog.show()
        if isDir:
            self.__projectBrowserCodeStyleCheckerDialog.start(
                fn, save=True)
        else:
            self.__projectBrowserCodeStyleCheckerDialog.start(
                fn, save=True, repeat=True)
    
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
    
    def __editorCodeStyleCheck(self):
        """
        Private slot to handle the code style check context menu action
        of the editors.
        """
        editor = e5App().getObject("ViewManager").activeWindow()
        if editor is not None:
            if editor.checkDirty() and editor.getFileName() is not None:
                from CheckerPlugins.CodeStyleChecker.CodeStyleCheckerDialog \
                    import CodeStyleCheckerDialog
                self.__editorCodeStyleCheckerDialog = CodeStyleCheckerDialog(
                    self)
                self.__editorCodeStyleCheckerDialog.show()
                self.__editorCodeStyleCheckerDialog.start(
                    editor.getFileName(),
                    save=True,
                    repeat=True)
