# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

=begin edoc
File implementing a debug client.
=end

# insert path to ourself in front of the search path
$:.insert(0, File.dirname($0))

require 'Debuggee'
require 'AsyncIO'
require 'DebugClientBaseModule'

class DebugClient
=begin edoc
Class implementing the client side of the debugger.
=end
    include AsyncIO
    include DebugClientBase
    
    def initialize
=begin edoc
Constructor
=end
        initializeAsyncIO
        initializeDebugClient
        
        @variant = "No Qt-Version"
    end
end

# We are normally called by the debugger to execute directly

if __FILE__ == $0
    debugClient = DebugClient.new()
    debugClient.main()
end
