# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the debug server.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os

from PyQt5.QtCore import pyqtSignal, QModelIndex
from PyQt5.QtNetwork import QTcpServer, QHostAddress, QHostInfo, \
    QNetworkInterface

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox

from .BreakPointModel import BreakPointModel
from .WatchPointModel import WatchPointModel
from . import DebugClientCapabilities

import Preferences
import Utilities


DebuggerInterfaces = [
    "DebuggerInterfacePython",
    "DebuggerInterfacePython3",
    ##    "DebuggerInterfaceRuby",
    "DebuggerInterfaceNone",
]


class DebugServer(QTcpServer):
    """
    Class implementing the debug server embedded within the IDE.
    
    @signal clientProcessStdout(str) emitted after the client has sent some
        output via stdout
    @signal clientProcessStderr(str) emitted after the client has sent some
        output via stderr
    @signal clientOutput(str) emitted after the client has sent some output
    @signal clientRawInputSent() emitted after the data was sent to the
        debug client
    @signal clientLine(filename, lineno, forStack) emitted after the
        debug client has executed a line of code
    @signal clientStack(stack) emitted after the debug client has executed a
        line of code
    @signal clientThreadList(currentId, threadList) emitted after a thread list
        has been received
    @signal clientThreadSet() emitted after the client has acknowledged the
        change of the current thread
    @signal clientVariables(scope, variables) emitted after a variables dump
        has been received
    @signal clientVariable(scope, variables) emitted after a dump for one class
        variable has been received
    @signal clientStatement(bool) emitted after an interactive command has
        been executed. The parameter is 0 to indicate that the command is
        complete and 1 if it needs more input.
    @signal clientException(exception) emitted after an exception occured on
        the client side
    @signal clientSyntaxError(exception) emitted after a syntax error has been
        detected on the client side
    @signal clientSignal(signal) emitted after a signal has been generated on
        the client side
    @signal clientExit(int) emitted with the exit status after the client has
        exited
    @signal clientClearBreak(filename, lineno) emitted after the debug client
        has decided to clear a temporary breakpoint
    @signal clientBreakConditionError(fn, lineno) emitted after the client has
        signaled a syntax error in a breakpoint condition
    @signal clientClearWatch(condition) emitted after the debug client
            has decided to clear a temporary watch expression
    @signal clientWatchConditionError(condition) emitted after the client has
        signaled a syntax error in a watch expression
    @signal clientRawInput(prompt, echo) emitted after a raw input request was
        received
    @signal clientBanner(banner) emitted after the client banner was received
    @signal clientCapabilities(int capabilities, string cltype) emitted after
        the clients capabilities were received
    @signal clientCompletionList(completionList, text) emitted after the client
        the commandline completion list and the reworked searchstring was
        received from the client
    @signal passiveDebugStarted(str, bool) emitted after the debug client has
        connected in passive debug mode
    @signal clientGone(bool) emitted if the client went away (planned or
        unplanned)
    @signal clientInterpreterChanged(str) emitted to signal a change of the
        client interpreter
    @signal utPrepared(nrTests, exc_type, exc_value) emitted after the client
        has loaded a unittest suite
    @signal utFinished() emitted after the client signalled the end of the
        unittest
    @signal utStartTest(testname, testdocu) emitted after the client has
        started a test
    @signal utStopTest() emitted after the client has finished a test
    @signal utTestFailed(testname, exc_info, id) emitted after the client
        reported a failed test
    @signal utTestErrored(testname, exc_info, id) emitted after the client
        reported an errored test
    @signal utTestSkipped(testname, reason, id) emitted after the client
        reported a skipped test
    @signal utTestFailedExpected(testname, exc_info, id) emitted after the
        client reported an expected test failure
    @signal utTestSucceededUnexpected(testname, id) emitted after the client
        reported an unexpected test success
    @signal callTraceInfo emitted after the client reported the call trace
        data (isCall, fromFile, fromLine, fromFunction, toFile, toLine,
        toFunction)
    @signal appendStdout(msg) emitted when a passive debug connection is
        established or lost
    """
    clientClearBreak = pyqtSignal(str, int)
    clientClearWatch = pyqtSignal(str)
    clientGone = pyqtSignal(bool)
    clientProcessStdout = pyqtSignal(str)
    clientProcessStderr = pyqtSignal(str)
    clientRawInputSent = pyqtSignal()
    clientOutput = pyqtSignal(str)
    clientLine = pyqtSignal(str, int, bool)
    clientStack = pyqtSignal(list)
    clientThreadList = pyqtSignal(int, list)
    clientThreadSet = pyqtSignal()
    clientVariables = pyqtSignal(int, list)
    clientVariable = pyqtSignal(int, list)
    clientStatement = pyqtSignal(bool)
    clientException = pyqtSignal(str, str, list)
    clientSyntaxError = pyqtSignal(str, str, int, int)
    clientSignal = pyqtSignal(str, str, int, str, str)
    clientExit = pyqtSignal(int)
    clientBreakConditionError = pyqtSignal(str, int)
    clientWatchConditionError = pyqtSignal(str)
    clientRawInput = pyqtSignal(str, bool)
    clientBanner = pyqtSignal(str, str, str)
    clientCapabilities = pyqtSignal(int, str)
    clientCompletionList = pyqtSignal(list, str)
    clientInterpreterChanged = pyqtSignal(str)
    utPrepared = pyqtSignal(int, str, str)
    utStartTest = pyqtSignal(str, str)
    utStopTest = pyqtSignal()
    utTestFailed = pyqtSignal(str, str, str)
    utTestErrored = pyqtSignal(str, str, str)
    utTestSkipped = pyqtSignal(str, str, str)
    utTestFailedExpected = pyqtSignal(str, str, str)
    utTestSucceededUnexpected = pyqtSignal(str, str)
    utFinished = pyqtSignal()
    passiveDebugStarted = pyqtSignal(str, bool)
    callTraceInfo = pyqtSignal(bool, str, str, str, str, str, str)
    appendStdout = pyqtSignal(str)
    
    def __init__(self):
        """
        Constructor
        """
        super(DebugServer, self).__init__()
        
        # create our models
        self.breakpointModel = BreakPointModel(self)
        self.watchpointModel = WatchPointModel(self)
        self.watchSpecialCreated = \
            self.tr("created", "must be same as in EditWatchpointDialog")
        self.watchSpecialChanged = \
            self.tr("changed", "must be same as in EditWatchpointDialog")
        
        self.networkInterface = Preferences.getDebugger("NetworkInterface")
        if self.networkInterface == "all":
            hostAddress = QHostAddress("0.0.0.0")  # QHostAddress.Any)
        elif self.networkInterface == "allv6":
            hostAddress = QHostAddress("::")  # QHostAddress.AnyIPv6)
        else:
            hostAddress = QHostAddress(self.networkInterface)
        self.networkInterfaceName, self.networkInterfaceIndex = \
            self.__getNetworkInterfaceAndIndex(self.networkInterface)
        
        if Preferences.getDebugger("PassiveDbgEnabled"):
            sock = Preferences.getDebugger("PassiveDbgPort")  # default: 42424
            self.listen(hostAddress, sock)
            self.passive = True
            self.passiveClientExited = False
        else:
            if hostAddress.toString().lower().startswith("fe80"):
                hostAddress.setScopeId(self.networkInterfaceName)
            self.listen(hostAddress)
            self.passive = False
        
        self.debuggerInterface = None
        self.debugging = False
        self.running = False
        self.clientProcess = None
        self.clientInterpreter = ""
        self.clientType = \
            Preferences.Prefs.settings.value('DebugClient/Type')
        if self.clientType is None:
            import sys
            if sys.version_info[0] == 2:
                self.clientType = 'Python2'
            else:
                self.clientType = 'Python3'
        # Change clientType if dependent interpreter not exist anymore
        # (maybe deinstalled,...)
        elif self.clientType == 'Python2' and Preferences.getDebugger(
                "PythonInterpreter") == '':
            self.clientType = 'Python3'
        elif self.clientType == 'Python3' and Preferences.getDebugger(
                "Python3Interpreter") == '':
            self.clientType = 'Python2'
        
        self.lastClientType = ''
        self.__autoClearShell = False
        
        self.clientClearBreak.connect(self.__clientClearBreakPoint)
        self.clientClearWatch.connect(self.__clientClearWatchPoint)
        self.newConnection.connect(self.__newConnection)
        
        self.breakpointModel.rowsAboutToBeRemoved.connect(
            self.__deleteBreakPoints)
        self.breakpointModel.dataAboutToBeChanged.connect(
            self.__breakPointDataAboutToBeChanged)
        self.breakpointModel.dataChanged.connect(self.__changeBreakPoints)
        self.breakpointModel.rowsInserted.connect(self.__addBreakPoints)
        
        self.watchpointModel.rowsAboutToBeRemoved.connect(
            self.__deleteWatchPoints)
        self.watchpointModel.dataAboutToBeChanged.connect(
            self.__watchPointDataAboutToBeChanged)
        self.watchpointModel.dataChanged.connect(self.__changeWatchPoints)
        self.watchpointModel.rowsInserted.connect(self.__addWatchPoints)
        
        self.__registerDebuggerInterfaces()
        
    def getHostAddress(self, localhost):
        """
        Public method to get the IP address or hostname the debug server is
        listening.
        
        @param localhost flag indicating to return the address for localhost
            (boolean)
        @return IP address or hostname (string)
        """
        if self.networkInterface == "all":
            if localhost:
                return "127.0.0.1"
            else:
                return "{0}@@v4".format(QHostInfo.localHostName())
        elif self.networkInterface == "allv6":
            if localhost:
                return "::1"
            else:
                return "{0}@@v6".format(QHostInfo.localHostName())
        else:
            return "{0}@@i{1}".format(self.networkInterface,
                                      self.networkInterfaceIndex)
        
    def __getNetworkInterfaceAndIndex(self, address):
        """
        Private method to determine the network interface and the interface
        index.
        
        @param address address to determine the info for (string)
        @return tuple of network interface name (string) and index (integer)
        """
        if address not in ["all", "allv6"]:
            for networkInterface in QNetworkInterface.allInterfaces():
                addressEntries = networkInterface.addressEntries()
                if len(addressEntries) > 0:
                    for addressEntry in addressEntries:
                        if addressEntry.ip().toString().lower() == \
                                address.lower():
                            return networkInterface.humanReadableName(), \
                                networkInterface.index()
        
        return "", 0
        
    def preferencesChanged(self):
        """
        Public slot to handle the preferencesChanged signal.
        """
        self.__registerDebuggerInterfaces()
        
    def __registerDebuggerInterfaces(self):
        """
        Private method to register the available debugger interface modules.
        """
        self.__clientCapabilities = {}
        self.__clientAssociations = {}
        
        for interface in DebuggerInterfaces:
            modName = "Debugger.{0}".format(interface)
            mod = __import__(modName)
            components = modName.split('.')
            for comp in components[1:]:
                mod = getattr(mod, comp)
            
            clientLanguage, clientCapabilities, clientExtensions = \
                mod.getRegistryData()
            if clientLanguage:
                self.__clientCapabilities[clientLanguage] = clientCapabilities
                for extension in clientExtensions:
                    if extension not in self.__clientAssociations:
                        self.__clientAssociations[extension] = clientLanguage
        
    def getSupportedLanguages(self, shellOnly=False):
        """
        Public slot to return the supported programming languages.
        
        @param shellOnly flag indicating only languages supporting an
            interactive shell should be returned
        @return list of supported languages (list of strings)
        """
        languages = list(self.__clientCapabilities.keys())
        try:
            languages.remove("None")
        except ValueError:
            pass    # it is not in the list
        
        if shellOnly:
            languages = \
                [lang for lang in languages
                 if self.__clientCapabilities[lang] &
                    DebugClientCapabilities.HasShell]
        
        return languages[:]
        
    def getExtensions(self, language):
        """
        Public slot to get the extensions associated with the given language.
        
        @param language language to get extensions for (string)
        @return tuple of extensions associated with the language
            (tuple of strings)
        """
        extensions = []
        for ext, lang in list(self.__clientAssociations.items()):
            if lang == language:
                extensions.append(ext)
        
        return tuple(extensions)
        
    def __createDebuggerInterface(self, clientType=None):
        """
        Private slot to create the debugger interface object.
        
        @param clientType type of the client interface to be created (string)
        """
        if self.lastClientType != self.clientType or clientType is not None:
            if clientType is None:
                clientType = self.clientType
            if clientType == "Python2":
                from .DebuggerInterfacePython import DebuggerInterfacePython
                self.debuggerInterface = DebuggerInterfacePython(
                    self, self.passive)
            elif clientType == "Python3":
                from .DebuggerInterfacePython3 import DebuggerInterfacePython3
                self.debuggerInterface = DebuggerInterfacePython3(
                    self, self.passive)
            elif clientType == "Ruby":
                from .DebuggerInterfaceRuby import DebuggerInterfaceRuby
                self.debuggerInterface = DebuggerInterfaceRuby(
                    self, self.passive)
            elif clientType == "None":
                from .DebuggerInterfaceNone import DebuggerInterfaceNone
                self.debuggerInterface = DebuggerInterfaceNone(
                    self, self.passive)
            else:
                from .DebuggerInterfaceNone import DebuggerInterfaceNone
                self.debuggerInterface = DebuggerInterfaceNone(
                    self, self.passive)
                self.clientType = "None"
        
    def __setClientType(self, clType):
        """
        Private method to set the client type.
        
        @param clType type of client to be started (string)
        """
        if clType is not None and clType in self.getSupportedLanguages():
            self.clientType = clType
            Preferences.Prefs.settings.setValue(
                'DebugClient/Type', self.clientType)
        
    def startClient(self, unplanned=True, clType=None, forProject=False,
                    runInConsole=False):
        """
        Public method to start a debug client.
        
        @keyparam unplanned flag indicating that the client has died (boolean)
        @keyparam clType type of client to be started (string)
        @keyparam forProject flag indicating a project related action (boolean)
        @keyparam runInConsole flag indicating to start the debugger in a
            console window (boolean)
        """
        self.running = False
        
        if not self.passive or not self.passiveClientExited:
            if self.debuggerInterface and self.debuggerInterface.isConnected():
                self.shutdownServer()
                self.clientGone.emit(unplanned and self.debugging)
        
        if clType:
            self.__setClientType(clType)
        
        # only start the client, if we are not in passive mode
        if not self.passive:
            if self.clientProcess:
                self.clientProcess.kill()
                self.clientProcess.waitForFinished(1000)
                self.clientProcess.deleteLater()
                self.clientProcess = None
            
            self.__createDebuggerInterface()
            if forProject:
                project = e5App().getObject("Project")
                if not project.isDebugPropertiesLoaded():
                    self.clientProcess, isNetworked, clientInterpreter = \
                        self.debuggerInterface.startRemote(self.serverPort(),
                                                           runInConsole)
                else:
                    self.clientProcess, isNetworked, clientInterpreter = \
                        self.debuggerInterface.startRemoteForProject(
                            self.serverPort(), runInConsole)
            else:
                self.clientProcess, isNetworked, clientInterpreter = \
                    self.debuggerInterface.startRemote(
                        self.serverPort(), runInConsole)
            
            if self.clientProcess:
                self.clientProcess.readyReadStandardError.connect(
                    self.__clientProcessError)
                self.clientProcess.readyReadStandardOutput.connect(
                    self.__clientProcessOutput)
                
                # Perform actions necessary, if client type has changed
                if self.lastClientType != self.clientType:
                    self.lastClientType = self.clientType
                    self.remoteBanner()
                elif self.__autoClearShell:
                    self.__autoClearShell = False
                    self.remoteBanner()
                self.remoteClientVariables(0, [], 0)
                self.remoteClientVariables(1, [], 0)
            else:
                if clType and self.lastClientType:
                    self.__setClientType(self.lastClientType)
        else:
            self.__createDebuggerInterface("None")
            clientInterpreter = ""
        
        if clientInterpreter != self.clientInterpreter:
            self.clientInterpreter = clientInterpreter
            self.clientInterpreterChanged.emit(clientInterpreter)

    def __clientProcessOutput(self):
        """
        Private slot to process client output received via stdout.
        """
        output = str(self.clientProcess.readAllStandardOutput(),
                     Preferences.getSystem("IOEncoding"),
                     'replace')
        self.clientProcessStdout.emit(output)
        
    def __clientProcessError(self):
        """
        Private slot to process client output received via stderr.
        """
        error = str(self.clientProcess.readAllStandardError(),
                    Preferences.getSystem("IOEncoding"),
                    'replace')
        self.clientProcessStderr.emit(error)
        
    def __clientClearBreakPoint(self, fn, lineno):
        """
        Private slot to handle the clientClearBreak signal.
        
        @param fn filename of breakpoint to clear (string)
        @param lineno line number of breakpoint to clear (integer)
        """
        if self.debugging:
            index = self.breakpointModel.getBreakPointIndex(fn, lineno)
            self.breakpointModel.deleteBreakPointByIndex(index)

    def __deleteBreakPoints(self, parentIndex, start, end):
        """
        Private slot to delete breakpoints.
        
        @param parentIndex index of parent item (QModelIndex)
        @param start start row (integer)
        @param end end row (integer)
        """
        if self.debugging:
            for row in range(start, end + 1):
                index = self.breakpointModel.index(row, 0, parentIndex)
                fn, lineno = \
                    self.breakpointModel.getBreakPointByIndex(index)[0:2]
                self.remoteBreakpoint(fn, lineno, False)

    def __changeBreakPoints(self, startIndex, endIndex):
        """
        Private slot to set changed breakpoints.
        
        @param startIndex starting index of the change breakpoins (QModelIndex)
        @param endIndex ending index of the change breakpoins (QModelIndex)
        """
        if self.debugging:
            self.__addBreakPoints(
                QModelIndex(), startIndex.row(), endIndex.row())

    def __breakPointDataAboutToBeChanged(self, startIndex, endIndex):
        """
        Private slot to handle the dataAboutToBeChanged signal of the
        breakpoint model.
        
        @param startIndex start index of the rows to be changed (QModelIndex)
        @param endIndex end index of the rows to be changed (QModelIndex)
        """
        if self.debugging:
            self.__deleteBreakPoints(
                QModelIndex(), startIndex.row(), endIndex.row())
        
    def __addBreakPoints(self, parentIndex, start, end):
        """
        Private slot to add breakpoints.
        
        @param parentIndex index of parent item (QModelIndex)
        @param start start row (integer)
        @param end end row (integer)
        """
        if self.debugging:
            for row in range(start, end + 1):
                index = self.breakpointModel.index(row, 0, parentIndex)
                fn, line, cond, temp, enabled, ignorecount = \
                    self.breakpointModel.getBreakPointByIndex(index)[:6]
                self.remoteBreakpoint(fn, line, True, cond, temp)
                if not enabled:
                    self.__remoteBreakpointEnable(fn, line, False)
                if ignorecount:
                    self.__remoteBreakpointIgnore(fn, line, ignorecount)

    def __makeWatchCondition(self, cond, special):
        """
        Private method to construct the condition string.
        
        @param cond condition (string)
        @param special special condition (string)
        @return condition string (string)
        """
        if special == "":
            _cond = cond
        else:
            if special == self.watchSpecialCreated:
                _cond = "{0} ??created??".format(cond)
            elif special == self.watchSpecialChanged:
                _cond = "{0} ??changed??".format(cond)
        return _cond
        
    def __splitWatchCondition(self, cond):
        """
        Private method to split a remote watch expression.
        
        @param cond remote expression (string)
        @return tuple of local expression (string) and special condition
            (string)
        """
        if cond.endswith(" ??created??"):
            cond, special = cond.split()
            special = self.watchSpecialCreated
        elif cond.endswith(" ??changed??"):
            cond, special = cond.split()
            special = self.watchSpecialChanged
        else:
            cond = cond
            special = ""
        
        return cond, special
        
    def __clientClearWatchPoint(self, condition):
        """
        Private slot to handle the clientClearWatch signal.
        
        @param condition expression of watch expression to clear (string)
        """
        if self.debugging:
            cond, special = self.__splitWatchCondition(condition)
            index = self.watchpointModel.getWatchPointIndex(cond, special)
            self.watchpointModel.deleteWatchPointByIndex(index)
        
    def __deleteWatchPoints(self, parentIndex, start, end):
        """
        Private slot to delete watch expressions.
        
        @param parentIndex index of parent item (QModelIndex)
        @param start start row (integer)
        @param end end row (integer)
        """
        if self.debugging:
            for row in range(start, end + 1):
                index = self.watchpointModel.index(row, 0, parentIndex)
                cond, special = \
                    self.watchpointModel.getWatchPointByIndex(index)[0:2]
                cond = self.__makeWatchCondition(cond, special)
                self.__remoteWatchpoint(cond, False)
        
    def __watchPointDataAboutToBeChanged(self, startIndex, endIndex):
        """
        Private slot to handle the dataAboutToBeChanged signal of the
        watch expression model.
        
        @param startIndex start index of the rows to be changed (QModelIndex)
        @param endIndex end index of the rows to be changed (QModelIndex)
        """
        if self.debugging:
            self.__deleteWatchPoints(
                QModelIndex(), startIndex.row(), endIndex.row())
        
    def __addWatchPoints(self, parentIndex, start, end):
        """
        Private slot to set a watch expression.
        
        @param parentIndex index of parent item (QModelIndex)
        @param start start row (integer)
        @param end end row (integer)
        """
        if self.debugging:
            for row in range(start, end + 1):
                index = self.watchpointModel.index(row, 0, parentIndex)
                cond, special, temp, enabled, ignorecount = \
                    self.watchpointModel.getWatchPointByIndex(index)[:5]
                cond = self.__makeWatchCondition(cond, special)
                self.__remoteWatchpoint(cond, True, temp)
                if not enabled:
                    self.__remoteWatchpointEnable(cond, False)
                if ignorecount:
                    self.__remoteWatchpointIgnore(cond, ignorecount)
        
    def __changeWatchPoints(self, startIndex, endIndex):
        """
        Private slot to set changed watch expressions.
        
        @param startIndex start index of the rows to be changed (QModelIndex)
        @param endIndex end index of the rows to be changed (QModelIndex)
        """
        if self.debugging:
            self.__addWatchPoints(
                QModelIndex(), startIndex.row(), endIndex.row())
        
    def getClientCapabilities(self, type):
        """
        Public method to retrieve the debug clients capabilities.
        
        @param type debug client type (string)
        @return debug client capabilities (integer)
        """
        try:
            return self.__clientCapabilities[type]
        except KeyError:
            return 0    # no capabilities
        
    def getClientInterpreter(self):
        """
        Public method to get the interpreter of the debug client.
        
        @return interpreter of the debug client (string)
        """
        return self.clientInterpreter
        
    def __newConnection(self):
        """
        Private slot to handle a new connection.
        """
        sock = self.nextPendingConnection()
        peerAddress = sock.peerAddress().toString()
        if peerAddress not in Preferences.getDebugger("AllowedHosts"):
            # the peer is not allowed to connect
            res = E5MessageBox.yesNo(
                None,
                self.tr("Connection from illegal host"),
                self.tr(
                    """<p>A connection was attempted by the illegal host"""
                    """ <b>{0}</b>. Accept this connection?</p>""")
                .format(peerAddress),
                icon=E5MessageBox.Warning)
            if not res:
                sock.abort()
                return
            else:
                allowedHosts = Preferences.getDebugger("AllowedHosts")
                allowedHosts.append(peerAddress)
                Preferences.setDebugger("AllowedHosts", allowedHosts)
        
        if self.passive:
            self.__createDebuggerInterface(
                Preferences.getDebugger("PassiveDbgType"))
        
        accepted = self.debuggerInterface.newConnection(sock)
        if accepted:
            # Perform actions necessary, if client type has changed
            if self.lastClientType != self.clientType:
                self.lastClientType = self.clientType
                self.remoteBanner()
            elif self.__autoClearShell:
                self.__autoClearShell = False
                self.remoteBanner()
            elif self.passive:
                self.remoteBanner()
            
            self.debuggerInterface.flush()

    def shutdownServer(self):
        """
        Public method to cleanly shut down.
        
        It closes our socket and shuts down
        the debug client. (Needed on Win OS)
        """
        if self.debuggerInterface is not None:
            self.debuggerInterface.shutdown()

    def remoteEnvironment(self, env):
        """
        Public method to set the environment for a program to debug, run, ...
        
        @param env environment settings (string)
        """
        envlist = Utilities.parseEnvironmentString(env)
        envdict = {}
        for el in envlist:
            try:
                key, value = el.split('=', 1)
                if value.startswith('"') or value.startswith("'"):
                    value = value[1:-1]
                envdict[key] = value
            except ValueError:
                pass
        self.debuggerInterface.remoteEnvironment(envdict)
        
    def remoteLoad(self, fn, argv, wd, env, autoClearShell=True,
                   tracePython=False, autoContinue=True, forProject=False,
                   runInConsole=False, autoFork=False, forkChild=False,
                   clientType="", enableCallTrace=False):
        """
        Public method to load a new program to debug.
        
        @param fn the filename to debug (string)
        @param argv the commandline arguments to pass to the program (string)
        @param wd the working directory for the program (string)
        @param env environment settings (string)
        @keyparam autoClearShell flag indicating, that the interpreter window
            should be cleared (boolean)
        @keyparam tracePython flag indicating if the Python library should be
            traced as well (boolean)
        @keyparam autoContinue flag indicating, that the debugger should not
            stop at the first executable line (boolean)
        @keyparam forProject flag indicating a project related action (boolean)
        @keyparam runInConsole flag indicating to start the debugger in a
            console window (boolean)
        @keyparam autoFork flag indicating the automatic fork mode (boolean)
        @keyparam forkChild flag indicating to debug the child after forking
            (boolean)
        @keyparam clientType client type to be used (string)
        @keyparam enableCallTrace flag indicating to enable the call trace
            function (boolean)
        """
        self.__autoClearShell = autoClearShell
        self.__autoContinue = autoContinue
        
        # Restart the client
        try:
            if clientType:
                self.__setClientType(clientType)
            else:
                self.__setClientType(
                    self.__clientAssociations[os.path.splitext(fn)[1]])
        except KeyError:
            self.__setClientType('Python3')    # assume it is a Python3 file
        self.startClient(False, forProject=forProject,
                         runInConsole=runInConsole)
        
        self.setCallTraceEnabled(enableCallTrace)
        self.remoteEnvironment(env)
        
        self.debuggerInterface.remoteLoad(fn, argv, wd, tracePython,
                                          autoContinue, autoFork, forkChild)
        self.debugging = True
        self.running = True
        self.__restoreBreakpoints()
        self.__restoreWatchpoints()

    def remoteRun(self, fn, argv, wd, env, autoClearShell=True,
                  forProject=False, runInConsole=False,
                  autoFork=False, forkChild=False,
                  clientType=""):
        """
        Public method to load a new program to run.
        
        @param fn the filename to run (string)
        @param argv the commandline arguments to pass to the program (string)
        @param wd the working directory for the program (string)
        @param env environment settings (string)
        @keyparam autoClearShell flag indicating, that the interpreter window
            should be cleared (boolean)
        @keyparam forProject flag indicating a project related action (boolean)
        @keyparam runInConsole flag indicating to start the debugger in a
            console window (boolean)
        @keyparam autoFork flag indicating the automatic fork mode (boolean)
        @keyparam forkChild flag indicating to debug the child after forking
            (boolean)
        @keyparam clientType client type to be used (string)
        """
        self.__autoClearShell = autoClearShell
        
        # Restart the client
        try:
            if clientType:
                self.__setClientType(clientType)
            else:
                self.__setClientType(
                    self.__clientAssociations[os.path.splitext(fn)[1]])
        except KeyError:
            self.__setClientType('Python3')    # assume it is a Python3 file
        self.startClient(False, forProject=forProject,
                         runInConsole=runInConsole)
        
        self.remoteEnvironment(env)
        
        self.debuggerInterface.remoteRun(fn, argv, wd, autoFork, forkChild)
        self.debugging = False
        self.running = True

    def remoteCoverage(self, fn, argv, wd, env, autoClearShell=True,
                       erase=False, forProject=False, runInConsole=False,
                       clientType=""):
        """
        Public method to load a new program to collect coverage data.
        
        @param fn the filename to run (string)
        @param argv the commandline arguments to pass to the program (string)
        @param wd the working directory for the program (string)
        @param env environment settings (string)
        @keyparam autoClearShell flag indicating, that the interpreter window
            should be cleared (boolean)
        @keyparam erase flag indicating that coverage info should be
            cleared first (boolean)
        @keyparam forProject flag indicating a project related action (boolean)
        @keyparam runInConsole flag indicating to start the debugger in a
            console window (boolean)
        @keyparam clientType client type to be used (string)
        """
        self.__autoClearShell = autoClearShell
        
        # Restart the client
        try:
            if clientType:
                self.__setClientType(clientType)
            else:
                self.__setClientType(
                    self.__clientAssociations[os.path.splitext(fn)[1]])
        except KeyError:
            self.__setClientType('Python3')    # assume it is a Python3 file
        self.startClient(False, forProject=forProject,
                         runInConsole=runInConsole)
        
        self.remoteEnvironment(env)
        
        self.debuggerInterface.remoteCoverage(fn, argv, wd, erase)
        self.debugging = False
        self.running = True

    def remoteProfile(self, fn, argv, wd, env, autoClearShell=True,
                      erase=False, forProject=False,
                      runInConsole=False,
                      clientType=""):
        """
        Public method to load a new program to collect profiling data.
        
        @param fn the filename to run (string)
        @param argv the commandline arguments to pass to the program (string)
        @param wd the working directory for the program (string)
        @param env environment settings (string)
        @keyparam autoClearShell flag indicating, that the interpreter window
            should be cleared (boolean)
        @keyparam erase flag indicating that timing info should be cleared
            first (boolean)
        @keyparam forProject flag indicating a project related action (boolean)
        @keyparam runInConsole flag indicating to start the debugger in a
            console window (boolean)
        @keyparam clientType client type to be used (string)
        """
        self.__autoClearShell = autoClearShell
        
        # Restart the client
        try:
            if clientType:
                self.__setClientType(clientType)
            else:
                self.__setClientType(
                    self.__clientAssociations[os.path.splitext(fn)[1]])
        except KeyError:
            self.__setClientType('Python3')    # assume it is a Python3 file
        self.startClient(False, forProject=forProject,
                         runInConsole=runInConsole)
        
        self.remoteEnvironment(env)
        
        self.debuggerInterface.remoteProfile(fn, argv, wd, erase)
        self.debugging = False
        self.running = True

    def remoteStatement(self, stmt):
        """
        Public method to execute a Python statement.
        
        @param stmt the Python statement to execute (string). It
              should not have a trailing newline.
        """
        self.debuggerInterface.remoteStatement(stmt)

    def remoteStep(self):
        """
        Public method to single step the debugged program.
        """
        self.debuggerInterface.remoteStep()

    def remoteStepOver(self):
        """
        Public method to step over the debugged program.
        """
        self.debuggerInterface.remoteStepOver()

    def remoteStepOut(self):
        """
        Public method to step out the debugged program.
        """
        self.debuggerInterface.remoteStepOut()

    def remoteStepQuit(self):
        """
        Public method to stop the debugged program.
        """
        self.debuggerInterface.remoteStepQuit()

    def remoteContinue(self, special=False):
        """
        Public method to continue the debugged program.
        
        @param special flag indicating a special continue operation
        """
        self.debuggerInterface.remoteContinue(special)

    def remoteBreakpoint(self, fn, line, set, cond=None, temp=False):
        """
        Public method to set or clear a breakpoint.
        
        @param fn filename the breakpoint belongs to (string)
        @param line linenumber of the breakpoint (int)
        @param set flag indicating setting or resetting a breakpoint (boolean)
        @param cond condition of the breakpoint (string)
        @param temp flag indicating a temporary breakpoint (boolean)
        """
        self.debuggerInterface.remoteBreakpoint(fn, line, set, cond, temp)
        
    def __remoteBreakpointEnable(self, fn, line, enable):
        """
        Private method to enable or disable a breakpoint.
        
        @param fn filename the breakpoint belongs to (string)
        @param line linenumber of the breakpoint (int)
        @param enable flag indicating enabling or disabling a breakpoint
            (boolean)
        """
        self.debuggerInterface.remoteBreakpointEnable(fn, line, enable)
        
    def __remoteBreakpointIgnore(self, fn, line, count):
        """
        Private method to ignore a breakpoint the next couple of occurrences.
        
        @param fn filename the breakpoint belongs to (string)
        @param line linenumber of the breakpoint (int)
        @param count number of occurrences to ignore (int)
        """
        self.debuggerInterface.remoteBreakpointIgnore(fn, line, count)
        
    def __remoteWatchpoint(self, cond, set, temp=False):
        """
        Private method to set or clear a watch expression.
        
        @param cond expression of the watch expression (string)
        @param set flag indicating setting or resetting a watch expression
            (boolean)
        @param temp flag indicating a temporary watch expression (boolean)
        """
        # cond is combination of cond and special (s. watch expression viewer)
        self.debuggerInterface.remoteWatchpoint(cond, set, temp)
    
    def __remoteWatchpointEnable(self, cond, enable):
        """
        Private method to enable or disable a watch expression.
        
        @param cond expression of the watch expression (string)
        @param enable flag indicating enabling or disabling a watch expression
            (boolean)
        """
        # cond is combination of cond and special (s. watch expression viewer)
        self.debuggerInterface.remoteWatchpointEnable(cond, enable)
    
    def __remoteWatchpointIgnore(self, cond, count):
        """
        Private method to ignore a watch expression the next couple of
        occurrences.
        
        @param cond expression of the watch expression (string)
        @param count number of occurrences to ignore (int)
        """
        # cond is combination of cond and special (s. watch expression viewer)
        self.debuggerInterface.remoteWatchpointIgnore(cond, count)
    
    def remoteRawInput(self, s):
        """
        Public method to send the raw input to the debugged program.
        
        @param s the raw input (string)
        """
        self.debuggerInterface.remoteRawInput(s)
        self.clientRawInputSent.emit()
        
    def remoteThreadList(self):
        """
        Public method to request the list of threads from the client.
        """
        self.debuggerInterface.remoteThreadList()
        
    def remoteSetThread(self, tid):
        """
        Public method to request to set the given thread as current thread.
        
        @param tid id of the thread (integer)
        """
        self.debuggerInterface.remoteSetThread(tid)
        
    def remoteClientVariables(self, scope, filter, framenr=0):
        """
        Public method to request the variables of the debugged program.
        
        @param scope the scope of the variables (0 = local, 1 = global)
        @param filter list of variable types to filter out (list of int)
        @param framenr framenumber of the variables to retrieve (int)
        """
        self.debuggerInterface.remoteClientVariables(scope, filter, framenr)
        
    def remoteClientVariable(self, scope, filter, var, framenr=0):
        """
        Public method to request the variables of the debugged program.
        
        @param scope the scope of the variables (0 = local, 1 = global)
        @param filter list of variable types to filter out (list of int)
        @param var list encoded name of variable to retrieve (string)
        @param framenr framenumber of the variables to retrieve (int)
        """
        self.debuggerInterface.remoteClientVariable(
            scope, filter, var, framenr)
        
    def remoteClientSetFilter(self, scope, filter):
        """
        Public method to set a variables filter list.
        
        @param scope the scope of the variables (0 = local, 1 = global)
        @param filter regexp string for variable names to filter out (string)
        """
        self.debuggerInterface.remoteClientSetFilter(scope, filter)
        
    def setCallTraceEnabled(self, on):
        """
        Public method to set the call trace state.
        
        @param on flag indicating to enable the call trace function (boolean)
        """
        self.debuggerInterface.setCallTraceEnabled(on)
        
    def remoteEval(self, arg):
        """
        Public method to evaluate arg in the current context of the debugged
        program.
        
        @param arg the arguments to evaluate (string)
        """
        self.debuggerInterface.remoteEval(arg)
        
    def remoteExec(self, stmt):
        """
        Public method to execute stmt in the current context of the debugged
        program.
        
        @param stmt statement to execute (string)
        """
        self.debuggerInterface.remoteExec(stmt)
        
    def remoteBanner(self):
        """
        Public slot to get the banner info of the remote client.
        """
        self.debuggerInterface.remoteBanner()
        
    def remoteCapabilities(self):
        """
        Public slot to get the debug clients capabilities.
        """
        self.debuggerInterface.remoteCapabilities()
        
    def remoteCompletion(self, text):
        """
        Public slot to get the a list of possible commandline completions
        from the remote client.
        
        @param text the text to be completed (string)
        """
        self.debuggerInterface.remoteCompletion(text)

    def remoteUTPrepare(self, fn, tn, tfn, failed, cov, covname, coverase,
                        clientType=""):
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
        @keyparam clientType client type to be used (string)
        """
        # Restart the client if there is already a program loaded.
        try:
            if clientType:
                self.__setClientType(clientType)
            else:
                self.__setClientType(
                    self.__clientAssociations[os.path.splitext(fn)[1]])
        except KeyError:
            self.__setClientType('Python3')    # assume it is a Python3 file
        self.startClient(False)
        
        self.debuggerInterface.remoteUTPrepare(
            fn, tn, tfn, failed, cov, covname, coverase)
        self.debugging = False
        self.running = True
        
    def remoteUTRun(self):
        """
        Public method to start a unittest run.
        """
        self.debuggerInterface.remoteUTRun()
        
    def remoteUTStop(self):
        """
        public method to stop a unittest run.
        """
        self.debuggerInterface.remoteUTStop()
        
    def signalClientOutput(self, line):
        """
        Public method to process a line of client output.
        
        @param line client output (string)
        """
        self.clientOutput.emit(line)
        
    def signalClientLine(self, filename, lineno, forStack=False):
        """
        Public method to process client position feedback.
        
        @param filename name of the file currently being executed (string)
        @param lineno line of code currently being executed (integer)
        @param forStack flag indicating this is for a stack dump (boolean)
        """
        self.clientLine.emit(filename, lineno, forStack)
        
    def signalClientStack(self, stack):
        """
        Public method to process a client's stack information.
        
        @param stack list of stack entries. Each entry is a tuple of three
            values giving the filename, linenumber and method
            (list of lists of (string, integer, string))
        """
        self.clientStack.emit(stack)
        
    def signalClientThreadList(self, currentId, threadList):
        """
        Public method to process the client thread list info.
        
        @param currentId id of the current thread (integer)
        @param threadList list of dictionaries containing the thread data
        """
        self.clientThreadList.emit(currentId, threadList)
        
    def signalClientThreadSet(self):
        """
        Public method to handle the change of the client thread.
        """
        self.clientThreadSet.emit()
        
    def signalClientVariables(self, scope, variables):
        """
        Public method to process the client variables info.
        
        @param scope scope of the variables (-1 = empty global, 1 = global,
            0 = local)
        @param variables the list of variables from the client
        """
        self.clientVariables.emit(scope, variables)
        
    def signalClientVariable(self, scope, variables):
        """
        Public method to process the client variable info.
        
        @param scope scope of the variables (-1 = empty global, 1 = global,
            0 = local)
        @param variables the list of members of a classvariable from the client
        """
        self.clientVariable.emit(scope, variables)
        
    def signalClientStatement(self, more):
        """
        Public method to process the input response from the client.
        
        @param more flag indicating that more user input is required
        """
        self.clientStatement.emit(more)
        
    def signalClientException(self, exceptionType, exceptionMessage,
                              stackTrace):
        """
        Public method to process the exception info from the client.
        
        @param exceptionType type of exception raised (string)
        @param exceptionMessage message given by the exception (string)
        @param stackTrace list of stack entries with the exception position
            first. Each stack entry is a list giving the filename and the
            linenumber.
        """
        if self.running:
            self.clientException.emit(exceptionType, exceptionMessage,
                                      stackTrace)
        
    def signalClientSyntaxError(self, message, filename, lineNo, characterNo):
        """
        Public method to process the syntax error info from the client.
        
        @param message message of the syntax error (string)
        @param filename translated filename of the syntax error position
            (string)
        @param lineNo line number of the syntax error position (integer)
        @param characterNo character number of the syntax error position
            (integer)
        """
        if self.running:
            self.clientSyntaxError.emit(message, filename, lineNo, characterNo)
        
    def signalClientSignal(self, message, filename, lineNo,
                           funcName, funcArgs):
        """
        Public method to process a signal generated on the client side.
        
        @param message message of the syntax error
        @type str
        @param filename translated filename of the syntax error position
        @type str
        @param lineNo line number of the syntax error position
        @type int
        @param funcName name of the function causing the signal
        @type str
        @param funcArgs function arguments
        @type str
        """
        if self.running:
            self.clientSignal.emit(message, filename, lineNo,
                                   funcName, funcArgs)
        
    def signalClientExit(self, status):
        """
        Public method to process the client exit status.
        
        @param status exit code as a string (string)
        """
        if self.passive:
            self.__passiveShutDown()
        self.clientExit.emit(int(status))
        if Preferences.getDebugger("AutomaticReset"):
            self.startClient(False)
        if self.passive:
            self.__createDebuggerInterface("None")
            self.signalClientOutput(self.tr('\nNot connected\n'))
            self.signalClientStatement(False)
        self.running = False
        
    def signalClientClearBreak(self, filename, lineno):
        """
        Public method to process the client clear breakpoint command.
        
        @param filename filename of the breakpoint (string)
        @param lineno line umber of the breakpoint (integer)
        """
        self.clientClearBreak.emit(filename, lineno)
        
    def signalClientBreakConditionError(self, filename, lineno):
        """
        Public method to process the client breakpoint condition error info.
        
        @param filename filename of the breakpoint (string)
        @param lineno line umber of the breakpoint (integer)
        """
        self.clientBreakConditionError.emit(filename, lineno)
        
    def signalClientClearWatch(self, condition):
        """
        Public slot to handle the clientClearWatch signal.
        
        @param condition expression of watch expression to clear (string)
        """
        self.clientClearWatch.emit(condition)
        
    def signalClientWatchConditionError(self, condition):
        """
        Public method to process the client watch expression error info.
        
        @param condition expression of watch expression to clear (string)
        """
        self.clientWatchConditionError.emit(condition)
        
    def signalClientRawInput(self, prompt, echo):
        """
        Public method to process the client raw input command.
        
        @param prompt the input prompt (string)
        @param echo flag indicating an echoing of the input (boolean)
        """
        self.clientRawInput.emit(prompt, echo)
        
    def signalClientBanner(self, version, platform, debugClient):
        """
        Public method to process the client banner info.
        
        @param version interpreter version info (string)
        @param platform hostname of the client (string)
        @param debugClient additional debugger type info (string)
        """
        self.clientBanner.emit(version, platform, debugClient)
        
    def signalClientCapabilities(self, capabilities, clientType):
        """
        Public method to process the client capabilities info.
        
        @param capabilities bitmaks with the client capabilities (integer)
        @param clientType type of the debug client (string)
        """
        self.__clientCapabilities[clientType] = capabilities
        self.clientCapabilities.emit(capabilities, clientType)
        
    def signalClientCompletionList(self, completionList, text):
        """
        Public method to process the client auto completion info.
        
        @param completionList list of possible completions (list of strings)
        @param text the text to be completed (string)
        """
        self.clientCompletionList.emit(completionList, text)
        
    def signalClientCallTrace(self, isCall, fromFile, fromLine, fromFunction,
                              toFile, toLine, toFunction):
        """
        Public method to process the client call trace data.
        
        @param isCall flag indicating a 'call' (boolean)
        @param fromFile name of the originating file (string)
        @param fromLine line number in the originating file (string)
        @param fromFunction name of the originating function (string)
        @param toFile name of the target file (string)
        @param toLine line number in the target file (string)
        @param toFunction name of the target function (string)
        """
        self.callTraceInfo.emit(
            isCall, fromFile, fromLine, fromFunction,
            toFile, toLine, toFunction)
        
    def clientUtPrepared(self, result, exceptionType, exceptionValue):
        """
        Public method to process the client unittest prepared info.
        
        @param result number of test cases (0 = error) (integer)
        @param exceptionType exception type (string)
        @param exceptionValue exception message (string)
        """
        self.utPrepared.emit(result, exceptionType, exceptionValue)
        
    def clientUtStartTest(self, testname, doc):
        """
        Public method to process the client start test info.
        
        @param testname name of the test (string)
        @param doc short description of the test (string)
        """
        self.utStartTest.emit(testname, doc)
        
    def clientUtStopTest(self):
        """
        Public method to process the client stop test info.
        """
        self.utStopTest.emit()
        
    def clientUtTestFailed(self, testname, traceback, id):
        """
        Public method to process the client test failed info.
        
        @param testname name of the test (string)
        @param traceback lines of traceback info (list of strings)
        @param id id of the test (string)
        """
        self.utTestFailed.emit(testname, traceback, id)
        
    def clientUtTestErrored(self, testname, traceback, id):
        """
        Public method to process the client test errored info.
        
        @param testname name of the test (string)
        @param traceback lines of traceback info (list of strings)
        @param id id of the test (string)
        """
        self.utTestErrored.emit(testname, traceback, id)
        
    def clientUtTestSkipped(self, testname, reason, id):
        """
        Public method to process the client test skipped info.
        
        @param testname name of the test (string)
        @param reason reason for skipping the test (string)
        @param id id of the test (string)
        """
        self.utTestSkipped.emit(testname, reason, id)
        
    def clientUtTestFailedExpected(self, testname, traceback, id):
        """
        Public method to process the client test failed expected info.
        
        @param testname name of the test (string)
        @param traceback lines of traceback info (list of strings)
        @param id id of the test (string)
        """
        self.utTestFailedExpected.emit(testname, traceback, id)
        
    def clientUtTestSucceededUnexpected(self, testname, id):
        """
        Public method to process the client test succeeded unexpected info.
        
        @param testname name of the test (string)
        @param id id of the test (string)
        """
        self.utTestSucceededUnexpected.emit(testname, id)
        
    def clientUtFinished(self):
        """
        Public method to process the client unit test finished info.
        """
        self.utFinished.emit()
        
    def passiveStartUp(self, fn, exc):
        """
        Public method to handle a passive debug connection.
        
        @param fn filename of the debugged script (string)
        @param exc flag to enable exception reporting of the IDE (boolean)
        """
        self.appendStdout.emit(self.tr("Passive debug connection received\n"))
        self.passiveClientExited = False
        self.debugging = True
        self.running = True
        self.__restoreBreakpoints()
        self.__restoreWatchpoints()
        self.passiveDebugStarted.emit(fn, exc)
        
    def __passiveShutDown(self):
        """
        Private method to shut down a passive debug connection.
        """
        self.passiveClientExited = True
        self.shutdownServer()
        self.appendStdout.emit(self.tr("Passive debug connection closed\n"))
        
    def __restoreBreakpoints(self):
        """
        Private method to restore the breakpoints after a restart.
        """
        if self.debugging:
            self.__addBreakPoints(
                QModelIndex(), 0, self.breakpointModel.rowCount() - 1)
    
    def __restoreWatchpoints(self):
        """
        Private method to restore the watch expressions after a restart.
        """
        if self.debugging:
            self.__addWatchPoints(
                QModelIndex(), 0, self.watchpointModel.rowCount() - 1)
    
    def getBreakPointModel(self):
        """
        Public slot to get a reference to the breakpoint model object.
        
        @return reference to the breakpoint model object (BreakPointModel)
        """
        return self.breakpointModel

    def getWatchPointModel(self):
        """
        Public slot to get a reference to the watch expression model object.
        
        @return reference to the watch expression model object
            (WatchPointModel)
        """
        return self.watchpointModel
    
    def isConnected(self):
        """
        Public method to test, if the debug server is connected to a backend.
        
        @return flag indicating a connection (boolean)
        """
        return self.debuggerInterface and self.debuggerInterface.isConnected()
