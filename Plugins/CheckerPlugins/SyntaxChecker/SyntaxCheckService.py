# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#
# pylint: disable=C0103

"""
Module implementing an interface to add different languages to do a syntax
check.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QObject, pyqtSignal

from E5Gui.E5Application import e5App
from Utilities import determinePythonVersion


class SyntaxCheckService(QObject):
    """
    Implement the syntax check service.
    
    Plugins can add other languages to the syntax check by calling addLanguage
    and support of an extra checker module on the client side which has to
    connect directly to the background service.
    
    @signal syntaxChecked(str, dict) emitted when the syntax check was done for
        one file
    @signal batchFinished() emitted when a syntax check batch is done
    @signal error(str, str) emitted in case of an error
    """
    syntaxChecked = pyqtSignal(str, dict)
    batchFinished = pyqtSignal()
    error = pyqtSignal(str, str)
    
    def __init__(self):
        """
        Constructor
        """
        super(SyntaxCheckService, self).__init__()
        self.backgroundService = e5App().getObject("BackgroundService")
        self.__supportedLanguages = {}
        
        self.queuedBatches = []
        self.batchesFinished = True

    def __determineLanguage(self, filename, source):
        """
        Private methode to determine the language of the file.
        
        @param filename of the sourcefile (str)
        @param source code of the file (str)
        @return language of the file or None if not found (str or None)
        """
        pyVer = determinePythonVersion(filename, source)
        if pyVer:
            return 'Python{0}'.format(pyVer)
        
        for lang, (env, getArgs, getExt) in self.__supportedLanguages.items():
            if filename.endswith(tuple(getExt())):
                return lang
        
        return None

    def addLanguage(
            self, lang, env, path, module, getArgs, getExt, callback, onError):
        """
        Public method to register a new language to the supported languages.
        
        @param lang new language to check syntax (str)
        @param env the environment in which the checker is implemented (str)
        @param path full path to the module (str)
        @param module name to import (str)
        @param getArgs function to collect the required arguments to call the
            syntax checker on client side (function)
        @param getExt function that returns the supported file extensions of
            the syntax checker (function)
        @param callback function on service response (function)
        @param onError callback function if client or service isn't available
            (function)
        """
        self.__supportedLanguages[lang] = env, getArgs, getExt
        # Connect to the background service
        self.backgroundService.serviceConnect(
            '{0}Syntax'.format(lang), env, path, module, callback, onError,
            onBatchDone=self.batchJobDone)

    def getLanguages(self):
        """
        Public method to return the supported language names.
        
        @return list of languanges supported (list of str)
        """
        return list(self.__supportedLanguages.keys())

    def removeLanguage(self, lang):
        """
        Public method to remove the language from syntax check.
        
        @param lang language to remove (str)
        """
        self.__supportedLanguages.pop(lang, None)
        self.backgroundService.serviceDisconnect(
            '{0}Syntax'.format(lang), lang)

    def getExtensions(self):
        """
        Public method to return all supported file extensions for the
        syntax checker dialog.
        
        @return set of all supported file extensions (set of str)
        """
        extensions = set()
        for env, getArgs, getExt in self.__supportedLanguages.values():
            for ext in getExt():
                extensions.add(ext)
        return extensions

    def syntaxCheck(self, lang, filename, source):
        """
        Public method to prepare a syntax check of one source file.
        
        @param lang language of the file or None to determine by internal
            algorithm (str or None)
        @param filename source filename (string)
        @param source string containing the code to check (string)
        """
        if not lang:
            lang = self.__determineLanguage(filename, source)
        if lang not in self.getLanguages():
            return
        data = [source]
        # Call the getArgs function to get the required arguments
        env, args, getExt = self.__supportedLanguages[lang]
        data.extend(args())
        self.backgroundService.enqueueRequest(
            '{0}Syntax'.format(lang), env, filename, data)
    
    def syntaxBatchCheck(self, argumentsList):
        """
        Public method to prepare a syntax check on multiple source files.
        
        @param argumentsList list of arguments tuples with each tuple
            containing filename and source (string, string)
        """
        data = {
        }
        for lang in self.getLanguages():
            data[lang] = []
        
        for filename, source in argumentsList:
            lang = self.__determineLanguage(filename, source)
            if lang not in self.getLanguages():
                continue
            else:
                jobData = [source]
                # Call the getArgs function to get the required arguments
                args = self.__supportedLanguages[lang][1]
                jobData.extend(args())
                data[lang].append((filename, jobData))
        
        self.queuedBatches = []
        for lang in self.getLanguages():
            if data[lang]:
                self.queuedBatches.append(lang)
                env = self.__supportedLanguages[lang][0]
                self.backgroundService.enqueueRequest(
                    'batch_{0}Syntax'.format(lang), env, "", data[lang])
                self.batchesFinished = False
    
    def cancelSyntaxBatchCheck(self):
        """
        Public method to cancel all batch jobs.
        """
        for lang in self.getLanguages():
            env = self.__supportedLanguages[lang][0]
            self.backgroundService.requestCancel(
                'batch_{0}Syntax'.format(lang), env)
    
    def __serviceError(self, fn, msg):
        """
        Private slot handling service errors.
        
        @param fn file name (string)
        @param msg message text (string)
        """
        self.error.emit(fn, msg)
    
    def serviceErrorPy2(self, fx, lang, fn, msg):
        """
        Public method handling service errors for Python 2.
        
        @param fx service name (string)
        @param lang language (string)
        @param fn file name (string)
        @param msg message text (string)
        """
        if fx in ['Python2Syntax', 'batch_Python2Syntax']:
            if fx == 'Python2Syntax':
                self.__serviceError(fn, msg)
            else:
                self.__serviceError(self.tr("Python 2 batch check"), msg)
                self.batchJobDone(fx, lang)
    
    def serviceErrorPy3(self, fx, lang, fn, msg):
        """
        Public method handling service errors for Python 2.
        
        @param fx service name (string)
        @param lang language (string)
        @param fn file name (string)
        @param msg message text (string)
        """
        if fx in ['Python3Syntax', 'batch_Python3Syntax']:
            if fx == 'Python3Syntax':
                self.__serviceError(fn, msg)
            else:
                self.__serviceError(self.tr("Python 3 batch check"), msg)
                self.batchJobDone(fx, lang)
    
    def serviceErrorJavaScript(self, fx, lang, fn, msg):
        """
        Public method handling service errors for JavaScript.
        
        @param fx service name (string)
        @param lang language (string)
        @param fn file name (string)
        @param msg message text (string)
        """
        if fx in ['JavaScriptSyntax', 'batch_JavaScriptSyntax']:
            if fx == 'JavaScriptSyntax':
                self.__serviceError(fn, msg)
            else:
                self.__serviceError(self.tr("JavaScript batch check"), msg)
                self.batchJobDone(fx, lang)
    
    def batchJobDone(self, fx, lang):
        """
        Public slot handling the completion of a batch job.
        
        @param fx service name (string)
        @param lang language (string)
        """
        if fx in ['Python2Syntax', 'batch_Python2Syntax',
                  'Python3Syntax', 'batch_Python3Syntax',
                  'JavaScriptSyntax', 'batch_JavaScriptSyntax']:
            if lang in self.queuedBatches:
                self.queuedBatches.remove(lang)
            # prevent sending the signal multiple times
            if len(self.queuedBatches) == 0 and not self.batchesFinished:
                self.batchFinished.emit()
                self.batchesFinished = True
