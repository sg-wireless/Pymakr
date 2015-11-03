# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for a new property.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5FileDialog

from .Ui_SvnPropSetDialog import Ui_SvnPropSetDialog

import Utilities
import UI.PixmapCache


class SvnPropSetDialog(QDialog, Ui_SvnPropSetDialog):
    """
    Class implementing a dialog to enter the data for a new property.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        """
        super(SvnPropSetDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.fileButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.propFileCompleter = E5FileCompleter(self.propFileEdit)
        
    @pyqtSlot()
    def on_fileButton_clicked(self):
        """
        Private slot called by pressing the file selection button.
        """
        fn = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select file for property"),
            self.propFileEdit.text(),
            "")
        
        if fn:
            self.propFileEdit.setText(Utilities.toNativeSeparators(fn))
        
    def getData(self):
        """
        Public slot used to retrieve the data entered into the dialog.
        
        @return tuple of three values giving the property name, a flag
            indicating a file was selected and the text of the property
            or the selected filename. (string, boolean, string)
        """
        if self.fileRadioButton.isChecked():
            return (self.propNameEdit.text(), True, self.propFileEdit.text())
        else:
            return (self.propNameEdit.text(), False,
                    self.propTextEdit.toPlainText())
