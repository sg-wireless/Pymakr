# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the QFontDialog wizard plugin.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QDialog

from E5Gui.E5Application import e5App
from E5Gui.E5Action import E5Action
from E5Gui import E5MessageBox

# Start-Of-Header
name = "QFontDialog Wizard Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = True
deactivateable = True
version = "6.1.0"
className = "FontDialogWizard"
packageName = "__core__"
shortDescription = "Show the QFontDialog wizard."
longDescription = """This plugin shows the QFontDialog wizard."""
pyqtApi = 2
python2Compatible = True
# End-Of-Header

error = ""


class FontDialogWizard(QObject):
    """
    Class implementing the QFontDialog wizard plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        super(FontDialogWizard, self).__init__(ui)
        self.__ui = ui

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        self.__initAction()
        self.__initMenu()
        
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        menu = self.__ui.getMenu("wizards")
        if menu:
            menu.removeAction(self.action)
        self.__ui.removeE5Actions([self.action], 'wizards')
    
    def __initAction(self):
        """
        Private method to initialize the action.
        """
        self.action = E5Action(
            self.tr('QFontDialog Wizard'),
            self.tr('Q&FontDialog Wizard...'), 0, 0, self,
            'wizards_qfontdialog')
        self.action.setStatusTip(self.tr('QFontDialog Wizard'))
        self.action.setWhatsThis(self.tr(
            """<b>QFontDialog Wizard</b>"""
            """<p>This wizard opens a dialog for entering all the parameters"""
            """ needed to create a QFontDialog. The generated code is"""
            """ inserted at the current cursor position.</p>"""
        ))
        self.action.triggered.connect(self.__handle)
        
        self.__ui.addE5Actions([self.action], 'wizards')

    def __initMenu(self):
        """
        Private method to add the actions to the right menu.
        """
        menu = self.__ui.getMenu("wizards")
        if menu:
            menu.addAction(self.action)
    
    def __callForm(self, editor):
        """
        Private method to display a dialog and get the code.
        
        @param editor reference to the current editor
        @return the generated code (string)
        """
        from WizardPlugins.FontDialogWizard.FontDialogWizardDialog import \
            FontDialogWizardDialog
        dlg = FontDialogWizardDialog(None)
        if dlg.exec_() == QDialog.Accepted:
            line, index = editor.getCursorPosition()
            indLevel = editor.indentation(line) // editor.indentationWidth()
            if editor.indentationsUseTabs():
                indString = '\t'
            else:
                indString = editor.indentationWidth() * ' '
            return (dlg.getCode(indLevel, indString), True)
        else:
            return (None, False)
        
    def __handle(self):
        """
        Private method to handle the wizards action.
        """
        editor = e5App().getObject("ViewManager").activeWindow()
        
        if editor is None:
            E5MessageBox.critical(
                self.__ui,
                self.tr('No current editor'),
                self.tr('Please open or create a file first.'))
        else:
            code, ok = self.__callForm(editor)
            if ok:
                line, index = editor.getCursorPosition()
                # It should be done on this way to allow undo
                editor.beginUndoAction()
                editor.insertAt(code, line, index)
                editor.endUndoAction()
