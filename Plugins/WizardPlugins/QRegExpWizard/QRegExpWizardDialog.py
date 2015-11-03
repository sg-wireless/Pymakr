# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the QRegExp wizard dialog.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QFileInfo, QRegExp, Qt, pyqtSlot, qVersion
from PyQt5.QtGui import QClipboard, QTextCursor
from PyQt5.QtWidgets import QWidget, QDialog, QApplication, QDialogButtonBox, \
    QVBoxLayout, QTableWidgetItem

from E5Gui import E5MessageBox, E5FileDialog
from E5Gui.E5MainWindow import E5MainWindow

from .Ui_QRegExpWizardDialog import Ui_QRegExpWizardWidget

import UI.PixmapCache

import Utilities
import Preferences


class QRegExpWizardWidget(QWidget, Ui_QRegExpWizardWidget):
    """
    Class implementing the QRegExp wizard dialog.
    """
    def __init__(self, parent=None, fromEric=True):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        @param fromEric flag indicating a call from within eric6
        """
        super(QRegExpWizardWidget, self).__init__(parent)
        self.setupUi(self)
        
        # initialize icons of the tool buttons
        # regexp tool buttons
        self.charButton.setIcon(UI.PixmapCache.getIcon("characters.png"))
        self.anycharButton.setIcon(UI.PixmapCache.getIcon("anychar.png"))
        self.repeatButton.setIcon(UI.PixmapCache.getIcon("repeat.png"))
        self.nonGroupButton.setIcon(UI.PixmapCache.getIcon("nongroup.png"))
        self.groupButton.setIcon(UI.PixmapCache.getIcon("group.png"))
        self.altnButton.setIcon(UI.PixmapCache.getIcon("altn.png"))
        self.beglineButton.setIcon(UI.PixmapCache.getIcon("begline.png"))
        self.endlineButton.setIcon(UI.PixmapCache.getIcon("endline.png"))
        self.wordboundButton.setIcon(
            UI.PixmapCache.getIcon("wordboundary.png"))
        self.nonwordboundButton.setIcon(
            UI.PixmapCache.getIcon("nonwordboundary.png"))
        self.poslookaheadButton.setIcon(
            UI.PixmapCache.getIcon("poslookahead.png"))
        self.neglookaheadButton.setIcon(
            UI.PixmapCache.getIcon("neglookahead.png"))
        self.undoButton.setIcon(UI.PixmapCache.getIcon("editUndo.png"))
        self.redoButton.setIcon(UI.PixmapCache.getIcon("editRedo.png"))
        # wildcard tool buttons
        self.wildcardCharButton.setIcon(
            UI.PixmapCache.getIcon("characters.png"))
        self.wildcardAnycharButton.setIcon(
            UI.PixmapCache.getIcon("anychar.png"))
        self.wildcardRepeatButton.setIcon(UI.PixmapCache.getIcon("repeat.png"))
        # W3C tool buttons
        self.w3cCharButton.setIcon(UI.PixmapCache.getIcon("characters.png"))
        self.w3cAnycharButton.setIcon(UI.PixmapCache.getIcon("anychar.png"))
        self.w3cRepeatButton.setIcon(UI.PixmapCache.getIcon("repeat.png"))
        self.w3cGroupButton.setIcon(UI.PixmapCache.getIcon("group.png"))
        self.w3cAltnButton.setIcon(UI.PixmapCache.getIcon("altn.png"))
        
        # initialize the syntax pattern combo
        self.syntaxCombo.addItem("RegExp", QRegExp.RegExp)
        self.syntaxCombo.addItem("RegExp2", QRegExp.RegExp2)
        self.syntaxCombo.addItem("Wildcard", QRegExp.Wildcard)
        self.syntaxCombo.addItem("Unix Wildcard", QRegExp.WildcardUnix)
        self.syntaxCombo.addItem("Fixed String", QRegExp.FixedString)
        self.syntaxCombo.addItem("W3C XML Schema 1.1", QRegExp.W3CXmlSchema11)
        if qVersion() >= "5.0.0":
            self.syntaxCombo.setCurrentIndex(1)
        
        self.saveButton = self.buttonBox.addButton(
            self.tr("Save"), QDialogButtonBox.ActionRole)
        self.saveButton.setToolTip(
            self.tr("Save the regular expression to a file"))
        self.loadButton = self.buttonBox.addButton(
            self.tr("Load"), QDialogButtonBox.ActionRole)
        self.loadButton.setToolTip(
            self.tr("Load a regular expression from a file"))
        self.validateButton = self.buttonBox.addButton(
            self.tr("Validate"), QDialogButtonBox.ActionRole)
        self.validateButton.setToolTip(
            self.tr("Validate the regular expression"))
        self.executeButton = self.buttonBox.addButton(
            self.tr("Execute"), QDialogButtonBox.ActionRole)
        self.executeButton.setToolTip(
            self.tr("Execute the regular expression"))
        self.nextButton = self.buttonBox.addButton(
            self.tr("Next match"), QDialogButtonBox.ActionRole)
        self.nextButton.setToolTip(
            self.tr("Show the next match of the regular expression"))
        self.nextButton.setEnabled(False)
        
        if fromEric:
            self.buttonBox.setStandardButtons(
                QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
            self.copyButton = None
        else:
            self.copyButton = self.buttonBox.addButton(
                self.tr("Copy"), QDialogButtonBox.ActionRole)
            self.copyButton.setToolTip(
                self.tr("Copy the regular expression to the clipboard"))
            self.buttonBox.setStandardButtons(QDialogButtonBox.Close)
            self.variableLabel.hide()
            self.variableLineEdit.hide()
            self.variableLine.hide()
            self.regexpLineEdit.setFocus()
    
    @pyqtSlot(int)
    def on_syntaxCombo_currentIndexChanged(self, index):
        """
        Private slot handling the selection of a pattern syntax.
        
        @param index index of the selected entry (integer)
        """
        syntax = self.syntaxCombo.itemData(index)
        self.regexpButtonsFrame.setVisible(syntax in [
            QRegExp.RegExp, QRegExp.RegExp2])
        self.regexpButtonsFrame.setEnabled(syntax in [
            QRegExp.RegExp, QRegExp.RegExp2])
        self.wildcardButtonsFrame.setVisible(syntax in [
            QRegExp.Wildcard, QRegExp.WildcardUnix])
        self.wildcardButtonsFrame.setEnabled(syntax in [
            QRegExp.Wildcard, QRegExp.WildcardUnix])
        self.w3cButtonsFrame.setVisible(syntax in [QRegExp.W3CXmlSchema11])
        self.w3cButtonsFrame.setEnabled(syntax in [QRegExp.W3CXmlSchema11])

    def __insertString(self, s, steps=0):
        """
        Private method to insert a string into line edit and move cursor.
        
        @param s string to be inserted into the regexp line edit
            (string)
        @param steps number of characters to move the cursor (integer).
            Negative steps moves cursor back, positives forward.
        """
        self.regexpLineEdit.insert(s)
        self.regexpLineEdit.cursorForward(False, steps)
        
    @pyqtSlot()
    def on_anycharButton_clicked(self):
        """
        Private slot to handle the any character toolbutton.
        """
        self.__insertString(".")
        
    @pyqtSlot()
    def on_nonGroupButton_clicked(self):
        """
        Private slot to handle the non group toolbutton.
        """
        self.__insertString("(?:)", -1)
        
    @pyqtSlot()
    def on_groupButton_clicked(self):
        """
        Private slot to handle the group toolbutton.
        """
        self.__insertString("()", -1)
        
    @pyqtSlot()
    def on_altnButton_clicked(self):
        """
        Private slot to handle the alternatives toolbutton.
        """
        self.__insertString("(|)", -2)
        
    @pyqtSlot()
    def on_beglineButton_clicked(self):
        """
        Private slot to handle the begin line toolbutton.
        """
        self.__insertString("^")
        
    @pyqtSlot()
    def on_endlineButton_clicked(self):
        """
        Private slot to handle the end line toolbutton.
        """
        self.__insertString("$")
        
    @pyqtSlot()
    def on_wordboundButton_clicked(self):
        """
        Private slot to handle the word boundary toolbutton.
        """
        self.__insertString("\\b")
        
    @pyqtSlot()
    def on_nonwordboundButton_clicked(self):
        """
        Private slot to handle the non word boundary toolbutton.
        """
        self.__insertString("\\B")
        
    @pyqtSlot()
    def on_poslookaheadButton_clicked(self):
        """
        Private slot to handle the positive lookahead toolbutton.
        """
        self.__insertString("(?=)", -1)
        
    @pyqtSlot()
    def on_neglookaheadButton_clicked(self):
        """
        Private slot to handle the negative lookahead toolbutton.
        """
        self.__insertString("(?!)", -1)
        
    @pyqtSlot()
    def on_repeatButton_clicked(self):
        """
        Private slot to handle the repeat toolbutton.
        """
        from .QRegExpWizardRepeatDialog import QRegExpWizardRepeatDialog
        dlg = QRegExpWizardRepeatDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self.__insertString(dlg.getRepeat())
        
    @pyqtSlot()
    def on_charButton_clicked(self):
        """
        Private slot to handle the characters toolbutton.
        """
        from .QRegExpWizardCharactersDialog import \
            QRegExpWizardCharactersDialog
        dlg = QRegExpWizardCharactersDialog(
            mode=QRegExpWizardCharactersDialog.RegExpMode, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.__insertString(dlg.getCharacters())
    
    @pyqtSlot()
    def on_wildcardCharButton_clicked(self):
        """
        Private slot to handle the wildcard characters toolbutton.
        """
        from .QRegExpWizardCharactersDialog import \
            QRegExpWizardCharactersDialog
        dlg = QRegExpWizardCharactersDialog(
            mode=QRegExpWizardCharactersDialog.WildcardMode, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.__insertString(dlg.getCharacters())
    
    @pyqtSlot()
    def on_wildcardAnycharButton_clicked(self):
        """
        Private slot to handle the wildcard any character toolbutton.
        """
        self.__insertString("?")
    
    @pyqtSlot()
    def on_wildcardRepeatButton_clicked(self):
        """
        Private slot to handle the wildcard multiple characters toolbutton.
        """
        self.__insertString("*")
    
    @pyqtSlot()
    def on_w3cCharButton_clicked(self):
        """
        Private slot to handle the wildcard characters toolbutton.
        """
        from .QRegExpWizardCharactersDialog import \
            QRegExpWizardCharactersDialog
        dlg = QRegExpWizardCharactersDialog(
            mode=QRegExpWizardCharactersDialog.W3CMode, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.__insertString(dlg.getCharacters())
    
    @pyqtSlot()
    def on_w3cAnycharButton_clicked(self):
        """
        Private slot to handle the W3C any character toolbutton.
        """
        self.__insertString(".")
    
    @pyqtSlot()
    def on_w3cRepeatButton_clicked(self):
        """
        Private slot to handle the W3C repeat toolbutton.
        """
        from .QRegExpWizardRepeatDialog import QRegExpWizardRepeatDialog
        dlg = QRegExpWizardRepeatDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self.__insertString(dlg.getRepeat())
    
    @pyqtSlot()
    def on_w3cGroupButton_clicked(self):
        """
        Private slot to handle the W3C group toolbutton.
        """
        self.__insertString("()", -1)
    
    @pyqtSlot()
    def on_w3cAltnButton_clicked(self):
        """
        Private slot to handle the alternatives toolbutton.
        """
        self.__insertString("(|)", -2)
    
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.validateButton:
            self.on_validateButton_clicked()
        elif button == self.executeButton:
            self.on_executeButton_clicked()
        elif button == self.saveButton:
            self.on_saveButton_clicked()
        elif button == self.loadButton:
            self.on_loadButton_clicked()
        elif button == self.nextButton:
            self.on_nextButton_clicked()
        elif self.copyButton and button == self.copyButton:
            self.on_copyButton_clicked()
    
    @pyqtSlot()
    def on_saveButton_clicked(self):
        """
        Private slot to save the regexp to a file.
        """
        fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            self,
            self.tr("Save regular expression"),
            "",
            self.tr("RegExp Files (*.rx);;All Files (*)"),
            None,
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        if fname:
            ext = QFileInfo(fname).suffix()
            if not ext:
                ex = selectedFilter.split("(*")[1].split(")")[0]
                if ex:
                    fname += ex
            if QFileInfo(fname).exists():
                res = E5MessageBox.yesNo(
                    self,
                    self.tr("Save regular expression"),
                    self.tr("<p>The file <b>{0}</b> already exists."
                            " Overwrite it?</p>").format(fname),
                    icon=E5MessageBox.Warning)
                if not res:
                    return
            
            syntax = self.syntaxCombo.itemData(self.syntaxCombo.currentIndex())
            try:
                f = open(
                    Utilities.toNativeSeparators(fname), "w", encoding="utf-8")
                f.write("syntax={0}\n".format(syntax))
                f.write(self.regexpLineEdit.text())
                f.close()
            except IOError as err:
                E5MessageBox.information(
                    self,
                    self.tr("Save regular expression"),
                    self.tr("""<p>The regular expression could not"""
                            """ be saved.</p><p>Reason: {0}</p>""")
                    .format(str(err)))
    
    @pyqtSlot()
    def on_loadButton_clicked(self):
        """
        Private slot to load a regexp from a file.
        """
        fname = E5FileDialog.getOpenFileName(
            self,
            self.tr("Load regular expression"),
            "",
            self.tr("RegExp Files (*.rx);;All Files (*)"))
        if fname:
            try:
                f = open(
                    Utilities.toNativeSeparators(fname), "r", encoding="utf-8")
                regexp = f.read()
                f.close()
                if regexp.startswith("syntax="):
                    lines = regexp.splitlines()
                    syntax = int(lines[0].replace("syntax=", ""))
                    index = self.syntaxCombo.findData(syntax)
                    self.syntaxCombo.setCurrentIndex(index)
                    regexp = lines[1]
                self.regexpLineEdit.setText(regexp)
            except IOError as err:
                E5MessageBox.information(
                    self,
                    self.tr("Save regular expression"),
                    self.tr("""<p>The regular expression could not"""
                            """ be saved.</p><p>Reason: {0}</p>""")
                    .format(str(err)))

    @pyqtSlot()
    def on_copyButton_clicked(self):
        """
        Private slot to copy the regexp string into the clipboard.
        
        This slot is only available, if not called from within eric6.
        """
        escaped = self.regexpLineEdit.text()
        if escaped:
            escaped = escaped.replace("\\", "\\\\")
            cb = QApplication.clipboard()
            cb.setText(escaped, QClipboard.Clipboard)
            if cb.supportsSelection():
                cb.setText(escaped, QClipboard.Selection)

    @pyqtSlot()
    def on_validateButton_clicked(self):
        """
        Private slot to validate the entered regexp.
        """
        regex = self.regexpLineEdit.text()
        if regex:
            re = QRegExp(regex)
            if self.caseSensitiveCheckBox.isChecked():
                re.setCaseSensitivity(Qt.CaseSensitive)
            else:
                re.setCaseSensitivity(Qt.CaseInsensitive)
            re.setMinimal(self.minimalCheckBox.isChecked())
            re.setPatternSyntax(
                self.syntaxCombo.itemData(self.syntaxCombo.currentIndex()))
            if re.isValid():
                E5MessageBox.information(
                    self,
                    self.tr("Validation"),
                    self.tr("""The regular expression is valid."""))
            else:
                E5MessageBox.critical(
                    self,
                    self.tr("Error"),
                    self.tr("""Invalid regular expression: {0}""")
                    .format(re.errorString()))
                return
        else:
            E5MessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("""A regular expression must be given."""))

    @pyqtSlot()
    def on_executeButton_clicked(self, startpos=0):
        """
        Private slot to execute the entered regexp on the test text.
        
        This slot will execute the entered regexp on the entered test
        data and will display the result in the table part of the dialog.
        
        @param startpos starting position for the regexp matching
        """
        regex = self.regexpLineEdit.text()
        text = self.textTextEdit.toPlainText()
        if regex and text:
            re = QRegExp(regex)
            if self.caseSensitiveCheckBox.isChecked():
                re.setCaseSensitivity(Qt.CaseSensitive)
            else:
                re.setCaseSensitivity(Qt.CaseInsensitive)
            re.setMinimal(self.minimalCheckBox.isChecked())
            syntax = self.syntaxCombo.itemData(self.syntaxCombo.currentIndex())
            wildcard = syntax in [QRegExp.Wildcard, QRegExp.WildcardUnix]
            re.setPatternSyntax(syntax)
            if not re.isValid():
                E5MessageBox.critical(
                    self,
                    self.tr("Error"),
                    self.tr("""Invalid regular expression: {0}""")
                    .format(re.errorString()))
                return
            offset = re.indexIn(text, startpos)
            captures = re.captureCount()
            row = 0
            OFFSET = 5
            
            self.resultTable.setColumnCount(0)
            self.resultTable.setColumnCount(3)
            self.resultTable.setRowCount(0)
            self.resultTable.setRowCount(OFFSET)
            self.resultTable.setItem(
                row, 0, QTableWidgetItem(self.tr("Regexp")))
            self.resultTable.setItem(row, 1, QTableWidgetItem(regex))
            
            if offset != -1:
                self.lastMatchEnd = offset + re.matchedLength()
                self.nextButton.setEnabled(True)
                row += 1
                self.resultTable.setItem(
                    row, 0, QTableWidgetItem(self.tr("Offset")))
                self.resultTable.setItem(
                    row, 1, QTableWidgetItem("{0:d}".format(offset)))
                
                if not wildcard:
                    row += 1
                    self.resultTable.setItem(
                        row, 0, QTableWidgetItem(self.tr("Captures")))
                    self.resultTable.setItem(
                        row, 1, QTableWidgetItem("{0:d}".format(captures)))
                    row += 1
                    self.resultTable.setItem(
                        row, 1, QTableWidgetItem(self.tr("Text")))
                    self.resultTable.setItem(
                        row, 2, QTableWidgetItem(self.tr("Characters")))
                    
                row += 1
                self.resultTable.setItem(
                    row, 0, QTableWidgetItem(self.tr("Match")))
                self.resultTable.setItem(
                    row, 1, QTableWidgetItem(re.cap(0)))
                self.resultTable.setItem(
                    row, 2,
                    QTableWidgetItem("{0:d}".format(re.matchedLength())))
                
                if not wildcard:
                    for i in range(1, captures + 1):
                        if len(re.cap(i)) > 0:
                            row += 1
                            self.resultTable.insertRow(row)
                            self.resultTable.setItem(
                                row, 0,
                                QTableWidgetItem(
                                    self.tr("Capture #{0}").format(i)))
                            self.resultTable.setItem(
                                row, 1,
                                QTableWidgetItem(re.cap(i)))
                            self.resultTable.setItem(
                                row, 2,
                                QTableWidgetItem(
                                    "{0:d}".format(len(re.cap(i)))))
                else:
                    self.resultTable.setRowCount(3)
                
                # highlight the matched text
                tc = self.textTextEdit.textCursor()
                tc.setPosition(offset)
                tc.setPosition(self.lastMatchEnd, QTextCursor.KeepAnchor)
                self.textTextEdit.setTextCursor(tc)
            else:
                self.nextButton.setEnabled(False)
                self.resultTable.setRowCount(2)
                row += 1
                if startpos > 0:
                    self.resultTable.setItem(
                        row, 0,
                        QTableWidgetItem(self.tr("No more matches")))
                else:
                    self.resultTable.setItem(
                        row, 0,
                        QTableWidgetItem(self.tr("No matches")))
                
                # remove the highlight
                tc = self.textTextEdit.textCursor()
                tc.setPosition(0)
                self.textTextEdit.setTextCursor(tc)
            
            self.resultTable.resizeColumnsToContents()
            self.resultTable.resizeRowsToContents()
            self.resultTable.verticalHeader().hide()
            self.resultTable.horizontalHeader().hide()
        else:
            E5MessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("""A regular expression and a text must"""
                        """ be given."""))
        
    @pyqtSlot()
    def on_nextButton_clicked(self):
        """
        Private slot to find the next match.
        """
        self.on_executeButton_clicked(self.lastMatchEnd)
        
    def on_regexpLineEdit_textChanged(self, txt):
        """
        Private slot called when the regexp changes.
        
        @param txt the new text of the line edit (string)
        """
        self.nextButton.setEnabled(False)
        
    def __getPatternSyntaxCode(self, syntaxValue):
        """
        Private method to convert a pattern syntax value into a
        pattern syntax string.
        
        @param syntaxValue pattern syntax value (integer)
        @return pattern syntax string (string)
        """
        syntax = "QRegExp."
        if syntaxValue == QRegExp.RegExp:
            syntax += "RegExp"
        elif syntaxValue == QRegExp.RegExp2:
            syntax += "RegExp2"
        elif syntaxValue == QRegExp.Wildcard:
            syntax += "Wildcard"
        elif syntaxValue == QRegExp.WildcardUnix:
            syntax += "WildcardUnix"
        elif syntaxValue == QRegExp.FixedString:
            syntax += "FixedString"
        elif syntaxValue == QRegExp.W3CXmlSchema11:
            syntax += "W3CXmlSchema11"
        return syntax
        
    def getCode(self, indLevel, indString):
        """
        Public method to get the source code.
        
        @param indLevel indentation level (int)
        @param indString string used for indentation (space or tab) (string)
        @return generated code (string)
        """
        # calculate the indentation string
        istring = indLevel * indString
        estring = os.linesep + indLevel * indString
        
        # now generate the code
        reVar = self.variableLineEdit.text()
        if not reVar:
            reVar = "regexp"
            
        regexp = self.regexpLineEdit.text()
        
        code = '{0} = QRegExp(r"""{1}"""){2}'.format(
            reVar, regexp.replace('"', '\\"'), os.linesep)
        if not self.caseSensitiveCheckBox.isChecked():
            code += '{0}{1}.setCaseSensitivity(Qt.CaseInsensitive){2}'.format(
                    istring, reVar, os.linesep)
        if self.minimalCheckBox.isChecked():
            code += '{0}{1}.setMinimal(True){2}'.format(
                istring, reVar, os.linesep)
        syntax = self.syntaxCombo.itemData(self.syntaxCombo.currentIndex())
        needPatternSyntax = True
        if qVersion() < "5.0.0" and syntax == QRegExp.RegExp or \
           qVersion() >= "5.0.0" and syntax == QRegExp.RegExp2:
            # default value selected
            needPatternSyntax = False
        if needPatternSyntax:
            code += '{0}{1}.setPatternSyntax({2}){3}'.format(
                    istring, reVar, self.__getPatternSyntaxCode(syntax),
                    estring)
        return code


class QRegExpWizardDialog(QDialog):
    """
    Class for the dialog variant.
    """
    def __init__(self, parent=None, fromEric=True):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        @param fromEric flag indicating a call from within eric6
        """
        super(QRegExpWizardDialog, self).__init__(parent)
        self.setModal(fromEric)
        self.setSizeGripEnabled(True)
        
        self.__layout = QVBoxLayout(self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__layout)
        
        self.cw = QRegExpWizardWidget(self, fromEric)
        size = self.cw.size()
        self.__layout.addWidget(self.cw)
        self.resize(size)
        self.setWindowTitle(self.cw.windowTitle())
        
        self.cw.buttonBox.accepted.connect(self.accept)
        self.cw.buttonBox.rejected.connect(self.reject)
    
    def getCode(self, indLevel, indString):
        """
        Public method to get the source code.
        
        @param indLevel indentation level (int)
        @param indString string used for indentation (space or tab) (string)
        @return generated code (string)
        """
        return self.cw.getCode(indLevel, indString)


class QRegExpWizardWindow(E5MainWindow):
    """
    Main window class for the standalone dialog.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(QRegExpWizardWindow, self).__init__(parent)
        self.cw = QRegExpWizardWidget(self, fromEric=False)
        size = self.cw.size()
        self.setCentralWidget(self.cw)
        self.resize(size)
        self.setWindowTitle(self.cw.windowTitle())
        
        self.setStyle(
            Preferences.getUI("Style"), Preferences.getUI("StyleSheet"))
        
        self.cw.buttonBox.accepted.connect(self.close)
        self.cw.buttonBox.rejected.connect(self.close)
