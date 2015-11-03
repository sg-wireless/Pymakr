# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Parse a JavaScript file and retrieve variables and functions.

It uses the JavaScript parser contained in the jasy web framework.
"""

from __future__ import unicode_literals

import jasy.js.parse.Parser as jsParser
import jasy.js.tokenize.Tokenizer as jsTokenizer

import Utilities
import Utilities.ClassBrowsers as ClassBrowsers
from . import ClbrBaseClasses

SUPPORTED_TYPES = [ClassBrowsers.JS_SOURCE]
    
_modules = {}   # cache of modules we've seen


class VisibilityMixin(ClbrBaseClasses.ClbrVisibilityMixinBase):
    """
    Mixin class implementing the notion of visibility.
    """
    def __init__(self):
        """
        Constructor
        """
        if self.name.startswith('__'):
            self.setPrivate()
        elif self.name.startswith('_'):
            self.setProtected()
        else:
            self.setPublic()


class Function(ClbrBaseClasses.Function, VisibilityMixin):
    """
    Class to represent a Python function.
    """
    def __init__(self, module, name, file, lineno, signature='',
                 separator=','):
        """
        Constructor
        
        @param module name of the module containing this function
        @param name name of this function
        @param file filename containing this class
        @param lineno linenumber of the class definition
        @param signature parameterlist of the method
        @param separator string separating the parameters
        """
        ClbrBaseClasses.Function.__init__(self, module, name, file, lineno,
                                          signature, separator)
        VisibilityMixin.__init__(self)


class Attribute(ClbrBaseClasses.Attribute, VisibilityMixin):
    """
    Class to represent a class attribute.
    """
    def __init__(self, module, name, file, lineno):
        """
        Constructor
        
        @param module name of the module containing this class
        @param name name of this class
        @param file filename containing this attribute
        @param lineno linenumber of the class definition
        """
        ClbrBaseClasses.Attribute.__init__(self, module, name, file, lineno)
        VisibilityMixin.__init__(self)


class Visitor(object):
    """
    Class implementing a visitor going through the parsed tree.
    """
    def __init__(self, src, module, filename):
        """
        Constructor
        
        @param src source to be parsed (string)
        @param module name of the module (string)
        @param filename file name (string)
        """
        self.__dict = {}
        self.__dict_counts = {}
        self.__root = None
        self.__stack = []
        
        self.__module = module
        self.__file = filename
        self.__source = src
        
        # normalize line endings
        self.__source = self.__source.replace("\r\n", "\n").replace("\r", "\n")
        
        # ensure source ends with an eol
        if self.__source[-1] != '\n':
            self.__source = self.__source + '\n'
    
    def parse(self):
        """
        Public method to parse the source.
        
        @return dictionary containing the parsed information
        """
        try:
            self.__root = jsParser.parse(self.__source, self.__file)
            self.__visit(self.__root)
        except jsParser.SyntaxError:
            # ignore syntax errors of the parser
            pass
        except jsTokenizer.ParseError:
            # ignore syntax errors of the tokenizer
            pass
        
        return self.__dict
    
    def __visit(self, root):
        """
        Private method implementing the visit logic delegating to interesting
        methods.
        
        @param root root node to visit
        """
        call = lambda n: getattr(self, "visit_{0}".format(n.type),
                                 self.visit_noop)(n)
        call(root)
        for node in root:
            self.__visit(node)
    
    def visit_noop(self, node):
        """
        Public method to ignore the given node.
        
        @param node reference to the node (jasy.js.parse.Node.Node)
        """
        pass

    def visit_function(self, node):
        """
        Public method to treat a function node.
        
        @param node reference to the node (jasy.js.parse.Node.Node)
        """
        if node.type == "function" and \
           getattr(node, "name", None) and \
           node.functionForm == "declared_form":
            if self.__stack and self.__stack[-1].endlineno < node.line:
                del self.__stack[-1]
            endline = node.line + self.__source.count(
                '\n', node.start, node.end)
            if getattr(node, "params", None):
                func_sig = ", ".join([p.value for p in node.params])
            else:
                func_sig = ""
            if self.__stack:
                # it's a nested function
                cur_func = self.__stack[-1]
                f = Function(None, node.name,
                             self.__file, node.line, func_sig)
                f.setEndLine(endline)
                cur_func._addmethod(node.name, f)
            else:
                f = Function(self.__module, node.name,
                             self.__file, node.line, func_sig)
                f.setEndLine(endline)
                func_name = node.name
                if func_name in self.__dict_counts:
                    self.__dict_counts[func_name] += 1
                    func_name = "{0}_{1:d}".format(
                        func_name, self.__dict_counts[func_name])
                else:
                    self.__dict_counts[func_name] = 0
                self.__dict[func_name] = f
            self.__stack.append(f)

    def visit_property_init(self, node):
        """
        Public method to treat a property_init node.
        
        @param node reference to the node (jasy.js.parse.Node.Node)
        """
        if node.type == "property_init" and node[1].type == "function":
            if self.__stack and self.__stack[-1].endlineno < node[0].line:
                del self.__stack[-1]
            endline = node[0].line + self.__source.count(
                '\n', node.start, node[1].end)
            if getattr(node[1], "params", None):
                func_sig = ", ".join([p.value for p in node[1].params])
            else:
                func_sig = ""
            if self.__stack:
                # it's a nested function
                cur_func = self.__stack[-1]
                f = Function(None, node[0].value,
                             self.__file, node[0].line, func_sig)
                f.setEndLine(endline)
                cur_func._addmethod(node[0].value, f)
            else:
                f = Function(self.__module, node[0].value,
                             self.__file, node[0].line, func_sig)
                f.setEndLine(endline)
                func_name = node[0].value
                if func_name in self.__dict_counts:
                    self.__dict_counts[func_name] += 1
                    func_name = "{0}_{1:d}".format(
                        func_name, self.__dict_counts[func_name])
                else:
                    self.__dict_counts[func_name] = 0
                self.__dict[func_name] = f
            self.__stack.append(f)
    
    def visit_var(self, node):
        """
        Public method to treat a variable node.
        
        @param node reference to the node (jasy.js.parse.Node.Node)
        """
        if node.type == "var" and \
           node.parent.type == "script" and \
           node.getChildrenLength():
            if self.__stack and self.__stack[-1].endlineno < node[0].line:
                del self.__stack[-1]
            if self.__stack:
                # function variables
                for var in node:
                    attr = Attribute(
                        self.__module, var.name, self.__file, var.line)
                    self.__stack[-1]._addattribute(attr)
            else:
                # global variable
                if "@@Globals@@" not in self.__dict:
                    self.__dict["@@Globals@@"] = ClbrBaseClasses.ClbrBase(
                        self.__module, "Globals", self.__file, 0)
                for var in node:
                    self.__dict["@@Globals@@"]._addglobal(Attribute(
                        self.__module, var.name, self.__file, var.line))
    
    def visit_const(self, node):
        """
        Public method to treat a constant node.
        
        @param node reference to the node (jasy.js.parse.Node.Node)
        """
        if node.type == "const" and \
           node.parent.type == "script" and \
           node.getChildrenLength():
            if self.__stack and self.__stack[-1].endlineno < node[0].line:
                del self.__stack[-1]
            if self.__stack:
                # function variables
                for var in node:
                    attr = Attribute(self.__module, "const " + var.name,
                                     self.__file, var.line)
                    self.__stack[-1]._addattribute(attr)
            else:
                # global variable
                if "@@Globals@@" not in self.__dict:
                    self.__dict["@@Globals@@"] = ClbrBaseClasses.ClbrBase(
                        self.__module, "Globals", self.__file, 0)
                for var in node:
                    self.__dict["@@Globals@@"]._addglobal(
                        Attribute(self.__module, "const " + var.name,
                                  self.__file, var.line))


def readmodule_ex(module, path=[]):
    """
    Read a JavaScript file and return a dictionary of functions and variables.

    @param module name of the JavaScript file (string)
    @param path path the file should be searched in (list of strings)
    @return the resulting dictionary
    """
    global _modules
    
    dict = {}

    if module in _modules:
        # we've seen this file before...
        return _modules[module]

    # search the path for the file
    f = None
    fullpath = list(path)
    f, file, (suff, mode, type) = ClassBrowsers.find_module(module, fullpath)
    if f:
        f.close()
    if type not in SUPPORTED_TYPES:
        # not CORBA IDL source, can't do anything with this module
        _modules[module] = dict
        return dict

    _modules[module] = dict
    try:
        src = Utilities.readEncodedFile(file)[0]
    except (UnicodeError, IOError):
        # can't do anything with this module
        _modules[module] = dict
        return dict
    
    visitor = Visitor(src, module, file)
    dict = visitor.parse()
    _modules[module] = dict
    return dict
