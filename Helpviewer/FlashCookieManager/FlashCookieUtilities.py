# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing some utility functions.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QProcessEnvironment

import Globals


def flashDataPathForOS():
    """
    Function to determine the OS dependent path where Flash cookies
    are stored.
    
    @return Flash data path
    @rtype str
    """
    # On Microsoft Windows NT 5.x and 6.x, they are stored in:
    # %APPDATA%\Macromedia\Flash Player\#SharedObjects\
    # %APPDATA%\Macromedia\Flash Player\macromedia.com\support\flashplayer\sys\
    # On Mac OS X, they are stored in:
    # ~/Library/Preferences/Macromedia/Flash Player/#SharedObjects/
    # ~/Library/Preferences/Macromedia/Flash Player/macromedia.com/support/⏎
    #   flashplayer/sys/
    # On Linux or Unix, they are stored in:
    # ~/.macromedia/Flash_Player/#SharedObjects/
    # ~/.macromedia/Flash_Player/macromedia.com/support/flashplayer/sys/
    # For Linux and Unix systems, if the open-source Gnash plugin is being used
    #  instead of the official Adobe Flash, they will instead be found at:
    # ~/.gnash/SharedObjects/
    
    flashPath = ""
    
    if Globals.isWindowsPlatform():
        appData = QProcessEnvironment.systemEnvironment().value("APPDATA")
        appData = appData.replace("\\", "/")
        flashPath = appData + "/Macromedia/Flash Player"
    elif Globals.isMacPlatform():
        flashPath = os.path.expanduser(
            "~/Library/Preferences/Macromedia/Flash Player")
    else:
        if os.path.exists(os.path.expanduser("~/.macromedia")):
            flashPath = os.path.expanduser("~/.macromedia/Flash_Player")
        elif os.path.exists(os.path.expanduser("~/.gnash")):
            flashPath = os.path.expanduser("~/.gnash")
    
    return flashPath
