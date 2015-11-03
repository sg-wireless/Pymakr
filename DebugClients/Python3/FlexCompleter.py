# -*- coding: utf-8 -*-

"""
Word completion for the eric6 shell.

<h4>NOTE for eric6 variant</h4>

    This version is a re-implementation of rlcompleter
    as found in the Python3 library. It is modified to work with the eric6
    debug clients.

<h4>Original rlcompleter documentation</h4>

    This requires the latest extension to the readline module. The completer
    completes keywords, built-ins and globals in a selectable namespace (which
    defaults to __main__); when completing NAME.NAME..., it evaluates (!) the
    expression up to the last dot and completes its attributes.

    It's very cool to do "import sys" type "sys.", hit the
    completion key (twice), and see the list of names defined by the
    sys module!

    Tip: to use the tab key as the completion key, call

        readline.parse_and_bind("tab: complete")

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
    When the original stdin is not a tty device, GNU readline is never
    used, and this module (and the readline module) are silently inactive.
    </li>
    </ul>
"""

import builtins
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
        
        @param namespace The namespace for the completer.
        @exception TypeError raised to indicate a wrong data structure of
            the namespace object
        """
        if namespace and not isinstance(namespace, dict):
            raise TypeError('namespace must be a dictionary')

        # Don't bind to namespace quite yet, but flag whether the user wants a
        # specific namespace or to use __main__.__dict__. This will allow us
        # to bind to __main__.__dict__ at completion time, not now.
        if namespace is None:
            self.use_main_ns = True
        else:
            self.use_main_ns = False
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

    def _callable_postfix(self, val, word):
        """
        Protected method to check for a callable.
        
        @param val value to check (object)
        @param word word to ammend (string)
        @return ammended word (string)
        """
        if hasattr(val, '__call__'):
            word = word + "("
        return word

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
        for word in keyword.kwlist:
            if word[:n] == text:
                matches.append(word)
        for nspace in [builtins.__dict__, self.namespace]:
            for word, val in nspace.items():
                if word[:n] == text and word != "__builtins__":
                    matches.append(self._callable_postfix(val, word))
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

        # Another option, seems to work great. Catches things like ''.<tab>
        m = re.match(r"(\S+(\.\w+)*)\.(\w*)", text)

        if not m:
            return
        expr, attr = m.group(1, 3)
        try:
            thisobject = eval(expr, self.namespace)
        except Exception:
            return []

        # get the content of the object, except __builtins__
        words = dir(thisobject)
        if "__builtins__" in words:
            words.remove("__builtins__")

        if hasattr(object, '__class__'):
            words.append('__class__')
            words = words + get_class_members(object.__class__)
        matches = []
        n = len(attr)
        for word in words:
            try:
                if word[:n] == attr and hasattr(thisobject, word):
                    val = getattr(thisobject, word)
                    word = self._callable_postfix(
                        val, "{0}.{1}".format(expr, word))
                    matches.append(word)
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
    ret = dir(klass)
    if hasattr(klass, '__bases__'):
        for base in klass.__bases__:
            ret = ret + get_class_members(base)
    return ret
