from PyQt5.QtWidgets import QToolButton, QLineEdit, QComboBox, QLabel, QPushButton

from Project import Ui_PropertiesDialog
from Plugins.FullUI.ProjectProperties import Ui_PropertiesDialog as New_Ui_PropertiesDialog

originalSetupUi = None

def replaceProjectPropertiesDialog():
    # this dialog is also used for new projects
    global originalSetupUi

    Ui_PropertiesDialog.Ui_PropertiesDialog = New_Ui_PropertiesDialog.Ui_PropertiesDialog
    
    # we must create fake widgets (hidden ones) to satisfy the original window content
    originalSetupUi = Ui_PropertiesDialog.Ui_PropertiesDialog.setupUi
    Ui_PropertiesDialog.Ui_PropertiesDialog.setupUi = projectPropertiesDialog_setupUi


def projectPropertiesDialog_setupUi(self, PropertiesDialog):
    fakeToolButton = QToolButton()
    fakeLineEdit = QLineEdit()
    fakeComboBox = QComboBox()
    fakeLabel = QLabel()
    fakePushButton = QPushButton()
    self.mainscriptButton = fakeToolButton
    self.mainscriptEdit = fakeLineEdit
    self.languageComboBox = fakeComboBox
    self.versionEdit = fakeLineEdit
    self.vcsLabel = fakeLabel
    self.vcsInfoButton = fakePushButton

    originalSetupUi(self, PropertiesDialog)

replaceProjectPropertiesDialog()
