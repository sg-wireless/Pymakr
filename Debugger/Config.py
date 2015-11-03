# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module defining the different Python types and their display strings.
"""

from __future__ import unicode_literals

try:
    from PyQt5.QtCore import QT_TRANSLATE_NOOP
    
    # Variables type definition
    ConfigVarTypeDispStrings = [
        QT_TRANSLATE_NOOP('Variable Types', 'Hidden Attributes'),
        QT_TRANSLATE_NOOP('Variable Types', 'None'),
        QT_TRANSLATE_NOOP('Variable Types', 'Type'),
        QT_TRANSLATE_NOOP('Variable Types', 'Boolean'),
        QT_TRANSLATE_NOOP('Variable Types', 'Integer'),
        QT_TRANSLATE_NOOP('Variable Types', 'Long Integer'),
        QT_TRANSLATE_NOOP('Variable Types', 'Float'),
        QT_TRANSLATE_NOOP('Variable Types', 'Complex'),
        QT_TRANSLATE_NOOP('Variable Types', 'String'),
        QT_TRANSLATE_NOOP('Variable Types', 'Unicode String'),
        QT_TRANSLATE_NOOP('Variable Types', 'Tuple'),
        QT_TRANSLATE_NOOP('Variable Types', 'List/Array'),
        QT_TRANSLATE_NOOP('Variable Types', 'Dictionary/Hash/Map'),
        QT_TRANSLATE_NOOP('Variable Types', 'Dictionary Proxy'),
        QT_TRANSLATE_NOOP('Variable Types', 'Set'),
        QT_TRANSLATE_NOOP('Variable Types', 'File'),
        QT_TRANSLATE_NOOP('Variable Types', 'X Range'),
        QT_TRANSLATE_NOOP('Variable Types', 'Slice'),
        QT_TRANSLATE_NOOP('Variable Types', 'Buffer'),
        QT_TRANSLATE_NOOP('Variable Types', 'Class'),
        QT_TRANSLATE_NOOP('Variable Types', 'Class Instance'),
        QT_TRANSLATE_NOOP('Variable Types', 'Class Method'),
        QT_TRANSLATE_NOOP('Variable Types', 'Class Property'),
        QT_TRANSLATE_NOOP('Variable Types', 'Generator'),
        QT_TRANSLATE_NOOP('Variable Types', 'Function'),
        QT_TRANSLATE_NOOP('Variable Types', 'Builtin Function'),
        QT_TRANSLATE_NOOP('Variable Types', 'Code'),
        QT_TRANSLATE_NOOP('Variable Types', 'Module'),
        QT_TRANSLATE_NOOP('Variable Types', 'Ellipsis'),
        QT_TRANSLATE_NOOP('Variable Types', 'Traceback'),
        QT_TRANSLATE_NOOP('Variable Types', 'Frame'),
        QT_TRANSLATE_NOOP('Variable Types', 'Other')
    ]
except ImportError:
    # Variables type definition (for non-Qt only)
    ConfigVarTypeDispStrings = [
        'Hidden Attributes', 'None', 'Type', 'Boolean', 'Integer',
        'Long Integer', 'Float', 'Complex', 'String', 'Unicode String',
        'Tuple', 'List/Array', 'Dictionary/Hash/Map', 'Dictionary Proxy',
        'Set', 'File', 'X Range', 'Slice', 'Buffer', 'Class',
        'Class Instance', 'Class Method', 'Class Property', 'Generator',
        'Function', 'Builtin Function', 'Code', 'Module', 'Ellipsis',
        'Traceback', 'Frame', 'Other']
