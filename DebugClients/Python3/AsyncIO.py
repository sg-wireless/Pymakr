# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a base class of an asynchronous interface for the debugger.
"""


class AsyncIO(object):
    """
    Class implementing asynchronous reading and writing.
    """
    def __init__(self):
        """
        Constructor
        """
        # There is no connection yet.
        self.disconnect()

    def disconnect(self):
        """
        Public method to disconnect any current connection.
        """
        self.readfd = None
        self.writefd = None

    def setDescriptors(self, rfd, wfd):
        """
        Public method called to set the descriptors for the connection.
        
        @param rfd file descriptor of the input file (int)
        @param wfd file descriptor of the output file (int)
        """
        self.rbuf = ''
        self.readfd = rfd

        self.wbuf = ''
        self.writefd = wfd

    def readReady(self, fd):
        """
        Public method called when there is data ready to be read.
        
        @param fd file descriptor of the file that has data to be read (int)
        """
        try:
            got = self.readfd.readline_p()
        except Exception:
            return

        if len(got) == 0:
            self.sessionClose()
            return

        self.rbuf = self.rbuf + got

        # Call handleLine for the line if it is complete.
        eol = self.rbuf.find('\n')

        while eol >= 0:
            s = self.rbuf[:eol + 1]
            self.rbuf = self.rbuf[eol + 1:]
            self.handleLine(s)
            eol = self.rbuf.find('\n')

    def writeReady(self, fd):
        """
        Public method called when we are ready to write data.
        
        @param fd file descriptor of the file that has data to be written (int)
        """
        self.writefd.write(self.wbuf)
        self.writefd.flush()
        self.wbuf = ''

    def write(self, s):
        """
        Public method to write a string.
        
        @param s the data to be written (string)
        """
        self.wbuf = self.wbuf + s
