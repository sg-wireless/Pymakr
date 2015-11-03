# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog used by the queue management functions.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

from PyQt5.QtCore import pyqtSlot, Qt, QProcess, QCoreApplication
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QAbstractItemView, \
    QListWidgetItem, QAbstractButton

from .Ui_HgQueuesQueueManagementDialog import Ui_HgQueuesQueueManagementDialog


class HgQueuesQueueManagementDialog(QDialog, Ui_HgQueuesQueueManagementDialog):
    """
    Class implementing a dialog used by the queue management functions.
    """
    NO_INPUT = 0
    NAME_INPUT = 1
    QUEUE_INPUT = 2
    
    def __init__(self, mode, title, suppressActive, repodir, vcs, parent=None):
        """
        Constructor
        
        @param mode mode of the dialog (HgQueuesQueueManagementDialog.NO_INPUT
            HgQueuesQueueManagementDialog.NAME_INPUT,
            HgQueuesQueueManagementDialog.QUEUE_INPUT)
        @param title title for the dialog (string)
        @param suppressActive flag indicating to not show the name of the
            active queue (boolean)
        @param repodir name of the repository directory (string)
        @param vcs reference to the vcs object
        @param parent reference to the parent widget (QWidget)
        @exception ValueError raised to indicate an invalid dialog mode
        """
        super(HgQueuesQueueManagementDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        if mode not in (HgQueuesQueueManagementDialog.NO_INPUT,
                        HgQueuesQueueManagementDialog.NAME_INPUT,
                        HgQueuesQueueManagementDialog.QUEUE_INPUT):
            raise ValueError("illegal value for mode")
        
        self.__mode = mode
        self.__repodir = repodir
        self.__suppressActive = suppressActive
        self.__hgClient = vcs.getClient()
        self.vcs = vcs
        
        self.inputFrame.setHidden(
            mode != HgQueuesQueueManagementDialog.NAME_INPUT)
        self.selectLabel.setHidden(
            mode != HgQueuesQueueManagementDialog.QUEUE_INPUT)
        if mode != HgQueuesQueueManagementDialog.QUEUE_INPUT:
            self.queuesList.setSelectionMode(QAbstractItemView.NoSelection)
        
        if mode == HgQueuesQueueManagementDialog.NO_INPUT:
            self.buttonBox.removeButton(
                self.buttonBox.button(QDialogButtonBox.Ok))
            self.buttonBox.removeButton(
                self.buttonBox.button(QDialogButtonBox.Cancel))
            self.refreshButton = self.buttonBox.addButton(
                self.tr("Refresh"), QDialogButtonBox.ActionRole)
            self.refreshButton.setToolTip(
                self.tr("Press to refresh the queues list"))
            self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        else:
            self.buttonBox.removeButton(
                self.buttonBox.button(QDialogButtonBox.Close))
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
            self.refreshButton = None
        
        self.setWindowTitle(title)
        
        self.show()
        QCoreApplication.processEvents()
        
        self.refresh()
    
    def __getQueuesList(self):
        """
        Private method to get a list of all queues and the name of the active
        queue.
        
        @return tuple with a list of all queues and the name of the active
            queue (list of strings, string)
        """
        queuesList = []
        activeQueue = ""
        
        args = self.vcs.initCommand("qqueue")
        args.append("--list")
        
        output = ""
        if self.__hgClient:
            output = self.__hgClient.runcommand(args)[0]
        else:
            process = QProcess()
            process.setWorkingDirectory(self.__repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.vcs.getEncoding(), 'replace')
        
        for queue in output.splitlines():
            queue = queue.strip()
            if queue.endswith(")"):
                queue = queue.rsplit(None, 1)[0]
                activeQueue = queue
            queuesList.append(queue)
        
        if self.__suppressActive:
            if activeQueue in queuesList:
                queuesList.remove(activeQueue)
            activeQueue = ""
        return queuesList, activeQueue
    
    @pyqtSlot(str)
    def on_nameEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the entered queue name.
        
        @param txt text of the edit (string)
        """
        if self.__mode == HgQueuesQueueManagementDialog.NAME_INPUT:
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(txt != "")
    
    @pyqtSlot()
    def on_queuesList_itemSelectionChanged(self):
        """
        Private slot to handle changes of selected queue names.
        """
        if self.__mode == HgQueuesQueueManagementDialog.QUEUE_INPUT:
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
                len(self.queuesList.selectedItems()) > 0)
    
    @pyqtSlot(QAbstractButton)
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.refreshButton:
            self.refresh()
        elif button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
    
    def refresh(self):
        """
        Public slot to refresh the list of queues.
        """
        self.queuesList.clear()
        queuesList, activeQueue = self.__getQueuesList()
        for queue in sorted(queuesList):
            itm = QListWidgetItem(queue, self.queuesList)
            if queue == activeQueue:
                font = itm.font()
                font.setBold(True)
                itm.setFont(font)
    
    def getData(self):
        """
        Public slot to get the data.
        
        @return queue name (string)
        """
        name = ""
        if self.__mode == HgQueuesQueueManagementDialog.NAME_INPUT:
            name = self.nameEdit.text().replace(" ", "_")
        elif self.__mode == HgQueuesQueueManagementDialog.QUEUE_INPUT:
            selItems = self.queuesList.selectedItems()
            if selItems:
                name = selItems[0].text()
        return name
