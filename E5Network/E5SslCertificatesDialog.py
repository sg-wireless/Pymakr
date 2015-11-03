# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show and edit all certificates.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, Qt, QByteArray, QFile, QFileInfo, \
    QIODevice, qVersion
from PyQt5.QtWidgets import QDialog, QTreeWidgetItem
try:
    from PyQt5.QtNetwork import QSslCertificate, QSslSocket, \
        QSslConfiguration, QSsl
except ImportError:
    pass

from E5Gui import E5MessageBox, E5FileDialog

from .Ui_E5SslCertificatesDialog import Ui_E5SslCertificatesDialog

import Preferences
import Utilities
import UI.PixmapCache
import Globals


class E5SslCertificatesDialog(QDialog, Ui_E5SslCertificatesDialog):
    """
    Class implementing a dialog to show and edit all certificates.
    """
    CertRole = Qt.UserRole + 1
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(E5SslCertificatesDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.serversViewButton.setIcon(
            UI.PixmapCache.getIcon("certificates.png"))
        self.serversDeleteButton.setIcon(
            UI.PixmapCache.getIcon("certificateDelete.png"))
        self.serversExportButton.setIcon(
            UI.PixmapCache.getIcon("certificateExport.png"))
        self.serversImportButton.setIcon(
            UI.PixmapCache.getIcon("certificateImport.png"))
        
        self.caViewButton.setIcon(
            UI.PixmapCache.getIcon("certificates.png"))
        self.caDeleteButton.setIcon(
            UI.PixmapCache.getIcon("certificateDelete.png"))
        self.caExportButton.setIcon(
            UI.PixmapCache.getIcon("certificateExport.png"))
        self.caImportButton.setIcon(
            UI.PixmapCache.getIcon("certificateImport.png"))
        
        self.__populateServerCertificatesTree()
        self.__populateCaCertificatesTree()
    
    def __populateServerCertificatesTree(self):
        """
        Private slot to populate the server certificates tree.
        """
        certificateDict = Globals.toDict(
            Preferences.Prefs.settings.value("Ssl/CaCertificatesDict"))
        for server in certificateDict:
            for cert in QSslCertificate.fromData(certificateDict[server]):
                self.__createServerCertificateEntry(server, cert)
        
        self.serversCertificatesTree.expandAll()
        for i in range(self.serversCertificatesTree.columnCount()):
            self.serversCertificatesTree.resizeColumnToContents(i)
    
    def __createServerCertificateEntry(self, server, cert):
        """
        Private method to create a server certificate entry.
        
        @param server server name of the certificate (string)
        @param cert certificate to insert (QSslCertificate)
        """
        # step 1: extract the info to be shown
        if qVersion() >= "5.0.0":
            organisation = Utilities.decodeString(
                ", ".join(cert.subjectInfo(QSslCertificate.Organization)))
            commonName = Utilities.decodeString(
                ", ".join(cert.subjectInfo(QSslCertificate.CommonName)))
        else:
            organisation = Utilities.decodeString(
                cert.subjectInfo(QSslCertificate.Organization))
            commonName = Utilities.decodeString(
                cert.subjectInfo(QSslCertificate.CommonName))
        if organisation is None or organisation == "":
            organisation = self.tr("(Unknown)")
        if commonName is None or commonName == "":
            commonName = self.tr("(Unknown common name)")
        expiryDate = cert.expiryDate().toString("yyyy-MM-dd")
        
        # step 2: create the entry
        items = self.serversCertificatesTree.findItems(
            organisation,
            Qt.MatchFixedString | Qt.MatchCaseSensitive)
        if len(items) == 0:
            parent = QTreeWidgetItem(
                self.serversCertificatesTree, [organisation])
        else:
            parent = items[0]
        
        itm = QTreeWidgetItem(parent, [commonName, server, expiryDate])
        itm.setData(0, self.CertRole, cert.toPem())
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_serversCertificatesTree_currentItemChanged(self, current, previous):
        """
        Private slot handling a change of the current item in the
        server certificates list.
        
        @param current new current item (QTreeWidgetItem)
        @param previous previous current item (QTreeWidgetItem)
        """
        enable = current is not None and current.parent() is not None
        self.serversViewButton.setEnabled(enable)
        self.serversDeleteButton.setEnabled(enable)
        self.serversExportButton.setEnabled(enable)
    
    @pyqtSlot()
    def on_serversViewButton_clicked(self):
        """
        Private slot to show data of the selected server certificate.
        """
        try:
            from E5Network.E5SslCertificatesInfoDialog import \
                E5SslCertificatesInfoDialog
            cert = QSslCertificate.fromData(
                self.serversCertificatesTree.currentItem().data(
                    0, self.CertRole))
            dlg = E5SslCertificatesInfoDialog(cert, self)
            dlg.exec_()
        except ImportError:
            pass
    
    @pyqtSlot()
    def on_serversDeleteButton_clicked(self):
        """
        Private slot to delete the selected server certificate.
        """
        itm = self.serversCertificatesTree.currentItem()
        res = E5MessageBox.yesNo(
            self,
            self.tr("Delete Server Certificate"),
            self.tr("""<p>Shall the server certificate really be"""
                    """ deleted?</p><p>{0}</p>"""
                    """<p>If the server certificate is deleted, the"""
                    """ normal security checks will be reinstantiated"""
                    """ and the server has to present a valid"""
                    """ certificate.</p>""")
            .format(itm.text(0)))
        if res:
            server = itm.text(1)
            cert = self.serversCertificatesTree.currentItem().data(
                0, self.CertRole)
            
            # delete the selected entry and its parent entry,
            # if it was the only one
            parent = itm.parent()
            parent.takeChild(parent.indexOfChild(itm))
            if parent.childCount() == 0:
                self.serversCertificatesTree.takeTopLevelItem(
                    self.serversCertificatesTree.indexOfTopLevelItem(parent))
            
            # delete the certificate from the user certificate store
            certificateDict = Globals.toDict(
                Preferences.Prefs.settings.value("Ssl/CaCertificatesDict"))
            if server in certificateDict:
                certs = QSslCertificate.fromData(certificateDict[server])
                if cert in certs:
                    certs.remove(cert)
                if certs:
                    pems = QByteArray()
                    for cert in certs:
                        pems.append(cert.toPem() + '\n')
                    certificateDict[server] = pems
                else:
                    del certificateDict[server]
            Preferences.Prefs.settings.setValue(
                "Ssl/CaCertificatesDict",
                certificateDict)
            
            # delete the certificate from the default certificates
            self.__updateDefaultConfiguration()
    
    @pyqtSlot()
    def on_serversImportButton_clicked(self):
        """
        Private slot to import server certificates.
        """
        certs = self.__importCertificate()
        if certs:
            server = "*"
            certificateDict = Globals.toDict(
                Preferences.Prefs.settings.value("Ssl/CaCertificatesDict"))
            if server in certificateDict:
                sCerts = QSslCertificate.fromData(certificateDict[server])
            else:
                sCerts = []
            
            pems = QByteArray()
            for cert in certs:
                if cert in sCerts:
                    if qVersion() >= "5.0.0":
                        commonStr = ", ".join(
                            cert.subjectInfo(QSslCertificate.CommonName))
                    else:
                        commonStr = cert.subjectInfo(
                            QSslCertificate.CommonName)
                    E5MessageBox.warning(
                        self,
                        self.tr("Import Certificate"),
                        self.tr(
                            """<p>The certificate <b>{0}</b> already exists."""
                            """ Skipping.</p>""")
                        .format(Utilities.decodeString(commonStr)))
                else:
                    pems.append(cert.toPem() + '\n')
            if server not in certificateDict:
                certificateDict[server] = QByteArray()
            certificateDict[server].append(pems)
            Preferences.Prefs.settings.setValue(
                "Ssl/CaCertificatesDict",
                certificateDict)
            
            self.serversCertificatesTree.clear()
            self.__populateServerCertificatesTree()
            
            self.__updateDefaultConfiguration()
    
    @pyqtSlot()
    def on_serversExportButton_clicked(self):
        """
        Private slot to export the selected server certificate.
        """
        cert = self.serversCertificatesTree.currentItem().data(
            0, self.CertRole)
        fname = self.serversCertificatesTree.currentItem().text(0)\
            .replace(" ", "").replace("\t", "")
        self.__exportCertificate(fname, cert)
    
    def __updateDefaultConfiguration(self):
        """
        Private method to update the default SSL configuration.
        """
        caList = self.__getSystemCaCertificates()
        certificateDict = Globals.toDict(
            Preferences.Prefs.settings.value("Ssl/CaCertificatesDict"))
        for server in certificateDict:
            for cert in QSslCertificate.fromData(certificateDict[server]):
                if cert not in caList:
                    caList.append(cert)
        sslCfg = QSslConfiguration.defaultConfiguration()
        sslCfg.setCaCertificates(caList)
        QSslConfiguration.setDefaultConfiguration(sslCfg)
    
    def __getSystemCaCertificates(self):
        """
        Private method to get the list of system certificates.
        
        @return list of system certificates (list of QSslCertificate)
        """
        caList = QSslCertificate.fromData(Globals.toByteArray(
            Preferences.Prefs.settings.value("Help/SystemCertificates")))
        if not caList:
            caList = QSslSocket.systemCaCertificates()
        return caList
    
    def __populateCaCertificatesTree(self):
        """
        Private slot to populate the CA certificates tree.
        """
        for cert in self.__getSystemCaCertificates():
            self.__createCaCertificateEntry(cert)
        
        self.caCertificatesTree.expandAll()
        for i in range(self.caCertificatesTree.columnCount()):
            self.caCertificatesTree.resizeColumnToContents(i)
        self.caCertificatesTree.sortItems(0, Qt.AscendingOrder)
    
    def __createCaCertificateEntry(self, cert):
        """
        Private method to create a CA certificate entry.
        
        @param cert certificate to insert (QSslCertificate)
        """
        # step 1: extract the info to be shown
        if qVersion() >= "5.0.0":
            organisation = Utilities.decodeString(
                ", ".join(cert.subjectInfo(QSslCertificate.Organization)))
            commonName = Utilities.decodeString(
                ", ".join(cert.subjectInfo(QSslCertificate.CommonName)))
        else:
            organisation = Utilities.decodeString(
                cert.subjectInfo(QSslCertificate.Organization))
            commonName = Utilities.decodeString(
                cert.subjectInfo(QSslCertificate.CommonName))
        if organisation is None or organisation == "":
            organisation = self.tr("(Unknown)")
        if commonName is None or commonName == "":
            commonName = self.tr("(Unknown common name)")
        expiryDate = cert.expiryDate().toString("yyyy-MM-dd")
        
        # step 2: create the entry
        items = self.caCertificatesTree.findItems(
            organisation,
            Qt.MatchFixedString | Qt.MatchCaseSensitive)
        if len(items) == 0:
            parent = QTreeWidgetItem(self.caCertificatesTree, [organisation])
        else:
            parent = items[0]
        
        itm = QTreeWidgetItem(parent, [commonName, expiryDate])
        itm.setData(0, self.CertRole, cert.toPem())
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_caCertificatesTree_currentItemChanged(self, current, previous):
        """
        Private slot handling a change of the current item
        in the CA certificates list.
        
        @param current new current item (QTreeWidgetItem)
        @param previous previous current item (QTreeWidgetItem)
        """
        enable = current is not None and current.parent() is not None
        self.caViewButton.setEnabled(enable)
        self.caDeleteButton.setEnabled(enable)
        self.caExportButton.setEnabled(enable)
    
    @pyqtSlot()
    def on_caViewButton_clicked(self):
        """
        Private slot to show data of the selected CA certificate.
        """
        try:
            from E5Network.E5SslCertificatesInfoDialog import \
                E5SslCertificatesInfoDialog
            cert = QSslCertificate.fromData(
                self.caCertificatesTree.currentItem().data(0, self.CertRole))
            dlg = E5SslCertificatesInfoDialog(cert, self)
            dlg.exec_()
        except ImportError:
            pass
    
    @pyqtSlot()
    def on_caDeleteButton_clicked(self):
        """
        Private slot to delete the selected CA certificate.
        """
        itm = self.caCertificatesTree.currentItem()
        res = E5MessageBox.yesNo(
            self,
            self.tr("Delete CA Certificate"),
            self.tr(
                """<p>Shall the CA certificate really be deleted?</p>"""
                """<p>{0}</p>"""
                """<p>If the CA certificate is deleted, the browser"""
                """ will not trust any certificate issued by this CA.</p>""")
            .format(itm.text(0)))
        if res:
            cert = self.caCertificatesTree.currentItem().data(0, self.CertRole)
            
            # delete the selected entry and its parent entry,
            # if it was the only one
            parent = itm.parent()
            parent.takeChild(parent.indexOfChild(itm))
            if parent.childCount() == 0:
                self.caCertificatesTree.takeTopLevelItem(
                    self.caCertificatesTree.indexOfTopLevelItem(parent))
            
            # delete the certificate from the CA certificate store
            caCerts = self.__getSystemCaCertificates()
            if cert in caCerts:
                caCerts.remove(cert)
            pems = QByteArray()
            for cert in caCerts:
                pems.append(cert.toPem() + '\n')
            Preferences.Prefs.settings.setValue(
                "Help/SystemCertificates", pems)
            
            # delete the certificate from the default certificates
            self.__updateDefaultConfiguration()
    
    @pyqtSlot()
    def on_caImportButton_clicked(self):
        """
        Private slot to import server certificates.
        """
        certs = self.__importCertificate()
        if certs:
            caCerts = self.__getSystemCaCertificates()
            for cert in certs:
                if cert in caCerts:
                    if qVersion() >= "5.0.0":
                        commonStr = ", ".join(
                            cert.subjectInfo(QSslCertificate.CommonName))
                    else:
                        commonStr = cert.subjectInfo(
                            QSslCertificate.CommonName)
                    E5MessageBox.warning(
                        self,
                        self.tr("Import Certificate"),
                        self.tr(
                            """<p>The certificate <b>{0}</b> already exists."""
                            """ Skipping.</p>""")
                        .format(Utilities.decodeString(commonStr)))
                else:
                    caCerts.append(cert)
            
            pems = QByteArray()
            for cert in caCerts:
                pems.append(cert.toPem() + '\n')
            Preferences.Prefs.settings.setValue(
                "Help/SystemCertificates", pems)
            
            self.caCertificatesTree.clear()
            self.__populateCaCertificatesTree()
            
            self.__updateDefaultConfiguration()
    
    @pyqtSlot()
    def on_caExportButton_clicked(self):
        """
        Private slot to export the selected CA certificate.
        """
        cert = self.caCertificatesTree.currentItem().data(0, self.CertRole)
        fname = self.caCertificatesTree.currentItem().text(0)\
            .replace(" ", "").replace("\t", "")
        self.__exportCertificate(fname, cert)
    
    def __exportCertificate(self, name, cert):
        """
        Private slot to export a certificate.
        
        @param name default file name without extension (string)
        @param cert certificate to be exported (QSslCertificate)
        """
        if cert is not None:
            fname, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
                self,
                self.tr("Export Certificate"),
                name,
                self.tr("Certificate File (PEM) (*.pem);;"
                        "Certificate File (DER) (*.der)"),
                None,
                E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
            
            if fname:
                ext = QFileInfo(fname).suffix()
                if not ext or ext not in ["pem", "der"]:
                    ex = selectedFilter.split("(*")[1].split(")")[0]
                    if ex:
                        fname += ex
                if QFileInfo(fname).exists():
                    res = E5MessageBox.yesNo(
                        self,
                        self.tr("Export Certificate"),
                        self.tr("<p>The file <b>{0}</b> already exists."
                                " Overwrite it?</p>").format(fname),
                        icon=E5MessageBox.Warning)
                    if not res:
                        return
                
                f = QFile(fname)
                if not f.open(QIODevice.WriteOnly):
                    E5MessageBox.critical(
                        self,
                        self.tr("Export Certificate"),
                        self.tr(
                            """<p>The certificate could not be written"""
                            """ to file <b>{0}</b></p><p>Error: {1}</p>""")
                        .format(fname, f.errorString()))
                    return
                
                if fname.endswith(".pem"):
                    crt = cert.toPem()
                else:
                    crt = cert.toDer()
                f.write(crt)
                f.close()
    
    def __importCertificate(self):
        """
        Private method to read a certificate.
        
        @return certificates read (list of QSslCertificate)
        """
        fname = E5FileDialog.getOpenFileName(
            self,
            self.tr("Import Certificate"),
            "",
            self.tr("Certificate Files (*.pem *.crt *.der *.cer *.ca);;"
                    "All Files (*)"))
        
        if fname:
            f = QFile(fname)
            if not f.open(QIODevice.ReadOnly):
                E5MessageBox.critical(
                    self,
                    self.tr("Export Certificate"),
                    self.tr(
                        """<p>The certificate could not be read from file"""
                        """ <b>{0}</b></p><p>Error: {1}</p>""")
                    .format(fname, f.errorString()))
                return []
            
            crt = f.readAll()
            f.close()
            cert = QSslCertificate.fromData(crt, QSsl.Pem)
            if not cert:
                cert = QSslCertificate.fromData(crt, QSsl.Der)
            
            return cert
        
        return []
