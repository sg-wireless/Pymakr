# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the helpviewer main window.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QByteArray, QSize, QTimer, \
    QUrl, QThread, QTextCodec
from PyQt5.QtGui import QDesktopServices, QKeySequence, QFont, QFontMetrics, \
    QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QDockWidget, \
    QComboBox, QLabel, QSplitter, QMenu, QToolButton, QLineEdit, \
    QApplication, QWhatsThis, QDialog, QHBoxLayout, QProgressBar, QAction, \
    QInputDialog
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtWebKit import QWebSettings, QWebDatabase, QWebSecurityOrigin
from PyQt5.QtWebKitWidgets import QWebPage
try:
    from PyQt5.QtHelp import QHelpEngine, QHelpEngineCore, QHelpSearchQuery
    QTHELP_AVAILABLE = True
except ImportError:
    QTHELP_AVAILABLE = False

from .Network.NetworkAccessManager import SSL_AVAILABLE

from .data import icons_rc          # __IGNORE_WARNING__
from .data import html_rc           # __IGNORE_WARNING__
from .data import javascript_rc     # __IGNORE_WARNING__

from E5Gui.E5Action import E5Action
from E5Gui import E5MessageBox, E5FileDialog, E5ErrorMessage
from E5Gui.E5MainWindow import E5MainWindow
from E5Gui.E5Application import e5App
from E5Gui.E5ZoomWidget import E5ZoomWidget

import Preferences
from Preferences import Shortcuts

import Utilities
import Globals

import UI.PixmapCache
import UI.Config
from UI.Info import Version


class HelpWindow(E5MainWindow):
    """
    Class implementing the web browser main window.
    
    @signal helpClosed() emitted after the window was requested to close down
    @signal zoomTextOnlyChanged(bool) emitted after the zoom text only setting
        was changed
    """
    zoomTextOnlyChanged = pyqtSignal(bool)
    helpClosed = pyqtSignal()
    privacyChanged = pyqtSignal(bool)
    
    helpwindows = []

    maxMenuFilePathLen = 75
    
    _fromEric = False
    useQtHelp = QTHELP_AVAILABLE
    
    _networkAccessManager = None
    _cookieJar = None
    _helpEngine = None
    _bookmarksManager = None
    _historyManager = None
    _passwordManager = None
    _adblockManager = None
    _downloadManager = None
    _feedsManager = None
    _userAgentsManager = None
    _syncManager = None
    _speedDial = None
    _personalInformationManager = None
    _greaseMonkeyManager = None
    _notification = None
    _featurePermissionManager = None
    _flashCookieManager = None
    
    def __init__(self, home, path, parent, name, fromEric=False,
                 initShortcutsOnly=False, searchWord=None):
        """
        Constructor
        
        @param home the URL to be shown (string)
        @param path the path of the working dir (usually '.') (string)
        @param parent parent widget of this window (QWidget)
        @param name name of this window (string)
        @param fromEric flag indicating whether it was called from within
            eric6 (boolean)
        @keyparam initShortcutsOnly flag indicating to just initialize the
            keyboard shortcuts (boolean)
        @keyparam searchWord word to search for (string)
        """
        super(HelpWindow, self).__init__(parent)
        self.setObjectName(name)
        self.setWindowTitle(self.tr("eric6 Web Browser"))
        
        self.fromEric = fromEric
        self.__class__._fromEric = fromEric
        self.initShortcutsOnly = initShortcutsOnly
        self.setWindowIcon(UI.PixmapCache.getIcon("ericWeb.png"))

        self.mHistory = []
        self.__lastConfigurationPageName = ""
        
        self.__eventMouseButtons = Qt.NoButton
        self.__eventKeyboardModifiers = Qt.NoModifier
        
        if self.initShortcutsOnly:
            self.__initActions()
        else:
            from .SearchWidget import SearchWidget
            from .HelpTocWidget import HelpTocWidget
            from .HelpIndexWidget import HelpIndexWidget
            from .HelpSearchWidget import HelpSearchWidget
            from .HelpBrowserWV import HelpBrowser
            from .HelpTabWidget import HelpTabWidget
            from .AdBlock.AdBlockIcon import AdBlockIcon
            from .VirusTotal.VirusTotalApi import VirusTotalAPI
            
            HelpWindow.setUseQtHelp(self.fromEric)
            
            if not self.fromEric:
                self.setStyle(Preferences.getUI("Style"),
                              Preferences.getUI("StyleSheet"))
                
                # initialize some SSL stuff
                from E5Network.E5SslUtilities import initSSL
                initSSL()
            
            if self.useQtHelp:
                self.__helpEngine = \
                    QHelpEngine(os.path.join(Utilities.getConfigDir(),
                                             "browser", "eric6help.qhc"), self)
                self.__removeOldDocumentation()
                self.__helpEngine.warning.connect(self.__warning)
            else:
                self.__helpEngine = None
            self.__helpInstaller = None
            
            self.__zoomWidget = E5ZoomWidget(
                UI.PixmapCache.getPixmap("zoomOut.png"),
                UI.PixmapCache.getPixmap("zoomIn.png"),
                UI.PixmapCache.getPixmap("zoomReset.png"), self)
            self.statusBar().addPermanentWidget(self.__zoomWidget)
            self.__zoomWidget.setMapping(
                HelpBrowser.ZoomLevels, HelpBrowser.ZoomLevelDefault)
            self.__zoomWidget.valueChanged.connect(self.__zoomValueChanged)
            
            self.tabWidget = HelpTabWidget(self)
            self.tabWidget.currentChanged[int].connect(self.__currentChanged)
            self.tabWidget.titleChanged.connect(self.__titleChanged)
            self.tabWidget.showMessage.connect(self.statusBar().showMessage)
            self.tabWidget.browserClosed.connect(self.__browserClosed)
            self.tabWidget.browserZoomValueChanged.connect(
                self.__zoomWidget.setValue)
            
            self.findDlg = SearchWidget(self, self)
            centralWidget = QWidget()
            layout = QVBoxLayout()
            layout.setContentsMargins(1, 1, 1, 1)
            layout.addWidget(self.tabWidget)
            layout.addWidget(self.findDlg)
            self.tabWidget.setSizePolicy(
                QSizePolicy.Preferred, QSizePolicy.Expanding)
            centralWidget.setLayout(layout)
            self.setCentralWidget(centralWidget)
            self.findDlg.hide()
            
            if self.useQtHelp:
                # setup the TOC widget
                self.__tocWindow = HelpTocWidget(self.__helpEngine, self)
                self.__tocDock = QDockWidget(self.tr("Contents"), self)
                self.__tocDock.setObjectName("TocWindow")
                self.__tocDock.setWidget(self.__tocWindow)
                self.addDockWidget(Qt.LeftDockWidgetArea, self.__tocDock)
                
                # setup the index widget
                self.__indexWindow = HelpIndexWidget(self.__helpEngine, self)
                self.__indexDock = QDockWidget(self.tr("Index"), self)
                self.__indexDock.setObjectName("IndexWindow")
                self.__indexDock.setWidget(self.__indexWindow)
                self.addDockWidget(Qt.LeftDockWidgetArea, self.__indexDock)
                
                # setup the search widget
                self.__searchWord = searchWord
                self.__indexing = False
                self.__indexingProgress = None
                self.__searchEngine = self.__helpEngine.searchEngine()
                self.__searchEngine.indexingStarted.connect(
                    self.__indexingStarted)
                self.__searchEngine.indexingFinished.connect(
                    self.__indexingFinished)
                self.__searchWindow = HelpSearchWidget(
                    self.__searchEngine, self)
                self.__searchDock = QDockWidget(self.tr("Search"), self)
                self.__searchDock.setObjectName("SearchWindow")
                self.__searchDock.setWidget(self.__searchWindow)
                self.addDockWidget(Qt.LeftDockWidgetArea, self.__searchDock)
            
            if Preferences.getHelp("SaveGeometry"):
                g = Preferences.getGeometry("HelpViewerGeometry")
            else:
                g = QByteArray()
            if g.isEmpty():
                s = QSize(800, 800)
                self.resize(s)
            else:
                self.restoreGeometry(g)
            
            self.__setIconDatabasePath()
            self.__initWebSettings()
            
            self.__initActions()
            self.__initMenus()
            self.__initToolbars()
            
            self.historyManager()
            
            syncMgr = self.syncManager()
            syncMgr.syncMessage.connect(self.statusBar().showMessage)
            syncMgr.syncError.connect(self.statusBar().showMessage)
            
            self.tabWidget.newBrowser(home)
            self.tabWidget.currentBrowser().setFocus()
            
            self.__class__.helpwindows.append(self)
            
            self.__adBlockIcon = AdBlockIcon(self)
            self.statusBar().addPermanentWidget(self.__adBlockIcon)
            self.__adBlockIcon.setEnabled(
                Preferences.getHelp("AdBlockEnabled"))
            self.tabWidget.currentChanged[int].connect(
                self.__adBlockIcon.currentChanged)
            self.tabWidget.sourceChanged.connect(
                self.__adBlockIcon.sourceChanged)
            
            QDesktopServices.setUrlHandler("http", self.__linkActivated)
            QDesktopServices.setUrlHandler("https", self.__linkActivated)
            
            # setup connections
            self.__activating = False
            if self.useQtHelp:
                # TOC window
                self.__tocWindow.linkActivated.connect(self.__linkActivated)
                self.__tocWindow.escapePressed.connect(
                    self.__activateCurrentBrowser)
                # index window
                self.__indexWindow.linkActivated.connect(self.__linkActivated)
                self.__indexWindow.linksActivated.connect(
                    self.__linksActivated)
                self.__indexWindow.escapePressed.connect(
                    self.__activateCurrentBrowser)
                # search window
                self.__searchWindow.linkActivated.connect(
                    self.__linkActivated)
                self.__searchWindow.escapePressed.connect(
                    self.__activateCurrentBrowser)
            
            state = Preferences.getHelp("HelpViewerState")
            self.restoreState(state)
            
            self.__initHelpDb()
            
            self.__virusTotal = VirusTotalAPI(self)
            self.__virusTotal.submitUrlError.connect(
                self.__virusTotalSubmitUrlError)
            self.__virusTotal.urlScanReport.connect(
                self.__virusTotalUrlScanReport)
            self.__virusTotal.fileScanReport.connect(
                self.__virusTotalFileScanReport)
            
            self.__previewer = None
            self.__shutdownCalled = False
            
            self.flashCookieManager()
            
            if self.useQtHelp:
                QTimer.singleShot(0, self.__lookForNewDocumentation)
                if self.__searchWord is not None:
                    QTimer.singleShot(0, self.__searchForWord)
            
            self.__lastActiveWindow = None
            e5App().focusChanged[QWidget, QWidget].connect(
                self.__appFocusChanged)
            
            QTimer.singleShot(0, syncMgr.loadSettings)
    
    def __del__(self):
        """
        Special method called during object destruction.
        
        Note: This empty variant seems to get rid of the Qt message
        'Warning: QBasicTimer::start: QBasicTimer can only be used with
        threads started with QThread'
        """
        pass
    
    def __setIconDatabasePath(self, enable=True):
        """
        Private method to set the favicons path.
        
        @param enable flag indicating to enabled icon storage (boolean)
        """
        if enable:
            iconDatabasePath = os.path.join(Utilities.getConfigDir(),
                                            "browser", "favicons")
            if not os.path.exists(iconDatabasePath):
                os.makedirs(iconDatabasePath)
        else:
            iconDatabasePath = ""   # setting an empty path disables it
        QWebSettings.setIconDatabasePath(iconDatabasePath)
        
    def __initWebSettings(self):
        """
        Private method to set the global web settings.
        """
        standardFont = Preferences.getHelp("StandardFont")
        fixedFont = Preferences.getHelp("FixedFont")

        settings = QWebSettings.globalSettings()
        settings.setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
        
        settings.setFontFamily(QWebSettings.StandardFont,
                               standardFont.family())
        settings.setFontSize(QWebSettings.DefaultFontSize,
                             standardFont.pointSize())
        settings.setFontFamily(QWebSettings.FixedFont, fixedFont.family())
        settings.setFontSize(QWebSettings.DefaultFixedFontSize,
                             fixedFont.pointSize())
        
        styleSheet = Preferences.getHelp("UserStyleSheet")
        settings.setUserStyleSheetUrl(self.__userStyleSheet(styleSheet))
        
        settings.setAttribute(
            QWebSettings.AutoLoadImages,
            Preferences.getHelp("AutoLoadImages"))
        settings.setAttribute(
            QWebSettings.JavaEnabled,
            Preferences.getHelp("JavaEnabled"))
        settings.setAttribute(
            QWebSettings.JavascriptEnabled,
            Preferences.getHelp("JavaScriptEnabled"))
        settings.setAttribute(
            QWebSettings.JavascriptCanOpenWindows,
            Preferences.getHelp("JavaScriptCanOpenWindows"))
        settings.setAttribute(
            QWebSettings.JavascriptCanAccessClipboard,
            Preferences.getHelp("JavaScriptCanAccessClipboard"))
        settings.setAttribute(
            QWebSettings.PluginsEnabled,
            Preferences.getHelp("PluginsEnabled"))
        
        if hasattr(QWebSettings, "PrintElementBackgrounds"):
            settings.setAttribute(
                QWebSettings.PrintElementBackgrounds,
                Preferences.getHelp("PrintBackgrounds"))
        
        if hasattr(QWebSettings, "setOfflineStoragePath"):
            settings.setAttribute(
                QWebSettings.OfflineStorageDatabaseEnabled,
                Preferences.getHelp("OfflineStorageDatabaseEnabled"))
            webDatabaseDir = os.path.join(
                Utilities.getConfigDir(), "browser", "webdatabases")
            if not os.path.exists(webDatabaseDir):
                os.makedirs(webDatabaseDir)
            settings.setOfflineStoragePath(webDatabaseDir)
            settings.setOfflineStorageDefaultQuota(
                Preferences.getHelp("OfflineStorageDatabaseQuota") *
                1024 * 1024)
        
        if hasattr(QWebSettings, "OfflineWebApplicationCacheEnabled"):
            settings.setAttribute(
                QWebSettings.OfflineWebApplicationCacheEnabled,
                Preferences.getHelp("OfflineWebApplicationCacheEnabled"))
            appCacheDir = os.path.join(
                Utilities.getConfigDir(), "browser", "webappcaches")
            if not os.path.exists(appCacheDir):
                os.makedirs(appCacheDir)
            settings.setOfflineWebApplicationCachePath(appCacheDir)
            settings.setOfflineWebApplicationCacheQuota(
                Preferences.getHelp("OfflineWebApplicationCacheQuota") *
                1024 * 1024)
        
        if hasattr(QWebSettings, "LocalStorageEnabled"):
            settings.setAttribute(
                QWebSettings.LocalStorageEnabled,
                Preferences.getHelp("LocalStorageEnabled"))
            localStorageDir = os.path.join(
                Utilities.getConfigDir(), "browser", "weblocalstorage")
            if not os.path.exists(localStorageDir):
                os.makedirs(localStorageDir)
            settings.setLocalStoragePath(localStorageDir)
        
        if hasattr(QWebSettings, "DnsPrefetchEnabled"):
            settings.setAttribute(
                QWebSettings.DnsPrefetchEnabled,
                Preferences.getHelp("DnsPrefetchEnabled"))
        
        if hasattr(QWebSettings, "defaultTextEncoding"):
            settings.setDefaultTextEncoding(
                Preferences.getHelp("DefaultTextEncoding"))
        
        if hasattr(QWebSettings, "SpatialNavigationEnabled"):
            settings.setAttribute(
                QWebSettings.SpatialNavigationEnabled,
                Preferences.getHelp("SpatialNavigationEnabled"))
        if hasattr(QWebSettings, "LinksIncludedInFocusChain"):
            settings.setAttribute(
                QWebSettings.LinksIncludedInFocusChain,
                Preferences.getHelp("LinksIncludedInFocusChain"))
        if hasattr(QWebSettings, "LocalContentCanAccessRemoteUrls"):
            settings.setAttribute(
                QWebSettings.LocalContentCanAccessRemoteUrls,
                Preferences.getHelp("LocalContentCanAccessRemoteUrls"))
        if hasattr(QWebSettings, "LocalContentCanAccessFileUrls"):
            settings.setAttribute(
                QWebSettings.LocalContentCanAccessFileUrls,
                Preferences.getHelp("LocalContentCanAccessFileUrls"))
        if hasattr(QWebSettings, "XSSAuditingEnabled"):
            settings.setAttribute(
                QWebSettings.XSSAuditingEnabled,
                Preferences.getHelp("XSSAuditingEnabled"))
        if hasattr(QWebSettings, "SiteSpecificQuirksEnabled"):
            settings.setAttribute(
                QWebSettings.SiteSpecificQuirksEnabled,
                Preferences.getHelp("SiteSpecificQuirksEnabled"))
        
        QWebSecurityOrigin.addLocalScheme("eric")
    
    def __initActions(self):
        """
        Private method to define the user interface actions.
        """
        # list of all actions
        self.__actions = []
        
        self.newTabAct = E5Action(
            self.tr('New Tab'),
            UI.PixmapCache.getIcon("tabNew.png"),
            self.tr('&New Tab'),
            QKeySequence(self.tr("Ctrl+T", "File|New Tab")),
            0, self, 'help_file_new_tab')
        self.newTabAct.setStatusTip(self.tr('Open a new help window tab'))
        self.newTabAct.setWhatsThis(self.tr(
            """<b>New Tab</b>"""
            """<p>This opens a new help window tab.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.newTabAct.triggered.connect(self.newTab)
        self.__actions.append(self.newTabAct)
        
        self.newAct = E5Action(
            self.tr('New Window'),
            UI.PixmapCache.getIcon("newWindow.png"),
            self.tr('New &Window'),
            QKeySequence(self.tr("Ctrl+N", "File|New Window")),
            0, self, 'help_file_new_window')
        self.newAct.setStatusTip(self.tr('Open a new help browser window'))
        self.newAct.setWhatsThis(self.tr(
            """<b>New Window</b>"""
            """<p>This opens a new help browser window.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.newAct.triggered.connect(self.newWindow)
        self.__actions.append(self.newAct)
        
        self.openAct = E5Action(
            self.tr('Open File'),
            UI.PixmapCache.getIcon("open.png"),
            self.tr('&Open File'),
            QKeySequence(self.tr("Ctrl+O", "File|Open")),
            0, self, 'help_file_open')
        self.openAct.setStatusTip(self.tr('Open a help file for display'))
        self.openAct.setWhatsThis(self.tr(
            """<b>Open File</b>"""
            """<p>This opens a new help file for display."""
            """ It pops up a file selection dialog.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.openAct.triggered.connect(self.__openFile)
        self.__actions.append(self.openAct)
        
        self.openTabAct = E5Action(
            self.tr('Open File in New Tab'),
            UI.PixmapCache.getIcon("openNewTab.png"),
            self.tr('Open File in New &Tab'),
            QKeySequence(self.tr("Shift+Ctrl+O", "File|Open in new tab")),
            0, self, 'help_file_open_tab')
        self.openTabAct.setStatusTip(
            self.tr('Open a help file for display in a new tab'))
        self.openTabAct.setWhatsThis(self.tr(
            """<b>Open File in New Tab</b>"""
            """<p>This opens a new help file for display in a new tab."""
            """ It pops up a file selection dialog.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.openTabAct.triggered.connect(self.__openFileNewTab)
        self.__actions.append(self.openTabAct)
        
        self.saveAsAct = E5Action(
            self.tr('Save As'),
            UI.PixmapCache.getIcon("fileSaveAs.png"),
            self.tr('&Save As...'),
            QKeySequence(self.tr("Shift+Ctrl+S", "File|Save As")),
            0, self, 'help_file_save_as')
        self.saveAsAct.setStatusTip(
            self.tr('Save the current page to disk'))
        self.saveAsAct.setWhatsThis(self.tr(
            """<b>Save As...</b>"""
            """<p>Saves the current page to disk.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.saveAsAct.triggered.connect(self.__savePageAs)
        self.__actions.append(self.saveAsAct)
        
        self.savePageScreenAct = E5Action(
            self.tr('Save Page Screen'),
            UI.PixmapCache.getIcon("fileSavePixmap.png"),
            self.tr('Save Page Screen...'),
            0, 0, self, 'help_file_save_page_screen')
        self.savePageScreenAct.setStatusTip(
            self.tr('Save the current page as a screen shot'))
        self.savePageScreenAct.setWhatsThis(self.tr(
            """<b>Save Page Screen...</b>"""
            """<p>Saves the current page as a screen shot.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.savePageScreenAct.triggered.connect(self.__savePageScreen)
        self.__actions.append(self.savePageScreenAct)
        
        self.saveVisiblePageScreenAct = E5Action(
            self.tr('Save Visible Page Screen'),
            UI.PixmapCache.getIcon("fileSaveVisiblePixmap.png"),
            self.tr('Save Visible Page Screen...'),
            0, 0, self, 'help_file_save_visible_page_screen')
        self.saveVisiblePageScreenAct.setStatusTip(
            self.tr('Save the visible part of the current page as a'
                    ' screen shot'))
        self.saveVisiblePageScreenAct.setWhatsThis(self.tr(
            """<b>Save Visible Page Screen...</b>"""
            """<p>Saves the visible part of the current page as a"""
            """ screen shot.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.saveVisiblePageScreenAct.triggered.connect(
                self.__saveVisiblePageScreen)
        self.__actions.append(self.saveVisiblePageScreenAct)
        
        bookmarksManager = self.bookmarksManager()
        self.importBookmarksAct = E5Action(
            self.tr('Import Bookmarks'),
            self.tr('&Import Bookmarks...'),
            0, 0, self, 'help_file_import_bookmarks')
        self.importBookmarksAct.setStatusTip(
            self.tr('Import bookmarks from other browsers'))
        self.importBookmarksAct.setWhatsThis(self.tr(
            """<b>Import Bookmarks</b>"""
            """<p>Import bookmarks from other browsers.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.importBookmarksAct.triggered.connect(
                bookmarksManager.importBookmarks)
        self.__actions.append(self.importBookmarksAct)
        
        self.exportBookmarksAct = E5Action(
            self.tr('Export Bookmarks'),
            self.tr('&Export Bookmarks...'),
            0, 0, self, 'help_file_export_bookmarks')
        self.exportBookmarksAct.setStatusTip(
            self.tr('Export the bookmarks into a file'))
        self.exportBookmarksAct.setWhatsThis(self.tr(
            """<b>Export Bookmarks</b>"""
            """<p>Export the bookmarks into a file.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.exportBookmarksAct.triggered.connect(
                bookmarksManager.exportBookmarks)
        self.__actions.append(self.exportBookmarksAct)
        
        self.printAct = E5Action(
            self.tr('Print'),
            UI.PixmapCache.getIcon("print.png"),
            self.tr('&Print'),
            QKeySequence(self.tr("Ctrl+P", "File|Print")),
            0, self, 'help_file_print')
        self.printAct.setStatusTip(self.tr('Print the displayed help'))
        self.printAct.setWhatsThis(self.tr(
            """<b>Print</b>"""
            """<p>Print the displayed help text.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.printAct.triggered.connect(self.tabWidget.printBrowser)
        self.__actions.append(self.printAct)
        
        if Globals.isLinuxPlatform():
            self.printPdfAct = E5Action(
                self.tr('Print as PDF'),
                UI.PixmapCache.getIcon("printPdf.png"),
                self.tr('Print as PDF'),
                0, 0, self, 'help_file_print_pdf')
            self.printPdfAct.setStatusTip(self.tr(
                'Print the displayed help as PDF'))
            self.printPdfAct.setWhatsThis(self.tr(
                """<b>Print as PDF</b>"""
                """<p>Print the displayed help text as a PDF file.</p>"""
            ))
            if not self.initShortcutsOnly:
                self.printPdfAct.triggered.connect(
                    self.tabWidget.printBrowserPdf)
            self.__actions.append(self.printPdfAct)
        else:
            self.printPdfAct = None
        
        self.printPreviewAct = E5Action(
            self.tr('Print Preview'),
            UI.PixmapCache.getIcon("printPreview.png"),
            self.tr('Print Preview'),
            0, 0, self, 'help_file_print_preview')
        self.printPreviewAct.setStatusTip(self.tr(
            'Print preview of the displayed help'))
        self.printPreviewAct.setWhatsThis(self.tr(
            """<b>Print Preview</b>"""
            """<p>Print preview of the displayed help text.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.printPreviewAct.triggered.connect(
                self.tabWidget.printPreviewBrowser)
        self.__actions.append(self.printPreviewAct)
        
        self.closeAct = E5Action(
            self.tr('Close'),
            UI.PixmapCache.getIcon("close.png"),
            self.tr('&Close'),
            QKeySequence(self.tr("Ctrl+W", "File|Close")),
            0, self, 'help_file_close')
        self.closeAct.setStatusTip(self.tr(
            'Close the current help window'))
        self.closeAct.setWhatsThis(self.tr(
            """<b>Close</b>"""
            """<p>Closes the current help window.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.closeAct.triggered.connect(self.tabWidget.closeBrowser)
        self.__actions.append(self.closeAct)
        
        self.closeAllAct = E5Action(
            self.tr('Close All'),
            self.tr('Close &All'),
            0, 0, self, 'help_file_close_all')
        self.closeAllAct.setStatusTip(self.tr('Close all help windows'))
        self.closeAllAct.setWhatsThis(self.tr(
            """<b>Close All</b>"""
            """<p>Closes all help windows except the first one.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.closeAllAct.triggered.connect(
                self.tabWidget.closeAllBrowsers)
        self.__actions.append(self.closeAllAct)
        
        self.privateBrowsingAct = E5Action(
            self.tr('Private Browsing'),
            UI.PixmapCache.getIcon("privateBrowsing.png"),
            self.tr('Private &Browsing'),
            0, 0, self, 'help_file_private_browsing')
        self.privateBrowsingAct.setStatusTip(self.tr('Private Browsing'))
        self.privateBrowsingAct.setWhatsThis(self.tr(
            """<b>Private Browsing</b>"""
            """<p>Enables private browsing. In this mode no history is"""
            """ recorded anymore.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.privateBrowsingAct.triggered.connect(
                self.__privateBrowsing)
        self.privateBrowsingAct.setCheckable(True)
        self.__actions.append(self.privateBrowsingAct)
        
        self.exitAct = E5Action(
            self.tr('Quit'),
            UI.PixmapCache.getIcon("exit.png"),
            self.tr('&Quit'),
            QKeySequence(self.tr("Ctrl+Q", "File|Quit")),
            0, self, 'help_file_quit')
        self.exitAct.setStatusTip(self.tr('Quit the eric6 Web Browser'))
        self.exitAct.setWhatsThis(self.tr(
            """<b>Quit</b>"""
            """<p>Quit the eric6 Web Browser.</p>"""
        ))
        if not self.initShortcutsOnly:
            if self.fromEric:
                self.exitAct.triggered.connect(self.close)
            else:
                self.exitAct.triggered.connect(self.__closeAllWindows)
        self.__actions.append(self.exitAct)
        
        self.backAct = E5Action(
            self.tr('Backward'),
            UI.PixmapCache.getIcon("back.png"),
            self.tr('&Backward'),
            QKeySequence(self.tr("Alt+Left", "Go|Backward")),
            QKeySequence(self.tr("Backspace", "Go|Backward")),
            self, 'help_go_backward')
        self.backAct.setStatusTip(self.tr('Move one help screen backward'))
        self.backAct.setWhatsThis(self.tr(
            """<b>Backward</b>"""
            """<p>Moves one help screen backward. If none is"""
            """ available, this action is disabled.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.backAct.triggered.connect(self.__backward)
        self.__actions.append(self.backAct)
        
        self.forwardAct = E5Action(
            self.tr('Forward'),
            UI.PixmapCache.getIcon("forward.png"),
            self.tr('&Forward'),
            QKeySequence(self.tr("Alt+Right", "Go|Forward")),
            QKeySequence(self.tr("Shift+Backspace", "Go|Forward")),
            self, 'help_go_foreward')
        self.forwardAct.setStatusTip(self.tr(
            'Move one help screen forward'))
        self.forwardAct.setWhatsThis(self.tr(
            """<b>Forward</b>"""
            """<p>Moves one help screen forward. If none is"""
            """ available, this action is disabled.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.forwardAct.triggered.connect(self.__forward)
        self.__actions.append(self.forwardAct)
        
        self.homeAct = E5Action(
            self.tr('Home'),
            UI.PixmapCache.getIcon("home.png"),
            self.tr('&Home'),
            QKeySequence(self.tr("Ctrl+Home", "Go|Home")),
            0, self, 'help_go_home')
        self.homeAct.setStatusTip(self.tr(
            'Move to the initial help screen'))
        self.homeAct.setWhatsThis(self.tr(
            """<b>Home</b>"""
            """<p>Moves to the initial help screen.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.homeAct.triggered.connect(self.__home)
        self.__actions.append(self.homeAct)
        
        self.reloadAct = E5Action(
            self.tr('Reload'),
            UI.PixmapCache.getIcon("reload.png"),
            self.tr('&Reload'),
            QKeySequence(self.tr("Ctrl+R", "Go|Reload")),
            QKeySequence(self.tr("F5", "Go|Reload")),
            self, 'help_go_reload')
        self.reloadAct.setStatusTip(self.tr(
            'Reload the current help screen'))
        self.reloadAct.setWhatsThis(self.tr(
            """<b>Reload</b>"""
            """<p>Reloads the current help screen.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.reloadAct.triggered.connect(self.__reload)
        self.__actions.append(self.reloadAct)
        
        self.stopAct = E5Action(
            self.tr('Stop'),
            UI.PixmapCache.getIcon("stopLoading.png"),
            self.tr('&Stop'),
            QKeySequence(self.tr("Ctrl+.", "Go|Stop")),
            QKeySequence(self.tr("Esc", "Go|Stop")),
            self, 'help_go_stop')
        self.stopAct.setStatusTip(self.tr('Stop loading'))
        self.stopAct.setWhatsThis(self.tr(
            """<b>Stop</b>"""
            """<p>Stops loading of the current tab.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.stopAct.triggered.connect(self.__stopLoading)
        self.__actions.append(self.stopAct)
        
        self.copyAct = E5Action(
            self.tr('Copy'),
            UI.PixmapCache.getIcon("editCopy.png"),
            self.tr('&Copy'),
            QKeySequence(self.tr("Ctrl+C", "Edit|Copy")),
            0, self, 'help_edit_copy')
        self.copyAct.setStatusTip(self.tr('Copy the selected text'))
        self.copyAct.setWhatsThis(self.tr(
            """<b>Copy</b>"""
            """<p>Copy the selected text to the clipboard.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.copyAct.triggered.connect(self.__copy)
        self.__actions.append(self.copyAct)
        
        self.findAct = E5Action(
            self.tr('Find...'),
            UI.PixmapCache.getIcon("find.png"),
            self.tr('&Find...'),
            QKeySequence(self.tr("Ctrl+F", "Edit|Find")),
            0, self, 'help_edit_find')
        self.findAct.setStatusTip(self.tr('Find text in page'))
        self.findAct.setWhatsThis(self.tr(
            """<b>Find</b>"""
            """<p>Find text in the current page.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.findAct.triggered.connect(self.__find)
        self.__actions.append(self.findAct)
        
        self.findNextAct = E5Action(
            self.tr('Find next'),
            UI.PixmapCache.getIcon("findNext.png"),
            self.tr('Find &next'),
            QKeySequence(self.tr("F3", "Edit|Find next")),
            0, self, 'help_edit_find_next')
        self.findNextAct.setStatusTip(self.tr(
            'Find next occurrence of text in page'))
        self.findNextAct.setWhatsThis(self.tr(
            """<b>Find next</b>"""
            """<p>Find the next occurrence of text in the current page.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.findNextAct.triggered.connect(self.findDlg.findNext)
        self.__actions.append(self.findNextAct)
        
        self.findPrevAct = E5Action(
            self.tr('Find previous'),
            UI.PixmapCache.getIcon("findPrev.png"),
            self.tr('Find &previous'),
            QKeySequence(self.tr("Shift+F3", "Edit|Find previous")),
            0, self, 'help_edit_find_previous')
        self.findPrevAct.setStatusTip(
            self.tr('Find previous occurrence of text in page'))
        self.findPrevAct.setWhatsThis(self.tr(
            """<b>Find previous</b>"""
            """<p>Find the previous occurrence of text in the current"""
            """ page.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.findPrevAct.triggered.connect(self.findDlg.findPrevious)
        self.__actions.append(self.findPrevAct)
        
        self.bookmarksManageAct = E5Action(
            self.tr('Manage Bookmarks'),
            self.tr('&Manage Bookmarks...'),
            QKeySequence(self.tr("Ctrl+Shift+B", "Help|Manage bookmarks")),
            0, self, 'help_bookmarks_manage')
        self.bookmarksManageAct.setStatusTip(self.tr(
            'Open a dialog to manage the bookmarks.'))
        self.bookmarksManageAct.setWhatsThis(self.tr(
            """<b>Manage Bookmarks...</b>"""
            """<p>Open a dialog to manage the bookmarks.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.bookmarksManageAct.triggered.connect(
                self.__showBookmarksDialog)
        self.__actions.append(self.bookmarksManageAct)
        
        self.bookmarksAddAct = E5Action(
            self.tr('Add Bookmark'),
            UI.PixmapCache.getIcon("addBookmark.png"),
            self.tr('Add &Bookmark...'),
            QKeySequence(self.tr("Ctrl+D", "Help|Add bookmark")),
            0, self, 'help_bookmark_add')
        self.bookmarksAddAct.setIconVisibleInMenu(False)
        self.bookmarksAddAct.setStatusTip(self.tr(
            'Open a dialog to add a bookmark.'))
        self.bookmarksAddAct.setWhatsThis(self.tr(
            """<b>Add Bookmark</b>"""
            """<p>Open a dialog to add the current URL as a bookmark.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.bookmarksAddAct.triggered.connect(self.__addBookmark)
        self.__actions.append(self.bookmarksAddAct)
        
        self.bookmarksAddFolderAct = E5Action(
            self.tr('Add Folder'),
            self.tr('Add &Folder...'),
            0, 0, self, 'help_bookmark_show_all')
        self.bookmarksAddFolderAct.setStatusTip(self.tr(
            'Open a dialog to add a new bookmarks folder.'))
        self.bookmarksAddFolderAct.setWhatsThis(self.tr(
            """<b>Add Folder...</b>"""
            """<p>Open a dialog to add a new bookmarks folder.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.bookmarksAddFolderAct.triggered.connect(
                self.__addBookmarkFolder)
        self.__actions.append(self.bookmarksAddFolderAct)
        
        self.bookmarksAllTabsAct = E5Action(
            self.tr('Bookmark All Tabs'),
            self.tr('Bookmark All Tabs...'),
            0, 0, self, 'help_bookmark_all_tabs')
        self.bookmarksAllTabsAct.setStatusTip(self.tr(
            'Bookmark all open tabs.'))
        self.bookmarksAllTabsAct.setWhatsThis(self.tr(
            """<b>Bookmark All Tabs...</b>"""
            """<p>Open a dialog to add a new bookmarks folder for"""
            """ all open tabs.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.bookmarksAllTabsAct.triggered.connect(self.bookmarkAll)
        self.__actions.append(self.bookmarksAllTabsAct)
        
        self.whatsThisAct = E5Action(
            self.tr('What\'s This?'),
            UI.PixmapCache.getIcon("whatsThis.png"),
            self.tr('&What\'s This?'),
            QKeySequence(self.tr("Shift+F1", "Help|What's This?'")),
            0, self, 'help_help_whats_this')
        self.whatsThisAct.setStatusTip(self.tr('Context sensitive help'))
        self.whatsThisAct.setWhatsThis(self.tr(
            """<b>Display context sensitive help</b>"""
            """<p>In What's This? mode, the mouse cursor shows an arrow"""
            """ with a question mark, and you can click on the interface"""
            """ elements to get a short description of what they do and how"""
            """ to use them. In dialogs, this feature can be accessed using"""
            """ the context help button in the titlebar.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.whatsThisAct.triggered.connect(self.__whatsThis)
        self.__actions.append(self.whatsThisAct)
        
        self.aboutAct = E5Action(
            self.tr('About'),
            self.tr('&About'),
            0, 0, self, 'help_help_about')
        self.aboutAct.setStatusTip(self.tr(
            'Display information about this software'))
        self.aboutAct.setWhatsThis(self.tr(
            """<b>About</b>"""
            """<p>Display some information about this software.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.aboutAct.triggered.connect(self.__about)
        self.__actions.append(self.aboutAct)
        
        self.aboutQtAct = E5Action(
            self.tr('About Qt'),
            self.tr('About &Qt'),
            0, 0, self, 'help_help_about_qt')
        self.aboutQtAct.setStatusTip(
            self.tr('Display information about the Qt toolkit'))
        self.aboutQtAct.setWhatsThis(self.tr(
            """<b>About Qt</b>"""
            """<p>Display some information about the Qt toolkit.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.aboutQtAct.triggered.connect(self.__aboutQt)
        self.__actions.append(self.aboutQtAct)
        
        self.zoomInAct = E5Action(
            self.tr('Zoom in'),
            UI.PixmapCache.getIcon("zoomIn.png"),
            self.tr('Zoom &in'),
            QKeySequence(self.tr("Ctrl++", "View|Zoom in")),
            QKeySequence(self.tr("Zoom In", "View|Zoom in")),
            self, 'help_view_zoom_in')
        self.zoomInAct.setStatusTip(self.tr('Zoom in on the text'))
        self.zoomInAct.setWhatsThis(self.tr(
            """<b>Zoom in</b>"""
            """<p>Zoom in on the text. This makes the text bigger.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.zoomInAct.triggered.connect(self.__zoomIn)
        self.__actions.append(self.zoomInAct)
        
        self.zoomOutAct = E5Action(
            self.tr('Zoom out'),
            UI.PixmapCache.getIcon("zoomOut.png"),
            self.tr('Zoom &out'),
            QKeySequence(self.tr("Ctrl+-", "View|Zoom out")),
            QKeySequence(self.tr("Zoom Out", "View|Zoom out")),
            self, 'help_view_zoom_out')
        self.zoomOutAct.setStatusTip(self.tr('Zoom out on the text'))
        self.zoomOutAct.setWhatsThis(self.tr(
            """<b>Zoom out</b>"""
            """<p>Zoom out on the text. This makes the text smaller.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.zoomOutAct.triggered.connect(self.__zoomOut)
        self.__actions.append(self.zoomOutAct)
        
        self.zoomResetAct = E5Action(
            self.tr('Zoom reset'),
            UI.PixmapCache.getIcon("zoomReset.png"),
            self.tr('Zoom &reset'),
            QKeySequence(self.tr("Ctrl+0", "View|Zoom reset")),
            0, self, 'help_view_zoom_reset')
        self.zoomResetAct.setStatusTip(self.tr(
            'Reset the zoom of the text'))
        self.zoomResetAct.setWhatsThis(self.tr(
            """<b>Zoom reset</b>"""
            """<p>Reset the zoom of the text. """
            """This sets the zoom factor to 100%.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.zoomResetAct.triggered.connect(self.__zoomReset)
        self.__actions.append(self.zoomResetAct)
        
        if hasattr(QWebSettings, 'ZoomTextOnly'):
            self.zoomTextOnlyAct = E5Action(
                self.tr('Zoom text only'),
                self.tr('Zoom &text only'),
                0, 0, self, 'help_view_zoom_text_only')
            self.zoomTextOnlyAct.setCheckable(True)
            self.zoomTextOnlyAct.setStatusTip(self.tr(
                'Zoom text only; pictures remain constant'))
            self.zoomTextOnlyAct.setWhatsThis(self.tr(
                """<b>Zoom text only</b>"""
                """<p>Zoom text only; pictures remain constant.</p>"""
            ))
            if not self.initShortcutsOnly:
                self.zoomTextOnlyAct.triggered[bool].connect(
                    self.__zoomTextOnly)
            self.__actions.append(self.zoomTextOnlyAct)
        else:
            self.zoomTextOnlyAct = None
        
        self.pageSourceAct = E5Action(
            self.tr('Show page source'),
            self.tr('Show page source'),
            QKeySequence(self.tr('Ctrl+U')), 0,
            self, 'help_show_page_source')
        self.pageSourceAct.setStatusTip(self.tr(
            'Show the page source in an editor'))
        self.pageSourceAct.setWhatsThis(self.tr(
            """<b>Show page source</b>"""
            """<p>Show the page source in an editor.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.pageSourceAct.triggered.connect(self.__showPageSource)
        self.__actions.append(self.pageSourceAct)
        self.addAction(self.pageSourceAct)
        
        self.fullScreenAct = E5Action(
            self.tr('Full Screen'),
            UI.PixmapCache.getIcon("windowFullscreen.png"),
            self.tr('&Full Screen'),
            QKeySequence(self.tr('F11')), 0,
            self, 'help_view_full_scree')
        if not self.initShortcutsOnly:
            self.fullScreenAct.triggered.connect(self.__viewFullScreen)
        self.__actions.append(self.fullScreenAct)
        self.addAction(self.fullScreenAct)
        
        self.nextTabAct = E5Action(
            self.tr('Show next tab'),
            self.tr('Show next tab'),
            QKeySequence(self.tr('Ctrl+Alt+Tab')), 0,
            self, 'help_view_next_tab')
        if not self.initShortcutsOnly:
            self.nextTabAct.triggered.connect(self.__nextTab)
        self.__actions.append(self.nextTabAct)
        self.addAction(self.nextTabAct)
        
        self.prevTabAct = E5Action(
            self.tr('Show previous tab'),
            self.tr('Show previous tab'),
            QKeySequence(self.tr('Shift+Ctrl+Alt+Tab')), 0,
            self, 'help_view_previous_tab')
        if not self.initShortcutsOnly:
            self.prevTabAct.triggered.connect(self.__prevTab)
        self.__actions.append(self.prevTabAct)
        self.addAction(self.prevTabAct)
        
        self.switchTabAct = E5Action(
            self.tr('Switch between tabs'),
            self.tr('Switch between tabs'),
            QKeySequence(self.tr('Ctrl+1')), 0,
            self, 'help_switch_tabs')
        if not self.initShortcutsOnly:
            self.switchTabAct.triggered.connect(self.__switchTab)
        self.__actions.append(self.switchTabAct)
        self.addAction(self.switchTabAct)
        
        self.prefAct = E5Action(
            self.tr('Preferences'),
            UI.PixmapCache.getIcon("configure.png"),
            self.tr('&Preferences...'), 0, 0, self, 'help_preferences')
        self.prefAct.setStatusTip(self.tr(
            'Set the prefered configuration'))
        self.prefAct.setWhatsThis(self.tr(
            """<b>Preferences</b>"""
            """<p>Set the configuration items of the application"""
            """ with your prefered values.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.prefAct.triggered.connect(self.__showPreferences)
        self.__actions.append(self.prefAct)

        self.acceptedLanguagesAct = E5Action(
            self.tr('Languages'),
            UI.PixmapCache.getIcon("flag.png"),
            self.tr('&Languages...'), 0, 0,
            self, 'help_accepted_languages')
        self.acceptedLanguagesAct.setStatusTip(self.tr(
            'Configure the accepted languages for web pages'))
        self.acceptedLanguagesAct.setWhatsThis(self.tr(
            """<b>Languages</b>"""
            """<p>Configure the accepted languages for web pages.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.acceptedLanguagesAct.triggered.connect(
                self.__showAcceptedLanguages)
        self.__actions.append(self.acceptedLanguagesAct)
        
        self.cookiesAct = E5Action(
            self.tr('Cookies'),
            UI.PixmapCache.getIcon("cookie.png"),
            self.tr('C&ookies...'), 0, 0, self, 'help_cookies')
        self.cookiesAct.setStatusTip(self.tr(
            'Configure cookies handling'))
        self.cookiesAct.setWhatsThis(self.tr(
            """<b>Cookies</b>"""
            """<p>Configure cookies handling.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.cookiesAct.triggered.connect(
                self.__showCookiesConfiguration)
        self.__actions.append(self.cookiesAct)
        
        self.flashCookiesAct = E5Action(
            self.tr('Flash Cookies'),
            UI.PixmapCache.getIcon("flashCookie.png"),
            self.tr('&Flash Cookies...'), 0, 0, self, 'help_flash_cookies')
        self.flashCookiesAct.setStatusTip(self.tr(
            'Manage flash cookies'))
        self.flashCookiesAct.setWhatsThis(self.tr(
            """<b>Flash Cookies</b>"""
            """<p>Show a dialog to manage the flash cookies.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.flashCookiesAct.triggered.connect(
                self.__showFlashCookiesManagement)
        self.__actions.append(self.flashCookiesAct)
        
        self.offlineStorageAct = E5Action(
            self.tr('Offline Storage'),
            UI.PixmapCache.getIcon("preferences-html5.png"),
            self.tr('Offline &Storage...'), 0, 0,
            self, 'help_offline_storage')
        self.offlineStorageAct.setStatusTip(self.tr(
            'Configure offline storage'))
        self.offlineStorageAct.setWhatsThis(self.tr(
            """<b>Offline Storage</b>"""
            """<p>Opens a dialog to configure offline storage.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.offlineStorageAct.triggered.connect(
                self.__showOfflineStorageConfiguration)
        self.__actions.append(self.offlineStorageAct)
        
        self.personalDataAct = E5Action(
            self.tr('Personal Information'),
            UI.PixmapCache.getIcon("pim.png"),
            self.tr('Personal Information...'),
            0, 0,
            self, 'help_personal_information')
        self.personalDataAct.setStatusTip(self.tr(
            'Configure personal information for completing form fields'))
        self.personalDataAct.setWhatsThis(self.tr(
            """<b>Personal Information...</b>"""
            """<p>Opens a dialog to configure the personal information"""
            """ used for completing form fields.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.personalDataAct.triggered.connect(
                self.__showPersonalInformationDialog)
        self.__actions.append(self.personalDataAct)
        
        self.greaseMonkeyAct = E5Action(
            self.tr('GreaseMonkey Scripts'),
            UI.PixmapCache.getIcon("greaseMonkey.png"),
            self.tr('GreaseMonkey Scripts...'),
            0, 0,
            self, 'help_greasemonkey')
        self.greaseMonkeyAct.setStatusTip(self.tr(
            'Configure the GreaseMonkey Scripts'))
        self.greaseMonkeyAct.setWhatsThis(self.tr(
            """<b>GreaseMonkey Scripts...</b>"""
            """<p>Opens a dialog to configure the available GreaseMonkey"""
            """ Scripts.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.greaseMonkeyAct.triggered.connect(
                self.__showGreaseMonkeyConfigDialog)
        self.__actions.append(self.greaseMonkeyAct)
        
        self.editMessageFilterAct = E5Action(
            self.tr('Edit Message Filters'),
            UI.PixmapCache.getIcon("warning.png"),
            self.tr('Edit Message Filters...'), 0, 0, self,
            'help_manage_message_filters')
        self.editMessageFilterAct.setStatusTip(self.tr(
            'Edit the message filters used to suppress unwanted messages'))
        self.editMessageFilterAct.setWhatsThis(self.tr(
            """<b>Edit Message Filters</b>"""
            """<p>Opens a dialog to edit the message filters used to"""
            """ suppress unwanted messages been shown in an error"""
            """ window.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.editMessageFilterAct.triggered.connect(
                E5ErrorMessage.editMessageFilters)
        self.__actions.append(self.editMessageFilterAct)

        self.featurePermissionAct = E5Action(
            self.tr('Edit HTML5 Feature Permissions'),
            UI.PixmapCache.getIcon("featurePermission.png"),
            self.tr('Edit HTML5 Feature Permissions...'), 0, 0, self,
            'help_edit_feature_permissions')
        self.featurePermissionAct.setStatusTip(self.tr(
            'Edit the remembered HTML5 feature permissions'))
        self.featurePermissionAct.setWhatsThis(self.tr(
            """<b>Edit HTML5 Feature Permissions</b>"""
            """<p>Opens a dialog to edit the remembered HTML5"""
            """ feature permissions.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.featurePermissionAct.triggered.connect(
                self.__showFeaturePermissionDialog)
        self.__actions.append(self.featurePermissionAct)

        if self.useQtHelp or self.initShortcutsOnly:
            self.syncTocAct = E5Action(
                self.tr('Sync with Table of Contents'),
                UI.PixmapCache.getIcon("syncToc.png"),
                self.tr('Sync with Table of Contents'),
                0, 0, self, 'help_sync_toc')
            self.syncTocAct.setStatusTip(self.tr(
                'Synchronizes the table of contents with current page'))
            self.syncTocAct.setWhatsThis(self.tr(
                """<b>Sync with Table of Contents</b>"""
                """<p>Synchronizes the table of contents with current"""
                """ page.</p>"""
            ))
            if not self.initShortcutsOnly:
                self.syncTocAct.triggered.connect(self.__syncTOC)
            self.__actions.append(self.syncTocAct)
            
            self.showTocAct = E5Action(
                self.tr('Table of Contents'),
                self.tr('Table of Contents'),
                0, 0, self, 'help_show_toc')
            self.showTocAct.setStatusTip(self.tr(
                'Shows the table of contents window'))
            self.showTocAct.setWhatsThis(self.tr(
                """<b>Table of Contents</b>"""
                """<p>Shows the table of contents window.</p>"""
            ))
            if not self.initShortcutsOnly:
                self.showTocAct.triggered.connect(self.__showTocWindow)
            self.__actions.append(self.showTocAct)
            
            self.showIndexAct = E5Action(
                self.tr('Index'),
                self.tr('Index'),
                0, 0, self, 'help_show_index')
            self.showIndexAct.setStatusTip(self.tr(
                'Shows the index window'))
            self.showIndexAct.setWhatsThis(self.tr(
                """<b>Index</b>"""
                """<p>Shows the index window.</p>"""
            ))
            if not self.initShortcutsOnly:
                self.showIndexAct.triggered.connect(self.__showIndexWindow)
            self.__actions.append(self.showIndexAct)
            
            self.showSearchAct = E5Action(
                self.tr('Search'),
                self.tr('Search'),
                0, 0, self, 'help_show_search')
            self.showSearchAct.setStatusTip(self.tr(
                'Shows the search window'))
            self.showSearchAct.setWhatsThis(self.tr(
                """<b>Search</b>"""
                """<p>Shows the search window.</p>"""
            ))
            if not self.initShortcutsOnly:
                self.showSearchAct.triggered.connect(
                    self.__showSearchWindow)
            self.__actions.append(self.showSearchAct)
            
            self.manageQtHelpDocsAct = E5Action(
                self.tr('Manage QtHelp Documents'),
                self.tr('Manage QtHelp &Documents'),
                0, 0, self, 'help_qthelp_documents')
            self.manageQtHelpDocsAct.setStatusTip(self.tr(
                'Shows a dialog to manage the QtHelp documentation set'))
            self.manageQtHelpDocsAct.setWhatsThis(self.tr(
                """<b>Manage QtHelp Documents</b>"""
                """<p>Shows a dialog to manage the QtHelp documentation"""
                """ set.</p>"""
            ))
            if not self.initShortcutsOnly:
                self.manageQtHelpDocsAct.triggered.connect(
                    self.__manageQtHelpDocumentation)
            self.__actions.append(self.manageQtHelpDocsAct)
            
            self.manageQtHelpFiltersAct = E5Action(
                self.tr('Manage QtHelp Filters'),
                self.tr('Manage QtHelp &Filters'),
                0, 0, self, 'help_qthelp_filters')
            self.manageQtHelpFiltersAct.setStatusTip(self.tr(
                'Shows a dialog to manage the QtHelp filters'))
            self.manageQtHelpFiltersAct.setWhatsThis(self.tr(
                """<b>Manage QtHelp Filters</b>"""
                """<p>Shows a dialog to manage the QtHelp filters.</p>"""
            ))
            if not self.initShortcutsOnly:
                self.manageQtHelpFiltersAct.triggered.connect(
                    self.__manageQtHelpFilters)
            self.__actions.append(self.manageQtHelpFiltersAct)
            
            self.reindexDocumentationAct = E5Action(
                self.tr('Reindex Documentation'),
                self.tr('&Reindex Documentation'),
                0, 0, self, 'help_qthelp_reindex')
            self.reindexDocumentationAct.setStatusTip(self.tr(
                'Reindexes the documentation set'))
            self.reindexDocumentationAct.setWhatsThis(self.tr(
                """<b>Reindex Documentation</b>"""
                """<p>Reindexes the documentation set.</p>"""
            ))
            if not self.initShortcutsOnly:
                self.reindexDocumentationAct.triggered.connect(
                    self.__searchEngine.reindexDocumentation)
            self.__actions.append(self.reindexDocumentationAct)
        
        self.clearPrivateDataAct = E5Action(
            self.tr('Clear private data'),
            self.tr('&Clear private data'),
            0, 0,
            self, 'help_clear_private_data')
        self.clearPrivateDataAct.setStatusTip(self.tr(
            'Clear private data'))
        self.clearPrivateDataAct.setWhatsThis(self.tr(
            """<b>Clear private data</b>"""
            """<p>Clears the private data like browsing history, search"""
            """ history or the favicons database.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.clearPrivateDataAct.triggered.connect(
                self.__clearPrivateData)
        self.__actions.append(self.clearPrivateDataAct)
        
        self.clearIconsAct = E5Action(
            self.tr('Clear icons database'),
            self.tr('Clear &icons database'),
            0, 0,
            self, 'help_clear_icons_db')
        self.clearIconsAct.setStatusTip(self.tr(
            'Clear the database of favicons'))
        self.clearIconsAct.setWhatsThis(self.tr(
            """<b>Clear icons database</b>"""
            """<p>Clears the database of favicons of previously visited"""
            """ URLs.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.clearIconsAct.triggered.connect(self.__clearIconsDatabase)
        self.__actions.append(self.clearIconsAct)
        
        self.searchEnginesAct = E5Action(
            self.tr('Configure Search Engines'),
            self.tr('Configure Search &Engines...'),
            0, 0,
            self, 'help_search_engines')
        self.searchEnginesAct.setStatusTip(self.tr(
            'Configure the available search engines'))
        self.searchEnginesAct.setWhatsThis(self.tr(
            """<b>Configure Search Engines...</b>"""
            """<p>Opens a dialog to configure the available search"""
            """ engines.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.searchEnginesAct.triggered.connect(
                self.__showEnginesConfigurationDialog)
        self.__actions.append(self.searchEnginesAct)
        
        self.passwordsAct = E5Action(
            self.tr('Manage Saved Passwords'),
            UI.PixmapCache.getIcon("passwords.png"),
            self.tr('Manage Saved Passwords...'),
            0, 0,
            self, 'help_manage_passwords')
        self.passwordsAct.setStatusTip(self.tr(
            'Manage the saved passwords'))
        self.passwordsAct.setWhatsThis(self.tr(
            """<b>Manage Saved Passwords...</b>"""
            """<p>Opens a dialog to manage the saved passwords.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.passwordsAct.triggered.connect(self.__showPasswordsDialog)
        self.__actions.append(self.passwordsAct)
        
        self.adblockAct = E5Action(
            self.tr('Ad Block'),
            UI.PixmapCache.getIcon("adBlockPlus.png"),
            self.tr('&Ad Block...'),
            0, 0,
            self, 'help_adblock')
        self.adblockAct.setStatusTip(self.tr(
            'Configure AdBlock subscriptions and rules'))
        self.adblockAct.setWhatsThis(self.tr(
            """<b>Ad Block...</b>"""
            """<p>Opens a dialog to configure AdBlock subscriptions and"""
            """ rules.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.adblockAct.triggered.connect(self.__showAdBlockDialog)
        self.__actions.append(self.adblockAct)
        
        self.flashblockAct = E5Action(
            self.tr('ClickToFlash'),
            UI.PixmapCache.getIcon("flashBlock.png"),
            self.tr('&ClickToFlash...'),
            0, 0,
            self, 'help_flashblock')
        self.flashblockAct.setStatusTip(self.tr(
            'Configure ClickToFlash whitelist'))
        self.flashblockAct.setWhatsThis(self.tr(
            """<b>ClickToFlash...</b>"""
            """<p>Opens a dialog to configure the ClickToFlash"""
            """ whitelist.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.flashblockAct.triggered.connect(
                self.__showClickToFlashDialog)
        self.__actions.append(self.flashblockAct)
        
        if SSL_AVAILABLE:
            self.certificatesAct = E5Action(
                self.tr('Manage SSL Certificates'),
                UI.PixmapCache.getIcon("certificates.png"),
                self.tr('Manage SSL Certificates...'),
                0, 0,
                self, 'help_manage_certificates')
            self.certificatesAct.setStatusTip(self.tr(
                'Manage the saved SSL certificates'))
            self.certificatesAct.setWhatsThis(self.tr(
                """<b>Manage SSL Certificates...</b>"""
                """<p>Opens a dialog to manage the saved SSL"""
                """ certificates.</p>"""
            ))
            if not self.initShortcutsOnly:
                self.certificatesAct.triggered.connect(
                    self.__showCertificatesDialog)
            self.__actions.append(self.certificatesAct)
        
        self.toolsMonitorAct = E5Action(
            self.tr('Network Monitor'),
            self.tr('&Network Monitor...'),
            0, 0,
            self, 'help_tools_network_monitor')
        self.toolsMonitorAct.setStatusTip(self.tr(
            'Show the network monitor dialog'))
        self.toolsMonitorAct.setWhatsThis(self.tr(
            """<b>Network Monitor...</b>"""
            """<p>Shows the network monitor dialog.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.toolsMonitorAct.triggered.connect(
                self.__showNetworkMonitor)
        self.__actions.append(self.toolsMonitorAct)
        
        self.showDownloadManagerAct = E5Action(
            self.tr('Downloads'),
            self.tr('Downloads'),
            0, 0, self, 'help_show_downloads')
        self.showDownloadManagerAct.setStatusTip(self.tr(
            'Shows the downloads window'))
        self.showDownloadManagerAct.setWhatsThis(self.tr(
            """<b>Downloads</b>"""
            """<p>Shows the downloads window.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.showDownloadManagerAct.triggered.connect(
                self.__showDownloadsWindow)
        self.__actions.append(self.showDownloadManagerAct)
        
        self.feedsManagerAct = E5Action(
            self.tr('RSS Feeds Dialog'),
            UI.PixmapCache.getIcon("rss22.png"),
            self.tr('&RSS Feeds Dialog...'),
            QKeySequence(self.tr("Ctrl+Shift+F", "Help|RSS Feeds Dialog")),
            0, self, 'help_rss_feeds')
        self.feedsManagerAct.setStatusTip(self.tr(
            'Open a dialog showing the configured RSS feeds.'))
        self.feedsManagerAct.setWhatsThis(self.tr(
            """<b>RSS Feeds Dialog...</b>"""
            """<p>Open a dialog to show the configured RSS feeds."""
            """ It can be used to mange the feeds and to show their"""
            """ contents.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.feedsManagerAct.triggered.connect(self.__showFeedsManager)
        self.__actions.append(self.feedsManagerAct)
        
        self.siteInfoAct = E5Action(
            self.tr('Siteinfo Dialog'),
            UI.PixmapCache.getIcon("helpAbout.png"),
            self.tr('&Siteinfo Dialog...'),
            QKeySequence(self.tr("Ctrl+Shift+I", "Help|Siteinfo Dialog")),
            0, self, 'help_siteinfo')
        self.siteInfoAct.setStatusTip(self.tr(
            'Open a dialog showing some information about the current site.'))
        self.siteInfoAct.setWhatsThis(self.tr(
            """<b>Siteinfo Dialog...</b>"""
            """<p>Opens a dialog showing some information about the current"""
            """ site.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.siteInfoAct.triggered.connect(self.__showSiteinfoDialog)
        self.__actions.append(self.siteInfoAct)
        
        self.userAgentManagerAct = E5Action(
            self.tr('Manage User Agent Settings'),
            self.tr('Manage &User Agent Settings'),
            0, 0, self, 'help_user_agent_settings')
        self.userAgentManagerAct.setStatusTip(self.tr(
            'Shows a dialog to manage the User Agent settings'))
        self.userAgentManagerAct.setWhatsThis(self.tr(
            """<b>Manage User Agent Settings</b>"""
            """<p>Shows a dialog to manage the User Agent settings.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.userAgentManagerAct.triggered.connect(
                self.__showUserAgentsDialog)
        self.__actions.append(self.userAgentManagerAct)
        
        self.synchronizationAct = E5Action(
            self.tr('Synchronize data'),
            UI.PixmapCache.getIcon("sync.png"),
            self.tr('&Synchronize Data...'),
            0, 0, self, 'help_synchronize_data')
        self.synchronizationAct.setStatusTip(self.tr(
            'Shows a dialog to synchronize data via the network'))
        self.synchronizationAct.setWhatsThis(self.tr(
            """<b>Synchronize Data...</b>"""
            """<p>This shows a dialog to synchronize data via the"""
            """ network.</p>"""
        ))
        if not self.initShortcutsOnly:
            self.synchronizationAct.triggered.connect(
                self.__showSyncDialog)
        self.__actions.append(self.synchronizationAct)
        
        self.backAct.setEnabled(False)
        self.forwardAct.setEnabled(False)
        
        # now read the keyboard shortcuts for the actions
        Shortcuts.readShortcuts(helpViewer=self)
    
    def getActions(self):
        """
        Public method to get a list of all actions.
        
        @return list of all actions (list of E5Action)
        """
        return self.__actions[:]
        
    def __initMenus(self):
        """
        Private method to create the menus.
        """
        mb = self.menuBar()
        
        menu = mb.addMenu(self.tr('&File'))
        menu.setTearOffEnabled(True)
        menu.addAction(self.newTabAct)
        menu.addAction(self.newAct)
        menu.addAction(self.openAct)
        menu.addAction(self.openTabAct)
        menu.addSeparator()
        menu.addAction(self.saveAsAct)
        menu.addAction(self.savePageScreenAct)
        menu.addAction(self.saveVisiblePageScreenAct)
        menu.addSeparator()
        menu.addAction(self.printPreviewAct)
        menu.addAction(self.printAct)
        if self.printPdfAct:
            menu.addAction(self.printPdfAct)
        menu.addSeparator()
        menu.addAction(self.closeAct)
        menu.addAction(self.closeAllAct)
        menu.addSeparator()
        menu.addAction(self.privateBrowsingAct)
        menu.addSeparator()
        menu.addAction(self.exitAct)
        
        menu = mb.addMenu(self.tr('&Edit'))
        menu.setTearOffEnabled(True)
        menu.addAction(self.copyAct)
        menu.addSeparator()
        menu.addAction(self.findAct)
        menu.addAction(self.findNextAct)
        menu.addAction(self.findPrevAct)
        
        menu = mb.addMenu(self.tr('&View'))
        menu.setTearOffEnabled(True)
        menu.addAction(self.zoomInAct)
        menu.addAction(self.zoomResetAct)
        menu.addAction(self.zoomOutAct)
        if self.zoomTextOnlyAct is not None:
            menu.addAction(self.zoomTextOnlyAct)
        menu.addSeparator()
        menu.addAction(self.pageSourceAct)
        menu.addAction(self.fullScreenAct)
        if hasattr(QWebSettings, 'defaultTextEncoding'):
            self.__textEncodingMenu = menu.addMenu(
                self.tr("Text Encoding"))
            self.__textEncodingMenu.aboutToShow.connect(
                self.__aboutToShowTextEncodingMenu)
            self.__textEncodingMenu.triggered.connect(self.__setTextEncoding)
        
        menu = mb.addMenu(self.tr('&Go'))
        menu.setTearOffEnabled(True)
        menu.addAction(self.backAct)
        menu.addAction(self.forwardAct)
        menu.addAction(self.homeAct)
        menu.addSeparator()
        menu.addAction(self.stopAct)
        menu.addAction(self.reloadAct)
        if self.useQtHelp:
            menu.addSeparator()
            menu.addAction(self.syncTocAct)
        
        from .History.HistoryMenu import HistoryMenu
        self.historyMenu = HistoryMenu(self, self.tabWidget)
        self.historyMenu.setTearOffEnabled(True)
        self.historyMenu.setTitle(self.tr('H&istory'))
        self.historyMenu.openUrl.connect(self.openUrl)
        self.historyMenu.newUrl.connect(self.openUrlNewTab)
        mb.addMenu(self.historyMenu)
        
        from .Bookmarks.BookmarksMenu import BookmarksMenuBarMenu
        self.bookmarksMenu = BookmarksMenuBarMenu(self)
        self.bookmarksMenu.setTearOffEnabled(True)
        self.bookmarksMenu.setTitle(self.tr('&Bookmarks'))
        self.bookmarksMenu.openUrl.connect(self.openUrl)
        self.bookmarksMenu.newUrl.connect(self.openUrlNewTab)
        mb.addMenu(self.bookmarksMenu)
        
        bookmarksActions = []
        bookmarksActions.append(self.bookmarksManageAct)
        bookmarksActions.append(self.bookmarksAddAct)
        bookmarksActions.append(self.bookmarksAllTabsAct)
        bookmarksActions.append(self.bookmarksAddFolderAct)
        bookmarksActions.append("--SEPARATOR--")
        bookmarksActions.append(self.importBookmarksAct)
        bookmarksActions.append(self.exportBookmarksAct)
        self.bookmarksMenu.setInitialActions(bookmarksActions)
        
        menu = mb.addMenu(self.tr('&Settings'))
        menu.setTearOffEnabled(True)
        menu.addAction(self.prefAct)
        menu.addAction(self.acceptedLanguagesAct)
        menu.addAction(self.cookiesAct)
        menu.addAction(self.flashCookiesAct)
        menu.addAction(self.offlineStorageAct)
        menu.addAction(self.personalDataAct)
        menu.addAction(self.greaseMonkeyAct)
        menu.addAction(self.featurePermissionAct)
        menu.addSeparator()
        menu.addAction(self.editMessageFilterAct)
        menu.addSeparator()
        menu.addAction(self.searchEnginesAct)
        menu.addSeparator()
        menu.addAction(self.passwordsAct)
        if SSL_AVAILABLE:
            menu.addAction(self.certificatesAct)
        menu.addSeparator()
        menu.addAction(self.adblockAct)
        menu.addAction(self.flashblockAct)
        menu.addSeparator()
        self.__settingsMenu = menu
        self.__settingsMenu.aboutToShow.connect(
            self.__aboutToShowSettingsMenu)
        
        from .UserAgent.UserAgentMenu import UserAgentMenu
        self.__userAgentMenu = UserAgentMenu(self.tr("Global User Agent"))
        menu.addMenu(self.__userAgentMenu)
        menu.addAction(self.userAgentManagerAct)
        menu.addSeparator()
        
        if self.useQtHelp:
            menu.addAction(self.manageQtHelpDocsAct)
            menu.addAction(self.manageQtHelpFiltersAct)
            menu.addAction(self.reindexDocumentationAct)
            menu.addSeparator()
        menu.addAction(self.clearPrivateDataAct)
        menu.addAction(self.clearIconsAct)
        
        menu = mb.addMenu(self.tr("&Tools"))
        menu.setTearOffEnabled(True)
        menu.addAction(self.feedsManagerAct)
        menu.addAction(self.siteInfoAct)
        menu.addSeparator()
        menu.addAction(self.synchronizationAct)
        menu.addSeparator()
        menu.addAction(self.toolsMonitorAct)
        
        menu = mb.addMenu(self.tr("&Window"))
        menu.setTearOffEnabled(True)
        menu.addAction(self.showDownloadManagerAct)
        if self.useQtHelp:
            menu.addSeparator()
            menu.addAction(self.showTocAct)
            menu.addAction(self.showIndexAct)
            menu.addAction(self.showSearchAct)
        
        mb.addSeparator()
        
        menu = mb.addMenu(self.tr('&Help'))
        menu.setTearOffEnabled(True)
        menu.addAction(self.aboutAct)
        menu.addAction(self.aboutQtAct)
        menu.addSeparator()
        menu.addAction(self.whatsThisAct)
    
    def __initToolbars(self):
        """
        Private method to create the toolbars.
        """
        filetb = self.addToolBar(self.tr("File"))
        filetb.setObjectName("FileToolBar")
        filetb.setIconSize(UI.Config.ToolBarIconSize)
        filetb.addAction(self.newTabAct)
        filetb.addAction(self.newAct)
        filetb.addAction(self.openAct)
        filetb.addAction(self.openTabAct)
        filetb.addSeparator()
        filetb.addAction(self.saveAsAct)
        filetb.addAction(self.savePageScreenAct)
        filetb.addSeparator()
        filetb.addAction(self.printPreviewAct)
        filetb.addAction(self.printAct)
        if self.printPdfAct:
            filetb.addAction(self.printPdfAct)
        filetb.addSeparator()
        filetb.addAction(self.closeAct)
        filetb.addAction(self.exitAct)
        
        self.savePageScreenMenu = QMenu(self)
        self.savePageScreenMenu.addAction(self.savePageScreenAct)
        self.savePageScreenMenu.addAction(self.saveVisiblePageScreenAct)
        savePageScreenButton = filetb.widgetForAction(self.savePageScreenAct)
        savePageScreenButton.setMenu(self.savePageScreenMenu)
        savePageScreenButton.setPopupMode(QToolButton.MenuButtonPopup)
        
        edittb = self.addToolBar(self.tr("Edit"))
        edittb.setObjectName("EditToolBar")
        edittb.setIconSize(UI.Config.ToolBarIconSize)
        edittb.addAction(self.copyAct)
        
        viewtb = self.addToolBar(self.tr("View"))
        viewtb.setObjectName("ViewToolBar")
        viewtb.setIconSize(UI.Config.ToolBarIconSize)
        viewtb.addAction(self.zoomInAct)
        viewtb.addAction(self.zoomResetAct)
        viewtb.addAction(self.zoomOutAct)
        viewtb.addSeparator()
        viewtb.addAction(self.fullScreenAct)
        
        findtb = self.addToolBar(self.tr("Find"))
        findtb.setObjectName("FindToolBar")
        findtb.setIconSize(UI.Config.ToolBarIconSize)
        findtb.addAction(self.findAct)
        findtb.addAction(self.findNextAct)
        findtb.addAction(self.findPrevAct)
        
        if self.useQtHelp:
            filtertb = self.addToolBar(self.tr("Filter"))
            filtertb.setObjectName("FilterToolBar")
            self.filterCombo = QComboBox()
            self.filterCombo.setMinimumWidth(
                QFontMetrics(QFont()).width("ComboBoxWithEnoughWidth"))
            filtertb.addWidget(QLabel(self.tr("Filtered by: ")))
            filtertb.addWidget(self.filterCombo)
            self.__helpEngine.setupFinished.connect(self.__setupFilterCombo)
            self.filterCombo.activated[str].connect(
                self.__filterQtHelpDocumentation)
            self.__setupFilterCombo()
        
        settingstb = self.addToolBar(self.tr("Settings"))
        settingstb.setObjectName("SettingsToolBar")
        settingstb.setIconSize(UI.Config.ToolBarIconSize)
        settingstb.addAction(self.prefAct)
        settingstb.addAction(self.acceptedLanguagesAct)
        settingstb.addAction(self.cookiesAct)
        settingstb.addAction(self.flashCookiesAct)
        settingstb.addAction(self.offlineStorageAct)
        settingstb.addAction(self.personalDataAct)
        settingstb.addAction(self.greaseMonkeyAct)
        settingstb.addAction(self.featurePermissionAct)
        
        toolstb = self.addToolBar(self.tr("Tools"))
        toolstb.setObjectName("ToolsToolBar")
        toolstb.setIconSize(UI.Config.ToolBarIconSize)
        toolstb.addAction(self.feedsManagerAct)
        toolstb.addAction(self.siteInfoAct)
        toolstb.addSeparator()
        toolstb.addAction(self.synchronizationAct)
        
        helptb = self.addToolBar(self.tr("Help"))
        helptb.setObjectName("HelpToolBar")
        helptb.setIconSize(UI.Config.ToolBarIconSize)
        helptb.addAction(self.whatsThisAct)
        
        self.addToolBarBreak()
        
        gotb = self.addToolBar(self.tr("Go"))
        gotb.setObjectName("GoToolBar")
        gotb.setIconSize(UI.Config.ToolBarIconSize)
        gotb.addAction(self.backAct)
        gotb.addAction(self.forwardAct)
        gotb.addAction(self.reloadAct)
        gotb.addAction(self.stopAct)
        gotb.addAction(self.homeAct)
        gotb.addSeparator()
        
        self.__navigationSplitter = QSplitter(gotb)
        self.__navigationSplitter.addWidget(self.tabWidget.stackedUrlBar())
        
        from .HelpWebSearchWidget import HelpWebSearchWidget
        self.searchEdit = HelpWebSearchWidget(self)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        self.searchEdit.setSizePolicy(sizePolicy)
        self.searchEdit.search.connect(self.__linkActivated)
        self.__navigationSplitter.addWidget(self.searchEdit)
        gotb.addWidget(self.__navigationSplitter)
        
        self.__navigationSplitter.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.__navigationSplitter.setCollapsible(0, False)
        
        self.backMenu = QMenu(self)
        self.backMenu.aboutToShow.connect(self.__showBackMenu)
        self.backMenu.triggered.connect(self.__navigationMenuActionTriggered)
        backButton = gotb.widgetForAction(self.backAct)
        backButton.setMenu(self.backMenu)
        backButton.setPopupMode(QToolButton.MenuButtonPopup)
        
        self.forwardMenu = QMenu(self)
        self.forwardMenu.aboutToShow.connect(self.__showForwardMenu)
        self.forwardMenu.triggered.connect(
            self.__navigationMenuActionTriggered)
        forwardButton = gotb.widgetForAction(self.forwardAct)
        forwardButton.setMenu(self.forwardMenu)
        forwardButton.setPopupMode(QToolButton.MenuButtonPopup)
        
        from .Bookmarks.BookmarksToolBar import BookmarksToolBar
        bookmarksModel = self.bookmarksManager().bookmarksModel()
        self.bookmarksToolBar = BookmarksToolBar(self, bookmarksModel, self)
        self.bookmarksToolBar.setObjectName("BookmarksToolBar")
        self.bookmarksToolBar.setIconSize(UI.Config.ToolBarIconSize)
        self.bookmarksToolBar.openUrl.connect(self.openUrl)
        self.bookmarksToolBar.newUrl.connect(self.openUrlNewTab)
        self.addToolBarBreak()
        self.addToolBar(self.bookmarksToolBar)
        
        self.addToolBarBreak()
        vttb = self.addToolBar(self.tr("VirusTotal"))
        vttb.setObjectName("VirusTotalToolBar")
        vttb.setIconSize(UI.Config.ToolBarIconSize)
        vttb.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.virustotalScanCurrentAct = vttb.addAction(
            UI.PixmapCache.getIcon("virustotal.png"),
            self.tr("Scan current site"),
            self.__virusTotalScanCurrentSite)
        self.virustotalIpReportAct = vttb.addAction(
            UI.PixmapCache.getIcon("virustotal.png"),
            self.tr("IP Address Report"),
            self.__virusTotalIpAddressReport)
        self.virustotalDomainReportAct = vttb.addAction(
            UI.PixmapCache.getIcon("virustotal.png"),
            self.tr("Domain Report"),
            self.__virusTotalDomainReport)
        if not Preferences.getHelp("VirusTotalEnabled") or \
           Preferences.getHelp("VirusTotalServiceKey") == "":
            self.virustotalScanCurrentAct.setEnabled(False)
            self.virustotalIpReportAct.setEnabled(False)
            self.virustotalDomainReportAct.setEnabled(False)
        
    def __nextTab(self):
        """
        Private slot used to show the next tab.
        """
        fwidget = QApplication.focusWidget()
        while fwidget and not hasattr(fwidget, 'nextTab'):
            fwidget = fwidget.parent()
        if fwidget:
            fwidget.nextTab()
        
    def __prevTab(self):
        """
        Private slot used to show the previous tab.
        """
        fwidget = QApplication.focusWidget()
        while fwidget and not hasattr(fwidget, 'prevTab'):
            fwidget = fwidget.parent()
        if fwidget:
            fwidget.prevTab()
        
    def __switchTab(self):
        """
        Private slot used to switch between the current and the previous
        current tab.
        """
        fwidget = QApplication.focusWidget()
        while fwidget and not hasattr(fwidget, 'switchTab'):
            fwidget = fwidget.parent()
        if fwidget:
            fwidget.switchTab()
        
    def __whatsThis(self):
        """
        Private slot called in to enter Whats This mode.
        """
        QWhatsThis.enterWhatsThisMode()
        
    def __titleChanged(self, browser, title):
        """
        Private slot called to handle a change of s browser's title.
        
        @param browser reference to the browser (HelpBrowser)
        @param title new title (string)
        """
        self.historyManager().updateHistoryEntry(
            browser.url().toString(), title)
    
    @pyqtSlot()
    def newTab(self, link=None, requestData=None, addNextTo=None):
        """
        Public slot called to open a new help window tab.
        
        @param link file to be displayed in the new window (string or QUrl)
        @param requestData tuple containing the request data (QNetworkRequest,
            QNetworkAccessManager.Operation, QByteArray)
        @param addNextTo reference to the browser to open the tab after
            (HelpBrowser)
        """
        if addNextTo:
            self.tabWidget.newBrowserAfter(addNextTo, link, requestData)
        else:
            self.tabWidget.newBrowser(link, requestData)
    
    @pyqtSlot()
    def newWindow(self, link=None):
        """
        Public slot called to open a new help browser dialog.
        
        @param link file to be displayed in the new window (string or QUrl)
        """
        if link is None:
            linkName = ""
        elif isinstance(link, QUrl):
            linkName = link.toString()
        else:
            linkName = link
        h = HelpWindow(linkName, ".", self.parent(), "qbrowser", self.fromEric)
        h.show()
    
    def previewer(self):
        """
        Public method to get a reference to the previewer tab.
        
        @return reference to the previewer tab (HelpBrowserWV)
        """
        if self.__previewer is None:
            if self.tabWidget.count() != 1 or \
               self.currentBrowser().url().toString() not in [
                    "", "eric:home", "eric:speeddial", "about:blank"]:
                self.newTab()
            self.__previewer = self.currentBrowser()
        self.tabWidget.setCurrentWidget(self.__previewer)
        return self.__previewer
    
    def __browserClosed(self, browser):
        """
        Private slot handling the closure of a browser tab.
        
        @param browser reference to the browser window (QWidget)
        """
        if browser is self.__previewer:
            self.__previewer = None
    
    def __openFile(self):
        """
        Private slot called to open a file.
        """
        fn = E5FileDialog.getOpenFileName(
            self,
            self.tr("Open File"),
            "",
            self.tr("Help Files (*.html *.htm);;"
                    "PDF Files (*.pdf);;"
                    "CHM Files (*.chm);;"
                    "All Files (*)"
                    ))
        if fn:
            if Utilities.isWindowsPlatform():
                url = "file:///" + Utilities.fromNativeSeparators(fn)
            else:
                url = "file://" + fn
            self.currentBrowser().setSource(QUrl(url))
        
    def __openFileNewTab(self):
        """
        Private slot called to open a file in a new tab.
        """
        fn = E5FileDialog.getOpenFileName(
            self,
            self.tr("Open File"),
            "",
            self.tr("Help Files (*.html *.htm);;"
                    "PDF Files (*.pdf);;"
                    "CHM Files (*.chm);;"
                    "All Files (*)"
                    ))
        if fn:
            if Utilities.isWindowsPlatform():
                url = "file:///" + Utilities.fromNativeSeparators(fn)
            else:
                url = "file://" + fn
            self.newTab(url)
        
    def __savePageAs(self):
        """
        Private slot to save the current page.
        """
        browser = self.currentBrowser()
        if browser is not None:
            browser.saveAs()
    
    @pyqtSlot()
    def __savePageScreen(self, visibleOnly=False):
        """
        Private slot to save the current page as a screen shot.
        
        @param visibleOnly flag indicating to just save the visible part
            of the page (boolean)
        """
        from .PageScreenDialog import PageScreenDialog
        self.__pageScreen = PageScreenDialog(
            self.currentBrowser(), visibleOnly=visibleOnly)
        self.__pageScreen.show()
        
    def __saveVisiblePageScreen(self):
        """
        Private slot to save the visible part of the current page as a screen
        shot.
        """
        self.__savePageScreen(visibleOnly=True)
        
    def __about(self):
        """
        Private slot to show the about information.
        """
        E5MessageBox.about(
            self,
            self.tr("eric6 Web Browser"),
            self.tr(
                """<b>eric6 Web Browser - {0}</b>"""
                """<p>The eric6 Web Browser is a combined help file and HTML"""
                """ browser. It is part of the eric6 development"""
                """ toolset.</p>"""
            ).format(Version))
        
    def __aboutQt(self):
        """
        Private slot to show info about Qt.
        """
        E5MessageBox.aboutQt(self, self.tr("eric6 Web Browser"))

    def setBackwardAvailable(self, b):
        """
        Public slot called when backward references are available.
        
        @param b flag indicating availability of the backwards action (boolean)
        """
        self.backAct.setEnabled(b)
        
    def setForwardAvailable(self, b):
        """
        Public slot called when forward references are available.
        
        @param b flag indicating the availability of the forwards action
            (boolean)
        """
        self.forwardAct.setEnabled(b)
        
    def setLoadingActions(self, b):
        """
        Public slot to set the loading dependent actions.
        
        @param b flag indicating the loading state to consider (boolean)
        """
        self.reloadAct.setEnabled(not b)
        self.stopAct.setEnabled(b)
        
    def __addBookmark(self):
        """
        Private slot called to add the displayed file to the bookmarks.
        """
        view = self.currentBrowser()
        url = bytes(view.url().toEncoded()).decode()
        title = view.title()
        description = ""
        meta = view.page().mainFrame().metaData()
        if "description" in meta:
            description = meta["description"][0]
        
        from .Bookmarks.AddBookmarkDialog import AddBookmarkDialog
        dlg = AddBookmarkDialog()
        dlg.setUrl(url)
        dlg.setTitle(title)
        dlg.setDescription(description)
        menu = self.bookmarksManager().menu()
        idx = self.bookmarksManager().bookmarksModel().nodeIndex(menu)
        dlg.setCurrentIndex(idx)
        dlg.exec_()
        
    def __addBookmarkFolder(self):
        """
        Private slot to add a new bookmarks folder.
        """
        from .Bookmarks.AddBookmarkDialog import AddBookmarkDialog
        dlg = AddBookmarkDialog()
        menu = self.bookmarksManager().menu()
        idx = self.bookmarksManager().bookmarksModel().nodeIndex(menu)
        dlg.setCurrentIndex(idx)
        dlg.setFolder(True)
        dlg.exec_()
        
    def __showBookmarksDialog(self):
        """
        Private slot to show the bookmarks dialog.
        """
        from .Bookmarks.BookmarksDialog import BookmarksDialog
        self.__bookmarksDialog = BookmarksDialog(self)
        self.__bookmarksDialog.openUrl.connect(self.openUrl)
        self.__bookmarksDialog.newUrl.connect(self.openUrlNewTab)
        self.__bookmarksDialog.show()
        
    def bookmarkAll(self):
        """
        Public slot to bookmark all open tabs.
        """
        from .Bookmarks.AddBookmarkDialog import AddBookmarkDialog
        dlg = AddBookmarkDialog()
        dlg.setFolder(True)
        dlg.setTitle(self.tr("Saved Tabs"))
        dlg.exec_()
        
        folder = dlg.addedNode()
        if folder is None:
            return
        
        from .Bookmarks.BookmarkNode import BookmarkNode
        for browser in self.tabWidget.browsers():
            bookmark = BookmarkNode(BookmarkNode.Bookmark)
            bookmark.url = bytes(browser.url().toEncoded()).decode()
            bookmark.title = browser.title()
            meta = browser.page().mainFrame().metaData()
            if "description" in meta:
                bookmark.desc = meta["description"][0]
            
            self.bookmarksManager().addBookmark(folder, bookmark)
        
    def __find(self):
        """
        Private slot to handle the find action.
        
        It opens the search dialog in order to perform the various
        search actions and to collect the various search info.
        """
        self.findDlg.showFind()
        
    def __closeAllWindows(self):
        """
        Private slot to close all windows.
        """
        for browser in HelpWindow.helpwindows:
            if browser != self:
                browser.close()
        self.close()
        
    def closeEvent(self, e):
        """
        Protected event handler for the close event.
        
        @param e the close event (QCloseEvent)
                <br />This event is simply accepted after the history has been
                saved and all window references have been deleted.
        """
        if not self.__shutdownCalled:
            res = self.shutdown()
            
            if res:
                e.accept()
                self.helpClosed.emit()
            else:
                e.ignore()
        else:
            e.accept()
    
    def shutdown(self):
        """
        Public method to shut down the web browser.
        
        @return flag indicating successful shutdown (boolean)
        """
        if not self.tabWidget.shallShutDown():
            return False
        
        if not self.downloadManager().allowQuit():
            return False
        
        self.downloadManager().shutdown()
        
        self.__closeNetworkMonitor()
        
        self.cookieJar().close()
        
        self.bookmarksToolBar.setModel(None)
        self.bookmarksManager().close()
        
        self.historyManager().close()
        
        self.passwordManager().close()
        
        self.adBlockManager().close()
        
        self.userAgentsManager().close()
        
        self.speedDial().close()
        
        self.syncManager().close()
        
        self.__virusTotal.close()
        
        self.flashCookieManager().shutdown()
        
        self.searchEdit.openSearchManager().close()
        
        if self.useQtHelp:
            self.__searchEngine.cancelIndexing()
            self.__searchEngine.cancelSearching()
            
            if self.__helpInstaller:
                self.__helpInstaller.stop()
        
        self.searchEdit.saveSearches()
        
        self.tabWidget.closeAllBrowsers()
        
        state = self.saveState()
        Preferences.setHelp("HelpViewerState", state)

        if Preferences.getHelp("SaveGeometry"):
            if not self.__isFullScreen():
                Preferences.setGeometry("HelpViewerGeometry",
                                        self.saveGeometry())
        else:
            Preferences.setGeometry("HelpViewerGeometry", QByteArray())
        
        try:
            if self.fromEric or len(self.__class__.helpwindows) > 1:
                del self.__class__.helpwindows[
                    self.__class__.helpwindows.index(self)]
        except ValueError:
            pass
        
        if not self.fromEric:
            Preferences.syncPreferences()
        
        self.__shutdownCalled = True
        return True

    def __backward(self):
        """
        Private slot called to handle the backward action.
        """
        self.currentBrowser().backward()
    
    def __forward(self):
        """
        Private slot called to handle the forward action.
        """
        self.currentBrowser().forward()
    
    def __home(self):
        """
        Private slot called to handle the home action.
        """
        self.currentBrowser().home()
    
    def __reload(self):
        """
        Private slot called to handle the reload action.
        """
        self.currentBrowser().reload()
    
    def __stopLoading(self):
        """
        Private slot called to handle loading of the current page.
        """
        self.currentBrowser().stop()
    
    def __zoomValueChanged(self, value):
        """
        Private slot to handle value changes of the zoom widget.
        
        @param value zoom value (integer)
        """
        self.currentBrowser().setZoomValue(value)
    
    def __zoomIn(self):
        """
        Private slot called to handle the zoom in action.
        """
        self.currentBrowser().zoomIn()
        self.__zoomWidget.setValue(self.currentBrowser().zoomValue())
    
    def __zoomOut(self):
        """
        Private slot called to handle the zoom out action.
        """
        self.currentBrowser().zoomOut()
        self.__zoomWidget.setValue(self.currentBrowser().zoomValue())
    
    def __zoomReset(self):
        """
        Private slot called to handle the zoom reset action.
        """
        self.currentBrowser().zoomReset()
        self.__zoomWidget.setValue(self.currentBrowser().zoomValue())
    
    def __zoomTextOnly(self, textOnly):
        """
        Private slot called to handle the zoom text only action.
        
        @param textOnly flag indicating to zoom text only (boolean)
        """
        QWebSettings.globalSettings().setAttribute(
            QWebSettings.ZoomTextOnly, textOnly)
        self.zoomTextOnlyChanged.emit(textOnly)
    
    def __viewFullScreen(self):
        """
        Private slot called to toggle fullscreen mode.
        """
        if self.__isFullScreen():
            # switch back to normal
            self.setWindowState(self.windowState() & ~Qt.WindowFullScreen)
            self.menuBar().show()
            self.fullScreenAct.setIcon(
                UI.PixmapCache.getIcon("windowFullscreen.png"))
            self.fullScreenAct.setIconText(self.tr('Full Screen'))
        else:
            # switch to full screen
            self.setWindowState(self.windowState() | Qt.WindowFullScreen)
            self.menuBar().hide()
            self.fullScreenAct.setIcon(
                UI.PixmapCache.getIcon("windowRestore.png"))
            self.fullScreenAct.setIconText(self.tr('Restore Window'))
    
    def __isFullScreen(self):
        """
        Private method to determine, if the window is in full screen mode.
        
        @return flag indicating full screen mode (boolean)
        """
        return self.windowState() & Qt.WindowFullScreen
    
    def __copy(self):
        """
        Private slot called to handle the copy action.
        """
        self.currentBrowser().copy()
    
    def __privateBrowsing(self):
        """
        Private slot to switch private browsing.
        """
        settings = QWebSettings.globalSettings()
        pb = settings.testAttribute(QWebSettings.PrivateBrowsingEnabled)
        if not pb:
            txt = self.tr(
                """<b>Are you sure you want to turn on private"""
                """ browsing?</b><p>When private browsing is turned on,"""
                """ web pages are not added to the history, searches"""
                """ are not added to the list of recent searches and"""
                """ web site icons and cookies are not stored."""
                """ HTML5 offline storage will be deactivated."""
                """ Until you close the window, you can still click"""
                """ the Back and Forward buttons to return to the"""
                """ web pages you have opened.</p>""")
            res = E5MessageBox.yesNo(self, "", txt)
            if res:
                self.setPrivateMode(True)
        else:
            self.setPrivateMode(False)
    
    def setPrivateMode(self, on):
        """
        Public method to set the privacy mode.
        
        @param on flag indicating the privacy state (boolean)
        """
        QWebSettings.globalSettings().setAttribute(
            QWebSettings.PrivateBrowsingEnabled, on)
        if on:
            self.__setIconDatabasePath(False)
        else:
            self.__setIconDatabasePath(True)
        self.privateBrowsingAct.setChecked(on)
        self.privacyChanged.emit(on)
    
    def currentBrowser(self):
        """
        Public method to get a reference to the current help browser.
        
        @return reference to the current help browser (HelpBrowser)
        """
        return self.tabWidget.currentBrowser()
    
    def browserAt(self, index):
        """
        Public method to get a reference to the help browser with the given
        index.
        
        @param index index of the browser to get (integer)
        @return reference to the indexed help browser (HelpBrowser)
        """
        return self.tabWidget.browserAt(index)
    
    def browsers(self):
        """
        Public method to get a list of references to all help browsers.
        
        @return list of references to help browsers (list of HelpBrowser)
        """
        return self.tabWidget.browsers()
    
    def __currentChanged(self, index):
        """
        Private slot to handle the currentChanged signal.
        
        @param index index of the current tab (integer)
        """
        if index > -1:
            cb = self.currentBrowser()
            if cb is not None:
                self.setForwardAvailable(cb.isForwardAvailable())
                self.setBackwardAvailable(cb.isBackwardAvailable())
                self.setLoadingActions(cb.isLoading())
                
                # set value of zoom widget
                self.__zoomWidget.setValue(cb.zoomValue())
    
    def __showPreferences(self):
        """
        Private slot to set the preferences.
        """
        from Preferences.ConfigurationDialog import ConfigurationDialog
        dlg = ConfigurationDialog(
            self, 'Configuration', True, fromEric=self.fromEric,
            displayMode=ConfigurationDialog.HelpBrowserMode)
        dlg.preferencesChanged.connect(self.preferencesChanged)
        dlg.masterPasswordChanged.connect(self.masterPasswordChanged)
        dlg.show()
        if self.__lastConfigurationPageName:
            dlg.showConfigurationPageByName(self.__lastConfigurationPageName)
        else:
            dlg.showConfigurationPageByName("empty")
        dlg.exec_()
        QApplication.processEvents()
        if dlg.result() == QDialog.Accepted:
            dlg.setPreferences()
            Preferences.syncPreferences()
            self.preferencesChanged()
        self.__lastConfigurationPageName = dlg.getConfigurationPageName()
    
    def preferencesChanged(self):
        """
        Public slot to handle a change of preferences.
        """
        if not self.fromEric:
            self.setStyle(Preferences.getUI("Style"),
                          Preferences.getUI("StyleSheet"))
        
        self.__initWebSettings()
        
        self.networkAccessManager().preferencesChanged()
        
        self.historyManager().preferencesChanged()
        
        self.tabWidget.preferencesChanged()
        
        self.searchEdit.preferencesChanged()
        
        self.__virusTotal.preferencesChanged()
        if not Preferences.getHelp("VirusTotalEnabled") or \
           Preferences.getHelp("VirusTotalServiceKey") == "":
            self.virustotalScanCurrentAct.setEnabled(False)
            self.virustotalIpReportAct.setEnabled(False)
            self.virustotalDomainReportAct.setEnabled(False)
        else:
            self.virustotalScanCurrentAct.setEnabled(True)
            self.virustotalIpReportAct.setEnabled(True)
            self.virustotalDomainReportAct.setEnabled(True)
    
    def masterPasswordChanged(self, oldPassword, newPassword):
        """
        Public slot to handle the change of the master password.
        
        @param oldPassword current master password (string)
        @param newPassword new master password (string)
        """
        from Preferences.ConfigurationDialog import ConfigurationDialog
        self.passwordManager().masterPasswordChanged(oldPassword, newPassword)
        if self.fromEric and isinstance(self.sender(), ConfigurationDialog):
            # we were called from our local configuration dialog
            Preferences.convertPasswords(oldPassword, newPassword)
            Utilities.crypto.changeRememberedMaster(newPassword)
    
    def __showAcceptedLanguages(self):
        """
        Private slot to configure the accepted languages for web pages.
        """
        from .HelpLanguagesDialog import HelpLanguagesDialog
        dlg = HelpLanguagesDialog(self)
        dlg.exec_()
        self.networkAccessManager().languagesChanged()
    
    def __showCookiesConfiguration(self):
        """
        Private slot to configure the cookies handling.
        """
        from .CookieJar.CookiesConfigurationDialog import \
            CookiesConfigurationDialog
        dlg = CookiesConfigurationDialog(self)
        dlg.exec_()
    
    def __showFlashCookiesManagement(self):
        """
        Private slot to show the flash cookies management dialog.
        """
        self.flashCookieManager().showFlashCookieManagerDialog()
    
    def __showOfflineStorageConfiguration(self):
        """
        Private slot to configure the offline storage.
        """
        from .OfflineStorage.OfflineStorageConfigDialog import \
            OfflineStorageConfigDialog
        dlg = OfflineStorageConfigDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            dlg.storeData()
            self.__initWebSettings()
    
    @classmethod
    def setUseQtHelp(cls, use):
        """
        Class method to set the QtHelp usage.
        
        @param use flag indicating usage (boolean)
        """
        if use:
            cls.useQtHelp = use and QTHELP_AVAILABLE
        else:
            cls.useQtHelp = False
    
    @classmethod
    def helpEngine(cls):
        """
        Class method to get a reference to the help engine.
        
        @return reference to the help engine (QHelpEngine)
        """
        if cls.useQtHelp:
            if cls._helpEngine is None:
                cls._helpEngine = \
                    QHelpEngine(os.path.join(Utilities.getConfigDir(),
                                             "browser", "eric6help.qhc"))
            return cls._helpEngine
        else:
            return None
        
    @classmethod
    def networkAccessManager(cls):
        """
        Class method to get a reference to the network access manager.
        
        @return reference to the network access manager (NetworkAccessManager)
        """
        if cls._networkAccessManager is None:
            from .Network.NetworkAccessManager import NetworkAccessManager
            from .CookieJar.CookieJar import CookieJar
            cls._networkAccessManager = \
                NetworkAccessManager(cls.helpEngine())
            cls._cookieJar = CookieJar()
            cls._networkAccessManager.setCookieJar(cls._cookieJar)
        
        return cls._networkAccessManager
        
    @classmethod
    def cookieJar(cls):
        """
        Class method to get a reference to the cookie jar.
        
        @return reference to the cookie jar (CookieJar)
        """
        return cls.networkAccessManager().cookieJar()
        
    def __clearIconsDatabase(self):
        """
        Private slot to clear the icons databse.
        """
        QWebSettings.clearIconDatabase()
        
    @pyqtSlot(QUrl)
    def __linkActivated(self, url):
        """
        Private slot to handle the selection of a link in the TOC window.
        
        @param url URL to be shown (QUrl)
        """
        if not self.__activating:
            self.__activating = True
            req = QNetworkRequest(url)
            req.setRawHeader(b"X-Eric6-UserLoadAction", b"1")
            self.currentBrowser().setSource(
                None, (req, QNetworkAccessManager.GetOperation, b""))
            self.__activating = False
        
    def __linksActivated(self, links, keyword):
        """
        Private slot to select a topic to be shown.
        
        @param links dictionary with help topic as key (string) and
            URL as value (QUrl)
        @param keyword keyword for the link set (string)
        """
        if not self.__activating:
            from .HelpTopicDialog import HelpTopicDialog
            self.__activating = True
            dlg = HelpTopicDialog(self, keyword, links)
            if dlg.exec_() == QDialog.Accepted:
                self.currentBrowser().setSource(dlg.link())
            self.__activating = False
    
    def __activateCurrentBrowser(self):
        """
        Private slot to activate the current browser.
        """
        self.currentBrowser().setFocus()
        
    def __syncTOC(self):
        """
        Private slot to synchronize the TOC with the currently shown page.
        """
        if self.useQtHelp:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            url = self.currentBrowser().source()
            self.__showTocWindow()
            if not self.__tocWindow.syncToContent(url):
                self.statusBar().showMessage(
                    self.tr("Could not find an associated content."), 5000)
            QApplication.restoreOverrideCursor()
        
    def __showTocWindow(self):
        """
        Private method to show the table of contents window.
        """
        if self.useQtHelp:
            self.__activateDock(self.__tocWindow)
        
    def __hideTocWindow(self):
        """
        Private method to hide the table of contents window.
        """
        if self.useQtHelp:
            self.__tocDock.hide()
        
    def __showIndexWindow(self):
        """
        Private method to show the index window.
        """
        if self.useQtHelp:
            self.__activateDock(self.__indexWindow)
        
    def __hideIndexWindow(self):
        """
        Private method to hide the index window.
        """
        if self.useQtHelp:
            self.__indexDock.hide()
        
    def __showSearchWindow(self):
        """
        Private method to show the search window.
        """
        if self.useQtHelp:
            self.__activateDock(self.__searchWindow)
        
    def __hideSearchWindow(self):
        """
        Private method to hide the search window.
        """
        if self.useQtHelp:
            self.__searchDock.hide()
        
    def __activateDock(self, widget):
        """
        Private method to activate the dock widget of the given widget.
        
        @param widget reference to the widget to be activated (QWidget)
        """
        widget.parent().show()
        widget.parent().raise_()
        widget.setFocus()
        
    def __setupFilterCombo(self):
        """
        Private slot to setup the filter combo box.
        """
        if self.useQtHelp:
            curFilter = self.filterCombo.currentText()
            if not curFilter:
                curFilter = self.__helpEngine.currentFilter()
            self.filterCombo.clear()
            self.filterCombo.addItems(self.__helpEngine.customFilters())
            idx = self.filterCombo.findText(curFilter)
            if idx < 0:
                idx = 0
            self.filterCombo.setCurrentIndex(idx)
        
    def __filterQtHelpDocumentation(self, customFilter):
        """
        Private slot to filter the QtHelp documentation.
        
        @param customFilter name of filter to be applied (string)
        """
        if self.__helpEngine:
            self.__helpEngine.setCurrentFilter(customFilter)
        
    def __manageQtHelpDocumentation(self):
        """
        Private slot to manage the QtHelp documentation database.
        """
        if self.useQtHelp:
            from .QtHelpDocumentationDialog import QtHelpDocumentationDialog
            dlg = QtHelpDocumentationDialog(self.__helpEngine, self)
            dlg.exec_()
            if dlg.hasChanges():
                for i in sorted(dlg.getTabsToClose(), reverse=True):
                    self.tabWidget.closeBrowserAt(i)
                self.__helpEngine.setupData()
        
    def getSourceFileList(self):
        """
        Public method to get a list of all opened source files.
        
        @return dictionary with tab id as key and host/namespace as value
        """
        return self.tabWidget.getSourceFileList()
        
    def __manageQtHelpFilters(self):
        """
        Private slot to manage the QtHelp filters.
        """
        if self.useQtHelp:
            from .QtHelpFiltersDialog import QtHelpFiltersDialog
            dlg = QtHelpFiltersDialog(self.__helpEngine, self)
            dlg.exec_()
        
    def __indexingStarted(self):
        """
        Private slot to handle the start of the indexing process.
        """
        if self.useQtHelp:
            self.__indexing = True
            if self.__indexingProgress is None:
                self.__indexingProgress = QWidget()
                layout = QHBoxLayout(self.__indexingProgress)
                layout.setContentsMargins(0, 0, 0, 0)
                sizePolicy = QSizePolicy(QSizePolicy.Preferred,
                                         QSizePolicy.Maximum)
                
                label = QLabel(self.tr("Updating search index"))
                label.setSizePolicy(sizePolicy)
                layout.addWidget(label)
                
                progressBar = QProgressBar()
                progressBar.setRange(0, 0)
                progressBar.setTextVisible(False)
                progressBar.setFixedHeight(16)
                progressBar.setSizePolicy(sizePolicy)
                layout.addWidget(progressBar)
                
                self.statusBar().insertPermanentWidget(
                    0, self.__indexingProgress)
        
    def __indexingFinished(self):
        """
        Private slot to handle the start of the indexing process.
        """
        if self.useQtHelp:
            self.statusBar().removeWidget(self.__indexingProgress)
            self.__indexingProgress = None
            self.__indexing = False
            if self.__searchWord is not None:
                self.__searchForWord()
        
    def __searchForWord(self):
        """
        Private slot to search for a word.
        """
        if self.useQtHelp and not self.__indexing and \
                self.__searchWord is not None:
            self.__searchDock.show()
            self.__searchDock.raise_()
            query = QHelpSearchQuery(QHelpSearchQuery.DEFAULT,
                                     [self.__searchWord])
            self.__searchEngine.search([query])
            self.__searchWord = None
        
    def search(self, word):
        """
        Public method to search for a word.
        
        @param word word to search for (string)
        """
        if self.useQtHelp:
                self.__searchWord = word
                self.__searchForWord()
        
    def __removeOldDocumentation(self):
        """
        Private slot to remove non-existing documentation from the help engine.
        """
        for namespace in self.__helpEngine.registeredDocumentations():
            docFile = self.__helpEngine.documentationFileName(namespace)
            if not os.path.exists(docFile):
                self.__helpEngine.unregisterDocumentation(namespace)
        
    def __lookForNewDocumentation(self):
        """
        Private slot to look for new documentation to be loaded into the
        help database.
        """
        if self.useQtHelp:
            from .HelpDocsInstaller import HelpDocsInstaller
            self.__helpInstaller = HelpDocsInstaller(
                self.__helpEngine.collectionFile())
            self.__helpInstaller.errorMessage.connect(
                self.__showInstallationError)
            self.__helpInstaller.docsInstalled.connect(self.__docsInstalled)
            
            self.statusBar().showMessage(
                self.tr("Looking for Documentation..."))
            self.__helpInstaller.installDocs()
        
    def __showInstallationError(self, message):
        """
        Private slot to show installation errors.
        
        @param message message to be shown (string)
        """
        E5MessageBox.warning(
            self,
            self.tr("eric6 Web Browser"),
            message)
        
    def __docsInstalled(self, installed):
        """
        Private slot handling the end of documentation installation.
        
        @param installed flag indicating that documents were installed
            (boolean)
        """
        if self.useQtHelp:
            if installed:
                self.__helpEngine.setupData()
            self.statusBar().clearMessage()
        
    def __initHelpDb(self):
        """
        Private slot to initialize the documentation database.
        """
        if self.useQtHelp:
            if not self.__helpEngine.setupData():
                return
            
            unfiltered = self.tr("Unfiltered")
            if unfiltered not in self.__helpEngine.customFilters():
                hc = QHelpEngineCore(self.__helpEngine.collectionFile())
                hc.setupData()
                hc.addCustomFilter(unfiltered, [])
                hc = None
                del hc
                
                self.__helpEngine.blockSignals(True)
                self.__helpEngine.setCurrentFilter(unfiltered)
                self.__helpEngine.blockSignals(False)
                self.__helpEngine.setupData()
        
    def __warning(self, msg):
        """
        Private slot handling warnings from the help engine.
        
        @param msg message sent by the help  engine (string)
        """
        E5MessageBox.warning(
            self,
            self.tr("Help Engine"), msg)
        
    def __aboutToShowSettingsMenu(self):
        """
        Private slot to show the Settings menu.
        """
        self.editMessageFilterAct.setEnabled(
            E5ErrorMessage.messageHandlerInstalled())
        
    def __showBackMenu(self):
        """
        Private slot showing the backwards navigation menu.
        """
        self.backMenu.clear()
        history = self.currentBrowser().history()
        historyCount = history.count()
        backItems = history.backItems(historyCount)
        for index in range(len(backItems) - 1, -1, -1):
            item = backItems[index]
            act = QAction(self)
            act.setData(-1 * (index + 1))
            icon = HelpWindow.__getWebIcon(item.url())
            act.setIcon(icon)
            act.setText(item.title())
            self.backMenu.addAction(act)
        
    def __showForwardMenu(self):
        """
        Private slot showing the forwards navigation menu.
        """
        self.forwardMenu.clear()
        history = self.currentBrowser().history()
        historyCount = history.count()
        forwardItems = history.forwardItems(historyCount)
        for index in range(len(forwardItems)):
            item = forwardItems[index]
            act = QAction(self)
            act.setData(index + 1)
            icon = HelpWindow.__getWebIcon(item.url())
            act.setIcon(icon)
            act.setText(item.title())
            self.forwardMenu.addAction(act)
        
    def __navigationMenuActionTriggered(self, act):
        """
        Private slot to go to the selected page.
        
        @param act reference to the action selected in the navigation menu
            (QAction)
        """
        offset = act.data()
        history = self.currentBrowser().history()
        historyCount = history.count()
        if offset < 0:
            # go back
            history.goToItem(history.backItems(historyCount)[-1 * offset - 1])
        else:
            # go forward
            history.goToItem(history.forwardItems(historyCount)[offset - 1])
        
    def __clearPrivateData(self):
        """
        Private slot to clear the private data.
        """
        from .HelpClearPrivateDataDialog import HelpClearPrivateDataDialog
        dlg = HelpClearPrivateDataDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            # browsing history, search history, favicons, disk cache, cookies,
            # passwords, web databases, downloads, Flash cookies
            (history, searches, favicons, cache, cookies,
             passwords, databases, downloads, flashCookies, historyPeriod) = \
                dlg.getData()
            if history:
                self.historyManager().clear(historyPeriod)
                self.tabWidget.clearClosedTabsList()
            if searches:
                self.searchEdit.clear()
            if downloads:
                self.downloadManager().cleanup()
                self.downloadManager().hide()
            if favicons:
                self.__clearIconsDatabase()
            if cache:
                try:
                    self.networkAccessManager().cache().clear()
                except AttributeError:
                    pass
            if cookies:
                self.cookieJar().clear()
            if passwords:
                self.passwordManager().clear()
            if databases:
                if hasattr(QWebDatabase, "removeAllDatabases"):
                    QWebDatabase.removeAllDatabases()
                else:
                    for securityOrigin in QWebSecurityOrigin.allOrigins():
                        for database in securityOrigin.databases():
                            QWebDatabase.removeDatabase(database)
            if flashCookies:
                from .HelpLanguagesDialog import HelpLanguagesDialog
                languages = Preferences.toList(
                    Preferences.Prefs.settings.value(
                        "Help/AcceptLanguages",
                        HelpLanguagesDialog.defaultAcceptLanguages()))
                if languages:
                    language = languages[0]
                    langCode = language.split("[")[1][:2]
                self.newTab(
                    "http://www.macromedia.com/support/documentation/"
                    "{0}/flashplayer/help/settings_manager07.html".format(
                        langCode))
        
    def __showEnginesConfigurationDialog(self):
        """
        Private slot to show the search engines configuration dialog.
        """
        from .OpenSearch.OpenSearchDialog import OpenSearchDialog
        
        dlg = OpenSearchDialog(self)
        dlg.exec_()
        
    def searchEnginesAction(self):
        """
        Public method to get a reference to the search engines configuration
        action.
        
        @return reference to the search engines configuration action (QAction)
        """
        return self.searchEnginesAct
        
    def __showPasswordsDialog(self):
        """
        Private slot to show the passwords management dialog.
        """
        from .Passwords.PasswordsDialog import PasswordsDialog
        
        dlg = PasswordsDialog(self)
        dlg.exec_()
        
    def __showCertificatesDialog(self):
        """
        Private slot to show the certificates management dialog.
        """
        from E5Network.E5SslCertificatesDialog import E5SslCertificatesDialog
        
        dlg = E5SslCertificatesDialog(self)
        dlg.exec_()
        
    def __showAdBlockDialog(self):
        """
        Private slot to show the AdBlock configuration dialog.
        """
        self.adBlockManager().showDialog()
        
    def __showClickToFlashDialog(self):
        """
        Private slot to open the ClickToFlash whitelist configuration dialog.
        """
        from .HelpBrowserWV import HelpWebPage
        HelpWebPage.webPluginFactory().plugin("ClickToFlash").configure()
        
    def __showPersonalInformationDialog(self):
        """
        Private slot to show the Personal Information configuration dialog.
        """
        self.personalInformationManager().showConfigurationDialog()
        
    def __showGreaseMonkeyConfigDialog(self):
        """
        Private slot to show the GreaseMonkey scripts configuration dialog.
        """
        self.greaseMonkeyManager().showConfigurationDialog()
        
    def __showFeaturePermissionDialog(self):
        """
        Private slot to show the feature permission dialog.
        """
        self.featurePermissionManager().showFeaturePermissionsDialog()
        
    def __showNetworkMonitor(self):
        """
        Private slot to show the network monitor dialog.
        """
        from E5Network.E5NetworkMonitor import E5NetworkMonitor
        monitor = E5NetworkMonitor.instance(self.networkAccessManager())
        monitor.show()
        
    def __showDownloadsWindow(self):
        """
        Private slot to show the downloads dialog.
        """
        self.downloadManager().show()
        
    def __closeNetworkMonitor(self):
        """
        Private slot to close the network monitor dialog.
        """
        from E5Network.E5NetworkMonitor import E5NetworkMonitor
        E5NetworkMonitor.closeMonitor()
        
    def __showPageSource(self):
        """
        Private slot to show the source of the current page in  an editor.
        """
        from QScintilla.MiniEditor import MiniEditor
        src = self.currentBrowser().page().mainFrame().toHtml()
        editor = MiniEditor(parent=self)
        editor.setText(src, "Html")
        editor.setLanguage("dummy.html")
        editor.show()
        
    @classmethod
    def icon(cls, url):
        """
        Class method to get the icon for an URL.
        
        @param url URL to get icon for (QUrl)
        @return icon for the URL (QIcon)
        """
        icon = HelpWindow.__getWebIcon(url)
        if icon.isNull():
            hostUrl = QUrl()
            hostUrl.setScheme(url.scheme())
            hostUrl.setHost(url.host())
            icon = HelpWindow.__getWebIcon(hostUrl)
        
        if icon.isNull():
            pixmap = QWebSettings.webGraphic(
                QWebSettings.DefaultFrameIconGraphic)
            if pixmap.isNull():
                pixmap = UI.PixmapCache.getPixmap("defaultIcon.png")
                QWebSettings.setWebGraphic(
                    QWebSettings.DefaultFrameIconGraphic, pixmap)
            return QIcon(pixmap)
        
        return icon

    @staticmethod
    def __getWebIcon(url):
        """
        Private static method to fetch the icon for a URL.
        
        @param url URL to get icon for (QUrl)
        @return icon for the URL (QIcon)
        """
        scheme = url.scheme()
        if scheme in ["eric", "about"]:
            return UI.PixmapCache.getIcon("ericWeb.png")
        elif scheme == "qthelp" and QTHELP_AVAILABLE:
            return UI.PixmapCache.getIcon("qthelp.png")
        elif scheme == "file":
            return UI.PixmapCache.getIcon("fileMisc.png")
        elif scheme == "abp":
            return UI.PixmapCache.getIcon("adBlockPlus.png")
        
        icon = QWebSettings.iconForUrl(url)
        if icon.isNull():
            # try again
            QThread.usleep(10)
            icon = QWebSettings.iconForUrl(url)
        if not icon.isNull():
            icon = QIcon(icon.pixmap(22, 22))
        return icon
        
    @classmethod
    def bookmarksManager(cls):
        """
        Class method to get a reference to the bookmarks manager.
        
        @return reference to the bookmarks manager (BookmarksManager)
        """
        if cls._bookmarksManager is None:
            from .Bookmarks.BookmarksManager import BookmarksManager
            cls._bookmarksManager = BookmarksManager()
        
        return cls._bookmarksManager
        
    def openUrl(self, url, title):
        """
        Public slot to load a URL from the bookmarks menu or bookmarks toolbar
        in the current tab.
        
        @param url url to be opened (QUrl)
        @param title title of the bookmark (string)
        """
        self.__linkActivated(url)
        
    def openUrlNewTab(self, url, title):
        """
        Public slot to load a URL from the bookmarks menu or bookmarks toolbar
        in a new tab.
        
        @param url url to be opened (QUrl)
        @param title title of the bookmark (string)
        """
        req = QNetworkRequest(url)
        req.setRawHeader(b"X-Eric6-UserLoadAction", b"1")
        self.newTab(None, (req, QNetworkAccessManager.GetOperation, b""))
        
    @classmethod
    def historyManager(cls):
        """
        Class method to get a reference to the history manager.
        
        @return reference to the history manager (HistoryManager)
        """
        if cls._historyManager is None:
            from .History.HistoryManager import HistoryManager
            cls._historyManager = HistoryManager()
        
        return cls._historyManager
        
    @classmethod
    def passwordManager(cls):
        """
        Class method to get a reference to the password manager.
        
        @return reference to the password manager (PasswordManager)
        """
        if cls._passwordManager is None:
            from .Passwords.PasswordManager import PasswordManager
            cls._passwordManager = PasswordManager()
        
        return cls._passwordManager
        
    @classmethod
    def adBlockManager(cls):
        """
        Class method to get a reference to the AdBlock manager.
        
        @return reference to the AdBlock manager (AdBlockManager)
        """
        if cls._adblockManager is None:
            from .AdBlock.AdBlockManager import AdBlockManager
            cls._adblockManager = AdBlockManager()
        
        return cls._adblockManager
    
    def adBlockIcon(self):
        """
        Public method to get a reference to the AdBlock icon.
        
        @return reference to the AdBlock icon (AdBlockIcon)
        """
        return self.__adBlockIcon
    
    @classmethod
    def downloadManager(cls):
        """
        Class method to get a reference to the download manager.
        
        @return reference to the password manager (DownloadManager)
        """
        if cls._downloadManager is None:
            from .Download.DownloadManager import DownloadManager
            cls._downloadManager = DownloadManager()
        
        return cls._downloadManager
        
    @classmethod
    def personalInformationManager(cls):
        """
        Class method to get a reference to the personal information manager.
        
        @return reference to the personal information manager
            (PersonalInformationManager)
        """
        if cls._personalInformationManager is None:
            from .PersonalInformationManager.PersonalInformationManager \
                import PersonalInformationManager
            cls._personalInformationManager = PersonalInformationManager()
        
        return cls._personalInformationManager
        
    @classmethod
    def greaseMonkeyManager(cls):
        """
        Class method to get a reference to the GreaseMonkey manager.
        
        @return reference to the GreaseMonkey manager (GreaseMonkeyManager)
        """
        if cls._greaseMonkeyManager is None:
            from .GreaseMonkey.GreaseMonkeyManager import GreaseMonkeyManager
            cls._greaseMonkeyManager = GreaseMonkeyManager()
        
        return cls._greaseMonkeyManager
        
    @classmethod
    def featurePermissionManager(cls):
        """
        Class method to get a reference to the feature permission manager.
        
        @return reference to the feature permission manager
        @rtype FeaturePermissionManager
        """
        if cls._featurePermissionManager is None:
            from .FeaturePermissions.FeaturePermissionManager import \
                FeaturePermissionManager
            cls._featurePermissionManager = FeaturePermissionManager()
        
        return cls._featurePermissionManager
        
    @classmethod
    def flashCookieManager(cls):
        """
        Class method to get a reference to the flash cookies manager.
        
        @return reference to the feature permission manager
        @rtype FlashCookieManager
        """
        if cls._flashCookieManager is None:
            from .FlashCookieManager.FlashCookieManager import \
                FlashCookieManager
            cls._flashCookieManager = FlashCookieManager()
        
        return cls._flashCookieManager
        
    @classmethod
    def mainWindow(cls):
        """
        Class method to get a reference to the main window.
        
        @return reference to the main window (HelpWindow)
        """
        if cls.helpwindows:
            return cls.helpwindows[0]
        else:
            return None
        
    @classmethod
    def mainWindows(cls):
        """
        Class method to get references to all main windows.
        
        @return references to all main window (list of HelpWindow)
        """
        return cls.helpwindows
        
    def __appFocusChanged(self, old, now):
        """
        Private slot to handle a change of the focus.
        
        @param old reference to the widget, that lost focus (QWidget or None)
        @param now reference to the widget having the focus (QWidget or None)
        """
        if isinstance(now, HelpWindow):
            self.__lastActiveWindow = now
        
    def getWindow(self):
        """
        Public method to get a reference to the most recent active help window.
        
        @return reference to most recent help window
        @rtype HelpWindow
        """
        if self.__lastActiveWindow:
            return self.__lastActiveWindow
        
        return self.mainWindow()
        
    def openSearchManager(self):
        """
        Public method to get a reference to the opensearch manager object.
        
        @return reference to the opensearch manager object (OpenSearchManager)
        """
        return self.searchEdit.openSearchManager()
    
    def __aboutToShowTextEncodingMenu(self):
        """
        Private slot to populate the text encoding menu.
        """
        self.__textEncodingMenu.clear()
        
        codecs = []
        for codec in QTextCodec.availableCodecs():
            codecs.append(str(codec, encoding="utf-8").lower())
        codecs.sort()
        
        defaultTextEncoding = \
            QWebSettings.globalSettings().defaultTextEncoding().lower()
        if defaultTextEncoding in codecs:
            currentCodec = defaultTextEncoding
        else:
            currentCodec = ""
        
        isDefaultEncodingUsed = True
        isoMenu = QMenu(self.tr("ISO"), self.__textEncodingMenu)
        winMenu = QMenu(self.tr("Windows"), self.__textEncodingMenu)
        isciiMenu = QMenu(self.tr("ISCII"), self.__textEncodingMenu)
        uniMenu = QMenu(self.tr("Unicode"), self.__textEncodingMenu)
        otherMenu = QMenu(self.tr("Other"), self.__textEncodingMenu)
        ibmMenu = QMenu(self.tr("IBM"), self.__textEncodingMenu)
        
        for codec in codecs:
            if codec.startswith(("iso", "latin", "csisolatin")):
                act = isoMenu.addAction(codec)
            elif codec.startswith(("windows", "cp1")):
                act = winMenu.addAction(codec)
            elif codec.startswith("iscii"):
                act = isciiMenu.addAction(codec)
            elif codec.startswith("utf"):
                act = uniMenu.addAction(codec)
            elif codec.startswith(("ibm", "csibm", "cp")):
                act = ibmMenu.addAction(codec)
            else:
                act = otherMenu.addAction(codec)
            
            act.setData(codec)
            act.setCheckable(True)
            if currentCodec == codec:
                act.setChecked(True)
                isDefaultEncodingUsed = False
        
        act = self.__textEncodingMenu.addAction(
            self.tr("Default Encoding"))
        act.setData("")
        act.setCheckable(True)
        act.setChecked(isDefaultEncodingUsed)
        self.__textEncodingMenu.addMenu(uniMenu)
        self.__textEncodingMenu.addMenu(isoMenu)
        self.__textEncodingMenu.addMenu(winMenu)
        self.__textEncodingMenu.addMenu(ibmMenu)
        self.__textEncodingMenu.addMenu(isciiMenu)
        self.__textEncodingMenu.addMenu(otherMenu)
    
    def __setTextEncoding(self, act):
        """
        Private slot to set the selected text encoding as the default for
        this session.
        
        @param act reference to the selected action (QAction)
        """
        codec = act.data()
        if codec == "":
            QWebSettings.globalSettings().setDefaultTextEncoding("")
        else:
            QWebSettings.globalSettings().setDefaultTextEncoding(codec)
    
    def eventMouseButtons(self):
        """
        Public method to get the last recorded mouse buttons.
        
        @return mouse buttons (Qt.MouseButtons)
        """
        return self.__eventMouseButtons
    
    def eventKeyboardModifiers(self):
        """
        Public method to get the last recorded keyboard modifiers.
        
        @return keyboard modifiers (Qt.KeyboardModifiers)
        """
        return self.__eventKeyboardModifiers
    
    def setEventMouseButtons(self, buttons):
        """
        Public method to record mouse buttons.
        
        @param buttons mouse buttons to record (Qt.MouseButtons)
        """
        self.__eventMouseButtons = buttons
    
    def setEventKeyboardModifiers(self, modifiers):
        """
        Public method to record keyboard modifiers.
        
        @param modifiers keyboard modifiers to record (Qt.KeyboardModifiers)
        """
        self.__eventKeyboardModifiers = modifiers
    
    def mousePressEvent(self, evt):
        """
        Protected method called by a mouse press event.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        if evt.button() == Qt.XButton1:
            self.currentBrowser().pageAction(QWebPage.Back).trigger()
        elif evt.button() == Qt.XButton2:
            self.currentBrowser().pageAction(QWebPage.Forward).trigger()
        else:
            super(HelpWindow, self).mousePressEvent(evt)

    @classmethod
    def feedsManager(cls):
        """
        Class method to get a reference to the RSS feeds manager.
        
        @return reference to the RSS feeds manager (FeedsManager)
        """
        if cls._feedsManager is None:
            from .Feeds.FeedsManager import FeedsManager
            cls._feedsManager = FeedsManager()
        
        return cls._feedsManager
    
    def __showFeedsManager(self):
        """
        Private slot to show the feeds manager dialog.
        """
        feedsManager = self.feedsManager()
        feedsManager.openUrl.connect(self.openUrl)
        feedsManager.newUrl.connect(self.openUrlNewTab)
        feedsManager.rejected.connect(self.__feedsManagerClosed)
        feedsManager.show()
    
    def __feedsManagerClosed(self):
        """
        Private slot to handle closing the feeds manager dialog.
        """
        feedsManager = self.sender()
        feedsManager.openUrl.disconnect(self.openUrl)
        feedsManager.newUrl.disconnect(self.openUrlNewTab)
        feedsManager.rejected.disconnect(self.__feedsManagerClosed)
    
    def __showSiteinfoDialog(self):
        """
        Private slot to show the site info dialog.
        """
        from .SiteInfo.SiteInfoDialog import SiteInfoDialog
        self.__siteinfoDialog = SiteInfoDialog(self.currentBrowser(), self)
        self.__siteinfoDialog.show()

    @classmethod
    def userAgentsManager(cls):
        """
        Class method to get a reference to the user agents manager.
        
        @return reference to the user agents manager (UserAgentManager)
        """
        if cls._userAgentsManager is None:
            from .UserAgent.UserAgentManager import UserAgentManager
            cls._userAgentsManager = UserAgentManager()
        
        return cls._userAgentsManager
    
    def __showUserAgentsDialog(self):
        """
        Private slot to show the user agents management dialog.
        """
        from .UserAgent.UserAgentsDialog import UserAgentsDialog
        
        dlg = UserAgentsDialog(self)
        dlg.exec_()
    
    @classmethod
    def syncManager(cls):
        """
        Class method to get a reference to the data synchronization manager.
        
        @return reference to the data synchronization manager (SyncManager)
        """
        if cls._syncManager is None:
            from .Sync.SyncManager import SyncManager
            cls._syncManager = SyncManager()
        
        return cls._syncManager
    
    def __showSyncDialog(self):
        """
        Private slot to show the synchronization dialog.
        """
        self.syncManager().showSyncDialog()
    
    @classmethod
    def speedDial(cls):
        """
        Class methdo to get a reference to the speed dial.
        
        @return reference to the speed dial (SpeedDial)
        """
        if cls._speedDial is None:
            from .SpeedDial.SpeedDial import SpeedDial
            cls._speedDial = SpeedDial()
        
        return cls._speedDial
    
    def keyPressEvent(self, evt):
        """
        Protected method to handle key presses.
        
        @param evt reference to the key press event (QKeyEvent)
        """
        number = -1
        key = evt.key()
        
        if key == Qt.Key_1:
            number = 1
        elif key == Qt.Key_2:
            number = 2
        elif key == Qt.Key_3:
            number = 3
        elif key == Qt.Key_4:
            number = 4
        elif key == Qt.Key_5:
            number = 5
        elif key == Qt.Key_6:
            number = 6
        elif key == Qt.Key_7:
            number = 7
        elif key == Qt.Key_8:
            number = 8
        elif key == Qt.Key_9:
            number = 9
        elif key == Qt.Key_0:
            number = 10
        
        if number != -1:
            if evt.modifiers() == Qt.KeyboardModifiers(Qt.AltModifier):
                if number == 10:
                    number = self.tabWidget.count()
                self.tabWidget.setCurrentIndex(number - 1)
                return
            
            if evt.modifiers() == Qt.KeyboardModifiers(Qt.MetaModifier):
                url = self.speedDial().urlForShortcut(number - 1)
                if url.isValid():
                    self.__linkActivated(url)
                    return
        
        super(HelpWindow, self).keyPressEvent(evt)
    
    ###########################################################################
    ## Interface to VirusTotal below                                         ##
    ###########################################################################
    
    def __virusTotalScanCurrentSite(self):
        """
        Private slot to ask VirusTotal for a scan of the URL of the current
        browser.
        """
        cb = self.currentBrowser()
        if cb is not None:
            url = cb.url()
            if url.scheme() in ["http", "https", "ftp"]:
                self.requestVirusTotalScan(url)
    
    def requestVirusTotalScan(self, url):
        """
        Public method to submit a request to scan an URL by VirusTotal.
        
        @param url URL to be scanned (QUrl)
        """
        self.__virusTotal.submitUrl(url)
    
    def __virusTotalSubmitUrlError(self, msg):
        """
        Private slot to handle an URL scan submission error.
        
        @param msg error message (str)
        """
        E5MessageBox.critical(
            self,
            self.tr("VirusTotal Scan"),
            self.tr("""<p>The VirusTotal scan could not be"""
                    """ scheduled.<p>\n<p>Reason: {0}</p>""").format(msg))
    
    def __virusTotalUrlScanReport(self, url):
        """
        Private slot to initiate the display of the URL scan report page.
        
        @param url URL of the URL scan report page (string)
        """
        self.newTab(url)
    
    def __virusTotalFileScanReport(self, url):
        """
        Private slot to initiate the display of the file scan report page.
        
        @param url URL of the file scan report page (string)
        """
        self.newTab(url)
    
    def __virusTotalIpAddressReport(self):
        """
        Private slot to retrieve an IP address report.
        """
        ip, ok = QInputDialog.getText(
            self,
            self.tr("IP Address Report"),
            self.tr("Enter a valid IPv4 address in dotted quad notation:"),
            QLineEdit.Normal)
        if ok and ip:
            if ip.count(".") == 3:
                self.__virusTotal.getIpAddressReport(ip)
            else:
                E5MessageBox.information(
                    self,
                    self.tr("IP Address Report"),
                    self.tr("""The given IP address is not in dotted quad"""
                            """ notation."""))
    
    def __virusTotalDomainReport(self):
        """
        Private slot to retrieve a domain report.
        """
        domain, ok = QInputDialog.getText(
            self,
            self.tr("Domain Report"),
            self.tr("Enter a valid domain name:"),
            QLineEdit.Normal)
        if ok and domain:
            self.__virusTotal.getDomainReport(domain)
    
    ###########################################################################
    ## Style sheet handling below                                            ##
    ###########################################################################
    
    def reloadUserStyleSheet(self):
        """
        Public method to reload the user style sheet.
        """
        settings = QWebSettings.globalSettings()
        styleSheet = Preferences.getHelp("UserStyleSheet")
        settings.setUserStyleSheetUrl(self.__userStyleSheet(styleSheet))
    
    def __userStyleSheet(self, styleSheetFile):
        """
        Private method to generate the user style sheet.
        
        @param styleSheetFile name of the user style sheet file (string)
        @return style sheet (QUrl)
        """
        userStyle = self.adBlockManager().elementHidingRules() + \
            "{display:none !important;}"
        
        if styleSheetFile:
            try:
                f = open(styleSheetFile, "r")
                fileData = f.read()
                f.close()
                fileData = fileData.replace("\n", "")
                userStyle += fileData
            except IOError:
                pass
        
        encodedStyle = bytes(QByteArray(userStyle.encode("utf-8")).toBase64())\
            .decode()
        dataString = "data:text/css;charset=utf-8;base64,{0}".format(
            encodedStyle)
        
        return QUrl(dataString)
    
    ##########################################
    ## Support for desktop notifications below
    ##########################################
    
    @classmethod
    def showNotification(cls, icon, heading, text):
        """
        Class method to show a desktop notification.
        
        @param icon icon to be shown in the notification (QPixmap)
        @param heading heading of the notification (string)
        @param text text of the notification (string)
        """
        if cls._fromEric:
            e5App().getObject("UserInterface").showNotification(
                icon, heading, text)
        else:
            if Preferences.getUI("NotificationsEnabled"):
                if cls._notification is None:
                    from UI.NotificationWidget import NotificationWidget
                    cls._notification = NotificationWidget()
                cls._notification.setPixmap(icon)
                cls._notification.setHeading(heading)
                cls._notification.setText(text)
                cls._notification.setTimeout(
                    Preferences.getUI("NotificationTimeout"))
                cls._notification.move(
                    Preferences.getUI("NotificationPosition"))
                cls._notification.show()
    
    @classmethod
    def notificationsEnabled(cls):
        """
        Class method to check, if notifications are enabled.
        
        @return flag indicating, if notifications are enabled (boolean)
        """
        if cls._fromEric:
            return e5App().getObject("UserInterface").notificationsEnabled()
        else:
            return Preferences.getUI("NotificationsEnabled")
