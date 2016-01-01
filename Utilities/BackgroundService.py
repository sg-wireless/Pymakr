# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#
# pylint: disable=C0103

"""
Module implementing a background service for the various checkers and other
python interpreter dependent functions.
"""

from __future__ import unicode_literals

import json
import os
import struct
import sys
from zlib import adler32

from PyQt5.QtCore import QProcess, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QTcpServer, QHostAddress

from E5Gui import E5MessageBox
from E5Gui.E5Application import e5App
import Preferences
import Utilities

from eric6config import getConfig


class BackgroundService(QTcpServer):
    """
    Class implementing the main part of the background service.
    """
    serviceNotAvailable = pyqtSignal(str, str, str, str)
    batchJobDone = pyqtSignal(str, str)
    
    def __init__(self):
        """
        Constructor of the BackgroundService class.
        """
        self.processes = {}
        self.connections = {}
        self.isWorking = None
        self.runningJob = [None, None, None, None]
        self.__queue = []
        self.services = {}

        super(BackgroundService, self).__init__()

        networkInterface = Preferences.getDebugger("NetworkInterface")
        if networkInterface == "all" or '.' in networkInterface:
            self.hostAddress = '127.0.0.1'
        else:
            self.hostAddress = '::1'
        self.listen(QHostAddress(self.hostAddress))

        self.newConnection.connect(self.on_newConnection)
        
        port = self.serverPort()
        ## Note: Need the port if started external in debugger:
        print('BackgroundService listening on: %i' % port)
        for pyName in ['Python', 'Python3']:
            interpreter = Preferences.getDebugger(
                pyName + "Interpreter")
            process = self.__startExternalClient(interpreter, port)
            if process:
                if pyName == 'Python':
                    pyName = 'Python2'
                self.processes[pyName] = process, interpreter

    def __startExternalClient(self, interpreter, port):
        """
        Private method to start the background client as external process.
        
        @param interpreter path and name of the executable to start (string)
        @param port socket port to which the interpreter should connect (int)
        @return the process object (QProcess or None)
        """
        if interpreter == "" or not Utilities.isinpath(interpreter):
            return None
        
        backgroundClient = os.path.join(
            getConfig('ericDir'),
            "Utilities", "BackgroundClient.py")
        proc = QProcess()
        proc.setProcessChannelMode(QProcess.ForwardedChannels)
        args = [backgroundClient, self.hostAddress, str(port)]
        proc.start(interpreter, args)
        if not proc.waitForStarted(10000):
            proc = None
        return proc
    
    def __processQueue(self):
        """
        Private method to take the next service request and send it to the
        client.
        """
        if self.__queue and self.isWorking is None:
            fx, lang, fn, data = self.__queue.pop(0)
            self.isWorking = lang
            self.runningJob = fx, lang, fn, data
            self.__send(fx, lang, fn, data)
    
    def __send(self, fx, lang, fn, data):
        """
        Private method to send a job request to one of the clients.
        
        @param fx remote function name to execute (str)
        @param lang language to connect to (str)
        @param fn filename for identification (str)
        @param data function argument(s) (any basic datatype)
        """
        self.__cancelled = False
        connection = self.connections.get(lang)
        if connection is None:
            if fx != 'INIT':
                # Avoid growing recursion deep which could itself result in an
                # exception
                QTimer.singleShot(
                    0,
                    lambda: self.serviceNotAvailable.emit(
                        fx, lang, fn, self.tr(
                            '{0} not configured.').format(lang)))
            # Reset flag and continue processing queue
            self.isWorking = None
            self.__processQueue()
        else:
            packedData = json.dumps([fx, fn, data])
            if sys.version_info[0] == 3:
                packedData = bytes(packedData, 'utf-8')
            header = struct.pack(
                b'!II', len(packedData), adler32(packedData) & 0xffffffff)
            connection.write(header)
            connection.write(b'JOB   ')    # 6 character message type
            connection.write(packedData)

    def __receive(self, lang):
        """
        Private method to receive the response from the clients.
        
        @param lang language of the incomming connection (str)
        """
        connection = self.connections[lang]
        while connection.bytesAvailable():
            if self.__cancelled:
                connection.readAll()
                continue
            
            header = connection.read(struct.calcsize(b'!II'))
            length, datahash = struct.unpack(b'!II', header)
            
            packedData = b''
            while len(packedData) < length:
                connection.waitForReadyRead(50)
                packedData += connection.read(length - len(packedData))

            assert adler32(packedData) & 0xffffffff == datahash, \
                'Hashes not equal'
            if sys.version_info[0] == 3:
                packedData = packedData.decode('utf-8')
            # "check" if is's a tuple of 3 values
            fx, fn, data = json.loads(packedData)
            
            if fx == 'INIT':
                pass
            elif fx == 'EXCEPTION':
                # Remove connection because it'll close anyway
                self.connections.pop(lang, None)
                # Call sys.excepthook(type, value, traceback) to emulate the
                # exception which was caught on the client
                sys.excepthook(*data)
                res = E5MessageBox.question(
                    None,
                    self.tr("Restart background client?"),
                    self.tr(
                        "<p>The background client for <b>{0}</b> has stopped"
                        " due to an exception. It's used by various plug-ins"
                        " like the different checkers.</p>"
                        "<p>Select"
                        "<ul>"
                        "<li><b>'Yes'</b> to restart the client, but abort the"
                        " last job</li>"
                        "<li><b>'Retry'</b> to restart the client and the last"
                        " job</li>"
                        "<li><b>'No'</b> to leave the client off.</li>"
                        "</ul></p>"
                        "<p>Note: The client can be restarted by opening and"
                        " accepting the preferences dialog or reloading/"
                        "changing the project.</p>").format(lang),
                    E5MessageBox.Yes | E5MessageBox.No | E5MessageBox.Retry,
                    E5MessageBox.Yes)
                
                if res == E5MessageBox.Retry:
                    self.enqueueRequest(*self.runningJob)
                else:
                    fx, lng, fn, data = self.runningJob
                    self.services[(fx, lng)][3](fx, lng, fn, self.tr(
                        'An error in Erics background client stopped the'
                        ' service.')
                    )
                if res != E5MessageBox.No:
                    self.isWorking = None
                    self.restartService(lang, True)
                    return
            elif data == 'Unknown service.':
                callback = self.services.get((fx, lang))
                if callback:
                    callback[3](fx, lang, fn, data)
            elif fx.startswith("batch_"):
                fx = fx.replace("batch_", "")
                if data != "__DONE__":
                    callback = self.services.get((fx, lang))
                    if callback:
                        callback[2](fn, *data)
                    continue
                else:
                    self.batchJobDone.emit(fx, lang)
            else:
                callback = self.services.get((fx, lang))
                if callback:
                    callback[2](fn, *data)
        
        self.isWorking = None
        self.__processQueue()

    def preferencesOrProjectChanged(self):
        """
        Public slot to restart the built in languages.
        """
        for pyName in ['Python', 'Python3']:
            interpreter = Preferences.getDebugger(
                pyName + "Interpreter")
            
            if pyName == 'Python':
                pyName = 'Python2'
            
            # Tweak the processes list to reflect the changed interpreter
            proc, inter = self.processes.pop(pyName, [None, None])
            self.processes[pyName] = proc, interpreter
            
            self.restartService(pyName)

    def restartService(self, language, forceKill=False):
        """
        Public method to restart a given lanuage.
        
        @param language to restart (str)
        @keyparam forceKill flag to kill a running task (bool)
        """
        try:
            proc, interpreter = self.processes.pop(language)
        except KeyError:
            return
        
        # Don't kill a process if it's still working
        if not forceKill:
            while self.isWorking is not None:
                QApplication.processEvents()
        
        conn = self.connections.pop(language, None)
        if conn:
            conn.blockSignals(True)
            conn.close()
        if proc:
            proc.close()
        
        port = self.serverPort()
        process = self.__startExternalClient(interpreter, port)
        if process:
            self.processes[language] = process, interpreter

    def enqueueRequest(self, fx, lang, fn, data):
        """
        Public method implementing a queued processing of incomming events.
        
        Dublicate service requests updates an older request to avoid overrun or
        starving of the services.
        @param fx function name of the service (str)
        @param lang language to connect to (str)
        @param fn filename for identification (str)
        @param data function argument(s) (any basic datatype(s))
        """
        args = [fx, lang, fn, data]
        if fx == 'INIT':
            self.__queue.insert(0, args)
        else:
            for pendingArg in self.__queue:
                # Check if it's the same service request (fx, lang, fn equal)
                if pendingArg[:3] == args[:3]:
                    # Update the data
                    pendingArg[3] = args[3]
                    break
            else:
                self.__queue.append(args)
        self.__processQueue()
    
    def requestCancel(self, fx, lang):
        """
        Public method to ask a batch job to terminate.
        
        @param fx function name of the service (str)
        @param lang language to connect to (str)
        """
        self.__cancelled = True
        
        entriesToRemove = []
        for pendingArg in self.__queue:
            if pendingArg[:2] == [fx, lang]:
                entriesToRemove.append(pendingArg)
        for entryToRemove in entriesToRemove:
            self.__queue.remove(entryToRemove)
        
        connection = self.connections.get(lang)
        if connection is None:
            return
        else:
            header = struct.pack(b'!II', 0, 0)
            connection.write(header)
            connection.write(b'CANCEL')    # 6 character message type
    
    def serviceConnect(
            self, fx, lang, modulepath, module, callback,
            onErrorCallback=None, onBatchDone=None):
        """
        Public method to announce a new service to the background
        service/client.
        
        @param fx function name of the service (str)
        @param lang language of the new service (str)
        @param modulepath full path to the module (str)
        @param module name to import (str)
        @param callback function called on service response (function)
        @param onErrorCallback function called, if client isn't available
            (function)
        @param onBatchDone function called when a batch job is done (function)
        """
        self.services[(fx, lang)] = \
            modulepath, module, callback, onErrorCallback
        self.enqueueRequest('INIT', lang, fx, [modulepath, module])
        if onErrorCallback:
            self.serviceNotAvailable.connect(onErrorCallback)
        if onBatchDone:
            self.batchJobDone.connect(onBatchDone)
    
    def serviceDisconnect(self, fx, lang):
        """
        Public method to remove the service from the service list.
        
        @param fx function name of the service (function)
        @param lang language of the service (str)
        """
        serviceArgs = self.services.pop((fx, lang), None)
        if serviceArgs and serviceArgs[3]:
            self.serviceNotAvailable.disconnect(serviceArgs[3])

    def on_newConnection(self):
        """
        Private slot for new incomming connections from the clients.
        """
        connection = self.nextPendingConnection()
        if not connection.waitForReadyRead(1000):
            return
        lang = connection.read(64)
        if sys.version_info[0] == 3:
            lang = lang.decode('utf-8')
        # Avoid hanging of eric on shutdown
        if self.connections.get(lang):
            self.connections[lang].close()
        if self.isWorking == lang:
            self.isWorking = None
        self.connections[lang] = connection
        connection.readyRead.connect(
            lambda x=lang: self.__receive(x))
        connection.disconnected.connect(
            lambda x=lang: self.on_disconnectSocket(x))
            
        for (fx, lng), args in self.services.items():
            if lng == lang:
                # Register service with modulepath and module
                self.enqueueRequest('INIT', lng, fx, args[:2])
        
        # Syntax check the open editors again
        try:
            vm = e5App().getObject("ViewManager")
        except KeyError:
            return
        for editor in vm.getOpenEditors():
            if editor.getLanguage() == lang:
                QTimer.singleShot(0, editor.checkSyntax)

    def on_disconnectSocket(self, lang):
        """
        Private slot called when connection to a client is lost.
        
        @param lang client language which connection is lost (str)
        """
        conn = self.connections.pop(lang, None)
        if conn:
            conn.close()
            fx, lng, fn, data = self.runningJob
            if fx != 'INIT' and lng == lang:
                self.services[(fx, lng)][3](fx, lng, fn, self.tr(
                    'Erics background client disconnected because of an'
                    ' unknown reason.')
                )
            self.isWorking = None
            
            res = E5MessageBox.yesNo(
                None,
                self.tr('Background client disconnected.'),
                self.tr(
                    'The background client for <b>{0}</b> disconnect because'
                    ' of an unknown reason.<br>Should it be restarted?'
                ).format(lang),
                yesDefault=True)
            if res:
                self.restartService(lang)

    def shutdown(self):
        """
        Public method to cleanup the connections and processes when eric is
        shuting down.
        """
        for connection in self.connections.values():
            # Prevent calling of on_disconnectSocket
            connection.blockSignals(True)
            connection.close()
        
        for process, interpreter in self.processes.values():
            process.close()
            process = None
