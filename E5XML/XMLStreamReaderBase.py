# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a base class for all of eric6s XML stream writers.
"""

from __future__ import unicode_literals

import pickle
import base64

from PyQt5.QtCore import QXmlStreamReader, QCoreApplication

from E5Gui import E5MessageBox


class XMLStreamReaderBase(QXmlStreamReader):
    """
    Class implementing a base class for all of eric6s XML stream readers.
    """
    def __init__(self, device):
        """
        Constructor
        
        @param device reference to the I/O device to read from (QIODevice)
        """
        super(XMLStreamReaderBase, self).__init__(device)
    
    def toBool(self, value):
        """
        Public method to convert the given value to bool.
        
        @param value value to be converted ("True", "False", "1", "0")
        @return converted value (boolean) or None in case of an error
        """
        if value.lower() in ["true", "false"]:
            return value.lower() == "true"
        
        if value in ["1", "0"]:
            return bool(int(value))
        
        self.raiseBadValue(value)
        return None
    
    def showErrorMessage(self):
        """
        Public method to show an error message.
        """
        if self.hasError():
            msg = QCoreApplication.translate(
                "XMLStreamReaderBase",
                "<p>XML parse error in file <b>{0}</b>, line {1},"
                " column {2}</p><p>Error: {3}</p>").format(
                self.device().fileName(),
                self.lineNumber(), self.columnNumber(),
                self.errorString())
            E5MessageBox.warning(
                None,
                QCoreApplication.translate(
                    "XMLStreamReaderBase", "XML parse error"),
                msg)
    
    def raiseUnexpectedStartTag(self, tag):
        """
        Public method to raise an error for an unexpected start tag.
        
        @param tag name of the unexpected tag (string)
        """
        self.raiseError(QCoreApplication.translate(
            "XMLStreamReaderBase", "Unexpected start tag '{0}'.".format(tag)))
    
    def raiseUnsupportedFormatVersion(self, version):
        """
        Public method to raise an error for an unsupported file format version.
        
        @param version unsupported version (string)
        """
        self.raiseError(QCoreApplication.translate(
            "XMLStreamReaderBase",
            "File format version '{0}' is not supported.").format(version))
    
    def raiseBadValue(self, value):
        """
        Public method to raise an error for a bad value.
        
        @param value bad value (string)
        """
        self.raiseError(QCoreApplication.translate(
            "XMLStreamReaderBase", "Bad value: {0}").format(value))
    
    def readXML(self):
        """
        Public method to read and parse the XML document.
        """
        pass
    
    def attribute(self, name, default=""):
        """
        Public method to read the given attribute of the current tag.
        
        @param name name of the attribute (string)
        @param default default value (string)
        @return value of the requested tag attribute (string)
        """
        att = self.attributes().value(name)
        if att == "":
            att = default
        return att
    
    def _skipUnknownElement(self):
        """
        Protected method to skip over all unknown elements.
        """
        if not self.isStartElement():
            return
        
        while not self.atEnd():
            self.readNext()
            if self.isEndElement():
                break
            
            if self.isStartElement():
                self._skipUnknownElement()
    
    def _readBasics(self):
        """
        Protected method to read an object of a basic Python type.
        
        @return Python object read
        """
        while not self.atEnd():
            self.readNext()
            if self.isStartElement():
                try:
                    if self.name() == "none":
                        val = None
                    elif self.name() == "int":
                        val = int(self.readElementText())
                    elif self.name() == "long":
                        # backward compatibility to 4.6
                        val = int(self.readElementText())
                    elif self.name() == "bool":
                        b = self.readElementText()
                        if b == "True":
                            val = True
                        else:
                            val = False
                    elif self.name() == "float":
                        val = float(self.readElementText())
                    elif self.name() == "complex":
                        real, imag = self.readElementText().split()
                        val = float(real) + float(imag) * 1j
                    elif self.name() == "string":
                        val = self.readElementText()
                    elif self.name() == "unicode":
                        # backward compatibility to 4.6
                        val = self.readElementText()
                    elif self.name() == "bytes":
                        by = bytes([int(b) for b in
                                    self.readElementText().split(",")])
                        val = by
                    elif self.name() == "bytearray":
                        by = bytearray([int(b) for b in
                                        self.readElementText().split(",")])
                        val = by
                    elif self.name() == "tuple":
                        val = self.__readTuple()
                        return val
                    elif self.name() == "list":
                        val = self.__readList()
                        return val
                    elif self.name() == "dict":
                        val = self.__readDict()
                        return val
                    elif self.name() == "set":
                        val = self.__readSet()
                        return val
                    elif self.name() == "frozenset":
                        val = self.__readFrozenset()
                        return val
                    elif self.name() == "pickle":
                        encoding = self.attribute("encoding")
                        if encoding != "base64":
                            self.raiseError(QCoreApplication.translate(
                                "XMLStreamReaderBase",
                                "Pickle data encoding '{0}' is not"
                                " supported.").format(encoding))
                            continue
                        b64 = self.readElementText()
                        pic = base64.b64decode(b64.encode("ASCII"))
                        val = pickle.loads(pic)
                    else:
                        self._skipUnknownElement()
                except ValueError as err:
                    self.raiseError(str(err))
                    continue
            
            if self.isEndElement():
                if self.name() in [
                        "tuple", "list", "dict", "set", "frozenset"]:
                    return None
                else:
                    return val
    
    def __readTuple(self):
        """
        Private method to read a Python tuple.
        
        @return Python tuple
        """
        li = []
        while not self.atEnd():
            val = self._readBasics()
            if self.isEndElement() and self.name() == "tuple" and val is None:
                return tuple(li)
            else:
                li.append(val)
    
    def __readList(self):
        """
        Private method to read a Python list.
        
        @return Python list
        """
        li = []
        while not self.atEnd():
            val = self._readBasics()
            if self.isEndElement() and self.name() == "list" and val is None:
                return li
            else:
                li.append(val)
    
    def __readDict(self):
        """
        Private method to read a Python dictionary.
        
        @return Python dictionary
        """
        d = {}
        while not self.atEnd():
            self.readNext()
            if self.isStartElement():
                if self.name() == "key":
                    key = self._readBasics()
                elif self.name() == "value":
                    d[key] = self._readBasics()
                    if self.isEndElement() and self.name() == "dict":
                        self.readNext()
            
            if self.isEndElement() and self.name() == "dict":
                return d
    
    def __readSet(self):
        """
        Private method to read a Python set.
        
        @return Python set
        """
        li = []
        while not self.atEnd():
            val = self._readBasics()
            if self.isEndElement() and self.name() == "set" and val is None:
                return set(li)
            else:
                li.append(val)
    
    def __readFrozenset(self):
        """
        Private method to read a Python set.
        
        @return Python set
        """
        li = []
        while not self.atEnd():
            val = self._readBasics()
            if self.isEndElement() and \
                    self.name() == "frozenset" and \
                    val is None:
                return frozenset(li)
            else:
                li.append(val)
