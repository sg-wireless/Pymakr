import os

from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSlot
from UI.EmailDialog import EmailDialog
from E5Gui.E5Action import E5Action
from Feedback.SendReport import sendReport
import Preferences
import Utilities
import UI.Info

# Start-Of-Header
name = "Feedback"
author = "Pycom"
autoactivate = True
deactivateable = False
version = "1.0.0"
className = "PluginFeedback"
packageName = "PluginFeedback"
shortDescription = "Implement the feedback window"
longDescription = "Allow users to report bugs and send suggestions (over HTTP)"

pyqtApi = 2
python2Compatible = True

def getID():
    ID = Preferences.Prefs.settings.value("Feedback/ID", "")
    if ID == "":
        import uuid
        ID = uuid.uuid4().hex
        Preferences.Prefs.settings.setValue("Feedback/ID", ID)
    else:
        ID = Preferences.Prefs.settings.value("Feedback/ID", "")

    return ID


class HTTPFeedbackDialog(EmailDialog):
    def __init__(self, mode="bug", parent=None):
        super(HTTPFeedbackDialog, self).__init__(mode, parent)
        self.__mode = mode

    @pyqtSlot()
    def on_sendButton_clicked(self):

        extra = "{0}----\n{1}----\n{2}".format(
            Utilities.generateVersionInfo("\n"), 
            Utilities.generatePluginsVersionInfo("\n"),
            Utilities.generateDistroInfo("\n"))

        params = {
            "type": self.__mode,
            "product": UI.Info.Program,
            "version": UI.Info.Version,
            "uid": getID(),
            "email": "",
            "title": self.subject.text(),
            "description": self.message.toPlainText(),
            "extra": extra
        }
        files = []
        for i in xrange(0, self.attachments.topLevelItemCount()):
            files.append(self.attachments.topLevelItem(i).text(0))

        sendReport(params, files, "upload")
        
        
        self.accept()


class PluginFeedback(QObject):
    def __init__(self,  ui):
        super(PluginFeedback, self).__init__(ui)
        self.__ui = ui



    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        self.__installMenus()
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        pass

    def __installMenu(self, text, menuText, tooltip, whatsthis, name, callback):
        menu = self.__ui.getMenu('help')
        reportAct = E5Action(
            self.tr(text),
            self.tr(menuText),
            0, 0, self, name)

        reportAct.setStatusTip(self.tr(tooltip))
        reportAct.setWhatsThis(self.tr(
            "<b>" + text + "...</b>" +
            "<p>" + whatsthis + "</p>"
        ))

        act = self.__ui.getMenuAction("help", name)

        menu.insertAction(act, reportAct)
        menu.removeAction(act)
        reportAct.triggered.connect(callback)
        return reportAct

    def __installMenus(self):
        self.__reportBugAct = self.__installMenu(
            'Report Bug', 'Report &Bug...', 'Report a bug',
            'Opens a dialog to report a bug.',
            'report_bug', self.__reportBug)

        self.__featRequestAct = self.__installMenu(
            'Request Feature', 'Request &Feature...',
            'Send a feature request',
            'Opens a dialog to send a feature request.',
            'request_feature', self.__requestFeature)


    def showFeedbackDialog(self, mode):
        self.dlg = HTTPFeedbackDialog(mode)
        self.dlg.show()

    def __reportBug(self):
        """
        Private slot to handle the Report Bug dialog.
        """
        self.showFeedbackDialog("bug")

    def __requestFeature(self):
        """
        Private slot to handle the Request a feature dialog.
        """
        self.showFeedbackDialog("feature")
