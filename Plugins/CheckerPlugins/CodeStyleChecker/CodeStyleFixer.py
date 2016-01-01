# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class to fix certain code style issues.
"""

from __future__ import unicode_literals
try:
    # Python 2
    from StringIO import StringIO       # __IGNORE_EXCEPTION__
except ImportError:
    # Python 3
    from io import StringIO             # __IGNORE_WARNING__
import os
import re
import tokenize

# CodeStyleCheckerDialog tries to import FixableCodeStyleIssues what fail under
# Python3. So ignore it.
try:
    import pep8
except ImportError:
    pass

FixableCodeStyleIssues = [
    "D111", "D112", "D113", "D121", "D131", "D141",
    "D142", "D143", "D144", "D145",
    "D221", "D222", "D231", "D242", "D243", "D244",
    "D245", "D246", "D247",
    "E101", "E111", "E121", "E122", "E123", "E124",
    "E125", "E126", "E127", "E128", "E133", "E201",
    "E202", "E203", "E211", "E221", "E222", "E223",
    "E224", "E225", "E226", "E227", "E228", "E231",
    "E241", "E242", "E251", "E261", "E262", "E271",
    "E272", "E273", "E274", "E301", "E302", "E303",
    "E304", "E401", "E501", "E502", "E701", "E702",
    "E703", "E711", "E712",
    "N804", "N805", "N806",
    "W191", "W291", "W292", "W293", "W391", "W603",
]


class CodeStyleFixer(object):
    """
    Class implementing a fixer for certain code style issues.
    """
    def __init__(self, filename, sourceLines, fixCodes, noFixCodes,
                 maxLineLength, inPlace, eol, backup=False):
        """
        Constructor
        
        @param filename name of the file to be fixed (string)
        @param sourceLines list of source lines including eol marker
            (list of string)
        @param fixCodes list of codes to be fixed as a comma separated
            string (string)
        @param noFixCodes list of codes not to be fixed as a comma
            separated string (string)
        @param maxLineLength maximum allowed line length (integer)
        @param inPlace flag indicating to modify the file in place (boolean)
        @param eol end of line character(s) (string)
        @param backup flag indicating to create a backup before fixing
            anything (boolean)
        """
        super(CodeStyleFixer, self).__init__()
        
        self.__filename = filename
        self.__origName = ""
        self.__source = sourceLines[:]  # save a copy
        self.__fixCodes = [c.strip() for c in fixCodes.split(",") if c.strip()]
        self.__noFixCodes = [
            c.strip() for c in noFixCodes.split(",") if c.strip()]
        self.__maxLineLength = maxLineLength
        self.fixed = 0
        
        self.__reindenter = None
        self.__indentWord = self.__getIndentWord()
        
        if inPlace:
            self.__createBackup = backup
        else:
            self.__origName = self.__filename
            self.__filename = os.path.join(
                os.path.dirname(self.__filename),
                "fixed_" + os.path.basename(self.__filename))
            self.__createBackup = False
        self.__eol = eol

        self.__fixes = {
            "D111": self.__fixD111,
            "D112": self.__fixD112,
            "D113": self.__fixD112,
            "D121": self.__fixD121,
            "D131": self.__fixD131,
            "D141": self.__fixD141,
            "D142": self.__fixD142,
            "D143": self.__fixD143,
            "D144": self.__fixD144,
            "D145": self.__fixD145,
            "D221": self.__fixD221,
            "D222": self.__fixD221,
            "D231": self.__fixD131,
            "D242": self.__fixD242,
            "D243": self.__fixD243,
            "D244": self.__fixD242,
            "D245": self.__fixD243,
            "D246": self.__fixD144,
            "D247": self.__fixD247,
            "E101": self.__fixE101,
            "E111": self.__fixE101,
            "E121": self.__fixE121,
            "E122": self.__fixE122,
            "E123": self.__fixE123,
            "E124": self.__fixE121,
            "E125": self.__fixE125,
            "E126": self.__fixE126,
            "E127": self.__fixE127,
            "E128": self.__fixE127,
            "E133": self.__fixE126,
            "E201": self.__fixE201,
            "E202": self.__fixE201,
            "E203": self.__fixE201,
            "E211": self.__fixE201,
            "E221": self.__fixE221,
            "E222": self.__fixE221,
            "E223": self.__fixE221,
            "E224": self.__fixE221,
            "E225": self.__fixE225,
            "E226": self.__fixE225,
            "E227": self.__fixE225,
            "E228": self.__fixE225,
            "E231": self.__fixE231,
            "E241": self.__fixE221,
            "E242": self.__fixE221,
            "E251": self.__fixE251,
            "E261": self.__fixE261,
            "E262": self.__fixE261,
            "E271": self.__fixE221,
            "E272": self.__fixE221,
            "E273": self.__fixE221,
            "E274": self.__fixE221,
            "E301": self.__fixE301,
            "E302": self.__fixE302,
            "E303": self.__fixE303,
            "E304": self.__fixE304,
            "E401": self.__fixE401,
            "E501": self.__fixE501,
            "E502": self.__fixE502,
            "E701": self.__fixE701,
            "E702": self.__fixE702,
            "E703": self.__fixE702,
            "E711": self.__fixE711,
            "E712": self.__fixE711,
            "N804": self.__fixN804,
            "N805": self.__fixN804,
            "N806": self.__fixN806,
            "W191": self.__fixE101,
            "W291": self.__fixW291,
            "W292": self.__fixW292,
            "W293": self.__fixW291,
            "W391": self.__fixW391,
            "W603": self.__fixW603,
        }
        self.__modified = False
        self.__stackLogical = []
        # These need to be fixed before the file is saved but after all
        # other inline fixes. These work with logical lines.
        self.__stack = []
        # These need to be fixed before the file is saved but after all
        # inline fixes.
        
        self.__multiLineNumbers = None
        self.__docLineNumbers = None
        
        self.__lastID = 0
    
    def saveFile(self, encoding):
        """
        Public method to save the modified file.
        
        @param encoding encoding of the source file (string)
        @return error message on failure (tuple of str)
        """
        import codecs
        
        if not self.__modified:
            # no need to write
            return
        
        if self.__createBackup:
            # create a backup file before writing any changes
            if os.path.islink(self.__filename):
                bfn = '{0}~'.format(os.path.realpath(self.__filename))
            else:
                bfn = '{0}~'.format(self.__filename)
            try:
                os.remove(bfn)
            except EnvironmentError:
                # if there was an error, ignore it
                pass
            try:
                os.rename(self.__filename, bfn)
            except EnvironmentError:
                # if there was an error, ignore it
                pass
        
        txt = "".join(self.__source)
        try:
            enc = 'utf-8' if encoding == 'utf-8-bom' else encoding
            txt = txt.encode(enc)
            if encoding == 'utf-8-bom':
                txt = codecs.BOM_UTF8 + txt
            
            with open(self.__filename, "wb") as fp:
                fp.write(txt)
        except (IOError, UnicodeError) as err:
            # Could not save the file! Skipping it. Reason: {0}
            return ("FWRITE_ERROR", (str(err),))
        return
    
    def __codeMatch(self, code):
        """
        Private method to check, if the code should be fixed.
        
        @param code to check (string)
        @return flag indicating it should be fixed (boolean)
        """
        def mutualStartswith(a, b):
            """
            Local helper method to compare the beginnings of two strings
            against each other.
            
            @return flag indicating that one string starts with the other
                (boolean)
            """
            return b.startswith(a) or a.startswith(b)
        
        if self.__noFixCodes:
            for noFixCode in [c.strip() for c in self.__noFixCodes]:
                if mutualStartswith(code.lower(), noFixCode.lower()):
                    return False

        if self.__fixCodes:
            for fixCode in [c.strip() for c in self.__fixCodes]:
                if mutualStartswith(code.lower(), fixCode.lower()):
                    return True
            return False

        return True
    
    def fixIssue(self, line, pos, message):
        """
        Public method to fix the fixable issues.
        
        @param line line number of issue (integer)
        @param pos character position of issue (integer)
        @param message message text (string)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if isinstance(message, (tuple, list)):
            code = message[0].strip()
        else:
            code = message.split(None, 1)[0].strip()
        
        if line <= len(self.__source) and \
           self.__codeMatch(code) and \
           code in self.__fixes:
            res = self.__fixes[code](code, line, pos)
            if res[0] == 1:
                self.__modified = True
                self.fixed += 1
        else:
            res = (0, "", 0)
        
        return res
    
    def finalize(self):
        """
        Public method to apply all deferred fixes.
        
        @return dictionary containing the fix results
        """
        results = {}
        
        # step 1: do fixes operating on logical lines first
        for id_, code, line, pos in self.__stackLogical:
            res, msg, _ = self.__fixes[code](code, line, pos, apply=True)
            if res == 1:
                self.__modified = True
                self.fixed += 1
            results[id_] = (res, msg)
        
        # step 2: do fixes that change the number of lines
        for id_, code, line, pos in reversed(self.__stack):
            res, msg, _ = self.__fixes[code](code, line, pos, apply=True)
            if res == 1:
                self.__modified = True
                self.fixed += 1
            results[id_] = (res, msg)
        
        return results
    
    def __getID(self):
        """
        Private method to get the ID for a deferred fix.
        
        @return ID for a deferred fix (integer)
        """
        self.__lastID += 1
        return self.__lastID
    
    def __findLogical(self):
        """
        Private method to extract the index of all the starts and ends of
        lines.
        
        @return tuple containing two lists of integer with start and end tuples
            of lines
        """
        logical_start = []
        logical_end = []
        last_newline = True
        sio = StringIO("".join(self.__source))
        parens = 0
        for t in tokenize.generate_tokens(sio.readline):
            if t[0] in [tokenize.COMMENT, tokenize.DEDENT,
                        tokenize.INDENT, tokenize.NL,
                        tokenize.ENDMARKER]:
                continue
            if not parens and t[0] in [tokenize.NEWLINE, tokenize.SEMI]:
                last_newline = True
                logical_end.append((t[3][0] - 1, t[2][1]))
                continue
            if last_newline and not parens:
                logical_start.append((t[2][0] - 1, t[2][1]))
                last_newline = False
            if t[0] == tokenize.OP:
                if t[1] in '([{':
                    parens += 1
                elif t[1] in '}])':
                    parens -= 1
        return logical_start, logical_end
    
    def __getLogical(self, line, pos):
        """
        Private method to get the logical line corresponding to the given
        position.
        
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return tuple of a tuple of two integers giving the start of the
            logical line, another tuple of two integers giving the end
            of the logical line and a list of strings with the original
            source lines
        """
        try:
            (logical_start, logical_end) = self.__findLogical()
        except (SyntaxError, tokenize.TokenError):
            return None

        line = line - 1
        ls = None
        le = None
        for i in range(0, len(logical_start)):
            x = logical_end[i]
            if x[0] > line or (x[0] == line and x[1] > pos):
                le = x
                ls = logical_start[i]
                break
        if ls is None:
            return None
        
        original = self.__source[ls[0]:le[0] + 1]
        return ls, le, original
    
    def __getIndentWord(self):
        """
        Private method to determine the indentation type.
        
        @return string to be used for an indentation (string)
        """
        sio = StringIO("".join(self.__source))
        indentWord = "    "     # default in case of failure
        try:
            for token in tokenize.generate_tokens(sio.readline):
                if token[0] == tokenize.INDENT:
                    indentWord = token[1]
                    break
        except (SyntaxError, tokenize.TokenError):
            pass
        return indentWord
    
    def __getIndent(self, line):
        """
        Private method to get the indentation string.
        
        @param line line to determine the indentation string from (string)
        @return indentation string (string)
        """
        return line.replace(line.lstrip(), "")
    
    def __multilineStringLines(self):
        """
        Private method to determine the line numbers that are within multi line
        strings and these which are part of a documentation string.
        
        @return tuple of a set of line numbers belonging to a multi line
            string and a set of line numbers belonging to a multi line
            documentation string (tuple of two set of integer)
        """
        if self.__multiLineNumbers is None:
            source = "".join(self.__source)
            sio = StringIO(source)
            self.__multiLineNumbers = set()
            self.__docLineNumbers = set()
            previousTokenType = ''
            try:
                for t in tokenize.generate_tokens(sio.readline):
                    tokenType = t[0]
                    startRow = t[2][0]
                    endRow = t[3][0]

                    if (tokenType == tokenize.STRING and startRow != endRow):
                        if previousTokenType != tokenize.INDENT:
                            self.__multiLineNumbers |= set(
                                range(startRow, 1 + endRow))
                        else:
                            self.__docLineNumbers |= set(
                                range(startRow, 1 + endRow))

                    previousTokenType = tokenType
            except (SyntaxError, tokenize.TokenError):
                pass
        
        return self.__multiLineNumbers, self.__docLineNumbers
    
    def __fixReindent(self, line, pos, logical):
        """
        Private method to fix a badly indented line.

        This is done by adding or removing from its initial indent only.
        
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @param logical logical line structure
        @return flag indicating a change was done (boolean)
        """
        assert logical
        ls, _, original = logical

        rewrapper = IndentationWrapper(original)
        valid_indents = rewrapper.pep8Expected()
        if not rewrapper.rel_indent:
            return False
        
        if line > ls[0]:
            # got a valid continuation line number
            row = line - ls[0] - 1
            # always pick the first option for this
            valid = valid_indents[row]
            got = rewrapper.rel_indent[row]
        else:
            return False
        
        line1 = ls[0] + row
        # always pick the expected indent, for now.
        indent_to = valid[0]

        if got != indent_to:
            orig_line = self.__source[line1]
            new_line = ' ' * (indent_to) + orig_line.lstrip()
            if new_line == orig_line:
                return False
            else:
                self.__source[line1] = new_line
                return True
        else:
            return False
    
    def __fixWhitespace(self, line, offset, replacement):
        """
        Private method to correct whitespace at the given offset.
        
        @param line line to be corrected (string)
        @param offset offset within line (integer)
        @param replacement replacement string (string)
        @return corrected line
        """
        left = line[:offset].rstrip(" \t")
        right = line[offset:].lstrip(" \t")
        if right.startswith("#"):
            return line
        else:
            return left + replacement + right
    
    def __fixD111(self, code, line, pos):
        """
        Private method to fix docstring enclosed in wrong quotes.
       
        Codes: D111
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        line = line - 1
        quotes = re.match(r"""\s*[ru]?('''|'|\")""",
                          self.__source[line]).group(1)
        left, right = self.__source[line].split(quotes, 1)
        self.__source[line] = left + '"""' + right
        while line < len(self.__source):
            if self.__source[line].rstrip().endswith(quotes):
                left, right = self.__source[line].rsplit(quotes, 1)
                self.__source[line] = left + '"""' + right
                break
            line += 1
        
        # Triple single quotes converted to triple double quotes.
        return (1, "FD111", 0)
    
    def __fixD112(self, code, line, pos):
        """
        Private method to fix docstring 'r' or 'u' in leading quotes.
        
        Codes: D112, D113
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        line = line - 1
        if code == "D112":
            insertChar = "r"
        elif code == "D113":
            insertChar = "u"
        else:
            return (0, "", 0)
        
        newText = self.__getIndent(self.__source[line]) + \
            insertChar + self.__source[line].lstrip()
        self.__source[line] = newText
        # Introductory quotes corrected to be {0}"""
        return (1, ('FD112', (insertChar,)), 0)
    
    def __fixD121(self, code, line, pos, apply=False):
        """
        Private method to fix a single line docstring on multiple lines.
       
        Codes: D121
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            line = line - 1
            if not self.__source[line].lstrip().startswith(
                    ('"""', 'r"""', 'u"""')):
                # only correctly formatted docstrings will be fixed
                return (0, "", 0)
            
            docstring = self.__source[line].rstrip() + \
                self.__source[line + 1].strip()
            if docstring.endswith('"""'):
                docstring += self.__eol
            else:
                docstring += self.__source[line + 2].lstrip()
                self.__source[line + 2] = ""
            
            self.__source[line] = docstring
            self.__source[line + 1] = ""
            # Single line docstring put on one line.
            return (1, "FD121", 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixD131(self, code, line, pos):
        """
        Private method to fix a docstring summary not ending with a
        period.
       
        Codes: D131
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        line = line - 1
        newText = ""
        if self.__source[line].rstrip().endswith(('"""', "'''")) and \
           self.__source[line].lstrip().startswith(('"""', 'r"""', 'u"""')):
            # it is a one-liner
            newText = self.__source[line].rstrip()[:-3].rstrip() + "." + \
                self.__source[line].rstrip()[-3:] + self.__eol
        else:
            if line < len(self.__source) - 1 and \
                (not self.__source[line + 1].strip() or
                 self.__source[line + 1].lstrip().startswith("@") or
                 (self.__source[line + 1].strip() in ('"""', "'''") and
                  not self.__source[line].lstrip().startswith("@"))):
                newText = self.__source[line].rstrip() + "." + self.__eol
        
        if newText:
            self.__source[line] = newText
            # Period added to summary line.
            return (1, "FD131", 0)
        else:
            return (0, "", 0)
    
    def __fixD141(self, code, line, pos, apply=False):
        """
        Private method to fix a function/method docstring preceded by a
        blank line.
       
        Codes: D141
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            line = line - 1
            self.__source[line - 1] = ""
            # Blank line before function/method docstring removed.
            return (1, "FD141", 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixD142(self, code, line, pos, apply=False):
        """
        Private method to fix a class docstring not preceded by a
        blank line.
       
        Codes: D142
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            line = line - 1
            self.__source[line] = self.__eol + self.__source[line]
            # Blank line inserted before class docstring.
            return (1, "FD142", 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixD143(self, code, line, pos, apply=False):
        """
        Private method to fix a class docstring not followed by a
        blank line.
       
        Codes: D143
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            line = line - 1
            self.__source[line] += self.__eol
            # Blank line inserted after class docstring.
            return (1, "FD143", 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixD144(self, code, line, pos, apply=False):
        """
        Private method to fix a docstring summary not followed by a
        blank line.
       
        Codes: D144
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            line = line - 1
            if not self.__source[line].rstrip().endswith("."):
                # only correct summary lines can be fixed here
                return (0, "", 0)
            
            self.__source[line] += self.__eol
            # Blank line inserted after docstring summary.
            return (1, "FD144", 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixD145(self, code, line, pos, apply=False):
        """
        Private method to fix the last paragraph of a multi-line docstring
        not followed by a blank line.
       
        Codes: D143
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            line = line - 1
            self.__source[line] = self.__eol + self.__source[line]
            # Blank line inserted after last paragraph of docstring.
            return (1, "FD145", 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixD221(self, code, line, pos, apply=False):
        """
        Private method to fix leading and trailing quotes of docstring
        not on separate lines.
       
        Codes: D221, D222
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            line = line - 1
            indent = self.__getIndent(self.__source[line])
            source = self.__source[line].strip()
            if code == "D221":
                # leading
                if source.startswith(("r", "u")):
                    first, second = source[:4], source[4:].strip()
                else:
                    first, second = source[:3], source[3:].strip()
            else:
                # trailing
                first, second = source[:-3].strip(), source[-3:]
            newText = indent + first + self.__eol + \
                indent + second + self.__eol
            self.__source[line] = newText
            if code == "D221":
                # Leading quotes put on separate line.
                msg = "FD221"
            else:
                # Trailing quotes put on separate line.
                msg = "FD222"
            return (1, msg, 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixD242(self, code, line, pos, apply=False):
        """
        Private method to fix a class or function/method docstring preceded
        by a blank line.
       
        Codes: D242, D244
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            line = line - 1
            self.__source[line - 1] = ""
            if code == "D242":
                # Blank line before class docstring removed.
                msg = "FD242"
            else:
                # Blank line before function/method docstring removed.
                msg = "FD244"
            return (1, msg, 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixD243(self, code, line, pos, apply=False):
        """
        Private method to fix a class or function/method docstring followed
        by a blank line.
       
        Codes: D243, D245
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            line = line - 1
            self.__source[line + 1] = ""
            if code == "D243":
                # Blank line after class docstring removed.
                msg = "FD243"
            else:
                # Blank line after function/method docstring removed.
                msg = "FD245"
            return (1, msg, 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixD247(self, code, line, pos, apply=False):
        """
        Private method to fix a last paragraph of a docstring followed
        by a blank line.
       
        Codes: D247
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            line = line - 1
            self.__source[line - 1] = ""
            # Blank line after last paragraph removed.
            return (1, "FD247", 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixE101(self, code, line, pos):
        """
        Private method to fix obsolete tab usage and indentation errors.
        
        Codes: E101, E111, W191
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if self.__reindenter is None:
            self.__reindenter = Reindenter(self.__source)
            self.__reindenter.run()
        fixedLine = self.__reindenter.fixedLine(line - 1)
        if fixedLine is not None and fixedLine != self.__source[line - 1]:
            self.__source[line - 1] = fixedLine
            if code in ["E101", "W191"]:
                # Tab converted to 4 spaces.
                msg = "FE101"
            else:
                # Indentation adjusted to be a multiple of four.
                msg = "FE111"
            return (1, msg, 0)
        else:
            return (0, "", 0)
    
    def __fixE121(self, code, line, pos, apply=False):
        """
        Private method to fix the indentation of continuation lines and
        closing brackets.
       
        Codes: E121, E124
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            logical = self.__getLogical(line, pos)
            if logical:
                # Fix by adjusting initial indent level.
                changed = self.__fixReindent(line, pos, logical)
                if changed:
                    if code == "E121":
                        # Indentation of continuation line corrected.
                        msg = "FE121"
                    elif code == "E124":
                        # Indentation of closing bracket corrected.
                        msg = "FE124"
                    return (1, msg, 0)
            return (0, "", 0)
        else:
            id = self.__getID()
            self.__stackLogical.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixE122(self, code, line, pos, apply=False):
        """
        Private method to fix a missing indentation of continuation lines.
        
        Codes: E122
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            logical = self.__getLogical(line, pos)
            if logical:
                # Fix by adding an initial indent.
                modified = self.__fixReindent(line, pos, logical)
                if not modified:
                    # fall back to simple method
                    line = line - 1
                    text = self.__source[line]
                    indentation = self.__getIndent(text)
                    self.__source[line] = indentation + \
                        self.__indentWord + text.lstrip()
                # Missing indentation of continuation line corrected.
                return (1, "FE122", 0)
            return (0, "", 0)
        else:
            id = self.__getID()
            self.__stackLogical.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixE123(self, code, line, pos, apply=False):
        """
        Private method to fix the indentation of a closing bracket lines.
        
        Codes: E123
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            logical = self.__getLogical(line, pos)
            if logical:
                # Fix by deleting whitespace to the correct level.
                logicalLines = logical[2]
                row = line - 1
                text = self.__source[row]
                newText = self.__getIndent(logicalLines[0]) + text.lstrip()
                if newText == text:
                    # fall back to slower method
                    changed = self.__fixReindent(line, pos, logical)
                else:
                    self.__source[row] = newText
                    changed = True
                if changed:
                    # Closing bracket aligned to opening bracket.
                    return (1, "FE123", 0)
            return (0, "", 0)
        else:
            id = self.__getID()
            self.__stackLogical.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixE125(self, code, line, pos, apply=False):
        """
        Private method to fix the indentation of continuation lines not
        distinguishable from next logical line.
       
        Codes: E125
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            logical = self.__getLogical(line, pos)
            if logical:
                # Fix by adjusting initial indent level.
                modified = self.__fixReindent(line, pos, logical)
                if not modified:
                    row = line - 1
                    text = self.__source[row]
                    self.__source[row] = self.__getIndent(text) + \
                        self.__indentWord + text.lstrip()
                # Indentation level changed.
                return (1, "FE125", 0)
            return (0, "", 0)
        else:
            id = self.__getID()
            self.__stackLogical.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixE126(self, code, line, pos, apply=False):
        """
        Private method to fix over-indented/under-indented hanging
        indentation.
       
        Codes: E126, E133
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            logical = self.__getLogical(line, pos)
            if logical:
                # Fix by deleting whitespace to the left.
                logicalLines = logical[2]
                row = line - 1
                text = self.__source[row]
                newText = self.__getIndent(logicalLines[0]) + \
                    self.__indentWord + text.lstrip()
                if newText == text:
                    # fall back to slower method
                    changed = self.__fixReindent(line, pos, logical)
                else:
                    self.__source[row] = newText
                    changed = True
                if changed:
                    # Indentation level of hanging indentation changed.
                    return (1, "FE126", 0)
            return (0, "", 0)
        else:
            id = self.__getID()
            self.__stackLogical.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixE127(self, code, line, pos, apply=False):
        """
        Private method to fix over/under indented lines.
       
        Codes: E127, E128
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            logical = self.__getLogical(line, pos)
            if logical:
                # Fix by inserting/deleting whitespace to the correct level.
                logicalLines = logical[2]
                row = line - 1
                text = self.__source[row]
                newText = text
                
                if logicalLines[0].rstrip().endswith('\\'):
                    newText = self.__getIndent(logicalLines[0]) + \
                        self.__indentWord + text.lstrip()
                else:
                    startIndex = None
                    for symbol in '([{':
                        if symbol in logicalLines[0]:
                            foundIndex = logicalLines[0].find(symbol) + 1
                            if startIndex is None:
                                startIndex = foundIndex
                            else:
                                startIndex = min(startIndex, foundIndex)

                    if startIndex is not None:
                        newText = startIndex * ' ' + text.lstrip()
                    
                if newText == text:
                    # fall back to slower method
                    changed = self.__fixReindent(line, pos, logical)
                else:
                    self.__source[row] = newText
                    changed = True
                if changed:
                    # Visual indentation corrected.
                    return (1, "FE127", 0)
            return (0, "", 0)
        else:
            id = self.__getID()
            self.__stackLogical.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixE201(self, code, line, pos):
        """
        Private method to fix extraneous whitespace.
       
        Codes: E201, E202, E203, E211
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        line = line - 1
        text = self.__source[line]
        
        if '"""' in text or "'''" in text or text.rstrip().endswith('\\'):
            return (0, "", 0)
        
        newText = self.__fixWhitespace(text, pos, '')
        if newText == text:
            return (0, "", 0)
        
        self.__source[line] = newText
        # Extraneous whitespace removed.
        return (1, "FE201", 0)
    
    def __fixE221(self, code, line, pos):
        """
        Private method to fix extraneous whitespace around operator or
        keyword.
       
        Codes: E221, E222, E223, E224, E241, E242, E271, E272, E273, E274
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        line = line - 1
        text = self.__source[line]
        
        if '"""' in text or "'''" in text or text.rstrip().endswith('\\'):
            return (0, "", 0)
        
        newText = self.__fixWhitespace(text, pos, ' ')
        if newText == text:
            return (0, "", 0)
        
        self.__source[line] = newText
        return (1, "FE221", 0)
    
    def __fixE225(self, code, line, pos):
        """
        Private method to fix extraneous whitespaces around operator.
       
        Codes: E225, E226, E227, E228
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        line = line - 1
        text = self.__source[line]
        
        if '"""' in text or "'''" in text or text.rstrip().endswith('\\'):
            return (0, "", 0)
        
        newText = text
        # determine length of operator
        tokens = '<>*/=^&|%!+-'
        pos2 = pos
        token_delimiter = len(tokens)
        for i in range(3):
            if pos2 < len(text) and text[pos2] in tokens[:token_delimiter]:
                pos2 += 1
                # only the first five could be repeated
                token_delimiter = 5
            else:
                break
        if pos2 < len(text) and text[pos2] not in ' \t':
            newText = self.__fixWhitespace(newText, pos2, ' ')
        newText = self.__fixWhitespace(newText, pos, ' ')
        if newText == text:
            return (0, "", 0)
        
        self.__source[line] = newText
        # Missing whitespaces added.
        return (1, "FE225", 0)
    
    def __fixE231(self, code, line, pos):
        """
        Private method to fix missing whitespace after ',;:'.
        
        Codes: E231
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        line = line - 1
        pos = pos + 1
        self.__source[line] = self.__source[line][:pos] + \
            " " + self.__source[line][pos:]
        # Missing whitespace added.
        return (1, "FE231", 0)
    
    def __fixE251(self, code, line, pos):
        """
        Private method to fix extraneous whitespace around keyword and
        default parameter equals.
       
        Codes: E251
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        line = line - 1
        text = self.__source[line]
        
        # This is necessary since pep8 sometimes reports columns that goes
        # past the end of the physical line. This happens in cases like,
        # foo(bar\n=None)
        col = min(pos, len(text) - 1)
        if text[col].strip():
            newText = text
        else:
            newText = text[:col].rstrip() + text[col:].lstrip()
        
        # There could be an escaped newline
        #
        #     def foo(a=\
        #             1)
        if newText.endswith(('=\\\n', '=\\\r\n', '=\\\r')):
            self.__source[line] = newText.rstrip("\n\r \t\\")
            self.__source[line + 1] = self.__source[line + 1].lstrip()
        else:
            self.__source[line] = newText
        # Extraneous whitespace removed.
        return (1, "FE251", 0)
    
    def __fixE261(self, code, line, pos):
        """
        Private method to fix whitespace before or after inline comment.
        
        Codes: E261, E262
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        line = line - 1
        text = self.__source[line]
        left = text[:pos].rstrip(' \t#')
        right = text[pos:].lstrip(' \t#')
        newText = left + ("  # " + right if right.strip() else right)
        self.__source[line] = newText
        # Whitespace around comment sign corrected.
        return (1, "FE261", 0)
    
    def __fixE301(self, code, line, pos, apply=False):
        """
        Private method to fix the need for one blank line.
       
        Codes: E301
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            self.__source.insert(line - 1, self.__eol)
            # One blank line inserted.
            return (1, "FE301", 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixE302(self, code, line, pos, apply=False):
        """
        Private method to fix the need for two blank lines.
       
        Codes: E302
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            # count blank lines
            index = line - 1
            blanks = 0
            while index:
                if self.__source[index - 1].strip() == "":
                    blanks += 1
                    index -= 1
                else:
                    break
            delta = blanks - 2
            
            line -= 1
            if delta < 0:
                # insert blank lines (one or two)
                while delta < 0:
                    self.__source.insert(line, self.__eol)
                    delta += 1
                # %n blank line(s) inserted.
                return (1, ("FE302+", 2 - blanks), 0)
            elif delta > 0:
                # delete superfluous blank lines
                while delta > 0:
                    del self.__source[line - 1]
                    line -= 1
                    delta -= 1
                # %n superfluous line(s) removed.
                return (1, ("FE302-", blanks - 2), 0)
            else:
                return (0, "", 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixE303(self, code, line, pos, apply=False):
        """
        Private method to fix superfluous blank lines.
       
        Codes: E303
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            index = line - 3
            while index:
                if self.__source[index].strip() == "":
                    del self.__source[index]
                    index -= 1
                else:
                    break
            # Superfluous blank lines removed.
            return (1, "FE303", 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixE304(self, code, line, pos, apply=False):
        """
        Private method to fix superfluous blank lines after a function
        decorator.
       
        Codes: E304
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            index = line - 2
            while index:
                if self.__source[index].strip() == "":
                    del self.__source[index]
                    index -= 1
                else:
                    break
            # Superfluous blank lines after function decorator removed.
            return (1, "FE304", 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixE401(self, code, line, pos, apply=False):
        """
        Private method to fix multiple imports on one line.
       
        Codes: E401
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            line = line - 1
            text = self.__source[line]
            if not text.lstrip().startswith("import"):
                return (0, "", 0)
            
            # pep8 (1.3.1) reports false positive if there is an import
            # statement followed by a semicolon and some unrelated
            # statement with commas in it.
            if ';' in text:
                return (0, "", 0)
            
            newText = text[:pos].rstrip("\t ,") + self.__eol + \
                self.__getIndent(text) + "import " + text[pos:].lstrip("\t ,")
            self.__source[line] = newText
            # Imports were put on separate lines.
            return (1, "FE401", 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixE501(self, code, line, pos, apply=False):
        """
        Private method to fix the long lines by breaking them.
       
        Codes: E501
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            multilineStringLines, docStringLines = \
                self.__multilineStringLines()
            isDocString = line in docStringLines
            line = line - 1
            text = self.__source[line]
            if line > 0:
                prevText = self.__source[line - 1]
            else:
                prevText = ""
            if line < len(self.__source) - 1:
                nextText = self.__source[line + 1]
            else:
                nextText = ""
            shortener = LineShortener(
                text, prevText, nextText,
                maxLength=self.__maxLineLength, eol=self.__eol,
                indentWord=self.__indentWord, isDocString=isDocString)
            changed, newText, newNextText = shortener.shorten()
            if changed:
                if newText != text:
                    self.__source[line] = newText
                if newNextText and newNextText != nextText:
                    if newNextText == " ":
                        newNextText = ""
                    self.__source[line + 1] = newNextText
                # Long lines have been shortened.
                return (1, "FE501", 0)
            else:
                return (0, "", 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixE502(self, code, line, pos):
        """
        Private method to fix redundant backslash within brackets.
       
        Codes: E502
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        self.__source[line - 1] = \
            self.__source[line - 1].rstrip("\n\r \t\\") + self.__eol
        # Redundant backslash in brackets removed.
        return (1, "FE502", 0)
    
    def __fixE701(self, code, line, pos, apply=False):
        """
        Private method to fix colon-separated compound statements.
       
        Codes: E701
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            line = line - 1
            text = self.__source[line]
            pos = pos + 1
            
            newText = text[:pos] + self.__eol + self.__getIndent(text) + \
                self.__indentWord + text[pos:].lstrip("\n\r \t\\") + \
                self.__eol
            self.__source[line] = newText
            # Compound statement corrected.
            return (1, "FE701", 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixE702(self, code, line, pos, apply=False):
        """
        Private method to fix semicolon-separated compound statements.
        
        Codes: E702, E703
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            line = line - 1
            text = self.__source[line]
            
            if text.rstrip().endswith("\\"):
                # normalize '1; \\\n2' into '1; 2'
                self.__source[line] = text.rstrip("\n\r \t\\")
                self.__source[line + 1] = self.__source[line + 1].lstrip()
            elif text.rstrip().endswith(";"):
                self.__source[line] = text.rstrip("\n\r \t;") + self.__eol
            else:
                first = text[:pos].rstrip("\n\r \t;") + self.__eol
                second = text[pos:].lstrip("\n\r \t;")
                self.__source[line] = first + self.__getIndent(text) + second
            # Compound statement corrected.
            return (1, "FE702", 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixE711(self, code, line, pos):
        """
        Private method to fix comparison with None.
       
        Codes: E711, E712
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        line = line - 1
        text = self.__source[line]
        
        rightPos = pos + 2
        if rightPos >= len(text):
            return (0, "", 0)
        
        left = text[:pos].rstrip()
        center = text[pos:rightPos]
        right = text[rightPos:].lstrip()
        
        if not right.startswith(("None", "True", "False")):
            return (0, "", 0)
        
        if center.strip() == "==":
            center = "is"
        elif center.strip() == "!=":
            center = "is not"
        else:
            return (0, "", 0)
        
        self.__source[line] = " ".join([left, center, right])
        # Comparison to None/True/False corrected.
        return (1, "FE711", 0)
    
    def __fixN804(self, code, line, pos, apply=False):
        """
        Private method to fix a wrong first argument of normal and
        class methods.
       
        Codes: N804, N805
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            line = line - 1
            text = self.__source[line]
            if code == "N804":
                arg = "cls"
            else:
                arg = "self"
            
            if text.rstrip().endswith("("):
                newText = text + self.__getIndent(text) + \
                    self.__indentWord + arg + "," + self.__eol
            else:
                index = text.find("(") + 1
                left = text[:index]
                right = text[index:]
                if right.startswith(")"):
                    center = arg
                else:
                    center = arg + ", "
                newText = left + center + right
            self.__source[line] = newText
            # '{0}' argument added.
            return (1, ("FN804", (arg,)), 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixN806(self, code, line, pos, apply=False):
        """
        Private method to fix a wrong first argument of static methods.
        
        Codes: N806
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @keyparam apply flag indicating, that the fix should be applied
            (boolean)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        if apply:
            line = line - 1
            text = self.__source[line]
            index = text.find("(") + 1
            left = text[:index]
            right = text[index:]
            
            if right.startswith(("cls", "self")):
                # cls or self are on the definition line
                if right.startswith("cls"):
                    right = right[3:]
                    arg = "cls"
                else:
                    right = right[4:]
                    arg = "self"
                right = right.lstrip(", ")
                newText = left + right
                self.__source[line] = newText
            else:
                # they are on the next line
                line = line + 1
                text = self.__source[line]
                indent = self.__getIndent(text)
                right = text.lstrip()
                if right.startswith("cls"):
                    right = right[3:]
                    arg = "cls"
                else:
                    right = right[4:]
                    arg = "self"
                right = right.lstrip(", ")
                if right.startswith("):"):
                    # merge with previous line
                    self.__source[line - 1] = \
                        self.__source[line - 1].rstrip() + right
                    self.__source[line] = ""
                else:
                    self.__source[line] = indent + right
            
            # '{0}' argument removed.
            return (1, ("FN806", arg), 0)
        else:
            id = self.__getID()
            self.__stack.append((id, code, line, pos))
            return (-1, "", id)
    
    def __fixW291(self, code, line, pos):
        """
        Private method to fix trailing whitespace.
       
        Codes: W291, W293
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        self.__source[line - 1] = re.sub(r'[\t ]+(\r?)$', r"\1",
                                         self.__source[line - 1])
        # Whitespace stripped from end of line.
        return (1, "FW291", 0)
    
    def __fixW292(self, code, line, pos):
        """
        Private method to fix a missing newline at the end of file.
       
        Codes: W292
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        self.__source[line - 1] += self.__eol
        # newline added to end of file.
        return (1, "FW292", 0)
    
    def __fixW391(self, code, line, pos):
        """
        Private method to fix trailing blank lines.
       
        Codes: W391
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        index = line - 1
        while index:
            if self.__source[index].strip() == "":
                del self.__source[index]
                index -= 1
            else:
                break
        # Superfluous trailing blank lines removed from end of file.
        return (1, "FW391", 0)
    
    def __fixW603(self, code, line, pos):
        """
        Private method to fix the not equal notation.
       
        Codes: W603
        
        @param code code of the issue (string)
        @param line line number of the issue (integer)
        @param pos position inside line (integer)
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message for the fix (string) and an ID for a deferred
            fix (integer)
        """
        self.__source[line - 1] = self.__source[line - 1].replace("<>", "!=")
        # '<>' replaced by '!='.
        return (1, "FW603", 0)


class Reindenter(object):
    """
    Class to reindent badly-indented code to uniformly use four-space
    indentation.

    Released to the public domain, by Tim Peters, 03 October 2000.
    """
    def __init__(self, sourceLines):
        """
        Constructor
        
        @param sourceLines list of source lines including eol marker
            (list of string)
        """
        # Raw file lines.
        self.raw = sourceLines
        self.after = []

        # File lines, rstripped & tab-expanded.  Dummy at start is so
        # that we can use tokenize's 1-based line numbering easily.
        # Note that a line is all-blank iff it's "\n".
        self.lines = [line.rstrip().expandtabs() + "\n"
                      for line in self.raw]
        self.lines.insert(0, None)
        self.index = 1  # index into self.lines of next line

        # List of (lineno, indentlevel) pairs, one for each stmt and
        # comment line.  indentlevel is -1 for comment lines, as a
        # signal that tokenize doesn't know what to do about them;
        # indeed, they're our headache!
        self.stats = []
    
    def run(self):
        """
        Public method to run the re-indenter.
        
        @return flag indicating that a change was done (boolean)
        """
        try:
            stats = self.__genStats(tokenize.generate_tokens(self.getline))
        except (SyntaxError, tokenize.TokenError):
            return False
        
        # Remove trailing empty lines.
        lines = self.lines
        while lines and lines[-1] == "\n":
            lines.pop()
        # Sentinel.
        stats.append((len(lines), 0))
        # Map count of leading spaces to # we want.
        have2want = {}
        # Program after transformation.
        after = self.after = []
        # Copy over initial empty lines -- there's nothing to do until
        # we see a line with *something* on it.
        i = stats[0][0]
        after.extend(lines[1:i])
        for i in range(len(stats) - 1):
            thisstmt, thislevel = stats[i]
            nextstmt = stats[i + 1][0]
            have = self.__getlspace(lines[thisstmt])
            want = thislevel * 4
            if want < 0:
                # A comment line.
                if have:
                    # An indented comment line.  If we saw the same
                    # indentation before, reuse what it most recently
                    # mapped to.
                    want = have2want.get(have, -1)
                    if want < 0:
                        # Then it probably belongs to the next real stmt.
                        for j in range(i + 1, len(stats) - 1):
                            jline, jlevel = stats[j]
                            if jlevel >= 0:
                                if have == self.__getlspace(lines[jline]):
                                    want = jlevel * 4
                                break
                    if want < 0:  # Maybe it's a hanging comment like this one,
                        # in which case we should shift it like its base
                        # line got shifted.
                        for j in range(i - 1, -1, -1):
                            jline, jlevel = stats[j]
                            if jlevel >= 0:
                                want = \
                                    have + \
                                    self.__getlspace(after[jline - 1]) - \
                                    self.__getlspace(lines[jline])
                                break
                    if want < 0:
                        # Still no luck -- leave it alone.
                        want = have
                else:
                    want = 0
            assert want >= 0
            have2want[have] = want
            diff = want - have
            if diff == 0 or have == 0:
                after.extend(lines[thisstmt:nextstmt])
            else:
                for line in lines[thisstmt:nextstmt]:
                    if diff > 0:
                        if line == "\n":
                            after.append(line)
                        else:
                            after.append(" " * diff + line)
                    else:
                        remove = min(self.__getlspace(line), -diff)
                        after.append(line[remove:])
        return self.raw != self.after
    
    def fixedLine(self, line):
        """
        Public method to get a fixed line.
        
        @param line number of the line to retrieve (integer)
        @return fixed line (string)
        """
        if line < len(self.after):
            return self.after[line]
    
    def getline(self):
        """
        Public method to get a line of text for tokenize.
        
        @return line of text (string)
        """
        if self.index >= len(self.lines):
            line = ""
        else:
            line = self.lines[self.index]
            self.index += 1
        return line

    def __genStats(self, tokens):
        """
        Private method to generate the re-indent statistics.
        
        @param tokens tokens generator (tokenize._tokenize)
        @return reference to the generated statistics
        """
        find_stmt = True  # next token begins a fresh stmt?
        level = 0  # current indent level
        stats = []

        for t in tokens:
            token_type = t[0]
            sline = t[2][0]
            line = t[4]

            if token_type == tokenize.NEWLINE:
                # A program statement, or ENDMARKER, will eventually follow,
                # after some (possibly empty) run of tokens of the form
                #     (NL | COMMENT)* (INDENT | DEDENT+)?
                self.find_stmt = True

            elif token_type == tokenize.INDENT:
                find_stmt = True
                level += 1

            elif token_type == tokenize.DEDENT:
                find_stmt = True
                level -= 1

            elif token_type == tokenize.COMMENT:
                if find_stmt:
                    stats.append((sline, -1))
                    # but we're still looking for a new stmt, so leave
                    # find_stmt alone

            elif token_type == tokenize.NL:
                pass

            elif find_stmt:
                # This is the first "real token" following a NEWLINE, so it
                # must be the first token of the next program statement, or an
                # ENDMARKER.
                find_stmt = False
                if line:   # not endmarker
                    stats.append((sline, level))
        
        return stats
    
    def __getlspace(self, line):
        """
        Private method to count number of leading blanks.
        
        @param line line to check (string)
        @return number of leading blanks (integer)
        """
        i = 0
        n = len(line)
        while i < n and line[i] == " ":
            i += 1
        return i


class IndentationWrapper(object):
    """
    Class used by fixers dealing with indentation.

    Each instance operates on a single logical line.
    """
    SKIP_TOKENS = frozenset([
        tokenize.COMMENT, tokenize.NL, tokenize.INDENT,
        tokenize.DEDENT, tokenize.NEWLINE, tokenize.ENDMARKER
    ])

    def __init__(self, physical_lines):
        """
        Constructor
        
        @param physical_lines list of physical lines to operate on
            (list of strings)
        """
        self.lines = physical_lines
        self.tokens = []
        self.rel_indent = None
        sio = StringIO(''.join(physical_lines))
        for t in tokenize.generate_tokens(sio.readline):
            if not len(self.tokens) and t[0] in self.SKIP_TOKENS:
                continue
            if t[0] != tokenize.ENDMARKER:
                self.tokens.append(t)

        self.logical_line = self.__buildTokensLogical(self.tokens)

    def __buildTokensLogical(self, tokens):
        """
        Private method to build a logical line from a list of tokens.
        
        @param tokens list of tokens as generated by tokenize.generate_tokens
        @return logical line (string)
        """
        # from pep8.py with minor modifications
        logical = []
        previous = None
        for t in tokens:
            token_type, text = t[0:2]
            if token_type in self.SKIP_TOKENS:
                continue
            if previous:
                end_line, end = previous[3]
                start_line, start = t[2]
                if end_line != start_line:  # different row
                    prev_text = self.lines[end_line - 1][end - 1]
                    if prev_text == ',' or (prev_text not in '{[('
                                            and text not in '}])'):
                        logical.append(' ')
                elif end != start:  # different column
                    fill = self.lines[end_line - 1][end:start]
                    logical.append(fill)
            logical.append(text)
            previous = t
        logical_line = ''.join(logical)
        assert logical_line.lstrip() == logical_line
        assert logical_line.rstrip() == logical_line
        return logical_line

    def pep8Expected(self):
        """
        Public method to replicate logic in pep8.py, to know what level to
        indent things to.

        @return list of lists, where each list represents valid indent levels
        for the line in question, relative from the initial indent. However,
        the first entry is the indent level which was expected.
        """
        # What follows is an adjusted version of
        # pep8.py:continuation_line_indentation. All of the comments have been
        # stripped and the 'yield' statements replaced with 'pass'.
        if not self.tokens:
            return

        first_row = self.tokens[0][2][0]
        nrows = 1 + self.tokens[-1][2][0] - first_row

        # here are the return values
        valid_indents = [list()] * nrows
        indent_level = self.tokens[0][2][1]
        valid_indents[0].append(indent_level)

        if nrows == 1:
            # bug, really.
            return valid_indents

        indent_next = self.logical_line.endswith(':')

        row = depth = 0
        parens = [0] * nrows
        self.rel_indent = rel_indent = [0] * nrows
        indent = [indent_level]
        indent_chances = {}
        last_indent = (0, 0)
        last_token_multiline = None

        for token_type, text, start, end, line in self.tokens:
            newline = row < start[0] - first_row
            if newline:
                row = start[0] - first_row
                newline = (not last_token_multiline and
                           token_type not in (tokenize.NL, tokenize.NEWLINE))

            if newline:
                # This is where the differences start. Instead of looking at
                # the line and determining whether the observed indent matches
                # our expectations, we decide which type of indentation is in
                # use at the given indent level, and return the offset. This
                # algorithm is susceptible to "carried errors", but should
                # through repeated runs eventually solve indentation for
                # multiline expressions.

                if depth:
                    for open_row in range(row - 1, -1, -1):
                        if parens[open_row]:
                            break
                else:
                    open_row = 0

                # That's all we get to work with. This code attempts to
                # "reverse" the below logic, and place into the valid indents
                # list
                vi = []
                add_second_chances = False
                if token_type == tokenize.OP and text in ']})':
                    # this line starts with a closing bracket, so it needs to
                    # be closed at the same indent as the opening one.
                    if indent[depth]:
                        # hanging indent
                        vi.append(indent[depth])
                    else:
                        # visual indent
                        vi.append(indent_level + rel_indent[open_row])
                elif depth and indent[depth]:
                    # visual indent was previously confirmed.
                    vi.append(indent[depth])
                    add_second_chances = True
                elif depth and True in indent_chances.values():
                    # visual indent happened before, so stick to
                    # visual indent this time.
                    if depth > 1 and indent[depth - 1]:
                        vi.append(indent[depth - 1])
                    else:
                        # stupid fallback
                        vi.append(indent_level + 4)
                    add_second_chances = True
                elif not depth:
                    vi.append(indent_level + 4)
                else:
                    # must be in hanging indent
                    hang = rel_indent[open_row] + 4
                    vi.append(indent_level + hang)

                # about the best we can do without look-ahead
                if (indent_next and vi[0] == indent_level + 4 and
                        nrows == row + 1):
                    vi[0] += 4

                if add_second_chances:
                    # visual indenters like to line things up.
                    min_indent = vi[0]
                    for col, what in indent_chances.items():
                        if col > min_indent and (
                            what is True or
                            (what == str and token_type == tokenize.STRING) or
                            (what == text and token_type == tokenize.OP)
                        ):
                            vi.append(col)
                    vi = sorted(vi)

                valid_indents[row] = vi

                # Returning to original continuation_line_indentation() from
                # pep8.
                visual_indent = indent_chances.get(start[1])
                last_indent = start
                rel_indent[row] = pep8.expand_indent(line) - indent_level
                hang = rel_indent[row] - rel_indent[open_row]

                if token_type == tokenize.OP and text in ']})':
                    pass
                elif visual_indent is True:
                    if not indent[depth]:
                        indent[depth] = start[1]

            # line altered: comments shouldn't define a visual indent
            if parens[row] and not indent[depth] and token_type not in (
                tokenize.NL, tokenize.COMMENT
            ):
                indent[depth] = start[1]
                indent_chances[start[1]] = True
            elif token_type == tokenize.STRING or text in (
                'u', 'ur', 'b', 'br'
            ):
                indent_chances[start[1]] = str

            if token_type == tokenize.OP:
                if text in '([{':
                    depth += 1
                    indent.append(0)
                    parens[row] += 1
                elif text in ')]}' and depth > 0:
                    prev_indent = indent.pop() or last_indent[1]
                    for d in range(depth):
                        if indent[d] > prev_indent:
                            indent[d] = 0
                    for ind in list(indent_chances):
                        if ind >= prev_indent:
                            del indent_chances[ind]
                    depth -= 1
                    if depth and indent[depth]:  # modified
                        indent_chances[indent[depth]] = True
                    for idx in range(row, -1, -1):
                        if parens[idx]:
                            parens[idx] -= 1
                            break
                assert len(indent) == depth + 1
                if start[1] not in indent_chances:
                    indent_chances[start[1]] = text

            last_token_multiline = (start[0] != end[0])

        return valid_indents


class LineShortener(object):
    """
    Class used to shorten lines to a given maximum of characters.
    """
    def __init__(self, curLine, prevLine, nextLine, maxLength=79, eol="\n",
                 indentWord="    ", isDocString=False):
        """
        Constructor
        
        @param curLine text to work on (string)
        @param prevLine line before the text to work on (string)
        @param nextLine line after the text to work on (string)
        @keyparam maxLength maximum allowed line length (integer)
        @keyparam eol eond-of-line marker (string)
        @keyparam indentWord string used for indentation (string)
        @keyparam isDocString flag indicating that the line belongs to
            a documentation string (boolean)
        """
        self.__text = curLine
        self.__prevText = prevLine
        self.__nextText = nextLine
        self.__maxLength = maxLength
        self.__eol = eol
        self.__indentWord = indentWord
        self.__isDocString = isDocString
    
    def shorten(self):
        """
        Public method to shorten the line wrapped by the class instance.
        
        @return tuple of a flag indicating successful shortening, the
            shortened line and the changed next line (boolean, string, string)
        """
        # 1. check for comment
        if self.__text.lstrip().startswith('#'):
            lastComment = True
            if self.__nextText.lstrip().startswith('#'):
                lastComment = False

            # Wrap commented lines.
            newText = self.__shortenComment(lastComment)
            if newText == self.__text:
                return False, "", ""
            else:
                return True, newText, ""
        elif '#' in self.__text:
            pos = self.__text.rfind("#")
            newText = self.__text[:pos].rstrip() + self.__eol + \
                self.__getIndent(self.__text) + self.__text[pos:]
            if newText == self.__text:
                return False, "", ""
            else:
                return True, newText, ""

        # Do multi line doc strings
        if self.__isDocString:
            source = self.__text.rstrip()
            blank = source.rfind(" ")
            while blank > self.__maxLength and blank != -1:
                blank = source.rfind(" ", 0, blank)
            if blank == -1:
                # Cannot break
                return False, "", ""
            else:
                first = self.__text[:blank]
                second = self.__text[blank:].lstrip()
                if self.__nextText.strip():
                    if self.__nextText.lstrip().startswith("@"):
                        # eric doc comment
                        # create a new line and indent it
                        newText = first + self.__eol + \
                            self.__getIndent(first) + self.__indentWord + \
                            second
                        newNext = ""
                    else:
                        newText = first + self.__eol
                        newNext = self.__getIndent(self.__nextText) + \
                            second.rstrip() + " " + self.__nextText.lstrip()
                else:
                    # empty line, add a new line
                    newText = first + self.__eol + self.__getIndent(first) + \
                        second
                    newNext = ""
            return True, newText, newNext
        
        indent = self.__getIndent(self.__text)
        source = self.__text[len(indent):]
        assert source.lstrip() == source
        sio = StringIO(source)
        
        # Check for multi line string.
        try:
            tokens = list(tokenize.generate_tokens(sio.readline))
        except (SyntaxError, tokenize.TokenError):
            if source.rstrip().endswith("\\"):
                # just join the continuation line and let the next run
                # handle it once it tokenizes ok
                newText = indent + source.rstrip()[:-1].rstrip() + " " + \
                    self.__nextText.lstrip()
                if indent:
                    newNext = indent
                else:
                    newNext = " "
                return True, newText, newNext
            else:
                multilineCandidate = self.__breakMultiline()
                if multilineCandidate:
                    return True, multilineCandidate[0], multilineCandidate[1]
                else:
                    return False, "", ""

        # Handle statements by putting the right hand side on a line by itself.
        # This should let the next pass shorten it.
        if source.startswith('return '):
            newText = (
                indent +
                'return (' +
                self.__eol +
                indent + self.__indentWord + re.sub('^return ', '', source) +
                indent + ')' + self.__eol
            )
            return True, newText, ""
        
        candidates = self.__shortenLine(tokens, source, indent)
        if candidates:
            candidates = list(sorted(
                set(candidates).union([self.__text]),
                key=lambda x: self.__lineShorteningRank(x)))
            if candidates[0] == self.__text:
                return False, "", ""
            return True, candidates[0], ""
        
        source = self.__text
        rs = source.rstrip()
        if rs.endswith(("'", '"')) and " " in source:
            if rs.endswith(('"""', "'''")):
                quote = rs[-3:]
            else:
                quote = rs[-1]
            blank = source.rfind(" ")
            maxLen = self.__maxLength - 2 - len(quote)
            while blank > maxLen and blank != -1:
                blank = source.rfind(" ", 0, blank)
            if blank != -1:
                if source[blank + 1:].startswith(quote):
                    first = source[:maxLen]
                    second = source[maxLen:]
                else:
                    first = source[:blank]
                    second = source[blank + 1:]
                return (
                    True,
                    first + quote + " \\" + self.__eol +
                    indent + self.__indentWord + quote + second,
                    "")
            else:
                # Cannot break
                return False, "", ""
        
        return False, "", ""
    
    def __shortenComment(self, isLast):
        """
        Private method to shorten a comment line.
        
        @param isLast flag indicating, that the line is the last comment line
            (boolean)
        @return shortened comment line (string)
        """
        if len(self.__text) <= self.__maxLength:
            return self.__text
        
        newText = self.__text.rstrip()

        # PEP 8 recommends 72 characters for comment text.
        indentation = self.__getIndent(newText) + '# '
        maxLength = min(self.__maxLength,
                        len(indentation) + 72)

        MIN_CHARACTER_REPEAT = 5
        if len(newText) - len(newText.rstrip(newText[-1])) >= \
                MIN_CHARACTER_REPEAT and \
                not newText[-1].isalnum():
            # Trim comments that end with things like ---------
            return newText[:maxLength] + self.__eol
        elif isLast and re.match(r"\s*#+\s*\w+", newText):
            import textwrap
            splitLines = textwrap.wrap(newText.lstrip(" \t#"),
                                       initial_indent=indentation,
                                       subsequent_indent=indentation,
                                       width=maxLength,
                                       break_long_words=False,
                                       break_on_hyphens=False)
            return self.__eol.join(splitLines) + self.__eol
        else:
            return newText + self.__eol
    
    def __breakMultiline(self):
        """
        Private method to break multi line strings.
        
        @return tuple of the shortened line and the changed next line
            (string, string)
        """
        indentation = self.__getIndent(self.__text)

        # Handle special case.
        for symbol in '([{':
            # Only valid if symbol is not on a line by itself.
            if (
                symbol in self.__text and
                self.__text.strip() != symbol and
                self.__text.rstrip().endswith((',', '%'))
            ):
                index = 1 + self.__text.find(symbol)

                if index <= len(self.__indentWord) + len(indentation):
                    continue

                if self.__isProbablyInsideStringOrComment(
                        self.__text, index - 1):
                    continue

                return (self.__text[:index].rstrip() + self.__eol +
                        indentation + self.__indentWord +
                        self.__text[index:].lstrip(), "")
        
        newText = self.__text
        newNext = self.__nextText
        blank = newText.rfind(" ")
        while blank > self.__maxLength and blank != -1:
            blank = newText.rfind(" ", 0, blank)
        if blank != -1:
            first = self.__text[:blank]
            second = self.__text[blank:].strip()
            if newNext.strip():
                newText = first + self.__eol
                if second.endswith(")"):
                    # don't merge with next line
                    newText += self.__getIndent(newText) + second + self.__eol
                    newNext = ""
                else:
                    newNext = self.__getIndent(newNext) + \
                        second + " " + newNext.lstrip()
            else:
                # empty line, add a new line
                newText = first + self.__eol
                newNext = self.__getIndent(newNext) + \
                    second + self.__eol + newNext.lstrip()
            return newText, newNext
        else:
            return None
    
    def __isProbablyInsideStringOrComment(self, line, index):
        """
        Private method to check, if the given string might be inside a string
        or comment.
        
        @param line line to check (string)
        @param index position inside line to check (integer)
        @return flag indicating the possibility of being inside a string
            or comment
        """
        # Check against being in a string.
        for quote in ['"', "'"]:
            pos = line.find(quote)
            if pos != -1 and pos <= index:
                return True

        # Check against being in a comment.
        pos = line.find('#')
        if pos != -1 and pos <= index:
            return True

        return False
    
    def __shortenLine(self, tokens, source, indent):
        """
        Private method to shorten a line of code at an operator.
        
        @param tokens tokens of the line as generated by tokenize
            (list of token)
        @param source code string to work at (string)
        @param indent indentation string of the code line (string)
        @return list of candidates (list of string)
        """
        candidates = []
        
        for tkn in tokens:
            tokenType = tkn[0]
            tokenString = tkn[1]

            if (
                tokenType == tokenize.COMMENT and
                not self.__prevText.rstrip().endswith('\\')
            ):
                # Move inline comments to previous line.
                offset = tkn[2][1]
                first = source[:offset]
                second = source[offset:]
                candidates.append(
                    indent + second.strip() + self.__eol +
                    indent + first.strip() + self.__eol)
            elif tokenType == tokenize.OP and tokenString != '=':
                # Don't break on '=' after keyword as this violates PEP 8.

                assert tokenType != tokenize.INDENT

                offset = tkn[2][1] + 1
                first = source[:offset]

                secondIndent = indent
                if first.rstrip().endswith('('):
                    secondIndent += self.__indentWord
                elif '(' in first:
                    secondIndent += ' ' * (1 + first.find('('))
                else:
                    secondIndent += self.__indentWord

                second = (secondIndent + source[offset:].lstrip())
                if not second.strip():
                    continue

                # Do not begin a line with a comma
                if second.lstrip().startswith(','):
                    continue
                
                # Do end a line with a dot
                if first.rstrip().endswith('.'):
                    continue
                
                if tokenString in '+-*/,':
                    newText = first + ' \\' + self.__eol + second
                else:
                    newText = first + self.__eol + second

                # Only fix if syntax is okay.
                if self.__checkSyntax(self.__normalizeMultiline(newText)):
                    candidates.append(indent + newText)
        
        return candidates
    
    def __normalizeMultiline(self, text):
        """
        Private method to remove multiline-related code that will cause syntax
        error.
        
        @param text code line to work on (string)
        @return normalized code line (string)
        """
        for quote in '\'"':
            dictPattern = r"^{q}[^{q}]*{q} *: *".format(q=quote)
            if re.match(dictPattern, text):
                if not text.strip().endswith('}'):
                    text += '}'
                return '{' + text

        if text.startswith('def ') and text.rstrip().endswith(':'):
            # Do not allow ':' to be alone. That is invalid.
            splitText = [item.strip() for item in text.split(self.__eol)]
            if ':' not in splitText and 'def' not in splitText:
                return text[len('def'):].strip().rstrip(':')

        return text
    
    def __lineShorteningRank(self, candidate):
        """
        Private method to rank a candidate.
        
        @param candidate candidate line to rank (string)
        @return rank of the candidate (integer)
        """
        rank = 0
        if candidate.strip():
            if candidate == self.__text:
                # give the original a disadvantage
                rank += 50
            
            lines = candidate.split(self.__eol)

            offset = 0
            if lines[0].rstrip()[-1] not in '([{':
                for symbol in '([{':
                    offset = max(offset, 1 + lines[0].find(symbol))

            maxLength = max([offset + len(x.strip()) for x in lines])
            rank += maxLength
            rank += len(lines)

            badStartingSymbol = {
                '(': ')',
                '[': ']',
                '{': '}'}.get(lines[0][-1], None)

            if len(lines) > 1:
                if (badStartingSymbol and
                        lines[1].lstrip().startswith(badStartingSymbol)):
                    rank += 20

            if re.match(r".*[+\-\*/] \($", lines[0]):
                # "1 * (\n" is ugly as hell.
                rank += 100

            for currentLine in lines:
                for badStart in ['.', '%', '+', '-', '/']:
                    if currentLine.startswith(badStart):
                        rank += 100

                for ending in '([{':
                    # Avoid lonely opening. They result in longer lines.
                    if currentLine.endswith(ending) and \
                            len(currentLine.strip()) <= len(self.__indentWord):
                        rank += 100

                if currentLine.endswith('%'):
                    rank -= 20

                # Try to break list comprehensions at the "for".
                if currentLine.lstrip().startswith('for'):
                    rank -= 50

                rank += 10 * self.__countUnbalancedBrackets(currentLine)
        else:
            rank = 100000
        
        return max(0, rank)
    
    def __countUnbalancedBrackets(self, line):
        """
        Private method to determine the number of unmatched open/close
        brackets.
        
        @param line line to work at (string)
        @return number of unmatched open/close brackets (integer)
        """
        count = 0
        for opening, closing in ['()', '[]', '{}']:     # __IGNORE_WARNING__
            count += abs(line.count(opening) - line.count(closing))
        
        return count
    
    def __getIndent(self, line):
        """
        Private method to get the indentation string.
        
        @param line line to determine the indentation string from (string)
        @return indentation string (string)
        """
        # copied from CodeStyleFixer
        return line.replace(line.lstrip(), "")
    
    def __checkSyntax(self, code):
        """
        Private method to check the syntax of the given code fragment.
        
        @param code code fragment to check (string)
        @return flag indicating syntax is ok (boolean)
        """
        code = code.replace("\r\n", "\n").replace("\r", "\n")
        try:
            return compile(code, '<string>', 'exec')
        except (SyntaxError, TypeError, UnicodeDecodeError):
            return False
