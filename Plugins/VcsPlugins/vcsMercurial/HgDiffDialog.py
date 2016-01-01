# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the hg diff command process.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

from PyQt5.QtCore import pyqtSlot, QFileInfo, Qt
from PyQt5.QtGui import QTextCursor, QCursor
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QApplication

from E5Gui import E5MessageBox, E5FileDialog
from E5Gui.E5Application import e5App

from .Ui_HgDiffDialog import Ui_HgDiffDialog
from .HgDiffHighlighter import HgDiffHighlighter
from .HgDiffGenerator import HgDiffGenerator

import Utilities
import Preferences


class HgDiffDialog(QWidget, Ui_HgDiffDialog):
    """
    Class implementing a dialog to show the output of the hg diff command
    process.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super(HgDiffDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.refreshButton = self.buttonBox.addButton(
            self.tr("Refresh"), QDialogButtonBox.ActionRole)
        self.refreshButton.setToolTip(
            self.tr("Press to refresh the display"))
        self.refreshButton.setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Save).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.searchWidget.attachTextEdit(self.contents)
        
        self.vcs = vcs
        
        font = Preferences.getEditorOtherFonts("MonospacedFont")
        self.contents.setFontFamily(font.family())
        self.contents.setFontPointSize(font.pointSize())
        
        self.highlighter = HgDiffHighlighter(self.contents.document())
        
        self.__diffGenerator = HgDiffGenerator(vcs, self)
        self.__diffGenerator.finished.connect(self.__generatorFinished)
    
    def closeEvent(self, e):
        """
        Protected slot implementing a close event handler.
        
        @param e close event (QCloseEvent)
        """
        self.__diffGenerator.stopProcess()
        e.accept()
    
    def start(self, fn, versions=None, bundle=None, qdiff=False,
              refreshable=False):
        """
        Public slot to start the hg diff command.
        
        @param fn filename to be diffed (string)
        @keyparam versions list of versions to be diffed (list of up to
            2 strings or None)
        @keyparam bundle name of a bundle file (string)
        @keyparam qdiff flag indicating qdiff command shall be used (boolean)
        @keyparam refreshable flag indicating a refreshable diff (boolean)
        """
        self.refreshButton.setVisible(refreshable)
        
        self.errorGroup.hide()
        self.filename = fn
        
        self.contents.clear()
        self.filesCombo.clear()
        
        if qdiff:
            self.setWindowTitle(self.tr("Patch Contents"))
        
        self.raise_()
        self.activateWindow()
        
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        procStarted = self.__diffGenerator.start(
            fn, versions=versions, bundle=bundle, qdiff=qdiff)
        if not procStarted:
            E5MessageBox.critical(
                self,
                self.tr('Process Generation Error'),
                self.tr(
                    'The process {0} could not be started. '
                    'Ensure, that it is in the search path.'
                ).format('hg'))
    
    def __generatorFinished(self):
        """
        Private slot connected to the finished signal.
        """
        QApplication.restoreOverrideCursor()
        self.refreshButton.setEnabled(True)
        
        diff, errors, fileSeparators = self.__diffGenerator.getResult()
        
        if diff:
            self.contents.setPlainText("".join(diff))
        else:
            self.contents.setPlainText(
                self.tr('There is no difference.'))
        
        if errors:
            self.errorGroup.show()
            self.errors.setPlainText("".join(errors))
            self.errors.ensureCursorVisible()
        
        self.buttonBox.button(QDialogButtonBox.Save).setEnabled(bool(diff))
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        self.buttonBox.button(QDialogButtonBox.Close).setFocus(
            Qt.OtherFocusReason)
        
        tc = self.contents.textCursor()
        tc.movePosition(QTextCursor.Start)
        self.contents.setTextCursor(tc)
        self.contents.ensureCursorVisible()
        
        self.filesCombo.addItem(self.tr("<Start>"), 0)
        self.filesCombo.addItem(self.tr("<End>"), -1)
        for oldFile, newFile, pos in sorted(fileSeparators):
            if not oldFile:
                self.filesCombo.addItem(newFile, pos)
            elif oldFile != newFile:
                self.filesCombo.addItem(
                    "{0}\n{1}".format(oldFile, newFile), pos)
            else:
                self.filesCombo.addItem(oldFile, pos)
    
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Save):
            self.on_saveButton_clicked()
        elif button == self.refreshButton:
            self.on_refreshButton_clicked()
    
    @pyqtSlot(int)
    def on_filesCombo_activated(self, index):
        """
        Private slot to handle the selection of a file.
        
        @param index activated row (integer)
        """
        para = self.filesCombo.itemData(index)
        
        if para == 0:
            tc = self.contents.textCursor()
            tc.movePosition(QTextCursor.Start)
            self.contents.setTextCursor(tc)
            self.contents.ensureCursorVisible()
        elif para == -1:
            tc = self.contents.textCursor()
            tc.movePosition(QTextCursor.End)
            self.contents.setTextCursor(tc)
            self.contents.ensureCursorVisible()
        else:
            # step 1: move cursor to end
            tc = self.contents.textCursor()
            tc.movePosition(QTextCursor.End)
            self.contents.setTextCursor(tc)
            self.contents.ensureCursorVisible()
            
            # step 2: move cursor to desired line
            tc = self.contents.textCursor()
            delta = tc.blockNumber() - para
            tc.movePosition(QTextCursor.PreviousBlock, QTextCursor.MoveAnchor,
                            delta)
            self.contents.setTextCursor(tc)
            self.contents.ensureCursorVisible()
    
    @pyqtSlot()
    def on_saveButton_clicked(self):
        """
        Private slot to handle the Save button press.
        
        It saves the diff shown in the dialog to a file in the local
        filesystem.
        """
        if isinstance(self.filename, list):
            if len(self.filename) > 1:
                fname = self.vcs.splitPathList(self.filename)[0]
            else:
                dname, fname = self.vcs.splitPath(self.filename[0])
                if fname != '.':
                    fname = "{0}.diff".format(self.filename[0])
                else:
                    fname = dname
        else:
            fname = self.vcs.splitPath(self.filename)[0]
        
        fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            self,
            self.tr("Save Diff"),
            fname,
            self.tr("Patch Files (*.diff)"),
            None,
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        
        if not fname:
            return  # user aborted
        
        ext = QFileInfo(fname).suffix()
        if not ext:
            ex = selectedFilter.split("(*")[1].split(")")[0]
            if ex:
                fname += ex
        if QFileInfo(fname).exists():
            res = E5MessageBox.yesNo(
                self,
                self.tr("Save Diff"),
                self.tr("<p>The patch file <b>{0}</b> already exists."
                        " Overwrite it?</p>").format(fname),
                icon=E5MessageBox.Warning)
            if not res:
                return
        fname = Utilities.toNativeSeparators(fname)
        
        eol = e5App().getObject("Project").getEolString()
        try:
            f = open(fname, "w", encoding="utf-8", newline="")
            f.write(eol.join(self.contents.toPlainText().splitlines()))
            f.close()
        except IOError as why:
            E5MessageBox.critical(
                self, self.tr('Save Diff'),
                self.tr(
                    '<p>The patch file <b>{0}</b> could not be saved.'
                    '<br>Reason: {1}</p>')
                .format(fname, str(why)))
    
    @pyqtSlot()
    def on_refreshButton_clicked(self):
        """
        Private slot to refresh the display.
        """
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        
        self.buttonBox.button(QDialogButtonBox.Save).setEnabled(False)
        self.refreshButton.setEnabled(False)
        
        self.start(self.filename, refreshable=True)
