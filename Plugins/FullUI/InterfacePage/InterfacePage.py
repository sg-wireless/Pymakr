import os
from PyQt5.QtWidgets import QLineEdit,QLabel, QToolButton, QComboBox
import Preferences

from Preferences.ConfigurationPages.InterfacePage import InterfacePage
from Preferences.ConfigurationPages import Ui_InterfacePage
from Plugins.FullUI.InterfacePage import Ui_InterfacePage as New_Ui_InterfacePage
from FullUI import UiHelper
oldSetupUi = None
oldSave = None
oldInit = None


#override Ui_InterfacePage
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
    self.styleComboBox.setReadOnly(True)

    oldSetupUi(self, ui_interfacepage)

#override InterfacePage
def save(self):
    print("Save override InterfacePage")
    newStyleSheet = getNewStyleSheet(self)
    self.styleSheetEdit.setText(newStyleSheet)
    # Preferences.setUI(
    #         "StyleSheet",
    #         newStyleSheet)
    oldSave(self)

#override InterfacePage
def init(self):
    oldInit(self)
    print("Init override InterfacePage")
    fakeComboBox = QComboBox()
    self.colorComboBox = fakeComboBox
    self.__path = os.path.dirname(os.path.realpath(__file__))
    self.__pluginsPath = self.__path[0:self.__path.index('/Plugins/')+8]
    populateColorStyleCombo(self)

def getCurrentStyle():
    curStyle = Preferences.getUI("StyleSheet")
    if "style-light.qss" in curStyle:
        return 'Light'
    else:
        return 'Dark'

def getNewStyleSheet(self):
    boxIndex = self.colorComboBox.currentIndex()
    styleSheets = ['qdarkstyle/style.qss','qdarkstyle/style-light.qss']
    return self.__pluginsPath + "/PycomStyle/" + styleSheets[boxIndex]

def populateColorStyleCombo(self):
    curStyle = getCurrentStyle()
    styles = ['Dark','Light']
    for style in styles:
        self.colorComboBox.addItem(style, style)
    currentIndex = self.colorComboBox.findData(curStyle)
    if currentIndex == -1:
        currentIndex = 0
    self.colorComboBox.setCurrentIndex(currentIndex)

def hookInterfacePage():
    global oldSetupUi
    global oldSave
    global oldInit
    Ui_InterfacePage.Ui_InterfacePage = New_Ui_InterfacePage.Ui_InterfacePage
    oldSetupUi = Ui_InterfacePage.Ui_InterfacePage.setupUi
    Ui_InterfacePage.Ui_InterfacePage.setupUi = modifiedSetupUI

    if oldSave == None:
    
        #InterfacePage
        oldSave = InterfacePage.save
        oldInit = InterfacePage.__init__
        InterfacePage.save = save
        InterfacePage.__init__ = init

hookInterfacePage() 