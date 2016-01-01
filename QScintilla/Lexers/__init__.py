# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Package implementing lexers for the various supported programming languages.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QCoreApplication

from QScintilla.QsciScintillaCompat import QSCINTILLA_VERSION

import Preferences
import UI.PixmapCache

# The lexer registry
# Dictionary with the language name as key. Each entry is a list with
#       0. display string (string)
#       1. dummy filename to derive lexer name (string)
#       2. reference to a function instantiating the specific lexer
#          This function must take a reference to the parent as argument.
#       3. list of open file filters (list of strings)
#       4. list of save file filters (list of strings)
#       5. default lexer associations (list of strings of filename wildcard
#          patterns to be associated with the lexer)
#       6. name of an icon file (string)
LexerRegistry = {}


def registerLexer(name, displayString, filenameSample, getLexerFunc,
                  openFilters=[], saveFilters=[],
                  defaultAssocs=[], iconFileName=""):
    """
    Module function to register a custom QScintilla lexer.
    
    @param name lexer language name (string)
    @param displayString display string (string)
    @param filenameSample dummy filename to derive lexer name (string)
    @param getLexerFunc reference to a function instantiating the specific
        lexer. This function must take a reference to the parent as its only
        argument.
    @keyparam openFilters list of open file filters (list of strings)
    @keyparam saveFilters list of save file filters (list of strings)
    @keyparam defaultAssocs default lexer associations (list of strings of
        filename wildcard patterns to be associated with the lexer)
    @keyparam iconFileName name of an icon file (string)
    @exception KeyError raised when the given name is already in use
    """
    global LexerRegistry
    if name in LexerRegistry:
        raise KeyError('Lexer "{0}" already registered.'.format(name))
    else:
        LexerRegistry[name] = [displayString, filenameSample, getLexerFunc,
                               openFilters, saveFilters, defaultAssocs[:],
                               iconFileName]


def unregisterLexer(name):
    """
    Module function to unregister a custom QScintilla lexer.
    
    @param name lexer language name (string)
    """
    if name in LexerRegistry:
        del LexerRegistry[name]


def getSupportedLanguages():
    """
    Module function to get a dictionary of supported lexer languages.
    
    @return dictionary of supported lexer languages. The keys are the
        internal language names. The items are lists of three entries.
        The first is the display string for the language, the second
        is a dummy file name, which can be used to derive the lexer, and
        the third is the name of an icon file.
        (string, string, string)
    """
    supportedLanguages = {
        "Bash": [QCoreApplication.translate('Lexers', "Bash"), 'dummy.sh',
                 "lexerBash.png"],
        "Batch": [QCoreApplication.translate('Lexers', "Batch"), 'dummy.bat',
                  "lexerBatch.png"],
        "C++": [QCoreApplication.translate('Lexers', "C/C++"), 'dummy.cpp',
                "lexerCPP.png"],
        "C#": [QCoreApplication.translate('Lexers', "C#"), 'dummy.cs',
               "lexerCsharp.png"],
        "CMake": [QCoreApplication.translate('Lexers', "CMake"), 'dummy.cmake',
                  "lexerCMake.png"],
        "CSS": [QCoreApplication.translate('Lexers', "CSS"), 'dummy.css',
                "lexerCSS.png"],
        "D": [QCoreApplication.translate('Lexers', "D"), 'dummy.d',
              "lexerD.png"],
        "Diff": [QCoreApplication.translate('Lexers', "Diff"), 'dummy.diff',
                 "lexerDiff.png"],
        "Fortran": [QCoreApplication.translate('Lexers', "Fortran"),
                    'dummy.f95', "lexerFortran.png"],
        "Fortran77": [QCoreApplication.translate('Lexers', "Fortran77"),
                      'dummy.f', "lexerFortran.png"],
        "HTML": [QCoreApplication.translate('Lexers', "HTML/PHP/XML"),
                 'dummy.html', "lexerHTML.png"],
        "IDL": [QCoreApplication.translate('Lexers', "IDL"), 'dummy.idl',
                "lexerIDL.png"],
        "Java": [QCoreApplication.translate('Lexers', "Java"), 'dummy.java',
                 "lexerJava.png"],
        "JavaScript": [QCoreApplication.translate('Lexers', "JavaScript"),
                       'dummy.js', "lexerJavaScript.png"],
        "Lua": [QCoreApplication.translate('Lexers', "Lua"), 'dummy.lua',
                "lexerLua.png"],
        "Makefile": [QCoreApplication.translate('Lexers', "Makefile"),
                     'dummy.mak', "lexerMakefile.png"],
        "Pascal": [QCoreApplication.translate('Lexers', "Pascal"), 'dummy.pas',
                   "lexerPascal.png"],
        "Perl": [QCoreApplication.translate('Lexers', "Perl"), 'dummy.pl',
                 "lexerPerl.png"],
        "PostScript": [QCoreApplication.translate('Lexers', "PostScript"),
                       'dummy.ps', "lexerPostscript.png"],
        "Povray": [QCoreApplication.translate('Lexers', "Povray"), 'dummy.pov',
                   "lexerPOV.png"],
        "Properties": [QCoreApplication.translate('Lexers', "Properties"),
                       'dummy.ini', "lexerProperties.png"],
        "Python2": [QCoreApplication.translate('Lexers', "Python2"),
                    'dummy.py', "lexerPython.png"],
        "Python3": [QCoreApplication.translate('Lexers', "Python3"),
                    'dummy.py', "lexerPython3.png"],
        "QSS": [QCoreApplication.translate('Lexers', "QSS"), 'dummy.qss',
                "lexerCSS.png"],
        "Ruby": [QCoreApplication.translate('Lexers', "Ruby"), 'dummy.rb',
                 "lexerRuby.png"],
        "SQL": [QCoreApplication.translate('Lexers', "SQL"), 'dummy.sql',
                "lexerSQL.png"],
        "TCL": [QCoreApplication.translate('Lexers', "TCL"), 'dummy.tcl',
                "lexerTCL.png"],
        "TeX": [QCoreApplication.translate('Lexers', "TeX"), 'dummy.tex',
                "lexerTeX.png"],
        "VHDL": [QCoreApplication.translate('Lexers', "VHDL"), 'dummy.vhd',
                 "lexerVHDL.png"],
        "XML": [QCoreApplication.translate('Lexers', "XML"), 'dummy.xml',
                "lexerXML.png"],
        "YAML": [QCoreApplication.translate('Lexers', "YAML"), 'dummy.yml',
                 "lexerYAML.png"],
    }
    
    if QSCINTILLA_VERSION() >= 0x020501:
        supportedLanguages.update({
            "Matlab": [QCoreApplication.translate('Lexers', "Matlab"),
                       'dummy.m.matlab', "lexerMatlab.png"],
            "Octave": [QCoreApplication.translate('Lexers', "Octave"),
                       'dummy.m.octave', "lexerOctave.png"],
        })
    
    if QSCINTILLA_VERSION() >= 0x020802:
        supportedLanguages["Gettext"] = \
            [QCoreApplication.translate('Lexers', "Gettext"), 'dummy.po',
             "lexerGettext.png"]
    
    if QSCINTILLA_VERSION() >= 0x020803:
        supportedLanguages["CoffeeScript"] = \
            [QCoreApplication.translate('Lexers', "CoffeeScript"),
             'dummy.coffee', "lexerCoffeeScript.png"]
    
    for name in LexerRegistry:
        if not name.startswith("Pygments|"):
            supportedLanguages[name] = \
                LexerRegistry[name][:2] + [LexerRegistry[name][6]]
    
    supportedLanguages["Guessed"] = \
        [QCoreApplication.translate('Lexers', "Pygments"), 'dummy.pygments',
         ""]
    
    return supportedLanguages


def getLanguageIcon(language, pixmap):
    """
    Module function to get an icon for a language.
    
    @param language language of the lexer (string)
    @param pixmap flag indicating to return a pixmap (boolean)
    @return icon for the language (QPixmap or QIcon)
    """
    supportedLanguages = getSupportedLanguages()
    if language in supportedLanguages:
        iconFileName = supportedLanguages[language][2]
    else:
        iconFileName = ""
    if pixmap:
        return UI.PixmapCache.getPixmap(iconFileName)
    else:
        return UI.PixmapCache.getIcon(iconFileName)


def getLexer(language, parent=None, pyname=""):
    """
    Module function to instantiate a lexer object for a given language.
    
    @param language language of the lexer (string)
    @param parent reference to the parent object (QObject)
    @keyparam pyname name of the pygments lexer to use (string)
    @return reference to the instanciated lexer object (QsciLexer)
    """
    if not pyname:
        try:
            if language in ["Python", "Python2", "Python3"]:
                from .LexerPython import LexerPython
                return LexerPython(language, parent)
            elif language == "C++":
                from .LexerCPP import LexerCPP
                return LexerCPP(
                    parent,
                    Preferences.getEditor("CppCaseInsensitiveKeywords"))
            elif language == "C#":
                from .LexerCSharp import LexerCSharp
                return LexerCSharp(parent)
            elif language == "IDL":
                from .LexerIDL import LexerIDL
                return LexerIDL(parent)
            elif language == "Java":
                from .LexerJava import LexerJava
                return LexerJava(parent)
            elif language == "JavaScript":
                from .LexerJavaScript import LexerJavaScript
                return LexerJavaScript(parent)
            elif language == "SQL":
                from .LexerSQL import LexerSQL
                return LexerSQL(parent)
            elif language == "HTML":
                from .LexerHTML import LexerHTML
                return LexerHTML(parent)
            elif language == "Perl":
                from .LexerPerl import LexerPerl
                return LexerPerl(parent)
            elif language == "Bash":
                from .LexerBash import LexerBash
                return LexerBash(parent)
            elif language == "Ruby":
                from .LexerRuby import LexerRuby
                return LexerRuby(parent)
            elif language == "Lua":
                from .LexerLua import LexerLua
                return LexerLua(parent)
            elif language == "CSS":
                from .LexerCSS import LexerCSS
                return LexerCSS(parent)
            elif language == "TeX":
                from .LexerTeX import LexerTeX
                return LexerTeX(parent)
            elif language == "Diff":
                from .LexerDiff import LexerDiff
                return LexerDiff(parent)
            elif language == "Makefile":
                from .LexerMakefile import LexerMakefile
                return LexerMakefile(parent)
            elif language == "Properties":
                from .LexerProperties import LexerProperties
                return LexerProperties(parent)
            elif language == "Batch":
                from .LexerBatch import LexerBatch
                return LexerBatch(parent)
            elif language == "D":
                from .LexerD import LexerD
                return LexerD(parent)
            elif language == "Povray":
                from .LexerPOV import LexerPOV
                return LexerPOV(parent)
            elif language == "CMake":
                from .LexerCMake import LexerCMake
                return LexerCMake(parent)
            elif language == "VHDL":
                from .LexerVHDL import LexerVHDL
                return LexerVHDL(parent)
            elif language == "TCL":
                from .LexerTCL import LexerTCL
                return LexerTCL(parent)
            elif language == "Fortran":
                from .LexerFortran import LexerFortran
                return LexerFortran(parent)
            elif language == "Fortran77":
                from .LexerFortran77 import LexerFortran77
                return LexerFortran77(parent)
            elif language == "Pascal":
                from .LexerPascal import LexerPascal
                return LexerPascal(parent)
            elif language == "PostScript":
                from .LexerPostScript import LexerPostScript
                return LexerPostScript(parent)
            elif language == "XML":
                from .LexerXML import LexerXML
                return LexerXML(parent)
            elif language == "YAML":
                from .LexerYAML import LexerYAML
                return LexerYAML(parent)
            elif language == "Matlab":
                from .LexerMatlab import LexerMatlab
                return LexerMatlab(parent)
            elif language == "Octave":
                from .LexerOctave import LexerOctave
                return LexerOctave(parent)
            elif language == "QSS":
                from .LexerQSS import LexerQSS
                return LexerQSS(parent)
            elif language == "Gettext":
                from .LexerPO import LexerPO
                return LexerPO(parent)
            elif language == "CoffeeScript":
                from .LexerCoffeeScript import LexerCoffeeScript
                return LexerCoffeeScript(parent)
            
            elif language in LexerRegistry:
                return LexerRegistry[language][2](parent)
            
            else:
                return __getPygmentsLexer(parent)
        except ImportError:
            return __getPygmentsLexer(parent)
    else:
        return __getPygmentsLexer(parent, name=pyname)


def __getPygmentsLexer(parent, name=""):
    """
    Private module function to instantiate a pygments lexer.
    
    @param parent reference to the parent widget
    @keyparam name name of the pygments lexer to use (string)
    @return reference to the lexer (LexerPygments) or None
    """
    from .LexerPygments import LexerPygments
    lexer = LexerPygments(parent, name=name)
    if lexer.canStyle():
        return lexer
    else:
        return None
    

def getOpenFileFiltersList(includeAll=False, asString=False,
                           withAdditional=True):
    """
    Module function to get the file filter list for an open file operation.
    
    @param includeAll flag indicating the inclusion of the
        All Files filter (boolean)
    @param asString flag indicating the list should be returned
        as a string (boolean)
    @keyparam withAdditional flag indicating to include additional filters
        defined by the user (boolean)
    @return file filter list (list of strings or string)
    """
    openFileFiltersList = [
        QCoreApplication.translate(
            'Lexers',
            'Python Files (*.py *.py2 *.py3)'),
        QCoreApplication.translate(
            'Lexers',
            'Python GUI Files (*.pyw *.pyw2 *.pyw3)'),
        QCoreApplication.translate(
            'Lexers',
            'Pyrex Files (*.pyx)'),
        QCoreApplication.translate(
            'Lexers',
            'Quixote Template Files (*.ptl)'),
        QCoreApplication.translate(
            'Lexers',
            'Ruby Files (*.rb)'),
        QCoreApplication.translate(
            'Lexers',
            'IDL Files (*.idl)'),
        QCoreApplication.translate(
            'Lexers',
            'C Files (*.h *.c)'),
        QCoreApplication.translate(
            'Lexers',
            'C++ Files (*.h *.hpp *.hh *.cxx *.cpp *.cc)'),
        QCoreApplication.translate(
            'Lexers',
            'C# Files (*.cs)'),
        QCoreApplication.translate(
            'Lexers',
            'HTML Files (*.html *.htm *.asp *.shtml)'),
        QCoreApplication.translate(
            'Lexers',
            'CSS Files (*.css)'),
        QCoreApplication.translate(
            'Lexers',
            'QSS Files (*.qss)'),
        QCoreApplication.translate(
            'Lexers',
            'PHP Files (*.php *.php3 *.php4 *.php5 *.phtml)'),
        QCoreApplication.translate(
            'Lexers',
            'XML Files (*.xml *.xsl *.xslt *.dtd *.svg *.xul *.xsd)'),
        QCoreApplication.translate(
            'Lexers',
            'Qt Resource Files (*.qrc)'),
        QCoreApplication.translate(
            'Lexers',
            'D Files (*.d *.di)'),
        QCoreApplication.translate(
            'Lexers',
            'Java Files (*.java)'),
        QCoreApplication.translate(
            'Lexers',
            'JavaScript Files (*.js)'),
        QCoreApplication.translate(
            'Lexers',
            'SQL Files (*.sql)'),
        QCoreApplication.translate(
            'Lexers',
            'Docbook Files (*.docbook)'),
        QCoreApplication.translate(
            'Lexers',
            'Perl Files (*.pl *.pm *.ph)'),
        QCoreApplication.translate(
            'Lexers',
            'Lua Files (*.lua)'),
        QCoreApplication.translate(
            'Lexers',
            'Tex Files (*.tex *.sty *.aux *.toc *.idx)'),
        QCoreApplication.translate(
            'Lexers',
            'Shell Files (*.sh)'),
        QCoreApplication.translate(
            'Lexers',
            'Batch Files (*.bat *.cmd)'),
        QCoreApplication.translate(
            'Lexers',
            'Diff Files (*.diff *.patch)'),
        QCoreApplication.translate(
            'Lexers',
            'Makefiles (*.mak)'),
        QCoreApplication.translate(
            'Lexers',
            'Properties Files (*.properties *.ini *.inf *.reg *.cfg'
            ' *.cnf *.rc)'),
        QCoreApplication.translate(
            'Lexers',
            'Povray Files (*.pov)'),
        QCoreApplication.translate(
            'Lexers',
            'CMake Files (CMakeLists.txt *.cmake *.ctest)'),
        QCoreApplication.translate(
            'Lexers',
            'VHDL Files (*.vhd *.vhdl)'),
        QCoreApplication.translate(
            'Lexers',
            'TCL/Tk Files (*.tcl *.tk)'),
        QCoreApplication.translate(
            'Lexers',
            'Fortran Files (*.f90 *.f95 *.f2k)'),
        QCoreApplication.translate(
            'Lexers',
            'Fortran77 Files (*.f *.for)'),
        QCoreApplication.translate(
            'Lexers',
            'Pascal Files (*.dpr *.dpk *.pas *.dfm *.inc *.pp)'),
        QCoreApplication.translate(
            'Lexers',
            'PostScript Files (*.ps)'),
        QCoreApplication.translate(
            'Lexers',
            'YAML Files (*.yaml *.yml)'),
    ]
    
    if QSCINTILLA_VERSION() >= 0x020501:
        openFileFiltersList.extend([
            QCoreApplication.translate(
                'Lexers',
                'Matlab Files (*.m *.m.matlab)'),
            QCoreApplication.translate(
                'Lexers',
                'Octave Files (*.m *.m.octave)'),
        ])
    
    if QSCINTILLA_VERSION() >= 0x020802:
        openFileFiltersList.append(
            QCoreApplication.translate(
                'Lexers',
                'Gettext Files (*.po)'),
        )
    
    if QSCINTILLA_VERSION() >= 0x020803:
        openFileFiltersList.append(
            QCoreApplication.translate(
                'Lexers',
                'CoffeeScript Files (*.coffee)'),
        )
    
    for name in LexerRegistry:
        openFileFiltersList.extend(LexerRegistry[name][3])
    
    if withAdditional:
        openFileFiltersList.extend(
            Preferences.getEditor("AdditionalOpenFilters"))
    
    openFileFiltersList.sort()
    if includeAll:
        openFileFiltersList.append(
            QCoreApplication.translate('Lexers', 'All Files (*)'))
    
    if asString:
        return ';;'.join(openFileFiltersList)
    else:
        return openFileFiltersList


def getSaveFileFiltersList(includeAll=False, asString=False,
                           withAdditional=True):
    """
    Module function to get the file filter list for a save file operation.
    
    @param includeAll flag indicating the inclusion of the
        All Files filter (boolean)
    @param asString flag indicating the list should be returned
        as a string (boolean)
    @keyparam withAdditional flag indicating to include additional filters
        defined by the user (boolean)
    @return file filter list (list of strings or string)
    """
    saveFileFiltersList = [
        QCoreApplication.translate(
            'Lexers',
            "Python2 Files (*.py2)"),
        QCoreApplication.translate(
            'Lexers',
            "Python3 Files (*.py)"),
        QCoreApplication.translate(
            'Lexers',
            "Python2 GUI Files (*.pyw2)"),
        QCoreApplication.translate(
            'Lexers',
            "Python3 GUI Files (*.pyw)"),
        QCoreApplication.translate(
            'Lexers',
            "Pyrex Files (*.pyx)"),
        QCoreApplication.translate(
            'Lexers',
            "Quixote Template Files (*.ptl)"),
        QCoreApplication.translate(
            'Lexers',
            "Ruby Files (*.rb)"),
        QCoreApplication.translate(
            'Lexers',
            "IDL Files (*.idl)"),
        QCoreApplication.translate(
            'Lexers',
            "C Files (*.c)"),
        QCoreApplication.translate(
            'Lexers',
            "C++ Files (*.cpp)"),
        QCoreApplication.translate(
            'Lexers',
            "C++/C Header Files (*.h)"),
        QCoreApplication.translate(
            'Lexers',
            "C# Files (*.cs)"),
        QCoreApplication.translate(
            'Lexers',
            "HTML Files (*.html)"),
        QCoreApplication.translate(
            'Lexers',
            "PHP Files (*.php)"),
        QCoreApplication.translate(
            'Lexers',
            "ASP Files (*.asp)"),
        QCoreApplication.translate(
            'Lexers',
            "CSS Files (*.css)"),
        QCoreApplication.translate(
            'Lexers',
            "QSS Files (*.qss)"),
        QCoreApplication.translate(
            'Lexers',
            "XML Files (*.xml)"),
        QCoreApplication.translate(
            'Lexers',
            "XSL Files (*.xsl)"),
        QCoreApplication.translate(
            'Lexers',
            "DTD Files (*.dtd)"),
        QCoreApplication.translate(
            'Lexers',
            "Qt Resource Files (*.qrc)"),
        QCoreApplication.translate(
            'Lexers',
            "D Files (*.d)"),
        QCoreApplication.translate(
            'Lexers',
            "D Interface Files (*.di)"),
        QCoreApplication.translate(
            'Lexers',
            "Java Files (*.java)"),
        QCoreApplication.translate(
            'Lexers',
            "JavaScript Files (*.js)"),
        QCoreApplication.translate(
            'Lexers',
            "SQL Files (*.sql)"),
        QCoreApplication.translate(
            'Lexers',
            "Docbook Files (*.docbook)"),
        QCoreApplication.translate(
            'Lexers',
            "Perl Files (*.pl)"),
        QCoreApplication.translate(
            'Lexers',
            "Perl Module Files (*.pm)"),
        QCoreApplication.translate(
            'Lexers',
            "Lua Files (*.lua)"),
        QCoreApplication.translate(
            'Lexers',
            "Shell Files (*.sh)"),
        QCoreApplication.translate(
            'Lexers',
            "Batch Files (*.bat)"),
        QCoreApplication.translate(
            'Lexers',
            "TeX Files (*.tex)"),
        QCoreApplication.translate(
            'Lexers',
            "TeX Template Files (*.sty)"),
        QCoreApplication.translate(
            'Lexers',
            "Diff Files (*.diff)"),
        QCoreApplication.translate(
            'Lexers',
            "Make Files (*.mak)"),
        QCoreApplication.translate(
            'Lexers',
            "Properties Files (*.ini)"),
        QCoreApplication.translate(
            'Lexers',
            "Configuration Files (*.cfg)"),
        QCoreApplication.translate(
            'Lexers',
            'Povray Files (*.pov)'),
        QCoreApplication.translate(
            'Lexers',
            'CMake Files (CMakeLists.txt)'),
        QCoreApplication.translate(
            'Lexers',
            'CMake Macro Files (*.cmake)'),
        QCoreApplication.translate(
            'Lexers',
            'VHDL Files (*.vhd)'),
        QCoreApplication.translate(
            'Lexers',
            'TCL Files (*.tcl)'),
        QCoreApplication.translate(
            'Lexers',
            'Tk Files (*.tk)'),
        QCoreApplication.translate(
            'Lexers',
            'Fortran Files (*.f95)'),
        QCoreApplication.translate(
            'Lexers',
            'Fortran77 Files (*.f)'),
        QCoreApplication.translate(
            'Lexers',
            'Pascal Files (*.pas)'),
        QCoreApplication.translate(
            'Lexers',
            'PostScript Files (*.ps)'),
        QCoreApplication.translate(
            'Lexers',
            'YAML Files (*.yml)'),
    ]
    
    if QSCINTILLA_VERSION() >= 0x020501:
        saveFileFiltersList.extend([
            QCoreApplication.translate(
                'Lexers',
                'Matlab Files (*.m)'),
            QCoreApplication.translate(
                'Lexers',
                'Octave Files (*.m.octave)'),
        ])
    
    if QSCINTILLA_VERSION() >= 0x020802:
        saveFileFiltersList.append(
            QCoreApplication.translate(
                'Lexers',
                'Gettext Files (*.po)'),
        )
    
    if QSCINTILLA_VERSION() >= 0x020803:
        saveFileFiltersList.append(
            QCoreApplication.translate(
                'Lexers',
                'CoffeeScript Files (*.coffee)'),
        )
    
    for name in LexerRegistry:
        saveFileFiltersList.extend(LexerRegistry[name][4])
    
    if withAdditional:
        saveFileFiltersList.extend(
            Preferences.getEditor("AdditionalSaveFilters"))
    
    saveFileFiltersList.sort()
    
    if includeAll:
        saveFileFiltersList.append(
            QCoreApplication.translate('Lexers', 'All Files (*)'))
    
    if asString:
        return ';;'.join(saveFileFiltersList)
    else:
        return saveFileFiltersList


def getDefaultLexerAssociations():
    """
    Module function to get a dictionary with the default associations.
    
    @return dictionary with the default lexer associations
    """
    assocs = {
        '*.sh': "Bash",
        '*.bash': "Bash",
        "*.bat": "Batch",
        "*.cmd": "Batch",
        '*.cpp': "C++",
        '*.cxx': "C++",
        '*.cc': "C++",
        '*.c': "C++",
        '*.hpp': "C++",
        '*.hh': "C++",
        '*.h': "C++",
        '*.cs': "C#",
        'CMakeLists.txt': "CMake",
        '*.cmake': "CMake",
        '*.cmake.in': "CMake",
        '*.ctest': "CMake",
        '*.ctest.in': "CMake",
        '*.css': "CSS",
        '*.qss': "QSS",
        "*.d": "D",
        "*.di": "D",
        "*.diff": "Diff",
        "*.patch": "Diff",
        '*.html': "HTML",
        '*.htm': "HTML",
        '*.asp': "HTML",
        '*.shtml': "HTML",
        '*.php': "HTML",
        '*.php3': "HTML",
        '*.php4': "HTML",
        '*.php5': "HTML",
        '*.phtml': "HTML",
        '*.xml': "HTML",
        '*.xsl': "HTML",
        '*.svg': "HTML",
        '*.xsd': "HTML",
        '*.xslt': "HTML",
        '*.dtd': "HTML",
        '*.rdf': "HTML",
        '*.xul': "HTML",
        '*.docbook': "HTML",
        '*.ui': "HTML",
        '*.ts': "HTML",
        '*.qrc': "HTML",
        '*.kid': "HTML",
        '*.idl': "IDL",
        '*.java': "Java",
        '*.js': "JavaScript",
        '*.lua': "Lua",
        "*makefile": "Makefile",
        "Makefile*": "Makefile",
        "*.mak": "Makefile",
        '*.pl': "Perl",
        '*.pm': "Perl",
        '*.ph': "Perl",
        '*.pov': "Povray",
        "*.properties": "Properties",
        "*.ini": "Properties",
        "*.inf": "Properties",
        "*.reg": "Properties",
        "*.cfg": "Properties",
        "*.cnf": "Properties",
        "*.rc": "Properties",
        '*.py': "Python",
        '*.pyw': "Python",
        '*.py2': "Python",
        '*.pyw2': "Python",
        '*.py3': "Python",
        '*.pyw3': "Python",
        '*.pyx': "Python",
        '*.ptl': "Python",
        '*.rb': "Ruby",
        '*.rbw': "Ruby",
        '*.sql': "SQL",
        "*.tex": "TeX",
        "*.sty": "TeX",
        "*.aux": "TeX",
        "*.toc": "TeX",
        "*.idx": "TeX",
        '*.vhd': "VHDL",
        '*.vhdl': "VHDL",
        "*.tcl": "TCL",
        "*.tk": "TCL",
        "*.f": "Fortran77",
        "*.for": "Fortran77",
        "*.f90": "Fortran",
        "*.f95": "Fortran",
        "*.f2k": "Fortran",
        "*.dpr": "Pascal",
        "*.dpk": "Pascal",
        "*.pas": "Pascal",
        "*.dfm": "Pascal",
        "*.inc": "Pascal",
        "*.pp": "Pascal",
        "*.ps": "PostScript",
        "*.xml": "XML",
        "*.xsl": "XML",
        "*.svg": "XML",
        "*.xsd": "XML",
        "*.xslt": "XML",
        "*.dtd": "XML",
        "*.rdf": "XML",
        "*.xul": "XML",
        "*.yaml": "YAML",
        "*.yml": "YAML",
        '*.e4d': "XML",
        '*.e4k': "XML",
        '*.e4m': "XML",
        '*.e4p': "XML",
        '*.e4q': "XML",
        '*.e4s': "XML",
        '*.e4t': "XML",
        '*.e5d': "XML",
        '*.e5k': "XML",
        '*.e5m': "XML",
        '*.e5p': "XML",
        '*.e5q': "XML",
        '*.e5s': "XML",
        '*.e5t': "XML",
        '*.e6d': "XML",
        '*.e6k': "XML",
        '*.e6m': "XML",
        '*.e6p': "XML",
        '*.e6q': "XML",
        '*.e6s': "XML",
        '*.e6t': "XML",
    }
    
    if QSCINTILLA_VERSION() >= 0x020501:
        assocs.update({
            '*.m': "Matlab",
            '*.m.matlab': "Matlab",
            '*.m.octave': "Octave",
        })
    
    if QSCINTILLA_VERSION() >= 0x020803:
        assocs['*.coffee'] = "CoffeeScript"
    
    for name in LexerRegistry:
        for pattern in LexerRegistry[name][5]:
            assocs[pattern] = name
    
    return assocs
