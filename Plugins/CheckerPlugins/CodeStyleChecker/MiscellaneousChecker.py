# -*- coding: utf-8 -*-

# Copyright (c) 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a checker for miscellaneous checks.
"""

from __future__ import unicode_literals

import sys
import ast
import re
import itertools
from string import Formatter


class MiscellaneousChecker(object):
    """
    Class implementing a checker for miscellaneous checks.
    """
    Codes = [
        "M101", "M102",
        "M111", "M112",
        "M121",
        
        "M601",
        "M611", "M612", "M613",
        "M621", "M622", "M623", "M624", "M625",
        "M631", "M632",
        
        "M701", "M702",
        
        "M801",
        "M811",
        
        "M901",
    ]
    
    Formatter = Formatter()
    FormatFieldRegex = re.compile(r'^((?:\s|.)*?)(\..*|\[.*\])?$')

    def __init__(self, source, filename, select, ignore, expected, repeat,
                 args):
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
        @param expected list of expected codes
        @type list of str
        @param repeat flag indicating to report each occurrence of a code
        @type bool
        @param args dictionary of arguments for the miscellaneous checks
        @type dict
        """
        self.__select = tuple(select)
        self.__ignore = ('',) if select else tuple(ignore)
        self.__expected = expected[:]
        self.__repeat = repeat
        self.__filename = filename
        self.__source = source[:]
        self.__args = args
        
        self.__blindExceptRegex = re.compile(
            r'(except:)')                               # __IGNORE_WARNING__
        self.__pep3101FormatRegex = re.compile(
            r'^(?:[^\'"]*[\'"][^\'"]*[\'"])*\s*%|^\s*%')

        # statistics counters
        self.counters = {}
        
        # collection of detected errors
        self.errors = []
        
        checkersWithCodes = [
            (self.__checkCoding, ("M101", "M102")),
            (self.__checkCopyright, ("M111", "M112")),
            (self.__checkBlindExcept, ("M121",)),
            (self.__checkPep3101, ("M601",)),
            (self.__checkFormatString, ("M611", "M612", "M613",
                                        "M621", "M622", "M623", "M624", "M625",
                                        "M631", "M632")),
            (self.__checkFuture, ("M701", "M702")),
            (self.__checkPrintStatements, ("M801",)),
            (self.__checkTuple, ("M811", )),
        ]
        
        self.__defaultArgs = {
            "CodingChecker": 'latin-1, utf-8',
            "CopyrightChecker": {
                "MinFilesize": 0,
                "Author": "",
            },
        }
        
        self.__checkers = []
        for checker, codes in checkersWithCodes:
            if any(not (code and self.__ignoreCode(code))
                    for code in codes):
                self.__checkers.append(checker)
    
    def __ignoreCode(self, code):
        """
        Private method to check if the message code should be ignored.

        @param code message code to check for
        @type str
        @return flag indicating to ignore the given code
        @rtype bool
        """
        return (code.startswith(self.__ignore) and
                not code.startswith(self.__select))
    
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
        if self.__ignoreCode(code):
            return
        
        if code in self.counters:
            self.counters[code] += 1
        else:
            self.counters[code] = 1
        
        # Don't care about expected codes
        if code in self.__expected:
            return
        
        if code and (self.counters[code] == 1 or self.__repeat):
            # record the issue with one based line number
            self.errors.append(
                (self.__filename, lineNumber + 1, offset, (code, args)))
    
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
                     'M901', exc_type.__name__, exc.args[0])
    
    def run(self):
        """
        Public method to check the given source against miscellaneous
        conditions.
        """
        if not self.__filename:
            # don't do anything, if essential data is missing
            return
        
        if not self.__checkers:
            # don't do anything, if no codes were selected
            return
        
        source = "".join(self.__source)
        # Check type for py2: if not str it's unicode
        if sys.version_info[0] == 2:
            try:
                source = source.encode('utf-8')
            except UnicodeError:
                pass
        try:
            self.__tree = compile(source, self.__filename, 'exec',
                                  ast.PyCF_ONLY_AST)
        except (SyntaxError, TypeError):
            self.__reportInvalidSyntax()
            return
        
        for check in self.__checkers:
            check()
    
    def __getCoding(self):
        """
        Private method to get the defined coding of the source.
        
        @return tuple containing the line number and the coding
        @rtype tuple of int and str
        """
        for lineno, line in enumerate(self.__source[:2]):
            matched = re.search('coding[:=]\s*([-\w_.]+)', line, re.IGNORECASE)
            if matched:
                return lineno, matched.group(1)
        else:
            return 0, ""
    
    def __checkCoding(self):
        """
        Private method to check the presence of a coding line and valid
        encodings.
        """
        if len(self.__source) == 0:
            return
        
        encodings = [e.lower().strip()
                     for e in self.__args.get(
                     "CodingChecker", self.__defaultArgs["CodingChecker"])
                     .split(",")]
        lineno, coding = self.__getCoding()
        if coding:
            if coding.lower() not in encodings:
                self.__error(lineno, 0, "M102", coding)
        else:
            self.__error(0, 0, "M101")
    
    def __checkCopyright(self):
        """
        Private method to check the presence of a copyright statement.
        """
        source = "".join(self.__source)
        copyrightArgs = self.__args.get(
            "CopyrightChecker", self.__defaultArgs["CopyrightChecker"])
        copyrightMinFileSize = copyrightArgs.get(
            "MinFilesize",
            self.__defaultArgs["CopyrightChecker"]["MinFilesize"])
        copyrightAuthor = copyrightArgs.get(
            "Author",
            self.__defaultArgs["CopyrightChecker"]["Author"])
        copyrightRegexStr = \
            r"Copyright\s+(\(C\)\s+)?(\d{{4}}\s+-\s+)?\d{{4}}\s+{author}"
        
        tocheck = max(1024, copyrightMinFileSize)
        topOfSource = source[:tocheck]
        if len(topOfSource) < copyrightMinFileSize:
            return

        copyrightRe = re.compile(copyrightRegexStr.format(author=r".*"),
                                 re.IGNORECASE)
        if not copyrightRe.search(topOfSource):
            self.__error(0, 0, "M111")
            return
        
        if copyrightAuthor:
            copyrightAuthorRe = re.compile(
                copyrightRegexStr.format(author=copyrightAuthor),
                re.IGNORECASE)
            if not copyrightAuthorRe.search(topOfSource):
                self.__error(0, 0, "M112")
    
    def __checkBlindExcept(self):
        """
        Private method to check for blind except statements.
        """
        for lineno, line in enumerate(self.__source):
            match = self.__blindExceptRegex.search(line)
            if match:
                self.__error(lineno, match.start(), "M121")
    
    def __checkPrintStatements(self):
        """
        Private method to check for print statements.
        """
        for node in ast.walk(self.__tree):
            if (isinstance(node, ast.Call) and
                getattr(node.func, 'id', None) == 'print') or \
               (hasattr(ast, 'Print') and isinstance(node, ast.Print)):
                self.__error(node.lineno - 1, node.col_offset, "M801")
    
    def __checkTuple(self):
        """
        Private method to check for one element tuples.
        """
        for node in ast.walk(self.__tree):
            if isinstance(node, ast.Tuple) and \
                    len(node.elts) == 1:
                self.__error(node.lineno - 1, node.col_offset, "M811")
    
    def __checkFuture(self):
        """
        Private method to check the __future__ imports.
        """
        expectedImports = set(
            [i.strip()
             for i in self.__args.get("FutureChecker", "").split(",")
             if bool(i.strip())])
        if len(expectedImports) == 0:
            # nothing to check for; disabling the check
            return
        
        imports = set()
        node = None
        hasCode = False
        
        for node in ast.walk(self.__tree):
            if (isinstance(node, ast.ImportFrom) and
                    node.module == '__future__'):
                imports |= set(name.name for name in node.names)
            elif isinstance(node, ast.Expr):
                if not isinstance(node.value, ast.Str):
                    hasCode = True
                    break
            elif not isinstance(node, (ast.Module, ast.Str)):
                hasCode = True
                break

        if isinstance(node, ast.Module) or not hasCode:
            return

        if not (imports >= expectedImports):
            if imports:
                self.__error(node.lineno - 1, node.col_offset, "M701",
                             ", ".join(expectedImports), ", ".join(imports))
            else:
                self.__error(node.lineno - 1, node.col_offset, "M702",
                             ", ".join(expectedImports))
    
    def __checkPep3101(self):
        """
        Private method to check for old style string formatting.
        """
        for lineno, line in enumerate(self.__source):
            match = self.__pep3101FormatRegex.search(line)
            if match:
                lineLen = len(line)
                pos = line.find('%')
                formatPos = pos
                formatter = '%'
                if line[pos + 1] == "(":
                    pos = line.find(")", pos)
                c = line[pos]
                while c not in "diouxXeEfFgGcrs":
                    pos += 1
                    if pos >= lineLen:
                        break
                    c = line[pos]
                if c in "diouxXeEfFgGcrs":
                    formatter += c
                self.__error(lineno, formatPos, "M601", formatter)
    
    def __checkFormatString(self):
        """
        Private method to check string format strings.
        """
        coding = self.__getCoding()[1]
        if not coding:
            # default to utf-8
            coding = "utf-8"
        
        visitor = TextVisitor()
        visitor.visit(self.__tree)
        for node in visitor.nodes:
            text = node.s
            if sys.version_info[0] > 2 and isinstance(text, bytes):
                try:
                    text = text.decode(coding)
                except UnicodeDecodeError:
                    continue
            fields, implicit, explicit = self.__getFields(text)
            if implicit:
                if node in visitor.calls:
                    self.__error(node.lineno - 1, node.col_offset, "M611")
                else:
                    if node.is_docstring:
                        self.__error(node.lineno - 1, node.col_offset, "M612")
                    else:
                        self.__error(node.lineno - 1, node.col_offset, "M613")
            
            if node in visitor.calls:
                call, strArgs = visitor.calls[node]
                
                numbers = set()
                names = set()
                # Determine which fields require a keyword and which an arg
                for name in fields:
                    fieldMatch = self.FormatFieldRegex.match(name)
                    try:
                        number = int(fieldMatch.group(1))
                    except ValueError:
                        number = -1
                    # negative numbers are considered keywords
                    if number >= 0:
                        numbers.add(number)
                    else:
                        names.add(fieldMatch.group(1))
                
                keywords = set(keyword.arg for keyword in call.keywords)
                numArgs = len(call.args)
                if strArgs:
                    numArgs -= 1
                if sys.version_info < (3, 5):
                    hasKwArgs = bool(call.kwargs)
                    hasStarArgs = bool(call.starargs)
                else:
                    hasKwArgs = any(kw.arg is None for kw in call.keywords)
                    hasStarArgs = sum(1 for arg in call.args
                                      if isinstance(arg, ast.Starred))
                    
                    if hasKwArgs:
                        keywords.discard(None)
                    if hasStarArgs:
                        numArgs -= 1
                
                # if starargs or kwargs is not None, it can't count the
                # parameters but at least check if the args are used
                if hasKwArgs:
                    if not names:
                        # No names but kwargs
                        self.__error(call.lineno - 1, call.col_offset, "M623")
                if hasStarArgs:
                    if not numbers:
                        # No numbers but args
                        self.__error(call.lineno - 1, call.col_offset, "M624")
                
                if not hasKwArgs and not hasStarArgs:
                    # can actually verify numbers and names
                    for number in sorted(numbers):
                        if number >= numArgs:
                            self.__error(call.lineno - 1, call.col_offset,
                                         "M621", number)
                    
                    for name in sorted(names):
                        if name not in keywords:
                            self.__error(call.lineno - 1, call.col_offset,
                                         "M622", name)
                
                for arg in range(numArgs):
                    if arg not in numbers:
                        self.__error(call.lineno - 1, call.col_offset, "M631",
                                     arg)
                
                for keyword in keywords:
                    if keyword not in names:
                        self.__error(call.lineno - 1, call.col_offset, "M632",
                                     keyword)
                
                if implicit and explicit:
                    self.__error(call.lineno - 1, call.col_offset, "M625")
    
    def __getFields(self, string):
        """
        Private method to extract the format field information.
        
        @param string format string to be parsed
        @type str
        @return format field information as a tuple with fields, implicit
            field definitions present and explicit field definitions present
        @rtype tuple of set of str, bool, bool
        """
        fields = set()
        cnt = itertools.count()
        implicit = False
        explicit = False
        try:
            for literal, field, spec, conv in self.Formatter.parse(string):
                if field is not None and (conv is None or conv in 'rsa'):
                    if not field:
                        field = str(next(cnt))
                        implicit = True
                    else:
                        explicit = True
                    fields.add(field)
                    fields.update(parsedSpec[1]
                                  for parsedSpec in self.Formatter.parse(spec)
                                  if parsedSpec[1] is not None)
        except ValueError:
            return set(), False, False
        else:
            return fields, implicit, explicit


class TextVisitor(ast.NodeVisitor):
    """
    Class implementing a node visitor for bytes and str instances.

    It tries to detect docstrings as string of the first expression of each
    module, class or function.
    """
    # modelled after the string format flake8 extension
    
    def __init__(self):
        """
        Constructor
        """
        super(TextVisitor, self).__init__()
        self.nodes = []
        self.calls = {}

    def __addNode(self, node):
        """
        Private method to add a node to our list of nodes.
        
        @param node reference to the node to add
        @type ast.AST
        """
        if not hasattr(node, 'is_docstring'):
            node.is_docstring = False
        self.nodes.append(node)

    def __isBaseString(self, node):
        """
        Private method to determine, if a node is a base string node.
        
        @param node reference to the node to check
        @type ast.AST
        @return flag indicating a base string
        @rtype bool
        """
        typ = (ast.Str,)
        if sys.version_info[0] > 2:
            typ += (ast.Bytes,)
        return isinstance(node, typ)

    def visit_Str(self, node):
        """
        Public method to record a string node.
        
        @param node reference to the string node
        @type ast.Str
        """
        self.__addNode(node)

    def visit_Bytes(self, node):
        """
        Public method to record a bytes node.
        
        @param node reference to the bytes node
        @type ast.Bytes
        """
        self.__addNode(node)

    def __visitDefinition(self, node):
        """
        Private method handling class and function definitions.
        
        @param node reference to the node to handle
        @type ast.FunctionDef or ast.ClassDef
        """
        # Manually traverse class or function definition
        # * Handle decorators normally
        # * Use special check for body content
        # * Don't handle the rest (e.g. bases)
        for decorator in node.decorator_list:
            self.visit(decorator)
        self.__visitBody(node)

    def __visitBody(self, node):
        """
        Private method to traverse the body of the node manually.

        If the first node is an expression which contains a string or bytes it
        marks that as a docstring.
        
        @param node reference to the node to traverse
        @type ast.AST
        """
        if (node.body and isinstance(node.body[0], ast.Expr) and
                self.__isBaseString(node.body[0].value)):
            node.body[0].value.is_docstring = True

        for subnode in node.body:
            self.visit(subnode)

    def visit_Module(self, node):
        """
        Public method to handle a module.
        
        @param node reference to the node to handle
        @type ast.Module
        """
        self.__visitBody(node)

    def visit_ClassDef(self, node):
        """
        Public method to handle a class definition.
        
        @param node reference to the node to handle
        @type ast.ClassDef
        """
        # Skipped nodes: ('name', 'bases', 'keywords', 'starargs', 'kwargs')
        self.__visitDefinition(node)

    def visit_FunctionDef(self, node):
        """
        Public method to handle a function definition.
        
        @param node reference to the node to handle
        @type ast.FunctionDef
        """
        # Skipped nodes: ('name', 'args', 'returns')
        self.__visitDefinition(node)

    def visit_Call(self, node):
        """
        Public method to handle a function call.
        
        @param node reference to the node to handle
        @type ast.Call
        """
        if (isinstance(node.func, ast.Attribute) and
                node.func.attr == 'format'):
            if self.__isBaseString(node.func.value):
                self.calls[node.func.value] = (node, False)
            elif (isinstance(node.func.value, ast.Name) and
                    node.func.value.id == 'str' and node.args and
                    self.__isBaseString(node.args[0])):
                self.calls[node.args[0]] = (node, True)
        super(TextVisitor, self).generic_visit(node)
