# -*- coding: utf-8 -*-

# Copyright (c) 2014 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class for showing an editor marker map.
"""

from __future__ import unicode_literals

from E5Gui.E5MapWidget import E5MapWidget

import Preferences


class EditorMarkerMap(E5MapWidget):
    """
    Class implementing a class for showing an editor marker map.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(EditorMarkerMap, self).__init__(parent)
        
        self.setWhatsThis(self.tr(
            """<b>Editor Map</b>"""
            """<p>This shows a 'map' of the editor. The visible area is"""
            """ highlighted by the box and all markers like bookmarks,"""
            """ breakpoints, errors or changed lines are indicated"""
            """ by differently colored lines configurable via the"""
            """ Editor\u279dStyle page of the configuration dialog.</p>"""
        ))
        
        # initialize colors for various markers
        self.initColors()
    
    def initColors(self):
        """
        Public method to initialize the colors.
        """
        self.setBackgroundColor(
            Preferences.getEditorColour("MarkerMapBackground"))
        
        self.__bookmarkColor = Preferences.getEditorColour("BookmarksMap")
        self.__errorColor = Preferences.getEditorColour("ErrorsMap")
        self.__warningColor = Preferences.getEditorColour("WarningsMap")
        self.__breakpointColor = Preferences.getEditorColour("BreakpointsMap")
        self.__taskColor = Preferences.getEditorColour("TasksMap")
        self.__coverageColor = Preferences.getEditorColour("CoverageMap")
        self.__changeColor = Preferences.getEditorColour("ChangesMap")
        self.__currentLineMarker = Preferences.getEditorColour("CurrentMap")
        self.__searchMarkerColor = Preferences.getEditorColour(
            "SearchMarkersMap")
        self.update()
    
    def __drawIndicator(self, line, painter, color):
        """
        Private method to draw an indicator.
        
        @param line line number (integer)
        @param painter reference to the painter (QPainter)
        @param color color to be used (QColor)
        """
        position = self.value2Position(line)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(self.generateIndicatorRect(position))
    
    def _paintIt(self, painter):
        """
        Protected method for painting the widget's indicators.
        
        @param painter reference to the painter object (QPainter)
        """
        # draw indicators in reverse order of priority
        
        # 1. changes
        for line in self._master.getChangeLines():
            self.__drawIndicator(line, painter, self.__changeColor)
        
        # 2. coverage
        for line in self._master.getCoverageLines():
            self.__drawIndicator(line, painter, self.__coverageColor)
        
        # 3. tasks
        for line in self._master.getTaskLines():
            self.__drawIndicator(line, painter, self.__taskColor)
        
        # 4. breakpoints
        for line in self._master.getBreakpointLines():
            self.__drawIndicator(line, painter, self.__breakpointColor)
        
        # 5. bookmarks
        for line in self._master.getBookmarkLines():
            self.__drawIndicator(line, painter, self.__bookmarkColor)
        
        # 6. search markers
        for line in self._master.getSearchIndicatorLines():
            self.__drawIndicator(line, painter, self.__searchMarkerColor)
        
        # 7. warnings
        for line in self._master.getWarningLines():
            self.__drawIndicator(line, painter, self.__warningColor)
        
        # 8. errors
        for line in self._master.getSyntaxErrorLines():
            self.__drawIndicator(line, painter, self.__errorColor)
        
        # 9. current line
        self.__drawIndicator(self._master.getCursorPosition()[0], painter,
                             self.__currentLineMarker)
