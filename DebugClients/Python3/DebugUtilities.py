# -*- coding: utf-8 -*-

# Copyright (c) 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing utilities functions for the debug client.
"""

#
# Taken from inspect.py of Python 3.4
#

from collections import namedtuple
from inspect import iscode, isframe

# Create constants for the compiler flags in Include/code.h
# We try to get them from dis to avoid duplication, but fall
# back to hardcoding so the dependency is optional
try:
    from dis import COMPILER_FLAG_NAMES
except ImportError:
    CO_OPTIMIZED, CO_NEWLOCALS = 0x1, 0x2
    CO_VARARGS, CO_VARKEYWORDS = 0x4, 0x8
    CO_NESTED, CO_GENERATOR, CO_NOFREE = 0x10, 0x20, 0x40
else:
    mod_dict = globals()
    for k, v in COMPILER_FLAG_NAMES.items():
        mod_dict["CO_" + v] = k

ArgInfo = namedtuple('ArgInfo', 'args varargs keywords locals')


def getargvalues(frame):
    """
    Function to get information about arguments passed into a
    particular frame.
    
    @param frame reference to a frame object to be processed
    @type frame
    @return tuple of four things, where 'args' is a list of the argument names,
        'varargs' and 'varkw' are the names of the * and ** arguments or None
        and 'locals' is the locals dictionary of the given frame.
    @exception TypeError raised if the input parameter is not a frame object
    """
    if not isframe(frame):
        raise TypeError('{0!r} is not a frame object'.format(frame))

    args, varargs, kwonlyargs, varkw = _getfullargs(frame.f_code)
    return ArgInfo(args + kwonlyargs, varargs, varkw, frame.f_locals)


def _getfullargs(co):
    """
    Protected function to get information about the arguments accepted
    by a code object.
    
    @param co reference to a code object to be processed
    @type code
    @return tuple of four things, where 'args' and 'kwonlyargs' are lists of
        argument names, and 'varargs' and 'varkw' are the names of the
        * and ** arguments or None.
    @exception TypeError raised if the input parameter is not a code object
    """
    if not iscode(co):
        raise TypeError('{0!r} is not a code object'.format(co))

    nargs = co.co_argcount
    names = co.co_varnames
    nkwargs = co.co_kwonlyargcount
    args = list(names[:nargs])
    kwonlyargs = list(names[nargs:nargs + nkwargs])

    nargs += nkwargs
    varargs = None
    if co.co_flags & CO_VARARGS:
        varargs = co.co_varnames[nargs]
        nargs = nargs + 1
    varkw = None
    if co.co_flags & CO_VARKEYWORDS:
        varkw = co.co_varnames[nargs]
    return args, varargs, kwonlyargs, varkw


def formatargvalues(args, varargs, varkw, locals,
                    formatarg=str,
                    formatvarargs=lambda name: '*' + name,
                    formatvarkw=lambda name: '**' + name,
                    formatvalue=lambda value: '=' + repr(value)):
    """
    Function to format an argument spec from the 4 values returned
    by getargvalues.
    
    @param args list of argument names
    @type list of str
    @param varargs name of the variable arguments
    @type str
    @param varkw name of the keyword arguments
    @type str
    @param locals reference to the local variables dictionary
    @type dict
    @keyparam formatarg argument formatting function
    @type func
    @keyparam formatvarargs variable arguments formatting function
    @type func
    @keyparam formatvarkw keyword arguments formatting function
    @type func
    @keyparam formatvalue value formating functtion
    @type func
    @return formatted call signature
    @rtype str
    """
    specs = []
    for i in range(len(args)):
        name = args[i]
        specs.append(formatarg(name) + formatvalue(locals[name]))
    if varargs:
        specs.append(formatvarargs(varargs) + formatvalue(locals[varargs]))
    if varkw:
        specs.append(formatvarkw(varkw) + formatvalue(locals[varkw]))
    argvalues = '(' + ', '.join(specs) + ')'
    if '__return__' in locals:
        argvalues += " -> " + formatvalue(locals['__return__'])
    return argvalues

#
# eflag: noqa = M702
