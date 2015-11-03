# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for a switch operation.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_SvnSwitchDialog import Ui_SvnSwitchDialog


class SvnSwitchDialog(QDialog, Ui_SvnSwitchDialog):
    """
    Class implementing a dialog to enter the data for a switch operation.
    """
    def __init__(self, taglist, reposURL, standardLayout, parent=None):
        """
        Constructor
        
        @param taglist list of previously entered tags (list of strings)
        @param reposURL repository path (string) or None
        @param standardLayout flag indicating the layout of the
            repository (boolean)
        @param parent parent widget (QWidget)
        """
        super(SvnSwitchDialog, self).__init__(parent)
        self.setupUi(self)
       
        self.tagCombo.clear()
        self.tagCombo.addItems(sorted(taglist))
        
        if reposURL is not None and reposURL != "":
            self.tagCombo.setEditText(reposURL)
            
        if not standardLayout:
            self.TagTypeGroup.setEnabled(False)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    def getParameters(self):
        """
        Public method to retrieve the tag data.
        
        @return tuple of string and int (tag, tag type)
        """
        tag = self.tagCombo.currentText()
        tagType = 0
        if self.regularButton.isChecked():
            tagType = 1
        elif self.branchButton.isChecked():
            tagType = 2
        if not tag:
            tagType = 4
        return (tag, tagType)
