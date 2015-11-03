# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to save a screenshot of a web page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, Qt, QFile, QFileInfo
from PyQt5.QtGui import QImage, QPainter, QPixmap
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QAbstractButton

from E5Gui import E5FileDialog, E5MessageBox

from .Ui_PageScreenDialog import Ui_PageScreenDialog


class PageScreenDialog(QDialog, Ui_PageScreenDialog):
    """
    Class documentation goes here.
    """
    def __init__(self, view, visibleOnly=False, parent=None):
        """
        Constructor
        
        @param view reference to the web view containing the page to be saved
            (HelpBrowser)
        @param visibleOnly flag indicating to just save the visible part
            of the page (boolean)
        @param parent reference to the parent widget (QWidget)
        """
        super(PageScreenDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.__view = view
        self.__createPixmap(visibleOnly)
        self.pageScreenLabel.setPixmap(self.__pagePixmap)
    
    def __createPixmap(self, visibleOnly):
        """
        Private slot to create a pixmap of the associated view's page.
        
        @param visibleOnly flag indicating to just save the visible part
            of the page (boolean)
        """
        page = self.__view.page()
        origSize = page.viewportSize()
        if not visibleOnly:
            page.setViewportSize(page.mainFrame().contentsSize())
        
        image = QImage(page.viewportSize(), QImage.Format_ARGB32)
        painter = QPainter(image)
        page.mainFrame().render(painter)
        painter.end()
        
        self.__pagePixmap = QPixmap.fromImage(image)
        
        page.setViewportSize(origSize)
    
    def __savePageScreen(self):
        """
        Private slot to save the page screen.
        
        @return flag indicating success (boolean)
        """
        fileName = E5FileDialog.getSaveFileName(
            self,
            self.tr("Save Page Screen"),
            self.tr("screen.png"),
            self.tr("Portable Network Graphics File (*.png)"),
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        if not fileName:
            return False
        
        if QFileInfo(fileName).exists():
            res = E5MessageBox.yesNo(
                self,
                self.tr("Save Page Screen"),
                self.tr("<p>The file <b>{0}</b> already exists."
                        " Overwrite it?</p>").format(fileName),
                icon=E5MessageBox.Warning)
            if not res:
                return False
        
        file = QFile(fileName)
        if not file.open(QFile.WriteOnly):
            E5MessageBox.warning(
                self,
                self.tr("Save Page Screen"),
                self.tr("Cannot write file '{0}:\n{1}.")
                .format(fileName, file.errorString()))
            return False
        
        res = self.__pagePixmap.save(file)
        file.close()
        
        if not res:
            E5MessageBox.warning(
                self,
                self.tr("Save Page Screen"),
                self.tr("Cannot write file '{0}:\n{1}.")
                .format(fileName, file.errorString()))
            return False
        
        return True
    
    @pyqtSlot(QAbstractButton)
    def on_buttonBox_clicked(self, button):
        """
        Private slot to handle clicks of the dialog buttons.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.reject()
        elif button == self.buttonBox.button(QDialogButtonBox.Save):
            if self.__savePageScreen():
                self.accept()
