# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

=begin edoc
File implementing an asynchronous file like socket interface for the debugger.
=end

require 'socket'

require 'DebugProtocol'

def AsyncPendingWrite(file)
=begin edoc
Module function to check for data to be written.

@param file The file object to be checked (file)
@return Flag indicating if there is data wating (int)
=end
    begin
        pending = file.pendingWrite
    rescue
        pending = 0
    end
    return pending
end

class AsyncFile
=begin edoc
# Class wrapping a socket object with a file interface.
=end
    @@maxtries = 10
    @@maxbuffersize = 1024 * 1024 * 4
    
    def initialize(sock, mode, name)
=begin edoc
Constructor

@param sock the socket object being wrapped
@param mode mode of this file (string)
@param name name of this file (string)
=end
        
        # Initialise the attributes.
        @closed = false
        @sock = sock
        @mode = mode
        @name = name
        @nWriteErrors = 0

        @wpending = ''
    end

    def checkMode(mode)
=begin edoc
Private method to check the mode.

This method checks, if an operation is permitted according to
the mode of the file. If it is not, an IOError is raised.

@param mode the mode to be checked (string)
=end
        if mode != @mode
            raise IOError, '[Errno 9] Bad file descriptor'
        end
    end

    def nWrite(n)
=begin edoc
Private method to write a specific number of pending bytes.

@param n the number of bytes to be written (int)
=end
        if n > 0
            begin
                buf = "%s%s" % [@wpending[0...n], EOT]
                sent = @sock.send(buf, 0)
                if sent > n
                    sent -= EOT.length
                end
                @wpending = @wpending[sent..-1]
                @nWriteErrors = 0
            rescue IOError
                @nWriteErrors += 1
                if @nWriteErrors > self.maxtries
                    raise
                    # assume that an error that occurs 10 times wont go away
                end
            end
        end
    end

    def pendingWrite
=begin edoc
Public method that returns the number of bytes waiting to be written.

@return the number of bytes to be written (int)
=end
        ind = @wpending.rindex("\n")
        if ind
            return ind + 1
        else
            return 0
        end
    end

    def close
=begin edoc
Public method to close the file.
=end
        if not @closed
            flush()
            begin
                @sock.close()
            rescue IOError
            end
            @closed = true
        end
    end
    
    def flush
=begin edoc
Public method to write all pending bytes.
=end
        nWrite(@wpending.length)
    end
    
    def isatty
=begin edoc
Public method to indicate whether a tty interface is supported.

@return always false
=end
        return false
    end
    
    def fileno
=begin edoc
Public method returning the file number.

@return file number (int)
=end
        return @sock.fileno()
    end
    
    def getSock
=begin edoc
Public method to get the socket object.

@return the socket object
=end
        return @sock
    end
    
    def read(size = -1)
=begin edoc
Public method to read bytes from this file.

@param size maximum number of bytes to be read (int)
@return the bytes read (any)
=end
        checkMode('r')

        if size < 0
            size = 20000
        end

        return @sock.recv(size)
    end
    
    def readline(size = -1)
=begin edoc
Public method to read a line from this file.

<b>Note</b>: This method will not block and may return
only a part of a line if that is all that is available.

@param size maximum number of bytes to be read (int)
@return one line of text up to size bytes (string)
=end
        checkMode('r')

        if size < 0
            size = 20000
        end

        # The integration of the debugger client event loop and the connection
        # to the debugger relies on the two lines of the debugger command being
        # delivered as two separate events.  Therefore we make sure we only
        # read a line at a time.
        line = @sock.recv(size, Socket::MSG_PEEK)

        eol = line.index("\n")

        if eol and eol >= 0
            size = eol + 1
        else
            size = line.length
        end

        # Now we know how big the line is, read it for real.
        return @sock.recv(size)
    end
    
    def readlines(sizehint = -1)
=begin edoc
Public method to read all lines from this file.

@param sizehint hint of the numbers of bytes to be read (int)
@return list of lines read (list of strings)
=end
        lines = []
        room = sizehint

        line = readline(room)
        linelen = line.length

        while linelen > 0
            lines << line

            if sizehint >= 0
                room = room - linelen

                if room <= 0
                    break
                end
            end

            line = readline(room)
            linelen = line.length
        end

        return lines
    end
    
    def gets()
=begin edoc
 Public method to read a line from this file.
=end
        readline()
    end

   def seek(offset, whence=IO::SEEK_SET)
=begin edoc
Public method to move the filepointer.

@exception IOError This method is not supported and always raises an
       IOError.
=end
        raise IOError, '[Errno 29] Illegal seek'
    end
    
    def tell
=begin edoc
Public method to get the filepointer position.

@exception IOError This method is not supported and always raises an
      IOError.
=end
        raise IOError, '[Errno 29] Illegal seek'
    end

    def <<(s)
=begin edoc
Synonym for write(s).

@param s bytes to be written (string)
=end
        write(s)
    end

    def write(s)
=begin edoc
Public method to write a string to the file.

@param s bytes to be written (string)
=end
        checkMode("w")
        tries = 0
        s = s.to_s
        if @wpending.length == 0
            @wpending = s.dup
        elsif @wpending.length + s.length > @@maxbuffersize
            # flush wpending if too big
            while @wpending.length > 0
                # if we have a persistent error in sending the data, an
                # exception will be raised in nWrite
                flush
                tries += 1
                if tries > @@maxtries
                    raise IOError, "Too many attempts to send data"
                end
            end
            @wpending = s.dup
        else
            @wpending << s
        end
        nWrite(pendingWrite())
    end

    def writelines(list)
=begin edoc
Public method to write a list of strings to the file.

@param list the list to be written (list of string)
=end
        list.each do |s|
            write(s)
        end
    end
end
