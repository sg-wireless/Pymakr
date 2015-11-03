# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a progress dialog allowing a customized progress bar label.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QProgressBar, QProgressDialog


class E5ProgressDialog(QProgressDialog):
    """
    Class implementing a progress dialog allowing a customized progress bar
    label.
    """
    def __init__(self, labelText, cancelButtonText, minimum, maximum,
                 format=None, parent=None, flags=Qt.WindowFlags()):
        """
        Constructor
        
        @param labelText text of the dialog label (string)
        @param cancelButtonText text of the cancel button (string)
        @param minimum minimum value (integer)
        @param maximum maximum value (integer)
        @keyparam format label format of the progress bar (string)
        @keyparam parent reference to the parent widget (QWidget)
        @keyparam flags window flags of the dialog (Qt.WindowFlags)
        """
        super(E5ProgressDialog, self).__init__(
            labelText, cancelButtonText, minimum, maximum, parent, flags)
        
        self.__progressBar = QProgressBar(self)
        self.__progressBar.setMinimum(minimum)
        self.__progressBar.setMaximum(maximum)
        if format:
            self.__progressBar.setFormat(format)
        
        self.setBar(self.__progressBar)
    
    def format(self):
        """
        Public method to get the progress bar format.
        
        @return progress bar format (string)
        """
        return self.__progressBar.format()
    
    def setFormat(self, format):
        """
        Public method to set the progress bar format.
        
        @param format progress bar format (string)
        """
        self.__progressBar.setFormat(format)
