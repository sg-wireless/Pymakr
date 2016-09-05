from PyQt5.QtCore import QObject


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
    def __init__(self,  ui):
        super(PluginPycomStyle, self).__init__(ui)
        self.__loadFont()

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
            QFontDatabase.addApplicationFont(self.__path + 
                "/FullUI/Fonts/RobotoMono-" + variation + ".ttf")


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
