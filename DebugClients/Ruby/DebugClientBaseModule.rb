# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

=begin edoc
File implementing a debug client base module.
=end

require 'socket'

require 'DebugQuit'
require 'DebugProtocol'
require 'DebugClientCapabilities'
require 'AsyncFile'
require 'Config'
require 'Completer'

$DebugClientInstance = nil
$debugging = false

module DebugClientBase
=begin edoc
Module implementing the client side of the debugger.

It provides access to the Ruby interpeter from a debugger running in another
process.

The protocol between the debugger and the client assumes that there will be
a single source of debugger commands and a single source of Ruby
statements.  Commands and statement are always exactly one line and may be
interspersed.

The protocol is as follows.  First the client opens a connection to the
debugger and then sends a series of one line commands.  A command is either
&gt;Load&lt;, &gt;Step&lt;, &gt;StepInto&lt;, ... or a Ruby statement. 
See DebugProtocol.rb for a listing of valid protocol tokens.

A Ruby statement consists of the statement to execute, followed (in a
separate line) by &gt;OK?&lt;.  If the statement was incomplete then the response
is &gt;Continue&lt;.  If there was an exception then the response is &gt;Exception&lt;.
Otherwise the response is &gt;OK&lt;.  The reason for the &gt;OK?&lt; part is to
provide a sentinal (ie. the responding &gt;OK&lt;) after any possible output as a
result of executing the command.

The client may send any other lines at any other time which should be
interpreted as program output.

If the debugger closes the session there is no response from the client.
The client may close the session at any time as a result of the script
being debugged closing or crashing.

<b>Note</b>: This module is meant to be mixed in by individual DebugClient classes.
Do not use it directly.
=end
    @@clientCapabilities = HasDebugger | HasInterpreter | HasShell | HasCompleter
    
    attr_accessor :passive, :traceRuby
    
    def initializeDebugClient
=begin edoc
Method to initialize the module
=end
        
        # The context to run the debugged program in.
        @debugBinding = eval("def e4dc_DebugBinding; binding; end; e4dc_DebugBinding",
              TOPLEVEL_BINDING, 
              __FILE__,
              __LINE__ - 3)

        # The context to run the shell commands in.
        @shellBinding = eval("def e4dc_ShellBinding; binding; end; e4dc_ShellBinding",
              TOPLEVEL_BINDING, 
              __FILE__,
              __LINE__ - 3)
        
        # stack frames
        @frames = []
        @framenr = 0

        # The list of complete lines to execute.
        @buffer = ''
        @lineno = 0
        
        # The list of regexp objects to filter variables against
        @globalsFilterObjects = []
        @localsFilterObjects = []

        @pendingResponse = ResponseOK
        @mainProcStr = nil          # used for the passive mode
        @passive = false            # used to indicate the passive mode
        @running = nil

        @readstream = nil
        @writestream = nil
        @errorstream = nil
        
        @variant = 'You should not see this'
        
        @completer = Completer.new(@shellBinding)
    end
    
    def handleException
=begin edoc
Private method called in the case of an exception

It ensures that the debug server is informed of the raised exception.
=end
        @pendingResponse = ResponseException
    end
    
    def sessionClose
=begin edoc
Privat method to close the session with the debugger and terminate.
=end
        set_trace_func nil
        if $debugging
            $debugging = false
            @running = nil
            DEBUGGER__.context(DEBUGGER__.last_thread).step_quit()
        end
        
        # clean up asyncio
        disconnect()
        
        # make sure we close down our end of the socket
        # might be overkill as normally stdin, stdout and stderr
        # SHOULD be closed on exit, but it does not hurt to do it here
        @readstream.close()
        @writestream.close()
        @errorstream.close()
        
        # Ok, go away.
        exit()
    end
    
    def unhandled_exception(exc)
=begin edoc
Private method to report an unhandled exception.

@param exc the exception object
=end
        if SystemExit === exc
            if $debugging
                $debugging = false
            else
                progTerminated(exc.status)
            end
            return
        end
        
        # split the exception message
        msgParts = exc.message.split(":", 3)
        filename = File.expand_path(msgParts[0])
        linenr = msgParts[1].to_i
        
        if ScriptError === exc
            msgParts = msgParts[2].split(":", 3)
            filename = msgParts[0].sub(/in `require'/, "")
            linenr = msgParts[1].to_i
            exclist = [""]
            exclist << [filename, linenr, 0]
            write("%s%s\n" % [ResponseSyntax, exclist.inspect])
            return
        end
        
        exclist = ["unhandled %s" % exc.class, msgParts[2].sub(/in /, "")]
        exclist << [filename, linenr]
        
        # process the traceback
        frList = exc.backtrace
        frList.each do |frame|
            next if frame =~ /DebugClientBaseModule/
            break if frame =~ /\(eval\)/
            frameParts = frame.split(":", 3)
            filename = File.expand_path(frameParts[0])
            linenr = frameParts[1].to_i
            next if [filename, linenr] == exclist[-1]
            exclist << [filename, linenr]
        end
        
        write("%s%s\n" % [ResponseException, exclist.inspect])
    end
    
    def handleLine(line)
=begin edoc
Private method to handle the receipt of a complete line.

It first looks for a valid protocol token at the start of the line. Thereafter
it trys to execute the lines accumulated so far.

@param line the received line
=end
        
        # Remove any newline
        if line[-1] == "\n"
            line = line[0...-1]
        end
        
##        STDOUT << line << "\n"          ## debug
        
        eoc = line.index("<")
        
        if eoc and eoc >= 0 and line[0,1] == ">"
            # Get the command part and any argument
            cmd = line[0..eoc]
            arg = line[eoc+1..-1]
            
            case cmd
            when RequestOK
                write(@pendingResponse + "\n")
                @pendingResponse = ResponseOK
                return
            
            when RequestEnv
                # convert a Python stringified hash to a Ruby stringified hash
                arg.gsub!(/: u/, "=>")
                arg.gsub!(/u'/, "'")
                eval(arg).each do |key, value|
                    if key[-1..-1] == "+"
                        key = key[0..-2]
                        if ENV[key]
                            ENV[key] += value
                        else
                            ENV[key] = value
                        end
                    else
                        ENV[key] = value
                    end
                end
                return
            
            when RequestVariables
                frmnr, scope, filter = eval("[%s]" % arg.gsub(/u'/, "'").gsub(/u"/,'"'))
                dumpVariables(frmnr.to_i, scope.to_i, filter)
                return
            
            when RequestVariable
                var, frmnr, scope, filter = \
                    eval("[%s]" % arg.gsub(/u'/, "'").gsub(/u"/,'"'))
                dumpVariable(var, frmnr.to_i, scope.to_i, filter)
                return
                
            when RequestStep
                DEBUGGER__.context(DEBUGGER__.last_thread).stop_next()
                @eventExit = true
                return
            
            when RequestStepOver
                DEBUGGER__.context(DEBUGGER__.last_thread).step_over()
                @eventExit = true
                return
            
            when RequestStepOut
                DEBUGGER__.context(DEBUGGER__.last_thread).step_out()
                @eventExit = true
                return
            
            when RequestStepQuit
                set_trace_func nil
                wasDebugging = $debugging
                $debugging = false
                @running = nil
                if @passive
                    progTerminated(42)
                else
                    DEBUGGER__.context(DEBUGGER__.last_thread).step_quit() if wasDebugging
                end
                return
            
            when RequestContinue
                special = arg.to_i
                if special == 0
                    DEBUGGER__.context(DEBUGGER__.last_thread).step_continue()
                else
                    # special == 1 means a continue while doing a step over
                    # this occurs when an expception is raised doing a step over
                    DEBUGGER__.context(DEBUGGER__.last_thread).step_over()
                end
                @eventExit = true
                return
            
            when RequestSetFilter
                scope, filterString = eval("[%s]" % arg)
                generateFilterObjects(scope.to_i, filterString)
                return
            
            when RequestLoad
                $debugging = true
                ARGV.clear()
                wd, fn, args, traceRuby = arg.split("|", -4)
                @traceRuby = traceRuby.to_i == 1 ? true : false
                ARGV.concat(eval(args.gsub(/u'/, "'").gsub(/u"/,'"')))
                $:.insert(0, File.dirname(fn))
                if wd == ''
                    Dir.chdir($:[0])
                else
                    Dir.chdir(wd)
                end
                @running = fn
                command = "$0 = '%s'; require '%s'" % [fn, fn]
                RubyVM::InstructionSequence.compile_option = {
                    trace_instruction: true
                }
                set_trace_func proc { |event, file, line, id, binding_, klass, *rest|
                    DEBUGGER__.context.trace_func(event, file, line, id, binding_, klass)
                }
                begin
                    eval(command, @debugBinding)
                rescue DebugQuit
                    # just ignore it
                rescue Exception => exc
                    unhandled_exception(exc)
                ensure
                    set_trace_func(nil)
                    @running = nil
                end
                return
            
            when RequestRun
                $debugging = false
                ARGV.clear()
                wd, fn, args = arg.split("|", -3)
                ARGV.concat(eval(args.gsub(/u'/, "'").gsub(/u"/,'"')))
                $:.insert(0, File.dirname(fn))
                if wd == ''
                    Dir.chdir($:[0])
                else
                    Dir.chdir(wd)
                end
                command = "$0 = '%s'; require '%s'" % [fn, fn]
                @frames = []
                set_trace_func proc { |event, file, line, id, binding_, klass, *rest|
                    trace_func(event, file, line, id, binding_, klass)
                }
                begin
                    eval(command, @debugBinding)
                rescue SystemExit
                    # ignore it
                rescue Exception => exc
                    unhandled_exception(exc)
                ensure
                    set_trace_func(nil)
                end
                return
            
            when RequestShutdown
                sessionClose()
                return
            
            when RequestBreak
                fn, line, temporary, set, cond = arg.split("@@")
                line = line.to_i
                set = set.to_i
                temporary = temporary.to_i == 1 ? true : false
                
                if set == 1
                    if cond == 'None'
                        cond = nil
                    end
                    DEBUGGER__.context(DEBUGGER__.last_thread)\
                        .add_break_point(fn, line, temporary, cond)
                else
                    DEBUGGER__.context(DEBUGGER__.last_thread)\
                        .delete_break_point(fn, line)
                end
                return
            
            when RequestBreakEnable
                fn, line, enable = arg.split(',')
                line = line.to_i
                enable = enable.to_i == 1 ? true : false
                DEBUGGER__.context(DEBUGGER__.last_thread)\
                    .enable_break_point(fn, line, enable)
                return
            
            when RequestBreakIgnore
                fn, line, count = arg.split(',')
                line = line.to_i
                count = count.to_i
                DEBUGGER__.context(DEBUGGER__.last_thread)\
                    .ignore_break_point(fn, line, count)
                return
            
            when RequestWatch
                cond, temporary, set = arg.split('@@')
                set = set.to_i
                temporary = temporary.to_i == 1 ? true : false
                
                if set == 1
                    DEBUGGER__.context(DEBUGGER__.last_thread)\
                        .add_watch_point(cond, temporary)
                else
                    DEBUGGER__.context(DEBUGGER__.last_thread).delete_watch_point(cond)
                end
                return
                
            when RequestWatchEnable
                cond, enable = arg.split(',')
                enable = enable.to_i == 1 ? true : false
                DEBUGGER__.context(DEBUGGER__.last_thread)\
                    .enable_watch_point(cond, enable)
                return
                
            when RequestWatchIgnore
                cond, count = arg.split(',')
                count = count.to_i
                DEBUGGER__.context(DEBUGGER__.last_thread).ignore_watch_point(cond, count)
                return
                
            when RequestEval, RequestExec
                if not @running                
                    binding_ = @shellBinding
                else
                    binding_ = DEBUGGER__.context(DEBUGGER__.last_thread).current_binding
                end
                write("\n")
                begin
                    value = eval(arg, binding_)
                rescue Exception => exc
                    list = []
                    list << "%s: %s\n" % \
                        [exc.class, exc.to_s.sub(/stdin:\d+:(in `.*':?)?/, '')]
                    $@.each do |l|
                        break if l =~ /e4dc_ShellBinding/ or l =~ /e4dc_DebugBinding/ or \
                                 l =~ /:in `require'$/
                        list << "%s\n" % l.sub(/\(eval\)/, "(e3dc)")
                    end
                    list.each do |entry|
                        write(entry)
                    end
                else
                    write("=> #{value.inspect}\n")
                    write("#{ResponseOK}\n")
                end
                return
                
            when RequestBanner
                version = "ruby #{RUBY_VERSION} (#{RUBY_RELEASE_DATE}) [#{RUBY_PLATFORM}]"
                write("%s('%s','%s','%s')\n" % \
                    [ResponseBanner, version, Socket.gethostname(), @variant])
                return
            
            when RequestCapabilities
                write("%s%d, 'Ruby'\n" % \
                    [ResponseCapabilities, @@clientCapabilities])
                return
            
            when RequestCompletion
                completionList(arg)
                return
                
            else
                puts "Got unsupported command %s.\n" % cmd
                return
            end
        end
        
        if @buffer
            @buffer << "\n" << line
            @lineno += 1
        else
            @buffer = line.dup
        end
        
        # check for completeness
        if not canEval?
            @pendingResponse = ResponseContinue
        else
            command = @buffer.dup
            @buffer = ""
            begin
                res = "=> "
                if not @running
                    res << eval(command, @shellBinding, "stdin", @lineno).inspect << "\n"
                else
                    res << eval(command, 
                        DEBUGGER__.context(DEBUGGER__.last_thread).get_binding(@framenr), 
                        "stdin", @lineno).inspect << "\n"
                end
                write(res)
            rescue SystemExit => exc
                progTerminated(exc.status)
            rescue ScriptError, StandardError => exc
                list = []
                list << "%s: %s\n" % \
                    [exc.class, exc.to_s.sub(/stdin:\d+:(in `.*':?)?/, '')]
                $@.each do |l|
                    break if l =~ /e4dc_ShellBinding/ or l =~ /e4dc_DebugBinding/ or \
                             l =~ /:in `require'$/
                    list << "%s\n" % l.sub(/\(eval\)/, "(e3dc)")
                end
                list.each do |entry|
                    write(entry)
                end
                handleException()
            end
        end
    end
    
    def canEval?
=begin edoc
Private method to check if the buffer's contents can be evaluated.

@return flag indicating if an eval might succeed (boolean)
=end
        indent = 0
        if @buffer =~ /,\s*$/
            return false
        end
        
        @buffer.split($/).each do |l|
            if l =~ /^\s*(class|module|def|if|unless|case|while|until|for|begin)\b[^_]/
                indent += 1
            end
            if l =~ /\s*do\s*(\|.*\|)?\s*$/
                indent += 1
            end
            if l =~ /^\s*end\s*$|^\s*end\b[^_]/
                indent -= 1
            end
            if l =~ /\{\s*(\|.*\|)?\s*$/
                indent += 1
            end
            if l =~ /^\s*\}/
                indent -= 1
            end
        end
        
        if indent > 0
            return false
        end
        return true
    end
    
    def trace_func(event, file, line, id, binding_, klass)
=begin edoc
Method executed by the tracing facility.

It is used to save the execution context of an exception.

@param event the tracing event (String)
@param file the name of the file being traced (String)
@param line the line number being traced (int)
@param id object id
@param binding_ a binding object
@param klass name of a class
=end
        case event
        when 'line'
            if @frames[0]
                @frames[0] = binding_
            else
                @frames.unshift binding_
            end
            
        when 'call'
            @frames.unshift binding_
        
        when 'class'
            @frames.unshift binding_
            
        when 'return', 'end'
            @frames.shift

        when 'end'
            @frames.shift
        
        when 'raise'
            set_trace_func nil
        end
    end

    def write(s)
=begin edoc
Private method to write data to the output stream.

@param s data to be written (string)
=end
        @writestream.write(s)
        @writestream.flush()
    end
    
    def interact
=begin edoc
Private method to Interact with  the debugger.
=end
        setDescriptors(@readstream, @writestream)
        $DebugClientInstance = self
        
        if not @passive
            # At this point simulate an event loop.
            eventLoop()
        end
    end
    
    def eventLoop
=begin edoc
Private method implementing our event loop.
=end
        @eventExit = nil
        
        while @eventExit == nil
            wrdy = []
            
            if AsyncPendingWrite(@writestream) > 0
                wrdy << @writestream.getSock()
            end
            
            if AsyncPendingWrite(@errorstream) > 0
                wrdy << @errorstream.getSock()
            end
            
            rrdy, wrdy, xrdy = select([@readstream.getSock()], wrdy, [])
            
            if rrdy.include?(@readstream.getSock())
                readReady(@readstream.fileno())
            end
            
            if wrdy.include?(@writestream.getSock())
                writeReady(@writestream.fileno())
            end
            
            if wrdy.include?(@errorstream.getSock())
                writeReady(@errorstream.fileno())
            end
        end
        
        @eventExit = nil
    end
    
    def eventPoll
=begin edoc
Private method to poll for events like 'set break point'.
=end
        
        # the choice of a ~0.5 second poll interval is arbitrary.
        lasteventpolltime = @lasteventpolltime ? @lasteventpolltime : Time.now
        now = Time.now
        if now - lasteventpolltime < 0.5
            @lasteventpolltime = lasteventpolltime
            return
        else
            @lasteventpolltime = now
        end
        
        wrdy = []
        
        if AsyncPendingWrite(@writestream) > 0
            wrdy << @writestream.getSock()
        end
        
        if AsyncPendingWrite(@errorstream) > 0
            wrdy << @errorstream.getSock()
        end
        
        rrdy, wrdy, xrdy = select([@readstream.getSock()], wrdy, [], 0)
        
        if rrdy == nil
            return
        end
        
        if rrdy.include?(@readstream.getSock())
            readReady(@readstream.fileno())
        end
        
        if wrdy.include?(@writestream.getSock())
            writeReady(@writestream.fileno())
        end
        
        if wrdy.include?(@errorstream.getSock())
            writeReady(@errorstream.fileno())
        end
    end
    
    def connectDebugger(port, remoteAddress=nil, redirect=true)
=begin edoc
Public method to establish a session with the debugger. 

It opens a network connection to the debugger, connects it to stdin, 
stdout and stderr and saves these file objects in case the application
being debugged redirects them itself.

@param port the port number to connect to (int)
@param remoteAddress the network address of the debug server host (string)
@param redirect flag indicating redirection of stdin, stdout and stderr (boolean)
=end
        if remoteAddress == nil
            sock = TCPSocket.new(DebugAddress, port)
        else
            if remoteAddress =~ /@@i/
                remoteAddress, interface = remoteAddress.split("@@i")
            else
                interface = 0
            end
            if remoteAddress.downcase =~ /^fe80/
                remoteAddress = "%s%%%s" % [remoteAddress, interface]
            end
            sock = TCPSocket.new(remoteAddress, port)
        end
        
        @readstream = AsyncFile.new(sock, "r", "stdin")
        @writestream = AsyncFile.new(sock, "w", "stdout")
        @errorstream = AsyncFile.new(sock, "w", "stderr")
        
        if redirect
            $stdin = @readstream
            $stdout = @writestream
            $stderr = @errorstream
        end
    end
    
    def progTerminated(status)
=begin edoc
Private method to tell the debugger that the program has terminated.

@param status the return status
=end
        if status == nil
            status = 0
        else
            begin
                Integer(status)
            rescue
                status = 1
            end
        end
        
        set_trace_func(nil)
        @running = nil
        write("%s%d\n" % [ResponseExit, status])
    end
    
    def dumpVariables(frmnr, scope, filter)
=begin edoc
Private method to return the variables of a frame to the debug server.

@param frmnr distance of frame reported on. 0 is the current frame (int)
@param scope 1 to report global variables, 0 for local variables (int)
@param filter the indices of variable types to be filtered (list of int)
=end
        if $debugging
            if scope == 0
                @framenr = frmnr
            end
            binding_, file, line, id = DEBUGGER__.context(DEBUGGER__.last_thread)\
                .get_frame(frmnr)
        else
            binding_ = @frames[frmnr]
        end
        varlist = [scope]
        if scope >= 1
            # dump global variables
            vlist = formatVariablesList(global_variables, binding_, scope, filter)
        elsif scope == 0
            # dump local variables
            vlist = formatVariablesList(eval("local_variables", binding_), 
                                        binding_, scope, filter)
        end
        varlist.concat(vlist)
        write("%s%s\n" % [ResponseVariables, varlist.inspect])
    end
    
    def dumpVariable(var, frmnr, scope, filter)
=begin edoc
Private method to return the variables of a frame to the debug server.

@param var list encoded name of the requested variable (list of strings)
@param frmnr distance of frame reported on. 0 is the current frame (int)
@param scope 1 to report global variables, 0 for local variables (int)
@param filter the indices of variable types to be filtered (list of int)
=end
       if $debugging
            binding_, file, line, id = DEBUGGER__.context(DEBUGGER__.last_thread)\
                .get_frame(frmnr)
        else
            binding_ = @frames[frmnr]
        end
        varlist = [scope, var]
        i = 0
        obj = nil
        keylist = nil
        formatSequences = false
        access = ""
        isDict = false
        
        while i < var.length
            if ["[]", "{}"].include?(var[i][-2..-1])
                if i+1 == var.length
                    keylist = [var[i][0..-3]]
                    formatSequences = true
                    if access.length == 0
                        access = "#{var[i][0..-3]}"
                    else
                        access << "[#{var[i][0..-3]}]"
                    end
                    if var[i][-2..-1] == "{}"
                        isDict = true
                    end
                    break
                else
                    if access.length == 0
                        access = "#{var[i][0..-3]}"
                    else
                        access << "[#{var[i][0..-3]}]"
                    end
                end
            else
                if access.length != 0
                    access << "[#{var[i]}]"
                    obj = eval(access, binding_)
                    binding_ = obj.instance_eval{binding()}
                    access = ""
                else
                    obj = eval(var[i], binding_)
                    binding_ = obj.instance_eval{binding()}
                end
            end
            i += 1
        end
        if formatSequences
            bind = binding_
        else
            bind = obj.instance_eval{binding()}
        end
        if not keylist
            keylist = obj.instance_variables
            access = nil
        else
            if access.length != 0
                obj = eval(access, bind)
            end
            if isDict
                keylist = obj.keys()
            else
                keylist = Array.new(obj.length){|i| i}
            end
        end
        vlist = formatVariablesList(keylist, bind, scope, filter, 
                                    excludeSelf=true, access=access)
        varlist.concat(vlist)
        write("%s%s\n" % [ResponseVariable, varlist.inspect])
    end
    
    def formatVariablesList(keylist, binding_, scope, filter = [],
                            excludeSelf = false, access = nil)
=begin edoc
Private method to produce a formated variables list.

The binding passed in to it is scanned. Variables are
only added to the list, if their type is not contained 
in the filter list and their name doesn't match any of the filter expressions.
The formated variables list (a list of lists of 3 values) is returned.

@param keylist keys of the dictionary
@param binding_ the binding to be scanned
@param scope 1 to filter using the globals filter, 0 using the locals filter (int).
    Variables are only added to the list, if their name do not match any of the
    filter expressions.
@param filter the indices of variable types to be filtered. Variables are
    only added to the list, if their type is not contained in the filter 
    list.
@param excludeSelf flag indicating if the self object should be excluded from
    the listing (boolean)
@param access String specifying the access path to (String)
@return A list consisting of a list of formatted variables. Each variable
    entry is a list of three elements, the variable name, its type and 
    value.
=end
        varlist = []
        if scope >= 1
            patternFilterObjects = @globalsFilterObjects
        else
            patternFilterObjects = @localsFilterObjects
            begin
                obj = eval("self", binding_)
            rescue StandardError, ScriptError
                obj = nil
            end
            if not excludeSelf and obj.class != Object
                keylist << "self"
            end
        end
        
        keylist.each do |key|
            # filter based on the filter pattern
            matched = false
            patternFilterObjects.each do |pat|
                if pat.match(key)
                    matched = true
                    break
                end
            end
            next if matched
            
            if key.to_s == '$KCODE' or key.to_s == '$=' or key.to_s == '$-K'
                varlist << [key.to_s, "NilClass", "nil"]
                next
            end
        
            begin
                if access
                    if key.to_s == key
                        key = "'%s'" % key
                    else
                        key = key.to_s
                    end
                    k = "#{access}[%s]" % key
                    obj = eval(k, binding_)
                else
                    obj = eval(key.to_s, binding_)
                end
            rescue NameError
                next
            end
            
            if obj or obj.class == NilClass or obj.class == FalseClass
                otype = obj.class.to_s
                if obj.inspect.nil?
                    otype = ""
                    oval = ""
                else
                    oval = obj.inspect.gsub(/=>/,":")
                end
            else
                otype = ""
                oval = obj.inspect
            end
            
            next if inFilter?(filter, otype, oval)
            
            if oval.index("#<") == 0
                addr = extractAddress(oval)
                oval = "<#{otype} object at #{addr}>"
            end
            if obj
                if obj.class == Array or obj.class == Hash
                    oval = "%d" % obj.length()
                end
            end
            varlist << [key.to_s, otype, oval]
        end
        return varlist
    end
    
    def extractAddress(var)
=begin edoc
Private method to extract the address part of an object description.

@param var object description (String)
@return the address contained in the object description (String)
=end
        m = var.match(/^#<.*?:([^:]*?) /)
        if m
            return m[1]
        else
            return ""
        end
    end
    
    def extractTypeAndAddress(var)
=begin edoc
Private method to extract the address and type parts of an object description.

@param var object description (String)
@return list containing the type and address contained in the object 
    description (Array of two String)
=end
        m = var.match(/^#<(.*?):(.*?) /)
        if m
            return [m[1], m[2]]
        else
            return ["", ""]
        end
    end
    
    def inFilter?(filter, otype, oval)
=begin edoc
Private method to check, if a variable is to be filtered based on its type.

@param filter the indices of variable types to be filtered (Array of int.
@param otype type of the variable to be checked (String)
@param oval variable value to be checked (String)
@return flag indicating, whether the variable should be filtered (boolean)
=end
        cindex = ConfigVarTypeStrings.index(otype)
        if cindex == nil 
            if oval.index("#<") == 0 
                if filter.include?(ConfigVarTypeStrings.index("instance"))
                    return true
                else
                    return false
                end
            elsif ['FalseClass', 'TrueClass'].include?(otype)
                if filter.include?(ConfigVarTypeStrings.index("bool"))
                    return true
                else
                    return false
                end
            else
                if filter.include?(ConfigVarTypeStrings.index("other"))
                    return true
                else
                    return false
                end
            end
        end
        if filter.include?(cindex)
            return true
        end
        return false
    end
    
    def generateFilterObjects(scope, filterString)
=begin edoc
Private method to convert a filter string to a list of filter objects.

@param scope 1 to generate filter for global variables, 0 for local variables (int)
@param filterString string of filter patterns separated by ';'
=end
        patternFilterObjects = []
        for pattern in filterString.split(';')
            patternFilterObjects << Regexp.compile('^%s$' % pattern)
        end
        if scope == 1
            @globalsFilterObjects = patternFilterObjects[0..-1]
        else
            @localsFilterObjects = patternFilterObjects[0..-1]
        end
    end
    
    def completionList(text)
=begin edoc
Method used to handle the command completion request

@param text the text to be completed (string)
=end
        completions = @completer.complete(text).compact.sort.uniq
        write("%s%s||%s\n" % [ResponseCompletion, completions.inspect, text])
    end
    
    def startProgInDebugger(progargs, wd = '', host = nil, 
            port = nil, exceptions = true, traceRuby = false, redirect=true)
=begin edoc
Method used to start the remote debugger.

@param progargs commandline for the program to be debugged 
    (list of strings)
@param wd working directory for the program execution (string)
@param host hostname of the debug server (string)
@param port portnumber of the debug server (int)
@param exceptions flag to enable exception reporting of the IDE (boolean)
@param traceRuby flag to enable tracing into the Ruby library
@param redirect flag indicating redirection of stdin, stdout and stderr (boolean)
=end
        $debugging = true
        
        if host == nil
            host = ENV.fetch('ERICHOST', 'localhost')
        end
        if port == nil
            port = ENV.fetch('ERICPORT', 42424)
        end
        
        connectDebugger(port, host, redirect) #TCPSocket.gethostbyname(host)[3])
        DEBUGGER__.attach(self)
        
        @traceRuby = traceRuby
        
        fn = progargs.shift
        fn = File.expand_path(fn)
        
        ARGV.clear()
        ARGV.concat(progargs)
        $:.insert(0, File.dirname(fn))
        if wd == ''
            Dir.chdir($:[0])
        else
            Dir.chdir(wd)
        end
        @running = fn
        
        @passive = true
        write("%s%s|%d\n" % [PassiveStartup, @running, exceptions ? 1 : 0])
        interact()
        
        command = "$0 = '%s'; require '%s'" % [fn, fn]
        set_trace_func proc { |event, file, line, id, binding_, klass, *rest|
            DEBUGGER__.context.trace_func(event, file, line, id, binding_, klass)
        }
        begin
            eval(command, @debugBinding)
        rescue DebugQuit
            # just ignore it
        rescue Exception => exc
            unhandled_exception(exc)
        ensure
            set_trace_func(nil)
            @running = nil
        end
        # just a short delay because client might shut down too quickly otherwise
        sleep(1)    
    end
    
    def main
=begin edoc
Public method implementing the main method.
=end
        if ARGV.include?('--')
            args = ARGV[0..-1]
            host = nil
            port = nil
            wd = ''
            traceRuby = false
            exceptions = true
            redirect = true
            while args[0]
                if args[0] == '-h'
                    host = args[1]
                    args.shift
                    args.shift
                elsif args[0] == '-p'
                    port = args[1]
                    args.shift
                    args.shift
                elsif args[0] == '-w'
                    wd = args[1]
                    args.shift
                    args.shift
                elsif args[0] == '-t'
                    traceRuby = true
                    args.shift
                elsif args[0] == '-e'
                    exceptions = false
                    args.shift
                elsif args[0] == '-n'
                    redirect = false
                    args.shift
                elsif args[0] == '--'
                    args.shift
                    break
                else        # unknown option
                    args.shift
                end
            end
            if args.length == 0
                STDOUT << "No program given. Aborting!"
            else
                startProgInDebugger(args, wd, host, port, 
                                    exceptions = exceptions, traceRuby = traceRuby,
                                    redirect = redirect)
            end
        else
            if ARGV[0] == '--no-encoding'
                # just ignore it, it's here to be compatible with python debugger
                ARGV.shift
            end
            
            begin
                port = ARGV[0].to_i
            rescue
                port = -1
            end
            
            begin
                redirect = ARGV[1].to_i
                redirect = redirect == 1 ? true : false
            rescue
                redirect = true
            end
            
            begin
                remoteAddress = ARGV[2]
            rescue
                remoteAddress = nil
            end
            
            ARGV.clear()
            $:.insert(0,"")
            if port >= 0
                connectDebugger(port, remoteAddress, redirect)
                DEBUGGER__.attach(self)
                interact()
            end
        end
    end
end
