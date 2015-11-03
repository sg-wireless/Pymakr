# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the bookmarks manager.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSignal, Qt, QT_TRANSLATE_NOOP, QObject, QFile, \
    QIODevice, QXmlStreamReader, QDate, QDateTime, QFileInfo, QUrl, \
    QCoreApplication
from PyQt5.QtWidgets import QUndoStack, QUndoCommand, QDialog

from E5Gui import E5MessageBox, E5FileDialog

from .BookmarkNode import BookmarkNode

from Utilities.AutoSaver import AutoSaver
import Utilities
import Preferences

BOOKMARKBAR = QT_TRANSLATE_NOOP("BookmarksManager", "Bookmarks Bar")
BOOKMARKMENU = QT_TRANSLATE_NOOP("BookmarksManager", "Bookmarks Menu")

StartRoot = 0
StartMenu = 1
StartToolBar = 2


class BookmarksManager(QObject):
    """
    Class implementing the bookmarks manager.
    
    @signal entryAdded(BookmarkNode) emitted after a bookmark node has been
        added
    @signal entryRemoved(BookmarkNode, int, BookmarkNode) emitted after a
        bookmark node has been removed
    @signal entryChanged(BookmarkNode) emitted after a bookmark node has been
        changed
    @signal bookmarksSaved() emitted after the bookmarks were saved
    @signal bookmarksReloaded() emitted after the bookmarks were reloaded
    """
    entryAdded = pyqtSignal(BookmarkNode)
    entryRemoved = pyqtSignal(BookmarkNode, int, BookmarkNode)
    entryChanged = pyqtSignal(BookmarkNode)
    bookmarksSaved = pyqtSignal()
    bookmarksReloaded = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(BookmarksManager, self).__init__(parent)
        
        self.__saveTimer = AutoSaver(self, self.save)
        self.entryAdded.connect(self.__saveTimer.changeOccurred)
        self.entryRemoved.connect(self.__saveTimer.changeOccurred)
        self.entryChanged.connect(self.__saveTimer.changeOccurred)
        
        self.__initialize()
    
    def __initialize(self):
        """
        Private method to initialize some data.
        """
        self.__loaded = False
        self.__bookmarkRootNode = None
        self.__toolbar = None
        self.__menu = None
        self.__bookmarksModel = None
        self.__commands = QUndoStack()
    
    @classmethod
    def getFileName(cls):
        """
        Class method to get the file name of the bookmark file.
        
        @return name of the bookmark file (string)
        """
        return os.path.join(Utilities.getConfigDir(), "browser",
                            "bookmarks.xbel")
    
    def close(self):
        """
        Public method to close the bookmark manager.
        """
        self.__saveTimer.saveIfNeccessary()
    
    def undoRedoStack(self):
        """
        Public method to get a reference to the undo stack.
        
        @return reference to the undo stack (QUndoStack)
        """
        return self.__commands
    
    def changeExpanded(self):
        """
        Public method to handle a change of the expanded state.
        """
        self.__saveTimer.changeOccurred()
    
    def reload(self):
        """
        Public method used to initiate a reloading of the bookmarks.
        """
        self.__initialize()
        self.load()
        self.bookmarksReloaded.emit()
    
    def load(self):
        """
        Public method to load the bookmarks.
        
        @exception RuntimeError raised to indicate an error loading the
            bookmarks
        """
        if self.__loaded:
            return
        
        self.__loaded = True
        
        bookmarkFile = self.getFileName()
        if not QFile.exists(bookmarkFile):
            from . import DefaultBookmarks_rc       # __IGNORE_WARNING__
            bookmarkFile = QFile(":/DefaultBookmarks.xbel")
            bookmarkFile.open(QIODevice.ReadOnly)
        
        from .XbelReader import XbelReader
        reader = XbelReader()
        self.__bookmarkRootNode = reader.read(bookmarkFile)
        if reader.error() != QXmlStreamReader.NoError:
            E5MessageBox.warning(
                None,
                self.tr("Loading Bookmarks"),
                self.tr(
                    """Error when loading bookmarks on line {0},"""
                    """ column {1}:\n {2}""")
                .format(reader.lineNumber(),
                        reader.columnNumber(),
                        reader.errorString()))
        
        others = []
        for index in range(
                len(self.__bookmarkRootNode.children()) - 1, -1, -1):
            node = self.__bookmarkRootNode.children()[index]
            if node.type() == BookmarkNode.Folder:
                if (node.title == self.tr("Toolbar Bookmarks") or
                    node.title == BOOKMARKBAR) and \
                   self.__toolbar is None:
                    node.title = self.tr(BOOKMARKBAR)
                    self.__toolbar = node
                
                if (node.title == self.tr("Menu") or
                    node.title == BOOKMARKMENU) and \
                   self.__menu is None:
                    node.title = self.tr(BOOKMARKMENU)
                    self.__menu = node
            else:
                others.append(node)
            self.__bookmarkRootNode.remove(node)
        
        if len(self.__bookmarkRootNode.children()) > 0:
            raise RuntimeError("Error loading bookmarks.")
        
        if self.__toolbar is None:
            self.__toolbar = BookmarkNode(BookmarkNode.Folder,
                                          self.__bookmarkRootNode)
            self.__toolbar.title = self.tr(BOOKMARKBAR)
        else:
            self.__bookmarkRootNode.add(self.__toolbar)
        
        if self.__menu is None:
            self.__menu = BookmarkNode(BookmarkNode.Folder,
                                       self.__bookmarkRootNode)
            self.__menu.title = self.tr(BOOKMARKMENU)
        else:
            self.__bookmarkRootNode.add(self.__menu)
        
        for node in others:
            self.__menu.add(node)
        
        self.__convertFromOldBookmarks()
    
    def save(self):
        """
        Public method to save the bookmarks.
        """
        if not self.__loaded:
            return
        
        from .XbelWriter import XbelWriter
        writer = XbelWriter()
        bookmarkFile = self.getFileName()
        
        # save root folder titles in English (i.e. not localized)
        self.__menu.title = BOOKMARKMENU
        self.__toolbar.title = BOOKMARKBAR
        if not writer.write(bookmarkFile, self.__bookmarkRootNode):
            E5MessageBox.warning(
                None,
                self.tr("Saving Bookmarks"),
                self.tr("""Error saving bookmarks to <b>{0}</b>.""")
                .format(bookmarkFile))
        
        # restore localized titles
        self.__menu.title = self.tr(BOOKMARKMENU)
        self.__toolbar.title = self.tr(BOOKMARKBAR)
        
        self.bookmarksSaved.emit()
    
    def addBookmark(self, parent, node, row=-1):
        """
        Public method to add a bookmark.
        
        @param parent reference to the node to add to (BookmarkNode)
        @param node reference to the node to add (BookmarkNode)
        @param row row number (integer)
        """
        if not self.__loaded:
            return
        
        self.setTimestamp(node, BookmarkNode.TsAdded,
                          QDateTime.currentDateTime())
        
        command = InsertBookmarksCommand(self, parent, node, row)
        self.__commands.push(command)
    
    def removeBookmark(self, node):
        """
        Public method to remove a bookmark.
        
        @param node reference to the node to be removed (BookmarkNode)
        """
        if not self.__loaded:
            return
        
        parent = node.parent()
        row = parent.children().index(node)
        command = RemoveBookmarksCommand(self, parent, row)
        self.__commands.push(command)
    
    def setTitle(self, node, newTitle):
        """
        Public method to set the title of a bookmark.
        
        @param node reference to the node to be changed (BookmarkNode)
        @param newTitle title to be set (string)
        """
        if not self.__loaded:
            return
        
        command = ChangeBookmarkCommand(self, node, newTitle, True)
        self.__commands.push(command)
    
    def setUrl(self, node, newUrl):
        """
        Public method to set the URL of a bookmark.
        
        @param node reference to the node to be changed (BookmarkNode)
        @param newUrl URL to be set (string)
        """
        if not self.__loaded:
            return
        
        command = ChangeBookmarkCommand(self, node, newUrl, False)
        self.__commands.push(command)
    
    def setNodeChanged(self, node):
        """
        Public method to signal changes of bookmarks other than title, URL
        or timestamp.
        
        @param node reference to the bookmark (BookmarkNode)
        """
        self.__saveTimer.changeOccurred()
    
    def setTimestamp(self, node, timestampType, timestamp):
        """
        Public method to set the URL of a bookmark.
        
        @param node reference to the node to be changed (BookmarkNode)
        @param timestampType type of the timestamp to set
            (BookmarkNode.TsAdded, BookmarkNode.TsModified,
            BookmarkNode.TsVisited)
        @param timestamp timestamp to set (QDateTime)
        """
        if not self.__loaded:
            return
        
        assert timestampType in [BookmarkNode.TsAdded,
                                 BookmarkNode.TsModified,
                                 BookmarkNode.TsVisited]
        
        if timestampType == BookmarkNode.TsAdded:
            node.added = timestamp
        elif timestampType == BookmarkNode.TsModified:
            node.modified = timestamp
        elif timestampType == BookmarkNode.TsVisited:
            node.visited = timestamp
        self.__saveTimer.changeOccurred()
    
    def bookmarks(self):
        """
        Public method to get a reference to the root bookmark node.
        
        @return reference to the root bookmark node (BookmarkNode)
        """
        if not self.__loaded:
            self.load()
        
        return self.__bookmarkRootNode
    
    def menu(self):
        """
        Public method to get a reference to the bookmarks menu node.
        
        @return reference to the bookmarks menu node (BookmarkNode)
        """
        if not self.__loaded:
            self.load()
        
        return self.__menu
    
    def toolbar(self):
        """
        Public method to get a reference to the bookmarks toolbar node.
        
        @return reference to the bookmarks toolbar node (BookmarkNode)
        """
        if not self.__loaded:
            self.load()
        
        return self.__toolbar
    
    def bookmarksModel(self):
        """
        Public method to get a reference to the bookmarks model.
        
        @return reference to the bookmarks model (BookmarksModel)
        """
        if self.__bookmarksModel is None:
            from .BookmarksModel import BookmarksModel
            self.__bookmarksModel = BookmarksModel(self, self)
        return self.__bookmarksModel
    
    def importBookmarks(self):
        """
        Public method to import bookmarks.
        """
        from .BookmarksImportDialog import BookmarksImportDialog
        dlg = BookmarksImportDialog()
        if dlg.exec_() == QDialog.Accepted:
            importRootNode = dlg.getImportedBookmarks()
            if importRootNode is not None:
                self.addBookmark(self.menu(), importRootNode)
    
    def exportBookmarks(self):
        """
        Public method to export the bookmarks.
        """
        fileName, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            None,
            self.tr("Export Bookmarks"),
            "eric6_bookmarks.xbel",
            self.tr("XBEL bookmarks (*.xbel);;"
                    "XBEL bookmarks (*.xml);;"
                    "HTML Bookmarks (*.html)"))
        if not fileName:
            return
        
        ext = QFileInfo(fileName).suffix()
        if not ext:
            ex = selectedFilter.split("(*")[1].split(")")[0]
            if ex:
                fileName += ex
        
        ext = QFileInfo(fileName).suffix()
        if ext == "html":
            from .NsHtmlWriter import NsHtmlWriter
            writer = NsHtmlWriter()
        else:
            from .XbelWriter import XbelWriter
            writer = XbelWriter()
        if not writer.write(fileName, self.__bookmarkRootNode):
            E5MessageBox.critical(
                None,
                self.tr("Exporting Bookmarks"),
                self.tr("""Error exporting bookmarks to <b>{0}</b>.""")
                .format(fileName))
    
    def __convertFromOldBookmarks(self):
        """
        Private method to convert the old bookmarks into the new ones.
        """
        bmNames = Preferences.Prefs.settings.value('Bookmarks/Names')
        bmFiles = Preferences.Prefs.settings.value('Bookmarks/Files')
        
        if bmNames is not None and bmFiles is not None:
            if len(bmNames) == len(bmFiles):
                convertedRootNode = BookmarkNode(BookmarkNode.Folder)
                convertedRootNode.title = self.tr("Converted {0}")\
                    .format(QDate.currentDate().toString(
                        Qt.SystemLocaleShortDate))
                for i in range(len(bmNames)):
                    node = BookmarkNode(BookmarkNode.Bookmark,
                                        convertedRootNode)
                    node.title = bmNames[i]
                    url = QUrl(bmFiles[i])
                    if not url.scheme():
                        url.setScheme("file")
                    node.url = url.toString()
                self.addBookmark(self.menu(), convertedRootNode)
                
                Preferences.Prefs.settings.remove('Bookmarks')
    
    def iconChanged(self, url):
        """
        Public slot to update the icon image for an URL.
        
        @param url URL of the icon to update (QUrl or string)
        """
        if isinstance(url, QUrl):
            url = url.toString()
        nodes = self.bookmarksForUrl(url)
        for node in nodes:
            self.bookmarksModel().entryChanged(node)
    
    def bookmarkForUrl(self, url, start=StartRoot):
        """
        Public method to get a bookmark node for a given URL.
        
        @param url URL of the bookmark to search for (QUrl or string)
        @keyparam start indicator for the start of the search
            (StartRoot, StartMenu, StartToolBar)
        @return bookmark node for the given url (BookmarkNode)
        """
        if start == StartMenu:
            startNode = self.__menu
        elif start == StartToolBar:
            startNode = self.__toolbar
        else:
            startNode = self.__bookmarkRootNode
        if startNode is None:
            return None
        
        if isinstance(url, QUrl):
            url = url.toString()
        
        return self.__searchBookmark(url, startNode)
    
    def __searchBookmark(self, url, startNode):
        """
        Private method get a bookmark node for a given URL.
        
        @param url URL of the bookmark to search for (string)
        @param startNode reference to the node to start searching
            (BookmarkNode)
        @return bookmark node for the given url (BookmarkNode)
        """
        bm = None
        for node in startNode.children():
            if node.type() == BookmarkNode.Folder:
                bm = self.__searchBookmark(url, node)
            elif node.type() == BookmarkNode.Bookmark:
                if node.url == url:
                    bm = node
            if bm is not None:
                return bm
        return None
    
    def bookmarksForUrl(self, url, start=StartRoot):
        """
        Public method to get a list of bookmark nodes for a given URL.
        
        @param url URL of the bookmarks to search for (QUrl or string)
        @keyparam start indicator for the start of the search
            (StartRoot, StartMenu, StartToolBar)
        @return list of bookmark nodes for the given url (list of BookmarkNode)
        """
        if start == StartMenu:
            startNode = self.__menu
        elif start == StartToolBar:
            startNode = self.__toolbar
        else:
            startNode = self.__bookmarkRootNode
        if startNode is None:
            return None
        
        if isinstance(url, QUrl):
            url = url.toString()
        
        return self.__searchBookmarks(url, startNode)
    
    def __searchBookmarks(self, url, startNode):
        """
        Private method get a list of bookmark nodes for a given URL.
        
        @param url URL of the bookmarks to search for (string)
        @param startNode reference to the node to start searching
            (BookmarkNode)
        @return list of bookmark nodes for the given url (list of BookmarkNode)
        """
        bm = []
        for node in startNode.children():
            if node.type() == BookmarkNode.Folder:
                bm.extend(self.__searchBookmarks(url, node))
            elif node.type() == BookmarkNode.Bookmark:
                if node.url == url:
                    bm.append(node)
        return bm


class RemoveBookmarksCommand(QUndoCommand):
    """
    Class implementing the Remove undo command.
    """
    def __init__(self, bookmarksManager, parent, row):
        """
        Constructor
        
        @param bookmarksManager reference to the bookmarks manager
            (BookmarksManager)
        @param parent reference to the parent node (BookmarkNode)
        @param row row number of bookmark (integer)
        """
        super(RemoveBookmarksCommand, self).__init__(
            QCoreApplication.translate("BookmarksManager", "Remove Bookmark"))
        
        self._row = row
        self._bookmarksManager = bookmarksManager
        try:
            self._node = parent.children()[row]
        except IndexError:
            self._node = BookmarkNode()
        self._parent = parent
    
    def undo(self):
        """
        Public slot to perform the undo action.
        """
        self._parent.add(self._node, self._row)
        self._bookmarksManager.entryAdded.emit(self._node)
    
    def redo(self):
        """
        Public slot to perform the redo action.
        """
        self._parent.remove(self._node)
        self._bookmarksManager.entryRemoved.emit(
            self._parent, self._row, self._node)


class InsertBookmarksCommand(RemoveBookmarksCommand):
    """
    Class implementing the Insert undo command.
    """
    def __init__(self, bookmarksManager, parent, node, row):
        """
        Constructor
        
        @param bookmarksManager reference to the bookmarks manager
            (BookmarksManager)
        @param parent reference to the parent node (BookmarkNode)
        @param node reference to the node to be inserted (BookmarkNode)
        @param row row number of bookmark (integer)
        """
        RemoveBookmarksCommand.__init__(self, bookmarksManager, parent, row)
        self.setText(QCoreApplication.translate(
            "BookmarksManager", "Insert Bookmark"))
        self._node = node
    
    def undo(self):
        """
        Public slot to perform the undo action.
        """
        RemoveBookmarksCommand.redo(self)
    
    def redo(self):
        """
        Public slot to perform the redo action.
        """
        RemoveBookmarksCommand.undo(self)


class ChangeBookmarkCommand(QUndoCommand):
    """
    Class implementing the Insert undo command.
    """
    def __init__(self, bookmarksManager, node, newValue, title):
        """
        Constructor
        
        @param bookmarksManager reference to the bookmarks manager
            (BookmarksManager)
        @param node reference to the node to be changed (BookmarkNode)
        @param newValue new value to be set (string)
        @param title flag indicating a change of the title (True) or
            the URL (False) (boolean)
        """
        super(ChangeBookmarkCommand, self).__init__()
        
        self._bookmarksManager = bookmarksManager
        self._title = title
        self._newValue = newValue
        self._node = node
        
        if self._title:
            self._oldValue = self._node.title
            self.setText(QCoreApplication.translate(
                "BookmarksManager", "Name Change"))
        else:
            self._oldValue = self._node.url
            self.setText(QCoreApplication.translate(
                "BookmarksManager", "Address Change"))
    
    def undo(self):
        """
        Public slot to perform the undo action.
        """
        if self._title:
            self._node.title = self._oldValue
        else:
            self._node.url = self._oldValue
        self._bookmarksManager.entryChanged.emit(self._node)
    
    def redo(self):
        """
        Public slot to perform the redo action.
        """
        if self._title:
            self._node.title = self._newValue
        else:
            self._node.url = self._newValue
        self._bookmarksManager.entryChanged.emit(self._node)
