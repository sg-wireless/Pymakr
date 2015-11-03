# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a custom widget indicating the strength of a password.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QProgressBar

from Utilities.PasswordChecker import PasswordChecker


class E5PasswordMeter(QProgressBar):
    """
    Class implementing a custom widget indicating the strength of a password.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(E5PasswordMeter, self).__init__(parent)
        
        super(E5PasswordMeter, self).setTextVisible(False)
        super(E5PasswordMeter, self).setMaximum(100)
        self.__increment = 100 // (PasswordChecker.Complexity_VeryStrong + 1)
        
        self.__indicatorColors = [
            "#ff0000",      # red
            "#ff8800",      # orange
            "#ffff00",      # yellow
            "#ccff00",      # yellow green
            "#00ff00",      # green
        ]
        self.__noIndicator = "#ffffff"
        
        self.__styleSheetTemplate = \
            "QProgressBar {{"\
            " border: 2px solid black;" \
            " border-radius: 5px;" \
            " text-align: center; }}" \
            "QProgressBar::chunk:horizontal {{" \
            " background-color: {0}; }}"
        self.setStyleSheet(
            self.__styleSheetTemplate.format(self.__noIndicator))
    
    def checkPasswordStrength(self, password):
        """
        Public slot to check the password strength and update the
        progress bar accordingly.
        
        @param password password to be checked (string)
        """
        strength = PasswordChecker().checkPassword(password)
        self.setStyleSheet(self.__styleSheetTemplate.format(
            self.__indicatorColors[strength]))
        super(E5PasswordMeter, self).setValue(
            (strength + 1) * self.__increment)
    
    def setValue(self, value):
        """
        Public method to set the value.
        
        Overwritten to do nothing.
        
        @param value value (integer)
        """
        pass
    
    def setMaximum(self, value):
        """
        Public method to set the maximum value.
        
        Overwritten to do nothing.
        
        @param value maximum value (integer)
        """
        pass
    
    def setMinimum(self, value):
        """
        Public method to set the minimal value.
        
        Overwritten to do nothing.
        
        @param value minimum value (integer)
        """
        pass

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    meter = E5PasswordMeter()
    meter.show()
    meter.checkPasswordStrength("Blah2+")
    app.exec_()
