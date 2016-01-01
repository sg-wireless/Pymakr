# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for the configuration of eric6.
"""

from __future__ import unicode_literals

import os
import types

from PyQt5.QtCore import QMetaObject, pyqtSignal, Qt, QRect, pyqtSlot
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSizePolicy, QSpacerItem, QWidget, QTreeWidget, \
    QStackedWidget, QDialog, QSplitter, QScrollArea, QApplication, \
    QDialogButtonBox, QFrame, QVBoxLayout, QTreeWidgetItem, QLabel

from E5Gui.E5Application import e5App
from E5Gui.E5LineEdit import E5ClearableLineEdit
from E5Gui import E5MessageBox
from E5Gui.E5MainWindow import E5MainWindow

from Globals import isMacPlatform

import Preferences

import UI.PixmapCache

from eric6config import getConfig


class ConfigurationPageItem(QTreeWidgetItem):
    """
    Class implementing a QTreeWidgetItem holding the configuration page data.
    """
    def __init__(self, parent, text, pageName, iconFile):
        """
        Constructor
        
        @param parent parent widget of the item (QTreeWidget or
            QTreeWidgetItem)
        @param text text to be displayed (string)
        @param pageName name of the configuration page (string)
        @param iconFile file name of the icon to be shown (string)
        """
        super(ConfigurationPageItem, self).__init__(parent, [text])
        self.setIcon(0, UI.PixmapCache.getIcon(iconFile))
        
        self.__pageName = pageName
        
    def getPageName(self):
        """
        Public method to get the name of the associated configuration page.
        
        @return name of the configuration page (string)
        """
        return self.__pageName


class ConfigurationWidget(QWidget):
    """
    Class implementing a dialog for the configuration of eric6.
    
    @signal preferencesChanged() emitted after settings have been changed
    @signal masterPasswordChanged(str, str) emitted after the master
        password has been changed with the old and the new password
    @signal accepted() emitted to indicate acceptance of the changes
    @signal rejected() emitted to indicate rejection of the changes
    """
    preferencesChanged = pyqtSignal()
    masterPasswordChanged = pyqtSignal(str, str)
    accepted = pyqtSignal()
    rejected = pyqtSignal()
    
    DefaultMode = 0
    HelpBrowserMode = 1
    TrayStarterMode = 2
    
    def __init__(self, parent=None, fromEric=True, displayMode=DefaultMode,
                 expandedEntries=[]):
        """
        Constructor
        
        @param parent The parent widget of this dialog. (QWidget)
        @keyparam fromEric flag indicating a dialog generation from within the
            eric6 ide (boolean)
        @keyparam displayMode mode of the configuration dialog
            (DefaultMode, HelpBrowserMode, TrayStarterMode)
        @exception RuntimeError raised to indicate an invalid dialog mode
        @keyparam expandedEntries list of entries to be shown expanded
            (list of strings)
        """
        assert displayMode in (
            ConfigurationWidget.DefaultMode,
            ConfigurationWidget.HelpBrowserMode,
            ConfigurationWidget.TrayStarterMode
        )
        
        super(ConfigurationWidget, self).__init__(parent)
        self.fromEric = fromEric
        self.displayMode = displayMode
        
        self.__setupUi()
        
        self.itmDict = {}
        
        if not fromEric:
            from PluginManager.PluginManager import PluginManager
            try:
                self.pluginManager = e5App().getObject("PluginManager")
            except KeyError:
                self.pluginManager = PluginManager(self)
                e5App().registerObject("PluginManager", self.pluginManager)
        
        if displayMode == ConfigurationWidget.DefaultMode:
            self.configItems = {
                # key : [display string, pixmap name, dialog module name or
                #        page creation function, parent key,
                #        reference to configuration page (must always be last)]
                # The dialog module must have the module function 'create' to
                # create the configuration page. This must have the method
                # 'save' to save the settings.
                "applicationPage":
                [self.tr("Application"), "preferences-application.png",
                 "ApplicationPage", None, None],
                "cooperationPage":
                [self.tr("Cooperation"), "preferences-cooperation.png",
                 "CooperationPage", None, None],
                "corbaPage":
                [self.tr("CORBA"), "preferences-orbit.png",
                 "CorbaPage", None, None],
                "emailPage":
                [self.tr("Email"), "preferences-mail_generic.png",
                 "EmailPage", None, None],
                "graphicsPage":
                [self.tr("Graphics"), "preferences-graphics.png",
                 "GraphicsPage", None, None],
                "iconsPage":
                [self.tr("Icons"), "preferences-icons.png",
                 "IconsPage", None, None],
                "ircPage":
                [self.tr("IRC"), "irc.png",
                 "IrcPage", None, None],
                "logViewerPage":
                [self.tr("Log-Viewer"), "preferences-logviewer.png",
                 "LogViewerPage", None, None],
                "mimeTypesPage":
                [self.tr("Mimetypes"), "preferences-mimetypes.png",
                 "MimeTypesPage", None, None],
                "networkPage":
                [self.tr("Network"), "preferences-network.png",
                 "NetworkPage", None, None],
                "notificationsPage":
                [self.tr("Notifications"),
                 "preferences-notifications.png",
                 "NotificationsPage", None, None],
                "pluginManagerPage":
                [self.tr("Plugin Manager"),
                 "preferences-pluginmanager.png",
                 "PluginManagerPage", None, None],
                "printerPage":
                [self.tr("Printer"), "preferences-printer.png",
                 "PrinterPage", None, None],
                "pythonPage":
                [self.tr("Python"), "preferences-python.png",
                 "PythonPage", None, None],
                "qtPage":
                [self.tr("Qt"), "preferences-qtlogo.png",
                 "QtPage", None, None],
                "securityPage":
                [self.tr("Security"), "preferences-security.png",
                 "SecurityPage", None, None],
                "shellPage":
                [self.tr("Shell"), "preferences-shell.png",
                 "ShellPage", None, None],
                "tasksPage":
                [self.tr("Tasks"), "task.png",
                 "TasksPage", None, None],
                "templatesPage":
                [self.tr("Templates"), "preferences-template.png",
                 "TemplatesPage", None, None],
                "trayStarterPage":
                [self.tr("Tray Starter"), "erict.png",
                 "TrayStarterPage", None, None],
                "vcsPage":
                [self.tr("Version Control Systems"),
                 "preferences-vcs.png",
                 "VcsPage", None, None],
                
                "0debuggerPage":
                [self.tr("Debugger"), "preferences-debugger.png",
                 None, None, None],
                "debuggerGeneralPage":
                [self.tr("General"), "preferences-debugger.png",
                 "DebuggerGeneralPage", "0debuggerPage", None],
                "debuggerPythonPage":
                [self.tr("Python"), "preferences-pyDebugger.png",
                 "DebuggerPythonPage", "0debuggerPage", None],
                "debuggerPython3Page":
                [self.tr("Python3"), "preferences-pyDebugger.png",
                 "DebuggerPython3Page", "0debuggerPage", None],
                
                "0editorPage":
                [self.tr("Editor"), "preferences-editor.png",
                 None, None, None],
                "editorAPIsPage":
                [self.tr("APIs"), "preferences-api.png",
                 "EditorAPIsPage", "0editorPage", None],
                "editorAutocompletionPage":
                [self.tr("Autocompletion"),
                 "preferences-autocompletion.png",
                 "EditorAutocompletionPage", "0editorPage", None],
                "editorAutocompletionQScintillaPage":
                [self.tr("QScintilla"), "qscintilla.png",
                 "EditorAutocompletionQScintillaPage",
                 "editorAutocompletionPage", None],
                "editorCalltipsPage":
                [self.tr("Calltips"), "preferences-calltips.png",
                 "EditorCalltipsPage", "0editorPage", None],
                "editorCalltipsQScintillaPage":
                [self.tr("QScintilla"), "qscintilla.png",
                 "EditorCalltipsQScintillaPage", "editorCalltipsPage", None],
                "editorGeneralPage":
                [self.tr("General"), "preferences-general.png",
                 "EditorGeneralPage", "0editorPage", None],
                "editorFilePage":
                [self.tr("Filehandling"),
                 "preferences-filehandling.png",
                 "EditorFilePage", "0editorPage", None],
                "editorSearchPage":
                [self.tr("Searching"), "preferences-search.png",
                 "EditorSearchPage", "0editorPage", None],
                "editorSpellCheckingPage":
                [self.tr("Spell checking"),
                 "preferences-spellchecking.png",
                 "EditorSpellCheckingPage", "0editorPage", None],
                "editorStylesPage":
                [self.tr("Style"), "preferences-styles.png",
                 "EditorStylesPage", "0editorPage", None],
                "editorSyntaxPage":
                [self.tr("Code Checkers"), "preferences-debugger.png",
                 "EditorSyntaxPage", "0editorPage", None],
                "editorTypingPage":
                [self.tr("Typing"), "preferences-typing.png",
                 "EditorTypingPage", "0editorPage", None],
                "editorExportersPage":
                [self.tr("Exporters"), "preferences-exporters.png",
                 "EditorExportersPage", "0editorPage", None],
                
                "1editorLexerPage":
                [self.tr("Highlighters"),
                 "preferences-highlighting-styles.png",
                 None, "0editorPage", None],
                "editorHighlightersPage":
                [self.tr("Filetype Associations"),
                 "preferences-highlighter-association.png",
                 "EditorHighlightersPage", "1editorLexerPage", None],
                "editorHighlightingStylesPage":
                [self.tr("Styles"),
                 "preferences-highlighting-styles.png",
                 "EditorHighlightingStylesPage", "1editorLexerPage", None],
                "editorKeywordsPage":
                [self.tr("Keywords"), "preferences-keywords.png",
                 "EditorKeywordsPage", "1editorLexerPage", None],
                "editorPropertiesPage":
                [self.tr("Properties"), "preferences-properties.png",
                 "EditorPropertiesPage", "1editorLexerPage", None],
                
                "1editorMouseClickHandlers":
                [self.tr("Mouse Click Handlers"),
                 "preferences-mouse-click-handler.png",
                 "EditorMouseClickHandlerPage", "0editorPage", None],
                
                "0helpPage":
                [self.tr("Help"), "preferences-help.png",
                 None, None, None],
                "helpAppearancePage":
                [self.tr("Appearance"), "preferences-styles.png",
                 "HelpAppearancePage", "0helpPage", None],
                "helpDocumentationPage":
                [self.tr("Help Documentation"),
                 "preferences-helpdocumentation.png",
                 "HelpDocumentationPage", "0helpPage", None],
                "helpFlashCookieManagerPage":
                [self.tr("Flash Cookie Manager"),
                 "flashCookie16.png",
                 "HelpFlashCookieManagerPage", "0helpPage", None],
                "helpViewersPage":
                [self.tr("Help Viewers"),
                 "preferences-helpviewers.png",
                 "HelpViewersPage", "0helpPage", None],
                "helpVirusTotalPage":
                [self.tr("VirusTotal Interface"), "virustotal.png",
                 "HelpVirusTotalPage", "0helpPage", None],
                "helpWebBrowserPage":
                [self.tr("eric6 Web Browser"), "ericWeb.png",
                 "HelpWebBrowserPage", "0helpPage", None],
                
                "0projectPage":
                [self.tr("Project"), "preferences-project.png",
                 None, None, None],
                "projectBrowserPage":
                [self.tr("Project Viewer"), "preferences-project.png",
                 "ProjectBrowserPage", "0projectPage", None],
                "projectPage":
                [self.tr("Project"), "preferences-project.png",
                 "ProjectPage", "0projectPage", None],
                "multiProjectPage":
                [self.tr("Multiproject"),
                 "preferences-multiproject.png",
                 "MultiProjectPage", "0projectPage", None],
                
                "0interfacePage":
                [self.tr("Interface"), "preferences-interface.png",
                 None, None, None],
                "interfacePage":
                [self.tr("Interface"), "preferences-interface.png",
                 "InterfacePage", "0interfacePage", None],
                "viewmanagerPage":
                [self.tr("Viewmanager"), "preferences-viewmanager.png",
                 "ViewmanagerPage", "0interfacePage", None],
            }
            
            self.configItems.update(
                e5App().getObject("PluginManager").getPluginConfigData())
        
        elif displayMode == ConfigurationWidget.HelpBrowserMode:
            self.configItems = {
                # key : [display string, pixmap name, dialog module name or
                #        page creation function, parent key,
                #        reference to configuration page (must always be last)]
                # The dialog module must have the module function 'create' to
                # create the configuration page. This must have the method
                # 'save' to save the settings.
                "interfacePage":
                [self.tr("Interface"), "preferences-interface.png",
                 "HelpInterfacePage", None, None],
                "networkPage":
                [self.tr("Network"), "preferences-network.png",
                 "NetworkPage", None, None],
                "printerPage":
                [self.tr("Printer"), "preferences-printer.png",
                 "PrinterPage", None, None],
                "securityPage":
                [self.tr("Security"), "preferences-security.png",
                 "SecurityPage", None, None],
                
                "0helpPage":
                [self.tr("Help"), "preferences-help.png",
                 None, None, None],
                "helpAppearancePage":
                [self.tr("Appearance"), "preferences-styles.png",
                 "HelpAppearancePage", "0helpPage", None],
                "helpDocumentationPage":
                [self.tr("Help Documentation"),
                 "preferences-helpdocumentation.png",
                 "HelpDocumentationPage", "0helpPage", None],
                "helpFlashCookieManagerPage":
                [self.tr("Flash Cookie Manager"),
                 "flashCookie16.png",
                 "HelpFlashCookieManagerPage", "0helpPage", None],
                "helpVirusTotalPage":
                [self.tr("VirusTotal Interface"), "virustotal.png",
                 "HelpVirusTotalPage", "0helpPage", None],
                "helpWebBrowserPage":
                [self.tr("eric6 Web Browser"), "ericWeb.png",
                 "HelpWebBrowserPage", "0helpPage", None],
            }
        
        elif displayMode == ConfigurationWidget.TrayStarterMode:
            self.configItems = {
                # key : [display string, pixmap name, dialog module name or
                #        page creation function, parent key,
                #        reference to configuration page (must always be last)]
                # The dialog module must have the module function 'create' to
                # create the configuration page. This must have the method
                # 'save' to save the settings.
                "trayStarterPage":
                [self.tr("Tray Starter"), "erict.png",
                 "TrayStarterPage", None, None],
            }
        
        else:
            raise RuntimeError("Illegal mode value: {0}".format(displayMode))
        
        # generate the list entries
        self.__expandedEntries = []
        for key in sorted(self.configItems.keys()):
            pageData = self.configItems[key]
            if pageData[3]:
                if pageData[3] in self.itmDict:
                    pitm = self.itmDict[pageData[3]]  # get the parent item
                else:
                    continue
            else:
                pitm = self.configList
            self.itmDict[key] = ConfigurationPageItem(pitm, pageData[0], key,
                                                      pageData[1])
            self.itmDict[key].setData(0, Qt.UserRole, key)
            if (not self.fromEric or
                displayMode != ConfigurationWidget.DefaultMode or
                    key in expandedEntries):
                self.itmDict[key].setExpanded(True)
        self.configList.sortByColumn(0, Qt.AscendingOrder)
        
        # set the initial size of the splitter
        self.configSplitter.setSizes([200, 600])
        
        self.configList.itemActivated.connect(self.__showConfigurationPage)
        self.configList.itemClicked.connect(self.__showConfigurationPage)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.rejected)
        
        if displayMode != ConfigurationWidget.TrayStarterMode:
            self.__initLexers()
        
    def accept(self):
        """
        Public slot to accept the buttonBox accept signal.
        """
        if not isMacPlatform():
            wdg = self.focusWidget()
            if wdg == self.configList:
                return
        
        self.accepted.emit()
        
    def __setupUi(self):
        """
        Private method to perform the general setup of the configuration
        widget.
        """
        self.setObjectName("ConfigurationDialog")
        self.resize(900, 650)
        self.verticalLayout_2 = QVBoxLayout(self)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        
        self.configSplitter = QSplitter(self)
        self.configSplitter.setOrientation(Qt.Horizontal)
        self.configSplitter.setObjectName("configSplitter")
        
        self.configListWidget = QWidget(self.configSplitter)
        self.leftVBoxLayout = QVBoxLayout(self.configListWidget)
        self.leftVBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.leftVBoxLayout.setSpacing(0)
        self.leftVBoxLayout.setObjectName("leftVBoxLayout")
        self.configListSearch = E5ClearableLineEdit(
            self, self.tr("Enter search text..."))
        self.configListSearch.setObjectName("configListSearch")
        self.leftVBoxLayout.addWidget(self.configListSearch)
        self.configList = QTreeWidget()
        self.configList.setObjectName("configList")
        self.leftVBoxLayout.addWidget(self.configList)
        self.configListSearch.textChanged.connect(self.__searchTextChanged)
        
        self.scrollArea = QScrollArea(self.configSplitter)
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setWidgetResizable(False)
        self.scrollArea.setObjectName("scrollArea")
        
        self.configStack = QStackedWidget()
        self.configStack.setFrameShape(QFrame.Box)
        self.configStack.setFrameShadow(QFrame.Sunken)
        self.configStack.setObjectName("configStack")
        self.scrollArea.setWidget(self.configStack)
        
        self.emptyPage = QWidget()
        self.emptyPage.setGeometry(QRect(0, 0, 372, 591))
        self.emptyPage.setObjectName("emptyPage")
        self.vboxlayout = QVBoxLayout(self.emptyPage)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setContentsMargins(6, 6, 6, 6)
        self.vboxlayout.setObjectName("vboxlayout")
        spacerItem = QSpacerItem(
            20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.emptyPagePixmap = QLabel(self.emptyPage)
        self.emptyPagePixmap.setAlignment(Qt.AlignCenter)
        self.emptyPagePixmap.setObjectName("emptyPagePixmap")
        self.emptyPagePixmap.setPixmap(
            QPixmap(os.path.join(getConfig('ericPixDir'), 'eric.png')))
        self.vboxlayout.addWidget(self.emptyPagePixmap)
        self.textLabel1 = QLabel(self.emptyPage)
        self.textLabel1.setAlignment(Qt.AlignCenter)
        self.textLabel1.setObjectName("textLabel1")
        self.vboxlayout.addWidget(self.textLabel1)
        spacerItem1 = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem1)
        self.configStack.addWidget(self.emptyPage)
        
        self.verticalLayout_2.addWidget(self.configSplitter)
        
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(
            QDialogButtonBox.Apply | QDialogButtonBox.Cancel |
            QDialogButtonBox.Ok | QDialogButtonBox.Reset)
        self.buttonBox.setObjectName("buttonBox")
        if not self.fromEric and \
                self.displayMode == ConfigurationWidget.DefaultMode:
            self.buttonBox.button(QDialogButtonBox.Apply).hide()
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Reset).setEnabled(False)
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.setWindowTitle(self.tr("Preferences"))
        
        self.configList.header().hide()
        self.configList.header().setSortIndicator(0, Qt.AscendingOrder)
        self.configList.setSortingEnabled(True)
        self.textLabel1.setText(
            self.tr("Please select an entry of the list \n"
                    "to display the configuration page."))
        
        QMetaObject.connectSlotsByName(self)
        self.setTabOrder(self.configList, self.configStack)
        
        self.configStack.setCurrentWidget(self.emptyPage)
        
        self.configList.setFocus()
    
    def __searchTextChanged(self, text):
        """
        Private slot to handle a change of the search text.
        
        @param text text to search for (string)
        """
        self.__searchChildItems(self.configList.invisibleRootItem(), text)
    
    def __searchChildItems(self, parent, text):
        """
        Private method to enable child items based on a search string.
        
        @param parent reference to the parent item (QTreeWidgetItem)
        @param text text to search for (string)
        @return flag indicating an enabled child item (boolean)
        """
        childEnabled = False
        text = text.lower()
        for index in range(parent.childCount()):
            itm = parent.child(index)
            if itm.childCount() > 0:
                enable = self.__searchChildItems(itm, text) or \
                    text == "" or text in itm.text(0).lower()
            else:
                enable = text == "" or text in itm.text(0).lower()
            if enable:
                childEnabled = True
            itm.setDisabled(not enable)
        
        return childEnabled
    
    def __initLexers(self):
        """
        Private method to initialize the dictionary of preferences lexers.
        """
        import QScintilla.Lexers
        from .PreferencesLexer import PreferencesLexer, \
            PreferencesLexerLanguageError
        
        self.lexers = {}
        for language in QScintilla.Lexers.getSupportedLanguages():
            if language not in self.lexers:
                try:
                    self.lexers[language] = PreferencesLexer(language, self)
                except PreferencesLexerLanguageError:
                    pass
        
    def __importConfigurationPage(self, name):
        """
        Private method to import a configuration page module.
        
        @param name name of the configuration page module (string)
        @return reference to the configuration page module
        """
        modName = "Preferences.ConfigurationPages.{0}".format(name)
        try:
            mod = __import__(modName)
            components = modName.split('.')
            for comp in components[1:]:
                mod = getattr(mod, comp)
            return mod
        except ImportError:
            E5MessageBox.critical(
                self,
                self.tr("Configuration Page Error"),
                self.tr("""<p>The configuration page <b>{0}</b>"""
                        """ could not be loaded.</p>""").format(name))
            return None
        
    def __showConfigurationPage(self, itm, column):
        """
        Private slot to show a selected configuration page.
        
        @param itm reference to the selected item (QTreeWidgetItem)
        @param column column that was selected (integer) (ignored)
        """
        pageName = itm.getPageName()
        self.showConfigurationPageByName(pageName, setCurrent=False)
        
    def __initPage(self, pageData):
        """
        Private method to initialize a configuration page.
        
        @param pageData data structure for the page to initialize
        @return reference to the initialized page
        """
        page = None
        if isinstance(pageData[2], types.FunctionType):
            page = pageData[2](self)
        else:
            mod = self.__importConfigurationPage(pageData[2])
            if mod:
                page = mod.create(self)
        if page is not None:
            self.configStack.addWidget(page)
            pageData[-1] = page
            try:
                page.setMode(self.displayMode)
            except AttributeError:
                pass
        return page
        
    def showConfigurationPageByName(self, pageName, setCurrent=True):
        """
        Public slot to show a named configuration page.
        
        @param pageName name of the configuration page to show (string)
        @param setCurrent flag indicating to set the current item (boolean)
        """
        if pageName == "empty" or pageName not in self.configItems:
            page = self.emptyPage
        else:
            pageData = self.configItems[pageName]
            if pageData[-1] is None and pageData[2] is not None:
                # the page was not loaded yet, create it
                page = self.__initPage(pageData)
            else:
                page = pageData[-1]
            if page is None:
                page = self.emptyPage
            elif setCurrent:
                items = self.configList.findItems(
                    pageData[0],
                    Qt.MatchFixedString | Qt.MatchRecursive)
                for item in items:
                    if item.data(0, Qt.UserRole) == pageName:
                        self.configList.setCurrentItem(item)
        self.configStack.setCurrentWidget(page)
        ssize = self.scrollArea.size()
        if self.scrollArea.horizontalScrollBar():
            ssize.setHeight(
                ssize.height() -
                self.scrollArea.horizontalScrollBar().height() - 2)
        if self.scrollArea.verticalScrollBar():
            ssize.setWidth(
                ssize.width() -
                self.scrollArea.verticalScrollBar().width() - 2)
        psize = page.minimumSizeHint()
        self.configStack.resize(max(ssize.width(), psize.width()),
                                max(ssize.height(), psize.height()))
        
        if page != self.emptyPage:
            page.polishPage()
            self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)
            self.buttonBox.button(QDialogButtonBox.Reset).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(False)
            self.buttonBox.button(QDialogButtonBox.Reset).setEnabled(False)
        
        # reset scrollbars
        for sb in [self.scrollArea.horizontalScrollBar(),
                   self.scrollArea.verticalScrollBar()]:
            if sb:
                sb.setValue(0)
        
        self.__currentConfigurationPageName = pageName
        
    def getConfigurationPageName(self):
        """
        Public method to get the page name of the current page.
        
        @return page name of the current page (string)
        """
        return self.__currentConfigurationPageName
        
    def calledFromEric(self):
        """
        Public method to check, if invoked from within eric.
        
        @return flag indicating invocation from within eric (boolean)
        """
        return self.fromEric
        
    def getPage(self, pageName):
        """
        Public method to get a reference to the named page.
        
        @param pageName name of the configuration page (string)
        @return reference to the page or None, indicating page was
            not loaded yet
        """
        return self.configItems[pageName][-1]
        
    def getLexers(self):
        """
        Public method to get a reference to the lexers dictionary.
        
        @return reference to the lexers dictionary
        """
        return self.lexers
        
    def setPreferences(self):
        """
        Public method called to store the selected values into the preferences
        storage.
        """
        for key, pageData in list(self.configItems.items()):
            if pageData[-1]:
                pageData[-1].save()
                # page was loaded (and possibly modified)
                QApplication.processEvents()    # ensure HMI is responsive
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Apply):
            self.on_applyButton_clicked()
        elif button == self.buttonBox.button(QDialogButtonBox.Reset):
            self.on_resetButton_clicked()
        
    @pyqtSlot()
    def on_applyButton_clicked(self):
        """
        Private slot called to apply the settings of the current page.
        """
        if self.configStack.currentWidget() != self.emptyPage:
            page = self.configStack.currentWidget()
            savedState = page.saveState()
            page.save()
            self.preferencesChanged.emit()
            if savedState is not None:
                page.setState(savedState)
        
    @pyqtSlot()
    def on_resetButton_clicked(self):
        """
        Private slot called to reset the settings of the current page.
        """
        if self.configStack.currentWidget() != self.emptyPage:
            currentPage = self.configStack.currentWidget()
            savedState = currentPage.saveState()
            pageName = self.configList.currentItem().getPageName()
            self.configStack.removeWidget(currentPage)
            if pageName == "editorHighlightingStylesPage":
                self.__initLexers()
            self.configItems[pageName][-1] = None
            
            self.showConfigurationPageByName(pageName)
            if savedState is not None:
                self.configStack.currentWidget().setState(savedState)
        
    def getExpandedEntries(self):
        """
        Public method to get a list of expanded entries.
        
        @return list of expanded entries (list of string)
        """
        return self.__expandedEntries
    
    @pyqtSlot(QTreeWidgetItem)
    def on_configList_itemCollapsed(self, item):
        """
        Private slot handling a list entry being collapsed.
        
        @param item reference to the collapsed item (QTreeWidgetItem)
        """
        pageName = item.data(0, Qt.UserRole)
        if pageName in self.__expandedEntries:
            self.__expandedEntries.remove(pageName)
    
    @pyqtSlot(QTreeWidgetItem)
    def on_configList_itemExpanded(self, item):
        """
        Private slot handling a list entry being expanded.
        
        @param item reference to the expanded item (QTreeWidgetItem)
        """
        pageName = item.data(0, Qt.UserRole)
        if pageName not in self.__expandedEntries:
            self.__expandedEntries.append(pageName)


class ConfigurationDialog(QDialog):
    """
    Class for the dialog variant.
    
    @signal preferencesChanged() emitted after settings have been changed
    @signal masterPasswordChanged(str, str) emitted after the master
        password has been changed with the old and the new password
    """
    preferencesChanged = pyqtSignal()
    masterPasswordChanged = pyqtSignal(str, str)
    
    DefaultMode = ConfigurationWidget.DefaultMode
    HelpBrowserMode = ConfigurationWidget.HelpBrowserMode
    TrayStarterMode = ConfigurationWidget.TrayStarterMode
    
    def __init__(self, parent=None, name=None, modal=False,
                 fromEric=True, displayMode=ConfigurationWidget.DefaultMode,
                 expandedEntries=[]):
        """
        Constructor
        
        @param parent The parent widget of this dialog. (QWidget)
        @param name The name of this dialog. string
        @param modal Flag indicating a modal dialog. (boolean)
        @keyparam fromEric flag indicating a dialog generation from within the
            eric6 ide (boolean)
        @keyparam displayMode mode of the configuration dialog
            (DefaultMode, HelpBrowserMode, TrayStarterMode)
        @keyparam expandedEntries list of entries to be shown expanded
            (list of strings)
        """
        super(ConfigurationDialog, self).__init__(parent)
        if name:
            self.setObjectName(name)
        self.setModal(modal)
        self.setWindowFlags(Qt.Window)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.cw = ConfigurationWidget(self, fromEric=fromEric,
                                      displayMode=displayMode,
                                      expandedEntries=expandedEntries)
        size = self.cw.size()
        self.layout.addWidget(self.cw)
        self.resize(size)
        self.setWindowTitle(self.cw.windowTitle())
        
        self.cw.accepted.connect(self.accept)
        self.cw.rejected.connect(self.reject)
        self.cw.preferencesChanged.connect(self.__preferencesChanged)
        self.cw.masterPasswordChanged.connect(self.__masterPasswordChanged)
        
    def __preferencesChanged(self):
        """
        Private slot to handle a change of the preferences.
        """
        self.preferencesChanged.emit()
        
    def __masterPasswordChanged(self, oldPassword, newPassword):
        """
        Private slot to handle the change of the master password.
        
        @param oldPassword current master password (string)
        @param newPassword new master password (string)
        """
        self.masterPasswordChanged.emit(oldPassword, newPassword)
        
    def showConfigurationPageByName(self, pageName):
        """
        Public slot to show a named configuration page.
        
        @param pageName name of the configuration page to show (string)
        """
        self.cw.showConfigurationPageByName(pageName)
        
    def getConfigurationPageName(self):
        """
        Public method to get the page name of the current page.
        
        @return page name of the current page (string)
        """
        return self.cw.getConfigurationPageName()
        
    def getExpandedEntries(self):
        """
        Public method to get a list of expanded entries.
        
        @return list of expanded entries (list of string)
        """
        return self.cw.getExpandedEntries()
        
    def setPreferences(self):
        """
        Public method called to store the selected values into the preferences
        storage.
        """
        self.cw.setPreferences()
    
    def accept(self):
        """
        Public method to accept the dialog.
        """
        super(ConfigurationDialog, self).accept()


class ConfigurationWindow(E5MainWindow):
    """
    Main window class for the standalone dialog.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(ConfigurationWindow, self).__init__(parent)
        
        self.cw = ConfigurationWidget(self, fromEric=False)
        size = self.cw.size()
        self.setCentralWidget(self.cw)
        self.resize(size)
        self.setWindowTitle(self.cw.windowTitle())
        
        self.setStyle(Preferences.getUI("Style"),
                      Preferences.getUI("StyleSheet"))
        
        self.cw.accepted.connect(self.accept)
        self.cw.rejected.connect(self.close)
        
    def showConfigurationPageByName(self, pageName):
        """
        Public slot to show a named configuration page.
        
        @param pageName name of the configuration page to show (string)
        """
        self.cw.showConfigurationPageByName(pageName)
        
    def accept(self):
        """
        Public slot called by the Ok button.
        """
        self.cw.setPreferences()
        Preferences.saveResetLayout()
        Preferences.syncPreferences()
        self.close()
