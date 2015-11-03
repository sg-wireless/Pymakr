# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a disk cache respecting privacy.
"""

from __future__ import unicode_literals

from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtNetwork import QNetworkDiskCache


class NetworkDiskCache(QNetworkDiskCache):
    """
    Class implementing a disk cache respecting privacy.
    """
    def prepare(self, metaData):
        """
        Public method to prepare the disk cache file.
        
        @param metaData meta data for a URL (QNetworkCacheMetaData)
        @return reference to the IO device (QIODevice)
        """
        if QWebSettings.globalSettings().testAttribute(
                QWebSettings.PrivateBrowsingEnabled):
            return None
        
        return QNetworkDiskCache.prepare(self, metaData)
