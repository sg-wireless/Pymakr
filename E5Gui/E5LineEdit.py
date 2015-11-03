# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing specialized line edits.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt, QEvent, qVersion
from PyQt5.QtGui import QPainter, QPalette
from PyQt5.QtWidgets import QLineEdit, QStyle, QWidget, QHBoxLayout, \
    QBoxLayout, QLayout, QApplication, QSpacerItem, QSizePolicy
if qVersion() >= "5.0.0":
    from PyQt5.QtWidgets import QStyleOptionFrame
else:
    from PyQt5.QtWidgets import QStyleOptionFrameV2 as QStyleOptionFrame

import UI.PixmapCache


class E5LineEditSideWidget(QWidget):
    """
    Class implementing the side widgets for the line edit class.
    """
    sizeHintChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(E5LineEditSideWidget, self).__init__(parent)
    
    def event(self, evt):
        """
        Public method to handle events.
        
        @param evt reference to the event (QEvent)
        @return flag indicating, whether the event was recognized (boolean)
        """
        if evt.type() == QEvent.LayoutRequest:
            self.sizeHintChanged.emit()
        return QWidget.event(self, evt)


class E5LineEdit(QLineEdit):
    """
    Class implementing a line edit widget showing some inactive text.
    """
    LeftSide = 0
    RightSide = 1
    
    def __init__(self, parent=None, inactiveText=""):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        @param inactiveText text to be shown on inactivity (string)
        """
        super(E5LineEdit, self).__init__(parent)
        
        self.setMinimumHeight(22)
        
        if qVersion() < "4.7.0":
            self.__inactiveText = inactiveText
        else:
            self.setPlaceholderText(inactiveText)
        
        self.__mainLayout = QHBoxLayout(self)
        self.__mainLayout.setContentsMargins(0, 0, 0, 0)
        self.__mainLayout.setSpacing(0)
        
        self.__leftMargin = 0
        self.__leftWidget = E5LineEditSideWidget(self)
        self.__leftWidget.resize(0, 0)
        self.__leftLayout = QHBoxLayout(self.__leftWidget)
        self.__leftLayout.setContentsMargins(0, 0, 2, 0)
        if QApplication.isRightToLeft():
            self.__leftLayout.setDirection(QBoxLayout.RightToLeft)
        else:
            self.__leftLayout.setDirection(QBoxLayout.LeftToRight)
        self.__leftLayout.setSizeConstraint(QLayout.SetFixedSize)
        
        self.__rightWidget = E5LineEditSideWidget(self)
        self.__rightWidget.resize(0, 0)
        self.__rightLayout = QHBoxLayout(self.__rightWidget)
        self.__rightLayout.setContentsMargins(0, 0, 2, 0)
        if self.isRightToLeft():
            self.__rightLayout.setDirection(QBoxLayout.RightToLeft)
        else:
            self.__rightLayout.setDirection(QBoxLayout.LeftToRight)
        
        horizontalSpacer = QSpacerItem(
            0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.__mainLayout.addWidget(
            self.__leftWidget, 0, Qt.AlignVCenter | Qt.AlignLeft)
        self.__mainLayout.addItem(horizontalSpacer)
        self.__mainLayout.addWidget(
            self.__rightWidget, 0, Qt.AlignVCenter | Qt.AlignRight)
        if self.isRightToLeft():
            self.__mainLayout.setDirection(QBoxLayout.RightToLeft)
        else:
            self.__mainLayout.setDirection(QBoxLayout.LeftToRight)
        
        self.setWidgetSpacing(3)
        self.__leftWidget.sizeHintChanged.connect(self._updateTextMargins)
        self.__rightWidget.sizeHintChanged.connect(self._updateTextMargins)
    
    def setLeftMargin(self, margin):
        """
        Public method to set the left margin.
        
        @param margin left margin in pixel (integer)
        """
        self.__leftMargin = margin
    
    def leftMargin(self):
        """
        Public method to get the size of the left margin.
        
        @return left margin in pixel (integer)
        """
        return self.__leftMargin
    
    def event(self, evt):
        """
        Public method to handle events.
        
        @param evt reference to the event (QEvent)
        @return flag indicating, whether the event was recognized (boolean)
        """
        if evt.type() == QEvent.LayoutDirectionChange:
            if self.isRightToLeft():
                self.__mainLayout.setDirection(QBoxLayout.RightToLeft)
                self.__leftLayout.setDirection(QBoxLayout.RightToLeft)
                self.__rightLayout.setDirection(QBoxLayout.RightToLeft)
            else:
                self.__mainLayout.setDirection(QBoxLayout.LeftToRight)
                self.__leftLayout.setDirection(QBoxLayout.LeftToRight)
                self.__rightLayout.setDirection(QBoxLayout.LeftToRight)
        return QLineEdit.event(self, evt)
    
    def paintEvent(self, evt):
        """
        Protected method handling a paint event.
        
        @param evt reference to the paint event (QPaintEvent)
        """
        super(E5LineEdit, self).paintEvent(evt)
        
        if qVersion() < "4.7.0":
            if not self.text() and \
               self.__inactiveText and \
               not self.hasFocus():
                panel = QStyleOptionFrame()
                self.initStyleOption(panel)
                textRect = self.style().subElementRect(
                    QStyle.SE_LineEditContents, panel, self)
                textRect.adjust(2, 0, 0, 0)
                left = self.textMargin(self.LeftSide)
                right = self.textMargin(self.RightSide)
                textRect.adjust(left, 0, -right, 0)
                painter = QPainter(self)
                painter.setPen(self.palette().brush(
                    QPalette.Disabled, QPalette.Text).color())
                painter.drawText(
                    textRect, Qt.AlignLeft | Qt.AlignVCenter,
                    self.__inactiveText)
    
    def _updateTextMargins(self):
        """
        Protected slot to update the text margins.
        """
        if self.__leftMargin == 0:
            left = self.__leftWidget.sizeHint().width()
        else:
            left = self.__leftMargin
        right = self.__rightWidget.sizeHint().width()
        top = 0
        bottom = 0
        self.setTextMargins(left, top, right, bottom)
    
    def addWidget(self, widget, position):
        """
        Public method to add a widget to a side.
        
        @param widget reference to the widget to add (QWidget)
        @param position position to add to (E5LineEdit.LeftSide,
            E5LineEdit.RightSide)
        """
        if widget is None:
            return
        
        if self.isRightToLeft():
            if position == self.LeftSide:
                position = self.RightSide
            else:
                position = self.LeftSide
        if position == self.LeftSide:
            self.__leftLayout.addWidget(widget)
        else:
            self.__rightLayout.insertWidget(1, widget)
    
    def removeWidget(self, widget):
        """
        Public method to remove a widget from a side.
        
        @param widget reference to the widget to remove (QWidget)
        """
        if widget is None:
            return
        
        self.__leftLayout.removeWidget(widget)
        self.__rightLayout.removeWidget(widget)
        widget.hide()
    
    def widgetSpacing(self):
        """
        Public method to get the side widget spacing.
        
        @return side widget spacing (integer)
        """
        return self.__leftLayout.spacing()
    
    def setWidgetSpacing(self, spacing):
        """
        Public method to set the side widget spacing.
        
        @param spacing side widget spacing (integer)
        """
        self.__leftLayout.setSpacing(spacing)
        self.__rightLayout.setSpacing(spacing)
        self._updateTextMargins()
    
    def textMargin(self, position):
        """
        Public method to get the text margin for a side.
        
        @param position side to get margin for (E5LineEdit.LeftSide,
            E5LineEdit.RightSide)
        @return text margin (integer)
        """
        spacing = self.__rightLayout.spacing()
        w = 0
        if position == self.LeftSide:
            w = self.__leftWidget.sizeHint().width()
        else:
            w = self.__rightWidget.sizeHint().width()
        if w == 0:
            return 0
        return w + spacing * 2
    
    def inactiveText(self):
        """
        Public method to get the inactive text.
        
        @return inactive text (string)
        """
        if qVersion() < "4.7.0":
            return self.__inactiveText
        else:
            return self.placeholderText()
    
    def setInactiveText(self, inactiveText):
        """
        Public method to set the inactive text.
        
        @param inactiveText text to be shown on inactivity (string)
        """
        if qVersion() < "4.7.0":
            self.__inactiveText = inactiveText
            self.update()
        else:
            self.setPlaceholderText(inactiveText)


class E5ClearableLineEdit(E5LineEdit):
    """
    Class implementing a line edit widget showing some inactive text and a
    clear button, if it has some contents.
    """
    def __init__(self, parent=None, inactiveText="",
                 side=E5LineEdit.RightSide):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        @keyparam inactiveText text to be shown on inactivity (string)
        @keyparam side side the clear button should be shown at
            (E5LineEdit.RightSide, E5LineEdit.LeftSide)
        """
        assert side in [E5LineEdit.RightSide, E5LineEdit.LeftSide]
        
        super(E5ClearableLineEdit, self).__init__(parent, inactiveText)
        
        from E5Gui.E5LineEditButton import E5LineEditButton
        self.__clearButton = E5LineEditButton(self)
        self.__clearButton.setIcon(UI.PixmapCache.getIcon("clearLeft.png"))
        self.addWidget(self.__clearButton, side)
        self.__clearButton.setVisible(False)
        
        self.__clearButton.clicked.connect(self.clear)
        self.textChanged.connect(self.__textChanged)
    
    def __textChanged(self, txt):
        """
        Private slot to handle changes of the text.
        
        @param txt text (string)
        """
        self.__clearButton.setVisible(txt != "")
