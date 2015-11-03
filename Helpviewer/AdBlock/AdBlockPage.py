# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class to apply AdBlock rules to a web page.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject, QUrl


class AdBlockPage(QObject):
    """
    Class to apply AdBlock rules to a web page.
    """
    def hideBlockedPageEntries(self, page):
        """
        Public method to apply AdBlock rules to a web page.
        
        @param page reference to the web page (HelpWebPage)
        """
        if page is None or page.mainFrame() is None:
            return
        
        import Helpviewer.HelpWindow
        manager = Helpviewer.HelpWindow.HelpWindow.adBlockManager()
        if not manager.isEnabled():
            return
        
        docElement = page.mainFrame().documentElement()
        
        for entry in page.getAdBlockedPageEntries():
            urlString = entry.urlString()
            if urlString.endswith((".js", ".css")):
                continue
            
            urlEnd = ""
            pos = urlString.rfind("/")
            if pos >= 0:
                urlEnd = urlString[pos + 1:]
            if urlString.endswith("/"):
                urlEnd = urlString[:-1]
            
            selector = \
                'img[src$="{0}"], iframe[src$="{0}"], embed[src$="{0}"]'\
                .format(urlEnd)
            elements = docElement.findAll(selector)
            
            for element in elements:
                src = element.attribute("src")
                src = src.replace("../", "")
                if src in urlString:
                    element.setStyleProperty("display", "none")
        
        # apply domain specific element hiding rules
        elementHiding = manager.elementHidingRulesForDomain(page.url())
        if not elementHiding:
            return
        
        elementHiding += "{display: none !important;}\n</style>"
        
        bodyElement = docElement.findFirst("body")
        bodyElement.appendInside(
            '<style type="text/css">\n/* AdBlock for eric */\n' +
            elementHiding)


class AdBlockedPageEntry(object):
    """
    Class implementing a data structure for web page rules.
    """
    def __init__(self, rule, url):
        """
        Constructor
        
        @param rule AdBlock rule to add (AdBlockRule)
        @param url URL that matched the rule (QUrl)
        """
        self.rule = rule
        self.url = QUrl(url)
    
    def __eq__(self, other):
        """
        Special method to test equality.
        
        @param other reference to the other entry (AdBlockedPageEntry)
        @return flag indicating equality (boolean)
        """
        return self.rule == other.rule and self.url == other.url
    
    def urlString(self):
        """
        Public method to get the URL as a string.
        
        @return URL as a string (string)
        """
        return self.url.toString()
