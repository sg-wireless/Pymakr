# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a reader for open search engine descriptions.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QXmlStreamReader, QIODevice, QCoreApplication


class OpenSearchReader(QXmlStreamReader):
    """
    Class implementing a reader for open search engine descriptions.
    """
    def read(self, device):
        """
        Public method to read the description.
        
        @param device device to read the description from (QIODevice)
        @return search engine object (OpenSearchEngine)
        """
        self.clear()
        
        if not device.isOpen():
            device.open(QIODevice.ReadOnly)
        
        self.setDevice(device)
        return self.__read()
    
    def __read(self):
        """
        Private method to read and parse the description.
        
        @return search engine object (OpenSearchEngine)
        """
        from .OpenSearchEngine import OpenSearchEngine
        engine = OpenSearchEngine()
        
        while not self.isStartElement() and not self.atEnd():
            self.readNext()
        
        if self.name() != "OpenSearchDescription" or \
           self.namespaceUri() != "http://a9.com/-/spec/opensearch/1.1/":
            self.raiseError(QCoreApplication.translate(
                "OpenSearchReader",
                "The file is not an OpenSearch 1.1 file."))
            return engine
        
        while not self.atEnd():
            self.readNext()
            
            if not self.isStartElement():
                continue
            
            if self.name() == "ShortName":
                engine.setName(self.readElementText())
                
            elif self.name() == "Description":
                engine.setDescription(self.readElementText())
                
            elif self.name() == "Url":
                type_ = self.attributes().value("type")
                url = self.attributes().value("template")
                method = self.attributes().value("method")
                
                if type_ == "application/x-suggestions+json" and \
                   engine.suggestionsUrlTemplate():
                    continue
                
                if (not type_ or
                    type_ == "text/html" or
                    type_ == "application/xhtml+xml") and \
                   engine.suggestionsUrlTemplate():
                    continue
                
                if not url:
                    continue
                
                parameters = []
                
                self.readNext()
                
                while not (self.isEndElement() and self.name() == "Url"):
                    if not self.isStartElement() or \
                       (self.name() != "Param" and self.name() != "Parameter"):
                        self.readNext()
                        continue
                    
                    key = self.attributes().value("name")
                    value = self.attributes().value("value")
                    
                    if key and value:
                        parameters.append((key, value))
                    
                    while not self.isEndElement():
                        self.readNext()
                
                if type_ == "application/x-suggestions+json":
                    engine.setSuggestionsUrlTemplate(url)
                    engine.setSuggestionsParameters(parameters)
                    engine.setSuggestionsMethod(method)
                elif not type_ or \
                    type_ == "text/html" or \
                        type_ == "application/xhtml+xml":
                    engine.setSearchUrlTemplate(url)
                    engine.setSearchParameters(parameters)
                    engine.setSearchMethod(method)
                
            elif self.name() == "Image":
                engine.setImageUrl(self.readElementText())
            
            if engine.name() and \
               engine.description() and \
               engine.suggestionsUrlTemplate() and \
               engine.searchUrlTemplate() and \
               engine.imageUrl():
                break
        
        return engine
