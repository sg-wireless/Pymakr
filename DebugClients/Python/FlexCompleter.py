# -*- coding: utf-8 -*-

"""
Word completion for the eric6 shell.

<h4>NOTE for eric6 variant</h4>

    This version is a re-implementation of FlexCompleter
    as found in the PyQwt package. It is modified to work with the eric6 debug
    clients.


<h4>NOTE for the PyQwt variant</h4>

    This version is a re-implementation of FlexCompleter
    with readline support for PyQt&sip-3.6 and earlier.

    Full readline support is present in PyQt&sip-snapshot-20030531 and later.


<h4>NOTE for FlexCompleter</h4>

    This version is a re-implementation of rlcompleter with
    selectable namespace.

    The problem with rlcompleter is that it's hardwired to work with
    __main__.__dict__, and in some cases one may have 'sandboxed' namespaces.
    So this class is a ripoff of rlcompleter, with the namespace to work in as
    an optional parameter.
    
    This class can be used just like rlcompleter, but the Completer class now
    has a constructor with the optional 'namespace' parameter.
    
    A patch has been submitted to Python@sourceforge for these changes to go in
    the standard Python distribution.


<h4>Original rlcompleter documentation</h4>

    This requires the latest extension to the readline module (the
    completes keywords, built-ins and globals in __main__; when completing
    NAME.NAME..., it evaluates (!) the expression up to the last dot and
    completes its attributes.
    
    It's very cool to do "import string" type "string.", hit the
    completion key (twice), and see the list of names defined by the
    string module!
    
    Tip: to use the tab key as the completion key, call
    
    'readline.parse_and_bind("tab: complete")'
    
    <b>Notes</b>:
    <ul>
    <li>
    Exceptions raised by the completer function are *ignored* (and
    generally cause the completion to fail).  This is a feature -- since
    readline sets the tty device in raw (or cbreak) mode, printing a
    traceback wouldn't work well without some complicated hoopla to save,
    reset and restore the tty state.
    </li>
    <li>
    The evaluation of the NAME.NAME... form may cause arbitrary
    application defined code to be executed if an object with a
    __getattr__ hook is found.  Since it is the responsibility of the
    application (or the user) to enable this feature, I consider this an
    acceptable risk.  More complicated expressions (e.g. function calls or
    indexing operations) are *not* evaluated.
    </li>
    <li>
    GNU readline is also used by the built-in functions input() and
    raw_input(), and thus these also benefit/suffer from the completer
    features.  Clearly an interactive application can benefit by
    specifying its own completer function and using raw_input() for all
    its input.
    </li>
    <li>
    When the original stdin is not a tty device, GNU readline is never
    used, and this module (and the readline module) are silently inactive.
    </li>
    </ul>
"""

#*****************************************************************************
#
# Since this file is essentially a minimally modified copy of the rlcompleter
# module which is part of the standard Python distribution, I assume that the
# proper procedure is to maintain its copyright as belonging to the Python
# Software Foundation:
#
#       Copyright (C) 2001 Python Software Foundation, www.python.org
#
#  Distributed under the terms of the Python Software Foundation license.
#
#  Full text available at:
#
#                  http://www.python.org/2.1/license.html
#
#*****************************************************************************

import __builtin__
import __main__

__all__ = ["Completer"]


class Completer(object):
    """
    Class implementing the command line completer object.
    """
    def __init__(self, namespace=None):
        """
        Constructor

        Completer([namespace]) -> completer instance.

        If unspecified, the default namespace where completions are performed
        is __main__ (technically, __main__.__dict__). Namespaces should be
        given as dictionaries.

        Completer instances should be used as the completion mechanism of
        readline via the set_completer() call:

        readline.set_completer(Completer(my_namespace).complete)
        
        @param namespace namespace for the completer
        @exception TypeError raised to indicate a wrong namespace structure
        """
        if namespace and not isinstance(namespace, dict):
            raise TypeError('namespace must be a dictionary')

        # Don't bind to namespace quite yet, but flag whether the user wants a
        # specific namespace or to use __main__.__dict__. This will allow us
        # to bind to __main__.__dict__ at completion time, not now.
        if namespace is None:
            self.use_main_ns = 1
        else:
            self.use_main_ns = 0
            self.namespace = namespace

    def complete(self, text, state):
        """
        Public method to return the next possible completion for 'text'.

        This is called successively with state == 0, 1, 2, ... until it
        returns None.  The completion should begin with 'text'.
        
        @param text The text to be completed. (string)
        @param state The state of the completion. (integer)
        @return The possible completions as a list of strings.
        """
        if self.use_main_ns:
            self.namespace = __main__.__dict__
            
        if state == 0:
            if "." in text:
                self.matches = self.attr_matches(text)
            else:
                self.matches = self.global_matches(text)
        try:
            return self.matches[state]
        except IndexError:
            return None

    def global_matches(self, text):
        """
        Public method to compute matches when text is a simple name.

        @param text The text to be completed. (string)
        @return A list of all keywords, built-in functions and names currently
        defined in self.namespace that match.
        """
        import keyword
        matches = []
        n = len(text)
        for list in [keyword.kwlist,
                     __builtin__.__dict__.keys(),
                     self.namespace.keys()]:
            for word in list:
                if word[:n] == text and \
                   word != "__builtins__" and \
                   word not in matches:
                    matches.append(word)
        return matches

    def attr_matches(self, text):
        """
        Public method to compute matches when text contains a dot.

        Assuming the text is of the form NAME.NAME....[NAME], and is
        evaluatable in self.namespace, it will be evaluated and its attributes
        (as revealed by dir()) are used as possible completions.  (For class
        instances, class members are are also considered.)

        <b>WARNING</b>: this can still invoke arbitrary C code, if an object
        with a __getattr__ hook is evaluated.
        
        @param text The text to be completed. (string)
        @return A list of all matches.
        """
        import re

    # Testing. This is the original code:
    #m = re.match(r"(\w+(\.\w+)*)\.(\w*)", text)

    # Modified to catch [] in expressions:
    #m = re.match(r"([\w\[\]]+(\.[\w\[\]]+)*)\.(\w*)", text)

        # Another option, seems to work great. Catches things like ''.<tab>
        m = re.match(r"(\S+(\.\w+)*)\.(\w*)", text)

        if not m:
            return
        expr, attr = m.group(1, 3)
        object = eval(expr, self.namespace)
        words = dir(object)
        if hasattr(object, '__class__'):
            words.append('__class__')
            words = words + get_class_members(object.__class__)
        matches = []
        n = len(attr)
        for word in words:
            try:
                if word[:n] == attr and word != "__builtins__":
                    match = "%s.%s" % (expr, word)
                    if match not in matches:
                        matches.append(match)
            except:
                # some badly behaved objects pollute dir() with non-strings,
                # which cause the completion to fail.  This way we skip the
                # bad entries and can still continue processing the others.
                pass
        return matches


def get_class_members(klass):
    """
    Module function to retrieve the class members.
    
    @param klass The class object to be analysed.
    @return A list of all names defined in the class.
    """
    # PyQwt's hack for PyQt&sip-3.6 and earlier
    if hasattr(klass, 'getLazyNames'):
        return klass.getLazyNames()
    # vanilla Python stuff
    ret = dir(klass)
    if hasattr(klass, '__bases__'):
        for base in klass.__bases__:
            ret = ret + get_class_members(base)
    return ret

#
# eflag: FileType = Python2
