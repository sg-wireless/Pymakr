# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a syntax highlighter for unified and context diff outputs.
"""

from __future__ import unicode_literals

from E5Gui.E5GenericDiffHighlighter import TERMINAL, E5GenericDiffHighlighter


class SvnDiffHighlighter(E5GenericDiffHighlighter):
    """
    Class implementing a diff highlighter for Git.
    """
    def __init__(self, doc):
        """
        Constructor
        
        @param doc reference to the text document (QTextDocument)
        """
        super(SvnDiffHighlighter, self).__init__(doc)

    def generateRules(self):
        """
        Public method to generate the rule set.
        """
        diffHeader = self.makeFormat(fg=self.textColor,
                                     bg=self.headerColor)
        diffHeaderBold = self.makeFormat(fg=self.textColor,
                                         bg=self.headerColor,
                                         bold=True)
        diffContext = self.makeFormat(fg=self.textColor,
                                      bg=self.contextColor)

        diffAdded = self.makeFormat(fg=self.textColor,
                                    bg=self.addedColor)
        diffRemoved = self.makeFormat(fg=self.textColor,
                                      bg=self.removedColor)
        
        diffBarRegex = TERMINAL(r'^=+$')

        diffHeaderRegex = TERMINAL(r'^[iI]ndex: \S+')
        
        diffOldRegex = TERMINAL(r'^--- ')
        diffNewRegex = TERMINAL(r'^\+\+\+')
        diffContextRegex = TERMINAL(r'^@@ ')
        
        diffAddedRegex = TERMINAL(r'^[+>]|^A ')
        diffRemovedRegex = TERMINAL(r'^[-<]|^D ')
        
        self.createRules((diffOldRegex, diffRemoved),
                         (diffNewRegex, diffAdded),
                         (diffContextRegex, diffContext),
                         (diffHeaderRegex, diffHeader),
                         (diffBarRegex, diffHeaderBold),
                         (diffAddedRegex, diffAdded),
                         (diffRemovedRegex, diffRemoved),
                         )
