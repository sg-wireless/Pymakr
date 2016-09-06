from PyQt5.QtCore import QObject
from FullUI import UiHelper

# Start-Of-Header
name = "Lite UI"
author = "Pycom"
autoactivate = True
deactivateable = False
version = "1.0.0"
className = "PluginLiteUI"
packageName = "PluginFullUI"
shortDescription = "Pycom Lite version of Eric's GUI"
longDescription = "This plugin adapts the UI for a novice audience"

pyqtApi = 2
python2Compatible = True

class PluginLiteUI(QObject):
    def __init__(self, ui):
        super(PluginLiteUI, self).__init__(ui)
        self.__ui = ui

    def activate(self):
        """
        Public method to activate this plugin.

        @return tuple of None and activation status (boolean)
        """
        self.__setupMenu()
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        pass

    def __setupMenu(self):
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
