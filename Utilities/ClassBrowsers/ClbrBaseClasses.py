# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing base classes used by the various class browsers.
"""


from __future__ import unicode_literals


class _ClbrBase(object):
    """
    Class implementing the base of all class browser objects.
    """
    def __init__(self, module, name, file, lineno):
        """
        Constructor
        
        @param module name of the module containing this class
        @param name name of this class
        @param file filename containing this object
        @param lineno linenumber of the class definition
        """
        self.module = module
        self.name = name
        self.file = file
        self.lineno = lineno
        self.endlineno = -1     # marker for "not set"
        
    def setEndLine(self, endLineNo):
        """
        Public method to set the ending line number.
        
        @param endLineNo number of the last line (integer)
        """
        self.endlineno = endLineNo


class ClbrBase(_ClbrBase):
    """
    Class implementing the base of all complex class browser objects.
    """
    def __init__(self, module, name, file, lineno):
        """
        Constructor
        
        @param module name of the module containing this class
        @param name name of this class
        @param file filename containing this object
        @param lineno linenumber of the class definition
        """
        _ClbrBase.__init__(self, module, name, file, lineno)
        self.methods = {}
        self.attributes = {}
        self.classes = {}
        self.globals = {}
        
    def _addmethod(self, name, function):
        """
        Protected method to add information about a method.
        
        @param name name of method to be added (string)
        @param function Function object to be added
        """
        self.methods[name] = function
        
    def _getmethod(self, name):
        """
        Protected method to retrieve a method by name.
        
        @param name name of the method (string)
        @return the named method or None
        """
        try:
            return self.methods[name]
        except KeyError:
            return None
        
    def _addglobal(self, attr):
        """
        Protected method to add information about global variables.
        
        @param attr Attribute object to be added (Attribute)
        """
        if attr.name not in self.globals:
            self.globals[attr.name] = attr
        else:
            self.globals[attr.name].addAssignment(attr.lineno)
        
    def _getglobal(self, name):
        """
        Protected method to retrieve a global variable by name.
        
        @param name name of the global variable (string)
        @return the named global variable or None
        """
        try:
            return self.globals[name]
        except KeyError:
            return None
        
    def _addattribute(self, attr):
        """
        Protected method to add information about attributes.
        
        @param attr Attribute object to be added (Attribute)
        """
        if attr.name not in self.attributes:
            self.attributes[attr.name] = attr
        else:
            self.attributes[attr.name].addAssignment(attr.lineno)
        
    def _getattribute(self, name):
        """
        Protected method to retrieve an attribute by name.
        
        @param name name of the attribute (string)
        @return the named attribute or None
        """
        try:
            return self.attributes[name]
        except KeyError:
            return None
        
    def _addclass(self, name, _class):
        """
        Protected method method to add a nested class to this class.
        
        @param name name of the class
        @param _class Class object to be added (Class)
        """
        self.classes[name] = _class


class ClbrVisibilityMixinBase(object):
    """
    Class implementing the base class of all visibility mixins.
    """
    def isPrivate(self):
        """
        Public method to check, if the visibility is Private.
        
        @return flag indicating Private visibility (boolean)
        """
        return self.visibility == 0
        
    def isProtected(self):
        """
        Public method to check, if the visibility is Protected.
        
        @return flag indicating Protected visibility (boolean)
        """
        return self.visibility == 1
        
    def isPublic(self):
        """
        Public method to check, if the visibility is Public.
        
        @return flag indicating Public visibility (boolean)
        """
        return self.visibility == 2
        
    def setPrivate(self):
        """
        Public method to set the visibility to Private.
        """
        self.visibility = 0
        
    def setProtected(self):
        """
        Public method to set the visibility to Protected.
        """
        self.visibility = 1
        
    def setPublic(self):
        """
        Public method to set the visibility to Public.
        """
        self.visibility = 2


class Attribute(_ClbrBase):
    """
    Class to represent an attribute.
    """
    def __init__(self, module, name, file, lineno):
        """
        Constructor
        
        @param module name of the module containing this class
        @param name name of this class
        @param file filename containing this attribute
        @param lineno linenumber of the class definition
        """
        _ClbrBase.__init__(self, module, name, file, lineno)
        
        self.linenos = [lineno]
    
    def addAssignment(self, lineno):
        """
        Public method to add another assignment line number.
        
        @param lineno linenumber of the additional attribute assignment
            (integer)
        """
        if lineno not in self.linenos:
            self.linenos.append(lineno)


class Class(ClbrBase):
    """
    Class to represent a class.
    """
    def __init__(self, module, name, super, file, lineno):
        """
        Constructor
        
        @param module name of the module containing this class
        @param name name of this class
        @param super list of class names this class is inherited from
        @param file filename containing this class
        @param lineno linenumber of the class definition
        """
        ClbrBase.__init__(self, module, name, file, lineno)
        if super is None:
            super = []
        self.super = super


class Module(ClbrBase):
    """
    Class to represent a module.
    """
    def __init__(self, module, name, file, lineno):
        """
        Constructor
        
        @param module name of the module containing this module
        @param name name of this module
        @param file filename containing this module
        @param lineno linenumber of the module definition
        """
        ClbrBase.__init__(self, module, name, file, lineno)


class Function(ClbrBase):
    """
    Class to represent a function or method.
    """
    General = 0
    Static = 1
    Class = 2
    
    def __init__(self, module, name, file, lineno, signature='', separator=',',
                 modifierType=General, annotation=""):
        """
        Constructor
        
        @param module name of the module containing this function
        @param name name of this function
        @param file filename containing this class
        @param lineno linenumber of the class definition
        @param signature parameterlist of the method
        @param separator string separating the parameters
        @param modifierType type of the function
        @param annotation return annotation
        """
        ClbrBase.__init__(self, module, name, file, lineno)
        self.parameters = [e.strip() for e in signature.split(separator)]
        self.modifier = modifierType
        self.annotation = annotation


class Coding(ClbrBase):
    """
    Class to represent a source coding.
    """
    def __init__(self, module, file, lineno, coding):
        """
        Constructor
        
        @param module name of the module containing this module
        @param file filename containing this module
        @param lineno linenumber of the module definition
        @param coding character coding of the source file
        """
        ClbrBase.__init__(self, module, "Coding", file, lineno)
        self.coding = coding
