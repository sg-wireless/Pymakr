# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing functions to generate page previews.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWebKitWidgets import QWebFrame


def renderTabPreview(page, w, h):
    """
    Public function to render a pixmap of a page.
    
    @param page reference to the page to be previewed (QWebPage)
    @param w width of the preview pixmap (integer)
    @param h height of the preview pixmap (integer)
    @return preview pixmap (QPixmap)
    """
    oldSize = page.viewportSize()
    width = page.mainFrame().contentsSize().width()
    page.setViewportSize(QSize(width, int(width * h / w)))
    pageImage = __render(page, page.viewportSize().width(),
                         page.viewportSize().height())
    page.setViewportSize(oldSize)
    return pageImage.scaled(
        w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)


def __render(page, w, h):
    """
    Private function to render a pixmap of given size for a web page.
    
    @param page reference to the page to be rendered (QWebPage)
    @param w width of the pixmap (integer)
    @param h height of the pixmap (integer)
    @return rendered pixmap (QPixmap)
    """
    # create the page image
    pageImage = QPixmap(w, h)
    pageImage.fill(Qt.transparent)
    
    # render it
    p = QPainter(pageImage)
    page.mainFrame().render(p, QWebFrame.ContentsLayer)
    p.end()
    
    return pageImage
