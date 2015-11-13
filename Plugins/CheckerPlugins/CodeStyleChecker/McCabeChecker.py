# -*- coding: utf-8 -*-

# Copyright (c) 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a checker for code complexity.
"""

import sys
import ast

from mccabe import PathGraphingAstVisitor


class McCabeChecker(object):
    """
    Class implementing a checker for code complexity iaw. McCabe.
    """
    Codes = [
        "C101",
        
        "C901",
    ]

    def __init__(self, source, filename, select, ignore, maxComplexity=10):
        """
        Constructor
        
        @param source source code to be checked
        @type list of str
        @param filename name of the source file
        @type str
        @param select list of selected codes
        @type list of str
        @param ignore list of codes to be ignored
        @type list of str
        @param maxComplexity maximum allowed complexity value
        @type int
        """
        self.__filename = filename
        self.__source = source[:]
        self.__maxComplexity = maxComplexity
        self.__select = tuple(select)
        self.__ignore = ('',) if select else tuple(ignore)
        
        # statistics counters
        self.counters = {}
        
        # collection of detected errors
        self.errors = []
    
    def __error(self, lineNumber, offset, code, *args):
        """
        Private method to record an issue.
        
        @param lineNumber line number of the issue
        @type int
        @param offset position within line of the issue
        @type int
        @param code message code
        @type str
        @param args arguments for the message
        @type list
        """
        if code in self.counters:
            self.counters[code] += 1
        else:
            self.counters[code] = 1
        
        if code:
            # record the issue with one based line number
            self.errors.append(
                (self.__filename, lineNumber, offset, (code, args)))
    
    def __reportInvalidSyntax(self):
        """
        Private method to report a syntax error.
        """
        exc_type, exc = sys.exc_info()[:2]
        if len(exc.args) > 1:
            offset = exc.args[1]
            if len(offset) > 2:
                offset = offset[1:3]
        else:
            offset = (1, 0)
        self.__error(offset[0] - 1, offset[1] or 0,
                     'C901', exc_type.__name__, exc.args[0])
    
    def __ignoreCode(self, code):
        """
        Private method to check if the error code should be ignored.

        @param code message code to check for (string)
        @return flag indicating to ignore the given code (boolean)
        """
        return (code.startswith(self.__ignore) and
                not code.startswith(self.__select))
    
    def run(self):
        """
        Public method to check the given source for code complexity.
        """
        if not self.__filename or not self.__source:
            # don't do anything, if essential data is missing
            return
        
        if self.__ignoreCode("C101"):
            # don't do anything, if this should be ignored
            return
        
        try:
            tree = compile(''.join(self.__source), self.__filename, 'exec',
                           ast.PyCF_ONLY_AST)
        except (SyntaxError, TypeError):
            self.__reportInvalidSyntax()
            return
        
        visitor = PathGraphingAstVisitor()
        visitor.preorder(tree, visitor)
        for graph in visitor.graphs.values():
            if graph.complexity() > self.__maxComplexity:
                self.__error(graph.lineno, 0, "C101",
                             graph.entity, graph.complexity())

#
# eflag: noqa = M702
