# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to compare two files.
"""

from __future__ import unicode_literals

import os
import time

from PyQt5.QtCore import QFileInfo, QEvent, pyqtSlot
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QWidget, QApplication, QDialogButtonBox

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5MessageBox, E5FileDialog
from E5Gui.E5MainWindow import E5MainWindow

from .Ui_DiffDialog import Ui_DiffDialog
from .DiffHighlighter import DiffHighlighter

import Utilities
import Preferences
import UI.PixmapCache

from difflib import SequenceMatcher

# This function is copied from python 2.3 and slightly modified.
# The header lines contain a tab after the filename.


def unified_diff(a, b, fromfile='', tofile='', fromfiledate='',
                 tofiledate='', n=3, lineterm='\n'):
    """
    Compare two sequences of lines; generate the delta as a unified diff.

    Unified diffs are a compact way of showing line changes and a few
    lines of context.  The number of context lines is set by 'n' which
    defaults to three.

    By default, the diff control lines (those with ---, +++, or @@) are
    created with a trailing newline.  This is helpful so that inputs
    created from file.readlines() result in diffs that are suitable for
    file.writelines() since both the inputs and outputs have trailing
    newlines.

    For inputs that do not have trailing newlines, set the lineterm
    argument to "" so that the output will be uniformly newline free.

    The unidiff format normally has a header for filenames and modification
    times.  Any or all of these may be specified using strings for
    'fromfile', 'tofile', 'fromfiledate', and 'tofiledate'.  The modification
    times are normally expressed in the format returned by time.ctime().

    Example:

    <pre>
    &gt;&gt;&gt; for line in unified_diff('one two three four'.split(),
    ...             'zero one tree four'.split(), 'Original', 'Current',
    ...             'Sat Jan 26 23:30:50 1991', 'Fri Jun 06 10:20:52 2003',
    ...             lineterm=''):
    ...     print line
    --- Original Sat Jan 26 23:30:50 1991
    +++ Current Fri Jun 06 10:20:52 2003
    @@ -1,4 +1,4 @@
    +zero
     one
    -two
    -three
    +tree
     four
    </pre>
    
    @param a first sequence of lines (list of strings)
    @param b second sequence of lines (list of strings)
    @param fromfile filename of the first file (string)
    @param tofile filename of the second file (string)
    @param fromfiledate modification time of the first file (string)
    @param tofiledate modification time of the second file (string)
    @param n number of lines of context (integer)
    @param lineterm line termination string (string)
    @return a generator yielding lines of differences
    """
    started = False
    for group in SequenceMatcher(None, a, b).get_grouped_opcodes(n):
        if not started:
            yield '--- {0}\t{1}{2}'.format(fromfile, fromfiledate, lineterm)
            yield '+++ {0}\t{1}{2}'.format(tofile, tofiledate, lineterm)
            started = True
        i1, i2, j1, j2 = group[0][1], group[-1][2], group[0][3], group[-1][4]
        yield "@@ -{0:d},{1:d} +{2:d},{3:d} @@{4}".format(
            i1 + 1, i2 - i1, j1 + 1, j2 - j1, lineterm)
        for tag, i1, i2, j1, j2 in group:
            if tag == 'equal':
                for line in a[i1:i2]:
                    yield ' ' + line
                continue
            if tag == 'replace' or tag == 'delete':
                for line in a[i1:i2]:
                    yield '-' + line
            if tag == 'replace' or tag == 'insert':
                for line in b[j1:j2]:
                    yield '+' + line

# This function is copied from python 2.3 and slightly modified.
# The header lines contain a tab after the filename.


def context_diff(a, b, fromfile='', tofile='',
                 fromfiledate='', tofiledate='', n=3, lineterm='\n'):
    r"""
    Compare two sequences of lines; generate the delta as a context diff.

    Context diffs are a compact way of showing line changes and a few
    lines of context.  The number of context lines is set by 'n' which
    defaults to three.

    By default, the diff control lines (those with *** or ---) are
    created with a trailing newline.  This is helpful so that inputs
    created from file.readlines() result in diffs that are suitable for
    file.writelines() since both the inputs and outputs have trailing
    newlines.

    For inputs that do not have trailing newlines, set the lineterm
    argument to "" so that the output will be uniformly newline free.

    The context diff format normally has a header for filenames and
    modification times.  Any or all of these may be specified using
    strings for 'fromfile', 'tofile', 'fromfiledate', and 'tofiledate'.
    The modification times are normally expressed in the format returned
    by time.ctime().  If not specified, the strings default to blanks.

    Example:

    <pre>
    &gt;&gt;&gt; print ''.join(
    ...       context_diff('one\ntwo\nthree\nfour\n'.splitlines(1),
    ...       'zero\none\ntree\nfour\n'.splitlines(1), 'Original', 'Current',
    ...       'Sat Jan 26 23:30:50 1991', 'Fri Jun 06 10:22:46 2003')),
    *** Original Sat Jan 26 23:30:50 1991
    --- Current Fri Jun 06 10:22:46 2003
    ***************
    *** 1,4 ****
      one
    ! two
    ! three
      four
    --- 1,4 ----
    + zero
      one
    ! tree
      four
    </pre>
    
    @param a first sequence of lines (list of strings)
    @param b second sequence of lines (list of strings)
    @param fromfile filename of the first file (string)
    @param tofile filename of the second file (string)
    @param fromfiledate modification time of the first file (string)
    @param tofiledate modification time of the second file (string)
    @param n number of lines of context (integer)
    @param lineterm line termination string (string)
    @return a generator yielding lines of differences
    """
    started = False
    prefixmap = {'insert': '+ ', 'delete': '- ', 'replace': '! ',
                 'equal': '  '}
    for group in SequenceMatcher(None, a, b).get_grouped_opcodes(n):
        if not started:
            yield '*** {0}\t{1}{2}'.format(fromfile, fromfiledate, lineterm)
            yield '--- {0}\t{1}{2}'.format(tofile, tofiledate, lineterm)
            started = True

        yield '***************{0}'.format(lineterm)
        if group[-1][2] - group[0][1] >= 2:
            yield '*** {0:d},{1:d} ****{2}'.format(
                group[0][1] + 1, group[-1][2], lineterm)
        else:
            yield '*** {0:d} ****{1}'.format(group[-1][2], lineterm)
        visiblechanges = [e for e in group if e[0] in ('replace', 'delete')]
        if visiblechanges:
            for tag, i1, i2, _, _ in group:
                if tag != 'insert':
                    for line in a[i1:i2]:
                        yield prefixmap[tag] + line

        if group[-1][4] - group[0][3] >= 2:
            yield '--- {0:d},{1:d} ----{2}'.format(
                group[0][3] + 1, group[-1][4], lineterm)
        else:
            yield '--- {0:d} ----{1}'.format(group[-1][4], lineterm)
        visiblechanges = [e for e in group if e[0] in ('replace', 'insert')]
        if visiblechanges:
            for tag, _, _, j1, j2 in group:
                if tag != 'delete':
                    for line in b[j1:j2]:
                        yield prefixmap[tag] + line


class DiffDialog(QWidget, Ui_DiffDialog):
    """
    Class implementing a dialog to compare two files.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(DiffDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.file1Button.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.file2Button.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.file1Completer = E5FileCompleter(self.file1Edit)
        self.file2Completer = E5FileCompleter(self.file2Edit)
        
        self.diffButton = self.buttonBox.addButton(
            self.tr("Compare"), QDialogButtonBox.ActionRole)
        self.diffButton.setToolTip(
            self.tr("Press to perform the comparison of the two files"))
        self.saveButton = self.buttonBox.addButton(
            self.tr("Save"), QDialogButtonBox.ActionRole)
        self.saveButton.setToolTip(
            self.tr("Save the output to a patch file"))
        self.diffButton.setEnabled(False)
        self.saveButton.setEnabled(False)
        self.diffButton.setDefault(True)
        
        self.searchWidget.attachTextEdit(self.contents)
        
        self.filename1 = ''
        self.filename2 = ''
        
        self.updateInterval = 20    # update every 20 lines
        
        font = Preferences.getEditorOtherFonts("MonospacedFont")
        self.contents.setFontFamily(font.family())
        self.contents.setFontPointSize(font.pointSize())
        
        self.highlighter = DiffHighlighter(self.contents.document())
        
        # connect some of our widgets explicitly
        self.file1Edit.textChanged.connect(self.__fileChanged)
        self.file2Edit.textChanged.connect(self.__fileChanged)
        
    def show(self, filename=None):
        """
        Public slot to show the dialog.
        
        @param filename name of a file to use as the first file (string)
        """
        if filename:
            self.file1Edit.setText(filename)
        super(DiffDialog, self).show()
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.diffButton:
            self.on_diffButton_clicked()
        elif button == self.saveButton:
            self.on_saveButton_clicked()
        
    @pyqtSlot()
    def on_saveButton_clicked(self):
        """
        Private slot to handle the Save button press.
        
        It saves the diff shown in the dialog to a file in the local
        filesystem.
        """
        dname, fname = Utilities.splitPath(self.filename2)
        if fname != '.':
            fname = "{0}.diff".format(self.filename2)
        else:
            fname = dname
            
        fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            self,
            self.tr("Save Diff"),
            fname,
            self.tr("Patch Files (*.diff)"),
            None,
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        
        if not fname:
            return
        
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
        
        try:
            f = open(fname, "w", encoding="utf-8")
            txt = self.contents.toPlainText()
            try:
                f.write(txt)
            except UnicodeError:
                pass
            f.close()
        except IOError as why:
            E5MessageBox.critical(
                self, self.tr('Save Diff'),
                self.tr(
                    '<p>The patch file <b>{0}</b> could not be saved.<br />'
                    'Reason: {1}</p>').format(fname, str(why)))

    @pyqtSlot()
    def on_diffButton_clicked(self):
        """
        Private slot to handle the Compare button press.
        """
        self.filename1 = Utilities.toNativeSeparators(self.file1Edit.text())
        try:
            filemtime1 = time.ctime(os.stat(self.filename1).st_mtime)
        except IOError:
            filemtime1 = ""
        try:
            f1 = open(self.filename1, "r", encoding="utf-8")
            lines1 = f1.readlines()
            f1.close()
        except IOError:
            E5MessageBox.critical(
                self,
                self.tr("Compare Files"),
                self.tr(
                    """<p>The file <b>{0}</b> could not be read.</p>""")
                .format(self.filename1))
            return

        self.filename2 = Utilities.toNativeSeparators(self.file2Edit.text())
        try:
            filemtime2 = time.ctime(os.stat(self.filename2).st_mtime)
        except IOError:
            filemtime2 = ""
        try:
            f2 = open(self.filename2, "r", encoding="utf-8")
            lines2 = f2.readlines()
            f2.close()
        except IOError:
            E5MessageBox.critical(
                self,
                self.tr("Compare Files"),
                self.tr(
                    """<p>The file <b>{0}</b> could not be read.</p>""")
                .format(self.filename2))
            return
        
        self.contents.clear()
        self.saveButton.setEnabled(False)
        
        if self.unifiedRadioButton.isChecked():
            self.__generateUnifiedDiff(
                lines1, lines2, self.filename1, self.filename2,
                filemtime1, filemtime2)
        else:
            self.__generateContextDiff(
                lines1, lines2, self.filename1, self.filename2,
                filemtime1, filemtime2)
        
        tc = self.contents.textCursor()
        tc.movePosition(QTextCursor.Start)
        self.contents.setTextCursor(tc)
        self.contents.ensureCursorVisible()
        
        self.saveButton.setEnabled(True)

    def __appendText(self, txt):
        """
        Private method to append text to the end of the contents pane.
        
        @param txt text to insert (string)
        """
        tc = self.contents.textCursor()
        tc.movePosition(QTextCursor.End)
        self.contents.setTextCursor(tc)
        self.contents.insertPlainText(txt)
        
    def __generateUnifiedDiff(self, a, b, fromfile, tofile,
                              fromfiledate, tofiledate):
        """
        Private slot to generate a unified diff output.
        
        @param a first sequence of lines (list of strings)
        @param b second sequence of lines (list of strings)
        @param fromfile filename of the first file (string)
        @param tofile filename of the second file (string)
        @param fromfiledate modification time of the first file (string)
        @param tofiledate modification time of the second file (string)
        """
        paras = 0
        for line in unified_diff(a, b, fromfile, tofile,
                                 fromfiledate, tofiledate):
            self.__appendText(line)
            paras += 1
            if not (paras % self.updateInterval):
                QApplication.processEvents()
            
        if paras == 0:
            self.__appendText(self.tr('There is no difference.'))

    def __generateContextDiff(self, a, b, fromfile, tofile,
                              fromfiledate, tofiledate):
        """
        Private slot to generate a context diff output.
        
        @param a first sequence of lines (list of strings)
        @param b second sequence of lines (list of strings)
        @param fromfile filename of the first file (string)
        @param tofile filename of the second file (string)
        @param fromfiledate modification time of the first file (string)
        @param tofiledate modification time of the second file (string)
        """
        paras = 0
        for line in context_diff(a, b, fromfile, tofile,
                                 fromfiledate, tofiledate):
            self.__appendText(line)
            paras += 1
            if not (paras % self.updateInterval):
                QApplication.processEvents()
            
        if paras == 0:
            self.__appendText(self.tr('There is no difference.'))

    def __fileChanged(self):
        """
        Private slot to enable/disable the Compare button.
        """
        if not self.file1Edit.text() or \
           not self.file2Edit.text():
            self.diffButton.setEnabled(False)
        else:
            self.diffButton.setEnabled(True)

    def __selectFile(self, lineEdit):
        """
        Private slot to display a file selection dialog.
        
        @param lineEdit field for the display of the selected filename
                (QLineEdit)
        """
        filename = E5FileDialog.getOpenFileName(
            self,
            self.tr("Select file to compare"),
            lineEdit.text(),
            "")
            
        if filename:
            lineEdit.setText(Utilities.toNativeSeparators(filename))

    @pyqtSlot()
    def on_file1Button_clicked(self):
        """
        Private slot to handle the file 1 file selection button press.
        """
        self.__selectFile(self.file1Edit)

    @pyqtSlot()
    def on_file2Button_clicked(self):
        """
        Private slot to handle the file 2 file selection button press.
        """
        self.__selectFile(self.file2Edit)


class DiffWindow(E5MainWindow):
    """
    Main window class for the standalone dialog.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(DiffWindow, self).__init__(parent)
        
        self.setStyle(Preferences.getUI("Style"),
                      Preferences.getUI("StyleSheet"))
        
        self.cw = DiffDialog(self)
        self.cw.installEventFilter(self)
        size = self.cw.size()
        self.setCentralWidget(self.cw)
        self.resize(size)
    
    def eventFilter(self, obj, event):
        """
        Public method to filter events.
        
        @param obj reference to the object the event is meant for (QObject)
        @param event reference to the event object (QEvent)
        @return flag indicating, whether the event was handled (boolean)
        """
        if event.type() == QEvent.Close:
            QApplication.exit()
            return True
        
        return False
