# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for the configuration of a keyboard shortcut.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, QEvent, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from .Ui_ShortcutDialog import Ui_ShortcutDialog


class ShortcutDialog(QDialog, Ui_ShortcutDialog):
    """
    Class implementing a dialog for the configuration of a keyboard shortcut.
    
    @signal shortcutChanged(QKeySequence, QKeySequence, bool, string) emitted
        after the OK button was pressed
    """
    shortcutChanged = pyqtSignal(QKeySequence, QKeySequence, bool, str)
    
    def __init__(self, parent=None, name=None, modal=False):
        """
        Constructor
        
        @param parent The parent widget of this dialog. (QWidget)
        @param name The name of this dialog. (string)
        @param modal Flag indicating a modal dialog. (boolean)
        """
        super(ShortcutDialog, self).__init__(parent)
        if name:
            self.setObjectName(name)
        self.setModal(modal)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.keyIndex = 0
        self.keys = [0, 0, 0, 0]
        self.noCheck = False
        self.objectType = ""
        
        self.primaryClearButton.clicked.connect(self.__clear)
        self.alternateClearButton.clicked.connect(self.__clear)
        self.primaryButton.clicked.connect(self.__typeChanged)
        self.alternateButton.clicked.connect(self.__typeChanged)
        
        self.shortcutsGroup.installEventFilter(self)
        self.primaryButton.installEventFilter(self)
        self.alternateButton.installEventFilter(self)
        self.primaryClearButton.installEventFilter(self)
        self.alternateClearButton.installEventFilter(self)
        self.keyEdit.installEventFilter(self)
        self.alternateKeyEdit.installEventFilter(self)
        
        self.buttonBox.button(QDialogButtonBox.Ok).installEventFilter(self)
        self.buttonBox.button(QDialogButtonBox.Cancel).installEventFilter(self)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())

    def setKeys(self, key, alternateKey, noCheck, objectType):
        """
        Public method to set the key to be configured.
        
        @param key key sequence to be changed (QKeySequence)
        @param alternateKey alternate key sequence to be changed (QKeySequence)
        @param noCheck flag indicating that no uniqueness check should
            be performed (boolean)
        @param objectType type of the object (string).
        """
        self.keyIndex = 0
        self.keys = [0, 0, 0, 0]
        self.keyEdit.setText(key.toString())
        self.alternateKeyEdit.setText(alternateKey.toString())
        self.primaryButton.setChecked(True)
        self.noCheck = noCheck
        self.objectType = objectType
        
    def on_buttonBox_accepted(self):
        """
        Private slot to handle the OK button press.
        """
        self.hide()
        self.shortcutChanged.emit(
            QKeySequence(self.keyEdit.text()),
            QKeySequence(self.alternateKeyEdit.text()),
            self.noCheck, self.objectType)

    def __clear(self):
        """
        Private slot to handle the Clear button press.
        """
        self.keyIndex = 0
        self.keys = [0, 0, 0, 0]
        self.__setKeyEditText("")
        
    def __typeChanged(self):
        """
        Private slot to handle the change of the shortcuts type.
        """
        self.keyIndex = 0
        self.keys = [0, 0, 0, 0]
        
    def __setKeyEditText(self, txt):
        """
        Private method to set the text of a key edit.
        
        @param txt text to be set (string)
        """
        if self.primaryButton.isChecked():
            self.keyEdit.setText(txt)
        else:
            self.alternateKeyEdit.setText(txt)
        
    def eventFilter(self, watched, event):
        """
        Public method called to filter the event queue.
        
        @param watched the QObject being watched
        @param event the event that occurred
        @return always False
        """
        if event.type() == QEvent.KeyPress:
            self.keyPressEvent(event)
            return True
            
        return False
        
    def keyPressEvent(self, evt):
        """
        Protected method to handle a key press event.
        
        @param evt the key event (QKeyEvent)
        """
        if evt.key() in [Qt.Key_Control, Qt.Key_Meta, Qt.Key_Shift, Qt.Key_Alt,
                         Qt.Key_Menu, Qt.Key_Hyper_L, Qt.Key_Hyper_R,
                         Qt.Key_Super_L, Qt.Key_Super_R]:
            return
    
        if self.keyIndex == 4:
            self.keyIndex = 0
            self.keys = [0, 0, 0, 0]
    
        if evt.key() == Qt.Key_Backtab and evt.modifiers() & Qt.ShiftModifier:
            self.keys[self.keyIndex] = Qt.Key_Tab
        else:
            self.keys[self.keyIndex] = evt.key()
        
        if evt.modifiers() & Qt.ShiftModifier:
            self.keys[self.keyIndex] += Qt.SHIFT
        if evt.modifiers() & Qt.ControlModifier:
            self.keys[self.keyIndex] += Qt.CTRL
        if evt.modifiers() & Qt.AltModifier:
            self.keys[self.keyIndex] += Qt.ALT
        if evt.modifiers() & Qt.MetaModifier:
            self.keys[self.keyIndex] += Qt.META
        
        self.keyIndex += 1
        
        if self.keyIndex == 1:
            self.__setKeyEditText(QKeySequence(self.keys[0]).toString())
        elif self.keyIndex == 2:
            self.__setKeyEditText(
                QKeySequence(self.keys[0], self.keys[1]).toString())
        elif self.keyIndex == 3:
            self.__setKeyEditText(QKeySequence(
                self.keys[0], self.keys[1],
                self.keys[2]).toString())
        elif self.keyIndex == 4:
            self.__setKeyEditText(QKeySequence(
                self.keys[0], self.keys[1],
                self.keys[2], self.keys[3]).toString())
