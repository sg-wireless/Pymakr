# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a TestResult derivative for the eric6 debugger.
"""

import select
from unittest import TestResult


from DebugProtocol import ResponseUTTestFailed, ResponseUTTestErrored, \
    ResponseUTStartTest, ResponseUTStopTest, ResponseUTTestSkipped, \
    ResponseUTTestFailedExpected, ResponseUTTestSucceededUnexpected


class DCTestResult(TestResult):
    """
    A TestResult derivative to work with eric6's debug client.
    
    For more details see unittest.py of the standard python distribution.
    """
    def __init__(self, parent):
        """
        Constructor
        
        @param parent The parent widget.
        """
        TestResult.__init__(self)
        self.parent = parent
        
    def addFailure(self, test, err):
        """
        Public method called if a test failed.
        
        @param test Reference to the test object
        @param err The error traceback
        """
        TestResult.addFailure(self, test, err)
        tracebackLines = self._exc_info_to_string(err, test)
        self.parent.write('{0}{1}\n'.format(
            ResponseUTTestFailed,
            str((str(test), tracebackLines, test.id()))))
        
    def addError(self, test, err):
        """
        Public method called if a test errored.
        
        @param test Reference to the test object
        @param err The error traceback
        """
        TestResult.addError(self, test, err)
        tracebackLines = self._exc_info_to_string(err, test)
        self.parent.write('{0}{1}\n'.format(
            ResponseUTTestErrored,
            str((str(test), tracebackLines, test.id()))))
        
    def addSkip(self, test, reason):
        """
        Public method called if a test was skipped.
        
        @param test reference to the test object
        @param reason reason for skipping the test (string)
        """
        TestResult.addSkip(self, test, reason)
        self.parent.write('{0}{1}\n'.format(
            ResponseUTTestSkipped,
            str((str(test), reason, test.id()))))
        
    def addExpectedFailure(self, test, err):
        """
        Public method called if a test failed expected.
        
        @param test reference to the test object
        @param err error traceback
        """
        TestResult.addExpectedFailure(self, test, err)
        tracebackLines = self._exc_info_to_string(err, test)
        self.parent.write('{0}{1}\n'.format(
            ResponseUTTestFailedExpected,
            str((str(test), tracebackLines, test.id()))))
        
    def addUnexpectedSuccess(self, test):
        """
        Public method called if a test succeeded expectedly.
        
        @param test reference to the test object
        """
        TestResult.addUnexpectedSuccess(self, test)
        self.parent.write('{0}{1}\n'.format(
            ResponseUTTestSucceededUnexpected,
            str((str(test), test.id()))))
        
    def startTest(self, test):
        """
        Public method called at the start of a test.
        
        @param test Reference to the test object
        """
        TestResult.startTest(self, test)
        self.parent.write('{0}{1}\n'.format(
            ResponseUTStartTest,
            str((str(test), test.shortDescription()))))

    def stopTest(self, test):
        """
        Public method called at the end of a test.
        
        @param test Reference to the test object
        """
        TestResult.stopTest(self, test)
        self.parent.write('{0}\n'.format(ResponseUTStopTest))
        
        # ensure that pending input is processed
        rrdy, wrdy, xrdy = select.select(
            [self.parent.readstream], [], [], 0.01)

        if self.parent.readstream in rrdy:
            self.parent.readReady(self.parent.readstream.fileno())
