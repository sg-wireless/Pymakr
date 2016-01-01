# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Package implementing various functions/classes needed everywhere within eric6.
"""

from __future__ import unicode_literals
try:
    str = unicode
    import locale
    import urllib

    def quote(url):
        """
        Replacement for the urllib.quote function because of unicode problems.
        
        @param url text to quote (string)
        @return quoted url (string)
        """
        return urllib.quote(url.encode('utf-8'))
except NameError:
    basestring = str
    from urllib.parse import quote    # __IGNORE_WARNING__

import os
import sys
import codecs
import re
import fnmatch
import glob
import getpass


def __showwarning(message, category, filename, lineno, file=None, line=""):
    """
    Module function to raise a SyntaxError for a SyntaxWarning.
    
    @param message warning object
    @param category type object of the warning
    @param filename name of the file causing the warning (string)
    @param lineno line number causing the warning (integer)
    @param file file to write the warning message to (ignored)
    @param line line causing the warning (ignored)
    @raise SyntaxError
    """
    if category is SyntaxWarning:
        err = SyntaxError(str(message))
        err.filename = filename
        err.lineno = lineno
        raise err
    
import warnings
warnings.showwarning = __showwarning

from codecs import BOM_UTF8, BOM_UTF16, BOM_UTF32

from PyQt5.QtCore import QRegExp, QDir, QProcess, Qt, QByteArray, \
    qVersion, PYQT_VERSION_STR, QCoreApplication, QCryptographicHash
from PyQt5.Qsci import QSCINTILLA_VERSION_STR, QsciScintilla

# import these methods into the Utilities namespace
from Globals import (  # __IGNORE_WARNING__
    isWindowsPlatform, isLinuxPlatform, isMacPlatform, getConfigDir,
    setConfigDir, getPythonModulesDirectory, getPyQt5ModulesDirectory,
    getQtBinariesPath)

from E5Gui.E5Application import e5App

from UI.Info import Program, Version

import Preferences
from Plugins.CheckerPlugins.SyntaxChecker.SyntaxCheck import (  # __IGNORE_WARNING__
    normalizeCode)

from eric6config import getConfig

configDir = None

codingBytes_regexps = [
    (2, re.compile(br'''coding[:=]\s*([-\w_.]+)''')),
    (1, re.compile(br'''<\?xml.*\bencoding\s*=\s*['"]([-\w_.]+)['"]\?>''')),
]
coding_regexps = [
    (2, re.compile(r'''coding[:=]\s*([-\w_.]+)''')),
    (1, re.compile(r'''<\?xml.*\bencoding\s*=\s*['"]([-\w_.]+)['"]\?>''')),
]

supportedCodecs = [
    'utf-8',
    'iso8859-1', 'iso8859-15', 'iso8859-2', 'iso8859-3',
    'iso8859-4', 'iso8859-5', 'iso8859-6', 'iso8859-7',
    'iso8859-8', 'iso8859-9', 'iso8859-10', 'iso8859-11',
    'iso8859-13', 'iso8859-14', 'iso8859-16', 'latin-1',
    'koi8-r', 'koi8-u',
    'utf-16', 'utf-32',
    'cp037', 'cp424', 'cp437', 'cp500', 'cp737', 'cp775',
    'cp850', 'cp852', 'cp855', 'cp856', 'cp857', 'cp860',
    'cp861', 'cp862', 'cp863', 'cp864', 'cp865', 'cp866',
    'cp869', 'cp874', 'cp875', 'cp932', 'cp949', 'cp950',
    'cp1006', 'cp1026', 'cp1140', 'cp1250', 'cp1251',
    'cp1252', 'cp1253', 'cp1254', 'cp1255', 'cp1256',
    'cp1257', 'cp1258',
    'gb2312', 'gb18030',
    'ascii'
]


class CodingError(Exception):
    """
    Class implementing an exception, which is raised, if a given coding is
    incorrect.
    """
    def __init__(self, coding):
        """
        Constructor
        
        @param coding coding to include in the message (string)
        """
        self.errorMessage = QCoreApplication.translate(
            "CodingError",
            "The coding '{0}' is wrong for the given text.").format(coding)
        
    def __repr__(self):
        """
        Special method returning a representation of the exception.
        
        @return string representing the error message
        """
        return str(self.errorMessage)
        
    def __str__(self):
        """
        Special method returning a string representation of the exception.
        
        @return string representing the error message
        """
        return str(self.errorMessage)
    

def get_codingBytes(text):
    """
    Function to get the coding of a bytes text.
    
    @param text bytes text to inspect (bytes)
    @return coding string
    """
    lines = text.splitlines()
    for coding in codingBytes_regexps:
        coding_re = coding[1]
        head = lines[:coding[0]]
        for l in head:
            m = coding_re.search(l)
            if m:
                return str(m.group(1), "ascii").lower()
    return None


def get_coding(text):
    """
    Function to get the coding of a text.
    
    @param text text to inspect (string)
    @return coding string
    """
    lines = text.splitlines()
    for coding in coding_regexps:
        coding_re = coding[1]
        head = lines[:coding[0]]
        for l in head:
            m = coding_re.search(l)
            if m:
                return m.group(1).lower()
    return None


def readEncodedFile(filename):
    """
    Function to read a file and decode its contents into proper text.
    
    @param filename name of the file to read (string)
    @return tuple of decoded text and encoding (string, string)
    """
    f = open(filename, "rb")
    text = f.read()
    f.close()
    return decode(text)


def readEncodedFileWithHash(filename):
    """
    Function to read a file, calculate a hash value and decode its contents
    into proper text.
    
    @param filename name of the file to read (string)
    @return tuple of decoded text, encoding and hash value (string, string,
        string)
    """
    f = open(filename, "rb")
    text = f.read()
    f.close()
    hash = str(QCryptographicHash.hash(
               QByteArray(text), QCryptographicHash.Md5).toHex(),
               encoding="ASCII")
    return decode(text) + (hash, )


def decode(text):
    """
    Function to decode some byte text into a string.
    
    @param text byte text to decode (bytes)
    @return tuple of decoded text and encoding (string, string)
    """
    try:
        if text.startswith(BOM_UTF8):
            # UTF-8 with BOM
            return str(text[len(BOM_UTF8):], 'utf-8'), 'utf-8-bom'
        elif text.startswith(BOM_UTF16):
            # UTF-16 with BOM
            return str(text[len(BOM_UTF16):], 'utf-16'), 'utf-16'
        elif text.startswith(BOM_UTF32):
            # UTF-32 with BOM
            return str(text[len(BOM_UTF32):], 'utf-32'), 'utf-32'
        coding = get_codingBytes(text)
        if coding:
            return str(text, coding), coding
    except (UnicodeError, LookupError):
        pass
    
    # Assume UTF-8
    try:
        return str(text, 'utf-8'), 'utf-8-guessed'
    except (UnicodeError, LookupError):
        pass
    
    guess = None
    if Preferences.getEditor("AdvancedEncodingDetection"):
        # Try the universal character encoding detector
        try:
            import ThirdParty.CharDet.chardet
            guess = ThirdParty.CharDet.chardet.detect(text)
            if guess and guess['confidence'] > 0.95 and \
                    guess['encoding'] is not None:
                codec = guess['encoding'].lower()
                return str(text, codec), '{0}-guessed'.format(codec)
        except (UnicodeError, LookupError):
            pass
        except ImportError:
            pass
    
    # Try default encoding
    try:
        codec = Preferences.getEditor("DefaultEncoding")
        return str(text, codec), '{0}-default'.format(codec)
    except (UnicodeError, LookupError):
        pass
    
    if Preferences.getEditor("AdvancedEncodingDetection"):
        # Use the guessed one even if confifence level is low
        if guess and guess['encoding'] is not None:
            try:
                codec = guess['encoding'].lower()
                return str(text, codec), '{0}-guessed'.format(codec)
            except (UnicodeError, LookupError):
                pass
    
    # Assume UTF-8 loosing information
    return str(text, "utf-8", "ignore"), 'utf-8-ignore'


def readEncodedFileWithEncoding(filename, encoding):
    """
    Function to read a file and decode its contents into proper text.
    
    @param filename name of the file to read (string)
    @keyparam encoding encoding to be used to read the file (string)
    @return tuple of decoded text and encoding (string, string)
    """
    f = open(filename, "rb")
    text = f.read()
    f.close()
    if encoding:
        try:
            return str(text, encoding), '{0}-selected'.format(encoding)
        except (UnicodeError, LookupError):
            pass
        # Try default encoding
        try:
            codec = Preferences.getEditor("DefaultEncoding")
            return str(text, codec), '{0}-default'.format(codec)
        except (UnicodeError, LookupError):
            pass
        # Assume UTF-8 loosing information
        return str(text, "utf-8", "ignore"), 'utf-8-ignore'
    else:
        return decode(text)


def writeEncodedFile(filename, text, orig_coding):
    """
    Function to write a file with properly encoded text.
    
    @param filename name of the file to read (string)
    @param text text to be written (string)
    @param orig_coding type of the original encoding (string)
    @return encoding used for writing the file (string)
    """
    etext, encoding = encode(text, orig_coding)
    
    f = open(filename, "wb")
    f.write(etext)
    f.close()
    
    return encoding


def encode(text, orig_coding):
    """
    Function to encode text into a byte text.
    
    @param text text to be encoded (string)
    @param orig_coding type of the original encoding (string)
    @return tuple of encoded text and encoding used (bytes, string)
    @exception CodingError raised to indicate an invalid encoding
    """
    encoding = None
    if orig_coding == 'utf-8-bom':
        etext, encoding = BOM_UTF8 + text.encode("utf-8"), 'utf-8-bom'
    else:
        # Try declared coding spec
        coding = get_coding(text)
        if coding:
            try:
                etext, encoding = text.encode(coding), coding
            except (UnicodeError, LookupError):
                # Error: Declared encoding is incorrect
                raise CodingError(coding)
        else:
            if orig_coding and orig_coding.endswith(
                    ('-selected', '-default', '-guessed', '-ignore')):
                coding = orig_coding\
                    .replace("-selected", "")\
                    .replace("-default", "")\
                    .replace("-guessed", "")\
                    .replace("-ignore", "")
                try:
                    etext, encoding = text.encode(coding), coding
                except (UnicodeError, LookupError):
                    pass
            
            if encoding is None:
                # Try configured default
                try:
                    codec = Preferences.getEditor("DefaultEncoding")
                    etext, encoding = text.encode(codec), codec
                except (UnicodeError, LookupError):
                    pass
                
                if encoding is None:
                    # Try saving as ASCII
                    try:
                        etext, encoding = text.encode('ascii'), 'ascii'
                    except UnicodeError:
                        pass
                    
                    if encoding is None:
                        # Save as UTF-8 without BOM
                        etext, encoding = text.encode('utf-8'), 'utf-8'
    
    return etext, encoding


def decodeString(text):
    """
    Function to decode a string containing Unicode encoded characters.
    
    @param text text containing encoded chars (string)
    @return decoded text (string)
    """
    buf = b""
    index = 0
    while index < len(text):
        if text[index] == "\\":
            qb = QByteArray.fromHex(text[index:index + 4])
            buf += bytes(qb)
            index += 4
        else:
            buf += codecs.encode(text[index], "utf-8")
            index += 1
    buf = buf.replace(b"\x00", b"")
    return decodeBytes(buf)
    

def decodeBytes(buffer):
    """
    Function to decode some byte text into a string.
    
    @param buffer byte buffer to decode (bytes)
    @return decoded text (string)
    """
    # try UTF with BOM
    try:
        if buffer.startswith(BOM_UTF8):
            # UTF-8 with BOM
            return str(buffer[len(BOM_UTF8):], encoding='utf-8')
        elif buffer.startswith(BOM_UTF16):
            # UTF-16 with BOM
            return str(buffer[len(BOM_UTF16):], encoding='utf-16')
        elif buffer.startswith(BOM_UTF32):
            # UTF-32 with BOM
            return str(buffer[len(BOM_UTF32):], encoding='utf-32')
    except (UnicodeError, LookupError):
        pass
    
    # try UTF-8
    try:
        return str(buffer, encoding="utf-8")
    except UnicodeError:
        pass
    
    # try codec detection
    try:
        import ThirdParty.CharDet.chardet
        guess = ThirdParty.CharDet.chardet.detect(buffer)
        if guess and guess['encoding'] is not None:
            codec = guess['encoding'].lower()
            return str(buffer, encoding=codec)
    except (UnicodeError, LookupError):
        pass
    except ImportError:
        pass
    
    return str(buffer, encoding="utf-8", errors="ignore")


def readStringFromStream(stream):
    """
    Module function to read a string from the given stream.
    
    @param stream data stream opened for reading (QDataStream)
    @return string read from the stream (string)
    """
    data = stream.readString()
    if data is None:
        data = b""
    return data.decode('utf-8')


_escape = re.compile("[&<>\"'\u0080-\uffff]")

_escape_map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#x27;",
}


def escape_entities(m, map=_escape_map):
    """
    Function to encode html entities.
    
    @param m the match object
    @param map the map of entities to encode
    @return the converted text (string)
    """
    char = m.group()
    text = map.get(char)
    if text is None:
        text = "&#{0:d};".format(ord(char))
    return text
    

def html_encode(text, pattern=_escape):
    """
    Function to correctly encode a text for html.
    
    @param text text to be encoded (string)
    @param pattern search pattern for text to be encoded (string)
    @return the encoded text (string)
    """
    if not text:
        return ""
    text = pattern.sub(escape_entities, text)
    return text

_uescape = re.compile('[\u0080-\uffff]')


def escape_uentities(m):
    """
    Function to encode html entities.
    
    @param m the match object
    @return the converted text (string)
    """
    char = m.group()
    text = "&#{0:d};".format(ord(char))
    return text
    

def html_uencode(text, pattern=_uescape):
    """
    Function to correctly encode a unicode text for html.
    
    @param text text to be encoded (string)
    @param pattern search pattern for text to be encoded (string)
    @return the encoded text (string)
    """
    if not text:
        return ""
    text = pattern.sub(escape_uentities, text)
    return text

_uunescape = re.compile('&#\d+;')


def unescape_uentities(m):
    """
    Function to decode html entities.
    
    @param m the match object
    @return the converted text (string)
    """
    char = m.group()
    ord = int(char[2:-1])
    return chr(ord)


def html_udecode(text, pattern=_uunescape):
    """
    Function to correctly decode a html text to a unicode text.
    
    @param text text to be decoded (string)
    @param pattern search pattern for text to be decoded (string)
    @return the decoded text (string)
    """
    if not text:
        return ""
    text = pattern.sub(unescape_uentities, text)
    return text


def convertLineEnds(text, eol):
    """
    Function to convert the end of line characters.
    
    @param text text to be converted (string)
    @param eol new eol setting (string)
    @return text with converted eols (string)
    """
    if eol == '\r\n':
        regexp = re.compile(r"""(\r(?!\n)|(?<!\r)\n)""")
        return regexp.sub(lambda m, eol='\r\n': eol, text)
    elif eol == '\n':
        regexp = re.compile(r"""(\r\n|\r)""")
        return regexp.sub(lambda m, eol='\n': eol, text)
    elif eol == '\r':
        regexp = re.compile(r"""(\r\n|\n)""")
        return regexp.sub(lambda m, eol='\r': eol, text)
    else:
        return text


def linesep():
    """
    Function to return the lineseparator used by the editor.
    
    @return line separator used by the editor (string)
    """
    eolMode = Preferences.getEditor("EOLMode")
    if eolMode == QsciScintilla.EolUnix:
        return "\n"
    elif eolMode == QsciScintilla.EolMac:
        return "\r"
    else:
        return "\r\n"


def extractFlags(text):
    """
    Function to extract eric specific flags out of the given text.
    
    Flags are contained in comments and are introduced by 'eflag:'.
    The rest of the line is interpreted as 'key = value'. value is
    analyzed for being an integer or float value. If that fails, it
    is assumed to be a string. If a key does not contain a '='
    character, it is assumed to be a boolean flag. Flags are expected
    at the very end of a file. The search is ended, if a line without
    the 'eflag:' marker is found.
    
    @param text text to be scanned (string)
    @return dictionary of string, boolean, complex, float and int
    """
    flags = {}
    if isinstance(text, basestring):
        lines = text.rstrip().splitlines()
    else:
        lines = text
    for line in reversed(lines):
        try:
            index = line.index("eflag:")
        except ValueError:
            # no flag found, don't look any further
            break
        
        flag = line[index + 6:].strip()
        if "=" in flag:
            key, value = flag.split("=", 1)
            key = key.strip()
            value = value.strip()
            
            if value.lower() in ["true", "false", "yes", "no", "ok"]:
                # it is a flag
                flags[key] = value.lower() in ["true", "yes", "ok"]
                continue
            
            try:
                # interpret as int first
                value = int(value)
            except ValueError:
                try:
                    # interpret as float next
                    value = float(value)
                except ValueError:
                    pass
            
            flags[key] = value
        else:
            # treat it as a boolean
            if flag[0] == "-":
                # false flags start with '-'
                flags[flag[1:]] = False
            else:
                flags[flag] = True
    
    return flags


def extractFlagsFromFile(filename):
    """
    Function to extract eric specific flags out of the given file.
    
    @param filename name of the file to be scanned (string)
    @return dictionary of string, boolean, complex, float and int
    """
    try:
        source, encoding = readEncodedFile(filename)
    except (UnicodeError, IOError):
        return {}
    
    return extractFlags(source)


def extractLineFlags(line, startComment="#", endComment=""):
    """
    Function to extract flags starting and ending with '__' from a line
    comment.
    
    @param line line to extract flags from (string)
    @keyparam startComment string identifying the start of the comment (string)
    @keyparam endComment string identifying the end of a comment (string)
    @return list containing the extracted flags (list of strings)
    """
    flags = []
    
    pos = line.rfind(startComment)
    if pos >= 0:
        comment = line[pos + len(startComment):].strip()
        if endComment:
            comment = comment.replace("endComment", "")
        flags = [f.strip() for f in comment.split()
                 if (f.startswith("__") and f.endswith("__"))]
    return flags


def toNativeSeparators(path):
    """
    Function returning a path, that is using native separator characters.
    
    @param path path to be converted (string)
    @return path with converted separator characters (string)
    """
    return QDir.toNativeSeparators(path)
    

def fromNativeSeparators(path):
    """
    Function returning a path, that is using "/" separator characters.
    
    @param path path to be converted (string)
    @return path with converted separator characters (string)
    """
    return QDir.fromNativeSeparators(path)
    

def normcasepath(path):
    """
    Function returning a path, that is normalized with respect to its case
    and references.
    
    @param path file path (string)
    @return case normalized path (string)
    """
    return os.path.normcase(os.path.normpath(path))
    

def normabspath(path):
    """
    Function returning a normalized, absolute path.
    
    @param path file path (string)
    @return absolute, normalized path (string)
    """
    return os.path.abspath(path)
    

def normcaseabspath(path):
    """
    Function returning an absolute path, that is normalized with respect to
    its case and references.
    
    @param path file path (string)
    @return absolute, normalized path (string)
    """
    return os.path.normcase(os.path.abspath(path))
    

def normjoinpath(a, *p):
    """
    Function returning a normalized path of the joined parts passed into it.
    
    @param a first path to be joined (string)
    @param p variable number of path parts to be joind (string)
    @return normalized path (string)
    """
    return os.path.normpath(os.path.join(a, *p))
    

def normabsjoinpath(a, *p):
    """
    Function returning a normalized, absolute path of the joined parts passed
    into it.
    
    @param a first path to be joined (string)
    @param p variable number of path parts to be joind (string)
    @return absolute, normalized path (string)
    """
    return os.path.abspath(os.path.join(a, *p))
    

def relpath(path, start=os.path.curdir):
    """
    Return a relative version of a path.
    
    @param path path to make relative (string)
    @param start path to make relative from (string)
    @return relative path (string)
    @exception ValueError raised to indicate an invalid path
    """
    if not path:
        raise ValueError("no path specified")

    start_list = os.path.abspath(start).split(os.path.sep)
    path_list = os.path.abspath(path).split(os.path.sep)

    # Work out how much of the filepath is shared by start and path.
    i = len(os.path.commonprefix([start_list, path_list]))

    rel_list = [os.path.pardir] * (len(start_list) - i) + path_list[i:]
    if not rel_list:
        return os.path.curdir
    return os.path.join(*rel_list)


def isinpath(file):
    """
    Function to check for an executable file.
    
    @param file filename of the executable to check (string)
    @return flag to indicate, if the executable file is accessible
        via the searchpath defined by the PATH environment variable.
    """
    if os.path.isabs(file):
        return os.access(file, os.X_OK)
    
    if os.path.exists(os.path.join(os.curdir, file)):
        return os.access(os.path.join(os.curdir, file), os.X_OK)
    
    path = getEnvironmentEntry('PATH')
    
    # environment variable not defined
    if path is None:
        return False
    
    dirs = path.split(os.pathsep)
    for dir in dirs:
        if os.access(os.path.join(dir, file), os.X_OK):
            return True
    
    return False


def startswithPath(path, start):
    """
    Function to check, if a path starts with a given start path.
    
    @param path path to be checked (string)
    @param start start path (string)
    @return flag indicating that the path starts with the given start
        path (boolean)
    """
    if start:
        if path == start:
            return True
        elif normcasepath(toNativeSeparators(path)).startswith(
                normcasepath(toNativeSeparators(start + "/"))):
            return True
        else:
            return False
    else:
        return False


def relativePath(path, start):
    """
    Function to convert a file path to a path relative to a start path.
    
    @param path file or directory name to convert (string)
    @param start start path (string)
    @return relative path or unchanged path, if path does not start with
        the start path (string)
    """
    if startswithPath(path, start):
        if path == start:
            return ""
        else:
            return path[len(start) + 1:]
    else:
        return path


def relativeUniversalPath(path, start):
    """
    Function to convert a file path to a path relative to a start path
    with universal separators.
    
    @param path file or directory name to convert (string)
    @param start start path (string)
    @return relative path or unchanged path, if path does not start with
        the start path with universal separators (string)
    """
    return fromNativeSeparators(relativePath(path, start))


def absolutePath(path, start):
    """
    Public method to convert a path relative to a start path to an
    absolute path.
    
    @param path file or directory name to convert (string)
    @param start start path (string)
    @return absolute path (string)
    """
    if not os.path.isabs(path):
        path = os.path.join(start, path)
    return path


def absoluteUniversalPath(path, start):
    """
    Public method to convert a path relative to a start path with
    universal separators to an absolute path.
    
    @param path file or directory name to convert (string)
    @param start start path (string)
    @return absolute path with native separators (string)
    """
    if not os.path.isabs(path):
        path = toNativeSeparators(os.path.join(start, path))
    return path


def getExecutablePath(file):
    """
    Function to build the full path of an executable file from the environment.
    
    @param file filename of the executable to check (string)
    @return full executable name, if the executable file is accessible
        via the searchpath defined by the PATH environment variable, or an
        empty string otherwise.
    """
    if os.path.isabs(file):
        if os.access(file, os.X_OK):
            return file
        else:
            return ""
        
    cur_path = os.path.join(os.curdir, file)
    if os.path.exists(cur_path):
        if os.access(cur_path, os.X_OK):
            return cur_path

    path = os.getenv('PATH')
    
    # environment variable not defined
    if path is None:
        return ""
        
    dirs = path.split(os.pathsep)
    for dir in dirs:
        exe = os.path.join(dir, file)
        if os.access(exe, os.X_OK):
            return exe
            
    return ""
    

def getExecutablePaths(file):
    """
    Function to build all full path of an executable file from the environment.
    
    @param file filename of the executable (string)
    @return list of full executable names (list of strings), if the executable
        file is accessible via the searchpath defined by the PATH environment
        variable, or an empty list otherwise.
    """
    paths = []
    
    if os.path.isabs(file):
        if os.access(file, os.X_OK):
            return [file]
        else:
            return []
        
    cur_path = os.path.join(os.curdir, file)
    if os.path.exists(cur_path):
        if os.access(cur_path, os.X_OK):
            paths.append(cur_path)

    path = os.getenv('PATH')
    
    # environment variable not defined
    if path is not None:
        dirs = path.split(os.pathsep)
        for dir in dirs:
            exe = os.path.join(dir, file)
            if os.access(exe, os.X_OK) and exe not in paths:
                paths.append(exe)
    
    return paths
    

def isExecutable(exe):
    """
    Function to check, if a file is executable.
    
    @param exe filename of the executable to check (string)
    @return flag indicating executable status (boolean)
    """
    return os.access(exe, os.X_OK)
    

def samepath(f1, f2):
    """
    Function to compare two paths.
    
    @param f1 first path for the compare (string)
    @param f2 second path for the compare (string)
    @return flag indicating whether the two paths represent the
        same path on disk.
    """
    if f1 is None or f2 is None:
        return False
    
    if normcaseabspath(os.path.realpath(f1)) == \
            normcaseabspath(os.path.realpath(f2)):
        return True
    
    return False


def samefilepath(f1, f2):
    """
    Function to compare two paths. Strips the filename.
    
    @param f1 first filepath for the compare (string)
    @param f2 second filepath for the compare (string)
    @return flag indicating whether the two paths represent the
        same path on disk.
    """
    if f1 is None or f2 is None:
        return False
    
    if (normcaseabspath(os.path.dirname(os.path.realpath(f1))) ==
            normcaseabspath(os.path.dirname(os.path.realpath(f2)))):
        return True
    
    return False

try:
    EXTSEP = os.extsep
except AttributeError:
    EXTSEP = "."


def splitPath(name):
    """
    Function to split a pathname into a directory part and a file part.
    
    @param name path name (string)
    @return a tuple of 2 strings (dirname, filename).
    """
    if os.path.isdir(name):
        dn = os.path.abspath(name)
        fn = "."
    else:
        dn, fn = os.path.split(name)
    return (dn, fn)


def joinext(prefix, ext):
    """
    Function to join a file extension to a path.
    
    The leading "." of ext is replaced by a platform specific extension
    separator if necessary.
    
    @param prefix the basepart of the filename (string)
    @param ext the extension part (string)
    @return the complete filename (string)
    """
    if ext[0] != ".":
        ext = ".{0}".format(ext)
        # require leading separator to match os.path.splitext
    return prefix + EXTSEP + ext[1:]


def compactPath(path, width, measure=len):
    """
    Function to return a compacted path fitting inside the given width.
    
    @param path path to be compacted (string)
    @param width width for the compacted path (integer)
    @param measure reference to a function used to measure the length of the
        string
    @return compacted path (string)
    """
    if measure(path) <= width:
        return path
    
    ellipsis = '...'
    
    head, tail = os.path.split(path)
    mid = len(head) // 2
    head1 = head[:mid]
    head2 = head[mid:]
    while head1:
        # head1 is same size as head2 or one shorter
        path = os.path.join("{0}{1}{2}".format(head1, ellipsis, head2), tail)
        if measure(path) <= width:
            return path
        head1 = head1[:-1]
        head2 = head2[1:]
    path = os.path.join(ellipsis, tail)
    if measure(path) <= width:
        return path
    while tail:
        path = "{0}{1}".format(ellipsis, tail)
        if measure(path) <= width:
            return path
        tail = tail[1:]
    return ""
    

def direntries(path, filesonly=False, pattern=None, followsymlinks=True,
               checkStop=None):
    """
    Function returning a list of all files and directories.
    
    @param path root of the tree to check
    @param filesonly flag indicating that only files are wanted
    @param pattern a filename pattern to check against
    @param followsymlinks flag indicating whether symbolic links
            should be followed
    @param checkStop function to be called to check for a stop
    @return list of all files and directories in the tree rooted
        at path. The names are expanded to start with path.
    """
    if filesonly:
        files = []
    else:
        files = [path]
    try:
        entries = os.listdir(path)
        for entry in entries:
            if checkStop and checkStop():
                break
            
            if entry in ['CVS', 'cvs',
                         '.svn', '_svn',
                         '.hg', '_hg',
                         '.ropeproject', '_ropeproject',
                         '.eric6project', '_eric6project',
                         '.issues', '_issues']:
                continue
            
            fentry = os.path.join(path, entry)
            if pattern and \
                not os.path.isdir(fentry) and \
                    not fnmatch.fnmatch(entry, pattern):
                # entry doesn't fit the given pattern
                continue
                
            if os.path.isdir(fentry):
                if os.path.islink(fentry) and not followsymlinks:
                    continue
                files += direntries(
                    fentry, filesonly, pattern, followsymlinks, checkStop)
            else:
                files.append(fentry)
    except OSError:
        pass
    except UnicodeDecodeError:
        pass
    return files


def getDirs(path, excludeDirs):
    """
    Function returning a list of all directories below path.
    
    @param path root of the tree to check
    @param excludeDirs basename of directories to ignore
    @return list of all directories found
    """
    try:
        names = os.listdir(path)
    except EnvironmentError:
        return

    dirs = []
    for name in names:
        if os.path.isdir(os.path.join(path, name)) and \
                not os.path.islink(os.path.join(path, name)):
            exclude = 0
            for e in excludeDirs:
                if name.split(os.sep, 1)[0] == e:
                    exclude = 1
                    break
            if not exclude:
                dirs.append(os.path.join(path, name))

    for name in dirs[:]:
        if not os.path.islink(name):
            dirs = dirs + getDirs(name, excludeDirs)

    return dirs


def getTestFileName(fn):
    """
    Function to build the filename of a unittest file.
    
    The filename for the unittest file is built by prepending
    the string "test" to the filename passed into this function.
    
    @param fn filename basis to be used for the unittest filename (string)
    @return filename of the corresponding unittest file (string)
    """
    dn, fn = os.path.split(fn)
    return os.path.join(dn, "test{0}".format(fn))


def parseOptionString(s):
    """
    Function used to convert an option string into a list of options.
    
    @param s option string (string or string)
    @return list of options (list of strings)
    """
    rx = QRegExp(r"""\s([\w=/-]*"[^"]+"|[\w=/-]*'[^']+'|[^\s]+)""")
    s = re.sub(r"%[A-Z%]", _percentReplacementFunc, s)
    return parseString(s, rx)
    

def parseEnvironmentString(s):
    """
    Function used to convert an environment string into a list of environment
    settings.
    
    @param s environment string (string)
    @return list of environment settings (list of strings)
    """
    rx = QRegExp(r"""\s(\w+\+?=[^\s]+|\w+="[^"]+"|\w+='[^']+')""")
    return parseString(s, rx)


def parseString(s, rx):
    """
    Function used to convert a string into a list.
    
    @param s string to be parsed (string)
    @param rx regex defining the parse pattern (QRegExp)
    @return list of parsed data (list of strings)
    """
    olist = []
    if not s.startswith(' '):
        # prepare the  string to fit our pattern
        s = ' ' + s
        
    pos = rx.indexIn(s)
    while pos != -1:
        cs = rx.cap(1)
        if cs.startswith('"') or cs.startswith("'"):
            cs = cs[1:-1]
        olist.append(cs)
        pos += rx.matchedLength()
        pos = rx.indexIn(s, pos)
        
    return olist


def _percentReplacementFunc(matchobj):
    """
    Protected function called for replacing % codes.
    
    @param matchobj matchobject for the code
    @return replacement string
    """
    return getPercentReplacement(matchobj.group(0))
    

def getPercentReplacement(code):
    """
    Function to get the replacement for code.
    
    @param code code indicator (string)
    @return replacement string (string)
    """
    if code in ["C", "%C"]:
        # column of the cursor of the current editor
        aw = e5App().getObject("ViewManager").activeWindow()
        if aw is None:
            column = -1
        else:
            column = aw.getCursorPosition()[1]
        return "{0:d}".format(column)
    elif code in ["D", "%D"]:
        # directory of active editor
        aw = e5App().getObject("ViewManager").activeWindow()
        if aw is None:
            dn = "not_available"
        else:
            fn = aw.getFileName()
            if fn is None:
                dn = "not_available"
            else:
                dn = os.path.dirname(fn)
        return dn
    elif code in ["F", "%F"]:
        # filename (complete) of active editor
        aw = e5App().getObject("ViewManager").activeWindow()
        if aw is None:
            fn = "not_available"
        else:
            fn = aw.getFileName()
            if fn is None:
                fn = "not_available"
        return fn
    elif code in ["H", "%H"]:
        # home directory
        return getHomeDir()
    elif code in ["L", "%L"]:
        # line of the cursor of the current editor
        aw = e5App().getObject("ViewManager").activeWindow()
        if aw is None:
            line = 0
        else:
            line = aw.getCursorPosition()[0] + 1
        return "{0:d}".format(line)
    elif code in ["P", "%P"]:
        # project path
        projectPath = e5App().getObject("Project").getProjectPath()
        if not projectPath:
            projectPath = "not_available"
        return projectPath
    elif code in ["S", "%S"]:
        # selected text of the current editor
        aw = e5App().getObject("ViewManager").activeWindow()
        if aw is None:
            text = "not_available"
        else:
            text = aw.selectedText()
        return text
    elif code in ["U", "%U"]:
        # username
        un = getUserName()
        if un is None:
            return code
        else:
            return un
    elif code in ["%", "%%"]:
        # the percent sign
        return "%"
    else:
        # unknown code, just return it
        return code
    

def getPercentReplacementHelp():
    """
    Function to get the help text for the supported %-codes.
    
    @returns help text (string)
    """
    return QCoreApplication.translate(
        "Utilities",
        """<p>You may use %-codes as placeholders in the string."""
        """ Supported codes are:"""
        """<table>"""
        """<tr><td>%C</td><td>column of the cursor of the current editor"""
        """</td></tr>"""
        """<tr><td>%D</td><td>directory of the current editor</td></tr>"""
        """<tr><td>%F</td><td>filename of the current editor</td></tr>"""
        """<tr><td>%H</td><td>home directory of the current user</td></tr>"""
        """<tr><td>%L</td><td>line of the cursor of the current editor"""
        """</td></tr>"""
        """<tr><td>%P</td><td>path of the current project</td></tr>"""
        """<tr><td>%S</td><td>selected text of the current editor</td></tr>"""
        """<tr><td>%U</td><td>username of the current user</td></tr>"""
        """<tr><td>%%</td><td>the percent sign</td></tr>"""
        """</table>"""
        """</p>""")


def getUserName():
    """
    Function to get the user name.
    
    @return user name (string)
    """
    user = getpass.getuser()
    
    if isWindowsPlatform():
        if not user:
            return win32_GetUserName()
        else:
            if sys.version_info[0] == 2:
                user = user.decode(locale.getpreferredencoding())
    
    return user


def getRealName():
    """
    Function to get the real name of the user.
    
    @return real name of the user (string)
    """
    if isWindowsPlatform():
        return win32_getRealName()
    else:
        import pwd
        user = getpass.getuser()
        return pwd.getpwnam(user).pw_gecos


def getHomeDir():
    """
    Function to get a users home directory.
    
    @return home directory (string)
    """
    return QDir.homePath()
    

def getPythonLibPath():
    """
    Function to determine the path to Python's library.
    
    @return path to the Python library (string)
    """
    pyFullVers = sys.version.split()[0]

    vl = re.findall("[0-9.]*", pyFullVers)[0].split(".")
    major = vl[0]
    minor = vl[1]

    pyVers = major + "." + minor

    if isWindowsPlatform():
        libDir = sys.prefix + "\\Lib"
    else:
        try:
            syslib = sys.lib
        except AttributeError:
            syslib = "lib"
        libDir = sys.prefix + "/" + syslib + "/python" + pyVers
        
    return libDir
    

def getPythonVersion():
    """
    Function to get the Python version (major, minor) as an integer value.
    
    @return An integer representing major and minor version number (integer)
    """
    return sys.hexversion >> 16


def determinePythonVersion(filename, source, editor=None):
    """
    Function to determine the python version of a given file.
    
    @param filename name of the file with extension (str)
    @param source of the file (str)
    @keyparam editor reference to the editor, if the file is opened
        already (Editor object)
    @return Python version if file is Python2 or Python3 (int)
    """
    pyAssignment = {"Python": 2, "Python2": 2, "Python3": 3}
    
    if not editor:
        viewManager = e5App().getObject('ViewManager')
        editor = viewManager.getOpenEditor(filename)
    
    # Maybe the user has changed the language
    if editor and editor.getFileType() in pyAssignment:
        return pyAssignment[editor.getFileType()]

    pyVer = 0
    if filename:
        if not source:
            source = readEncodedFile(filename)[0]
        flags = extractFlags(source)
        ext = os.path.splitext(filename)[1]
        py2Ext = Preferences.getPython("PythonExtensions")
        py3Ext = Preferences.getPython("Python3Extensions")
        project = e5App().getObject('Project')
        basename = os.path.basename(filename)
        
        if "FileType" in flags:
            pyVer = pyAssignment.get(flags["FileType"], 0)
        elif project.isOpen() and project.isProjectFile(filename):
            language = project.getEditorLexerAssoc(basename)
            if not language:
                language = Preferences.getEditorLexerAssoc(basename)
            if language in ['Python2', 'Python3']:
                pyVer = pyAssignment[language]
        
        if pyVer:
            # Skip the next tests
            pass
        elif (Preferences.getProject("DeterminePyFromProject") and
              project.isOpen() and
              project.isProjectFile(filename) and
              ext in py2Ext + py3Ext):
                    pyVer = pyAssignment.get(project.getProjectLanguage(), 0)
        elif ext in py2Ext and ext not in py3Ext:
            pyVer = 2
        elif ext in py3Ext and ext not in py2Ext:
            pyVer = 3
        elif source:
            if isinstance(source, basestring):
                line0 = source.splitlines()[0]
            else:
                line0 = source[0]
            if line0.startswith("#!"):
                if "python3" in line0:
                    pyVer = 3
                elif "python" in line0:
                    pyVer = 2
        
        if pyVer == 0 and ext in py2Ext + py3Ext:
            pyVer = sys.version_info[0]
        
        if editor and pyVer:
            editor.filetype = "Python{0}".format(pyVer)
    
    return pyVer


###############################################################################
# functions for environment handling
###############################################################################


def getEnvironmentEntry(key, default=None):
    """
    Module function to get an environment entry.
    
    @param key key of the requested environment entry (string)
    @param default value to be returned, if the environment doesn't contain
        the requested entry (string)
    @return the requested entry or the default value, if the entry wasn't
        found (string or None)
    """
    filter = QRegExp("^{0}[ \t]*=".format(key))
    if isWindowsPlatform():
        filter.setCaseSensitivity(Qt.CaseInsensitive)
    
    entries = [e for e in QProcess.systemEnvironment()
               if filter.indexIn(e) != -1]
    if not entries:
        return default
    
    # if there are multiple entries, just consider the first one
    ename, val = entries[0].split("=", 1)
    return val.strip()


def hasEnvironmentEntry(key):
    """
    Module function to check, if the environment contains an entry.
    
    @param key key of the requested environment entry (string)
    @return flag indicating the presence of the requested entry (boolean)
    """
    filter = QRegExp("^{0}[ \t]*=".format(key))
    if isWindowsPlatform():
        filter.setCaseSensitivity(Qt.CaseInsensitive)
    
    entries = [e for e in QProcess.systemEnvironment()
               if filter.indexIn(e) != -1]
    return len(entries) > 0

###############################################################################
# Qt utility functions below
###############################################################################


def generateQtToolName(toolname):
    """
    Module function to generate the executable name for a Qt tool like
    designer.
    
    @param toolname base name of the tool (string)
    @return the Qt tool name without extension (string)
    """
    return "{0}{1}{2}".format(Preferences.getQt("QtToolsPrefix4"),
                              toolname,
                              Preferences.getQt("QtToolsPostfix4")
                              )


def getQtMacBundle(toolname):
    """
    Module function to determine the correct Mac OS X bundle name for Qt tools.
    
    @param toolname  plain name of the tool (e.g. "designer") (string)
    @return bundle name of the Qt tool (string)
    """
    qtDir = getQtBinariesPath()
    bundles = [
        os.path.join(
            qtDir, 'bin', generateQtToolName(toolname.capitalize())) + ".app",
        os.path.join(qtDir, 'bin', generateQtToolName(toolname)) + ".app",
        os.path.join(
            qtDir, generateQtToolName(toolname.capitalize())) + ".app",
        os.path.join(qtDir, generateQtToolName(toolname)) + ".app",
    ]
    for bundle in bundles:
        if os.path.exists(bundle):
            return bundle
    return ""


def prepareQtMacBundle(toolname, version, args):
    """
    Module function for starting Qt tools that are Mac OS X bundles.

    @param toolname  plain name of the tool (e.g. "designer") (string)
    @param version indication for the requested version (Qt 4) (integer)
    @param args    name of input file for tool, if any (list of strings)
    @return command-name and args for QProcess (tuple)
    """
    if version != 4:
        return ("", [])
    
    fullBundle = getQtMacBundle(toolname)
    if fullBundle == "":
        return ("", [])

    newArgs = []
    newArgs.append("-a")
    newArgs.append(fullBundle)
    if args:
        newArgs.append("--args")
        newArgs += args

    return ("open", newArgs)

###############################################################################
# Qt utility functions below
###############################################################################


def generatePySideToolPath(toolname):
    """
    Module function to generate the executable path for a PySide tool.
    
    @param toolname base name of the tool (string or QString)
    @return the PySide tool path with extension (string)
    """
    if isWindowsPlatform():
        pysideInterpreter = checkPyside()
        interpreter = sys.version_info[0] - 2
        hasPyside = pysideInterpreter[interpreter]
        # if it isn't the internal interpreter, it has to be the external one
        if not hasPyside:
            interpreter = not interpreter
        if interpreter:
            prefix = os.path.dirname(
                Preferences.getDebugger("Python3Interpreter"))
        else:
            prefix = os.path.dirname(
                Preferences.getDebugger("PythonInterpreter"))
        if toolname == "pyside-uic":
            return os.path.join(prefix, "Scripts", toolname + '.exe')
        else:
            return os.path.join(prefix, "Lib", "site-packages", "PySide",
                                toolname + ".exe")
    else:
        return toolname


def checkPyside():
    """
    Module function to check the presence of PySide.
    
    @return list of two flags indicating the presence of PySide for Python2
        and PySide for Python3 (boolean, boolean)
    """
    pysideInformation = []
    for interpreterName in ["PythonInterpreter", "Python3Interpreter"]:
        interpreter = Preferences.getDebugger(interpreterName)
        if interpreter == "" or not isinpath(interpreter):
            hasPyside = False
        else:
            hasPyside = False
            checker = os.path.join(getConfig('ericDir'),
                                   "Utilities", "PySideImporter.py")
            args = [checker]
            proc = QProcess()
            proc.setProcessChannelMode(QProcess.MergedChannels)
            proc.start(interpreter, args)
            finished = proc.waitForFinished(30000)
            if finished:
                if proc.exitCode() == 0:
                    hasPyside = True
        pysideInformation.append(hasPyside)
    
    return pysideInformation

###############################################################################
# Other utility functions below
###############################################################################


def generateVersionInfo(linesep='\n'):
    """
    Module function to generate a string with various version infos.
    
    @param linesep string to be used to separate lines (string)
    @return string with version infos (string)
    """
    try:
        import sip
        sip_version_str = sip.SIP_VERSION_STR
    except (ImportError, AttributeError):
        sip_version_str = "sip version not available"
    
    info = "Version Numbers:{0}  Python {1}{2}".format(
        linesep, sys.version.split()[0], linesep)
    info += "  Qt {0}{1}  PyQt {2}{3}".format(
        qVersion(), linesep, PYQT_VERSION_STR, linesep)
    info += "  sip {0}{1}  QScintilla {2}{3}".format(
        sip_version_str, linesep, QSCINTILLA_VERSION_STR, linesep)
    try:
        from PyQt5.QtWebKit import qWebKitVersion
        info += "  WebKit {0}{1}".format(qWebKitVersion(), linesep)
    except ImportError:
        pass
    info += "  {0} {1}{2}".format(
        Program, Version, linesep * 2)
    info += "Platform: {0}{1}{2}{3}".format(
        sys.platform, linesep, sys.version, linesep)
    
    return info


def generatePluginsVersionInfo(linesep='\n'):
    """
    Module function to generate a string with plugins version infos.
    
    @param linesep string to be used to separate lines (string)
    @return string with plugins version infos (string)
    """
    infoStr = ""
    app = e5App()
    if app is not None:
        try:
            pm = app.getObject("PluginManager")
            versions = {}
            for info in pm.getPluginInfos():
                versions[info[0]] = info[2]
            
            infoStr = "Plugins Version Numbers:{0}".format(linesep)
            for pluginName in sorted(versions.keys()):
                infoStr += "  {0} {1}{2}".format(
                           pluginName, versions[pluginName], linesep)
        except KeyError:
            pass
    
    return infoStr


def generateDistroInfo(linesep='\n'):
    """
    Module function to generate a string with distribution infos.
    
    @param linesep string to be used to separate lines (string)
    @return string with plugins version infos (string)
    """
    infoStr = ""
    if isLinuxPlatform():
        releaseList = glob.glob("/etc/*-release")
        if releaseList:
            infoStr = "Distribution Info:{0}".format(linesep)
            infoParas = []
            for rfile in releaseList:
                try:
                    f = open(rfile, "r")
                    lines = f.read().splitlines()
                    f.close
                except IOError:
                    continue
                
                lines.insert(0, rfile)
                infoParas.append('  ' + (linesep + '  ').join(lines))
            infoStr += (linesep + linesep).join(infoParas)
    
    return infoStr


def toBool(dataStr):
    """
    Module function to convert a string to a boolean value.
    
    @param dataStr string to be converted (string)
    @return converted boolean value (boolean)
    """
    if dataStr in ["True", "true", "1", "Yes", "yes"]:
        return True
    elif dataStr in ["False", "false", "0", "No", "no"]:
        return False
    else:
        return bool(dataStr)

###############################################################################
# posix compatibility functions below
###############################################################################

# None right now

###############################################################################
# win32 compatibility functions below
###############################################################################


def win32_Kill(pid):
    """
    Function to provide an os.kill equivalent for Win32.
    
    @param pid process id (integer)
    @return result of the kill (boolean)
    """
    import win32api
    handle = win32api.OpenProcess(1, 0, pid)
    return (0 != win32api.TerminateProcess(handle, 0))


def win32_GetUserName():
    """
    Function to get the user name under Win32.
    
    @return user name (string)
    """
    try:
        import win32api
        return win32api.GetUserName()
    except ImportError:
        try:
            u = getEnvironmentEntry('USERNAME')
        except KeyError:
            u = getEnvironmentEntry('username', None)
        return u


def win32_getRealName():
    """
    Function to get the user's real name (aka. display name) under Win32.
    
    @return real name of the current user (string)
    """
    import ctypes
    
    GetUserNameEx = ctypes.windll.secur32.GetUserNameExW
    NameDisplay = 3

    size = ctypes.pointer(ctypes.c_ulong(0))
    GetUserNameEx(NameDisplay, None, size)

    nameBuffer = ctypes.create_unicode_buffer(size.contents.value)
    GetUserNameEx(NameDisplay, nameBuffer, size)
    return nameBuffer.value
