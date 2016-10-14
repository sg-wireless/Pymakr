from PyQt5.QtCore import QObject, QSize, Qt
from PyQt5.QtWidgets import QToolBar, QMenu
from FullUI import UiHelper
from E5Gui.E5Application import e5App
from E5Gui.E5MessageBox import E5MessageBox

import FullUI.PreferencesDialog.SimplifyPreferences
import Preferences
import UI

# Start-Of-Header
name = "Lite UI"
author = "Pycom"
autoactivate = True
deactivateable = True
version = "1.0.0"
className = "PluginLiteUI"
packageName = "PluginLiteUI"
shortDescription = "Pycom light version of Eric's GUI"
longDescription = "This plugin adapts the UI for a novice audience"

pyqtApi = 2
python2Compatible = True

bottomTabsToShow = {"Pycom Console"} # options: "Pycom Console","Shell", "Task-Viewer", "Numbers", "Translator","Local Shell","Log-Viewer"
leftTabsToShow = {"File-Browser","Project-Viewer"} # options: "File-Browser","Project-Viewer","Multiproject-Viewer","Template-Viewer","Symbols","File-Browser"

class PluginLiteUI(QObject):
    def __init__(self, ui):
        super(PluginLiteUI, self).__init__(ui)

        self.__ui = ui
        self.__toolbars = e5App().getObject("ToolbarManager")
        self.__sourcesBrowser = e5App().getObject("ProjectBrowser").getProjectBrowser("sources")

        # override window loaded event
        self.__oldShowEvent = self.__ui.showEvent
        self.__ui.showEvent = self.__windowLoaded

        self.__ui._UserInterface__populateToolbarsMenu = self.__populateToolbarsMenu

        # override source browser createPythonPopupMenus
        self.__oldCreatePythonPopupMenus = self.__sourcesBrowser._ProjectSourcesBrowser__createPythonPopupMenus
        self.__sourcesBrowser._ProjectSourcesBrowser__createPythonPopupMenus = self.__createPythonPopupMenus


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

    def __windowLoaded(self, event):
        """
        Private method that gets called when the main window gets visible.
        """
        # remove preferences items
        self.__simplifyPreferences()
        self.__setupMenus()


        self.__oldShowEvent(event)

        self.__setupSidebars()
        self.__hideStatusBar()
        self.__setupToolbars()
        e5App().getObject("ViewManager").editorOpenedEd.connect(self.__on_new_editor)

        # I must run only once
        self.__ui.showEvent = self.__oldShowEvent
        self.__showInitialTip()

    def __setupMenus(self):
        """
        Private method that hides engineer-level menus and makes the others
        non-detachable.
        """
        # hide unused menus
        for menu in ["view", "extras", "window", "bookmarks", "plugins"]:
            UiHelper.hideUnusedMenu(self.__ui, menu)

        toRemove = {
            "file":      ["Open &Bookmarked Files",
                          "Search &File...",
                          "Save &Copy...",
                          "Export as",
                          "Print Preview",
                          "&Print"],
            "edit":      ["Re&vert to last saved state",
                          "&Indent",
                          "U&nindent",
                          "Toggle Comment",
                          "Convert selection to upper case",
                          "Convert selection to lower case",
                          "Sort",
                          "Complete",
                          "&Calltip",
                          "&Goto Line...",
                          "Goto &Brace",
                          "Goto Last &Edit Location",
                          "Goto Previous Method or Class",
                          "Goto Next Method or Class",
                          "Select to &brace",
                          "&Deselect all",
                          "Shorten empty lines",
                          "Convert &Line End Characters"],
            "project":   ["Session",
                          "Add &translation...",
                          "&Diagrams",
                          "Chec&k",
                          "Sho&w",
                          "Source &Documentation",
                          "Pac&kagers",
                          "&Properties...",
                          "&User Properties...",
                          "Filetype Associations...",
                          "Lexer Associations..."],
            "settings":  ["E&xport Preferences...",
                          "I&mport Preferences...",
                          "Tool&bars...",
                          "Keyboard &Shortcuts...",
                          "&Export Keyboard Shortcuts...",
                          "&Import Keyboard Shortcuts...",
                          "Show external &tools"],
            "help":      ["Show &Versions",
                          "Show &downloadable versions...",
                          "Show Error &Log..."]
        }

        for menu, items in toRemove.iteritems():
            UiHelper.removeWidgetActions(self.__ui.getMenu(menu), items)

        removeFromSearch = ["&Quicksearch",
                            "Quicksearch &backwards",
                            "Search current word forward",
                            "Search current word backward",
                            "Clear search markers",
                            "Search in &Files...",
                            "Replace in F&iles...",
                            "Search in Open Files...",
                            "Replace in Open Files..."]

        for el in self.__ui.getMenu("edit").actions():
            if el.text() == self.__ui.tr("&Search"):
                UiHelper.removeWidgetActions(el.menu(), removeFromSearch)
                break

    def __initLiteToolbar(self, ui, toolbarManager):

        # find first toolbar
        firstToolbar = None

        for toolbar in ui.findChildren(QToolBar):
            if toolbar.isVisible():
                firstToolbar = toolbar
                break


        toCopy = [
                    ['file', ["&Save", "&Open...", "&New"]],
                    ['project', ["&Save", "&Open...", "&New..."]],
        ]

        self.__toolbar = QToolBar(self.tr("Lite tools"), ui)
        self.__toolbar.setIconSize(UI.Config.ToolBarIconSize)
        self.__toolbar.setObjectName("LiteUI")
        self.__toolbar.setToolTip(self.tr('Pymakr lite tools'))

        title = self.__toolbar.windowTitle()
        toolbarManager.addToolBar(self.__toolbar, title)

        # load new toolbar actions
        for bar in toCopy:
            for el in self.__ui.getToolbar(bar[0])[1].actions():
                if el.text() in bar[1]:
                    self.__toolbar.addAction(el)
                    toolbarManager.addAction(el, title)

        ui.registerToolbar("lite", title, self.__toolbar)
        if firstToolbar:
            ui.insertToolBar(firstToolbar, self.__toolbar)
        else:
            ui.addToolBar(self.__toolbar)

        self.__toolbar.setIconSize(QSize(32, 32))

    def __setupToolbars(self):
        self.__initLiteToolbar(self.__ui, self.__toolbars)

        for toolbar in ["project", "edit", "file", "quicksearch", "search", "spelling"]:
            UiHelper.hideToolbar(self.__ui, toolbar)

        self.__fixToolbars()

    def __setupSidebars(self):
        """
        Private method that hides the pro-level sidebars
        """
        allLeftTabs = {"File-Browser",
                      "Project-Viewer",
                      "Multiproject-Viewer",
                      "Template-Viewer",
                      "Symbols",
                      "File-Browser"}

        allBottomTabs = {"Pycom Console", "Shell", "Task-Viewer", "Numbers", "Translator","Local Shell","Log-Viewer"}

        toHideBottom = list(allBottomTabs - bottomTabsToShow)
        toHideLeft = list(allLeftTabs - leftTabsToShow)

        UiHelper.hideItemsSidebar(self.__ui.leftSidebar, toHideLeft)
        UiHelper.hideItemsSidebar(self.__ui.bottomSidebar, toHideBottom)


    def __fixToolbars(self):
        self.__toolbars._fixedToolbars = True # ask future toolbars to be fixed
        for toolbar in self.__ui.findChildren(QToolBar):
            toolbar.setMovable(False)

    def __hideStatusBar(self):
        self.__ui.statusBar().hide()

    def __populateToolbarsMenu(self, menu):
        menu.clear()

    def __on_new_editor(self, editor):
        itemstoHide = ["Autosave enabled",
                       "Typing aids enabled",
                       "Automatic Completion enabled",
                       "Complete",
                       "Calltip",
                       "Check",
                       "Show",
                       "Diagrams",
                       "Tools",
                       "New Document View",
                       "New Document View (with new split)",
                       "Close",
                       "Re-Open With Encoding",
                       "Save",
                       "Save As...",
                       "Save Copy..."]

        UiHelper.hideWidgetActions(editor.menu, itemstoHide)


    def __createPythonPopupMenus(self):
        itemsToRemove = ["Run unittest...",
                         "Diagrams",
                         "Check",
                         "Show",
                         "Configure..."]

        self.__oldCreatePythonPopupMenus()
        UiHelper.removeWidgetActions(self.__sourcesBrowser.sourceMenu, itemsToRemove)

    def __simplifyPreferences(self):
        toDeleteTxt = ['Shell', 'Tasks', 'Interface',
                       'Editor/Autocompletion', 'Editor/Calltips', 'Editor/Code Checkers',
                       'Editor/Exporters', 'Editor/Filehandling', 'Editor/Highlighters/Properties',
                       'Editor/Searching', 'Editor/Spell checking', 'Editor/Typing'
                       ]
        FullUI.PreferencesDialog.SimplifyPreferences.toDeleteExtend(toDeleteTxt)

    def __showInitialTip(self):
        if Preferences.Prefs.settings.value("UI/AdvancedInterfaceTipShown", False) != "true":
            E5MessageBox.information(self.__ui,
                self.__ui.tr("Pymakr hint"),
                self.__ui.tr("<b>Hint</b><br><br>If you're an expert, you can always switch to the full interface by selecting<i>Settings > Switch to expert interface</i> in the main menu."))
            Preferences.Prefs.settings.setValue("UI/AdvancedInterfaceTipShown", "true")
