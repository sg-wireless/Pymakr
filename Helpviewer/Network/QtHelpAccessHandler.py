# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a scheme access handler for QtHelp.
"""

from __future__ import unicode_literals

import mimetypes
import os

from PyQt5.QtCore import QByteArray

from .SchemeAccessHandler import SchemeAccessHandler

from .NetworkReply import NetworkReply

QtDocPath = "qthelp://com.trolltech."

ExtensionMap = {
    ".bmp": "image/bmp",
    ".css": "text/css",
    ".gif": "image/gif",
    ".html": "text/html",
    ".htm": "text/html",
    ".ico": "image/x-icon",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".js": "application/x-javascript",
    ".mng": "video/x-mng",
    ".pbm": "image/x-portable-bitmap",
    ".pgm": "image/x-portable-graymap",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".ppm": "image/x-portable-pixmap",
    ".rss": "application/rss+xml",
    ".svg": "image/svg+xml",
    ".svgz": "image/svg+xml",
    ".text": "text/plain",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".txt": "text/plain",
    ".xbm": "image/x-xbitmap",
    ".xml": "text/xml",
    ".xpm": "image/x-xpm",
    ".xsl": "text/xsl",
    ".xhtml": "application/xhtml+xml",
    ".wml": "text/vnd.wap.wml",
    ".wmlc": "application/vnd.wap.wmlc",
}


class QtHelpAccessHandler(SchemeAccessHandler):
    """
    Class implementing a scheme access handler for QtHelp.
    """
    def __init__(self, engine, parent=None):
        """
        Constructor
        
        @param engine reference to the help engine (QHelpEngine)
        @param parent reference to the parent object (QObject)
        """
        SchemeAccessHandler.__init__(self, parent)
        
        self.__engine = engine
    
    def __mimeFromUrl(self, url):
        """
        Private method to guess the mime type given an URL.
        
        @param url URL to guess the mime type from (QUrl)
        @return mime type for the given URL (string)
        """
        path = url.path()
        ext = os.path.splitext(path)[1].lower()
        if ext in ExtensionMap:
            return ExtensionMap[ext]
        else:
            return "application/octet-stream"
    
    def createRequest(self, op, request, outgoingData=None):
        """
        Public method to create a request.
        
        @param op the operation to be performed
            (QNetworkAccessManager.Operation)
        @param request reference to the request object (QNetworkRequest)
        @param outgoingData reference to an IODevice containing data to be sent
            (QIODevice)
        @return reference to the created reply object (QNetworkReply)
        """
        url = request.url()
        strUrl = url.toString()
        
        # For some reason the url to load is already wrong (passed from webkit)
        # though the css file and the references inside should work that way.
        # One possible problem might be that the css is loaded at the same
        # level as the html, thus a path inside the css like
        # (../images/foo.png) might cd out of the virtual folder
        if not self.__engine.findFile(url).isValid():
            if strUrl.startswith(QtDocPath):
                newUrl = request.url()
                if not newUrl.path().startswith("/qdoc/"):
                    newUrl.setPath("qdoc" + newUrl.path())
                    url = newUrl
                    strUrl = url.toString()
        
        mimeType = mimetypes.guess_type(strUrl)[0]
        if mimeType is None:
            # do our own (limited) guessing
            mimeType = self.__mimeFromUrl(url)
        
        if self.__engine.findFile(url).isValid():
            data = self.__engine.fileData(url)
        else:
            data = QByteArray(self.tr(
                """<title>Error 404...</title>"""
                """<div align="center"><br><br>"""
                """<h1>The page could not be found</h1><br>"""
                """<h3>'{0}'</h3></div>""").format(strUrl).encode("utf-8"))
        return NetworkReply(request, data, mimeType, self.parent())
