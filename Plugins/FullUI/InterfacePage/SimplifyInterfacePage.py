from PyQt5.QtWidgets import QToolButton, QLineEdit, QTextEdit, QCheckBox, QComboBox, QLabel, QPushButton
import os
import Preferences
import FullUI.InterfacePage.InterfacePage
from Preferences.ConfigurationPages.InterfacePage import InterfacePage as OldInterfacePage

originalSave = None
originalInit = None

path = os.path.dirname(os.path.realpath(__file__))
sl = "/"
if "\Plugins" in path:
    sl = "\\"
pluginsPath = path[0:path.index(sl+'Plugins'+sl)+8]


# data
styles = ['Dark','Light']
styleSheets = ['qdarkstyle/style.qss','qdarkstyle/style-light.qss']

#override InterfacePage
def save(self):
    newStyleSheet = getNewStyleSheet(self)
    self.styleSheetEdit.setText(newStyleSheet)
    originalSave(self)

#override InterfacePage
def newInit(self):
    originalInit(self)
    populateColorStyleCombo(self)
    
def getCurrentStyle():
    curStyle = Preferences.getUI("StyleSheet")
    for i,qssFileName in enumerate(styleSheets):
        if qssFileName in curStyle:
            return styles[i]

def getNewStyleSheet(self):
    boxIndex = self.colorComboBox.currentIndex()
    return pluginsPath + "/PycomStyle/" + styleSheets[boxIndex]

def populateColorStyleCombo(self):
    for style in styles:
        self.colorComboBox.addItem(style, style)

    curStyle = getCurrentStyle()
    currentIndex = self.colorComboBox.findData(curStyle)
    if currentIndex == -1:
        currentIndex = 0
    self.colorComboBox.setCurrentIndex(currentIndex)

def hookInterfacePage():
    global originalInit
    global originalSave
    if originalInit == None:
        originalSave = OldInterfacePage.save
        originalInit = OldInterfacePage.__init__
        OldInterfacePage.save = save
        OldInterfacePage.__init__ = newInit
    
hookInterfacePage()