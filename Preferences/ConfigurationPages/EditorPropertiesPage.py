# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor Properties configuration page.
"""

from __future__ import unicode_literals

from QScintilla.QsciScintillaCompat import QSCINTILLA_VERSION

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorPropertiesPage import Ui_EditorPropertiesPage

import Preferences


class EditorPropertiesPage(ConfigurationPageBase, Ui_EditorPropertiesPage):
    """
    Class implementing the Editor Properties configuration page.
    """
    def __init__(self, lexers):
        """
        Constructor
        
        @param lexers reference to the lexers dictionary
        """
        super(EditorPropertiesPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("EditorPropertiesPage")
        
        self.languages = sorted(list(lexers.keys())[:])
        
        # set initial values
        # All
        self.allFoldCompactCheckBox.setChecked(
            Preferences.getEditor("AllFoldCompact"))
        
        # Bash
        self.foldBashCommentCheckBox.setChecked(
            Preferences.getEditor("BashFoldComment"))
        
        # C++
        self.foldCppCommentCheckBox.setChecked(
            Preferences.getEditor("CppFoldComment"))
        self.foldCppPreprocessorCheckBox.setChecked(
            Preferences.getEditor("CppFoldPreprocessor"))
        self.foldCppAtElseCheckBox.setChecked(
            Preferences.getEditor("CppFoldAtElse"))
        self.cppIndentOpeningBraceCheckBox.setChecked(
            Preferences.getEditor("CppIndentOpeningBrace"))
        self.cppIndentClosingBraceCheckBox.setChecked(
            Preferences.getEditor("CppIndentClosingBrace"))
        self.cppCaseInsensitiveCheckBox.setChecked(
            Preferences.getEditor("CppCaseInsensitiveKeywords"))
        self.cppDollarAllowedCheckBox.setChecked(
            Preferences.getEditor("CppDollarsAllowed"))
        if QSCINTILLA_VERSION() >= 0x020500:
            self.cppStylePreprocessorCheckBox.setChecked(
                Preferences.getEditor("CppStylePreprocessor"))
        else:
            self.cppStylePreprocessorCheckBox.setEnabled(False)
        if QSCINTILLA_VERSION() >= 0x020600:
            self.cppHighlightTripleQuotedCheckBox.setChecked(
                Preferences.getEditor("CppHighlightTripleQuotedStrings"))
        else:
            self.cppHighlightTripleQuotedCheckBox.setEnabled(False)
        if QSCINTILLA_VERSION() >= 0x020700:
            self.cppHighlightHashQuotedCheckBox.setChecked(
                Preferences.getEditor("CppHighlightHashQuotedStrings"))
        else:
            self.cppHighlightHashQuotedCheckBox.setEnabled(False)
        if QSCINTILLA_VERSION() >= 0x020900:
            self.cppHighlightBackQuotedCheckBox.setChecked(
                Preferences.getEditor("CppHighlightBackQuotedStrings"))
            self.cppHighlightEsacepSequencesCheckBox.setChecked(
                Preferences.getEditor("CppHighlightEscapeSequences"))
            self.cppVerbatimStringEscapeAllowedCheckBox.setChecked(
                Preferences.getEditor(
                    "CppVerbatimStringEscapeSequencesAllowed"))
        else:
            self.cppHighlightBackQuotedCheckBox.setEnabled(False)
            self.cppHighlightEsacepSequencesCheckBox.setEnabled(False)
            self.cppVerbatimStringEscapeAllowedCheckBox.setEnabled(False)
        
        # CMake
        self.cmakeFoldAtElseCheckBox.setChecked(
            Preferences.getEditor("CMakeFoldAtElse"))
        
        # CoffeeScript
        if "CoffeeScript" in self.languages:
            self.foldCoffeeScriptCommentCheckBox.setChecked(
                Preferences.getEditor("CoffeScriptFoldComment"))
            self.coffeeScriptDollarAllowedCheckBox.setChecked(
                Preferences.getEditor("CoffeeScriptDollarsAllowed"))
            self.coffeeScriptStylePreprocessorCheckBox.setChecked(
                Preferences.getEditor("CoffeeScriptStylePreprocessor"))
        else:
            self.coffeeScriptGroup.setEnabled(False)
        
        # CSS
        self.foldCssCommentCheckBox.setChecked(
            Preferences.getEditor("CssFoldComment"))
        if QSCINTILLA_VERSION() >= 0x020700:
            self.cssHssCheckBox.setChecked(
                Preferences.getEditor("CssHssSupport"))
            self.cssLessCheckBox.setChecked(
                Preferences.getEditor("CssLessSupport"))
            self.cssSassyCheckBox.setChecked(
                Preferences.getEditor("CssSassySupport"))
        else:
            self.cssHssCheckBox.setEnabled(False)
            self.cssLessCheckBox.setEnabled(False)
            self.cssSassyCheckBox.setEnabled(False)
        
        # D
        self.foldDCommentCheckBox.setChecked(
            Preferences.getEditor("DFoldComment"))
        self.foldDAtElseCheckBox.setChecked(
            Preferences.getEditor("DFoldAtElse"))
        self.dIndentOpeningBraceCheckBox.setChecked(
            Preferences.getEditor("DIndentOpeningBrace"))
        self.dIndentClosingBraceCheckBox.setChecked(
            Preferences.getEditor("DIndentClosingBrace"))
        
        # Gettext
        if "Gettext" in self.languages:
            self.foldPoCommentCheckBox.setChecked(
                Preferences.getEditor("PoFoldComment"))
        else:
            self.gettextGroup.setEnabled(False)
        
        # HTML
        self.foldHtmlPreprocessorCheckBox.setChecked(
            Preferences.getEditor("HtmlFoldPreprocessor"))
        self.htmlCaseSensitiveTagsCheckBox.setChecked(
            Preferences.getEditor("HtmlCaseSensitiveTags"))
        self.foldHtmlScriptCommentsCheckBox.setChecked(
            Preferences.getEditor("HtmlFoldScriptComments"))
        self.foldHtmlScriptHereDocsCheckBox.setChecked(
            Preferences.getEditor("HtmlFoldScriptHeredocs"))
        if QSCINTILLA_VERSION() >= 0x020500:
            self.htmlDjangoCheckBox.setChecked(
                Preferences.getEditor("HtmlDjangoTemplates"))
            self.htmlMakoCheckBox.setChecked(
                Preferences.getEditor("HtmlMakoTemplates"))
        else:
            self.htmlDjangoCheckBox.setEnabled(False)
            self.htmlMakoCheckBox.setEnabled(False)
        
        # Pascal
        if "Pascal" in self.languages:
            self.pascalGroup.setEnabled(True)
            self.foldPascalCommentCheckBox.setChecked(
                Preferences.getEditor("PascalFoldComment"))
            self.foldPascalPreprocessorCheckBox.setChecked(
                Preferences.getEditor("PascalFoldPreprocessor"))
            if QSCINTILLA_VERSION() >= 0x020400:
                self.pascalSmartHighlightingCheckBox.setChecked(
                    Preferences.getEditor("PascalSmartHighlighting"))
            else:
                self.pascalSmartHighlightingCheckBox.setEnabled(False)
        else:
            self.pascalGroup.setEnabled(False)
        
        # Perl
        self.foldPerlCommentCheckBox.setChecked(
            Preferences.getEditor("PerlFoldComment"))
        self.foldPerlPackagesCheckBox.setChecked(
            Preferences.getEditor("PerlFoldPackages"))
        self.foldPerlPODBlocksCheckBox.setChecked(
            Preferences.getEditor("PerlFoldPODBlocks"))
        if QSCINTILLA_VERSION() >= 0x020600:
            self.foldPerlAtElseCheckBox.setChecked(
                Preferences.getEditor("PerlFoldAtElse"))
        else:
            self.foldPerlAtElseCheckBox.setEnabled(False)
        
        # PostScript
        if "PostScript" in self.languages:
            self.postscriptGroup.setEnabled(True)
            self.psFoldAtElseCheckBox.setChecked(
                Preferences.getEditor("PostScriptFoldAtElse"))
            self.psMarkTokensCheckBox.setChecked(
                Preferences.getEditor("PostScriptTokenize"))
            self.psLevelSpinBox.setValue(
                Preferences.getEditor("PostScriptLevel"))
        else:
            self.postscriptGroup.setEnabled(False)
        
        # Povray
        self.foldPovrayCommentCheckBox.setChecked(
            Preferences.getEditor("PovFoldComment"))
        self.foldPovrayDirectivesCheckBox.setChecked(
            Preferences.getEditor("PovFoldDirectives"))
        
        # Properties
        if QSCINTILLA_VERSION() >= 0x020500:
            self.propertiesInitialSpacesCheckBox.setChecked(
                Preferences.getEditor("PropertiesInitialSpaces"))
        else:
            self.propertiesInitialSpacesCheckBox.setEnabled(False)
        
        # Python
        self.pythonBadIndentationComboBox.addItems([
            self.tr("No Warning"),
            self.tr("Inconsistent"),
            self.tr("Tabs after Spaces"),
            self.tr("Spaces"),
            self.tr("Tabs"),
        ])
        self.pythonBadIndentationComboBox.setCurrentIndex(
            Preferences.getEditor("PythonBadIndentation"))
        self.foldPythonCommentCheckBox.setChecked(
            Preferences.getEditor("PythonFoldComment"))
        self.foldPythonStringCheckBox.setChecked(
            Preferences.getEditor("PythonFoldString"))
        self.pythonAutoindentCheckBox.setChecked(
            Preferences.getEditor("PythonAutoIndent"))
        self.pythonV2UnicodeAllowedCheckBox.setChecked(
            Preferences.getEditor("PythonAllowV2Unicode"))
        self.pythonV3BinaryAllowedCheckBox.setChecked(
            Preferences.getEditor("PythonAllowV3Binary"))
        self.pythonV3BytesAllowedCheckBox.setChecked(
            Preferences.getEditor("PythonAllowV3Bytes"))
        if QSCINTILLA_VERSION() >= 0x020500:
            self.foldPythonQuotesCheckBox.setChecked(
                Preferences.getEditor("PythonFoldQuotes"))
            self.pythonStringsOverNewlineCheckBox.setChecked(
                Preferences.getEditor("PythonStringsOverNewLineAllowed"))
        else:
            self.foldPythonQuotesCheckBox.setEnabled(False)
            self.pythonStringsOverNewlineCheckBox.setEnabled(False)
        if QSCINTILLA_VERSION() >= 0x020600:
            self.pythonHighlightSubidentifierCheckBox.setChecked(
                Preferences.getEditor("PythonHighlightSubidentifier"))
        else:
            self.pythonHighlightSubidentifierCheckBox.setEnabled(False)
        
        # Ruby
        if QSCINTILLA_VERSION() >= 0x020500:
            self.foldRubyCommentCheckBox.setChecked(
                Preferences.getEditor("RubyFoldComment"))
        else:
            self.foldRubyCommentCheckBox.setEnabled(False)
        
        # SQL
        self.foldSqlCommentCheckBox.setChecked(
            Preferences.getEditor("SqlFoldComment"))
        self.sqlBackslashEscapesCheckBox.setChecked(
            Preferences.getEditor("SqlBackslashEscapes"))
        if QSCINTILLA_VERSION() >= 0x020500:
            self.sqlFoldAtElseCheckBox.setChecked(
                Preferences.getEditor("SqlFoldAtElse"))
            self.sqlFoldOnlyBeginCheckBox.setChecked(
                Preferences.getEditor("SqlFoldOnlyBegin"))
            self.sqlDottedWordsCheckBox.setChecked(
                Preferences.getEditor("SqlDottedWords"))
            self.sqlHashCommentsCheckBox.setChecked(
                Preferences.getEditor("SqlHashComments"))
            self.sqlQuotedIdentifiersCheckBox.setChecked(
                Preferences.getEditor("SqlQuotedIdentifiers"))
        else:
            self.sqlFoldAtElseCheckBox.setEnabled(False)
            self.sqlFoldOnlyBeginCheckBox.setEnabled(False)
            self.sqlDottedWordsCheckBox.setEnabled(False)
            self.sqlHashCommentsCheckBox.setEnabled(False)
            self.sqlQuotedIdentifiersCheckBox.setEnabled(False)
        
        # TCL
        if QSCINTILLA_VERSION() >= 0x020500:
            self.foldTclCommentCheckBox.setChecked(
                Preferences.getEditor("TclFoldComment"))
        else:
            self.foldTclCommentCheckBox.setEnabled(False)
        
        # TeX
        if QSCINTILLA_VERSION() >= 0x020500:
            self.foldTexCommentCheckBox.setChecked(
                Preferences.getEditor("TexFoldComment"))
            self.texProcessCommentsCheckBox.setChecked(
                Preferences.getEditor("TexProcessComments"))
            self.texProcessIfCheckBox.setChecked(
                Preferences.getEditor("TexProcessIf"))
        else:
            self.foldTexCommentCheckBox.setEnabled(False)
            self.texProcessCommentsCheckBox.setEnabled(False)
            self.texProcessIfCheckBox.setEnabled(False)
        
        # VHDL
        self.vhdlFoldCommentCheckBox.setChecked(
            Preferences.getEditor("VHDLFoldComment"))
        self.vhdlFoldAtElseCheckBox.setChecked(
            Preferences.getEditor("VHDLFoldAtElse"))
        self.vhdlFoldAtBeginCheckBox.setChecked(
            Preferences.getEditor("VHDLFoldAtBegin"))
        self.vhdlFoldAtParenthesisCheckBox.setChecked(
            Preferences.getEditor("VHDLFoldAtParenthesis"))
        
        # XML
        self.xmlSyleScriptsCheckBox.setChecked(
            Preferences.getEditor("XMLStyleScripts"))
        
        # YAML
        if "YAML" in self.languages:
            self.yamlGroup.setEnabled(True)
            self.foldYamlCommentCheckBox.setChecked(
                Preferences.getEditor("YAMLFoldComment"))
        else:
            self.yamlGroup.setEnabled(False)
        
    def save(self):
        """
        Public slot to save the Editor Properties (1) configuration.
        """
        # All
        Preferences.setEditor(
            "AllFoldCompact",
            self.allFoldCompactCheckBox.isChecked())
        
        # Bash
        Preferences.setEditor(
            "BashFoldComment",
            self.foldBashCommentCheckBox.isChecked())
        
        # CMake
        Preferences.setEditor(
            "CMakeFoldAtElse",
            self.cmakeFoldAtElseCheckBox.isChecked())
        
        # C++
        Preferences.setEditor(
            "CppFoldComment",
            self.foldCppCommentCheckBox.isChecked())
        Preferences.setEditor(
            "CppFoldPreprocessor",
            self.foldCppPreprocessorCheckBox.isChecked())
        Preferences.setEditor(
            "CppFoldAtElse",
            self.foldCppAtElseCheckBox.isChecked())
        Preferences.setEditor(
            "CppIndentOpeningBrace",
            self.cppIndentOpeningBraceCheckBox.isChecked())
        Preferences.setEditor(
            "CppIndentClosingBrace",
            self.cppIndentClosingBraceCheckBox.isChecked())
        Preferences.setEditor(
            "CppCaseInsensitiveKeywords",
            self.cppCaseInsensitiveCheckBox.isChecked())
        Preferences.setEditor(
            "CppDollarsAllowed",
            self.cppDollarAllowedCheckBox.isChecked())
        if QSCINTILLA_VERSION() >= 0x020500:
            Preferences.setEditor(
                "CppStylePreprocessor",
                self.cppStylePreprocessorCheckBox.isChecked())
        if QSCINTILLA_VERSION() >= 0x020600:
            Preferences.setEditor(
                "CppHighlightTripleQuotedStrings",
                self.cppHighlightTripleQuotedCheckBox.isChecked())
        if QSCINTILLA_VERSION() >= 0x020700:
            Preferences.setEditor(
                "CppHighlightHashQuotedStrings",
                self.cppHighlightHashQuotedCheckBox.isChecked())
        if QSCINTILLA_VERSION() >= 0x020900:
            Preferences.setEditor(
                "CppHighlightBackQuotedStrings",
                self.cppHighlightBackQuotedCheckBox.isChecked())
            Preferences.setEditor(
                "CppHighlightEscapeSequences",
                self.cppHighlightEsacepSequencesCheckBox.isChecked())
            Preferences.setEditor(
                "CppVerbatimStringEscapeSequencesAllowed",
                self.cppVerbatimStringEscapeAllowedCheckBox.isChecked())
        
        # CMake
        Preferences.setEditor(
            "CMakeFoldAtElse",
            self.cmakeFoldAtElseCheckBox.isChecked())
        
        # CoffeeScript
        if "CoffeeScript" in self.languages:
            Preferences.setEditor(
                "CoffeScriptFoldComment",
                self.foldCoffeeScriptCommentCheckBox.isChecked())
            Preferences.setEditor(
                "CoffeeScriptDollarsAllowed",
                self.coffeeScriptDollarAllowedCheckBox.isChecked())
            Preferences.setEditor(
                "CoffeeScriptStylePreprocessor",
                self.coffeeScriptStylePreprocessorCheckBox.isChecked())
        
        # CSS
        Preferences.setEditor(
            "CssFoldComment",
            self.foldCssCommentCheckBox.isChecked())
        if QSCINTILLA_VERSION() >= 0x020700:
            Preferences.setEditor(
                "CssHssSupport",
                self.cssHssCheckBox.isChecked())
            Preferences.setEditor(
                "CssLessSupport",
                self.cssLessCheckBox.isChecked())
            Preferences.setEditor(
                "CssSassySupport",
                self.cssSassyCheckBox.isChecked())
        
        # D
        Preferences.setEditor(
            "DFoldComment",
            self.foldDCommentCheckBox.isChecked())
        Preferences.setEditor(
            "DFoldAtElse",
            self.foldDAtElseCheckBox.isChecked())
        Preferences.setEditor(
            "DIndentOpeningBrace",
            self.dIndentOpeningBraceCheckBox.isChecked())
        Preferences.setEditor(
            "DIndentClosingBrace",
            self.dIndentClosingBraceCheckBox.isChecked())
        
        # Gettext
        if "Gettext" in self.languages:
            Preferences.setEditor(
                "PoFoldComment",
                self.foldPoCommentCheckBox.isChecked())
        
        # HTML
        Preferences.setEditor(
            "HtmlFoldPreprocessor",
            self.foldHtmlPreprocessorCheckBox.isChecked())
        Preferences.setEditor(
            "HtmlCaseSensitiveTags",
            self.htmlCaseSensitiveTagsCheckBox.isChecked())
        Preferences.setEditor(
            "HtmlFoldScriptComments",
            self.foldHtmlScriptCommentsCheckBox.isChecked())
        Preferences.setEditor(
            "HtmlFoldScriptHeredocs",
            self.foldHtmlScriptHereDocsCheckBox.isChecked())
        if QSCINTILLA_VERSION() >= 0x020500:
            Preferences.setEditor(
                "HtmlDjangoTemplates",
                self.htmlDjangoCheckBox.isChecked())
            Preferences.setEditor(
                "HtmlMakoTemplates",
                self.htmlMakoCheckBox.isChecked())
        
        # Pascal
        if "Pascal" in self.languages:
            Preferences.setEditor(
                "PascalFoldComment",
                self.foldPascalCommentCheckBox.isChecked())
            Preferences.setEditor(
                "PascalFoldPreprocessor",
                self.foldPascalPreprocessorCheckBox.isChecked())
            Preferences.setEditor(
                "PascalSmartHighlighting",
                self.pascalSmartHighlightingCheckBox.isChecked())
        
        # Perl
        Preferences.setEditor(
            "PerlFoldComment",
            self.foldPerlCommentCheckBox.isChecked())
        Preferences.setEditor(
            "PerlFoldPackages",
            self.foldPerlPackagesCheckBox.isChecked())
        Preferences.setEditor(
            "PerlFoldPODBlocks",
            self.foldPerlPODBlocksCheckBox.isChecked())
        if QSCINTILLA_VERSION() >= 0x020600:
            Preferences.setEditor(
                "PerlFoldAtElse",
                self.foldPerlAtElseCheckBox.isChecked())
        
        # PostScript
        if "PostScript" in self.languages:
            Preferences.setEditor(
                "PostScriptFoldAtElse",
                self.psFoldAtElseCheckBox.isChecked())
            Preferences.setEditor(
                "PostScriptTokenize",
                self.psMarkTokensCheckBox.isChecked())
            Preferences.setEditor(
                "PostScriptLevel",
                self.psLevelSpinBox.value())
        
        # Povray
        Preferences.setEditor(
            "PovFoldComment",
            self.foldPovrayCommentCheckBox.isChecked())
        Preferences.setEditor(
            "PovFoldDirectives",
            self.foldPovrayDirectivesCheckBox.isChecked())
        
        # Properties
        if QSCINTILLA_VERSION() >= 0x020500:
            Preferences.setEditor(
                "PropertiesInitialSpaces",
                self.propertiesInitialSpacesCheckBox.isChecked())
        
        # Python
        Preferences.setEditor(
            "PythonFoldComment",
            self.foldPythonCommentCheckBox.isChecked())
        Preferences.setEditor(
            "PythonFoldString",
            self.foldPythonStringCheckBox.isChecked())
        Preferences.setEditor(
            "PythonBadIndentation",
            self.pythonBadIndentationComboBox.currentIndex())
        Preferences.setEditor(
            "PythonAutoIndent",
            self.pythonAutoindentCheckBox.isChecked())
        Preferences.setEditor(
            "PythonAllowV2Unicode",
            self.pythonV2UnicodeAllowedCheckBox.isChecked())
        Preferences.setEditor(
            "PythonAllowV3Binary",
            self.pythonV3BinaryAllowedCheckBox.isChecked())
        Preferences.setEditor(
            "PythonAllowV3Bytes",
            self.pythonV3BytesAllowedCheckBox.isChecked())
        if QSCINTILLA_VERSION() >= 0x020500:
            Preferences.setEditor(
                "PythonFoldQuotes",
                self.foldPythonQuotesCheckBox.isChecked())
            Preferences.setEditor(
                "PythonStringsOverNewLineAllowed",
                self.pythonStringsOverNewlineCheckBox.isChecked())
        if QSCINTILLA_VERSION() >= 0x020600:
            Preferences.setEditor(
                "PythonHighlightSubidentifier",
                self.pythonHighlightSubidentifierCheckBox.isChecked())
        
        # Ruby
        if QSCINTILLA_VERSION() >= 0x020500:
            Preferences.setEditor(
                "RubyFoldComment",
                self.foldRubyCommentCheckBox.isChecked())
        
        # SQL
        Preferences.setEditor(
            "SqlFoldComment",
            self.foldSqlCommentCheckBox.isChecked())
        Preferences.setEditor(
            "SqlBackslashEscapes",
            self.sqlBackslashEscapesCheckBox.isChecked())
        if QSCINTILLA_VERSION() >= 0x020500:
            Preferences.setEditor(
                "SqlFoldAtElse",
                self.sqlFoldAtElseCheckBox.isChecked())
            Preferences.setEditor(
                "SqlFoldOnlyBegin",
                self.sqlFoldOnlyBeginCheckBox.isChecked())
            Preferences.setEditor(
                "SqlDottedWords",
                self.sqlDottedWordsCheckBox.isChecked())
            Preferences.setEditor(
                "SqlHashComments",
                self.sqlHashCommentsCheckBox.isChecked())
            Preferences.setEditor(
                "SqlQuotedIdentifiers",
                self.sqlQuotedIdentifiersCheckBox.isChecked())
        
        # TCL
        if QSCINTILLA_VERSION() >= 0x020500:
            Preferences.setEditor(
                "TclFoldComment",
                self.foldTclCommentCheckBox.isChecked())
        
        # TeX
        if QSCINTILLA_VERSION() >= 0x020500:
            Preferences.setEditor(
                "TexFoldComment",
                self.foldTexCommentCheckBox.isChecked())
            Preferences.setEditor(
                "TexProcessComments",
                self.texProcessCommentsCheckBox.isChecked())
            Preferences.setEditor(
                "TexProcessIf",
                self.texProcessIfCheckBox.isChecked())
        
        # VHDL
        Preferences.setEditor(
            "VHDLFoldComment",
            self.vhdlFoldCommentCheckBox.isChecked())
        Preferences.setEditor(
            "VHDLFoldAtElse",
            self.vhdlFoldAtElseCheckBox.isChecked())
        Preferences.setEditor(
            "VHDLFoldAtBegin",
            self.vhdlFoldAtBeginCheckBox.isChecked())
        Preferences.setEditor(
            "VHDLFoldAtParenthesis",
            self.vhdlFoldAtParenthesisCheckBox.isChecked())
        
        # XML
        Preferences.setEditor(
            "XMLStyleScripts",
            self.xmlSyleScriptsCheckBox.isChecked())
        
        # YAML
        if "YAML" in self.languages:
            Preferences.setEditor(
                "YAMLFoldComment",
                self.foldYamlCommentCheckBox.isChecked())


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = EditorPropertiesPage(dlg.getLexers())
    return page
