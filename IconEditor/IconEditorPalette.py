# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a palette widget for the icon editor.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor, QPainter, QPixmap
from PyQt5.QtWidgets import QWidget, QBoxLayout, QLabel, QFrame, QPushButton, \
    QSpinBox, QGroupBox, QVBoxLayout, QRadioButton, QSpacerItem, QSizePolicy, \
    QColorDialog


class IconEditorPalette(QWidget):
    """
    Class implementing a palette widget for the icon editor.
    
    @signal colorSelected(QColor) emitted after a new color has been selected
    @signal compositingChanged(QPainter.CompositionMode) emitted to signal a
        change of the compositing mode
    """
    colorSelected = pyqtSignal(QColor)
    compositingChanged = pyqtSignal(QPainter.CompositionMode)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(IconEditorPalette, self).__init__(parent)
        
        if self.layoutDirection == Qt.Horizontal:
            direction = QBoxLayout.LeftToRight
        else:
            direction = QBoxLayout.TopToBottom
        self.__layout = QBoxLayout(direction, self)
        self.setLayout(self.__layout)
        
        self.__preview = QLabel(self)
        self.__preview.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.__preview.setFixedHeight(64)
        self.__preview.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.__preview.setWhatsThis(self.tr(
            """<b>Preview</b>"""
            """<p>This is a 1:1 preview of the current icon.</p>"""
        ))
        self.__layout.addWidget(self.__preview)
        
        self.__color = QLabel(self)
        self.__color.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.__color.setFixedHeight(24)
        self.__color.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.__color.setWhatsThis(self.tr(
            """<b>Current Color</b>"""
            """<p>This is the currently selected color used for drawing.</p>"""
        ))
        self.__layout.addWidget(self.__color)
        
        self.__colorTxt = QLabel(self)
        self.__colorTxt.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.__colorTxt.setWhatsThis(self.tr(
            """<b>Current Color Value</b>"""
            """<p>This is the currently selected color value used for"""
            """ drawing.</p>"""
        ))
        self.__layout.addWidget(self.__colorTxt)
        
        self.__colorButton = QPushButton(self.tr("Select Color"), self)
        self.__colorButton.setWhatsThis(self.tr(
            """<b>Select Color</b>"""
            """<p>Select the current drawing color via a color selection"""
            """ dialog.</p>"""
        ))
        self.__colorButton.clicked.connect(self.__selectColor)
        self.__layout.addWidget(self.__colorButton)
        
        self.__colorAlpha = QSpinBox(self)
        self.__colorAlpha.setRange(0, 255)
        self.__colorAlpha.setWhatsThis(self.tr(
            """<b>Select alpha channel value</b>"""
            """<p>Select the value for the alpha channel of the current"""
            """ color.</p>"""
        ))
        self.__layout.addWidget(self.__colorAlpha)
        self.__colorAlpha.valueChanged[int].connect(self.__alphaChanged)
        
        self.__compositingGroup = QGroupBox(self.tr("Compositing"), self)
        self.__compositingGroupLayout = QVBoxLayout(self.__compositingGroup)
        self.__compositingGroup.setLayout(self.__compositingGroupLayout)
        self.__sourceButton = QRadioButton(self.tr("Replace"),
                                           self.__compositingGroup)
        self.__sourceButton.setWhatsThis(self.tr(
            """<b>Replace</b>"""
            """<p>Replace the existing pixel with a new color.</p>"""
        ))
        self.__sourceButton.clicked[bool].connect(self.__compositingChanged)
        self.__compositingGroupLayout.addWidget(self.__sourceButton)
        self.__sourceOverButton = QRadioButton(self.tr("Blend"),
                                               self.__compositingGroup)
        self.__sourceOverButton.setWhatsThis(self.tr(
            """<b>Blend</b>"""
            """<p>Blend the new color over the existing pixel.</p>"""
        ))
        self.__sourceOverButton.setChecked(True)
        self.__sourceOverButton.clicked[bool].connect(
            self.__compositingChanged)
        self.__compositingGroupLayout.addWidget(self.__sourceOverButton)
        self.__layout.addWidget(self.__compositingGroup)
        
        spacer = QSpacerItem(
            10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.__layout.addItem(spacer)
    
    def previewChanged(self, pixmap):
        """
        Public slot to update the preview.
        
        @param pixmap new preview pixmap (QPixmap)
        """
        self.__preview.setPixmap(pixmap)
    
    def colorChanged(self, color):
        """
        Public slot to update the color preview.
        
        @param color new color (QColor)
        """
        self.__currentColor = color
        self.__currentAlpha = color.alpha()
        
        pm = QPixmap(90, 18)
        pm.fill(color)
        self.__color.setPixmap(pm)
        
        self.__colorTxt.setText(
            "{0:d}, {1:d}, {2:d}, {3:d}".format(
                color.red(), color.green(), color.blue(), color.alpha()))
        
        self.__colorAlpha.setValue(self.__currentAlpha)
    
    def __selectColor(self):
        """
        Private slot to select a new drawing color.
        """
        col = QColorDialog.getColor(self.__currentColor)
        col.setAlpha(self.__currentAlpha)
        
        if col.isValid():
            self.colorSelected.emit(col)
    
    def __alphaChanged(self, val):
        """
        Private slot to track changes of the alpha channel.
        
        @param val value of the alpha channel
        """
        if val != self.__currentAlpha:
            col = QColor(self.__currentColor)
            col.setAlpha(val)
            self.colorSelected.emit(col)
    
    def setCompositingMode(self, mode):
        """
        Public method to set the compositing mode.
        
        @param mode compositing mode to set (QPainter.CompositionMode)
        """
        if mode == QPainter.CompositionMode_Source:
            self.__sourceButton.setChecked(True)
        elif mode == QPainter.CompositionMode_SourceOver:
            self.__sourceOverButton.setChecked(True)
    
    def __compositingChanged(self, on):
        """
        Private slot to handle a change of the compositing mode.
        
        @param on flag indicating the checked state of the compositing button
            (boolean)
        """
        if on:
            if self.__sourceButton.isChecked():
                self.compositingChanged.emit(
                    QPainter.CompositionMode_Source)
            elif self.__sourceOverButton.isChecked():
                self.compositingChanged.emit(
                    QPainter.CompositionMode_SourceOver)
