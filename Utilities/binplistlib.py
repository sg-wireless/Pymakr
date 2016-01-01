# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a library for reading and writing binary property list
files.

Binary Property List (plist) files provide a faster and smaller serialization
format for property lists on OS X. This is a library for generating binary
plists which can be read by OS X, iOS, or other clients.

The API models the plistlib API, and will call through to plistlib when
XML serialization or deserialization is required.

To generate plists with UID values, wrap the values with the Uid object. The
value must be an int.

To generate plists with NSData/CFData values, wrap the values with the
Data object. The value must be a bytes object.

Date values can only be datetime.datetime objects.

The exceptions InvalidPlistException and NotBinaryPlistException may be
thrown to indicate that the data cannot be serialized or deserialized as
a binary plist.

Plist generation example:
<pre>
    from binplistlib import *
    from datetime import datetime
    plist = {'aKey':'aValue',
             '0':1.322,
             'now':datetime.now(),
             'list':[1,2,3],
             'tuple':('a','b','c')
             }
    try:
        writePlist(plist, "example.plist")
    except (InvalidPlistException, NotBinaryPlistException) as e:
        print("Something bad happened:", e)
</pre>
Plist parsing example:
<pre>
    from binplistlib import *
    try:
        plist = readPlist("example.plist")
        print(plist)
    except (InvalidPlistException, NotBinaryPlistException) as e:
        print("Not a plist:", e)
</pre>
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

#
# Ported from the Python 2 biplist.py script.
#
# Original License:
#
# Copyright (c) 2010, Andrew Wooster
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of biplist nor the names of its contributors may be
#      used to endorse or promote products derived from this software without
#      specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

from collections import namedtuple
from io import BytesIO
import calendar
import datetime
import math
import plistlib
from struct import pack, unpack

__all__ = [
    'Uid', 'Data', 'readPlist', 'writePlist', 'readPlistFromBytes',
    'writePlistToBytes', 'InvalidPlistException', 'NotBinaryPlistException'
]

apple_reference_date_offset = 978307200


class Uid(int):
    """
    Class implementing a wrapper around integers for representing UID values.
    
    This is used in keyed archiving.
    """
    def __repr__(self):
        """
        Special method to return an object representation.
        
        @return object representation (string)
        """
        return "Uid(%d)" % self


class Data(bytes):
    """
    Class implementing a wrapper around bytes types for representing Data
    values.
    """
    pass


class InvalidPlistException(Exception):
    """
    Exception raised when the plist is incorrectly formatted.
    """
    pass


class NotBinaryPlistException(Exception):
    """
    Exception raised when a binary plist was expected but not encountered.
    """
    pass


def readPlist(pathOrFile):
    """
    Module function to read a plist file.
    
    @param pathOrFile name of the plist file (string) or an open file
        (file object)
    @return reference to the read object
    @exception InvalidPlistException raised to signal an invalid plist file
    """
    didOpen = False
    result = None
    if isinstance(pathOrFile, str):
        pathOrFile = open(pathOrFile, 'rb')
        didOpen = True
    try:
        reader = PlistReader(pathOrFile)
        result = reader.parse()
    except NotBinaryPlistException as e:
        try:
            pathOrFile.seek(0)
            result = plistlib.readPlist(pathOrFile)
        except Exception as e:
            raise InvalidPlistException(e)
    if didOpen:
        pathOrFile.close()
    return result


def writePlist(rootObject, pathOrFile, binary=True):
    """
    Module function to write a plist file.
    
    @param rootObject reference to the object to be written
    @param pathOrFile name of the plist file (string) or an open file
        (file object)
    @param binary flag indicating the generation of a binary plist file
        (boolean)
    """
    if not binary:
        plistlib.writePlist(rootObject, pathOrFile)
        return
    else:
        didOpen = False
        if isinstance(pathOrFile, str):
            pathOrFile = open(pathOrFile, 'wb')
            didOpen = True
        writer = PlistWriter(pathOrFile)
        writer.writeRoot(rootObject)
        if didOpen:
            pathOrFile.close()
        return


def readPlistFromBytes(data):
    """
    Module function to read from a plist bytes object.
    
    @param data plist data (bytes)
    @return reference to the read object
    """
    return readPlist(BytesIO(data))


def writePlistToBytes(rootObject, binary=True):
    """
    Module function to write a plist bytes object.
    
    @param rootObject reference to the object to be written
    @param binary flag indicating the generation of a binary plist bytes
        object (boolean)
    @return bytes object containing the plist data
    """
    if not binary:
        return plistlib.writePlistToBytes(rootObject)
    else:
        io = BytesIO()
        writer = PlistWriter(io)
        writer.writeRoot(rootObject)
        return io.getvalue()


def is_stream_binary_plist(stream):
    """
    Module function to check, if the stream is a binary plist.
    
    @param stream plist stream (file object)
    @return flag indicating a binary plist (boolean)
    """
    stream.seek(0)
    header = stream.read(7)
    if header == b'bplist0':
        return True
    else:
        return False

PlistTrailer = namedtuple(
    'PlistTrailer',
    'offsetSize, objectRefSize, offsetCount, topLevelObjectNumber,'
    ' offsetTableOffset')
PlistByteCounts = namedtuple(
    'PlistByteCounts',
    'nullBytes, boolBytes, intBytes, realBytes, dateBytes, dataBytes,'
    ' stringBytes, uidBytes, arrayBytes, setBytes, dictBytes')


class PlistReader(object):
    """
    Class implementing the plist reader.
    """
    file = None
    contents = b''
    offsets = None
    trailer = None
    currentOffset = 0
    
    def __init__(self, fileOrStream):
        """
        Constructor
        
        @param fileOrStream open file containing the plist data (file object)
        """
        self.reset()
        self.file = fileOrStream
    
    def parse(self):
        """
        Public method to parse the plist data.
        
        @return unpickled object
        """
        return self.readRoot()
    
    def reset(self):
        """
        Public method to reset the instance object.
        """
        self.trailer = None
        self.contents = b''
        self.offsets = []
        self.currentOffset = 0
    
    def readRoot(self):
        """
        Public method to read the root object.
        
        @return unpickled object
        @exception InvalidPlistException raised to indicate an invalid
            plist file
        """
        result = None
        self.reset()
        # Get the header, make sure it's a valid file.
        if not is_stream_binary_plist(self.file):
            raise NotBinaryPlistException()
        self.file.seek(0)
        self.contents = self.file.read()
        if len(self.contents) < 32:
            raise InvalidPlistException("File is too short.")
        trailerContents = self.contents[-32:]
        try:
            self.trailer = PlistTrailer._make(
                unpack("!xxxxxxBBQQQ", trailerContents))
            offset_size = self.trailer.offsetSize * self.trailer.offsetCount
            offset = self.trailer.offsetTableOffset
            offset_contents = self.contents[offset:offset + offset_size]
            offset_i = 0
            while offset_i < self.trailer.offsetCount:
                begin = self.trailer.offsetSize * offset_i
                tmp_contents = offset_contents[
                    begin:begin + self.trailer.offsetSize]
                tmp_sized = self.getSizedInteger(
                    tmp_contents, self.trailer.offsetSize)
                self.offsets.append(tmp_sized)
                offset_i += 1
            self.setCurrentOffsetToObjectNumber(
                self.trailer.topLevelObjectNumber)
            result = self.readObject()
        except TypeError as e:
            raise InvalidPlistException(e)
        return result
    
    def setCurrentOffsetToObjectNumber(self, objectNumber):
        """
        Public method to set the current offset.
        
        @param objectNumber number of the object (integer)
        """
        self.currentOffset = self.offsets[objectNumber]
    
    def readObject(self):
        """
        Public method to read the object data.
        
        @return unpickled object
        @exception InvalidPlistException raised to indicate an invalid
            plist file
        """
        result = None
        tmp_byte = self.contents[self.currentOffset:self.currentOffset + 1]
        marker_byte = unpack("!B", tmp_byte)[0]
        format = (marker_byte >> 4) & 0x0f
        extra = marker_byte & 0x0f
        self.currentOffset += 1
        
        def proc_extra(extra):
            if extra == 0b1111:
                #self.currentOffset += 1
                extra = self.readObject()
            return extra
        
        # bool, null, or fill byte
        if format == 0b0000:
            if extra == 0b0000:
                result = None
            elif extra == 0b1000:
                result = False
            elif extra == 0b1001:
                result = True
            elif extra == 0b1111:
                pass  # fill byte
            else:
                raise InvalidPlistException(
                    "Invalid object found at offset: {0}".format(
                        self.currentOffset - 1))
        # int
        elif format == 0b0001:
            extra = proc_extra(extra)
            result = self.readInteger(pow(2, extra))
        # real
        elif format == 0b0010:
            extra = proc_extra(extra)
            result = self.readReal(extra)
        # date
        elif format == 0b0011 and extra == 0b0011:
            result = self.readDate()
        # data
        elif format == 0b0100:
            extra = proc_extra(extra)
            result = self.readData(extra)
        # ascii string
        elif format == 0b0101:
            extra = proc_extra(extra)
            result = self.readAsciiString(extra)
        # Unicode string
        elif format == 0b0110:
            extra = proc_extra(extra)
            result = self.readUnicode(extra)
        # uid
        elif format == 0b1000:
            result = self.readUid(extra)
        # array
        elif format == 0b1010:
            extra = proc_extra(extra)
            result = self.readArray(extra)
        # set
        elif format == 0b1100:
            extra = proc_extra(extra)
            result = set(self.readArray(extra))
        # dict
        elif format == 0b1101:
            extra = proc_extra(extra)
            result = self.readDict(extra)
        else:
            raise InvalidPlistException(
                "Invalid object found: {{format: {0}, extra: {1}}}".format(
                    bin(format), bin(extra)))
        return result
    
    def readInteger(self, bytes):
        """
        Public method to read an Integer object.
        
        @param bytes length of the object (integer)
        @return integer object
        """
        result = 0
        original_offset = self.currentOffset
        data = self.contents[self.currentOffset:self.currentOffset + bytes]
        result = self.getSizedInteger(data, bytes)
        self.currentOffset = original_offset + bytes
        return result
    
    def readReal(self, length):
        """
        Public method to read a Real object.
        
        @param length length of the object (integer)
        @return float object
        @exception InvalidPlistException raised to indicate an invalid
            plist file
        """
        result = 0.0
        to_read = pow(2, length)
        data = self.contents[self.currentOffset:self.currentOffset + to_read]
        if length == 2:  # 4 bytes
            result = unpack('>f', data)[0]
        elif length == 3:  # 8 bytes
            result = unpack('>d', data)[0]
        else:
            raise InvalidPlistException(
                "Unknown real of length {0} bytes".format(to_read))
        return result
    
    def readRefs(self, count):
        """
        Public method to read References.
        
        @param count amount of the references (integer)
        @return list of references (list of integers)
        """
        refs = []
        i = 0
        while i < count:
            fragment = self.contents[
                self.currentOffset:
                self.currentOffset + self.trailer.objectRefSize]
            ref = self.getSizedInteger(fragment, len(fragment))
            refs.append(ref)
            self.currentOffset += self.trailer.objectRefSize
            i += 1
        return refs
    
    def readArray(self, count):
        """
        Public method to read an Array object.
        
        @param count number of array elements (integer)
        @return list of unpickled objects
        """
        result = []
        values = self.readRefs(count)
        i = 0
        while i < len(values):
            self.setCurrentOffsetToObjectNumber(values[i])
            value = self.readObject()
            result.append(value)
            i += 1
        return result
    
    def readDict(self, count):
        """
        Public method to read a Dictionary object.
        
        @param count number of dictionary elements (integer)
        @return dictionary of unpickled objects
        """
        result = {}
        keys = self.readRefs(count)
        values = self.readRefs(count)
        i = 0
        while i < len(keys):
            self.setCurrentOffsetToObjectNumber(keys[i])
            key = self.readObject()
            self.setCurrentOffsetToObjectNumber(values[i])
            value = self.readObject()
            result[key] = value
            i += 1
        return result
    
    def readAsciiString(self, length):
        """
        Public method to read an ASCII encoded string.
        
        @param length length of the string (integer)
        @return ASCII encoded string
        """
        result = str(unpack(
            "!{0}s".format(length),
            self.contents[self.currentOffset:self.currentOffset + length])[0],
            encoding="ascii")
        self.currentOffset += length
        return result
    
    def readUnicode(self, length):
        """
        Public method to read an Unicode encoded string.
        
        @param length length of the string (integer)
        @return unicode encoded string
        """
        actual_length = length * 2
        data = self.contents[
            self.currentOffset:self.currentOffset + actual_length]
        # unpack not needed?!! data = unpack(">%ds" % (actual_length), data)[0]
        self.currentOffset += actual_length
        return data.decode('utf_16_be')
    
    def readDate(self):
        """
        Public method to read a date.
        
        @return date object (datetime.datetime)
        """
        global apple_reference_date_offset
        result = unpack(
            ">d",
            self.contents[self.currentOffset:self.currentOffset + 8])[0]
        result = datetime.datetime.utcfromtimestamp(
            result + apple_reference_date_offset)
        self.currentOffset += 8
        return result
    
    def readData(self, length):
        """
        Public method to read some bytes.
        
        @param length number of bytes to read (integer)
        @return Data object
        """
        result = self.contents[self.currentOffset:self.currentOffset + length]
        self.currentOffset += length
        return Data(result)
    
    def readUid(self, length):
        """
        Public method to read a UID.
        
        @param length length of the UID (integer)
        @return Uid object
        """
        return Uid(self.readInteger(length + 1))
    
    def getSizedInteger(self, data, bytes):
        """
        Public method to read an integer of a specific size.
        
        @param data data to extract the integer from (bytes)
        @param bytes length of the integer (integer)
        @return read integer (integer)
        @exception InvalidPlistException raised to indicate an invalid
            plist file
        """
        result = 0
        # 1, 2, and 4 byte integers are unsigned
        if bytes == 1:
            result = unpack('>B', data)[0]
        elif bytes == 2:
            result = unpack('>H', data)[0]
        elif bytes == 4:
            result = unpack('>L', data)[0]
        elif bytes == 8:
            result = unpack('>q', data)[0]
        else:
            raise InvalidPlistException(
                "Encountered integer longer than 8 bytes.")
        return result


class HashableWrapper(object):
    """
    Class wrapping a hashable value.
    """
    def __init__(self, value):
        """
        Constructor
        
        @param value object value
        """
        self.value = value

    def __repr__(self):
        """
        Special method to generate a representation of the object.
        
        @return object representation (string)
        """
        return "<HashableWrapper: %s>" % [self.value]


class BoolWrapper(object):
    """
    Class wrapping a boolean value.
    """
    def __init__(self, value):
        """
        Constructor
        
        @param value object value (boolean)
        """
        self.value = value

    def __repr__(self):
        """
        Special method to generate a representation of the object.
        
        @return object representation (string)
        """
        return "<BoolWrapper: %s>" % self.value


class PlistWriter(object):
    """
    Class implementing the plist writer.
    """
    header = b'bplist00bybiplist1.0'
    file = None
    byteCounts = None
    trailer = None
    computedUniques = None
    writtenReferences = None
    referencePositions = None
    wrappedTrue = None
    wrappedFalse = None
    
    def __init__(self, file):
        """
        Constructor
        
        @param file file to write the plist data to (file object)
        """
        self.reset()
        self.file = file
        self.wrappedTrue = BoolWrapper(True)
        self.wrappedFalse = BoolWrapper(False)

    def reset(self):
        """
        Public method to reset the instance object.
        """
        self.byteCounts = PlistByteCounts(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self.trailer = PlistTrailer(0, 0, 0, 0, 0)
        
        # A set of all the uniques which have been computed.
        self.computedUniques = set()
        # A list of all the uniques which have been written.
        self.writtenReferences = {}
        # A dict of the positions of the written uniques.
        self.referencePositions = {}
        
    def positionOfObjectReference(self, obj):
        """
        Public method to get the position of an object.
        
        If the given object has been written already, return its
        position in the offset table. Otherwise, return None.
        
        @param obj object
        @return position of the object (integer)
        """
        return self.writtenReferences.get(obj)
        
    def writeRoot(self, root):
        """
        Public method to write an object to a plist file.
        
        Strategy is:
        <ul>
        <li>write header</li>
        <li>wrap root object so everything is hashable</li>
        <li>compute size of objects which will be written
          <ul>
          <li>need to do this in order to know how large the object refs
            will be in the list/dict/set reference lists</li>
        </ul></li>
        <li>write objects
          <ul>
          <li>keep objects in writtenReferences</li>
          <li>keep positions of object references in referencePositions</li>
          <li>write object references with the length computed previously</li>
        </ul></li>
        <li>computer object reference length</li>
        <li>write object reference positions</li>
        <li>write trailer</li>
        </ul>
        
        @param root reference to the object to be written
        """
        output = self.header
        wrapped_root = self.wrapRoot(root)
        should_reference_root = True
        self.computeOffsets(
            wrapped_root, asReference=should_reference_root, isRoot=True)
        self.trailer = self.trailer._replace(
            **{'objectRefSize': self.intSize(len(self.computedUniques))})
        (_, output) = self.writeObjectReference(wrapped_root, output)
        output = self.writeObject(
            wrapped_root, output, setReferencePosition=True)
        
        # output size at this point is an upper bound on how big the
        # object reference offsets need to be.
        self.trailer = self.trailer._replace(**{
            'offsetSize': self.intSize(len(output)),
            'offsetCount': len(self.computedUniques),
            'offsetTableOffset': len(output),
            'topLevelObjectNumber': 0
        })
        
        output = self.writeOffsetTable(output)
        output += pack('!xxxxxxBBQQQ', *self.trailer)
        self.file.write(output)
    
    def wrapRoot(self, root):
        """
        Public method to generate object wrappers.
        
        @param root object to be wrapped
        @return wrapped object
        """
        if isinstance(root, bool):
            if root is True:
                return self.wrappedTrue
            else:
                return self.wrappedFalse
        elif isinstance(root, set):
            n = set()
            for value in root:
                n.add(self.wrapRoot(value))
            return HashableWrapper(n)
        elif isinstance(root, dict):
            n = {}
            for key, value in root.items():
                n[self.wrapRoot(key)] = self.wrapRoot(value)
            return HashableWrapper(n)
        elif isinstance(root, list):
            n = []
            for value in root:
                n.append(self.wrapRoot(value))
            return HashableWrapper(n)
        elif isinstance(root, tuple):
            n = tuple([self.wrapRoot(value) for value in root])
            return HashableWrapper(n)
        else:
            return root

    def incrementByteCount(self, field, incr=1):
        """
        Public method to increment the byte count.
        
        @param field field to evaluate
        @param incr byte count increment (integer)
        """
        self.byteCounts = self.byteCounts._replace(
            **{field: self.byteCounts.__getattribute__(field) + incr})

    def __checkKey(self, key):
        """
        Private method to check the validity of a key.
        
        @param key key to be checked
        @exception InvalidPlistException raised to indicate an invalid
            plist file
        """
        if key is None:
            raise InvalidPlistException(
                'Dictionary keys cannot be null in plists.')
        elif isinstance(key, Data):
            raise InvalidPlistException(
                'Data cannot be dictionary keys in plists.')
        elif not isinstance(key, str):
            raise InvalidPlistException('Keys must be strings.')
    
    def __processSize(self, size):
        """
        Private method to process a size.
        
        @param size size value to be processed (int)
        @return processed size (int)
        """
        if size > 0b1110:
            size += self.intSize(size)
        return size
    
    def computeOffsets(self, obj, asReference=False, isRoot=False):
        """
        Public method to compute offsets of an object.
        
        @param obj plist object
        @param asReference flag indicating offsets as references (boolean)
        @param isRoot flag indicating a root object (boolean)
        @exception InvalidPlistException raised to indicate an invalid
            plist file
        """
        # If this should be a reference, then we keep a record of it in the
        # uniques table.
        if asReference:
            if obj in self.computedUniques:
                return
            else:
                self.computedUniques.add(obj)
        
        if obj is None:
            self.incrementByteCount('nullBytes')
        elif isinstance(obj, BoolWrapper):
            self.incrementByteCount('boolBytes')
        elif isinstance(obj, Uid):
            size = self.intSize(obj)
            self.incrementByteCount('uidBytes', incr=1 + size)
        elif isinstance(obj, int):
            size = self.intSize(obj)
            self.incrementByteCount('intBytes', incr=1 + size)
        elif isinstance(obj, (float)):
            size = self.realSize(obj)
            self.incrementByteCount('realBytes', incr=1 + size)
        elif isinstance(obj, datetime.datetime):
            self.incrementByteCount('dateBytes', incr=2)
        elif isinstance(obj, Data):
            size = self.__processSize(len(obj))
            self.incrementByteCount('dataBytes', incr=1 + size)
        elif isinstance(obj, str):
            size = self.__processSize(len(obj))
            self.incrementByteCount('stringBytes', incr=1 + size)
        elif isinstance(obj, HashableWrapper):
            obj = obj.value
            if isinstance(obj, set):
                size = self.__processSize(len(obj))
                self.incrementByteCount('setBytes', incr=1 + size)
                for value in obj:
                    self.computeOffsets(value, asReference=True)
            elif isinstance(obj, (list, tuple)):
                size = self.__processSize(len(obj))
                self.incrementByteCount('arrayBytes', incr=1 + size)
                for value in obj:
                    self.computeOffsets(value, asReference=True)
            elif isinstance(obj, dict):
                size = self.__processSize(len(obj))
                self.incrementByteCount('dictBytes', incr=1 + size)
                for key, value in obj.items():
                    self.__checkKey(key)
                    self.computeOffsets(key, asReference=True)
                    self.computeOffsets(value, asReference=True)
        else:
            raise InvalidPlistException("Unknown object type.")

    def writeObjectReference(self, obj, output):
        """
        Public method to write an object reference.
        
        Tries to write an object reference, adding it to the references
        table. Does not write the actual object bytes or set the reference
        position. Returns a tuple of whether the object was a new reference
        (True if it was, False if it already was in the reference table)
        and the new output.
        
        @param obj object to be written
        @param output output stream to append the object to
        @return flag indicating a new reference and the new output
        """
        position = self.positionOfObjectReference(obj)
        if position is None:
            self.writtenReferences[obj] = len(self.writtenReferences)
            output += self.binaryInt(len(self.writtenReferences) - 1,
                                     bytes=self.trailer.objectRefSize)
            return (True, output)
        else:
            output += self.binaryInt(
                position, bytes=self.trailer.objectRefSize)
            return (False, output)

    def writeObject(self, obj, output, setReferencePosition=False):
        """
        Public method to serialize the given object to the output.
        
        @param obj object to be serialized
        @param output output to be serialized to (bytes)
        @param setReferencePosition flag indicating, that the reference
            position the object was written to shall be recorded (boolean)
        @return new output
        """
        def proc_variable_length(format, length):
            result = ''
            if length > 0b1110:
                result += pack('!B', (format << 4) | 0b1111)
                result = self.writeObject(length, result)
            else:
                result += pack('!B', (format << 4) | length)
            return result
        
        if setReferencePosition:
            self.referencePositions[obj] = len(output)
        
        if obj is None:
            output += pack('!B', 0b00000000)
        elif isinstance(obj, BoolWrapper):
            if obj.value is False:
                output += pack('!B', 0b00001000)
            else:
                output += pack('!B', 0b00001001)
        elif isinstance(obj, Uid):
            size = self.intSize(obj)
            output += pack('!B', (0b1000 << 4) | size - 1)
            output += self.binaryInt(obj)
        elif isinstance(obj, int):
            bytes = self.intSize(obj)
            root = math.log(bytes, 2)
            output += pack('!B', (0b0001 << 4) | int(root))
            output += self.binaryInt(obj)
        elif isinstance(obj, float):
            # just use doubles
            output += pack('!B', (0b0010 << 4) | 3)
            output += self.binaryReal(obj)
        elif isinstance(obj, datetime.datetime):
            timestamp = calendar.timegm(obj.utctimetuple())
            timestamp -= apple_reference_date_offset
            output += pack('!B', 0b00110011)
            output += pack('!d', float(timestamp))
        elif isinstance(obj, Data):
            output += proc_variable_length(0b0100, len(obj))
            output += obj
        elif isinstance(obj, str):
            # Python 3 uses unicode strings only
            bytes = obj.encode('utf_16_be')
            output += proc_variable_length(0b0110, len(bytes) / 2)
            output += bytes
        elif isinstance(obj, HashableWrapper):
            obj = obj.value
            if isinstance(obj, (set, list, tuple)):
                if isinstance(obj, set):
                    output += proc_variable_length(0b1100, len(obj))
                else:
                    output += proc_variable_length(0b1010, len(obj))
            
                objectsToWrite = []
                for objRef in obj:
                    (isNew, output) = self.writeObjectReference(objRef, output)
                    if isNew:
                        objectsToWrite.append(objRef)
                for objRef in objectsToWrite:
                    output = self.writeObject(
                        objRef, output, setReferencePosition=True)
            elif isinstance(obj, dict):
                output += proc_variable_length(0b1101, len(obj))
                keys = []
                values = []
                objectsToWrite = []
                for key, value in obj.items():
                    keys.append(key)
                    values.append(value)
                for key in keys:
                    (isNew, output) = self.writeObjectReference(key, output)
                    if isNew:
                        objectsToWrite.append(key)
                for value in values:
                    (isNew, output) = self.writeObjectReference(value, output)
                    if isNew:
                        objectsToWrite.append(value)
                for objRef in objectsToWrite:
                    output = self.writeObject(
                        objRef, output, setReferencePosition=True)
        return output
    
    def writeOffsetTable(self, output):
        """
        Public method to write all of the object reference offsets.
        
        @param output current output (bytes)
        @return new output (bytes)
        @exception InvalidPlistException raised to indicate an invalid
            plist file
        """
        all_positions = []
        writtenReferences = list(self.writtenReferences.items())
        writtenReferences.sort(key=lambda x: x[1])
        for obj, order in writtenReferences:
            position = self.referencePositions.get(obj)
            if position is None:
                raise InvalidPlistException(
                    "Error while writing offsets table. Object not found. {0}"
                    .format(obj))
            output += self.binaryInt(position, self.trailer.offsetSize)
            all_positions.append(position)
        return output
    
    def binaryReal(self, obj):
        """
        Public method to pack a real object.
        
        @param obj real to be packed
        @return serialized object (bytes)
        """
        # just use doubles
        result = pack('>d', obj)
        return result
    
    def binaryInt(self, obj, bytes=None):
        """
        Public method to pack an integer object.
        
        @param obj integer to be packed
        @param bytes length the integer should be packed into (integer)
        @return serialized object (bytes)
        @exception InvalidPlistException raised to indicate an invalid
            plist file
        """
        result = ''
        if bytes is None:
            bytes = self.intSize(obj)
        if bytes == 1:
            result += pack('>B', obj)
        elif bytes == 2:
            result += pack('>H', obj)
        elif bytes == 4:
            result += pack('>L', obj)
        elif bytes == 8:
            result += pack('>q', obj)
        else:
            raise InvalidPlistException(
                "Core Foundation can't handle integers with size greater"
                " than 8 bytes.")
        return result
    
    def intSize(self, obj):
        """
        Public method to determine the number of bytes necessary to store the
        given integer.
        
        @param obj integer object
        @return number of bytes required (integer)
        @exception InvalidPlistException raised to indicate an invalid
            plist file
        """
        # SIGNED
        if obj < 0:  # Signed integer, always 8 bytes
            return 8
        # UNSIGNED
        elif obj <= 0xFF:  # 1 byte
            return 1
        elif obj <= 0xFFFF:  # 2 bytes
            return 2
        elif obj <= 0xFFFFFFFF:  # 4 bytes
            return 4
        # SIGNED
        # 0x7FFFFFFFFFFFFFFF is the max.
        elif obj <= 0x7FFFFFFFFFFFFFFF:  # 8 bytes
            return 8
        else:
            raise InvalidPlistException(
                "Core Foundation can't handle integers with size greater"
                " than 8 bytes.")
    
    def realSize(self, obj):
        """
        Public method to determine the number of bytes necessary to store the
        given real.
        
        @param obj real object
        @return number of bytes required (integer)
        """
        return 8
