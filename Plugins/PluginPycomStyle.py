import os
import sys

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QFontDatabase, QFont, QColor
from PyQt5.Qsci import QsciScintilla
from Preferences.PreferencesLexer import PreferencesLexer
import Preferences

from PluginUpdate import calc_int_version
from PycomStyle.qdarkstyle import pyqt5_style_rc

import UI.Info


# Start-Of-Header
name = "Pycom Style"
author = "Pycom"
autoactivate = True
deactivateable = False
version = "1.0.0"
className = "PluginPycomStyle"
packageName = "PluginPycomStyle"
shortDescription = "Set UI themes"
longDescription = "This plugin sets colors, fonts and control sizes and shapes"

pyqtApi = 2
python2Compatible = True

class PluginPycomStyle(QObject):
    def __init__(self, ui):
        super(PluginPycomStyle, self).__init__(ui)
        self.__ui = ui
        self.__path = os.path.dirname(os.path.realpath(__file__))
        self.__loadFont()

        # first time settings initialization
        if not Preferences.isConfigured() or \
           Preferences.Prefs.settings.value("General/IniVersion", 0) <= \
             calc_int_version(UI.Info.Version) or \
           hasattr(ui, 'firstBoot'):
            ui.firstBoot = True
            self.__firstLoad()

    def activate(self):
        """
        Public method to activate this plugin.

        @return tuple of None and activation status (boolean)
        """
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        pass

    def __firstLoad(self):
        """
        Private method called if there are no settings.
        """
        self.__setupDefaultParameters()
        self.__loadPythonColors()

        self.__ui.setStyle(Preferences.getUI("Style"),
                           Preferences.getUI("StyleSheet"))

    def __loadFont(self):
        osFamily = sys.platform
        if osFamily == 'darwin':
            fontVariations = ["Thin", "ThinItalic"]
            self.__defaultFontSize = 14
        else:
            fontVariations = ["Light", "LightItalic"]
            self.__defaultFontSize = -1

        for variation in fontVariations:
            QFontDatabase.addApplicationFont(self.__path + \
              "/PycomStyle/Fonts/RobotoMono-" + variation + ".ttf")


    def __applyMonokaiPython(self, lexerName):
        defaultFont = QFont("Roboto Mono", self.__defaultFontSize, -1, False)
        colors = ["#ffffff", "#888877", "#ae81ff", "#ffff88",
                  "#ffff88", "#ff3377", "#ffff88", "#ffff88",
                  "#aaff33", "#aaff47", "#ff3377", "#ffffff",
                  "#888877", "#f8f8f0", "#ffe892", "#aa88ff"]

        lexer = PreferencesLexer(lexerName)

        for i in range(0, 15):
            lexer.setPaper(QColor(Qt.black), i)
            lexer.setFont(defaultFont, i)
            lexer.setColor(QColor(colors[i]), i)

        # specific values now
        # comment
        defaultFont.setItalic(True)
        lexer.setFont(defaultFont, 1)
        defaultFont.setItalic(False)

        # class name
        defaultFont.setUnderline(True)
        lexer.setFont(defaultFont, 8)

        # Unclosed string
        lexer.setPaper(QColor("#f92672"), 13)
        lexer.setEolFill(True, 13)


        lexer.writeSettings(Preferences.Prefs.settings, "Scintilla")

    def __loadPythonColors(self):
        self.__applyMonokaiPython("C++")
        self.__applyMonokaiPython("Python2")
        self.__applyMonokaiPython("Python3")

    def __setupDefaultParameters(self):
        defaultFont = QFont("Roboto Mono", self.__defaultFontSize, -1, False)

        editorOtherFontsDefaults = {
            "MarginsFont": defaultFont,
            "DefaultFont": defaultFont,
            "MonospacedFont": defaultFont}

        shellDefaults = {
            "UseMonospacedFont": True,
            "MonospacedFont": defaultFont,
            "MarginsFont": defaultFont}

        editorDefaults = {
            "FoldingStyle": 7, # arrow tree
            "ShowWhitespace": True,
            "UseMonospacedFont": True,
            "OverrideEditAreaColours": True,
            "CustomSelectionColours": True,
            "EdgeMode": QsciScintilla.EdgeLine,
            "EdgeColumn": 80,
            "CaretLineVisible": True,
            "ColourizeSelText": True,
            "AutoCompletionEnabled": True,
            "AutoCompletionCaseSensitivity": False,
            "AutoCompletionReplaceWord": True,
            "AutoCompletionThreshold": 1,
            "AutoCompletionFillups": True,
            "AutoCompletionScintillaOnFail": True,
            "CallTipsEnabled": True,
            "CallTipsVisible": 0,
            "OnlineSyntaxCheckInterval": 0,
            "MiniContextMenu": True,
            "AnnotationsEnabled": False}

        editorColorsDefaults = {
            "MatchingBrace": QColor(Qt.green),
            "MatchingBraceBack": QColor(Qt.darkGray),
            "CallTipsBackground": QColor(Qt.lightGray),
            "NonmatchingBrace": QColor(Qt.red),
            "NonmatchingBraceBack": QColor(Qt.darkGray),
            "SelectionBackground": QColor("#49483E"),
            "SelectionForeground": QColor(Qt.white),
            "SearchMarkers": QColor("#FFE792"),
            "CaretForeground": QColor(Qt.white),
            "CaretLineBackground": QColor("#202020"),
            "WhitespaceForeground": QColor(Qt.black),
            "WhitespaceBackground": QColor(Qt.black),
            "IndentationGuidesBackground": QColor(Qt.black),
            "IndentationGuidesForeground": QColor("#303030"),
            "OnlineChangeTraceMarkerUnsaved": QColor("#FF3377"),
            "OnlineChangeTraceMarkerSaved": QColor("#AAFF33"),
            "EditAreaBackground": QColor(Qt.black),
            "MarginsForeground": QColor("#808080"),
            "MarginsBackground": QColor("#202020"),
            "FoldMarkersForeground": QColor("#808080"),
            "FoldMarkersBackground": QColor(Qt.black),
            "FoldmarginBackground": QColor(Qt.black),
            "MarkerMapBackground": QColor("#202020"),
            "CurrentMap": QColor(Qt.white),
            "Edge": QColor("#303030")}


        for n, value in editorOtherFontsDefaults.iteritems():
            Preferences.setEditorOtherFonts(n, value)

        for n, value in shellDefaults.iteritems():
            Preferences.setShell(n, value)

        for n, value in editorDefaults.iteritems():
            Preferences.setEditor(n, value)

        for n, value in editorColorsDefaults.iteritems():
            Preferences.setEditorColour(n, value)

        Preferences.setUI("StyleSheet", \
            self.__path + "/PycomStyle/qdarkstyle/style.qss")

        self.__ui.setStyle(Preferences.getUI("Style"), Preferences.getUI("StyleSheet"))
