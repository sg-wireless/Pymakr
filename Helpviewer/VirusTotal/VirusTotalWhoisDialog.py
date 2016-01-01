# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the 'whois' information.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_VirusTotalWhoisDialog import Ui_VirusTotalWhoisDialog

import UI.PixmapCache


class VirusTotalWhoisDialog(QDialog, Ui_VirusTotalWhoisDialog):
    """
    Class implementing a dialog to show the 'whois' information.
    """
    def __init__(self, domain, whois, parent=None):
        """
        Constructor
        
        @param domain domain name
        @type str
        @param whois whois information
        @type str
        @param parent reference to the parent widget
        @type QWidget
        """
        super(VirusTotalWhoisDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.headerLabel.setText(
            self.tr("<b>Whois information for domain {0}</b>").format(domain))
        self.headerPixmap.setPixmap(
            UI.PixmapCache.getPixmap("virustotal.png"))
        self.whoisEdit.setPlainText(whois)
