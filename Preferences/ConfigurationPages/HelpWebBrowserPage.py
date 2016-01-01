# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Help web browser configuration page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, QLocale
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtWebKit import QWebSettings

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_HelpWebBrowserPage import Ui_HelpWebBrowserPage

import Preferences
import UI.PixmapCache


class HelpWebBrowserPage(ConfigurationPageBase, Ui_HelpWebBrowserPage):
    """
    Class implementing the Help web browser configuration page.
    """
    def __init__(self, configDialog):
        """
        Constructor
        
        @param configDialog reference to the configuration dialog
            (ConfigurationDialog)
        """
        super(HelpWebBrowserPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("HelpWebBrowserPage")
        
        self.__configDlg = configDialog
        mw = configDialog.parent().parent()
        if hasattr(mw, "helpWindow") and mw.helpWindow is not None:
            self.__helpWindow = mw.helpWindow
        elif hasattr(mw, "currentBrowser"):
            self.__helpWindow = mw
        else:
            self.__helpWindow = None
        self.setCurrentPageButton.setEnabled(self.__helpWindow is not None)
        
        defaultSchemes = ["file://", "http://", "https://"]
        self.defaultSchemeCombo.addItems(defaultSchemes)
        
        self.clickToFlashCheckBox.setIcon(
            UI.PixmapCache.getIcon("flashBlock.png"))
        
        # set initial values
        self.singleHelpWindowCheckBox.setChecked(
            Preferences.getHelp("SingleHelpWindow"))
        self.saveGeometryCheckBox.setChecked(
            Preferences.getHelp("SaveGeometry"))
        self.webSuggestionsCheckBox.setChecked(
            Preferences.getHelp("WebSearchSuggestions"))
        self.showTabPreviews.setChecked(
            Preferences.getHelp("ShowPreview"))
        self.accessKeysCheckBox.setChecked(
            Preferences.getHelp("AccessKeysEnabled"))
        
        self.javaCheckBox.setChecked(
            Preferences.getHelp("JavaEnabled"))
        self.javaScriptGroup.setChecked(
            Preferences.getHelp("JavaScriptEnabled"))
        self.jsOpenWindowsCheckBox.setChecked(
            Preferences.getHelp("JavaScriptCanOpenWindows"))
        self.jsCloseWindowsCheckBox.setChecked(
            Preferences.getHelp("JavaScriptCanCloseWindows"))
        self.jsClipboardCheckBox.setChecked(
            Preferences.getHelp("JavaScriptCanAccessClipboard"))
        self.pluginsGroup.setChecked(
            Preferences.getHelp("PluginsEnabled"))
        self.clickToFlashCheckBox.setChecked(
            Preferences.getHelp("ClickToFlashEnabled"))
        self.doNotTrackCheckBox.setChecked(
            Preferences.getHelp("DoNotTrack"))
        self.sendRefererCheckBox.setChecked(
            Preferences.getHelp("SendReferer"))
        
        self.diskCacheCheckBox.setChecked(
            Preferences.getHelp("DiskCacheEnabled"))
        self.cacheSizeSpinBox.setValue(
            Preferences.getHelp("DiskCacheSize"))
        cachePolicy = Preferences.getHelp("CachePolicy")
        if cachePolicy == QNetworkRequest.PreferNetwork:
            self.cacheKeepButton.setChecked(True)
        elif cachePolicy == QNetworkRequest.PreferCache:
            self.cachePreferButton.setChecked(True)
        elif cachePolicy == QNetworkRequest.AlwaysCache:
            self.cacheOfflineButton.setChecked(True)
        
        self.printBackgroundsCheckBox.setChecked(
            Preferences.getHelp("PrintBackgrounds"))
        
        self.startupCombo.setCurrentIndex(
            Preferences.getHelp("StartupBehavior"))
        self.homePageEdit.setText(
            Preferences.getHelp("HomePage"))
        
        self.defaultSchemeCombo.setCurrentIndex(
            self.defaultSchemeCombo.findText(
                Preferences.getHelp("DefaultScheme")))
        
        historyLimit = Preferences.getHelp("HistoryLimit")
        idx = 0
        if historyLimit == 1:
            idx = 0
        elif historyLimit == 7:
            idx = 1
        elif historyLimit == 14:
            idx = 2
        elif historyLimit == 30:
            idx = 3
        elif historyLimit == 365:
            idx = 4
        elif historyLimit == -1:
            idx = 5
        elif historyLimit == -2:
            idx = 6
        else:
            idx = 5
        self.expireHistory.setCurrentIndex(idx)
        
        for language in range(2, QLocale.LastLanguage + 1):
            countries = [l.country() for l in QLocale.matchingLocales(
                language, QLocale.AnyScript, QLocale.AnyCountry)]
            if len(countries) > 0:
                self.languageCombo.addItem(
                    QLocale.languageToString(language), language)
        self.languageCombo.model().sort(0)
        self.languageCombo.insertSeparator(0)
        self.languageCombo.insertItem(0, QLocale.languageToString(0), 0)
        index = self.languageCombo.findData(
            Preferences.getHelp("SearchLanguage"))
        if index > -1:
            self.languageCombo.setCurrentIndex(index)
        
        if hasattr(QWebSettings, "SpatialNavigationEnabled"):
            self.spatialCheckBox.setChecked(
                Preferences.getHelp("SpatialNavigationEnabled"))
        else:
            self.spatialCheckBox.setEnabled(False)
        if hasattr(QWebSettings, "LinksIncludedInFocusChain"):
            self.linksInFocusChainCheckBox.setChecked(
                Preferences.getHelp("LinksIncludedInFocusChain"))
        else:
            self.linksInFocusChainCheckBox.setEnabled(False)
        if hasattr(QWebSettings, "XSSAuditingEnabled"):
            self.xssAuditingCheckBox.setChecked(
                Preferences.getHelp("XSSAuditingEnabled"))
        else:
            self.xssAuditingCheckBox.setEnabled(False)
        if hasattr(QWebSettings, "SiteSpecificQuirksEnabled"):
            self.quirksCheckBox.setChecked(
                Preferences.getHelp("SiteSpecificQuirksEnabled"))
        else:
            self.quirksCheckBox.setEnabled(False)
    
    def save(self):
        """
        Public slot to save the Help Viewers configuration.
        """
        Preferences.setHelp(
            "SingleHelpWindow",
            self.singleHelpWindowCheckBox.isChecked())
        Preferences.setHelp(
            "SaveGeometry",
            self.saveGeometryCheckBox.isChecked())
        Preferences.setHelp(
            "WebSearchSuggestions",
            self.webSuggestionsCheckBox.isChecked())
        Preferences.setHelp(
            "ShowPreview",
            self.showTabPreviews.isChecked())
        Preferences.setHelp(
            "AccessKeysEnabled",
            self.accessKeysCheckBox.isChecked())
        
        Preferences.setHelp(
            "JavaEnabled",
            self.javaCheckBox.isChecked())
        Preferences.setHelp(
            "JavaScriptEnabled",
            self.javaScriptGroup.isChecked())
        Preferences.setHelp(
            "JavaScriptCanOpenWindows",
            self.jsOpenWindowsCheckBox.isChecked())
        Preferences.setHelp(
            "JavaScriptCanCloseWindows",
            self.jsCloseWindowsCheckBox.isChecked())
        Preferences.setHelp(
            "JavaScriptCanAccessClipboard",
            self.jsClipboardCheckBox.isChecked())
        Preferences.setHelp(
            "PluginsEnabled",
            self.pluginsGroup.isChecked())
        Preferences.setHelp(
            "ClickToFlashEnabled",
            self.clickToFlashCheckBox.isChecked())
        Preferences.setHelp(
            "DoNotTrack",
            self.doNotTrackCheckBox.isChecked())
        Preferences.setHelp(
            "SendReferer",
            self.sendRefererCheckBox.isChecked())
        
        Preferences.setHelp(
            "DiskCacheEnabled",
            self.diskCacheCheckBox.isChecked())
        Preferences.setHelp(
            "DiskCacheSize",
            self.cacheSizeSpinBox.value())
        if self.cacheKeepButton.isChecked():
            Preferences.setHelp(
                "CachePolicy",
                QNetworkRequest.PreferNetwork)
        elif self.cachePreferButton.isChecked():
            Preferences.setHelp(
                "CachePolicy",
                QNetworkRequest.PreferCache)
        elif self.cacheOfflineButton.isChecked():
            Preferences.setHelp(
                "CachePolicy",
                QNetworkRequest.AlwaysCache)
        
        Preferences.setHelp(
            "PrintBackgrounds",
            self.printBackgroundsCheckBox.isChecked())
        
        Preferences.setHelp(
            "StartupBehavior",
            self.startupCombo.currentIndex())
        Preferences.setHelp(
            "HomePage",
            self.homePageEdit.text())
        
        Preferences.setHelp(
            "DefaultScheme",
            self.defaultSchemeCombo.currentText())
        
        idx = self.expireHistory.currentIndex()
        if idx == 0:
            historyLimit = 1
        elif idx == 1:
            historyLimit = 7
        elif idx == 2:
            historyLimit = 14
        elif idx == 3:
            historyLimit = 30
        elif idx == 4:
            historyLimit = 365
        elif idx == 5:
            historyLimit = -1
        elif idx == 6:
            historyLimit = -2
        Preferences.setHelp("HistoryLimit", historyLimit)
        
        languageIndex = self.languageCombo.currentIndex()
        if languageIndex > -1:
            language = self.languageCombo.itemData(languageIndex)
        else:
            # fall back to system default
            language = QLocale.system().language()
        Preferences.setHelp("SearchLanguage", language)
        
        if hasattr(QWebSettings, "SpatialNavigationEnabled"):
            Preferences.setHelp(
                "SpatialNavigationEnabled",
                self.spatialCheckBox.isChecked())
        if hasattr(QWebSettings, "LinksIncludedInFocusChain"):
            Preferences.setHelp(
                "LinksIncludedInFocusChain",
                self.linksInFocusChainCheckBox.isChecked())
        if hasattr(QWebSettings, "XSSAuditingEnabled"):
            Preferences.setHelp(
                "XSSAuditingEnabled",
                self.xssAuditingCheckBox.isChecked())
        if hasattr(QWebSettings, "SiteSpecificQuirksEnabled"):
            Preferences.setHelp(
                "SiteSpecificQuirksEnabled",
                self.quirksCheckBox.isChecked())
    
    @pyqtSlot()
    def on_setCurrentPageButton_clicked(self):
        """
        Private slot to set the current page as the home page.
        """
        url = self.__helpWindow.currentBrowser().url()
        self.homePageEdit.setText(bytes(url.toEncoded()).decode())
    
    @pyqtSlot()
    def on_defaultHomeButton_clicked(self):
        """
        Private slot to set the default home page.
        """
        self.homePageEdit.setText(Preferences.Prefs.helpDefaults["HomePage"])
    
    @pyqtSlot(int)
    def on_startupCombo_currentIndexChanged(self, index):
        """
        Private slot to enable elements depending on the selected startup
        entry.
        
        @param index index of the selected entry (integer)
        """
        enable = index == 0
        self.homePageLabel.setEnabled(enable)
        self.homePageEdit.setEnabled(enable)
        self.defaultHomeButton.setEnabled(enable)
        self.setCurrentPageButton.setEnabled(enable)
    
    @pyqtSlot()
    def on_refererWhitelistButton_clicked(self):
        """
        Private slot to edit the referer whitelist.
        """
        from Helpviewer.Network.SendRefererWhitelistDialog import \
            SendRefererWhitelistDialog
        SendRefererWhitelistDialog(self).exec_()
    
    @pyqtSlot()
    def on_noCacheHostsButton_clicked(self):
        """
        Private slot to edit the list of hosts exempted from caching.
        """
        from Helpviewer.Network.NoCacheHostsDialog import \
            NoCacheHostsDialog
        NoCacheHostsDialog(self).exec_()


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = HelpWebBrowserPage(dlg)
    return page
