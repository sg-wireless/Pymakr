# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 Tobias Rzepka <tobias.rzepka@gmail.com>
#

"""
Module implementing some workarounds to let eric6 run under Python 2.
"""


import __builtin__
import codecs
import imp
import locale
import os
import sys

# convert all command line arguments to unicode
sys.argv = [arg.decode(locale.getpreferredencoding()) for arg in sys.argv]

"""
Improvement for the os.path.join function because the original join doesn't
use the correct encoding.
"""
# Save original function for use in joinAsUnicode
__join = os.path.join
# Flag to disable unicode conversion of join function
os.path.join_unicode = True


def joinAsUnicode(*args):
    """
    Convert none unicode parameter of the os.path.join into unicode.
    
    @param args paths which should be joined (str, unicode)
    @return unicode str of the path (unicode)
    """
    if os.path.join_unicode:
        convArgs = []
        for arg in args:
            if isinstance(arg, str):
                arg = arg.decode(locale.getpreferredencoding(), 'replace')
            convArgs.append(arg)
        return __join(*convArgs)
    else:
        return __join(*args)

# Replace os.path.join with unicode aware version
os.path.join = joinAsUnicode

"""
Improvement for the imp.load_source and imp.find_module functions because the
originals doesn't use the correct encoding.
"""
# Save original function for use in load_sourceAsStr and find_moduleAsStr
__load_source = imp.load_source
__find_module = imp.find_module


def load_sourceAsStr(*args):
    """
    Convert none str parameter of the imp.load_source into str.
    
    @param args  (str, unicode)
    @return list of args converted to str (list)
    """
    convArgs = []
    for arg in args:
        if isinstance(arg, unicode):
            arg = arg.encode(sys.getfilesystemencoding(), 'strict')
        convArgs.append(arg)
    return __load_source(*convArgs)


def find_moduleAsStr(*args):
    """
    Convert none str parameter of the imp.find_module into str.
    
    @param args  (str, unicode)
    @return list of args converted to str (list)
    """
    convArgs = []
    for arg in args:
        if isinstance(arg, unicode):
            arg = arg.encode(sys.getfilesystemencoding(), 'strict')
        convArgs.append(arg)
    return __find_module(*convArgs)
    
# Replace imp.load_source and imp.find_module with unicode aware version
imp.load_source = load_sourceAsStr
imp.find_module = find_moduleAsStr

"""
Improvement for the sys.path list because some other functions doesn't expect
unicode in the sys.path list.
"""


class PlainStrList(list):
    """
    Keep track that all added paths to sys.path are str.
    """
    def __init__(self, *args):
        """
        Constructor
        
        @param args list of paths to start with (list)
        """
        super(PlainStrList, self).__init__()
        self.extend(list(args))

    def __convert(self, element):
        """
        Private method to convert unicode to file system encoding.
        
        @param element to convert from unicode to file system encoding (any)
        @return converted element
        """
        if isinstance(element, unicode):
            # Throw exception if it can't be converted, otherwise exception
            # could occur somewhere else
            element = element.encode(sys.getfilesystemencoding(), 'strict')
        return element

    def __setitem__(self, idx, value):
        """
        Special method to overwrite a specific list item.
        
        @param idx index of the item (int)
        @param value the new value (any)
        """
        super(PlainStrList, self).__setitem__(idx, self.__convert(value))

    def insert(self, idx, value):
        """
        Public method to insert a specific list item.
        
        @param idx index of the item (int)
        @param value the new value (any)
        """
        super(PlainStrList, self).insert(idx, self.__convert(value))


# insert a conversion function from unicode to str at sys.path access
sys.path = PlainStrList(*sys.path)

"""
The open function and File class simulates the open behaviour of Python3.

The Eric6 used features are emulated only. The not emulated features
should throw a NotImplementedError exception.
"""


def open(file, mode='r', buffering=-1, encoding=None,
         errors=None, newline=None, closefd=True):
    """
    Replacement for the build in open function.
    
    @param file filename or file descriptor (string)
    @keyparam mode access mode (string)
    @keyparam buffering size of the read buffer (string)
    @keyparam encoding character encoding for reading/ writing (string)
    @keyparam errors behavior for the character encoding ('strict',
        'explicit', ...) (string)
    @keyparam newline controls how universal newlines works (string)
    @keyparam closefd close underlying file descriptor if given as file
        parameter (boolean)
    @return Returns the new file object
    """
    return File(file, mode, buffering, encoding, errors, newline, closefd)


class File(file):   # __IGNORE_WARNING__
    """
    Facade for the original file class.
    """
    def __init__(self, filein, mode='r', buffering=-1,
                 encoding=None, errors=None, newline=None, closefd=True):
        """
        Constructor
        
        It checks for unimplemented parameters.
        
        @param filein filename or file descriptor (string)
        @keyparam mode access mode (string)
        @keyparam buffering size of the read buffer (string)
        @keyparam encoding character encoding for reading/ writing (string)
        @keyparam errors behavior for the character encoding ('strict',
            'explicit', ...) (string)
        @keyparam newline controls how universal newlines works (string)
        @keyparam closefd close underlying file descriptor if given as file
            parameter (boolean)
        @exception NotImplementedError for not implemented method parameters
        """
        self.__encoding = encoding
        self.__newline = str(newline)
        self.__closefd = closefd
        if newline is not None:
            if 'r' in mode:
                raise NotImplementedError
            else:
                mode = mode.replace('t', 'b')
                if 'b' not in mode:
                    mode = mode + 'b'

        if closefd is False:
            raise NotImplementedError

        if errors is None:
            self.__errors = 'strict'
        else:
            self.__errors = errors

        file.__init__(self, filein, mode, buffering)    # __IGNORE_WARNING__

    def read(self, n=-1):
        """
        Public method to read n bytes or all if n=-1 from file.
        
        @keyparam n bytecount or all if n=-1 (int)
        @return decoded bytes read
        """
        txt = super(File, self).read(n)
        if self.__encoding is None:
            return txt
        else:
            return codecs.decode(txt, self.__encoding)

    def readline(self, limit=-1):
        """
        Public method to read one line from file.
        
        @keyparam limit maximum bytes to read or all if limit=-1 (int)
        @return decoded line read
        """
        txt = super(File, self).readline(limit)
        if self.__encoding is None:
            return txt
        else:
            return codecs.decode(txt, self.__encoding)

    def readlines(self, hint=-1):
        """
        Public method to read all lines from file.
        
        @keyparam hint maximum bytes to read or all if hint=-1 (int)
        @return decoded lines read
        """
        if self.__encoding is None:
            return super(File, self).readlines(hint)
        else:
            return [codecs.decode(txt, self.__encoding)
                    for txt in super(File, self).readlines(hint)]

    def write(self, txt):
        """
        Public method to write given data to file and encode if needed.
        
        @param txt data to write. (str, bytes)
        """
        if self.__encoding is not None:
            txt = codecs.encode(txt, self.__encoding, self.__errors)
        elif isinstance(txt, unicode):
            txt = codecs.encode(txt, 'utf-8', self.__errors)

        if self.__newline in ['\r\n', '\r']:
            txt = txt.replace('\n', self.__newline)

        super(File, self).write(txt)

    def next(self):
        """
        Public method used in an iterator.
        
        @return decoded data read
        """
        txt = super(File, self).next()
        if self.__encoding is None:
            return txt
        else:
            return codecs.decode(txt, self.__encoding)

# Inject into the __builtin__ dictionary
__builtin__.open = open

#
# eflag: FileType = Python2
# eflag: noqa = M702
