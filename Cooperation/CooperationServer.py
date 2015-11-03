# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the cooperation server.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtNetwork import QTcpServer

from .Connection import Connection

import Preferences


class CooperationServer(QTcpServer):
    """
    Class implementing the cooperation server.
    
    @signal newConnection(connection) emitted after a new connection was
        received (Connection)
    """
    newConnection = pyqtSignal(Connection)
    
    def __init__(self, address, parent=None):
        """
        Constructor
        
        @param address address the server should listen on (QHostAddress)
        @param parent reference to the parent object (QObject)
        """
        super(CooperationServer, self).__init__(parent)
        
        self.__address = address
    
    def incomingConnection(self, socketDescriptor):
        """
        Public method handling an incoming connection.
        
        @param socketDescriptor native socket descriptor (integer)
        """
        connection = Connection(self)
        connection.setSocketDescriptor(socketDescriptor)
        self.newConnection.emit(connection)
    
    def startListening(self, port=-1, findFreePort=False):
        """
        Public method to start listening for new connections.
        
        @param port port to listen on (integer)
        @param findFreePort flag indicating to search for a free port
            depending on the configuration (boolean)
        @return tuple giving a flag indicating success (boolean) and
            the port the server listens on
        """
        res = self.listen(self.__address, port)
        if findFreePort and Preferences.getCooperation("TryOtherPorts"):
            endPort = port + Preferences.getCooperation("MaxPortsToTry")
            while not res and port < endPort:
                port += 1
                res = self.listen(self.__address, port)
        return res, port
