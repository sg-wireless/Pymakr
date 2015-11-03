#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
#

from __future__ import unicode_literals

import re

import jasy.core.Console as Console

__all__ = ["CommentException", "Comment"]


# Used to measure the doc indent size (with leading stars in front of content)
docIndentReg = re.compile(r"^(\s*\*\s*)(\S*)")


class CommentException(Exception):
    """
    Thrown when errors during comment processing are detected.
    """
    def __init__(self, message, lineNo=0):
        Exception.__init__(self, "Comment error: %s (line: %s)" % (message, lineNo+1))


class Comment():
    """
    Comment class is attached to parsed nodes and used to store all comment related
    information.
    
    The class supports a new Markdown and TomDoc inspired dialect to make developers life
    easier and work less repeative.
    """
    
    # Relation to code
    context = None
    
    # Collected text of the comment
    text = None
    
    def __init__(self, text, context=None, lineNo=0, indent="", fileId=None):

        # Store context (relation to code)
        self.context = context
        
        # Store fileId
        self.fileId = fileId
        
        # Figure out the type of the comment based on the starting characters

        # Inline comments
        if text.startswith("//"):
            # "// hello" => "   hello"
            text = "  " + text[2:]
            self.variant = "single"
            
        # Doc comments
        elif text.startswith("/**"):
            # "/** hello */" => "    hello "
            text = "   " + text[3:-2]
            self.variant = "doc"

        # Protected comments which should not be removed
        # (e.g these are used for license blocks)
        elif text.startswith("/*!"):
            # "/*! hello */" => "    hello "
            text = "   " + text[3:-2]
            self.variant = "protected"
            
        # A normal multiline comment
        elif text.startswith("/*"):
            # "/* hello */" => "   hello "
            text = "  " + text[2:-2]
            self.variant = "multi"
            
        else:
            raise CommentException("Invalid comment text: %s" % text, lineNo)

        # Multi line comments need to have their indentation removed
        if "\n" in text:
            text = self.__outdent(text, indent, lineNo)

        # For single line comments strip the surrounding whitespace
        else:
            # " hello " => "hello"
            text = text.strip()

        # The text of the comment
        self.text = text
    
    def __outdent(self, text, indent, startLineNo):
        """
        Outdent multi line comment text and filtering empty lines
        """
        
        lines = []

        # First, split up the comments lines and remove the leading indentation
        for lineNo, line in enumerate((indent+text).split("\n")):

            if line.startswith(indent):
                lines.append(line[len(indent):].rstrip())

            elif line.strip() == "":
                lines.append("")

            else:
                # Only warn for doc comments, otherwise it might just be code commented
                # out which is sometimes formatted pretty crazy when commented out
                if self.variant == "doc":
                    Console.warn("Could not outdent doc comment at line %s in %s",
                        startLineNo+lineNo, self.fileId)
                    
                return text

        # Find first line with real content, then grab the one after it to get the 
        # characters which need 
        outdentString = ""
        for lineNo, line in enumerate(lines):

            if line != "" and line.strip() != "":
                matchedDocIndent = docIndentReg.match(line)
                
                if not matchedDocIndent:
                    # As soon as we find a non doc indent like line we stop
                    break
                    
                elif matchedDocIndent.group(2) != "":
                    # otherwise we look for content behind the indent to get the 
                    # correct real indent (with spaces)
                    outdentString = matchedDocIndent.group(1)
                    break
                
            lineNo += 1

        # Process outdenting to all lines (remove the outdentString from the start
        # of the lines)
        if outdentString != "":

            lineNo = 0
            outdentStringLen = len(outdentString)

            for lineNo, line in enumerate(lines):
                if len(line) <= outdentStringLen:
                    lines[lineNo] = ""

                else:
                    if not line.startswith(outdentString):
                        
                        # Only warn for doc comments, otherwise it might just be code
                        # commented out which is sometimes formatted pretty crazy when
                        # commented out
                        if self.variant == "doc":
                            Console.warn(
                                "Invalid indentation in doc comment at line %s in %s",
                                startLineNo+lineNo, self.fileId)
                        
                    else:
                        lines[lineNo] = line[outdentStringLen:]

        # Merge final lines and remove leading and trailing new lines
        return "\n".join(lines).strip("\n")
