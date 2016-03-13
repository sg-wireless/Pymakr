# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the autocompletion interface to jedi.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject

from QScintilla.Editor import Editor

from E5Gui.E5Application import e5App

import jedi


class JediCompleter(QObject):
    """
    Class implementing the autocompletion interface to jedi.
    """
    PictureIDs = {
        "class": "?{0}".format(Editor.ClassID),
        "instance": "?{0}".format(Editor.ClassID),
        "function": "?{0}".format(Editor.MethodID),
        "module": "?{0}".format(Editor.AttributeID),
        "param": "?{0}".format(Editor.AttributeID),
        "statement": "?{0}".format(Editor.AttributeID),
        "import": "",
        "None": "",
    }
    
    def __init__(self, plugin, parent=None):
        """
        Constructor
        
        @param plugin reference to the plugin object
        @param parent parent (QObject)
        """
        QObject.__init__(self, parent)
    
    def getCompletions(self, editor):
        """
        Public method to calculate the possible completions.
        
        @param editor reference to the editor object, that called this method
            QScintilla.Editor)
        @return list of proposals (QStringList)
        """
        filename = editor.getFileName()
        line, index = editor.getCursorPosition()
        line += 1       # jedi line numbers are 1 based
        source = editor.text()
        try:
            script = jedi.Script(source, line, index, filename)
            completions = script.completions()
            names = []
            for completion in completions:
                context = completion.full_name
                if context.endswith(".{0}".format(completion.name)):
                    context = context.rsplit(".", 1)[0]
                if context:
                    name = "{0} ({1})".format(completion.name, context)
                else:
                    name = completion.name
                if completion.type in self.PictureIDs and \
                        self.PictureIDs[completion.type] != "":
                    name += self.PictureIDs[completion.type]
                names.append(name)
            return names
        except Exception:
            return []
    
    def getCallTips(self, pos, editor):
        """
        Public method to calculate calltips.
        
        @param pos position in the text for the calltip (integer)
        @param editor reference to the editor object, that called this method
            QScintilla.Editor)
        @return list of possible calltips (list of strings)
        """
        filename = editor.getFileName()
        source = editor.text()
        cts = []
        try:
            line, index = editor.lineIndexFromPosition(pos)
            line += 1       # jedi line numbers are 1 based
            index += 1      # move beyond (
            script = jedi.Script(source, line, index, filename)
            signatures = script.call_signatures()
            if signatures is not None:
                for signature in signatures:
                    name = signature.name
                    sig = ", ".join([
                        param.description for param in signature.params])
                    cts.append("{0}({1})".format(name, sig))
        except Exception:
            pass
        return cts
    
    
    def gotoDefinition(self, editor):
        """
        Public slot to find the definition for the word at the cursor position
        and go to it.
        
        Note: This is executed upon a mouse click sequence.
        
        @param editor reference to the calling editor (Editor)
        """
        filename = editor.getFileName()
        line, index = editor.getCursorPosition()
        line += 1       # jedi line numbers are 1 based
        source = editor.text()
        definitions = []
        try:
            script = jedi.Script(source, line, index, filename)
            definitions = script.goto_assignments()
        except Exception:
            pass
        
        if definitions and definitions[0].module_path is not None:
            if definitions[0].line is None:
                line = 0
            else:
                line = definitions[0].line
            e5App().getObject("ViewManager").openSourceFile(
                definitions[0].module_path, line, next=True)
        else:
            e5App().getObject("UserInterface").statusBar().showMessage(
                self.tr('No definition found'), 5000)
