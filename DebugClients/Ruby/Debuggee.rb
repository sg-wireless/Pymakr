# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

# Debuggee.rb is based in parts on debug.rb from Ruby and debuggee.rb.
# Original copyrights of these files follow below.
#
# debug.rb
# Copyright (C) 2000  Network Applied Communication Laboratory, Inc.
# Copyright (C) 2000  Information-technology Promotion Agency, Japan
#
# debuggee.rb
# Copyright (c) 2000 NAKAMURA, Hiroshi

=begin edoc
File implementing the real debugger, which is connected to the IDE frontend.
=end

require 'continuation'

require 'DebugQuit'
require 'rbconfig'

class DEBUGGER__
=begin edoc
Class implementing the real debugger.
=end
    MUTEX = Mutex.new

    class Context
=begin edoc
Class defining the current execution context.
=end
        def initialize
=begin edoc
Constructor
=end
            if Thread.current == Thread.main
                @stop_next = 1
            else
                @stop_next = 0
            end
            @last_file = nil
            @file = nil
            @line = nil
            @no_step = nil
            @frames = []
            @frame_pos = 0 #LJ - for FR
            @finish_pos = 0
            @trace = false
            @catch = ["StandardError"] #LJ - for FR
            @suspend_next = false
        end

        def stop_next(n=1)
=begin edoc
Method to set the next stop point (i.e. stop at next line).

@param counter defining the stop point (int)
=end
            @stop_next = n
        end

        def step_over(n=1)
=begin edoc
Method to set the next stop point skipping function calls.

@param counter defining the stop point (int)
=end
            @stop_next = n
            @no_step = @frames.size - @frame_pos
        end
    
        def step_out
=begin edoc
Method to set the next stop point after the function call returns.
=end
            if @frame_pos != @frames.size
                @finish_pos = @frames.size - @frame_pos
                @frame_pos = 0
                @stop_next -= 1
            end
        end
    
        def step_continue
=begin edoc
Method to continue execution until next breakpoint or watch expression.
=end
            @stop_next = 1
            @no_step = -1
        end
    
        def step_quit
=begin edoc
Method to stop debugging.
=end
            raise DebugQuit.new
        end
    
        def set_suspend
=begin edoc
Method to suspend all threads.
=end
            @suspend_next = true
        end

        def clear_suspend
=begin edoc
Method to clear the suspend state.
=end
            @suspend_next = false
        end

        def suspend_all
=begin edoc
Method to suspend all threads.
=end
            DEBUGGER__.suspend
        end

        def resume_all
=begin edoc
Method to resume all threads.
=end
            DEBUGGER__.resume
        end

        def check_suspend
=begin edoc
Method to check the suspend state.
=end
            while MUTEX.synchronize {
                if @suspend_next
                    DEBUGGER__.waiting.push Thread.current
                    @suspend_next = false
                    true
                end
            }
            end
        end

        def stdout
=begin edoc
Method returning the stdout object.

@return reference to the stdout object
=end
            DEBUGGER__.stdout
        end

        def break_points
=begin edoc
Method to return the list of breakpoints

@return Array containing all breakpoints.
=end
            DEBUGGER__.break_points
        end

        def context(th)
=begin edoc
Method returning the context of a thread.

@param th thread object to get the context for
@return the context for the thread
=end
            DEBUGGER__.context(th)
        end

        def attached?
=begin edoc
Method returning the attached state.

@return flag indicating, whether the debugger is attached to the IDE.
=end
            DEBUGGER__.attached?
        end

        def set_last_thread(th)
=begin edoc
Method to remember the last thread.

@param th thread to be remembered.
=end
            DEBUGGER__.set_last_thread(th)
        end

        def debug_silent_eval(str, binding_)
=begin edoc
Method to eval a string without output.

@param str String containing the expression to be evaluated
@param binding_ the binding for the evaluation
@return the result of the evaluation
=end
            val = eval(str, binding_)
            val
        end

        def thnum
=begin edoc
Method returning the thread number of the current thread.

@return thread number of the current thread.
=end
            num = DEBUGGER__.instance_eval{@thread_list[Thread.current]}
            unless num
                DEBUGGER__.make_thread_list
                num = DEBUGGER__.instance_eval{@thread_list[Thread.current]}
            end
            num
        end

        def debug_command(file, line, id, binding_)
=begin edoc
Method to execute the next debug command.
=end
            MUTEX.lock
            set_last_thread(Thread.current)
            unless attached?
                MUTEX.unlock
                resume_all
                return
            end
            @frame_pos = 0
            @frames[0] = [binding_, file, line, id]
            stdout.printf_line(@frames)
            MUTEX.unlock
            resume_all
            eventLoop
        end

        def frame_set_pos(file, line)
=begin edoc
Method to set the frame position of the current frame.
=end
            if @frames[0]
                @frames[0][1] = file
                @frames[0][2] = line
            end
        end

        def check_break_points(file, pos, binding_, id)
=begin edoc
Method to check, if the given position contains an active breakpoint.

@param file filename containing the currently executed line (String)
@param pos line number currently executed (int)
@param binding_ current binding object
@param id (ignored)
@return flag indicating an active breakpoint (boolean)
=end
            # bp[0] enabled flag
            # bp[1] 0 = breakpoint, 1 = watch expression
            # bp[2] filename
            # bp[3] linenumber
            # bp[4] temporary flag
            # bp[5] condition
            # bp[6] ignore count
            # bp[7] special condition
            # bp[8] hash of special values
            return false if break_points.empty?
            break_points.each do |b|
                if b[0]
                    if b[1] == 0 and b[2] == file and b[3] == pos   # breakpoint
                        # Evaluate condition
                        if b[5]
                            begin
                                if debug_silent_eval(b[5], binding_)
                                    if b[6] == 0    # ignore count reached
                                        # Delete once reached if temporary breakpoint
                                        clear_break_point(file, pos) if b[4]
                                        return true
                                    else
                                        b[6] -= 1
                                    end
                                end
                            rescue StandardError, ScriptError
                                nil
                            end
                        else
                            if b[6] == 0    # ignore count reached
                                # Delete once reached if temporary breakpoint
                                clear_break_point(file, pos) if b[4]
                                return true
                            else
                                b[6] -= 1
                            end
                        end
                    elsif b[1] == 1                                 # watch expression
                        begin
                            bd = @frame_pos
                            val = debug_silent_eval(b[5], binding_)
                            if b[7].length() > 0
                                if b[7] == "??created??"
                                    if b[8][bd][0] == false
                                        b[8][bd][0] = true
                                        b[8][bd][1] = val
                                        return true
                                    else
                                        next
                                    end
                                end
                                b[8][bd][0] = true
                                if b[7] == "??changed??"
                                    if b[8][bd][1] != val
                                        b[8][bd][1] = val
                                        if b[8][bd][2] > 0
                                            b[8][bd][2] -= 1
                                            next
                                        else
                                            return true
                                        end
                                    else
                                        next
                                    end
                                end
                                next
                            end
                            if val
                                if b[6] == 0    # ignore count reached
                                    # Delete once reached if temporary breakpoint
                                    clear_watch_point(b[2]) if b[4]
                                    return true
                                else
                                    b[6] -= 1
                                end
                            end
                        rescue StandardError, ScriptError
                            if b[7].length() > 0
                                if b[8][bd]
                                    b[8][bd][0] = false
                                else
                                    b[8][bd] = [false, nil, b[6]]
                                end
                            else
                                val = nil
                            end
                        end
                    end
                end
            end
            return false
        end

        def clear_break_point(file, pos)
=begin edoc
Method to delete a specific breakpoint.

@param file filename containing the breakpoint (String)
@param pos line number containing the breakpoint (int)
=end
            delete_break_point(file, pos)
            stdout.printf_clear_breakpoint(file, pos)
        end
    
        def add_break_point(file, pos, temp = false, cond = nil)
=begin edoc
Method to add a breakpoint.

@param file filename for the breakpoint (String)
@param pos line number for the breakpoint (int)
@param temp flag indicating a temporary breakpoint (boolean)
@param cond condition of a conditional breakpoint (String)
=end
            break_points.push [true, 0, file, pos, temp, cond, 0]
        end

        def delete_break_point(file, pos)
=begin edoc
Method to delete a breakpoint.

@param file filename of the breakpoint (String)
@param pos line number of the breakpoint (int)
=end
            break_points.delete_if { |bp|
                bp[1] == 0 and bp[2] == file and bp[3] == pos
            }
        end

        def enable_break_point(file, pos, enable)
=begin edoc
Method to set the enabled state of a breakpoint.

@param file filename of the breakpoint (String)
@param pos line number of the breakpoint (int)
@param enable flag indicating the new enabled state (boolean)
=end
            break_points.each do |bp|
                if (bp[1] == 0 and bp[2] == file and bp[3] == pos)
                    bp[0] = enable 
                    break
                end
            end
        end

        def ignore_break_point(file, pos, count)
=begin edoc
Method to set the ignore count of a breakpoint.

@param file filename of the breakpoint (String)
@param pos line number of the breakpoint (int)
@param count ignore count to be set (int)
=end
            break_points.each do |bp|
                if (bp[2] == file and bp[3] == pos)
                    bp[6] = count 
                    break
                end
            end
        end

        def clear_watch_point(cond)
=begin edoc
Method to delete a specific watch expression.

@param cond expression specifying the watch expression (String)
=end
            delete_watch_point(cond)
            stdout.printf_clear_watchexpression(cond)
        end
    
        def add_watch_point(cond, temp = false)
=begin edoc
Method to add a watch expression.

@param cond expression of the watch expression (String)
@param temp flag indicating a temporary watch expression (boolean)
=end
            co1, co2 = cond.split()
            if co2 == "??created??" or co2 == "??changed??"
                break_points.push [true, 1, cond, 0, temp, co1, 0, co2, {}]
            else
                break_points.push [true, 1, cond, 0, temp, cond, 0, "", {}]
            end
        end
    
        def delete_watch_point(cond)
=begin edoc
Method to delete a watch expression.

@param cond expression of the watch expression (String)
=end
            break_points.delete_if { |bp|
                bp[1] == 1 and bp[2] == cond
            }
        end
    
        def enable_watch_point(cond, enable)
=begin edoc
Method to set the enabled state of a watch expression.

@param cond expression of the watch expression (String)
@param enable flag indicating the new enabled state (boolean)
=end
            break_points.each do |bp|
                if (bp[1] == 1 and bp[2] == cond)
                    bp[0] = enable
                    break
                end
            end
        end
    
        def ignore_watch_point(cond, count)
=begin edoc
Method to set the ignore count of a watch expression.

@param cond expression of the watch expression (String)
@param count ignore count to be set (int)
=end
            break_points.each do |bp|
                if (bp[1] == 1 and bp[2] == cond)
                    bp[6] = count
                    break
                end
            end
        end
    
        def excn_handle(file, line, id, binding_)
=begin edoc
Method to handle an exception

@param file filename containing the currently executed line (String)
@param pos line number currently executed (int)
@param id (ignored)
@param binding_ current binding object
=end
            if $!.class <= SystemExit
                set_trace_func nil
                stdout.printf_exit($!.status)
                return
            elsif $!.class <= ScriptError
                msgParts = $!.message.split(":", 3)
                filename = File.expand_path(msgParts[0])
                linenr = msgParts[1].to_i
                exclist = ["", [filename, linenr, 0]]
                stdout.printf_scriptExcn(exclist)
            else
                exclist = ["%s" % $!.class, "%s" % $!, [file, line]]
                @frames.each do |_binding, _file, _line, _id|
                    next if [_file, _line] == exclist[-1]
                    exclist << [_file, _line, '', '']
                end
                stdout.printf_excn(exclist)
            end
            debug_command(file, line, id, binding_)
        end

        def skip_it?(file)
=begin edoc
Method to filter out debugger files.

Tracing is turned off for files that are part of the
debugger that are called from the application being debugged.

@param file name of the file to be checked (String)
@return flag indicating, whether the file should be skipped (boolean)
=end
            if file =~ /\(eval\)/
                return true
            end
           
            if not traceRuby? and
               (file =~ /#{RbConfig::CONFIG['sitelibdir']}/ or
                file =~ /#{RbConfig::CONFIG['rubylibdir']}/)
                return true
            end
            
            if ["AsyncFile.rb", "AsyncIO.rb", "Config.rb", "DebugClient.rb",
                "DebugClientBaseModule.rb", "DebugClientCapabilities.rb",
                "DebugProtocol.rb", "DebugQuit.rb", "Debuggee.rb"].include?(
                    File.basename(file))
                return true
            end
            return false
        end
    
        def trace_func(event, file, line, id, binding_, klass)
=begin edoc
Method executed by the tracing facility.

@param event the tracing event (String)
@param file the name of the file being traced (String)
@param line the line number being traced (int)
@param id object id
@param binding_ a binding object
@param klass name of a class
=end
            context(Thread.current).check_suspend
          
            if skip_it?(file) and not ["call","return"].include?(event)
                case event
                when 'line'
                    frame_set_pos(file, line)
                    
                when 'call'
                    @frames.unshift [binding_, file, line, id]
                
                when 'c-call'
                    frame_set_pos(file, line)
            
                when 'class'
                    @frames.unshift [binding_, file, line, id]
                    
                when 'return', 'end'
                    @frames.shift
        
                when 'raise' 
                    excn_handle(file, line, id, binding_)
                    
                end
                @last_file = file
                return
            end
        
            @file = file
            @line = line
            
            case event
            when 'line'
                frame_set_pos(file, line)
                eventPoll
                if !@no_step or @frames.size == @no_step
                    @stop_next -= 1
                    @stop_next = -1 if @stop_next < 0
                elsif @frames.size < @no_step
                    @stop_next = 0        # break here before leaving...
                else
                    # nothing to do. skipped.
                end
                if check_break_points(file, line, binding_, id) or @stop_next == 0 
                    @no_step = nil
                    suspend_all
                    debug_command(file, line, id, binding_)
                end
    
            when 'call'
                @frames.unshift [binding_, file, line, id]
                if check_break_points(file, id.id2name, binding_, id) or
                    check_break_points(klass.to_s, id.id2name, binding_, id)
                    suspend_all
                    debug_command(file, line, id, binding_)
                end
    
            when 'c-call'
                frame_set_pos(file, line)
##                if id == :require and klass == Kernel
##                    @frames.unshift [binding_, file, line, id]
##                else
##                    frame_set_pos(file, line)
##                end
##        
##            when 'c-return'
##                if id == :require and klass == Kernel
##                    if @frames.size == @finish_pos
##                        @stop_next = 1
##                        @finish_pos = 0
##                    end
##                    @frames.shift
##                end
    
            when 'class'
                @frames.unshift [binding_, file, line, id]
    
            when 'return', 'end'
                if @frames.size == @finish_pos
                    @stop_next = 1
                    @finish_pos = 0
                end
                @frames.shift
    
            when 'raise'
                @no_step = nil
                @stop_next = 0        # break here before leaving...
                excn_handle(file, line, id, binding_)
    
            end
            @last_file = file
        end
    end

    trap("INT") { DEBUGGER__.interrupt }
    @last_thread = Thread::main
    @max_thread = 1
    @thread_list = {Thread::main => 1}
    @break_points = []
    @waiting = []
    @stdout = STDOUT
    @loaded_files = {}

    class SilentObject
=begin edoc
Class defining an object that ignores all messages.
=end
        def method_missing( msg_id, *a, &b )
=begin edoc
Method invoked for all messages it cannot handle.

@param msg_id symbol for the method called
@param *a arguments passed to the missing method
@param &b unknown
=end
        end
    end
    SilentClient = SilentObject.new()
    @client = SilentClient
    @attached = false

    class <<DEBUGGER__
=begin edoc
Class defining a singleton object for the debugger.
=end
        def stdout
=begin edoc
Method returning the stdout object.

@return reference to the stdout object
=end
            @stdout
        end

        def stdout=(s)
=begin edoc
Method to set the stdout object.

@param s reference to the stdout object
=end
            @stdout = s
        end

        def break_points
=begin edoc
Method to return the list of breakpoints

@return Array containing all breakpoints.
=end
            @break_points
        end

        def last_thread
=begin edoc
Method returning the last active thread.

@return active thread
=end
            @last_thread
        end

        def attach( debugger )
=begin edoc
Method to connect the debugger to the IDE.

@param debugger reference to the object handling the
    communication with the IDE.
=end
            unless @attached
                set_client( debugger )
                @attached = true
                interrupt
            else
                false
            end
        end

        def client
=begin edoc
Method returning a reference to the client object.

@return reference to the client object.
=end
            @client
        end

        def set_client( debugger )
=begin edoc
Method to set the client handling the connection.

@param debugger reference to the object handling the connection
=end
            @client = Client.new( debugger )
            DEBUGGER__.stdout = @client
        end

        def attached?
=begin edoc
Method returning the attached state.

@return flag indicating, whether the debugger is attached to the IDE.
=end
            @attached
        end

        def quit(status = 0)
=begin edoc
Method to quit the debugger.

@param status exit status of the program
=end
            @client.printf_exit(status)
            STDERR.flush; STDOUT.flush
        end

        def waiting
=begin edoc
Method returning the waiting list.

@return the waiting list
=end
            @waiting
        end

        def set_last_thread(th)
=begin edoc
Method to remember the last thread.

@param th thread to be remembered.
=end
            @last_thread = th
        end

        def suspend
=begin edoc
Method to suspend the program being debugged.
=end
            MUTEX.synchronize do
                make_thread_list
                for th, in @thread_list
                    next if th == Thread.current
                    context(th).set_suspend
                end
            end
            # Schedule other threads to suspend as soon as possible.
            Thread.pass
        end

        def resume
=begin edoc
Method to resume the program being debugged.
=end
            MUTEX.synchronize do
                make_thread_list
                for th, in @thread_list
                    next if th == Thread.current
                    context(th).clear_suspend
                end
                waiting.each do |th|
                    th.run
                end
                waiting.clear
            end
            # Schedule other threads to restart as soon as possible.
            Thread.pass
        end

        def context(thread=Thread.current)
=begin edoc
Method returning the context of a thread.

@param th threat the context is requested for
@return context object for the thread
=end
            c = thread[:__debugger_data__]
            unless c
                thread[:__debugger_data__] = c = Context.new
            end
            c
        end

        def interrupt
=begin edoc
Method to stop execution at the next instruction.
=end
            context(@last_thread).stop_next
        end

        def get_thread(num)
=begin edoc
Method returning a thread by number.

@param num thread number (int)
@return thread with the requested number
=end
            th = @thread_list.key(num)
            unless th
                @stdout.print "No thread ##{num}\n"
                throw :debug_error
            end
            th
            end

        def thread_list(num)
=begin edoc
Method to list the state of a thread.

@param num thread number (int)
=end
            th = get_thread(num)
            if th == Thread.current
                @stdout.print "+"
            else
                @stdout.print " "
            end
            @stdout.printf "%d ", num
            @stdout.print th.inspect, "\t"
            file = context(th).instance_eval{@file}
            if file
                @stdout.print file,":",context(th).instance_eval{@line}
            end
            @stdout.print "\n"
        end

        def thread_list_all
=begin edoc
Method to list the state of all threads.
=end
            for th in @thread_list.values.sort
                thread_list(th)
            end
        end

        def make_thread_list
=begin edoc
Method to create a thread list.
=end
            hash = {}
            for th in Thread::list
                next if (th[:__debugger_hidden__])
                if @thread_list.key? th
                    hash[th] = @thread_list[th]
                else
                    @max_thread += 1
                    hash[th] = @max_thread
                end
            end
            @thread_list = hash
        end

        def debug_thread_info(input, binding_)
=begin edoc
Method handling the thread related debug commands.

@param input debug command (String)
@param binding_ reference to the binding object
=end
            case input
            when /^l(?:ist)?/
                make_thread_list
                thread_list_all

            when /^c(?:ur(?:rent)?)?$/
                make_thread_list
                thread_list(@thread_list[Thread.current])

            when /^(?:sw(?:itch)?\s+)?(\d+)/
                make_thread_list
                th = get_thread($1.to_i)
                if th == Thread.current
                    @stdout.print "It's the current thread.\n"
                else
                    thread_list(@thread_list[th])
                    context(th).stop_next
                    th.run
                    return :cont
                end

            when /^stop\s+(\d+)/
                make_thread_list
                th = get_thread($1.to_i)
                if th == Thread.current
                    @stdout.print "It's the current thread.\n"
                elsif th.stop?
                    @stdout.print "Already stopped.\n"
                else
                    thread_list(@thread_list[th])
                    context(th).suspend 
                end

            when /^resume\s+(\d+)/
                make_thread_list
                th = get_thread($1.to_i)
                if th == Thread.current
                    @stdout.print "It's the current thread.\n"
                elsif !th.stop?
                    @stdout.print "Already running."
                else
                    thread_list(@thread_list[th])
                    th.run
                end
            end
        end
    
        def eventLoop
=begin edoc
Method calling the main event loop.
=end
            @client.eventLoop
        end
    
        def eventPoll
=begin edoc
Method calling the main function polling for an event sent by the IDE.
=end
            @client.eventPoll
        end
        
        def traceRuby?
=begin edoc
Method to check, if we should trace into the Ruby interpreter libraries.
=end
            @client.traceRuby?
        end
    end


    class Context
        def eventLoop
=begin edoc
Method calling the main event loop.
=end
            DEBUGGER__.eventLoop
        end
    
        def eventPoll
=begin edoc
Method calling the main function polling for an event sent by the IDE.
=end
            DEBUGGER__.eventPoll
        end
        
        def traceRuby?
=begin edoc
Method to check, if we should trace into the Ruby interpreter libraries.
=end
            DEBUGGER__.traceRuby?
        end
    end

    require 'DebugProtocol'
  
    class Client
=begin edoc
Class handling the connection to the IDE.
=end
        def initialize( debugger )
=begin edoc
Constructor

@param debugger reference to the object having the IDE connection.
=end
            @debugger = debugger
        end

        def eventLoop
=begin edoc
Method calling the main event loop.
=end
            @debugger.eventLoop()
        end
    
        def eventPoll
=begin edoc
Method calling the main function polling for an event sent by the IDE.
=end
            @debugger.eventPoll()
        end
        
        def traceRuby?
=begin edoc
Method to check, if we should trace into the Ruby interpreter libraries.
=end
            @debugger.traceRuby
        end

        def printf( *args )
=begin edoc
Method to print something to the IDE.

@param *args Arguments to be printed.
=end
            @debugger.write("#{args.join(', ')}\n")
        end

        def printf_line(frames)
=begin edoc
Method to report the current line and the current stack trace to the IDE.

@param frames reference to the array containing the stack trace.
=end
            fr_list = []
            for bind, file, line, id in frames
                break unless bind
                break if file =~ /\(eval\)/
                fr_list << [file, line, id ? id.id2name : '', '']
            end
            
            @debugger.write("%s%s\n" % [ResponseLine, fr_list.inspect])
        end

        def printf_excn(exclist)
=begin edoc
Method to report an exception to the IDE.

@param exclist info about the exception to be reported
=end
            @debugger.write("%s%s\n" % [ResponseException, exclist.inspect])
        end
    
        def printf_scriptExcn(exclist)
=begin edoc
Method to report a ScriptError to the IDE.

@param exclist info about the exception to be reported
=end
            @debugger.write("%s%s\n" % [ResponseSyntax, exclist.inspect])
        end

        def printf_clear_breakpoint(file, line)
=begin edoc
Method to report the deletion of a temporary breakpoint to the IDE.

@param file filename of the breakpoint (String)
@param line line number of the breakpoint (int)
=end
            @debugger.write("%s%s,%d\n" % [ResponseClearBreak, file, line])
        end
    
        def printf_clear_watchexpression(cond)
=begin edoc
Method to report the deletion of a temporary watch expression to the IDE.

@param cond expression of the watch expression (String)
=end
            @debugger.write("%s%s\n" % [ResponseClearWatch, cond])
        end
    
        def printf_exit(status)
=begin edoc
Method to report the exit status to the IDE.

@param status exit status of the program (int)
=end
            @debugger.write("%s%d\n" % [ResponseExit, status])
        end
    end

    class Context
        def current_frame
=begin edoc
Method returning the current execution frame.

@return current execution frame
=end
            @frames[@frame_pos]
        end
    
        def get_frame(frameno)
=begin edoc
Method returning a specific execution frame.

@param frameno frame number of the frame to be returned (int)
@return the requested execution frame
=end
            @frames[frameno]
        end
    
        def current_binding
=begin edoc
Method returning the binding object of the current execution frame.

@return binding object of the current execution frame
=end
            @frames[@frame_pos][0]
        end
    
        def get_binding(frameno)
=begin edoc
Method returning the binding object of a specific execution frame.

@param frameno frame number of the frame (int)
@return the requested binding object
=end
            @frames[frameno][0]
        end
    end
  
    Thread.main["name"] = 'Main'
end
