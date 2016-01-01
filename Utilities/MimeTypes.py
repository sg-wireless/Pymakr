# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing mimetype dependent functions.
"""

from __future__ import unicode_literals

import mimetypes

import Preferences


def isTextFile(filename):
    """
    Function to test, if the given file is a text (i.e. editable) file.
    
    @param filename name of the file to be checked (string)
    @return flag indicating an editable file (boolean)
    """
    type_ = mimetypes.guess_type(filename)[0]
    if (type_ is None or
        type_.split("/")[0] == "text" or
            type_ in Preferences.getUI("TextMimeTypes")):
        return True
    else:
        return False


def mimeType(filename):
    """
    Function to get the mime type of a file.
    
    @param filename name of the file to be checked (string)
    @return mime type of the file (string)
    """
    return mimetypes.guess_type(filename)[0]
