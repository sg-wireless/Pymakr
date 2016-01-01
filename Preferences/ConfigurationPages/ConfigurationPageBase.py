# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the base class for all configuration pages.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtWidgets import QWidget, QColorDialog, QFontDialog


class ConfigurationPageBase(QWidget):
    """
    Class implementing the base class for all configuration pages.
    """
    def __init__(self):
        """
        Constructor
        """
        super(ConfigurationPageBase, self).__init__()
        
        self.__coloursDict = {}
        
    def polishPage(self):
        """
        Public slot to perform some polishing actions.
        """
        return
        
    def saveState(self):
        """
        Public method to save the current state of the widget.
        """
        return
        
    def setState(self, state):
        """
        Public method to set the state of the widget.
        
        @param state state data generated by saveState
        """
        return
        
    def initColour(self, colourKey, button, prefMethod, byName=False,
                   hasAlpha=False):
        """
        Public method to initialize a colour selection button.
        
        @param colourKey key of the colour resource (string)
        @param button reference to a button to show the colour on (QPushButton)
        @param prefMethod preferences method to get the colour
        @keyparam byName flag indicating to retrieve/save by colour name
            (boolean)
        @keyparam hasAlpha flag indicating to allow alpha channel (boolean)
        """
        colour = QColor(prefMethod(colourKey))
        size = button.size()
        pm = QPixmap(size.width() / 2, size.height() / 2)
        pm.fill(colour)
        button.setIconSize(pm.size())
        button.setIcon(QIcon(pm))
        button.setProperty("colorKey", colourKey)
        button.setProperty("hasAlpha", hasAlpha)
        button.clicked.connect(self.__selectColourSlot)
        self.__coloursDict[colourKey] = [colour, byName]
        
    @pyqtSlot()
    def __selectColourSlot(self):
        """
        Private slot to select a color.
        """
        button = self.sender()
        colorKey = button.property("colorKey")
        hasAlpha = button.property("hasAlpha")
        
        if hasAlpha:
            colour = QColorDialog.getColor(
                self.__coloursDict[colorKey][0], None, "",
                QColorDialog.ShowAlphaChannel)
        else:
            colour = QColorDialog.getColor(self.__coloursDict[colorKey][0])
        if colour.isValid():
            size = button.iconSize()
            pm = QPixmap(size.width(), size.height())
            pm.fill(colour)
            button.setIcon(QIcon(pm))
            self.__coloursDict[colorKey][0] = colour
        
    def saveColours(self, prefMethod):
        """
        Public method to save the colour selections.
        
        @param prefMethod preferences method to set the colour
        """
        for key in self.__coloursDict:
            if self.__coloursDict[key][1]:
                prefMethod(key, self.__coloursDict[key][0].name())
            else:
                prefMethod(key, self.__coloursDict[key][0])
        
    def selectFont(self, fontSample, fontVar, showFontInfo=False):
        """
        Public method used by the font selection buttons.
        
        @param fontSample reference to the font sample widget (QLineEdit)
        @param fontVar reference to the variable containing the font (QFont)
        @param showFontInfo flag indicating to show some font info
            as the sample (boolean)
        @return selected font (QFont)
        """
        font, ok = QFontDialog.getFont(fontVar)
        if ok:
            fontSample.setFont(font)
            if showFontInfo:
                fontSample.setText(
                    "{0} {1}".format(font.family(), font.pointSize()))
        else:
            font = fontVar
        return font
