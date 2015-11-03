# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

=begin edoc
File implementing a command line completer class.
=end

#
# This code is mostly based on the completer found in irb of the Ruby package
# Original copyright
#       by Keiju ISHITSUKA(keiju@ishitsuka.com)
#       From Original Idea of shugo@ruby-lang.org
#

class Completer
=begin edoc
Class implementing a command completer.
=end
    ReservedWords = [
        "BEGIN", "END",
        "alias", "and", 
        "begin", "break", 
        "case", "class",
        "def", "defined", "do",
        "else", "elsif", "end", "ensure",
        "false", "for", 
        "if", "in", 
        "module", 
        "next", "nil", "not",
        "or", 
        "redo", "rescue", "retry", "return",
        "self", "super",
        "then", "true",
        "undef", "unless", "until",
        "when", "while",
        "yield",
    ]
    
    def initialize(binding)
=begin edoc
constructor

@param binding binding object used to determine the possible completions
=end
        @binding = binding
    end
    
    def complete(input)
=begin edoc
Public method to select the possible completions

@param input text to be completed (String)
@return list of possible completions (Array)
=end
        case input
        when /^((["'`]).*\2)\.([^.]*)$/
        # String
            receiver = $1
            message = $3
            
            candidates = String.instance_methods.collect{|m| m.to_s}
            select_message(receiver, message, candidates)

        when /^(\/[^\/]*\/)\.([^.]*)$/
        # Regexp
            receiver = $1
            message = Regexp.quote($2)

            candidates = Regexp.instance_methods.collect{|m| m.to_s}
            select_message(receiver, message, candidates)

        when /^([^\]]*\])\.([^.]*)$/
        # Array
            receiver = $1
            message = Regexp.quote($2)

            candidates = Array.instance_methods.collect{|m| m.to_s}
            select_message(receiver, message, candidates)

        when /^([^\}]*\})\.([^.]*)$/
        # Proc or Hash
            receiver = $1
            message = Regexp.quote($2)

            candidates = Proc.instance_methods.collect{|m| m.to_s}
            candidates |= Hash.instance_methods.collect{|m| m.to_s}
            select_message(receiver, message, candidates)
    
        when /^(:[^:.]*)$/
        # Symbol
            if Symbol.respond_to?(:all_symbols)
                sym = $1
                candidates = Symbol.all_symbols.collect{|s| ":" + s.id2name}
                candidates.grep(/^#{sym}/)
            else
                []
            end

        when /^::([A-Z][^:\.\(]*)$/
        # Absolute Constant or class methods
            receiver = $1
            candidates = Object.constants.collect{|m| m.to_s}
            candidates.grep(/^#{receiver}/).collect{|e| "::" + e}

        when /^([A-Z].*)::([^:.]*)$/
        # Constant or class methods
            receiver = $1
            message = Regexp.quote($4)
            begin
                candidates = eval("#{receiver}.constants.collect{|m| m.to_s}", bind)
                candidates |= eval("#{receiver}.methods.collect{|m| m.to_s}", bind)
            rescue Exception
                candidates = []
            end
            select_message(receiver, message, candidates, "::")

        when /^(:[^:.]+)(\.|::)([^.]*)$/
        # Symbol
            receiver = $1
            sep = $2
            message = Regexp.quote($3)

            candidates = Symbol.instance_methods.collect{|m| m.to_s}
            select_message(receiver, message, candidates, sep)

        when /^(-?(0[dbo])?[0-9_]+(\.[0-9_]+)?([eE]-?[0-9]+)?)(\.|::)([^.]*)$/
        # Numeric
            receiver = $1
            sep = $5
            message = Regexp.quote($6)

            begin
                candidates = eval(receiver, @binding).methods.collect{|m| m.to_s}
            rescue Exception
                candidates
            end
            select_message(receiver, message, candidates, sep)

        when /^(-?0x[0-9a-fA-F_]+)(\.|::)([^.]*)$/
        # Numeric(0xFFFF)
            receiver = $1
            sep = $2
            message = Regexp.quote($3)
            
            begin
                candidates = eval(receiver, bind).methods.collect{|m| m.to_s}
            rescue Exception
                candidates = []
            end
            select_message(receiver, message, candidates, sep)

        when /^(\$[^.]*)$/
        # Global variable
            candidates = global_variables.grep(Regexp.new(Regexp.quote($1)))

        when /^([^."].*)(\.|::)([^.]*)$/
        # variable.func or func.func
            receiver = $1
            sep = $2
            message = Regexp.quote($3)

            gv = eval("global_variables", @binding).collect{|m| m.to_s}
            lv = eval("local_variables", @binding).collect{|m| m.to_s}
            cv = eval("self.class.constants", @binding).collect{|m| m.to_s}
    
            if (gv | lv | cv).include?(receiver) or \
                /^[A-Z]/ =~ receiver && /\./ !~ receiver
                # foo.func and foo is var. OR
                # foo::func and foo is var. OR
                # foo::Const and foo is var. OR
                # Foo::Bar.func
                begin
                    candidates = []
                    rec = eval(receiver, bind)
                    if sep == "::" and rec.kind_of?(Module)
                        candidates = rec.constants.collect{|m| m.to_s}
                    end
                    candidates |= rec.methods.collect{|m| m.to_s}
                rescue Exception
                    candidates = []
                end
            else
                # func1.func2
                candidates = []
                ObjectSpace.each_object(Module){|m|
                    begin
                        name = m.name
                    rescue Exception
                        name = ""
                    end
                    begin
                        next if m.name != "IRB::Context" and 
                            /^(IRB|SLex|RubyLex|RubyToken)/ =~ m.name
                    rescue Exception
                        next
                    end
                    candidates.concat m.instance_methods(false).collect{|x| x.to_s}
                }
                candidates.sort!
                candidates.uniq!
            end
            select_message(receiver, message, candidates, sep)

        when /^\.([^.]*)$/
        # unknown(maybe String)

            receiver = ""
            message = Regexp.quote($1)

            candidates = String.instance_methods(true).collect{|m| m.to_s}
            select_message(receiver, message, candidates)

        else
            candidates = eval(
                "methods | private_methods | local_variables | self.class.constants",
                @binding).collect{|m| m.to_s}
            
            (candidates|ReservedWords).grep(/^#{Regexp.quote(input)}/)
        end
    end

    Operators = ["%", "&", "*", "**", "+",  "-",  "/",
      "<", "<<", "<=", "<=>", "==", "===", "=~", ">", ">=", ">>",
      "[]", "[]=", "^", "!", "!=", "!~"]

    def select_message(receiver, message, candidates, sep = ".")
=begin edoc
Method used to pick completion candidates.

@param receiver object receiving the message
@param message message to be sent to object
@param candidates possible completion candidates
@param sep separater string
@return filtered list of candidates
=end
        candidates.grep(/^#{message}/).collect do |e|
            case e
            when /^[a-zA-Z_]/
                receiver + sep + e
            when /^[0-9]/
            when *Operators
                #receiver + " " + e
            end
        end
    end
end
