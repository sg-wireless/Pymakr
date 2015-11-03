# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Ruby debugger interface for the debug server.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QObject, QTextCodec, QProcess, QProcessEnvironment, \
    QTimer

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox

from . import DebugProtocol
from . import DebugClientCapabilities

import Preferences
import Utilities

from eric6config import getConfig


ClientDefaultCapabilities = \
    DebugClientCapabilities.HasDebugger | \
    DebugClientCapabilities.HasShell | \
    DebugClientCapabilities.HasInterpreter | \
    DebugClientCapabilities.HasCompleter
    
ClientTypeAssociations = [".rb"]


def getRegistryData():
    """
    Module function to get characterising data for the debugger interface.
    
    @return list of the following data. Client type (string), client
        capabilities (integer), client type association (list of strings)
    """
    if Preferences.getDebugger("RubyInterpreter"):
        return ["Ruby", ClientDefaultCapabilities, ClientTypeAssociations]
    else:
        return ["", 0, []]


class DebuggerInterfaceRuby(QObject):
    """
    Class implementing the Ruby debugger interface for the debug server.
    """
    def __init__(self, debugServer, passive):
        """
        Constructor
        
        @param debugServer reference to the debug server (DebugServer)
        @param passive flag indicating passive connection mode (boolean)
        """
        super(DebuggerInterfaceRuby, self).__init__()
        
        self.__isNetworked = True
        self.__autoContinue = not passive
        
        self.debugServer = debugServer
        self.passive = passive
        self.process = None
        
        self.qsock = None
        self.queue = []
        
        # set default values for capabilities of clients
        self.clientCapabilities = ClientDefaultCapabilities
        
        # set translation function
        self.translate = self.__identityTranslation
        
        self.codec = QTextCodec.codecForName(
            str(Preferences.getSystem("StringEncoding")))
        
        if passive:
            # set translation function
            if Preferences.getDebugger("PathTranslation"):
                self.translateRemote = \
                    Preferences.getDebugger("PathTranslationRemote")
                self.translateLocal = \
                    Preferences.getDebugger("PathTranslationLocal")
                self.translate = self.__remoteTranslation
            else:
                self.translate = self.__identityTranslation

    def __identityTranslation(self, fn, remote2local=True):
        """
        Private method to perform the identity path translation.
        
        @param fn filename to be translated (string)
        @param remote2local flag indicating the direction of translation
            (False = local to remote, True = remote to local [default])
        @return translated filename (string)
        """
        return fn
        
    def __remoteTranslation(self, fn, remote2local=True):
        """
        Private method to perform the path translation.
        
        @param fn filename to be translated (string)
        @param remote2local flag indicating the direction of translation
            (False = local to remote, True = remote to local [default])
        @return translated filename (string)
        """
        if remote2local:
            return fn.replace(self.translateRemote, self.translateLocal)
        else:
            return fn.replace(self.translateLocal, self.translateRemote)
        
    def __startProcess(self, program, arguments, environment=None):
        """
        Private method to start the debugger client process.
        
        @param program name of the executable to start (string)
        @param arguments arguments to be passed to the program (list of string)
        @param environment dictionary of environment settings to pass
            (dict of string)
        @return the process object (QProcess) or None
        """
        proc = QProcess()
        if environment is not None:
            env = QProcessEnvironment()
            for key, value in list(environment.items()):
                env.insert(key, value)
            proc.setProcessEnvironment(env)
        args = []
        for arg in arguments:
            args.append(arg)
        proc.start(program, args)
        if not proc.waitForStarted(10000):
            proc = None
        
        return proc
        
    def startRemote(self, port, runInConsole):
        """
        Public method to start a remote Ruby interpreter.
        
        @param port portnumber the debug server is listening on (integer)
        @param runInConsole flag indicating to start the debugger in a
            console window (boolean)
        @return client process object (QProcess), a flag to indicate
            a network connection (boolean) and the name of the interpreter
            in case of a local execution (string)
        """
        interpreter = Preferences.getDebugger("RubyInterpreter")
        if interpreter == "":
            E5MessageBox.critical(
                None,
                self.tr("Start Debugger"),
                self.tr("""<p>No Ruby interpreter configured.</p>"""))
            return None, False, ""
        
        debugClient = os.path.join(
            getConfig('ericDir'), "DebugClients", "Ruby", "DebugClient.rb")
        
        redirect = str(Preferences.getDebugger("RubyRedirect"))
        
        if Preferences.getDebugger("RemoteDbgEnabled"):
            ipaddr = self.debugServer.getHostAddress(False)[0]
            rexec = Preferences.getDebugger("RemoteExecution")
            rhost = Preferences.getDebugger("RemoteHost")
            if rhost == "":
                rhost = "localhost"
            if rexec:
                args = Utilities.parseOptionString(rexec) + \
                    [rhost, interpreter, os.path.abspath(debugClient),
                        str(port), redirect, ipaddr]
                args[0] = Utilities.getExecutablePath(args[0])
                process = self.__startProcess(args[0], args[1:])
                if process is None:
                    E5MessageBox.critical(
                        None,
                        self.tr("Start Debugger"),
                        self.tr(
                            """<p>The debugger backend could not be"""
                            """ started.</p>"""))
                
                # set translation function
                if Preferences.getDebugger("PathTranslation"):
                    self.translateRemote = \
                        Preferences.getDebugger("PathTranslationRemote")
                    self.translateLocal = \
                        Preferences.getDebugger("PathTranslationLocal")
                    self.translate = self.__remoteTranslation
                else:
                    self.translate = self.__identityTranslation
                return process, self.__isNetworked, ""
        
        # set translation function
        self.translate = self.__identityTranslation
        
        # setup the environment for the debugger
        if Preferences.getDebugger("DebugEnvironmentReplace"):
            clientEnv = {}
        else:
            clientEnv = os.environ.copy()
        envlist = Utilities.parseEnvironmentString(
            Preferences.getDebugger("DebugEnvironment"))
        for el in envlist:
            try:
                key, value = el.split('=', 1)
                if value.startswith('"') or value.startswith("'"):
                    value = value[1:-1]
                clientEnv[str(key)] = str(value)
            except ValueError:
                pass
        
        ipaddr = self.debugServer.getHostAddress(True)
        if runInConsole or Preferences.getDebugger("ConsoleDbgEnabled"):
            ccmd = Preferences.getDebugger("ConsoleDbgCommand")
            if ccmd:
                args = Utilities.parseOptionString(ccmd) + \
                    [interpreter, os.path.abspath(debugClient),
                        str(port), '0', ipaddr]
                args[0] = Utilities.getExecutablePath(args[0])
                process = self.__startProcess(args[0], args[1:], clientEnv)
                if process is None:
                    E5MessageBox.critical(
                        None,
                        self.tr("Start Debugger"),
                        self.tr(
                            """<p>The debugger backend could not be"""
                            """ started.</p>"""))
                return process, self.__isNetworked, interpreter
        
        process = self.__startProcess(
            interpreter,
            [debugClient, str(port), redirect, ipaddr],
            clientEnv)
        if process is None:
            E5MessageBox.critical(
                None,
                self.tr("Start Debugger"),
                self.tr(
                    """<p>The debugger backend could not be started.</p>"""))
        return process, self.__isNetworked, interpreter

    def startRemoteForProject(self, port, runInConsole):
        """
        Public method to start a remote Ruby interpreter for a project.
        
        @param port portnumber the debug server is listening on (integer)
        @param runInConsole flag indicating to start the debugger in a
            console window (boolean)
        @return client process object (QProcess), a flag to indicate
            a network connection (boolean) and the name of the interpreter
            in case of a local execution (string)
        """
        project = e5App().getObject("Project")
        if not project.isDebugPropertiesLoaded():
            return None, self.__isNetworked, ""
        
        # start debugger with project specific settings
        interpreter = project.getDebugProperty("INTERPRETER")
        debugClient = project.getDebugProperty("DEBUGCLIENT")
        
        redirect = str(project.getDebugProperty("REDIRECT"))
        
        if project.getDebugProperty("REMOTEDEBUGGER"):
            ipaddr = self.debugServer.getHostAddress(False)[0]
            rexec = project.getDebugProperty("REMOTECOMMAND")
            rhost = project.getDebugProperty("REMOTEHOST")
            if rhost == "":
                rhost = "localhost"
            if rexec:
                args = Utilities.parseOptionString(rexec) + \
                    [rhost, interpreter, os.path.abspath(debugClient),
                        str(port), redirect, ipaddr]
                args[0] = Utilities.getExecutablePath(args[0])
                process = self.__startProcess(args[0], args[1:])
                if process is None:
                    E5MessageBox.critical(
                        None,
                        self.tr("Start Debugger"),
                        self.tr(
                            """<p>The debugger backend could not be"""
                            """ started.</p>"""))
                # set translation function
                if project.getDebugProperty("PATHTRANSLATION"):
                    self.translateRemote = \
                        project.getDebugProperty("REMOTEPATH")
                    self.translateLocal = \
                        project.getDebugProperty("LOCALPATH")
                    self.translate = self.__remoteTranslation
                else:
                    self.translate = self.__identityTranslation
                return process, self.__isNetworked, ""
        
        # set translation function
        self.translate = self.__identityTranslation
        
        # setup the environment for the debugger
        if project.getDebugProperty("ENVIRONMENTOVERRIDE"):
            clientEnv = {}
        else:
            clientEnv = os.environ.copy()
        envlist = Utilities.parseEnvironmentString(
            project.getDebugProperty("ENVIRONMENTSTRING"))
        for el in envlist:
            try:
                key, value = el.split('=', 1)
                if value.startswith('"') or value.startswith("'"):
                    value = value[1:-1]
                clientEnv[str(key)] = str(value)
            except ValueError:
                pass
        
        ipaddr = self.debugServer.getHostAddress(True)
        if runInConsole or project.getDebugProperty("CONSOLEDEBUGGER"):
            ccmd = project.getDebugProperty("CONSOLECOMMAND") or \
                Preferences.getDebugger("ConsoleDbgCommand")
            if ccmd:
                args = Utilities.parseOptionString(ccmd) + \
                    [interpreter, os.path.abspath(debugClient),
                        str(port), '0', ipaddr]
                args[0] = Utilities.getExecutablePath(args[0])
                process = self.__startProcess(args[0], args[1:], clientEnv)
                if process is None:
                    E5MessageBox.critical(
                        None,
                        self.tr("Start Debugger"),
                        self.tr(
                            """<p>The debugger backend could not be"""
                            """ started.</p>"""))
                return process, self.__isNetworked, interpreter
        
        process = self.__startProcess(
            interpreter,
            [debugClient, str(port), redirect, ipaddr],
            clientEnv)
        if process is None:
            E5MessageBox.critical(
                None,
                self.tr("Start Debugger"),
                self.tr(
                    """<p>The debugger backend could not be started.</p>"""))
        return process, self.__isNetworked, interpreter

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
        # If we already have a connection, refuse this one.  It will be closed
        # automatically.
        if self.qsock is not None:
            return False
        
        sock.disconnected.connect(self.debugServer.startClient)
        sock.readyRead.connect(self.__parseClientLine)
        
        self.qsock = sock
        
        # Get the remote clients capabilities
        self.remoteCapabilities()
        return True
        
    def flush(self):
        """
        Public slot to flush the queue.
        """
        # Send commands that were waiting for the connection.
        for cmd in self.queue:
            self.qsock.write(cmd.encode('utf8'))
        
        self.queue = []
        
    def shutdown(self):
        """
        Public method to cleanly shut down.
        
        It closes our socket and shuts down
        the debug client. (Needed on Win OS)
        """
        if self.qsock is None:
            return
        
        # do not want any slots called during shutdown
        self.qsock.disconnected.disconnect(self.debugServer.startClient)
        self.qsock.readyRead.disconnect(self.__parseClientLine)
        
        # close down socket, and shut down client as well.
        self.__sendCommand('{0}\n'.format(DebugProtocol.RequestShutdown))
        self.qsock.flush()
        
        self.qsock.close()
        
        # reinitialize
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
        self.__sendCommand('{0}{1}\n'.format(
            DebugProtocol.RequestEnv, str(env)))
        
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
            (ignored)
        @keyparam forkChild flag indicating to debug the child after forking
            (boolean) (ignored)
        """
        self.__autoContinue = autoContinue
        
        wd = self.translate(wd, False)
        fn = self.translate(os.path.abspath(fn), False)
        self.__sendCommand('{0}{1}|{2}|{3}|{4:d}\n'.format(
            DebugProtocol.RequestLoad, wd, fn,
            str(Utilities.parseOptionString(argv)),
            traceInterpreter))
        
    def remoteRun(self, fn, argv, wd, autoFork=False, forkChild=False):
        """
        Public method to load a new program to run.
        
        @param fn the filename to run (string)
        @param argv the commandline arguments to pass to the program (string)
        @param wd the working directory for the program (string)
        @keyparam autoFork flag indicating the automatic fork mode (boolean)
            (ignored)
        @keyparam forkChild flag indicating to debug the child after forking
            (boolean) (ignored)
        """
        wd = self.translate(wd, False)
        fn = self.translate(os.path.abspath(fn), False)
        self.__sendCommand('{0}{1}|{2}|{3}\n'.format(
            DebugProtocol.RequestRun, wd, fn,
            str(Utilities.parseOptionString(argv))))
        
    def remoteCoverage(self, fn, argv, wd, erase=False):
        """
        Public method to load a new program to collect coverage data.
        
        @param fn the filename to run (string)
        @param argv the commandline arguments to pass to the program (string)
        @param wd the working directory for the program (string)
        @keyparam erase flag indicating that coverage info should be
            cleared first (boolean)
        @exception NotImplementedError raised to indicate that this interface
            is not supported
        """
        raise NotImplementedError("Interface not available.")

    def remoteProfile(self, fn, argv, wd, erase=False):
        """
        Public method to load a new program to collect profiling data.
        
        @param fn the filename to run (string)
        @param argv the commandline arguments to pass to the program (string)
        @param wd the working directory for the program (string)
        @keyparam erase flag indicating that timing info should be cleared
            first (boolean)
        @exception NotImplementedError raised to indicate that this interface
            is not supported
        """
        raise NotImplementedError("Interface not available.")

    def remoteStatement(self, stmt):
        """
        Public method to execute a Ruby statement.
        
        @param stmt the Ruby statement to execute (string). It
              should not have a trailing newline.
        """
        self.__sendCommand('{0}\n'.format(stmt))
        self.__sendCommand(DebugProtocol.RequestOK + '\n')

    def remoteStep(self):
        """
        Public method to single step the debugged program.
        """
        self.__sendCommand(DebugProtocol.RequestStep + '\n')

    def remoteStepOver(self):
        """
        Public method to step over the debugged program.
        """
        self.__sendCommand(DebugProtocol.RequestStepOver + '\n')

    def remoteStepOut(self):
        """
        Public method to step out the debugged program.
        """
        self.__sendCommand(DebugProtocol.RequestStepOut + '\n')

    def remoteStepQuit(self):
        """
        Public method to stop the debugged program.
        """
        self.__sendCommand(DebugProtocol.RequestStepQuit + '\n')

    def remoteContinue(self, special=False):
        """
        Public method to continue the debugged program.
        
        @param special flag indicating a special continue operation (boolean)
        """
        self.__sendCommand('{0}{1:d}\n'.format(
            DebugProtocol.RequestContinue, special))

    def remoteBreakpoint(self, fn, line, set, cond=None, temp=False):
        """
        Public method to set or clear a breakpoint.
        
        @param fn filename the breakpoint belongs to (string)
        @param line linenumber of the breakpoint (int)
        @param set flag indicating setting or resetting a breakpoint (boolean)
        @param cond condition of the breakpoint (string)
        @param temp flag indicating a temporary breakpoint (boolean)
        """
        fn = self.translate(fn, False)
        self.__sendCommand('{0}{1}@@{2:d}@@{3:d}@@{4:d}@@{5}\n'.format(
            DebugProtocol.RequestBreak, fn, line, temp, set, cond))
        
    def remoteBreakpointEnable(self, fn, line, enable):
        """
        Public method to enable or disable a breakpoint.
        
        @param fn filename the breakpoint belongs to (string)
        @param line linenumber of the breakpoint (int)
        @param enable flag indicating enabling or disabling a breakpoint
            (boolean)
        """
        fn = self.translate(fn, False)
        self.__sendCommand('{0}{1},{2:d},{3:d}\n'.format(
            DebugProtocol.RequestBreakEnable, fn, line, enable))
        
    def remoteBreakpointIgnore(self, fn, line, count):
        """
        Public method to ignore a breakpoint the next couple of occurrences.
        
        @param fn filename the breakpoint belongs to (string)
        @param line linenumber of the breakpoint (int)
        @param count number of occurrences to ignore (int)
        """
        fn = self.translate(fn, False)
        self.__sendCommand('{0}{1},{2:d},{3:d}\n'.format(
            DebugProtocol.RequestBreakIgnore, fn, line, count))
        
    def remoteWatchpoint(self, cond, set, temp=False):
        """
        Public method to set or clear a watch expression.
        
        @param cond expression of the watch expression (string)
        @param set flag indicating setting or resetting a watch expression
            (boolean)
        @param temp flag indicating a temporary watch expression (boolean)
        """
        # cond is combination of cond and special (s. watch expression viewer)
        self.__sendCommand('{0}{1}@@{2:d}@@{3:d}\n'.format(
            DebugProtocol.RequestWatch, cond, temp, set))
    
    def remoteWatchpointEnable(self, cond, enable):
        """
        Public method to enable or disable a watch expression.
        
        @param cond expression of the watch expression (string)
        @param enable flag indicating enabling or disabling a watch expression
            (boolean)
        """
        # cond is combination of cond and special (s. watch expression viewer)
        self.__sendCommand('{0}{1},{2:d}\n'.format(
            DebugProtocol.RequestWatchEnable, cond, enable))
    
    def remoteWatchpointIgnore(self, cond, count):
        """
        Public method to ignore a watch expression the next couple of
        occurrences.
        
        @param cond expression of the watch expression (string)
        @param count number of occurrences to ignore (int)
        """
        # cond is combination of cond and special (s. watch expression viewer)
        self.__sendCommand('{0}{1},{2:d}\n'.format(
            DebugProtocol.RequestWatchIgnore, cond, count))
    
    def remoteRawInput(self, s):
        """
        Public method to send the raw input to the debugged program.
        
        @param s the raw input (string)
        """
        self.__sendCommand(s + '\n')
        
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
        self.__sendCommand('{0}{1:d}, {2:d}, {3}\n'.format(
            DebugProtocol.RequestVariables, framenr, scope, str(filter)))
        
    def remoteClientVariable(self, scope, filter, var, framenr=0):
        """
        Public method to request the variables of the debugged program.
        
        @param scope the scope of the variables (0 = local, 1 = global)
        @param filter list of variable types to filter out (list of int)
        @param var list encoded name of variable to retrieve (string)
        @param framenr framenumber of the variables to retrieve (int)
        """
        self.__sendCommand('{0}{1}, {2:d}, {3:d}, {4}\n'.format(
            DebugProtocol.RequestVariable, str(var), framenr, scope,
            str(filter)))
        
    def remoteClientSetFilter(self, scope, filter):
        """
        Public method to set a variables filter list.
        
        @param scope the scope of the variables (0 = local, 1 = global)
        @param filter regexp string for variable names to filter out (string)
        """
        self.__sendCommand('{0}{1:d}, "{2}"\n'.format(
            DebugProtocol.RequestSetFilter, scope, filter))
        
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
        self.__sendCommand('{0}{1}\n'.format(DebugProtocol.RequestEval, arg))
        
    def remoteExec(self, stmt):
        """
        Public method to execute stmt in the current context of the debugged
        program.
        
        @param stmt statement to execute (string)
        """
        self.__sendCommand('{0}{1}\n'.format(DebugProtocol.RequestExec, stmt))
        
    def remoteBanner(self):
        """
        Public slot to get the banner info of the remote client.
        """
        self.__sendCommand(DebugProtocol.RequestBanner + '\n')
        
    def remoteCapabilities(self):
        """
        Public slot to get the debug clients capabilities.
        """
        self.__sendCommand(DebugProtocol.RequestCapabilities + '\n')
        
    def remoteCompletion(self, text):
        """
        Public slot to get the a list of possible commandline completions
        from the remote client.
        
        @param text the text to be completed (string)
        """
        self.__sendCommand("{0}{1}\n".format(
            DebugProtocol.RequestCompletion, text))
        
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
        @exception NotImplementedError raised to indicate that this interface
            is not supported
        """
        raise NotImplementedError("Interface not available.")
        
    def remoteUTRun(self):
        """
        Public method to start a unittest run.
        
        @exception NotImplementedError raised to indicate that this interface
            is not supported
        """
        raise NotImplementedError("Interface not available.")
        
    def remoteUTStop(self):
        """
        Public method to stop a unittest run.
        
        @exception NotImplementedError raised to indicate that this interface
            is not supported
        """
        raise NotImplementedError("Interface not available.")
        
    def __parseClientLine(self):
        """
        Private method to handle data from the client.
        """
        while self.qsock and self.qsock.canReadLine():
            qs = self.qsock.readLine()
            if self.codec is not None:
                line = self.codec.toUnicode(qs)
            else:
                line = bytes(qs).decode()
            if line.endswith(DebugProtocol.EOT):
                line = line[:-len(DebugProtocol.EOT)]
                if not line:
                    continue
            
##            print("Server: ", line)          ##debug
            
            eoc = line.find('<') + 1
            
            # Deal with case where user has written directly to stdout
            # or stderr, but not line terminated and we stepped over the
            # write call, in that case the >line< will not be the first
            # string read from the socket...
            boc = line.find('>')
            if boc > 0 and eoc > boc:
                self.debugServer.signalClientOutput(line[:boc])
                line = line[boc:]
                eoc = line.find('<') + 1
                boc = line.find('>')
            
            if boc >= 0 and eoc > boc:
                resp = line[boc:eoc]
                
                if resp == DebugProtocol.ResponseLine:
                    stack = eval(line[eoc:-1])
                    for s in stack:
                        s[0] = self.translate(s[0], True)
                    cf = stack[0]
                    if self.__autoContinue:
                        self.__autoContinue = False
                        QTimer.singleShot(0, self.remoteContinue)
                    else:
                        self.debugServer.signalClientLine(cf[0], int(cf[1]))
                        self.debugServer.signalClientStack(stack)
                    continue
                
                if resp == DebugProtocol.ResponseVariables:
                    vlist = eval(line[eoc:-1])
                    scope = vlist[0]
                    try:
                        variables = vlist[1:]
                    except IndexError:
                        variables = []
                    self.debugServer.signalClientVariables(scope, variables)
                    continue
                
                if resp == DebugProtocol.ResponseVariable:
                    vlist = eval(line[eoc:-1])
                    scope = vlist[0]
                    try:
                        variables = vlist[1:]
                    except IndexError:
                        variables = []
                    self.debugServer.signalClientVariable(scope, variables)
                    continue
                
                if resp == DebugProtocol.ResponseOK:
                    self.debugServer.signalClientStatement(False)
                    continue
                
                if resp == DebugProtocol.ResponseContinue:
                    self.debugServer.signalClientStatement(True)
                    continue
                
                if resp == DebugProtocol.ResponseException:
                    exc = line[eoc:-1]
                    exc = self.translate(exc, True)
                    try:
                        exclist = eval(exc)
                        exctype = exclist[0]
                        excmessage = exclist[1]
                        stack = exclist[2:]
                    except (IndexError, ValueError, SyntaxError):
                        exctype = None
                        excmessage = ''
                        stack = []
                    self.debugServer.signalClientException(
                        exctype, excmessage, stack)
                    continue
                
                if resp == DebugProtocol.ResponseSyntax:
                    exc = line[eoc:-1]
                    exc = self.translate(exc, True)
                    try:
                        message, (fn, ln, cn) = eval(exc)
                        if fn is None:
                            fn = ''
                    except (IndexError, ValueError):
                        message = None
                        fn = ''
                        ln = 0
                        cn = 0
                    self.debugServer.signalClientSyntaxError(
                        message, fn, ln, cn)
                    continue
                
                if resp == DebugProtocol.ResponseExit:
                    self.debugServer.signalClientExit(line[eoc:-1])
                    continue
                
                if resp == DebugProtocol.ResponseClearBreak:
                    fn, lineno = line[eoc:-1].split(',')
                    lineno = int(lineno)
                    fn = self.translate(fn, True)
                    self.debugServer.signalClientClearBreak(fn, lineno)
                    continue
                
                if resp == DebugProtocol.ResponseClearWatch:
                    cond = line[eoc:-1]
                    self.debugServer.signalClientClearWatch(cond)
                    continue
                
                if resp == DebugProtocol.ResponseBanner:
                    version, platform, dbgclient = eval(line[eoc:-1])
                    self.debugServer.signalClientBanner(
                        version, platform, dbgclient)
                    continue
                
                if resp == DebugProtocol.ResponseCapabilities:
                    cap, clType = eval(line[eoc:-1])
                    self.clientCapabilities = cap
                    self.debugServer.signalClientCapabilities(cap, clType)
                    continue
                
                if resp == DebugProtocol.ResponseCompletion:
                    clstring, text = line[eoc:-1].split('||')
                    cl = eval(clstring)
                    self.debugServer.signalClientCompletionList(cl, text)
                    continue
                
                if resp == DebugProtocol.PassiveStartup:
                    fn, exc = line[eoc:-1].split('|')
                    exc = bool(exc)
                    fn = self.translate(fn, True)
                    self.debugServer.passiveStartUp(fn, exc)
                    continue
            
            self.debugServer.signalClientOutput(line)

    def __sendCommand(self, cmd):
        """
        Private method to send a single line command to the client.
        
        @param cmd command to send to the debug client (string)
        """
        if self.qsock is not None:
            self.qsock.write(cmd.encode('utf8'))
        else:
            self.queue.append(cmd)
