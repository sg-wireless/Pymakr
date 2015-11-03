# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to edit the data of a search engine.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_OpenSearchEditDialog import Ui_OpenSearchEditDialog


class OpenSearchEditDialog(QDialog, Ui_OpenSearchEditDialog):
    """
    Class implementing a dialog to edit the data of a search engine.
    """
    def __init__(self, engine, parent=None):
        """
        Constructor
        
        @param engine reference to the search engine (OpenSearchEngine)
        @param parent reference to the parent object (QWidget)
        """
        super(OpenSearchEditDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__engine = engine
        
        self.nameEdit.setText(engine.name())
        self.descriptionEdit.setText(engine.description())
        self.imageEdit.setText(engine.imageUrl())
        self.searchEdit.setText(engine.searchUrlTemplate())
        self.suggestionsEdit.setText(engine.suggestionsUrlTemplate())
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
    
    def accept(self):
        """
        Public slot to accept the data entered.
        """
        self.__engine.setName(self.nameEdit.text())
        self.__engine.setDescription(self.descriptionEdit.text())
        self.__engine.setImageUrlAndLoad(self.imageEdit.text())
        self.__engine.setSearchUrlTemplate(self.searchEdit.text())
        self.__engine.setSuggestionsUrlTemplate(self.suggestionsEdit.text())
        
        super(OpenSearchEditDialog, self).accept()
