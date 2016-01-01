# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Parse a Ruby file and retrieve classes, modules, methods and attributes.

Parse enough of a Ruby file to recognize class, module and method definitions
and to find out the superclasses of a class as well as its attributes.

It is based on the Python class browser found in this package.
"""

from __future__ import unicode_literals

import re

import Utilities
import Utilities.ClassBrowsers as ClassBrowsers
from . import ClbrBaseClasses

SUPPORTED_TYPES = [ClassBrowsers.RB_SOURCE]
    
_getnext = re.compile(
r"""
    (?P<String>
        =begin .*? =end
    
    |   <<-? (?P<HereMarker1> [a-zA-Z0-9_]+? ) [ \t]* .*? (?P=HereMarker1)

    |   <<-? ['"] (?P<HereMarker2> [^'"]+? ) ['"] [ \t]* .*? (?P=HereMarker2)

    |   " [^"\\\n]* (?: \\. [^"\\\n]*)* "

    |   ' [^'\\\n]* (?: \\. [^'\\\n]*)* '
    )

|   (?P<CodingLine>
        ^ \# \s* [*_-]* \s* coding[:=] \s* (?P<Coding> [-\w_.]+ ) \s* [*_-]* $
    )

|   (?P<Comment>
        ^
        [ \t]* \#+ .*? $
    )

|   (?P<Method>
        ^
        (?P<MethodIndent> [ \t]* )
        def [ \t]+
        (?:
            (?P<MethodName2> [a-zA-Z0-9_]+ (?: \. | :: )
            [a-zA-Z_] [a-zA-Z0-9_?!=]* )
        |
            (?P<MethodName> [a-zA-Z_] [a-zA-Z0-9_?!=]* )
        |
            (?P<MethodName3> [^( \t]{1,3} )
        )
        [ \t]*
        (?:
            \( (?P<MethodSignature> (?: [^)] | \)[ \t]*,? )*? ) \)
        )?
        [ \t]*
    )

|   (?P<Class>
        ^
        (?P<ClassIndent> [ \t]* )
        class
        (?:
            [ \t]+
            (?P<ClassName> [A-Z] [a-zA-Z0-9_]* )
            [ \t]*
            (?P<ClassSupers> < [ \t]* [A-Z] [a-zA-Z0-9_:]* )?
        |
            [ \t]* << [ \t]*
            (?P<ClassName2> [a-zA-Z_] [a-zA-Z0-9_:]* )
        )
        [ \t]*
    )

|   (?P<ClassIgnored>
        \(
        [ \t]*
        class
        .*?
        end
        [ \t]*
        \)
    )

|   (?P<Module>
        ^
        (?P<ModuleIndent> [ \t]* )
        module [ \t]+
        (?P<ModuleName> [A-Z] [a-zA-Z0-9_:]* )
        [ \t]*
    )

|   (?P<AccessControl>
        ^
        (?P<AccessControlIndent> [ \t]* )
        (?:
            (?P<AccessControlType> private | public | protected ) [^_]
        |
            (?P<AccessControlType2>
            private_class_method | public_class_method )
        )
        \(?
        [ \t]*
        (?P<AccessControlList> (?: : [a-zA-Z0-9_]+ , \s* )*
        (?: : [a-zA-Z0-9_]+ )+ )?
        [ \t]*
        \)?
    )

|   (?P<Attribute>
        ^
        (?P<AttributeIndent> [ \t]* )
        (?P<AttributeName> (?: @ | @@ ) [a-zA-Z0-9_]* )
        [ \t]* =
    )

|   (?P<Attr>
        ^
        (?P<AttrIndent> [ \t]* )
        attr
        (?P<AttrType> (?: _accessor | _reader | _writer ) )?
        \(?
        [ \t]*
        (?P<AttrList> (?: : [a-zA-Z0-9_]+ , \s* )*
        (?: : [a-zA-Z0-9_]+ | true | false )+ )
        [ \t]*
        \)?
    )

|   (?P<Begin>
            ^
            [ \t]*
            (?: def | if | unless | case | while | until | for | begin )
            \b [^_]
        |
            [ \t]* do [ \t]* (?: \| .*? \| )? [ \t]* $
    )

|   (?P<BeginEnd>
        \b (?: if ) \b [^_] .*? $
        |
        \b (?: if ) \b [^_] .*? end [ \t]* $
    )

|   (?P<End>
        [ \t]*
        (?:
            end [ \t]* $
        |
            end \b [^_]
        )
    )""",
    re.VERBOSE | re.DOTALL | re.MULTILINE).search

_commentsub = re.compile(r"""#[^\n]*\n|#[^\n]*$""").sub

_modules = {}                           # cache of modules we've seen


class VisibilityMixin(ClbrBaseClasses.ClbrVisibilityMixinBase):
    """
    Mixin class implementing the notion of visibility.
    """
    def __init__(self):
        """
        Constructor
        """
        self.setPublic()


class Class(ClbrBaseClasses.Class, VisibilityMixin):
    """
    Class to represent a Ruby class.
    """
    def __init__(self, module, name, super, file, lineno):
        """
        Constructor
        
        @param module name of the module containing this class
        @param name name of this class
        @param super list of class names this class is inherited from
        @param file filename containing this class
        @param lineno linenumber of the class definition
        """
        ClbrBaseClasses.Class.__init__(self, module, name, super, file, lineno)
        VisibilityMixin.__init__(self)


class Module(ClbrBaseClasses.Module, VisibilityMixin):
    """
    Class to represent a Ruby module.
    """
    def __init__(self, module, name, file, lineno):
        """
        Constructor
        
        @param module name of the module containing this class
        @param name name of this class
        @param file filename containing this class
        @param lineno linenumber of the class definition
        """
        ClbrBaseClasses.Module.__init__(self, module, name, file, lineno)
        VisibilityMixin.__init__(self)


class Function(ClbrBaseClasses.Function, VisibilityMixin):
    """
    Class to represent a Ruby function.
    """
    def __init__(self, module, name, file, lineno, signature='',
                 separator=','):
        """
        Constructor
        
        @param module name of the module containing this function
        @param name name of this function
        @param file filename containing this class
        @param lineno linenumber of the class definition
        @param signature parameterlist of the method
        @param separator string separating the parameters
        """
        ClbrBaseClasses.Function.__init__(self, module, name, file, lineno,
                                          signature, separator)
        VisibilityMixin.__init__(self)


class Attribute(ClbrBaseClasses.Attribute, VisibilityMixin):
    """
    Class to represent a class or module attribute.
    """
    def __init__(self, module, name, file, lineno):
        """
        Constructor
        
        @param module name of the module containing this class
        @param name name of this class
        @param file filename containing this attribute
        @param lineno linenumber of the class definition
        """
        ClbrBaseClasses.Attribute.__init__(self, module, name, file, lineno)
        VisibilityMixin.__init__(self)
        self.setPrivate()


def readmodule_ex(module, path=[]):
    """
    Read a Ruby file and return a dictionary of classes, functions and modules.

    @param module name of the Ruby file (string)
    @param path path the file should be searched in (list of strings)
    @return the resulting dictionary
    """
    global _modules
    
    dict = {}
    dict_counts = {}

    if module in _modules:
        # we've seen this file before...
        return _modules[module]

    # search the path for the file
    f = None
    fullpath = list(path)
    f, file, (suff, mode, type) = ClassBrowsers.find_module(module, fullpath)
    if f:
        f.close()
    if type not in SUPPORTED_TYPES:
        # not Ruby source, can't do anything with this module
        _modules[module] = dict
        return dict

    _modules[module] = dict
    classstack = []  # stack of (class, indent) pairs
    acstack = []    # stack of (access control, indent) pairs
    indent = 0
    try:
        src = Utilities.readEncodedFile(file)[0]
    except (UnicodeError, IOError):
        # can't do anything with this module
        _modules[module] = dict
        return dict

    lineno, last_lineno_pos = 1, 0
    cur_obj = None
    lastGlobalEntry = None
    i = 0
    while True:
        m = _getnext(src, i)
        if not m:
            break
        start, i = m.span()

        if m.start("Method") >= 0:
            # found a method definition or function
            thisindent = indent
            indent += 1
            meth_name = m.group("MethodName") or \
                m.group("MethodName2") or \
                m.group("MethodName3")
            meth_sig = m.group("MethodSignature")
            meth_sig = meth_sig and meth_sig.replace('\\\n', '') or ''
            meth_sig = _commentsub('', meth_sig)
            lineno = lineno + src.count('\n', last_lineno_pos, start)
            last_lineno_pos = start
            if meth_name.startswith('self.'):
                meth_name = meth_name[5:]
            elif meth_name.startswith('self::'):
                meth_name = meth_name[6:]
            # close all classes/modules indented at least as much
            while classstack and \
                    classstack[-1][1] >= thisindent:
                if classstack[-1][0] is not None:
                    # record the end line
                    classstack[-1][0].setEndLine(lineno - 1)
                del classstack[-1]
            while acstack and \
                    acstack[-1][1] >= thisindent:
                del acstack[-1]
            if classstack:
                # it's a class/module method
                cur_class = classstack[-1][0]
                if isinstance(cur_class, Class) or \
                        isinstance(cur_class, Module):
                    # it's a method
                    f = Function(None, meth_name,
                                 file, lineno, meth_sig)
                    cur_class._addmethod(meth_name, f)
                else:
                    f = cur_class
                # set access control
                if acstack:
                    accesscontrol = acstack[-1][0]
                    if accesscontrol == "private":
                        f.setPrivate()
                    elif accesscontrol == "protected":
                        f.setProtected()
                    elif accesscontrol == "public":
                        f.setPublic()
                # else it's a nested def
            else:
                # it's a function
                f = Function(module, meth_name,
                             file, lineno, meth_sig)
                if meth_name in dict_counts:
                    dict_counts[meth_name] += 1
                    meth_name = "{0}_{1:d}".format(
                        meth_name, dict_counts[meth_name])
                else:
                    dict_counts[meth_name] = 0
                dict[meth_name] = f
            if not classstack:
                if lastGlobalEntry:
                    lastGlobalEntry.setEndLine(lineno - 1)
                lastGlobalEntry = f
            if cur_obj and isinstance(cur_obj, Function):
                cur_obj.setEndLine(lineno - 1)
            cur_obj = f
            classstack.append((f, thisindent))  # Marker for nested fns

        elif m.start("String") >= 0:
            pass

        elif m.start("Comment") >= 0:
            pass

        elif m.start("ClassIgnored") >= 0:
            pass

        elif m.start("Class") >= 0:
            # we found a class definition
            thisindent = indent
            indent += 1
            lineno = lineno + src.count('\n', last_lineno_pos, start)
            last_lineno_pos = start
            # close all classes/modules indented at least as much
            while classstack and \
                    classstack[-1][1] >= thisindent:
                if classstack[-1][0] is not None:
                    # record the end line
                    classstack[-1][0].setEndLine(lineno - 1)
                del classstack[-1]
            class_name = m.group("ClassName") or m.group("ClassName2")
            inherit = m.group("ClassSupers")
            if inherit:
                # the class inherits from other classes
                inherit = inherit[1:].strip()
                inherit = [_commentsub('', inherit)]
            # remember this class
            cur_class = Class(module, class_name, inherit,
                              file, lineno)
            if not classstack:
                if class_name in dict:
                    cur_class = dict[class_name]
                else:
                    dict[class_name] = cur_class
            else:
                cls = classstack[-1][0]
                if class_name in cls.classes:
                    cur_class = cls.classes[class_name]
                elif cls.name == class_name or class_name == "self":
                    cur_class = cls
                else:
                    cls._addclass(class_name, cur_class)
            if not classstack:
                if lastGlobalEntry:
                    lastGlobalEntry.setEndLine(lineno - 1)
                lastGlobalEntry = cur_class
            cur_obj = cur_class
            classstack.append((cur_class, thisindent))
            while acstack and \
                    acstack[-1][1] >= thisindent:
                del acstack[-1]
            acstack.append(["public", thisindent])
            # default access control is 'public'

        elif m.start("Module") >= 0:
            # we found a module definition
            thisindent = indent
            indent += 1
            lineno = lineno + src.count('\n', last_lineno_pos, start)
            last_lineno_pos = start
            # close all classes/modules indented at least as much
            while classstack and \
                    classstack[-1][1] >= thisindent:
                if classstack[-1][0] is not None:
                    # record the end line
                    classstack[-1][0].setEndLine(lineno - 1)
                del classstack[-1]
            module_name = m.group("ModuleName")
            # remember this class
            cur_class = Module(module, module_name, file, lineno)
            if not classstack:
                if module_name in dict:
                    cur_class = dict[module_name]
                else:
                    dict[module_name] = cur_class
            else:
                cls = classstack[-1][0]
                if module_name in cls.classes:
                    cur_class = cls.classes[module_name]
                elif cls.name == module_name:
                    cur_class = cls
                else:
                    cls._addclass(module_name, cur_class)
            if not classstack:
                if lastGlobalEntry:
                    lastGlobalEntry.setEndLine(lineno - 1)
                lastGlobalEntry = cur_class
            cur_obj = cur_class
            classstack.append((cur_class, thisindent))
            while acstack and \
                    acstack[-1][1] >= thisindent:
                del acstack[-1]
            acstack.append(["public", thisindent])
            # default access control is 'public'

        elif m.start("AccessControl") >= 0:
            aclist = m.group("AccessControlList")
            if aclist is None:
                index = -1
                while index >= -len(acstack):
                    if acstack[index][1] < indent:
                        actype = m.group("AccessControlType") or \
                            m.group("AccessControlType2").split('_')[0]
                        acstack[index][0] = actype.lower()
                        break
                    else:
                        index -= 1
            else:
                index = -1
                while index >= -len(classstack):
                    if classstack[index][0] is not None and \
                       not isinstance(classstack[index][0], Function) and \
                       not classstack[index][1] >= indent:
                        parent = classstack[index][0]
                        actype = m.group("AccessControlType") or \
                            m.group("AccessControlType2").split('_')[0]
                        actype = actype.lower()
                        for name in aclist.split(","):
                            name = name.strip()[1:]   # get rid of leading ':'
                            acmeth = parent._getmethod(name)
                            if acmeth is None:
                                continue
                            if actype == "private":
                                acmeth.setPrivate()
                            elif actype == "protected":
                                acmeth.setProtected()
                            elif actype == "public":
                                acmeth.setPublic()
                        break
                    else:
                        index -= 1

        elif m.start("Attribute") >= 0:
            lineno = lineno + src.count('\n', last_lineno_pos, start)
            last_lineno_pos = start
            index = -1
            while index >= -len(classstack):
                if classstack[index][0] is not None and \
                   not isinstance(classstack[index][0], Function) and \
                   not classstack[index][1] >= indent:
                    attr = Attribute(
                        module, m.group("AttributeName"), file, lineno)
                    classstack[index][0]._addattribute(attr)
                    break
                else:
                    index -= 1
                    if lastGlobalEntry:
                        lastGlobalEntry.setEndLine(lineno - 1)
                    lastGlobalEntry = None

        elif m.start("Attr") >= 0:
            lineno = lineno + src.count('\n', last_lineno_pos, start)
            last_lineno_pos = start
            index = -1
            while index >= -len(classstack):
                if classstack[index][0] is not None and \
                   not isinstance(classstack[index][0], Function) and \
                   not classstack[index][1] >= indent:
                    parent = classstack[index][0]
                    if m.group("AttrType") is None:
                        nv = m.group("AttrList").split(",")
                        if not nv:
                            break
                        name = nv[0].strip()[1:]    # get rid of leading ':'
                        attr = parent._getattribute("@" + name) or \
                            parent._getattribute("@@" + name) or \
                            Attribute(module, "@" + name, file, lineno)
                        if len(nv) == 1 or nv[1].strip() == "false":
                            attr.setProtected()
                        elif nv[1].strip() == "true":
                            attr.setPublic()
                        parent._addattribute(attr)
                    else:
                        access = m.group("AttrType")
                        for name in m.group("AttrList").split(","):
                            name = name.strip()[1:]   # get rid of leading ':'
                            attr = parent._getattribute("@" + name) or \
                                parent._getattribute("@@" + name) or \
                                Attribute(module, "@" + name, file, lineno)
                            if access == "_accessor":
                                attr.setPublic()
                            elif access == "_reader" or access == "_writer":
                                if attr.isPrivate():
                                    attr.setProtected()
                                elif attr.isProtected():
                                    attr.setPublic()
                            parent._addattribute(attr)
                    break
                else:
                    index -= 1

        elif m.start("Begin") >= 0:
            # a begin of a block we are not interested in
            indent += 1

        elif m.start("End") >= 0:
            # an end of a block
            indent -= 1
            if indent < 0:
                # no negative indent allowed
                if classstack:
                    # it's a class/module method
                    indent = classstack[-1][1]
                else:
                    indent = 0
        
        elif m.start("BeginEnd") >= 0:
            pass
        
        elif m.start("CodingLine") >= 0:
            # a coding statement
            coding = m.group("Coding")
            lineno = lineno + src.count('\n', last_lineno_pos, start)
            last_lineno_pos = start
            if "@@Coding@@" not in dict:
                dict["@@Coding@@"] = ClbrBaseClasses.Coding(
                    module, file, lineno, coding)

        else:
            assert 0, "regexp _getnext found something unexpected"

    return dict
