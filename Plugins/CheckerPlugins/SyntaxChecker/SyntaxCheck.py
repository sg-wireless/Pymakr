# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#
# pylint: disable=C0103

"""
Module implementing the syntax check for Python 2/3.
"""

from __future__ import unicode_literals

import ast
import re
import sys
import traceback
import multiprocessing

try:
    from pyflakes.checker import Checker
    from pyflakes.messages import ImportStarUsed
except ImportError:
    pass

VcsConflictMarkerRe = re.compile(
    r"""^<<<<<<< .*?=======.*?>>>>>>> .*?$""",
    re.MULTILINE | re.DOTALL)


def initService():
    """
    Initialize the service and return the entry point.
    
    @return the entry point for the background client (function)
    """
    return syntaxAndPyflakesCheck


def initBatchService():
    """
    Initialize the batch service and return the entry point.
    
    @return the entry point for the background client (function)
    """
    return syntaxAndPyflakesBatchCheck


def normalizeCode(codestring):
    """
    Function to normalize the given code.
    
    @param codestring code to be normalized (string)
    @return normalized code (string)
    """
    codestring = codestring.replace("\r\n", "\n").replace("\r", "\n")

    if codestring and codestring[-1] != '\n':
        codestring = codestring + '\n'

    # Check type for py2: if not str it's unicode
    if sys.version_info[0] == 2:
        try:
            codestring = codestring.encode('utf-8')
        except UnicodeError:
            pass
    
    return codestring


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


def syntaxAndPyflakesCheck(filename, codestring, checkFlakes=True,
                           ignoreStarImportWarnings=False):
    """
    Function to compile one Python source file to Python bytecode
    and to perform a pyflakes check.
    
    @param filename source filename (string)
    @param codestring string containing the code to compile (string)
    @keyparam checkFlakes flag indicating to do a pyflakes check (boolean)
    @keyparam ignoreStarImportWarnings flag indicating to
        ignore 'star import' warnings (boolean)
    @return dictionary with the keys 'error' and 'warnings' which
            hold a list containing details about the error/ warnings
            (file name, line number, column, codestring (only at syntax
            errors), the message, a list with arguments for the message)
    """
    return __syntaxAndPyflakesCheck(filename, codestring, checkFlakes,
                                    ignoreStarImportWarnings)


def syntaxAndPyflakesBatchCheck(argumentsList, send, fx, cancelled):
    """
    Module function to check syntax for a batch of files.
    
    @param argumentsList list of arguments tuples as given for
        syntaxAndPyflakesCheck
    @param send reference to send function (function)
    @param fx registered service name (string)
    @param cancelled reference to function checking for a cancellation
        (function)
    """
    try:
        NumberOfProcesses = multiprocessing.cpu_count()
        if NumberOfProcesses >= 1:
            NumberOfProcesses -= 1
    except NotImplementedError:
        NumberOfProcesses = 1

    # Create queues
    taskQueue = multiprocessing.Queue()
    doneQueue = multiprocessing.Queue()

    # Submit tasks (initially two time number of processes
    initialTasks = 2 * NumberOfProcesses
    for task in argumentsList[:initialTasks]:
        taskQueue.put(task)

    # Start worker processes
    for i in range(NumberOfProcesses):
        multiprocessing.Process(target=worker, args=(taskQueue, doneQueue))\
            .start()

    # Get and send results
    endIndex = len(argumentsList) - initialTasks
    for i in range(len(argumentsList)):
        filename, result = doneQueue.get()
        send(fx, filename, result)
        if cancelled():
            # just exit the loop ignoring the results of queued tasks
            break
        if i < endIndex:
            taskQueue.put(argumentsList[i + initialTasks])

    # Tell child processes to stop
    for i in range(NumberOfProcesses):
        taskQueue.put('STOP')


def worker(input, output):
    """
    Module function acting as the parallel worker for the style check.
    
    @param input input queue (multiprocessing.Queue)
    @param output output queue (multiprocessing.Queue)
    """
    for filename, args in iter(input.get, 'STOP'):
        source, checkFlakes, ignoreStarImportWarnings = args
        result = __syntaxAndPyflakesCheck(filename, source, checkFlakes,
                                          ignoreStarImportWarnings)
        output.put((filename, result))


def __syntaxAndPyflakesCheck(filename, codestring, checkFlakes=True,
                             ignoreStarImportWarnings=False):
    """
    Function to compile one Python source file to Python bytecode
    and to perform a pyflakes check.
    
    @param filename source filename (string)
    @param codestring string containing the code to compile (string)
    @keyparam checkFlakes flag indicating to do a pyflakes check (boolean)
    @keyparam ignoreStarImportWarnings flag indicating to
        ignore 'star import' warnings (boolean)
    @return dictionary with the keys 'error' and 'warnings' which
            hold a list containing details about the error/ warnings
            (file name, line number, column, codestring (only at syntax
            errors), the message, a list with arguments for the message)
    """
    try:
        import builtins
    except ImportError:
        import __builtin__ as builtins        # __IGNORE_WARNING__
    
    try:
        if sys.version_info[0] == 2:
            file_enc = filename.encode(sys.getfilesystemencoding())
        else:
            file_enc = filename
        
        # It also encode the code back to avoid 'Encoding declaration in
        # unicode string' exception on Python2
        codestring = normalizeCode(codestring)
        
        # Check for VCS conflict markers
        conflict = VcsConflictMarkerRe.search(codestring)
        if conflict is not None:
            start, i = conflict.span()
            lineindex = 1 + codestring.count("\n", 0, start)
            return [{'error':
                     (file_enc, lineindex, 0, "",
                      "VCS conflict marker found")
                     }]
        
        if filename.endswith('.ptl'):
            try:
                import quixote.ptl_compile
            except ImportError:
                return [{'error': (filename, 0, 0, '',
                        'Quixote plugin not found.')}]
            template = quixote.ptl_compile.Template(codestring, file_enc)
            template.compile()
        else:
            module = builtins.compile(
                codestring, file_enc, 'exec', ast.PyCF_ONLY_AST)
    except SyntaxError as detail:
        index = 0
        code = ""
        error = ""
        lines = traceback.format_exception_only(SyntaxError, detail)
        if sys.version_info[0] == 2:
            lines = [x.decode(sys.getfilesystemencoding()) for x in lines]
        match = re.match('\s*File "(.+)", line (\d+)',
                         lines[0].replace('<string>', filename))
        if match is not None:
            fn, line = match.group(1, 2)
            if lines[1].startswith('SyntaxError:'):
                error = re.match('SyntaxError: (.+)', lines[1]).group(1)
            else:
                code = re.match('(.+)', lines[1]).group(1)
                for seLine in lines[2:]:
                    if seLine.startswith('SyntaxError:'):
                        error = re.match('SyntaxError: (.+)', seLine).group(1)
                    elif seLine.rstrip().endswith('^'):
                        index = len(seLine.rstrip()) - 4
        else:
            fn = detail.filename
            line = detail.lineno or 1
            error = detail.msg
        return [{'error': (fn, int(line), index, code.strip(), error)}]
    except ValueError as detail:
        try:
            fn = detail.filename
            line = detail.lineno
            error = detail.msg
        except AttributeError:
            fn = filename
            line = 1
            error = str(detail)
        return [{'error': (fn, line, 0, "", error)}]
    except Exception as detail:
        try:
            fn = detail.filename
            line = detail.lineno
            error = detail.msg
            return [{'error': (fn, line, 0, "", error)}]
        except:         # this catchall is intentional
            pass
    
    # pyflakes
    if not checkFlakes:
        return [{}]
    
    results = []
    lines = codestring.splitlines()
    try:
        warnings = Checker(module, filename, withDoctest=True)
        warnings.messages.sort(key=lambda a: a.lineno)
        for warning in warnings.messages:
            if ignoreStarImportWarnings and \
                    isinstance(warning, ImportStarUsed):
                continue
            
            _fn, lineno, col, message, msg_args = warning.getMessageData()
            if "__IGNORE_WARNING__" not in extractLineFlags(
                    lines[lineno - 1].strip()):
                results.append((_fn, lineno, col, "", message, msg_args))
    except SyntaxError as err:
        if err.text.strip():
            msg = err.text.strip()
        else:
            msg = err.msg
        results.append((filename, err.lineno, 0, "FLAKES_ERROR", msg, []))
    
    return [{'warnings': results}]
