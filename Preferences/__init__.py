# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Package implementing the preferences interface.

The preferences interface consists of a class, which defines the default
values for all configuration items and stores the actual values. These
values are read and written to the eric6 preferences file by module
functions. The data is stored in a file in a subdirectory of the users home
directory. The individual configuration data is accessed by accessor functions
defined on the module level. The module is simply imported wherever it is
needed with the statement 'import Preferences'. Do not use
'from Preferences import *' to import it.
"""

from __future__ import unicode_literals
try:
    basestring    # __IGNORE_WARNING__
except NameError:
    basestring = str

import os
import fnmatch
import shutil
import json
import sys

from PyQt5.QtCore import QDir, QPoint, QLocale, QSettings, QFileInfo, \
    QCoreApplication, QByteArray, QSize, QUrl, Qt, QLibraryInfo
from PyQt5.QtGui import QColor, QFont, QPalette
from PyQt5.QtWidgets import QInputDialog, QApplication
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtWebKit import QWebSettings
from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from E5Gui import E5FileDialog

from E5Network.E5Ftp import E5FtpProxyType

from Globals import settingsNameOrganization, settingsNameGlobal, \
    settingsNameRecent, isWindowsPlatform, findPythonInterpreters, \
    getPyQt5ModulesDirectory

from Project.ProjectBrowserFlags import SourcesBrowserFlag, FormsBrowserFlag, \
    ResourcesBrowserFlag, TranslationsBrowserFlag, InterfacesBrowserFlag, \
    OthersBrowserFlag, AllBrowsersFlag

from Helpviewer.FlashCookieManager.FlashCookieUtilities import \
    flashDataPathForOS


class Prefs(object):
    """
    A class to hold all configuration items for the application.
    """
    # defaults for the variables window
    varDefaults = {
        "LocalsFilter": "[]",
        "GlobalsFilter": "[]"
    }
    
    # defaults for the debugger
    debuggerDefaults = {
        "RemoteDbgEnabled": False,
        "RemoteHost": "",
        "RemoteExecution": "",
        "PassiveDbgEnabled": False,
        "PassiveDbgPort": 42424,
        "PassiveDbgType": "Python",
        "AutomaticReset": False,
        "Autosave": True,
        "ThreeStateBreakPoints": False,
        "SuppressClientExit": False,
        "BreakAlways": False,
        "ShowExceptionInShell": True,
        "PythonInterpreter": "",
        "Python3Interpreter": "",
        "RubyInterpreter": "",
        "DebugClientType": "standard",
        # supported "standard", "threaded", "custom"
        "DebugClient": "",
        "DebugClientType3": "standard",
        # supported "standard", "threaded", "custom"
        "DebugClient3": "",
        "DebugEnvironmentReplace": False,
        "DebugEnvironment": "",
        "PythonRedirect": True,
        "PythonNoEncoding": False,
        "Python3Redirect": True,
        "Python3NoEncoding": False,
        "RubyRedirect": True,
        "ConsoleDbgEnabled": False,
        "ConsoleDbgCommand": "",
        "PathTranslation": False,
        "PathTranslationRemote": "",
        "PathTranslationLocal": "",
        "NetworkInterface": "127.0.0.1",
        "AutoViewSourceCode": False,
    }
    debuggerDefaults["AllowedHosts"] = ["127.0.0.1", "::1%0"]
    if sys.version_info[0] == 2:
        debuggerDefaults["PythonExtensions"] = ".py .pyw .py2 .pyw2 .ptl"
        # space separated list of Python extensions
        debuggerDefaults["Python3Extensions"] = ".py .pyw .py3 .pyw3"
        # space separated list of Python3 extensions
    else:
        debuggerDefaults["PythonExtensions"] = ".py2 .pyw2 .ptl"
        # space separated list of Python extensions
        debuggerDefaults["Python3Extensions"] = ".py .pyw .py3 .pyw3"
        # space separated list of Python3 extensions
    
    # defaults for the UI settings
    uiDefaults = {
        "Language": "System",
        "Style": "System",
        "StyleSheet": "",
        "ViewManager": "tabview",
        "LayoutType": "Sidebars",
        "SidebarDelay": 200,
        # allowed values are "Toolboxes" and "Sidebars"
        "LayoutShellEmbedded": 0,           # 0 = separate
                                            # 1 = embedded in debug browser
        "LayoutFileBrowserEmbedded": 0,     # 0 = separate
                                            # 1 = embedded in debug browser
                                            # 2 = embedded in project browser
        "BrowsersListFoldersFirst": True,
        "BrowsersHideNonPublic": False,
        "BrowsersListContentsByOccurrence": False,
        "BrowsersListHiddenFiles": False,
        "BrowsersFileFilters": "*.py[co];*.so;*.dll",
        "LogViewerAutoRaise": True,
        "LogViewerStdoutFilter": [],
        "LogViewerStderrFilter": [],
        "LogViewerStdxxxFilter": [],
        "SingleApplicationMode": False,
        "CaptionShowsFilename": True,
        "CaptionFilenameLength": 100,
        "RecentNumber": 9,
        "TopLeftByLeft": True,
        "BottomLeftByLeft": False,
        "TopRightByRight": True,
        "BottomRightByRight": False,
        "TabViewManagerFilenameLength": 40,
        "TabViewManagerFilenameOnly": True,
        "ShowFilePreview": True,
        "ShowFilePreviewJS": True,
        "ShowFilePreviewSSI": True,
        "ViewProfiles2": {
            "edit": [
                # saved state main window with toolbox windows (0)
                QByteArray(),
                # visibility of the toolboxes/sidebars (1)
                # left, bottom, right
                [True, True, True],
                # saved states of the splitters and sidebars of the
                # sidebars layout (2)
                # left splitter, vertical splitter, left sidebar,
                # bottom sidebar, right splitter, right sidebar
                [QByteArray(), QByteArray(), QByteArray(),
                 QByteArray(), QByteArray(), QByteArray()],
            ],
            "debug": [
                # saved state main window with toolbox windows (0)
                QByteArray(),
                # visibility of the toolboxes/sidebars (1)
                # left, bottom, right
                [False, True, True],
                # saved states of the splitters and sidebars of the
                # sidebars layout (2)
                # left splitter, vertical splitter, left sidebar,
                # bottom sidebar, right splitter, right sidebar
                [QByteArray(), QByteArray(), QByteArray(),
                 QByteArray(), QByteArray(), QByteArray()],
            ],
        },
        "ToolbarManagerState": QByteArray(),
        "PreviewSplitterState": QByteArray(),
        "ShowSplash": True,
        "SingleCloseButton": False,
        "SplitOrientationVertical": False,
        
        "PerformVersionCheck": 4,
        # 0 = off
        # 1 = at startup
        # 2 = daily
        # 3 = weekly
        # 4 = monthly
        "UseProxy": False,
        "UseSystemProxy": True,
        "UseHttpProxyForAll": False,
        "ProxyHost/Http": "",
        "ProxyHost/Https": "",
        "ProxyHost/Ftp": "",
        "ProxyPort/Http": 80,
        "ProxyPort/Https": 443,
        "ProxyPort/Ftp": 21,
        "ProxyUser/Http": "",
        "ProxyUser/Https": "",
        "ProxyUser/Ftp": "",
        "ProxyPassword/Http": "",
        "ProxyPassword/Https": "",
        "ProxyPassword/Ftp": "",
        "ProxyType/Ftp": E5FtpProxyType.NoProxy,
        "ProxyAccount/Ftp": "",
        "ProxyExceptions": "localhost,127.0.0.,::1",
        
        "PluginRepositoryUrl6":
        "http://eric-ide.python-projects.org/plugins6/repository.xml",
        "VersionsUrls6": [
            "http://die-offenbachs.homelinux.org:48888/eric/versions/"
            "versions6",
            "http://eric-ide.python-projects.org/versions/versions6",
        ],
        
        "OpenOnStartup": 0,        # 0 = nothing
                                   # 1 = last file
                                   # 2 = last project
                                   # 3 = last multiproject
                                   # 4 = last global session
        
        "DownloadPath": "",
        "RequestDownloadFilename": True,
        "CheckErrorLog": True,
        
        "LogStdErrColour": QColor(Qt.red),
        "NotificationsEnabled": True,
        "NotificationTimeout": 5,       # time in seconds the notification
                                        # is shown
        "NotificationPosition": QPoint(10, 10),
        "TextMimeTypes": [
            "application/bookmarks.xbel",
            "application/x-xbel",
            "application/opensearchdescription+xml",
            "application/x-actionscript",
            "application/x-actionscript3",
            "application/x-awk",
            "application/x-sh",
            "application/x-shellscript",
            "application/x-shell-session",
            "application/x-dos-batch",
            "application/x-befunge",
            "application/x-brainfuck",
            "application/x-javascript+cheetah",
            "application/x-javascript+spitfire",
            "application/x-cheetah",
            "application/x-spitfire",
            "application/xml+cheetah",
            "application/xml+spitfire",
            "application/x-clojure",
            "application/x-coldfusion",
            "application/x-cython",
            "application/x-django-templating",
            "application/x-jinja",
            "application/xml-dtd",
            "application/x-ecl",
            "application/x-ruby-templating",
            "application/x-evoque",
            "application/xml+evoque",
            "application/x-fantom",
            "application/x-genshi",
            "application/x-kid",
            "application/x-genshi-text",
            "application/x-gettext",
            "application/x-troff",
            "application/xhtml+xml",
            "application/x-php",
            "application/x-httpd-php",
            "application/x-httpd-php3",
            "application/x-httpd-php4",
            "application/x-httpd-php5",
            "application/x-hybris",
            "application/x-javascript+django",
            "application/x-javascript+jinja",
            "application/x-javascript+ruby",
            "application/x-javascript+genshi",
            "application/javascript",
            "application/x-javascript",
            "application/x-javascript+php",
            "application/x-javascript+smarty",
            "application/json",
            "application/x-jsp",
            "application/x-julia",
            "application/x-httpd-lasso",
            "application/x-httpd-lasso[89]",
            "application/x-httpd-lasso8",
            "application/x-httpd-lasso9",
            "application/x-javascript+lasso",
            "application/xml+lasso",
            "application/x-lua",
            "application/x-javascript+mako",
            "application/x-mako",
            "application/xml+mako",
            "application/x-gooddata-maql",
            "application/x-mason",
            "application/x-moonscript",
            "application/x-javascript+myghty",
            "application/x-myghty",
            "application/xml+myghty",
            "application/x-newlisp",
            "application/x-openedge",
            "application/x-perl",
            "application/postscript",
            "application/x-pypylog",
            "application/x-python3",
            "application/x-python",
            "application/x-qml",
            "application/x-racket",
            "application/x-pygments-tokens",
            "application/x-ruby",
            "application/x-standardml",
            "application/x-scheme",
            "application/x-sh-session",
            "application/x-smarty",
            "application/x-ssp",
            "application/x-tcl",
            "application/x-csh",
            "application/x-urbiscript",
            "application/xml+velocity",
            "application/xquery",
            "application/xml+django",
            "application/xml+jinja",
            "application/xml+ruby",
            "application/xml",
            "application/rss+xml",
            "application/atom+xml",
            "application/xml+php",
            "application/xml+smarty",
            "application/xsl+xml",
            "application/xslt+xml",
            "application/x-desktop",
            
            "image/svg+xml",
        ],
    }
    
    iconsDefaults = {
        "Path": [],
    }
    
    # defaults for the cooperation settings
    cooperationDefaults = {
        "ServerPort": 42000,
        "AutoStartServer": False,
        "TryOtherPorts": True,
        "MaxPortsToTry": 100,
        "AutoAcceptConnections": False,
        "BannedUsers": [],
    }
    
    # defaults for the editor settings
    editorDefaults = {
        "AutosaveInterval": 0,
        "TabWidth": 4,
        "IndentWidth": 4,
        "IndentationGuides": True,
        "UnifiedMargins": False,
        "LinenoMargin": True,
        "FoldingMargin": True,
        "FoldingStyle": 1,
        "TabForIndentation": False,
        "TabIndents": True,
        "ConvertTabsOnLoad": False,
        "AutomaticEOLConversion": True,
        "ShowWhitespace": False,
        "WhitespaceSize": 1,
        "ShowEOL": False,
        "UseMonospacedFont": False,
        "WrapLongLinesMode": QsciScintilla.WrapNone,
        "WrapVisualFlag": QsciScintilla.WrapFlagNone,
        "WarnFilesize": 512,
        "ClearBreaksOnClose": True,
        "StripTrailingWhitespace": False,
        "CommentColumn0": True,
        "OverrideEditAreaColours": False,
        
        "EdgeMode": QsciScintilla.EdgeNone,
        "EdgeColumn": 80,
        
        "AutoIndentation": True,
        "BraceHighlighting": True,
        "CreateBackupFile": False,
        "CaretLineVisible": False,
        "CaretLineAlwaysVisible": False,
        "CaretWidth": 1,
        "ColourizeSelText": False,
        "CustomSelectionColours": False,
        "ExtendSelectionToEol": False,
        
        "AutoPrepareAPIs": False,
        
        "AutoCompletionEnabled": False,
        "AutoCompletionCaseSensitivity": True,
        "AutoCompletionReplaceWord": False,
        "AutoCompletionShowSingle": False,
        "AutoCompletionSource": QsciScintilla.AcsDocument,
        "AutoCompletionThreshold": 2,
        "AutoCompletionFillups": False,
        "AutoCompletionScintillaOnFail": False,
        # show QScintilla completions, if plug-in fails
        
        "CallTipsEnabled": False,
        "CallTipsVisible": 0,
        "CallTipsStyle": QsciScintilla.CallTipsNoContext,
        "CallTipsScintillaOnFail": False,
        # show QScintilla calltips, if plug-in fails
        
        "AutoCheckSyntax": True,
        "OnlineSyntaxCheck": True,
        "OnlineSyntaxCheckInterval": 5,
        
        "OnlineChangeTrace": True,
        "OnlineChangeTraceInterval": 500,      # 1000 milliseconds
        
        "AutoReopen": False,
        
        "AnnotationsEnabled": True,
        
        "MiniContextMenu": False,
        
        "SearchMarkersEnabled": True,
        "QuickSearchMarkersEnabled": True,
        "MarkOccurrencesEnabled": True,
        "MarkOccurrencesTimeout": 500,     # 500 milliseconds
        "AdvancedEncodingDetection": True,
        
        "SpellCheckingEnabled": True,
        "AutoSpellCheckingEnabled": True,
        "AutoSpellCheckChunkSize": 30,
        "SpellCheckStringsOnly": True,
        "SpellCheckingMinWordSize": 3,
        "SpellCheckingDefaultLanguage": "en_US",
        "SpellCheckingPersonalWordList": "",
        "SpellCheckingPersonalExcludeList": "",
        
        "DefaultEncoding": "utf-8",
        "DefaultOpenFilter": QCoreApplication.translate(
            'Lexers', 'Python Files (*.py *.py2 *.py3)'),
        "DefaultSaveFilter": QCoreApplication.translate(
            'Lexers', "Python3 Files (*.py)"),
        "AdditionalOpenFilters": [],
        "AdditionalSaveFilters": [],
        
        "ZoomFactor": 0,
        
        "PreviewHtmlFileNameExtensions": ["html", "htm", "svg", "asp", "kid"],
        "PreviewMarkdownFileNameExtensions": ["md", "markdown"],
        "PreviewRestFileNameExtensions": ["rst"],
        "PreviewQssFileNameExtensions": ["qss"],
        "PreviewRestUseSphinx": False,
        
        "VirtualSpaceOptions": QsciScintilla.SCVS_NONE,
        
        "MouseClickHandlersEnabled": True,
        
        # All (most) lexers
        "AllFoldCompact": True,
        
        # Bash specifics
        "BashFoldComment": True,
        
        # CMake specifics
        "CMakeFoldAtElse": False,
        
        # C++ specifics
        "CppCaseInsensitiveKeywords": False,
        "CppFoldComment": True,
        "CppFoldPreprocessor": False,
        "CppFoldAtElse": False,
        "CppIndentOpeningBrace": False,
        "CppIndentClosingBrace": False,
        "CppDollarsAllowed": True,
        "CppStylePreprocessor": False,
        "CppHighlightTripleQuotedStrings": False,
        "CppHighlightHashQuotedStrings": False,
        "CppHighlightBackQuotedStrings": False,
        "CppHighlightEscapeSequences": False,
        "CppVerbatimStringEscapeSequencesAllowed": False,
        
        # CoffeeScript specifics
        "CoffeScriptFoldComment": False,
        "CoffeeScriptDollarsAllowed": True,
        "CoffeeScriptStylePreprocessor": False,
        
        # CSS specifics
        "CssFoldComment": True,
        "CssHssSupport": False,
        "CssLessSupport": False,
        "CssSassySupport": False,
        
        # D specifics
        "DFoldComment": True,
        "DFoldAtElse": False,
        "DIndentOpeningBrace": False,
        "DIndentClosingBrace": False,
        
        # Gettext specifics
        "PoFoldComment": False,
        
        # HTML specifics
        "HtmlFoldPreprocessor": False,
        "HtmlFoldScriptComments": False,
        "HtmlFoldScriptHeredocs": False,
        "HtmlCaseSensitiveTags": False,
        "HtmlDjangoTemplates": False,
        "HtmlMakoTemplates": False,
        
        # Pascal specifics
        "PascalFoldComment": True,
        "PascalFoldPreprocessor": False,
        "PascalSmartHighlighting": True,
        
        # Perl specifics
        "PerlFoldComment": True,
        "PerlFoldPackages": True,
        "PerlFoldPODBlocks": True,
        "PerlFoldAtElse": False,
        
        # PostScript specifics
        "PostScriptTokenize": False,
        "PostScriptLevel": 3,
        "PostScriptFoldAtElse": False,
        
        # Povray specifics
        "PovFoldComment": True,
        "PovFoldDirectives": False,
        
        # Properties specifics
        "PropertiesInitialSpaces": True,
        
        # Python specifics
        "PythonBadIndentation": QsciLexerPython.Inconsistent,
        "PythonFoldComment": True,
        "PythonFoldString": True,
        "PythonAutoIndent": True,
        "PythonAllowV2Unicode": True,
        "PythonAllowV3Binary": True,
        "PythonAllowV3Bytes": True,
        "PythonFoldQuotes": False,
        "PythonStringsOverNewLineAllowed": False,
        "PythonHighlightSubidentifier": True,
        
        # Ruby specifics
        "RubyFoldComment": False,
        
        # SQL specifics
        "SqlFoldComment": True,
        "SqlBackslashEscapes": False,
        "SqlDottedWords": False,
        "SqlFoldAtElse": False,
        "SqlFoldOnlyBegin": False,
        "SqlHashComments": False,
        "SqlQuotedIdentifiers": False,
        
        # TCL specifics
        "TclFoldComment": False,
        
        # TeX specifics
        "TexFoldComment": False,
        "TexProcessComments": False,
        "TexProcessIf": True,
        
        # VHDL specifics
        "VHDLFoldComment": True,
        "VHDLFoldAtElse": True,
        "VHDLFoldAtBegin": True,
        "VHDLFoldAtParenthesis": True,
        
        # XML specifics
        "XMLStyleScripts": True,
        
        # YAML specifics
        "YAMLFoldComment": False,
    }
    
    if isWindowsPlatform():
        editorDefaults["EOLMode"] = QsciScintilla.EolWindows
    else:
        editorDefaults["EOLMode"] = QsciScintilla.EolUnix
    
    try:
        # since QScintilla 2.7.0
        editorDefaults["CallTipsPosition"] = QsciScintilla.CallTipsBelowText
    except AttributeError:
        editorDefaults["CallTipsPosition"] = 0
    
    editorColourDefaults = {
        "CurrentMarker": QColor(Qt.yellow),
        "ErrorMarker": QColor(Qt.red),
        "MatchingBrace": QColor(Qt.green),
        "MatchingBraceBack": QColor(Qt.white),
        "NonmatchingBrace": QColor(Qt.red),
        "NonmatchingBraceBack": QColor(Qt.white),
        "CallTipsBackground": QColor(Qt.white),
        "CaretForeground": QColor(Qt.black),
        "CaretLineBackground": QColor(Qt.white),
        "Edge": QColor(Qt.lightGray),
        "SelectionBackground": QColor(Qt.black),
        "SelectionForeground": QColor(Qt.white),
        "SearchMarkers": QColor(Qt.blue),
        "MarginsBackground": QColor(Qt.lightGray),
        "MarginsForeground": QColor(Qt.black),
        "FoldmarginBackground": QColor("#e6e6e6"),
        "FoldMarkersForeground": QColor(Qt.white),
        "FoldMarkersBackground": QColor(Qt.black),
        "SpellingMarkers": QColor(Qt.red),
        "AnnotationsWarningForeground": QColor("#606000"),
        "AnnotationsWarningBackground": QColor("#ffffd0"),
        "AnnotationsErrorForeground": QColor("#600000"),
        "AnnotationsErrorBackground": QColor("#ffd0d0"),
        "AnnotationsStyleForeground": QColor("#000060"),
        "AnnotationsStyleBackground": QColor("#d0d0ff"),
        "WhitespaceForeground": QColor(Qt.darkGray),
        "WhitespaceBackground": QColor(Qt.white),
        "OnlineChangeTraceMarkerUnsaved": QColor("#ff8888"),
        "OnlineChangeTraceMarkerSaved": QColor("#88ff88"),
        "IndentationGuidesBackground": QColor(Qt.white),
        "IndentationGuidesForeground": QColor(Qt.black),
        # colors for the marker map
        "BookmarksMap": QColor("#f8c700"),
        "ErrorsMap": QColor("#dd0000"),
        "WarningsMap": QColor("#606000"),
        "BreakpointsMap": QColor("#f55c07"),
        "TasksMap": QColor("#2278f8"),
        "CoverageMap": QColor("#ad3636"),
        "ChangesMap": QColor("#00b000"),
        "CurrentMap": QColor("#000000"),
        "SearchMarkersMap": QColor(Qt.blue),
        "MarkerMapBackground": QColor("#e7e7e7"),
    }
    
    editorOtherFontsDefaults = {
        "MarginsFont": "Sans Serif,10,-1,5,50,0,0,0,0,0",
        "DefaultFont": "Sans Serif,10,-1,5,50,0,0,0,0,0",
        "MonospacedFont": "Courier,10,-1,5,50,0,0,0,0,0",
    }
    
    editorTypingDefaults = {
        "Python/EnabledTypingAids": True,
        "Python/InsertClosingBrace": True,
        "Python/IndentBrace": False,
        "Python/SkipBrace": True,
        "Python/InsertQuote": True,
        "Python/DedentElse": True,
        "Python/DedentExcept": True,
        "Python/Py24StyleTry": True,
        "Python/InsertImport": True,
        "Python/InsertSelf": True,
        "Python/InsertBlank": True,
        "Python/ColonDetection": True,
        "Python/DedentDef": False,
        
        "Ruby/EnabledTypingAids": True,
        "Ruby/InsertClosingBrace": True,
        "Ruby/IndentBrace": True,
        "Ruby/SkipBrace": True,
        "Ruby/InsertQuote": True,
        "Ruby/InsertBlank": True,
        "Ruby/InsertHereDoc": True,
        "Ruby/InsertInlineDoc": True,
    }
    
    editorExporterDefaults = {
        "HTML/WYSIWYG": True,
        "HTML/Folding": False,
        "HTML/OnlyStylesUsed": False,
        "HTML/FullPathAsTitle": False,
        "HTML/UseTabs": False,
        
        "RTF/WYSIWYG": True,
        "RTF/UseTabs": False,
        "RTF/Font": "Courier New,10,-1,5,50,0,0,0,0,0",
        
        "PDF/Magnification": 0,
        "PDF/Font": "Helvetica",  # must be Courier, Helvetica or Times
        "PDF/PageSize": "A4",         # must be A4 or Letter
        "PDF/MarginLeft": 36,
        "PDF/MarginRight": 36,
        "PDF/MarginTop": 36,
        "PDF/MarginBottom": 36,
        
        "TeX/OnlyStylesUsed": False,
        "TeX/FullPathAsTitle": False,
        
        "ODT/WYSIWYG": True,
        "ODT/OnlyStylesUsed": False,
        "ODT/UseTabs": False,
    }
    
    # defaults for the printer settings
    printerDefaults = {
        "PrinterName": "",
        "ColorMode": True,
        "FirstPageFirst": True,
        "Magnification": -3,
        "Orientation": 0,
        "PageSize": 0,
        "HeaderFont": "Serif,10,-1,5,50,0,0,0,0,0",
        "LeftMargin": 1.0,
        "RightMargin": 1.0,
        "TopMargin": 1.0,
        "BottomMargin": 1.0,
    }
    
    # defaults for the project settings
    projectDefaults = {
        "SearchNewFiles": False,
        "SearchNewFilesRecursively": False,
        "AutoIncludeNewFiles": False,
        "AutoLoadSession": False,
        "AutoSaveSession": False,
        "SessionAllBreakpoints": False,
        "XMLTimestamp": True,
        "AutoCompileForms": False,
        "AutoCompileResources": False,
        "AutoLoadDbgProperties": False,
        "AutoSaveDbgProperties": False,
        "HideGeneratedForms": False,
        "FollowEditor": True,
        "FollowCursorLine": True,
        "AutoPopulateItems": True,
        "RecentNumber": 9,
        "DeterminePyFromProject": True,
    }
    
    # defaults for the multi project settings
    multiProjectDefaults = {
        "OpenMasterAutomatically": True,
        "XMLTimestamp": True,
        "RecentNumber": 9,
        "Workspace": "",
    }
    
    # defaults for the project browser flags settings
    projectBrowserFlagsDefaults = {
        "Qt4": (
            SourcesBrowserFlag |
            FormsBrowserFlag |
            ResourcesBrowserFlag |
            TranslationsBrowserFlag |
            InterfacesBrowserFlag |
            OthersBrowserFlag),
        "Qt4C": (
            SourcesBrowserFlag |
            ResourcesBrowserFlag |
            TranslationsBrowserFlag |
            InterfacesBrowserFlag |
            OthersBrowserFlag),
        "PyQt5": (
            SourcesBrowserFlag |
            FormsBrowserFlag |
            ResourcesBrowserFlag |
            TranslationsBrowserFlag |
            InterfacesBrowserFlag |
            OthersBrowserFlag),
        "PyQt5C": (
            SourcesBrowserFlag |
            ResourcesBrowserFlag |
            TranslationsBrowserFlag |
            InterfacesBrowserFlag |
            OthersBrowserFlag),
        "E6Plugin": (
            SourcesBrowserFlag |
            FormsBrowserFlag |
            ResourcesBrowserFlag |
            TranslationsBrowserFlag |
            InterfacesBrowserFlag |
            OthersBrowserFlag),
        "Console": (
            SourcesBrowserFlag |
            InterfacesBrowserFlag |
            OthersBrowserFlag),
        "Other": (
            SourcesBrowserFlag |
            InterfacesBrowserFlag |
            OthersBrowserFlag),
        "PySide": (
            SourcesBrowserFlag |
            FormsBrowserFlag |
            ResourcesBrowserFlag |
            TranslationsBrowserFlag |
            InterfacesBrowserFlag |
            OthersBrowserFlag),
        "PySideC": (
            SourcesBrowserFlag |
            ResourcesBrowserFlag |
            TranslationsBrowserFlag |
            InterfacesBrowserFlag |
            OthersBrowserFlag),
    }
    
    # defaults for the project browser colour settings
    projectBrowserColourDefaults = {
        "Highlighted": QColor(Qt.red),
        
        "VcsAdded": QColor(Qt.blue),
        "VcsConflict": QColor(Qt.red),
        "VcsModified": QColor(Qt.yellow),
        "VcsReplaced": QColor(Qt.cyan),
        "VcsUpdate": QColor(Qt.green),
        "VcsRemoved": QColor(Qt.magenta)
    }
    
    # defaults for the help settings
    helpDefaults = {
        "HelpViewerType": 1,      # this corresponds with the radio button id
        "CustomViewer": "",
        "PythonDocDir": "",
        "Python2DocDir": "",
        "QtDocDir": "",
        "Qt4DocDir": "",
        "Qt5DocDir": "",
        "PyQt4DocDir": "",
        "PyQt5DocDir": "",
        "PySideDocDir": "",
        "SingleHelpWindow": True,
        "SaveGeometry": True,
        "HelpViewerState": QByteArray(),
        "WebSearchSuggestions": True,
        "WebSearchEngine": "Google",
        "WebSearchKeywords": [],    # array of two tuples (keyword,
                                    # search engine name)
        "DiskCacheEnabled": True,
        "DiskCacheSize": 50,        # 50 MB
        "CachePolicy": QNetworkRequest.PreferNetwork,
        "AcceptCookies": 2,         # CookieJar.AcceptOnlyFromSitesNavigatedTo
        "KeepCookiesUntil": 0,      # CookieJar.KeepUntilExpire
        "FilterTrackingCookies": True,
        "PrintBackgrounds": False,
        "StartupBehavior": 1,      # show speed dial
        "HomePage": "eric:home",
        "HistoryLimit": 30,
        "DefaultScheme": "file://",
        "AdBlockEnabled": False,
        "AdBlockSubscriptions": [],
        "AdBlockUpdatePeriod": 1,
        "AdBlockExceptions": [],
        "OfflineStorageDatabaseQuota": 50,     # 50 MB
        "UserAgent": "",
        "ShowPreview": True,
        "DownloadManagerRemovePolicy": 0,      # never delete downloads
        "DownloadManagerSize": QSize(400, 300),
        "DownloadManagerPosition": QPoint(),
        "DownloadManagerDownloads": [],
        "AccessKeysEnabled": True,
        "VirusTotalEnabled": False,
        "VirusTotalServiceKey": "",
        "VirusTotalSecure": True,
        "SearchLanguage": QLocale().language(),
        "DoNotTrack": False,
        "SendReferer": True,
        "SendRefererWhitelist": ["qt-apps.org", "kde-apps.org"],
        "NoCacheHosts": ["qt-project.org"],
        "RssFeeds": [],
        "SyncEnabled": False,
        "SyncBookmarks": True,
        "SyncHistory": True,
        "SyncPasswords": False,
        "SyncUserAgents": True,
        "SyncSpeedDial": True,
        "SyncEncryptData": False,
        "SyncEncryptionKey": "",
        "SyncEncryptionKeyLength": 32,      # 16, 24 or 32
        "SyncEncryptPasswordsOnly": False,
        "SyncType": 0,
        "SyncFtpServer": "",
        "SyncFtpUser": "",
        "SyncFtpPassword": "",
        "SyncFtpPath": "",
        "SyncFtpPort": 21,
        "SyncFtpIdleTimeout": 30,
        "SyncDirectoryPath": "",
        "WarnOnMultipleClose": True,
        "ClickToFlashEnabled": False,
        "ClickToFlashWhitelist": [],
        "PimFullName": "",
        "PimFirstName": "",
        "PimLastName": "",
        "PimEmail": "",
        "PimPhone": "",
        "PimMobile": "",
        "PimAddress": "",
        "PimCity": "",
        "PimZip": "",
        "PimState": "",
        "PimCountry": "",
        "PimHomePage": "",
        "PimSpecial1": "",
        "PimSpecial2": "",
        "PimSpecial3": "",
        "PimSpecial4": "",
        "GreaseMonkeyDisabledScripts": [],
        # Flash Cookie Manager
        "FlashCookiesDeleteOnStartExit": False,
        "FlashCookieAutoRefresh": False,
        "FlashCookieNotify": False,
        "FlashCookiesWhitelist": [],
        "FlashCookiesBlacklist": [],
        "FlashCookiesDataPath": flashDataPathForOS(),
    }
    
    @classmethod
    def initWebSettingsDefaults(cls):
        """
        Class method to initialize the web settings related defaults.
        """
        websettings = QWebSettings.globalSettings()
        fontFamily = websettings.fontFamily(QWebSettings.StandardFont)
        fontSize = websettings.fontSize(QWebSettings.DefaultFontSize)
        cls.helpDefaults["StandardFont"] = \
            QFont(fontFamily, fontSize).toString()
        fontFamily = websettings.fontFamily(QWebSettings.FixedFont)
        fontSize = websettings.fontSize(QWebSettings.DefaultFixedFontSize)
        cls.helpDefaults["FixedFont"] = QFont(fontFamily, fontSize).toString()
        cls.helpDefaults.update({
            "AutoLoadImages":
            websettings.testAttribute(QWebSettings.AutoLoadImages),
            "UserStyleSheet": "",
            "SaveUrlColor": QColor(248, 248, 210),
            "JavaEnabled":
            websettings.testAttribute(QWebSettings.JavaEnabled),
            "JavaScriptEnabled":
            websettings.testAttribute(QWebSettings.JavascriptEnabled),
            "JavaScriptCanOpenWindows":
            websettings.testAttribute(
                QWebSettings.JavascriptCanOpenWindows),
            "JavaScriptCanCloseWindows":
            websettings.testAttribute(
                QWebSettings.JavascriptCanCloseWindows),
            "JavaScriptCanAccessClipboard":
            websettings.testAttribute(
                QWebSettings.JavascriptCanAccessClipboard),
            "PluginsEnabled":
            websettings.testAttribute(QWebSettings.PluginsEnabled),
            "OfflineStorageDatabaseEnabled":
            websettings.testAttribute(
                QWebSettings.OfflineStorageDatabaseEnabled),
        })
        if hasattr(QWebSettings, "OfflineWebApplicationCacheEnabled"):
            cls.helpDefaults.update({
                "OfflineWebApplicationCacheEnabled":
                websettings.testAttribute(
                    QWebSettings.OfflineWebApplicationCacheEnabled),
                "OfflineWebApplicationCacheQuota": 50,     # 50 MB
            })
        if hasattr(QWebSettings, "LocalStorageEnabled"):
            cls.helpDefaults["LocalStorageEnabled"] = \
                websettings.testAttribute(QWebSettings.LocalStorageEnabled)
        if hasattr(QWebSettings, "DnsPrefetchEnabled"):
            cls.helpDefaults["DnsPrefetchEnabled"] = \
                websettings.testAttribute(QWebSettings.DnsPrefetchEnabled)
        if hasattr(QWebSettings, "defaultTextEncoding"):
            cls.helpDefaults["DefaultTextEncoding"] = \
                websettings.defaultTextEncoding()
        if hasattr(QWebSettings, "SpatialNavigationEnabled"):
            cls.helpDefaults["SpatialNavigationEnabled"] = \
                websettings.testAttribute(
                    QWebSettings.SpatialNavigationEnabled)
        if hasattr(QWebSettings, "LinksIncludedInFocusChain"):
            cls.helpDefaults["LinksIncludedInFocusChain"] = \
                websettings.testAttribute(
                    QWebSettings.LinksIncludedInFocusChain)
        if hasattr(QWebSettings, "LocalContentCanAccessRemoteUrls"):
            cls.helpDefaults["LocalContentCanAccessRemoteUrls"] = \
                websettings.testAttribute(
                    QWebSettings.LocalContentCanAccessRemoteUrls)
        if hasattr(QWebSettings, "LocalContentCanAccessFileUrls"):
            cls.helpDefaults["LocalContentCanAccessFileUrls"] = \
                websettings.testAttribute(
                    QWebSettings.LocalContentCanAccessFileUrls)
        if hasattr(QWebSettings, "XSSAuditingEnabled"):
            cls.helpDefaults["XSSAuditingEnabled"] = \
                websettings.testAttribute(QWebSettings.XSSAuditingEnabled)
        if hasattr(QWebSettings, "SiteSpecificQuirksEnabled"):
            cls.helpDefaults["SiteSpecificQuirksEnabled"] = \
                websettings.testAttribute(
                    QWebSettings.SiteSpecificQuirksEnabled)
        
        cls.webSettingsIntitialized = True
    
    webSettingsIntitialized = False

    # defaults for system settings
    sysDefaults = {
        "StringEncoding": "utf-8",
        "IOEncoding": "utf-8",
    }
    
    # defaults for the shell settings
    shellDefaults = {
        "LinenoMargin": True,
        "AutoCompletionEnabled": True,
        "CallTipsEnabled": True,
        "WrapEnabled": True,
        "MaxHistoryEntries": 100,
        "SyntaxHighlightingEnabled": True,
        "ShowStdOutErr": True,
        "UseMonospacedFont": False,
        "MonospacedFont": "Courier,10,-1,5,50,0,0,0,0,0",
        "MarginsFont": "Sans Serif,10,-1,5,50,0,0,0,0,0",
    }

    # defaults for Qt related stuff
    qtDefaults = {
        "Qt4TranslationsDir": "",
        "QtToolsPrefix4": "",
        "QtToolsPostfix4": "",
        "PyuicIndent": 4,
        "PyuicFromImports": False,
    }
    
    # defaults for corba related stuff
    corbaDefaults = {
        "omniidl": "omniidl"
    }
    
    # defaults for user related stuff
    userDefaults = {
        "Email": "",
        "MailServer": "",
        "Signature": "",
        "MailServerAuthentication": False,
        "MailServerUser": "",
        "MailServerPassword": "",
        "MailServerUseTLS": False,
        "MailServerPort": 25,
        "UseSystemEmailClient": False,
        "MasterPassword": "",           # stores the password hash
        "UseMasterPassword": False,
        "SavePasswords": False,
    }
    
    # defaults for vcs related stuff
    vcsDefaults = {
        "AutoClose": False,
        "AutoSaveFiles": True,
        "AutoSaveProject": True,
        "AutoUpdate": False,
        "StatusMonitorInterval": 30,
        "MonitorLocalStatus": False,
    }
    
    # defaults for tasks related stuff
    tasksDefaults = {
        "TasksFixmeMarkers": "FIX" + "ME:",
        "TasksWarningMarkers": "WARN" + "ING:",
        "TasksTodoMarkers": "TO" + "DO:",
        "TasksNoteMarkers": "NO" + "TE:",
        # needed to keep it from being recognized as a task
        "TasksFixmeColor": QColor("#FFA0A0"),
        "TasksWarningColor": QColor("#FFFFA0"),
        "TasksTodoColor": QColor("#A0FFA0"),
        "TasksNoteColor": QColor("#A0A0FF"),
        "ClearOnFileClose": True,
        "TasksProjectAutoSave": True,
    }
    
    # defaults for templates related stuff
    templatesDefaults = {
        "AutoOpenGroups": True,
        "SingleDialog": False,
        "ShowTooltip": False,
        "SeparatorChar": "$",
        "EditorFont": "Monospace,9,-1,5,50,0,0,0,0,0",
    }
    
    # defaults for plugin manager related stuff
    pluginManagerDefaults = {
        "ActivateExternal": True,
        "DownloadPath": "",
        "UpdatesCheckInterval": 3,
        # 0 = off
        # 1 = daily
        # 2 = weekly
        # 3 = monthly
        "CheckInstalledOnly": True,
        # list of plug-ins not to shown in the repo dialog
        "HiddenPlugins": [],
        # parameters for housekeeping
        "KeepGenerations": 2,
        "KeepHidden": False,
    }
    
    # defaults for the printer settings
    graphicsDefaults = {
        "Font": "SansSerif,10,-1,5,50,0,0,0,0,0"
    }
    
    # defaults for the icon editor
    iconEditorDefaults = {
        "IconEditorState": QByteArray(),
    }
    
    # defaults for pyflakes
    pyflakesDefaults = {
        "IncludeInSyntaxCheck": True,
        "IgnoreStarImportWarnings": True,
    }
    
    # defaults for tray starter
    trayStarterDefaults = {
        "TrayStarterIcon": "erict.png",
        # valid values are: erict.png, erict-hc.png,
        #                   erict-bw.png, erict-bwi.png
    }
    
    # defaults for geometry
    geometryDefaults = {
        "HelpViewerGeometry": QByteArray(),
        "HelpInspectorGeometry": QByteArray(),
        "IconEditorGeometry": QByteArray(),
        "MainGeometry": QByteArray(),
        "MainMaximized": False,
    }

    # if true, revert layouts to factory defaults
    resetLayout = False
    
    # defaults for IRC
    ircDefaults = {
        "ShowTimestamps": True,
        "TimestampIncludeDate": False,
        "TimeFormat": "hh:mm",
        "DateFormat": "yyyy-MM-dd",
        
        "NetworkMessageColour": "#000055",
        "ServerMessageColour": "#91640A",
        "ErrorMessageColour": "#FF0000",
        "TimestampColour": "#709070",
        "HyperlinkColour": "#0000FF",
        "ChannelMessageColour": "#000000",
        "OwnNickColour": "#000000",
        "NickColour": "#18B33C",
        "JoinChannelColour": "#72D672",
        "LeaveChannelColour": "#B00000",
        "ChannelInfoColour": "#9E54B3",
        
        "EnableIrcColours": True,
        "IrcColor0": "#FFFF00",
        "IrcColor1": "#000000",
        "IrcColor2": "#000080",
        "IrcColor3": "#008000",
        "IrcColor4": "#FF0000",
        "IrcColor5": "#A52A2A",
        "IrcColor6": "#800080",
        "IrcColor7": "#FF8000",
        "IrcColor8": "#808000",
        "IrcColor9": "#00FF00",
        "IrcColor10": "#008080",
        "IrcColor11": "#00FFFF",
        "IrcColor12": "#0000FF",
        "IrcColor13": "#FFC0CB",
        "IrcColor14": "#A0A0A0",
        "IrcColor15": "#C0C0C0",
        
        "ShowNotifications": True,
        "NotifyJoinPart": True,
        "NotifyMessage": False,
        "NotifyNick": False,
        
        "AutoUserInfoLookup": True,
        "AutoUserInfoMax": 200,
        "AutoUserInfoInterval": 90,
        
        "MarkPositionWhenHidden": True,
        "MarkerLineForegroundColour": "#000000",    # Black on
        "MarkerLineBackgroundColour": "#ffff00",    # Yellow
        
        "AskOnShutdown": True,
    }


def readToolGroups(prefClass=Prefs):
    """
    Module function to read the tool groups configuration.
    
    @param prefClass preferences class used as the storage area
    @return list of tuples defing the tool groups
    """
    toolGroups = []
    groups = int(prefClass.settings.value("Toolgroups/Groups", 0))
    for groupIndex in range(groups):
        groupName = prefClass.settings.value(
            "Toolgroups/{0:02d}/Name".format(groupIndex))
        group = [groupName, []]
        items = int(prefClass.settings.value(
            "Toolgroups/{0:02d}/Items".format(groupIndex), 0))
        for ind in range(items):
            menutext = prefClass.settings.value(
                "Toolgroups/{0:02d}/{1:02d}/Menutext".format(groupIndex, ind))
            icon = prefClass.settings.value(
                "Toolgroups/{0:02d}/{1:02d}/Icon".format(groupIndex, ind))
            executable = prefClass.settings.value(
                "Toolgroups/{0:02d}/{1:02d}/Executable".format(
                    groupIndex, ind))
            arguments = prefClass.settings.value(
                "Toolgroups/{0:02d}/{1:02d}/Arguments".format(groupIndex, ind))
            redirect = prefClass.settings.value(
                "Toolgroups/{0:02d}/{1:02d}/Redirect".format(groupIndex, ind))
            
            if menutext:
                if menutext == '--':
                    tool = {
                        'menutext': '--',
                        'icon': '',
                        'executable': '',
                        'arguments': '',
                        'redirect': 'no',
                    }
                    group[1].append(tool)
                elif executable:
                    tool = {
                        'menutext': menutext,
                        'icon': icon,
                        'executable': executable,
                        'arguments': arguments,
                        'redirect': redirect,
                    }
                    group[1].append(tool)
        toolGroups.append(group)
    currentGroup = int(
        prefClass.settings.value("Toolgroups/Current Group", -1))
    return toolGroups, currentGroup
    

def saveToolGroups(toolGroups, currentGroup, prefClass=Prefs):
    """
    Module function to write the tool groups configuration.
    
    @param toolGroups reference to the list of tool groups
    @param currentGroup index of the currently selected tool group (integer)
    @param prefClass preferences class used as the storage area
    """
    # first step, remove all tool group entries
    prefClass.settings.remove("Toolgroups")
    
    # second step, write the tool group entries
    prefClass.settings.setValue("Toolgroups/Groups", len(toolGroups))
    groupIndex = 0
    for group in toolGroups:
        prefClass.settings.setValue(
            "Toolgroups/{0:02d}/Name".format(groupIndex), group[0])
        prefClass.settings.setValue(
            "Toolgroups/{0:02d}/Items".format(groupIndex), len(group[1]))
        ind = 0
        for tool in group[1]:
            prefClass.settings.setValue(
                "Toolgroups/{0:02d}/{1:02d}/Menutext".format(groupIndex, ind),
                tool['menutext'])
            prefClass.settings.setValue(
                "Toolgroups/{0:02d}/{1:02d}/Icon".format(groupIndex, ind),
                tool['icon'])
            prefClass.settings.setValue(
                "Toolgroups/{0:02d}/{1:02d}/Executable".format(
                    groupIndex, ind),
                tool['executable'])
            prefClass.settings.setValue(
                "Toolgroups/{0:02d}/{1:02d}/Arguments".format(groupIndex, ind),
                tool['arguments'])
            prefClass.settings.setValue(
                "Toolgroups/{0:02d}/{1:02d}/Redirect".format(groupIndex, ind),
                tool['redirect'])
            ind += 1
        groupIndex += 1
    prefClass.settings.setValue("Toolgroups/Current Group", currentGroup)
    

def initPreferences():
    """
    Module function to initialize the central configuration store.
    """
    Prefs.settings = QSettings(
        QSettings.IniFormat, QSettings.UserScope,
        settingsNameOrganization, settingsNameGlobal)
    if not isWindowsPlatform():
        hp = QDir.homePath()
        dn = QDir(hp)
        dn.mkdir(".eric6")
    QCoreApplication.setOrganizationName(settingsNameOrganization)
    QCoreApplication.setApplicationName(settingsNameGlobal)
    
    # Avoid nasty behavior of QSettings in combination with Py2
    Prefs.settings.value("UI/SingleApplicationMode")
    

def syncPreferences(prefClass=Prefs):
    """
    Module function to sync the preferences to disk.
    
    In addition to syncing, the central configuration store is reinitialized
    as well.
    
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("General/Configured", True)
    prefClass.settings.sync()
    

def exportPreferences(prefClass=Prefs):
    """
    Module function to export the current preferences.
    
    @param prefClass preferences class used as the storage area
    """
    filename, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
        None,
        QCoreApplication.translate("Preferences", "Export Preferences"),
        "",
        QCoreApplication.translate(
            "Preferences",
            "Properties File (*.ini);;All Files (*)"),
        None,
        E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
    if filename:
        ext = QFileInfo(filename).suffix()
        if not ext:
            ex = selectedFilter.split("(*")[1].split(")")[0]
            if ex:
                filename += ex
        settingsFile = prefClass.settings.fileName()
        prefClass.settings = None
        shutil.copy(settingsFile, filename)
        initPreferences()


def importPreferences(prefClass=Prefs):
    """
    Module function to import preferences from a file previously saved by
    the export function.
    
    @param prefClass preferences class used as the storage area
    """
    filename = E5FileDialog.getOpenFileName(
        None,
        QCoreApplication.translate("Preferences", "Import Preferences"),
        "",
        QCoreApplication.translate(
            "Preferences",
            "Properties File (*.ini);;All Files (*)"))
    if filename:
        settingsFile = prefClass.settings.fileName()
        shutil.copy(filename, settingsFile)
        initPreferences()


def isConfigured(prefClass=Prefs):
    """
    Module function to check, if the the application has been configured.
    
    @param prefClass preferences class used as the storage area
    @return flag indicating the configured status (boolean)
    """
    return toBool(prefClass.settings.value("General/Configured", False))
    

def initRecentSettings():
    """
    Module function to initialize the central configuration store for recently
    opened files and projects.
    
    This function is called once upon import of the module.
    """
    Prefs.rsettings = QSettings(
        QSettings.IniFormat, QSettings.UserScope,
        settingsNameOrganization, settingsNameRecent)
    

def getVarFilters(prefClass=Prefs):
    """
    Module function to retrieve the variables filter settings.
    
    @param prefClass preferences class used as the storage area
    @return a tuple defining the variables filter
    """
    localsFilter = eval(prefClass.settings.value(
        "Variables/LocalsFilter", prefClass.varDefaults["LocalsFilter"]))
    globalsFilter = eval(prefClass.settings.value(
        "Variables/GlobalsFilter", prefClass.varDefaults["GlobalsFilter"]))
    return (localsFilter, globalsFilter)
    

def setVarFilters(filters, prefClass=Prefs):
    """
    Module function to store the variables filter settings.
    
    @param filters variable filters to set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Variables/LocalsFilter", str(filters[0]))
    prefClass.settings.setValue("Variables/GlobalsFilter", str(filters[1]))
    

def getDebugger(key, prefClass=Prefs):
    """
    Module function to retrieve the debugger settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested debugger setting
    """
    if key in ["RemoteDbgEnabled", "PassiveDbgEnabled",
               "AutomaticReset", "DebugEnvironmentReplace",
               "PythonRedirect", "PythonNoEncoding",
               "Python3Redirect", "Python3NoEncoding",
               "RubyRedirect",
               "ConsoleDbgEnabled", "PathTranslation",
               "Autosave", "ThreeStateBreakPoints",
               "SuppressClientExit", "BreakAlways",
               "AutoViewSourceCode", "ShowExceptionInShell",
               ]:
        return toBool(prefClass.settings.value(
            "Debugger/" + key, prefClass.debuggerDefaults[key]))
    elif key in ["PassiveDbgPort"]:
        return int(
            prefClass.settings.value(
                "Debugger/" + key, prefClass.debuggerDefaults[key]))
    elif key in ["AllowedHosts"]:
        return toList(
            prefClass.settings.value(
                "Debugger/" + key, prefClass.debuggerDefaults[key]))
    elif key in ["PythonInterpreter", "Python3Interpreter"]:
        interpreter = \
            prefClass.settings.value(
                "Debugger/" + key, prefClass.debuggerDefaults[key])
        if not interpreter:
            pyVersion = 2 if key == "PythonInterpreter" else 3
            if sys.version_info[0] == pyVersion:
                return sys.executable

            interpreters = findPythonInterpreters(pyVersion)
            if interpreters:
                if len(interpreters) == 1:
                    interpreter = interpreters[0]
                else:
                    selection, ok = QInputDialog.getItem(
                        None,
                        QCoreApplication.translate(
                            "Preferences",
                            "Select Python{0} Interpreter").format(pyVersion),
                        QCoreApplication.translate(
                            "Preferences",
                            "Select the Python{0} interpreter to be used:")
                        .format(pyVersion),
                        interpreters,
                        0, False)
                    if ok and selection != "":
                        interpreter = selection
                if interpreter:
                    setDebugger(key, interpreter)
        return interpreter
    else:
        return prefClass.settings.value(
            "Debugger/" + key, prefClass.debuggerDefaults[key])
    

def setDebugger(key, value, prefClass=Prefs):
    """
    Module function to store the debugger settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Debugger/" + key, value)


def getPython(key, prefClass=Prefs):
    """
    Module function to retrieve the Python settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested debugger setting
    """
    if key in ["PythonExtensions", "Python3Extensions"]:
        exts = []
        for ext in getDebugger(key, prefClass).split():
            if ext.startswith("."):
                exts.append(ext)
            else:
                exts.append(".{0}".format(ext))
        return exts


def setPython(key, value, prefClass=Prefs):
    """
    Module function to store the Python settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["PythonExtensions", "Python3Extensions"]:
        setDebugger(key, value, prefClass)


def getUILanguage(prefClass=Prefs):
    """
    Module function to retrieve the language for the user interface.
    
    @param prefClass preferences class used as the storage area
    @return the language for the UI
    """
    lang = prefClass.settings.value("UI/Language",
                                    prefClass.uiDefaults["Language"])
    if lang == "None" or lang == "" or lang is None:
        return None
    else:
        return lang
    

def setUILanguage(lang, prefClass=Prefs):
    """
    Module function to store the language for the user interface.
    
    @param lang the language
    @param prefClass preferences class used as the storage area
    """
    if lang is None:
        prefClass.settings.setValue("UI/Language", "None")
    else:
        prefClass.settings.setValue("UI/Language", lang)


def getUILayout(prefClass=Prefs):
    """
    Module function to retrieve the layout for the user interface.
    
    @param prefClass preferences class used as the storage area
    @return the UI layout as a tuple of main layout, flag for
        an embedded shell and a value for an embedded file browser
    """
    layoutType = prefClass.settings.value(
        "UI/LayoutType", prefClass.uiDefaults["LayoutType"])
    if layoutType in ["DockWindows", "FloatingWindows"]:
        # change old fashioned layouts to the modern default
        layoutType = prefClass.uiDefaults["LayoutType"]
    layout = (layoutType,
              int(prefClass.settings.value("UI/LayoutShellEmbedded",
                  prefClass.uiDefaults["LayoutShellEmbedded"])),
              int(prefClass.settings.value("UI/LayoutFileBrowserEmbedded",
                  prefClass.uiDefaults["LayoutFileBrowserEmbedded"])),
              )
    return layout
    

def setUILayout(layout, prefClass=Prefs):
    """
    Module function to store the layout for the user interface.
    
    @param layout the layout type
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("UI/LayoutType", layout[0])
    prefClass.settings.setValue("UI/LayoutShellEmbedded", layout[1])
    prefClass.settings.setValue("UI/LayoutFileBrowserEmbedded", layout[2])


def getViewManager(prefClass=Prefs):
    """
    Module function to retrieve the selected viewmanager type.
    
    @param prefClass preferences class used as the storage area
    @return the viewmanager type
    """
    return prefClass.settings.value(
        "UI/ViewManager", prefClass.uiDefaults["ViewManager"])
    

def setViewManager(vm, prefClass=Prefs):
    """
    Module function to store the selected viewmanager type.
    
    @param vm the viewmanager type
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("UI/ViewManager", vm)


def getUI(key, prefClass=Prefs):
    """
    Module function to retrieve the various UI settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested UI setting
    """
    if key in ["BrowsersListFoldersFirst", "BrowsersHideNonPublic",
               "BrowsersListContentsByOccurrence", "BrowsersListHiddenFiles",
               "LogViewerAutoRaise",
               "SingleApplicationMode", "TabViewManagerFilenameOnly",
               "ShowFilePreview", "ShowFilePreviewJS", "ShowFilePreviewSSI",
               "CaptionShowsFilename", "ShowSplash",
               "SingleCloseButton", "SplitOrientationVertical",
               "UseProxy", "UseSystemProxy", "UseHttpProxyForAll",
               "TopLeftByLeft", "BottomLeftByLeft",
               "TopRightByRight", "BottomRightByRight",
               "RequestDownloadFilename",
               "LayoutShellEmbedded", "LayoutFileBrowserEmbedded",
               "CheckErrorLog", "NotificationsEnabled"]:
        return toBool(prefClass.settings.value(
            "UI/" + key, prefClass.uiDefaults[key]))
    elif key in ["TabViewManagerFilenameLength", "CaptionFilenameLength",
                 "ProxyPort/Http", "ProxyPort/Https", "ProxyPort/Ftp",
                 "ProxyType/Ftp", "OpenOnStartup",
                 "PerformVersionCheck", "RecentNumber", "NotificationTimeout",
                 "SidebarDelay"]:
        return int(prefClass.settings.value(
            "UI/" + key, prefClass.uiDefaults[key]))
    elif key in ["ProxyPassword/Http", "ProxyPassword/Https",
                 "ProxyPassword/Ftp", ]:
        from Utilities.crypto import pwConvert
        return pwConvert(
            prefClass.settings.value("UI/" + key, prefClass.uiDefaults[key]),
            encode=False)
    elif key in ["LogStdErrColour"]:
        col = prefClass.settings.value("UI/" + key)
        if col is not None:
            return QColor(col)
        else:
            return prefClass.uiDefaults[key]
    elif key in "ViewProfiles2":
        profiles = prefClass.settings.value("UI/ViewProfiles2")
        if profiles is not None:
            viewProfiles = {}
            profiles = json.loads(profiles)
            for name in ["edit", "debug"]:
                viewProfiles[name] = [
                    QByteArray.fromBase64(profiles[name][0].encode("utf-8")),
                    profiles[name][1][:],
                    []
                ]
                for bs in profiles[name][2]:
                    viewProfiles[name][2].append(
                        QByteArray.fromBase64(bs.encode("utf-8")))
        else:
            # migrate from the old ViewProfiles settings
            try:
                profiles = prefClass.settings.value("UI/ViewProfiles")
            except TypeError:
                profiles = None
            if profiles is not None:
                if isinstance(profiles, basestring):
                    profiles = eval(profiles)
                viewProfiles = {}
                for name in ["edit", "debug"]:
                    viewProfiles[name] = [
                        QByteArray(profiles[name][4]),
                        profiles[name][5][:],
                        []
                    ]
                    for b in profiles[name][6]:
                        viewProfiles[name][2].append(QByteArray(b))
                    # correct some entries
                    while (len(viewProfiles[name][1]) < len(
                            prefClass.uiDefaults["ViewProfiles2"][name][1])):
                        viewProfiles[name][1].append(True)
                    while len(viewProfiles[name][2]) < len(
                            prefClass.uiDefaults["ViewProfiles2"][name][2]):
                        viewProfiles[name][2].append(QByteArray())
            else:
                # use the defaults
                viewProfiles = prefClass.uiDefaults["ViewProfiles2"]
        # Remove unused setting
        prefClass.settings.remove("UI/ViewProfiles")
        return viewProfiles
    elif key in ["ToolbarManagerState", "PreviewSplitterState"]:
        state = prefClass.settings.value("UI/" + key)
        if state is not None:
            return state
        else:
            return prefClass.uiDefaults[key]
    elif key in ["VersionsUrls6"]:
        urls = toList(
            prefClass.settings.value("UI/" + key, prefClass.uiDefaults[key]))
        if len(urls) == 0:
            return prefClass.uiDefaults[key]
        else:
            return urls
    elif key in ["LogViewerStdoutFilter", "LogViewerStderrFilter",
                 "LogViewerStdxxxFilter", "TextMimeTypes"]:
        return toList(
            prefClass.settings.value("UI/" + key, prefClass.uiDefaults[key]))
    else:
        return prefClass.settings.value("UI/" + key, prefClass.uiDefaults[key])
    

def setUI(key, value, prefClass=Prefs):
    """
    Module function to store the various UI settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key == "ViewProfiles2":
        profiles = {}
        for name in ["edit", "debug"]:
            profiles[name] = [
                bytes(value[name][0].toBase64()).decode(),
                value[name][1][:],
                []
            ]
            for ba in value[name][2]:
                profiles[name][2].append(bytes(ba.toBase64()).decode())
        prefClass.settings.setValue("UI/" + key, json.dumps(profiles))
    elif key == "LogStdErrColour":
        prefClass.settings.setValue("UI/" + key, value.name())
    elif key in ["ProxyPassword/Http", "ProxyPassword/Https",
                 "ProxyPassword/Ftp", ]:
        from Utilities.crypto import pwConvert
        prefClass.settings.setValue("UI/" + key, pwConvert(value, encode=True))
    else:
        prefClass.settings.setValue("UI/" + key, value)
    

def getIcons(key, prefClass=Prefs):
    """
    Module function to retrieve the various Icons settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested Icons setting
    """
    dirlist = prefClass.settings.value("UI/Icons/" + key)
    if dirlist is not None:
        return dirlist
    else:
        return prefClass.iconsDefaults[key]
    

def setIcons(key, value, prefClass=Prefs):
    """
    Module function to store the various Icons settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("UI/Icons/" + key, value)
    

def getCooperation(key, prefClass=Prefs):
    """
    Module function to retrieve the various Cooperation settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested UI setting
    """
    if key in ["AutoStartServer", "TryOtherPorts", "AutoAcceptConnections"]:
        return toBool(prefClass.settings.value(
            "Cooperation/" + key, prefClass.cooperationDefaults[key]))
    elif key in ["ServerPort", "MaxPortsToTry"]:
        return int(prefClass.settings.value(
            "Cooperation/" + key, prefClass.cooperationDefaults[key]))
    elif key in ["BannedUsers"]:
        return toList(prefClass.settings.value(
            "Cooperation/" + key, prefClass.cooperationDefaults[key]))
    else:
        return prefClass.settings.value(
            "Cooperation/" + key, prefClass.cooperationDefaults[key])
    

def setCooperation(key, value, prefClass=Prefs):
    """
    Module function to store the various Cooperation settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Cooperation/" + key, value)


def getEditor(key, prefClass=Prefs):
    """
    Module function to retrieve the various editor settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested editor setting
    """
    if key in ["DefaultEncoding", "DefaultOpenFilter", "DefaultSaveFilter",
               "SpellCheckingDefaultLanguage", "SpellCheckingPersonalWordList",
               "SpellCheckingPersonalExcludeList"]:
        return prefClass.settings.value(
            "Editor/" + key, prefClass.editorDefaults[key])
    elif key in ["AutosaveInterval", "TabWidth", "IndentWidth",
                 "FoldingStyle", "WarnFilesize", "EdgeMode", "EdgeColumn",
                 "CaretWidth", "AutoCompletionSource",
                 "AutoCompletionThreshold", "CallTipsVisible",
                 "CallTipsStyle", "MarkOccurrencesTimeout",
                 "AutoSpellCheckChunkSize", "SpellCheckingMinWordSize",
                 "PostScriptLevel", "EOLMode", "ZoomFactor", "WhitespaceSize",
                 "OnlineSyntaxCheckInterval", "OnlineChangeTraceInterval",
                 "WrapLongLinesMode", "WrapVisualFlag", "CallTipsPosition",
                 "VirtualSpaceOptions"]:
        return int(prefClass.settings.value(
            "Editor/" + key, prefClass.editorDefaults[key]))
    elif key in ["AdditionalOpenFilters", "AdditionalSaveFilters",
                 "PreviewMarkdownFileNameExtensions",
                 "PreviewRestFileNameExtensions",
                 "PreviewHtmlFileNameExtensions",
                 "PreviewQssFileNameExtensions"]:
        return toList(prefClass.settings.value(
            "Editor/" + key, prefClass.editorDefaults[key]))
    elif key in ["PythonBadIndentation"]:
        value = prefClass.settings.value(
            "Editor/" + key, prefClass.editorDefaults[key])
        if value in ["true", "True"]:
            value = 1
        elif value in ["false", "False"]:
            value = 0
        return QsciLexerPython.IndentationWarning(int(value))
    else:
        return toBool(prefClass.settings.value(
            "Editor/" + key, prefClass.editorDefaults[key]))
    

def setEditor(key, value, prefClass=Prefs):
    """
    Module function to store the various editor settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Editor/" + key, value)
    

def getEditorColour(key, prefClass=Prefs):
    """
    Module function to retrieve the various editor marker colours.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested editor colour
    """
    col = prefClass.settings.value("Editor/Colour/" + key)
    if col is not None:
        if len(col) == 9:
            # color string with alpha
            return QColor.fromRgba(int(col[1:], 16))
        else:
            return QColor(col)
    else:
        # palette based defaults here because of Qt5
        if key == "EditAreaForeground":
            return QApplication.palette().color(QPalette.Active, QPalette.Base)
        elif key == "EditAreaBackground":
            return QApplication.palette().color(QPalette.Active, QPalette.Text)
        else:
            return prefClass.editorColourDefaults[key]
    

def setEditorColour(key, value, prefClass=Prefs):
    """
    Module function to store the various editor marker colours.
    
    @param key the key of the colour to be set
    @param value the colour to be set
    @param prefClass preferences class used as the storage area
    """
    if value.alpha() < 255:
        val = "#{0:8x}".format(value.rgba())
    else:
        val = value.name()
    prefClass.settings.setValue("Editor/Colour/" + key, val)
    

def getEditorOtherFonts(key, prefClass=Prefs):
    """
    Module function to retrieve the various editor fonts except the lexer
    fonts.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested editor font (QFont)
    """
    f = QFont()
    f.fromString(prefClass.settings.value(
        "Editor/Other Fonts/" + key, prefClass.editorOtherFontsDefaults[key]))
    return f
    

def setEditorOtherFonts(key, font, prefClass=Prefs):
    """
    Module function to store the various editor fonts except the lexer fonts.
    
    @param key the key of the font to be set
    @param font the font to be set (QFont)
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Editor/Other Fonts/" + key, font.toString())
    

def getEditorAPI(key, prefClass=Prefs):
    """
    Module function to retrieve the various lists of api files.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested list of api files (list of strings)
    """
    apis = prefClass.settings.value("Editor/APIs/" + key)
    if apis is not None:
        if len(apis) and apis[0] == "":
            return []
        else:
            return apis
    else:
        return []
    

def setEditorAPI(key, apilist, prefClass=Prefs):
    """
    Module function to store the various lists of api files.
    
    @param key the key of the api to be set
    @param apilist the list of api files (list of strings)
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Editor/APIs/" + key, apilist)
    

def getEditorKeywords(key, prefClass=Prefs):
    """
    Module function to retrieve the various lists of language keywords.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested list of language keywords (list of strings)
    """
    keywords = prefClass.settings.value("Editor/Keywords/" + key)
    if keywords is not None:
        return keywords
    else:
        return []
    

def setEditorKeywords(key, keywordsLists, prefClass=Prefs):
    """
    Module function to store the various lists of language keywords.
    
    @param key the key of the api to be set
    @param keywordsLists the list of language keywords (list of strings)
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Editor/Keywords/" + key, keywordsLists)
    

def getEditorLexerAssocs(prefClass=Prefs):
    """
    Module function to retrieve all lexer associations.
    
    @param prefClass preferences class used as the storage area
    @return a reference to the list of lexer associations
        (dictionary of strings)
    """
    editorLexerAssoc = {}
    prefClass.settings.beginGroup("Editor/LexerAssociations")
    keyList = prefClass.settings.childKeys()
    prefClass.settings.endGroup()
    
    import QScintilla.Lexers
    editorLexerAssocDefaults = QScintilla.Lexers.getDefaultLexerAssociations()
    
    if len(keyList) == 0:
        # build from scratch
        for key in list(editorLexerAssocDefaults.keys()):
            editorLexerAssoc[key] = editorLexerAssocDefaults[key]
    else:
        for key in keyList:
            if key in editorLexerAssocDefaults:
                defaultValue = editorLexerAssocDefaults[key]
            else:
                defaultValue = ""
            editorLexerAssoc[key] = prefClass.settings.value(
                "Editor/LexerAssociations/" + key, defaultValue)
        
        # check for new default lexer associations
        for key in list(editorLexerAssocDefaults.keys()):
            if key not in editorLexerAssoc:
                editorLexerAssoc[key] = editorLexerAssocDefaults[key]
    return editorLexerAssoc
    

def setEditorLexerAssocs(assocs, prefClass=Prefs):
    """
    Module function to retrieve all lexer associations.
    
    @param assocs dictionary of lexer associations to be set
    @param prefClass preferences class used as the storage area
    """
    # first remove lexer associations that no longer exist, than save the rest
    prefClass.settings.beginGroup("Editor/LexerAssociations")
    keyList = prefClass.settings.childKeys()
    prefClass.settings.endGroup()
    for key in keyList:
        if key not in assocs:
            prefClass.settings.remove("Editor/LexerAssociations/" + key)
    for key in assocs:
        prefClass.settings.setValue(
            "Editor/LexerAssociations/" + key, assocs[key])
    

def getEditorLexerAssoc(filename, prefClass=Prefs):
    """
    Module function to retrieve a lexer association.
    
    @param filename filename used to determine the associated lexer language
        (string)
    @param prefClass preferences class used as the storage area
    @return the requested lexer language (string)
    """
    for pattern, language in list(getEditorLexerAssocs().items()):
        if fnmatch.fnmatch(filename, pattern):
            return language
    
    return ""
    

def getEditorTyping(key, prefClass=Prefs):
    """
    Module function to retrieve the various editor typing settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested editor setting
    """
    return toBool(prefClass.settings.value(
        "Editor/Typing/" + key, prefClass.editorTypingDefaults[key]))
    

def setEditorTyping(key, value, prefClass=Prefs):
    """
    Module function to store the various editor typing settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Editor/Typing/" + key, value)
    

def getEditorExporter(key, prefClass=Prefs):
    """
    Module function to retrieve the various editor exporters settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested editor setting
    """
    if key in ["RTF/Font"]:
        f = QFont()
        f.fromString(prefClass.settings.value(
            "Editor/Exporters/" + key, prefClass.editorExporterDefaults[key]))
        return f
    elif key in ["HTML/WYSIWYG", "HTML/Folding", "HTML/OnlyStylesUsed",
                 "HTML/FullPathAsTitle", "HTML/UseTabs", "RTF/WYSIWYG",
                 "RTF/UseTabs", "TeX/OnlyStylesUsed", "TeX/FullPathAsTitle",
                 "ODT/WYSIWYG", "ODT/OnlyStylesUsed", "ODT/UseTabs"]:
        return toBool(prefClass.settings.value(
            "Editor/Exporters/" + key, prefClass.editorExporterDefaults[key]))
    elif key in ["PDF/Magnification", "PDF/MarginLeft", "PDF/MarginRight",
                 "PDF/MarginTop", "PDF/MarginBottom"]:
        return int(prefClass.settings.value(
            "Editor/Exporters/" + key, prefClass.editorExporterDefaults[key]))
    else:
        return prefClass.settings.value(
            "Editor/Exporters/" + key, prefClass.editorExporterDefaults[key])


def setEditorExporter(key, value, prefClass=Prefs):
    """
    Module function to store the various editor exporters settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["RTF/Font"]:
        prefClass.settings.setValue(
            "Editor/Exporters/" + key, value.toString())
    else:
        prefClass.settings.setValue("Editor/Exporters/" + key, value)
    

def getPrinter(key, prefClass=Prefs):
    """
    Module function to retrieve the various printer settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested printer setting
    """
    if key in ["ColorMode", "FirstPageFirst"]:
        return toBool(prefClass.settings.value(
            "Printer/" + key, prefClass.printerDefaults[key]))
    elif key in ["Magnification", "Orientation", "PageSize"]:
        return int(prefClass.settings.value(
            "Printer/" + key, prefClass.printerDefaults[key]))
    elif key in ["LeftMargin", "RightMargin", "TopMargin", "BottomMargin"]:
        return float(prefClass.settings.value(
            "Printer/" + key, prefClass.printerDefaults[key]))
    elif key in ["HeaderFont"]:
        f = QFont()
        f.fromString(prefClass.settings.value(
            "Printer/" + key, prefClass.printerDefaults[key]))
        return f
    else:
        return prefClass.settings.value(
            "Printer/" + key, prefClass.printerDefaults[key])


def setPrinter(key, value, prefClass=Prefs):
    """
    Module function to store the various printer settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["HeaderFont"]:
        prefClass.settings.setValue("Printer/" + key, value.toString())
    else:
        prefClass.settings.setValue("Printer/" + key, value)


def getShell(key, prefClass=Prefs):
    """
    Module function to retrieve the various shell settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested shell setting
    """
    if key in ["MonospacedFont", "MarginsFont"]:
        f = QFont()
        f.fromString(prefClass.settings.value(
            "Shell/" + key, prefClass.shellDefaults[key]))
        return f
    elif key in ["MaxHistoryEntries"]:
        return int(prefClass.settings.value(
            "Shell/" + key, prefClass.shellDefaults[key]))
    else:
        return toBool(prefClass.settings.value(
            "Shell/" + key, prefClass.shellDefaults[key]))


def setShell(key, value, prefClass=Prefs):
    """
    Module function to store the various shell settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["MonospacedFont", "MarginsFont"]:
        prefClass.settings.setValue("Shell/" + key, value.toString())
    else:
        prefClass.settings.setValue("Shell/" + key, value)


def getProject(key, prefClass=Prefs):
    """
    Module function to retrieve the various project handling settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested project setting
    """
    if key in ["RecentNumber"]:
        return int(prefClass.settings.value(
            "Project/" + key, prefClass.projectDefaults[key]))
    else:
        return toBool(prefClass.settings.value(
            "Project/" + key, prefClass.projectDefaults[key]))
    

def setProject(key, value, prefClass=Prefs):
    """
    Module function to store the various project handling settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Project/" + key, value)
    

def getProjectBrowserFlags(key, prefClass=Prefs):
    """
    Module function to retrieve the various project browser flags settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested project setting
    """
    try:
        default = prefClass.projectBrowserFlagsDefaults[key]
    except KeyError:
        default = AllBrowsersFlag
    
    return int(prefClass.settings.value(
        "Project/BrowserFlags/" + key, default))
    

def setProjectBrowserFlags(key, value, prefClass=Prefs):
    """
    Module function to store the various project browser flags settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Project/BrowserFlags/" + key, value)
    

def setProjectBrowserFlagsDefault(key, value, prefClass=Prefs):
    """
    Module function to store the various project browser flags settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.projectBrowserFlagsDefaults[key] = value
    

def removeProjectBrowserFlags(key, prefClass=Prefs):
    """
    Module function to remove a project browser flags setting.
    
    @param key the key of the setting to be removed
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.remove("Project/BrowserFlags/" + key)
    

def getProjectBrowserColour(key, prefClass=Prefs):
    """
    Module function to retrieve the various project browser colours.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested project browser colour
    """
    col = prefClass.settings.value("Project/Colour/" + key)
    if col is not None:
        return QColor(col)
    else:
        return prefClass.projectBrowserColourDefaults[key]
    

def setProjectBrowserColour(key, value, prefClass=Prefs):
    """
    Module function to store the various project browser colours.
    
    @param key the key of the colour to be set
    @param value the colour to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Project/Colour/" + key, value.name())
    

def getMultiProject(key, prefClass=Prefs):
    """
    Module function to retrieve the various project handling settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested project setting
    """
    if key in ["RecentNumber"]:
        return int(prefClass.settings.value(
            "MultiProject/" + key, prefClass.multiProjectDefaults[key]))
    elif key in ["OpenMasterAutomatically", "XMLTimestamp"]:
        return toBool(prefClass.settings.value(
            "MultiProject/" + key, prefClass.multiProjectDefaults[key]))
    else:
        return prefClass.settings.value(
            "MultiProject/" + key, prefClass.multiProjectDefaults[key])
    

def setMultiProject(key, value, prefClass=Prefs):
    """
    Module function to store the various project handling settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("MultiProject/" + key, value)
    

def getQt4DocDir(prefClass=Prefs):
    """
    Module function to retrieve the Qt4DocDir setting.
    
    @param prefClass preferences class used as the storage area
    @return the requested Qt4DocDir setting (string)
    """
    s = prefClass.settings.value(
        "Help/Qt4DocDir", prefClass.helpDefaults["Qt4DocDir"])
    if s == "":
        s = os.getenv("QT4DOCDIR", "")
    if s == "":
        s = os.path.join(
            QLibraryInfo.location(QLibraryInfo.DocumentationPath), "html")
    return s
    

def getQt5DocDir(prefClass=Prefs):
    """
    Module function to retrieve the Qt5DocDir setting.
    
    @param prefClass preferences class used as the storage area
    @return the requested Qt4DocDir setting (string)
    """
    s = prefClass.settings.value(
        "Help/Qt5DocDir", prefClass.helpDefaults["Qt5DocDir"])
    if s == "":
        s = os.getenv("QT5DOCDIR", "")
    if s == "":
        s = os.path.join(
            QLibraryInfo.location(QLibraryInfo.DocumentationPath), "qtdoc")
    return s


def getHelp(key, prefClass=Prefs):
    """
    Module function to retrieve the various help settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested help setting
    """
    if not prefClass.webSettingsIntitialized:
        prefClass.initWebSettingsDefaults()
    
    if key in ["StandardFont", "FixedFont"]:
        f = QFont()
        f.fromString(prefClass.settings.value(
            "Help/" + key, prefClass.helpDefaults[key]))
        return f
    elif key in ["SaveUrlColor"]:
        col = prefClass.settings.value("Help/" + key)
        if col is not None:
            return QColor(col)
        else:
            return prefClass.helpDefaults[key]
    elif key in ["WebSearchKeywords"]:
        # return a list of tuples of (keyword, engine name)
        keywords = []
        size = prefClass.settings.beginReadArray("Help/" + key)
        for index in range(size):
            prefClass.settings.setArrayIndex(index)
            keyword = prefClass.settings.value("Keyword")
            engineName = prefClass.settings.value("Engine")
            keywords.append((keyword, engineName))
        prefClass.settings.endArray()
        return keywords
    elif key in ["DownloadManagerDownloads"]:
        # return a list of tuples of (URL, save location, done flag, page url)
        downloads = []
        length = prefClass.settings.beginReadArray("Help/" + key)
        for index in range(length):
            prefClass.settings.setArrayIndex(index)
            url = prefClass.settings.value("URL")
            location = prefClass.settings.value("Location")
            done = toBool(prefClass.settings.value("Done"))
            pageUrl = prefClass.settings.value("PageURL")
            if pageUrl is None:
                pageUrl = QUrl()
            downloads.append((url, location, done, pageUrl))
        prefClass.settings.endArray()
        return downloads
    elif key == "RssFeeds":
        # return a list of tuples of (URL, title, icon)
        feeds = []
        length = prefClass.settings.beginReadArray("Help/" + key)
        for index in range(length):
            prefClass.settings.setArrayIndex(index)
            url = prefClass.settings.value("URL")
            title = prefClass.settings.value("Title")
            icon = prefClass.settings.value("Icon")
            feeds.append((url, title, icon))
        prefClass.settings.endArray()
        return feeds
    elif key in ["SyncFtpPassword", "SyncEncryptionKey"]:
        from Utilities.crypto import pwConvert
        return pwConvert(prefClass.settings.value(
            "Help/" + key, prefClass.helpDefaults[key]), encode=False)
    elif key in ["HelpViewerType", "DiskCacheSize", "AcceptCookies",
                 "KeepCookiesUntil", "StartupBehavior", "HistoryLimit",
                 "OfflineStorageDatabaseQuota",
                 "OfflineWebApplicationCacheQuota", "CachePolicy",
                 "DownloadManagerRemovePolicy", "AdBlockUpdatePeriod",
                 "SearchLanguage", "SyncType", "SyncFtpPort",
                 "SyncFtpIdleTimeout", "SyncEncryptionKeyLength"]:
        return int(prefClass.settings.value(
            "Help/" + key, prefClass.helpDefaults[key]))
    elif key in ["SingleHelpWindow", "SaveGeometry", "WebSearchSuggestions",
                 "DiskCacheEnabled", "FilterTrackingCookies",
                 "PrintBackgrounds", "AdBlockEnabled", "AutoLoadImages",
                 "JavaEnabled", "JavaScriptEnabled",
                 "JavaScriptCanOpenWindows", "JavaScriptCanCloseWindows",
                 "JavaScriptCanAccessClipboard",
                 "PluginsEnabled", "DnsPrefetchEnabled",
                 "OfflineStorageDatabaseEnabled",
                 "OfflineWebApplicationCacheEnabled", "LocalStorageEnabled",
                 "ShowPreview", "AccessKeysEnabled", "VirusTotalEnabled",
                 "VirusTotalSecure", "DoNotTrack", "SendReferer",
                 "SpatialNavigationEnabled", "LinksIncludedInFocusChain",
                 "LocalContentCanAccessRemoteUrls",
                 "LocalContentCanAccessFileUrls", "XSSAuditingEnabled",
                 "SiteSpecificQuirksEnabled", "SyncEnabled", "SyncBookmarks",
                 "SyncHistory", "SyncPasswords", "SyncUserAgents",
                 "SyncSpeedDial", "SyncEncryptData",
                 "SyncEncryptPasswordsOnly",
                 "WarnOnMultipleClose", "ClickToFlashEnabled",
                 "FlashCookiesDeleteOnStartExit", "FlashCookieAutoRefresh",
                 "FlashCookieNotify",
                 ]:
        return toBool(prefClass.settings.value(
            "Help/" + key, prefClass.helpDefaults[key]))
    elif key in ["AdBlockSubscriptions", "AdBlockExceptions",
                 "ClickToFlashWhitelist", "SendRefererWhitelist",
                 "GreaseMonkeyDisabledScripts", "NoCacheHosts",
                 "FlashCookiesWhitelist", "FlashCookiesBlacklist",
                 ]:
        return toList(prefClass.settings.value(
            "Help/" + key, prefClass.helpDefaults[key]))
    else:
        return prefClass.settings.value("Help/" + key,
                                        prefClass.helpDefaults[key])
    

def setHelp(key, value, prefClass=Prefs):
    """
    Module function to store the various help settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["StandardFont", "FixedFont"]:
        prefClass.settings.setValue("Help/" + key, value.toString())
    elif key == "SaveUrlColor":
        prefClass.settings.setValue("Help/" + key, value.name())
    elif key == "WebSearchKeywords":
        # value is list of tuples of (keyword, engine name)
        prefClass.settings.remove("Help/" + key)
        prefClass.settings.beginWriteArray("Help/" + key, len(value))
        index = 0
        for v in value:
            prefClass.settings.setArrayIndex(index)
            prefClass.settings.setValue("Keyword", v[0])
            prefClass.settings.setValue("Engine", v[1])
            index += 1
        prefClass.settings.endArray()
    elif key == "DownloadManagerDownloads":
        # value is list of tuples of (URL, save location, done flag, page url)
        prefClass.settings.remove("Help/" + key)
        prefClass.settings.beginWriteArray("Help/" + key, len(value))
        index = 0
        for v in value:
            prefClass.settings.setArrayIndex(index)
            prefClass.settings.setValue("URL", v[0])
            prefClass.settings.setValue("Location", v[1])
            prefClass.settings.setValue("Done", v[2])
            prefClass.settings.setValue("PageURL", v[3])
            index += 1
        prefClass.settings.endArray()
    elif key == "RssFeeds":
        # value is list of tuples of (URL, title, icon)
        prefClass.settings.remove("Help/" + key)
        prefClass.settings.beginWriteArray("Help/" + key, len(value))
        index = 0
        for v in value:
            prefClass.settings.setArrayIndex(index)
            prefClass.settings.setValue("URL", v[0])
            prefClass.settings.setValue("Title", v[1])
            prefClass.settings.setValue("Icon", v[2])
            index += 1
        prefClass.settings.endArray()
    elif key in ["SyncFtpPassword", "SyncEncryptionKey"]:
        from Utilities.crypto import pwConvert
        prefClass.settings.setValue(
            "Help/" + key, pwConvert(value, encode=True))
    else:
        prefClass.settings.setValue("Help/" + key, value)
    

def getSystem(key, prefClass=Prefs):
    """
    Module function to retrieve the various system settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested system setting
    """
    from Utilities import supportedCodecs
    if key in ["StringEncoding", "IOEncoding"]:
        encoding = prefClass.settings.value(
            "System/" + key, prefClass.sysDefaults[key])
        if encoding not in supportedCodecs:
            encoding = prefClass.sysDefaults[key]
        return encoding
    

def setSystem(key, value, prefClass=Prefs):
    """
    Module function to store the various system settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("System/" + key, value)
    

def getQt4TranslationsDir(prefClass=Prefs):
    """
    Module function to retrieve the Qt4TranslationsDir setting.
    
    @param prefClass preferences class used as the storage area
    @return the requested Qt4TranslationsDir setting (string)
    """
    s = prefClass.settings.value(
        "Qt/Qt4TranslationsDir", prefClass.qtDefaults["Qt4TranslationsDir"])
    if s == "":
        s = os.getenv("QT4TRANSLATIONSDIR", "")
    if s == "":
        s = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    if s == "" and isWindowsPlatform():
        transPath = os.path.join(getPyQt5ModulesDirectory(), "translations")
        if os.path.exists(transPath):
            s = transPath
    return s
    

def getQt(key, prefClass=Prefs):
    """
    Module function to retrieve the various Qt settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested Qt setting
    """
    if key == "Qt4TranslationsDir":
        return getQt4TranslationsDir(prefClass)
    elif key in ["PyuicIndent"]:
        return int(prefClass.settings.value(
            "Qt/" + key, prefClass.qtDefaults[key]))
    elif key in ["PyuicFromImports"]:
        return toBool(prefClass.settings.value(
            "Qt/" + key, prefClass.qtDefaults[key]))
    else:
        return prefClass.settings.value("Qt/" + key, prefClass.qtDefaults[key])
    

def setQt(key, value, prefClass=Prefs):
    """
    Module function to store the various Qt settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Qt/" + key, value)
    

def getCorba(key, prefClass=Prefs):
    """
    Module function to retrieve the various corba settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested corba setting
    """
    return prefClass.settings.value(
        "Corba/" + key, prefClass.corbaDefaults[key])
    

def setCorba(key, value, prefClass=Prefs):
    """
    Module function to store the various corba settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Corba/" + key, value)
    

def getUser(key, prefClass=Prefs):
    """
    Module function to retrieve the various user settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    if key == "MailServerPassword":
        from Utilities.crypto import pwConvert
        return pwConvert(prefClass.settings.value(
            "User/" + key, prefClass.userDefaults[key]), encode=False)
    elif key in ["MailServerPort"]:
        return int(prefClass.settings.value(
            "User/" + key, prefClass.userDefaults[key]))
    elif key in ["MailServerAuthentication", "MailServerUseTLS",
                 "UseSystemEmailClient", "UseMasterPassword",
                 "SavePasswords"]:
        return toBool(prefClass.settings.value(
            "User/" + key, prefClass.userDefaults[key]))
    else:
        return prefClass.settings.value(
            "User/" + key, prefClass.userDefaults[key])
    

def setUser(key, value, prefClass=Prefs):
    """
    Module function to store the various user settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key == "MailServerPassword":
        from Utilities.crypto import pwConvert
        prefClass.settings.setValue(
            "User/" + key, pwConvert(value, encode=True))
    elif key == "MasterPassword":
        from Utilities.crypto.py3PBKDF2 import hashPassword
        prefClass.settings.setValue(
            "User/" + key, hashPassword(value))
    else:
        prefClass.settings.setValue("User/" + key, value)
    

def getVCS(key, prefClass=Prefs):
    """
    Module function to retrieve the VCS related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    if key in ["StatusMonitorInterval"]:
        return int(prefClass.settings.value(
            "VCS/" + key, prefClass.vcsDefaults[key]))
    else:
        return toBool(prefClass.settings.value(
            "VCS/" + key, prefClass.vcsDefaults[key]))
    

def setVCS(key, value, prefClass=Prefs):
    """
    Module function to store the VCS related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("VCS/" + key, value)
    

def getTasks(key, prefClass=Prefs):
    """
    Module function to retrieve the Tasks related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    if key in ["TasksFixmeColor", "TasksWarningColor",
               "TasksTodoColor", "TasksNoteColor"]:
        col = prefClass.settings.value("Tasks/" + key)
        if col is not None:
            return QColor(col)
        else:
            return prefClass.tasksDefaults[key]
    elif key in ["ClearOnFileClose", "TasksProjectAutoSave"]:
        return toBool(prefClass.settings.value(
            "Tasks/" + key, prefClass.tasksDefaults[key]))
    else:
        return prefClass.settings.value(
            "Tasks/" + key, prefClass.tasksDefaults[key])
    

def setTasks(key, value, prefClass=Prefs):
    """
    Module function to store the Tasks related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["TasksFixmeColor", "TasksWarningColor",
               "TasksTodoColor", "TasksNoteColor"]:
        prefClass.settings.setValue("Tasks/" + key, value.name())
    else:
        prefClass.settings.setValue("Tasks/" + key, value)
    

def getTemplates(key, prefClass=Prefs):
    """
    Module function to retrieve the Templates related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    if key in ["SeparatorChar"]:
        return prefClass.settings.value(
            "Templates/" + key, prefClass.templatesDefaults[key])
    elif key in ["EditorFont"]:
        f = QFont()
        f.fromString(prefClass.settings.value(
            "Templates/" + key, prefClass.templatesDefaults[key]))
        return f
    else:
        return toBool(prefClass.settings.value(
            "Templates/" + key, prefClass.templatesDefaults[key]))
    

def setTemplates(key, value, prefClass=Prefs):
    """
    Module function to store the Templates related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["EditorFont"]:
        prefClass.settings.setValue("Templates/" + key, value.toString())
    else:
        prefClass.settings.setValue("Templates/" + key, value)
    

def getPluginManager(key, prefClass=Prefs):
    """
    Module function to retrieve the plugin manager related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    if key in ["DownloadPath"]:
        return prefClass.settings.value(
            "PluginManager/" + key, prefClass.pluginManagerDefaults[key])
    elif key in ["UpdatesCheckInterval", "KeepGenerations"]:
        return int(prefClass.settings.value(
            "PluginManager/" + key, prefClass.pluginManagerDefaults[key]))
    elif key in ["HiddenPlugins"]:
        return toList(prefClass.settings.value(
            "PluginManager/" + key, prefClass.pluginManagerDefaults[key]))
    else:
        return toBool(prefClass.settings.value(
            "PluginManager/" + key, prefClass.pluginManagerDefaults[key]))
    

def setPluginManager(key, value, prefClass=Prefs):
    """
    Module function to store the plugin manager related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("PluginManager/" + key, value)
    

def getGraphics(key, prefClass=Prefs):
    """
    Module function to retrieve the Graphics related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    if key in ["Font"]:
        font = prefClass.settings.value(
            "Graphics/" + key, prefClass.graphicsDefaults[key])
        if isinstance(font, QFont):
            # workaround for an old bug in eric < 4.4
            return font
        else:
            f = QFont()
            f.fromString(font)
            return f
    else:
        return prefClass.settings.value(
            "Graphics/" + key, prefClass.graphicsDefaults[key])
    

def setGraphics(key, value, prefClass=Prefs):
    """
    Module function to store the Graphics related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["Font"]:
        prefClass.settings.setValue("Graphics/" + key, value.toString())
    else:
        prefClass.settings.setValue("Graphics/" + key, value)
    

def getIconEditor(key, prefClass=Prefs):
    """
    Module function to retrieve the Icon Editor related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    return prefClass.settings.value(
        "IconEditor/" + key, prefClass.iconEditorDefaults[key])
    

def setIconEditor(key, value, prefClass=Prefs):
    """
    Module function to store the Icon Editor related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("IconEditor/" + key, value)


def getFlakes(key, prefClass=Prefs):
    """
    Module function to retrieve the pyflakes related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    if key in ["IncludeInSyntaxCheck", "IgnoreStarImportWarnings"]:
        return toBool(prefClass.settings.value("Py3Flakes/" + key,
                      prefClass.pyflakesDefaults[key]))
    else:
        return prefClass.settings.value(
            "Py3Flakes/" + key, prefClass.pyflakesDefaults[key])
    

def setFlakes(key, value, prefClass=Prefs):
    """
    Module function to store the pyflakes related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("Py3Flakes/" + key, value)


def getTrayStarter(key, prefClass=Prefs):
    """
    Module function to retrieve the tray starter related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    return prefClass.settings.value(
        "TrayStarter/" + key, prefClass.trayStarterDefaults[key])
    

def setTrayStarter(key, value, prefClass=Prefs):
    """
    Module function to store the tray starter related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("TrayStarter/" + key, value)
    

def getIrc(key, prefClass=Prefs):
    """
    Module function to retrieve the IRC related settings.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested user setting
    """
    if key in ["TimestampIncludeDate", "ShowTimestamps", "ShowNotifications",
               "NotifyJoinPart", "NotifyMessage", "NotifyNick",
               "EnableIrcColours", "AutoUserInfoLookup",
               "MarkPositionWhenHidden", "AskOnShutdown"]:
        return toBool(prefClass.settings.value(
            "IRC/" + key, prefClass.ircDefaults[key]))
    elif key in ["AutoUserInfoMax", "AutoUserInfoInterval"]:
        return int(prefClass.settings.value(
            "IRC/" + key, prefClass.ircDefaults[key]))
    else:
        return prefClass.settings.value(
            "IRC/" + key, prefClass.ircDefaults[key])


def setIrc(key, value, prefClass=Prefs):
    """
    Module function to store the IRC related settings.
    
    @param key the key of the setting to be set
    @param value the value to be set
    @param prefClass preferences class used as the storage area
    """
    prefClass.settings.setValue("IRC/" + key, value)


def getGeometry(key, prefClass=Prefs):
    """
    Module function to retrieve the display geometry.
    
    @param key the key of the value to get
    @param prefClass preferences class used as the storage area
    @return the requested geometry setting
    """
    if key in ["MainMaximized"]:
        return toBool(prefClass.settings.value(
            "Geometry/" + key,
            prefClass.geometryDefaults[key]))
    else:
        v = prefClass.settings.value("Geometry/" + key)
        if v is not None:
            return v
        else:
            return prefClass.geometryDefaults[key]


def setGeometry(key, value, prefClass=Prefs):
    """
    Module function to store the display geometry.
    
    @param key the key of the setting to be set
    @param value the geometry to be set
    @param prefClass preferences class used as the storage area
    """
    if key in ["MainMaximized"]:
        prefClass.settings.setValue("Geometry/" + key, value)
    else:
        if prefClass.resetLayout:
            v = prefClass.geometryDefaults[key]
        else:
            v = value
        prefClass.settings.setValue("Geometry/" + key, v)


def resetLayout(prefClass=Prefs):
    """
    Module function to set a flag not storing the current layout.
    
    @param prefClass preferences class used as the storage area
    """
    prefClass.resetLayout = True


def shouldResetLayout(prefClass=Prefs):
    """
    Module function to indicate a reset of the layout.
    
    @param prefClass preferences class used as the storage area
    @return flag indicating a reset of the layout (boolean)
    """
    return prefClass.resetLayout
    

def saveResetLayout(prefClass=Prefs):
    """
    Module function to save the reset layout.
    
    @param prefClass preferences class used as the storage area
    """
    if prefClass.resetLayout:
        for key in list(prefClass.geometryDefaults.keys()):
            prefClass.settings.setValue(
                "Geometry/" + key,
                prefClass.geometryDefaults[key])


def toBool(value):
    """
    Module function to convert a value to bool.
    
    @param value value to be converted
    @return converted data
    """
    if value in ["true", "1", "True"]:
        return True
    elif value in ["false", "0", "False"]:
        return False
    else:
        return bool(value)


def toList(value):
    """
    Module function to convert a value to a list.
    
    @param value value to be converted
    @return converted data
    """
    if value is None:
        return []
    elif not isinstance(value, list):
        return [value]
    else:
        return value


def toByteArray(value):
    """
    Module function to convert a value to a byte array.
    
    @param value value to be converted
    @return converted data
    """
    if value is None:
        return QByteArray()
    else:
        return value


def toDict(value):
    """
    Module function to convert a value to a dictionary.
    
    @param value value to be converted
    @return converted data
    """
    if value is None:
        return {}
    else:
        return value


def convertPasswords(oldPassword, newPassword, prefClass=Prefs):
    """
    Module function to convert all passwords.
    
    @param oldPassword current master password (string)
    @param newPassword new master password (string)
    @param prefClass preferences class used as the storage area
    """
    from Utilities.crypto import pwRecode
    for key in ["ProxyPassword/Http", "ProxyPassword/Https",
                "ProxyPassword/Ftp", ]:
        prefClass.settings.setValue(
            "UI/" + key,
            pwRecode(
                prefClass.settings.value("UI/" + key,
                                         prefClass.uiDefaults[key]),
                oldPassword,
                newPassword
            )
        )
    for key in ["MailServerPassword"]:
        prefClass.settings.setValue(
            "User/" + key,
            pwRecode(
                prefClass.settings.value("User/" + key,
                                         prefClass.userDefaults[key]),
                oldPassword,
                newPassword
            )
        )
    for key in ["SyncFtpPassword", "SyncEncryptionKey"]:
        prefClass.settings.setValue(
            "Help/" + key,
            pwRecode(
                prefClass.settings.value("Help/" + key,
                                         prefClass.helpDefaults[key]),
                oldPassword,
                newPassword
            )
        )


initPreferences()
initRecentSettings()
