# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a zoom widget for the status bar.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QWidget

from .Ui_E5ZoomWidget import Ui_E5ZoomWidget


class E5ZoomWidget(QWidget, Ui_E5ZoomWidget):
    """
    Class implementing a zoom widget for the status bar.
    """
    valueChanged = pyqtSignal(int)
    
    def __init__(self, outPix, inPix, resetPix, parent=None):
        """
        Constructor
        
        @param outPix pixmap for the zoom out button (QPixmap)
        @param inPix pixmap for the zoom in button (QPixmap)
        @param resetPix pixmap for the zoom reset button (QPixmap)
        @param parent reference to the parent widget (QWidget)
        """
        super(E5ZoomWidget, self).__init__(parent)
        self.setupUi(self)
        
        self.zoomOutLabel.setPixmap(outPix.scaled(16, 16))
        self.zoomInLabel.setPixmap(inPix.scaled(16, 16))
        self.zoomResetLabel.setPixmap(resetPix.scaled(16, 16))
        
        self.zoomOutLabel.clicked.connect(self.__zoomOut)
        self.zoomInLabel.clicked.connect(self.__zoomIn)
        self.zoomResetLabel.clicked.connect(self.__zoomReset)
        
        self.slider.valueChanged.connect(self._sliderValueChanged)
        
        self.__default = 0
        self.__percent = False
        
        # mapped slider
        self.__mapped = False
        self.__mapping = []
        
        self.__setValueLabelWidth()
    
    @pyqtSlot(int)
    def on_slider_sliderMoved(self, value):
        """
        Private slot to handle changes of the zoom value.
        
        @param value value of the slider (integer)
        """
        if self.__mapped:
            self.valueChanged.emit(self.__mapping[value])
        else:
            self.valueChanged.emit(value)
    
    def setValue(self, value):
        """
        Public slot to set the value.
        
        @param value new zoom value (integer)
        """
        self.slider.setValue(self.__indexForValue(value))
    
    def value(self):
        """
        Public method to get the current value.
        
        @return current zoom value (integer)
        """
        if self.__mapped:
            return self.__mapping[self.slider.value()]
        else:
            return self.slider.value()
    
    def setMinimum(self, minimum):
        """
        Public method to set the minimum value.
        
        @param minimum new minimum value (integer)
        """
        if not self.__mapped:
            self.slider.setMinimum(minimum)
            self.__setValueLabelWidth()
    
    def minimum(self):
        """
        Public method to get the minimum value.
        
        @return minimum value (integer)
        """
        if self.__mapped:
            return self.__mapping[0]
        else:
            return self.slider.minimum()
    
    def setMaximum(self, maximum):
        """
        Public method to set the maximum value.
        
        @param maximum new maximum value (integer)
        """
        if not self.__mapped:
            self.slider.setMaximum(maximum)
            self.__setValueLabelWidth()
    
    def maximum(self):
        """
        Public method to get the maximum value.
        
        @return maximum value (integer)
        """
        if self.__mapped:
            return self.__mapping[-1]
        else:
            return self.slider.maximum()
    
    def setSingleStep(self, value):
        """
        Public method to set the single step value.
        
        @param value value for the single step (integer)
        """
        self.slider.setSingleStep(value)
    
    def singleStep(self):
        """
        Public method to get the single step value.
        
        @return single step value (integer)
        """
        return self.slider.singleStep()
    
    def setPageStep(self, value):
        """
        Public method to set the page step value.
        
        @param value page step value (integer)
        """
        self.slider.setPageStep(value)
    
    def pageStep(self):
        """
        Public method to get the page step value.
        
        @return page step value (integer)
        """
        return self.slider.pageStep()
    
    def setDefault(self, value):
        """
        Public method to set the default zoom value.
        
        @param value default zoom value (integer)
        """
        self.__default = self.__indexForValue(value)
    
    def default(self):
        """
        Public method to get the default zoom value.
        
        @return default zoom value (integer)
        """
        if self.__mapped:
            return self.__mapping[self.__default]
        else:
            return self.__default
    
    def setPercent(self, on):
        """
        Public method to set the percent mode of the widget.
        
        @param on flag indicating percent mode (boolean)
        """
        self.__percent = on
        self.__setValueLabelWidth()
    
    def isPercent(self):
        """
        Public method to get the percent mode.
        
        @return flag indicating percent mode (boolean)
        """
        return self.__percent
    
    def setMapping(self, mapping, default, percent=True):
        """
        Public method to set a zoom level mapping.
        
        When zoom level mapping is activated, the slider covers
        values from 0 to the max. index of the mapping list. The
        default value is the value of the default zoom level. If
        percent is given, the zoom level is shown as a percent value.
        
        @param mapping list of mapping values (list of integer)
        @param default index of the default value (integer)
        @keyparam percent flag indicating to show zoom value in percent
            (boolean)
        """
        if mapping:
            self.__mapping = mapping[:]
            self.__mapped = True
            self.slider.setMinimum(0)
            self.slider.setMaximum(len(self.__mapping) - 1)
            self.__default = self.__indexForValue(default)
            self.__percent = percent
            self.slider.setValue(self.__default)
        else:
            # switch back to default values
            self.__mapping = []
            self.__mapped = False
            self.slider.setMinimum(-10)
            self.slider.setMaximum(20)
            self.__default = 0
            self.__percent = False
            self.slider.setValue(0)
        self.__setValueLabelWidth()
    
    def mapping(self):
        """
        Public method to get the current mapping.
        
        @return tuple of the mapping and the default index
            (list of integer, integer)
        """
        return self.__mapping[:], self.__default
    
    def isMapped(self):
        """
        Public method to check for a mapped zoom widget.
        
        @return flag indicating a mapped zoom widget (boolean)
        """
        return self.__mapped
    
    def __zoomReset(self):
        """
        Private slot to reset the value.
        """
        self.slider.setValue(self.__default)
        self.valueChanged.emit(self.value())
    
    def __zoomOut(self):
        """
        Private slot to zoom out one step.
        """
        self.slider.setValue(self.slider.value() - self.slider.singleStep())
        self.valueChanged.emit(self.value())
    
    def __zoomIn(self):
        """
        Private slot to zoom in one step.
        """
        self.slider.setValue(self.slider.value() + self.slider.singleStep())
        self.valueChanged.emit(self.value())
    
    def _sliderValueChanged(self, value):
        """
        Protected slot to handle changes of the slider value.
        
        @param value slider value (integer)
        """
        if self.__mapped:
            val = self.__mapping[value]
        else:
            val = value
        fmtStr = "{0}%" if self.__percent else "{0}"
        self.valueLabel.setText(fmtStr.format(val))
    
    def __setValueLabelWidth(self):
        """
        Private slot to determine the width of the zoom value label.
        """
        if self.__mapped:
            labelLen = max([len(str(v)) for v in self.__mapping])
        else:
            labelLen = max(
                len(str(self.slider.maximum())),
                len(str(self.slider.minimum()))
            )
        fmtStr = "{0}%" if self.__percent else "{0}"
        label = fmtStr.format("0" * labelLen)
        width = self.valueLabel.fontMetrics().width(label)
        self.valueLabel.setMinimumWidth(width)
        self.valueLabel.setMaximumWidth(width)
    
    def __indexForValue(self, value):
        """
        Private method to get the nearest index for a given value.
        
        @param value value to get the index for (integer)
        @return index into the mapping list or the unchanged value,
            if mapping is not set (integer)
        """
        if self.__mapped:
            try:
                index = self.__mapping.index(value)
            except ValueError:
                for index in range(len(self.__mapping)):
                    if value <= self.__mapping[index]:
                        break
        else:
            index = value
        return index
