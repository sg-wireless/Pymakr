# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a base class for all of eric6s XML stream writers.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import sys
import pickle
import base64

from PyQt5.QtCore import QXmlStreamWriter


class XMLStreamWriterBase(QXmlStreamWriter):
    """
    Class implementing a base class for all of eric6s XML stream writers.
    """
    def __init__(self, device):
        """
        Constructor
        
        @param device reference to the I/O device to write to (QIODevice)
        """
        super(XMLStreamWriterBase, self).__init__(device)
        
        self.basics = {
            type(None): self._write_none,
            int: self._write_int,
            float: self._write_float,
            complex: self._write_complex,
            bool: self._write_bool,
            str: self._write_string,
            bytearray: self._write_bytearray,
            tuple: self._write_tuple,
            list: self._write_list,
            dict: self._write_dictionary,
            set: self._write_set,
            frozenset: self._write_frozenset,
        }
        # 'bytes' is identical to 'str' in Py2
        if sys.version_info[0] >= 3:
            self.basics[bytes] = self._write_bytes

        self.setAutoFormatting(True)
        self.setAutoFormattingIndent(2)
    
    def writeXML(self):
        """
        Public method to write the XML to the file.
        """
        # write the XML header
        self.writeStartDocument()
    
    def writeBasics(self, tag, pyobject):
        """
        Public method to write a tag with a basic Python object dump.
        
        @param tag tag name (string)
        @param pyobject object to be dumped
        """
        self.writeStartElement(tag)
        self._writeBasics(pyobject)
        self.writeEndElement()
    
    def _writeBasics(self, pyobject):
        """
        Protected method to dump an object of a basic Python type.
        
        @param pyobject object to be dumped
        """
        writeMethod = self.basics.get(type(pyobject)) or \
            self._write_unimplemented
        writeMethod(pyobject)

    ###########################################################################
    ## The various writer methods for basic types
    ###########################################################################

    def _write_none(self, value):
        """
        Protected method to dump a NoneType object.
        
        @param value value to be dumped (None) (ignored)
        """
        self.writeEmptyElement("none")
        
    def _write_int(self, value):
        """
        Protected method to dump an int object.
        
        @param value value to be dumped (integer)
        """
        self.writeTextElement("int", str(value))
        
    def _write_bool(self, value):
        """
        Protected method to dump a bool object.
        
        @param value value to be dumped (boolean)
        """
        self.writeTextElement("bool", str(value))
        
    def _write_float(self, value):
        """
        Protected method to dump a float object.
        
        @param value value to be dumped (float)
        """
        self.writeTextElement("float", str(value))
        
    def _write_complex(self, value):
        """
        Protected method to dump a complex object.
        
        @param value value to be dumped (complex)
        """
        self.writeTextElement("complex", '{0} {1}'.format(
            value.real, value.imag))
        
    def _write_string(self, value):
        """
        Protected method to dump a str object.
        
        @param value value to be dumped (string)
        """
        self.writeTextElement("string", str(value))
        
    def _write_bytes(self, value):
        """
        Protected method to dump a bytes object.
        
        @param value value to be dumped (bytes)
        """
        self.writeTextElement(
            "bytes", ",".join(["{0:d}".format(b) for b in value]))
        
    def _write_bytearray(self, value):
        """
        Protected method to dump a bytearray object.
        
        @param value value to be dumped (bytearray)
        """
        self.writeTextElement(
            "bytearray", ",".join(["{0:d}".format(b) for b in value]))
    
    def _write_tuple(self, value):
        """
        Protected method to dump a tuple object.
        
        @param value value to be dumped (tuple)
        """
        self.writeStartElement("tuple")
        for elem in value:
            self._writeBasics(elem)
        self.writeEndElement()
    
    def _write_list(self, value):
        """
        Protected method to dump a list object.
        
        @param value value to be dumped (list)
        """
        self.writeStartElement("list")
        for elem in value:
            self._writeBasics(elem)
        self.writeEndElement()
    
    def _write_dictionary(self, value):
        """
        Protected method to dump a dict object.
        
        @param value value to be dumped (dictionary)
        """
        self.writeStartElement("dict")
        try:
            keys = sorted(list(value.keys()))
        except TypeError:
            keys = list(value.keys())
        for key in keys:
            self.writeStartElement("key")
            self._writeBasics(key)
            self.writeEndElement()
            
            self.writeStartElement("value")
            self._writeBasics(value[key])
            self.writeEndElement()
        self.writeEndElement()
    
    def _write_set(self, value):
        """
        Protected method to dump a set object.
        
        @param value value to be dumped (set)
        """
        self.writeStartElement("set")
        for elem in value:
            self._writeBasics(elem)
        self.writeEndElement()
    
    def _write_frozenset(self, value):
        """
        Protected method to dump a frozenset object.
        
        @param value value to be dumped (frozenset)
        """
        self.writeStartElement("frozenset")
        for elem in value:
            self._writeBasics(elem)
        self.writeEndElement()
    
    def _write_unimplemented(self, value):
        """
        Protected method to dump a type, that has no special method.
        
        @param value value to be dumped (any pickleable object)
        """
        self.writeStartElement("pickle")
        self.writeAttribute("method", "pickle")
        self.writeAttribute("encoding", "base64")
        self.writeCharacters(
            str(base64.b64encode(pickle.dumps(value)), "ASCII"))
        self.writeEndElement()
