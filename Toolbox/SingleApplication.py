# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the single application server and client.
"""

from __future__ import unicode_literals

from PyQt5.QtNetwork import QLocalServer, QLocalSocket


class SingleApplicationServer(QLocalServer):
    """
    Class implementing the single application server base class.
    """
    def __init__(self, name):
        """
        Constructor
        
        @param name name this server is listening to (string)
        """
        super(SingleApplicationServer, self).__init__()
        
        res = self.listen(name)
        if not res:
            # maybe it crashed last time
            self.removeServer(name)
            self.listen(name)
        
        self.newConnection.connect(self.__newConnection)

        self.qsock = None

    def __newConnection(self):
        """
        Private slot to handle a new connection.
        """
        sock = self.nextPendingConnection()

        # If we already have a connection, refuse this one.  It will be closed
        # automatically.
        if self.qsock is not None:
            return

        self.qsock = sock

        self.qsock.readyRead.connect(self.__parseLine)
        self.qsock.disconnected.connect(self.__disconnected)

    def __parseLine(self):
        """
        Private method to handle data from the client.
        """
        while self.qsock and self.qsock.canReadLine():
            line = bytes(self.qsock.readLine()).decode()
            
##            print(line)          ##debug
            
            eoc = line.find('<') + 1
            
            boc = line.find('>')
            if boc >= 0 and eoc > boc:
                # handle the command sent by the client.
                cmd = line[boc:eoc]
                params = line[eoc:-1]
                
                self.handleCommand(cmd, params)
    
    def __disconnected(self):
        """
        Private method to handle the closure of the socket.
        """
        self.qsock = None
    
    def shutdown(self):
        """
        Public method used to shut down the server.
        """
        if self.qsock is not None:
            self.qsock.readyRead.disconnect(self.__parseLine)
            self.qsock.disconnected.disconnect(self.__disconnected)
        
        self.qsock = None
        
        self.close()

    def handleCommand(self, cmd, params):
        """
        Public slot to handle the command sent by the client.
        
        <b>Note</b>: This method must be overridden by subclasses.
        
        @param cmd commandstring (string)
        @param params parameterstring (string)
        @exception RuntimeError raised to indicate that this method must be
            implemented by a subclass
        """
        raise RuntimeError("'handleCommand' must be overridden")


class SingleApplicationClient(object):
    """
    Class implementing the single application client base class.
    """
    def __init__(self, name):
        """
        Constructor
        
        @param name name of the local server to connect to (string)
        """
        self.name = name
        self.connected = False
        
    def connect(self):
        """
        Public method to connect the single application client to its server.
        
        @return value indicating success or an error number. Value is one of:
            <table>
                <tr><td>0</td><td>No application is running</td></tr>
                <tr><td>1</td><td>Application is already running</td></tr>
            </table>
        """
        self.sock = QLocalSocket()
        self.sock.connectToServer(self.name)
        if self.sock.waitForConnected(10000):
            self.connected = True
            return 1
        else:
            err = self.sock.error()
            if err == QLocalSocket.ServerNotFoundError:
                return 0
            else:
                return -err
        
    def disconnect(self):
        """
        Public method to disconnect from the Single Appliocation server.
        """
        self.sock.disconnectFromServer()
        self.connected = False
    
    def processArgs(self, args):
        """
        Public method to process the command line args passed to the UI.
        
        <b>Note</b>: This method must be overridden by subclasses.
        
        @param args command line args (list of strings)
        @exception RuntimeError raised to indicate that this method must be
            implemented by a subclass
        """
        raise RuntimeError("'processArgs' must be overridden")
    
    def sendCommand(self, cmd):
        """
        Public method to send the command to the application server.
        
        @param cmd command to be sent (string)
        """
        if self.connected:
            self.sock.write(cmd)
            self.sock.flush()
        
    def errstr(self):
        """
        Public method to return a meaningful error string for the last error.
        
        @return error string for the last error (string)
        """
        return self.sock.errorString()
