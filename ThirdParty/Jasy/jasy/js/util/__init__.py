#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
#

#
# minimized for using just the parser within eric6
# Copyright (c) 2013 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

from __future__ import unicode_literals

pseudoTypes = set(["any", "var", "undefined", "null", "true", "false", "this",
                   "arguments"])
builtinTypes = set(["Object", "String", "Number", "Boolean", "Array", "Function",
                    "RegExp", "Date"])
