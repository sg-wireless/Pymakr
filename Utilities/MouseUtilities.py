# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing utility functions related to Mouse stuff.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QCoreApplication

import Globals

if Globals.isMacPlatform():
    __modifier2String = {
        Qt.ShiftModifier: QCoreApplication.translate(
            "MouseUtilities", "Shift"),
        Qt.AltModifier: QCoreApplication.translate(
            "MouseUtilities", "Alt"),
        Qt.ControlModifier: QCoreApplication.translate(
            "MouseUtilities", "Cmd"),
        Qt.MetaModifier: QCoreApplication.translate(
            "MouseUtilities", "Ctrl"),
    }
    __modifierOrder = [Qt.MetaModifier, Qt.AltModifier, Qt.ShiftModifier,
                       Qt.ControlModifier]
else:
    __modifier2String = {
        Qt.ShiftModifier: QCoreApplication.translate(
            "MouseUtilities", "Shift"),
        Qt.AltModifier: QCoreApplication.translate(
            "MouseUtilities", "Alt"),
        Qt.ControlModifier: QCoreApplication.translate(
            "MouseUtilities", "Ctrl"),
        Qt.MetaModifier: QCoreApplication.translate(
            "MouseUtilities", "Meta"),
    }
    __modifierOrder = [Qt.MetaModifier, Qt.ControlModifier, Qt.AltModifier,
                       Qt.ShiftModifier]


__button2String = {
    Qt.LeftButton: QCoreApplication.translate(
        "MouseUtilities", "Left Button"),
    Qt.RightButton: QCoreApplication.translate(
        "MouseUtilities", "Right Button"),
    Qt.MidButton: QCoreApplication.translate(
        "MouseUtilities", "Middle Button"),
    Qt.XButton1: QCoreApplication.translate(
        "MouseUtilities", "Extra Button 1"),
    Qt.XButton2: QCoreApplication.translate(
        "MouseUtilities", "Extra Button 2"),
}


def MouseButtonModifier2String(modifiers, button):
    """
    Function to convert a modifier and mouse button combination to a
    displayable string.
    
    @param modifiers keyboard modifiers of the handler
    @type Qt.KeyboardModifiers
    @param button mouse button of the handler
    @type Qt.MouseButton
    @return display string of the modifier and mouse button combination
    @rtype str
    """
    if button not in __button2String:
        return ""
    
    parts = []
    for mod in __modifierOrder:
        if modifiers & mod:
            parts.append(__modifier2String[mod])
    parts.append(__button2String[button])
    return "+".join(parts)
