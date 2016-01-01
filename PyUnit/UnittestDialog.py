# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the UI to the pyunit package.
"""

from __future__ import unicode_literals

import unittest
import sys
import time
import re
import os

from PyQt5.QtCore import pyqtSignal, QEvent, Qt, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QDialog, QApplication, QDialogButtonBox, \
    QListWidgetItem

from E5Gui.E5Application import e5App
from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5MessageBox, E5FileDialog
from E5Gui.E5MainWindow import E5MainWindow

from .Ui_UnittestDialog import Ui_UnittestDialog

import UI.PixmapCache

import Utilities
import Preferences


class UnittestDialog(QWidget, Ui_UnittestDialog):
    """
    Class implementing the UI to the pyunit package.
    
    @signal unittestFile(str, int, int) emitted to show the source of a
        unittest file
    @signal unittestStopped() emitted after a unit test was run
    """
    unittestFile = pyqtSignal(str, int, int)
    unittestStopped = pyqtSignal()
    
    def __init__(self, prog=None, dbs=None, ui=None, fromEric=False,
                 parent=None, name=None):
        """
        Constructor
        
        @param prog filename of the program to open
        @param dbs reference to the debug server object. It is an indication
            whether we were called from within the eric6 IDE
        @param ui reference to the UI object
        @param fromEric flag indicating an instantiation from within the
            eric IDE (boolean)
        @param parent parent widget of this dialog (QWidget)
        @param name name of this dialog (string)
        """
        super(UnittestDialog, self).__init__(parent)
        if name:
            self.setObjectName(name)
        self.setupUi(self)
        
        self.fileDialogButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.startButton = self.buttonBox.addButton(
            self.tr("Start"), QDialogButtonBox.ActionRole)
        self.startButton.setToolTip(self.tr(
            "Start the selected testsuite"))
        self.startButton.setWhatsThis(self.tr(
            """<b>Start Test</b>"""
            """<p>This button starts the selected testsuite.</p>"""))
        self.startFailedButton = self.buttonBox.addButton(
            self.tr("Rerun Failed"), QDialogButtonBox.ActionRole)
        self.startFailedButton.setToolTip(
            self.tr("Reruns failed tests of the selected testsuite"))
        self.startFailedButton.setWhatsThis(self.tr(
            """<b>Rerun Failed</b>"""
            """<p>This button reruns all failed tests of the selected"""
            """ testsuite.</p>"""))
        self.stopButton = self.buttonBox.addButton(
            self.tr("Stop"), QDialogButtonBox.ActionRole)
        self.stopButton.setToolTip(self.tr("Stop the running unittest"))
        self.stopButton.setWhatsThis(self.tr(
            """<b>Stop Test</b>"""
            """<p>This button stops a running unittest.</p>"""))
        self.stopButton.setEnabled(False)
        self.startButton.setDefault(True)
        self.startFailedButton.setEnabled(False)
        
        self.dbs = dbs
        self.__fromEric = fromEric
        
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowFlags(
                Qt.WindowContextHelpButtonHint))
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        self.setWindowTitle(self.tr("Unittest"))
        if dbs:
            self.ui = ui
        else:
            self.localCheckBox.hide()
        self.__setProgressColor("green")
        self.progressLed.setDarkFactor(150)
        self.progressLed.off()
        
        self.testSuiteCompleter = E5FileCompleter(self.testsuiteComboBox)
        
        self.fileHistory = []
        self.testNameHistory = []
        self.running = False
        self.savedModulelist = None
        self.savedSysPath = sys.path
        if prog:
            self.insertProg(prog)
        
        self.rxPatterns = [
            self.tr("^Failure: "),
            self.tr("^Error: "),
        ]
        
        self.__failedTests = []
        
        # now connect the debug server signals if called from the eric6 IDE
        if self.dbs:
            self.dbs.utPrepared.connect(self.__UTPrepared)
            self.dbs.utFinished.connect(self.__setStoppedMode)
            self.dbs.utStartTest.connect(self.testStarted)
            self.dbs.utStopTest.connect(self.testFinished)
            self.dbs.utTestFailed.connect(self.testFailed)
            self.dbs.utTestErrored.connect(self.testErrored)
            self.dbs.utTestSkipped.connect(self.testSkipped)
            self.dbs.utTestFailedExpected.connect(self.testFailedExpected)
            self.dbs.utTestSucceededUnexpected.connect(
                self.testSucceededUnexpected)
    
    def keyPressEvent(self, evt):
        """
        Protected slot to handle key press events.
        
        @param evt key press event to handle (QKeyEvent)
        """
        if evt.key() == Qt.Key_Escape and self.__fromEric:
            self.close()
    
    def __setProgressColor(self, color):
        """
        Private methode to set the color of the progress color label.
        
        @param color colour to be shown (string)
        """
        self.progressLed.setColor(QColor(color))
        
    def insertProg(self, prog):
        """
        Public slot to insert the filename prog into the testsuiteComboBox
        object.
        
        @param prog filename to be inserted (string)
        """
        # prepend the selected file to the testsuite combobox
        if prog is None:
            prog = ""
        if prog in self.fileHistory:
            self.fileHistory.remove(prog)
        self.fileHistory.insert(0, prog)
        self.testsuiteComboBox.clear()
        self.testsuiteComboBox.addItems(self.fileHistory)
        
    def insertTestName(self, testName):
        """
        Public slot to insert a test name into the testComboBox object.
        
        @param testName name of the test to be inserted (string)
        """
        # prepend the selected file to the testsuite combobox
        if testName is None:
            testName = ""
        if testName in self.testNameHistory:
            self.testNameHistory.remove(testName)
        self.testNameHistory.insert(0, testName)
        self.testComboBox.clear()
        self.testComboBox.addItems(self.testNameHistory)
        
    @pyqtSlot()
    def on_fileDialogButton_clicked(self):
        """
        Private slot to open a file dialog.
        """
        if self.dbs:
            py2Extensions = \
                ' '.join(["*{0}".format(ext)
                          for ext in self.dbs.getExtensions('Python2')])
            py3Extensions = \
                ' '.join(["*{0}".format(ext)
                          for ext in self.dbs.getExtensions('Python3')])
            filter = self.tr(
                "Python3 Files ({1});;Python2 Files ({0});;All Files (*)")\
                .format(py2Extensions, py3Extensions)
        else:
            filter = self.tr("Python Files (*.py);;All Files (*)")
        prog = E5FileDialog.getOpenFileName(
            self,
            "",
            self.testsuiteComboBox.currentText(),
            filter)
        
        if not prog:
            return
        
        self.insertProg(Utilities.toNativeSeparators(prog))
        
    @pyqtSlot(str)
    def on_testsuiteComboBox_editTextChanged(self, txt):
        """
        Private slot to handle changes of the test file name.
        
        @param txt name of the test file (string)
        """
        if self.dbs:
            exts = self.dbs.getExtensions("Python2")
            flags = Utilities.extractFlagsFromFile(txt)
            if txt.endswith(exts) or \
               ("FileType" in flags and
                    flags["FileType"] in ["Python", "Python2"]):
                self.coverageCheckBox.setChecked(False)
                self.coverageCheckBox.setEnabled(False)
                self.localCheckBox.setChecked(False)
                self.localCheckBox.setEnabled(False)
                return
        
        self.coverageCheckBox.setEnabled(True)
        self.localCheckBox.setEnabled(True)
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.startButton:
            self.on_startButton_clicked()
        elif button == self.stopButton:
            self.on_stopButton_clicked()
        elif button == self.startFailedButton:
            self.on_startButton_clicked(failedOnly=True)
        
    @pyqtSlot()
    def on_startButton_clicked(self, failedOnly=False):
        """
        Private slot to start the test.
        
        @keyparam failedOnly flag indicating to run only failed tests (boolean)
        """
        if self.running:
            return
        
        prog = self.testsuiteComboBox.currentText()
        if not prog:
            E5MessageBox.critical(
                self,
                self.tr("Unittest"),
                self.tr("You must enter a test suite file."))
            return
        
        # prepend the selected file to the testsuite combobox
        self.insertProg(prog)
        self.sbLabel.setText(self.tr("Preparing Testsuite"))
        QApplication.processEvents()
        
        testFunctionName = self.testComboBox.currentText()
        if testFunctionName:
            self.insertTestName(testFunctionName)
        else:
            testFunctionName = "suite"
        
        # build the module name from the filename without extension
        self.testName = os.path.splitext(os.path.basename(prog))[0]
        
        if self.dbs and not self.localCheckBox.isChecked():
            # we are cooperating with the eric6 IDE
            project = e5App().getObject("Project")
            if project.isOpen() and project.isProjectSource(prog):
                mainScript = project.getMainScript(True)
                clientType = project.getProjectLanguage()
            else:
                mainScript = os.path.abspath(prog)
                flags = Utilities.extractFlagsFromFile(mainScript)
                if mainScript.endswith(
                    tuple(Preferences.getPython("PythonExtensions"))) or \
                   ("FileType" in flags and
                        flags["FileType"] in ["Python", "Python2"]):
                    clientType = "Python2"
                else:
                    clientType = ""
            if failedOnly and self.__failedTests:
                failed = [t.split(".", 1)[1] for t in self.__failedTests]
            else:
                failed = []
            self.__failedTests = []
            self.dbs.remoteUTPrepare(
                prog, self.testName, testFunctionName, failed,
                self.coverageCheckBox.isChecked(), mainScript,
                self.coverageEraseCheckBox.isChecked(), clientType=clientType)
        else:
            # we are running as an application or in local mode
            sys.path = [os.path.dirname(os.path.abspath(prog))] + \
                self.savedSysPath
            
            # clean up list of imported modules to force a reimport upon
            # running the test
            if self.savedModulelist:
                for modname in list(sys.modules.keys()):
                    if modname not in self.savedModulelist:
                        # delete it
                        del(sys.modules[modname])
            self.savedModulelist = sys.modules.copy()
            
            # now try to generate the testsuite
            try:
                module = __import__(self.testName)
                try:
                    if failedOnly and self.__failedTests:
                        test = unittest.defaultTestLoader.loadTestsFromNames(
                            [t.split(".", 1)[1] for t in self.__failedTests],
                            module)
                    else:
                        test = unittest.defaultTestLoader.loadTestsFromName(
                            testFunctionName, module)
                except AttributeError:
                    test = unittest.defaultTestLoader.loadTestsFromModule(
                        module)
            except:
                exc_type, exc_value, exc_tb = sys.exc_info()
                E5MessageBox.critical(
                    self,
                    self.tr("Unittest"),
                    self.tr(
                        "<p>Unable to run test <b>{0}</b>.<br>"
                        "{1}<br>{2}</p>")
                    .format(self.testName, str(exc_type),
                            str(exc_value)))
                return
                
            # now set up the coverage stuff
            if self.coverageCheckBox.isChecked():
                if self.dbs:
                    # we are cooperating with the eric6 IDE
                    project = e5App().getObject("Project")
                    if project.isOpen() and project.isProjectSource(prog):
                        mainScript = project.getMainScript(True)
                        if not mainScript:
                            mainScript = os.path.abspath(prog)
                    else:
                        mainScript = os.path.abspath(prog)
                else:
                    mainScript = os.path.abspath(prog)
                
                from DebugClients.Python3.coverage import coverage
                cover = coverage(
                    data_file="{0}.coverage".format(
                        os.path.splitext(mainScript)[0]))
                if self.coverageEraseCheckBox.isChecked():
                    cover.erase()
            else:
                cover = None
            
            self.testResult = QtTestResult(self)
            self.totalTests = test.countTestCases()
            self.__failedTests = []
            self.__setRunningMode()
            if cover:
                cover.start()
            test.run(self.testResult)
            if cover:
                cover.stop()
                cover.save()
            self.__setStoppedMode()
            sys.path = self.savedSysPath
        
    def __UTPrepared(self, nrTests, exc_type, exc_value):
        """
        Private slot to handle the utPrepared signal.
        
        If the unittest suite was loaded successfully, we ask the
        client to run the test suite.
        
        @param nrTests number of tests contained in the test suite (integer)
        @param exc_type type of exception occured during preparation (string)
        @param exc_value value of exception occured during preparation (string)
        """
        if nrTests == 0:
            E5MessageBox.critical(
                self,
                self.tr("Unittest"),
                self.tr(
                    "<p>Unable to run test <b>{0}</b>.<br>{1}<br>{2}</p>")
                .format(self.testName, exc_type, exc_value))
            return
            
        self.totalTests = nrTests
        self.__setRunningMode()
        self.dbs.remoteUTRun()
        
    @pyqtSlot()
    def on_stopButton_clicked(self):
        """
        Private slot to stop the test.
        """
        if self.dbs and not self.localCheckBox.isChecked():
            self.dbs.remoteUTStop()
        elif self.testResult:
            self.testResult.stop()
            
    def on_errorsListWidget_currentTextChanged(self, text):
        """
        Private slot to handle the highlighted signal.
        
        @param text current text (string)
        """
        if text:
            for pattern in self.rxPatterns:
                text = re.sub(pattern, "", text)
            itm = self.testsListWidget.findItems(
                text, Qt.MatchFlags(Qt.MatchExactly))[0]
            self.testsListWidget.setCurrentItem(itm)
            self.testsListWidget.scrollToItem(itm)
        
    def __setRunningMode(self):
        """
        Private method to set the GUI in running mode.
        """
        self.running = True
        
        # reset counters and error infos
        self.runCount = 0
        self.failCount = 0
        self.errorCount = 0
        self.skippedCount = 0
        self.expectedFailureCount = 0
        self.unexpectedSuccessCount = 0
        self.remainingCount = self.totalTests

        # reset the GUI
        self.progressCounterRunCount.setText(str(self.runCount))
        self.progressCounterRemCount.setText(str(self.remainingCount))
        self.progressCounterFailureCount.setText(str(self.failCount))
        self.progressCounterErrorCount.setText(str(self.errorCount))
        self.progressCounterSkippedCount.setText(str(self.skippedCount))
        self.progressCounterExpectedFailureCount.setText(
            str(self.expectedFailureCount))
        self.progressCounterUnexpectedSuccessCount.setText(
            str(self.unexpectedSuccessCount))
        self.errorsListWidget.clear()
        self.testsListWidget.clear()
        self.progressProgressBar.setRange(0, self.totalTests)
        self.__setProgressColor("green")
        self.progressProgressBar.reset()
        self.stopButton.setEnabled(True)
        self.startButton.setEnabled(False)
        self.stopButton.setDefault(True)
        self.sbLabel.setText(self.tr("Running"))
        self.progressLed.on()
        QApplication.processEvents()
        
        self.startTime = time.time()
        
    def __setStoppedMode(self):
        """
        Private method to set the GUI in stopped mode.
        """
        self.stopTime = time.time()
        self.timeTaken = float(self.stopTime - self.startTime)
        self.running = False
        
        self.startButton.setEnabled(True)
        self.startFailedButton.setEnabled(bool(self.__failedTests))
        self.stopButton.setEnabled(False)
        if self.__failedTests:
            self.startFailedButton.setDefault(True)
            self.startButton.setDefault(False)
        else:
            self.startFailedButton.setDefault(False)
            self.startButton.setDefault(True)
        if self.runCount == 1:
            self.sbLabel.setText(
                self.tr("Ran {0} test in {1:.3f}s")
                    .format(self.runCount, self.timeTaken))
        else:
            self.sbLabel.setText(
                self.tr("Ran {0} tests in {1:.3f}s")
                    .format(self.runCount, self.timeTaken))
        self.progressLed.off()
        
        self.unittestStopped.emit()

    def testFailed(self, test, exc, id):
        """
        Public method called if a test fails.
        
        @param test name of the test (string)
        @param exc string representation of the exception (string)
        @param id id of the test (string)
        """
        self.failCount += 1
        self.progressCounterFailureCount.setText(str(self.failCount))
        itm = QListWidgetItem(self.tr("Failure: {0}").format(test))
        itm.setData(Qt.UserRole, (test, exc))
        self.errorsListWidget.insertItem(0, itm)
        self.__failedTests.append(id)
        
    def testErrored(self, test, exc, id):
        """
        Public method called if a test errors.
        
        @param test name of the test (string)
        @param exc string representation of the exception (string)
        @param id id of the test (string)
        """
        self.errorCount += 1
        self.progressCounterErrorCount.setText(str(self.errorCount))
        itm = QListWidgetItem(self.tr("Error: {0}").format(test))
        itm.setData(Qt.UserRole, (test, exc))
        self.errorsListWidget.insertItem(0, itm)
        self.__failedTests.append(id)
        
    def testSkipped(self, test, reason, id):
        """
        Public method called if a test was skipped.
        
        @param test name of the test (string)
        @param reason reason for skipping the test (string)
        @param id id of the test (string)
        """
        self.skippedCount += 1
        self.progressCounterSkippedCount.setText(str(self.skippedCount))
        itm = QListWidgetItem(self.tr("    Skipped: {0}").format(reason))
        itm.setForeground(Qt.blue)
        self.testsListWidget.insertItem(1, itm)
        
    def testFailedExpected(self, test, exc, id):
        """
        Public method called if a test fails expectedly.
        
        @param test name of the test (string)
        @param exc string representation of the exception (string)
        @param id id of the test (string)
        """
        self.expectedFailureCount += 1
        self.progressCounterExpectedFailureCount.setText(
            str(self.expectedFailureCount))
        itm = QListWidgetItem(self.tr("    Expected Failure"))
        itm.setForeground(Qt.blue)
        self.testsListWidget.insertItem(1, itm)
        
    def testSucceededUnexpected(self, test, id):
        """
        Public method called if a test succeeds unexpectedly.
        
        @param test name of the test (string)
        @param id id of the test (string)
        """
        self.unexpectedSuccessCount += 1
        self.progressCounterUnexpectedSuccessCount.setText(
            str(self.unexpectedSuccessCount))
        itm = QListWidgetItem(self.tr("    Unexpected Success"))
        itm.setForeground(Qt.red)
        self.testsListWidget.insertItem(1, itm)
        
    def testStarted(self, test, doc):
        """
        Public method called if a test is about to be run.
        
        @param test name of the started test (string)
        @param doc documentation of the started test (string)
        """
        if doc:
            self.testsListWidget.insertItem(0, "    {0}".format(doc))
        self.testsListWidget.insertItem(0, test)
        if self.dbs is None or self.localCheckBox.isChecked():
            QApplication.processEvents()
        
    def testFinished(self):
        """
        Public method called if a test has finished.
        
        <b>Note</b>: It is also called if it has already failed or errored.
        """
        # update the counters
        self.remainingCount -= 1
        self.runCount += 1
        self.progressCounterRunCount.setText(str(self.runCount))
        self.progressCounterRemCount.setText(str(self.remainingCount))
        
        # update the progressbar
        if self.errorCount:
            self.__setProgressColor("red")
        elif self.failCount:
            self.__setProgressColor("orange")
        self.progressProgressBar.setValue(self.runCount)
        
    def on_errorsListWidget_itemDoubleClicked(self, lbitem):
        """
        Private slot called by doubleclicking an errorlist entry.
        
        It will popup a dialog showing the stacktrace.
        If called from eric, an additional button is displayed
        to show the python source in an eric source viewer (in
        erics main window.
        
        @param lbitem the listbox item that was double clicked
        """
        self.errListIndex = self.errorsListWidget.row(lbitem)
        text = lbitem.text()
        self.on_errorsListWidget_currentTextChanged(text)

        # get the error info
        test, tracebackText = lbitem.data(Qt.UserRole)

        # now build the dialog
        from .Ui_UnittestStacktraceDialog import Ui_UnittestStacktraceDialog
        self.dlg = QDialog()
        ui = Ui_UnittestStacktraceDialog()
        ui.setupUi(self.dlg)
        self.dlg.traceback = ui.traceback
        
        ui.showButton = ui.buttonBox.addButton(
            self.tr("Show Source"), QDialogButtonBox.ActionRole)
        ui.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.dlg.setWindowTitle(text)
        ui.testLabel.setText(test)
        ui.traceback.setPlainText(tracebackText)
        
        # one more button if called from eric
        if self.dbs:
            ui.showButton.clicked.connect(self.__showSource)
        else:
            ui.showButton.hide()

        # and now fire it up
        self.dlg.show()
        self.dlg.exec_()
        
    def __showSource(self):
        """
        Private slot to show the source of a traceback in an eric6 editor.
        """
        if not self.dbs:
            return
            
        # get the error info
        tracebackLines = self.dlg.traceback.toPlainText().splitlines()
        # find the last entry matching the pattern
        for index in range(len(tracebackLines) - 1, -1, -1):
            fmatch = re.search(r'File "(.*?)", line (\d*?),.*',
                               tracebackLines[index])
            if fmatch:
                break
        if fmatch:
            fn, ln = fmatch.group(1, 2)
            self.unittestFile.emit(fn, int(ln), 1)
    
    def hasFailedTests(self):
        """
        Public method to check, if there are failed tests from the last run.
        
        @return flag indicating the presence of failed tests (boolean)
        """
        return bool(self.__failedTests)


class QtTestResult(unittest.TestResult):
    """
    A TestResult derivative to work with a graphical GUI.
    
    For more details see pyunit.py of the standard python distribution.
    """
    def __init__(self, parent):
        """
        Constructor
        
        @param parent The parent widget.
        """
        super(QtTestResult, self).__init__()
        self.parent = parent
        
    def addFailure(self, test, err):
        """
        Public method called if a test failed.
        
        @param test reference to the test object
        @param err error traceback
        """
        super(QtTestResult, self).addFailure(test, err)
        tracebackLines = self._exc_info_to_string(err, test)
        self.parent.testFailed(str(test), tracebackLines, test.id())
        
    def addError(self, test, err):
        """
        Public method called if a test errored.
        
        @param test reference to the test object
        @param err error traceback
        """
        super(QtTestResult, self).addError(test, err)
        tracebackLines = self._exc_info_to_string(err, test)
        self.parent.testErrored(str(test), tracebackLines, test.id())
        
    def addSkip(self, test, reason):
        """
        Public method called if a test was skipped.
        
        @param test reference to the test object
        @param reason reason for skipping the test (string)
        """
        super(QtTestResult, self).addSkip(test, reason)
        self.parent.testSkipped(str(test), reason, test.id())
        
    def addExpectedFailure(self, test, err):
        """
        Public method called if a test failed expected.
        
        @param test reference to the test object
        @param err error traceback
        """
        super(QtTestResult, self).addExpectedFailure(test, err)
        tracebackLines = self._exc_info_to_string(err, test)
        self.parent.testFailedExpected(str(test), tracebackLines, test.id())
        
    def addUnexpectedSuccess(self, test):
        """
        Public method called if a test succeeded expectedly.
        
        @param test reference to the test object
        """
        super(QtTestResult, self).addUnexpectedSuccess(test)
        self.parent.testSucceededUnexpected(str(test), test.id())
        
    def startTest(self, test):
        """
        Public method called at the start of a test.
        
        @param test Reference to the test object
        """
        super(QtTestResult, self).startTest(test)
        self.parent.testStarted(str(test), test.shortDescription())

    def stopTest(self, test):
        """
        Public method called at the end of a test.
        
        @param test Reference to the test object
        """
        super(QtTestResult, self).stopTest(test)
        self.parent.testFinished()


class UnittestWindow(E5MainWindow):
    """
    Main window class for the standalone dialog.
    """
    def __init__(self, prog=None, parent=None):
        """
        Constructor
        
        @param prog filename of the program to open
        @param parent reference to the parent widget (QWidget)
        """
        super(UnittestWindow, self).__init__(parent)
        self.cw = UnittestDialog(prog=prog, parent=self)
        self.cw.installEventFilter(self)
        size = self.cw.size()
        self.setCentralWidget(self.cw)
        self.resize(size)
        
        self.setStyle(Preferences.getUI("Style"),
                      Preferences.getUI("StyleSheet"))
    
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
