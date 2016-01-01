# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#
# Original (c) 2005 Divmod, Inc.  See __init__.py file for details
#
# This module is based on pyflakes for Python2 and Python3, but was modified to
# be integrated into eric6

"""
Module providing the class Message and its subclasses.
"""


class Message(object):
    """
    Class defining the base for all specific message classes.
    """
    message_id = 'F00'
    message = ''
    message_args = ()

    def __init__(self, filename, loc):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of the issue
        """
        self.filename = filename
        self.lineno = loc.lineno
        self.col = getattr(loc, 'col_offset', 0)

    def __str__(self):
        """
        Special method return a string representation of the instance object.
        
        @return string representation of the object (string)
        """
        return '%s:%s: %s' % (
            self.filename, self.lineno, self.message % self.message_args)
    
    def getMessageData(self):
        """
        Public method to get the individual message data elements.
        
        @return tuple containing file name, line number, column, message ID
            and message arguments (string, integer, integer, string, list)
        """
        return (self.filename, self.lineno, self.col, self.message_id,
                self.message_args)


class UnusedImport(Message):
    """
    Class defining the "Unused Import" message.
    """
    message_id = 'F01'
    message = '%r imported but unused'

    def __init__(self, filename, loc, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of the issue
        @param name name of the unused import (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name,)


class RedefinedWhileUnused(Message):
    """
    Class defining the "Redefined While Unused" message.
    """
    message_id = 'F02'
    message = 'redefinition of unused %r from line %r'

    def __init__(self, filename, loc, name, orig_loc):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of the issue
        @param name name of the redefined object (string)
        @param orig_loc location of the original definition
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name, orig_loc.lineno)


class RedefinedInListComp(Message):
    """
    Class defining the "Redefined In List Comprehension" message.
    """
    message_id = 'F12'
    message = 'list comprehension redefines %r from line %r'

    def __init__(self, filename, loc, name, orig_loc):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of the issue
        @param name name of the redefined object (string)
        @param orig_loc location of the original definition
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name, orig_loc.lineno)


class ImportShadowedByLoopVar(Message):
    """
    Class defining the "Import Shadowed By Loop Var" message.
    """
    message_id = 'F03'
    message = 'import %r from line %r shadowed by loop variable'

    def __init__(self, filename, loc, name, orig_loc):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of the issue
        @param name name of the shadowed import (string)
        @param orig_loc location of the import
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name, orig_loc.lineno)


class ImportStarUsed(Message):
    """
    Class defining the "Import Star Used" message.
    """
    message_id = 'F04'
    message = "'from %s import *' used; unable to detect undefined names"

    def __init__(self, filename, loc, modname):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of the issue
        @param modname name of the module imported using star import (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (modname,)


class UndefinedName(Message):
    """
    Class defining the "Undefined Name" message.
    """
    message_id = 'F05'
    message = 'undefined name %r'

    def __init__(self, filename, loc, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of the issue
        @param name undefined name (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name,)


class DoctestSyntaxError(Message):
    """
    Class defining the "Doctest syntax Error" message.
    """
    message_id = 'F13'
    message = 'syntax error in doctest'

    def __init__(self, filename, loc, position=None):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of the issue
        @param position position of the syntax error
        """
        Message.__init__(self, filename, loc)
        if position:
            (self.lineno, self.col) = position
        self.message_args = ()


class UndefinedExport(Message):
    """
    Class defining the "Undefined Export" message.
    """
    message_id = 'F06'
    message = 'undefined name %r in __all__'

    def __init__(self, filename, loc, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of the issue
        @param name undefined exported name (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name,)


class UndefinedLocal(Message):
    """
    Class defining the "Undefined Local Variable" message.
    """
    message_id = 'F07'
    message = ('local variable %r (defined in enclosing scope on line %r) '
               'referenced before assignment')

    def __init__(self, filename, loc, name, orig_loc):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of the issue
        @param name name of the prematurely referenced variable (string)
        @param orig_loc location of the variable definition
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name, orig_loc.lineno)


class DuplicateArgument(Message):
    """
    Class defining the "Duplicate Argument" message.
    """
    message_id = 'F08'
    message = 'duplicate argument %r in function definition'

    def __init__(self, filename, loc, name):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of the issue
        @param name name of the duplicate argument (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (name,)


class LateFutureImport(Message):
    """
    Class defining the "Late Future Import" message.
    """
    message_id = 'F10'
    message = 'future import(s) %r after other statements'

    def __init__(self, filename, loc, names):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of the issue
        @param names names of the imported futures (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (names,)


class UnusedVariable(Message):
    """
    Class defining the "Unused Variable" message.
    
    Indicates that a variable has been explicitly assigned to but not actually
    used.
    """
    message_id = 'F11'
    message = 'local variable %r is assigned to but never used'

    def __init__(self, filename, loc, names):
        """
        Constructor
        
        @param filename name of the file (string)
        @param loc location of the issue
        @param names names of unused variable (string)
        """
        Message.__init__(self, filename, loc)
        self.message_args = (names,)


class ReturnWithArgsInsideGenerator(Message):
    """
    Class defining the "Return values in generator" message.
    
    Indicates a return statement with arguments inside a generator.
    """
    message_id = 'F14'
    message = '\'return\' with argument inside generator'


class ReturnOutsideFunction(Message):
    """
    Class defining the "Return outside function" message.
    
    Indicates a return statement outside of a function/method.
    """
    message_id = 'F15'
    message = '\'return\' outside function'

#
# eflag: noqa = M702
