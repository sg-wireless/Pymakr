# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dummy debugger interface for the debug server.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject


ClientDefaultCapabilities = 0
    
ClientTypeAssociations = []


def getRegistryData():
    """
    Module functionto get characterising data for the debugger interface.
    
    @return list of the following data. Client type (string), client
        capabilities (integer), client type association (list of strings)
    """
    return ["None", ClientDefaultCapabilities, ClientTypeAssociations]


class DebuggerInterfaceNone(QObject):
    """
    Class implementing a dummy debugger interface for the debug server.
    """
    def __init__(self, debugServer, passive):
        """
        Constructor
        
        @param debugServer reference to the debug server (DebugServer)
        @param passive flag indicating passive connection mode (boolean)
        """
        super(DebuggerInterfaceNone, self).__init__()
        
        self.debugServer = debugServer
        self.passive = passive
        
        self.qsock = None
        self.queue = []
        # set default values for capabilities of clients
        self.clientCapabilities = ClientDefaultCapabilities
        
    def startRemote(self, port, runInConsole):
        """
        Public method to start a remote Python interpreter.
        
        @param port portnumber the debug server is listening on (integer)
        @param runInConsole flag indicating to start the debugger in a
            console window (boolean)
        @return client process object (QProcess), a flag to indicate
            a network connection (boolean) and the name of the interpreter
            in case of a local execution (string)
        """
        return None, True, ""

    def startRemoteForProject(self, port, runInConsole):
        """
        Public method to start a remote Python interpreter for a project.
        
        @param port portnumber the debug server is listening on (integer)
        @param runInConsole flag indicating to start the debugger in a
            console window (boolean)
        @return client process object (QProcess), a flag to indicate
            a network connection (boolean) and the name of the interpreter
            in case of a local execution (string)
        """
        return None, True, ""

    def getClientCapabilities(self):
        """
        Public method to retrieve the debug clients capabilities.
        
        @return debug client capabilities (integer)
        """
        return self.clientCapabilities
        
    def newConnection(self, sock):
        """
        Public slot to handle a new connection.
        
        @param sock reference to the socket object (QTcpSocket)
        @return flag indicating success (boolean)
        """
        return False
        
    def flush(self):
        """
        Public slot to flush the queue.
        """
        self.queue = []
        
    def shutdown(self):
        """
        Public method to cleanly shut down.
        
        It closes our socket and shuts down
        the debug client. (Needed on Win OS)
        """
        self.qsock = None
        self.queue = []
        
    def isConnected(self):
        """
        Public method to test, if a debug client has connected.
        
        @return flag indicating the connection status (boolean)
        """
        return self.qsock is not None
        
    def remoteEnvironment(self, env):
        """
        Public method to set the environment for a program to debug, run, ...
        
        @param env environment settings (dictionary)
        """
        return
        
    def remoteLoad(self, fn, argv, wd, traceInterpreter=False,
                   autoContinue=True, autoFork=False, forkChild=False):
        """
        Public method to load a new program to debug.
        
        @param fn the filename to debug (string)
        @param argv the commandline arguments to pass to the program (string)
        @param wd the working directory for the program (string)
        @keyparam traceInterpreter flag indicating if the interpreter library
            should be traced as well (boolean)
        @keyparam autoContinue flag indicating, that the debugger should not
            stop at the first executable line (boolean)
        @keyparam autoFork flag indicating the automatic fork mode (boolean)
        @keyparam forkChild flag indicating to debug the child after forking
            (boolean)
        """
        return
        
    def remoteRun(self, fn, argv, wd, autoFork=False, forkChild=False):
        """
        Public method to load a new program to run.
        
        @param fn the filename to run (string)
        @param argv the commandline arguments to pass to the program (string)
        @param wd the working directory for the program (string)
        @keyparam autoFork flag indicating the automatic fork mode (boolean)
        @keyparam forkChild flag indicating to debug the child after forking
            (boolean)
        """
        return
        
    def remoteCoverage(self, fn, argv, wd, erase=False):
        """
        Public method to load a new program to collect coverage data.
        
        @param fn the filename to run (string)
        @param argv the commandline arguments to pass to the program (string)
        @param wd the working directory for the program (string)
        @keyparam erase flag indicating that coverage info should be
            cleared first (boolean)
        """
        return

    def remoteProfile(self, fn, argv, wd, erase=False):
        """
        Public method to load a new program to collect profiling data.
        
        @param fn the filename to run (string)
        @param argv the commandline arguments to pass to the program (string)
        @param wd the working directory for the program (string)
        @keyparam erase flag indicating that timing info should be cleared
            first (boolean)
        """
        return

    def remoteStatement(self, stmt):
        """
        Public method to execute a Python statement.
        
        @param stmt the Python statement to execute (string). It
              should not have a trailing newline.
        """
        self.debugServer.signalClientStatement(False)
        return

    def remoteStep(self):
        """
        Public method to single step the debugged program.
        """
        return

    def remoteStepOver(self):
        """
        Public method to step over the debugged program.
        """
        return

    def remoteStepOut(self):
        """
        Public method to step out the debugged program.
        """
        return

    def remoteStepQuit(self):
        """
        Public method to stop the debugged program.
        """
        return

    def remoteContinue(self, special=False):
        """
        Public method to continue the debugged program.
        
        @param special flag indicating a special continue operation
        """
        return

    def remoteBreakpoint(self, fn, line, set, cond=None, temp=False):
        """
        Public method to set or clear a breakpoint.
        
        @param fn filename the breakpoint belongs to (string)
        @param line linenumber of the breakpoint (int)
        @param set flag indicating setting or resetting a breakpoint (boolean)
        @param cond condition of the breakpoint (string)
        @param temp flag indicating a temporary breakpoint (boolean)
        """
        return
        
    def remoteBreakpointEnable(self, fn, line, enable):
        """
        Public method to enable or disable a breakpoint.
        
        @param fn filename the breakpoint belongs to (string)
        @param line linenumber of the breakpoint (int)
        @param enable flag indicating enabling or disabling a breakpoint
            (boolean)
        """
        return
        
    def remoteBreakpointIgnore(self, fn, line, count):
        """
        Public method to ignore a breakpoint the next couple of occurrences.
        
        @param fn filename the breakpoint belongs to (string)
        @param line linenumber of the breakpoint (int)
        @param count number of occurrences to ignore (int)
        """
        return
        
    def remoteWatchpoint(self, cond, set, temp=False):
        """
        Public method to set or clear a watch expression.
        
        @param cond expression of the watch expression (string)
        @param set flag indicating setting or resetting a watch expression
            (boolean)
        @param temp flag indicating a temporary watch expression (boolean)
        """
        return
    
    def remoteWatchpointEnable(self, cond, enable):
        """
        Public method to enable or disable a watch expression.
        
        @param cond expression of the watch expression (string)
        @param enable flag indicating enabling or disabling a watch
            expression (boolean)
        """
        return
    
    def remoteWatchpointIgnore(self, cond, count):
        """
        Public method to ignore a watch expression the next couple of
        occurrences.
        
        @param cond expression of the watch expression (string)
        @param count number of occurrences to ignore (int)
        """
        return
    
    def remoteRawInput(self, s):
        """
        Public method to send the raw input to the debugged program.
        
        @param s the raw input (string)
        """
        return
        
    def remoteThreadList(self):
        """
        Public method to request the list of threads from the client.
        """
        return
        
    def remoteSetThread(self, tid):
        """
        Public method to request to set the given thread as current thread.
        
        @param tid id of the thread (integer)
        """
        return
        
    def remoteClientVariables(self, scope, filter, framenr=0):
        """
        Public method to request the variables of the debugged program.
        
        @param scope the scope of the variables (0 = local, 1 = global)
        @param filter list of variable types to filter out (list of int)
        @param framenr framenumber of the variables to retrieve (int)
        """
        return
        
    def remoteClientVariable(self, scope, filter, var, framenr=0):
        """
        Public method to request the variables of the debugged program.
        
        @param scope the scope of the variables (0 = local, 1 = global)
        @param filter list of variable types to filter out (list of int)
        @param var list encoded name of variable to retrieve (string)
        @param framenr framenumber of the variables to retrieve (int)
        """
        return
        
    def remoteClientSetFilter(self, scope, filter):
        """
        Public method to set a variables filter list.
        
        @param scope the scope of the variables (0 = local, 1 = global)
        @param filter regexp string for variable names to filter out (string)
        """
        return
        
    def setCallTraceEnabled(self, on):
        """
        Public method to set the call trace state.
        
        @param on flag indicating to enable the call trace function (boolean)
        """
        return
    
    def remoteEval(self, arg):
        """
        Public method to evaluate arg in the current context of the debugged
        program.
        
        @param arg the arguments to evaluate (string)
        """
        return
        
    def remoteExec(self, stmt):
        """
        Public method to execute stmt in the current context of the debugged
        program.
        
        @param stmt statement to execute (string)
        """
        return
        
    def remoteBanner(self):
        """
        Public slot to get the banner info of the remote client.
        """
        self.debugServer.signalClientBanner("No backend", "", "")
        return
        
    def remoteCapabilities(self):
        """
        Public slot to get the debug clients capabilities.
        """
        return
        
    def remoteCompletion(self, text):
        """
        Public slot to get the a list of possible commandline completions
        from the remote client.
        
        @param text the text to be completed (string)
        """
        return
        
    def remoteUTPrepare(self, fn, tn, tfn, failed, cov, covname, coverase):
        """
        Public method to prepare a new unittest run.
        
        @param fn the filename to load (string)
        @param tn the testname to load (string)
        @param tfn the test function name to load tests from (string)
        @param failed list of failed test, if only failed test should be run
            (list of strings)
        @param cov flag indicating collection of coverage data is requested
            (boolean)
        @param covname filename to be used to assemble the coverage caches
            filename (string)
        @param coverase flag indicating erasure of coverage data is requested
            (boolean)
        """
        return
        
    def remoteUTRun(self):
        """
        Public method to start a unittest run.
        """
        return
        
    def remoteUTStop(self):
        """
        public method to stop a unittest run.
        """
        return
