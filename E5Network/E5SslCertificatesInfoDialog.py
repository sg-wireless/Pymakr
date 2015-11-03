# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show SSL certificate infos.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_E5SslCertificatesInfoDialog import Ui_E5SslCertificatesInfoDialog


class E5SslCertificatesInfoDialog(QDialog, Ui_E5SslCertificatesInfoDialog):
    """
    Class implementing a dialog to show SSL certificate infos.
    """
    def __init__(self, certificateChain, parent=None):
        """
        Constructor
        
        @param certificateChain SSL certificate chain (list of QSslCertificate)
        @param parent reference to the parent widget (QWidget)
        """
        super(E5SslCertificatesInfoDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.sslWidget.showCertificateChain(certificateChain)
