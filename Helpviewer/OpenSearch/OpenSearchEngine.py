# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the open search engine.
"""

from __future__ import unicode_literals

import re
import json

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QLocale, QUrl, QByteArray, \
    QBuffer, QIODevice, QObject, qVersion
from PyQt5.QtGui import QImage
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager, \
    QNetworkReply

from UI.Info import Program

import Preferences
import Utilities


class OpenSearchEngine(QObject):
    """
    Class implementing the open search engine.
    
    @signal imageChanged() emitted after the icon has been changed
    @signal suggestions(list of strings) emitted after the suggestions have
            been received
    """
    imageChanged = pyqtSignal()
    suggestions = pyqtSignal(list)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(OpenSearchEngine, self).__init__(parent)
        
        self.__suggestionsReply = None
        self.__networkAccessManager = None
        self._name = ""
        self._description = ""
        self._searchUrlTemplate = ""
        self._suggestionsUrlTemplate = ""
        self._searchParameters = []            # list of two tuples
        self._suggestionsParameters = []       # list of two tuples
        self._imageUrl = ""
        self.__image = QImage()
        self.__iconMoved = False
        self.__searchMethod = "get"
        self.__suggestionsMethod = "get"
        self.__requestMethods = {
            "get": QNetworkAccessManager.GetOperation,
            "post": QNetworkAccessManager.PostOperation,
        }
        
        self.__replies = []
    
    @classmethod
    def parseTemplate(cls, searchTerm, searchTemplate):
        """
        Class method to parse a search template.
        
        @param searchTerm term to search for (string)
        @param searchTemplate template to be parsed (string)
        @return parsed template (string)
        """
        locale = QLocale(Preferences.getHelp("SearchLanguage"))
        language = locale.name().split("_")[0]
        country = language.lower()
        
        result = searchTemplate
        result = result.replace("{count}", "20")
        result = result.replace("{startIndex}", "0")
        result = result.replace("{startPage}", "0")
        result = result.replace("{language}", language)
        result = result.replace("{country}", country)
        result = result.replace("{inputEncoding}", "UTF-8")
        result = result.replace("{outputEncoding}", "UTF-8")
        result = result.replace(
            "{searchTerms}",
            bytes(QUrl.toPercentEncoding(searchTerm)).decode())
        result = re.sub(r"""\{([^\}]*:|)source\??\}""", Program, result)

        return result
    
    @pyqtSlot(result=str)
    def name(self):
        """
        Public method to get the name of the engine.
        
        @return name of the engine (string)
        """
        return self._name
    
    def setName(self, name):
        """
        Public method to set the engine name.
        
        @param name name of the engine (string)
        """
        self._name = name
    
    def description(self):
        """
        Public method to get the description of the engine.
        
        @return description of the engine (string)
        """
        return self._description
    
    def setDescription(self, description):
        """
        Public method to set the engine description.
        
        @param description description of the engine (string)
        """
        self._description = description
    
    def searchUrlTemplate(self):
        """
        Public method to get the search URL template of the engine.
        
        @return search URL template of the engine (string)
        """
        return self._searchUrlTemplate
    
    def setSearchUrlTemplate(self, searchUrlTemplate):
        """
        Public method to set the engine search URL template.
        
        @param searchUrlTemplate search URL template of the engine (string)
        """
        self._searchUrlTemplate = searchUrlTemplate
    
    def searchUrl(self, searchTerm):
        """
        Public method to get a URL ready for searching.
        
        @param searchTerm term to search for (string)
        @return URL (QUrl)
        """
        if not self._searchUrlTemplate:
            return QUrl()
        
        ret = QUrl.fromEncoded(
            self.parseTemplate(searchTerm, self._searchUrlTemplate)
            .encode("utf-8"))
        
        if self.__searchMethod != "post":
            if qVersion() >= "5.0.0":
                from PyQt5.QtCore import QUrlQuery
                urlQuery = QUrlQuery(ret)
                for parameter in self._searchParameters:
                    urlQuery.addQueryItem(
                        parameter[0],
                        self.parseTemplate(searchTerm, parameter[1]))
                ret.setQuery(urlQuery)
            else:
                for parameter in self._searchParameters:
                    ret.addQueryItem(
                        parameter[0],
                        self.parseTemplate(searchTerm, parameter[1]))
        
        return ret
    
    def providesSuggestions(self):
        """
        Public method to check, if the engine provides suggestions.
        
        @return flag indicating suggestions are provided (boolean)
        """
        return self._suggestionsUrlTemplate != ""
    
    def suggestionsUrlTemplate(self):
        """
        Public method to get the search URL template of the engine.
        
        @return search URL template of the engine (string)
        """
        return self._suggestionsUrlTemplate
    
    def setSuggestionsUrlTemplate(self, suggestionsUrlTemplate):
        """
        Public method to set the engine suggestions URL template.
        
        @param suggestionsUrlTemplate suggestions URL template of the
            engine (string)
        """
        self._suggestionsUrlTemplate = suggestionsUrlTemplate
    
    def suggestionsUrl(self, searchTerm):
        """
        Public method to get a URL ready for suggestions.
        
        @param searchTerm term to search for (string)
        @return URL (QUrl)
        """
        if not self._suggestionsUrlTemplate:
            return QUrl()
        
        ret = QUrl.fromEncoded(QByteArray(self.parseTemplate(
            searchTerm, self._suggestionsUrlTemplate).encode("utf-8")))
        
        if self.__searchMethod != "post":
            if qVersion() >= "5.0.0":
                from PyQt5.QtCore import QUrlQuery
                urlQuery = QUrlQuery(ret)
                for parameter in self._suggestionsParameters:
                    urlQuery.addQueryItem(
                        parameter[0],
                        self.parseTemplate(searchTerm, parameter[1]))
                ret.setQuery(urlQuery)
            else:
                for parameter in self._suggestionsParameters:
                    ret.addQueryItem(
                        parameter[0],
                        self.parseTemplate(searchTerm, parameter[1]))
        
        return ret
    
    def searchParameters(self):
        """
        Public method to get the search parameters of the engine.
        
        @return search parameters of the engine (list of two tuples)
        """
        return self._searchParameters[:]
    
    def setSearchParameters(self, searchParameters):
        """
        Public method to set the engine search parameters.
        
        @param searchParameters search parameters of the engine
            (list of two tuples)
        """
        self._searchParameters = searchParameters[:]
    
    def suggestionsParameters(self):
        """
        Public method to get the suggestions parameters of the engine.
        
        @return suggestions parameters of the engine (list of two tuples)
        """
        return self._suggestionsParameters[:]
    
    def setSuggestionsParameters(self, suggestionsParameters):
        """
        Public method to set the engine suggestions parameters.
        
        @param suggestionsParameters suggestions parameters of the
            engine (list of two tuples)
        """
        self._suggestionsParameters = suggestionsParameters[:]
    
    def searchMethod(self):
        """
        Public method to get the HTTP request method used to perform search
        requests.
        
        @return HTTP request method (string)
        """
        return self.__searchMethod
    
    def setSearchMethod(self, method):
        """
        Public method to set the HTTP request method used to perform search
        requests.
        
        @param method HTTP request method (string)
        """
        requestMethod = method.lower()
        if requestMethod not in self.__requestMethods:
            return
        
        self.__searchMethod = requestMethod
    
    def suggestionsMethod(self):
        """
        Public method to get the HTTP request method used to perform
        suggestions requests.
        
        @return HTTP request method (string)
        """
        return self.__suggestionsMethod
    
    def setSuggestionsMethod(self, method):
        """
        Public method to set the HTTP request method used to perform
        suggestions requests.
        
        @param method HTTP request method (string)
        """
        requestMethod = method.lower()
        if requestMethod not in self.__requestMethods:
            return
        
        self.__suggestionsMethod = requestMethod
    
    def imageUrl(self):
        """
        Public method to get the image URL of the engine.
        
        @return image URL of the engine (string)
        """
        return self._imageUrl
    
    def setImageUrl(self, imageUrl):
        """
        Public method to set the engine image URL.
        
        @param imageUrl image URL of the engine (string)
        """
        self._imageUrl = imageUrl
    
    def setImageUrlAndLoad(self, imageUrl):
        """
        Public method to set the engine image URL.
        
        @param imageUrl image URL of the engine (string)
        """
        self.setImageUrl(imageUrl)
        self.__iconMoved = False
        self.loadImage()
    
    def loadImage(self):
        """
        Public method to load the image of the engine.
        """
        if self.__networkAccessManager is None or not self._imageUrl:
            return
        
        reply = self.__networkAccessManager.get(
            QNetworkRequest(QUrl.fromEncoded(self._imageUrl.encode("utf-8"))))
        reply.finished.connect(self.__imageObtained)
        self.__replies.append(reply)
    
    def __imageObtained(self):
        """
        Private slot to receive the image of the engine.
        """
        reply = self.sender()
        if reply is None:
            return
        
        response = reply.readAll()
        
        reply.close()
        if reply in self.__replies:
            self.__replies.remove(reply)
        reply.deleteLater()
        
        if response.isEmpty():
            return
        
        if response.startsWith(b"<html>") or response.startsWith(b"HTML"):
            self.__iconMoved = True
            self.__image = QImage()
        else:
            self.__image.loadFromData(response)
        self.imageChanged.emit()
    
    def image(self):
        """
        Public method to get the image of the engine.
        
        @return image of the engine (QImage)
        """
        if not self.__iconMoved and self.__image.isNull():
            self.loadImage()
        
        return self.__image
    
    def setImage(self, image):
        """
        Public method to set the image of the engine.
        
        @param image image to be set (QImage)
        """
        if not self._imageUrl:
            imageBuffer = QBuffer()
            imageBuffer.open(QIODevice.ReadWrite)
            if image.save(imageBuffer, "PNG"):
                self._imageUrl = "data:image/png;base64,{0}".format(
                    bytes(imageBuffer.buffer().toBase64()).decode())
        
        self.__image = QImage(image)
        self.imageChanged.emit()
    
    def isValid(self):
        """
        Public method to check, if the engine is valid.
        
        @return flag indicating validity (boolean)
        """
        return self._name and self._searchUrlTemplate
    
    def __eq__(self, other):
        """
        Special method implementing the == operator.
        
        @param other reference to an open search engine (OpenSearchEngine)
        @return flag indicating equality (boolean)
        """
        if not isinstance(other, OpenSearchEngine):
            return NotImplemented
        
        return self._name == other._name and \
            self._description == other._description and \
            self._imageUrl == other._imageUrl and \
            self._searchUrlTemplate == other._searchUrlTemplate and \
            self._suggestionsUrlTemplate == other._suggestionsUrlTemplate and \
            self._searchParameters == other._searchParameters and \
            self._suggestionsParameters == other._suggestionsParameters
    
    def __lt__(self, other):
        """
        Special method implementing the < operator.
        
        @param other reference to an open search engine (OpenSearchEngine)
        @return flag indicating less than (boolean)
        """
        if not isinstance(other, OpenSearchEngine):
            return NotImplemented
        
        return self._name < other._name
    
    def requestSuggestions(self, searchTerm):
        """
        Public method to request suggestions.
        
        @param searchTerm term to get suggestions for (string)
        """
        if not searchTerm or not self.providesSuggestions():
            return
        
        if self.__networkAccessManager is None:
            return
        
        if self.__suggestionsReply is not None:
            self.__suggestionsReply.abort()
            self.__suggestionsReply.deleteLater()
            self.__suggestionsReply = None
        
        if self.__suggestionsMethod not in self.__requestMethods:
            # ignore
            return
        
        if self.__suggestionsMethod == "get":
            self.__suggestionsReply = self.networkAccessManager().get(
                QNetworkRequest(self.suggestionsUrl(searchTerm)))
        else:
            parameters = []
            for parameter in self._suggestionsParameters:
                parameters.append(parameter[0] + "=" + parameter[1])
            data = "&".join(parameters)
            self.__suggestionsReply = self.networkAccessManager().post(
                QNetworkRequest(self.suggestionsUrl(searchTerm)), data)
        self.__suggestionsReply.finished.connect(
            self.__suggestionsObtained)
    
    def __suggestionsObtained(self):
        """
        Private slot to receive the suggestions.
        """
        if self.__suggestionsReply.error() == QNetworkReply.NoError:
            buffer = bytes(self.__suggestionsReply.readAll())
            response = Utilities.decodeBytes(buffer)
            response = response.strip()
            
            self.__suggestionsReply.close()
            self.__suggestionsReply.deleteLater()
            self.__suggestionsReply = None
            
            if len(response) == 0:
                return
            
            try:
                result = json.loads(response)
            except ValueError:
                return
            
            try:
                suggestions = result[1]
            except IndexError:
                return
            
            self.suggestions.emit(suggestions)
    
    def networkAccessManager(self):
        """
        Public method to get a reference to the network access manager object.
        
        @return reference to the network access manager object
            (QNetworkAccessManager)
        """
        return self.__networkAccessManager
    
    def setNetworkAccessManager(self, networkAccessManager):
        """
        Public method to set the reference to the network access manager.
        
        @param networkAccessManager reference to the network access manager
            object (QNetworkAccessManager)
        """
        self.__networkAccessManager = networkAccessManager
