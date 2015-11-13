# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the code style checker.
"""

import sys
import multiprocessing

import pep8
from NamingStyleChecker import NamingStyleChecker

# register the name checker
pep8.register_check(NamingStyleChecker, NamingStyleChecker.Codes)

from DocStyleChecker import DocStyleChecker
from MiscellaneousChecker import MiscellaneousChecker
from McCabeChecker import McCabeChecker


def initService():
    """
    Initialize the service and return the entry point.
    
    @return the entry point for the background client (function)
    """
    return codeStyleCheck


def initBatchService():
    """
    Initialize the batch service and return the entry point.
    
    @return the entry point for the background client (function)
    """
    return codeStyleBatchCheck


class CodeStyleCheckerReport(pep8.BaseReport):
    """
    Class implementing a special report to be used with our dialog.
    """
    def __init__(self, options):
        """
        Constructor
        
        @param options options for the report (optparse.Values)
        """
        super(CodeStyleCheckerReport, self).__init__(options)
        
        self.__repeat = options.repeat
        self.errors = []
    
    def error_args(self, line_number, offset, code, check, *args):
        """
        Public method to collect the error messages.
        
        @param line_number line number of the issue (integer)
        @param offset position within line of the issue (integer)
        @param code message code (string)
        @param check reference to the checker function (function)
        @param args arguments for the message (list)
        @return error code (string)
        """
        code = super(CodeStyleCheckerReport, self).error_args(
            line_number, offset, code, check, *args)
        if code and (self.counters[code] == 1 or self.__repeat):
            self.errors.append(
                (self.filename, line_number, offset, (code, args))
            )
        return code


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


def codeStyleCheck(filename, source, args):
    """
    Do the code style check and/ or fix found errors.
    
    @param filename source filename (string)
    @param source string containing the code to check (string)
    @param args arguments used by the codeStyleCheck function (list of
        excludeMessages (str), includeMessages (str), repeatMessages
        (bool), fixCodes (str), noFixCodes (str), fixIssues (bool),
        maxLineLength (int), hangClosing (bool), docType (str), errors
        (list of str), eol (str), encoding (str), backup (bool))
    @return tuple of stats (dict) and results (tuple for each found violation
        of style (tuple of lineno (int), position (int), text (str), ignored
            (bool), fixed (bool), autofixing (bool), fixedMsg (str)))
    """
    return __checkCodeStyle(filename, source, args)


def codeStyleBatchCheck(argumentsList, send, fx, cancelled):
    """
    Module function to check code style for a batch of files.
    
    @param argumentsList list of arguments tuples as given for codeStyleCheck
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
    for filename, source, args in iter(input.get, 'STOP'):
        result = __checkCodeStyle(filename, source, args)
        output.put((filename, result))


def __checkCodeStyle(filename, source, args):
    """
    Private module function to perform the code style check and/or fix
    found errors.
    
    @param filename source filename (string)
    @param source string containing the code to check (string)
    @param args arguments used by the codeStyleCheck function (list of
        excludeMessages (str), includeMessages (str), repeatMessages
        (bool), fixCodes (str), noFixCodes (str), fixIssues (bool),
        maxLineLength (int), hangClosing (bool), docType (str), errors
        (list of str), eol (str), encoding (str), backup (bool))
    @return tuple of stats (dict) and results (tuple for each found violation
        of style (tuple of lineno (int), position (int), text (str), ignored
            (bool), fixed (bool), autofixing (bool), fixedMsg (str)))
    """
    (excludeMessages, includeMessages, repeatMessages, fixCodes, noFixCodes,
     fixIssues, maxLineLength, hangClosing, docType, maxComplexity,
     miscellaneousArgs, errors, eol, encoding, backup) = args
    
    stats = {}

    if fixIssues:
        from CodeStyleFixer import CodeStyleFixer
        fixer = CodeStyleFixer(
            filename, source, fixCodes, noFixCodes,
            maxLineLength, True, eol, backup)  # always fix in place
    else:
        fixer = None
    
    if not errors:
        # avoid 'Encoding declaration in unicode string' exception on Python2
        if sys.version_info[0] == 2:
            if encoding == 'utf-8-bom':
                enc = 'utf-8'
            else:
                enc = encoding
            source = [line.encode(enc) for line in source]
        
        if includeMessages:
            select = [s.strip() for s in
                      includeMessages.split(',') if s.strip()]
        else:
            select = []
        if excludeMessages:
            ignore = [i.strip() for i in
                      excludeMessages.split(',') if i.strip()]
        else:
            ignore = []
        
        # check coding style
        styleGuide = pep8.StyleGuide(
            reporter=CodeStyleCheckerReport,
            repeat=repeatMessages,
            select=select,
            ignore=ignore,
            max_line_length=maxLineLength,
            hang_closing=hangClosing,
        )
        report = styleGuide.check_files([filename])
        stats.update(report.counters)
        errors = report.errors

        # check documentation style
        docStyleChecker = DocStyleChecker(
            source, filename, select, ignore, [], repeatMessages,
            maxLineLength=maxLineLength, docType=docType)
        docStyleChecker.run()
        stats.update(docStyleChecker.counters)
        errors += docStyleChecker.errors
        
        # miscellaneous additional checks
        miscellaneousChecker = MiscellaneousChecker(
            source, filename, select, ignore, [], repeatMessages,
            miscellaneousArgs)
        miscellaneousChecker.run()
        stats.update(miscellaneousChecker.counters)
        errors += miscellaneousChecker.errors
        
        # check code complexity iaw. McCabe
        mccabeChecker = McCabeChecker(
            source, filename, select, ignore, maxComplexity)
        mccabeChecker.run()
        stats.update(mccabeChecker.counters)
        errors += mccabeChecker.errors
    
    errorsDict = {}
    for fname, lineno, position, text in errors:
        if lineno > len(source):
            lineno = len(source)
        # inverse processing of messages and fixes
        errorLine = errorsDict.setdefault(lineno, [])
        errorLine.append([position, text])
    deferredFixes = {}
    results = []
    for lineno, errors in errorsDict.items():
        errors.sort(key=lambda x: x[0], reverse=True)
        for position, text in errors:
            if source:
                if "__IGNORE_WARNING__" not in \
                        extractLineFlags(source[lineno - 1].strip()):
                    if fixer:
                        res, msg, id_ = fixer.fixIssue(lineno, position, text)
                        if res == -1:
                            itm = [lineno, position, text]
                            deferredFixes[id_] = itm
                        else:
                            itm = [lineno, position, text, False,
                                   res == 1, True, msg]
                    else:
                        itm = [lineno, position, text, False,
                               False, False, '']
                    results.append(itm)
                else:
                    results.append([lineno, position, text, True,
                                    False, False, ''])
            else:
                results.append([lineno, position, text, False,
                                False, False, ''])
    
    if fixer:
        deferredResults = fixer.finalize()
        for id_ in deferredResults:
            fixed, msg = deferredResults[id_]
            itm = deferredFixes[id_]
            itm.extend([False, fixed == 1, True, msg])

        errMsg = fixer.saveFile(encoding)
        if errMsg:
            for result in results:
                result[-1] = errMsg

    return stats, results

#
# eflag: noqa = M702
