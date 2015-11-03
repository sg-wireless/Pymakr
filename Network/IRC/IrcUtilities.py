# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing functions used by several IRC objects.
"""

from __future__ import unicode_literals

import re

from PyQt5.QtCore import QTime, QCoreApplication
from PyQt5.QtWidgets import QApplication

import Utilities
import Preferences


__UrlRe = re.compile(
    r"""((?:http|ftp|https):\/\/[\w\-_]+(?:\.[\w\-_]+)+"""
    r"""(?:[\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?)""")
__ColorRe = re.compile(
    r"""((?:\x03(?:0[0-9]|1[0-5]|[0-9])?(?:,(?:0[0-9]|1[0-5]|[0-9]))?)"""
    r"""|\x02|\x03|\x13|\x15|\x16|\x17|\x1d|\x1f)""")


def ircTimestamp():
    """
    Module method to generate a time stamp string.
    
    @return time stamp (string)
    """
    if Preferences.getIrc("ShowTimestamps"):
        if Preferences.getIrc("TimestampIncludeDate"):
            if QApplication.isLeftToRight():
                f = "{0} {1}"
            else:
                f = "{1} {0}"
            formatString = f.format(Preferences.getIrc("DateFormat"),
                                    Preferences.getIrc("TimeFormat"))
        else:
            formatString = Preferences.getIrc("TimeFormat")
        return '<font color="{0}">[{1}]</font> '.format(
            Preferences.getIrc("TimestampColour"),
            QTime.currentTime().toString(formatString))
    else:
        return ""


def ircFilter(msg):
    """
    Module method to make the message HTML compliant and detect URLs.
    
    @param msg message to process (string)
    @return processed message (string)
    """
    # step 1: cleanup message
    msg = Utilities.html_encode(msg)
    
    # step 2: replace IRC formatting characters
    openTags = []
    parts = __ColorRe.split(msg)
    msgParts = []
    for part in parts:
        if part == "\x02":                                  # bold
            if openTags and openTags[-1] == "b":
                msgParts.append("</" + openTags.pop(-1) + ">")
            else:
                msgParts.append("<b>")
                openTags.append("b")
        elif part in ["\x03", "\x17"]:
            if Preferences.getIrc("EnableIrcColours"):
                if openTags and openTags[-1] == "span":
                    msgParts.append("</" + openTags.pop(-1) + ">")
                else:
                    continue
            else:
                continue
        elif part == "\x0f":                                # reset
            while openTags:
                msgParts.append("</" + openTags.pop(-1) + ">")
        elif part == "\x13":                                # strikethru
            if openTags and openTags[-1] == "s":
                msgParts.append("</" + openTags.pop(-1) + ">")
            else:
                msgParts.append("<s>")
                openTags.append("s")
        elif part in ["\x15", "\x1f"]:                      # underline
            if openTags and openTags[-1] == "u":
                msgParts.append("</" + openTags.pop(-1) + ">")
            else:
                msgParts.append("<u>")
                openTags.append("u")
        elif part == "\x16":
            # revert color not supported
            continue
        elif part == "\x1d":                                # italic
            if openTags and openTags[-1] == "i":
                msgParts.append("</" + openTags.pop(-1) + ">")
            else:
                msgParts.append("<i>")
                openTags.append("i")
        elif part.startswith("\x03"):
            if Preferences.getIrc("EnableIrcColours"):
                colors = part[1:].split(",", 1)
                if len(colors) == 1:
                    # foreground color only
                    tag = '<span style="color:{0}">'.format(Preferences.getIrc(
                        "IrcColor{0}".format(int(colors[0]))))
                else:
                    if colors[0]:
                        # foreground and background
                        tag = '<span style="background-color:{0};color={1}">'\
                            .format(Preferences.getIrc(
                                "IrcColor{0}".format(int(colors[0]))),
                                Preferences.getIrc(
                                    "IrcColor{0}".format(int(colors[1]))))
                    else:
                        # background only
                        tag = '<span style="background-color:{0}">'.format(
                            Preferences.getIrc(
                                "IrcColor{0}".format(int(colors[1]))))
                msgParts.append(tag)
                openTags.append("span")
            else:
                continue
        else:
            msgParts.append(part)
    msg = "".join(msgParts)
    
    # step 3: find http and https links
    parts = __UrlRe.split(msg)
    msgParts = []
    for part in parts:
        if part.startswith(("http://", "https://", "ftp://")):
            msgParts.append('<a href="{0}" style="color:{1}">{0}</a>'.format(
                part, Preferences.getIrc("HyperlinkColour")))
        else:
            msgParts.append(part)
    
    return "".join(msgParts)


__channelModesDict = None


def __initChannelModesDict():
    """
    Private module function to initialize the channels modes dictionary.
    """
    global __channelModesDict
    
    modesDict = {
        "a": QCoreApplication.translate("IrcUtilities", "anonymous"),
        "b": QCoreApplication.translate("IrcUtilities", "ban mask"),
        "c": QCoreApplication.translate("IrcUtilities", "no colors allowed"),
        "e": QCoreApplication.translate("IrcUtilities", "ban exception mask"),
        "i": QCoreApplication.translate("IrcUtilities", "invite only"),
        "k": QCoreApplication.translate("IrcUtilities", "password protected"),
        "l": QCoreApplication.translate("IrcUtilities", "user limit"),
        "m": QCoreApplication.translate("IrcUtilities", "moderated"),
        "n": QCoreApplication.translate("IrcUtilities",
                                        "no messages from outside"),
        "p": QCoreApplication.translate("IrcUtilities", "private"),
        "q": QCoreApplication.translate("IrcUtilities", "quiet"),
        "r": QCoreApplication.translate("IrcUtilities", "reop channel"),
        "s": QCoreApplication.translate("IrcUtilities", "secret"),
        "t": QCoreApplication.translate("IrcUtilities", "topic protection"),
        "I": QCoreApplication.translate("IrcUtilities", "invitation mask"),
    }
    __channelModesDict = modesDict


def getChannelModesDict():
    """
    Module function to get the dictionary with the channel modes mappings.
    
    @return dictionary with channel modes mapping (dict)
    """
    global __channelModesDict
    
    if __channelModesDict is None:
        __initChannelModesDict()
    
    return __channelModesDict
