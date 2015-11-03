# -*- coding: utf-8 -*-

# Copyright (c) 2004 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the TR Previewer main window.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QDir, QTimer, QFileInfo, pyqtSignal, QEvent, QSize, \
    QTranslator, QObject, Qt, QCoreApplication
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QSizePolicy, QSpacerItem, QWidget, QHBoxLayout, \
    QWhatsThis, QMdiArea, qApp, QApplication, QComboBox, QVBoxLayout, \
    QAction, QLabel
from PyQt5 import uic


from E5Gui import E5MessageBox, E5FileDialog
from E5Gui.E5MainWindow import E5MainWindow

import UI.PixmapCache
import UI.Config

import Preferences


noTranslationName = QCoreApplication.translate(
    "TRPreviewer", "<No translation>")


class TRPreviewer(E5MainWindow):
    """
    Class implementing the UI Previewer main window.
    """
    def __init__(self, filenames=[], parent=None, name=None):
        """
        Constructor
        
        @param filenames filenames of form and/or translation files to load
        @param parent parent widget of this window (QWidget)
        @param name name of this window (string)
        """
        self.mainWidget = None
        self.currentFile = QDir.currentPath()
        
        super(TRPreviewer, self).__init__(parent)
        if not name:
            self.setObjectName("TRPreviewer")
        else:
            self.setObjectName(name)
        
        self.setStyle(Preferences.getUI("Style"),
                      Preferences.getUI("StyleSheet"))
        
        self.resize(QSize(800, 600).expandedTo(self.minimumSizeHint()))
        self.statusBar()
        
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        self.setWindowTitle(self.tr("Translations Previewer"))

        self.cw = QWidget(self)
        self.cw.setObjectName("qt_central_widget")
        
        self.TRPreviewerLayout = QVBoxLayout(self.cw)
        self.TRPreviewerLayout.setContentsMargins(6, 6, 6, 6)
        self.TRPreviewerLayout.setSpacing(6)
        self.TRPreviewerLayout.setObjectName("TRPreviewerLayout")

        self.languageLayout = QHBoxLayout()
        self.languageLayout.setContentsMargins(0, 0, 0, 0)
        self.languageLayout.setSpacing(6)
        self.languageLayout.setObjectName("languageLayout")

        self.languageLabel = QLabel(
            self.tr("Select language file"), self.cw)
        self.languageLabel.setObjectName("languageLabel")
        self.languageLayout.addWidget(self.languageLabel)

        self.languageCombo = QComboBox(self.cw)
        self.languageCombo.setObjectName("languageCombo")
        self.languageCombo.setEditable(False)
        self.languageCombo.setToolTip(self.tr("Select language file"))
        self.languageCombo.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.languageLayout.addWidget(self.languageCombo)
        
        languageSpacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.languageLayout.addItem(languageSpacer)
        self.TRPreviewerLayout.addLayout(self.languageLayout)

        self.preview = WidgetArea(self.cw)
        self.preview.setObjectName("preview")
        self.TRPreviewerLayout.addWidget(self.preview)
        self.preview.lastWidgetClosed.connect(self.__updateActions)

        self.setCentralWidget(self.cw)
        
        self.languageCombo.activated[str].connect(self.setTranslation)
        
        self.translations = TranslationsDict(self.languageCombo, self)
        self.translations.translationChanged.connect(
            self.preview.rebuildWidgets)
        
        self.__initActions()
        self.__initMenus()
        self.__initToolbars()
        
        self.__updateActions()
        
        # fire up the single application server
        from .TRSingleApplication import TRSingleApplicationServer
        self.SAServer = TRSingleApplicationServer(self)
        self.SAServer.loadForm.connect(self.preview.loadWidget)
        self.SAServer.loadTranslation.connect(self.translations.add)
        
        # defere loading of a UI file until we are shown
        self.filesToLoad = filenames[:]
        
    def show(self):
        """
        Public slot to show this dialog.
        
        This overloaded slot loads a UI file to be previewed after
        the main window has been shown. This way, previewing a dialog
        doesn't interfere with showing the main window.
        """
        super(TRPreviewer, self).show()
        if self.filesToLoad:
            filenames, self.filesToLoad = (self.filesToLoad[:], [])
            first = True
            for fn in filenames:
                fi = QFileInfo(fn)
                if fi.suffix().lower() == 'ui':
                    self.preview.loadWidget(fn)
                elif fi.suffix().lower() == 'qm':
                    self.translations.add(fn, first)
                    first = False
            
            self.__updateActions()
        
    def closeEvent(self, event):
        """
        Protected event handler for the close event.
        
        @param event close event (QCloseEvent)
        """
        if self.SAServer is not None:
            self.SAServer.shutdown()
            self.SAServer = None
        event.accept()
        
    def __initActions(self):
        """
        Private method to define the user interface actions.
        """
        self.openUIAct = QAction(
            UI.PixmapCache.getIcon("openUI.png"),
            self.tr('&Open UI Files...'), self)
        self.openUIAct.setStatusTip(self.tr('Open UI files for display'))
        self.openUIAct.setWhatsThis(self.tr(
            """<b>Open UI Files</b>"""
            """<p>This opens some UI files for display.</p>"""
        ))
        self.openUIAct.triggered.connect(self.__openWidget)
        
        self.openQMAct = QAction(
            UI.PixmapCache.getIcon("openQM.png"),
            self.tr('Open &Translation Files...'), self)
        self.openQMAct.setStatusTip(self.tr(
            'Open Translation files for display'))
        self.openQMAct.setWhatsThis(self.tr(
            """<b>Open Translation Files</b>"""
            """<p>This opens some translation files for display.</p>"""
        ))
        self.openQMAct.triggered.connect(self.__openTranslation)
        
        self.reloadAct = QAction(
            UI.PixmapCache.getIcon("reload.png"),
            self.tr('&Reload Translations'), self)
        self.reloadAct.setStatusTip(self.tr(
            'Reload the loaded translations'))
        self.reloadAct.setWhatsThis(self.tr(
            """<b>Reload Translations</b>"""
            """<p>This reloads the translations for the loaded"""
            """ languages.</p>"""
        ))
        self.reloadAct.triggered.connect(self.translations.reload)
        
        self.exitAct = QAction(
            UI.PixmapCache.getIcon("exit.png"), self.tr('&Quit'), self)
        self.exitAct.setShortcut(QKeySequence(
            self.tr("Ctrl+Q", "File|Quit")))
        self.exitAct.setStatusTip(self.tr('Quit the application'))
        self.exitAct.setWhatsThis(self.tr(
            """<b>Quit</b>"""
            """<p>Quit the application.</p>"""
        ))
        self.exitAct.triggered.connect(qApp.closeAllWindows)
        
        self.whatsThisAct = QAction(
            UI.PixmapCache.getIcon("whatsThis.png"),
            self.tr('&What\'s This?'), self)
        self.whatsThisAct.setShortcut(QKeySequence(self.tr("Shift+F1")))
        self.whatsThisAct.setStatusTip(self.tr('Context sensitive help'))
        self.whatsThisAct.setWhatsThis(self.tr(
            """<b>Display context sensitive help</b>"""
            """<p>In What's This? mode, the mouse cursor shows an arrow"""
            """ with a question mark, and you can click on the interface"""
            """ elements to get a short description of what they do and"""
            """ how to use them. In dialogs, this feature can be accessed"""
            """ using the context help button in the titlebar.</p>"""
        ))
        self.whatsThisAct.triggered.connect(self.__whatsThis)

        self.aboutAct = QAction(self.tr('&About'), self)
        self.aboutAct.setStatusTip(self.tr(
            'Display information about this software'))
        self.aboutAct.setWhatsThis(self.tr(
            """<b>About</b>"""
            """<p>Display some information about this software.</p>"""
        ))
        self.aboutAct.triggered.connect(self.__about)
        
        self.aboutQtAct = QAction(self.tr('About &Qt'), self)
        self.aboutQtAct.setStatusTip(
            self.tr('Display information about the Qt toolkit'))
        self.aboutQtAct.setWhatsThis(self.tr(
            """<b>About Qt</b>"""
            """<p>Display some information about the Qt toolkit.</p>"""
        ))
        self.aboutQtAct.triggered.connect(self.__aboutQt)
        
        self.tileAct = QAction(self.tr('&Tile'), self)
        self.tileAct.setStatusTip(self.tr('Tile the windows'))
        self.tileAct.setWhatsThis(self.tr(
            """<b>Tile the windows</b>"""
            """<p>Rearrange and resize the windows so that they are"""
            """ tiled.</p>"""
        ))
        self.tileAct.triggered.connect(self.preview.tileSubWindows)
        
        self.cascadeAct = QAction(self.tr('&Cascade'), self)
        self.cascadeAct.setStatusTip(self.tr('Cascade the windows'))
        self.cascadeAct.setWhatsThis(self.tr(
            """<b>Cascade the windows</b>"""
            """<p>Rearrange and resize the windows so that they are"""
            """ cascaded.</p>"""
        ))
        self.cascadeAct.triggered.connect(self.preview.cascadeSubWindows)
        
        self.closeAct = QAction(
            UI.PixmapCache.getIcon("close.png"), self.tr('&Close'), self)
        self.closeAct.setShortcut(QKeySequence(self.tr(
            "Ctrl+W", "File|Close")))
        self.closeAct.setStatusTip(self.tr('Close the current window'))
        self.closeAct.setWhatsThis(self.tr(
            """<b>Close Window</b>"""
            """<p>Close the current window.</p>"""
        ))
        self.closeAct.triggered.connect(self.preview.closeWidget)
        
        self.closeAllAct = QAction(self.tr('Clos&e All'), self)
        self.closeAllAct.setStatusTip(self.tr('Close all windows'))
        self.closeAllAct.setWhatsThis(self.tr(
            """<b>Close All Windows</b>"""
            """<p>Close all windows.</p>"""
        ))
        self.closeAllAct.triggered.connect(self.preview.closeAllWidgets)

    def __initMenus(self):
        """
        Private method to create the menus.
        """
        mb = self.menuBar()

        menu = mb.addMenu(self.tr('&File'))
        menu.setTearOffEnabled(True)
        menu.addAction(self.openUIAct)
        menu.addAction(self.openQMAct)
        menu.addAction(self.reloadAct)
        menu.addSeparator()
        menu.addAction(self.closeAct)
        menu.addAction(self.closeAllAct)
        menu.addSeparator()
        menu.addAction(self.exitAct)
        
        self.windowMenu = mb.addMenu(self.tr('&Window'))
        self.windowMenu.setTearOffEnabled(True)
        self.windowMenu.aboutToShow.connect(self.__showWindowMenu)
        self.windowMenu.triggered.connect(self.preview.toggleSelectedWidget)
        
        mb.addSeparator()
        
        menu = mb.addMenu(self.tr('&Help'))
        menu.setTearOffEnabled(True)
        menu.addAction(self.aboutAct)
        menu.addAction(self.aboutQtAct)
        menu.addSeparator()
        menu.addAction(self.whatsThisAct)

    def __initToolbars(self):
        """
        Private method to create the toolbars.
        """
        filetb = self.addToolBar(self.tr("File"))
        filetb.setIconSize(UI.Config.ToolBarIconSize)
        filetb.addAction(self.openUIAct)
        filetb.addAction(self.openQMAct)
        filetb.addAction(self.reloadAct)
        filetb.addSeparator()
        filetb.addAction(self.closeAct)
        filetb.addSeparator()
        filetb.addAction(self.exitAct)
        
        helptb = self.addToolBar(self.tr("Help"))
        helptb.setIconSize(UI.Config.ToolBarIconSize)
        helptb.addAction(self.whatsThisAct)
    
    def __whatsThis(self):
        """
        Private slot called in to enter Whats This mode.
        """
        QWhatsThis.enterWhatsThisMode()
        
    def __updateActions(self):
        """
        Private slot to update the actions state.
        """
        if self.preview.hasWidgets():
            self.closeAct.setEnabled(True)
            self.closeAllAct.setEnabled(True)
            self.tileAct.setEnabled(True)
            self.cascadeAct.setEnabled(True)
        else:
            self.closeAct.setEnabled(False)
            self.closeAllAct.setEnabled(False)
            self.tileAct.setEnabled(False)
            self.cascadeAct.setEnabled(False)
        
        if self.translations.hasTranslations():
            self.reloadAct.setEnabled(True)
        else:
            self.reloadAct.setEnabled(False)

    def __about(self):
        """
        Private slot to show the about information.
        """
        E5MessageBox.about(
            self,
            self.tr("TR Previewer"),
            self.tr(
                """<h3> About TR Previewer </h3>"""
                """<p>The TR Previewer loads and displays Qt User-Interface"""
                """ files and translation files and shows dialogs for a"""
                """ selected language.</p>"""
            )
        )
    
    def __aboutQt(self):
        """
        Private slot to show info about Qt.
        """
        E5MessageBox.aboutQt(self, self.tr("TR Previewer"))
    
    def __openWidget(self):
        """
        Private slot to handle the Open Dialog action.
        """
        fileNameList = E5FileDialog.getOpenFileNames(
            None,
            self.tr("Select UI files"),
            "",
            self.tr("Qt User-Interface Files (*.ui)"))
        
        for fileName in fileNameList:
            self.preview.loadWidget(fileName)
        
        self.__updateActions()
    
    def __openTranslation(self):
        """
        Private slot to handle the Open Translation action.
        """
        fileNameList = E5FileDialog.getOpenFileNames(
            None,
            self.tr("Select translation files"),
            "",
            self.tr("Qt Translation Files (*.qm)"))
        
        first = True
        for fileName in fileNameList:
            self.translations.add(fileName, first)
            first = False
        
        self.__updateActions()
    
    def setTranslation(self, name):
        """
        Public slot to activate a translation.
        
        @param name name (language) of the translation (string)
        """
        self.translations.set(name)
    
    def __showWindowMenu(self):
        """
        Private slot to handle the aboutToShow signal of the window menu.
        """
        self.windowMenu.clear()
        self.windowMenu.addAction(self.tileAct)
        self.windowMenu.addAction(self.cascadeAct)
        self.windowMenu.addSeparator()

        self.preview.showWindowMenu(self.windowMenu)
    
    def reloadTranslations(self):
        """
        Public slot to reload all translations.
        """
        self.translations.reload()


class Translation(object):
    """
    Class to store the properties of a translation.
    """
    def __init__(self):
        """
        Constructor
        """
        self.fileName = None
        self.name = None
        self.translator = None


class TranslationsDict(QObject):
    """
    Class to store all loaded translations.
    
    @signal translationChanged() emit after a translator was set
    """
    translationChanged = pyqtSignal()
    
    def __init__(self, selector, parent):
        """
        Constructor
        
        @param selector reference to the QComboBox used to show the
            available languages (QComboBox)
        @param parent parent widget (QWidget)
        """
        super(TranslationsDict, self).__init__(parent)
        
        self.selector = selector
        self.currentTranslator = None
        self.selector.addItem(noTranslationName)
        self.translations = []  # list of Translation objects
    
    def add(self, fileName, setTranslation=True):
        """
        Public method to add a translation to the list.
        
        If the translation file (*.qm) has not been loaded yet, it will
        be loaded automatically.
        
        @param fileName name of the translation file to be added (string)
        @param setTranslation flag indicating, if this should be set as
            the active translation (boolean)
        """
        if not self.__haveFileName(fileName):
            ntr = Translation()
            ntr.fileName = fileName
            ntr.name = self.__uniqueName(fileName)
            if ntr.name is None:
                E5MessageBox.warning(
                    self.parent(),
                    self.tr("Set Translator"),
                    self.tr(
                        """<p>The translation filename <b>{0}</b>"""
                        """ is invalid.</p>""").format(fileName))
                return
            
            ntr.translator = self.loadTransFile(fileName)
            if ntr.translator is None:
                return
            
            self.selector.addItem(ntr.name)
            self.translations.append(ntr)
        
        if setTranslation:
            tr = self.__findFileName(fileName)
            self.set(tr.name)
    
    def set(self, name):
        """
        Public slot to set a translator by name.
        
        @param name name (language) of the translator to set (string)
        """
        nTranslator = None
        
        if name != noTranslationName:
            trans = self.__findName(name)
            if trans is None:
                E5MessageBox.warning(
                    self.parent(),
                    self.tr("Set Translator"),
                    self.tr(
                        """<p>The translator <b>{0}</b> is not known.</p>""")
                    .format(name))
                return
                
            nTranslator = trans.translator
        
        if nTranslator == self.currentTranslator:
            return
        
        if self.currentTranslator is not None:
            QApplication.removeTranslator(self.currentTranslator)
        if nTranslator is not None:
            QApplication.installTranslator(nTranslator)
        self.currentTranslator = nTranslator
        
        self.selector.blockSignals(True)
        self.selector.setCurrentIndex(self.selector.findText(name))
        self.selector.blockSignals(False)
        
        self.translationChanged.emit()
    
    def reload(self):
        """
        Public method to reload all translators.
        """
        cname = self.selector.currentText()
        if self.currentTranslator is not None:
            QApplication.removeTranslator(self.currentTranslator)
            self.currentTranslator = None
        
        fileNames = []
        for trans in self.translations:
            trans.translator = None
            fileNames.append(trans.fileName)
        self.translations = []
        self.selector.clear()
        
        self.selector.addItem(noTranslationName)
        
        for fileName in fileNames:
            self.add(fileName, False)
        
        if self.__haveName(cname):
            self.set(cname)
        else:
            self.set(noTranslationName)
    
    def __findFileName(self, transFileName):
        """
        Private method to find a translation by file name.
        
        @param transFileName file name of the translation file (string)
        @return reference to a translation object or None
        """
        for trans in self.translations:
            if trans.fileName == transFileName:
                return trans
        return None
    
    def __findName(self, name):
        """
        Private method to find a translation by name.
        
        @param name name (language) of the translation (string)
        @return reference to a translation object or None
        """
        for trans in self.translations:
            if trans.name == name:
                return trans
        return None
    
    def __haveFileName(self, transFileName):
        """
        Private method to check for the presence of a translation.
        
        @param transFileName file name of the translation file (string)
        @return flag indicating the presence of the translation (boolean)
        """
        return self.__findFileName(transFileName) is not None
    
    def __haveName(self, name):
        """
        Private method to check for the presence of a named translation.
        
        @param name name (language) of the translation (string)
        @return flag indicating the presence of the translation (boolean)
        """
        return self.__findName(name) is not None
    
    def __uniqueName(self, transFileName):
        """
        Private method to generate a unique name.
        
        @param transFileName file name of the translation file (string)
        @return unique name (string or None)
        """
        name = os.path.basename(transFileName)
        if not name:
            return None
        
        uname = name
        cnt = 1
        while self.__haveName(uname):
            cnt += 1
            uname = "{0} <{1}>".format(name, cnt)
        
        return uname
    
    def __del(self, name):
        """
        Private method to delete a translator from the list of available
        translators.
        
        @param name name of the translator to delete (string)
        """
        if name == noTranslationName:
            return
        
        trans = self.__findName(name)
        if trans is None:
            return
        
        if self.selector().currentText() == name:
            self.set(noTranslationName)
        
        self.translations.remove(trans)
        del trans
    
    def loadTransFile(self, transFileName):
        """
        Public slot to load a translation file.
        
        @param transFileName file name of the translation file (string)
        @return reference to the new translator object (QTranslator)
        """
        tr = QTranslator()
        if tr.load(transFileName):
            return tr
        
        E5MessageBox.warning(
            self.parent(),
            self.tr("Load Translator"),
            self.tr("""<p>The translation file <b>{0}</b> could"""
                    """ not be loaded.</p>""").format(transFileName))
        return None

    def hasTranslations(self):
        """
        Public method to check for loaded translations.
        
        @return flag signaling if any translation was loaded (boolean)
        """
        return len(self.translations) > 0


class WidgetView(QWidget):
    """
    Class to show a dynamically loaded widget (or dialog).
    """
    def __init__(self, uiFileName, parent=None, name=None):
        """
        Constructor
        
        @param uiFileName name of the UI file to load (string)
        @param parent parent widget (QWidget)
        @param name name of this widget (string)
        """
        super(WidgetView, self).__init__(parent)
        if name:
            self.setObjectName(name)
            self.setWindowTitle(name)
        
        self.__widget = None
        self.__uiFileName = uiFileName
        self.__layout = QHBoxLayout(self)
        self.__valid = False
        self.__timer = QTimer(self)
        self.__timer.setSingleShot(True)
        self.__timer.timeout.connect(self.buildWidget)
    
    def isValid(self):
        """
        Public method to return the validity of this widget view.
        
        @return flag indicating the validity (boolean)
        """
        return self.__valid
    
    def uiFileName(self):
        """
        Public method to retrieve the name of the UI file.
        
        @return filename of the loaded UI file (string)
        """
        return self.__uiFileName
    
    def buildWidget(self):
        """
        Public slot to load a UI file.
        """
        if self.__widget:
            self.__widget.close()
            self.__layout.removeWidget(self.__widget)
            del self.__widget
            self.__widget = None
        
        try:
            self.__widget = uic.loadUi(self.__uiFileName)
        except:
            pass
        
        if not self.__widget:
            E5MessageBox.warning(
                self,
                self.tr("Load UI File"),
                self.tr(
                    """<p>The file <b>{0}</b> could not be loaded.</p>""")
                .format(self.__uiFileName))
            self.__valid = False
            return
        
        self.__widget.setParent(self)
        self.__layout.addWidget(self.__widget)
        self.__widget.show()
        self.__valid = True
        self.adjustSize()
        
        self.__timer.stop()
    
    def __rebuildWidget(self):
        """
        Private method to schedule a rebuild of the widget.
        """
        self.__timer.start(0)


class WidgetArea(QMdiArea):
    """
    Specialized MDI area to show the loaded widgets.
    
    @signal lastWidgetClosed() emitted after last widget was closed
    """
    lastWidgetClosed = pyqtSignal()
    rebuildWidgets = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        """
        super(WidgetArea, self).__init__(parent)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.widgets = []
    
    def loadWidget(self, uiFileName):
        """
        Public slot to load a UI file.
        
        @param uiFileName name of the UI file to load (string)
        """
        wview = self.__findWidget(uiFileName)
        if wview is None:
            name = os.path.basename(uiFileName)
            if not name:
                E5MessageBox.warning(
                    self,
                    self.tr("Load UI File"),
                    self.tr(
                        """<p>The file <b>{0}</b> could not be loaded.</p>""")
                    .format(uiFileName))
                return
            
            uname = name
            cnt = 1
            while self.findChild(WidgetView, uname) is not None:
                cnt += 1
                uname = "{0} <{1}>".format(name, cnt)
            name = uname
            
            wview = WidgetView(uiFileName, self, name)
            wview.buildWidget()
            if not wview.isValid():
                del wview
                return
            
            self.rebuildWidgets.connect(wview.buildWidget)  # __IGNORE_WARNING__
            wview.installEventFilter(self)  # __IGNORE_WARNING__
            
            win = self.addSubWindow(wview)  # __IGNORE_WARNING__
            self.widgets.append(win)
        
        wview.showNormal()  # __IGNORE_WARNING__
    
    def eventFilter(self, obj, ev):
        """
        Public method called to filter an event.
        
        @param obj object, that generated the event (QObject)
        @param ev the event, that was generated by object (QEvent)
        @return flag indicating if event was filtered out
        """
        if obj in self.widgets and ev.type() == QEvent.Close:
            try:
                self.widgets.remove(obj)
                if len(self.widgets) == 0:
                    self.lastWidgetClosed.emit()
            except ValueError:
                pass
        
        return QMdiArea.eventFilter(self, obj, ev)
    
    def __findWidget(self, uiFileName):
        """
        Private method to find a specific widget view.
        
        @param uiFileName filename of the loaded UI file (string)
        @return reference to the widget (WidgetView) or None
        """
        wviewList = self.findChildren(WidgetView)
        if wviewList is None:
            return None
        
        for wview in wviewList:
            if wview.uiFileName() == uiFileName:
                return wview
        
        return None
    
    def closeWidget(self):
        """
        Public slot to close the active window.
        """
        aw = self.activeSubWindow()
        if aw is not None:
            aw.close()
    
    def closeAllWidgets(self):
        """
        Public slot to close all windows.
        """
        for w in self.widgets[:]:
            w.close()
    
    def showWindowMenu(self, windowMenu):
        """
        Public method to set up the widgets part of the Window menu.
        
        @param windowMenu reference to the window menu
        """
        idx = 0
        for wid in self.widgets:
            act = windowMenu.addAction(wid.windowTitle())
            act.setData(idx)
            act.setCheckable(True)
            act.setChecked(not wid.isHidden())
            idx = idx + 1
    
    def toggleSelectedWidget(self, act):
        """
        Public method to handle the toggle of a window.
        
        @param act reference to the action that triggered (QAction)
        """
        idx = act.data()
        if idx is not None:
            self.__toggleWidget(self.widgets[idx])
    
    def __toggleWidget(self, w):
        """
        Private method to toggle a workspace window.
        
        @param w window to be toggled
        """
        if w.isHidden():
            w.show()
        else:
            w.hide()
    
    def hasWidgets(self):
        """
        Public method to check for loaded widgets.
        
        @return flag signaling if any widget was loaded (boolean)
        """
        return len(self.widgets) > 0
