# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a manager for open search engines.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSignal, QObject, QUrl, QFile, QDir, QIODevice
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox

from Utilities.AutoSaver import AutoSaver
import Utilities
import Preferences


class OpenSearchManager(QObject):
    """
    Class implementing a manager for open search engines.
    
    @signal changed() emitted to indicate a change
    @signal currentEngineChanged() emitted to indicate a change of
            the current search engine
    """
    changed = pyqtSignal()
    currentEngineChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        if parent is None:
            parent = e5App()
        super(OpenSearchManager, self).__init__(parent)
        
        self.__replies = []
        self.__engines = {}
        self.__keywords = {}
        self.__current = ""
        self.__loading = False
        self.__saveTimer = AutoSaver(self, self.save)
        
        self.changed.connect(self.__saveTimer.changeOccurred)
        
        self.load()
    
    def close(self):
        """
        Public method to close the open search engines manager.
        """
        self.__saveTimer.saveIfNeccessary()
    
    def currentEngineName(self):
        """
        Public method to get the name of the current search engine.
        
        @return name of the current search engine (string)
        """
        return self.__current
    
    def setCurrentEngineName(self, name):
        """
        Public method to set the current engine by name.
        
        @param name name of the new current engine (string)
        """
        if name not in self.__engines:
            return
        
        self.__current = name
        self.currentEngineChanged.emit()
        self.changed.emit()
    
    def currentEngine(self):
        """
        Public method to get a reference to the current engine.
        
        @return reference to the current engine (OpenSearchEngine)
        """
        if not self.__current or self.__current not in self.__engines:
            return None
        
        return self.__engines[self.__current]
    
    def setCurrentEngine(self, engine):
        """
        Public method to set the current engine.
        
        @param engine reference to the new current engine (OpenSearchEngine)
        """
        if engine is None:
            return
        
        for engineName in self.__engines:
            if self.__engines[engineName] == engine:
                self.setCurrentEngineName(engineName)
                break
    
    def engine(self, name):
        """
        Public method to get a reference to the named engine.
        
        @param name name of the engine (string)
        @return reference to the engine (OpenSearchEngine)
        """
        if name not in self.__engines:
            return None
        
        return self.__engines[name]
    
    def engineExists(self, name):
        """
        Public method to check, if an engine exists.
        
        @param name name of the engine (string)
        @return flag indicating an existing engine (boolean)
        """
        return name in self.__engines
    
    def allEnginesNames(self):
        """
        Public method to get a list of all engine names.
        
        @return sorted list of all engine names (list of strings)
        """
        return sorted(self.__engines.keys())
    
    def enginesCount(self):
        """
        Public method to get the number of available engines.
        
        @return number of engines (integer)
        """
        return len(self.__engines)
    
    def addEngine(self, engine):
        """
        Public method to add a new search engine.
        
        @param engine URL of the engine definition file (QUrl) or
            name of a file containing the engine definition (string)
            or reference to an engine object (OpenSearchEngine)
        @return flag indicating success (boolean)
        """
        from .OpenSearchEngine import OpenSearchEngine
        if isinstance(engine, QUrl):
            return self.__addEngineByUrl(engine)
        elif isinstance(engine, OpenSearchEngine):
            return self.__addEngineByEngine(engine)
        else:
            return self.__addEngineByFile(engine)
    
    def __addEngineByUrl(self, url):
        """
        Private method to add a new search engine given its URL.
        
        @param url URL of the engine definition file (QUrl)
        @return flag indicating success (boolean)
        """
        if not url.isValid():
            return
        
        from Helpviewer.HelpWindow import HelpWindow

        reply = HelpWindow.networkAccessManager().get(QNetworkRequest(url))
        reply.finished.connect(self.__engineFromUrlAvailable)
        reply.setParent(self)
        self.__replies.append(reply)
        
        return True
    
    def __addEngineByFile(self, filename):
        """
        Private method to add a new search engine given a filename.
        
        @param filename name of a file containing the engine definition
            (string)
        @return flag indicating success (boolean)
        """
        file_ = QFile(filename)
        if not file_.open(QIODevice.ReadOnly):
            return False
        
        from .OpenSearchReader import OpenSearchReader
        reader = OpenSearchReader()
        engine = reader.read(file_)
        
        if not self.__addEngineByEngine(engine):
            return False
        
        return True
    
    def __addEngineByEngine(self, engine):
        """
        Private method to add a new search engine given a reference to an
        engine.
        
        @param engine reference to an engine object (OpenSearchEngine)
        @return flag indicating success (boolean)
        """
        if engine is None:
            return False
        
        if not engine.isValid():
            return False
        
        if engine.name() in self.__engines:
            return False
        
        engine.setParent(self)
        self.__engines[engine.name()] = engine
        
        self.changed.emit()
        
        return True
    
    def removeEngine(self, name):
        """
        Public method to remove an engine.
        
        @param name name of the engine (string)
        """
        if len(self.__engines) <= 1:
            return
        
        if name not in self.__engines:
            return
        
        engine = self.__engines[name]
        for keyword in [k for k in self.__keywords
                        if self.__keywords[k] == engine]:
            del self.__keywords[keyword]
        del self.__engines[name]
        
        file_ = QDir(self.enginesDirectory()).filePath(
            self.generateEngineFileName(name))
        QFile.remove(file_)
        
        if name == self.__current:
            self.setCurrentEngineName(list(self.__engines.keys())[0])
        
        self.changed.emit()
    
    def generateEngineFileName(self, engineName):
        """
        Public method to generate a valid engine file name.
        
        @param engineName name of the engine (string)
        @return valid engine file name (string)
        """
        fileName = ""
        
        # strip special characters
        for c in engineName:
            if c.isspace():
                fileName += '_'
                continue
            
            if c.isalnum():
                fileName += c
        
        fileName += ".xml"
        
        return fileName
    
    def saveDirectory(self, dirName):
        """
        Public method to save the search engine definitions to files.
        
        @param dirName name of the directory to write the files to (string)
        """
        dir = QDir()
        if not dir.mkpath(dirName):
            return
        dir.setPath(dirName)
        
        from .OpenSearchWriter import OpenSearchWriter
        writer = OpenSearchWriter()
        
        for engine in list(self.__engines.values()):
            name = self.generateEngineFileName(engine.name())
            fileName = dir.filePath(name)
            
            file = QFile(fileName)
            if not file.open(QIODevice.WriteOnly):
                continue
            
            writer.write(file, engine)
    
    def save(self):
        """
        Public method to save the search engines configuration.
        """
        if self.__loading:
            return
        
        self.saveDirectory(self.enginesDirectory())
        
        Preferences.setHelp("WebSearchEngine", self.__current)
        keywords = []
        for k in self.__keywords:
            if self.__keywords[k]:
                keywords.append((k, self.__keywords[k].name()))
        Preferences.setHelp("WebSearchKeywords", keywords)
    
    def loadDirectory(self, dirName):
        """
        Public method to load the search engine definitions from files.
        
        @param dirName name of the directory to load the files from (string)
        @return flag indicating success (boolean)
        """
        if not QFile.exists(dirName):
            return False
        
        success = False
        
        dir = QDir(dirName)
        for name in dir.entryList(["*.xml"]):
            fileName = dir.filePath(name)
            if self.__addEngineByFile(fileName):
                success = True
        
        return success
    
    def load(self):
        """
        Public method to load the search engines configuration.
        """
        self.__loading = True
        self.__current = Preferences.getHelp("WebSearchEngine")
        keywords = Preferences.getHelp("WebSearchKeywords")
        
        if not self.loadDirectory(self.enginesDirectory()):
            self.restoreDefaults()
        
        for keyword, engineName in keywords:
            self.__keywords[keyword] = self.engine(engineName)
        
        if self.__current not in self.__engines and \
           len(self.__engines) > 0:
            self.__current = list(self.__engines.keys())[0]
        
        self.__loading = False
        self.currentEngineChanged.emit()
    
    def restoreDefaults(self):
        """
        Public method to restore the default search engines.
        """
        from .OpenSearchReader import OpenSearchReader
        from .DefaultSearchEngines import DefaultSearchEngines_rc   # __IGNORE_WARNING__
        
        defaultEngineFiles = ["YouTube.xml", "Amazoncom.xml", "Bing.xml",
                              "DeEn_Beolingus.xml", "Facebook.xml",
                              "Google_Im_Feeling_Lucky.xml", "Google.xml",
                              "LEO_DeuEng.xml", "LinuxMagazin.xml",
                              "Reddit.xml", "Wikia_en.xml", "Wikia.xml",
                              "Wikipedia.xml", "Wiktionary.xml", "Yahoo.xml"]
        # Keep this list in sync with the contents of the resource file.

        reader = OpenSearchReader()
        for engineFileName in defaultEngineFiles:
            engineFile = QFile(":/" + engineFileName)
            if not engineFile.open(QIODevice.ReadOnly):
                continue
            engine = reader.read(engineFile)
            self.__addEngineByEngine(engine)
    
    def enginesDirectory(self):
        """
        Public method to determine the directory containing the search engine
        descriptions.
        
        @return directory name (string)
        """
        return os.path.join(
            Utilities.getConfigDir(), "browser", "searchengines")
    
    def __confirmAddition(self, engine):
        """
        Private method to confirm the addition of a new search engine.
        
        @param engine reference to the engine to be added (OpenSearchEngine)
        @return flag indicating the engine shall be added (boolean)
        """
        if engine is None or not engine.isValid():
            return False
        
        host = QUrl(engine.searchUrlTemplate()).host()
        
        res = E5MessageBox.yesNo(
            None,
            "",
            self.tr(
                """<p>Do you want to add the following engine to your"""
                """ list of search engines?<br/><br/>Name: {0}<br/>"""
                """Searches on: {1}</p>""").format(engine.name(), host))
        return res
    
    def __engineFromUrlAvailable(self):
        """
        Private slot to add a search engine from the net.
        """
        reply = self.sender()
        if reply is None:
            return
        
        if reply.error() != QNetworkReply.NoError:
            reply.close()
            if reply in self.__replies:
                self.__replies.remove(reply)
            return
        
        from .OpenSearchReader import OpenSearchReader
        reader = OpenSearchReader()
        engine = reader.read(reply)
        
        reply.close()
        if reply in self.__replies:
            self.__replies.remove(reply)
        
        if not engine.isValid():
            return
        
        if self.engineExists(engine.name()):
            return
        
        if not self.__confirmAddition(engine):
            return
        
        if not self.__addEngineByEngine(engine):
            return
    
    def convertKeywordSearchToUrl(self, keywordSearch):
        """
        Public method to get the search URL for a keyword search.
        
        @param keywordSearch search string for keyword search (string)
        @return search URL (QUrl)
        """
        try:
            keyword, term = keywordSearch.split(" ", 1)
        except ValueError:
            return QUrl()
        
        if not term:
            return QUrl()
        
        engine = self.engineForKeyword(keyword)
        if engine:
            return engine.searchUrl(term)
        
        return QUrl()
    
    def engineForKeyword(self, keyword):
        """
        Public method to get the engine for a keyword.
        
        @param keyword keyword to get engine for (string)
        @return reference to the search engine object (OpenSearchEngine)
        """
        if keyword and keyword in self.__keywords:
            return self.__keywords[keyword]
        
        return None
    
    def setEngineForKeyword(self, keyword, engine):
        """
        Public method to set the engine for a keyword.
        
        @param keyword keyword to get engine for (string)
        @param engine reference to the search engine object (OpenSearchEngine)
            or None to remove the keyword
        """
        if not keyword:
            return
        
        if engine is None:
            try:
                del self.__keywords[keyword]
            except KeyError:
                pass
        else:
            self.__keywords[keyword] = engine
        
        self.changed.emit()
    
    def keywordsForEngine(self, engine):
        """
        Public method to get the keywords for a given engine.
        
        @param engine reference to the search engine object (OpenSearchEngine)
        @return list of keywords (list of strings)
        """
        return [k for k in self.__keywords if self.__keywords[k] == engine]
    
    def setKeywordsForEngine(self, engine, keywords):
        """
        Public method to set the keywords for an engine.
        
        @param engine reference to the search engine object (OpenSearchEngine)
        @param keywords list of keywords (list of strings)
        """
        if engine is None:
            return
        
        for keyword in self.keywordsForEngine(engine):
            del self.__keywords[keyword]
        
        for keyword in keywords:
            if not keyword:
                continue
            
            self.__keywords[keyword] = engine
        
        self.changed.emit()
    
    def enginesChanged(self):
        """
        Public slot to tell the search engine manager, that something has
        changed.
        """
        self.changed.emit()
