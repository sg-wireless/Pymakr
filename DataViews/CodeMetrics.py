# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

#
# Code mainly borrowed from the Pythius package which is
# Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
#

"""
Module implementing a simple Python code metrics analyzer.

@exception ValueError the tokenize module is too old
"""

from __future__ import unicode_literals

import os
import io
import sys
import keyword
import token
import tokenize
    
import Utilities

KEYWORD = token.NT_OFFSET + 1
COMMENT = tokenize.COMMENT
INDENT = token.INDENT
DEDENT = token.DEDENT
NEWLINE = token.NEWLINE
EMPTY = tokenize.NL


class Token(object):
    """
    Class to store the token related infos.
    """
    def __init__(self, **kw):
        """
        Constructor
        
        @keyparam **kw list of key, value pairs
        """
        self.__dict__.update(kw)


class Parser(object):
    """
    Class used to parse the source code of a Python file.
    """
    def parse(self, text):
        """
        Public method used to parse the source code.
        
        @param text the source code as read from a Python source file
        """
        self.tokenlist = []
        
        # convert eols
        text = Utilities.convertLineEnds(text, os.linesep)
        
        if not text.endswith(os.linesep):
            text = "{0}{1}".format(text, os.linesep)
            
        self.lines = text.count(os.linesep)
        
        source = io.BytesIO(text.encode("utf-8"))
        try:
            if sys.version_info[0] == 2:
                gen = tokenize.generate_tokens(source.readline)
            else:
                gen = tokenize.tokenize(source.readline)
            for toktype, toktext, start, end, line in gen:
                (srow, scol) = start
                (erow, ecol) = end
                if toktype in [token.NEWLINE, tokenize.NL]:
                    self.__addToken(toktype, os.linesep, srow, scol, line)
                elif toktype in [token.INDENT, token.DEDENT]:
                    self.__addToken(toktype, '', srow, scol, line)
                elif toktype == token.NAME and keyword.iskeyword(toktext):
                    toktype = KEYWORD
                    self.__addToken(toktype, toktext, srow, scol, line)
                else:
                    self.__addToken(toktype, toktext, srow, scol, line)
        except tokenize.TokenError as msg:
            print("Token Error: {0}".format(str(msg)))
            return
        
        return
    
    def __addToken(self, toktype, toktext, srow, scol, line):
        """
        Private method used to add a token to our list of tokens.
        
        @param toktype the type of the token (int)
        @param toktext the text of the token (string)
        @param srow starting row of the token (int)
        @param scol starting column of the token (int)
        @param line logical line the token was found (string)
        """
        self.tokenlist.append(Token(type=toktype, text=toktext, row=srow,
                                    col=scol, line=line))

spacer = ' '


class SourceStat(object):
    """
    Class used to calculate and store the source code statistics.
    """
    def __init__(self):
        """
        Constructor
        """
        self.identifiers = []
        # list of identifiers in order of appearance
        self.active = [('TOTAL ', -1, 0)]
        # stack of active identifiers and indent levels
        self.counters = {}
        # counters per identifier
        self.indent_level = 0

    def indent(self, tok):
        """
        Public method used to increment the indentation level.
        
        @param tok a token (Token, ignored)
        """
        self.indent_level += 1

    def dedent(self, tok):
        """
        Public method used to decrement the indentation level.
        
        @param tok the token to be processed (Token)
        @exception ValueError raised to indicate an invalid indentation level
        """
        self.indent_level -= 1
        if self.indent_level < 0:
            raise ValueError("INTERNAL ERROR: Negative indent level")

        # remove identifiers of a higher indentation
        while self.active and self.active[-1][1] >= self.indent_level:
            counters = self.counters.setdefault(self.active[-1][0], {})
            counters['start'] = self.active[-1][2]
            counters['end'] = tok.row - 1
            counters['lines'] = tok.row - self.active[-1][2]
            del self.active[-1]

    def push(self, identifier, row):
        """
        Public method used to store an identifier.
        
        @param identifier the identifier to be remembered (string)
        @param row the row, the identifier is defined in (int)
        """
        if len(self.active) > 1 and self.indent_level > self.active[-1][1]:
            qualified = self.active[-1][0] + '.' + identifier
        else:
            qualified = identifier
        self.active.append((qualified, self.indent_level, row))
        self.identifiers.append(qualified)

    def inc(self, key, value=1):
        """
        Public method used to increment the value of a key.
        
        @param key the key to be incremented
        @param value the increment (int)
        """
        for id, level, row in self.active:
            counters = self.counters.setdefault(id, {})
            counters[key] = counters.setdefault(key, 0) + value

    def dump(self):
        """
        Public method used to format and print the collected statistics.
        """
        label_len = 79 - len(spacer) - 6 * 6
        print(spacer + "FUNCTION / CLASS".ljust(label_len) +
              " START   END LINES  NLOC  COMM EMPTY")
        for id in self.identifiers + ['TOTAL ']:
            label = id
            counters = self.counters.get(id, {})
            msg = spacer + label.ljust(label_len)

            for key in ('start', 'end', 'lines', 'nloc', 'comments', 'empty'):
                if counters.get(key, 0):
                    msg += " {0:d}".format(counters[key])
                else:
                    msg += " " * 6

            print(msg)

    def getCounter(self, id, key):
        """
        Public method used to get a specific counter value.
        
        @param id id of the counter (string)
        @param key key of the value to be retrieved (string)
        @return the value of the requested counter (int)
        """
        return self.counters.get(id, {}).get(key, 0)


def summarize(total, key, value):
    """
    Module function used to collect overall statistics.
    
    @param total the dictionary for the overall statistics
    @param key the key to be summarize
    @param value the value to be added to the overall statistics
    @return the value added to the overall statistics
    """
    total[key] = total.setdefault(key, 0) + value
    return value


def analyze(filename, total):
    """
    Module function used analyze the source of a Python file.
    
    @param filename name of the Python file to be analyzed (string)
    @param total dictionary receiving the overall code statistics
    @return a statistics object with the collected code statistics (SourceStat)
    """
    try:
        text = Utilities.readEncodedFile(filename)[0]
    except (UnicodeError, IOError):
        return SourceStat()

    parser = Parser()
    parser.parse(text)

    stats = SourceStat()
    stats.inc('lines', parser.lines)
    for idx in range(len(parser.tokenlist)):
        tok = parser.tokenlist[idx]
        
        # counting
        if tok.type == NEWLINE:
            stats.inc('nloc')
        elif tok.type == COMMENT:
            stats.inc('comments')
            if tok.line.strip() == tok.text:
                stats.inc('commentlines')
        elif tok.type == EMPTY:
            if parser.tokenlist[idx - 1].type == token.OP:
                stats.inc('nloc')
            elif parser.tokenlist[idx - 1].type == COMMENT:
                continue
            else:
                stats.inc('empty')
        elif tok.type == INDENT:
            stats.indent(tok)
        elif tok.type == DEDENT:
            stats.dedent(tok)
        elif tok.type == KEYWORD:
            if tok.text in ("class", "def"):
                stats.push(parser.tokenlist[idx + 1].text, tok.row)

    # collect overall statistics
    summarize(total, 'lines', parser.lines)
    summarize(total, 'bytes', len(text))
    summarize(total, 'comments', stats.getCounter('TOTAL ', 'comments'))
    summarize(total, 'commentlines',
              stats.getCounter('TOTAL ', 'commentlines'))
    summarize(total, 'empty lines', stats.getCounter('TOTAL ', 'empty'))
    summarize(total, 'non-commentary lines',
              stats.getCounter('TOTAL ', 'nloc'))

    return stats
    

def main():
    """
    Module main function used when called as a script.
    
    Loop over all files given on the command line and collect the individual
    and overall source code statistics.
    """
    import sys
    
    files = sys.argv[1:]
    
    if not files:
        sys.exit(1)
        
    total = {}
    
    summarize(total, 'files', len(files))
    for file in files:
        print(file)
        stats = analyze(file, total)
        stats.dump()
        
    print("\nSummary")
    for key in ['files', 'lines', 'bytes', 'comments',
                'empty lines', 'non-commentary lines']:
        print(key.ljust(20) + "{0:d}".format(total[key]))
    
    sys.exit(0)

if __name__ == "__main__":
    main()
