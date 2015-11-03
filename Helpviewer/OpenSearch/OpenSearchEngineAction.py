# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a QAction subclass for open search.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QAction


class OpenSearchEngineAction(QAction):
    """
    Class implementing a QAction subclass for open search.
    """
    def __init__(self, engine, parent=None):
        """
        Constructor
        
        @param engine reference to the open search engine object
            (OpenSearchEngine)
        @param parent reference to the parent object (QObject)
        """
        super(OpenSearchEngineAction, self).__init__(parent)
        
        self.__engine = engine
        if self.__engine.networkAccessManager() is None:
            import Helpviewer.HelpWindow
            self.__engine.setNetworkAccessManager(
                Helpviewer.HelpWindow.HelpWindow.networkAccessManager())
        
        self.setText(engine.name())
        self.__imageChanged()
        
        engine.imageChanged.connect(self.__imageChanged)
    
    def __imageChanged(self):
        """
        Private slot handling a change of the associated image.
        """
        image = self.__engine.image()
        if image.isNull():
            import Helpviewer.HelpWindow
            self.setIcon(
                Helpviewer.HelpWindow.HelpWindow.icon(
                    QUrl(self.__engine.imageUrl())))
        else:
            self.setIcon(QIcon(QPixmap.fromImage(image)))
