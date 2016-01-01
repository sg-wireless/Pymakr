# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a widget to show SSL information.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import qVersion, Qt, QUrl, QPoint
from PyQt5.QtWidgets import QMenu, QGridLayout, QLabel, QSizePolicy
from PyQt5.QtNetwork import QSsl, QSslConfiguration, QSslCertificate

import UI.PixmapCache
import Utilities


class E5SslInfoWidget(QMenu):
    """
    Class implementing a widget to show SSL certificate infos.
    """
    def __init__(self, url, configuration, parent=None):
        """
        Constructor
        
        @param url URL to show SSL info for (QUrl)
        @param configuration SSL configuration (QSslConfiguration)
        @param parent reference to the parent widget (QWidget)
        """
        super(E5SslInfoWidget, self).__init__(parent)
        
        self.__url = QUrl(url)
        self.__configuration = QSslConfiguration(configuration)
        
        self.setMinimumWidth(400)
        
        certList = self.__configuration.peerCertificateChain()
        if certList:
            cert = certList[0]
        else:
            cert = QSslCertificate()
        
        layout = QGridLayout(self)
        rows = 0
        
        ##########################################
        ## Identity Information
        ##########################################
        imageLabel = QLabel(self)
        layout.addWidget(imageLabel, rows, 0, Qt.AlignCenter)
        
        label = QLabel(self)
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        label.setText(self.tr("Identity"))
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        layout.addWidget(label, rows, 1)
        rows += 1
        
        label = QLabel(self)
        label.setWordWrap(True)
        if cert.isNull():
            label.setText(self.tr(
                "Warning: this site is NOT carrying a certificate."))
            imageLabel.setPixmap(UI.PixmapCache.getPixmap("securityLow32.png"))
        else:
            if qVersion() >= "5.0.0":
                valid = not cert.isBlacklisted()
            else:
                valid = cert.isValid()
            if valid:
                if qVersion() >= "5.0.0":
                    txt = ", ".join(
                        cert.issuerInfo(QSslCertificate.CommonName))
                else:
                    txt = cert.issuerInfo(QSslCertificate.CommonName)
                label.setText(self.tr(
                    "The certificate for this site is valid"
                    " and has been verified by:\n{0}").format(
                    Utilities.decodeString(txt)))
                imageLabel.setPixmap(
                    UI.PixmapCache.getPixmap("securityHigh32.png"))
            else:
                label.setText(self.tr(
                    "The certificate for this site is NOT valid."))
                imageLabel.setPixmap(
                    UI.PixmapCache.getPixmap("securityLow32.png"))
            layout.addWidget(label, rows, 1)
            rows += 1
            
            label = QLabel(self)
            label.setWordWrap(True)
            label.setText(
                '<a href="moresslinfos">' +
                self.tr("Certificate Information") + "</a>")
            label.linkActivated.connect(self.__showCertificateInfos)
            layout.addWidget(label, rows, 1)
            rows += 1
        
        ##########################################
        ## Identity Information
        ##########################################
        imageLabel = QLabel(self)
        layout.addWidget(imageLabel, rows, 0, Qt.AlignCenter)
        
        label = QLabel(self)
        label.setWordWrap(True)
        label.setText(self.tr("Encryption"))
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        layout.addWidget(label, rows, 1)
        rows += 1
        
        cipher = self.__configuration.sessionCipher()
        if cipher.isNull():
            label = QLabel(self)
            label.setWordWrap(True)
            label.setText(self.tr(
                'Your connection to "{0}" is NOT encrypted.\n').format(
                self.__url.host()))
            layout.addWidget(label, rows, 1)
            imageLabel.setPixmap(UI.PixmapCache.getPixmap("securityLow32.png"))
            rows += 1
        else:
            label = QLabel(self)
            label.setWordWrap(True)
            label.setText(self.tr(
                'Your connection to "{0}" is encrypted.').format(
                self.__url.host()))
            layout.addWidget(label, rows, 1)
            
            proto = cipher.protocol()
            if proto == QSsl.SslV3:
                sslVersion = "SSL 3.0"
                imageLabel.setPixmap(
                    UI.PixmapCache.getPixmap("securityLow32.png"))
            elif proto == QSsl.TlsV1SslV3:
                sslVersion = "TLS 1.0/SSL 3.0"
                imageLabel.setPixmap(
                    UI.PixmapCache.getPixmap("securityLow32.png"))
            elif proto == QSsl.SslV2:
                sslVersion = "SSL 2.0"
                imageLabel.setPixmap(
                    UI.PixmapCache.getPixmap("securityLow32.png"))
            else:
                sslVersion = self.tr("unknown")
                imageLabel.setPixmap(
                    UI.PixmapCache.getPixmap("securityLow32.png"))
            if qVersion() >= "5.0.0":
                if proto == QSsl.TlsV1_0:
                    sslVersion = "TLS 1.0"
                    imageLabel.setPixmap(
                        UI.PixmapCache.getPixmap("securityHigh32.png"))
                elif proto == QSsl.TlsV1_1:
                    sslVersion = "TLS 1.1"
                    imageLabel.setPixmap(
                        UI.PixmapCache.getPixmap("securityHigh32.png"))
                elif proto == QSsl.TlsV1_2:
                    sslVersion = "TLS 1.2"
                    imageLabel.setPixmap(
                        UI.PixmapCache.getPixmap("securityHigh32.png"))
            else:
                if proto == QSsl.TlsV1:
                    sslVersion = "TLS 1.0"
                    imageLabel.setPixmap(
                        UI.PixmapCache.getPixmap("securityHigh32.png"))
            rows += 1
            
            label = QLabel(self)
            label.setWordWrap(True)
            label.setText(self.tr(
                "It uses protocol: {0}").format(sslVersion))
            layout.addWidget(label, rows, 1)
            rows += 1
            
            label = QLabel(self)
            label.setWordWrap(True)
            label.setText(self.tr(
                "It is encrypted using {0} at {1} bits, "
                "with {2} for message authentication and "
                "{3} as key exchange mechanism.\n\n").format(
                cipher.encryptionMethod(),
                cipher.usedBits(),
                cipher.authenticationMethod(),
                cipher.keyExchangeMethod()))
            layout.addWidget(label, rows, 1)
            rows += 1
    
    def showAt(self, pos):
        """
        Public method to show the widget.
        
        @param pos position to show at (QPoint)
        """
        self.adjustSize()
        xpos = pos.x() - self.width()
        if xpos < 0:
            xpos = 10
        p = QPoint(xpos, pos.y() + 10)
        self.move(p)
        self.show()
    
    def __showCertificateInfos(self):
        """
        Private slot to show certificate information.
        """
        from .E5SslCertificatesInfoDialog import E5SslCertificatesInfoDialog
        dlg = E5SslCertificatesInfoDialog(
            self.__configuration.peerCertificateChain())
        dlg.exec_()
    
    def accept(self):
        """
        Public method to accept the widget.
        """
        self.close()
