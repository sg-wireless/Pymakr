# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a specialized line edit for entering IRC messages.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, qVersion

from E5Gui.E5LineEdit import E5LineEdit, E5ClearableLineEdit


class IrcMessageEdit(E5ClearableLineEdit):
    """
    Class implementing a specialized line edit for entering IRC messages.
    """
    MaxHistory = 100
    
    def __init__(self, parent=None, inactiveText="",
                 side=E5LineEdit.RightSide):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        @keyparam inactiveText text to be shown on inactivity (string)
        @keyparam side side the clear button should be shown at
            (E5LineEdit.RightSide, E5LineEdit.LeftSide)
        """
        super(IrcMessageEdit, self).__init__(parent, inactiveText, side)
        
        self.__historyList = [""]   # initialize with one empty line
        self.__historyLine = 0
    
    def setText(self, text):
        """
        Public method to set the text.
        
        Note: This reimplementation ensures, that the cursor is at the end of
        the text.
        
        @param text text to be set (string)
        """
        super(IrcMessageEdit, self).setText(text)
        self.setCursorPosition(len(text))
    
    def keyPressEvent(self, evt):
        """
        Protected method implementing special key handling.
        
        @param evt reference to the event (QKeyEvent)
        """
        key = evt.key()
        if key == Qt.Key_Up:
            self.__getHistory(True)
            return
        elif key == Qt.Key_Down:
            self.__getHistory(False)
            return
        elif key in [Qt.Key_Return, Qt.Key_Enter]:
            if self.text():
                self.__addHistory(self.text())
        elif evt.text() == chr(21):
            # ^U: clear the text
            self.setText("")
        
        super(IrcMessageEdit, self).keyPressEvent(evt)
    
    def wheelEvent(self, evt):
        """
        Protected slot to support wheel events.
        
        @param evt reference to the wheel event (QWheelEvent)
        """
        if qVersion() >= "5.0.0":
            delta = evt.angleDelta().y()
        else:
            delta = evt.delta()
        if delta > 0:
            self.__getHistory(True)
        elif delta < 0:
            self.__getHistory(False)
        
        super(IrcMessageEdit, self).wheelEvent(evt)
    
    def __addHistory(self, txt):
        """
        Private method to add an entry to the history.
        
        @param txt text to be added to the history (string)
        """
        # Only add the entry, if it is not the same as last time
        if len(self.__historyList) == 1 or \
           (len(self.__historyList) > 1 and self.__historyList[1] != txt):
            # Replace empty first entry and add new empty first entry
            self.__historyList[0] = txt
            self.__historyList.insert(0, "")
            # Keep history below the defined limit
            del self.__historyList[IrcMessageEdit.MaxHistory:]
        
        self.__historyLine = 0
    
    def __getHistory(self, up):
        """
        Private method to move in the history.
        
        @param up flag indicating the direction (boolean)
        """
        # preserve the current text, if it is not empty
        if self.text():
            self.__historyList[self.__historyLine] = self.text()
        
        if up:
            self.__historyLine += 1
            # If the position was moved past the end of the history,
            # go to the last entry
            if self.__historyLine == len(self.__historyList):
                self.__historyLine -= 1
                return
        else:
            # If the position is at the top of the history, arrow-down shall
            # add the text to the history and clear the line edit for new input
            if self.__historyLine == 0:
                if self.text():
                    self.__addHistory(self.text())
                self.setText("")
            else:
                # If the position is not at the top of the history,
                # decrement it
                self.__historyLine -= 1
        
        # replace the text of the line edit with the selected history entry
        self.setText(self.__historyList[self.__historyLine])
