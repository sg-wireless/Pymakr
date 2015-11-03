# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing utilities to get a password and/or the current user name.

getpass(prompt) - prompt for a password, with echo turned off
getuser() - get the user name from the environment or password database

This module is a replacement for the one found in the Python distribution. It
is to provide a debugger compatible variant of the a.m. functions.
"""

__all__ = ["getpass", "getuser"]


def getuser():
    """
    Function to get the username from the environment or password database.

    First try various environment variables, then the password
    database.  This works on Windows as long as USERNAME is set.
    
    @return username (string)
    """
    # this is copied from the oroginal getpass.py
    
    import os

    for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
        user = os.environ.get(name)
        if user:
            return user

    # If this fails, the exception will "explain" why
    import pwd
    return pwd.getpwuid(os.getuid())[0]


def getpass(prompt='Password: '):
    """
    Function to prompt for a password, with echo turned off.
    
    @param prompt Prompt to be shown to the user (string)
    @return Password entered by the user (string)
    """
    return input(prompt, False)
    
unix_getpass = getpass
win_getpass = getpass
default_getpass = getpass
