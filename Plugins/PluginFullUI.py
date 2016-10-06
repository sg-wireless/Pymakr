# to enable some parts of the interface that are being disabled here.
# You can write into the settings:
#   UI/AdvancedBottomSidebar
#   UI/AdvancedLanguages

import os

from PyQt5.QtCore import QObject, QSize, QCoreApplication, QDir, Qt, QByteArray, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QDialog, QApplication
from E5Gui.E5Application import e5App
from E5Gui.E5Action import E5Action

from Project.Project import Project

from QScintilla import Lexers

from FullUI import UiHelper
from PluginUpdate import calc_int_version

import Preferences

import FullUI.PreferencesDialog.SimplifyPreferences
import FullUI.ProjectProperties.PropertiesDialog
import FullUI.InterfacePage.InterfacePage
import FullUI.InterfacePage.SimplifyInterfacePage
import UI.Info
 

# Start-Of-Header
name = "Full UI"
author = "Pycom"
autoactivate = True
deactivateable = False
version = "1.0.0"
className = "PluginFullUI"
packageName = "PluginFullUI"
shortDescription = "Pycom version of Eric's GUI"
longDescription = "This plugin adapts the UI for an engineering audience"

pyqtApi = 2
python2Compatible = True


def setupProjectBrowser():
    """
    Function that hides the project browser tabs
    """
    browser = e5App().getObject("ProjectBrowser")
    browser.setCurrentIndex(0)
    browser.setStyleSheet("QTabWidget::pane { border: 0; }")
    browser.getProjectBrowser("sources").hideColumn(1)
    browser.tabBar().hide()


def setupDefaultParameters():
    uiDefaults = {
        "SidebarDelay": 500,
        "TabViewManagerFilenameLength": 25,
        "PerformVersionCheck": 3, # weekly
        }

    helpDefaults = {"HelpViewerType": 3}

    # fill the workspace with a right Value
    multiProjectDefaults = {}
    multiProjectDefaults["Workspace"] = QDir.homePath()

    for n, value in uiDefaults.iteritems():
        Preferences.setUI(n, value)

    for n, value in helpDefaults.iteritems():
        Preferences.setHelp(n, value)

    for n, value in multiProjectDefaults.iteritems():
        Preferences.setMultiProject(n, value)

def disableExtraPlugins():
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
                        'PluginVcsPySvn']

    pluginManager = e5App().getObject("PluginManager")

    for obj in pluginManager.getPluginInfos():
        n = obj[0]
        if n in pluginsToDisable:
            pluginManager.deactivatePlugin(n)

def enableAdvancedCompletion():
    settings = {
        "JediCalltipsEnabled": True,
        "JediCompletionsEnabled": True,
        "JediCompletionsTimeout": 100,
        "ShowQScintillaCompletions": True
    }

    storage = Preferences.Prefs.settings

    for setting, value in settings.iteritems():
        storage.setValue("CompletionJedi/" + setting, value)

def customizeProjectTypeList():
    project = e5App().getObject("Project")
    for n, val in project.getProjectTypes("Python3").iteritems():
        project.unregisterProjectType(n)

    project.registerProjectType("Python", "Python Project")

class PluginFullUI(QObject):
    def __init__(self, ui):
        super(PluginFullUI, self).__init__(ui)

        # copy variables that will be used in the future
        self.__ui = ui
        self.__path = os.path.dirname(os.path.realpath(__file__))
        self.__toolbars = e5App().getObject("ToolbarManager")

        # override window loaded event
        self.__oldShowEvent = self.__ui.showEvent
        self.__ui.showEvent = self.__windowLoaded

        # hook method that creates toolbar menu
        self.__old_populateToolbarsMenu = self.__ui._UserInterface__populateToolbarsMenu
        self.__ui._UserInterface__populateToolbarsMenu = self.__populateToolbarsMenu

        # override methods that provide the supported languages
        Lexers.getSupportedLanguages = self.__getSupportedLanguages
        Project.getProgrammingLanguages = self.__getProgrammingLanguages

        # first time settings initialization
        if not Preferences.isConfigured() or \
           Preferences.Prefs.settings.value("General/IniVersion", "1.0.0.b1") == "1.0.0.b1" or \
           hasattr(ui, 'firstBoot'):
            ui.firstBoot = True
            self.__firstLoad()

        self.__viewAddSplit = e5App().getObject("ViewManager").addSplit

    def activate(self):
        """
        Public method to activate this plugin.

        @return tuple of None and activation status (boolean)
        """
        self.__setupMenu()
        setupProjectBrowser()
        customizeProjectTypeList()
        self.__hideExtras()

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
        setupDefaultParameters()
        enableAdvancedCompletion()

        Preferences.Prefs.settings.setValue("General/Configured", True)
        Preferences.Prefs.settings.setValue("General/IniVersion", UI.Info.Version)

    def __windowLoaded(self, event):
        """
        Private method that gets called when the main window gets visible.
        """
        e5App().getObject("ViewManager").editorOpenedEd.connect(self.__on_new_editor)
        self.__oldShowEvent(event)
        self.__setupToolbars()
        self.__setupSidebars()
        disableExtraPlugins()
        self.__setUiSwitchMenu()

        # next couple of lines are needed to make the main window appear on foreground in macOS
        self.__ui.show()
        self.__ui.raise_()

        # I must run only once
        self.__ui.showEvent = self.__oldShowEvent

    def __setupMenu(self):
        """
        Private method that hides pro-level menus and makes the others
        non-detachable.
        """
        # hide unused menus
        for menu in ["debug", "start", "unittest", "multiproject"]:
            UiHelper.hideUnusedMenu(self.__ui, menu)

        # make menus non-detachable
        for menu in ["file", "edit", "view", "project", "extras",
                     "settings", "window", "bookmarks", "plugins",
                     "help", "subwindow", "toolbars", "wizards",
                     "macros"]:
            UiHelper.setMenuNonDetachable(self.__ui, menu)

        toRemove = {
            "file":      ["New &Window"],
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
            "help":      ["&Helpviewer...",
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

        for menu, items in toRemove.iteritems():
            UiHelper.removeWidgetActions(self.__ui.getMenu(menu), items)

        toHide = {
            "window":    ["&Right Sidebar",
                          "Edit Profile",
                          "Debug Profile"],
        }

        for menu, items in toHide.iteritems():
            UiHelper.hideWidgetActions(self.__ui.getMenu(menu), items)

        # add help entries
        self.__addLinksIntoHelp()

    def __setupToolbars(self):
        """
        Private method that hides the unused toolbars
        """

        for toolbar in ["vcs", "start", "debug", "multiproject", "help",
                        "unittest", "tools", "settings", "view_profiles",
                        "subversion", "pysvn", "mercurial", "plugins",
                        "view", "bookmarks"]:
            UiHelper.hideToolbar(self.__ui, toolbar)

        toRemove = {
            "file": ["New &Window", "&Close", "Save &Copy...", "&Quit"],
            "edit": ["Clear", "C&omment", "Unco&mment"]
        }

        for toolbar, items in toRemove.iteritems():
            try:
                UiHelper.removeWidgetActions(self.__ui.getToolbar(toolbar)[1], items)
            except:
                pass

        # remove separators before
        separatorsToHide = {
            "file":     ["&New"]
        }

        for toolbar, items in separatorsToHide.iteritems():
            try:
                UiHelper.hideWidgetSeparator(self.__ui.getToolbar(toolbar)[1], items, "before")
            except:
                pass

        # remove separators after
        separatorsToHide = {
            "file":     ["New &Window", "&Open...", "&Close", "Save a&ll"],
            "edit":     ["&Redo", "Clear", "&Paste"],
            "project":  ["&Close"]
        }
        for toolbar, items in separatorsToHide.iteritems():
            try:
                UiHelper.hideWidgetSeparator(self.__ui.getToolbar(toolbar)[1], items)
            except:
                pass

        # set toolbars size
        toResize = ["file", "edit", "project", "bookmarks",
                    "quicksearch", "search", "spelling"]
        for toolbar in toResize:
            UiHelper.setToolbarSize(self.__ui, toolbar, QSize(32, 32))

    def __setupSidebars(self):
        """
        Private method that hides the pro-level sidebars
        """
        toHideLeft = ["Multiproject-Viewer",
                      "Template-Viewer",
                      "Symbols"]

        toHideBottom = ["Log-Viewer"]
        UiHelper.hideItemsSidebar(self.__ui.leftSidebar, toHideLeft)

        if Preferences.Prefs.settings.value("UI/AdvancedBottomSidebar", False) != "true":
            UiHelper.hideItemsSidebar(self.__ui.bottomSidebar, toHideBottom)

        self.__ui.leftSidebar.setMaximumWidth(300)
        self.__ui.bottomSidebar.setMaximumHeight(200)

        self.__ui.rightSidebar.hide()
        self.__ui.rightSidebar.clear()

    def __getSupportedLanguages(self):
        """
        Method to get a dictionary of supported lexer languages
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

        advancedLanguages = {
            "C++": [QCoreApplication.translate('Lexers', "C/C++"), 'dummy.cpp',
                    "lexerCPP.png"]
        }

        if Preferences.Prefs.settings.value("UI/AdvancedLanguages", False) == "true":
            supportedLanguages.update(advancedLanguages)

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

        UiHelper.hideWidgetActions(editor.menu, itemstoHide)

    def __getProgrammingLanguages(self):
        languages = ["Python2", "Python3"]

        if Preferences.Prefs.settings.value("UI/AdvancedLanguages", False) == "true":
            languages.append("C++")

        return languages

    def __hideViewManagerLed(self):
        e5App().getObject("ViewManager").currentTabWidget.setCornerWidget(None, Qt.TopLeftCorner)

    def __hideExtras(self):
        self.__ui.sbVcsMonitorLed.hide()
        self.__ui.sbZoom.slider.hide()
        self.__hideViewManagerLed()

    def __addSplit(self):
        self.__viewAddSplit()
        self.__hideViewManagerLed()

    def __populateToolbarsMenu(self, menu):
        self.__old_populateToolbarsMenu(menu)
        for i in menu.actions()[::-1]:
            if i.text() == menu.tr("&Hide all"):
                menu.removeAction(i)
                break

    def __setUiSwitchMenu(self):
        pluginManager = e5App().getObject("PluginManager")
        self.__LiteUiEnabled = pluginManager.isPluginActive('PluginLiteUI')
 
        if self.__LiteUiEnabled == True:
            # the LiteUI interface is running, show a menu for full interface
            menuText=self.tr("Switch to expert interface")
        else:
            menuText=self.tr("Switch to lite interface")

        settingsMenu = self.__ui.getMenu("settings")

        tooltipText = self.tr(menuText + '. This action will reset the program')
        self.switchUiStyleAct = E5Action(
            menuText,
            menuText + '...',
            0, 0, self, 'switch_ui_style')
        self.switchUiStyleAct.setStatusTip(tooltipText)
        self.switchUiStyleAct.setWhatsThis(
            """<b>""" + menuText + """</b>"""
            """<b>""" +tooltipText + """</b>"""
        )
        self.switchUiStyleAct.triggered.connect(self.__switchUi)
        self.__ui.actions.append(self.switchUiStyleAct)

        settingsMenu.addAction(self.switchUiStyleAct)
        settingsMenu.addSeparator()

    def __switchUi(self):
        # actually, the hook ain't needed, but is here to avoid
        # fast computers to load the new pymakr instance load old settings
        # while they are still being stored
        self.__oldCloseAllWindows = e5App().closeAllWindows
        e5App().closeAllWindows = self.__continueSwitchUi

        self.__ui._UserInterface__restart()

        e5App().closeAllWindows = self.__oldCloseAllWindows

    def __continueSwitchUi(self):
        self.__oldCloseAllWindows()
        pluginManager = e5App().getObject("PluginManager")
        if self.__LiteUiEnabled == True:
            pluginManager.deactivatePlugin("PluginLiteUI")
            # recover a copy of the expert toolbar, if found
            try:
                Preferences.Prefs.settings.setValue("UI/ToolbarManagerState", Preferences.Prefs.settings.value("UI/ExpertToolbarManagerState"))
                Preferences.Prefs.settings.setValue("UI/ViewProfiles2", Preferences.Prefs.settings.value("UI/ExpertViewProfiles2"))
            except:
                Preferences.Prefs.settings.remove("UI/ViewProfiles2")
                Preferences.Prefs.settings.remove("UI/ToolbarManagerState")
        else:
            # before going out, save a copy of the toolbars
            Preferences.Prefs.settings.setValue("UI/ExpertToolbarManagerState", Preferences.Prefs.settings.value("UI/ToolbarManagerState"))
            Preferences.Prefs.settings.setValue("UI/ExpertViewProfiles2", Preferences.Prefs.settings.value("UI/ViewProfiles2"))
            pluginManager.activatePlugin("PluginLiteUI")

        self.__manuallySaveInactivePlugins()
        Preferences.syncPreferences()

    def __manuallySaveInactivePlugins(self):
        names = []
        pluginManager = e5App().getObject("PluginManager")
        for name in list(pluginManager._PluginManager__inactiveModules.keys()):
            names.append(name)
        Preferences.Prefs.settings.setValue(pluginManager._PluginManager__inactivePluginsKey, names)

    def __addLinksIntoHelp(self):
        helpMenu = self.__ui.getMenu("help")

        menuText = "Go to Pycom documentation"
        tooltipText = "Open a web browser with the boards' documentation"
        self.goPycomDocAct = E5Action(
            menuText,
            menuText + '...',
            0, 0, self, 'go_to_doc')
        self.goPycomDocAct.setStatusTip(tooltipText)
        self.goPycomDocAct.setWhatsThis(
            """<b>""" + menuText + """</b>"""
            """<b>""" +tooltipText + """</b>"""
        )
        self.goPycomDocAct.triggered.connect(self.__goPycomDoc)
        self.__ui.actions.append(self.goPycomDocAct)

        helpMenu.addAction(self.goPycomDocAct)
        helpMenu.addSeparator()

    def __goPycomDoc(self):
        QDesktopServices.openUrl(QUrl("https://docs.pycom.io"))