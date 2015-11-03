# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing some utility functions for the Download package.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QCoreApplication


def timeString(timeRemaining):
    """
    Module function to format the given time.
    
    @param timeRemaining time to be formatted (float)
    @return time string (string)
    """
    if timeRemaining > 60:
        minutes = int(timeRemaining / 60)
        seconds = int(timeRemaining % 60)
        remaining = QCoreApplication.translate(
            "DownloadUtilities",
            "%n:{0:02} minutes remaining""", "",
            minutes).format(seconds)
    else:
        seconds = int(timeRemaining)
        remaining = QCoreApplication.translate(
            "DownloadUtilities",
            "%n seconds remaining", "", seconds)
    
    return remaining


def dataString(size):
    """
    Module function to generate a formatted size string.
    
    @param size size to be formatted (integer)
    @return formatted data string (string)
    """
    unit = ""
    if size < 1024:
        unit = QCoreApplication.translate("DownloadUtilities", "Bytes")
    elif size < 1024 * 1024:
        size /= 1024
        unit = QCoreApplication.translate("DownloadUtilities", "KiB")
    elif size < 1024 * 1024 * 1024:
        size /= 1024 * 1024
        unit = QCoreApplication.translate("DownloadUtilities", "MiB")
    else:
        size /= 1024 * 1024 * 1024
        unit = QCoreApplication.translate("DownloadUtilities", "GiB")
    return "{0:.1f} {1}".format(size, unit)
