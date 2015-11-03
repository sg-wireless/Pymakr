# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Flash blocker.
"""


from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSlot, QUrl, Qt, QByteArray, QTimer
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QMenu, QDialog, QLabel, QFormLayout
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtWebKit import QWebElement, QWebElementCollection
from PyQt5.QtWebKitWidgets import QWebHitTestResult, QWebView

from .Ui_ClickToFlash import Ui_ClickToFlash

import UI.PixmapCache


class ClickToFlash(QWidget, Ui_ClickToFlash):
    """
    Class implementing the Flash blocker.
    """
    _acceptedUrl = QUrl()
    _acceptedArgNames = []
    _acceptedArgValues = []

    def __init__(self, plugin, mimeType, url, argumentNames, argumentValues,
                 parent=None):
        """
        Constructor
        
        @param plugin reference to the plug-in (ClickToFlashPlugin)
        @param mimeType MIME type for the plug-in (string)
        @param url requested URL (QUrl)
        @param argumentNames list of argument names (list of strings)
        @param argumentValues list of argument values (list of strings)
        @param parent reference to the parent widget (QWidget)
        """
        super(ClickToFlash, self).__init__(parent)
        
        # Check AdBlock first
        import Helpviewer.HelpWindow
        manager = Helpviewer.HelpWindow.HelpWindow.adBlockManager()
        if manager.isEnabled():
            urlString = bytes(url.toEncoded()).decode()
            urlDomain = url.host()
            for subscription in manager.subscriptions():
                blockedRule = subscription.match(
                    QNetworkRequest(url), urlDomain, urlString)
                if blockedRule:
                    QTimer.singleShot(200, self.__hideAdBlocked)
                    return
        
        self.setupUi(self)
        
        self.__swapping = False
        self.__element = QWebElement()
        
        self.__plugin = plugin
        self.__url = QUrl(url)
        self.__argumentNames = argumentNames[:]
        self.__argumentValues = argumentValues[:]
        self.__mimeType = mimeType
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__showContextMenu)
        self.setToolTip(self.__url.toString())
        
        iconName = plugin.getIconName(mimeType)
        if iconName:
            self.loadFlashButton.setIcon(UI.PixmapCache.getIcon(iconName))
        else:
            self.loadFlashButton.setText(self.tr("Load"))
    
    @pyqtSlot()
    def on_loadFlashButton_clicked(self):
        """
        Private slot handling the flash activation.
        """
        self.__load()
    
    def __showContextMenu(self):
        """
        Private slot to show the context menu.
        """
        menu = QMenu()
        act = menu.addAction(self.tr("Object blocked by ClickToFlash"))
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        menu.addAction(
            self.tr("Show information about object"), self.__showInfo)
        menu.addSeparator()
        menu.addAction(self.tr("Load"), self.__load)
        menu.addAction(self.tr("Delete object"), self.__hideAdBlocked)
        menu.addSeparator()
        host = self.__url.host()
        add = menu.addAction(
            self.tr("Add '{0}' to Whitelist").format(host),
            self.__addToWhitelist)
        remove = menu.addAction(
            self.tr("Remove '{0}' from Whitelist").format(host),
            self.__removeFromWhitelist)
        onWhitelist = self.__plugin.onWhitelist(host)
        add.setEnabled(not onWhitelist)
        remove.setEnabled(onWhitelist)
        menu.addSeparator()
        menu.addAction(self.tr("Configure Whitelist"), self.__configure)
        menu.actions()[0].setEnabled(False)
        
        menu.exec_(QCursor.pos())
    
    def swapping(self):
        """
        Public method to check, if the plug-in is swapping.
        
        @return flag indicating the swapping status (boolean)
        """
        return self.__swapping
    
    def __configure(self):
        """
        Private slot to configure the whitelist.
        """
        self.__plugin.configure()
    
    def __addToWhitelist(self):
        """
        Private slot to add the host to the whitelist.
        """
        self.__plugin.addToWhitelist(self.__url.host())
    
    def __removeFromWhitelist(self):
        """
        Private slot to remove the host from the whitelist.
        """
        self.__plugin.removeFromWhitelist(self.__url.host())
    
    def __load(self, all=False):
        """
        Private slot to load the flash content.
        
        @param all flag indicating to load all flash players. (boolean)
        """
        self.__findElement()
        if not self.__element.isNull():
            substitute = self.__element.clone()
            substitute.setAttribute("type", self.__mimeType)
            self.__element.replace(substitute)

            ClickToFlash._acceptedUrl = self.__url
            ClickToFlash._acceptedArgNames = self.__argumentNames
            ClickToFlash._acceptedArgValues = self.__argumentValues
    
    def __findElement(self):
        """
        Private method to find the element belonging to this ClickToFlash
        instance.
        """
        parent = self.parentWidget()
        view = None
        while parent is not None:
            if isinstance(parent, QWebView):
                view = parent
                break
            parent = parent.parentWidget()
        if view is None:
            return
        
        objectPos = view.mapFromGlobal(self.loadFlashButton.mapToGlobal(
            self.loadFlashButton.pos()))
        objectFrame = view.page().frameAt(objectPos)
        hitResult = QWebHitTestResult()
        hitElement = QWebElement()
        
        if objectFrame is not None:
            hitResult = objectFrame.hitTestContent(objectPos)
            hitElement = hitResult.element()
        
        if not hitElement.isNull() and \
           hitElement.tagName().lower() in ["embed", "object"]:
            self.__element = hitElement
            return
        
        # hit test failed, trying to find element by src
        # attribute in elements of all frames on page (although less accurate
        frames = []
        frames.append(view.page().mainFrame())
        while frames:
            frame = frames.pop(0)
            if not frame:
                continue
            docElement = frame.documentElement()
            elements = QWebElementCollection()
            elements.append(docElement.findAll("embed"))
            elements.append(docElement.findAll("object"))
            
            for element in elements:
                if not self.__checkElement(element) and \
                   not self.__checkUrlOnElement(element, view):
                    continue
                self.__element = element
                return
            frames.extend(frame.childFrames())
    
    def __checkUrlOnElement(self, element, view):
        """
        Private slot to check the URL of an element.
        
        @param element reference to the element to check (QWebElement)
        @param view reference to the view object (QWebView)
        @return flag indicating a positive result (boolean)
        """
        checkString = element.attribute("src")
        if checkString == "":
            checkString = element.attribute("data")
        if checkString == "":
            checkString = element.attribute("value")
        
        checkString = view.url().resolved(QUrl(checkString)).toString(
            QUrl.RemoveQuery)
        return self.__url.toEncoded().contains(
            QByteArray(checkString.encode("utf-8")))
    
    def __checkElement(self, element):
        """
        Private slot to check an element against the saved arguments.
        
        @param element reference to the element to check (QWebElement)
        @return flag indicating a positive result (boolean)
        """
        if self.__argumentNames == element.attributeNames():
            for name in self.__argumentNames:
                if element.attribute(name) not in self.__argumentValues:
                    return False
            
            return True
        
        return False
    
    def __hideAdBlocked(self):
        """
        Private slot to hide the object.
        """
        self.__findElement()
        if not self.__element.isNull():
            self.__element.setStyleProperty("display", "none")
        else:
            self.hide()
    
    def __showInfo(self):
        """
        Private slot to show information about the blocked object.
        """
        dlg = QDialog()
        dlg.setWindowTitle(self.tr("Flash Object"))
        dlg.setSizeGripEnabled(True)
        layout = QFormLayout(dlg)
        layout.addRow(QLabel(self.tr("<b>Attribute Name</b>")),
                      QLabel(self.tr("<b>Value</b>")))
        
        index = 0
        for name in self.__argumentNames:
            nameLabel = QLabel(self.__elide(name, length=30))
            value = self.__argumentValues[index]
            valueLabel = QLabel(self.__elide(value, length=60))
            valueLabel.setTextInteractionFlags(
                Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
            layout.addRow(nameLabel, valueLabel)
            
            index += 1
        
        if index == 0:
            layout.addRow(QLabel(self.tr("No information available.")))
        
        dlg.setMaximumHeight(500)
        dlg.setMaximumWidth(500)
        dlg.exec_()
    
    def __elide(self, txt, mode=Qt.ElideMiddle, length=40):
        """
        Private method to elide some text.
        
        @param txt text to be elided (string)
        @keyparam mode elide mode (Qt.TextElideMode)
        @keyparam length amount of characters to be used (integer)
        @return the elided text (string)
        """
        if mode == Qt.ElideNone or len(txt) < length:
            return txt
        elif mode == Qt.ElideLeft:
            return "...{0}".format(txt[-length:])
        elif mode == Qt.ElideMiddle:
            return "{0}...{1}".format(txt[:length // 2], txt[-(length // 2):])
        elif mode == Qt.ElideRight:
            return "{0}...".format(txt[:length])
        else:
            # just in case
            return txt
    
    @classmethod
    def isAlreadyAccepted(cls, url, argumentNames, argumentValues):
        """
        Class method to check, if the given parameter combination is being
        accepted.
        
        @param url URL to be checked for (QUrl)
        @param argumentNames argument names to be checked for (list of strings)
        @param argumentValues argument values to be checked for (list of
            strings)
        @return flag indicating that this was already accepted (boolean)
        """
        return url == cls._acceptedUrl and \
            argumentNames == cls._acceptedArgNames and \
            argumentValues == cls._acceptedArgValues
