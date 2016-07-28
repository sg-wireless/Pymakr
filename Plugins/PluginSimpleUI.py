import os

from PyQt5.QtCore import QResource
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QSize
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtCore import QDir

from Project.Project import Project

from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QFont
from E5Gui.E5Application import e5App
from E5Gui.E5Action import E5Action
from PyQt5.Qsci import QsciScintilla
from PyQt5.QtGui import QFrame

from QScintilla import Lexers

from SimpleUI.qdarkstyle import pyqt5_style_rc

import Preferences
from Preferences.PreferencesLexer import PreferencesLexer

import UI.Info

# Start-Of-Header
name = "Simple UI"
author = "Pycom"
autoactivate = True
deactivateable = False
version = "1.0.0"
className = "PluginSimpleUI"
packageName = "PluginSimpleUI"
shortDescription = "This plugin simplifies the user interface so it gets easy to use for beginners"
longDescription = "Full GUI can be intimidating for casual users. " \
    "This plugin attempts to make it more friendly, giving option to enable advanced functionality later"

pyqtApi = 2
python2Compatible = True

class PluginSimpleUI(QObject):
    def __init__(self,  ui):
        super(PluginSimpleUI, self).__init__(ui)

        self.__ui = ui
        self.__path = os.path.dirname(os.path.realpath(__file__))
        self.__toolbars = e5App().getObject("ToolbarManager")

        self.__oldShowEvent = self.__ui.showEvent
        self.__ui.showEvent = self.__windowLoaded
        self.__ui.showPreferences = self.__showPreferences

        Lexers.getSupportedLanguages = self.__getSupportedLanguages
        Project.getProgrammingLanguages = self.__getProgrammingLanguages

        self.__loadFont()

        if not Preferences.isConfigured():
            self.__firstLoad()

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        self.__setupMenu()
        self.__setupProjectBrowser()
        self.__customizeProjecTypeList()
        self.__hideExtras()

        self.__viewAddSplit = e5App().getObject("ViewManager").addSplit
        e5App().getObject("ViewManager").addSplit = self.__addSplit
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
        self.__enableAdvancedCompletion()

        self.__ui.setStyle(Preferences.getUI("Style"),
                      Preferences.getUI("StyleSheet"))

        self.__hideToolbars()

        Preferences.Prefs.settings.setValue("General/Configured", True)

    def __loadFont(self):
        fontVariations = ["", "-Oblique"]

        for variation in fontVariations:
            QFontDatabase.addApplicationFont(self.__path + 
                "/SimpleUI/Fonts/DejaVuSansMono" + variation + ".ttf")

    def __windowLoaded(self, event):
        """
        Private method that gets called when the main window gets visible.
        """
        e5App().getObject("ViewManager").editorOpenedEd.connect(self.__on_new_editor)
        self.__oldShowEvent(event)
        self.__setupToolbars()
        self.__setupSidebars()
        self.__disableExtraPlugins()

        # I must run only once
        self.__ui.showEvent = self.__oldShowEvent

    def __removeWidgetActions(self, widget, items):
        """
        Private method that removes widget items.

        @param widget QWidget to modify
        @param items list of names of the elements to remove
        """
        for i, item in enumerate(items):
            items[i] = self.tr(item)

        for item in widget.actions():
            if item.text() in items:
                widget.removeAction(item)

    def __hideWidgetActions(self, widget, items):
        """
        Private method that hides widget items.

        @param widget QWidget to modify
        @param items list of names of the elements to hide
        """
        for i, item in enumerate(items):
            items[i] = self.tr(item)

        for item in widget.actions():
            if item.text() in items:
                item.setVisible(False)


    def __hideWidgetSeparator(self, widget, items,mode="after"):
        """
        Private method that hides the separator before/after some
        widget items.

        @param widget QWidget to modify
        @param items list of names of the elements right before the separators
        @param where is the separator located
        """
        for i, item in enumerate(items):
            items[i] = self.tr(item)

        toHide = False
        for item in widget.actions():
            if mode == "after":
                if item.text() == "" and toHide == True:
                    item.setVisible(False)
                    continue

                if item.text() in items:
                    toHide = True
                else:
                    toHide = False
            else:
                if item.text() == "":
                    prevSeparator = item
                elif item.text() in items and prevSeparator != None:
                    prevSeparator.setVisible(False)
                else:
                    prevSeparator = None


    def __setupMenu(self):
        """
        Private method that hides pro-level menus and makes the others
        non-detachable.
        """
        # hide unused menus
        for menu in ["debug", "start", "unittest", "multiproject"]:
            self.__ui.getMenuBarAction(menu).setVisible(False)

        # make menus non-detachable
        for menu in ["file", "edit", "view", "project", "extras",
                    "settings", "window", "bookmarks", "plugins", 
                    "help", "subwindow", "toolbars", "wizards",
                    "macros"]:
            self.__ui.getMenu(menu).setTearOffEnabled(False)

        toRemove = {
            "edit":      ["Clear",
                          "C&omment",
                          "Unco&mment",
                          "Stream Comment",
                          "Box Comment"],
            "view":      ["Zoom &in",
                          "Zoom &out",
                          "Zoom &reset",
                          "&Zoom",
                          "Preview"],
            "project":   ["Debugger", "&Version Control"],
            "extras":    ["&Builtin Tools"],
            "settings":  ["Manage SSL Certificates...",
                          "Reload &APIs",
                          "&View Profiles...",
                          "Edit Message Filters..."],
            "subwindow": ["&Multiproject-Viewer",
                          "Templ&ate-Viewer",
                          "S&ymbols-Viewer",
                          "&Debug-Viewer",
                          "Co&operation-Viewer",
                          "&IRC"],
            "help":       ["&Helpviewer...",
                           "&Eric API Documentation",
                           "&Pymakr API Documentation",
                           "Python &3 Documentation",
                           "Python &2 Documentation",
                           "Qt&4 Documentation",
                           "Qt&5 Documentation",
                           "PyQt&4 Documentation",
                           "PyQt&5 Documentation",
                           "&About Pymakr",
                           "About &Qt"]
        }

        toHide = {
            "window":    ["&Right Sidebar",
                          "Edit Profile",
                          "Debug Profile"],
        }

        for menu, items in toRemove.iteritems():
            self.__removeWidgetActions(self.__ui.getMenu(menu), items)

        for menu, items in toHide.iteritems():
            self.__hideWidgetActions(self.__ui.getMenu(menu), items)

        for item in self.__ui.getMenu("settings").actions():
            if item.text() == self.tr("&Preferences..."):
                item.triggered.disconnect()
                item.triggered.connect(self.__showPreferences)


    def __setupToolbars(self):
        """
        Private method that hides the pro-level toolbars
        """
        for toolbar in ["vcs", "start", "debug", "multiproject", "help",
                        "unittest", "tools", "settings", "view_profiles",
                        "subversion", "pysvn", "mercurial", "plugins",
                        "view"]:
            self.__ui.getToolbar(toolbar)[1].hide()
            self.__ui.unregisterToolbar(toolbar)

        toRemove = {
            "file": ["New &Window", "&Close", "Save &Copy...", "&Quit"],
            "edit": ["Clear", "C&omment", "Unco&mment"]
        }
        for toolbar, items in toRemove.iteritems():
            self.__removeWidgetActions(self.__ui.getToolbar(toolbar)[1], items)

        separatorsToHide = {
            "file":     ["&New"]
        }

        for toolbar, items in separatorsToHide.iteritems():
            self.__hideWidgetSeparator(self.__ui.getToolbar(toolbar)[1],
                items, "before")

        separatorsToHide = {
            "file":     ["New &Window", "&Open...", "&Close", "Save a&ll"],
            "edit":     ["&Redo", "Clear", "&Paste"],
            "project":  ["&Close"]
        }
        for toolbar, items in separatorsToHide.iteritems():
            self.__hideWidgetSeparator(self.__ui.getToolbar(toolbar)[1], items)

        toResize = ["file", "edit", "project", "bookmarks",
                    "quicksearch", "search", "spelling"]
        for toolbar in toResize:
            self.__ui.getToolbar(toolbar)[1].setIconSize(QSize(32, 32))

    def __hideToolbars(self):
        for toolbar in ["bookmarks"]:
            self.__ui.getToolbar(toolbar)[1].hide()

    def __setupSidebars(self):
        """
        Private method that hides the pro-level sidebars
        """
        toHideLeft = [self.tr("Multiproject-Viewer"),
                        self.tr("Template-Viewer"),
                        self.tr("Symbols")]
        toHideBottom = [self.tr("Task-Viewer"),
                        self.tr("Numbers")]
        self.__ui.rightSidebar.hide()
        self.__ui.rightSidebar.clear()

        for i in xrange(self.__ui.leftSidebar.count() - 1, 0, -1):
            if self.__ui.leftSidebar.tabText(i) in toHideLeft:
                self.__ui.leftSidebar.removeTab(i)
        
        self.__ui.leftSidebar.setMaximumWidth(300)
        self.__ui.bottomSidebar.setMaximumHeight(200)

        for i in xrange(self.__ui.bottomSidebar.count() - 1, 0, -1):
            if self.__ui.bottomSidebar.tabText(i) in toHideBottom:
                self.__ui.bottomSidebar.removeTab(i)

    def __setupProjectBrowser(self):
        """
        Private method that hides the project browser tabs
        """
        browser = e5App().getObject("ProjectBrowser")
        browser.setCurrentIndex(0)
        browser.setStyleSheet("QTabWidget::pane { border: 0; }")
        browser.getProjectBrowser("sources").hideColumn(1)
        browser.tabBar().hide()

    def __setupDefaultParameters(self):
        defaultFont = QFont("DejaVu Sans Mono", 11, -1, False)

        uiDefaults = {
            "SidebarDelay": 500,
            "TabViewManagerFilenameLength": 25,
            "PerformVersionCheck": 3, # weekly
            }

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
            "AnnotationsEnabled": False,
            }

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
                "CaretLineBackground": QColor("#3E3D32"),
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
                "Edge": QColor("#303030"),
                }

        editorOtherFontsDefaults = {
                "MarginsFont": defaultFont,
                "DefaultFont": defaultFont,
                "MonospacedFont": defaultFont,
                }

        shellDefaults = {
                "UseMonospacedFont": True,
                "MonospacedFont": defaultFont,
                "MarginsFont": defaultFont,
                }

        helpDefaults = {
                "HelpViewerType": 3,
                }


        # fill the workspace with a right Value
        multiProjectDefaults={}
        multiProjectDefaults["Workspace"] = QDir.tempPath() 

        for name, value in uiDefaults.iteritems():
            Preferences.setUI(name, value)

        for name, value in editorDefaults.iteritems():
            Preferences.setEditor(name, value)

        for name, value in editorColorsDefaults.iteritems():
            Preferences.setEditorColour(name, value)

        for name, value in editorOtherFontsDefaults.iteritems():
            Preferences.setEditorOtherFonts(name, value)

        for name, value in shellDefaults.iteritems():
            Preferences.setShell(name, value)

        for name, value in helpDefaults.iteritems():
            Preferences.setHelp(name, value)

        for name, value in multiProjectDefaults.iteritems():
            Preferences.setMultiProject(name, value)

        Preferences.setUI("StyleSheet",
            self.__path + "/SimpleUI/qdarkstyle/style.qss")

    def __disableExtraPlugins(self):

        pluginsToDisable = ['PluginEricapi',
                            'PluginWizardE5MessageBox',
                            'PluginEricdoc',
                            'PluginWizardQFileDialog',
                            'PluginWizardQColorDialog',
                            'PluginWizardQInputDialog',
                            'PluginWizardQMessageBox',
                            'PluginWizardQFontDialog',
                            'PluginVcsSubversion',
                            'PluginVcsMercurial',
                            'PluginVmListspace',
                            'PluginVcsPySvn'
                            ]
        pluginManager = e5App().getObject("PluginManager")

        for obj in pluginManager.getPluginInfos():
            name = obj[0]
            if name in pluginsToDisable:
                pluginManager.deactivatePlugin(name)

    def __applyMonokaiPython(self, lexerName):
        defaultFont = "DejaVu Sans Mono"
        defaultFontSize = 11
        colors = ["#ffffff", "#888877", "#ae81ff", "#ffff88",
                  "#ffff88", "#ff3377", "#ffff88", "#ffff88",
                  "#aaff33", "#aaff47", "#ff3377", "#ffffff",
                  "#888877", "#f8f8f0", "#ffe892", "#aa88ff"]

        lexer = PreferencesLexer(lexerName)

        for i in xrange(0, 15):
            lexer.setPaper(QColor(Qt.black), i)
            lexer.setFont(QFont(defaultFont, defaultFontSize, -1, False), i)
            lexer.setColor(QColor(colors[i]), i)

        # specific values now
        # comment
        lexer.setFont(QFont(defaultFont, defaultFontSize, -1, True), 1)

        # class name
        underlined = QFont(defaultFont, defaultFontSize, -1, False)
        underlined.setUnderline(True)
        lexer.setFont(underlined, 8)

        # Unclosed string
        lexer.setPaper(QColor("#f92672"), 13)
        lexer.setEolFill(True, 13)


        lexer.writeSettings(Preferences.Prefs.settings, "Scintilla")

    def __loadPythonColors(self):
        self.__applyMonokaiPython("Python2")
        self.__applyMonokaiPython("Python3")

    def __enableAdvancedCompletion(self):
        settings = {
            "JediCalltipsEnabled": True,
            "JediCompletionsEnabled": True,
            "JediCompletionsTimeout": 100,
            "ShowQScintillaCompletions": True
        }

        storage = Preferences.Prefs.settings

        for setting, value in settings.iteritems():
            storage.setValue("CompletionJedi/" + setting, value)

    def __getSupportedLanguages(self):
        """
        Private function to get a dictionary of supported lexer languages
        (overrides the original function).

        @return dictionary of supported lexer languages. The keys are the
            internal language names. The items are lists of three entries.
            The first is the display string for the language, the second
            is a dummy file name, which can be used to derive the lexer, and
            the third is the name of an icon file.
            (string, string, string)
        """
        supportedLanguages = {
            "Python2": [QCoreApplication.translate('Lexers', "Python2"),
                        'dummy.py', "lexerPython.png"],
            "Python3": [QCoreApplication.translate('Lexers', "Python3"),
                        'dummy.py', "lexerPython3.png"]
        }

        return supportedLanguages

    def __on_new_editor(self, editor):
        menu = editor.getMenu('Languages')
        for action in menu.actions():
            if action.text() == self.tr("Python2"):
                action.trigger()
            else:
                action.setChecked(False)

        itemstoHide = ['Revert to last saved state',
                       'Check spelling...',
                       'Check spelling of selection...',
                       'Remove from dictionary',
                       'Shorten empty lines',
                       'Languages',
                       'Encodings',
                       'End-of-Line Type',
                       'Use Monospaced Font',
                       'New Document View',
                       'New Document View (with new split)',
                       'Close',
                       'Re-Open With Encoding',
                       'Save',
                       'Save As...',
                       'Save Copy...']
        self.__hideWidgetActions(editor.menu, itemstoHide)

    def __customizeProjecTypeList(self):
        project = e5App().getObject("Project")
        for name, value in project.getProjectTypes("Python3").iteritems():
            project.unregisterProjectType(name)

        project.registerProjectType("Python", "Python Project")

    def __getProgrammingLanguages(self):
        return ["Python2", "Python3"]


    def __showPreferences(self, pageName=None):
        """
        Show modified preferences dialog
        
        @param pageName name of the configuration page to show (string)
        """
        ui = self.__ui
        from Preferences.ConfigurationDialog import ConfigurationDialog
        dlg = ConfigurationDialog(
            ui, 'Configuration',
            expandedEntries=ui._UserInterface__expandedConfigurationEntries,
        )

        self.__modifyPreferencesDialog(dlg)
        dlg.preferencesChanged.connect(ui._UserInterface__preferencesChanged)
        dlg.masterPasswordChanged.connect(ui._UserInterface__masterPasswordChanged)
        dlg.show()
        if pageName is not None:
            dlg.showConfigurationPageByName(pageName)
        elif ui._UserInterface__lastConfigurationPageName:
            dlg.showConfigurationPageByName(ui._UserInterface__lastConfigurationPageName)
        else:
            dlg.showConfigurationPageByName("empty")
        dlg.exec_()
        QApplication.processEvents()
        if dlg.result() == QDialog.Accepted:
            dlg.setPreferences()
            Preferences.syncPreferences()
            ui._UserInterface__preferencesChanged()
        ui._UserInterface__lastConfigurationPageName = dlg.getConfigurationPageName()
        ui._UserInterface__expandedConfigurationEntries = dlg.getExpandedEntries()

    def __modifyPreferencesDialog(self, dlg):
        toDeleteTxt = ['Cooperation', 'CORBA', 'Debugger', 'Email', 'Graphics',
            'Help', 'Icons', 'IRC', 'Mimetypes', 'Network', 'Printer', 'Project',
            'Python', 'Qt', 'Security', 'Templates', 'Tray Starter',
            'Version Control Systems']

        configList = dlg.cw.configList

        for i in xrange(configList.topLevelItemCount() - 1, 0, -1):
            item = configList.topLevelItem(i)
            if item.text(0) in toDeleteTxt:
                configList.takeTopLevelItem(i)

    def __hideExtras(self):
        self.__ui.sbVcsMonitorLed.hide()
        self.__ui.sbZoom.slider.hide()
        e5App().getObject("ViewManager").currentTabWidget.indicator.hide()

    def __addSplit(self):
        self.__viewAddSplit()
        e5App().getObject("ViewManager").currentTabWidget.indicator.hide()