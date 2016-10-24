import Preferences
from Preferences.ConfigurationDialog import ConfigurationDialog, ConfigurationWidget
from FullUI import UiHelper
oldInit = None

toDeleteTxt = ['Application', 'Cooperation', 'CORBA', 'Debugger', 'Email', 'Graphics',
                'Help', 'Icons', 'IRC', 'Mimetypes', 'Network', 'Notifications',
                'Plugin Manager', 'Printer', 'Python', 'Qt', 'Security',
                'Templates', 'Tray Starter', 'Version Control Systems', 'Editor/APIs',
                'Editor/Mouse Click Handlers','Interface',
                'Editor/Highlighters/Filetype Associations','Project','Project/Project Viewer']

def modifyPreferencesDialog(dlg):
    if Preferences.Prefs.settings.value("UI/AdvancedBottomSidebar", False) != "true":
        toDeleteTxt.extend(['Log-Viewer'])    
    configList = dlg.cw.configList

    UiHelper.removeTreeElements(configList, toDeleteTxt)


def modifiedInit(self, parent=None, name=None, modal=False,
                 fromEric=True, displayMode=ConfigurationWidget.DefaultMode,
                 expandedEntries=[]):

    oldInit(self, parent, name, modal, fromEric, displayMode, expandedEntries)
    modifyPreferencesDialog(self)

def toDeleteExtend(items):
    toDeleteTxt.extend(items)

def hookConfigurationDialog():
    global oldInit
    if oldInit is None:
        oldInit = ConfigurationDialog.__init__
        ConfigurationDialog.__init__ = modifiedInit

hookConfigurationDialog() 