# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the PyQt5 server part of the QRegularExpression wizzard.
"""

from __future__ import unicode_literals

import json
import sys


def rxValidate(regexp, options):
    """
    Function to validate the given regular expression.
    
    @param regexp regular expression to validate (string)
    @param options list of options (list of string)
    @return tuple of flag indicating validity (boolean), error
        string (string) and error offset (integer)
    """
    try:
        from PyQt5.QtCore import QRegularExpression
        rxOptions = QRegularExpression.NoPatternOption
        if "CaseInsensitiveOption" in options:
            rxOptions |= QRegularExpression.CaseInsensitiveOption
        if "MultilineOption" in options:
            rxOptions |= QRegularExpression.MultilineOption
        if "DotMatchesEverythingOption" in options:
            rxOptions |= QRegularExpression.DotMatchesEverythingOption
        if "ExtendedPatternSyntaxOption" in options:
            rxOptions |= QRegularExpression.ExtendedPatternSyntaxOption
        if "InvertedGreedinessOption" in options:
            rxOptions |= QRegularExpression.InvertedGreedinessOption
        if "UseUnicodePropertiesOption" in options:
            rxOptions |= QRegularExpression.UseUnicodePropertiesOption
        if "DontCaptureOption" in options:
            rxOptions |= QRegularExpression.DontCaptureOption
        
        error = ""
        errorOffset = -1
        re = QRegularExpression(regexp, rxOptions)
        valid = re.isValid()
        if not valid:
            error = re.errorString()
            errorOffset = re.patternErrorOffset()
    except ImportError:
        valid = False
        error = "ImportError"
        errorOffset = 0
    
    return valid, error, errorOffset


def rxExecute(regexp, options, text, startpos):
    """
    Function to execute the given regular expression for a given text.
    
    @param regexp regular expression to validate (string)
    @param options list of options (list of string)
    @param text text to execute on (string)
    @param startpos start position for the execution (integer)
    @return tuple of a flag indicating a successful match (boolean) and
        a list of captures containing the complete match as matched string
        (string), match start (integer), match end (integer) and match length
        (integer) for each entry
    """
    valid, error, errorOffset = rxValidate(regexp, options)
    if not valid:
        return valid, error, errorOffset
    
    from PyQt5.QtCore import QRegularExpression
    rxOptions = QRegularExpression.NoPatternOption
    if "CaseInsensitiveOption" in options:
        rxOptions |= QRegularExpression.CaseInsensitiveOption
    if "MultilineOption" in options:
        rxOptions |= QRegularExpression.MultilineOption
    if "DotMatchesEverythingOption" in options:
        rxOptions |= QRegularExpression.DotMatchesEverythingOption
    if "ExtendedPatternSyntaxOption" in options:
        rxOptions |= QRegularExpression.ExtendedPatternSyntaxOption
    if "InvertedGreedinessOption" in options:
        rxOptions |= QRegularExpression.InvertedGreedinessOption
    if "UseUnicodePropertiesOption" in options:
        rxOptions |= QRegularExpression.UseUnicodePropertiesOption
    if "DontCaptureOption" in options:
        rxOptions |= QRegularExpression.DontCaptureOption
    
    matched = False
    captures = []
    re = QRegularExpression(regexp, rxOptions)
    match = re.match(text, startpos)
    if match.hasMatch():
        matched = True
        for index in range(match.lastCapturedIndex() + 1):
            captures.append([
                match.captured(index),
                match.capturedStart(index),
                match.capturedEnd(index),
                match.capturedLength(index)
            ])
    
    return matched, captures


def main():
    """
    Function containing the main routine.
    """
    while True:
        commandStr = sys.stdin.readline()
        try:
            commandDict = json.loads(commandStr)
            responseDict = {"error": ""}
            if "command" in commandDict:
                command = commandDict["command"]
                if command == "exit":
                    break
                elif command == "available":
                    try:
                        import PyQt5    # __IGNORE_WARNING__
                        responseDict["available"] = True
                    except ImportError:
                        responseDict["available"] = False
                elif command == "validate":
                    valid, error, errorOffset = rxValidate(
                        commandDict["regexp"], commandDict["options"])
                    responseDict["valid"] = valid
                    responseDict["errorMessage"] = error
                    responseDict["errorOffset"] = errorOffset
                elif command == "execute":
                    valid, error, errorOffset = rxValidate(
                        commandDict["regexp"], commandDict["options"])
                    if not valid:
                        responseDict["valid"] = valid
                        responseDict["errorMessage"] = error
                        responseDict["errorOffset"] = errorOffset
                    else:
                        matched, captures = rxExecute(
                            commandDict["regexp"], commandDict["options"],
                            commandDict["text"], commandDict["startpos"])
                        responseDict["matched"] = matched
                        responseDict["captures"] = captures
        except ValueError as err:
            responseDict = {"error": str(err)}
        except Exception as err:
            responseDict = {"error": str(err)}
        responseStr = json.dumps(responseDict)
        sys.stdout.write(responseStr)
        sys.stdout.flush()
    
    sys.exit(0)


if __name__ == "__main__":
    main()
