# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the templates properties dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QRegExp, Qt, pyqtSlot
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QDialog

from .Ui_TemplatePropertiesDialog import Ui_TemplatePropertiesDialog

from E5Gui import E5MessageBox

import Preferences


class TemplatePropertiesDialog(QDialog, Ui_TemplatePropertiesDialog):
    """
    Class implementing the templates properties dialog.
    """
    def __init__(self, parent, groupMode=False, itm=None):
        """
        Constructor
        
        @param parent the parent widget (QWidget)
        @param groupMode flag indicating group mode (boolean)
        @param itm item (TemplateEntry or TemplateGroup) to
            read the data from
        """
        super(TemplatePropertiesDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.templateEdit.setFont(Preferences.getTemplates("EditorFont"))
        
        if not groupMode:
            self.nameEdit.setWhatsThis(self.tr(
                """<b>Template name<b><p>Enter the name of the template."""
                """ Templates may be autocompleted upon this name."""
                """ In order to support autocompletion. the template name"""
                """ must only consist of letters (a-z and A-Z),"""
                """ digits (0-9) and underscores (_).</p>"""
            ))
            self.__nameValidator = QRegExpValidator(QRegExp("[a-zA-Z0-9_]+"),
                                                    self.nameEdit)
            self.nameEdit.setValidator(self.__nameValidator)
        
        import QScintilla.Lexers
        self.languages = [("All", self.tr("All"))]
        supportedLanguages = QScintilla.Lexers.getSupportedLanguages()
        languages = sorted(supportedLanguages.keys())
        for language in languages:
            self.languages.append((language, supportedLanguages[language][0]))
        
        self.groupMode = groupMode
        if groupMode:
            langList = []
            for lang, langDisp in self.languages:
                langList.append(langDisp)
            
            self.groupLabel.setText(self.tr("Language:"))
            self.groupCombo.addItems(langList)
            self.templateLabel.setEnabled(False)
            self.templateEdit.setEnabled(False)
            self.templateEdit.setPlainText(self.tr("GROUP"))
            self.helpButton.setEnabled(False)
            self.descriptionLabel.hide()
            self.descriptionEdit.hide()
        else:
            groups = []
            for group in parent.getGroupNames():
                groups.append(group)
            self.groupCombo.addItems(groups)
        
        if itm is not None:
            self.nameEdit.setText(itm.getName())
            if groupMode:
                lang = itm.getLanguage()
                for l, d in self.languages:
                    if l == lang:
                        self.setSelectedGroup(d)
                        break
            else:
                self.setSelectedGroup(itm.getGroupName())
                self.templateEdit.setPlainText(itm.getTemplateText())
                self.descriptionEdit.setText(itm.getDescription())
            
            self.nameEdit.selectAll()
        
        self.__helpDialog = None

    def keyPressEvent(self, ev):
        """
        Protected method to handle the user pressing the escape key.
        
        @param ev key event (QKeyEvent)
        """
        if ev.key() == Qt.Key_Escape:
            res = E5MessageBox.yesNo(
                self,
                self.tr("Close dialog"),
                self.tr("""Do you really want to close the dialog?"""))
            if not res:
                self.reject()
    
    @pyqtSlot()
    def on_helpButton_clicked(self):
        """
        Private slot to show some help.
        """
        if self.__helpDialog is None:
            from .TemplateHelpDialog import TemplateHelpDialog
            self.__helpDialog = TemplateHelpDialog(self)
        self.__helpDialog.show()
        
    def setSelectedGroup(self, name):
        """
        Public method to select a group.
        
        @param name name of the group to be selected (string)
        """
        index = self.groupCombo.findText(name)
        self.groupCombo.setCurrentIndex(index)

    def getData(self):
        """
        Public method to get the data entered into the dialog.
        
        @return a tuple of two strings (name, language), if the dialog is in
            group mode, and a tuple of four strings (name, description, group
            name, template) otherwise.
        """
        if self.groupMode:
            return (self.nameEdit.text(),
                    self.languages[self.groupCombo.currentIndex()][0]
                    )
        else:
            return (self.nameEdit.text(),
                    self.descriptionEdit.text(),
                    self.groupCombo.currentText(),
                    self.templateEdit.toPlainText()
                    )
