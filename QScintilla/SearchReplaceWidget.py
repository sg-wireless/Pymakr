# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the search and replace widget.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot, QEvent
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QToolButton, QScrollArea, \
    QSizePolicy, QFrame

from .Editor import Editor

from E5Gui.E5Action import E5Action
from E5Gui import E5MessageBox

import Preferences

import UI.PixmapCache


class SearchReplaceWidget(QWidget):
    """
    Class implementing the search and replace widget.
    
    @signal searchListChanged() emitted to indicate a change of the search list
    """
    searchListChanged = pyqtSignal()
    
    def __init__(self, replace, vm, parent=None, sliding=False):
        """
        Constructor
        
        @param replace flag indicating a replace widget is called
        @param vm reference to the viewmanager object
        @param parent parent widget of this widget (QWidget)
        @param sliding flag indicating the widget is embedded in the
            sliding widget (boolean)
        """
        super(SearchReplaceWidget, self).__init__(parent)
        
        self.viewmanager = vm
        self.replace = replace
        self.__sliding = sliding
        if sliding:
            self.__topWidget = parent
        
        self.findHistory = vm.getSRHistory('search')
        if replace:
            from .Ui_ReplaceWidget import Ui_ReplaceWidget
            self.replaceHistory = vm.getSRHistory('replace')
            self.ui = Ui_ReplaceWidget()
            whatsThis = self.tr(
r"""<b>Find and Replace</b>
<p>This dialog is used to find some text and replace it with another text.
By checking the various checkboxes, the search can be made more specific.
The search string might be a regular expression. In a regular expression,
special characters interpreted are:</p>
"""
            )
        else:
            from .Ui_SearchWidget import Ui_SearchWidget
            self.ui = Ui_SearchWidget()
            whatsThis = self.tr(
r"""<b>Find</b>
<p>This dialog is used to find some text. By checking the various checkboxes,
the search can be made more specific. The search string might be a regular
expression. In a regular expression, special characters interpreted are:</p>
"""
            )
        self.ui.setupUi(self)
        if not replace:
            self.ui.wrapCheckBox.setChecked(True)
        
        whatsThis += self.tr(
r"""<table border="0">
<tr><td><code>.</code></td><td>Matches any character</td></tr>
<tr><td><code>\(</code></td><td>This marks the start of a region for tagging a
match.</td></tr>
<tr><td><code>\)</code></td><td>This marks the end of a tagged region.
</td></tr>
<tr><td><code>\\n</code></td>
<td>Where <code>n</code> is 1 through 9 refers to the first through ninth
tagged region when replacing. For example, if the search string was
<code>Fred\([1-9]\)XXX</code> and the replace string was <code>Sam\1YYY</code>,
when applied to <code>Fred2XXX</code> this would generate <code>Sam2YYY</code>.
</td></tr>
<tr><td><code>\&lt;</code></td>
<td>This matches the start of a word using Scintilla's definitions of words.
</td></tr>
<tr><td><code>\&gt;</code></td>
<td>This matches the end of a word using Scintilla's definition of words.
</td></tr>
<tr><td><code>\\x</code></td>
<td>This allows you to use a character x that would otherwise have a special
meaning. For example, \\[ would be interpreted as [ and not as the start of a
character set.</td></tr>
<tr><td><code>[...]</code></td>
<td>This indicates a set of characters, for example, [abc] means any of the
characters a, b or c. You can also use ranges, for example [a-z] for any lower
case character.</td></tr>
<tr><td><code>[^...]</code></td>
<td>The complement of the characters in the set. For example, [^A-Za-z] means
any character except an alphabetic character.</td></tr>
<tr><td><code>^</code></td>
<td>This matches the start of a line (unless used inside a set, see above).
</td></tr>
<tr><td><code>$</code></td> <td>This matches the end of a line.</td></tr>
<tr><td><code>*</code></td>
<td>This matches 0 or more times. For example, <code>Sa*m</code> matches
<code>Sm</code>, <code>Sam</code>, <code>Saam</code>, <code>Saaam</code>
and so on.</td></tr>
<tr><td><code>+</code></td>
<td>This matches 1 or more times. For example, <code>Sa+m</code> matches
<code>Sam</code>, <code>Saam</code>, <code>Saaam</code> and so on.</td></tr>
</table>
"""
        )
        self.setWhatsThis(whatsThis)
        
        self.ui.closeButton.setIcon(UI.PixmapCache.getIcon("close.png"))
        self.ui.findPrevButton.setIcon(
            UI.PixmapCache.getIcon("1leftarrow.png"))
        self.ui.findNextButton.setIcon(
            UI.PixmapCache.getIcon("1rightarrow.png"))
        
        if replace:
            self.ui.replaceButton.setIcon(
                UI.PixmapCache.getIcon("editReplace.png"))
            self.ui.replaceSearchButton.setIcon(
                UI.PixmapCache.getIcon("editReplaceSearch.png"))
            self.ui.replaceAllButton.setIcon(
                UI.PixmapCache.getIcon("editReplaceAll.png"))
        
        self.ui.findtextCombo.setCompleter(None)
        self.ui.findtextCombo.lineEdit().returnPressed.connect(
            self.__findByReturnPressed)
        if replace:
            self.ui.replacetextCombo.setCompleter(None)
            self.ui.replacetextCombo.lineEdit().returnPressed.connect(
                self.on_replaceButton_clicked)
        
        self.findNextAct = E5Action(
            self.tr('Find Next'),
            self.tr('Find Next'),
            0, 0, self, 'search_widget_find_next')
        self.findNextAct.triggered.connect(self.on_findNextButton_clicked)
        self.findNextAct.setEnabled(False)
        self.ui.findtextCombo.addAction(self.findNextAct)
        
        self.findPrevAct = E5Action(
            self.tr('Find Prev'),
            self.tr('Find Prev'),
            0, 0, self, 'search_widget_find_prev')
        self.findPrevAct.triggered.connect(self.on_findPrevButton_clicked)
        self.findPrevAct.setEnabled(False)
        self.ui.findtextCombo.addAction(self.findPrevAct)
        
        self.adjustSize()
        
        self.havefound = False
        self.__pos = None
        self.__findBackwards = False
        self.__selections = []
        self.__finding = False
    
    def changeEvent(self, evt):
        """
        Protected method handling state changes.
        
        @param evt event containing the state change (QEvent)
        """
        if evt.type() == QEvent.FontChange:
            self.adjustSize()
    
    def __selectionBoundary(self, selections=None):
        """
        Private method to calculate the current selection boundary.
        
        @param selections optional parameter giving the selections to
            calculate the boundary for (list of tuples of four integer)
        @return tuple of start line and index and end line and index
            (tuple of four integer)
        """
        if selections is None:
            selections = self.__selections
        if selections:
            lineNumbers = [sel[0] for sel in selections] + \
                          [sel[2] for sel in selections]
            indexNumbers = [sel[1] for sel in selections] + \
                           [sel[3] for sel in selections]
            startLine, startIndex, endLine, endIndex = (
                min(lineNumbers), min(indexNumbers),
                max(lineNumbers), max(indexNumbers))
        else:
            startLine, startIndex, endLine, endIndex = -1, -1, -1, -1
        
        return startLine, startIndex, endLine, endIndex
    
    def on_findtextCombo_editTextChanged(self, txt):
        """
        Private slot to enable/disable the find buttons.
        
        @param txt text of the find text combo (string)
        """
        if not txt:
            self.ui.findNextButton.setEnabled(False)
            self.findNextAct.setEnabled(False)
            self.ui.findPrevButton.setEnabled(False)
            self.findPrevAct.setEnabled(False)
            if self.replace:
                self.ui.replaceButton.setEnabled(False)
                self.ui.replaceSearchButton.setEnabled(False)
                self.ui.replaceAllButton.setEnabled(False)
        else:
            self.ui.findNextButton.setEnabled(True)
            self.findNextAct.setEnabled(True)
            self.ui.findPrevButton.setEnabled(True)
            self.findPrevAct.setEnabled(True)
            if self.replace:
                self.ui.replaceButton.setEnabled(False)
                self.ui.replaceSearchButton.setEnabled(False)
                self.ui.replaceAllButton.setEnabled(True)

    @pyqtSlot()
    def on_findNextButton_clicked(self):
        """
        Private slot to find the next occurrence of text.
        """
        self.findNext()
    
    def findNext(self):
        """
        Public slot to find the next occurrence of text.
        """
        if not self.havefound or not self.ui.findtextCombo.currentText():
            self.show(self.viewmanager.textForFind())
            return
        
        self.__findBackwards = False
        txt = self.ui.findtextCombo.currentText()
        
        # This moves any previous occurrence of this statement to the head
        # of the list and updates the combobox
        if txt in self.findHistory:
            self.findHistory.remove(txt)
        self.findHistory.insert(0, txt)
        self.ui.findtextCombo.clear()
        self.ui.findtextCombo.addItems(self.findHistory)
        self.searchListChanged.emit()
        
        ok = self.__findNextPrev(txt, False)
        if ok:
            if self.replace:
                self.ui.replaceButton.setEnabled(True)
                self.ui.replaceSearchButton.setEnabled(True)
        else:
            E5MessageBox.information(
                self, self.windowTitle(),
                self.tr("'{0}' was not found.").format(txt))

    @pyqtSlot()
    def on_findPrevButton_clicked(self):
        """
        Private slot to find the previous occurrence of text.
        """
        self.findPrev()
    
    def findPrev(self):
        """
        Public slot to find the next previous of text.
        """
        if not self.havefound or not self.ui.findtextCombo.currentText():
            self.show(self.viewmanager.textForFind())
            return
        
        self.__findBackwards = True
        txt = self.ui.findtextCombo.currentText()
        
        # This moves any previous occurrence of this statement to the head
        # of the list and updates the combobox
        if txt in self.findHistory:
            self.findHistory.remove(txt)
        self.findHistory.insert(0, txt)
        self.ui.findtextCombo.clear()
        self.ui.findtextCombo.addItems(self.findHistory)
        self.searchListChanged.emit()
        
        ok = self.__findNextPrev(txt, True)
        if ok:
            if self.replace:
                self.ui.replaceButton.setEnabled(True)
                self.ui.replaceSearchButton.setEnabled(True)
        else:
            E5MessageBox.information(
                self, self.windowTitle(),
                self.tr("'{0}' was not found.").format(txt))
    
    def __findByReturnPressed(self):
        """
        Private slot to handle the returnPressed signal of the findtext
        combobox.
        """
        if self.__findBackwards:
            self.findPrev()
        else:
            self.findNext()
    
    def __markOccurrences(self, txt):
        """
        Private method to mark all occurrences of the search text.
        
        @param txt text to search for (string)
        """
        aw = self.viewmanager.activeWindow()
        lineFrom = 0
        indexFrom = 0
        lineTo = -1
        indexTo = -1
        if self.ui.selectionCheckBox.isChecked():
            lineFrom, indexFrom, lineTo, indexTo = self.__selectionBoundary()
        
        aw.clearSearchIndicators()
        ok = aw.findFirstTarget(
            txt,
            self.ui.regexpCheckBox.isChecked(),
            self.ui.caseCheckBox.isChecked(),
            self.ui.wordCheckBox.isChecked(),
            lineFrom, indexFrom, lineTo, indexTo)
        while ok:
            tgtPos, tgtLen = aw.getFoundTarget()
            if tgtLen == 0:
                break
            if len(self.__selections) > 1:
                lineFrom, indexFrom = aw.lineIndexFromPosition(tgtPos)
                lineTo, indexTo = aw.lineIndexFromPosition(tgtPos + tgtLen)
                for sel in self.__selections:
                    if lineFrom == sel[0] and \
                       indexFrom >= sel[1] and \
                       indexTo <= sel[3]:
                        indicate = True
                        break
                else:
                    indicate = False
            else:
                indicate = True
            if indicate:
                aw.setSearchIndicator(tgtPos, tgtLen)
            ok = aw.findNextTarget()
        aw.updateMarkerMap()
    
    def __findNextPrev(self, txt, backwards):
        """
        Private method to find the next occurrence of the search text.
        
        @param txt text to search for (string)
        @param backwards flag indicating a backwards search (boolean)
        @return flag indicating success (boolean)
        """
        self.__finding = True
        
        if Preferences.getEditor("SearchMarkersEnabled"):
            self.__markOccurrences(txt)
        
        aw = self.viewmanager.activeWindow()
        aw.hideFindIndicator()
        cline, cindex = aw.getCursorPosition()
        
        ok = True
        lineFrom, indexFrom, lineTo, indexTo = aw.getSelection()
        boundary = self.__selectionBoundary()
        if backwards:
            if self.ui.selectionCheckBox.isChecked() and \
               (lineFrom, indexFrom, lineTo, indexTo) == boundary:
                # initial call
                line, index = boundary[2:]
            else:
                if (lineFrom, indexFrom) == (-1, -1):
                    # no selection present
                    line = cline
                    index = cindex
                else:
                    line = lineFrom
                    index = indexFrom
            if self.ui.selectionCheckBox.isChecked() and \
               line == boundary[0] and \
               index >= 0 and \
               index < boundary[1]:
                ok = False
            
            if ok and index < 0:
                line -= 1
                if self.ui.selectionCheckBox.isChecked():
                    if line < boundary[0]:
                        if self.ui.wrapCheckBox.isChecked():
                            line, index = boundary[2:]
                        else:
                            ok = False
                    else:
                        index = aw.lineLength(line)
                else:
                    if line < 0:
                        if self.ui.wrapCheckBox.isChecked():
                            line = aw.lines() - 1
                            index = aw.lineLength(line)
                        else:
                            ok = False
                    else:
                        index = aw.lineLength(line)
        else:
            if self.ui.selectionCheckBox.isChecked() and \
               (lineFrom, indexFrom, lineTo, indexTo) == boundary:
                # initial call
                line, index = boundary[:2]
            else:
                line = lineTo
                index = indexTo
        
        if ok:
            ok = aw.findFirst(
                txt,
                self.ui.regexpCheckBox.isChecked(),
                self.ui.caseCheckBox.isChecked(),
                self.ui.wordCheckBox.isChecked(),
                self.ui.wrapCheckBox.isChecked(),
                not backwards,
                line, index)
        
        if ok and self.ui.selectionCheckBox.isChecked():
            lineFrom, indexFrom, lineTo, indexTo = aw.getSelection()
            if len(self.__selections) > 1:
                for sel in self.__selections:
                    if lineFrom == sel[0] and \
                       indexFrom >= sel[1] and \
                       indexTo <= sel[3]:
                        ok = True
                        break
                else:
                    ok = False
            elif (lineFrom == boundary[0] and indexFrom >= boundary[1]) or \
                (lineFrom > boundary[0] and lineFrom < boundary[2]) or \
                    (lineFrom == boundary[2] and indexFrom <= boundary[3]):
                ok = True
            else:
                ok = False
            if not ok and len(self.__selections) > 1:
                # try again
                while not ok and \
                    ((backwards and lineFrom >= boundary[0]) or
                     (not backwards and lineFrom <= boundary[2])):
                    for ind in range(len(self.__selections)):
                        if lineFrom == self.__selections[ind][0]:
                            after = indexTo > self.__selections[ind][3]
                            if backwards:
                                if after:
                                    line, index = self.__selections[ind][2:]
                                else:
                                    if ind > 0:
                                        line, index = \
                                            self.__selections[ind - 1][2:]
                            else:
                                if after:
                                    if ind < len(self.__selections) - 1:
                                        line, index = \
                                            self.__selections[ind + 1][:2]
                                else:
                                    line, index = self.__selections[ind][:2]
                            break
                    else:
                        break
                    ok = aw.findFirst(
                        txt,
                        self.ui.regexpCheckBox.isChecked(),
                        self.ui.caseCheckBox.isChecked(),
                        self.ui.wordCheckBox.isChecked(),
                        self.ui.wrapCheckBox.isChecked(),
                        not backwards,
                        line, index)
                    if ok:
                        lineFrom, indexFrom, lineTo, indexTo = \
                            aw.getSelection()
                        if lineFrom < boundary[0] or \
                                lineFrom > boundary[2] or \
                                indexFrom < boundary[1] or \
                                indexFrom > boundary[3] or \
                                indexTo < boundary[1] or \
                                indexTo > boundary[3]:
                            ok = False
                            break
            if not ok:
                if self.ui.wrapCheckBox.isChecked():
                    # try it again
                    if backwards:
                        line, index = boundary[2:]
                    else:
                        line, index = boundary[:2]
                    ok = aw.findFirst(
                        txt,
                        self.ui.regexpCheckBox.isChecked(),
                        self.ui.caseCheckBox.isChecked(),
                        self.ui.wordCheckBox.isChecked(),
                        self.ui.wrapCheckBox.isChecked(),
                        not backwards,
                        line, index)
                    if ok:
                        lineFrom, indexFrom, lineTo, indexTo = \
                            aw.getSelection()
                        if len(self.__selections) > 1:
                            for sel in self.__selections:
                                if lineFrom == sel[0] and \
                                   indexFrom >= sel[1] and \
                                   indexTo <= sel[3]:
                                    ok = True
                                    break
                            else:
                                ok = False
                        elif (lineFrom == boundary[0] and
                              indexFrom >= boundary[1]) or \
                                (lineFrom > boundary[0] and
                                 lineFrom < boundary[2]) or \
                                (lineFrom == boundary[2]
                                 and indexFrom <= boundary[3]):
                            ok = True
                        else:
                            ok = False
                else:
                    ok = False
            
            if not ok:
                aw.selectAll(False)
                aw.setCursorPosition(cline, cindex)
                aw.ensureCursorVisible()
        
        if ok:
            sline, sindex, eline, eindex = aw.getSelection()
            aw.showFindIndicator(sline, sindex, eline, eindex)
        
        self.__finding = False
        
        return ok

    def __showFind(self, text=''):
        """
        Private method to display this widget in find mode.
        
        @param text text to be shown in the findtext edit (string)
        """
        self.replace = False
        
        self.ui.findtextCombo.clear()
        self.ui.findtextCombo.addItems(self.findHistory)
        self.ui.findtextCombo.setEditText(text)
        self.ui.findtextCombo.lineEdit().selectAll()
        self.ui.findtextCombo.setFocus()
        self.on_findtextCombo_editTextChanged(text)
        
        self.ui.caseCheckBox.setChecked(False)
        self.ui.wordCheckBox.setChecked(False)
        self.ui.wrapCheckBox.setChecked(True)
        self.ui.regexpCheckBox.setChecked(False)
        
        aw = self.viewmanager.activeWindow()
        self.updateSelectionCheckBox(aw)
        
        self.findNextAct.setShortcut(self.viewmanager.searchNextAct.shortcut())
        self.findNextAct.setAlternateShortcut(
            self.viewmanager.searchNextAct.alternateShortcut())
        self.findNextAct.setShortcutContext(Qt.WidgetShortcut)
        self.findPrevAct.setShortcut(self.viewmanager.searchPrevAct.shortcut())
        self.findPrevAct.setAlternateShortcut(
            self.viewmanager.searchPrevAct.alternateShortcut())
        self.findPrevAct.setShortcutContext(Qt.WidgetShortcut)
        
        self.havefound = True
        self.__findBackwards = False
    
    def selectionChanged(self):
        """
        Public slot tracking changes of selected text.
        """
        aw = self.sender()
        self.updateSelectionCheckBox(aw)
    
    @pyqtSlot(Editor)
    def updateSelectionCheckBox(self, editor):
        """
        Public slot to update the selection check box.
        
        @param editor reference to the editor (Editor)
        """
        if not self.__finding and isinstance(editor, Editor):
            if editor.hasSelectedText():
                selections = editor.getSelections()
                line1, index1, line2, index2 = \
                    self.__selectionBoundary(selections)
                if line1 != line2:
                    self.ui.selectionCheckBox.setEnabled(True)
                    self.ui.selectionCheckBox.setChecked(True)
                    self.__selections = selections
                    return
            
            self.ui.selectionCheckBox.setEnabled(False)
            self.ui.selectionCheckBox.setChecked(False)
            self.__selections = []

    @pyqtSlot()
    def on_replaceButton_clicked(self):
        """
        Private slot to replace one occurrence of text.
        """
        self.__doReplace(False)
    
    @pyqtSlot()
    def on_replaceSearchButton_clicked(self):
        """
        Private slot to replace one occurrence of text and search for the next
        one.
        """
        self.__doReplace(True)
    
    def __doReplace(self, searchNext):
        """
        Private method to replace one occurrence of text.
        
        @param searchNext flag indicating to search for the next occurrence
        (boolean).
        """
        self.__finding = True
        
        # Check enabled status due to dual purpose usage of this method
        if not self.ui.replaceButton.isEnabled() and \
           not self.ui.replaceSearchButton.isEnabled():
            return
        
        ftxt = self.ui.findtextCombo.currentText()
        rtxt = self.ui.replacetextCombo.currentText()
        
        # This moves any previous occurrence of this statement to the head
        # of the list and updates the combobox
        if rtxt in self.replaceHistory:
            self.replaceHistory.remove(rtxt)
        self.replaceHistory.insert(0, rtxt)
        self.ui.replacetextCombo.clear()
        self.ui.replacetextCombo.addItems(self.replaceHistory)
        
        aw = self.viewmanager.activeWindow()
        aw.hideFindIndicator()
        aw.replace(rtxt)
        
        if searchNext:
            ok = self.__findNextPrev(ftxt, self.__findBackwards)
            
            if not ok:
                self.ui.replaceButton.setEnabled(False)
                self.ui.replaceSearchButton.setEnabled(False)
                E5MessageBox.information(
                    self, self.windowTitle(),
                    self.tr("'{0}' was not found.").format(ftxt))
        else:
            self.ui.replaceButton.setEnabled(False)
            self.ui.replaceSearchButton.setEnabled(False)
        
        self.__finding = False
    
    @pyqtSlot()
    def on_replaceAllButton_clicked(self):
        """
        Private slot to replace all occurrences of text.
        """
        self.__finding = True
        
        replacements = 0
        ftxt = self.ui.findtextCombo.currentText()
        rtxt = self.ui.replacetextCombo.currentText()
        
        # This moves any previous occurrence of this statement to the head
        # of the list and updates the combobox
        if ftxt in self.findHistory:
            self.findHistory.remove(ftxt)
        self.findHistory.insert(0, ftxt)
        self.ui.findtextCombo.clear()
        self.ui.findtextCombo.addItems(self.findHistory)
        
        if rtxt in self.replaceHistory:
            self.replaceHistory.remove(rtxt)
        self.replaceHistory.insert(0, rtxt)
        self.ui.replacetextCombo.clear()
        self.ui.replacetextCombo.addItems(self.replaceHistory)
        
        aw = self.viewmanager.activeWindow()
        aw.hideFindIndicator()
        cline, cindex = aw.getCursorPosition()
        boundary = self.__selectionBoundary()
        if self.ui.selectionCheckBox.isChecked():
            line, index = boundary[:2]
        else:
            line = 0
            index = 0
        ok = aw.findFirst(
            ftxt,
            self.ui.regexpCheckBox.isChecked(),
            self.ui.caseCheckBox.isChecked(),
            self.ui.wordCheckBox.isChecked(),
            False, True, line, index)
        
        if ok and self.ui.selectionCheckBox.isChecked():
            lineFrom, indexFrom, lineTo, indexTo = aw.getSelection()
            if len(self.__selections) > 1:
                for sel in self.__selections:
                    if lineFrom == sel[0] and \
                       indexFrom >= sel[1] and \
                       indexTo <= sel[3]:
                        ok = True
                        break
                else:
                    ok = False
            elif (lineFrom == boundary[0] and indexFrom >= boundary[1]) or \
                (lineFrom > boundary[0] and lineFrom < boundary[2]) or \
                    (lineFrom == boundary[2] and indexFrom <= boundary[3]):
                ok = True
            else:
                ok = False
            if not ok and len(self.__selections) > 1:
                # try again
                while not ok and lineFrom <= boundary[2]:
                    for ind in range(len(self.__selections)):
                        if lineFrom == self.__selections[ind][0]:
                            after = indexTo > self.__selections[ind][3]
                            if after:
                                if ind < len(self.__selections) - 1:
                                    line, index = \
                                        self.__selections[ind + 1][:2]
                            else:
                                line, index = self.__selections[ind][:2]
                        break
                    else:
                        break
                    ok = aw.findFirst(
                        ftxt,
                        self.ui.regexpCheckBox.isChecked(),
                        self.ui.caseCheckBox.isChecked(),
                        self.ui.wordCheckBox.isChecked(),
                        False, True, line, index)
                    if ok:
                        lineFrom, indexFrom, lineTo, indexTo = \
                            aw.getSelection()
                        if lineFrom < boundary[0] or \
                                lineFrom > boundary[2] or \
                                indexFrom < boundary[1] or \
                                indexFrom > boundary[3] or \
                                indexTo < boundary[1] or \
                                indexTo > boundary[3]:
                            ok = False
                            break
            
            if not ok:
                aw.selectAll(False)
                aw.setCursorPosition(cline, cindex)
                aw.ensureCursorVisible()
        
        found = ok
        
        aw.beginUndoAction()
        wordWrap = self.ui.wrapCheckBox.isChecked()
        self.ui.wrapCheckBox.setChecked(False)
        while ok:
            aw.replace(rtxt)
            replacements += 1
            ok = self.__findNextPrev(ftxt, self.__findBackwards)
            self.__finding = True
        aw.endUndoAction()
        if wordWrap:
            self.ui.wrapCheckBox.setChecked(True)
        self.ui.replaceButton.setEnabled(False)
        self.ui.replaceSearchButton.setEnabled(False)
        
        if found:
            E5MessageBox.information(
                self, self.windowTitle(),
                self.tr("Replaced {0} occurrences.")
                .format(replacements))
        else:
            E5MessageBox.information(
                self, self.windowTitle(),
                self.tr("Nothing replaced because '{0}' was not found.")
                .format(ftxt))
        
        aw.setCursorPosition(cline, cindex)
        aw.ensureCursorVisible()
        
        self.__finding = False
        
    def __showReplace(self, text=''):
        """
        Private slot to display this widget in replace mode.
        
        @param text text to be shown in the findtext edit
        """
        self.replace = True
        
        self.ui.findtextCombo.clear()
        self.ui.findtextCombo.addItems(self.findHistory)
        self.ui.findtextCombo.setEditText(text)
        self.ui.findtextCombo.lineEdit().selectAll()
        self.ui.findtextCombo.setFocus()
        self.on_findtextCombo_editTextChanged(text)
        
        self.ui.replacetextCombo.clear()
        self.ui.replacetextCombo.addItems(self.replaceHistory)
        self.ui.replacetextCombo.setEditText('')
        
        self.ui.caseCheckBox.setChecked(False)
        self.ui.wordCheckBox.setChecked(False)
        self.ui.regexpCheckBox.setChecked(False)
        
        self.havefound = True
        
        aw = self.viewmanager.activeWindow()
        self.updateSelectionCheckBox(aw)
        if aw.hasSelectedText():
            line1, index1, line2, index2 = aw.getSelection()
            if line1 == line2:
                aw.setSelection(line1, index1, line1, index1)
                self.findNext()
        
        self.findNextAct.setShortcut(self.viewmanager.searchNextAct.shortcut())
        self.findNextAct.setAlternateShortcut(
            self.viewmanager.searchNextAct.alternateShortcut())
        self.findNextAct.setShortcutContext(Qt.WidgetShortcut)
        self.findPrevAct.setShortcut(self.viewmanager.searchPrevAct.shortcut())
        self.findPrevAct.setAlternateShortcut(
            self.viewmanager.searchPrevAct.alternateShortcut())
        self.findPrevAct.setShortcutContext(Qt.WidgetShortcut)

    def show(self, text=''):
        """
        Public slot to show the widget.
        
        @param text text to be shown in the findtext edit (string)
        """
        if self.replace:
            self.__showReplace(text)
        else:
            self.__showFind(text)
        super(SearchReplaceWidget, self).show()
        self.activateWindow()

    @pyqtSlot()
    def on_closeButton_clicked(self):
        """
        Private slot to close the widget.
        """
        aw = self.viewmanager.activeWindow()
        if aw:
            aw.hideFindIndicator()
        
        if self.__sliding:
            self.__topWidget.close()
        else:
            self.close()
    
    def keyPressEvent(self, event):
        """
        Protected slot to handle key press events.
        
        @param event reference to the key press event (QKeyEvent)
        """
        if event.key() == Qt.Key_Escape:
            aw = self.viewmanager.activeWindow()
            if aw:
                aw.setFocus(Qt.ActiveWindowFocusReason)
                aw.hideFindIndicator()
            event.accept()
            if self.__sliding:
                self.__topWidget.close()
            else:
                self.close()


class SearchReplaceSlidingWidget(QWidget):
    """
    Class implementing the search and replace widget with sliding behavior.
    
    @signal searchListChanged() emitted to indicate a change of the search list
    """
    searchListChanged = pyqtSignal()
    
    def __init__(self, replace, vm, parent=None):
        """
        Constructor
        
        @param replace flag indicating a replace widget is called
        @param vm reference to the viewmanager object
        @param parent parent widget of this widget (QWidget)
        """
        super(SearchReplaceSlidingWidget, self).__init__(parent)
        
        self.__searchReplaceWidget = \
            SearchReplaceWidget(replace, vm, self, True)
        
        self.__layout = QHBoxLayout(self)
        self.setLayout(self.__layout)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setAlignment(Qt.AlignTop)
        
        self.__leftButton = QToolButton(self)
        self.__leftButton.setArrowType(Qt.LeftArrow)
        self.__leftButton.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        self.__leftButton.setAutoRepeat(True)
        
        self.__scroller = QScrollArea(self)
        self.__scroller.setWidget(self.__searchReplaceWidget)
        self.__scroller.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.__scroller.setFrameShape(QFrame.NoFrame)
        self.__scroller.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.__scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.__scroller.setWidgetResizable(False)
        
        self.__rightButton = QToolButton(self)
        self.__rightButton.setArrowType(Qt.RightArrow)
        self.__rightButton.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        self.__rightButton.setAutoRepeat(True)
        
        self.__layout.addWidget(self.__leftButton)
        self.__layout.addWidget(self.__scroller)
        self.__layout.addWidget(self.__rightButton)
        
        self.setMaximumHeight(self.__searchReplaceWidget.sizeHint().height())
        self.adjustSize()
        
        self.__searchReplaceWidget.searchListChanged.connect(
            self.searchListChanged)
        self.__leftButton.clicked.connect(self.__slideLeft)
        self.__rightButton.clicked.connect(self.__slideRight)
    
    def changeEvent(self, evt):
        """
        Protected method handling state changes.

        @param evt event containing the state change (QEvent)
        """
        if evt.type() == QEvent.FontChange:
            self.setMaximumHeight(
                self.__searchReplaceWidget.sizeHint().height())
            self.adjustSize()
    
    def findNext(self):
        """
        Public slot to find the next occurrence of text.
        """
        self.__searchReplaceWidget.findNext()
    
    def findPrev(self):
        """
        Public slot to find the next previous of text.
        """
        self.__searchReplaceWidget.findPrev()
    
    def selectionChanged(self):
        """
        Public slot tracking changes of selected text.
        """
        editor = self.sender()
        self.__searchReplaceWidget.updateSelectionCheckBox(editor)
    
    @pyqtSlot(Editor)
    def updateSelectionCheckBox(self, editor):
        """
        Public slot to update the selection check box.
        
        @param editor reference to the editor (Editor)
        """
        self.__searchReplaceWidget.updateSelectionCheckBox(editor)

    def show(self, text=''):
        """
        Public slot to show the widget.
        
        @param text text to be shown in the findtext edit (string)
        """
        self.__searchReplaceWidget.show(text)
        super(SearchReplaceSlidingWidget, self).show()
        self.__enableScrollerButtons()
    
    def __slideLeft(self):
        """
        Private slot to move the widget to the left, i.e. show contents to the
        right.
        """
        self.__slide(True)
    
    def __slideRight(self):
        """
        Private slot to move the widget to the right, i.e. show contents to
        the left.
        """
        self.__slide(False)
    
    def __slide(self, toLeft):
        """
        Private method to move the sliding widget.
        
        @param toLeft flag indicating to move to the left (boolean)
        """
        scrollBar = self.__scroller.horizontalScrollBar()
        stepSize = scrollBar.singleStep()
        if toLeft:
            stepSize = -stepSize
        newValue = scrollBar.value() + stepSize
        if newValue < 0:
            newValue = 0
        elif newValue > scrollBar.maximum():
            newValue = scrollBar.maximum()
        scrollBar.setValue(newValue)
        self.__enableScrollerButtons()
    
    def __enableScrollerButtons(self):
        """
        Private method to set the enabled state of the scroll buttons.
        """
        scrollBar = self.__scroller.horizontalScrollBar()
        self.__leftButton.setEnabled(scrollBar.value() > 0)
        self.__rightButton.setEnabled(scrollBar.value() < scrollBar.maximum())
    
    def resizeEvent(self, evt):
        """
        Protected method to handle resize events.
        
        @param evt reference to the resize event (QResizeEvent)
        """
        self.__enableScrollerButtons()
        
        super(SearchReplaceSlidingWidget, self).resizeEvent(evt)
