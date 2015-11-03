# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Package implementing class browsers for various languages.

Currently it offers class browser support for the following
programming languages.

<ul>
<li>CORBA IDL</li>
<li>Python</li>
<li>Ruby</li>
</ul>
"""

from __future__ import unicode_literals

import os
import imp
import sys

import Preferences

PY_SOURCE = imp.PY_SOURCE
PTL_SOURCE = 128
RB_SOURCE = 129
IDL_SOURCE = 130
JS_SOURCE = 131

SUPPORTED_TYPES = [PY_SOURCE, PTL_SOURCE, RB_SOURCE, IDL_SOURCE, JS_SOURCE]

__extensions = {
    "IDL": [".idl"],
    "Python": [".py", ".pyw", ".ptl"],  # currently not used
    "Ruby": [".rb"],
    "JavaScript": [".js"],
}


def readmodule(module, path=[], isPyFile=False):
    """
    Read a source file and return a dictionary of classes, functions, modules,
    etc. .
    
    The real work of parsing the source file is delegated to the individual
    file parsers.

    @param module name of the source file (string)
    @param path path the file should be searched in (list of strings)
    @param isPyFile flag indicating a Python file (boolean)
    @return the resulting dictionary
    """
    ext = os.path.splitext(module)[1].lower()
    
    if ext in __extensions["IDL"]:
        from . import idlclbr
        dict = idlclbr.readmodule_ex(module, path)
        idlclbr._modules.clear()
    elif ext in __extensions["Ruby"]:
        from . import rbclbr
        dict = rbclbr.readmodule_ex(module, path)
        rbclbr._modules.clear()
    elif ext in __extensions["JavaScript"] and sys.version_info[0] == 3:
        from . import jsclbr
        dict = jsclbr.readmodule_ex(module, path)
        jsclbr._modules.clear()
    elif ext in Preferences.getPython("PythonExtensions") or \
        ext in Preferences.getPython("Python3Extensions") or \
            isPyFile:
        from . import pyclbr
        dict = pyclbr.readmodule_ex(module, path, isPyFile=isPyFile)
        pyclbr._modules.clear()
    else:
        # try Python if it is without extension
        from . import pyclbr
        dict = pyclbr.readmodule_ex(module, path)
        pyclbr._modules.clear()
    
    return dict


def find_module(name, path, isPyFile=False):
    """
    Module function to extend the Python module finding mechanism.
    
    This function searches for files in the given path. If the filename
    doesn't have an extension or an extension of .py, the normal search
    implemented in the imp module is used. For all other supported files
    only path is searched.
    
    @param name filename or modulename to search for (string)
    @param path search path (list of strings)
    @param isPyFile flag indicating a Python file (boolean)
    @return tuple of the open file, pathname and description. Description
        is a tuple of file suffix, file mode and file type)
    @exception ImportError The file or module wasn't found.
    """
    ext = os.path.splitext(name)[1].lower()
    
    if ext in __extensions["Ruby"]:
        for p in path:      # only search in path
            pathname = os.path.join(p, name)
            if os.path.exists(pathname):
                return (open(pathname), pathname, (ext, 'r', RB_SOURCE))
        raise ImportError
    
    elif ext in __extensions["IDL"]:
        for p in path:      # only search in path
            pathname = os.path.join(p, name)
            if os.path.exists(pathname):
                return (open(pathname), pathname, (ext, 'r', IDL_SOURCE))
        raise ImportError
    
    elif ext in __extensions["JavaScript"]:
        for p in path:      # only search in path
            pathname = os.path.join(p, name)
            if os.path.exists(pathname):
                return (open(pathname), pathname, (ext, 'r', JS_SOURCE))
        raise ImportError
    
    elif ext == '.ptl':
        for p in path:      # only search in path
            pathname = os.path.join(p, name)
            if os.path.exists(pathname):
                return (open(pathname), pathname, (ext, 'r', PTL_SOURCE))
        raise ImportError
    
    if name.lower().endswith('.py'):
        name = name[:-3]
    
    try:
        return imp.find_module(name, path)
    except ImportError:
        if name.lower().endswith(
                tuple(Preferences.getPython("PythonExtensions") +
                      Preferences.getPython("Python3Extensions"))) or \
                isPyFile:
            for p in path:      # search in path
                pathname = os.path.join(p, name)
                if os.path.exists(pathname):
                    return (open(pathname), pathname, (ext, 'r', PY_SOURCE))
        raise ImportError
    except SyntaxError:
        # re-raise as an import error
        raise ImportError
