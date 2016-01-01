# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a checker for naming conventions.
"""

import collections
import ast
import re
import os
import sys

try:
    ast.AsyncFunctionDef    # __IGNORE_EXCEPTION__
except AttributeError:
    ast.AsyncFunctionDef = ast.FunctionDef


class NamingStyleChecker(object):
    """
    Class implementing a checker for naming conventions.
    """
    LowercaseRegex = re.compile(r"[_a-z][_a-z0-9]*$")
    UppercaseRegexp = re.compile(r"[_A-Z][_A-Z0-9]*$")
    CamelcaseRegexp = re.compile(r"_?[A-Z][a-zA-Z0-9]*$")
    MixedcaseRegexp = re.compile(r"_?[a-z][a-zA-Z0-9]*$")
    
    Codes = [
        "N801", "N802", "N803", "N804", "N805", "N806", "N807", "N808",
        "N811", "N812", "N813", "N814", "N821", "N831"
    ]
    
    def __init__(self, tree, filename, options):
        """
        Constructor (according to 'extended' pep8.py API)
        
        @param tree AST tree of the source file
        @param filename name of the source file (string)
        @param options options as parsed by pep8.StyleGuide
        """
        self.__parents = collections.deque()
        self.__tree = tree
        self.__filename = filename
        
        self.__checkersWithCodes = {
            "classdef": [
                (self.__checkClassName, ("N801",)),
                (self.__checkNameToBeAvoided, ("N831",)),
            ],
            "functiondef": [
                (self.__checkFuntionName, ("N802",)),
                (self.__checkFunctionArgumentNames,
                    ("N803", "N804", "N805", "N806")),
                (self.__checkNameToBeAvoided, ("N831",)),
            ],
            "assign": [
                (self.__checkVariablesInFunction, ("N821",)),
                (self.__checkNameToBeAvoided, ("N831",)),
            ],
            "importfrom": [
                (self.__checkImportAs, ("N811", "N812", "N813", "N814")),
            ],
            "module": [
                (self.__checkModule, ("N807", "N808")),
            ],
        }
        
        self.__checkers = {}
        for key, checkers in self.__checkersWithCodes.items():
            for checker, codes in checkers:
                if any(not (code and options.ignore_code(code))
                        for code in codes):
                    if key not in self.__checkers:
                        self.__checkers[key] = []
                    self.__checkers[key].append(checker)

    def run(self):
        """
        Public method run by the pep8.py checker.
        
        @return tuple giving line number, offset within line, code and
            checker function
        """
        if self.__tree and self.__checkers:
            return self.__visitTree(self.__tree)
        else:
            return ()
    
    def __visitTree(self, node):
        """
        Private method to scan the given AST tree.
        
        @param node AST tree node to scan
        @return tuple giving line number, offset within line, code and
            checker function
        """
        for error in self.__visitNode(node):
            yield error
        self.__parents.append(node)
        for child in ast.iter_child_nodes(node):
            for error in self.__visitTree(child):
                yield error
        self.__parents.pop()
    
    def __visitNode(self, node):
        """
        Private method to inspect the given AST node.
        
        @param node AST tree node to inspect
        @return tuple giving line number, offset within line, code and
            checker function
        """
        if isinstance(node, ast.ClassDef):
            self.__tagClassFunctions(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self.__findGlobalDefs(node)
        
        checkerName = node.__class__.__name__.lower()
        if checkerName in self.__checkers:
            for checker in self.__checkers[checkerName]:
                for error in checker(node, self.__parents):
                    yield error + (self.__checkers[checkerName],)
    
    def __tagClassFunctions(self, classNode):
        """
        Private method to tag functions if they are methods, class methods or
        static methods.
        
        @param classNode AST tree node to tag
        """
        # try to find all 'old style decorators' like
        # m = staticmethod(m)
        lateDecoration = {}
        for node in ast.iter_child_nodes(classNode):
            if not (isinstance(node, ast.Assign) and
                    isinstance(node.value, ast.Call) and
                    isinstance(node.value.func, ast.Name)):
                continue
            funcName = node.value.func.id
            if funcName in ("classmethod", "staticmethod"):
                meth = (len(node.value.args) == 1 and node.value.args[0])
                if isinstance(meth, ast.Name):
                    lateDecoration[meth.id] = funcName

        # iterate over all functions and tag them
        for node in ast.iter_child_nodes(classNode):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            
            node.function_type = 'method'
            if node.name == "__new__":
                node.function_type = "classmethod"
            
            if node.name in lateDecoration:
                node.function_type = lateDecoration[node.name]
            elif node.decorator_list:
                names = [d.id for d in node.decorator_list
                         if isinstance(d, ast.Name) and
                         d.id in ("classmethod", "staticmethod")]
                if names:
                    node.function_type = names[0]

    def __findGlobalDefs(self, functionNode):
        """
        Private method amend a node with global definitions information.
        
        @param functionNode AST tree node to amend
        """
        globalNames = set()
        nodesToCheck = collections.deque(ast.iter_child_nodes(functionNode))
        while nodesToCheck:
            node = nodesToCheck.pop()
            if isinstance(node, ast.Global):
                globalNames.update(node.names)

            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                     ast.ClassDef)):
                nodesToCheck.extend(ast.iter_child_nodes(node))
        functionNode.global_names = globalNames
    
    def __getArgNames(self, node):
        """
        Private method to get the argument names of a function node.
        
        @param node AST node to extract arguments names from
        @return list of argument names (list of string)
        """
        if sys.version_info[0] == 3:
            posArgs = [arg.arg for arg in node.args.args]
            kwOnly = [arg.arg for arg in node.args.kwonlyargs]
            return posArgs + kwOnly
        else:
            def unpackArgs(args):
                """
                Local helper function to unpack function argument names.
                
                @param args list of AST node arguments
                @return list of argument names (list of string)
                """
                ret = []
                for arg in args:
                    if isinstance(arg, ast.Tuple):
                        ret.extend(unpackArgs(arg.elts))
                    else:
                        ret.append(arg.id)
                return ret
           
            return unpackArgs(node.args.args)
    
    def __error(self, node, code):
        """
        Private method to build the error information.
        
        @param node AST node to report an error for
        @param code error code to report (string)
        @return tuple giving line number, offset within line and error code
            (integer, integer, string)
        """
        if isinstance(node, ast.Module):
            lineno = 0
            offset = 0
        else:
            lineno = node.lineno
            offset = node.col_offset
            if isinstance(node, ast.ClassDef):
                lineno += len(node.decorator_list)
                offset += 6
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lineno += len(node.decorator_list)
                offset += 4
        return (lineno, offset, code)
    
    def __isNameToBeAvoided(self, name):
        """
        Private method to check, if the given name should be avoided.
        
        @param name name to be checked (string)
        @return flag indicating to avoid it (boolen)
        """
        return name in ("l", "O", "I")
    
    def __checkNameToBeAvoided(self, node, parents):
        """
        Private class to check the given node for a name to be avoided (N831).
        
        @param node AST note to check
        @param parents list of parent nodes
        @return tuple giving line number, offset within line and error code
            (integer, integer, string)
        """
        if isinstance(node, (ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            name = node.name
            if self.__isNameToBeAvoided(name):
                yield self.__error(node, "N831")
                return
        
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            argNames = self.__getArgNames(node)
            for arg in argNames:
                if self.__isNameToBeAvoided(arg):
                    yield self.__error(node, "N831")
                    return
        
        if isinstance(node, ast.Assign):
            for target in node.targets:
                name = isinstance(target, ast.Name) and target.id
                if not name:
                    return
                
                if self.__isNameToBeAvoided(name):
                    yield self.__error(node, "N831")
                    return
    
    def __checkClassName(self, node, parents):
        """
        Private class to check the given node for class name
        conventions (N801).
        
        Almost without exception, class names use the CapWords convention.
        Classes for internal use have a leading underscore in addition.
        
        @param node AST note to check
        @param parents list of parent nodes
        @return tuple giving line number, offset within line and error code
            (integer, integer, string)
        """
        if not self.CamelcaseRegexp.match(node.name):
            yield self.__error(node, "N801")
    
    def __checkFuntionName(self, node, parents):
        """
        Private class to check the given node for function name
        conventions (N802).
        
        Function names should be lowercase, with words separated by underscores
        as necessary to improve readability. Functions <b>not</b> being
        methods '__' in front and back are not allowed. Mixed case is allowed
        only in contexts where that's already the prevailing style
        (e.g. threading.py), to retain backwards compatibility.
        
        @param node AST note to check
        @param parents list of parent nodes
        @return tuple giving line number, offset within line and error code
            (integer, integer, string)
        """
        functionType = getattr(node, "function_type", "function")
        name = node.name
        if (functionType == "function" and "__" in (name[:2], name[-2:])) or \
                not self.LowercaseRegex.match(name):
            yield self.__error(node, "N802")
    
    def __checkFunctionArgumentNames(self, node, parents):
        """
        Private class to check the argument names of functions
        (N803, N804, N805, N806).
        
        The argument names of a function should be lowercase, with words
        separated by underscores. A class method should have 'cls' as the
        first argument. A method should have 'self' as the first argument.
        
        @param node AST note to check
        @param parents list of parent nodes
        @return tuple giving line number, offset within line and error code
            (integer, integer, string)
        """
        if node.args.kwarg is not None:
            if sys.version_info >= (3, 4):
                kwarg = node.args.kwarg.arg
            else:
                kwarg = node.args.kwarg
            if not self.LowercaseRegex.match(kwarg):
                yield self.__error(node, "N803")
                return
        
        if node.args.vararg is not None:
            if sys.version_info >= (3, 4):
                vararg = node.args.vararg.arg
            else:
                vararg = node.args.vararg
            if not self.LowercaseRegex.match(vararg):
                yield self.__error(node, "N803")
                return
        
        argNames = self.__getArgNames(node)
        functionType = getattr(node, "function_type", "function")
        
        if not argNames:
            if functionType == "method":
                yield self.__error(node, "N805")
            elif functionType == "classmethod":
                yield self.__error(node, "N804")
            return
        
        if functionType == "method":
            if argNames[0] != "self":
                yield self.__error(node, "N805")
        elif functionType == "classmethod":
            if argNames[0] != "cls":
                yield self.__error(node, "N804")
        elif functionType == "staticmethod":
            if argNames[0] in ("cls", "self"):
                yield self.__error(node, "N806")
        for arg in argNames:
            if not self.LowercaseRegex.match(arg):
                yield self.__error(node, "N803")
                return
    
    def __checkVariablesInFunction(self, node, parents):
        """
        Private method to check local variables in functions (N821).
        
        Local variables in functions should be lowercase.
        
        @param node AST note to check
        @param parents list of parent nodes
        @return tuple giving line number, offset within line and error code
            (integer, integer, string)
        """
        for parentFunc in reversed(parents):
            if isinstance(parentFunc, ast.ClassDef):
                return
            if isinstance(parentFunc, (ast.FunctionDef, ast.AsyncFunctionDef)):
                break
        else:
            return
        for target in node.targets:
            name = isinstance(target, ast.Name) and target.id
            if not name or name in parentFunc.global_names:
                return
            
            if not self.LowercaseRegex.match(name) and name[:1] != '_':
                yield self.__error(target, "N821")
    
    def __checkModule(self, node, parents):
        """
        Private method to check module naming conventions (N807, N808).
        
        Module and package names should be lowercase.
        
        @param node AST note to check
        @param parents list of parent nodes
        @return tuple giving line number, offset within line and error code
            (integer, integer, string)
        """
        if self.__filename:
            moduleName = os.path.splitext(os.path.basename(self.__filename))[0]
            if moduleName.lower() != moduleName:
                yield self.__error(node, "N807")
            
            if moduleName == "__init__":
                # we got a package
                packageName = \
                    os.path.split(os.path.dirname(self.__filename))[1]
                if packageName.lower() != packageName:
                    yield self.__error(node, "N808")
    
    def __checkImportAs(self, node, parents):
        """
        Private method to check that imports don't change the
        naming convention (N811, N812, N813, N814).
        
        @param node AST note to check
        @param parents list of parent nodes
        @return tuple giving line number, offset within line and error code
            (integer, integer, string)
        """
        for name in node.names:
            if not name.asname:
                continue
            
            if self.UppercaseRegexp.match(name.name):
                if not self.UppercaseRegexp.match(name.asname):
                    yield self.__error(node, "N811")
            elif self.LowercaseRegex.match(name.name):
                if not self.LowercaseRegex.match(name.asname):
                    yield self.__error(node, "N812")
            elif self.LowercaseRegex.match(name.asname):
                yield self.__error(node, "N813")
            elif self.UppercaseRegexp.match(name.asname):
                yield self.__error(node, "N814")

#
# eflag: noqa = M702
