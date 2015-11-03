# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a pixmap cache for icons.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon, QPainter


class PixmapCache(object):
    """
    Class implementing a pixmap cache for icons.
    """
    def __init__(self):
        """
        Constructor
        """
        self.pixmapCache = {}
        self.searchPath = []

    def getPixmap(self, key):
        """
        Public method to retrieve a pixmap.

        @param key name of the wanted pixmap (string)
        @return the requested pixmap (QPixmap)
        """
        if key:
            try:
                return self.pixmapCache[key]
            except KeyError:
                if not os.path.isabs(key):
                    for path in self.searchPath:
                        pm = QPixmap(path + "/" + key)
                        if not pm.isNull():
                            break
                    else:
                        pm = QPixmap()
                else:
                    pm = QPixmap(key)
                self.pixmapCache[key] = pm
                return self.pixmapCache[key]
        return QPixmap()

    def addSearchPath(self, path):
        """
        Public method to add a path to the search path.

        @param path path to add (string)
        """
        if path not in self.searchPath:
            self.searchPath.append(path)

pixCache = PixmapCache()


def getPixmap(key, cache=pixCache):
    """
    Module function to retrieve a pixmap.

    @param key name of the wanted pixmap (string)
    @param cache reference to the pixmap cache object (PixmapCache)
    @return the requested pixmap (QPixmap)
    """
    return cache.getPixmap(key)


def getIcon(key, cache=pixCache):
    """
    Module function to retrieve an icon.

    @param key name of the wanted icon (string)
    @param cache reference to the pixmap cache object (PixmapCache)
    @return the requested icon (QIcon)
    """
    return QIcon(cache.getPixmap(key))


def getSymlinkIcon(key, cache=pixCache):
    """
    Module function to retrieve a symbolic link icon.

    @param key name of the wanted icon (string)
    @param cache reference to the pixmap cache object (PixmapCache)
    @return the requested icon (QIcon)
    """
    pix1 = QPixmap(cache.getPixmap(key))
    pix2 = cache.getPixmap("symlink.png")
    painter = QPainter(pix1)
    painter.drawPixmap(0, 10, pix2)
    painter.end()
    return QIcon(pix1)


def getCombinedIcon(keys, cache=pixCache):
    """
    Module function to retrieve a symbolic link icon.

    @param keys list of names of icons (string)
    @param cache reference to the pixmap cache object (PixmapCache)
    @return the requested icon (QIcon)
    """
    height = width = 0
    pixmaps = []
    for key in keys:
        pix = cache.getPixmap(key)
        if not pix.isNull():
            height = max(height, pix.height())
            width = max(width, pix.width())
            pixmaps.append(pix)
    if pixmaps:
        pix = QPixmap(len(pixmaps) * width, height)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        x = 0
        for pixmap in pixmaps:
            painter.drawPixmap(x, 0, pixmap.scaled(QSize(width, height)))
            x += width
        painter.end()
        icon = QIcon(pix)
    else:
        icon = QIcon()
    return icon


def addSearchPath(path, cache=pixCache):
    """
    Module function to add a path to the search path.

    @param path path to add (string)
    @param cache reference to the pixmap cache object (PixmapCache)
    """
    cache.addSearchPath(path)
