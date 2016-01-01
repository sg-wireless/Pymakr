# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a syntax highlighter for unified and context diff outputs.
"""

from __future__ import unicode_literals

from E5Gui.E5GenericDiffHighlighter import TERMINAL, E5GenericDiffHighlighter


class HgDiffHighlighter(E5GenericDiffHighlighter):
    """
    Class implementing a diff highlighter for Git.
    """
    def __init__(self, doc):
        """
        Constructor
        
        @param doc reference to the text document (QTextDocument)
        """
        super(HgDiffHighlighter, self).__init__(doc)

    def generateRules(self):
        """
        Public method to generate the rule set.
        """
        diffHeader = self.makeFormat(fg=self.textColor,
                                     bg=self.headerColor)
        diffContext = self.makeFormat(fg=self.textColor,
                                      bg=self.contextColor)

        diffAdded = self.makeFormat(fg=self.textColor,
                                    bg=self.addedColor)
        diffRemoved = self.makeFormat(fg=self.textColor,
                                      bg=self.removedColor)
        
        diffHeaderRegex = TERMINAL(r'^diff -r ')

        diffOldRegex = TERMINAL(r'^--- ')
        diffNewRegex = TERMINAL(r'^\+\+\+ ')
        diffContextRegex = TERMINAL(r'^@@ ')
        
        diffAddedRegex = TERMINAL(r'^\+')
        diffRemovedRegex = TERMINAL(r'^-')
        
        self.createRules((diffOldRegex, diffRemoved),
                         (diffNewRegex, diffAdded),
                         (diffContextRegex, diffContext),
                         (diffHeaderRegex, diffHeader),
                         (diffAddedRegex, diffAdded),
                         (diffRemovedRegex, diffRemoved),
                         )
