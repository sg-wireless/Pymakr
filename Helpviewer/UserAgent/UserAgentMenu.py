# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a menu to select the user agent string.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QXmlStreamReader, QFile, QIODevice
from PyQt5.QtWidgets import QMenu, QAction, QActionGroup, QInputDialog, \
    QLineEdit

from E5Gui import E5MessageBox


class UserAgentMenu(QMenu):
    """
    Class implementing a menu to select the user agent string.
    """
    def __init__(self, title, url=None, parent=None):
        """
        Constructor
        
        @param title title of the menu (string)
        @param url URL to set user agent for (QUrl)
        @param parent reference to the parent widget (QWidget)
        """
        super(UserAgentMenu, self).__init__(title, parent)
        
        self.__manager = None
        self.__url = url
        if self.__url:
            if self.__url.isValid():
                import Helpviewer.HelpWindow
                self.__manager = \
                    Helpviewer.HelpWindow.HelpWindow.userAgentsManager()
            else:
                self.__url = None
        
        self.aboutToShow.connect(self.__populateMenu)
    
    def __populateMenu(self):
        """
        Private slot to populate the menu.
        """
        self.aboutToShow.disconnect(self.__populateMenu)
        
        self.__actionGroup = QActionGroup(self)
        
        # add default action
        self.__defaultUserAgent = QAction(self)
        self.__defaultUserAgent.setText(self.tr("Default"))
        self.__defaultUserAgent.setCheckable(True)
        self.__defaultUserAgent.triggered.connect(
            self.__switchToDefaultUserAgent)
        if self.__url:
            self.__defaultUserAgent.setChecked(
                self.__manager.userAgentForUrl(self.__url) == "")
        else:
            from Helpviewer.HelpBrowserWV import HelpWebPage
            self.__defaultUserAgent.setChecked(HelpWebPage().userAgent() == "")
        self.addAction(self.__defaultUserAgent)
        self.__actionGroup.addAction(self.__defaultUserAgent)
        isChecked = self.__defaultUserAgent.isChecked()
        
        # add default extra user agents
        isChecked = self.__addDefaultActions() or isChecked
        
        # add other action
        self.addSeparator()
        self.__otherUserAgent = QAction(self)
        self.__otherUserAgent.setText(self.tr("Other..."))
        self.__otherUserAgent.setCheckable(True)
        self.__otherUserAgent.triggered.connect(
            self.__switchToOtherUserAgent)
        self.addAction(self.__otherUserAgent)
        self.__actionGroup.addAction(self.__otherUserAgent)
        self.__otherUserAgent.setChecked(not isChecked)
    
    def __switchToDefaultUserAgent(self):
        """
        Private slot to set the default user agent.
        """
        if self.__url:
            self.__manager.removeUserAgent(self.__url.host())
        else:
            from Helpviewer.HelpBrowserWV import HelpWebPage
            HelpWebPage().setUserAgent("")
    
    def __switchToOtherUserAgent(self):
        """
        Private slot to set a custom user agent string.
        """
        from Helpviewer.HelpBrowserWV import HelpWebPage
        userAgent, ok = QInputDialog.getText(
            self,
            self.tr("Custom user agent"),
            self.tr("User agent:"),
            QLineEdit.Normal,
            HelpWebPage().userAgent(resolveEmpty=True))
        if ok:
            if self.__url:
                self.__manager.setUserAgentForUrl(self.__url, userAgent)
            else:
                HelpWebPage().setUserAgent(userAgent)
    
    def __changeUserAgent(self):
        """
        Private slot to change the user agent.
        """
        act = self.sender()
        if self.__url:
            self.__manager.setUserAgentForUrl(self.__url, act.data())
        else:
            from Helpviewer.HelpBrowserWV import HelpWebPage
            HelpWebPage().setUserAgent(act.data())
    
    def __addDefaultActions(self):
        """
        Private slot to add the default user agent entries.
        
        @return flag indicating that a user agent entry is checked (boolean)
        """
        from . import UserAgentDefaults_rc              # __IGNORE_WARNING__
        defaultUserAgents = QFile(":/UserAgentDefaults.xml")
        defaultUserAgents.open(QIODevice.ReadOnly)
        
        menuStack = []
        isChecked = False
        
        if self.__url:
            currentUserAgentString = self.__manager.userAgentForUrl(self.__url)
        else:
            from Helpviewer.HelpBrowserWV import HelpWebPage
            currentUserAgentString = HelpWebPage().userAgent()
        xml = QXmlStreamReader(defaultUserAgents)
        while not xml.atEnd():
            xml.readNext()
            if xml.isStartElement() and xml.name() == "separator":
                if menuStack:
                    menuStack[-1].addSeparator()
                else:
                    self.addSeparator()
                continue
            
            if xml.isStartElement() and xml.name() == "useragent":
                attributes = xml.attributes()
                title = attributes.value("description")
                userAgent = attributes.value("useragent")
                
                act = QAction(self)
                act.setText(title)
                act.setData(userAgent)
                act.setToolTip(userAgent)
                act.setCheckable(True)
                act.setChecked(userAgent == currentUserAgentString)
                act.triggered.connect(self.__changeUserAgent)
                if menuStack:
                    menuStack[-1].addAction(act)
                else:
                    self.addAction(act)
                self.__actionGroup.addAction(act)
                isChecked = isChecked or act.isChecked()
            
            if xml.isStartElement() and xml.name() == "useragentmenu":
                attributes = xml.attributes()
                title = attributes.value("title")
                if title == "v_a_r_i_o_u_s":
                    title = self.tr("Various")
                
                menu = QMenu(self)
                menu.setTitle(title)
                self.addMenu(menu)
                menuStack.append(menu)
            
            if xml.isEndElement() and xml.name() == "useragentmenu":
                menuStack.pop()
        
        if xml.hasError():
            E5MessageBox.critical(
                self,
                self.tr("Parsing default user agents"),
                self.tr(
                    """<p>Error parsing default user agents.</p><p>{0}</p>""")
                .format(xml.errorString()))
        
        return isChecked
