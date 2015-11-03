# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a web search widget for the web browser.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, QUrl, QModelIndex, QTimer, Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont, QIcon, \
    QPixmap
from PyQt5.QtWidgets import QMenu, QCompleter
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebPage

import UI.PixmapCache

import Preferences

from E5Gui.E5LineEdit import E5ClearableLineEdit


class HelpWebSearchWidget(E5ClearableLineEdit):
    """
    Class implementing a web search widget for the web browser.
    
    @signal search(QUrl) emitted when the search should be done
    """
    search = pyqtSignal(QUrl)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(HelpWebSearchWidget, self).__init__(parent)
        
        from E5Gui.E5LineEdit import E5LineEdit
        from E5Gui.E5LineEditButton import E5LineEditButton
        from .OpenSearch.OpenSearchManager import OpenSearchManager

        self.__mw = parent
        
        self.__openSearchManager = OpenSearchManager(self)
        self.__openSearchManager.currentEngineChanged.connect(
            self.__currentEngineChanged)
        self.__currentEngine = ""
        
        self.__enginesMenu = QMenu(self)
        
        self.__engineButton = E5LineEditButton(self)
        self.__engineButton.setMenu(self.__enginesMenu)
        self.addWidget(self.__engineButton, E5LineEdit.LeftSide)
        
        self.__searchButton = E5LineEditButton(self)
        self.__searchButton.setIcon(UI.PixmapCache.getIcon("webSearch.png"))
        self.addWidget(self.__searchButton, E5LineEdit.LeftSide)
        
        self.__model = QStandardItemModel(self)
        self.__completer = QCompleter()
        self.__completer.setModel(self.__model)
        self.__completer.setCompletionMode(
            QCompleter.UnfilteredPopupCompletion)
        self.__completer.setWidget(self)
        
        self.__searchButton.clicked.connect(self.__searchButtonClicked)
        self.textEdited.connect(self.__textEdited)
        self.returnPressed.connect(self.__searchNow)
        self.__completer.activated[QModelIndex].connect(
            self.__completerActivated)
        self.__completer.highlighted[QModelIndex].connect(
            self.__completerHighlighted)
        self.__enginesMenu.aboutToShow.connect(self.__showEnginesMenu)
        
        self.__suggestionsItem = None
        self.__suggestions = []
        self.__suggestTimer = None
        self.__suggestionsEnabled = Preferences.getHelp("WebSearchSuggestions")
        
        self.__recentSearchesItem = None
        self.__recentSearches = []
        self.__maxSavedSearches = 10
        
        self.__engine = None
        self.__loadSearches()
        self.__setupCompleterMenu()
        self.__currentEngineChanged()
    
    def __searchNow(self):
        """
        Private slot to perform the web search.
        """
        searchText = self.text()
        if not searchText:
            return
        
        globalSettings = QWebSettings.globalSettings()
        if not globalSettings.testAttribute(
                QWebSettings.PrivateBrowsingEnabled):
            if searchText in self.__recentSearches:
                self.__recentSearches.remove(searchText)
            self.__recentSearches.insert(0, searchText)
            if len(self.__recentSearches) > self.__maxSavedSearches:
                self.__recentSearches = \
                    self.__recentSearches[:self.__maxSavedSearches]
            self.__setupCompleterMenu()
        
        url = self.__openSearchManager.currentEngine().searchUrl(searchText)
        self.search.emit(url)
    
    def __setupCompleterMenu(self):
        """
        Private method to create the completer menu.
        """
        if not self.__suggestions or \
           (self.__model.rowCount() > 0 and
                self.__model.item(0) != self.__suggestionsItem):
            self.__model.clear()
            self.__suggestionsItem = None
        else:
            self.__model.removeRows(1, self.__model.rowCount() - 1)
        
        boldFont = QFont()
        boldFont.setBold(True)
        
        if self.__suggestions:
            if self.__model.rowCount() == 0:
                if not self.__suggestionsItem:
                    self.__suggestionsItem = QStandardItem(
                        self.tr("Suggestions"))
                    self.__suggestionsItem.setFont(boldFont)
                self.__model.appendRow(self.__suggestionsItem)
            
            for suggestion in self.__suggestions:
                self.__model.appendRow(QStandardItem(suggestion))
        
        if not self.__recentSearches:
            self.__recentSearchesItem = QStandardItem(
                self.tr("No Recent Searches"))
            self.__recentSearchesItem.setFont(boldFont)
            self.__model.appendRow(self.__recentSearchesItem)
        else:
            self.__recentSearchesItem = QStandardItem(
                self.tr("Recent Searches"))
            self.__recentSearchesItem.setFont(boldFont)
            self.__model.appendRow(self.__recentSearchesItem)
            for recentSearch in self.__recentSearches:
                self.__model.appendRow(QStandardItem(recentSearch))
        
        view = self.__completer.popup()
        view.setFixedHeight(view.sizeHintForRow(0) * self.__model.rowCount() +
                            view.frameWidth() * 2)
        
        self.__searchButton.setEnabled(
            bool(self.__recentSearches or self.__suggestions))
    
    def __completerActivated(self, index):
        """
        Private slot handling the selection of an entry from the completer.
        
        @param index index of the item (QModelIndex)
        """
        if self.__suggestionsItem and \
           self.__suggestionsItem.index().row() == index.row():
            return
        
        if self.__recentSearchesItem and \
           self.__recentSearchesItem.index().row() == index.row():
            return
        
        self.__searchNow()
    
    def __completerHighlighted(self, index):
        """
        Private slot handling the highlighting of an entry of the completer.
        
        @param index index of the item (QModelIndex)
        @return flah indicating a successful highlighting (boolean)
        """
        if self.__suggestionsItem and \
           self.__suggestionsItem.index().row() == index.row():
            return False
        
        if self.__recentSearchesItem and \
           self.__recentSearchesItem.index().row() == index.row():
            return False
        
        self.setText(index.data())
        return True
    
    def __textEdited(self, txt):
        """
        Private slot to handle changes of the search text.
        
        @param txt search text (string)
        """
        if self.__suggestionsEnabled:
            if self.__suggestTimer is None:
                self.__suggestTimer = QTimer(self)
                self.__suggestTimer.setSingleShot(True)
                self.__suggestTimer.setInterval(200)
                self.__suggestTimer.timeout.connect(self.__getSuggestions)
            self.__suggestTimer.start()
        else:
            self.__completer.setCompletionPrefix(txt)
            self.__completer.complete()
    
    def __getSuggestions(self):
        """
        Private slot to get search suggestions from the configured search
        engine.
        """
        searchText = self.text()
        if searchText:
            self.__openSearchManager.currentEngine()\
                .requestSuggestions(searchText)
    
    def __newSuggestions(self, suggestions):
        """
        Private slot to receive a new list of suggestions.
        
        @param suggestions list of suggestions (list of strings)
        """
        self.__suggestions = suggestions
        self.__setupCompleterMenu()
        self.__completer.complete()
    
    def __showEnginesMenu(self):
        """
        Private slot to handle the display of the engines menu.
        """
        self.__enginesMenu.clear()
        
        from .OpenSearch.OpenSearchEngineAction import OpenSearchEngineAction
        engineNames = self.__openSearchManager.allEnginesNames()
        for engineName in engineNames:
            engine = self.__openSearchManager.engine(engineName)
            action = OpenSearchEngineAction(engine, self.__enginesMenu)
            action.setData(engineName)
            action.triggered.connect(self.__changeCurrentEngine)
            self.__enginesMenu.addAction(action)
            
            if self.__openSearchManager.currentEngineName() == engineName:
                action.setCheckable(True)
                action.setChecked(True)
        
        ct = self.__mw.currentBrowser()
        linkedResources = ct.linkedResources("search")
        
        if len(linkedResources) > 0:
            self.__enginesMenu.addSeparator()
        
        for linkedResource in linkedResources:
            url = QUrl(linkedResource.href)
            title = linkedResource.title
            mimetype = linkedResource.type_
            
            if mimetype != "application/opensearchdescription+xml":
                continue
            if url.isEmpty():
                continue
            
            if url.isRelative():
                url = ct.url().resolved(url)
            
            if not title:
                if not ct.title():
                    title = url.host()
                else:
                    title = ct.title()
            
            action = self.__enginesMenu.addAction(
                self.tr("Add '{0}'").format(title),
                self.__addEngineFromUrl)
            action.setData(url)
            action.setIcon(ct.icon())
        
        self.__enginesMenu.addSeparator()
        self.__enginesMenu.addAction(self.__mw.searchEnginesAction())
        
        if self.__recentSearches:
            self.__enginesMenu.addAction(self.tr("Clear Recent Searches"),
                                         self.clear)
    
    def __changeCurrentEngine(self):
        """
        Private slot to handle the selection of a search engine.
        """
        action = self.sender()
        if action is not None:
            name = action.data()
            self.__openSearchManager.setCurrentEngineName(name)
    
    def __addEngineFromUrl(self):
        """
        Private slot to add a search engine given its URL.
        """
        action = self.sender()
        if action is not None:
            url = action.data()
            if not isinstance(url, QUrl):
                return
            
            self.__openSearchManager.addEngine(url)
    
    def __searchButtonClicked(self):
        """
        Private slot to show the search menu via the search button.
        """
        self.__setupCompleterMenu()
        self.__completer.complete()
    
    def clear(self):
        """
        Public method to clear all private data.
        """
        self.__recentSearches = []
        self.__setupCompleterMenu()
        super(HelpWebSearchWidget, self).clear()
        self.clearFocus()
    
    def preferencesChanged(self):
        """
        Public method to handle the change of preferences.
        """
        self.__suggestionsEnabled = Preferences.getHelp("WebSearchSuggestions")
        if not self.__suggestionsEnabled:
            self.__suggestions = []
            self.__setupCompleterMenu()
    
    def saveSearches(self):
        """
        Public method to save the recently performed web searches.
        """
        Preferences.Prefs.settings.setValue(
            'Help/WebSearches', self.__recentSearches)
    
    def __loadSearches(self):
        """
        Private method to load the recently performed web searches.
        """
        searches = Preferences.Prefs.settings.value('Help/WebSearches')
        if searches is not None:
            self.__recentSearches = searches
    
    def openSearchManager(self):
        """
        Public method to get a reference to the opensearch manager object.
        
        @return reference to the opensearch manager object (OpenSearchManager)
        """
        return self.__openSearchManager
    
    def __currentEngineChanged(self):
        """
        Private slot to track a change of the current search engine.
        """
        if self.__openSearchManager.engineExists(self.__currentEngine):
            oldEngine = self.__openSearchManager.engine(self.__currentEngine)
            oldEngine.imageChanged.disconnect(self.__engineImageChanged)
            if self.__suggestionsEnabled:
                oldEngine.suggestions.disconnect(self.__newSuggestions)
        
        newEngine = self.__openSearchManager.currentEngine()
        if newEngine.networkAccessManager() is None:
            newEngine.setNetworkAccessManager(self.__mw.networkAccessManager())
        newEngine.imageChanged.connect(self.__engineImageChanged)
        if self.__suggestionsEnabled:
            newEngine.suggestions.connect(self.__newSuggestions)
        
        self.setInactiveText(self.__openSearchManager.currentEngineName())
        self.__currentEngine = self.__openSearchManager.currentEngineName()
        self.__engineButton.setIcon(QIcon(QPixmap.fromImage(
            self.__openSearchManager.currentEngine().image())))
        self.__suggestions = []
        self.__setupCompleterMenu()
    
    def __engineImageChanged(self):
        """
        Private slot to handle a change of the current search engine icon.
        """
        self.__engineButton.setIcon(QIcon(QPixmap.fromImage(
            self.__openSearchManager.currentEngine().image())))
    
    def mousePressEvent(self, evt):
        """
        Protected method called by a mouse press event.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        if evt.button() == Qt.XButton1:
            self.__mw.currentBrowser().pageAction(QWebPage.Back).trigger()
        elif evt.button() == Qt.XButton2:
            self.__mw.currentBrowser().pageAction(QWebPage.Forward).trigger()
        else:
            super(HelpWebSearchWidget, self).mousePressEvent(evt)
