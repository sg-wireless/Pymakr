import os
import sys
import subprocess
from PyQt5.QtCore import QObject, QCoreApplication, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
from UI.Info import Version
from E5Gui import E5MessageBox

import UI
from E5Gui.E5Application import e5App
import Preferences
from PluginPycomDevice import PycomDeviceServer

# Start-Of-Header
name = "Fetch Updates"
author = "Pycom"
autoactivate = True
deactivateable = False
version = "1.0.0"
className = "PluginUpdate"
packageName = "PluginUpdate"
shortDescription = "Fetch software updates"
longDescription = "Fetch update notifications for software and firmware from the web server"


pyqtApi = 2
python2Compatible = True


def calc_int_version(version):
    """
        versions are numbered either ww.xx.yy or ww.xx.yy.rzz
        an example of the first one would be 1.10.00
        an example of the second one would be 1.10.00.b1

        the r character could be an 'a' for alpha, a 'b' for beta
        or 'rc' for release candidate

        easiest way is to convert the first form into the second,
        with r being 'r' for release

        direct translation from a JS function developed for the software
        server's manager
    """
    import re

    known_types = [b'a', b'b', b'rc', b'r']
    version_parts = version.split(".")
    dots = len(version_parts) - 1

    if dots != 2 and dots != 3:
        return None

    if dots == 2:
        version_parts.append('r0')

    release_type_number = re.match("([\D]+)([\d]+)", version_parts[3])
    release_type = known_types.index(release_type_number.group(1))
    if release_type == -1:
        return None

    version_parts[3] = release_type_number.group(2)

    # convert the numbers to integers
    for idx, val in enumerate(version_parts):
        version_parts[idx] = int(val)

    # number of bits per position: 6.7.10.2.7

    version = version_parts[0]
    version = (version << 7) | version_parts[1]
    version = (version << 10) | version_parts[2]
    version = (version << 2) | release_type
    version = (version << 7) | version_parts[3]

    return version

class PluginUpdate(QObject):
    def __init__(self,  ui):
        super(PluginUpdate, self).__init__(ui)
        Preferences.Prefs.uiDefaults['VersionsUrls6'] = ["https://software.pycom.io/findupgrade?product=pymakr&pymakr=true&type=all&platform=" + self.detectOsFamily()]
        self.__ui = ui
        self.__ui._UserInterface__versionCheckResult = self.__versionCheckResult
        self.__oldShowEvent = self.__ui.showEvent
        self.__ui.showEvent = self.__onWindowLoad
        self.__windowLoaded = False

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        self.__active = True
        if self.__windowLoaded == True:
            self.__initializeShell()

        self.__deviceServer = PycomDeviceServer()
        if self.__deviceServer.uname != None:
            self.processPycomDeviceVersion()
        self.__deviceServer.firmwareDetected.connect(self.processPycomDeviceVersion)
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        pass

    def detectLinuxVersion(self):
        FNULL = open(os.devnull, 'w')
        if subprocess.call(["dpkg", "--version"],stdout=FNULL, stderr=FNULL) == 0:
            return 'deb'
        elif subprocess.call(["rpm", "--version"],stdout=FNULL, stderr=FNULL) == 0:
            return 'rpm'
        return ''

    def detectOsFamily(self):
        osFamily = sys.platform.rstrip('1234567890')
        if osFamily == 'linux':
            osFamily = self.detectLinuxVersion()
        elif osFamily == 'darwin':
            osFamily = 'macos'
        return osFamily

    def __onWindowLoad(self, event):
        # I must run only once

        self.__ui.showEvent = self.__oldShowEvent
        self.__ui.showEvent(event)

        self.__windowLoaded = True


    def processPycomDeviceVersion(self):
        if PycomDeviceServer.uname != None:
            product = PycomDeviceServer.uname[0].lower()
            platform = PycomDeviceServer.uname[1].lower()
            url = "https://software.pycom.io/findupgrade?product=%s&type=stable&platform=%s" % (product, platform)
            try:
                request = QNetworkRequest(QUrl(url))
                networkManager = QNetworkAccessManager()
                request.setAttribute(QNetworkRequest.CacheLoadControlAttribute,
                                    QNetworkRequest.AlwaysNetwork)
                self.__request = request
                self.__networkManager = networkManager
                self.__reply = networkManager.get(self.__request)
                self.__reply.finished.connect(self.__PycomDeviceDownloadDone)
            except:
                pass

    def __PycomDeviceDownloadDone(self):
        """
        Private slot called, after the versions file has been downloaded
        from the internet.
        """
        import json
        reply = self.__reply
        try:
            if reply.error() == QNetworkReply.NoError:
                firmwareInfo = json.loads(str(reply.readAll()))
                reply.close()
            else:
                reply.close()
                return

            self.__PycomDeviceCheckResult(firmwareInfo)
        except:
            pass

    def __PycomDeviceCheckResult(self, firmwareInfo):
        ui = self.__ui
        if calc_int_version(firmwareInfo[u'version']) > calc_int_version(PycomDeviceServer.uname[2]):
            res = E5MessageBox.yesNo(
                ui,
                ui.tr("Update available"),
                ui.tr(
                    """The update to version <b>{0}</b> of the <b>{1}</b> is"""
                    """ available at <b>{2}</b>. Would you like"""
                    """ to get it?""")
                .format(firmwareInfo[u'version'], PycomDeviceServer.uname[0], firmwareInfo[u'file']),
                yesDefault=True)
            url = res and firmwareInfo[u'file'] or ''
            if url:
                QDesktopServices.openUrl(QUrl(url))

    def __versionCheckResult(self, versions):
        """
        Private method to show the result of the version check action.

        @param versions contents of the downloaded versions file (list of
            strings)
        """
        url = ""
        ui = self.__ui
        try:
            # check release version
            if calc_int_version(versions[0]) > calc_int_version(Version):
                res = E5MessageBox.yesNo(
                    ui,
                    ui.tr("Update available"),
                    ui.tr(
                        """Pymakr version <b>{0}</b> is now"""
                        """ available at <b>{1}</b>. Would you like"""
                        """ to get it?""")
                    .format(versions[0], versions[1]),
                    yesDefault=True)
                url = res and versions[1] or ''
            else:
                if ui.manualUpdatesCheck:
                    E5MessageBox.information(
                        ui,
                        ui.tr("Pymakr is up to date"),
                        ui.tr(
                            """You are using the latest version of"""
                            """ Pymakr"""))
        except IndexError:
            E5MessageBox.warning(
                ui,
                ui.tr("Error during updates check"),
                ui.tr("""Could not perform updates check."""))

        if url:
            QDesktopServices.openUrl(QUrl(url))

