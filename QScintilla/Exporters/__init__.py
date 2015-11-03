# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Package implementing exporters for various file formats.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QCoreApplication


def getSupportedFormats():
    """
    Module function to get a dictionary of supported exporters.
    
    @return dictionary of supported exporters. The keys are the
        internal format names. The items are the display strings
        for the exporters (string)
    """
    supportedFormats = {
        "HTML": QCoreApplication.translate('Exporters', "HTML"),
        "RTF": QCoreApplication.translate('Exporters', "RTF"),
        "PDF": QCoreApplication.translate('Exporters', "PDF"),
        "TeX": QCoreApplication.translate('Exporters', "TeX"),
        "ODT": QCoreApplication.translate('Exporters', "ODT"),
    }
    
    return supportedFormats


def getExporter(format, editor):
    """
    Module function to instantiate an exporter object for a given format.
    
    @param format format of the exporter (string)
    @param editor reference to the editor object (QScintilla.Editor.Editor)
    @return reference to the instanciated exporter object
        (QScintilla.Exporter.Exporter)
    """
    try:
        if format == "HTML":
            from .ExporterHTML import ExporterHTML
            return ExporterHTML(editor)
        elif format == "PDF":
            from .ExporterPDF import ExporterPDF
            return ExporterPDF(editor)
        elif format == "RTF":
            from .ExporterRTF import ExporterRTF
            return ExporterRTF(editor)
        elif format == "TeX":
            from .ExporterTEX import ExporterTEX
            return ExporterTEX(editor)
        elif format == "ODT":
            from .ExporterODT import ExporterODT
            return ExporterODT(editor)
    except ImportError:
        return None
