# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module documentation goes here.
"""

from __future__ import unicode_literals

import os
import sys

from PyQt5.QtCore import Qt, QObject, QCoreApplication, QTimer, QTranslator

from E5Gui.E5Application import e5App

import Preferences

# Start-Of-Header
name = "Jedi Code Completion Plug-in"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = True
deactivateable = True
version = "1.0.2"
className = "CompletionJediPlugin"
packageName = "CompletionJedi"
shortDescription = "Provide completions and calltips using Jedi"
longDescription = (
    """This plug-in provides code completions and calltips"""
    """ using the Jedi package."""
)
needsRestart = False
pyqtApi = 2
python2Compatible = True
# End-Of-Header

error = ""

sys.path.insert(0, os.path.join(os.path.dirname(__file__), packageName))

completionJediPluginObject = None


def createAutoCompletionPage(configDlg):
    """
    Module function to create the autocompletion configuration page.
    
    @param configDlg reference to the configuration dialog
    @return reference to the configuration page
    """
    global completionJediPluginObject
    from CompletionJedi.ConfigurationPage.AutoCompletionJediPage \
        import AutoCompletionJediPage
    page = AutoCompletionJediPage(completionJediPluginObject)
    return page


def createCallTipsPage(configDlg):
    """
    Module function to create the calltips configuration page.
    
    @param configDlg reference to the configuration dialog
    @return reference to the configuration page
    """
    global completionJediPluginObject
    from CompletionJedi.ConfigurationPage.CallTipsJediPage \
        import CallTipsJediPage
    page = CallTipsJediPage(completionJediPluginObject)
    return page


def createMouseClickHandlerPage(configDlg):
    """
    Module function to create the mouse click handler configuration page.
    
    @param configDlg reference to the configuration dialog
    @return reference to the configuration page
    """
    global completionJediPluginObject
    from CompletionJedi.ConfigurationPage.MouseClickHandlerJediPage \
        import MouseClickHandlerJediPage
    page = MouseClickHandlerJediPage(completionJediPluginObject)
    return page


def getConfigData():
    """
    Module function returning data as required by the configuration dialog.
    
    @return dictionary containing the relevant data
    """
    data = {
        "jediAutoCompletionPage": [
            QCoreApplication.translate("CompletionJediPlugin", "Jedi"),
            os.path.join("CompletionJedi", "ConfigurationPage",
                         "preferences-jedi.png"),
            createAutoCompletionPage, "editorAutocompletionPage", None],
        "jediCallTipsPage": [
            QCoreApplication.translate("CompletionJediPlugin", "Jedi"),
            os.path.join("CompletionJedi", "ConfigurationPage",
                         "preferences-jedi.png"),
            createCallTipsPage, "editorCalltipsPage", None],
    }
    
    if e5App().getObject("UserInterface").versionIsNewer("6.0.99", "20150627"):
        data["jediMouseClickHandlerPage"] = [
            QCoreApplication.translate("CompletionJediPlugin", "Jedi"),
            os.path.join("CompletionJedi", "ConfigurationPage",
                         "preferences-jedi.png"),
            createMouseClickHandlerPage, "1editorMouseClickHandlers", None]
    
    return data


def prepareUninstall():
    """
    Module function to prepare for an uninstallation.
    """
    Preferences.Prefs.settings.remove(CompletionJediPlugin.PreferencesKey)


def exeDisplayData():
    """
    Module function to support the display of some executable info.
    
    @return dictionary containing the data to query the presence of
        the executable
    """
    try:
        from CompletionJedi import jedi
        version = jedi.__version__
    except AttributeError:
        version = QCoreApplication.translate(
            "CompletionJediPlugin", "(unknown)")
    data = {
        "programEntry": "",                     # marker for simplified info
        "header": QCoreApplication.translate(
            "CompletionJediPlugin",
            "Code Completion - Jedi"),
        "text": os.path.join(os.path.dirname(__file__), packageName, "jedi"),
        "version": version,
    }
    
    return data


class CompletionJediPlugin(QObject):
    """
    Class documentation goes here.
    """
    PreferencesKey = "CompletionJedi"
    
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        super(CompletionJediPlugin, self).__init__(ui)
        self.__ui = ui
        self.__initialize()
        
        self.__defaults = {
            "JediCompletionsEnabled": False,
            "JediCompletionsTimeout": 100,
            "ShowQScintillaCompletions": True,
            
            "JediCalltipsEnabled": False,
            
            "MouseClickEnabled": True,
            "MouseClickGotoModifiers": int(
                Qt.ControlModifier | Qt.AltModifier),
            "MouseClickGotoButton": int(Qt.LeftButton),
        }
        
        self.__translator = None
        self.__loadTranslator()
        
        self.__acTimer = QTimer(self)
        self.__acTimer.setSingleShot(True)
        self.__acTimer.setInterval(
            self.getPreferences("JediCompletionsTimeout"))
        self.__acTimer.timeout.connect(self.__jediCompletions)
    
    def __initialize(self):
        """
        Private slot to (re)initialize the plug-in.
        """
        self.__jediObject = None
        self.__editors = []
    
    def activate(self):
        """
        Public method to activate this plug-in.
        
        @return tuple of None and activation status (boolean)
        """
        global error
        error = ""     # clear previous error
        
        global completionJediPluginObject
        completionJediPluginObject = self
        
        from CompletionJedi.JediCompleter import JediCompleter
        self.__jediObject = JediCompleter(self, self)
        
        e5App().getObject("ViewManager").editorOpenedEd.connect(
            self.__editorOpened)
        e5App().getObject("ViewManager").editorClosedEd.connect(
            self.__editorClosed)
        
        for editor in e5App().getObject("ViewManager").getOpenEditors():
            self.__editorOpened(editor)
        
        return None, True
    
    def deactivate(self):
        """
        Public method to deactivate this plug-in.
        """
        e5App().getObject("ViewManager").editorOpenedEd.disconnect(
            self.__editorOpened)
        e5App().getObject("ViewManager").editorClosedEd.disconnect(
            self.__editorClosed)
        
        for editor in self.__editors[:]:
            self.__editorClosed(editor)
        
        self.__initialize()
    
    def __loadTranslator(self):
        """
        Private method to load the translation file.
        """
        if self.__ui is not None:
            loc = self.__ui.getLocale()
            if loc and loc != "C":
                locale_dir = \
                    os.path.join(os.path.dirname(__file__),
                                 "CompletionJedi", "i18n")
                translation = "jedi_%s" % loc
                translator = QTranslator(None)
                loaded = translator.load(translation, locale_dir)
                if loaded:
                    self.__translator = translator
                    e5App().installTranslator(self.__translator)
                else:
                    print("Warning: translation file '{0}' could not"
                          " be loaded.".format(translation))
                    print("Using default.")
    
    def getPreferences(self, key):
        """
        Public method to retrieve the various refactoring settings.
        
        @param key the key of the value to get
        @return the requested refactoring setting
        """
        if key in ["JediCompletionsEnabled", "JediCalltipsEnabled",
                   "ShowQScintillaCompletions", "MouseClickEnabled"]:
            return Preferences.toBool(Preferences.Prefs.settings.value(
                self.PreferencesKey + "/" + key, self.__defaults[key]))
        else:
            return int(Preferences.Prefs.settings.value(
                self.PreferencesKey + "/" + key, self.__defaults[key]))
    
    def setPreferences(self, key, value):
        """
        Public method to store the various refactoring settings.
        
        @param key the key of the setting to be set (string)
        @param value the value to be set
        """
        Preferences.Prefs.settings.setValue(
            self.PreferencesKey + "/" + key, value)
        
        if key in ["JediCompletionsEnabled", "JediCalltipsEnabled",
                   "MouseClickEnabled"]:
            if value:
                if e5App().getObject("Project").isOpen():
                    for editor in e5App().getObject("ViewManager")\
                            .getOpenEditors():
                        if editor not in self.__editors:
                            self.__editorOpened(editor)
            else:
                for editor in self.__editors[:]:
                    self.__editorClosed(editor)
        elif key in ["MouseClickGotoModifiers", "MouseClickGotoButton"]:
            for editor in self.__editors:
                self.__disconnectMouseClickHandler(editor)
                self.__connectMouseClickHandler(editor)
        elif key == "JediCompletionsTimeout":
            self.__acTimer.setInterval(value)
    
    def __determineLanguage(self):
        """
        Private method to determine the valid language strings.
        
        @return list of valid language strings (list of string)
        """
        if sys.version_info[0] == 3:
            lang = ["Python3", "Pygments|Python 3"]
        elif sys.version_info[0] == 2:
            lang = ["Python", "Python2", "Pygments|Python"]
        else:
            lang = []
        
        return lang
    
    def __editorOpened(self, editor):
        """
        Private slot called, when a new editor was opened.
        
        @param editor reference to the new editor (QScintilla.Editor)
        """
        lang = self.__determineLanguage()
        
        if editor.getLanguage() in lang:
            self.__connectEditor(editor)
        
        editor.languageChanged.connect(self.__editorLanguageChanged)
        self.__editors.append(editor)
    
    def __editorClosed(self, editor):
        """
        Private slot called, when an editor was closed.
        
        @param editor reference to the editor (QScintilla.Editor)
        """
        if editor in self.__editors:
            editor.languageChanged.disconnect(self.__editorLanguageChanged)
            self.__disconnectEditor(editor)
            self.__editors.remove(editor)
    
    def __editorLanguageChanged(self, language):
        """
        Private slot to handle the language change of an editor.
        
        @param language programming language of the editor (string)
        """
        editor = self.sender()
        lang = self.__determineLanguage()
        
        if language in lang:
            try:
                if editor.getCompletionListHook("jedi") is None or \
                        editor.getCallTipHook("jedi") is None:
                    self.__connectEditor(editor)
            except AttributeError:
                # old interface (before 6.1.0)
                if editor.autoCompletionHook() != self.jediCompletions or \
                        editor.callTipHook() != self.jediCallTip:
                    self.__connectEditor(editor)
        else:
            self.__disconnectEditor(editor)
    
    def __connectEditor(self, editor):
        """
        Private method to connect an editor.
        
        @param editor reference to the editor (QScintilla.Editor)
        """
        if self.getPreferences("JediCompletionsEnabled"):
            self.__setAutoCompletionHook(editor)
        if self.getPreferences("JediCalltipsEnabled"):
            self.__setCalltipsHook(editor)
        
        if self.getPreferences("MouseClickEnabled"):
            self.__disconnectMouseClickHandler(editor)
            self.__connectMouseClickHandler(editor)
    
    def __connectMouseClickHandler(self, editor):
        """
        Private method to connect the mouse click handler to an editor.
        
        @param editor reference to the editor (QScintilla.Editor)
        """
        if self.getPreferences("MouseClickGotoButton"):
            try:
                editor.setMouseClickHandler(
                    "jedi",
                    self.getPreferences("MouseClickGotoModifiers"),
                    self.getPreferences("MouseClickGotoButton"),
                    self.__jediObject.gotoDefinition
                )
            except AttributeError:
                # eric versions before 6.1.0 don't support this
                pass
    
    def __disconnectEditor(self, editor):
        """
        Private method to disconnect an editor.
        
        @param editor reference to the editor (QScintilla.Editor)
        """
        try:
            if editor.getCompletionListHook("jedi"):
                self.__unsetAutoCompletionHook(editor)
        except AttributeError:
            # old interface (before 6.1.0)
            if editor.autoCompletionHook() == self.jediCompletions:
                self.__unsetAutoCompletionHook(editor)
        try:
            if editor.getCallTipHook("jedi"):
                self.__unsetCalltipsHook(editor)
        except AttributeError:
            # old interface (before 6.1.0)
            if editor.callTipHook() == self.jediCallTip:
                self.__unsetCalltipsHook(editor)
        
        self.__disconnectMouseClickHandler(editor)
    
    def __disconnectMouseClickHandler(self, editor):
        """
        Private method to disconnect the mouse click handler from an editor.
        
        @param editor reference to the editor (QScintilla.Editor)
        """
        try:
            editor.removeMouseClickHandlers("jedi")
        except AttributeError:
            # eric versions before 6.1.0 don't support this
            pass
    
    def __completionListSelected(self, id, txt):
        """
        Private slot to handle the selection from the completion list.
        
        @param id the ID of the user list (should be 1) (integer)
        @param txt the selected text (QString)
        """
        from QScintilla.Editor import EditorAutoCompletionListID
        
        editor = self.sender()
        if id == EditorAutoCompletionListID:
            lst = txt.split()
            if len(lst) > 1:
                txt = lst[0]
            
            if Preferences.getEditor("AutoCompletionReplaceWord"):
                editor.selectCurrentWord()
                editor.removeSelectedText()
                line, col = editor.getCursorPosition()
            else:
                line, col = editor.getCursorPosition()
                wLeft = editor.getWordLeft(line, col)
                if not txt.startswith(wLeft):
                    editor.selectCurrentWord()
                    editor.removeSelectedText()
                    line, col = editor.getCursorPosition()
                elif wLeft:
                    txt = txt[len(wLeft):]
            editor.insert(txt)
            editor.setCursorPosition(line, col + len(txt))
    
    def __setAutoCompletionHook(self, editor):
        """
        Private method to set the autocompletion hook.
        
        @param editor reference to the editor (QScintilla.Editor)
        """
        try:
            editor.addCompletionListHook("jedi", self.getCompletionsList)
        except AttributeError:
            # old interface (before 6.1.0)
            editor.userListActivated.connect(self.__completionListSelected)
            editor.setAutoCompletionHook(self.jediCompletions)
    
    def __unsetAutoCompletionHook(self, editor):
        """
        Private method to unset the autocompletion hook.
        
        @param editor reference to the editor (QScintilla.Editor)
        """
        try:
            editor.removeCompletionListHook("jedi")
        except AttributeError:
            # old interface (before 6.1.0)
            editor.unsetAutoCompletionHook()
            editor.userListActivated.disconnect(self.__completionListSelected)
    
    def jediCompletions(self, editor, context=False):
        """
        Public method to determine the autocompletion proposals.
        
        @param editor reference to the editor object, that called this method
            QScintilla.Editor)
        @param context flag indicating to autocomplete a context (boolean)
        """
        self.__currentEditor = editor
        if self.getPreferences("JediCompletionsTimeout"):
            self.__acTimer.stop()
            self.__acTimer.start()
        else:
            self.__jediCompletions()
    
    def __jediCompletions(self):
        """
        Private slot to show a list with completion proposals.
        """
        from QScintilla.Editor import EditorAutoCompletionListID
        
        if self.__currentEditor is not None:
            if self.__currentEditor.isListActive():
                self.__currentEditor.cancelList()
            completions = self.getCompletionsList(self.__currentEditor, False)
            if len(completions) == 0 and \
                    self.getPreferences("ShowQScintillaCompletions"):
                # try QScintilla autocompletion
                self.__currentEditor.autoCompleteQScintilla()
            else:
                completions.sort()
                self.__currentEditor.showUserList(EditorAutoCompletionListID,
                                                  completions)
    
    def getCompletionsList(self, editor, context):
        """
        Public method to get a list of possible completions.
        
        @param editor reference to the editor object, that called this method
            (QScintilla.Editor)
        @param context flag indicating to autocomplete a context (boolean)
        @return list of possible completions (list of strings)
        """
        completions = self.__jediObject.getCompletions(editor)
        return completions
    
    def __setCalltipsHook(self, editor):
        """
        Private method to set the calltip hook.
        
        @param editor reference to the editor (QScintilla.Editor)
        """
        try:
            editor.addCallTipHook("jedi", self.jediCallTip)
        except AttributeError:
            # old interface (before 6.1.0)
            editor.setCallTipHook(self.jediCallTip)
    
    def __unsetCalltipsHook(self, editor):
        """
        Private method to unset the calltip hook.
        
        @param editor reference to the editor (QScintilla.Editor)
        """
        try:
            editor.removeCallTipHook("jedi")
        except AttributeError:
            # old interface (before 6.1.0)
            editor.unsetCallTipHook()
    
    def jediCallTip(self, editor, pos, commas):
        """
        Public method to return a list of calltips.
        
        @param editor reference to the editor (QScintilla.Editor)
        @param pos position in the text for the calltip (integer)
        @param commas minimum number of commas contained in the calltip
            (integer)
        @return list of possible calltips (list of strings)
        """
        cts = self.__jediObject.getCallTips(pos, editor)
        return cts
