# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

=begin edoc
File implementing an asynchronous interface for the debugger.
=end

module AsyncIO
=begin edoc
Module implementing asynchronous reading and writing.
=end
    def initializeAsyncIO
=begin edoc
Function to initialize the module.
=end
        disconnect()
    end
    
    def disconnect
=begin edoc
Function to disconnect any current connection.
=end
        @readfd = nil
        @writefd = nil
    end
    
    def setDescriptors(rfd, wfd)
=begin edoc
Function called to set the descriptors for the connection.

@param fd file descriptor of the input file (int)
@param wfd file descriptor of the output file (int)
=end
        @rbuf = ''
        @readfd = rfd

        @wbuf = ''
        @writefd = wfd
    end
    
    def readReady(fd)
=begin edoc
Function called when there is data ready to be read.

@param fd file descriptor of the file that has data to be read (int)
=end
        begin
            got = @readfd.readline()
        rescue
            return
        end
        
        if got.length == 0
            sessionClose()
            return
        end
        
        @rbuf << got
        
        # Call handleLine for the line if it is complete.
        eol = @rbuf.index("\n")
        
        while eol and eol >= 0
            s = @rbuf[0..eol]
            @rbuf = @rbuf[eol+1..-1]
            handleLine(s)
            eol = @rbuf.index("\n")
        end
    end
    
    def writeReady(fd)
=begin edoc
Function called when we are ready to write data.

@param fd file descriptor of the file that has data to be written (int)
=end
        @writefd.write(@wbuf)
        @writefd.flush()
        @wbuf = ''
    end
    
    def write(s)
=begin edoc
Function to write a string.

@param s the data to be written (string)
=end
        @wbuf << s
    end
end
