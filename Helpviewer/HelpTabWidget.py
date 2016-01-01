# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the central widget showing the web pages.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QMenu, QToolButton, QDialog
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest

from E5Gui.E5TabWidget import E5TabWidget
from E5Gui import E5MessageBox
from E5Gui.E5Application import e5App

from .HelpBrowserWV import HelpBrowser

import UI.PixmapCache

import Utilities
import Preferences

from eric6config import getConfig


class HelpTabWidget(E5TabWidget):
    """
    Class implementing the central widget showing the web pages.
    
    @signal sourceChanged(HelpBrowser, QUrl) emitted after the URL of a browser
        has changed
    @signal titleChanged(HelpBrowser, str) emitted after the title of a browser
        has changed
    @signal showMessage(str) emitted to show a message in the main window
        status bar
    @signal browserClosed(QWidget) emitted after a browser was closed
    @signal browserZoomValueChanged(int) emitted to signal a change of the
        current browser's zoom level
    """
    sourceChanged = pyqtSignal(HelpBrowser, QUrl)
    titleChanged = pyqtSignal(HelpBrowser, str)
    showMessage = pyqtSignal(str)
    browserClosed = pyqtSignal(QWidget)
    browserZoomValueChanged = pyqtSignal(int)
    
    def __init__(self, parent):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        E5TabWidget.__init__(self, parent, dnd=True)
        
        from .HelpTabBar import HelpTabBar
        self.__tabBar = HelpTabBar(self)
        self.setCustomTabBar(True, self.__tabBar)
        
        self.__mainWindow = parent
        
        self.setUsesScrollButtons(True)
        self.setDocumentMode(True)
        self.setElideMode(Qt.ElideNone)
        
        from .ClosedTabsManager import ClosedTabsManager
        self.__closedTabsManager = ClosedTabsManager(self)
        self.__closedTabsManager.closedTabAvailable.connect(
            self.__closedTabAvailable)
        
        from .UrlBar.StackedUrlBar import StackedUrlBar
        self.__stackedUrlBar = StackedUrlBar(self)
        self.__tabBar.tabMoved.connect(self.__stackedUrlBar.moveBar)
        
        self.__tabContextMenuIndex = -1
        self.currentChanged[int].connect(self.__currentChanged)
        self.setTabContextMenuPolicy(Qt.CustomContextMenu)
        self.customTabContextMenuRequested.connect(self.__showContextMenu)
        
        self.__rightCornerWidget = QWidget(self)
        self.__rightCornerWidgetLayout = QHBoxLayout(self.__rightCornerWidget)
        self.__rightCornerWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.__rightCornerWidgetLayout.setSpacing(0)
        
        self.__navigationMenu = QMenu(self)
        self.__navigationMenu.aboutToShow.connect(self.__showNavigationMenu)
        self.__navigationMenu.triggered.connect(self.__navigationMenuTriggered)
        
        self.__navigationButton = QToolButton(self)
        self.__navigationButton.setIcon(
            UI.PixmapCache.getIcon("1downarrow.png"))
        self.__navigationButton.setToolTip(
            self.tr("Show a navigation menu"))
        self.__navigationButton.setPopupMode(QToolButton.InstantPopup)
        self.__navigationButton.setMenu(self.__navigationMenu)
        self.__navigationButton.setEnabled(False)
        self.__rightCornerWidgetLayout.addWidget(self.__navigationButton)
        
        self.__closedTabsMenu = QMenu(self)
        self.__closedTabsMenu.aboutToShow.connect(
            self.__aboutToShowClosedTabsMenu)
        
        self.__closedTabsButton = QToolButton(self)
        self.__closedTabsButton.setIcon(UI.PixmapCache.getIcon("trash.png"))
        self.__closedTabsButton.setToolTip(
            self.tr("Show a navigation menu for closed tabs"))
        self.__closedTabsButton.setPopupMode(QToolButton.InstantPopup)
        self.__closedTabsButton.setMenu(self.__closedTabsMenu)
        self.__closedTabsButton.setEnabled(False)
        self.__rightCornerWidgetLayout.addWidget(self.__closedTabsButton)
        
        self.__closeButton = QToolButton(self)
        self.__closeButton.setIcon(UI.PixmapCache.getIcon("close.png"))
        self.__closeButton.setToolTip(
            self.tr("Close the current help window"))
        self.__closeButton.setEnabled(False)
        self.__closeButton.clicked[bool].connect(self.closeBrowser)
        self.__rightCornerWidgetLayout.addWidget(self.__closeButton)
        if Preferences.getUI("SingleCloseButton") or \
           not hasattr(self, 'setTabsClosable'):
            self.__closeButton.show()
        else:
            self.setTabsClosable(True)
            self.tabCloseRequested.connect(self.closeBrowserAt)
            self.__closeButton.hide()
        
        self.setCornerWidget(self.__rightCornerWidget, Qt.TopRightCorner)
        
        self.__newTabButton = QToolButton(self)
        self.__newTabButton.setIcon(UI.PixmapCache.getIcon("plus.png"))
        self.__newTabButton.setToolTip(
            self.tr("Open a new help window tab"))
        self.setCornerWidget(self.__newTabButton, Qt.TopLeftCorner)
        self.__newTabButton.clicked[bool].connect(self.newBrowser)
        
        self.__initTabContextMenu()
        
        self.__historyCompleter = None
    
    def __initTabContextMenu(self):
        """
        Private method to create the tab context menu.
        """
        self.__tabContextMenu = QMenu(self)
        self.tabContextNewAct = self.__tabContextMenu.addAction(
            UI.PixmapCache.getIcon("tabNew.png"),
            self.tr('New Tab'), self.newBrowser)
        self.__tabContextMenu.addSeparator()
        self.leftMenuAct = self.__tabContextMenu.addAction(
            UI.PixmapCache.getIcon("1leftarrow.png"),
            self.tr('Move Left'), self.__tabContextMenuMoveLeft)
        self.rightMenuAct = self.__tabContextMenu.addAction(
            UI.PixmapCache.getIcon("1rightarrow.png"),
            self.tr('Move Right'), self.__tabContextMenuMoveRight)
        self.__tabContextMenu.addSeparator()
        self.tabContextCloneAct = self.__tabContextMenu.addAction(
            self.tr("Duplicate Page"), self.__tabContextMenuClone)
        self.__tabContextMenu.addSeparator()
        self.tabContextCloseAct = self.__tabContextMenu.addAction(
            UI.PixmapCache.getIcon("tabClose.png"),
            self.tr('Close'), self.__tabContextMenuClose)
        self.tabContextCloseOthersAct = self.__tabContextMenu.addAction(
            UI.PixmapCache.getIcon("tabCloseOther.png"),
            self.tr("Close Others"), self.__tabContextMenuCloseOthers)
        self.__tabContextMenu.addAction(
            self.tr('Close All'), self.closeAllBrowsers)
        self.__tabContextMenu.addSeparator()
        self.__tabContextMenu.addAction(
            UI.PixmapCache.getIcon("printPreview.png"),
            self.tr('Print Preview'), self.__tabContextMenuPrintPreview)
        self.__tabContextMenu.addAction(
            UI.PixmapCache.getIcon("print.png"),
            self.tr('Print'), self.__tabContextMenuPrint)
        self.__tabContextMenu.addAction(
            UI.PixmapCache.getIcon("printPdf.png"),
            self.tr('Print as PDF'), self.__tabContextMenuPrintPdf)
        self.__tabContextMenu.addSeparator()
        self.__tabContextMenu.addAction(
            UI.PixmapCache.getIcon("reload.png"),
            self.tr('Reload All'), self.reloadAllBrowsers)
        self.__tabContextMenu.addSeparator()
        self.__tabContextMenu.addAction(
            UI.PixmapCache.getIcon("addBookmark.png"),
            self.tr('Bookmark All Tabs'), self.__mainWindow.bookmarkAll)
        
        self.__tabBackContextMenu = QMenu(self)
        self.__tabBackContextMenu.addAction(
            self.tr('Close All'), self.closeAllBrowsers)
        self.__tabBackContextMenu.addAction(
            UI.PixmapCache.getIcon("reload.png"),
            self.tr('Reload All'), self.reloadAllBrowsers)
        self.__tabBackContextMenu.addAction(
            UI.PixmapCache.getIcon("addBookmark.png"),
            self.tr('Bookmark All Tabs'), self.__mainWindow.bookmarkAll)
        self.__tabBackContextMenu.addSeparator()
        self.__restoreClosedTabAct = self.__tabBackContextMenu.addAction(
            UI.PixmapCache.getIcon("trash.png"),
            self.tr('Restore Closed Tab'), self.restoreClosedTab)
        self.__restoreClosedTabAct.setEnabled(False)
        self.__restoreClosedTabAct.setData(0)
    
    def __showContextMenu(self, coord, index):
        """
        Private slot to show the tab context menu.
        
        @param coord the position of the mouse pointer (QPoint)
        @param index index of the tab the menu is requested for (integer)
        """
        coord = self.mapToGlobal(coord)
        if index == -1:
            self.__tabBackContextMenu.popup(coord)
        else:
            self.__tabContextMenuIndex = index
            self.leftMenuAct.setEnabled(index > 0)
            self.rightMenuAct.setEnabled(index < self.count() - 1)
            
            self.tabContextCloseOthersAct.setEnabled(self.count() > 1)
            
            self.__tabContextMenu.popup(coord)
    
    def __tabContextMenuMoveLeft(self):
        """
        Private method to move a tab one position to the left.
        """
        self.moveTab(self.__tabContextMenuIndex,
                     self.__tabContextMenuIndex - 1)
    
    def __tabContextMenuMoveRight(self):
        """
        Private method to move a tab one position to the right.
        """
        self.moveTab(self.__tabContextMenuIndex,
                     self.__tabContextMenuIndex + 1)
    
    def __tabContextMenuClone(self):
        """
        Private method to clone the selected tab.
        """
        idx = self.__tabContextMenuIndex
        if idx < 0:
            idx = self.currentIndex()
        if idx < 0 or idx > self.count():
            return
        
        req = QNetworkRequest(self.widget(idx).url())
        req.setRawHeader(b"X-Eric6-UserLoadAction", b"1")
        self.newBrowser(None, (req, QNetworkAccessManager.GetOperation, b""))
    
    def __tabContextMenuClose(self):
        """
        Private method to close the selected tab.
        """
        self.closeBrowserAt(self.__tabContextMenuIndex)
    
    def __tabContextMenuCloseOthers(self):
        """
        Private slot to close all other tabs.
        """
        index = self.__tabContextMenuIndex
        for i in list(range(self.count() - 1, index, -1)) + \
                list(range(index - 1, -1, -1)):
            self.closeBrowserAt(i)
    
    def __tabContextMenuPrint(self):
        """
        Private method to print the selected tab.
        """
        browser = self.widget(self.__tabContextMenuIndex)
        self.printBrowser(browser)
    
    def __tabContextMenuPrintPdf(self):
        """
        Private method to print the selected tab as PDF.
        """
        browser = self.widget(self.__tabContextMenuIndex)
        self.printBrowserPdf(browser)
    
    def __tabContextMenuPrintPreview(self):
        """
        Private method to show a print preview of the selected tab.
        """
        browser = self.widget(self.__tabContextMenuIndex)
        self.printPreviewBrowser(browser)
    
    def newBrowser(self, link=None, requestData=None, position=-1):
        """
        Public method to create a new web browser tab.
        
        @param link link to be shown (string or QUrl)
        @param requestData tuple containing the request data (QNetworkRequest,
            QNetworkAccessManager.Operation, QByteArray)
        @keyparam position position to create the new tab at or -1 to add it
            to the end (integer)
        """
        if link is None:
            linkName = ""
        elif isinstance(link, QUrl):
            linkName = link.toString()
        else:
            linkName = link
        
        from .UrlBar.UrlBar import UrlBar
        urlbar = UrlBar(self.__mainWindow, self)
        if self.__historyCompleter is None:
            import Helpviewer.HelpWindow
            from .History.HistoryCompleter import HistoryCompletionModel, \
                HistoryCompleter
            self.__historyCompletionModel = HistoryCompletionModel(self)
            self.__historyCompletionModel.setSourceModel(
                Helpviewer.HelpWindow.HelpWindow.historyManager()
                .historyFilterModel())
            self.__historyCompleter = HistoryCompleter(
                self.__historyCompletionModel, self)
            self.__historyCompleter.activated[str].connect(self.__pathSelected)
        urlbar.setCompleter(self.__historyCompleter)
        urlbar.returnPressed.connect(self.__lineEditReturnPressed)
        if position == -1:
            self.__stackedUrlBar.addWidget(urlbar)
        else:
            self.__stackedUrlBar.insertWidget(position, urlbar)
        
        browser = HelpBrowser(self.__mainWindow, self)
        urlbar.setBrowser(browser)
        
        browser.sourceChanged.connect(self.__sourceChanged)
        browser.titleChanged.connect(self.__titleChanged)
        browser.highlighted.connect(self.showMessage)
        browser.backwardAvailable.connect(
            self.__mainWindow.setBackwardAvailable)
        browser.forwardAvailable.connect(self.__mainWindow.setForwardAvailable)
        browser.loadStarted.connect(self.__loadStarted)
        browser.loadFinished.connect(self.__loadFinished)
        browser.iconChanged.connect(self.__iconChanged)
        browser.search.connect(self.newBrowser)
        browser.page().windowCloseRequested.connect(
            self.__windowCloseRequested)
        browser.page().printRequested.connect(self.__printRequested)
        browser.zoomValueChanged.connect(self.browserZoomValueChanged)
        
        if position == -1:
            index = self.addTab(browser, self.tr("..."))
        else:
            index = self.insertTab(position, browser, self.tr("..."))
        self.setCurrentIndex(index)
        
        self.__mainWindow.closeAct.setEnabled(True)
        self.__mainWindow.closeAllAct.setEnabled(True)
        self.__closeButton.setEnabled(True)
        self.__navigationButton.setEnabled(True)
        
        if not linkName and not requestData:
            if Preferences.getHelp("StartupBehavior") == 0:
                linkName = Preferences.getHelp("HomePage")
            elif Preferences.getHelp("StartupBehavior") == 1:
                linkName = "eric:speeddial"
        
        if linkName:
            browser.setSource(QUrl(linkName))
            if not browser.documentTitle():
                self.setTabText(index, self.__elide(linkName, Qt.ElideMiddle))
                self.setTabToolTip(index, linkName)
            else:
                self.setTabText(
                    index,
                    self.__elide(browser.documentTitle().replace("&", "&&")))
                self.setTabToolTip(index, browser.documentTitle())
        elif requestData:
            browser.load(*requestData)
    
    def newBrowserAfter(self, browser, link=None, requestData=None):
        """
        Public method to create a new web browser tab after a given one.
        
        @param browser reference to the browser to add after (HelpBrowser)
        @param link link to be shown (string or QUrl)
        @param requestData tuple containing the request data (QNetworkRequest,
            QNetworkAccessManager.Operation, QByteArray)
        """
        if browser:
            position = self.indexOf(browser) + 1
        else:
            position = -1
        self.newBrowser(link, requestData, position)
    
    def __showNavigationMenu(self):
        """
        Private slot to show the navigation button menu.
        """
        self.__navigationMenu.clear()
        for index in range(self.count()):
            act = self.__navigationMenu.addAction(
                self.tabIcon(index), self.tabText(index))
            act.setData(index)
    
    def __navigationMenuTriggered(self, act):
        """
        Private slot called to handle the navigation button menu selection.
        
        @param act reference to the selected action (QAction)
        """
        index = act.data()
        if index is not None:
            self.setCurrentIndex(index)
    
    def __windowCloseRequested(self):
        """
        Private slot to handle the windowCloseRequested signal of a browser.
        """
        page = self.sender()
        if page is None:
            return
        
        browser = page.view()
        if browser is None:
            return
        
        index = self.indexOf(browser)
        self.closeBrowserAt(index)
    
    def reloadAllBrowsers(self):
        """
        Public slot to reload all browsers.
        """
        for index in range(self.count()):
            browser = self.widget(index)
            browser and browser.reload()
    
    def closeBrowser(self):
        """
        Public slot called to handle the close action.
        """
        self.closeBrowserAt(self.currentIndex())
    
    def closeAllBrowsers(self):
        """
        Public slot called to handle the close all action.
        """
        for index in range(self.count() - 1, -1, -1):
            self.closeBrowserAt(index)
    
    def closeBrowserAt(self, index):
        """
        Public slot to close a browser based on its index.
        
        @param index index of browser to close (integer)
        """
        browser = self.widget(index)
        if browser is None:
            return
        
        if browser.isModified():
            ok = E5MessageBox.yesNo(
                self,
                self.tr("Do you really want to close this page?"),
                self.tr("""You have modified this page and when closing it"""
                        """ you would lose the modification.\nDo you really"""
                        """ want to close this page?"""))
            if not ok:
                return
        
        urlbar = self.__stackedUrlBar.widget(index)
        self.__stackedUrlBar.removeWidget(urlbar)
        urlbar.deleteLater()
        del urlbar
        
        self.__closedTabsManager.recordBrowser(browser, index)
        
        browser.closeWebInspector()
        browser.home()
        self.removeTab(index)
        self.browserClosed.emit(browser)
        browser.deleteLater()
        del browser
        
        if self.count() == 0:
            self.newBrowser()
        else:
            self.currentChanged[int].emit(self.currentIndex())
    
    def currentBrowser(self):
        """
        Public method to get a reference to the current browser.
        
        @return reference to the current browser (HelpBrowser)
        """
        return self.currentWidget()
    
    def browserAt(self, index):
        """
        Public method to get a reference to the browser with the given index.
        
        @param index index of the browser to get (integer)
        @return reference to the indexed browser (HelpBrowser)
        """
        return self.widget(index)
    
    def browsers(self):
        """
        Public method to get a list of references to all browsers.
        
        @return list of references to browsers (list of HelpBrowser)
        """
        li = []
        for index in range(self.count()):
            li.append(self.widget(index))
        return li
    
    @pyqtSlot()
    def printBrowser(self, browser=None):
        """
        Public slot called to print the displayed page.
        
        @param browser reference to the browser to be printed (HelpBrowser)
        """
        if browser is None:
            browser = self.currentBrowser()
        
        self.__printRequested(browser.page().mainFrame())
    
    def __printRequested(self, frame):
        """
        Private slot to handle a print request.
        
        @param frame reference to the frame to be printed (QWebFrame)
        """
        printer = QPrinter(mode=QPrinter.HighResolution)
        if Preferences.getPrinter("ColorMode"):
            printer.setColorMode(QPrinter.Color)
        else:
            printer.setColorMode(QPrinter.GrayScale)
        if Preferences.getPrinter("FirstPageFirst"):
            printer.setPageOrder(QPrinter.FirstPageFirst)
        else:
            printer.setPageOrder(QPrinter.LastPageFirst)
        printer.setPageMargins(
            Preferences.getPrinter("LeftMargin") * 10,
            Preferences.getPrinter("TopMargin") * 10,
            Preferences.getPrinter("RightMargin") * 10,
            Preferences.getPrinter("BottomMargin") * 10,
            QPrinter.Millimeter
        )
        printerName = Preferences.getPrinter("PrinterName")
        if printerName:
            printer.setPrinterName(printerName)
        
        printDialog = QPrintDialog(printer, self)
        if printDialog.exec_() == QDialog.Accepted:
            try:
                frame.print_(printer)
            except AttributeError:
                E5MessageBox.critical(
                    self,
                    self.tr("eric6 Web Browser"),
                    self.tr(
                        """<p>Printing is not available due to a bug in"""
                        """ PyQt5. Please upgrade.</p>"""))
                return
    
    @pyqtSlot()
    def printBrowserPdf(self, browser=None):
        """
        Public slot called to print the displayed page to PDF.
        
        @param browser reference to the browser to be printed (HelpBrowser)
        """
        if browser is None:
            browser = self.currentBrowser()
        
        self.__printPdfRequested(browser.page().mainFrame())
    
    def __printPdfRequested(self, frame):
        """
        Private slot to handle a print to PDF request.
        
        @param frame reference to the frame to be printed (QWebFrame)
        """
        printer = QPrinter(mode=QPrinter.HighResolution)
        if Preferences.getPrinter("ColorMode"):
            printer.setColorMode(QPrinter.Color)
        else:
            printer.setColorMode(QPrinter.GrayScale)
        printerName = Preferences.getPrinter("PrinterName")
        if printerName:
            printer.setPrinterName(printerName)
        printer.setOutputFormat(QPrinter.PdfFormat)
        name = frame.url().path().rsplit('/', 1)[-1]
        if name:
            name = name.rsplit('.', 1)[0]
            name += '.pdf'
            printer.setOutputFileName(name)
        
        printDialog = QPrintDialog(printer, self)
        if printDialog.exec_() == QDialog.Accepted:
            try:
                frame.print_(printer)
            except AttributeError:
                E5MessageBox.critical(
                    self,
                    self.tr("eric6 Web Browser"),
                    self.tr(
                        """<p>Printing is not available due to a bug in"""
                        """ PyQt5. Please upgrade.</p>"""))
                return
    
    @pyqtSlot()
    def printPreviewBrowser(self, browser=None):
        """
        Public slot called to show a print preview of the displayed file.
        
        @param browser reference to the browser to be printed (HelpBrowserWV)
        """
        from PyQt5.QtPrintSupport import QPrintPreviewDialog
        
        if browser is None:
            browser = self.currentBrowser()
        
        printer = QPrinter(mode=QPrinter.HighResolution)
        if Preferences.getPrinter("ColorMode"):
            printer.setColorMode(QPrinter.Color)
        else:
            printer.setColorMode(QPrinter.GrayScale)
        if Preferences.getPrinter("FirstPageFirst"):
            printer.setPageOrder(QPrinter.FirstPageFirst)
        else:
            printer.setPageOrder(QPrinter.LastPageFirst)
        printer.setPageMargins(
            Preferences.getPrinter("LeftMargin") * 10,
            Preferences.getPrinter("TopMargin") * 10,
            Preferences.getPrinter("RightMargin") * 10,
            Preferences.getPrinter("BottomMargin") * 10,
            QPrinter.Millimeter
        )
        printerName = Preferences.getPrinter("PrinterName")
        if printerName:
            printer.setPrinterName(printerName)
        
        self.__printPreviewBrowser = browser
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(self.__printPreview)
        preview.exec_()
    
    def __printPreview(self, printer):
        """
        Private slot to generate a print preview.
        
        @param printer reference to the printer object (QPrinter)
        """
        try:
            self.__printPreviewBrowser.print_(printer)
        except AttributeError:
            E5MessageBox.critical(
                self,
                self.tr("eric6 Web Browser"),
                self.tr(
                    """<p>Printing is not available due to a bug in PyQt5."""
                    """Please upgrade.</p>"""))
            return
    
    def __sourceChanged(self, url):
        """
        Private slot to handle a change of a browsers source.
        
        @param url URL of the new site (QUrl)
        """
        browser = self.sender()
        
        if browser is not None:
            self.sourceChanged.emit(browser, url)
    
    def __titleChanged(self, title):
        """
        Private slot to handle a change of a browsers title.
        
        @param title new title (string)
        """
        browser = self.sender()
        
        if browser is not None and isinstance(browser, QWidget):
            index = self.indexOf(browser)
            if title == "":
                title = browser.url().toString()
            
            self.setTabText(index, self.__elide(title.replace("&", "&&")))
            self.setTabToolTip(index, title)
        
            self.titleChanged.emit(browser, title)
    
    def __elide(self, txt, mode=Qt.ElideRight, length=40):
        """
        Private method to elide some text.
        
        @param txt text to be elided (string)
        @keyparam mode elide mode (Qt.TextElideMode)
        @keyparam length amount of characters to be used (integer)
        @return the elided text (string)
        """
        if mode == Qt.ElideNone or len(txt) < length:
            return txt
        elif mode == Qt.ElideLeft:
            return "...{0}".format(txt[-length:])
        elif mode == Qt.ElideMiddle:
            return "{0}...{1}".format(txt[:length // 2], txt[-(length // 2):])
        elif mode == Qt.ElideRight:
            return "{0}...".format(txt[:length])
        else:
            # just in case
            return txt
    
    def preferencesChanged(self):
        """
        Public slot to handle a change of preferences.
        """
        for browser in self.browsers():
            browser.preferencesChanged()
        
        for urlbar in self.__stackedUrlBar.urlBars():
            urlbar.preferencesChanged()
        
        if Preferences.getUI("SingleCloseButton") or \
           not hasattr(self, 'setTabsClosable'):
            if hasattr(self, 'setTabsClosable'):
                self.setTabsClosable(False)
                try:
                    self.tabCloseRequested.disconnect(self.closeBrowserAt)
                except TypeError:
                    pass
            self.__closeButton.show()
        else:
            self.setTabsClosable(True)
            self.tabCloseRequested.connect(self.closeBrowserAt)
            self.__closeButton.hide()
    
    def __loadStarted(self):
        """
        Private method to handle the loadStarted signal.
        """
        browser = self.sender()
        
        if browser is not None:
            index = self.indexOf(browser)
            anim = self.animationLabel(
                index, os.path.join(getConfig("ericPixDir"), "loading.gif"),
                100)
            if not anim:
                loading = QIcon(os.path.join(getConfig("ericPixDir"),
                                "loading.gif"))
                self.setTabIcon(index, loading)
            else:
                self.setTabIcon(index, QIcon())
            self.setTabText(index, self.tr("Loading..."))
            self.setTabToolTip(index, self.tr("Loading..."))
            self.showMessage.emit(self.tr("Loading..."))
            
            self.__mainWindow.setLoadingActions(True)
    
    def __loadFinished(self, ok):
        """
        Private method to handle the loadFinished signal.
        
        @param ok flag indicating the result (boolean)
        """
        browser = self.sender()
        if not isinstance(browser, HelpBrowser):
            return
        
        if browser is not None:
            import Helpviewer.HelpWindow
            index = self.indexOf(browser)
            self.resetAnimation(index)
            self.setTabIcon(
                index, Helpviewer.HelpWindow.HelpWindow.icon(browser.url()))
            if ok:
                self.showMessage.emit(self.tr("Finished loading"))
            else:
                self.showMessage.emit(self.tr("Failed to load"))
            
            self.__mainWindow.setLoadingActions(False)
    
    def __iconChanged(self):
        """
        Private slot to handle the icon change.
        """
        browser = self.sender()
        
        if browser is not None and isinstance(browser, QWidget):
            import Helpviewer.HelpWindow
            self.setTabIcon(
                self.indexOf(browser),
                Helpviewer.HelpWindow.HelpWindow.icon(browser.url()))
            Helpviewer.HelpWindow.HelpWindow.bookmarksManager()\
                .iconChanged(browser.url())
    
    def getSourceFileList(self):
        """
        Public method to get a list of all opened source files.
        
        @return dictionary with tab id as key and host/namespace as value
        """
        sourceList = {}
        for i in range(self.count()):
            browser = self.widget(i)
            if browser is not None and \
               browser.source().isValid():
                sourceList[i] = browser.source().host()
        
        return sourceList
    
    def shallShutDown(self):
        """
        Public method to check, if the application should be shut down.
        
        @return flag indicating a shut down (boolean)
        """
        if self.count() > 1 and Preferences.getHelp("WarnOnMultipleClose"):
            mb = E5MessageBox.E5MessageBox(
                E5MessageBox.Information,
                self.tr("Are you sure you want to close the window?"),
                self.tr("""Are you sure you want to close the window?\n"""
                        """You have %n tab(s) open.""", "", self.count()),
                modal=True,
                parent=self)
            if self.__mainWindow.fromEric:
                quitButton = mb.addButton(
                    self.tr("&Close"), E5MessageBox.AcceptRole)
                quitButton.setIcon(UI.PixmapCache.getIcon("close.png"))
            else:
                quitButton = mb.addButton(
                    self.tr("&Quit"), E5MessageBox.AcceptRole)
                quitButton.setIcon(UI.PixmapCache.getIcon("exit.png"))
            closeTabButton = mb.addButton(
                self.tr("C&lose Current Tab"), E5MessageBox.AcceptRole)
            closeTabButton.setIcon(UI.PixmapCache.getIcon("tabClose.png"))
            mb.addButton(E5MessageBox.Cancel)
            mb.exec_()
            if mb.clickedButton() == quitButton:
                return True
            else:
                if mb.clickedButton() == closeTabButton:
                    self.closeBrowser()
                return False
        
        return True
    
    def stackedUrlBar(self):
        """
        Public method to get a reference to the stacked url bar.
        
        @return reference to the stacked url bar (StackedUrlBar)
        """
        return self.__stackedUrlBar
    
    def currentUrlBar(self):
        """
        Public method to get a reference to the current url bar.
        
        @return reference to the current url bar (UrlBar)
        """
        return self.__stackedUrlBar.currentWidget()
    
    def __lineEditReturnPressed(self):
        """
        Private slot to handle the entering of an URL.
        """
        edit = self.sender()
        url = self.__guessUrlFromPath(edit.text())
        request = QNetworkRequest(url)
        request.setRawHeader(b"X-Eric6-UserLoadAction", b"1")
        if e5App().keyboardModifiers() == Qt.AltModifier:
            self.newBrowser(
                None, (request, QNetworkAccessManager.GetOperation, b""))
        else:
            self.currentBrowser().setSource(
                None, (request, QNetworkAccessManager.GetOperation, b""))
            self.currentBrowser().setFocus()
    
    def __pathSelected(self, path):
        """
        Private slot called when a URL is selected from the completer.
        
        @param path path to be shown (string)
        """
        url = self.__guessUrlFromPath(path)
        self.currentBrowser().setSource(url)
    
    def __guessUrlFromPath(self, path):
        """
        Private method to guess an URL given a path string.
        
        @param path path string to guess an URL for (string)
        @return guessed URL (QUrl)
        """
        manager = self.__mainWindow.openSearchManager()
        path = Utilities.fromNativeSeparators(path)
        url = manager.convertKeywordSearchToUrl(path)
        if url.isValid():
            return url
        
        try:
            url = QUrl.fromUserInput(path)
        except AttributeError:
            url = QUrl(path)
        
        if url.scheme() == "about" and \
           url.path() == "home":
            url = QUrl("eric:home")
        
        if url.scheme() in ["s", "search"]:
            url = manager.currentEngine().searchUrl(url.path().strip())
        
        if url.scheme() != "" and \
           (url.host() != "" or url.path() != ""):
            return url
        
        urlString = Preferences.getHelp("DefaultScheme") + path.strip()
        url = QUrl.fromEncoded(urlString.encode("utf-8"), QUrl.TolerantMode)
        
        return url
    
    def __currentChanged(self, index):
        """
        Private slot to handle an index change.
        
        @param index new index (integer)
        """
        self.__stackedUrlBar.setCurrentIndex(index)
        
        browser = self.browserAt(index)
        if browser is not None:
            if browser.url() == "" and browser.hasFocus():
                self.__stackedUrlBar.currentWidget.setFocus()
            elif browser.url() != "":
                browser.setFocus()
    
    def restoreClosedTab(self):
        """
        Public slot to restore the most recently closed tab.
        """
        if not self.canRestoreClosedTab():
            return
        
        act = self.sender()
        tab = self.__closedTabsManager.getClosedTabAt(act.data())
        
        self.newBrowser(tab.url.toString(), position=tab.position)
    
    def canRestoreClosedTab(self):
        """
        Public method to check, if closed tabs can be restored.
        
        @return flag indicating that closed tabs can be restored (boolean)
        """
        return self.__closedTabsManager.isClosedTabAvailable()
    
    def restoreAllClosedTabs(self):
        """
        Public slot to restore all closed tabs.
        """
        if not self.canRestoreClosedTab():
            return
        
        for tab in self.__closedTabsManager.allClosedTabs():
            self.newBrowser(tab.url.toString(), position=tab.position)
        self.__closedTabsManager.clearList()
    
    def clearClosedTabsList(self):
        """
        Public slot to clear the list of closed tabs.
        """
        self.__closedTabsManager.clearList()
    
    def __aboutToShowClosedTabsMenu(self):
        """
        Private slot to populate the closed tabs menu.
        """
        fm = self.__closedTabsMenu.fontMetrics()
        maxWidth = fm.width('m') * 40
        
        self.__closedTabsMenu.clear()
        index = 0
        for tab in self.__closedTabsManager.allClosedTabs():
            title = fm.elidedText(tab.title, Qt.ElideRight, maxWidth)
            self.__closedTabsMenu.addAction(
                self.__mainWindow.icon(tab.url), title,
                self.restoreClosedTab).setData(index)
            index += 1
        self.__closedTabsMenu.addSeparator()
        self.__closedTabsMenu.addAction(
            self.tr("Restore All Closed Tabs"), self.restoreAllClosedTabs)
        self.__closedTabsMenu.addAction(
            self.tr("Clear List"), self.clearClosedTabsList)
    
    def closedTabsManager(self):
        """
        Public slot to get a reference to the closed tabs manager.
        
        @return reference to the closed tabs manager (ClosedTabsManager)
        """
        return self.__closedTabsManager
    
    def __closedTabAvailable(self, avail):
        """
        Private slot to handle changes of the availability of closed tabs.
        
        @param avail flag indicating the availability of closed tabs (boolean)
        """
        self.__closedTabsButton.setEnabled(avail)
        self.__restoreClosedTabAct.setEnabled(avail)
