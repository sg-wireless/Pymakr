from PyQt5.QtWidgets import QLineEdit,QLabel, QToolButton, QComboBox
import Preferences

from Preferences.ConfigurationPages import Ui_InterfacePage
from Plugins.FullUI.InterfacePage import Ui_InterfacePage as New_Ui_InterfacePage
from FullUI import UiHelper
oldSetupUi = None

def modifiedSetupUI(self, ui_interfacepage):    
    fakeLineEdit = QLineEdit()
    fakeLabel = QLabel()
    fakeButton = QToolButton()
    fakeComboBox = QComboBox()
    self.label_3 = fakeLabel
    self.styleSheetEdit = fakeLineEdit
    self.styleSheetEdit.setReadOnly(True)
    self.styleSheetButton = fakeButton
    self.styleComboBox = fakeComboBox

    # setup new style box
    
    oldSetupUi(self, ui_interfacepage)

def hookInterfacePage():
    global oldSetupUi
    
    Ui_InterfacePage.Ui_InterfacePage = New_Ui_InterfacePage.Ui_InterfacePage
    oldSetupUi = Ui_InterfacePage.Ui_InterfacePage.setupUi
    Ui_InterfacePage.Ui_InterfacePage.setupUi = modifiedSetupUI

    
    
    # we must create fake widgets (hidden ones) to satisfy the original window content
    # oldSetupUi = Ui_InterfacePage.Ui_InterfacePage.setupUi
    # Ui_InterfacePage.Ui_InterfacePage.setupUi = modifiedSetupUI


hookInterfacePage() 