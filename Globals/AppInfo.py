# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a function to generate an application info.
"""

from __future__ import unicode_literals

from UI.Info import Version


def makeAppInfo(argv, name, arg, description, options=[]):
    """
    Module function to generate a dictionary describing the application.
    
    @param argv list of commandline parameters (list of strings)
    @param name name of the application (string)
    @param arg commandline arguments (string)
    @param description text describing the application (string)
    @param options list of additional commandline options
        (list of tuples of two strings (commandline option,
        option description)). The options --version, --help and -h are
        always present and must not be repeated in this list.
    @return dictionary describing the application
    """
    return {
        "bin": argv[0],
        "arg": arg,
        "name": name,
        "description": description,
        "version": Version,
        "options": options
    }
