# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to select code style message codes.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog, QTreeWidgetItem

from .Ui_CodeStyleCodeSelectionDialog import Ui_CodeStyleCodeSelectionDialog

import UI.PixmapCache


class CodeStyleCodeSelectionDialog(QDialog, Ui_CodeStyleCodeSelectionDialog):
    """
    Class implementing a dialog to select code style message codes.
    """
    def __init__(self, codes, showFixCodes, parent=None):
        """
        Constructor
        
        @param codes comma separated list of selected codes (string)
        @param showFixCodes flag indicating to show a list of fixable
            issues (boolean)
        @param parent reference to the parent widget (QWidget)
        """
        super(CodeStyleCodeSelectionDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.codeTable.headerItem().setText(self.codeTable.columnCount(), "")
        codeList = [code.strip() for code in codes.split(",") if code.strip()]
        
        from .translations import _messages, _messages_sample_args
        
        if showFixCodes:
            from .CodeStyleFixer import FixableCodeStyleIssues
            selectableCodes = FixableCodeStyleIssues
        else:
            selectableCodes = [x for x in list(_messages.keys())
                               if not x.startswith('F')]
        for code in sorted(selectableCodes):
            if code in _messages_sample_args:
                message = _messages[code].format(*_messages_sample_args[code])
            elif code in _messages:
                message = _messages[code]
            else:
                continue
            itm = QTreeWidgetItem(self.codeTable, [code, message])
            if code.startswith(("W", "C", "M")):
                itm.setIcon(0, UI.PixmapCache.getIcon("warning.png"))
            elif code.startswith("E"):
                itm.setIcon(0, UI.PixmapCache.getIcon("syntaxError.png"))
            elif code.startswith("N"):
                itm.setIcon(0, UI.PixmapCache.getIcon("namingError.png"))
            elif code.startswith("D"):
                itm.setIcon(0, UI.PixmapCache.getIcon("docstringError.png"))
            if code in codeList:
                itm.setSelected(True)
                codeList.remove(code)
        self.codeTable.resizeColumnToContents(0)
        self.codeTable.resizeColumnToContents(1)
        self.codeTable.header().setStretchLastSection(True)
        
        self.__extraCodes = codeList[:]
    
    def getSelectedCodes(self):
        """
        Public method to get a comma separated list of codes selected.
        
        @return comma separated list of selected codes (string)
        """
        selectedCodes = []
        
        for itm in self.codeTable.selectedItems():
            selectedCodes.append(itm.text(0))
        
        return ", ".join(self.__extraCodes + selectedCodes)
