# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the QRegularExpression wizard dialog.
"""

from __future__ import unicode_literals

import os
import re
import sys
import json

from PyQt5.QtCore import QFileInfo, pyqtSlot, QProcess, QByteArray
from PyQt5.QtGui import QClipboard, QTextCursor
from PyQt5.QtWidgets import QWidget, QDialog, QInputDialog, QApplication, \
    QDialogButtonBox, QVBoxLayout, QTableWidgetItem

from E5Gui import E5MessageBox, E5FileDialog
from E5Gui.E5MainWindow import E5MainWindow

from .Ui_QRegularExpressionWizardDialog import \
    Ui_QRegularExpressionWizardDialog

import UI.PixmapCache

import Utilities
import Preferences


class QRegularExpressionWizardWidget(QWidget,
                                     Ui_QRegularExpressionWizardDialog):
    """
    Class implementing the QRegularExpression wizard dialog.
    """
    def __init__(self, parent=None, fromEric=True):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        @param fromEric flag indicating a call from within eric6
        """
        super(QRegularExpressionWizardWidget, self).__init__(parent)
        self.setupUi(self)
        
        # initialize icons of the tool buttons
        self.commentButton.setIcon(UI.PixmapCache.getIcon("comment.png"))
        self.charButton.setIcon(UI.PixmapCache.getIcon("characters.png"))
        self.anycharButton.setIcon(UI.PixmapCache.getIcon("anychar.png"))
        self.repeatButton.setIcon(UI.PixmapCache.getIcon("repeat.png"))
        self.nonGroupButton.setIcon(UI.PixmapCache.getIcon("nongroup.png"))
        self.atomicGroupButton.setIcon(
            UI.PixmapCache.getIcon("atomicgroup.png"))
        self.groupButton.setIcon(UI.PixmapCache.getIcon("group.png"))
        self.namedGroupButton.setIcon(UI.PixmapCache.getIcon("namedgroup.png"))
        self.namedReferenceButton.setIcon(
            UI.PixmapCache.getIcon("namedreference.png"))
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
        self.poslookbehindButton.setIcon(
            UI.PixmapCache.getIcon("poslookbehind.png"))
        self.neglookbehindButton.setIcon(
            UI.PixmapCache.getIcon("neglookbehind.png"))
        self.undoButton.setIcon(UI.PixmapCache.getIcon("editUndo.png"))
        self.redoButton.setIcon(UI.PixmapCache.getIcon("editRedo.png"))
        
        self.namedGroups = re.compile(r"""\(?P<([^>]+)>""").findall
        
        # start the PyQt5 server part
        self.__pyqt5Available = False
        self.__pyqt5Server = QProcess(self)
        self.__pyqt5Server.start(
            sys.executable, [os.path.join(
                os.path.dirname(__file__), "QRegularExpressionWizardServer.py")
            ])
        if self.__pyqt5Server.waitForStarted(5000):
            self.__pyqt5Server.setReadChannel(QProcess.StandardOutput)
            if self.__sendCommand("available"):
                response = self.__receiveResponse()
                if response and response["available"]:
                    self.__pyqt5Available = True
        
        self.saveButton = self.buttonBox.addButton(
            self.tr("Save"), QDialogButtonBox.ActionRole)
        self.saveButton.setToolTip(
            self.tr("Save the regular expression to a file"))
        self.loadButton = self.buttonBox.addButton(
            self.tr("Load"), QDialogButtonBox.ActionRole)
        self.loadButton.setToolTip(
            self.tr("Load a regular expression from a file"))
        if self.__pyqt5Available:
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
        else:
            self.validateButton = None
            self.executeButton = None
            self.nextButton = None
        
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
            self.regexpTextEdit.setFocus()
    
    def __sendCommand(self, command, **kw):
        """
        Private method to send a command to the PyQt5 server.
        
        @param command dictionary with command string and related
            data (dict)
        @keyparam kw parameters for the command
        @return flag indicating a successful transmission (boolean)
        """
        result = False
        if command:
            commandDict = {"command": command}
            commandDict.update(kw)
            commandStr = json.dumps(commandDict) + "\n"
            data = QByteArray(commandStr.encode("utf-8"))
            self.__pyqt5Server.write(data)
            result = self.__pyqt5Server.waitForBytesWritten(10000)
        return result
    
    def __receiveResponse(self):
        """
        Private method to receive a response from the PyQt5 server.
        
        @return response dictionary (dict)
        """
        responseDict = {}
        if self.__pyqt5Server.waitForReadyRead(10000):
            data = bytes(self.__pyqt5Server.readAllStandardOutput())
            responseStr = data.decode("utf-8")
            responseDict = json.loads(responseStr)
            if responseDict["error"]:
                E5MessageBox.critical(
                    self,
                    self.tr("Communication Error"),
                    self.tr("""<p>The PyQt5 backend reported"""
                            """ an error.</p><p>{0}</p>""")
                    .format(responseDict["error"]))
                responseDict = {}
        
        return responseDict
    
    def shutdown(self):
        """
        Public method to shut down the PyQt5 server part.
        """
        self.__sendCommand("exit")
        self.__pyqt5Server.waitForFinished(5000)
    
    def __insertString(self, s, steps=0):
        """
        Private method to insert a string into line edit and move cursor.
        
        @param s string to be inserted into the regexp line edit
            (string)
        @param steps number of characters to move the cursor (integer).
            Negative steps moves cursor back, positives forward.
        """
        self.regexpTextEdit.insertPlainText(s)
        tc = self.regexpTextEdit.textCursor()
        if steps != 0:
            if steps < 0:
                act = QTextCursor.Left
                steps = abs(steps)
            else:
                act = QTextCursor.Right
            for i in range(steps):
                tc.movePosition(act)
        self.regexpTextEdit.setTextCursor(tc)
    
    @pyqtSlot()
    def on_commentButton_clicked(self):
        """
        Private slot to handle the comment toolbutton.
        """
        self.__insertString("(?#)", -1)
    
    @pyqtSlot()
    def on_charButton_clicked(self):
        """
        Private slot to handle the characters toolbutton.
        """
        from .QRegularExpressionWizardCharactersDialog import \
            QRegularExpressionWizardCharactersDialog
        dlg = QRegularExpressionWizardCharactersDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self.__insertString(dlg.getCharacters())
    
    @pyqtSlot()
    def on_anycharButton_clicked(self):
        """
        Private slot to handle the any character toolbutton.
        """
        self.__insertString(".")
    
    @pyqtSlot()
    def on_repeatButton_clicked(self):
        """
        Private slot to handle the repeat toolbutton.
        """
        from .QRegularExpressionWizardRepeatDialog import \
            QRegularExpressionWizardRepeatDialog
        dlg = QRegularExpressionWizardRepeatDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self.__insertString(dlg.getRepeat())
    
    @pyqtSlot()
    def on_nonGroupButton_clicked(self):
        """
        Private slot to handle the non group toolbutton.
        """
        self.__insertString("(?:)", -1)
    
    @pyqtSlot()
    def on_atomicGroupButton_clicked(self):
        """
        Private slot to handle the atomic non group toolbutton.
        """
        self.__insertString("(?>)", -1)
    
    @pyqtSlot()
    def on_groupButton_clicked(self):
        """
        Private slot to handle the group toolbutton.
        """
        self.__insertString("()", -1)
    
    @pyqtSlot()
    def on_namedGroupButton_clicked(self):
        """
        Private slot to handle the named group toolbutton.
        """
        self.__insertString("(?P<>)", -2)
    
    @pyqtSlot()
    def on_namedReferenceButton_clicked(self):
        """
        Private slot to handle the named reference toolbutton.
        """
        # determine cursor position as length into text
        length = self.regexpTextEdit.textCursor().position()
        
        # only present group names that occur before the current
        # cursor position
        regex = self.regexpTextEdit.toPlainText()[:length]
        names = self.namedGroups(regex)
        if not names:
            E5MessageBox.information(
                self,
                self.tr("Named reference"),
                self.tr("""No named groups have been defined yet."""))
            return
        
        groupName, ok = QInputDialog.getItem(
            self,
            self.tr("Named reference"),
            self.tr("Select group name:"),
            names,
            0, True)
        if ok and groupName:
            self.__insertString("(?P={0})".format(groupName))
    
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
    def on_poslookbehindButton_clicked(self):
        """
        Private slot to handle the positive lookbehind toolbutton.
        """
        self.__insertString("(?<=)", -1)
    
    @pyqtSlot()
    def on_neglookbehindButton_clicked(self):
        """
        Private slot to handle the negative lookbehind toolbutton.
        """
        self.__insertString("(?<!)", -1)
    
    @pyqtSlot()
    def on_undoButton_clicked(self):
        """
        Private slot to handle the undo action.
        """
        self.regexpTextEdit.document().undo()
    
    @pyqtSlot()
    def on_redoButton_clicked(self):
        """
        Private slot to handle the redo action.
        """
        self.regexpTextEdit.document().redo()
    
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
        Private slot to save the QRegularExpression to a file.
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
            
            try:
                f = open(
                    Utilities.toNativeSeparators(fname), "w", encoding="utf-8")
                f.write(self.regexpTextEdit.toPlainText())
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
        Private slot to load a QRegularExpression from a file.
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
                self.regexpTextEdit.setPlainText(regexp)
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
        Private slot to copy the QRegularExpression string into the clipboard.
        
        This slot is only available, if not called from within eric6.
        """
        escaped = self.regexpTextEdit.toPlainText()
        if escaped:
            escaped = escaped.replace("\\", "\\\\")
            cb = QApplication.clipboard()
            cb.setText(escaped, QClipboard.Clipboard)
            if cb.supportsSelection():
                cb.setText(escaped, QClipboard.Selection)

    @pyqtSlot()
    def on_validateButton_clicked(self):
        """
        Private slot to validate the entered QRegularExpression.
        """
        if not self.__pyqt5Available:
            # only available for PyQt5
            return
        
        regexp = self.regexpTextEdit.toPlainText()
        if regexp:
            options = []
            if self.caseInsensitiveCheckBox.isChecked():
                options.append("CaseInsensitiveOption")
            if self.multilineCheckBox.isChecked():
                options.append("MultilineOption")
            if self.dotallCheckBox.isChecked():
                options.append("DotMatchesEverythingOption")
            if self.extendedCheckBox.isChecked():
                options.append("ExtendedPatternSyntaxOption")
            if self.greedinessCheckBox.isChecked():
                options.append("InvertedGreedinessOption")
            if self.unicodeCheckBox.isChecked():
                options.append("UseUnicodePropertiesOption")
            if self.captureCheckBox.isChecked():
                options.append("DontCaptureOption")
            
            if self.__sendCommand("validate", options=options, regexp=regexp):
                response = self.__receiveResponse()
                if response and "valid" in response:
                    if response["valid"]:
                        E5MessageBox.information(
                            self,
                            self.tr("Validation"),
                            self.tr(
                                """The regular expression is valid."""))
                    else:
                        E5MessageBox.critical(
                            self,
                            self.tr("Error"),
                            self.tr("""Invalid regular expression: {0}""")
                            .format(response["errorMessage"]))
                        # move cursor to error offset
                        offset = response["errorOffset"]
                        tc = self.regexpTextEdit.textCursor()
                        tc.setPosition(offset)
                        self.regexpTextEdit.setTextCursor(tc)
                        self.regexpTextEdit.setFocus()
                        return
                else:
                    E5MessageBox.critical(
                        self,
                        self.tr("Communication Error"),
                        self.tr("""Invalid response received from"""
                                """ PyQt5 backend."""))
            else:
                E5MessageBox.critical(
                    self,
                    self.tr("Communication Error"),
                    self.tr("""Communication with PyQt5 backend"""
                            """ failed."""))
        else:
            E5MessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("""A regular expression must be given."""))

    @pyqtSlot()
    def on_executeButton_clicked(self, startpos=0):
        """
        Private slot to execute the entered QRegularExpression on the test
        text.
        
        This slot will execute the entered QRegularExpression on the entered
        test data and will display the result in the table part of the dialog.
        
        @param startpos starting position for the QRegularExpression matching
        """
        if not self.__pyqt5Available:
            # only available for PyQt5
            return
        
        regexp = self.regexpTextEdit.toPlainText()
        text = self.textTextEdit.toPlainText()
        if regexp and text:
            options = []
            if self.caseInsensitiveCheckBox.isChecked():
                options.append("CaseInsensitiveOption")
            if self.multilineCheckBox.isChecked():
                options.append("MultilineOption")
            if self.dotallCheckBox.isChecked():
                options.append("DotMatchesEverythingOption")
            if self.extendedCheckBox.isChecked():
                options.append("ExtendedPatternSyntaxOption")
            if self.greedinessCheckBox.isChecked():
                options.append("InvertedGreedinessOption")
            if self.unicodeCheckBox.isChecked():
                options.append("UseUnicodePropertiesOption")
            if self.captureCheckBox.isChecked():
                options.append("DontCaptureOption")
            
            if self.__sendCommand("execute", options=options, regexp=regexp,
                                  text=text, startpos=startpos):
                response = self.__receiveResponse()
                if response and ("valid" in response or "matched" in response):
                    if "valid" in response:
                        E5MessageBox.critical(
                            self,
                            self.tr("Error"),
                            self.tr("""Invalid regular expression: {0}""")
                            .format(response["errorMessage"]))
                        # move cursor to error offset
                        offset = response["errorOffset"]
                        tc = self.regexpTextEdit.textCursor()
                        tc.setPosition(offset)
                        self.regexpTextEdit.setTextCursor(tc)
                        self.regexpTextEdit.setFocus()
                        return
                    else:
                        row = 0
                        OFFSET = 5
                        
                        self.resultTable.setColumnCount(0)
                        self.resultTable.setColumnCount(3)
                        self.resultTable.setRowCount(0)
                        self.resultTable.setRowCount(OFFSET)
                        self.resultTable.setItem(
                            row, 0, QTableWidgetItem(self.tr("Regexp")))
                        self.resultTable.setItem(
                            row, 1, QTableWidgetItem(regexp))
                        if response["matched"]:
                            captures = response["captures"]
                            # index 0 is the complete match
                            offset = captures[0][1]
                            self.lastMatchEnd = captures[0][2]
                            self.nextButton.setEnabled(True)
                            row += 1
                            self.resultTable.setItem(
                                row, 0,
                                QTableWidgetItem(self.tr("Offset")))
                            self.resultTable.setItem(
                                row, 1,
                                QTableWidgetItem("{0:d}".format(offset)))
                            
                            row += 1
                            self.resultTable.setItem(
                                row, 0,
                                QTableWidgetItem(self.tr("Captures")))
                            self.resultTable.setItem(
                                row, 1,
                                QTableWidgetItem(
                                    "{0:d}".format(len(captures) - 1)))
                            row += 1
                            self.resultTable.setItem(
                                row, 1,
                                QTableWidgetItem(self.tr("Text")))
                            self.resultTable.setItem(
                                row, 2,
                                QTableWidgetItem(self.tr("Characters")))
                            
                            row += 1
                            self.resultTable.setItem(
                                row, 0,
                                QTableWidgetItem(self.tr("Match")))
                            self.resultTable.setItem(
                                row, 1,
                                QTableWidgetItem(captures[0][0]))
                            self.resultTable.setItem(
                                row, 2,
                                QTableWidgetItem(
                                    "{0:d}".format(captures[0][3])))
                            
                            for i in range(1, len(captures)):
                                if captures[i][0]:
                                    row += 1
                                    self.resultTable.insertRow(row)
                                    self.resultTable.setItem(
                                        row, 0,
                                        QTableWidgetItem(
                                            self.tr("Capture #{0}")
                                            .format(i)))
                                    self.resultTable.setItem(
                                        row, 1,
                                        QTableWidgetItem(captures[i][0]))
                                    self.resultTable.setItem(
                                        row, 2,
                                        QTableWidgetItem(
                                            "{0:d}".format(captures[i][3])))
                            
                            # highlight the matched text
                            tc = self.textTextEdit.textCursor()
                            tc.setPosition(offset)
                            tc.setPosition(
                                self.lastMatchEnd, QTextCursor.KeepAnchor)
                            self.textTextEdit.setTextCursor(tc)
                        else:
                            self.nextButton.setEnabled(False)
                            self.resultTable.setRowCount(2)
                            row += 1
                            if startpos > 0:
                                self.resultTable.setItem(
                                    row, 0,
                                    QTableWidgetItem(
                                        self.tr("No more matches")))
                            else:
                                self.resultTable.setItem(
                                    row, 0,
                                    QTableWidgetItem(
                                        self.tr("No matches")))
                            
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
                        self.tr("Communication Error"),
                        self.tr("""Invalid response received from"""
                                """ PyQt5 backend."""))
            else:
                E5MessageBox.critical(
                    self,
                    self.tr("Communication Error"),
                    self.tr("""Communication with PyQt5"""
                            """ backend failed."""))
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
    
    @pyqtSlot()
    def on_regexpTextEdit_textChanged(self):
        """
        Private slot called when the regexp changes.
        """
        if self.nextButton:
            self.nextButton.setEnabled(False)
    
    def getCode(self, indLevel, indString):
        """
        Public method to get the source code.
        
        @param indLevel indentation level (int)
        @param indString string used for indentation (space or tab) (string)
        @return generated code (string)
        """
        # calculate the indentation string
        i1string = (indLevel + 1) * indString
        estring = os.linesep + indLevel * indString
        
        # now generate the code
        reVar = self.variableLineEdit.text()
        if not reVar:
            reVar = "regexp"
        
        regexp = self.regexpTextEdit.toPlainText()
        
        options = []
        if self.caseInsensitiveCheckBox.isChecked():
            options.append("QRegularExpression.CaseInsensitiveOption")
        if self.multilineCheckBox.isChecked():
            options.append("QRegularExpression.MultilineOption")
        if self.dotallCheckBox.isChecked():
            options.append("QRegularExpression.DotMatchesEverythingOption")
        if self.extendedCheckBox.isChecked():
            options.append("QRegularExpression.ExtendedPatternSyntaxOption")
        if self.greedinessCheckBox.isChecked():
            options.append("QRegularExpression.InvertedGreedinessOption")
        if self.unicodeCheckBox.isChecked():
            options.append("QRegularExpression.UseUnicodePropertiesOption")
        if self.captureCheckBox.isChecked():
            options.append("QRegularExpression.DontCaptureOption")
        options = " |{0}{1}".format(os.linesep, i1string).join(options)
        
        code = '{0} = QRegularExpression('.format(reVar)
        if options:
            code += '{0}{1}r"""{2}""",'.format(
                os.linesep, i1string, regexp.replace('"', '\\"'))
            code += '{0}{1}{2}'.format(os.linesep, i1string, options)
        else:
            code += 'r"""{0}"""'.format(regexp.replace('"', '\\"'))
        code += '){0}'.format(estring)
        return code


class QRegularExpressionWizardDialog(QDialog):
    """
    Class for the dialog variant.
    """
    def __init__(self, parent=None, fromEric=True):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        @param fromEric flag indicating a call from within eric6
        """
        super(QRegularExpressionWizardDialog, self).__init__(parent)
        self.setModal(fromEric)
        self.setSizeGripEnabled(True)
        
        self.__layout = QVBoxLayout(self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__layout)
        
        self.cw = QRegularExpressionWizardWidget(self, fromEric)
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
    
    def accept(self):
        """
        Public slot to hide the dialog and set the result code to Accepted.
        """
        self.cw.shutdown()
        super(QRegularExpressionWizardDialog, self).accept()
    
    def reject(self):
        """
        Public slot to hide the dialog and set the result code to Rejected.
        """
        self.cw.shutdown()
        super(QRegularExpressionWizardDialog, self).reject()


class QRegularExpressionWizardWindow(E5MainWindow):
    """
    Main window class for the standalone dialog.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(QRegularExpressionWizardWindow, self).__init__(parent)
        self.cw = QRegularExpressionWizardWidget(self, fromEric=False)
        size = self.cw.size()
        self.setCentralWidget(self.cw)
        self.resize(size)
        self.setWindowTitle(self.cw.windowTitle())
        
        self.setStyle(
            Preferences.getUI("Style"), Preferences.getUI("StyleSheet"))
        
        self.cw.buttonBox.accepted.connect(self.close)
        self.cw.buttonBox.rejected.connect(self.close)
    
    def closeEvent(self, evt):
        """
        Protected method handling the close event.
        
        @param evt close event (QCloseEvent)
        """
        self.cw.shutdown()
        super(QRegularExpressionWizardWindow, self).closeEvent(evt)
