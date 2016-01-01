# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the VirusTotal IP address report.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QTreeWidgetItem

from .Ui_VirusTotalIpReportDialog import Ui_VirusTotalIpReportDialog

import UI.PixmapCache


class VirusTotalIpReportDialog(QDialog, Ui_VirusTotalIpReportDialog):
    """
    Class implementing a dialog to show the VirusTotal IP address report.
    """
    def __init__(self, ip, owner, resolutions, urls, parent=None):
        """
        Constructor
        
        @param ip IP address
        @type str
        @param owner owner of the IP address
        @type str
        @param resolutions list of resolved host names
        @type list of dict
        @param urls list of detected URLs
        @type list of dict
        @param parent reference to the parent widget
        @type QWidget
        """
        super(VirusTotalIpReportDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.headerLabel.setText(
            self.tr("<b>Report for IP {0}</b>").format(ip))
        self.headerPixmap.setPixmap(
            UI.PixmapCache.getPixmap("virustotal.png"))
        self.ownerLabel.setText(owner)
        
        for resolution in resolutions:
            QTreeWidgetItem(
                self.resolutionsList,
                [resolution["hostname"],
                 resolution["last_resolved"].split()[0]]
            )
        self.resolutionsList.resizeColumnToContents(0)
        self.resolutionsList.resizeColumnToContents(1)
        self.resolutionsList.sortByColumn(0, Qt.AscendingOrder)
        
        if not urls:
            self.detectedUrlsGroup.setVisible(False)
        for url in urls:
            QTreeWidgetItem(
                self.urlsList,
                [url["url"],
                 self.tr("{0}/{1}", "positives / total").format(
                    url["positives"], url["total"]),
                 url["scan_date"].split()[0]]
            )
        self.urlsList.resizeColumnToContents(0)
        self.urlsList.resizeColumnToContents(1)
        self.urlsList.resizeColumnToContents(2)
        self.urlsList.sortByColumn(0, Qt.AscendingOrder)
