from PyQt5.QtWidgets import QToolButton, QLineEdit, QTextEdit, QCheckBox, QComboBox, QLabel, QPushButton

from Preferences.ConfigurationPages import Ui_InterfacePage
from Plugins.FullUI.InterfacePage import Ui_InterfacePage as New_Ui_InterfacePage

originalSetupUi = None

def replaceInterfacePage():
    # this dialog is also used for new projects
    global originalSetupUi

    Ui_InterfacePage.Ui_InterfacePage = New_Ui_InterfacePage.Ui_InterfacePage
    originalSetupUi = Ui_InterfacePage.Ui_InterfacePage.setupUi
    Ui_InterfacePage.Ui_InterfacePage.setupUi = interfacePage_setupUi


def interfacePage_setupUi(self, interfacepage):
    fakeLineEdit = QLineEdit()
    fakeLabel = QLabel()
    fakeButton = QToolButton()
    fakeComboBox = QComboBox()
    print("Modiffied setupUI activated")
    self.label_3 = fakeLabel
    self.styleSheetEdit = fakeLineEdit
    self.styleSheetButton = fakeButton
    self.styleComboBox = fakeComboBox
    originalSetupUi(self, interfacepage)

replaceInterfacePage()