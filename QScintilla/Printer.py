# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the printer functionality.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QTime, QDate, Qt, QCoreApplication
from PyQt5.QtGui import QColor
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.Qsci import QsciPrinter

import Preferences


class Printer(QsciPrinter):
    """
    Class implementing the QextScintillaPrinter with a header.
    """
    def __init__(self, mode=QPrinter.ScreenResolution):
        """
        Constructor
        
        @param mode mode of the printer (QPrinter.PrinterMode)
        """
        super(Printer, self).__init__(mode)
        
        self.setMagnification(Preferences.getPrinter("Magnification"))
        if Preferences.getPrinter("ColorMode"):
            self.setColorMode(QPrinter.Color)
        else:
            self.setColorMode(QPrinter.GrayScale)
        if Preferences.getPrinter("FirstPageFirst"):
            self.setPageOrder(QPrinter.FirstPageFirst)
        else:
            self.setPageOrder(QPrinter.LastPageFirst)
        self.setPageMargins(
            Preferences.getPrinter("LeftMargin") * 10,
            Preferences.getPrinter("TopMargin") * 10,
            Preferences.getPrinter("RightMargin") * 10,
            Preferences.getPrinter("BottomMargin") * 10,
            QPrinter.Millimeter
        )
        printerName = Preferences.getPrinter("PrinterName")
        if printerName:
            self.setPrinterName(printerName)
        self.time = QTime.currentTime().toString(Qt.LocalDate)
        self.date = QDate.currentDate().toString(Qt.LocalDate)
        self.headerFont = Preferences.getPrinter("HeaderFont")
        
    def formatPage(self, painter, drawing, area, pagenr):
        """
        Public method to generate a header line.
        
        @param painter the paint canvas (QPainter)
        @param drawing flag indicating that something should be drawn
        @param area the drawing area (QRect)
        @param pagenr the page number (int)
        """
        fn = self.docName()
        
        header = QCoreApplication.translate(
            'Printer', '{0} - Printed on {1}, {2} - Page {3}')\
            .format(fn, self.date, self.time, pagenr)
        
        painter.save()
        painter.setFont(self.headerFont)    # set our header font
        painter.setPen(QColor(Qt.black))            # set color
        if drawing:
            painter.drawText(
                area.right() - painter.fontMetrics().width(header),
                area.top() + painter.fontMetrics().ascent(), header)
        area.setTop(area.top() + painter.fontMetrics().height() + 5)
        painter.restore()
