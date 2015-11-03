# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an asynchronous file like socket interface for the
debugger.
"""

import socket

from DebugProtocol import EOT


def AsyncPendingWrite(file):
    """
    Module function to check for data to be written.
    
    @param file The file object to be checked (file)
    @return Flag indicating if there is data wating (int)
    """
    try:
        pending = file.pendingWrite()
    except:
        pending = 0

    return pending


class AsyncFile(object):
    """
    Class wrapping a socket object with a file interface.
    """
    maxtries = 10
    maxbuffersize = 1024 * 1024 * 4
    
    def __init__(self, sock, mode, name):
        """
        Constructor
        
        @param sock the socket object being wrapped
        @param mode mode of this file (string)
        @param name name of this file (string)
        """
        # Initialise the attributes.
        self.closed = 0
        self.sock = sock
        self.mode = mode
        self.name = name
        self.nWriteErrors = 0
        self.encoding = "utf-8"

        self.wpending = u''

    def __checkMode(self, mode):
        """
        Private method to check the mode.
        
        This method checks, if an operation is permitted according to
        the mode of the file. If it is not, an IOError is raised.
        
        @param mode the mode to be checked (string)
        @exception IOError raised to indicate a bad file descriptor
        """
        if mode != self.mode:
            raise IOError('[Errno 9] Bad file descriptor')

    def __nWrite(self, n):
        """
        Private method to write a specific number of pending bytes.
        
        @param n the number of bytes to be written (int)
        """
        if n:
            try:
                buf = "%s%s" % (self.wpending[:n], EOT)
                try:
                    buf = buf.encode('utf-8')
                except (UnicodeEncodeError, UnicodeDecodeError):
                    pass
                self.sock.sendall(buf)
                self.wpending = self.wpending[n:]
                self.nWriteErrors = 0
            except socket.error:
                self.nWriteErrors += 1
                if self.nWriteErrors > self.maxtries:
                    self.wpending = u''  # delete all output

    def pendingWrite(self):
        """
        Public method that returns the number of bytes waiting to be written.
        
        @return the number of bytes to be written (int)
        """
        return self.wpending.rfind('\n') + 1

    def close(self, closeit=0):
        """
        Public method to close the file.
        
        @param closeit flag to indicate a close ordered by the debugger code
            (boolean)
        """
        if closeit and not self.closed:
            self.flush()
            self.sock.close()
            self.closed = 1

    def flush(self):
        """
        Public method to write all pending bytes.
        """
        self.__nWrite(len(self.wpending))

    def isatty(self):
        """
        Public method to indicate whether a tty interface is supported.
        
        @return always false
        """
        return 0

    def fileno(self):
        """
        Public method returning the file number.
        
        @return file number (int)
        """
        try:
            return self.sock.fileno()
        except socket.error:
            return -1

    def read_p(self, size=-1):
        """
        Public method to read bytes from this file.
        
        @param size maximum number of bytes to be read (int)
        @return the bytes read (any)
        """
        self.__checkMode('r')

        if size < 0:
            size = 20000

        return self.sock.recv(size).decode('utf8')

    def read(self, size=-1):
        """
        Public method to read bytes from this file.
        
        @param size maximum number of bytes to be read (int)
        @return the bytes read (any)
        """
        self.__checkMode('r')

        buf = raw_input()
        if size >= 0:
            buf = buf[:size]
        return buf

    def readline_p(self, size=-1):
        """
        Public method to read a line from this file.
        
        <b>Note</b>: This method will not block and may return
        only a part of a line if that is all that is available.
        
        @param size maximum number of bytes to be read (int)
        @return one line of text up to size bytes (string)
        """
        self.__checkMode('r')

        if size < 0:
            size = 20000

        # The integration of the debugger client event loop and the connection
        # to the debugger relies on the two lines of the debugger command being
        # delivered as two separate events.  Therefore we make sure we only
        # read a line at a time.
        line = self.sock.recv(size, socket.MSG_PEEK)

        eol = line.find('\n')

        if eol >= 0:
            size = eol + 1
        else:
            size = len(line)

        # Now we know how big the line is, read it for real.
        return self.sock.recv(size).decode('utf8')

    def readlines(self, sizehint=-1):
        """
        Public method to read all lines from this file.
        
        @param sizehint hint of the numbers of bytes to be read (int)
        @return list of lines read (list of strings)
        """
        self.__checkMode('r')

        lines = []
        room = sizehint

        line = self.readline_p(room)
        linelen = len(line)

        while linelen > 0:
            lines.append(line)

            if sizehint >= 0:
                room = room - linelen

                if room <= 0:
                    break

            line = self.readline_p(room)
            linelen = len(line)

        return lines

    def readline(self, sizehint=-1):
        """
        Public method to read one line from this file.
        
        @param sizehint hint of the numbers of bytes to be read (int)
        @return one line read (string)
        """
        self.__checkMode('r')

        line = raw_input() + '\n'
        if sizehint >= 0:
            line = line[:sizehint]
        return line
        
    def seek(self, offset, whence=0):
        """
        Public method to move the filepointer.
        
        @param offset offset to seek for
        @param whence where to seek from
        @exception IOError This method is not supported and always raises an
        IOError.
        """
        raise IOError('[Errno 29] Illegal seek')

    def tell(self):
        """
        Public method to get the filepointer position.
        
        @exception IOError This method is not supported and always raises an
        IOError.
        """
        raise IOError('[Errno 29] Illegal seek')

    def truncate(self, size=-1):
        """
        Public method to truncate the file.
        
        @param size size to truncate to (integer)
        @exception IOError This method is not supported and always raises an
        IOError.
        """
        raise IOError('[Errno 29] Illegal seek')

    def write(self, s):
        """
        Public method to write a string to the file.
        
        @param s bytes to be written (string)
        @exception socket.error raised to indicate too many send attempts
        """
        self.__checkMode('w')
        tries = 0
        if not self.wpending:
            self.wpending = s
        elif type(self.wpending) != type(s) or \
                len(self.wpending) + len(s) > self.maxbuffersize:
            # flush wpending so that different string types are not
            # concatenated
            while self.wpending:
                # if we have a persistent error in sending the data, an
                # exception will be raised in __nWrite
                self.flush()
                tries += 1
                if tries > self.maxtries:
                    raise socket.error("Too many attempts to send data")
            self.wpending = s
        else:
            self.wpending += s
        self.__nWrite(self.pendingWrite())

    def writelines(self, list):
        """
        Public method to write a list of strings to the file.
        
        @param list the list to be written (list of string)
        """
        map(self.write, list)

#
# eflag: FileType = Python2
