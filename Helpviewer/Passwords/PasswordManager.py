# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the password manager.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import pyqtSignal, QObject, QByteArray, QUrl, \
    QCoreApplication, QXmlStreamReader, qVersion
from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebPage

from E5Gui import E5MessageBox
from E5Gui.E5ProgressDialog import E5ProgressDialog

from Utilities.AutoSaver import AutoSaver
import Utilities
import Utilities.crypto
import Preferences


class PasswordManager(QObject):
    """
    Class implementing the password manager.
    
    @signal changed() emitted to indicate a change
    @signal passwordsSaved() emitted after the passwords were saved
    """
    changed = pyqtSignal()
    passwordsSaved = pyqtSignal()
    
    SEPARATOR = "===================="
    FORMS = "=====FORMS====="
    NEVER = "=====NEVER====="
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(PasswordManager, self).__init__(parent)
        
        self.__logins = {}
        self.__loginForms = {}
        self.__never = []
        self.__loaded = False
        self.__saveTimer = AutoSaver(self, self.save)
        
        self.changed.connect(self.__saveTimer.changeOccurred)
    
    def clear(self):
        """
        Public slot to clear the saved passwords.
        """
        if not self.__loaded:
            self.__load()
        
        self.__logins = {}
        self.__loginForms = {}
        self.__never = []
        self.__saveTimer.changeOccurred()
        self.__saveTimer.saveIfNeccessary()
        
        self.changed.emit()
    
    def getLogin(self, url, realm):
        """
        Public method to get the login credentials.
        
        @param url URL to get the credentials for (QUrl)
        @param realm realm to get the credentials for (string)
        @return tuple containing the user name (string) and password (string)
        """
        if not self.__loaded:
            self.__load()
        
        key = self.__createKey(url, realm)
        try:
            return self.__logins[key][0], Utilities.crypto.pwConvert(
                self.__logins[key][1], encode=False)
        except KeyError:
            return "", ""
    
    def setLogin(self, url, realm, username, password):
        """
        Public method to set the login credentials.
        
        @param url URL to set the credentials for (QUrl)
        @param realm realm to set the credentials for (string)
        @param username username for the login (string)
        @param password password for the login (string)
        """
        if not self.__loaded:
            self.__load()
        
        key = self.__createKey(url, realm)
        self.__logins[key] = (
            username,
            Utilities.crypto.pwConvert(password, encode=True)
        )
        self.changed.emit()
    
    def __createKey(self, url, realm):
        """
        Private method to create the key string for the login credentials.
        
        @param url URL to get the credentials for (QUrl)
        @param realm realm to get the credentials for (string)
        @return key string (string)
        """
        authority = url.authority()
        if authority.startswith("@"):
            authority = authority[1:]
        if realm:
            key = "{0}://{1} ({2})".format(
                url.scheme(), authority, realm)
        else:
            key = "{0}://{1}".format(url.scheme(), authority)
        return key
    
    def getFileName(self):
        """
        Public method to get the file name of the passwords file.
        
        @return name of the passwords file (string)
        """
        return os.path.join(Utilities.getConfigDir(), "browser", "logins.xml")
    
    def save(self):
        """
        Public slot to save the login entries to disk.
        """
        if not self.__loaded:
            return
        
        from .PasswordWriter import PasswordWriter
        loginFile = self.getFileName()
        writer = PasswordWriter()
        if not writer.write(
                loginFile, self.__logins, self.__loginForms, self.__never):
            E5MessageBox.critical(
                None,
                self.tr("Saving login data"),
                self.tr(
                    """<p>Login data could not be saved to <b>{0}</b></p>"""
                ).format(loginFile))
        else:
            self.passwordsSaved.emit()
    
    def __load(self):
        """
        Private method to load the saved login credentials.
        """
        loginFile = self.getFileName()
        if not os.path.exists(loginFile):
            self.__loadNonXml(os.path.splitext(loginFile)[0])
        else:
            from .PasswordReader import PasswordReader
            reader = PasswordReader()
            self.__logins, self.__loginForms, self.__never = \
                reader.read(loginFile)
            if reader.error() != QXmlStreamReader.NoError:
                E5MessageBox.warning(
                    None,
                    self.tr("Loading login data"),
                    self.tr("""Error when loading login data on"""
                            """ line {0}, column {1}:\n{2}""")
                    .format(reader.lineNumber(),
                            reader.columnNumber(),
                            reader.errorString()))
        
        self.__loaded = True
    
    def __loadNonXml(self, loginFile):
        """
        Private method to load non-XML password files.
        
        This method is to convert from the old, non-XML format to the new
        XML based format.
        
        @param loginFile name of the non-XML password file (string)
        """
        if os.path.exists(loginFile):
            try:
                f = open(loginFile, "r", encoding="utf-8")
                lines = f.read()
                f.close()
            except IOError as err:
                E5MessageBox.critical(
                    None,
                    self.tr("Loading login data"),
                    self.tr("""<p>Login data could not be loaded """
                            """from <b>{0}</b></p>"""
                            """<p>Reason: {1}</p>""")
                    .format(loginFile, str(err)))
                return
            
            data = []
            section = 0
            # 0 = login data, 1 = forms data, 2 = never store info
            for line in lines.splitlines():
                if line == self.FORMS:
                    section = 1
                    continue
                elif line == self.NEVER:
                    section = 2
                    continue
                
                if section == 0:
                    if line != self.SEPARATOR:
                        data.append(line)
                    else:
                        if len(data) != 3:
                            E5MessageBox.critical(
                                None,
                                self.tr("Loading login data"),
                                self.tr(
                                    """<p>Login data could not be loaded """
                                    """from <b>{0}</b></p>"""
                                    """<p>Reason: Wrong input format</p>""")
                                .format(loginFile))
                            return
                        self.__logins[data[0]] = (data[1], data[2])
                        data = []
                
                elif section == 1:
                    if line != self.SEPARATOR:
                        data.append(line)
                    else:
                        from .LoginForm import LoginForm
                        key = data[0]
                        form = LoginForm()
                        form.url = QUrl(data[1])
                        form.name = data[2]
                        form.hasAPassword = data[3] == "True"
                        for element in data[4:]:
                            name, value = element.split(" = ", 1)
                            form.elements.append((name, value))
                        self.__loginForms[key] = form
                        data = []
                
                elif section == 2:
                    self.__never.append(line)
            
            os.remove(loginFile)
        
        self.__loaded = True
        
        # this does the conversion
        self.save()
    
    def reload(self):
        """
        Public method to reload the login data.
        """
        if not self.__loaded:
            return
        
        self.__load()
    
    def close(self):
        """
        Public method to close the passwords manager.
        """
        self.__saveTimer.saveIfNeccessary()
    
    def removePassword(self, site):
        """
        Public method to remove a password entry.
        
        @param site web site name (string)
        """
        if site in self.__logins:
            del self.__logins[site]
            if site in self.__loginForms:
                del self.__loginForms[site]
            self.changed.emit()
    
    def allSiteNames(self):
        """
        Public method to get a list of all site names.
        
        @return sorted list of all site names (list of strings)
        """
        if not self.__loaded:
            self.__load()
        
        return sorted(self.__logins.keys())
    
    def sitesCount(self):
        """
        Public method to get the number of available sites.
        
        @return number of sites (integer)
        """
        if not self.__loaded:
            self.__load()
        
        return len(self.__logins)
    
    def siteInfo(self, site):
        """
        Public method to get a reference to the named site.
        
        @param site web site name (string)
        @return tuple containing the user name (string) and password (string)
        """
        if not self.__loaded:
            self.__load()
        
        if site not in self.__logins:
            return None
        
        return self.__logins[site][0], Utilities.crypto.pwConvert(
            self.__logins[site][1], encode=False)
    
    def post(self, request, data):
        """
        Public method to check, if the data to be sent contains login data.
        
        @param request reference to the network request (QNetworkRequest)
        @param data data to be sent (QByteArray)
        """
        # shall passwords be saved?
        if not Preferences.getUser("SavePasswords"):
            return
        
        # observe privacy
        if QWebSettings.globalSettings().testAttribute(
                QWebSettings.PrivateBrowsingEnabled):
            return
        
        if not self.__loaded:
            self.__load()
        
        # determine the url
        refererHeader = request.rawHeader(b"Referer")
        if refererHeader.isEmpty():
            return
        url = QUrl.fromEncoded(refererHeader)
        url = self.__stripUrl(url)
        
        # check that url isn't in __never
        if url.toString() in self.__never:
            return
        
        # check the request type
        navType = request.attribute(QNetworkRequest.User + 101)
        if navType is None:
            return
        if navType != QWebPage.NavigationTypeFormSubmitted:
            return
        
        # determine the QWebPage
        webPage = request.attribute(QNetworkRequest.User + 100)
        if webPage is None:
            return
        
        # determine the requests content type
        contentTypeHeader = request.rawHeader(b"Content-Type")
        if contentTypeHeader.isEmpty():
            return
        multipart = contentTypeHeader.startsWith(b"multipart/form-data")
        if multipart:
            boundary = contentTypeHeader.split(" ")[1].split("=")[1]
        else:
            boundary = None
        
        # find the matching form on the web page
        form = self.__findForm(webPage, data, boundary=boundary)
        if not form.isValid():
            return
        form.url = QUrl(url)
        
        # check, if the form has a password
        if not form.hasAPassword:
            return
        
        # prompt, if the form has never be seen
        key = self.__createKey(url, "")
        if key not in self.__loginForms:
            mb = E5MessageBox.E5MessageBox(
                E5MessageBox.Question,
                self.tr("Save password"),
                self.tr(
                    """<b>Would you like to save this password?</b><br/>"""
                    """To review passwords you have saved and remove them, """
                    """use the password management dialog of the Settings"""
                    """ menu."""),
                modal=True)
            neverButton = mb.addButton(
                self.tr("Never for this site"),
                E5MessageBox.DestructiveRole)
            noButton = mb.addButton(
                self.tr("Not now"), E5MessageBox.RejectRole)
            mb.addButton(E5MessageBox.Yes)
            mb.exec_()
            if mb.clickedButton() == neverButton:
                self.__never.append(url.toString())
                return
            elif mb.clickedButton() == noButton:
                return
        
        # extract user name and password
        user = ""
        password = ""
        for index in range(len(form.elements)):
            element = form.elements[index]
            type_ = form.elementTypes[element[0]]
            if user == "" and \
               type_ == "text":
                user = element[1]
            elif password == "" and \
                    type_ == "password":
                password = element[1]
                form.elements[index] = (element[0], "--PASSWORD--")
        if user and password:
            self.__logins[key] = \
                (user, Utilities.crypto.pwConvert(password, encode=True))
            self.__loginForms[key] = form
            self.changed.emit()
    
    def __stripUrl(self, url):
        """
        Private method to strip off all unneeded parts of a URL.
        
        @param url URL to be stripped (QUrl)
        @return stripped URL (QUrl)
        """
        cleanUrl = QUrl(url)
        if qVersion() >= "5.0.0":
            cleanUrl.setQuery("")
        else:
            cleanUrl.setQueryItems([])
        cleanUrl.setUserInfo("")
        
        authority = cleanUrl.authority()
        if authority.startswith("@"):
            authority = authority[1:]
        cleanUrl = QUrl("{0}://{1}{2}".format(
            cleanUrl.scheme(), authority, cleanUrl.path()))
        cleanUrl.setFragment("")
        return cleanUrl
    
    def __findForm(self, webPage, data, boundary=None):
        """
        Private method to find the form used for logging in.
        
        @param webPage reference to the web page (QWebPage)
        @param data data to be sent (QByteArray)
        @keyparam boundary boundary string (QByteArray) for multipart
            encoded data, None for urlencoded data
        @return parsed form (LoginForm)
        """
        from .LoginForm import LoginForm
        form = LoginForm()
        if boundary is not None:
            args = self.__extractMultipartQueryItems(data, boundary)
        else:
            if qVersion() >= "5.0.0":
                from PyQt5.QtCore import QUrlQuery
                argsUrl = QUrl.fromEncoded(
                    QByteArray(b"foo://bar.com/?" + QUrl.fromPercentEncoding(
                        data.replace(b"+", b"%20")).encode("utf-8")))
                encodedArgs = QUrlQuery(argsUrl).queryItems()
            else:
                argsUrl = QUrl.fromEncoded(
                    QByteArray(b"foo://bar.com/?" + data.replace(b"+", b"%20"))
                )
                encodedArgs = argsUrl.queryItems()
            args = set()
            for arg in encodedArgs:
                key = arg[0]
                value = arg[1]
                args.add((key, value))
        
        # extract the forms
        from Helpviewer.JavaScriptResources import parseForms_js
        lst = webPage.mainFrame().evaluateJavaScript(parseForms_js)
        for map in lst:
            formHasPasswords = False
            formName = map["name"]
            formIndex = map["index"]
            if isinstance(formIndex, float) and formIndex.is_integer():
                formIndex = int(formIndex)
            elements = map["elements"]
            formElements = set()
            formElementTypes = {}
            deadElements = set()
            for elementMap in elements:
                try:
                    name = elementMap["name"]
                    value = elementMap["value"]
                    type_ = elementMap["type"]
                except KeyError:
                    continue
                if type_ == "password":
                    formHasPasswords = True
                t = (name, value)
                try:
                    if elementMap["autocomplete"] == "off":
                        deadElements.add(t)
                except KeyError:
                    pass
                if name:
                    formElements.add(t)
                    formElementTypes[name] = type_
            if formElements.intersection(args) == args:
                form.hasAPassword = formHasPasswords
                if not formName:
                    form.name = formIndex
                else:
                    form.name = formName
                args.difference_update(deadElements)
                for elt in deadElements:
                    if elt[0] in formElementTypes:
                        del formElementTypes[elt[0]]
                form.elements = list(args)
                form.elementTypes = formElementTypes
                break
        
        return form
    
    def __extractMultipartQueryItems(self, data, boundary):
        """
        Private method to extract the query items for a post operation.
        
        @param data data to be sent (QByteArray)
        @param boundary boundary string (QByteArray)
        @return set of name, value pairs (set of tuple of string, string)
        """
        args = set()
        
        dataStr = bytes(data).decode()
        boundaryStr = bytes(boundary).decode()
        
        parts = dataStr.split(boundaryStr + "\r\n")
        for part in parts:
            if part.startswith("Content-Disposition"):
                lines = part.split("\r\n")
                name = lines[0].split("=")[1][1:-1]
                value = lines[2]
                args.add((name, value))
        
        return args
    
    def fill(self, page):
        """
        Public slot to fill login forms with saved data.
        
        @param page reference to the web page (QWebPage)
        """
        if page is None or page.mainFrame() is None:
            return
        
        if not self.__loaded:
            self.__load()
        
        url = page.mainFrame().url()
        url = self.__stripUrl(url)
        key = self.__createKey(url, "")
        if key not in self.__loginForms or \
           key not in self.__logins:
            return
        
        form = self.__loginForms[key]
        if form.url != url:
            return
        
        if form.name == "":
            formName = "0"
        else:
            try:
                formName = "{0:d}".format(int(form.name))
            except ValueError:
                formName = '"{0}"'.format(form.name)
        for element in form.elements:
            name = element[0]
            value = element[1]
            
            disabled = page.mainFrame().evaluateJavaScript(
                'document.forms[{0}].elements["{1}"].disabled'.format(
                    formName, name))
            if disabled:
                continue
            
            readOnly = page.mainFrame().evaluateJavaScript(
                'document.forms[{0}].elements["{1}"].readOnly'.format(
                    formName, name))
            if readOnly:
                continue
            
            type_ = page.mainFrame().evaluateJavaScript(
                'document.forms[{0}].elements["{1}"].type'.format(
                    formName, name))
            if type_ == "" or \
               type_ in ["hidden", "reset", "submit"]:
                continue
            if type_ == "password":
                value = Utilities.crypto.pwConvert(
                    self.__logins[key][1], encode=False)
            setType = type_ == "checkbox" and "checked" or "value"
            value = value.replace("\\", "\\\\")
            value = value.replace('"', '\\"')
            javascript = \
                'document.forms[{0}].elements["{1}"].{2}="{3}";'.format(
                    formName, name, setType, value)
            page.mainFrame().evaluateJavaScript(javascript)
    
    def masterPasswordChanged(self, oldPassword, newPassword):
        """
        Public slot to handle the change of the master password.
        
        @param oldPassword current master password (string)
        @param newPassword new master password (string)
        """
        if not self.__loaded:
            self.__load()
        
        progress = E5ProgressDialog(
            self.tr("Re-encoding saved passwords..."),
            None, 0, len(self.__logins), self.tr("%v/%m Passwords"),
            QApplication.activeModalWidget())
        progress.setMinimumDuration(0)
        progress.setWindowTitle(self.tr("Passwords"))
        count = 0
        
        for key in self.__logins:
            progress.setValue(count)
            QCoreApplication.processEvents()
            username, hash = self.__logins[key]
            hash = Utilities.crypto.pwRecode(hash, oldPassword, newPassword)
            self.__logins[key] = (username, hash)
            count += 1
        
        progress.setValue(len(self.__logins))
        QCoreApplication.processEvents()
        self.changed.emit()
