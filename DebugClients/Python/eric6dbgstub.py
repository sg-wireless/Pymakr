# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a debugger stub for remote debugging.
"""

import os
import sys
import distutils.sysconfig

from eric6config import getConfig

debugger = None
__scriptname = None

modDir = distutils.sysconfig.get_python_lib(True)
ericpath = os.getenv('ERICDIR', getConfig('ericDir'))

if ericpath not in sys.path:
    sys.path.insert(-1, ericpath)
    

def initDebugger(kind="standard"):
    """
    Module function to initialize a debugger for remote debugging.
    
    @param kind type of debugger ("standard" or "threads")
    @return flag indicating success (boolean)
    @exception ValueError raised to indicate an invalid debugger kind
        was requested
    """
    global debugger
    res = 1
    try:
        if kind == "standard":
            import DebugClient
            debugger = DebugClient.DebugClient()
        elif kind == "threads":
            import DebugClientThreads
            debugger = DebugClientThreads.DebugClientThreads()
        else:
            raise ValueError
    except ImportError:
        debugger = None
        res = 0
        
    return res


def runcall(func, *args):
    """
    Module function mimicing the Pdb interface.
    
    @param func function to be called (function object)
    @param *args arguments being passed to func
    @return the function result
    """
    global debugger, __scriptname
    return debugger.run_call(__scriptname, func, *args)
    

def setScriptname(name):
    """
    Module function to set the scriptname to be reported back to the IDE.
    
    @param name absolute pathname of the script (string)
    """
    global __scriptname
    __scriptname = name


def startDebugger(enableTrace=True, exceptions=True,
                  tracePython=False, redirect=True):
    """
    Module function used to start the remote debugger.
    
    @keyparam enableTrace flag to enable the tracing function (boolean)
    @keyparam exceptions flag to enable exception reporting of the IDE
        (boolean)
    @keyparam tracePython flag to enable tracing into the Python library
        (boolean)
    @keyparam redirect flag indicating redirection of stdin, stdout and
        stderr (boolean)
    """
    global debugger
    if debugger:
        debugger.startDebugger(enableTrace=enableTrace, exceptions=exceptions,
                               tracePython=tracePython, redirect=redirect)

#
# eflag: FileType = Python2
