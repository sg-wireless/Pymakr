# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to browse the log history.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os
import re

from PyQt5.QtCore import pyqtSlot, Qt, QDate, QProcess, QTimer, QRegExp, \
    QSize, QPoint
from PyQt5.QtGui import QCursor, QColor, QPixmap, QPainter, QPen, QBrush, QIcon
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QHeaderView, \
    QTreeWidgetItem, QApplication, QLineEdit, QMenu

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox

from .Ui_HgLogBrowserDialog import Ui_HgLogBrowserDialog

import UI.PixmapCache

COLORNAMES = ["blue", "darkgreen", "red", "green", "darkblue", "purple",
              "cyan", "olive", "magenta", "darkred", "darkmagenta",
              "darkcyan", "gray", "yellow"]
COLORS = [str(QColor(x).name()) for x in COLORNAMES]


class HgLogBrowserDialog(QWidget, Ui_HgLogBrowserDialog):
    """
    Class implementing a dialog to browse the log history.
    """
    IconColumn = 0
    BranchColumn = 1
    RevisionColumn = 2
    PhaseColumn = 3
    AuthorColumn = 4
    DateColumn = 5
    MessageColumn = 6
    TagsColumn = 7
    
    LargefilesCacheL = ".hglf/"
    LargefilesCacheW = ".hglf\\"
    PathSeparatorRe = re.compile(r"/|\\")
    
    ClosedIndicator = " \u2612"
    
    def __init__(self, vcs, mode="log", parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param mode mode of the dialog (string; one of log, incoming, outgoing)
        @param parent parent widget (QWidget)
        """
        super(HgLogBrowserDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.__position = QPoint()
        
        if mode == "log":
            self.setWindowTitle(self.tr("Mercurial Log"))
        elif mode == "incoming":
            self.setWindowTitle(self.tr("Mercurial Log (Incoming)"))
        elif mode == "outgoing":
            self.setWindowTitle(self.tr("Mercurial Log (Outgoing)"))
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.filesTree.headerItem().setText(self.filesTree.columnCount(), "")
        self.filesTree.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.refreshButton = self.buttonBox.addButton(
            self.tr("&Refresh"), QDialogButtonBox.ActionRole)
        self.refreshButton.setToolTip(
            self.tr("Press to refresh the list of changesets"))
        self.refreshButton.setEnabled(False)
        
        self.findPrevButton.setIcon(UI.PixmapCache.getIcon("1leftarrow.png"))
        self.findNextButton.setIcon(UI.PixmapCache.getIcon("1rightarrow.png"))
        self.__findBackwards = False
        
        self.modeComboBox.addItem(self.tr("Find"), "find")
        self.modeComboBox.addItem(self.tr("Filter"), "filter")
        
        self.fieldCombo.addItem(self.tr("Revision"), "revision")
        self.fieldCombo.addItem(self.tr("Author"), "author")
        self.fieldCombo.addItem(self.tr("Message"), "message")
        self.fieldCombo.addItem(self.tr("File"), "file")
        
        self.vcs = vcs
        if mode in ("log", "incoming", "outgoing"):
            self.commandMode = mode
            self.initialCommandMode = mode
        else:
            self.commandMode = "log"
            self.initialCommandMode = "log"
        self.__hgClient = vcs.getClient()
        
        self.__detailsTemplate = self.tr(
            "<table>"
            "<tr><td><b>Revision</b></td><td>{0}</td></tr>"
            "<tr><td><b>Date</b></td><td>{1}</td></tr>"
            "<tr><td><b>Author</b></td><td>{2}</td></tr>"
            "<tr><td><b>Branch</b></td><td>{3}</td></tr>"
            "<tr><td><b>Parents</b></td><td>{4}</td></tr>"
            "{5}"
            "</table>"
        )
        self.__tagsTemplate = self.tr(
            "<tr><td><b>Tags</b></td><td>{0}</td></tr>"
        )
        self.__bookmarksTemplate = self.tr(
            "<tr><td><b>Bookmarks</b></td><td>{0}</td></tr>"
        )
        
        self.__bundle = ""
        self.__filename = ""
        self.__isFile = False
        self.__currentRevision = ""
        self.intercept = False
        
        self.__initData()
        
        self.__allBranchesFilter = self.tr("All")
        
        self.fromDate.setDisplayFormat("yyyy-MM-dd")
        self.toDate.setDisplayFormat("yyyy-MM-dd")
        self.__resetUI()
        
        self.__messageRole = Qt.UserRole
        self.__changesRole = Qt.UserRole + 1
        self.__edgesRole = Qt.UserRole + 2
        self.__parentsRole = Qt.UserRole + 3
        
        if self.__hgClient:
            self.process = None
        else:
            self.process = QProcess()
            self.process.finished.connect(self.__procFinished)
            self.process.readyReadStandardOutput.connect(self.__readStdout)
            self.process.readyReadStandardError.connect(self.__readStderr)
        
        self.flags = {
            'A': self.tr('Added'),
            'D': self.tr('Deleted'),
            'M': self.tr('Modified'),
        }
        
        self.phases = {
            'draft': self.tr("Draft"),
            'public': self.tr("Public"),
            'secret': self.tr("Secret"),
        }
        
        self.__dotRadius = 8
        self.__rowHeight = 20
        
        self.logTree.setIconSize(
            QSize(100 * self.__rowHeight, self.__rowHeight))
        self.BookmarksColumn = self.logTree.columnCount()
        self.logTree.headerItem().setText(
            self.BookmarksColumn, self.tr("Bookmarks"))
        if self.vcs.version < (2, 1):
            self.logTree.setColumnHidden(self.PhaseColumn, True)
        
        self.__initActionsMenu()
    
    def __initActionsMenu(self):
        """
        Private method to initialize the actions menu.
        """
        self.__actionsMenu = QMenu()
        if self.vcs.version >= (2, 0):
            self.__graftAct = self.__actionsMenu.addAction(
                self.tr("Copy Changesets"), self.__graftActTriggered)
            self.__graftAct.setToolTip(self.tr(
                "Copy the selected changesets to the current branch"))
        else:
            self.__graftAct = None
        
        if self.vcs.version >= (2, 1):
            self.__phaseAct = self.__actionsMenu.addAction(
                self.tr("Change Phase"), self.__phaseActTriggered)
            self.__phaseAct.setToolTip(self.tr(
                "Change the phase of the selected revisions"))
            self.__phaseAct.setWhatsThis(self.tr(
                """<b>Change Phase</b>\n<p>This changes the phase of the"""
                """ selected revisions. The selected revisions have to have"""
                """ the same current phase.</p>"""))
        else:
            self.__phaseAct = None
        
        self.__tagAct = self.__actionsMenu.addAction(
            self.tr("Tag"), self.__tagActTriggered)
        self.__tagAct.setToolTip(self.tr("Tag the selected revision"))
        
        self.__switchAct = self.__actionsMenu.addAction(
            self.tr("Switch"), self.__switchActTriggered)
        self.__switchAct.setToolTip(self.tr(
            "Switch the working directory to the selected revision"))
        
        self.__actionsMenu.addSeparator()
        
        self.__pullAct = self.__actionsMenu.addAction(
            self.tr("Pull Changes"), self.__pullActTriggered)
        self.__pullAct.setToolTip(self.tr(
            "Pull changes from a remote repository"))
        if self.vcs.version >= (2, 0):
            self.__lfPullAct = self.__actionsMenu.addAction(
                self.tr("Pull Large Files"), self.__lfPullActTriggered)
            self.__lfPullAct.setToolTip(self.tr(
                "Pull large files for selected revisions"))
        else:
            self.__lfPullAct = None
        
        self.__actionsMenu.addSeparator()
        
        self.__pushAct = self.__actionsMenu.addAction(
            self.tr("Push Selected Changes"), self.__pushActTriggered)
        self.__pushAct.setToolTip(self.tr(
            "Push changes of the selected changeset and its ancestors"
            " to a remote repository"))
        self.__pushAllAct = self.__actionsMenu.addAction(
            self.tr("Push All Changes"), self.__pushAllActTriggered)
        self.__pushAllAct.setToolTip(self.tr(
            "Push all changes to a remote repository"))
        
        self.actionsButton.setIcon(
            UI.PixmapCache.getIcon("actionsToolButton.png"))
        self.actionsButton.setMenu(self.__actionsMenu)
    
    def __initData(self):
        """
        Private method to (re-)initialize some data.
        """
        self.__maxDate = QDate()
        self.__minDate = QDate()
        self.__filterLogsEnabled = True
        
        self.buf = []        # buffer for stdout
        self.diff = None
        self.__started = False
        self.__lastRev = 0
        self.projectMode = False
        
        # attributes to store log graph data
        self.__revs = []
        self.__revColors = {}
        self.__revColor = 0
        
        self.__branchColors = {}
        
        self.__projectRevision = -1
        self.__projectBranch = ""
    
    def closeEvent(self, e):
        """
        Protected slot implementing a close event handler.
        
        @param e close event (QCloseEvent)
        """
        if self.__hgClient:
            if self.__hgClient.isExecuting():
                self.__hgClient.cancel()
        else:
            if self.process is not None and \
               self.process.state() != QProcess.NotRunning:
                self.process.terminate()
                QTimer.singleShot(2000, self.process.kill)
                self.process.waitForFinished(3000)
        
        self.__position = self.pos()
        
        e.accept()
    
    def show(self):
        """
        Public slot to show the dialog.
        """
        if not self.__position.isNull():
            self.move(self.__position)
        self.__resetUI()
        
        super(HgLogBrowserDialog, self).show()
    
    def __resetUI(self):
        """
        Private method to reset the user interface.
        """
        self.branchCombo.clear()
        self.fromDate.setDate(QDate.currentDate())
        self.toDate.setDate(QDate.currentDate())
        self.fieldCombo.setCurrentIndex(self.fieldCombo.findData("message"))
        self.limitSpinBox.setValue(self.vcs.getPlugin().getPreferences(
            "LogLimit"))
        self.stopCheckBox.setChecked(self.vcs.getPlugin().getPreferences(
            "StopLogOnCopy"))
        
        if self.initialCommandMode in ("incoming", "outgoing"):
            self.nextButton.setEnabled(False)
            self.limitSpinBox.setEnabled(False)
        else:
            self.nextButton.setEnabled(True)
            self.limitSpinBox.setEnabled(True)
        
        self.logTree.clear()
        
        self.commandMode = self.initialCommandMode
    
    def __resizeColumnsLog(self):
        """
        Private method to resize the log tree columns.
        """
        self.logTree.header().resizeSections(QHeaderView.ResizeToContents)
        self.logTree.header().setStretchLastSection(True)
    
    def __resizeColumnsFiles(self):
        """
        Private method to resize the changed files tree columns.
        """
        self.filesTree.header().resizeSections(QHeaderView.ResizeToContents)
        self.filesTree.header().setStretchLastSection(True)
    
    def __resortFiles(self):
        """
        Private method to resort the changed files tree.
        """
        sortColumn = self.filesTree.sortColumn()
        self.filesTree.sortItems(
            1, self.filesTree.header().sortIndicatorOrder())
        self.filesTree.sortItems(
            sortColumn, self.filesTree.header().sortIndicatorOrder())
    
    def __getColor(self, n):
        """
        Private method to get the (rotating) name of the color given an index.
        
        @param n color index (integer)
        @return color name (string)
        """
        return COLORS[n % len(COLORS)]
    
    def __branchColor(self, branchName):
        """
        Private method to calculate a color for a given branch name.
        
        @param branchName name of the branch (string)
        @return name of the color to use (string)
        """
        if branchName not in self.__branchColors:
            self.__branchColors[branchName] = self.__getColor(
                len(self.__branchColors))
        return self.__branchColors[branchName]
    
    def __generateEdges(self, rev, parents):
        """
        Private method to generate edge info for the give data.
        
        @param rev revision to calculate edge info for (integer)
        @param parents list of parent revisions (list of integers)
        @return tuple containing the column and color index for
            the given node and a list of tuples indicating the edges
            between the given node and its parents
            (integer, integer, [(integer, integer, integer), ...])
        """
        if rev not in self.__revs:
            # new head
            self.__revs.append(rev)
            self.__revColors[rev] = self.__revColor
            self.__revColor += 1
        
        col = self.__revs.index(rev)
        color = self.__revColors.pop(rev)
        next = self.__revs[:]
        
        # add parents to next
        addparents = [p for p in parents if p not in next]
        next[col:col + 1] = addparents
        
        # set colors for the parents
        for i, p in enumerate(addparents):
            if not i:
                self.__revColors[p] = color
            else:
                self.__revColors[p] = self.__revColor
                self.__revColor += 1
        
        # add edges to the graph
        edges = []
        if parents[0] != -1:
            for ecol, erev in enumerate(self.__revs):
                if erev in next:
                    edges.append(
                        (ecol, next.index(erev), self.__revColors[erev]))
                elif erev == rev:
                    for p in parents:
                        edges.append(
                            (ecol, next.index(p), self.__revColors[p]))
        
        self.__revs = next
        return col, color, edges
    
    def __generateIcon(self, column, color, bottomedges, topedges, dotColor,
                       currentRev, closed):
        """
        Private method to generate an icon containing the revision tree for the
        given data.
        
        @param column column index of the revision (integer)
        @param color color of the node (integer)
        @param bottomedges list of edges for the bottom of the node
            (list of tuples of three integers)
        @param topedges list of edges for the top of the node
            (list of tuples of three integers)
        @param dotColor color to be used for the dot (QColor)
        @param currentRev flag indicating to draw the icon for the
            current revision (boolean)
        @param closed flag indicating to draw an icon for a closed
            branch (boolean)
        @return icon for the node (QIcon)
        """
        def col2x(col, radius):
            """
            Local function to calculate a x-position for a column.
            
            @param col column number (integer)
            @param radius radius of the indicator circle (integer)
            """
            return int(1.2 * radius) * col + radius // 2 + 3
        
        radius = self.__dotRadius
        w = len(bottomedges) * radius + 20
        h = self.__rowHeight
        
        dot_x = col2x(column, radius) - radius // 2
        dot_y = h // 2
        
        pix = QPixmap(w, h)
        pix.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(Qt.blue)
        pen.setWidth(2)
        painter.setPen(pen)
        
        lpen = QPen(pen)
        lpen.setColor(Qt.black)
        painter.setPen(lpen)
        
        # draw the revision history lines
        for y1, y2, lines in ((0, h, bottomedges),
                              (-h, 0, topedges)):
            if lines:
                for start, end, ecolor in lines:
                    lpen = QPen(pen)
                    lpen.setColor(QColor(self.__getColor(ecolor)))
                    lpen.setWidth(2)
                    painter.setPen(lpen)
                    x1 = col2x(start, radius)
                    x2 = col2x(end, radius)
                    painter.drawLine(x1, dot_y + y1, x2, dot_y + y2)
        
        penradius = 1
        pencolor = Qt.black
        
        dot_y = (h // 2) - radius // 2
        
        # draw a dot for the revision
        if currentRev:
            # enlarge dot for the current revision
            delta = 1
            radius += 2 * delta
            dot_y -= delta
            dot_x -= delta
            penradius = 3
        painter.setBrush(dotColor)
        pen = QPen(pencolor)
        pen.setWidth(penradius)
        painter.setPen(pen)
        if closed:
            painter.drawRect(dot_x - 2, dot_y + 1,
                             radius + 4, radius - 2)
        elif self.commandMode in ("incoming", "outgoing"):
            offset = radius // 2
            painter.drawConvexPolygon(
                QPoint(dot_x + offset, dot_y),
                QPoint(dot_x, dot_y + offset),
                QPoint(dot_x + offset, dot_y + 2 * offset),
                QPoint(dot_x + 2 * offset, dot_y + offset)
            )
        else:
            painter.drawEllipse(dot_x, dot_y, radius, radius)
        painter.end()
        return QIcon(pix)
    
    def __getParents(self, rev):
        """
        Private method to get the parents of the currently viewed
        file/directory.
        
        @param rev revision number to get parents for (string)
        @return list of parent revisions (list of integers)
        """
        errMsg = ""
        parents = [-1]
        
        if int(rev) > 0:
            args = self.vcs.initCommand("parents")
            if self.commandMode == "incoming":
                if self.__bundle:
                    args.append("--repository")
                    args.append(self.__bundle)
                elif self.vcs.bundleFile and \
                        os.path.exists(self.vcs.bundleFile):
                    args.append("--repository")
                    args.append(self.vcs.bundleFile)
            args.append("--template")
            args.append("{rev}\n")
            args.append("-r")
            args.append(rev)
            if not self.projectMode:
                args.append(self.__filename)
            
            output = ""
            if self.__hgClient:
                output, errMsg = self.__hgClient.runcommand(args)
            else:
                process = QProcess()
                process.setWorkingDirectory(self.repodir)
                process.start('hg', args)
                procStarted = process.waitForStarted(5000)
                if procStarted:
                    finished = process.waitForFinished(30000)
                    if finished and process.exitCode() == 0:
                        output = str(process.readAllStandardOutput(),
                                     self.vcs.getEncoding(), 'replace')
                    else:
                        if not finished:
                            errMsg = self.tr(
                                "The hg process did not finish within 30s.")
                else:
                    errMsg = self.tr("Could not start the hg executable.")
            
            if errMsg:
                E5MessageBox.critical(
                    self,
                    self.tr("Mercurial Error"),
                    errMsg)
            
            if output:
                parents = [int(p) for p in output.strip().splitlines()]
        
        return parents
    
    def __identifyProject(self):
        """
        Private method to determine the revision of the project directory.
        """
        errMsg = ""
        
        args = self.vcs.initCommand("identify")
        args.append("-nb")
        
        output = ""
        if self.__hgClient:
            output, errMsg = self.__hgClient.runcommand(args)
        else:
            process = QProcess()
            process.setWorkingDirectory(self.repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.vcs.getEncoding(), 'replace')
                else:
                    if not finished:
                        errMsg = self.tr(
                            "The hg process did not finish within 30s.")
            else:
                errMsg = self.tr("Could not start the hg executable.")
        
        if errMsg:
            E5MessageBox.critical(
                self,
                self.tr("Mercurial Error"),
                errMsg)
        
        if output:
            outputList = output.strip().split(None, 1)
            if len(outputList) == 2:
                self.__projectRevision = outputList[0].strip()
                if self.__projectRevision.endswith("+"):
                    self.__projectRevision = self.__projectRevision[:-1]
                self.__projectBranch = outputList[1].strip()
    
    def __getClosedBranches(self):
        """
        Private method to get the list of closed branches.
        """
        self.__closedBranchesRevs = []
        errMsg = ""
        
        args = self.vcs.initCommand("branches")
        args.append("--closed")
        
        output = ""
        if self.__hgClient:
            output, errMsg = self.__hgClient.runcommand(args)
        else:
            process = QProcess()
            process.setWorkingDirectory(self.repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.vcs.getEncoding(), 'replace')
                else:
                    if not finished:
                        errMsg = self.tr(
                            "The hg process did not finish within 30s.")
            else:
                errMsg = self.tr("Could not start the hg executable.")
        
        if errMsg:
            E5MessageBox.critical(
                self,
                self.tr("Mercurial Error"),
                errMsg)
        
        if output:
            for line in output.splitlines():
                if line.strip().endswith("(closed)"):
                    parts = line.split()
                    self.__closedBranchesRevs.append(
                        parts[-2].split(":", 1)[0])
    
    def __generateLogItem(self, author, date, message, revision, changedPaths,
                          parents, branches, tags, phase, bookmarks=None):
        """
        Private method to generate a log tree entry.
        
        @param author author info (string)
        @param date date info (string)
        @param message text of the log message (list of strings)
        @param revision revision info (string)
        @param changedPaths list of dictionary objects containing
            info about the changed files/directories
        @param parents list of parent revisions (list of integers)
        @param branches list of branches (list of strings)
        @param tags list of tags (string)
        @param phase phase of the entry (string)
        @param bookmarks list of bookmarks (string)
        @return reference to the generated item (QTreeWidgetItem)
        """
        msg = []
        for line in message:
            msg.append(line.strip())
        
        rev, node = revision.split(":")
        if rev in self.__closedBranchesRevs:
            closedStr = self.ClosedIndicator
        else:
            closedStr = ""
        msgtxt = msg[0]
        if len(msgtxt) > 30:
            msgtxt = "{0}...".format(msgtxt[:30])
        if phase in self.phases:
            phaseStr = self.phases[phase]
        else:
            phaseStr = phase
        columnLabels = [
            "",
            branches[0] + closedStr,
            "{0:>7}:{1}".format(rev, node),
            phaseStr,
            author,
            date,
            msgtxt,
            ", ".join(tags),
        ]
        if bookmarks is not None:
            columnLabels.append(", ".join(bookmarks))
        itm = QTreeWidgetItem(self.logTree, columnLabels)
        
        itm.setForeground(self.BranchColumn,
                          QBrush(QColor(self.__branchColor(branches[0]))))
        
        if not self.projectMode:
            parents = self.__getParents(rev)
        if not parents:
            parents = [int(rev) - 1]
        column, color, edges = self.__generateEdges(int(rev), parents)
        
        itm.setData(0, self.__messageRole, message)
        itm.setData(0, self.__changesRole, changedPaths)
        itm.setData(0, self.__edgesRole, edges)
        if parents == [-1]:
            itm.setData(0, self.__parentsRole, [])
        else:
            itm.setData(0, self.__parentsRole, parents)
        
        if self.logTree.topLevelItemCount() > 1:
            topedges = \
                self.logTree.topLevelItem(
                    self.logTree.indexOfTopLevelItem(itm) - 1)\
                .data(0, self.__edgesRole)
        else:
            topedges = None
        
        icon = self.__generateIcon(column, color, edges, topedges,
                                   QColor(self.__branchColor(branches[0])),
                                   rev == self.__projectRevision,
                                   rev in self.__closedBranchesRevs)
        itm.setIcon(0, icon)
        
        try:
            self.__lastRev = int(revision.split(":")[0])
        except ValueError:
            self.__lastRev = 0
        
        return itm
    
    def __generateFileItem(self, action, path, copyfrom):
        """
        Private method to generate a changed files tree entry.
        
        @param action indicator for the change action ("A", "D" or "M")
        @param path path of the file in the repository (string)
        @param copyfrom path the file was copied from (string)
        @return reference to the generated item (QTreeWidgetItem)
        """
        itm = QTreeWidgetItem(self.filesTree, [
            self.flags[action],
            path,
            copyfrom,
        ])
        
        return itm
    
    def __getLogEntries(self, startRev=None):
        """
        Private method to retrieve log entries from the repository.
        
        @param startRev revision number to start from (integer, string)
        """
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        QApplication.processEvents()
        
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        
        self.buf = []
        self.cancelled = False
        self.errors.clear()
        self.intercept = False
        
        preargs = []
        args = self.vcs.initCommand(self.commandMode)
        args.append('--verbose')
        if self.commandMode not in ("incoming", "outgoing"):
            args.append('--limit')
            args.append(str(self.limitSpinBox.value()))
        if self.commandMode in ("incoming", "outgoing"):
            args.append("--newest-first")
            if self.vcs.hasSubrepositories():
                args.append("--subrepos")
        if startRev is not None:
            args.append('--rev')
            args.append('{0}:0'.format(startRev))
        if not self.projectMode and \
           not self.fname == "." and \
           not self.stopCheckBox.isChecked():
            args.append('--follow')
        if self.commandMode == "log":
            args.append('--copies')
        if self.vcs.version >= (3, 0):
            args.append('--template')
            args.append(os.path.join(os.path.dirname(__file__),
                                     "templates",
                                     "logBrowserBookmarkPhase.tmpl"))
        else:
            args.append('--style')
            if self.vcs.version >= (2, 1):
                args.append(os.path.join(os.path.dirname(__file__),
                                         "styles",
                                         "logBrowserBookmarkPhase.style"))
            else:
                args.append(os.path.join(os.path.dirname(__file__),
                                         "styles",
                                         "logBrowserBookmark.style"))
        if self.commandMode == "incoming":
            if self.__bundle:
                args.append(self.__bundle)
            elif not self.vcs.hasSubrepositories():
                project = e5App().getObject("Project")
                self.vcs.bundleFile = os.path.join(
                    project.getProjectManagementDir(), "hg-bundle.hg")
                if os.path.exists(self.vcs.bundleFile):
                    os.remove(self.vcs.bundleFile)
                preargs = args[:]
                preargs.append("--quiet")
                preargs.append('--bundle')
                preargs.append(self.vcs.bundleFile)
                args.append(self.vcs.bundleFile)
        if not self.projectMode:
            args.append(self.__filename)
        
        if self.__hgClient:
            self.inputGroup.setEnabled(False)
            self.inputGroup.hide()
            
            if preargs:
                out, err = self.__hgClient.runcommand(preargs)
            else:
                err = ""
            if err:
                self.__showError(err)
            elif self.commandMode != "incoming" or \
                (self.vcs.bundleFile and
                 os.path.exists(self.vcs.bundleFile)) or \
                    self.__bundle:
                out, err = self.__hgClient.runcommand(args)
                self.buf = out.splitlines(True)
                if err:
                    self.__showError(err)
                self.__processBuffer()
            self.__finish()
        else:
            self.process.kill()
            
            self.process.setWorkingDirectory(self.repodir)
            
            self.inputGroup.setEnabled(True)
            self.inputGroup.show()
            
            if preargs:
                process = QProcess()
                process.setWorkingDirectory(self.repodir)
                process.start('hg', args)
                procStarted = process.waitForStarted(5000)
                if procStarted:
                    process.waitForFinished(30000)
            
            if self.commandMode != "incoming" or \
                (self.vcs.bundleFile and
                 os.path.exists(self.vcs.bundleFile)) or \
                    self.__bundle:
                self.process.start('hg', args)
                procStarted = self.process.waitForStarted(5000)
                if not procStarted:
                    self.inputGroup.setEnabled(False)
                    self.inputGroup.hide()
                    E5MessageBox.critical(
                        self,
                        self.tr('Process Generation Error'),
                        self.tr(
                            'The process {0} could not be started. '
                            'Ensure, that it is in the search path.'
                        ).format('hg'))
            else:
                self.__finish()
    
    def start(self, fn, bundle=None, isFile=False):
        """
        Public slot to start the hg log command.
        
        @param fn filename to show the log for (string)
        @keyparam bundle name of a bundle file (string)
        @keyparam isFile flag indicating log for a file is to be shown
            (boolean)
        """
        self.__bundle = bundle
        self.__isFile = isFile
        
        self.sbsCheckBox.setEnabled(isFile)
        self.sbsCheckBox.setVisible(isFile)
        
        self.errorGroup.hide()
        QApplication.processEvents()
        
        self.__initData()
        
        self.__filename = fn
        self.dname, self.fname = self.vcs.splitPath(fn)
        
        # find the root of the repo
        self.repodir = self.dname
        while not os.path.isdir(os.path.join(self.repodir, self.vcs.adminDir)):
            self.repodir = os.path.dirname(self.repodir)
            if os.path.splitdrive(self.repodir)[1] == os.sep:
                return
        
        self.projectMode = (self.fname == "." and self.dname == self.repodir)
        self.stopCheckBox.setDisabled(self.projectMode or self.fname == ".")
        self.activateWindow()
        self.raise_()
        
        self.logTree.clear()
        self.__started = True
        self.__identifyProject()
        self.__getClosedBranches()
        self.__getLogEntries()
    
    def __procFinished(self, exitCode, exitStatus):
        """
        Private slot connected to the finished signal.
        
        @param exitCode exit code of the process (integer)
        @param exitStatus exit status of the process (QProcess.ExitStatus)
        """
        self.__processBuffer()
        self.__finish()
    
    def __finish(self):
        """
        Private slot called when the process finished or the user pressed
        the button.
        """
        if self.process is not None and \
           self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            QTimer.singleShot(2000, self.process.kill)
            self.process.waitForFinished(3000)
        
        QApplication.restoreOverrideCursor()
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.inputGroup.setEnabled(False)
        self.inputGroup.hide()
        self.refreshButton.setEnabled(True)
    
    def __modifyForLargeFiles(self, filename):
        """
        Private method to convert the displayed file name for a large file.
        
        @param filename file name to be processed (string)
        @return processed file name (string)
        """
        if filename.startswith((self.LargefilesCacheL, self.LargefilesCacheW)):
            return self.tr("{0} (large file)").format(
                self.PathSeparatorRe.split(filename, 1)[1])
        else:
            return filename
    
    def __processBuffer(self):
        """
        Private method to process the buffered output of the hg log command.
        """
        noEntries = 0
        log = {"message": [], "bookmarks": None, "phase": ""}
        changedPaths = []
        initialText = True
        fileCopies = {}
        for s in self.buf:
            if s != "@@@\n":
                try:
                    key, value = s.split("|", 1)
                except ValueError:
                    key = ""
                    value = s
                if key == "change":
                    initialText = False
                    log["revision"] = value.strip()
                elif key == "user":
                    log["author"] = value.strip()
                elif key == "parents":
                    log["parents"] = \
                        [int(x.split(":", 1)[0])
                         for x in value.strip().split()]
                elif key == "date":
                    log["date"] = " ".join(value.strip().split()[:2])
                elif key == "description":
                    log["message"].append(value.strip())
                elif key == "file_adds":
                    if value.strip():
                        for f in value.strip().split(", "):
                            if f in fileCopies:
                                changedPaths.append({
                                    "action": "A",
                                    "path": self.__modifyForLargeFiles(f),
                                    "copyfrom": self.__modifyForLargeFiles(
                                        fileCopies[f]),
                                })
                            else:
                                changedPaths.append({
                                    "action": "A",
                                    "path": self.__modifyForLargeFiles(f),
                                    "copyfrom": "",
                                })
                elif key == "files_mods":
                    if value.strip():
                        for f in value.strip().split(", "):
                            changedPaths.append({
                                "action": "M",
                                "path": self.__modifyForLargeFiles(f),
                                "copyfrom": "",
                            })
                elif key == "file_dels":
                    if value.strip():
                        for f in value.strip().split(", "):
                            changedPaths.append({
                                "action": "D",
                                "path": self.__modifyForLargeFiles(f),
                                "copyfrom": "",
                            })
                elif key == "file_copies":
                    if value.strip():
                        for entry in value.strip().split(", "):
                            newName, oldName = entry[:-1].split(" (")
                            fileCopies[newName] = oldName
                elif key == "branches":
                    if value.strip():
                        log["branches"] = value.strip().split(", ")
                    else:
                        log["branches"] = ["default"]
                elif key == "tags":
                    log["tags"] = value.strip().split(", ")
                elif key == "bookmarks":
                    log["bookmarks"] = value.strip().split(", ")
                elif key == "phase":
                    log["phase"] = value.strip()
                else:
                    if initialText:
                        continue
                    if value.strip():
                        log["message"].append(value.strip())
            else:
                if len(log) > 1:
                    self.__generateLogItem(
                        log["author"], log["date"],
                        log["message"], log["revision"], changedPaths,
                        log["parents"], log["branches"], log["tags"],
                        log["phase"], log["bookmarks"])
                    dt = QDate.fromString(log["date"], Qt.ISODate)
                    if not self.__maxDate.isValid() and \
                       not self.__minDate.isValid():
                        self.__maxDate = dt
                        self.__minDate = dt
                    else:
                        if self.__maxDate < dt:
                            self.__maxDate = dt
                        if self.__minDate > dt:
                            self.__minDate = dt
                    noEntries += 1
                    log = {"message": [], "bookmarks": None, "phase": ""}
                    changedPaths = []
                    fileCopies = {}
        
        self.__resizeColumnsLog()
        
        if self.__started:
            self.logTree.setCurrentItem(self.logTree.topLevelItem(0))
            self.__started = False
        
        if self.commandMode in ("incoming", "outgoing"):
            self.commandMode = "log"    # switch to log mode
            if self.__lastRev > 0:
                self.nextButton.setEnabled(True)
                self.limitSpinBox.setEnabled(True)
        else:
            if noEntries < self.limitSpinBox.value() and not self.cancelled:
                self.nextButton.setEnabled(False)
                self.limitSpinBox.setEnabled(False)
        
        # update the log filters
        self.__filterLogsEnabled = False
        self.fromDate.setMinimumDate(self.__minDate)
        self.fromDate.setMaximumDate(self.__maxDate)
        self.fromDate.setDate(self.__minDate)
        self.toDate.setMinimumDate(self.__minDate)
        self.toDate.setMaximumDate(self.__maxDate)
        self.toDate.setDate(self.__maxDate)
        
        branchFilter = self.branchCombo.currentText()
        if not branchFilter:
            branchFilter = self.__allBranchesFilter
        self.branchCombo.clear()
        self.branchCombo.addItems(
            [self.__allBranchesFilter] + sorted(self.__branchColors.keys()))
        self.branchCombo.setCurrentIndex(
            self.branchCombo.findText(branchFilter))
        
        self.__filterLogsEnabled = True
        if self.__actionMode() == "filter":
            self.__filterLogs()
        self.__updateDiffButtons()
        self.__updateToolMenuActions()
        
        # restore current item
        if self.__currentRevision:
            items = self.logTree.findItems(
                self.__currentRevision, Qt.MatchExactly, self.RevisionColumn)
            if items:
                self.logTree.setCurrentItem(items[0])
                self.__currentRevision = ""
    
    def __readStdout(self):
        """
        Private slot to handle the readyReadStandardOutput signal.
        
        It reads the output of the process and inserts it into a buffer.
        """
        self.process.setReadChannel(QProcess.StandardOutput)
        
        while self.process.canReadLine():
            line = str(self.process.readLine(), self.vcs.getEncoding(),
                       'replace')
            self.buf.append(line)
    
    def __readStderr(self):
        """
        Private slot to handle the readyReadStandardError signal.
        
        It reads the error output of the process and inserts it into the
        error pane.
        """
        if self.process is not None:
            s = str(self.process.readAllStandardError(),
                    self.vcs.getEncoding(), 'replace')
            self.__showError(s)
    
    def __showError(self, out):
        """
        Private slot to show some error.
        
        @param out error to be shown (string)
        """
        self.errorGroup.show()
        self.errors.insertPlainText(out)
        self.errors.ensureCursorVisible()
    
    def __diffRevisions(self, rev1, rev2):
        """
        Private method to do a diff of two revisions.
        
        @param rev1 first revision number (integer)
        @param rev2 second revision number (integer)
        """
        if self.sbsCheckBox.isEnabled() and self.sbsCheckBox.isChecked():
            self.vcs.hgSbsDiff(self.__filename,
                               revisions=(str(rev1), str(rev2)))
        else:
            if self.diff is None:
                from .HgDiffDialog import HgDiffDialog
                self.diff = HgDiffDialog(self.vcs)
            self.diff.show()
            self.diff.raise_()
            self.diff.start(self.__filename, [rev1, rev2], self.__bundle)
    
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.cancelled = True
            if self.__hgClient:
                self.__hgClient.cancel()
            else:
                self.__finish()
        elif button == self.refreshButton:
            self.on_refreshButton_clicked()
    
    def __updateDiffButtons(self):
        """
        Private slot to update the enabled status of the diff buttons.
        """
        selectionLength = len(self.logTree.selectedItems())
        if selectionLength <= 1:
            current = self.logTree.currentItem()
            if current is None:
                self.diffP1Button.setEnabled(False)
                self.diffP2Button.setEnabled(False)
            else:
                parents = current.data(0, self.__parentsRole)
                self.diffP1Button.setEnabled(len(parents) > 0)
                self.diffP2Button.setEnabled(len(parents) > 1)
            
            self.diffRevisionsButton.setEnabled(False)
        elif selectionLength == 2:
            self.diffP1Button.setEnabled(False)
            self.diffP2Button.setEnabled(False)
            
            self.diffRevisionsButton.setEnabled(True)
        else:
            self.diffP1Button.setEnabled(False)
            self.diffP2Button.setEnabled(False)
            
            self.diffRevisionsButton.setEnabled(False)
    
    def __updateToolMenuActions(self):
        """
        Private slot to update the status of the tool menu actions and
        the tool menu button.
        """
        if self.initialCommandMode == "log" and self.projectMode:
            if self.__phaseAct is not None:
                # step 1: count entries with changeable phases
                secret = 0
                draft = 0
                public = 0
                for itm in self.logTree.selectedItems():
                    phase = itm.text(self.PhaseColumn)
                    if phase == self.phases["draft"]:
                        draft += 1
                    elif phase == self.phases["secret"]:
                        secret += 1
                    else:
                        public += 1
                
                # step 2: set the status of the phase button
                if public == 0 and \
                   ((secret > 0 and draft == 0) or
                        (secret == 0 and draft > 0)):
                    self.__phaseAct.setEnabled(True)
                else:
                    self.__phaseAct.setEnabled(False)
            
            if self.__graftAct is not None:
                # step 1: count selected entries not belonging to the
                #         current branch
                otherBranches = 0
                for itm in self.logTree.selectedItems():
                    branch = itm.text(self.BranchColumn)
                    if branch != self.__projectBranch:
                        otherBranches += 1
                
                # step 2: set the status of the graft action
                self.__graftAct.setEnabled(otherBranches > 0)
            
            self.__tagAct.setEnabled(len(self.logTree.selectedItems()) == 1)
            self.__switchAct.setEnabled(len(self.logTree.selectedItems()) == 1)
            
            if self.__lfPullAct is not None:
                if self.vcs.isExtensionActive("largefiles"):
                    self.__lfPullAct.setEnabled(bool(
                        self.logTree.selectedItems()))
                else:
                    self.__lfPullAct.setEnabled(False)
            
            self.__pushAct.setEnabled(
                len(self.logTree.selectedItems()) == 1 and
                self.logTree.selectedItems()[0].text(self.PhaseColumn) ==
                self.phases["draft"])
            
            self.actionsButton.setEnabled(True)
        else:
            self.actionsButton.setEnabled(False)
    
    def __updateGui(self, itm):
        """
        Private slot to update GUI elements except tool menu actions.
        
        @param itm reference to the item the update should be based on
            (QTreeWidgetItem)
        """
        self.detailsEdit.clear()
        self.messageEdit.clear()
        self.filesTree.clear()
        
        if itm is not None:
            if itm.text(self.TagsColumn):
                tagsStr = self.__tagsTemplate.format(itm.text(self.TagsColumn))
            else:
                tagsStr = ""
            if itm.text(self.BookmarksColumn):
                bookmarksStr = self.__bookmarksTemplate.format(
                    itm.text(self.BookmarksColumn))
            else:
                bookmarksStr = ""
            self.detailsEdit.setHtml(self.__detailsTemplate.format(
                itm.text(self.RevisionColumn),
                itm.text(self.DateColumn),
                itm.text(self.AuthorColumn),
                itm.text(self.BranchColumn).replace(
                    self.ClosedIndicator, ""),
                ", ".join(
                    [str(x) for x in itm.data(0, self.__parentsRole)]
                ),
                tagsStr + bookmarksStr,
            ))
            
            for line in itm.data(0, self.__messageRole):
                self.messageEdit.append(line.strip())
            
            changes = itm.data(0, self.__changesRole)
            if len(changes) > 0:
                for change in changes:
                    self.__generateFileItem(
                        change["action"], change["path"], change["copyfrom"])
                self.__resizeColumnsFiles()
                self.__resortFiles()
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_logTree_currentItemChanged(self, current, previous):
        """
        Private slot called, when the current item of the log tree changes.
        
        @param current reference to the new current item (QTreeWidgetItem)
        @param previous reference to the old current item (QTreeWidgetItem)
        """
        self.__updateGui(current)
        self.__updateDiffButtons()
        self.__updateToolMenuActions()
    
    @pyqtSlot()
    def on_logTree_itemSelectionChanged(self):
        """
        Private slot called, when the selection has changed.
        """
        if len(self.logTree.selectedItems()) == 1:
            self.__updateGui(self.logTree.selectedItems()[0])
        
        self.__updateDiffButtons()
        self.__updateToolMenuActions()
    
    @pyqtSlot()
    def on_nextButton_clicked(self):
        """
        Private slot to handle the Next button.
        """
        if self.__lastRev > 0:
            self.__getLogEntries(self.__lastRev - 1)
    
    @pyqtSlot()
    def on_diffP1Button_clicked(self):
        """
        Private slot to handle the Diff to Parent 1 button.
        """
        if len(self.logTree.selectedItems()):
            itm = self.logTree.selectedItems()[0]
        else:
            itm = self.logTree.currentItem()
        if itm is None:
            self.diffP1Button.setEnabled(False)
            return
        rev2 = int(itm.text(self.RevisionColumn).split(":")[0])
        
        rev1 = itm.data(0, self.__parentsRole)[0]
        if rev1 < 0:
            self.diffP1Button.setEnabled(False)
            return
        
        self.__diffRevisions(rev1, rev2)
    
    @pyqtSlot()
    def on_diffP2Button_clicked(self):
        """
        Private slot to handle the Diff to Parent 2 button.
        """
        if len(self.logTree.selectedItems()):
            itm = self.logTree.selectedItems()[0]
        else:
            itm = self.logTree.currentItem()
        if itm is None:
            self.diffP2Button.setEnabled(False)
            return
        rev2 = int(itm.text(self.RevisionColumn).split(":")[0])
        
        rev1 = itm.data(0, self.__parentsRole)[1]
        if rev1 < 0:
            self.diffP2Button.setEnabled(False)
            return
        
        self.__diffRevisions(rev1, rev2)
    
    @pyqtSlot()
    def on_diffRevisionsButton_clicked(self):
        """
        Private slot to handle the Compare Revisions button.
        """
        items = self.logTree.selectedItems()
        
        rev2 = int(items[0].text(self.RevisionColumn).split(":")[0])
        rev1 = int(items[1].text(self.RevisionColumn).split(":")[0])
        
        self.__diffRevisions(min(rev1, rev2), max(rev1, rev2))
    
    @pyqtSlot(QDate)
    def on_fromDate_dateChanged(self, date):
        """
        Private slot called, when the from date changes.
        
        @param date new date (QDate)
        """
        if self.__actionMode() == "filter":
            self.__filterLogs()
    
    @pyqtSlot(QDate)
    def on_toDate_dateChanged(self, date):
        """
        Private slot called, when the from date changes.
        
        @param date new date (QDate)
        """
        if self.__actionMode() == "filter":
            self.__filterLogs()
    
    @pyqtSlot(str)
    def on_branchCombo_activated(self, txt):
        """
        Private slot called, when a new branch is selected.
        
        @param txt text of the selected branch (string)
        """
        if self.__actionMode() == "filter":
            self.__filterLogs()
    
    @pyqtSlot(str)
    def on_fieldCombo_activated(self, txt):
        """
        Private slot called, when a new filter field is selected.
        
        @param txt text of the selected field (string)
        """
        if self.__actionMode() == "filter":
            self.__filterLogs()
    
    @pyqtSlot(str)
    def on_rxEdit_textChanged(self, txt):
        """
        Private slot called, when a filter expression is entered.
        
        @param txt filter expression (string)
        """
        if self.__actionMode() == "filter":
            self.__filterLogs()
        elif self.__actionMode() == "find":
            self.__findItem(self.__findBackwards, interactive=True)
    
    @pyqtSlot()
    def on_rxEdit_returnPressed(self):
        """
        Private slot handling a press of the Return key in the rxEdit input.
        """
        if self.__actionMode() == "find":
            self.__findItem(self.__findBackwards, interactive=True)
    
    def __filterLogs(self):
        """
        Private method to filter the log entries.
        """
        if self.__filterLogsEnabled:
            from_ = self.fromDate.date().toString("yyyy-MM-dd")
            to_ = self.toDate.date().addDays(1).toString("yyyy-MM-dd")
            branch = self.branchCombo.currentText()
            closedBranch = branch + '--'
            fieldIndex, searchRx, indexIsRole = self.__prepareFieldSearch()
            
            visibleItemCount = self.logTree.topLevelItemCount()
            currentItem = self.logTree.currentItem()
            for topIndex in range(self.logTree.topLevelItemCount()):
                topItem = self.logTree.topLevelItem(topIndex)
                if indexIsRole:
                    if fieldIndex == self.__changesRole:
                        changes = topItem.data(0, self.__changesRole)
                        txt = "\n".join(
                            [c["path"] for c in changes] +
                            [c["copyfrom"] for c in changes]
                        )
                    else:
                        # Find based on complete message text
                        txt = "\n".join(topItem.data(0, self.__messageRole))
                else:
                    txt = topItem.text(fieldIndex)
                if topItem.text(self.DateColumn) <= to_ and \
                   topItem.text(self.DateColumn) >= from_ and \
                   (branch == self.__allBranchesFilter or
                    topItem.text(self.BranchColumn) in
                        [branch, closedBranch]) and \
                   searchRx.indexIn(txt) > -1:
                    topItem.setHidden(False)
                    if topItem is currentItem:
                        self.on_logTree_currentItemChanged(topItem, None)
                else:
                    topItem.setHidden(True)
                    if topItem is currentItem:
                        self.messageEdit.clear()
                        self.filesTree.clear()
                    visibleItemCount -= 1
            self.logTree.header().setSectionHidden(
                self.IconColumn,
                visibleItemCount != self.logTree.topLevelItemCount())
    
    def __prepareFieldSearch(self):
        """
        Private slot to prepare the filed search data.
        
        @return tuple of field index, search expression and flag indicating
            that the field index is a data role (integer, string, boolean)
        """
        indexIsRole = False
        txt = self.fieldCombo.itemData(self.fieldCombo.currentIndex())
        if txt == "author":
            fieldIndex = self.AuthorColumn
            searchRx = QRegExp(self.rxEdit.text(), Qt.CaseInsensitive)
        elif txt == "revision":
            fieldIndex = self.RevisionColumn
            txt = self.rxEdit.text()
            if txt.startswith("^"):
                searchRx = QRegExp("^\s*{0}".format(txt[1:]),
                                   Qt.CaseInsensitive)
            else:
                searchRx = QRegExp(txt, Qt.CaseInsensitive)
        elif txt == "file":
            fieldIndex = self.__changesRole
            searchRx = QRegExp(self.rxEdit.text(), Qt.CaseInsensitive)
            indexIsRole = True
        else:
            fieldIndex = self.__messageRole
            searchRx = QRegExp(self.rxEdit.text(), Qt.CaseInsensitive)
            indexIsRole = True
        
        return fieldIndex, searchRx, indexIsRole
    
    @pyqtSlot(bool)
    def on_stopCheckBox_clicked(self, checked):
        """
        Private slot called, when the stop on copy/move checkbox is clicked.
        
        @param checked flag indicating the state of the check box (boolean)
        """
        self.vcs.getPlugin().setPreferences("StopLogOnCopy",
                                            self.stopCheckBox.isChecked())
        self.nextButton.setEnabled(True)
        self.limitSpinBox.setEnabled(True)
    
    @pyqtSlot()
    def on_refreshButton_clicked(self):
        """
        Private slot to refresh the log.
        """
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.inputGroup.setEnabled(True)
        self.inputGroup.show()
        self.refreshButton.setEnabled(False)
        
        # save the current items commit ID
        itm = self.logTree.currentItem()
        if itm is not None:
            self.__currentRevision = itm.text(self.RevisionColumn)
        else:
            self.__currentRevision = ""
        
        if self.initialCommandMode in ("incoming", "outgoing"):
            self.nextButton.setEnabled(False)
            self.limitSpinBox.setEnabled(False)
        else:
            self.nextButton.setEnabled(True)
            self.limitSpinBox.setEnabled(True)
        
        self.commandMode = self.initialCommandMode
        self.start(self.__filename, isFile=self.__isFile)
    
    def on_passwordCheckBox_toggled(self, isOn):
        """
        Private slot to handle the password checkbox toggled.
        
        @param isOn flag indicating the status of the check box (boolean)
        """
        if isOn:
            self.input.setEchoMode(QLineEdit.Password)
        else:
            self.input.setEchoMode(QLineEdit.Normal)
    
    @pyqtSlot()
    def on_sendButton_clicked(self):
        """
        Private slot to send the input to the mercurial process.
        """
        input = self.input.text()
        input += os.linesep
        
        if self.passwordCheckBox.isChecked():
            self.errors.insertPlainText(os.linesep)
            self.errors.ensureCursorVisible()
        else:
            self.errors.insertPlainText(input)
            self.errors.ensureCursorVisible()
        self.errorGroup.show()
        
        self.process.write(input)
        
        self.passwordCheckBox.setChecked(False)
        self.input.clear()
    
    def on_input_returnPressed(self):
        """
        Private slot to handle the press of the return key in the input field.
        """
        self.intercept = True
        self.on_sendButton_clicked()
    
    def keyPressEvent(self, evt):
        """
        Protected slot to handle a key press event.
        
        @param evt the key press event (QKeyEvent)
        """
        if self.intercept:
            self.intercept = False
            evt.accept()
            return
        super(HgLogBrowserDialog, self).keyPressEvent(evt)
    
    @pyqtSlot()
    def __phaseActTriggered(self):
        """
        Private slot to handle the Change Phase action.
        """
        currentPhase = self.logTree.selectedItems()[0].text(self.PhaseColumn)
        revs = []
        for itm in self.logTree.selectedItems():
            if itm.text(self.PhaseColumn) == currentPhase:
                revs.append(
                    itm.text(self.RevisionColumn).split(":")[0].strip())
        
        if not revs:
            self.__phaseAct.setEnabled(False)
            return
        
        if currentPhase == self.phases["draft"]:
            newPhase = self.phases["secret"]
            data = (revs, "s", True)
        else:
            newPhase = self.phases["draft"]
            data = (revs, "d", False)
        res = self.vcs.hgPhase(self.repodir, data)
        if res:
            for itm in self.logTree.selectedItems():
                itm.setText(self.PhaseColumn, newPhase)
    
    @pyqtSlot()
    def __graftActTriggered(self):
        """
        Private slot to handle the Copy Changesets action.
        """
        revs = []
        
        for itm in self.logTree.selectedItems():
            branch = itm.text(self.BranchColumn)
            if branch != self.__projectBranch:
                revs.append(
                    itm.text(self.RevisionColumn).strip().split(":", 1)[0])
        
        if revs:
            shouldReopen = self.vcs.hgGraft(self.repodir, revs)
            if shouldReopen:
                res = E5MessageBox.yesNo(
                    None,
                    self.tr("Copy Changesets"),
                    self.tr(
                        """The project should be reread. Do this now?"""),
                    yesDefault=True)
                if res:
                    e5App().getObject("Project").reopenProject()
                    return
            
            self.on_refreshButton_clicked()
    
    @pyqtSlot()
    def __tagActTriggered(self):
        """
        Private slot to tag the selected revision.
        """
        if len(self.logTree.selectedItems()) == 1:
            itm = self.logTree.selectedItems()[0]
            rev = itm.text(self.RevisionColumn).strip().split(":", 1)[0]
            tag = itm.text(self.TagsColumn).strip().split(", ", 1)[0]
            res = self.vcs.vcsTag(self.repodir, revision=rev, tagName=tag)
            if res:
                self.on_refreshButton_clicked()
    
    @pyqtSlot()
    def __switchActTriggered(self):
        """
        Private slot to switch the working directory to the
        selected revision.
        """
        if len(self.logTree.selectedItems()) == 1:
            itm = self.logTree.selectedItems()[0]
            rev = itm.text(self.RevisionColumn).strip().split(":", 1)[0]
            if rev:
                shouldReopen = self.vcs.vcsUpdate(self.repodir, revision=rev)
                if shouldReopen:
                    res = E5MessageBox.yesNo(
                        None,
                        self.tr("Switch"),
                        self.tr(
                            """The project should be reread. Do this now?"""),
                        yesDefault=True)
                    if res:
                        e5App().getObject("Project").reopenProject()
                        return
                
                self.on_refreshButton_clicked()
    
    @pyqtSlot()
    def __lfPullActTriggered(self):
        """
        Private slot to pull large files of selected revisions.
        """
        revs = []
        for itm in self.logTree.selectedItems():
            rev = itm.text(self.RevisionColumn).strip().split(":", 1)[0]
            if rev:
                revs.append(rev)
        
        if revs:
            self.vcs.getExtensionObject("largefiles").hgLfPull(
                self.repodir, revisions=revs)
    
    @pyqtSlot()
    def __pullActTriggered(self):
        """
        Private slot to pull changes from a remote repository.
        """
        self.vcs.hgPull(self.repodir)
        self.on_refreshButton_clicked()
    
    @pyqtSlot()
    def __pushActTriggered(self):
        """
        Private slot to push changes to a remote repository up to a selected
        changeset.
        """
        itm = self.logTree.selectedItems()[0]
        rev = itm.text(self.RevisionColumn).strip().split(":", 1)[0]
        if rev:
            self.vcs.hgPush(self.repodir, rev=rev)
            self.on_refreshButton_clicked()
    
    @pyqtSlot()
    def __pushAllActTriggered(self):
        """
        Private slot to push all changes to a remote repository.
        """
        self.vcs.hgPush(self.repodir)
        self.on_refreshButton_clicked()
    
    def __actionMode(self):
        """
        Private method to get the selected action mode.
        
        @return selected action mode (string, one of filter or find)
        """
        return self.modeComboBox.itemData(
            self.modeComboBox.currentIndex())
    
    @pyqtSlot(int)
    def on_modeComboBox_currentIndexChanged(self, index):
        """
        Private slot to react on mode changes.
        
        @param index index of the selected entry (integer)
        """
        mode = self.modeComboBox.itemData(index)
        findMode = mode == "find"
        filterMode = mode == "filter"
        
        self.fromDate.setEnabled(filterMode)
        self.toDate.setEnabled(filterMode)
        self.branchCombo.setEnabled(filterMode)
        self.findPrevButton.setVisible(findMode)
        self.findNextButton.setVisible(findMode)
        
        if findMode:
            for topIndex in range(self.logTree.topLevelItemCount()):
                self.logTree.topLevelItem(topIndex).setHidden(False)
            self.logTree.header().setSectionHidden(self.IconColumn, False)
        elif filterMode:
            self.__filterLogs()
    
    @pyqtSlot()
    def on_findPrevButton_clicked(self):
        """
        Private slot to find the previous item matching the entered criteria.
        """
        self.__findItem(True)
    
    @pyqtSlot()
    def on_findNextButton_clicked(self):
        """
        Private slot to find the next item matching the entered criteria.
        """
        self.__findItem(False)
    
    def __findItem(self, backwards=False, interactive=False):
        """
        Private slot to find an item matching the entered criteria.
        
        @param backwards flag indicating to search backwards (boolean)
        @param interactive flag indicating an interactive search (boolean)
        """
        self.__findBackwards = backwards
        
        fieldIndex, searchRx, indexIsRole = self.__prepareFieldSearch()
        currentIndex = self.logTree.indexOfTopLevelItem(
            self.logTree.currentItem())
        if backwards:
            if interactive:
                indexes = range(currentIndex, -1, -1)
            else:
                indexes = range(currentIndex - 1, -1, -1)
        else:
            if interactive:
                indexes = range(currentIndex, self.logTree.topLevelItemCount())
            else:
                indexes = range(currentIndex + 1,
                                self.logTree.topLevelItemCount())
        
        for index in indexes:
            topItem = self.logTree.topLevelItem(index)
            if indexIsRole:
                if fieldIndex == self.__changesRole:
                    changes = topItem.data(0, self.__changesRole)
                    txt = "\n".join(
                        [c["path"] for c in changes] +
                        [c["copyfrom"] for c in changes]
                    )
                else:
                    # Find based on complete message text
                    txt = "\n".join(topItem.data(0, self.__messageRole))
            else:
                txt = topItem.text(fieldIndex)
            if searchRx.indexIn(txt) > -1:
                self.logTree.setCurrentItem(self.logTree.topLevelItem(index))
                break
        else:
            E5MessageBox.information(
                self,
                self.tr("Find Commit"),
                self.tr("""'{0}' was not found.""").format(self.rxEdit.text()))
