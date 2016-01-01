# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog showing statistical data for the last code
style checker run.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QTreeWidgetItem

from .translations import _messages, _messages_sample_args

from .Ui_CodeStyleStatisticsDialog import Ui_CodeStyleStatisticsDialog

import UI.PixmapCache


class CodeStyleStatisticsDialog(QDialog, Ui_CodeStyleStatisticsDialog):
    """
    Class implementing a dialog showing statistical data for the last
    code style checker run.
    """
    def __init__(self, statistics, parent=None):
        """
        Constructor
        
        @param statistics dictionary with the statistical data
        @param parent reference to the parent widget (QWidget)
        """
        super(CodeStyleStatisticsDialog, self).__init__(parent)
        self.setupUi(self)
        
        stats = statistics.copy()
        filesCount = stats["_FilesCount"]
        filesIssues = stats["_FilesIssues"]
        fixesCount = stats["_IssuesFixed"]
        ignoresCount = stats["_IgnoredErrors"]
        del stats["_FilesCount"]
        del stats["_FilesIssues"]
        del stats["_IssuesFixed"]
        del stats["_IgnoredErrors"]
        
        totalIssues = 0
        
        for code in sorted(stats.keys()):
            message = _messages.get(code)
            if message is None:
                continue
            
            if code in _messages_sample_args:
                message = message.format(*_messages_sample_args[code])
            
            self.__createItem(stats[code], code, message)
            totalIssues += stats[code]
        
        self.totalIssues.setText(
            self.tr("%n issue(s) found", "", totalIssues))
        self.ignoredIssues.setText(
            self.tr("%n issue(s) ignored", "", ignoresCount))
        self.fixedIssues.setText(
            self.tr("%n issue(s) fixed", "", fixesCount))
        self.filesChecked.setText(
            self.tr("%n file(s) checked", "", filesCount))
        self.filesIssues.setText(
            self.tr("%n file(s) with issues found", "", filesIssues))
        
        self.statisticsList.resizeColumnToContents(0)
        self.statisticsList.resizeColumnToContents(1)
    
    def __createItem(self, count, code, message):
        """
        Private method to create an entry in the result list.
        
        @param count occurrences of the issue (integer)
        @param code of a code style issue message (string)
        @param message code style issue message to be shown (string)
        """
        itm = QTreeWidgetItem(self.statisticsList)
        itm.setData(0, Qt.DisplayRole, count)
        itm.setData(1, Qt.DisplayRole, code)
        itm.setData(2, Qt.DisplayRole, message)
        if code.startswith(("W", "C", "M")):
            itm.setIcon(1, UI.PixmapCache.getIcon("warning.png"))
        elif code.startswith("E"):
            itm.setIcon(1, UI.PixmapCache.getIcon("syntaxError.png"))
        elif code.startswith("N"):
            itm.setIcon(1, UI.PixmapCache.getIcon("namingError.png"))
        elif code.startswith("D"):
            itm.setIcon(1, UI.PixmapCache.getIcon("docstringError.png"))
        
        itm.setTextAlignment(0, Qt.AlignRight)
        itm.setTextAlignment(1, Qt.AlignHCenter)
