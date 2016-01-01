# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#
# pylint: disable=C0103

"""
Module implementing a Qt free version of a background client for the various
checkers and other python interpreter dependent functions.
"""

from __future__ import unicode_literals
try:
    bytes = unicode
    import StringIO as io   # __IGNORE_EXCEPTION__
except NameError:
    import io       # __IGNORE_WARNING__

import json
import socket
import struct
import sys
import time
import traceback
from zlib import adler32


class BackgroundClient(object):
    """
    Class implementing the main part of the background client.
    """
    def __init__(self, host, port):
        """
        Constructor of the BackgroundClient class.
        
        @param host ip address the background service is listening
        @param port port of the background service
        """
        self.services = {}
        self.batchServices = {}
        
        self.connection = socket.create_connection((host, port))
        ver = b'Python2' if sys.version_info[0] == 2 else b'Python3'
        self.connection.sendall(ver)

    def __initClientService(self, fn, path, module):
        """
        Private method to import the given module and register it as service.
        
        @param fn service name to register (str)
        @param path contains the path to the module (str)
        @param module name to import (str)
        @return text result of the import action (str)
        """
        sys.path.insert(1, path)
        try:
            importedModule = __import__(module, globals(), locals(), [], 0)
            self.services[fn] = importedModule.initService()
            try:
                self.batchServices["batch_" + fn] = \
                    importedModule.initBatchService()
            except AttributeError:
                pass
            return 'ok'
        except ImportError:
            return 'Import Error'

    def __send(self, fx, fn, data):
        """
        Private method to send a job response back to the BackgroundService.
        
        @param fx remote function name to execute (str)
        @param fn filename for identification (str)
        @param data return value(s) (any basic datatype)
        """
        packedData = json.dumps([fx, fn, data])
        if sys.version_info[0] == 3:
            packedData = bytes(packedData, 'utf-8')
        header = struct.pack(
            b'!II', len(packedData), adler32(packedData) & 0xffffffff)
        self.connection.sendall(header)
        self.connection.sendall(packedData)

    def __receive(self, length):
        """
        Private methode to receive the given length of bytes.
        
        @param length bytes to receive (int)
        @return received bytes or None if connection closed (bytes)
        """
        data = b''
        while len(data) < length:
            newData = self.connection.recv(length - len(data))
            if not newData:
                return None
            data += newData
        return data
    
    def __peek(self, length):
        """
        Private methode to peek the given length of bytes.
        
        @param length bytes to receive (int)
        @return received bytes (bytes)
        """
        data = b''
        self.connection.setblocking(False)
        try:
            data = self.connection.recv(length, socket.MSG_PEEK)
        except socket.error:
            pass
        self.connection.setblocking(True)
        return data
    
    def __cancelled(self):
        """
        Private method to check for a job cancellation.
        
        @return flag indicating a cancellation (boolean)
        """
        msg = self.__peek(struct.calcsize(b'!II') + 6)
        if msg[-6:] == b"CANCEL":
            # get rid of the message data
            self.__peek(struct.calcsize(b'!II') + 6)
            return True
        else:
            return False
    
    def run(self):
        """
        Public method implementing the main loop of the client.
        """
        try:
            while True:
                header = self.__receive(struct.calcsize(b'!II'))
                # Leave main loop if connection was closed.
                if not header:
                    break
                
                length, datahash = struct.unpack(b'!II', header)
                messageType = self.__receive(6)
                packedData = self.__receive(length)
                
                if messageType != b"JOB   ":
                    continue
                
                assert adler32(packedData) & 0xffffffff == datahash, \
                    'Hashes not equal'
                if sys.version_info[0] == 3:
                    packedData = packedData.decode('utf-8')
                
                fx, fn, data = json.loads(packedData)
                if fx == 'INIT':
                    ret = self.__initClientService(fn, *data)
                elif fx.startswith("batch_"):
                    callback = self.batchServices.get(fx)
                    if callback:
                        callback(data, self.__send, fx, self.__cancelled)
                        ret = "__DONE__"
                    else:
                        ret = 'Unknown batch service.'
                else:
                    callback = self.services.get(fx)
                    if callback:
                        ret = callback(fn, *data)
                    else:
                        ret = 'Unknown service.'
                
                self.__send(fx, fn, ret)
        except:
            exctype, excval, exctb = sys.exc_info()
            tbinfofile = io.StringIO()
            traceback.print_tb(exctb, None, tbinfofile)
            tbinfofile.seek(0)
            tbinfo = tbinfofile.read()
            del exctb
            self.__send(
                'EXCEPTION', '?', [str(exctype), str(excval), tbinfo])

        # Give time to process latest response on server side
        time.sleep(0.5)
        self.connection.shutdown(socket.SHUT_RDWR)
        self.connection.close()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Host and port parameters are missing. Abort.')
        sys.exit(1)
    
    host, port = sys.argv[1:]
    backgroundClient = BackgroundClient(host, int(port))
    # Start the main loop
    backgroundClient.run()
