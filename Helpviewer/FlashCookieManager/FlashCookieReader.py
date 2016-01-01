# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class to read flash cookies.
"""

#
# Note: The code is based on s2x.py
#

from __future__ import unicode_literals

import struct
import io

from PyQt5.QtCore import QDateTime


class FlashCookieReaderError(Exception):
    """
    Class containing data of a reader error.
    """
    def __init__(self, msg):
        """
        Constructor
        
        @param msg error message
        @type str
        """
        self.msg = msg


class FlashCookieReader(object):
    """
    Class implementing a reader for flash cookies (*.sol files).
    """
    Number = b'\x00'
    Boolean = b'\x01'
    String = b'\x02'
    ObjObj = b'\x03'
    Null = b'\x05'
    Undef = b'\x06'
    ObjArr = b'\x08'
    ObjDate = b'\x0B'
    ObjM = b'\x0D'
    ObjXml = b'\x0F'
    ObjCc = b'\x10'
    
    EpochCorrectionMsecs = 31 * 24 * 60 * 60 * 1000
    # Flash Epoch starts at 1969-12-01
    
    def __init__(self):
        """
        Constructor
        """
        self.__result = {}
        # dictionary with element name as key and tuple of
        # type and value as value
        self.__data = None
        self.__parsed = False
    
    def setBytes(self, solData):
        """
        Public method to set the contents of a sol file to be parsed.
        
        @param solData contents of the file
        @type bytes
        """
        self.__data = io.BytesIO(solData)
    
    def setFileName(self, solFilename):
        """
        Public method to set the name of a sol file to be parsed.
        
        @param solFilename name of the sol file
        @type str
        """
        self.__data = open(solFilename, "rb")
    
    def setFile(self, solFile):
        """
        Public method to set an open sol file to be parsed.
        
        @param solFile sol file to be parsed
        @type io.FileIO
        """
        self.__data = solFile
    
    def parse(self):
        """
        Public method to parse the sol file.
        
        @exception FlashCookieReaderError raised when encountering a parse
            issue
        """
        if self.__data is None:
            return
        
        self.__data.seek(0, 2)
        lenSolData = self.__data.tell()
        self.__data.seek(0)
        self.__data.read(2)
        sLenData = self.__data.read(4)
        lenData, = struct.unpack(">L", sLenData)    # unsigned long, big-endian
        if lenSolData != lenData + 6:
            raise FlashCookieReaderError(
                "Flash cookie data lengths don't match\n"
                "  file length: {0}\n"
                "  data length: {1}"
                .format(lenSolData - 6, lenData))
        sDataType = self.__data.read(4).decode("utf-8")             # 'TCSO'
        if sDataType != "TCSO":
            raise FlashCookieReaderError(
                "Flash cookie type is not 'TCSO'; found '{0}'."
                .format(sDataType))
        self.__data.read(6)
        lenSolName, = struct.unpack(">H", self.__data.read(2))
        # unsigned short,  big-endian
        solName = self.__data.read(lenSolName)
        solName = solName.decode("utf-8", "replace")
        self.__result["SolName"] = ("string", solName)
        self.__data.read(4)
        while self.__data.tell() < lenSolData:
            lenVariableName, = struct.unpack(">H", self.__data.read(2))
            # unsigned short,  big-endian
            variableName = self.__data.read(lenVariableName)
            variableName = variableName.decode("utf-8", "replace")
            variableType = self.__data.read(1)
            if len(variableType):
                if variableType == self.Number:
                    self.__parseNumber(variableName, self.__result)
                elif variableType == self.Boolean:
                    self.__parseBoolean(variableName, self.__result)
                elif variableType == self.String:
                    self.__parseString(variableName, self.__result)
                elif variableType == self.ObjObj:
                    self.__parseObject(variableName, self.__result)
                elif variableType == self.ObjArr:
                    self.__parseArray(variableName, self.__result)
                elif variableType == self.ObjDate:
                    self.__parseDate(variableName, self.__result)
                elif variableType == self.ObjXml:
                    self.__parseXml(variableName, self.__result)
                elif variableType == self.ObjCc:
                    self.__parseOcc(variableName, self.__result)
                elif variableType == self.ObjM:
                    self.__parseOjm(variableName, self.__result)
                elif variableType == self.Null:
                    self.__parseNull(variableName, self.__result)
                elif variableType == self.Undef:
                    self.__parseUndefined(variableName, self.__result)
                else:
                    raise FlashCookieReaderError(
                        "Unexpected Data Type: " + hex(ord(variableType)))
            self.__data.read(1)       # '\x00'
        self.__data.close()
        self.__parsed = True
        
    def __parseNumber(self, variableName, parent):
        """
        Private method to parse a number.
        
        @param variableName name of the variable to be parsed
        @type str
        @param parent reference to the dictionary to insert the result into
        @type dict
        """
        b = self.__data.read(8)
        if b == b"\x7F\xF0\x00\x00\x00\x00\x00\x00":
            value = "Infinity"
        elif b == b"\xFF\xF0\x00\x00\x00\x00\x00\x00":
            value = "-Infinity"
        elif b == b"\x7F\xF8\x00\x00\x00\x00\x00\x00":
            value = "NaN"
        else:
            value, = struct.unpack(">d", b)    # double, big-endian
            value = str(value)
        parent[variableName] = ("number", value)
    
    def __parseBoolean(self, variableName, parent):
        """
        Private method to parse a boolean.
        
        @param variableName name of the variable to be parsed
        @type str
        @param parent reference to the dictionary to insert the result into
        @type dict
        """
        b = self.__data.read(1)
        if b == b"\x00":
            value = "False"
        elif b == b"\x01":
            value = "True"
        else:
            # boolean value error; default to True
            value = "True"
        parent[variableName] = ("boolean", value)
    
    def __parseString(self, variableName, parent):
        """
        Private method to parse a string.
        
        @param variableName name of the variable to be parsed
        @type str
        @param parent reference to the dictionary to insert the result into
        @type dict
        """
        lenStr, = struct.unpack(">H", self.__data.read(2))
        # unsigned short, big-endian
        b = self.__data.read(lenStr)
        value = b.decode("utf-8", "replace")
        parent[variableName] = ("string", value)
    
    def __parseDate(self, variableName, parent):
        """
        Private method to parse a date.
        
        @param variableName name of the variable to be parsed
        @type str
        @param parent reference to the dictionary to insert the result into
        @type dict
        """
        msec, = struct.unpack(">d", self.__data.read(8))
        # double, big-endian
        # DateObject: Milliseconds Count From Dec. 1, 1969
        msec -= self.EpochCorrectionMsecs   # correct for Unix epoch
        minOffset, = struct.unpack(">h", self.__data.read(2))
        # short, big-endian
        offset = minOffset // 60    # offset in hours
        # Timezone: UTC + Offset
        value = QDateTime()
        value.setMSecsSinceEpoch(msec)
        value.setOffsetFromUtc(offset * 3600)
        parent[variableName] = ("date",
                                value.toString("yyyy-MM-dd HH:mm:ss t"))
    
    def __parseXml(self, variableName, parent):
        """
        Private method to parse XML.
        
        @param variableName name of the variable to be parsed
        @type str
        @param parent reference to the dictionary to insert the result into
        @type dict
        """
        lenCData, = struct.unpack(">L", self.__data.read(4))
        # unsigned long, big-endian
        cData = self.__data.read(lenCData)
        value = cData.decode("utf-8", "replace")
        parent[variableName] = ("xml", value)
    
    def __parseOjm(self, variableName, parent):
        """
        Private method to parse an m_object.
        
        @param variableName name of the variable to be parsed
        @type str
        @param parent reference to the dictionary to insert the result into
        @type dict
        """
        parent[variableName] = ("m_object", "")
    
    def __parseNull(self, variableName, parent):
        """
        Private method to parse a null object.
        
        @param variableName name of the variable to be parsed
        @type str
        @param parent reference to the dictionary to insert the result into
        @type dict
        """
        parent[variableName] = ("null", "")
    
    def __parseUndefined(self, variableName, parent):
        """
        Private method to parse an undefined object.
        
        @param variableName name of the variable to be parsed
        @type str
        @param parent reference to the dictionary to insert the result into
        @type dict
        """
        parent[variableName] = ("undefined", "")
    
    def __parseObject(self, variableName, parent):
        """
        Private method to parse an object.
        
        @param variableName name of the variable to be parsed
        @type str
        @param parent reference to the dictionary to insert the result into
        @type dict
        @exception FlashCookieReaderError raised when an issue with the cookie
            file is found
        """
        value = {}
        parent[variableName] = ("object", value)
        
        lenVariableName, = struct.unpack(">H", self.__data.read(2))
        # unsigned short,  big-endian
        while lenVariableName != 0:
            variableName = self.__data.read(lenVariableName)
            variableName = variableName.decode("utf-8", "replace")
            variableType = self.__data.read(1)
            if variableType == self.Number:
                self.__parseNumber(variableName, value)
            elif variableType == self.Boolean:
                self.__parseBoolean(variableName, value)
            elif variableType == self.String:
                self.__parseString(variableName, value)
            elif variableType == self.ObjObj:
                self.__parseObject(variableName, value)
            elif variableType == self.ObjArr:
                self.__parseArray(variableName, value)
            elif variableType == self.ObjDate:
                self.__parseDate(variableName, value)
            elif variableType == self.ObjXml:
                self.__parseXml(variableName, value)
            elif variableType == self.ObjCc:
                self.__parseOcc(variableName, value)
            elif variableType == self.ObjM:
                self.__parseOjm(variableName, value)
            elif variableType == self.Null:
                self.__parseNull(variableName, value)
            elif variableType == self.Undef:
                self.__parseUndefined(variableName, value)
            else:
                raise FlashCookieReaderError(
                    "Unexpected Data Type: " + hex(ord(variableType)))
            lenVariableName, = struct.unpack(">H", self.__data.read(2))
        self.__data.read(1)       # '\x09'
    
    def __parseArray(self, variableName, parent):
        """
        Private method to parse an array.
        
        @param variableName name of the variable to be parsed
        @type str
        @param parent reference to the dictionary to insert the result into
        @type dict
        @exception FlashCookieReaderError raised when an issue with the cookie
            file is found
        """
        arrayLength, = struct.unpack(">L", self.__data.read(4))
        # unsigned long, big-endian
        
        value = {}
        parent[variableName] = ("array; length={0}".format(arrayLength), value)
        
        lenVariableName, = struct.unpack(">H", self.__data.read(2))
        # unsigned short,  big-endian
        while lenVariableName != 0:
            variableName = self.__data.read(lenVariableName)
            variableName = variableName.decode("utf-8", "replace")
            variableType = self.__data.read(1)
            if variableType == self.Number:
                self.__parseNumber(variableName, value)
            elif variableType == self.Boolean:
                self.__parseBoolean(variableName, value)
            elif variableType == self.String:
                self.__parseString(variableName, value)
            elif variableType == self.ObjObj:
                self.__parseObject(variableName, value)
            elif variableType == self.ObjArr:
                self.__parseArray(variableName, value)
            elif variableType == self.ObjDate:
                self.__parseDate(variableName, value)
            elif variableType == self.ObjXml:
                self.__parseXml(variableName, value)
            elif variableType == self.ObjCc:
                self.__parseOcc(variableName, value)
            elif variableType == self.ObjM:
                self.__parseOjm(variableName, value)
            elif variableType == self.Null:
                self.__parseNull(variableName, value)
            elif variableType == self.Undef:
                self.__parseUndefined(variableName, value)
            else:
                raise FlashCookieReaderError(
                    "Unexpected Data Type: " + hex(ord(variableType)))
            lenVariableName, = struct.unpack(">H", self.__data.read(2))
        self.__data.read(1)       # '\x09'
    
    def __parseOcc(self, variableName, parent):
        """
        Private method to parse a c_object.
        
        @param variableName name of the variable to be parsed
        @type str
        @param parent reference to the dictionary to insert the result into
        @type dict
        @exception FlashCookieReaderError raised when an issue with the cookie
            file is found
        """
        lenCname = struct.unpack(">H", self.__data.read(2))
        # unsigned short,  big-endian
        cname = self.__data.read(lenCname)
        cname = cname.decode("utf-8", "replace")
        
        value = {}
        parent[variableName] = ("c_object; cname={0}".format(cname), value)
        
        lenVariableName, = struct.unpack(">H", self.__data.read(2))
        # unsigned short,  big-endian
        while lenVariableName != 0:
            variableName = self.__data.read(lenVariableName)
            variableName = variableName.decode("utf-8", "replace")
            variableType = self.__data.read(1)
            if variableType == self.Number:
                self.__parseNumber(variableName, value)
            elif variableType == self.Boolean:
                self.__parseBoolean(variableName, value)
            elif variableType == self.String:
                self.__parseString(variableName, value)
            elif variableType == self.ObjObj:
                self.__parseObject(variableName, value)
            elif variableType == self.ObjArr:
                self.__parseArray(variableName, value)
            elif variableType == self.ObjDate:
                self.__parseDate(variableName, value)
            elif variableType == self.ObjXml:
                self.__parseXml(variableName, value)
            elif variableType == self.ObjCc:
                self.__parseOcc(variableName, value)
            elif variableType == self.ObjM:
                self.__parseOjm(variableName, value)
            elif variableType == self.Null:
                self.__parseNull(variableName, value)
            elif variableType == self.Undef:
                self.__parseUndefined(variableName, value)
            else:
                raise FlashCookieReaderError(
                    "Unexpected Data Type: " + hex(ord(variableType)))
            lenVariableName, = struct.unpack(">H", self.__data.read(2))
        self.__data.read(1)       # '\x09'
    
    def toString(self, indent=0, parent=None):
        """
        Public method to convert the parsed cookie to a string representation.
        
        @param indent indentation level
        @type int
        @param parent reference to the dictionary to be converted
        @type dict
        @return string representation of the cookie
        @rtype str
        """
        indentStr = "  " * indent
        strArr = []
        
        if parent is None:
            parent = self.__result
        
        if not parent:
            return ""
        
        for variableName in sorted(parent.keys()):
            variableType, value = parent[variableName]
            if isinstance(value, dict):
                resultStr = self.toString(indent + 1, value)
                if resultStr:
                    strArr.append("{0}{1}:\n{2}"
                                  .format(indentStr, variableName, resultStr))
                else:
                    strArr.append("{0}{1}:"
                                  .format(indentStr, variableName))
            else:
                strArr.append("{0}{1}: {2}"
                              .format(indentStr, variableName, value))
        
        return "\n".join(strArr)
