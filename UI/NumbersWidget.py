# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a widget to show numbers in different formats.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QAbstractTableModel, \
    qVersion
from PyQt5.QtWidgets import QWidget, QHeaderView

from E5Gui.E5Application import e5App

from .Ui_NumbersWidget import Ui_NumbersWidget

import UI.PixmapCache


class BinaryModel(QAbstractTableModel):
    """
    Class implementing a model for entering binary numbers.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(BinaryModel, self).__init__(parent)
        
        self.__bits = 0
        self.__value = 0
    
    def rowCount(self, parent):
        """
        Public method to get the number of rows of the model.
        
        @param parent parent index (QModelIndex)
        @return number of columns (integer)
        """
        return 1
    
    def columnCount(self, parent):
        """
        Public method to get the number of columns of the model.
        
        @param parent parent index (QModelIndex)
        @return number of columns (integer)
        """
        return self.__bits
    
    def data(self, index, role=Qt.DisplayRole):
        """
        Public method to get data from the model.
        
        @param index index to get data for (QModelIndex)
        @param role role of the data to retrieve (integer)
        @return requested data
        """
        if role == Qt.CheckStateRole:
            return (self.__value >> (self.__bits - index.column() - 1)) & 1
        
        elif role == Qt.DisplayRole:
            return ""
        
        return None
    
    def flags(self, index):
        """
        Public method to get flags from the model.
        
        @param index index to get flags for (QModelIndex)
        @return flags (Qt.ItemFlags)
        """
        return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Public method to get header data from the model.
        
        @param section section number (integer)
        @param orientation orientation (Qt.Orientation)
        @param role role of the data to retrieve (integer)
        @return requested data
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return str(self.__bits - section - 1)
        
        return QAbstractTableModel.headerData(self, section, orientation, role)
    
    def setBits(self, bits):
        """
        Public slot to set the number of bits.
        
        @param bits number of bits to show (integer)
        """
        self.beginResetModel()
        self.__bits = bits
        self.endResetModel()
    
    def setValue(self, value):
        """
        Public slot to set the value to show.
        
        @param value value to show (integer)
        """
        self.beginResetModel()
        self.__value = value
        self.endResetModel()
    
    def setBitsAndValue(self, bits, value):
        """
        Public slot to set the number of bits and the value to show.
        
        @param bits number of bits to show (integer)
        @param value value to show (integer)
        """
        self.__bits = bits
        self.__value = value
        self.beginResetModel()
        self.endResetModel()
    
    def getValue(self):
        """
        Public slot to get the current value.
        
        @return current value of the model (integer)
        """
        return self.__value
    
    def setData(self, index, value, role=Qt.EditRole):
        """
        Public method to set the data of a node cell.
        
        @param index index of the node cell (QModelIndex)
        @param value value to be set
        @param role role of the data (integer)
        @return flag indicating success (boolean)
        """
        if role == Qt.CheckStateRole:
            if value == Qt.Checked and not self.data(index, Qt.CheckStateRole):
                # that seems like a hack; Qt 4.6 always sends Qt.Checked
                self.__value |= (1 << self.__bits - index.column() - 1)
            else:
                self.__value &= ~(1 << self.__bits - index.column() - 1)
            self.dataChanged.emit(index, index)
            return True
        
        return False


class NumbersWidget(QWidget, Ui_NumbersWidget):
    """
    Class implementing a widget to show numbers in different formats.
    
    @signal insertNumber(str) emitted after the user has entered a number
            and selected the number format
    """
    insertNumber = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(NumbersWidget, self).__init__(parent)
        self.setupUi(self)
        
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        
        self.__badNumberSheet = "background-color: #ffa0a0;"
        
        self.binInButton.setIcon(UI.PixmapCache.getIcon("2downarrow.png"))
        self.binOutButton.setIcon(UI.PixmapCache.getIcon("2uparrow.png"))
        self.octInButton.setIcon(UI.PixmapCache.getIcon("2downarrow.png"))
        self.octOutButton.setIcon(UI.PixmapCache.getIcon("2uparrow.png"))
        self.decInButton.setIcon(UI.PixmapCache.getIcon("2downarrow.png"))
        self.decOutButton.setIcon(UI.PixmapCache.getIcon("2uparrow.png"))
        self.hexInButton.setIcon(UI.PixmapCache.getIcon("2downarrow.png"))
        self.hexOutButton.setIcon(UI.PixmapCache.getIcon("2uparrow.png"))
        
        self.formatBox.addItem(self.tr("Auto"), 0)
        self.formatBox.addItem(self.tr("Dec"), 10)
        self.formatBox.addItem(self.tr("Hex"), 16)
        self.formatBox.addItem(self.tr("Oct"), 8)
        self.formatBox.addItem(self.tr("Bin"), 2)
        
        self.sizeBox.addItem("8", 8)
        self.sizeBox.addItem("16", 16)
        self.sizeBox.addItem("32", 32)
        self.sizeBox.addItem("64", 64)
        
        self.__input = 0
        self.__inputValid = True
        self.__bytes = 1
        
        self.__model = BinaryModel(self)
        self.binTable.setModel(self.__model)
        if qVersion() >= "5.0.0":
            self.binTable.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeToContents)
        else:
            self.binTable.horizontalHeader().setResizeMode(
                QHeaderView.ResizeToContents)
        self.__model.setBitsAndValue(self.__bytes * 8, self.__input)
        self.__model.dataChanged.connect(self.__binModelDataChanged)
    
    def __formatNumbers(self, format):
        """
        Private method to format the various number inputs.
        
        @param format number format indicator (integer)
        """
        self.__block(True)
        
        self.binEdit.setStyleSheet("")
        self.octEdit.setStyleSheet("")
        self.decEdit.setStyleSheet("")
        self.hexEdit.setStyleSheet("")
        
        # determine byte count
        bytes = 8
        tmp = self.__input
        for i in range(8):
            c = (tmp & 0xff00000000000000) >> 7 * 8
            if c != 0 and self.__input >= 0:
                break
            if c != 0xff and self.__input < 0:
                break
            tmp <<= 8
            bytes -= 1
        if bytes == 0:
            bytes = 1
        self.__bytes = bytes
        
        bytesIn = self.sizeBox.itemData(self.sizeBox.currentIndex()) // 8
        if bytesIn and bytes > bytesIn:
            self.sizeBox.setStyleSheet(self.__badNumberSheet)
        else:
            self.sizeBox.setStyleSheet("")
        
        # octal
        if format != 8:
            self.octEdit.setText("{0:0{1}o}".format(self.__input, bytesIn * 3))
        
        # decimal
        if format != 10:
            self.decEdit.setText("{0:d}".format(self.__input))
        
        # hexadecimal
        if format != 16:
            self.hexEdit.setText("{0:0{1}x}".format(self.__input, bytesIn * 2))
        
        # octal
        if format != 8:
            self.octEdit.setText("{0:0{1}o}".format(self.__input, bytesIn * 3))
        
        # binary
        if format != 2:
            num = "{0:0{1}b}".format(self.__input, bytesIn * 8)
            self.binEdit.setText(num)
        
        self.__model.setBitsAndValue(len(self.binEdit.text()), self.__input)
        
        self.__block(False)
    
    def __block(self, b):
        """
        Private slot to block some signals.
        
        @param b flah indicating the blocking state (boolean)
        """
        self.hexEdit.blockSignals(b)
        self.decEdit.blockSignals(b)
        self.octEdit.blockSignals(b)
        self.binEdit.blockSignals(b)
        self.binTable.blockSignals(b)
    
    @pyqtSlot(int)
    def on_sizeBox_valueChanged(self, value):
        """
        Private slot handling a change of the bit size.
        
        @param value selected bit size (integer)
        """
        self.__formatNumbers(10)
    
    @pyqtSlot()
    def on_byteOrderButton_clicked(self):
        """
        Private slot to swap the byte order.
        """
        bytesIn = self.sizeBox.itemData(self.sizeBox.currentIndex()) // 8
        if bytesIn == 0:
            bytesIn = self.__bytes
        
        tmp1 = self.__input
        tmp2 = 0
        for i in range(bytesIn):
            tmp2 <<= 8
            tmp2 |= tmp1 & 0xff
            tmp1 >>= 8
        
        self.__input = tmp2
        self.__formatNumbers(0)
    
    @pyqtSlot()
    def on_binInButton_clicked(self):
        """
        Private slot to retrieve a binary number from the current editor.
        """
        number = e5App().getObject("ViewManager").getNumber()
        if number == "":
            return
        
        self.binEdit.setText(number)
        self.binEdit.setFocus()
    
    @pyqtSlot(str)
    def on_binEdit_textChanged(self, txt):
        """
        Private slot to handle input of a binary number.
        
        @param txt text entered (string)
        """
        try:
            self.__input = int(txt, 2)
            self.__inputValid = True
        except ValueError:
            self.__inputValid = False
        
        if self.__inputValid:
            self.__formatNumbers(2)
        else:
            self.binEdit.setStyleSheet(self.__badNumberSheet)
    
    @pyqtSlot()
    def on_binOutButton_clicked(self):
        """
        Private slot to send a binary number.
        """
        self.insertNumber.emit(self.binEdit.text())
    
    def __binModelDataChanged(self, start, end):
        """
        Private slot to handle a change of the binary model value by the user.
        
        @param start start index (QModelIndex)
        @param end end index (QModelIndex)
        """
        val = self.__model.getValue()
        bytesIn = self.sizeBox.itemData(self.sizeBox.currentIndex()) // 8
        num = "{0:0{1}b}".format(val, bytesIn * 8)
        self.binEdit.setText(num)
    
    @pyqtSlot()
    def on_octInButton_clicked(self):
        """
        Private slot to retrieve an octal number from the current editor.
        """
        number = e5App().getObject("ViewManager").getNumber()
        if number == "":
            return
        
        self.octEdit.setText(number)
        self.octEdit.setFocus()
    
    @pyqtSlot(str)
    def on_octEdit_textChanged(self, txt):
        """
        Private slot to handle input of an octal number.
        
        @param txt text entered (string)
        """
        try:
            self.__input = int(txt, 8)
            self.__inputValid = True
        except ValueError:
            self.__inputValid = False
        
        if self.__inputValid:
            self.__formatNumbers(8)
        else:
            self.octEdit.setStyleSheet(self.__badNumberSheet)
    
    @pyqtSlot()
    def on_octOutButton_clicked(self):
        """
        Private slot to send an octal number.
        """
        self.insertNumber.emit(self.octEdit.text())
    
    @pyqtSlot()
    def on_decInButton_clicked(self):
        """
        Private slot to retrieve a decimal number from the current editor.
        """
        number = e5App().getObject("ViewManager").getNumber()
        if number == "":
            return
        
        self.decEdit.setText(number)
        self.decEdit.setFocus()
    
    @pyqtSlot(str)
    def on_decEdit_textChanged(self, txt):
        """
        Private slot to handle input of a decimal number.
        
        @param txt text entered (string)
        """
        try:
            self.__input = int(txt, 10)
            self.__inputValid = True
        except ValueError:
            self.__inputValid = False
        
        if self.__inputValid:
            self.__formatNumbers(10)
        else:
            self.decEdit.setStyleSheet(self.__badNumberSheet)
    
    @pyqtSlot()
    def on_decOutButton_clicked(self):
        """
        Private slot to send a decimal number.
        """
        self.insertNumber.emit(self.decEdit.text())
    
    @pyqtSlot()
    def on_hexInButton_clicked(self):
        """
        Private slot to retrieve a hexadecimal number from the current editor.
        """
        number = e5App().getObject("ViewManager").getNumber()
        if number == "":
            return
        
        self.hexEdit.setText(number)
        self.hexEdit.setFocus()
    
    @pyqtSlot(str)
    def on_hexEdit_textChanged(self, txt):
        """
        Private slot to handle input of a hexadecimal number.
        
        @param txt text entered (string)
        """
        try:
            self.__input = int(txt, 16)
            self.__inputValid = True
        except ValueError:
            self.__inputValid = False
        
        if self.__inputValid:
            self.__formatNumbers(16)
        else:
            self.hexEdit.setStyleSheet(self.__badNumberSheet)
    
    @pyqtSlot()
    def on_hexOutButton_clicked(self):
        """
        Private slot to send a hexadecimal number.
        """
        self.insertNumber.emit(self.hexEdit.text())
