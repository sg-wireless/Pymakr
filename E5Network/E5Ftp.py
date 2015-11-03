# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an extension to the Python FTP class to support FTP
proxies.
"""

from __future__ import unicode_literals

import ftplib
from socket import _GLOBAL_DEFAULT_TIMEOUT


class E5FtpProxyError(ftplib.Error):
    """
    Class to signal an error related to proxy configuration.
    
    The error message starts with a three digit error code followed by a
    space and the error string. Supported error codes are:
    <ul>
      <li>910: proxy error; the second number gives the category of the proxy
          error. The original response from the proxy is appended in the next
          line.</li>
      <li>930: proxy error; the second number gives the category of the proxy
          error. The original response from the proxy is appended in the next
          line.</li>
      <li>940: proxy error; the second number gives the category of the proxy
          error. The original response from the proxy is appended in the next
          line.</li>
      <li>950: proxy error; the second number gives the category of the proxy
          error. The original response from the proxy is appended in the next
          line.</li>
      <li>990: proxy usage is enabled but no proxy host given</li>
      <li>991: proxy usage is enabled but no proxy user given</li>
      <li>992: proxy usage is enabled but no proxy password given</li>
    </ul>
    """
    pass


class E5FtpProxyType(object):
    """
    Class defining the supported FTP proxy types.
    """
    NoProxy = 0                     # no proxy
    NonAuthorizing = 1              # non authorizing proxy
    UserAtServer = 2                # proxy login first, than user@remote.host
    Site = 3                        # proxy login first, than use SITE command
    Open = 4                        # proxy login first, than use OPEN command
    UserAtProxyuserAtServer = 5     # one login for both
    ProxyuserAtServer = 6
    # proxy login with remote host given, than normal remote login
    AuthResp = 7  # authenticate to proxy with AUTH and RESP commands
    Bluecoat = 8                    # bluecoat proxy


class E5Ftp(ftplib.FTP):
    """
    Class implementing an extension to the Python FTP class to support FTP
    proxies.
    """
    def __init__(self, host="", user="", password="", acct="",
                 proxyType=E5FtpProxyType.NoProxy, proxyHost="",
                 proxyPort=ftplib.FTP_PORT, proxyUser="", proxyPassword="",
                 proxyAccount="", timeout=_GLOBAL_DEFAULT_TIMEOUT):
        """
        Constructor
        
        @param host name of the FTP host (string)
        @param user user name for login to FTP host (string)
        @param password password for login to FTP host (string)
        @param acct account for login to FTP host (string)
        @param proxyType type of the FTP proxy (integer 0 to 8)
        @param proxyHost name of the FTP proxy (string)
        @param proxyPort port of the FTP proxy (integer)
        @param proxyUser user name for login to the proxy (string)
        @param proxyPassword password for login to the proxy (string)
        @param proxyAccount accounting info for the proxy (string)
        @param timeout timeout in seconds for blocking operations (integer)
        """
        super(E5Ftp, self).__init__()
        
        self.__timeout = timeout
        
        self.__proxyType = proxyType
        self.__proxyHost = proxyHost
        self.__proxyPort = proxyPort
        self.__proxyUser = proxyUser
        self.__proxyPassword = proxyPassword
        self.__proxyAccount = proxyAccount
        
        self.__host = host
        self.__port = ftplib.FTP_PORT
        self.__user = user
        self.__password = password
        self.__acct = acct
        
        if host:
            self.connect(host)
            if user:
                self.login(user, password, acct)
    
    def setProxy(self, proxyType=E5FtpProxyType.NoProxy, proxyHost="",
                 proxyPort=ftplib.FTP_PORT, proxyUser="", proxyPassword="",
                 proxyAccount=""):
        """
        Public method to set the proxy configuration.
        
        @param proxyType type of the FTP proxy (integer 0 to 8)
        @param proxyHost name of the FTP proxy (string)
        @param proxyPort port of the FTP proxy (integer)
        @param proxyUser user name for login to the proxy (string)
        @param proxyPassword password  for login to the proxy (string)
        @param proxyAccount accounting info for the proxy (string)
        """
        self.__proxyType = proxyType
        self.__proxyHost = proxyHost
        self.__proxyPort = proxyPort
        self.__proxyUser = proxyUser
        self.__proxyPassword = proxyPassword
        self.__proxyAccount = proxyAccount
    
    def setProxyAuthentication(self, proxyUser="", proxyPassword="",
                               proxyAccount=""):
        """
        Public method to set the proxy authentication info.
        
        @param proxyUser user name for login to the proxy (string)
        @param proxyPassword password  for login to the proxy (string)
        @param proxyAccount accounting info for the proxy (string)
        """
        self.__proxyUser = proxyUser
        self.__proxyPassword = proxyPassword
        self.__proxyAccount = proxyAccount
    
    def connect(self, host="", port=0, timeout=-999):
        """
        Public method to connect to the given FTP server.
        
        This extended method connects to the proxy instead of the given host,
        if a proxy is to be used. It throws an exception, if the proxy data
        is incomplete.
        
        @param host name of the FTP host (string)
        @param port port of the FTP host (integer)
        @param timeout timeout in seconds for blocking operations (integer)
        @return welcome message of the server (string)
        @exception E5FtpProxyError raised to indicate a proxy related issue
        """
        if host:
            self.__host = host
        if port:
            self.__port = port
        if timeout != -999:
            self.__timeout = timeout
        
        if self.__proxyType != E5FtpProxyType.NoProxy:
            if not self.__proxyHost:
                raise E5FtpProxyError(
                    "990 Proxy usage requested, but no proxy host given.")
            
            return super(E5Ftp, self).connect(
                self.__proxyHost, self.__proxyPort, self.__timeout)
        else:
            return super(E5Ftp, self).connect(
                self.__host, self.__port, self.__timeout)
    
    def login(self, user="", password="", acct=""):
        """
        Public method to login to the FTP server.
        
        This extended method respects the FTP proxy configuration. There are
        many different FTP proxy products available. But unfortunately there
        is no standard for how o traverse a FTP proxy. The lis below shows
        the sequence of commands used.
        
        <table>
          <tr><td>user</td><td>Username for remote host</td></tr>
          <tr><td>pass</td><td>Password for remote host</td></tr>
          <tr><td>pruser</td><td>Username for FTP proxy</td></tr>
          <tr><td>prpass</td><td>Password for FTP proxy</td></tr>
          <tr><td>remote.host</td><td>Hostname of the remote FTP server</td>
          </tr>
        </table>
        
        <dl>
          <dt>E5FtpProxyType.NoProxy:</dt>
          <dd>
            USER user<br/>
            PASS pass
          </dd>
          <dt>E5FtpProxyType.NonAuthorizing:</dt>
          <dd>
            USER user@remote.host<br/>
            PASS pass
          </dd>
          <dt>E5FtpProxyType.UserAtServer:</dt>
          <dd>
            USER pruser<br/>
            PASS prpass<br/>
            USER user@remote.host<br/>
            PASS pass
          </dd>
          <dt>E5FtpProxyType.Site:</dt>
          <dd>
            USER pruser<br/>
            PASS prpass<br/>
            SITE remote.site<br/>
            USER user<br/>
            PASS pass
          </dd>
          <dt>E5FtpProxyType.Open:</dt>
          <dd>
            USER pruser<br/>
            PASS prpass<br/>
            OPEN remote.site<br/>
            USER user<br/>
            PASS pass
          </dd>
          <dt>E5FtpProxyType.UserAtProxyuserAtServer:</dt>
          <dd>
            USER user@pruser@remote.host<br/>
            PASS pass@prpass
          </dd>
          <dt>E5FtpProxyType.ProxyuserAtServer:</dt>
          <dd>
            USER pruser@remote.host<br/>
            PASS prpass<br/>
            USER user<br/>
            PASS pass
          </dd>
          <dt>E5FtpProxyType.AuthResp:</dt>
          <dd>
            USER user@remote.host<br/>
            PASS pass<br/>
            AUTH pruser<br/>
            RESP prpass
          </dd>
          <dt>E5FtpProxyType.Bluecoat:</dt>
          <dd>
            USER user@remote.host pruser<br/>
            PASS pass<br/>
            ACCT prpass
          </dd>
        </dl>
        
        @param user username for the remote host (string)
        @param password password for the remote host (string)
        @param acct accounting information for the remote host (string)
        @return response sent by the remote host (string)
        @exception E5FtpProxyError raised to indicate a proxy related issue
        """
        if not user:
            user = "anonymous"
        if not password:
            # make sure it is a string
            password = ""
        if not acct:
            # make sure it is a string
            acct = ""
        if user == "anonymous" and password in {'', '-'}:
            password += "anonymous@"
        
        if self.__proxyType != E5FtpProxyType.NoProxy:
            if self.__proxyType != E5FtpProxyType.NonAuthorizing:
                # check, if a valid proxy configuration is known
                if not self.__proxyUser:
                    raise E5FtpProxyError(
                        "991 Proxy usage requested, but no proxy user given")
                if not self.__proxyPassword:
                    raise E5FtpProxyError(
                        "992 Proxy usage requested, but no proxy password"
                        " given")
            
            if self.__proxyType in [E5FtpProxyType.NonAuthorizing,
                                    E5FtpProxyType.AuthResp,
                                    E5FtpProxyType.Bluecoat]:
                user += "@" + self.__host
                if self.__proxyType == E5FtpProxyType.Bluecoat:
                    user += " " + self.__proxyUser
                    acct = self.__proxyPassword
            elif self.__proxyType == E5FtpProxyType.UserAtProxyuserAtServer:
                user = "{0}@{1}@{2}".format(
                    user, self.__proxyUser, self.__host)
                password = "{0}@{1}".format(password, self.__proxyPassword)
            else:
                pruser = self.__proxyUser
                if self.__proxyType == E5FtpProxyType.UserAtServer:
                    user += "@" + self.__host
                elif self.__proxyType == E5FtpProxyType.ProxyuserAtServer:
                    pruser += "@" + self.__host
                
                # authenticate to the proxy first
                presp = self.sendcmd("USER " + pruser)
                if presp[0] == "3":
                    presp = self.sendcmd("PASS " + self.__proxyPassword)
                if presp[0] == "3" and self.__proxyAccount:
                    presp = self.sendcmd("ACCT " + self.__proxyAccount)
                if presp[0] != "2":
                    raise E5FtpProxyError(
                        "9{0}0 Error authorizing at proxy\n{1}".format(
                            presp[0], presp))
                
                if self.__proxyType == E5FtpProxyType.Site:
                    # send SITE command
                    presp = self.sendcmd("SITE " + self.__host)
                    if presp[0] != "2":
                        raise E5FtpProxyError(
                            "9{0}0 Error sending SITE command\n{1}".format(
                                presp[0], presp))
                elif self.__proxyType == E5FtpProxyType.Open:
                    # send OPEN command
                    presp = self.sendcmd("OPEN " + self.__host)
                    if presp[0] != "2":
                        raise E5FtpProxyError(
                            "9{0}0 Error sending OPEN command\n{1}".format(
                                presp[0], presp))
        
        # authenticate to the remote host or combined to proxy and remote host
        resp = self.sendcmd("USER " + user)
        if resp[0] == "3":
            resp = self.sendcmd("PASS " + password)
        if resp[0] == "3":
            resp = self.sendcmd("ACCT " + acct)
        if resp[0] != "2":
            raise ftplib.error_reply(resp)
        
        if self.__proxyType == E5FtpProxyType.AuthResp:
            # authorize to the FTP proxy
            presp = self.sendcmd("AUTH " + self.__proxyUser)
            if presp[0] == "3":
                presp = self.sendcmd("RESP " + self.__proxyPassword)
            if presp[0] != "2":
                raise E5FtpProxyError(
                    "9{0}0 Error authorizing at proxy\n{1}".format(
                        presp[0], presp))
        
        return resp
