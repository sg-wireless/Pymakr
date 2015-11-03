# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to select a help topic to display.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QUrl

from .Ui_HelpTopicDialog import Ui_HelpTopicDialog


class HelpTopicDialog(QDialog, Ui_HelpTopicDialog):
    """
    Class implementing a dialog to select a help topic to display.
    """
    def __init__(self, parent, keyword, links):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        @param keyword keyword for the link set (string)
        @param links dictionary with help topic as key (string) and
            URL as value (QUrl)
        """
        super(HelpTopicDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.label.setText(self.tr("Choose a &topic for <b>{0}</b>:")
                           .format(keyword))
        
        self.__links = links
        for topic in sorted(self.__links):
            self.topicsList.addItem(topic)
        if self.topicsList.count() > 0:
            self.topicsList.setCurrentRow(0)
        self.topicsList.setFocus()
        
        self.topicsList.itemActivated.connect(self.accept)
    
    def link(self):
        """
        Public method to the link of the selected topic.
        
        @return URL of the selected topic (QUrl)
        """
        itm = self.topicsList.currentItem()
        if itm is None:
            return QUrl()
        
        topic = itm.text()
        if topic == "" or topic not in self.__links:
            return QUrl()
        
        return self.__links[topic]
