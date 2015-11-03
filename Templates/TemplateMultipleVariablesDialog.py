# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for entering multiple template variables.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QSizePolicy, QSpacerItem, QWidget, QHBoxLayout, \
    QLineEdit, QPushButton, QTextEdit, QDialog, QScrollArea, QFrame, \
    QGridLayout, QVBoxLayout, QLabel


class TemplateMultipleVariablesDialog(QDialog):
    """
    Class implementing a dialog for entering multiple template variables.
    """
    def __init__(self, variables, parent=None):
        """
        Constructor
        
        @param variables list of template variable names (list of strings)
        @param parent parent widget of this dialog (QWidget)
        """
        super(TemplateMultipleVariablesDialog, self).__init__(parent)

        self.TemplateMultipleVariablesDialogLayout = QVBoxLayout(self)
        self.TemplateMultipleVariablesDialogLayout.setContentsMargins(
            6, 6, 6, 6)
        self.TemplateMultipleVariablesDialogLayout.setSpacing(6)
        self.TemplateMultipleVariablesDialogLayout.setObjectName(
            "TemplateMultipleVariablesDialogLayout")
        self.setLayout(self.TemplateMultipleVariablesDialogLayout)

        # generate the scrollarea
        self.variablesView = QScrollArea(self)
        self.variablesView.setObjectName("variablesView")
        self.TemplateMultipleVariablesDialogLayout.addWidget(
            self.variablesView)
        
        self.variablesView.setWidgetResizable(True)
        self.variablesView.setFrameStyle(QFrame.NoFrame)
        
        self.top = QWidget(self)
        self.variablesView.setWidget(self.top)
        self.grid = QGridLayout(self.top)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(6)
        self.top.setLayout(self.grid)

        # populate the scrollarea with labels and text edits
        self.variablesEntries = {}
        row = 0
        for var in variables:
            label = QLabel("{0}:".format(var), self.top)
            self.grid.addWidget(label, row, 0, Qt.Alignment(Qt.AlignTop))
            if var.find(":") >= 0:
                formatStr = var[1:-1].split(":")[1]
                if formatStr in ["ml", "rl"]:
                    t = QTextEdit(self.top)
                    t.setTabChangesFocus(True)
                else:
                    t = QLineEdit(self.top)
            else:
                t = QLineEdit(self.top)
            self.grid.addWidget(t, row, 1)
            self.variablesEntries[var] = t
            row += 1
        # add a spacer to make the entries aligned at the top
        spacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.grid.addItem(spacer, row, 1)
        self.variablesEntries[variables[0]].setFocus()
        self.top.adjustSize()

        # generate the buttons
        layout1 = QHBoxLayout()
        layout1.setContentsMargins(0, 0, 0, 0)
        layout1.setSpacing(6)
        layout1.setObjectName("layout1")
        
        spacer1 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout1.addItem(spacer1)

        self.okButton = QPushButton(self)
        self.okButton.setObjectName("okButton")
        self.okButton.setDefault(True)
        layout1.addWidget(self.okButton)

        self.cancelButton = QPushButton(self)
        self.cancelButton.setObjectName("cancelButton")
        layout1.addWidget(self.cancelButton)
        
        spacer2 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout1.addItem(spacer2)
        
        self.TemplateMultipleVariablesDialogLayout.addLayout(layout1)

        # set the texts of the standard widgets
        self.setWindowTitle(self.tr("Enter Template Variables"))
        self.okButton.setText(self.tr("&OK"))
        self.cancelButton.setText(self.tr("&Cancel"))

        # polish up the dialog
        self.resize(QSize(400, 480).expandedTo(self.minimumSizeHint()))

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

    def getVariables(self):
        """
        Public method to get the values for all variables.
        
        @return dictionary with the variable as a key and its value (string)
        """
        values = {}
        for var, textEdit in list(self.variablesEntries.items()):
            try:
                values[var] = textEdit.text()
            except AttributeError:
                values[var] = textEdit.toPlainText()
        return values
